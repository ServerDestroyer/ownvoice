# T4-prep — stand-in material bundle (solo, done 2026-08-31)

**Objective:** build everything T4 (`steps/B3-dry-run.md`) needs that is not Chris's
time, so the dry run can start the day T3 finishes. Not a measurement step — no numbers
here belong to T4.

## What exists now

`intake/standin/` — a complete, synthetic intake bundle (README in the directory):

- `paper/paper.md` — three sections. Two contrasting for the arc-batched arm
  (`why-modelled-comfort-and-reported-comfort-diverge`, argumentative;
  `measurement-protocol`, procedural) and one for the serial control
  (`what-the-evidence-base-cannot-yet-settle`, argumentative).
- `sources/` — five invented works; `alvarez2019` and `dimitrova2020` carry
  `*.locators.json` sidecars, the other three deliberately do not.
- `template/standin-template.md` — section order, per-section requirements, section
  **types**, and which sections are the batched pair vs the serial control.
- `author-corpus/` — empty by design; fills from the T3 anchors. This is the one
  remaining `intake_check` gap and it is the correct one.

Deliberate citation defects, all confirmed landing where they should:
`(Whitfield, 2017)` and `Nakamura & Ellis (2016)` unresolvable → holds with ranked
candidates; `(see pretorius2018.md line 412)` a private line-number citation (the
Paper 007 "Kelley markdown line N" defect class); three sources without sidecars →
`needs_mapping: true`; `(Okafor, 2022a)` for the letter-suffixed year.

State from the prepass run is in `runs/t4/state/` (6/9 resolved, 3 holds).

## Three defects found by building it — all fixed

1. **B0 rejected a correctly-prepared B5 bundle.** `intake_check.py` flagged every
   non-markdown file as an unconverted input, so the `*.locators.json` sidecars that
   `prepass.py` reads (and that P-5 committee-verifiable locators depend on) made G0
   fail. Sidecars are now exempt; `scan.pdf` still fails, pinned in the selftest.
   This would have fired at T6 on the real paper.
2. **Narrative citations were never extracted.** `CITE_RE` matched only the
   parenthetical `(Author, 2020)` form; `Alvarez (2019) found ...` — as common as the
   parenthetical form in real papers — reached neither the ledger nor the holds report,
   so an ungrounded narrative claim was silently invisible to the gate that exists to
   catch it. On the stand-in paper this was 3 of 9 citations. Root cause was two
   layers: no narrative pattern, and the sentence splitter cut `Nakamura et al. (2019)`
   in half at the `al.` period. Both fixed, both pinned in `prepass.selftest`, and the
   T2 gate fixture now uses both citation forms (gate re-run: **PASS**, unchanged).
3. **The production path ran the weakest guard available.** `tock.py` calls
   `guard(skeleton, draft, sources)`, and the defaults were witness off, entailment
   off — so neither layer T1/T1b measured was ever active outside the benchmark.
   Defaults are now resolved, not hardcoded: the witness is on wherever an
   `OPENROUTER_API_KEY` exists (`OWNVOICE_WITNESS=0` forces it off), and MiniCheck is
   on iff its weights are already in `.models/` — it never triggers a download
   (`OWNVOICE_ENTAIL=none` forces it off). Selftests pin both off and stay offline.

**Verification:** `intake_check --selftest`, `prepass --selftest`, `guard --selftest`
all pass; `gate_prepass.py` (T2) PASS; `bench_guard.py --witness --entailment minicheck`
re-run end to end (4m40s) reproduces T1b exactly — out-of-lexicon hedge recall 1.00,
TRUE-PARAPHRASE false positives 0.00, all four thresholded classes PASS. Live guard on
a one-sentence pair shows the witness catching an out-of-lexicon hedge drop by default
and entailment no longer in `not_checked`.

## Watch at T6

- The ledger's locator is the **first** source paragraph containing surname + year. In
  the stand-in that was originally the markdown H1, which pointed the locator at the
  cover; the titles were shortened so it lands on the reference line. Real source
  markdown often carries the year in its title, so expect some Paper 007 locators to
  point at a title and need re-grounding by hand. Not fixed — ranking source paragraphs
  by match strength is a change to the prepass that should be made against real
  material, not invented material.
- The witness now runs on every guard call, including one per meld candidate. Cost per
  section was never measured (T1b measured ~$0.005 per 30-paragraph benchmark). T4
  should record it; if a six-arm sweep is expensive, cache scope is the knob.
