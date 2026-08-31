# B6 — Acceptance: Paper 007

**Objective:** the product's first real run. Only now do Paper 007's assets enter.
Prereqs: B1–B5 all done. Needs Chris (and the paper's author) throughout — this runs
over multiple sessions, one arc per session, per the product's own design.

**Procedure:**
1. Chris drops the assets into `intake/paper-007/` per its README (paper markdown,
   sources incl. the Kelley markdown with line numbering intact, CTU template with
   section types, author corpus with word/doc counts).
2. `python3 tools/intake_check.py intake/paper-007` — resolve every blocking gap.
   Note whether the author corpus clears the 50k/40-doc floor; if not, voice metrics
   run trend-only and the promise is "clean, not yet the author" (DESIGN §3.4).
3. `tools/prepass.py` — full grounding prepass. Expect the 33 "Kelley markdown line N"
   citations to land in holds; re-ground them to committee-verifiable page/section
   locators using the Kelley markdown as the bridge. This is the paper's
   committee-fatal defect; it closes before any prose work.
4. Draw the arc map (3–5 sections/arc, template top-level divisions, argument threads).
   Build the 2-AFC calibration set (8–10 pairs) from the author corpus.
5. Walk the paper arc by arc through the skill — one arc per session. Ticks with the
   author; tocks between sessions.
6. Paper pass (G7): staleness drain, template compliance, cross-section checks.
7. Then the generality check: a second paper of a different kind (different template),
   even a short one, through the same pipeline unchanged.

**Gate:** Paper 007 approved by its author arc by arc; paper pass clean; the second
paper runs without code changes (config only). Deliverables: the finished paper
markdown, the harvested hand-edit pairs, the learnings store, and a retrospective note
in BUILD.md on what the design got wrong.

**Out of scope (separate project):** docx conversion of the finished markdown.
