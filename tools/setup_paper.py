#!/usr/bin/env python3
"""Paper setup — one command from intake/<paper>/ to a walkable state tree (DESIGN §4).

Usage:  python3 tools/setup_paper.py --intake intake/standin --work runs/standin \\
            [--anchors runs/b1/anchors]
        python3 tools/setup_paper.py --selftest

Runs the intake gate (G0; refuses on a blocking gap) and the citation grounder (G1),
then materialises what tock.py expects and nothing used to create:
  <work>/state/board.json, grounding-ledger.json, holds-report.md, anchors/
  <work>/sections/<sid>/original.md          the section's prose as drafted
  <work>/sections/<sid>/template.md          that section's template block (id/type/arc)
  <work>/sections/<sid>/grounded-sources.md  the located source paragraph per citation
Section ids, types and arcs come from the template: each '## ...' block must carry
'- **id:**', '- **type:**' and '- **arc:**' lines (the anti-drift spine). A paper
section with no template entry is registered as type standard, arc --arc-default,
and reported. Re-running is safe: registered sections are left as they are.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from board import LIGHT_TYPES, Board  # noqa: E402
from intake_check import check  # noqa: E402
from prepass import BM25, extract_citations, paragraphs, run_prepass, sections_of  # noqa: E402


def template_sections(text: str) -> dict:
    """{section_id: {type, arc, block}} from '##'/'###' blocks with id/type/arc lines.

    Splits on two OR three hashes: a template that groups sections under a '##' part
    heading with a '###' per section used to collapse into one entry, taking the first
    id it found anywhere in the group and applying that group's type to every section
    in it — and a wrong type routes a section down the unguarded light path. Duplicate
    ids are a hard error for the same reason (2026-09-01)."""
    out = {}
    for head, body in re.findall(r"^#{2,3}\s+(.+?)\n(.*?)(?=^#{2,3}\s|\Z)", text,
                                 flags=re.M | re.S):
        sid = re.search(r"\*\*id:\*\*\s*`?([\w\-]+)`?", body)
        if not sid:
            continue
        typ = re.search(r"\*\*type:\*\*\s*(\w+)", body)
        arc = re.search(r"\*\*arc:\*\*\s*(\d+)", body)
        key = sid.group(1)
        if key in out:
            sys.exit(f"template declares id '{key}' twice — ids must be unique, "
                     "or sections silently inherit the wrong type and arc")
        out[key] = {"type": typ.group(1) if typ else "standard",
                    "arc": int(arc.group(1)) if arc else 1,
                    "block": f"## {head.strip()}\n{body.strip()}"}
    return out


def carry_author_decisions(prior: dict, fresh: dict) -> dict:
    """Re-apply the author's hold adjudications after the ledger is rebuilt.

    tick.holds_block writes the author's decisions INTO grounding-ledger.json — cut,
    "own" (AUTHOR_CLAIM), or a re-grounded source and locator. setup() always re-runs
    the prepass, which builds a ledger from scratch, so re-running setup after a
    sitting silently erased every one of them and asked the author again (2026-09-01)."""
    carried = 0
    for cite, old in prior.items():
        new = fresh.get(cite)
        if new is None:
            continue
        touched = ("adjudication" in old or old.get("source") == "AUTHOR_CLAIM"
                   or (old.get("resolves") and not new.get("resolves")))
        if not touched:
            continue
        for k in ("adjudication", "resolves", "source", "locator"):
            if k in old:
                new[k] = old[k]
        carried += 1
    return fresh, carried


WHOLE_SOURCE_WORDS = 2500  # a short source goes in whole; a long one by relevance


def grounded_sources(body: str, ledger: dict) -> str:
    """One block per citation in the section: locator, then the source material the
    drafter and guard may rely on — the whole source when it is short, otherwise the
    located paragraph plus the passages that best match the citing sentence (BM25).
    The located paragraph alone was the bibliographic line, which starved the drafter
    of content and made every sourced number read as invented (first pass, 2026-09-01)."""
    seen, blocks = set(), []
    for cite, sentence in extract_citations(body):
        if cite in seen:
            continue
        seen.add(cite)
        e = ledger.get(cite) or {}
        # NB: the citing sentence is deliberately NOT written into this file. It is a
        # verbatim sentence of the author's existing prose, and tock hands this whole
        # file to the drafter as [GROUNDED SOURCES] — which would put the prior draft
        # into a generator input, the one thing I1 forbids, invisibly to
        # assert_no_prior_draft (it only compares whole paragraphs). The author still
        # sees the citing sentence in state/holds-report.md (2026-09-01).
        if not e.get("resolves"):
            blocks.append(f"## ({cite}) — UNRESOLVED (open hold)")
            continue
        if e.get("source") == "AUTHOR_CLAIM":
            blocks.append(f"## ({cite}) — the author's own claim (no source)")
            continue
        loc = e.get("locator") or {}
        where = loc.get("published") or f"paragraph {loc.get('para')} (needs committee-verifiable mapping)"
        src = Path(e["source"])
        paras = paragraphs(src.read_text(errors="replace"))
        if sum(len(p.split()) for p in paras) <= WHOLE_SOURCE_WORDS:
            text = "\n\n".join(paras)
        else:
            idx = BM25()
            idx.add(str(src), paras)
            idx.finish()
            keep = {loc.get("para")} if loc.get("para") is not None else set()
            keep |= {i for _score, _src, i, _raw in idx.search(sentence, n=5)}
            text = "\n\n".join(f"[¶{i}] {paras[i]}" for i in sorted(k for k in keep if k is not None and k < len(paras)))
        blocks.append(f"## ({cite}) — {src.name}, {where}\n\n{text}")
    return "\n\n".join(blocks) + "\n" if blocks else "(no citations in this section)\n"


def setup(intake: Path, work: Path, anchors: Path | None, arc_default: int):
    gaps = [g for g in check(intake) if "not a blocker" not in g]
    if gaps:
        sys.exit("G0 FAIL — fix the intake first:\n" + "\n".join("  " + g for g in gaps))
    state = work / "state"
    state.mkdir(parents=True, exist_ok=True)
    papers = [p for p in (intake / "paper").rglob("*.md") if p.name.lower() != "readme.md"]
    if len(papers) != 1:
        sys.exit(f"expected exactly one paper markdown in {intake / 'paper'}, found {len(papers)}")
    paper = papers[0]
    ledger_path = state / "grounding-ledger.json"
    prior = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    run_prepass(paper, intake / "sources", state)  # G1
    ledger, carried = carry_author_decisions(prior, json.loads(ledger_path.read_text()))
    if carried:
        ledger_path.write_text(json.dumps(ledger, indent=1))
    tmpl_text = "\n\n".join(p.read_text() for p in sorted((intake / "template").rglob("*.md"))
                            if p.name.lower() != "readme.md")
    tmpl = template_sections(tmpl_text)
    board = Board(state)
    registered, untemplated, retyped = [], [], []
    for sid, body in sections_of(paper.read_text()):
        if sid == "_preamble":
            continue
        t = tmpl.get(sid)
        if not t:
            untemplated.append(sid)
        d = board.section_dir(sid)
        (d / "original.md").write_text(body.strip() + "\n")
        (d / "template.md").write_text((t["block"] if t else f"(no template entry for `{sid}`)") + "\n")
        (d / "grounded-sources.md").write_text(grounded_sources(body, ledger))
        want = (t["type"] if t else "standard", t["arc"] if t else arc_default)
        if sid not in board.data:
            board.add_section(sid, want[1], want[0])
        elif board.data[sid]["status"] in ("NEW", "SKIM") and \
                (board.data[sid]["type"], board.data[sid]["arc"]) != want:
            # the template is the spine, so correcting a type or arc there must reach
            # a section that has not started work. Only before work begins: re-typing
            # a section mid-flight would strand its drafts. Previously the template
            # file on disk was rewritten but the board kept the first registration,
            # so a mis-typed section stayed on the unguarded SKIM path (2026-09-01).
            board.data[sid].update(type=want[0], arc=want[1],
                                   status="NEW" if want[0] not in LIGHT_TYPES else "SKIM")
            board._write()
            retyped.append(f"{sid} -> {want[0]}, arc {want[1]}")
        registered.append(sid)
    if anchors:
        (state / "anchors").mkdir(exist_ok=True)
        for a in sorted(anchors.glob("anchor*.md")):
            shutil.copy(a, state / "anchors" / a.name)
    holds = [c for c, e in ledger.items() if not e.get("resolves")]
    print(f"sections registered: {len(registered)} -> {work / 'sections'}")
    for sid in registered:
        v = board.data[sid]
        print(f"  {sid:48} arc {v['arc']}  type {v['type']}")
    if untemplated:
        print(f"NOT IN TEMPLATE (registered as standard, arc {arc_default}): {untemplated}")
    if retyped:
        print(f"re-typed from the template (not yet started): {retyped}")
    if carried:
        print(f"carried {carried} author hold decision(s) through the ledger rebuild")
    print(f"citations: {len(ledger) - len(holds)}/{len(ledger)} resolved; {len(holds)} open holds -> {state / 'holds-report.md'}")
    if holds:
        print("  sections with open holds cannot draft until the author resolves them (I3): "
              + ", ".join(sorted({s for c in holds for s in ledger[c]['sections']})))
    print(f"anchors: {len(list((state / 'anchors').glob('*.md'))) if anchors else 0} in {state / 'anchors'}")
    print(f"board: {state / 'board.json'}")


def selftest():
    import tempfile
    t = template_sections("## 1. Intro\n\n- **id:** `intro`\n- **type:** argumentative\n- **arc:** 2\n- x\n\n## 2. Methods\n- **id:** methods\n- **type:** procedural\n")
    assert t["intro"] == {"type": "argumentative", "arc": 2, "block": t["intro"]["block"]} and "arc:** 2" in t["intro"]["block"]
    assert t["methods"]["type"] == "procedural" and t["methods"]["arc"] == 1
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for d in ("paper", "sources", "template", "author-corpus"):
            (td / "in" / d).mkdir(parents=True)
        (td / "in/paper/paper.md").write_text("## Intro\nA claim (Smith, 2020). A broken one (Chen, 2022).\n## Methods\nSteps.\n")
        (td / "in/sources/smith2020.md").write_text("Smith 2020 on turnout.\n\nTurnout rose.")
        (td / "in/sources/smith2020.locators.json").write_text('{"0": "p. 3"}')
        (td / "in/template/t.md").write_text("## Intro\n- **id:** intro\n- **type:** argumentative\n- **arc:** 1\n## Methods\n- **id:** methods\n- **type:** procedural\n- **arc:** 1\n")
        (td / "in/author-corpus/me.md").write_text("my prose " * 20)
        (td / "anch").mkdir(); (td / "anch/anchor1.md").write_text("anchor")
        setup(td / "in", td / "work", td / "anch", 1)
        b = json.loads((td / "work/state/board.json").read_text())
        assert b["intro"]["type"] == "argumentative" and b["methods"]["type"] == "procedural"
        gs = (td / "work/sections/intro/grounded-sources.md").read_text()
        assert "p. 3" in gs and "Smith 2020 on turnout" in gs and "UNRESOLVED" in gs, gs
        assert (td / "work/sections/methods/original.md").read_text().strip() == "Steps."
        assert (td / "work/state/anchors/anchor1.md").exists()
        setup(td / "in", td / "work", td / "anch", 1)  # idempotent re-run
        assert json.loads((td / "work/state/board.json").read_text())["intro"]["status"] == "NEW"
    print("selftest ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--intake"); ap.add_argument("--work")
    ap.add_argument("--anchors", help="dir of anchor*.md to copy into state/anchors/")
    ap.add_argument("--arc-default", type=int, default=1)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    elif a.intake and a.work:
        setup(Path(a.intake), Path(a.work), Path(a.anchors) if a.anchors else None, a.arc_default)
    else:
        ap.print_help()
