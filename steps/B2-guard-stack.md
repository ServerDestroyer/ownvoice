# B2 — Guard stack

**Objective:** build `tools/guard.py` — the G4 gate: bidirectional entailment + the
deterministic diffs — and benchmark it on ~30 seeded defects. Spec: DESIGN.md §5;
research basis: `research/12-hedge-preservation.md` (read it first, in full) in the
Humanising-Realtime repo.

**Components (in `tools/guard.py`, one CLI, `--selftest`):**
1. **Entailment wrapper** — AlignScore (355M) or MiniCheck (770M); clones exist in
   `/home/chris/coding/Humanising-Realtime/sources/repos/{AlignScore,MiniCheck}`. Runs
   both directions: skeleton→text (missing items) and text→skeleton+sources (invented
   claims). 16 GB GPU budget.
2. **Typed hedge/marker diff** — retune `factwash` (pip, Apache-2.0, offline), do not
   rebuild. Output classes: DROPPED attribution / STRENGTHENED certainty / REVERSED
   polarity / ADDED booster. Windows are fixed by measurement (research/12): hedges =
   matched sentence ±1; negation and attribution = matched sentence only. Unalignable
   output → verdict `UNCHECKABLE`, which is a FAIL, never a pass. Lexicon mining
   sources: BioScope (CC-BY 2.0), Szeged (INCLUDE the `investigation` subtype —
   research/12 reverses Kwon's exclusion for our use), PolNeAR.
3. **Citation/entity/number multiset diff** — deterministic: the multiset of citation
   markers, named entities, and numbers in output must equal the input's exactly.
4. **Mechanics lock** — for author-written spans: idiosyncratic punctuation/spacing/
   contractions are protected tokens; any normalization = FAIL (research/14).
5. **LLM witness** (the one untested element — measure it): covers the two classes
   lexicons can't; returns two booleans + span-validated markers, never a verdict;
   witness the SKELETON side once and cache. Use OpenRouter with meld-v1's model if B1
   is done, any cheap model otherwise.
6. Do NOT build: any certainty-score gate (published classifiers saturate on
   directional pairs — research/12). A pairwise certainty judge may exist as a
   `--diagnostic` flag only.

**Benchmark:** ~30 seeded defects per the research/12 recipe, on dissertation-register
sample text (use Paper 007 extracted text only if already available; else any academic
markdown). Classes: dropped concepts, invented claims, dropped qualifiers (in-lexicon /
out-of-lexicon / evidential-reframe subclasses), moved/merged citations, reversed
polarity. Save the seed library to `tools/seeds/` — the B4 tick script reuses it.

**Gate:** recall per class reported against expectations (~0.9 in-lexicon hedge drops,
~0.6 out-of-lexicon with witness, ~0.94 polarity); multiset diffs 100% by construction;
witness measured and its numbers written down.

**Record in BUILD.md:** per-class recall table, witness verdict, model/runtime footprint.
