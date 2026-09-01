# BUILD — state board

**Order changed 2026-08-31 by Chris: build everything first, test everything after.**
All build work (tooling for B1, B2, B4, B5) lands before any measurement session runs.
The measurement sessions — B1 run/rank/freeze, B2 benchmark, B3 dry run, B6
acceptance — form the test phase at the end. Known cost: B4 encodes the design as
written instead of what B3 proved; B3 findings may force B4 amendments.

| Step | What | Needs Chris? | Status |
|------|------|--------------|--------|
| B0 | Intake validator (`tools/intake_check.py`) | no | **done** 2026-08-31 |
| B1 | Meld harness (`tools/meld.py`) — the *run/rank/freeze session* moves to the test phase | build: no | **built** 2026-08-31 |
| B2 | Guard stack tooling (`tools/guard.py`) + seed-generator — the *30-seed benchmark* moves to the test phase | build: no | building |
| B4 | The walkthrough skill: board, arcs, tick/tock scripts, gates G0–G7, invariants I1–I8, learnings store, termbase | build: no | building |
| B5 | Grounding prepass (`tools/prepass.py`): source-search index, grounding ledger, citation→section fan-out | no | building |
| — | **TEST PHASE** (after all builds): B1 session (key, anchors, blind rank, freeze meld-v1) → B2 benchmark (30 seeds, recall table, witness measurement) → B3 dry run (two arcs + serial control, author in loop) → fold B3 amendments into B4 → B6 acceptance (Paper 007) | yes | blocked on builds |

## Frozen decisions (do not relitigate in a step session)

- Meld engine via OpenRouter; model pinned per paper; Claude never melds.
- Every retry regenerates from the locked skeleton; no generator ever sees a prior draft.
- Never gate on a certainty score; never optimize against a detector.
- Arcs 3–5 sections; blocks ≤50 min; sittings ≤90 min.
- Development runs on stand-in material; Paper 007 enters only at B6.

## Step log

- 2026-08-31 · B0 done — `tools/intake_check.py`, selftested, correctly fails empty intake.
- 2026-08-31 · B1 harness pre-built (`tools/meld.py`, `tools/meld_seeds.json`, 6 arms,
  leakage diagnostics, blind-sheet generator, selftested + dry-run verified). The B1
  *session* (run + rank + freeze) remains open.
- 2026-08-31 · B1 prep — model id corrected: `google/gemini-3.1-pro` does not exist on
  OpenRouter; the live id is `google/gemini-3.1-pro-preview` (verified against the
  public /models endpoint; meld.py default fixed). Stand-in draft staged at
  `runs/b1/draft.md` (6 LLM academic-register paragraphs); `runs/b1/anchors/README.md`
  explains what anchor files Chris must drop in. Dry-run assembled 36/36 prompts.
  Still blocked on Chris: OPENROUTER_API_KEY, anchor paragraphs, known-bad
  topic-matched anchor, challenger-model picks.
