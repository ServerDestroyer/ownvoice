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
  for the author.
- After each tick, run the next tock. WIP stays ≤ 2 arcs (I4 will fire otherwise).

## Paper pass (G7)

When every arc is closed: run `python3 tools/learnings.py --state state scan`, drain
`state/stale.json` — termbase matches auto-apply at dial 1–3; construction-rule
matches re-meld ONLY the matched paragraphs from the approved skeleton; every retouch
of approved prose is presented to the author as a diff (`board.modify_approved`
refuses anything else — I6).

## Hard rules (from BUILD.md frozen decisions)

- Claude never melds; the meld runs via OpenRouter with the frozen `tools/meld-v1.json`
  config (until B1's test session freezes it, `.env` MELD_* is the interim config).
- No generator input ever contains a prior draft (I1 is asserted; do not bypass).
- Detector/voice scores are diagnostics: they order candidates, they never gate,
  never route, never appear as targets.
- Author-written spans: mechanics lock applies; dial per §8; the author's original is
  always preserved and every change shown as a diff against it.
