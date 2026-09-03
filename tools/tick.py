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
from board import Board, Invariant, approve  # noqa: E402
from learnings import learnings_hash, load_all  # noqa: E402

BLOCK_MIN, SITTING_MIN = 50, 90
SEED_EVERY = 12  # ~1-in-10–15 items
MEANING_QUESTIONS = {  # item-specific — never a bare three-button tick
    "thesis": "Verified against which source, or amended to say what?",
    "point": "Where is this stated in the sources (or is it your own claim)?",
    "jargon": "Are these the exact terms you use? Correct any that are not.",
    "figure": "Do these figures/tables exist and show what the skeleton claims?",
    "requirement": "Does the section meet these template requirements? How?",
}
# skeleton heading -> (question key, one question PER item vs one for the whole list)
SKELETON_SECTIONS = {
    "thesis": ("thesis", True),
    "main points": ("point", True),
    "jargon": ("jargon", False),
    "figures": ("figure", False),
    "template requirements": ("requirement", False),
}


def skeleton_items(text: str) -> list[tuple[str, str, bool]]:
    """(question_key, text, per_item) for the parts of a skeleton the author marks.

    Only the meaning sections produce items. "Source claims NOT covered by the draft"
    is a note TO the author, not something to mark, and the jargon/figure/requirement
    lists are asked once each rather than line by line. Before this, every non-header
    line in the skeleton counted as an item — 41 questions for a 10-claim section,
    which blows the 50-minute block cap before the section is finished (2026-09-01)."""
    out, key, per_item, bucket = [], None, None, []

    def flush():
        if key and not per_item and bucket:
            out.append((key, "\n".join(bucket), False))
        bucket.clear()

    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            flush()
            head = s.lstrip("# ").lower()
            key = per_item = None
            for name, (k, p) in SKELETON_SECTIONS.items():
                if head.startswith(name) or name in head:
                    key, per_item = k, p
                    break
            continue
        if not s or key is None:
            continue
        s = re.sub(r"^(\d+[.)]|[-*•])\s*", "", s).strip()
        if not s:
            continue
        if per_item:
            out.append((key, s, True))
        else:
            bucket.append(s)
    flush()
    return out


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
        items = skeleton_items(sk.read_text())
        marks = []
        for qkey, it, _per_item in items:
            if not s.maybe_seeded_defect() or not s.check_time():
                return
            q = MEANING_QUESTIONS[qkey]
            print(f"\n[{sid}] {it}")
            ans = input(f"  {q}\n  verified/amended/added + answer (or 'hold') > ").strip()
            if ans.lower() == "hold":
                b.set_status(sid, "HELD_MEANING")
                s.record("meaning_hold", {"section": sid, "item": it})
                break
            marks.append({"item": it, "mark": ans})
            s.record("meaning_mark", {"section": sid, "kind": qkey, "item": it,
                                      "answer": ans})
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
    # A citation the author CUT stays resolves=false forever — that is what "cut"
    # means. Filtering on resolves alone re-asked about it at the start of every
    # later sitting, and the answer went to the previous prompt's question
    # (2026-09-02). An adjudicated hold is a settled hold.
    holds = {c: e for c, e in ledger.items()
             if not e.get("resolves") and not e.get("adjudication")}
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


def guard_report_lines(report: Path, limit: int = 10) -> list[str]:
    """What the meaning guard found, printed for the author at G5.

    tock.MEANING_GATE demotes every class except omission and fabrication to a
    warning, and the justification written into the code for that demotion is that
    these reach the author here. Until now the sitting printed no guard findings at
    all, so the demoted findings reached nobody and the justification was false — the
    hedge drops, attribution drops and polarity flips the research says LLM rewriting
    introduces were being recorded to disk and never read (2026-09-01)."""
    if not report.exists():
        return ["      (no guard report on disk)"]
    rep = json.loads(report.read_text())
    shown = [f for f in rep["findings"] if f["severity"] in ("fail", "warn")]
    if not shown:
        return ["      guard: clean"]
    counts = {}
    for f in shown:
        k = f"{f['type']} {f.get('property', '')}".strip()
        counts[k] = counts.get(k, 0) + 1
    out = ["      guard: " + ", ".join(f"{k} x{n}" for k, n in
                                      sorted(counts.items(), key=lambda kv: -kv[1]))]
    detail = [f for f in shown if f.get("cue") or f.get("token")]
    for f in detail[:limit]:
        cue = f.get("cue") or f.get("token")
        where = f.get("claim") or f.get("sentence") or ""
        out.append(f"        - {f['type']} {f.get('property', '')}: '{cue}'"
                   + (f"   in: {' '.join(where.split())[:90]}" if where else ""))
    if len(detail) > limit:
        out.append(f"        ... {len(detail) - limit} more in {report}")
    return out


