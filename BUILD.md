# BUILD — state board

**Chris's decision 2026-09-01: no more staged test sessions.** The polisher is frozen
as his own method (`tools/meld-v1.json`), the T3 ranking and the T4 dry run are
cancelled, and the product goes straight into use. Everything from here is
**adjust-in-use**: when something is wrong in a real session, fix it, and log the
change in the *Adjustment log* at the bottom with what prompted it. The skill and
tools carry notes where a rule is provisional.

## Use track

| # | Step | Status |
|---|------|--------|
| U1 | **End-to-end machine pass on the stand-in** — intake gate → citation grounder → section setup → skeleton → draft → guard → polisher sweep → candidates → review-ready. Record: `steps/U1-end-to-end.md`. | **done 2026-09-02** — both sections REVIEW_READY, zero retries; benchmark reproduces T1/T1b; 9 selftests + T2 gate pass |
| U1b | **Rehearsal sitting (Chris, interactive)** — `python3 tools/tick.py --state runs/standin2/state --arc 1`, then `--arc 2`, then `learnings.py scan`. The sitting is the ONLY surface never run with a human; do it on throwaway material first. | next — nothing to prepare |
| U2 | **Ship readiness** — 45-agent audit from a fresh clone; 10 confirmed obstacles fixed, secrets scan clean, install commands executed rather than assumed. Public at github.com/ServerDestroyer/ownvoice (MIT). Record, **including everything still untested**: `steps/U2-ship-readiness.md`. | **done 2026-09-03** |
| U3 | **First real paper** — assets into `intake/<paper>/`, `setup_paper.py`, then tick/tock arc by arc with the author. Paper 007 when its assets arrive; any templated paper before that. | after U1b |

## Retired test track (kept for the record; T1, T1b, T2 measured and stand)

| # | Session | Needs | Status |
|---|---------|-------|--------|
| T1 | **Guard benchmark** — MiniCheck wired, 30-seed library built, per-class recall measured, two gate defects found and fixed. Record: `steps/T1-guard-benchmark.md`. | (was mis-stated as "nothing": the seed generator and the witness both need OpenRouter) | **done 2026-08-31 except the witness** — Chris owes the blind direction labelling |
| T2 | **Prepass gate** — synthetic 20-citation paper, 5 seeded-broken; verify resolution, holds report, fan-out per `steps/B5-grounding-prepass.md` gate. Record: `steps/T2-prepass-gate.md`. | nothing | **done 2026-08-31** — PASS, no defects |
| T3 | **Polisher sitting** — 168-row comparison run exists (`runs/b1/`, sheets + `--tally` ready) but the ranking sitting is **cancelled**: meld-v1 frozen as Chris's method by decision. | cancelled 2026-09-01 (data kept) |
| T1b | **Witness measurement** — done. Out-of-lexicon recall 0.33 → **1.00**, FP 0.00; two wiring defects found+fixed (source-only witnessing, sum-not-union merge). Record: `steps/T1b-witness-measurement.md`. | (key delivered 2026-08-31) | **done 2026-08-31** — witness now defaults on (see step log); reverse with `OWNVOICE_WITNESS=0` |
| T4 | **Dry run** — cancelled; its stand-in material (`intake/standin/`) is U1's material instead. | cancelled 2026-09-01 |
| T5 | **Fold-in** — replaced by the adjustment log (continuous). | retired |
| T6 | **Acceptance** — becomes U2, real use; `steps/B6-acceptance.md` still holds the Paper 007 specifics (re-ground the 33 Kelley citations first). | folded into U2 |

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

## Adjustment log (what changed in use, and why — newest last)

- 2026-09-01 · meld-v1 frozen as Chris's method without a ranking sitting (his
  decision). Model qwen/qwen3.7-max, arm humanizing-polisher, T 0.2, thinking off.
- 2026-09-01/02 · **U1, the first end-to-end pass.** Nine plumbing defects fixed on the
  way through (no setup step existed; B0 rejected a correct B5 bundle; narrative
  citations were never extracted; a cut citation never cleared its hold; the guard
  judged every skeleton line a claim; omission and fabrication shared one reference; a
  crash orphaned the section; retries were blind; grounded sources held only the
  bibliographic line). Record and full detail: `steps/U1-end-to-end.md`.
- 2026-09-02 · **Adversarial review of that diff — 23 findings confirmed, 1 refuted**
  (six dimensions, every finding checked by two verifiers defaulting to refute). Three
  of the fixes above were themselves wrong, and all three were reverted or closed:
  (a) `radius=1` on the typed diff's count stage **is** the configuration T1 measured at
  in-lexicon hedge recall 0.17 against a 0.83 floor — reproduced on all 30 seeds, and
  unnecessary because the identity stage already tolerates a floated hedge; removed.
  (b) `MEANING_GATE`'s demotions were justified by the author seeing warnings at G5,
  and the sitting printed no guard findings at all — `tick.py` now prints the draft's
  report and each candidate's. (c) I1 was breached twice below
  `assert_no_prior_draft`'s paragraph-level check: guard notes quoted prior-draft
  sentences, and `grounded-sources.md` embedded the author's own `Citing sentence:`
  into what the drafter reads. Also fixed: I4 deadlocked every 3+ arc paper (SKIM
  counted as in flight); `setup_paper` erased the author's hold adjudications on
  re-run; I2 parked sections whose surviving candidates were clean; a fully bold main
  point was deleted from the locked claims; cut citations matched only the
  parenthetical form and are now verified absent mechanically; `sentences()` no longer
  merges after an acronym nor drops heading text; `template_sections` handles `###` and
  rejects duplicate ids; `apply_gate`'s test no longer passes vacuously.
