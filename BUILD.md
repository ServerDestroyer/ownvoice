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
| B2 | Guard stack tooling (`tools/guard.py`) + seed-generator — the *30-seed benchmark* moves to the test phase | build: no | **built** 2026-08-31 |
| B4 | The walkthrough skill: board, arcs, tick/tock scripts, gates G0–G7, invariants I1–I8, learnings store, termbase | build: no | **built** 2026-08-31 |
| B5 | Grounding prepass (`tools/prepass.py`): source-search index, grounding ledger, citation→section fan-out | no | **built** 2026-08-31 |
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
- 2026-08-31 · Build-first reorder executed. All tooling built and selftested:
  - **B5** `tools/prepass.py` — citation extractor, paragraph BM25 (no vector DB),
    grounding ledger with committee-verifiable locators (`.locators.json` maps,
    needs_mapping flag), GROUNDING_STALE fan-out, holds report with top-3
    candidates from the citing sentence's context.
  - **B2** `tools/guard.py` — layer 0 claim alignment (UNCHECKABLE = FAIL);
    layer 1 `factwash` 0.5.0 adopted (installed from GitHub into `.venv` — it is
    NOT on PyPI despite research/12; run guard under `.venv/bin/python`), fed
    per-claim (whole-text input misattributes cues); supplements factwash lacks:
    booster-insert, condition-drop, investigation-subtype hedges
    (`tools/guard_lexicon.json`, Kwon's exclusion reversed); measured windows
    (hedge ±1 sentence, negation/attribution matched sentence); citation/number/
    entity multiset diffs; mechanics lock (contractions + punctuation protected);
    witness (OpenRouter, two booleans, span-validated, skeleton-side cache) built
    but unmeasured; entailment wrapper declares not_checked until AlignScore/
    MiniCheck installs (test phase). No certainty-score gate anywhere.
    `tools/seed_defects.py` — 30-seed stratified generator per research/12 recipe
    with mechanical validators (sentence count, word-Levenshtein minimality);
    entailment filter deferred with seeds marked entailment_checked:false.
  - **B4** `tools/board.py` (state tree, append-only gates, I1–I8 asserted with one
    negative test each — all fire), `tools/tock.py` (idempotent TL;DR + ground →
    draft → guard → meld → guard → grade → rank pipeline; regen always from
    skeleton), `tools/tick.py` (meaning/holds/approval blocks, 50/90-min stops,
    seeded defects 1-in-12 with feedback, commit-before-reveal, micro-diversions,
    2-AFC identification calibration with catch trials, batch learnings
    ratification at arc close), `tools/learnings.py` (adversarial admission gate,
    trigger probes → stale.json, FDR suspend-not-delete, Vale termbase
    generation, termbase-beats-anchors conflict log),
    `.claude/skills/walkthrough/SKILL.md` (conductor).
  - Deferred to the test phase, deliberately: B1 session, 30-seed benchmark run +
    recall table, witness measurement, entailment model install, detector/voice
    diagnostic wiring into grades.json, B3 dry run (whose findings may amend B4),
    B6 acceptance.
