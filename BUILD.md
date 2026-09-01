# BUILD — state board

**Build phase: complete** (2026-08-31). All tooling exists and passes selftests. What
remains is the **test track** below — ordered, one session each, each session either
fully solo or a named Chris sitting with its needs listed. A session must be
finishable the day it starts: if a T-step's "needs" aren't in hand, do not start it.

Two lessons already paid for (do not repeat): (1) never order a Chris-blocked session
before solo-runnable work; (2) "build X" and "measure X" are different steps — never
share a label between them.

## Test track (do in this order; T1/T2 are solo and unblocked NOW)

| # | Session | Needs | Status |
|---|---------|-------|--------|
| T1 | **Guard benchmark** — MiniCheck wired, 30-seed library built, per-class recall measured, two gate defects found and fixed. Record: `steps/T1-guard-benchmark.md`. | (was mis-stated as "nothing": the seed generator and the witness both need OpenRouter) | **done 2026-08-31 except the witness** — Chris owes the blind direction labelling |
| T2 | **Prepass gate** — synthetic 20-citation paper, 5 seeded-broken; verify resolution, holds report, fan-out per `steps/B5-grounding-prepass.md` gate. | nothing | open — unblocked |
| T3 | **Meld sitting (~1 h, Chris)** — run arms, blind-rank, freeze `tools/meld-v1.json` + regression triples. Procedure: `steps/B1-meld-session.md`. | `.env` with OPENROUTER_API_KEY; 2–4 anchor paragraphs in `runs/b1/anchors/`; challenger-model picks; a topic-matched anchor for the known-bad control | open — blocked on Chris inputs |
| T1b | **Witness measurement (solo, ~20 min)** — the one part of T1 that could not run. `tools/py tools/bench_guard.py --witness --entailment minicheck`, then read out-of-lexicon hedge recall against T1's 0.33/0.40 baseline; decide whether the witness gets wired. | `.env` with OPENROUTER_API_KEY | open — blocked on the key |
| T4 | **Dry run (two sittings, Chris)** — two arc-batched sections + one serial control, seeded defects from T1's library, measurements per `steps/B3-dry-run.md`. | T1 + T3 done; Chris's time | open |
| T5 | **Fold-in (solo)** — encode T4's amendments into the skill/tools; re-run invariant negative tests; wire detector/voice diagnostics into grades.json if T4 showed they're needed. | T4's measurement file | open |
| T6 | **Acceptance (Chris + author, one arc per session)** — Paper 007 assets in, intake check, prepass (re-ground the 33 Kelley citations first), walk the paper; then the different-template generality check. Procedure: `steps/B6-acceptance.md`. | T1–T5 done; assets in `intake/paper-007/` | open |

## Build phase — done

| Step | What | Status |
|------|------|--------|
| B0 | Intake validator (`tools/intake_check.py`) | done 2026-08-31 |
| B1-build | Meld harness (`tools/meld.py`, seeds, .env config, blind sheets) | done 2026-08-31 |
| B2-build | Guard stack (`tools/guard.py`, lexicon, witness, entailment hooks) + `tools/seed_defects.py` | done 2026-08-31 |
| B4-build | Walkthrough skill (`tools/board.py`, `tock.py`, `tick.py`, `learnings.py`, `.claude/skills/walkthrough/`) — encodes the unproven design; T4 may amend | done 2026-08-31 |
| B5-build | Grounding prepass (`tools/prepass.py`) | done 2026-08-31 |

## Frozen decisions (do not relitigate in a step session)

- Meld engine via OpenRouter; model pinned per paper; Claude never melds.
- Every retry regenerates from the locked skeleton; no generator ever sees a prior draft.
- Never gate on a certainty score; never optimize against a detector.
- Arcs 3–5 sections; blocks ≤50 min; sittings ≤90 min.
- Development runs on stand-in material; Paper 007 enters only at T6.

## Step log

- 2026-08-31 · B0 done — `tools/intake_check.py`, selftested, correctly fails empty intake.
- 2026-08-31 · B1 harness pre-built (`tools/meld.py`, `tools/meld_seeds.json`, 6 arms,
  leakage diagnostics, blind-sheet generator, selftested + dry-run verified).
- 2026-08-31 · B1 prep — model id corrected: `google/gemini-3.1-pro` does not exist on
  OpenRouter; the live id is `google/gemini-3.1-pro-preview` (verified against the
  public /models endpoint; meld.py default fixed). Stand-in draft staged at
  `runs/b1/draft.md`; `runs/b1/anchors/README.md` explains what Chris must drop in.
- 2026-08-31 · Build-first reorder (Chris's decision); all tooling built and selftested:
  prepass (citation extractor, paragraph BM25, ledger with committee-verifiable
  locators, fan-out, holds report); guard (claim alignment with UNCHECKABLE=FAIL,
  factwash 0.5.0 from GitHub in `.venv` — NOT on PyPI, run guard under
  `.venv/bin/python` — plus `tools/guard_lexicon.json` supplements incl. the Szeged
  investigation-subtype reversal, measured windows, multiset diffs, mechanics lock,
  unmeasured witness, entailment declared not_checked until install); seed generator
  (30 stratified seeds, mechanical validators, entailment filter deferred); skill
  (board with I1–I8 asserted + negative-tested, idempotent tock, tick with 50/90-min
  stops, seeded defects 1-in-12, commit-before-reveal, 2-AFC calibration, learnings
  admission/FDR/termbase).
- 2026-08-31 · Execution order rebuilt as the test track above after the numbered
  B-order proved unworkable (Chris-blocked step ordered first; build/measure conflated
  under one label; test phase was an undifferentiated blob).
- 2026-08-31 · **T1 done except the witness** — full record in
  `steps/T1-guard-benchmark.md`. MiniCheck-Flan-T5-Large wired (AlignScore's pins do not
  build on py3.13); 30-seed library at `tools/seeds/` generated by **blind Haiku
  subagents**, not the two OpenRouter models the recipe names, because no key exists here
  — same mechanical validators via a new `--ingest` path. Headline: in-lexicon hedge drop
  1.00 (6/6), polarity 1.00, false-positive control 0/2, out-of-lexicon 0.33 (witness
  off), evidential reframe 0.00 exactly as `research/12` predicted, CONDITION-DROP 0.33
  against a 1.00 floor. **Two gate defects found and fixed**: the typed diff was a bare
  per-cue set difference and flagged every same-strength paraphrase (2/2 false positives),
  and the selftest meant to catch that passed vacuously. Measured complementarity:
  entailment catches 0.00 of hedge drops and booster inserts but 4/4 attribution drops —
  the two layers are complementary, not redundant, and attribution is not the blind spot
  the design feared. **Run tools via `tools/py`, not `.venv/bin/python`** (NixOS needs
  LD_LIBRARY_PATH + TRITON_LIBCUDA_PATH); entailment runs on CPU at ~0.2 s/pair, 78 s for
  the whole benchmark.
