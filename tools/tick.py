#!/usr/bin/env python3
"""B4 tick — one bounded human sitting (DESIGN.md §4 tick mechanics, research/13).

Order: print board -> meaning block (arc N+1, per-item questions, fresh attention)
-> holds block -> approval block (arc N) -> arc close (learnings ratification).
Mechanics encoded: commit after EVERY item (I8); seeded defects at ~1-in-12 with
immediate feedback; commit-before-reveal; side-by-side layout; two micro-diversions
per sitting; block <= 50 min, sitting hard-stop at 90; end on an approved section and
open the next arc's first skeleton. 2-AFC voice calibration: identification question
("which is your unassisted writing?"), never preference; catch trials; cumulative.

Usage:  python3 tools/tick.py --state state [--arc N]
        python3 tools/tick.py --selftest
Interactive; run it in a terminal. Every answer is written to disk immediately.
"""
import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from board import Board, approve  # noqa: E402
from learnings import learnings_hash, load_all  # noqa: E402

BLOCK_MIN, SITTING_MIN = 50, 90
SEED_EVERY = 12  # ~1-in-10–15 items
MEANING_QUESTIONS = {  # item-specific — never a bare three-button tick
    "thesis": "Verified against which source, or amended to say what?",
    "point": "Where is this stated in the sources (or is it your own claim)?",
    "jargon": "Is this the exact term you use? If not, give yours.",
    "figure": "Does this figure/table exist and show what the skeleton claims?",
    "requirement": "Does the section meet this template requirement? How?",
}


class Sitting:
    def __init__(self, state: Path):
        self.state = state
        self.t0 = time.monotonic()
        self.block_t0 = self.t0
        self.items = 0
        self.diversions_done = 0
        self.log = state / "sittings.jsonl"
        self.seeds = sorted((Path(__file__).parent / "seeds").glob("*.json"))
        self.seed_hits = self.seed_misses = 0

    def elapsed_min(self):
        return (time.monotonic() - self.t0) / 60

    def check_time(self) -> bool:
        """True = keep going. Enforces block <=50 and sitting <=90."""
        if self.elapsed_min() >= SITTING_MIN:
            print(f"\n== HARD STOP: sitting at {SITTING_MIN} min. Stop now. ==")
            return False
        if (time.monotonic() - self.block_t0) / 60 >= BLOCK_MIN:
            print(f"\n== Block at {BLOCK_MIN} min: take a break before the next block. ==")
            input("[enter] to start the next block ")
            self.block_t0 = time.monotonic()
        return True

    def maybe_diversion(self):
        """Two scripted ~2s goal-deactivating breaks per sitting."""
        half = SITTING_MIN / 2
        due = (self.diversions_done == 0 and self.elapsed_min() > half / 2) or \
              (self.diversions_done == 1 and self.elapsed_min() > half)
        if due:
            self.diversions_done += 1
            input("\n-- micro-diversion: look away from the screen, name one object "
                  "you can see. [enter] --")

    def record(self, kind: str, payload: dict):
        """Commit after every item (I8)."""
        with self.log.open("a") as f:
            f.write(json.dumps({"ts": time.strftime("%F %T"), "kind": kind,
                                **payload}) + "\n")
        self.items += 1

    def maybe_seeded_defect(self) -> bool:
        """Seeded defect at ~1-in-12, immediate feedback. Returns False on hard stop."""
        if not self.seeds or self.items % SEED_EVERY != SEED_EVERY - 1:
            return True
        seed = json.loads(random.choice(self.seeds).read_text())
        print("\n[review this paragraph against its original]")
        print(f"ORIGINAL: {seed['original']}\nCANDIDATE: {seed['seeded']}")
        ans = input("Any meaning/certainty defect? (describe, or 'none') > ").strip()
        caught = ans.lower() not in ("", "none", "no")
        if caught:
            self.seed_hits += 1
            print(f"HIT — this was a seeded {seed['class']}. Good catch.")
        else:
            self.seed_misses += 1
            print(f"MISS — this was a seeded {seed['class']}: compare again. "
                  "Defects ARE present in this stream; keep looking.")
        self.record("seeded_defect", {"class": seed["class"], "caught": caught})
        return self.check_time()


