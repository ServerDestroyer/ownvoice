# T3 — the polisher sitting (Chris, ~1 h)

The machine half ran 2026-09-01 (round 2; round 1 is archived under
`runs/b1/round1-sameclaims/` — its matched drafts carried the anchors' own claims, so
several models simply returned the anchor; not rankable). What is left is your ear.

**Setup that produced the sheets:** 7 arms (your humanizing-polisher + 6 research
arms) × 4 models (qwen3.7-max default; kimi-k3, deepseek-v4-pro-0813,
gemini-3.1-pro-preview challengers) × 2 anchor conditions, thinking off, T=0.2,
one paragraph per call. Unmatched = three thermal-comfort paragraphs with anchor 1.
Matched = for each of anchors 1–3, a machine paragraph on the same topic and form
whose claims come from the *neighbouring* whitepaper paragraph. 168 rows, no errors,
`runs/b1/round2-all-rows.json`.

## Stage A — which prompt (Qwen only, 48 candidates, ~40 min)

Open these four files and write a number in every `(rank: __ )`, 1 = best. Rank by
ear: does it read like you, and does it read well. Do **not** open any `key.json`.

- `runs/b1/qwen/blind_sheet.md` — unmatched, 3 paragraphs × 8 candidates
- `runs/b1/qwen-matched-1/blind_sheet.md` — matched, anchor 1, 8 candidates
- `runs/b1/qwen-matched-2/blind_sheet.md` — matched, anchor 2, 8 candidates
- `runs/b1/qwen-matched-3/blind_sheet.md` — matched, anchor 3, 8 candidates

Each set hides the unpolished draft among the candidates. If it does not rank last,
say so — that arm set is not earning its cost.

Then:

```
python3 tools/meld.py --tally runs/b1/qwen,runs/b1/qwen-matched-1,runs/b1/qwen-matched-2,runs/b1/qwen-matched-3
```

That prints mean rank per arm. Note the winner, and whether matched or unmatched
sheets read better.

## Stage B — which model (winning arm only, ~32 candidates, ~20 min)

```
python3 tools/meld.py --blind runs/b1/qwen,runs/b1/kimi,runs/b1/deepseek,runs/b1/gemini --arms <WINNER> --out runs/b1/stageB
python3 tools/meld.py --blind runs/b1/qwen-matched-1,runs/b1/kimi-matched-1,runs/b1/deepseek-matched-1,runs/b1/gemini-matched-1 --arms <WINNER> --out runs/b1/stageB-matched-1
```

(repeat for matched-2 and -3 if you have time; one is enough for direction). Rank the
same way, then `--tally` the stageB dirs.

## Freeze

Winner = (arm, model, matched|unmatched). I write `tools/meld-v1.json`, copy the 3–5
best (draft, anchor, output) rows into `tools/regression/`, record the tally in
BUILD.md, and — if matched wins — the anchor picker goes on the build board before T4.

## What the diagnostics already say (read after ranking, not before)

Leak (`leak_vs_anchor`) = share of the output's word-trigrams that come from your
anchor; copy (`copy_vs_draft`) = share that come from the draft. Length = output
words / draft words.

- Your arm on Qwen: matched leak 0.09 / copy 0.39 / length 121%; unmatched leak 0.19
  / copy 0.30 / length 150%. It rewrites, it does not copy either input, and it grows
  the text — 50% longer when the anchor is off-topic.
- **Deepseek returned the draft unchanged** for your arm in the matched condition
  (copy 1.00) and for roleplay-lip unmatched (0.90). Kimi likewise for continuation
  matched (0.96). "Did nothing" is a real failure mode for the short prompt on some
  engines.
- **Snippet-seeded copies the anchor** on deepseek and gemini (leak ~0.5): discard
  that arm regardless of ear.
- Gemini alone spent reasoning tokens (700–1300 per paragraph): thinking cannot be
  turned off there.
- No output carried a preface or disclaimer (0 of 168).
