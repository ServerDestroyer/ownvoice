# Working on Stet with Claude Code

Stet is past staged construction. It is **adjusted in use**: when something is wrong in
a real session, fix it, add the test that would have caught it, and record it. The
board is [BUILD.md](BUILD.md); the normative spec is [DESIGN.md](DESIGN.md).

## Before changing anything

1. Read BUILD.md's **Frozen decisions**. They came from an adversarial design review
   (`reviews/`) and four research spikes (`spikes/`). Do not relitigate them in passing.
2. Read the **Adjustment log** at the bottom of BUILD.md. Several obvious-looking
   "improvements" have already been made, measured, and reverted — the log says why.

## The rules that are not style preferences

- **The guard is a detector; policy lives in one place.** Everything `tools/guard.py`
  finds is a failure. `tock.MEANING_GATE` is the only place a finding is demoted to a
  warning. Demoting inside the guard corrupts `tools/bench_guard.py`, which counts a
  detection by severity — that has happened, and it silently rewrote the seed library.
- **A demoted finding must still reach the author.** `tools/tick.py` prints the guard's
  findings at approval. If they ever stop reaching the author, the demotion is
  unjustified and the gate must tighten instead.
- **No generator input ever contains a prior draft** (I1). `assert_no_prior_draft` only
  compares whole paragraphs, so single borrowed sentences slip past it. The real
  enforcement is in what `tock.guard_notes` may quote, and in `setup_paper` never
  writing the author's own citing sentences into what the drafter reads.
- **Scores never gate and never route.** Detector and voice numbers order candidates.
  Routing is by declared template type. This is asserted in `board.scores_never_gate`.
- **The polisher never runs without anchors.** With no author exemplar it produces a
  paid rewrite toward no one. `setup_paper` refuses an empty anchor directory and
  `tock` refuses to polish without one.
- **Never answer for the author.** The sitting's meaning, approval and voice-calibration
  blocks are the human's judgement. Answering them does not skip a step, it fabricates
  the measurement.

## Verification that counts

Every tool has `--selftest`, and they run on the standard library alone:

```bash
for t in intake_check prepass setup_paper board meld guard tock tick learnings; do
  python3 tools/$t.py --selftest
done
python3 tools/gate_prepass.py
```

Any change that loosens a gate must additionally reproduce the guard benchmark before
it counts:

```bash
tools/py tools/bench_guard.py --witness --entailment minicheck
```

The four thresholded classes must still pass their floors, and `tools/seeds/` must come
back unchanged. `steps/T1-guard-benchmark.md` and `steps/T1b-witness-measurement.md`
record the numbers that must hold.

## Style

Standard-library-first Python in `tools/`, each file with a `--selftest`. Markdown
throughout; no spaces in filenames. Comments explain *why*, especially where a fix
reverses an earlier one. This is not detector evasion — detector scores are diagnostics,
never targets (DESIGN P-4).
