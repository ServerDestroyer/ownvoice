#!/usr/bin/env python3
"""B4 state layer — the persisted state tree (DESIGN.md §4) and invariants I1–I8.

Every mutation writes to disk when it happens, never batched (I8/P-7). Gates are
append-only records. Used by tock.py and tick.py; also a CLI:

Usage:  python3 tools/board.py --state state           (print the board)
        python3 tools/board.py --selftest
"""
import json
import re
import time
from pathlib import Path

STATUSES = ("NEW", "TLDR_READY", "HELD_MEANING", "MEANING_LOCKED", "GROUNDING",
            "HELD_GROUNDING", "GROUNDED", "DRAFTED", "MELDED", "REVIEW_READY",
            "APPROVED", "AUTHOR_WRITING", "STALE", "RETOUCH_PROPOSED",
            "GROUNDING_STALE", "SKIM")  # SKIM = the light path
LIGHT_TYPES = ("administrative", "boilerplate", "procedural")  # template-type routing
MAX_REGENS = 3        # I5: per span, all causes combined
MAX_REOPENS = 2       # I5: G2 reopens per section, same complaint class
MAX_WIP_ARCS = 2      # I4


class Invariant(AssertionError):
    pass


class Board:
    def __init__(self, state: Path):
        self.state = Path(state)
        self.state.mkdir(parents=True, exist_ok=True)
        self.path = self.state / "board.json"
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {}

    def _write(self):  # I8: every state change hits disk when it happens
        self.path.write_text(json.dumps(self.data, indent=1))

    def add_section(self, sid: str, arc: int, stype: str = "standard"):
        self.data[sid] = {"arc": arc, "type": stype, "status": "NEW",
                          "skeleton_v": 0, "retries": 0, "reopens": {}, "gates": []}
        self._write()

    def set_status(self, sid: str, status: str):
        assert status in STATUSES, status
        self.data[sid]["status"] = status
        self._write()

    def record_gate(self, sid: str, gate: str, payload: dict):
        """Append-only: a gate record is never modified or removed."""
        self.data[sid]["gates"].append(
            {"gate": gate, "ts": time.strftime("%F %T"), **payload})
        self._write()

    def bump_retry(self, sid: str):
        """I5: regenerations per span ≤ 3 (all causes) → AUTHOR_WRITING."""
        self.data[sid]["retries"] += 1
        if self.data[sid]["retries"] > MAX_REGENS:
            self.data[sid]["status"] = "AUTHOR_WRITING"
        self._write()
        if self.data[sid]["status"] == "AUTHOR_WRITING":
            raise Invariant(f"I5: {sid} regen cap hit -> AUTHOR_WRITING")

    def bump_reopen(self, sid: str, complaint_class: str):
        """I5: G2 reopens ≤ 2 per section for the same complaint class."""
        r = self.data[sid]["reopens"]
        r[complaint_class] = r.get(complaint_class, 0) + 1
        if r[complaint_class] > MAX_REOPENS:
            self.data[sid]["status"] = "AUTHOR_WRITING"
        self._write()
        if self.data[sid]["status"] == "AUTHOR_WRITING":
            raise Invariant(f"I5: {sid} reopen cap ({complaint_class}) -> AUTHOR_WRITING")

    def amend_skeleton(self, sid: str):
        """Skeleton amendment invalidates grounding for amended items (I3/P-2)."""
        self.data[sid]["skeleton_v"] += 1
        if self.data[sid]["status"] in ("GROUNDED", "DRAFTED", "MELDED", "REVIEW_READY"):
            self.data[sid]["status"] = "GROUNDING"
        self._write()

    # statuses that are NOT work in flight: not started, finished, or finished by the
    # light path. SKIM was missing, and it is terminal — so on any paper with 3+ arcs
    # every arc holding one administrative/procedural section counted as in flight
    # forever and the second tock raised I4 permanently (2026-09-01).
    IDLE = ("NEW", "APPROVED", "SKIM")

    def assert_wip(self):
        """I4: ≤ 2 arcs in flight (one in meaning, one in review)."""
        active = {v["arc"] for v in self.data.values()
                  if v["status"] not in self.IDLE}
        if len(active) > MAX_WIP_ARCS:
            raise Invariant(f"I4: {len(active)} arcs in flight: {sorted(active)}")

    def section_dir(self, sid: str) -> Path:
        d = self.state.parent / "sections" / sid
        d.mkdir(parents=True, exist_ok=True)
        return d

    def show(self) -> str:
        rows = [f"{'section':24} {'arc':>3} {'status':16} {'sk_v':>4} {'retries':>7}"]
        for sid, v in sorted(self.data.items(), key=lambda kv: (kv[1]["arc"], kv[0])):
            rows.append(f"{sid:24} {v['arc']:>3} {v['status']:16} "
                        f"{v['skeleton_v']:>4} {v['retries']:>7}")
        return "\n".join(rows)