- 2026-09-03 · **Ship readiness (U2).** A 45-agent audit cloned the repo and tried to
  become a new user: 10 obstacles confirmed by two refuting verifiers each, all fixed.
  The important one: with no anchors the polisher still called the API for every
  paragraph, asking the model to make the text "sound like the text from" nothing — a
  paid rewrite toward no one. `setup_paper` now refuses an empty `--anchors` (and globs
  `*.md` so the author-corpus works directly), and `tock` refuses before the sweep.
  Also: `tools/py` exited 127 on any clone and now falls back to the system python;
  `tick` prints `NOT CHECKED` so a degraded guard cannot read as a clean pass;
  `OWNVOICE_WITNESS=0` now works from `.env`, where the docs say to put it; README
  gained a data-handling disclosure; `intake/standin/README.md` no longer claims its
  author corpus is empty or synthetic; `CLAUDE.md` was rewritten from the cancelled
  one-step-per-session protocol. Secrets scan clean across all history. Full record and
  the **untested list** in `steps/U2-ship-readiness.md`.
- 2026-09-03 · Name kept as OwnVoice (a rename to "Stet" was written and reverted at
  Chris's choice), MIT licensed, public at github.com/ServerDestroyer/ownvoice. The
  private `Deocracy/ownvoice` remains as `origin` and is behind; `public` is the live
  remote.
- 2026-09-02 · **`tick.py` corrected before its first use** — it asked 29 and 41
  questions where the sections hold 8 and 10 claims; approval wrote `approved.md` from
  the oldest superseded candidate whatever the author picked; the 2-AFC catch trial
  showed the same text twice and leaked the anchor's provenance comment; a cap hit
  during approval crashed the sitting. All fixed and tested. It has still never run
  with a human — that is U1b.

## Frozen decisions (do not relitigate in a step session)

- Polisher engine via OpenRouter; model pinned per paper; Claude never polishes.
  Default `qwen/qwen3.7-max` (Chris, 2026-09-01: highest output perplexity of 8
  candidates with thinking off and temperature honoured; Gemini 3.1 Pro cannot turn
  thinking off on OpenRouter). T3's blind ranking may overturn it; nothing else may.
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
- 2026-09-01 · **Polisher model: `qwen/qwen3.7-max` (Chris's decision).** Output
  perplexity under GPT-2 on 3 paragraphs × 8 models (`runs/b1/ppl-probe.json`, $0.09):
  qwen3.7-max highest at 145.9, gpt-5.6-terra-pro 137.1, kimi-k3 131.3, gemini 124.8;
  unpolished drafts 121.7. Direction only (within-model spread exceeds the gaps), and
  perplexity stays a selection heuristic, never a target. Default changed in `meld.py`,
  `tock.py` (skeleton + draft stages follow the same variable — untested there, T4
  will show), `.env.example`. Gemini demoted to challenger.
- 2026-09-01 · **Anchor pool delivered — T3 unblocked.** Chris pointed at the DAGS
  whitepaper (github.com/Deocracy/Whitepaper, nontechnical pre-release 020, Christopher
  Colantuono, 2019-08, 28 pp) as "the very best of the author's writings". Fetched,
  converted with pypdf (sidebars and pull-quotes dropped, hard wraps reflowed; 136
  paragraphs, ~13.4k words) to `runs/b1/anchors/dags-wp-nontechnical-020.md` and
  `intake/standin/author-corpus/`; `anchor1..3.md` picked (paragraphs 20, 39, 117).
  `intake_check intake/standin` now **PASS** with the expected below-floor NOTE (13.9k
  words / 1 doc vs 50k / 40 — voice metrics trend-only). Note for T3: this pool is
  *about* decentralised governance, i.e. topic-adjacent to Paper 007 — which is Chris's
  matched-anchor condition by construction, and the unmatched condition against the
  thermal-comfort stand-in.
- 2026-09-01 · **T3 solo half done.** Round 1 (168 rows) was thrown out and archived
  (`runs/b1/round1-sameclaims/`): its matched drafts were built from the anchors' own
  claims, so deepseek/kimi returned the anchor itself (leak 0.9, copy 0.01) — a
  degenerate condition, and a lesson: a matched draft must share topic and form, never
  claims. Also the staged `draft.md` was about participatory governance, i.e. not
  unmatched against a governance anchor pool; replaced by three thermal-comfort
  paragraphs. Round 2: 168 rows, 7 arms × 4 models × (unmatched + 3 matched anchors,
  drafts from the neighbouring pool paragraph's claims), thinking off, T=0.2, 0 errors,
  0 prefaced outputs, ~$1.5 total. Diagnostics: Chris's arm on Qwen rewrites without
  copying either input (leak ≤0.19, copy ≤0.39) but lengthens 21–50%; deepseek
  returned the draft unchanged for Chris's arm matched (copy 1.00); snippet-seeded
  copies the anchor on deepseek/gemini (discard); only Gemini spends reasoning tokens.
  `meld.py` gained cross-dir `--blind ... --arms --out` (Stage B) and `--tally`.
  Sitting procedure: `steps/T3-sitting.md` — Stage A 48 candidates on Qwen, Stage B
  ~32 on the winning arm across models.
