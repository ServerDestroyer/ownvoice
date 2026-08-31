# B5 — Grounding prepass tooling

**Objective:** the one-time, whole-paper grounding pass (DESIGN.md §4 "Grounding
prepass") as `tools/prepass.py`. Can run before or in parallel with B3/B4 — it has no
dependency on the meld or the skill.

**Build:**
1. **Citation extractor** — pull every in-text citation from the paper markdown
   (patterns incl. `(Author, Year)`, `(Author et al., Year)`, and degenerate forms like
   "X markdown line N").
2. **Source-search index** — BM25 over the markdown sources (stdlib-ish: a small
   tokenizer + BM25 is ~60 lines; no vector DB, no RAG framework — DESIGN §7.4 scope).
   Used to resolve citations AND to surface candidate passages for broken ones.
3. **Grounding ledger** — `state/grounding-ledger.json`:
   `citation -> {locator, resolves: bool, source, sections[]}`. Locators must map to
   committee-verifiable positions (page/section of the published source, via the
   per-source mapping notes required by the intake README) — never private markdown
   line numbers (P-5).
4. **Fan-out** — given a source marked bad, mark every citing section
   `GROUNDING_STALE` on the board.
5. **Holds report** — human-readable list of unresolvable citations, each with its top-3
   candidate passages, for the author's tick-A holds block.

**Gate:** runs end to end on sample sources: a synthetic paper with ~20 citations of
which 5 are seeded-broken → all 15 resolve with correct locators, all 5 land in the
holds report with sensible candidates, fan-out marks the right sections. `--selftest`
covers extractor and BM25.

**Record in BUILD.md:** resolution accuracy on the synthetic set; runtime on the sample.