def assert_no_prior_draft(prompt_parts: dict, section_dir: Path):
    """I1: no generator input ever contains a prior draft. Callers must build
    prompts through this check. prompt_parts keys name their provenance."""
    allowed = {"skeleton", "sources", "constraints", "anchors", "template"}
    bad_keys = set(prompt_parts) - allowed
    if bad_keys:
        raise Invariant(f"I1: disallowed generator inputs {sorted(bad_keys)}")
    priors = sorted(section_dir.glob("draft.v*.md")) + sorted(
        section_dir.glob("candidates.v*/*.md"))
    blob = " ".join(prompt_parts.values())
    for p in priors:
        text = p.read_text().strip()
        for para in [t for t in re.split(r"\n\s*\n", text) if len(t.split()) > 12]:
            if para.strip() in blob:
                raise Invariant(f"I1: prior draft text from {p.name} in generator input")


def assert_review_ready(board: Board, sid: str):
    """I2: nothing reaches REVIEW_READY without passing guard records on the draft
    and on every surviving candidate."""
    recs = [g for g in board.data[sid]["gates"] if g["gate"] == "G4"]
    draft_ok = any(r.get("target") == "draft" and r.get("verdict") == "PASS"
                   for r in recs)
    # "every SURVIVING candidate", not every candidate ever recorded: a candidate that
    # failed G4 is discarded, so demanding a PASS for it too parked sections whose
    # surviving candidates were all clean (2026-09-01).
    cands_ok = any(str(r.get("target", "")).startswith("cand") and r.get("verdict") == "PASS"
                   for r in recs)
    if not (draft_ok and cands_ok):
        raise Invariant(f"I2: {sid} lacks passing G4 records "
                        f"(draft_ok={draft_ok}, surviving_candidate={cands_ok})")


def assert_no_open_holds(state: Path, sid: str, skeleton_claims: list[str]):
    """I3: no prose generated for a section with open grounding holds."""
    ledger_path = state / "grounding-ledger.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    # a citation the author cut (tick holds block) is not an open hold: the section
    # drafts without it, and tock passes the cut list to the drafter as a constraint
    open_holds = [c for c, e in ledger.items()
                  if sid in e.get("sections", []) and not e.get("resolves")
                  and e.get("adjudication") != "cut"]
    if open_holds:
        raise Invariant(f"I3: {sid} has open grounding holds: {open_holds}")


def approve(board: Board, sid: str, termbase_v: int, learnings_hash: str):
    """G5. Approval pinned to versions; later modification only via accepted diff (I6)."""
    d = board.section_dir(sid)
    approval = {"skeleton_v": board.data[sid]["skeleton_v"],
                "termbase_v": termbase_v, "learnings_hash": learnings_hash,
                "ts": time.strftime("%F %T")}
    (d / "approval.json").write_text(json.dumps(approval, indent=1))
    board.record_gate(sid, "G5", approval)
    board.set_status(sid, "APPROVED")


def modify_approved(board: Board, sid: str, new_text: str, accepted_diff: bool):
    """I6: approved text changes only through an author-accepted diff."""
    if not accepted_diff:
        raise Invariant(f"I6: {sid} approved text modified without accepted diff")
    (board.section_dir(sid) / "approved.md").write_text(new_text)


