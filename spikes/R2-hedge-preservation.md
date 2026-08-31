# Spike R2 — Hedge/certainty preservation in rewriting

**Status:** complete (2026-08-31). **Reports to:** `research/12-hedge-preservation.md`.
**Feeds:** DESIGN.md §5 (guard stack — the deterministic hedge diff), B2's benchmark design.

## Question

The confirmed blind spot in the guard stack: a rewrite that drops a qualifier
("X may contribute" → "X contributes") passes bidirectional entailment. Restyling
measurably inflates certainty 37–75%. What is the best *deterministic or near-
deterministic* way to detect hedge/modality/stance shift between two versions of the
same claim, suitable for a per-paragraph gate on a local machine?

## Sub-questions

1. What taxonomies and lexicons of epistemic markers exist (hedges, boosters, modality,
   evidentials) with published coverage numbers — especially for academic prose?
   (Hyland's metadiscourse work, BioScope, SFU hedge corpora, etc.)
2. What tools/models measure certainty or claim strength directly (certainty
   classifiers, claim-strength regression) and what are their measured accuracies?
3. How have others instrumented certainty *change* between text pairs (summarization
   faithfulness work, claim-drift detection) — is there a working pair-diff method to
   adopt rather than invent?
4. Failure modes of lexicon matching (negation scope, hedges moved across sentence
   boundaries, hedge expressed syntactically not lexically) and the cheapest mitigations.
5. What should B2's seeded-defect benchmark contain for the hedge class — published
   examples of qualifier-drop errors, or generation recipes for realistic seeds?

## Method

Corpus first (`research/00-SYNTHESIS.md` finding on certainty inflation, `research/01`,
`research/05`, `research/06`; check `sources/manifests/` for already-collected papers
and repos on hedging/certainty), then web research for tools, lexicons, and measured
accuracies. Prefer things runnable locally (wordlists, spaCy rules, small classifiers).

## Deliverable and gate

`research/12-hedge-preservation.md`: recommended detection design for the guard stack
(lexicon + rules vs small model vs hybrid, with expected recall on the qualifier-drop
class), the concrete resources to use (names, licenses, availability), the benchmark
recipe for B2's ~30 seeds, and known failure modes with mitigations. Gate: B2 can be
built directly from the recommendation without further research.
