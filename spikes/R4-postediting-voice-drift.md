# Spike R4 — Post-editing voice drift (the Baumler line)

**Status:** complete (2026-08-31). **Reports to:** `research/14-postediting-voice-drift.md`.
**Feeds:** DESIGN.md §8 (polish dial 7–10), §6 (anchor policy), §5 (blind A/B calibration).

## Question

Baumler et al. (in-corpus, 81 participants, pre-registered): authors who post-edit LLM
text perceive the result as representative of their style while it measurably sits
closer to LLM text than their unassisted writing, and their stylistic diversity drops.
The design's top polish band (7–10) melds the author's *own* prose — the one place this
finding says we demonstrably degrade real voice while the author approves it. What
interventions does the literature support for keeping human editing of (or over) LLM
text from converging to LLM style?

## Sub-questions

1. The full Baumler result and its replications/neighbors: what exactly drifts (lexical,
   syntactic, rhythm), how fast, and does awareness of the effect reduce it?
2. Direction of workflow: does human-writes-then-machine-polishes drift less than
   machine-drafts-then-human-edits? Any measured comparison?
3. Diversity preservation: interventions shown to maintain stylistic variance
   (exemplar rotation, deliberate register mixing, constraint randomization) — anything
   measured, anywhere (style transfer, MT post-editing, creative-writing tools)?
4. Machine-translation post-editing literature (the oldest post-editing field):
   measured "post-editese" effects and the countermeasures that worked — what transfers?
5. Calibration mechanics: how to run the blind A/B (author's unassisted paragraph vs
   melded) so it yields usable signal at n=1 author — protocol, frequency, ordering
   effects.

## Method

Corpus first (`research/01` for Baumler, `research/00-SYNTHESIS.md`, `research/06` for
authorship measurement), then web research: post-editese in MT, human-AI co-writing
studies, style-diversity measurement. Report effect sizes and study quality.

## Deliverable and gate

`research/14-postediting-voice-drift.md`: what drifts and how fast; a ranked list of
countermeasures with their evidence class; concrete recommendations for dial 7–10
behavior and the anchor-pool composition; the blind A/B protocol spec. Gate: §8 and the
§5 calibration paragraph can be revised directly from it.
