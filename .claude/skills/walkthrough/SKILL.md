---
name: walkthrough
description: Run the OwnVoice paper walkthrough — arc-pipelined HITL loop over a templated paper. Use when the user says /walkthrough, "start the walkthrough", "run a tock", "run a tick", "arc status", or asks to advance a paper through the pipeline.
---

# Paper walkthrough conductor

You are the tick/tock conductor. The tools own all state; you never hold state in
conversation. Spec: DESIGN.md §4 (normative); invariants I1–I8 are asserted in code
(`tools/board.py`) — if an `Invariant` fires, report it and stop; never work around it.

## Setup (once per paper)

1. Draw the arc map with the author: 3–5 consecutive template sections per arc, one
   argument thread each. Write it into the template: every `## section` block must
   carry `- **id:**`, `- **type:**` (argumentative / procedural / administrative /
   boilerplate) and `- **arc:** N` lines. Routing is by template type, NEVER by a score.
2. `python3 tools/setup_paper.py --intake intake/<paper> --work runs/<paper> --anchors <dir of anchor*.md>`
   — runs G0 (refuses on a blocking gap) and G1, registers every section with its
   type and arc, writes `runs/<paper>/sections/<sid>/{original,template,grounded-sources}.md`
   and `runs/<paper>/state/{board.json,grounding-ledger.json,holds-report.md,anchors/}`.
   Re-runnable. Every later command takes `--state runs/<paper>/state`.
3. Anchors: paragraphs of the author's own prose (pool: `intake/<paper>/author-corpus/`).
   Chris's method prefers one of similar form and topic per draft paragraph.
4. Author conventions → `state/termbase.yml`, then
   `python3 tools/learnings.py --state runs/<paper>/state vale`.

## The loop (repeat per arc)

- **Tock (machine, between sittings):** `tools/py tools/tock.py --state runs/<paper>/state`
  — TL;DR extraction for NEW sections; the full pipeline for MEANING_LOCKED ones
  (ground → draft → guard → polisher sweep → guard candidates → grade → rank →
  REVIEW_READY). Idempotent; crash = re-run. `tools/py` is the venv python with the
  NixOS library paths set, so factwash and MiniCheck are active in the guard.
- **Tick (human sitting, ≤90 min):** `python3 tools/tick.py --state runs/<paper>/state --arc N`
  — board, meaning block for arc N+1, holds block, approval block for arc N,
  2-AFC calibration, arc close with batch learnings ratification. Interactive:
  the author runs it in a terminal; you prepare and read state, you do not answer
  for the author. Two of its blocks are *about* the author — which candidate sounds
  like them, and which passage is their own writing — so answering for them does not
  just skip a step, it fabricates the measurement.
- Light-path sections (administrative/boilerplate/procedural by template type) are not
  regenerated; they appear in the same approval block for a read and a sign-off, and
  an arc cannot close until every section in it is APPROVED.
- After each tick, run the next tock. WIP stays ≤ 2 arcs (I4 will fire otherwise);
  NEW, SKIM and APPROVED sections are not "in flight".

## What the guard gates, and what it only reports

`tools/guard.py` is a detector: everything it finds is a failure. `tock.MEANING_GATE`
is the ONLY place a finding is demoted, and it gates on omission and fabrication —
MISSING claim, MISSING/INVENTED citation, INVENTED number, and a cut citation that
reappeared in the prose. Everything else (dropped hedges and attributions, reversed
polarity, added boosters, unalignable sentences, entailment) is reported as a warning,
because those classes were measured on sentence-for-sentence rewrites and drafting
from a skeleton legitimately restructures sentences.

That demotion is only honest because the author sees the warnings: `tick.py` prints
the draft's guard report and every candidate's, with each cue and the claim it belongs
to. If you ever find those warnings are not reaching the author, the demotion is
unjustified and the gate must tighten — do not leave it demoted and silent.

## Paper pass (G7)

When every arc is closed: run
`python3 tools/learnings.py --state runs/<paper>/state scan`, drain
`state/stale.json` — termbase matches auto-apply at dial 1–3; construction-rule
matches re-meld ONLY the matched paragraphs from the approved skeleton; every retouch
of approved prose is presented to the author as a diff (`board.modify_approved`
refuses anything else — I6).

## Hard rules (from BUILD.md frozen decisions)

- Claude never polishes. The humanizing polisher runs via OpenRouter on the frozen
  `tools/meld-v1.json` — qwen/qwen3.7-max, arm `humanizing-polisher`, temperature 0.2,
  thinking off, one paragraph at a time. Headings, lists, tables, boxes and captions
  pass through untouched.
- No generator input ever contains a prior draft (I1). `assert_no_prior_draft` only
  compares whole paragraphs, so single borrowed sentences slip past it: the real
  enforcement is in what `tock.guard_notes` is allowed to quote and in
  `setup_paper.grounded_sources` never writing the author's own citing sentences into
  what the drafter reads. Both are pinned by tests; do not relax either.
- Detector/voice scores are diagnostics: they order candidates, they never gate,
  never route, never appear as targets.
- Author-written spans: mechanics lock applies; dial per §8; the author's original is
  always preserved and every change shown as a diff against it.

## When something is wrong in a real session

This project is past staged testing: it is adjusted in use. Fix the thing, add the test
that would have caught it, and add a dated line to the **Adjustment log** in BUILD.md
saying what prompted the change. A fix that loosens a gate needs the measurement re-run
(`tools/py tools/bench_guard.py --witness --entailment minicheck`) before it counts —
the 30-seed library and steps/T1*.md are what "the guard works" means here.