def latest_candidates(d: Path) -> tuple[Path | None, dict]:
    """(candidates dir, {stem: path}) for the CURRENT draft version only.

    Globbing every candidates.v* showed superseded generations side by side with no
    label, and the old pick resolution (`d / typed`) could never match a candidate —
    it silently fell through to candidates.v1/cand-1.md, so the approved file was a
    stale candidate the author had not chosen (2026-09-01)."""
    vers = [int(m.group(1)) for p in d.glob("candidates.v*")
            if (m := re.fullmatch(r"candidates\.v(\d+)", p.name))]
    if not vers:
        return None, {}
    cand_dir = d / f"candidates.v{max(vers)}"
    return cand_dir, {c.stem: c for c in sorted(cand_dir.glob("cand-*.md"))}


def approval_block(b: Board, s: Sitting, arc: int):
    """G5 for arc N. Commit-before-reveal: author ranks before seeing the
    machine ranking. Side-by-side candidates."""
    secs = [sid for sid, v in b.data.items()
            if v["arc"] == arc and v["status"] in ("REVIEW_READY", "SKIM")]
    if not secs:
        return
    print(f"\n=== APPROVAL BLOCK — arc {arc} ===")
    tb_v = 1  # termbase version bump is manual for now
    for sid in secs:
        if not s.maybe_seeded_defect() or not s.check_time():
            return
        s.maybe_diversion()
        d = b.section_dir(sid)
        if b.data[sid]["status"] == "SKIM":
            # Light path (administrative/boilerplate/procedural, routed by template
            # type): nothing was regenerated, so the author reads the original and
            # signs it off. Without this the section never left SKIM and arc_close —
            # which requires every section APPROVED — could never fire (2026-09-02).
            orig = d / "original.md"
            print(f"\n[{sid}] LIGHT PATH ({b.data[sid]['type']}) — not regenerated.")
            print(f"  read: {orig}")
            ans = input("approve / write > ").strip()
            if ans == "approve":
                if orig.exists():
                    (d / "approved.md").write_text(orig.read_text())
                approve(b, sid, tb_v, learnings_hash(s.state))
                print(f"{sid}: APPROVED (light path)")
            else:
                b.set_status(sid, "AUTHOR_WRITING")
            s.record("approval_outcome", {"section": sid, "outcome": ans, "path": "light"})
            continue
        cand_dir, picks = latest_candidates(d)
        if not picks:
            print(f"\n[{sid}] no candidates on disk — run a tock first; skipping.")
            continue
        dv = cand_dir.name.split(".v")[-1]
        draft_guard = d / f"guards.v{dv}.json"
        print(f"\n[{sid}] draft (skeleton -> prose):")
        for line in guard_report_lines(draft_guard):
            print(line)
        print(f"\n[{sid}] candidates from {cand_dir.name} (read side by side):")
        for stem, c in sorted(picks.items()):
            print(f"  {stem:8} {c}")
            for line in guard_report_lines(c.with_name(c.stem + ".guards.json")):
                print(line)
        while True:  # never silently substitute the author's pick
            yours = input(f"Your pick {sorted(picks)}, BEFORE seeing the machine "
                          "ranking (commit-before-reveal) > ").strip()
            if yours in picks:
                break
            print(f"  '{yours}' is not one of {sorted(picks)}.")
        machine = json.loads((d / "grades.json").read_text()).get("ranking", []) \
            if (d / "grades.json").exists() else []
        print(f"machine ranking was: {machine}")
        s.record("approval_pick", {"section": sid, "author": yours,
                                   "machine": machine, "agreed": bool(machine) and machine[0] == yours})
        ans = input("approve / complaint <span text> / meaning-wrong / write > ").strip()
        try:
            if ans == "approve":
                (d / "approved.md").write_text(picks[yours].read_text())
                approve(b, sid, tb_v, learnings_hash(s.state))
                print(f"{sid}: APPROVED ({yours})")
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
        except Invariant as e:
            # a cap reached here is a normal outcome (the section goes to the author),
            # not a reason to lose the rest of the sitting
            print(f"{sid}: {e}")
        s.record("approval_outcome", {"section": sid, "outcome": ans})


