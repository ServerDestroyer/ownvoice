# T1 — Guard benchmark

**Run:** 2026-08-31. **Spec:** `steps/B2-guard-stack.md` gate section; recipe and
acceptance criteria from `research/12-hedge-preservation.md` (Humanising-Realtime repo).

## What was done

1. **Entailment backend installed and wired.** MiniCheck-Flan-T5-Large (770M) into
   `.venv`; `tools/guard.py --entailment minicheck` runs both directions (skeleton→text
   for dropped concepts, text→skeleton+sources for invention). `--entailment none` still
   declares `not_checked` and never silently passes.
2. **30-seed library built** at `tools/seeds/` (tracked; the B4 tick script reuses it).
3. **Benchmark harness** `tools/bench_guard.py`, with `--selftest`.
4. **Two defects found and fixed in the gate.**
5. **Witness: not measured.** It needs OpenRouter and there is no key on this machine.

AlignScore was not used: its pinned deps (`bleurt` from git, `benepar`, `summac`) do not
build on Python 3.13. DESIGN §5 allows either; MiniCheck is the wired one.

## Deviation from spec: who generated the seeds

`research/12` says to prompt **two models that are not the meld engine at T=0.5**.
That path (`tools/seed_defects.py --pool`) calls OpenRouter, and no
`OPENROUTER_API_KEY` exists here, so on Chris's instruction the edits were made by
**blind Claude Haiku 4.5 subagents**: 9 agents wrote 36 stand-in dissertation paragraphs,
then 30 further agents each made one targeted minimal edit. Every agent got its paragraph
and its class instruction inline and was told to read no files; none saw `tools/guard.py`
or `tools/guard_lexicon.json`. The point of the spec's rule — a generator independent of,
and blind to, the answer key — holds. What is lost is the two-model diversity and the
T=0.5 setting.

Every seed went through the **same** mechanical validators as the API path, via a new
`tools/seed_defects.py --ingest`: identical sentence count, word edit distance ≤ 8, pool
paragraph carries ≥ 1 epistemic marker. 32 edits generated, 2 rejected (one non-minimal
at distance 12; one whose pool paragraph carried no epistemic marker), 2 replacements
drawn from spare pool paragraphs — 30 admitted.

Seeds record `generator: claude-haiku-4-5 (blind subagents...)`, `temperature: null`.
`label` is `null` on all 30: **Chris still owes the blind direction labelling**
(inflated / deflated / preserved) plus a second pass over ~12 for the self-agreement
bound. Until that exists every number below is provisional on the class assignments being
right — and two of them are not (see "Seed quality").

## Two defects the benchmark found in the gate

**1. The typed diff was a bare set difference.** `typed_diff` compared *cue identities*:
a source cue absent from the output fired `DROPPED`, so every same-strength paraphrase
was flagged. `research/12` specifies a typed change set over marker *classes* and says in
terms "never a bare set difference". Measured: TRUE-PARAPHRASE false-positive rate
**2/2** — the control class that exists precisely to catch this. `factwash` contributed
one of the two on `may → could`; its HEDGE lexicon carries `"may "` and `"could be"` but
not bare `could`, which is the coverage gap `tools/guard_lexicon.json` exists to close.

Fixed: the diff now fires on a fall in the **class count within the matched sentence**,
and uses the ±1 window only to rescue a cue that *floated* to a neighbour (its stated
purpose). A `factwash` finding is demoted to `info` only when our supplemented lexicon
positively shows every class it maps to survived — a genuine drop takes the class count
with it and stays a FAIL. Change of strength *within* a class is now declared
`certainty_gradation: not_checked` on every report rather than silently passed.

**2. The selftest that should have caught it passed vacuously.** It asserted that the
*output* cue (`could`) was not reported dropped — which can never happen, since only
source-side cues are ever reported. Replaced with real paraphrase-invariance cases.

