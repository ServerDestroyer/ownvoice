# T2 — Prepass gate (record)

**Date:** 2026-08-31 · **Spec:** [steps/B5-grounding-prepass.md](B5-grounding-prepass.md) gate section · **Runner:** `python3 tools/gate_prepass.py` (writes its fixture + state under `runs/t2/`, gitignored)

## Setup

Deterministic synthetic set written by the gate script itself (`runs/t2/`): a 4-section
paper with **20 distinct citations** (22 instances — two repeats across sections), 15
source files, 5 of them with `.locators.json` committee-verifiable maps. The 5
seeded-broken citations were chosen to stress distinct failure shapes, not just
absence:

1. `(Vance, 2016)` — author absent everywhere; year collides with tanaka2016.
2. `(Okonkwo, 2018)` — **wrong-year near-miss**: the corpus contains Okonkwo (2014),
   mentioned inside adeyemi2015.md.
3. `(Marsh et al., 2022)` — **topical near-miss**: citing sentence matches
   moreau2022.md's subject (deliberation quality metrics) but the work doesn't exist.
4. `field-notes.md line 40` — degenerate private line reference (the P-5 violation).
5. `(Ito, 2025)` — absent author, plausible recent year.

Resolvable set covers the harder citation forms: `et al.`, `&`-joined authors, and a
`2020a` year suffix.

## Results — gate PASS, no defects found

- **Resolution 20/20 correct**: all 15 resolvable citations resolve to the right
  source file; all 5 seeded-broken land in holds; no false resolution (including the
  Okonkwo wrong-year and Marsh topical near-misses).
- **Locators correct**: the 5 mapped sources return their published locator
  (`p. 3`, `pp. 112-114`, `sec. 4.2`, …) with `needs_mapping: false`; unmapped sources
  correctly flag `needs_mapping: true`. No private line numbers leak.
- **Sections correct**: repeated citations accumulate their section lists
  (Smithers → intro+background, Jonquil → intro+results).
- **Holds candidates**: every hold has 3 candidates. Where a near-miss exists the
  right passage ranks: moreau2022 ¶0 is Marsh's top candidate, and Okonkwo's top
  candidate is the adeyemi2015 paragraph that actually cites Okonkwo (2014) — exactly
  what an author needs to fix the year. Where the citation is truly absent (Vance,
  Ito, the degenerate ref), candidates are year-token noise — acceptable: the report
  is honest that nothing close exists.
- **Fan-out correct**: `--mark-bad jonquil2019.md` marks exactly `intro` and
  `results` GROUNDING_STALE on the board.
- **Runtime**: <0.01 s for the full prepass on 20 citations / 15 sources.
  At Paper-007 scale (33 citations) runtime is a non-issue.

## Observation (not a defect)

For holds with topic-free citing sentences, BM25 candidates degrade to year-token
matches. If real papers produce noisy holds, the fix is to widen the query window from
one sentence to the surrounding paragraph — not needed on this evidence.