def meaning_block(b: Board, s: Sitting, arc: int):
    """G2 for arc N+1. Every item marked verified/amended/added with an
    item-specific answer; side-by-side across the arc's skeletons."""
    secs = [sid for sid, v in b.data.items()
            if v["arc"] == arc and v["status"] == "TLDR_READY"]
    if not secs:
        return
    print(f"\n=== MEANING BLOCK — arc {arc} ({len(secs)} sections, side by side) ===")
    for sid in secs:
        print(f"\n--- {sid} skeletons are in {b.section_dir(sid)} — read them "
              f"side by side before answering ---")
    for sid in secs:
        sk = b.section_dir(sid) / f"skeleton.v{b.data[sid]['skeleton_v'] or 1}.md"
        items = [l.strip("-* \t") for l in sk.read_text().splitlines()
                 if l.strip() and not l.startswith("#")]
        marks = []
        for it in items:
            if not s.maybe_seeded_defect() or not s.check_time():
                return
            q = MEANING_QUESTIONS["point"]
            print(f"\n[{sid}] {it}")
            ans = input(f"  {q}\n  verified/amended/added + answer (or 'hold') > ").strip()
            if ans.lower() == "hold":
                b.set_status(sid, "HELD_MEANING")
                s.record("meaning_hold", {"section": sid, "item": it})
                break
            marks.append({"item": it, "mark": ans})
            s.record("meaning_mark", {"section": sid, "item": it, "answer": ans})
        else:
            missing = input(f"\n[{sid}] What does the draft NOT contain that it must? "
                            "(jargon, concepts, arguments; 'none') > ").strip()
            s.record("meaning_added", {"section": sid, "added": missing})
            b.record_gate(sid, "G2", {"items": len(marks), "verdict": "LOCKED"})
            b.set_status(sid, "MEANING_LOCKED")
            print(f"{sid}: MEANING_LOCKED")


def holds_block(b: Board, s: Sitting):
    """Block 2: adjudicate grounding holds — cut / replace source / own claim."""
    ledger_p = s.state / "grounding-ledger.json"
    if not ledger_p.exists():
        return
    ledger = json.loads(ledger_p.read_text())
    holds = {c: e for c, e in ledger.items() if not e.get("resolves")}
    if not holds:
        return
    print(f"\n=== HOLDS BLOCK ({len(holds)}) — candidates in state/holds-report.md ===")
    for cite, e in holds.items():
        if not s.check_time():
            return
        ans = input(f"{cite} (in {', '.join(e['sections'])}): "
                    "cut / source=<file> / own > ").strip()
        if ans.startswith("source="):
            e["resolves"] = True
            e["source"] = ans[7:]
        elif ans == "own":
            e["resolves"] = True
            e["source"] = "AUTHOR_CLAIM"
        else:
            e["adjudication"] = "cut"
        ledger_p.write_text(json.dumps(ledger, indent=1))  # I8
        s.record("hold_adjudicated", {"citation": cite, "answer": ans})


def approval_block(b: Board, s: Sitting, arc: int):
    """G5 for arc N. Commit-before-reveal: author ranks before seeing the
    machine ranking. Side-by-side candidates."""
    secs = [sid for sid, v in b.data.items()
            if v["arc"] == arc and v["status"] == "REVIEW_READY"]
    if not secs:
        return
    print(f"\n=== APPROVAL BLOCK — arc {arc} ===")
    tb_v = 1  # termbase version bump is manual for now
    for sid in secs:
        if not s.maybe_seeded_defect() or not s.check_time():
            return
        s.maybe_diversion()
        d = b.section_dir(sid)
        cands = sorted(d.glob("candidates.v*/cand-*.md"))
        cands = [c for c in cands if not c.name.endswith(".guards.json")]
        print(f"\n[{sid}] candidates (read side by side):")
        for c in cands:
            print(f"  {c}")
        yours = input("Your pick, BEFORE seeing the machine ranking "
                      "(commit-before-reveal) > ").strip()
        machine = json.loads((d / "grades.json").read_text()).get("ranking", []) \
            if (d / "grades.json").exists() else []
        print(f"machine ranking was: {machine}")
        s.record("approval_pick", {"section": sid, "author": yours,
                                   "machine": machine})
        ans = input("approve / complaint <span text> / meaning-wrong / write > ").strip()
        if ans == "approve":
            pick = d / yours if (d / yours).exists() else (cands[0] if cands else None)
            if pick:
                (d / "approved.md").write_text(pick.read_text())
            approve(b, sid, tb_v, learnings_hash(s.state))
            print(f"{sid}: APPROVED")
        elif ans.startswith("complaint"):
            v = b.data[sid]["skeleton_v"]
            (d / f"complaints.v{v}.md").write_text(ans[len("complaint"):].strip())
            b.set_status(sid, "GROUNDED")  # regen from skeleton; never edit a draft
            b.bump_retry(sid)
        elif ans == "meaning-wrong":
            b.set_status(sid, "TLDR_READY")
            b.bump_reopen(sid, "meaning")
        else:
            b.set_status(sid, "AUTHOR_WRITING")
        s.record("approval_outcome", {"section": sid, "outcome": ans})


