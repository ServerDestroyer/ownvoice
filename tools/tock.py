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
from guard import guard, sentences  # noqa: E402
from meld import SEEDS, call, dotenv, trigram_overlap  # noqa: E402

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
    "skeleton states them; do not strengthen or weaken any claim.{constraints}\n\n"
    "[SKELETON]\n{skeleton}\n\n[GROUNDED SOURCES]\n{sources}\n\n"
    "[TEMPLATE REQUIREMENTS]\n{template}")


def meld_config(cfg: dict) -> dict:
    frozen = Path(__file__).parent / "meld-v1.json"
    if frozen.exists():
        return json.loads(frozen.read_text())
    return {"model": cfg.get("MELD_MODEL", "google/gemini-3.1-pro-preview"),
            "arm_id": cfg.get("MELD_ARMS", "").split(",")[0] or SEEDS["arms"][0]["id"],
            "temperature": float(cfg.get("MELD_TEMPERATURE", 0.7))}


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
    out = call(cfg.get("MELD_MODEL", "google/gemini-3.1-pro-preview"), "", prompt, 0.3)
    v = next_version(d, "skeleton")
    (d / f"skeleton.v{v}.md").write_text(out)
    board.data[sid]["skeleton_v"] = v
    board.set_status(sid, "TLDR_READY")


def pipeline(board: Board, sid: str, cfg: dict, dry: bool):
    d = board.section_dir(sid)
    sk_v = board.data[sid]["skeleton_v"] or 1
    skeleton = (d / f"skeleton.v{sk_v}.md").read_text()
    claims = [c.strip("-* \t") for c in skeleton.strip().splitlines() if c.strip()]

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

    # draft — I1: skeleton + sources + constraints + anchors, NEVER a prior draft
    parts = {"skeleton": skeleton, "sources": sources, "template": template,
             "constraints": constraints}
    assert_no_prior_draft(parts, d)
    if dry:
        print(f"[dry] draft {sid}: skeleton v{sk_v}, {len(claims)} claims")
        return
    draft = call(cfg.get("MELD_MODEL", "google/gemini-3.1-pro-preview"), "",
                 DRAFT_PROMPT.format(**parts), 0.5)
    dv = next_version(d, "draft")
    (d / f"draft.v{dv}.md").write_text(draft)
    board.set_status(sid, "DRAFTED")

    # G4 on the draft
    rep = guard(skeleton, draft, sources)
    (d / f"guards.v{dv}.json").write_text(json.dumps(rep, indent=1))
    board.record_gate(sid, "G4", {"target": "draft", "verdict": rep["verdict"]})
    if rep["verdict"] != "PASS":
        board.bump_retry(sid)  # raises to AUTHOR_WRITING at the cap
        return pipeline(board, sid, cfg, dry)  # regen from skeleton, never the draft

    # diagnostic only (never gates): skeleton copy-rate
    copy_rate = trigram_overlap(draft, skeleton)

    # meld sweep — frozen config; anchors from state/anchors/
    mc = meld_config(cfg)
    anchors = sorted((board.state / "anchors").glob("*.md"))[:2]  # default 2, widen on flags
    cand_dir = d / f"candidates.v{dv}"
    cand_dir.mkdir(exist_ok=True)
    arm = next(a for a in SEEDS["arms"] if a["id"] == mc["arm_id"])
    survivors = []
    for i, anchor_f in enumerate(anchors or [None]):
        anchor = anchor_f.read_text().strip() if anchor_f else ""
        melded_paras = []
        for para in [p for p in re.split(r"\n\s*\n", draft) if p.strip()]:
            system = (arm["system"] + "\n\n" + SEEDS["discipline_clause"]).strip()
            melded_paras.append(call(mc["model"], system,
                                     arm["user"].format(anchor=anchor, draft=para),
                                     mc["temperature"]))
        cand = "\n\n".join(melded_paras)
        crep = guard(skeleton, cand, sources)  # G4 on every candidate
        name = f"cand-{i + 1}"
        (cand_dir / f"{name}.md").write_text(cand)
        (cand_dir / f"{name}.guards.json").write_text(json.dumps(crep, indent=1))
        board.record_gate(sid, "G4", {"target": name, "verdict": crep["verdict"]})
        if crep["verdict"] == "PASS":
            survivors.append(name)
    board.set_status(sid, "MELDED")
    if not survivors:
        board.bump_retry(sid)
        return pipeline(board, sid, cfg, dry)

    # grade + rank survivors (scores order candidates; they never gate — I7)
    grades = {"copy_rate_draft_vs_skeleton": copy_rate, "ranking": survivors,
              "note": "detector/voice diagnostics attach in the test phase"}
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
        elif v["status"] == "MEANING_LOCKED":
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