The first attempt at fix (1) counted classes across the whole ±1 window, which let a
hedged neighbour mask a real deletion and took in-lexicon recall from 1.00 to **0.17**.
Now a pinned regression test.

## Results — 30 seeds, backend `minicheck`, witness off

Three recalls, and the differences carry the finding. `recall_epistemic` is the typed
marker diff firing — the number `research/12`'s expectations refer to. `recall_gate` is a
FAIL for any reason. `entailment alone` is layer 3 on its own. Reporting only the gate
number would credit the hedge diff for catches made by entailment or the citation diff.

| class | n | epistemic layer | gate (any layer) | entailment alone | floor | acceptance |
|---|---|---|---|---|---|---|
| POLARITY-FLIP | 2 | 1.00 | 1.00 | 1.00 | ≥ 1.00 | PASS |
| CONDITION-DROP | 3 | 0.33 | 0.33 | 0.33 | ≥ 1.00 | **FAIL** |
| HEDGE-DROP-IN-LEX | 6 | 1.00 | 1.00 | 0.00 | ≥ 0.83 | PASS |
| TRUE-PARAPHRASE | 2 | 0.00 (false-positive rate) | 0.00 | 0.00 | ≤ 0.00 | PASS |
| HEDGE-DROP-OUT-LEX | 6 | 0.33 | 0.50 | 0.17 | — | report-only |
| EVIDENTIAL-REFRAME | 3 | 0.00 | 0.00 | 0.00 | — | report-only |
| ATTRIBUTION-DROP | 4 | 0.75 | 1.00 | 1.00 | — | report-only |
| BOOSTER-INSERT | 4 | 1.00 | 1.00 | 0.00 | — | report-only |

**Thresholded acceptance: FAIL** — on CONDITION-DROP alone.

Under `research/12`'s validation 3 (a seed entailment already vetoes is not testing the
named blind spot), 6 of 30 are excluded and the picture sharpens:

| class | n | epistemic layer | gate | entailment alone | floor | acceptance |
|---|---|---|---|---|---|---|
| POLARITY-FLIP | 2 | 1.00 | 1.00 | 1.00 | ≥ 1.00 | PASS |
| CONDITION-DROP | 2 | 0.00 | 0.00 | 0.00 | ≥ 1.00 | **FAIL** |
| HEDGE-DROP-IN-LEX | 6 | 1.00 | 1.00 | 0.00 | ≥ 0.83 | PASS |
| TRUE-PARAPHRASE | 2 | 0.00 (false-positive rate) | 0.00 | 0.00 | ≤ 0.00 | PASS |
| HEDGE-DROP-OUT-LEX | 5 | 0.40 | 0.40 | 0.00 | — | report-only |
| EVIDENTIAL-REFRAME | 3 | 0.00 | 0.00 | 0.00 | — | report-only |
| ATTRIBUTION-DROP | **0** | — | — | — | — | no seeds survive |
| BOOSTER-INSERT | 4 | 1.00 | 1.00 | 0.00 | — | report-only |

Per-seed record with the layers that fired: `runs/t1/bench.json` (untracked).

## Reading

- **The layered design is doing exactly what it was designed to do.** Entailment catches
  0.00 of the in-lexicon hedge drops and 0.00 of the booster inserts across real
  paragraphs — the named blind spot is real and the typed diff is the only thing covering
  it. Conversely the typed diff misses attribution cases entailment catches. The two
  layers are complementary, not redundant, and that is now measured rather than assumed.
- **Attribution drops are not the blind spot.** Entailment caught 4/4, including the
  `Copley demonstrates that → The` case the lexicon missed (`demonstrates` is not in the
  attribution list). The class empties entirely under strict admission. `research/12`
  called attribution the lowest-recall class and worried about it; on this evidence the
  entailment layer already covers it, and the lexicon's weakness there matters less than
  the design assumed. **n=4 — a direction, not a rate.**
