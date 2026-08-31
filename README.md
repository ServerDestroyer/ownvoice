# OwnVoice

A human-in-the-loop system that takes a meaning-correct but machine-written paper and
walks it, section by section, into prose a human wants to read — in the author's own
voice — without corrupting its content. Generic across any templated long-form paper
(dissertation, thesis, proposal, journal article); the per-paper template is the
mandatory anti-drift spine.

**Not detector evasion.** Detector scores are used only as diagnostics to rank
candidates. The author is the sole meaning authority and the only judge that closes a
gate.

## Why it's shaped this way

Every design decision is constrained by a measured research corpus (ten dimensions plus
four follow-up spikes, summarized in the design doc). The load-bearing findings:

- Iterative rewriting compounds damage (certainty inflates 37–75%, 16–27% of correct
  content regresses) → every retry **regenerates from a human-verified meaning
  skeleton**, never edits a prior draft.
- Entailment checks are blind to dropped qualifiers ("may contribute" → "contributes")
  → a deterministic typed hedge/marker diff sits beside them in the guard stack.
- Prompt-based voice transfer ceilings at LUAR ~0.51; exemplar melding wins on
  human-likeness, not authorship metrics → honest promise: *clean now, the author's
  voice as the hand-edit pair corpus grows*.
- Authors cannot perceive voice drift in their own polished text (g=0.01 perceived vs
  g=−1.43 measured) → a 2-AFC blind identification test calibrates approval.
- Review quality collapses past ~50-minute blocks and side-by-side judgment is the
  non-decaying mode → arcs of 3–5 sections, batched meaning verification, comparative
  layouts, seeded defects.

## The loop in one paragraph

A paper enters through an intake contract (template, paper markdown, sources as
markdown, author corpus). A one-time grounding prepass resolves every citation. Then
arcs of 3–5 sections cycle through: the author verifies and extends each section's
**meaning skeleton** (tick A), the machine grounds, drafts, guard-checks, and melds in
bulk (tock), the author reviews finished prose (tick B). The **meld** — a single-pass
rewrite of each guard-passing paragraph conditioned on 1–2 exemplar paragraphs of the
author's own writing, via OpenRouter — is the voice engine. Hard gates, append-only;
approved text changes only through an author-accepted diff; a staleness ledger
propagates late-arriving rules backward as reviewable diffs, never silent rewrites.

## Repository layout

- [DESIGN.md](DESIGN.md) — the build charter (v2.1): principles, the arc-pipelined
  state machine, gates G0–G7, invariants I1–I8, guard stack, meld spec, learnings
  system, build order B0–B6.
- [reviews/](reviews/) — the adversarial review record (red team, blue team,
  adjudication) that produced v2.
- [spikes/](spikes/) — the four completed research-spike charters (R1–R4).
- [tools/](tools/) — working code:
  - `intake_check.py` — B0 intake validator (`python3 tools/intake_check.py
    intake/<paper>`; `--selftest`).
  - `meld.py` + `meld_seeds.json` — B1 meld harness: six documented seed arms, OpenRouter
    caller, leakage diagnostics, blind-ranking sheet generator (`--dry-run`,
    `--selftest`, `--blind <run_dir>`; key via `OPENROUTER_API_KEY`).
- [intake/](intake/) — per-paper intake directories (assets themselves are gitignored;
  the first acceptance case is `paper-007`).

The research corpus (406 papers, ~160 repos, dimension reports 01–14) lives in the
private Humanising-Realtime research workspace; DESIGN.md cites it as `research/NN`.

## Status

Design frozen at v2.1 (post-review, post-spikes). B0 and B1 tooling built and
self-tested. Next: the B1 meld session (reconstruct the system prompt, freeze
model+prompt as meld v1), then B2 (guard stack), B3 (manual dry run with comparison
arm), B4 (the walkthrough skill), B5 (grounding prepass), B6 (acceptance on Paper 007).
