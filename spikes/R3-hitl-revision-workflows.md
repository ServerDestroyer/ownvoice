# Spike R3 — Human-in-the-loop long-document revision workflows

**Status:** complete (2026-08-31). **Reports to:** `research/13-hitl-revision-workflows.md`.
**Feeds:** DESIGN.md §4 (arc-pipelined model — attention economics), B3's measurement plan.

## Question

The arc-pipelined walkthrough rests on attention-economics claims that are currently
mechanism arguments, not measurements: batching meaning-verification is better than
serial per-section work; separating semantic judgment (meaning block) from aesthetic
judgment (approval block) reduces fatigue; ending sittings on finished work sustains
motivation; hard per-item marking prevents rubber-stamping. What does the empirical
literature actually say?

## Sub-questions

1. Batch vs interleaved review in human-computer workflows: measured effects on error
   detection, throughput, and fatigue (proofreading/annotation/code-review literatures).
2. Register/task-switching costs between evaluative modes (content correctness vs style
   judgment) — is the meaning-block/approval-block split supported?
3. Rubber-stamping and vigilance decrement in gated review (how fast does approval
   quality decay over consecutive items; what interface mechanics measurably counter it
   — forced per-item marking, blind items, attention checks)?
4. Mixed-initiative writing tools (Wordcraft, CoAuthor, academic-writing assistants):
   what interaction shapes did users sustain over long documents, and what was abandoned?
5. WIP limits and pipelining for a single human operator: any evidence for the ≤2-arcs
   bound, and for optimal batch size (the arc's ≤8 sections)?

## Method

Corpus first (`research/00-SYNTHESIS.md`, `research/04`, `research/09`, `research/10` —
oversight and reviewer-behavior findings), then web research across HCI/CSCW,
crowdsourcing-annotation, and code-review literatures. Prefer measured studies over
design essays; report effect sizes where they exist.

## Deliverable and gate

`research/13-hitl-revision-workflows.md`: verdict per §4 design claim
(supported / contradicted / unmeasured), recommended batch size and sitting structure
with evidence, the vigilance-decrement counter-mechanics worth encoding in the tick
script, and the specific measurements B3's dry run should record to validate locally.
Gate: B3's measurement plan can be written directly from it.