- **In-lexicon hedge drop 1.00 (6/6)** against a ≥0.83 floor, **polarity 1.00 (2/2)**,
  **false-positive control 0/2**. The closed-class controls behave.
- **Out-of-lexicon hedge 0.33 (0.40 admitted), witness off.** `research/12` budgets ~0.6
  *with* the witness. The misses are exactly the open-class tail — "something closer to",
  "something akin to", "hints at", "The position that commands increasing assent holds
  that". **This is the number that decides whether the witness gets wired, and it argues
  for wiring it.** One of the two catches was `appears → is`, an in-lexicon cue produced
  under the out-of-lexicon instruction, so 0.33 is if anything generous.
- **Evidential reframe 0.00 (3/3 missed), by every layer.** All three are clean
  `We → Researchers` reframes. `research/12` predicted exactly this ("the case our diff
  will miss and the human must catch"). Confirmed; the mitigation stays the human at G5
  plus the preserve-certainty clause in the meld prompt.
- **Condition drop fails its 1.00 floor**, and the floor is the problem as much as the
  code. Of three seeds only two instantiate the class (below); one miss is
  `only insofar as → since`, an out-of-lexicon conditional. `research/12`'s own measured
  lexicon recall for conditionals is **0.67**, so a 1.00 acceptance floor is not
  reachable by a lexicon at all.

**No lexicon was touched in response to these misses.** `research/12`'s mining rule fixes
candidate admission in advance (≥60% of newly-fired sentences gold, ≥10 firings) and
warns "never report lexicon recall on a corpus you mined from". Adding `only insofar as`,
`demonstrates`, or `hints at` now would make this table meaningless.

## Seed quality — two weak instances

- `condition-drop-3`: deletes `only` from "hold validity **only when** …", leaving
  `when`. The claim stays conditional, so this is a scope-narrowing (BROADENED) edit,
  which `research/12` explicitly says not to build a detector for. The gate is right to
  pass it; the seed does not instantiate its class.
- `hedge-drop-out-lex-4`: `appears → is` is an in-lexicon drop generated under the
  out-of-lexicon instruction.

Both should be regenerated before these numbers are quoted anywhere, and both will show
up in Chris's blind labelling.

## Runtime footprint

- MiniCheck-Flan-T5-Large (770M), **CPU**, fp32: ~0.2 s per (doc, claim) pair, ~5 s to
  load, ~4 GB peak RSS. Whole 30-seed benchmark: **78 s wall**.
- Model cache `.models/` 5.9 GB, `.venv/` 5.2 GB (torch + CUDA wheels). Both gitignored.
- **The GPU is not used, and not because of VRAM** — 16 GB is ample. torch 2.13 routes a
  T5 attention op to a Triton kernel; Triton JIT-compiles its CUDA glue with gcc against
  Python headers NixOS does not ship in the system profile, and the failure surfaces as a
  bare `FileNotFoundError: /sbin/ldconfig` from inside the forward pass. CPU is fast
  enough that this is not worth fixing now; `OWNVOICE_ENTAIL_DEVICE=auto` re-enables the
  GPU attempt if those headers ever exist.
- **Run tools through `tools/py`, not `.venv/bin/python`.** On NixOS the wheels need
  `LD_LIBRARY_PATH` for `libstdc++.so.6` and `libcuda.so.1`, plus `TRITON_LIBCUDA_PATH`;
  the wrapper sets all three from the running system generation.

## Open after T1

- **Witness unmeasured** — needs `OPENROUTER_API_KEY` in `/home/chris/coding/ownvoice/.env`.
  One command when the key lands: `tools/py tools/bench_guard.py --witness --entailment
  minicheck`. Out-of-lexicon 0.33–0.40 is the case for doing it.
- **Blind direction labelling** by Chris on all 30, plus ~12 relabelled for the
  self-agreement bound.
- **Two seeds to regenerate.**
- **The CONDITION-DROP acceptance floor of 1.00** needs a decision: it sits above the
  published lexicon ceiling for that class.
