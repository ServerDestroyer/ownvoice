# BUILD — state board

One build step per session (Chris's standing rule). A session: reads CLAUDE.md, does
exactly one step below, updates this board, commits, stops. Never start the next step
in the same session.

| Step | What | Needs Chris? | Status |
|------|------|--------------|--------|
| B0 | Intake validator (`tools/intake_check.py`) | no | **done** 2026-08-31 |
| B1 | Meld session: reconstruct prompt, run arms via `tools/meld.py`, blind-rank, freeze meld v1 (model id + prompt + config) | yes — OpenRouter key, 2–4 anchor paragraphs, draft paragraphs, confirm Gemini 3.1 Pro model id | open |
| B2 | Guard stack: entailment wrapper (AlignScore/MiniCheck), typed hedge diff (retune `factwash`), citation/entity/number multiset diff, mechanics lock; ~30-seed benchmark per DESIGN §10-B2 | no (build); Chris reviews results | open |
| B3 | Manual dry run: two contrasting sections through the arc loop by hand + one serial control section; record the DESIGN §10-B3 measurements | yes — author in the loop | open — blocked on B1+B2 |
| B4 | The walkthrough skill: board, arcs, tick/tock scripts, gates G0–G7, invariants I1–I8, learnings store, termbase | no (build) | open — blocked on B3 |
| B5 | Grounding prepass: source-search index, grounding ledger, citation→section fan-out | no | open |
| B6 | Acceptance: Paper 007 assets → intake check → walk end to end; then a second paper with a different template | yes — assets + author | open — blocked on B1–B5 |

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
