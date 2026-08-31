# B3 — Manual dry run with comparison arm

**Objective:** prove the arc loop by hand before any orchestration code, and produce
the only batch-vs-serial measurement that will ever exist (no literature covers it —
research/13). Needs Chris throughout. Prereqs: B1 (meld v1) and B2 (guard stack).

**Material:** three sections of stand-in academic text (NOT Paper 007): two
contrasting — one argumentative, one procedural — for the arc-batched run, one for the
serial control. Chris acts as the author.

**Procedure (follow DESIGN.md §4 stages literally, by hand, state in files under
`runs/b3/sections/<id>/`):**
1. **Batched arm (2 sections):** extract both TL;DR skeletons → Chris verifies both
   side-by-side in one sitting (tick A; per-item marks, item-specific questions) →
   ground claims → draft from skeleton (I1: generator never sees old draft) → run
   `tools/guard.py` → meld via meld-v1 → guard again → Chris reviews both in one
   approval sitting (tick B).
2. **Serial control (1 section):** same stages, but one section end-to-end in one
   sitting, interleaved.
3. Inject 2–3 seeded defects from `tools/seeds/` into the review material without
   telling Chris which items (tell him they exist — that's the mechanic).
4. Respect the caps: ≤3 regenerations/span, ≤2 skeleton reopens; amended skeleton items
   re-ground before redrafting (I3).

**Record (this is the point — measure, don't vibe):** author minutes per stage; amend
rate at G2; seeded-defect catch rate; G2 reopen rate; tick durations vs DESIGN's
estimates; **count of cross-section findings Chris caught only because the two
skeletons/drafts sat side-by-side** — if zero, arc batching loses its justification and
B4 must reconsider the serial loop. Keep every (draft, Chris-edit) pair — first
hand-edit corpus entries. Capture proposed learnings + Chris's ratifications.

**Gate:** both batched sections approved by Chris; all numbers above recorded in
`runs/b3/measurements.md`; loop shape confirmed or amendments to DESIGN §4 written.

**Record in BUILD.md:** the measurement summary and any DESIGN amendments.
