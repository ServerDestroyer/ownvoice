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
| T2 | **Prepass gate** — synthetic 20-citation paper, 5 seeded-broken; verify resolution, holds report, fan-out per `steps/B5-grounding-prepass.md` gate. Record: `steps/T2-prepass-gate.md`. | nothing | **done 2026-08-31** — PASS, no defects |
| T3 | **Polisher sitting (~1 h, Chris)** — run arms (Chris's humanizing-polisher arm + the 6 research arms) × anchor condition (matched vs unmatched) × models, blind-rank, freeze `tools/meld-v1.json` + regression triples. Procedure: `steps/B1-meld-session.md`. | 2–4 paragraphs of Chris's unassisted prose, any topic (paste in chat or drop in `runs/b1/anchors/`). Nothing else: matched drafts are generated solo from the anchors; key delivered; thinking-off + temperature verified live on 8 models (probe table in the procedure). Recommended challengers `deepseek-v4-pro-0813`, `x-ai/grok-4.3`, `moonshotai/kimi-k3` — Chris to confirm. | open — blocked ONLY on anchor prose |
| T1b | **Witness measurement** — done. Out-of-lexicon recall 0.33 → **1.00**, FP 0.00; two wiring defects found+fixed (source-only witnessing, sum-not-union merge). Record: `steps/T1b-witness-measurement.md`. | (key delivered 2026-08-31) | **done 2026-08-31** — witness now defaults on (see step log); reverse with `OWNVOICE_WITNESS=0` |
| T4 | **Dry run (two sittings, Chris)** — two arc-batched sections + one serial control, seeded defects from T1's library, measurements per `steps/B3-dry-run.md`. | T3 done; Chris's time. **Material is built**: `intake/standin/` (3 sections, 5 sources, template with section types, deliberate citation defects) — record `steps/T4-prep-standin.md` | open — blocked only on T3 + Chris's time |
| T5 | **Fold-in (solo)** — encode T4's amendments into the skill/tools; re-run invariant negative tests; wire detector/voice diagnostics into grades.json if T4 showed they're needed. | T4's measurement file | open |
| T6 | **Acceptance (Chris + author, one arc per session)** — Paper 007 assets in, intake check, prepass (re-ground the 33 Kelley citations first), walk the paper; then the different-template generality check. Procedure: `steps/B6-acceptance.md`. | T1–T5 done; assets in `intake/paper-007/` | open |

## Build phase — done

| Step | What | Status |
|------|------|--------|
| T4-prep | Stand-in material bundle (`intake/standin/`) + three defects it exposed | done 2026-08-31 |
| B0 | Intake validator (`tools/intake_check.py`) | done 2026-08-31 |
| B1-build | Meld harness (`tools/meld.py`, seeds, .env config, blind sheets) | done 2026-08-31 |
| B2-build | Guard stack (`tools/guard.py`, lexicon, witness, entailment hooks) + `tools/seed_defects.py` | done 2026-08-31 |
| B4-build | Walkthrough skill (`tools/board.py`, `tock.py`, `tick.py`, `learnings.py`, `.claude/skills/walkthrough/`) — encodes the unproven design; T4 may amend | done 2026-08-31 |
| B5-build | Grounding prepass (`tools/prepass.py`) | done 2026-08-31 |

## Component names (proposed 2026-09-01 from Chris's "humanizing polisher"; rename here)

| Name | Code | What it does |
|------|------|--------------|
| intake gate | `tools/intake_check.py` | G0 — the four inputs are present and markdown |
| citation grounder | `tools/prepass.py` | G1 — every citation resolves to a committee-verifiable locator or holds |
| meaning skeleton | `tock.py` TL;DR stage | the locked list of claims a section must carry |
| skeleton drafter | `tock.py` draft stage | regenerates prose from the skeleton, never from a prior draft |
| meaning guard | `tools/guard.py` (lexicon + witness + entailment layers) | G4 — the polished text still says exactly what the skeleton says |
| **humanizing polisher** | `tools/meld.py`, arm 0 of `meld_seeds.json` | Chris's method: one author paragraph + one draft paragraph, thinking off, low temperature |
| anchor picker | not built | chooses the author paragraph by form + topic — needed only if the matched condition wins T3 |
| blind ranker | `meld.py --blind` | shuffled sheet with the unpolished draft hidden in it |
| conductor | `board.py`, `tick.py`, `tock.py`, the walkthrough skill | the arc loop and its invariants |
| learnings store | `tools/learnings.py` | ratified author conventions, termbase, staleness scan |

"Meld" in code and older records = the humanizing polisher.

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
- 2026-08-31 · **T2 done — prepass gate PASS, no defects.** Record in
  `steps/T2-prepass-gate.md`; deterministic runner at `tools/gate_prepass.py`. 20 distinct
  citations (incl. et al./&/2020a forms), 5 seeded-broken incl. a wrong-year and a
  topical near-miss: 20/20 classified correctly, locators committee-verifiable with
  needs_mapping flags right, fan-out exact, holds candidates rank the true near-miss
  passages first. Runtime <0.01 s. Next unblocked solo work: none — T1b and T3 both
  wait on `OPENROUTER_API_KEY` in `.env`, plus T3's anchor/challenger inputs.
- 2026-08-31 · **Two weak T1 seeds regenerated** (the last open build item; Chris chose
  build-first over the test track). Blind Haiku subagents, same `--ingest` validators
  plus two new class-specific checks: out-lex seeds must leave the in-lexicon hedge
  multiset unchanged, condition-drop seeds must make a conditions marker disappear.
  Both pass; `entailment_checked: false` until the next bench_guard run. **The build
  is now fully made — nothing left to construct.** Everything remaining is
  measurement: T1b/T3 (need the key), T4–T6 (need Chris).
- 2026-08-31 · **T1b done** — key delivered ($5 limit; $0.009 spent). Witness =
  `google/gemini-3.1-flash-lite`, T=0.0, no system prompt, no thinking mode, one
  sentence per call, cached. First run failed its own control (TRUE-PARAPHRASE FP
  1.00): two wiring defects — witness ran on the source side only, and its cues were
  summed onto lexicon counts instead of unioned, so identical text self-flagged.
  Fixed in `typed_diff`/`guard`, three regressions pinned in selftest. After the fix:
  out-of-lexicon hedge recall **0.33 → 1.00**, FP 0.00, all floors PASS, and the
  CONDITION-DROP floor question is moot (class hits 1.00). Record:
  `steps/T1b-witness-measurement.md`. The witness-default question it left open was
  answered the same day — see the T4-material entry below.
- 2026-08-31 · **T4 material built (solo) — `intake/standin/`.** Three sections (an
  argumentative/procedural pair for the batched arm, one argumentative serial control),
  five invented sources (two with locator sidecars, three without), a template carrying
  section types, and an author-corpus that fills from the T3 anchors. Building it
  exposed three defects, all fixed and pinned: (1) **B0 rejected a correct B5 bundle** —
  `intake_check` failed the `*.locators.json` sidecars that `prepass` reads, so a
  properly-prepared intake could not pass G0 (would have fired at T6); (2) **narrative
  citations were never extracted** — `Alvarez (2019) found ...` reached neither the
  ledger nor holds (3 of 9 on the stand-in paper), because there was no narrative
  pattern and the sentence splitter cut `Nakamura et al. (2019)` at the `al.` period;
  T2's gate covered only the parenthetical form and so passed vacuously here — its
  fixture now uses both forms and still PASSes; (3) **the production path ran the
  weakest guard** — `tock.py` took the defaults, which were witness off and entailment
  off, so neither measured layer was ever live outside the benchmark. Defaults now
  resolve: witness on wherever a key exists (`OWNVOICE_WITNESS=0` off), MiniCheck on iff
  its weights are already in `.models/`, never downloading (`OWNVOICE_ENTAIL=none` off);
  selftests pin both off and stay offline. Verified: all four selftests pass, T2 gate
  PASS, and `bench_guard --witness --entailment minicheck` re-run end to end reproduces
  T1b exactly (out-of-lex 1.00, FP 0.00, four thresholded classes PASS). Record:
  `steps/T4-prep-standin.md`; open items for T6 noted there.
- 2026-09-01 · **Chris's original method recorded — the humanizing polisher.** The
  prompt the memory said was never saved now is: arm 0 of `tools/meld_seeds.json`,
  verbatim, interim production default. Its settings are now the harness defaults and
  were all previously wrong or absent: thinking is sent as the model's lowest setting
  (nothing was sent before, so every run thought at "medium"); temperature 0.2 (was
  0.7); one paragraph at a time with headings, lists, tables, boxes and captions passing
  through untouched (`meld.is_prose`, wired into `tock.py` too); temperature omitted for
  models that reject it. Live probe on 8 models (`runs/b1/thinking-probe.json`): all
  accept the switch; **Gemini 3.1 Pro cannot turn thinking off on OpenRouter**
  (mandatory, floor "low", 814 reasoning tokens for 48 of output, 20× the cost of the
  alternatives); gpt-5.6 family has no temperature. The topic-matched anchor is
  reframed from "known-bad control" to a **condition to be ranked** — research/11 says
  it hurts, Chris says it is best; T3 decides, the leak column and the guard catch the
  failure mode either way. Component names proposed above. Selftests pin the new arm
  as default, the thinking switch, and the prose filter.
