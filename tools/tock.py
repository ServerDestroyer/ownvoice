#!/usr/bin/env python3
"""B4 tock — machine work between sittings (DESIGN.md §4). Idempotent: crash = re-run.

For every MEANING_LOCKED section: ground -> draft -> guard -> meld sweep -> guard
candidates -> grade -> rank -> REVIEW_READY. Also: TL;DR extraction for NEW sections.

Usage:  python3 tools/tock.py --state state [--sections s1,s2] [--dry-run]
        python3 tools/tock.py --selftest
Config: .env (meld model etc.); frozen meld config from tools/meld-v1.json once the
B1 test session freezes it (falls back to .env/defaults until then).
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from board import (Board, assert_no_open_holds, assert_no_prior_draft,  # noqa: E402
                   assert_review_ready, scores_never_gate)
from guard import apply_gate, guard, sentences  # noqa: E402
from meld import SEEDS, call, dotenv, is_prose, trigram_overlap  # noqa: E402

# What may FAIL machine prose at G4: omission and fabrication. The certainty classes
# (hedge/attribution/condition/polarity/booster) were measured on sentence-for-
# sentence seed rewrites (T1); real drafting and real polishing both restructure
# sentences ("not survey noise; it concentrates..." -> "...concentrates ... rather
# than representing survey noise"), and gating on them parked every section at the
# regen cap. They are reported as warnings, order the candidates, and reach the author
# with the diff at G5 — the human veto against the original is the mitigation the
# design names for the rewrite hazard (adjust-in-use 2026-09-01; the 168-row T1
# benchmark and the CLI keep the full gate).
MEANING_GATE = {("MISSING", "claim"), ("MISSING", "citation"), ("INVENTED", "citation"),
                ("INVENTED", "number"), ("CITED", "cut_citation")}
DRAFT_GATE = MEANING_GATE

TLDR_PROMPT = (
    "Extract a skeleton from this section for author review. Inputs follow: the "
    "existing draft, the template's requirements for this section, and the grounded "
    "source passages it cites.\nReturn markdown with these headings exactly:\n"
    "## Thesis/topic sentences\n## Main points (in order)\n## Jargon and named "
    "concepts\n## Figures/tables\n## Template requirements\n## Source claims NOT "
    "covered by the draft\n\n[DRAFT]\n{draft}\n\n[TEMPLATE REQUIREMENTS]\n{template}"
    "\n\n[GROUNDED SOURCE PASSAGES]\n{sources}")
DRAFT_PROMPT = (
    "Write this paper section from the locked skeleton and grounded source passages "
    "below. Follow the arc's argument thread: connected argumentation, not a claim "
    "list. Preserve every hedge, qualifier, attribution and citation exactly as the "
    "skeleton states them; do not strengthen or weaken any claim. Output running prose "
    "paragraphs only: no heading, no lists, no preface.{constraints}\n\n"
    "[SKELETON]\n{skeleton}\n\n[GROUNDED SOURCES]\n{sources}\n\n"
    "[TEMPLATE REQUIREMENTS]\n{template}")


def claims_of(skeleton: str) -> list[str]:
    """The locked meaning = the numbered/bulleted lines under '## Main points' (plus
    the thesis lines). Headers, jargon lists, template-compliance notes and 'not
    covered' notes are author-review material, NOT claims: guarding against them
    flagged every draft with ~70 failures (first end-to-end pass, 2026-09-01)."""
    claims, section = [], ""
    for line in skeleton.splitlines():
        s = line.strip()
        if s.startswith("#"):
            section = s.lower()
            continue
        if not s or not ("main points" in section or "thesis" in section):
            continue
        s = re.sub(r"^(\d+[.)]|[-*•])\s*", "", s)            # list marker
        # strip a "**Label:**" prefix ONLY if something survives it: a point bolded in
        # full ("- **The reform did not reduce turnout.**") matched end to end and the
        # substitution deleted the entire claim from the locked set (2026-09-01)
        unlabelled = re.sub(r"^\*\*[^*]{0,80}\*\*\s*:?\s*", "", s)
        s = (unlabelled if unlabelled.strip() else s.replace("**", "")).strip().strip('"“”')
        # one claim = one sentence: the guard compares a claim against ONE prose
        # sentence, and MiniCheck scores two-sentence claims as unsupported. Any
        # abbreviation ("vs.", "e.g.", "Fig.") splits mid-claim, and a 2-word fragment
        # aligns to almost anything, so short pieces rejoin what they came from.
        parts, merged = re.split(r"(?<!et al\.)(?<=[.!?])\s+", s), []
        for sent in (p.strip() for p in parts if p.strip()):
            joins = merged and (len(sent.split()) < 4 or merged[-1].rstrip().endswith(
                ("vs.", "e.g.", "i.e.", "cf.", "Fig.", "fig.", "No.", "Dr.", "St.", "al.")))
            if joins:
                merged[-1] += " " + sent
            else:
                merged.append(sent)
        claims.extend(m for m in merged if len(m.split()) >= 4)
    if not claims:  # a skeleton without those headings: every non-header line
        claims = [re.sub(r"^(\d+[.)]|[-*•])\s*", "", l.strip()) for l in skeleton.splitlines()
                  if l.strip() and not l.strip().startswith("#")]
    return claims


def cut_citations(state: Path, sid: str) -> list[str]:
    """Citations the author cut in the holds block: the drafter must not cite them."""
    p = state / "grounding-ledger.json"
    if not p.exists():
        return []
    return [c for c, e in json.loads(p.read_text()).items()
            if sid in e.get("sections", []) and e.get("adjudication") == "cut"]


def cite_pattern(cite: str) -> re.Pattern:
    """A ledger key like "Whitfield, 2017" in BOTH written forms — the parenthetical
    "(Whitfield, 2017)" and the narrative "Whitfield (2017)". The first version matched
    only the parenthetical, so a cut narrative citation was never stripped from the
    locked claims, the guard kept reporting it MISSING, and the section burned its
    three regenerations and parked (2026-09-01)."""
    m = re.match(r"(.+?),\s*(\d{4}[a-z]?)$", cite.strip())
    if not m:
        return re.compile(re.escape(cite))
    who, yr = re.escape(m.group(1).strip()), re.escape(m.group(2))
    return re.compile(rf"\s*(?:\({who},?\s*{yr}\)|{who}\s*\({yr}\)|{who},\s*{yr})")


def meld_config(cfg: dict) -> dict:
    frozen = Path(__file__).parent / "meld-v1.json"
    if frozen.exists():
        return json.loads(frozen.read_text())
    return {"model": cfg.get("MELD_MODEL", "qwen/qwen3.7-max"),
            "arm_id": cfg.get("MELD_ARMS", "").split(",")[0] or SEEDS["arms"][0]["id"],
            "temperature": float(cfg.get("MELD_TEMPERATURE", 0.2)),
            "thinking": cfg.get("MELD_THINKING", "off")}


def next_version(d: Path, stem: str) -> int:
    vs = [int(m.group(1)) for p in d.glob(f"{stem}.v*.md")
          if (m := re.match(rf"{stem}\.v(\d+)\.md", p.name))]
    return max(vs, default=0) + 1


def tldr(board: Board, sid: str, cfg: dict, dry: bool):
    d = board.section_dir(sid)
    draft0 = (d / "original.md").read_text() if (d / "original.md").exists() else ""
    template = (d / "template.md").read_text() if (d / "template.md").exists() else ""
    sources = (d / "grounded-sources.md").read_text() \
        if (d / "grounded-sources.md").exists() else ""
    prompt = TLDR_PROMPT.format(draft=draft0, template=template, sources=sources)
    if dry:
        print(f"[dry] tldr {sid}: {len(prompt)} chars")
        return
    out = call(cfg.get("MELD_MODEL", "qwen/qwen3.7-max"), "", prompt, 0.3)
    v = next_version(d, "skeleton")
    (d / f"skeleton.v{v}.md").write_text(out)
    board.data[sid]["skeleton_v"] = v
    board.set_status(sid, "TLDR_READY")


def guard_notes(rep: dict, include_claims: bool) -> str:
    """Turn a failing guard report into constraints for the next regeneration.

    I1 (no generator input ever contains a prior draft) is enforced HERE, by what this
    is allowed to quote — assert_no_prior_draft only compares whole blank-line
    paragraphs, so a single borrowed sentence slips past it. A finding's "sentence" is
    always output text and is never quoted. A finding's "claim" is skeleton text on the
    draft path (safe: the skeleton is already in the prompt) but is a DRAFT sentence on
    the polisher path, where the guard runs prose against the paragraph it rewrote — so
    that path passes include_claims=False and gets cues and tokens only (2026-09-01)."""
    notes = []
    for f in rep["findings"]:
        if f["severity"] != "fail":
            continue
        what = f"{f['type']} {f.get('property', '')}".strip()
        cue = f.get("cue") or f.get("token")
        claim = (f.get("claim") or "")[:160] if include_claims else ""
        notes.append(f"- {what}" + (f" '{cue}'" if cue else "") + (f" in: {claim}" if claim else ""))
    if len(notes) > 12:
        notes = notes[:12] + [f"- (+{len(notes) - 12} more of the same kinds)"]
    return "\n".join(notes)


def pipeline(board: Board, sid: str, cfg: dict, dry: bool, prior_notes: str = ""):
    d = board.section_dir(sid)
    sk_v = board.data[sid]["skeleton_v"] or 1
    skeleton = (d / f"skeleton.v{sk_v}.md").read_text()
    claims = claims_of(skeleton)
    cut = cut_citations(board.state, sid)
    for c in cut:  # a cut citation leaves the locked claims too
        claims = [cite_pattern(c).sub("", x).strip() for x in claims]
    claims = [c for c in claims if len(c.split()) >= 4]
    claims_text = "\n".join(f"- {c}" for c in claims)  # what the guard holds the prose to

    # G3 — ground: every claim resolves or the section holds (I3 enforced)
    board.set_status(sid, "GROUNDING")
    assert_no_open_holds(board.state, sid, claims)
    board.record_gate(sid, "G3", {"claims": len(claims), "verdict": "PASS"})
    board.set_status(sid, "GROUNDED")

    sources = (d / "grounded-sources.md").read_text() \
        if (d / "grounded-sources.md").exists() else ""
    template = (d / "template.md").read_text() if (d / "template.md").exists() else ""
    complaints = (d / f"complaints.v{sk_v}.md").read_text() \
        if (d / f"complaints.v{sk_v}.md").exists() else ""
    constraints = f"\nConstraints from prior review (do not echo, obey):\n{complaints}" \
        if complaints else ""
    if cut:
        constraints += ("\nThe author has CUT these citations: do not cite them; keep the "
                        "claims they were attached to, stated as the author's own: " + "; ".join(cut))
    if prior_notes:
        constraints += ("\nThe previous attempt failed the meaning guard on these points; keep "
                        "every listed cue in the sentence that carries its claim:\n" + prior_notes)

    # draft — I1: skeleton + sources + constraints + anchors, NEVER a prior draft
    parts = {"skeleton": skeleton, "sources": sources, "template": template,
             "constraints": constraints}
    assert_no_prior_draft(parts, d)
    if dry:
        print(f"[dry] draft {sid}: skeleton v{sk_v}, {len(claims)} claims")
        return
    draft = call(cfg.get("MELD_MODEL", "qwen/qwen3.7-max"), "",
                 DRAFT_PROMPT.format(**parts), 0.5)
    dv = next_version(d, "draft")
    (d / f"draft.v{dv}.md").write_text(draft)
    board.set_status(sid, "DRAFTED")

    # G4 on the draft — against the locked claims, not the whole review skeleton;
    # radius 1 because prose written from a skeleton does not keep sentence boundaries
    # certified material for the fabrication check = everything the drafter was given
    # (the whole skeleton + sources), not just the claim lines
    rep = guard(claims_text, draft, skeleton + "\n\n" + sources, state=board.state)
    # I3, mechanically: a cut citation must be ABSENT from the prose. Until now the
    # only thing keeping it out was a sentence of English in the prompt, and nothing
    # in the stack could detect a generator that ignored it (2026-09-01).
    for c in cut:
        if cite_pattern(c).search(draft):
            rep["findings"].append({"type": "CITED", "property": "cut_citation",
                                    "token": c, "severity": "fail",
                                    "note": "the author cut this citation at the holds block"})
    rep = apply_gate(rep, DRAFT_GATE)
    (d / f"guards.v{dv}.json").write_text(json.dumps(rep, indent=1))
    board.record_gate(sid, "G4", {"target": "draft", "verdict": rep["verdict"]})
    if rep["verdict"] != "PASS":
        board.bump_retry(sid)  # raises to AUTHOR_WRITING at the cap
        # notes may quote the SKELETON claim here (it is already in the prompt); the
        # polisher path below must not, so it passes include_claims=False (I1)
        return pipeline(board, sid, cfg, dry, guard_notes(rep, include_claims=True))

    # diagnostic only (never gates): skeleton copy-rate
    copy_rate = trigram_overlap(draft, skeleton)

    # meld sweep — frozen config; anchors from state/anchors/
    mc = meld_config(cfg)
    anchors = sorted((board.state / "anchors").glob("*.md"))[:2]  # default 2, widen on flags
    cand_dir = d / f"candidates.v{dv}"
    cand_dir.mkdir(exist_ok=True)
    arm = next(a for a in SEEDS["arms"] if a["id"] == mc["arm_id"])
    survivors, diag = [], {}
    for i, anchor_f in enumerate(anchors or [None]):
        anchor = anchor_f.read_text().strip() if anchor_f else ""
        melded_paras, findings, not_checked = [], [], set()
        for para in [p for p in re.split(r"\n\s*\n", draft) if p.strip()]:
            if not is_prose(para):  # headings, lists, tables, boxes pass through untouched
                melded_paras.append(para)
                continue
            system = (arm["system"] + "\n\n" + SEEDS["discipline_clause"]).strip()
            polished = call(mc["model"], system,
                            arm["user"].format(anchor=anchor, draft=para),
                            mc["temperature"], mc.get("thinking", "off"))
            melded_paras.append(polished)
            # G4 on the polish: the full guard, sentence for sentence against the
            # draft paragraph it rewrote — the setting T1/T1b measured it in
            para_claims = "\n".join(f"- {s}" for s in sentences(para))
            prep = guard(para_claims, polished, sources, state=board.state)
            findings += prep["findings"]
            not_checked |= set(prep["not_checked"])
        cand = "\n\n".join(melded_paras)
        crep = apply_gate({"verdict": "", "findings": findings, "not_checked": sorted(not_checked)},
                          MEANING_GATE)
        name = f"cand-{i + 1}"
        # diagnostics for ordering and for the sitting — never gates (I7): warnings
        # from the guard, and how much of the anchor's wording leaked into the prose
        # (research/11's matched-anchor hazard; seen live on the first pass)
        diag[name] = {"warnings": crep["warnings"], "leak_vs_anchor": trigram_overlap(cand, anchor),
                      "copy_vs_draft": trigram_overlap(cand, draft), "anchor": anchor_f.name if anchor_f else None}
        (cand_dir / f"{name}.md").write_text(cand)
        (cand_dir / f"{name}.guards.json").write_text(json.dumps(crep, indent=1))
        board.record_gate(sid, "G4", {"target": name, "verdict": crep["verdict"]})
        if crep["verdict"] == "PASS":
            survivors.append(name)
    board.set_status(sid, "MELDED")
    if not survivors:
        board.bump_retry(sid)
        # include_claims=False: on this path a finding's "claim" is a sentence of the
        # DRAFT, and no prior draft may reach a generator input (I1)
        return pipeline(board, sid, cfg, dry, guard_notes(crep, include_claims=False))

    # grade + rank survivors (scores order candidates; they never gate — I7):
    # fewest guard warnings first, then least anchor leakage
    survivors.sort(key=lambda n: (diag[n]["warnings"], diag[n]["leak_vs_anchor"]))
    grades = {"copy_rate_draft_vs_skeleton": copy_rate, "ranking": survivors,
              "candidates": diag,
              "note": "ranking = (guard warnings, anchor leakage); the author sees every warning at G5"}
    (d / "grades.json").write_text(json.dumps(grades, indent=1))
    scores_never_gate({"guard_verdicts": "PASS"})  # the only gate inputs
    assert_review_ready(board, sid)  # I2
    board.set_status(sid, "REVIEW_READY")
    print(f"{sid}: REVIEW_READY ({len(survivors)} candidates)")


def run(state: Path, only: list[str], dry: bool):
    board = Board(state)
    board.assert_wip()  # I4
    cfg = dotenv()
    for sid, v in sorted(board.data.items(), key=lambda kv: kv[1]["arc"]):
        if only and sid not in only:
            continue
        if v["status"] == "NEW" and v["type"] not in ("administrative", "boilerplate",
                                                      "procedural"):
            tldr(board, sid, cfg, dry)
        elif v["status"] == "NEW":
            board.set_status(sid, "SKIM")  # light path: SKIM -> G5, routed by type only
        elif v["status"] in ("MEANING_LOCKED", "GROUNDING", "GROUNDED", "DRAFTED", "MELDED"):
            # the mid-pipeline statuses are where a crash leaves a section; resuming
            # regenerates from the locked skeleton (drafts are versioned, I1 holds),
            # which is what "idempotent: crash = re-run" promises
            try:
                pipeline(board, sid, cfg, dry)
            except Exception as e:  # I3 holds / I5 caps park the section, tock continues
                print(f"{sid}: parked — {e}", file=sys.stderr)


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        st = Path(td) / "state"
        b = Board(st)
        b.add_section("s1", 1)
        d = b.section_dir("s1")
        (d / "skeleton.v1.md").write_text("- X may hold (Smith, 2020).")
        b.data["s1"]["skeleton_v"] = 1
        b.set_status("s1", "MEANING_LOCKED")
        # dry pipeline reaches the draft stage with I1/I3 asserted
        run(st, ["s1"], dry=True)
        # light path: template-type routing, never a score
        b.add_section("adm", 1, stype="administrative")
        run(st, ["adm"], dry=True)
        assert json.loads(b.path.read_text())["adm"]["status"] == "SKIM"
        # open hold parks the section instead of generating prose (I3)
        (st / "grounding-ledger.json").write_text(json.dumps(
            {"Chen, 2022": {"resolves": False, "sections": ["s1"]}}))
        run(st, ["s1"], dry=True)  # prints parked, must not raise
        assert meld_config({})["model"]
        assert next_version(d, "draft") == 1

        # claims_of: only the meaning sections, and no claim may be deleted or split
        sk = ("## Thesis/topic sentences\n"
              "* Modelled comfort and reported comfort diverge in schools.\n"
              "\n## Main points (in order)\n"
              "1. **The reform did not reduce turnout.**\n"
              "2. **Limit:** Adaptive vs. steady-state models differ in mechanically "
              "ventilated rooms.\n"
              "3. Okafor et al. (2022) pooled 74 studies and found a small association.\n"
              "\n## Jargon and named concepts\n* Running mean window\n"
              "\n## Source claims NOT covered by the draft\n* Author note: resolve this.\n")
        cl = claims_of(sk)
        # a fully bold-emphasised point survives (the strip used to empty the line)
        assert any("reform did not reduce turnout" in c for c in cl), cl
        # "vs." does not tear one claim into two alignable fragments
        assert any("Adaptive vs. steady-state" in c and "ventilated rooms" in c
                   for c in cl), cl
        # "et al." likewise
        assert any(c.startswith("Okafor et al. (2022) pooled") for c in cl), cl
        assert not any("Running mean window" in c or "Author note" in c for c in cl), cl
        assert len(cl) == 4, cl

        # a cut citation is stripped in BOTH written forms, and detected if it leaks
        for form in ("The limit is shared (Whitfield, 2017).",
                     "The limit is shared with Whitfield (2017)."):
            assert "Whitfield" not in cite_pattern("Whitfield, 2017").sub("", form), form
            assert cite_pattern("Whitfield, 2017").search(form), form
        assert not cite_pattern("Whitfield, 2017").search("Whitfield argues the opposite.")
        assert ("CITED", "cut_citation") in MEANING_GATE   # a leak must FAIL, not warn

        # guard_notes never quotes prose that came from a draft (I1)
        rep = {"findings": [
            {"type": "MISSING", "property": "claim", "severity": "fail",
             "claim": "A verbatim sentence lifted from the previous draft."},
            {"type": "MISSING", "property": "citation", "token": "(Smith, 2020)",
             "severity": "fail"},
            {"type": "DROPPED", "property": "hedge", "cue": "may", "severity": "warn"}]}
        polish = guard_notes(rep, include_claims=False)
        assert "verbatim sentence" not in polish, polish        # the I1 guarantee
        assert "(Smith, 2020)" in polish and "MISSING claim" in polish, polish
        assert "may" not in polish                              # warnings are not constraints
        assert "verbatim sentence" in guard_notes(rep, include_claims=True)
    print("selftest ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="state")
    ap.add_argument("--sections", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    else:
        run(Path(a.state), [s for s in a.sections.split(",") if s], a.dry_run)
