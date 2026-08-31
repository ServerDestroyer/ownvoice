# Spike R1 — Is the meld inside or outside the measured voice ceiling?

**Status:** complete (2026-08-31). **Reports to:** `research/11-exemplar-meld-voice-ceiling.md`.
**Feeds:** DESIGN.md §6 (meld), B1 (prompt reconstruction and engine comparison).

## Question

Chris's melding technique — a *single-pass, paragraph-scoped* rewrite of draft content
conditioned on 1–2 concrete exemplar paragraphs of the target author, with a fixed
system prompt and no interaction — empirically beats humanizing tests in his experiments.
The research corpus says every prompt-and-retrieve personalisation method converges to
LUAR 0.484–0.508 vs 0.63 human. Is exemplar-anchored single-pass style transfer inside
that measured family (so the meld's ceiling is already known), or is it a distinct
method class with different measured behavior?

## Sub-questions

1. What exactly did PersonalBench (and the corpus's other authorship benchmarks)
   measure — is few-shot/exemplar conditioning in the measured method list, or only
   abstract style instructions and retrieval-augmented profiles?
2. What does the literature say about *single-pass* exemplar style transfer vs
   iterative approaches — any measured LUAR/authorship numbers for the one-shot case?
3. Engine sensitivity: any published evidence that style-transfer quality varies
   sharply by model family (Gemini vs Claude vs open models)? Chris observed Gemini 3.1
   Pro ≫ Claude, and newer Claude worse than older — is there corroboration or a
   mechanism (RLHF style-flattening, safety tuning)?
4. What system-prompt patterns for exemplar style transfer are documented as working
   (structure, exemplar placement, constraint phrasing, "one pass, no questions")?
   These seed B1's prompt reconstruction.
5. What is the best measurement protocol for a paragraph-scale voice claim (LUAR at
   paragraph granularity, Burrows's Delta window sizes, calibration pairs)?

## Method

Mine the existing corpus first (`research/00-SYNTHESIS.md`, `research/01`, `research/06`,
relevant `sources/papers/` and `sources/repos/` named in the manifests), then web
research for what the corpus lacks (exemplar/few-shot style transfer, one-shot
paraphrase style control, engine comparisons). Every claim carries a citation; separate
measured findings from vendor claims.

## Deliverable and gate

`research/11-exemplar-meld-voice-ceiling.md` in the corpus conventions: verdict on the
family-membership question (in / out / genuinely unmeasured), the measured numbers
found, the engine-sensitivity evidence, a candidate system-prompt seed list for B1, and
the recommended measurement protocol. Gate: the verdict is stated with its evidence
class, and B1's design can cite it.
