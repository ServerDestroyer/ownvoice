---
name: walkthrough
description: Run the OwnVoice paper walkthrough — arc-pipelined HITL loop over a templated paper. Use when the user says /walkthrough, "start the walkthrough", "run a tock", "run a tick", "arc status", or asks to advance a paper through the pipeline.
---

# Paper walkthrough conductor

You are the tick/tock conductor. The tools own all state; you never hold state in
conversation. Spec: DESIGN.md §4 (normative); invariants I1–I8 are asserted in code
(`tools/board.py`) — if an `Invariant` fires, report it and stop; never work around it.

## Setup (once per paper)

1. `python3 tools/intake_check.py intake/<paper>` — G0 must pass.
2. `python3 tools/prepass.py --paper <paper.md> --sources <sources/> --state state`
   — G1 grounding prepass; holds go to `state/holds-report.md`.
3. Draw the arc map with the author: 3–5 consecutive template sections per arc, one
   argument thread each → `state/arcs.md`. Register sections:
   `python3 -c` with `tools/board.py:Board.add_section(sid, arc, type)` — sections
   whose template type is administrative/boilerplate/procedural get that type (light
   path; routing is by template type, NEVER by any score).
4. Put 2–4 author anchor paragraphs in `state/anchors/` (not topic-matched).
5. Author conventions → `state/termbase.yml`, then
   `python3 tools/learnings.py --state state vale`.

## The loop (repeat per arc)

- **Tock (machine, between sittings):** `python3 tools/tock.py --state state`
  — TL;DR extraction for NEW sections; the full pipeline for MEANING_LOCKED ones
  (ground → draft → guard → meld sweep → guard candidates → grade → rank →
  REVIEW_READY). Idempotent; crash = re-run. Run it with the venv python
  (`.venv/bin/python`) so factwash is active in the guard.
- **Tick (human sitting, ≤90 min):** `python3 tools/tick.py --state state --arc N`
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
