# U1 — first end-to-end pass (2026-09-01/02)

**What it was for:** run one paper through every stage in order — intake gate,
citation grounder, section setup, skeleton, draft, meaning guard, humanizing polisher,
guard again, review-ready — and fix whatever broke. No staged test sessions: Chris
cancelled T3's ranking sitting and the T4 dry run, so this is the whole verification
before real use.

**Material:** `intake/standin/` (synthetic, built at T4-prep), anchors from the DAGS
whitepaper. Final run: `runs/standin2/`. The author's two decision points (locking
meaning, adjudicating holds) were simulated in a script, not performed by Chris.

## Result

Both argumentative sections reach REVIEW_READY on the **first attempt, zero retries**.
The procedural section takes the light path (SKIM) by template type. Draft guards PASS
with 1–2 warnings each. In both sections one polished candidate survived and the other
was correctly failed on a real gated class — a missing citation and a missing claim —
so the gate is doing work, not rubber-stamping.

Before the fixes below, the same material took 4 regenerations per section, hit the I5
cap, and parked with 11–16 guard failures per draft.

**Measurement unmoved:** `bench_guard --witness --entailment minicheck` reproduces T1
and T1b exactly — POLARITY-FLIP 1.00, CONDITION-DROP 1.00, HEDGE-DROP-IN-LEX 1.00,
TRUE-PARAPHRASE false positives 0.00, out-of-lexicon 1.00, 7 seeds entailment-vetoed,
seed files byte-identical. All nine selftests and the T2 gate pass.

## What the first pass exposed (fixed on the way through)

1. **No step turned an intake into a walkable state tree.** Built `setup_paper.py`:
   one command runs G0 and G1, registers every section with its template type and arc,
   and writes `sections/<sid>/{original,template,grounded-sources}.md`.
2. **B0 rejected a correctly-prepared B5 bundle** — `intake_check` failed the
   `*.locators.json` sidecars `prepass` reads. Would have fired at the real paper.
3. **Narrative citations were never extracted** — `Alvarez (2019) found ...` reached
   neither ledger nor holds (3 of 9 citations on the stand-in). T2's fixture used only
   the parenthetical form, so its gate passed vacuously; it now uses both.
4. **A cut citation never cleared its hold**, so the section stayed parked forever.
5. **The guard judged every skeleton line a claim** — headers, jargon lists and
   template-compliance notes included.
6. **Omission and fabrication were measured against the same reference.** MISSING now
   measures against the skeleton, INVENTED against skeleton + sources, and "thirty"
   equals "30".
7. **A crash mid-pipeline orphaned the section**; tock now resumes from any
   mid-pipeline status.
8. **Retries were blind** — every regeneration repeated the same drift. Guard findings
   now return as constraints.
9. **Grounded sources held only each source's bibliographic line**, starving the
   drafter and making every sourced number read as fabricated.

## What the adversarial review then caught (23 confirmed, 1 refuted)

Six reviewers over the diff, each finding checked by two independent verifiers whose
default was to refute. Full output in the workflow transcript. The three that mattered
were all introduced by the fixes above:

- **`radius=1` reintroduced a documented known-bad configuration.** Widening the typed
  diff's count stage to ±1 is the exact setting T1 measured at in-lexicon hedge recall
  **0.17** against a 0.83 floor, and it was running on every draft. Reviewers
  reproduced it on all 30 seeds. It also fed the polarity and booster checks a
  three-sentence window and manufactured false REVERSED/ADDED findings. Worst of all it
  was unnecessary: the sentence-boundary float it claimed to fix is already handled by
  the identity stage against the ±1 `wide` window. **Removed entirely.**
- **The justification for demoting findings to warnings did not exist.** `MEANING_GATE`
  demotes every class except omission and fabrication, on the stated grounds that they
  "reach the author with the diff at G5". `tick.py` printed no guard findings at all,
  so they reached nobody. The sitting now prints the draft's guard report and each
  candidate's, with cues and the claim each belongs to.
- **I1 was breached twice, invisibly to `assert_no_prior_draft`** (which only compares
  whole paragraphs). Guard notes quoted prior-draft sentences into the next prompt on
  the polisher path; `grounded-sources.md` ended every block with a verbatim
  `Citing sentence:` from the author's existing prose, and tock hands that whole file
  to the drafter. Both closed and pinned by tests.

Also fixed, each with a test: **I4 deadlocked any paper with 3+ arcs** (SKIM is
terminal but counted as work in flight); **`setup_paper` erased the author's hold
adjudications** on every re-run; **I2 parked sections whose surviving candidates were
clean** (it demanded a PASS from failed candidates too); **a fully bold-emphasised main
point was deleted from the locked claim set**; **cut citations matched only the
parenthetical form**, so a cut narrative citation burned the section's three
regenerations; a cut citation is now **mechanically verified absent** from the prose
rather than merely requested in the prompt; `sentences()` no longer merges a sentence
ending in an acronym with the next, nor deletes an assertion written as a heading;
`template_sections` handles `###` nesting and rejects duplicate ids; `apply_gate`'s
test no longer passes vacuously.

## Also fixed in the author's sitting (`tick.py`, never previously run)

- Asked a question per skeleton **line**: 29 and 41 questions for sections with 8 and
  10 claims. Now 9 and 11, with the item-specific questions the design specifies
  (thesis, point, jargon, figure, requirement) instead of the same one every time.
- **Approval saved the wrong file.** Whatever the author typed, `approved.md` was
  written from `candidates.v1/cand-1.md` — the oldest superseded generation. The pick
  now resolves against the current version only and re-prompts if unrecognised.
- The 2-AFC calibration showed **the same text twice** as its catch trial and displayed
  the anchor's `<!-- written prose, 2019-08 ... -->` provenance header, which hands the
  author the answer. Both fixed; it also falls back to ranked candidates so calibration
  works on the first sitting.
- A regeneration cap hit during approval threw an uncaught invariant and ended the
  sitting. Now reported; the sitting continues.
- The paper pass `scan` ran silently, which reads as "nothing to do". It now reports.

## Known ceilings (not defects — recorded so they are not rediscovered)

- The certainty classes (hedge, attribution, condition, polarity, booster) are measured
  on sentence-for-sentence rewrites. Drafting from a skeleton restructures sentences,
  so they fire often on drafts and are warnings there. The author is the backstop, and
  that is now real. The polisher step, which IS a 1:1 rewrite, guards each paragraph
  against the draft paragraph it rewrote.
- `INVENTED number` certifies against the whole grounded-sources bundle, so any number
  appearing anywhere in a cited source counts as certified. Coarse by construction.
- The ledger locator is the first source paragraph containing surname + year; real
  sources with the year in their title will point at the cover and need re-grounding.
- The polisher transplants the anchor's sentence shapes when anchor and draft are on
  unrelated topics. Measured per candidate as `leak_vs_anchor` in `grades.json`, used
  to rank, never to gate.

## Still not exercised

`tick.py` has been read closely, unit-tested and corrected, but has **never run with a
human in front of it**. That is U2's first act.