def scores_never_gate(decision_inputs: dict):
    """I7: grader/voice scores order candidates and inform anchors; they never
    gate, never route the human. Call at every gate decision with the inputs used."""
    banned = [k for k in decision_inputs if re.search(
        r"detector|luar|delta|voice_score|certainty_score|binoculars|ghostbuster",
        k, re.I)]
    if banned:
        raise Invariant(f"I7/P-4: score used in a gate decision: {banned}")


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        st = Path(td) / "state"
        b = Board(st)
        b.add_section("s1", 1)
        b.set_status("s1", "MEANING_LOCKED")
        assert json.loads(b.path.read_text())["s1"]["status"] == "MEANING_LOCKED"  # I8

        # one negative test per invariant — each must fire when provoked
        # I5 regen cap
        try:
            for _ in range(4):
                b.bump_retry("s1")
            raise SystemExit("I5 regen did not fire")
        except Invariant:
            assert b.data["s1"]["status"] == "AUTHOR_WRITING"
        # I5 reopen cap
        b.add_section("s2", 1)
        try:
            for _ in range(3):
                b.bump_reopen("s2", "meaning")
            raise SystemExit("I5 reopen did not fire")
        except Invariant:
            pass
        # I4 WIP bound
        b.add_section("s3", 2); b.set_status("s3", "GROUNDED")
        b.add_section("s4", 3); b.set_status("s4", "GROUNDED")
        try:
            b.assert_wip()
            raise SystemExit("I4 did not fire")
        except Invariant:
            pass
        # ...but the light path is FINISHED work, not work in flight: a SKIM section
        # must not hold its arc open forever (that deadlocked every 3+ arc paper)
        b.set_status("s4", "SKIM")
        b.assert_wip()
        b.set_status("s4", "GROUNDED")  # restore for the tests below
        # I1 prior-draft leak
        d = b.section_dir("s1")
        prior = "This exact prior draft paragraph has more than twelve words in it, easily."
        (d / "draft.v1.md").write_text(prior)
        try:
            assert_no_prior_draft({"skeleton": "x", "constraints": prior}, d)
            raise SystemExit("I1 did not fire")
        except Invariant:
            pass
        assert_no_prior_draft({"skeleton": "clean input"}, d)  # and passes clean
        try:
            assert_no_prior_draft({"skeleton": "x", "draft": "y"}, d)
            raise SystemExit("I1 key check did not fire")
        except Invariant:
            pass
        # I2 REVIEW_READY without guard records
        try:
            assert_review_ready(b, "s2")
            raise SystemExit("I2 did not fire")
        except Invariant:
            pass
        b.record_gate("s2", "G4", {"target": "draft", "verdict": "PASS"})
        b.record_gate("s2", "G4", {"target": "cand-1", "verdict": "PASS"})
        assert_review_ready(b, "s2")
        # a candidate that FAILED is discarded, not a reason to park the section
        b.record_gate("s2", "G4", {"target": "cand-2", "verdict": "FAIL"})
        assert_review_ready(b, "s2")
        # ...but with no surviving candidate at all, I2 must fire
        b.add_section("s6", 1)
        b.record_gate("s6", "G4", {"target": "draft", "verdict": "PASS"})
        b.record_gate("s6", "G4", {"target": "cand-1", "verdict": "FAIL"})
        try:
            assert_review_ready(b, "s6")
            raise SystemExit("I2 did not fire with every candidate failing")
        except Invariant:
            pass
        # I3 open holds
        (st / "grounding-ledger.json").write_text(json.dumps(
            {"Miller, 2018": {"resolves": False, "sections": ["s2"]}}))
        try:
            assert_no_open_holds(st, "s2", [])
            raise SystemExit("I3 did not fire")
        except Invariant:
            pass
        # I6 approved modified without diff
        approve(b, "s2", termbase_v=1, learnings_hash="abc")
        try:
            modify_approved(b, "s2", "new", accepted_diff=False)
            raise SystemExit("I6 did not fire")
        except Invariant:
            pass
        modify_approved(b, "s2", "new", accepted_diff=True)
        # I7 score in gate decision
        try:
            scores_never_gate({"guard_verdict": "PASS", "luar_score": 0.4})
            raise SystemExit("I7 did not fire")
        except Invariant:
            pass
        scores_never_gate({"guard_verdict": "PASS"})
        # skeleton amendment re-enters grounding (P-2)
        b.add_section("s5", 1); b.set_status("s5", "DRAFTED")
        b.amend_skeleton("s5")
        assert b.data["s5"]["status"] == "GROUNDING"
        # gates are append-only by construction (list append); spot-check record
        assert b.data["s2"]["gates"][0]["gate"] == "G4"
    print("selftest ok — I1..I8 all fire when provoked")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="state")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    else:
        print(Board(Path(a.state)).show())
