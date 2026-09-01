# T1b — Witness measurement (record)

**Date:** 2026-08-31 · **Command:** `tools/py tools/bench_guard.py --witness --entailment minicheck` · **Cost:** $0.009 of the $5 OpenRouter key

## Witness configuration (what actually runs)

- **Model:** `google/gemini-3.1-flash-lite` via OpenRouter (id verified live before
  spending; unlike T1's pro id, this one needed no `-preview` correction).
- **Settings:** temperature **0.0**, no system prompt, no reasoning/thinking mode
  requested — a plain chat completion per sentence. One sentence per call, JSON reply
  (`hedged?`, `attributed?`, quoted markers), markers span-validated against the
  sentence, response cached per sentence in `state/witness_cache.json`. The witness
  never renders a verdict — it only contributes extra marker cues to the typed diff.

## Two wiring defects found and fixed (the T1 pattern, again)

The first witness run flagged **both** TRUE-PARAPHRASE controls (FP 1.00 against a
0.00 floor) with up to nine `DROPPED:hedge` findings from a one-word same-strength
swap. Root cause, in `typed_diff`/`guard`:

1. **Source-only witnessing** — the matched output sentence was never witnessed, so
   any preserved out-of-lexicon hedge read as dropped.
2. **Sum instead of union** — witness cues were added to the lexicon counts, so a
   cue the lexicon already found (e.g. `appears`) counted twice on the source side
   and even identical text self-flagged.

Fix: witness **both sides** (cache makes it cheap) and merge witness cues by
**union**, not sum. Three regression cases pinned in `--selftest` (double-count,
paraphrase-across-phrasings, genuine out-of-lexicon drop).

## Results (30 seeds, incl. the two regenerated after T2)

| class | witness OFF (T1) | witness ON (fixed) |
|---|---|---|
| HEDGE-DROP-OUT-LEX | 0.33 | **1.00** |
| HEDGE-DROP-IN-LEX | 1.00 | 1.00 |
| CONDITION-DROP | 0.33 (weak seed) | **1.00** |
| EVIDENTIAL-REFRAME | 0.00 | 0.33 |
| ATTRIBUTION-DROP | 1.00 | 1.00 |
| BOOSTER-INSERT | 1.00 | 1.00 |
| POLARITY-FLIP | 1.00 | 1.00 |
| TRUE-PARAPHRASE (FP) | 0.00 | **0.00** |

**Thresholded acceptance: PASS** on both the full set and the entailment-admitted
subset. Full tables in `runs/t1/recall.md`.

## What this decides

- **The witness earns its wiring**: out-of-lexicon recall 0.33 → 1.00 at zero false
  positives, for ~$0.005 per 30-paragraph benchmark. Recommendation: make
  `--witness` the default when a key is present. **Chris to confirm.**
- **The CONDITION-DROP floor decision is moot**: with the regenerated seed and the
  witness, the class hits its 1.00 floor — no need to lower it.
- The regenerated `condition-drop-3` is entailment-vetoed (`entailment_clean: false`),
  so it reclassifies out of the "entailment-admitted" table exactly as research/12
  validation 3 prescribes — same as `condition-drop-1`.
- EVIDENTIAL-REFRAME stays honest at 0.33 (research/12 predicted ~0.00 for lexicon
  methods; the witness recovers one of three). Report-only, per design.

## Still open

- Blind direction labelling by Chris (all 30 + ~12 relabelled) — unchanged.
- Witness-default decision above.