def afc_pairs(state: Path, n: int, s: Sitting):
    """2-AFC identification: which of the two is YOUR unassisted writing?
    Cumulative log; catch trials (both yours) included. Never a preference question."""
    def sample(p: Path) -> str:
        """Strip the provenance comment before showing the text. anchor*.md opens with
        '<!-- written prose, 2019-08, ... -->', which hands the author the answer and
        makes the whole identification meaningless (2026-09-01)."""
        return re.sub(r"<!--.*?-->", "", p.read_text(), flags=re.S).strip()[:400]

    pool_own = sorted((state / "anchors").glob("*.md"))
    # before anything is approved (the first sitting), calibrate against the ranked
    # candidates instead of skipping calibration entirely
    pool_meld = sorted((state.parent / "sections").glob("*/approved.md")) or \
        sorted((state.parent / "sections").glob("*/candidates.v*/cand-*.md"))
    if not pool_own or not pool_meld:
        return
    print(f"\n=== 2-AFC calibration ({n} pairs) ===")
    for i in range(n):
        if not s.check_time():
            return
        # a catch trial is two DIFFERENT samples of the author's own writing; showing
        # the same text twice is a tell, not a control
        catch = random.random() < 0.2 and len(pool_own) > 1
        a_file = random.choice(pool_own)
        a = sample(a_file)
        b_ = sample(random.choice([p for p in pool_own if p != a_file])) if catch \
            else sample(random.choice(pool_meld))
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
    try:
        meaning_block(b, s, arc + 1)   # fresh attention first
        holds_block(b, s)
        approval_block(b, s, arc)
        afc_pairs(state, 4, s)
        arc_close(b, s, arc)
    except EOFError:
        # ctrl-D, or a piped run that ran out of input. Every answer was written to
        # disk as it was given (I8), so ending here loses nothing already answered.
        print("\n== sitting ended early (no more input). Answers so far are saved. ==")
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

        # the meaning block marks CLAIMS, not every line of the skeleton
        sk = ("## Thesis/topic sentences\n* The retrofit changed measured conditions.\n"
              "\n## Main points (in order)\n"
              "1. **Limit one:** The study covers a single climate zone.\n"
              "2. **Limit two:** The follow-up window is two weeks per season.\n"
              "\n## Jargon and named concepts\n* Running mean window\n* Occupant votes\n"
              "\n## Figures/tables\n* None.\n"
              "\n## Template requirements\n* States each limit: yes.\n"
              "\n## Source claims NOT covered by the draft\n"
              "* Author note: resolve Whitfield before drafting.\n")
        items = skeleton_items(sk)
        kinds = [k for k, _, _ in items]
        assert kinds == ["thesis", "point", "point", "jargon", "figure", "requirement"], kinds
        assert sum(1 for _, _, per in items if per) == 3          # thesis + 2 points
        assert all("Author note" not in t for _, t, _ in items)   # notes are not items
        assert len(items) < len([l for l in sk.splitlines()
                                 if l.strip() and not l.startswith("#")])
        assert "Occupant votes" in [t for k, t, _ in items if k == "jargon"][0]

        # the author's pick resolves to the CURRENT version and is never substituted
        d = b.section_dir("s1")
        for v, names in ((1, ["cand-1", "cand-2"]), (3, ["cand-1", "cand-2"])):
            (d / f"candidates.v{v}").mkdir(parents=True, exist_ok=True)
            for nm in names:
                (d / f"candidates.v{v}" / f"{nm}.md").write_text(f"v{v} {nm} prose")
            (d / f"candidates.v{v}" / "cand-1.guards.json").write_text("{}")
        cand_dir, picks = latest_candidates(d)
        assert cand_dir.name == "candidates.v3", cand_dir
        assert sorted(picks) == ["cand-1", "cand-2"], picks
        assert picks["cand-2"].read_text() == "v3 cand-2 prose"   # not v1, not cand-1
        assert latest_candidates(Path(td) / "nothing") == (None, {})

        # the demoted findings MUST be visible at G5 — that is what justifies demoting
        rep = {"findings": [
            {"type": "DROPPED", "property": "hedge", "cue": "may", "severity": "warn",
             "claim": "The retrofit may reduce discomfort."},
            {"type": "REVERSED", "property": "polarity", "severity": "warn",
             "claim": "The effect was not significant."},
            {"type": "NOT_CHECKED", "property": "entailment", "severity": "info"}]}
        (d / "cand-1.guards.json").write_text(json.dumps(rep))
        lines = guard_report_lines(d / "cand-1.guards.json")
        blob = "\n".join(lines)
        assert "DROPPED hedge" in blob and "REVERSED polarity" in blob, blob
        assert "'may'" in blob and "may reduce discomfort" in blob, blob
        assert "NOT_CHECKED" not in blob                      # info is not a warning
        assert guard_report_lines(d / "absent.json")[0].strip().startswith("(no guard")
        (d / "clean.guards.json").write_text(json.dumps({"findings": []}))
        assert "clean" in guard_report_lines(d / "clean.guards.json")[0]

        # a catch trial is two different own-samples, and provenance never leaks
        anch = st / "anchors"; anch.mkdir(parents=True, exist_ok=True)
        (anch / "anchor1.md").write_text("<!-- written prose, 2019 -->\n\nMy own words one.")
        (anch / "anchor2.md").write_text("<!-- spoken transcript -->\n\nMy own words two.")
        shown = re.sub(r"<!--.*?-->", "", (anch / "anchor1.md").read_text(),
                       flags=re.S).strip()[:400]
        assert shown == "My own words one." and "<!--" not in shown
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