def afc_pairs(state: Path, n: int, s: Sitting):
    """2-AFC identification: which of the two is YOUR unassisted writing?
    Cumulative log; catch trials (both yours) included. Never a preference question."""
    pool_own = sorted((state / "anchors").glob("*.md"))
    pool_meld = sorted((state.parent / "sections").glob("*/approved.md"))
    if not pool_own or not pool_meld:
        return
    print(f"\n=== 2-AFC calibration ({n} pairs) ===")
    for i in range(n):
        if not s.check_time():
            return
        catch = random.random() < 0.2
        a = random.choice(pool_own).read_text()[:400]
        b_ = a if catch else random.choice(pool_meld).read_text()[:400]
        first_is_own = random.random() < 0.5
        x, y = (a, b_) if first_is_own else (b_, a)
        print(f"\nPair {i + 1} — which is your unassisted writing?\nA: {x}\nB: {y}")
        ans = input("A/B > ").strip().upper()
        correct = catch or (ans == ("A" if first_is_own else "B"))
        s.record("afc", {"catch": catch, "correct": correct})
    rows = [json.loads(l) for l in (state / "sittings.jsonl").read_text().splitlines()
            if '"afc"' in l]
    real = [r for r in rows if not r["catch"]]
    if real:
        rate = sum(r["correct"] for r in real) / len(real)
        print(f"cumulative identification rate: {rate:.0%} over {len(real)} pairs")
        if rate > 0.75:
            print("NOTE: high identification + happy approvals = the Baumler "
                  "condition. Lower the dial / adjust anchors; do not celebrate.")


def arc_close(b: Board, s: Sitting, arc: int):
    """G6: all approved -> batch-ratify proposed learnings (one keystroke each)."""
    secs = [sid for sid, v in b.data.items() if v["arc"] == arc]
    if not secs or not all(b.data[x]["status"] == "APPROVED" for x in secs):
        return
    print(f"\n=== ARC {arc} CLOSE — learnings ratification (batch) ===")
    from learnings import ratify, veto
    for lid, l in load_all(s.state).items():
        if l["status"] == "proposed":
            k = input(f"{lid}: {l['behavior']} (scope {l['scope']}; over-application: "
                      f"{l['over_application']}) — y/n > ").strip().lower()
            (ratify if k == "y" else veto)(s.state, lid)
    for sid in secs:
        b.record_gate(sid, "G6", {"arc": arc, "verdict": "CLOSED"})


def run(state: Path, arc: int):
    b = Board(state)
    b.assert_wip()
    print(b.show())
    s = Sitting(state)
    meaning_block(b, s, arc + 1)   # fresh attention first
    holds_block(b, s)
    approval_block(b, s, arc)
    afc_pairs(state, 4, s)
    arc_close(b, s, arc)
    # end on finished work, open the next loop: next arc's first skeleton unmarked
    nxt = [sid for sid, v in b.data.items()
           if v["arc"] == arc + 1 and v["status"] == "TLDR_READY"]
    if nxt:
        print(f"\nOpen loop for next sitting: {nxt[0]} skeleton is ready, unmarked.")
    print(f"\nSitting: {s.elapsed_min():.0f} min, {s.items} items, "
          f"seeds {s.seed_hits} hit / {s.seed_misses} miss.")


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        st = Path(td) / "state"
        b = Board(st)
        s = Sitting(st)
        # time bounds
        assert s.check_time()
        s.t0 -= 91 * 60
        assert not s.check_time()
        # sitting log commits per item (I8)
        s2 = Sitting(st)
        s2.record("meaning_mark", {"section": "s1", "item": "x", "answer": "verified"})
        assert (st / "sittings.jsonl").exists()
        assert json.loads((st / "sittings.jsonl").read_text().splitlines()[0])[
            "kind"] == "meaning_mark"
        # seeded-defect cadence: fires only every SEED_EVERY-th item
        s3 = Sitting(st)
        s3.seeds = [Path(td) / "seed.json"]
        s3.items = SEED_EVERY - 2
        assert s3.maybe_seeded_defect()  # not due -> no prompt, returns True
        # arc close requires all approved
        b.add_section("s1", 1)
        arc_close(b, s2, 1)  # not approved -> no-op, must not raise
        assert not any(g["gate"] == "G6" for g in b.data["s1"]["gates"])
    print("selftest ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="state")
    ap.add_argument("--arc", type=int, default=1)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    else:
        run(Path(a.state), a.arc)
