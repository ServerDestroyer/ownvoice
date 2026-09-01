# B1 — Meld session: freeze meld v1

**Objective:** find the winning (model, prompt, temperature) for the meld and freeze it
as `tools/meld-v1.json`, with regression triples.

**Needs from Chris (collect at session start):**
- Repo-root `.env` (copy from `.env.example`, gitignored): `OPENROUTER_API_KEY`
  plus the run config — MELD_MODEL, MELD_TEMPERATURE, MELD_ARMS, MELD_OUT,
  MELD_DRAFT, MELD_ANCHOR. CLI flags override. Only live calls need the key —
  selftest/dry-run/blind run without it.
- 2–4 anchor paragraphs of Chris's own writing (note each: written or spoken
  transcript), any topic. Save to `runs/b1/anchors/anchor1.md` etc. These serve both
  anchor conditions (see `runs/b1/anchors/README.md`): unmatched against
  `runs/b1/draft.md` (staged), and matched against machine drafts generated on each
  anchor's own topic and form (`runs/b1/draft-matched-N.md`, generated solo once the
  anchors exist).
- Model ids verified live 2026-09-01 (see the probe table below).

**Chris's method, recorded 2026-09-01 (the humanizing polisher, arm 0 in
`tools/meld_seeds.json`):** one human paragraph of similar form and topic, one AI
paragraph, the prompt verbatim, thinking off (or lowest), temperature ~0.2, one
paragraph at a time; titles, subsections, boxes, forms and diagrams never go through
(`meld.is_prose`). The harness now defaults to all of this. It is the interim
production arm until this session freezes meld-v1.

**Thinking-off probe (2026-09-01, one paragraph each, `runs/b1/thinking-probe.json`):**

| model | thinking sent | reasoning tokens | temperature | cost/para |
|---|---|---|---|---|
| google/gemini-3.1-pro-preview | `effort: low` (thinking is **mandatory** on OpenRouter; cannot go lower) | **814** | yes | $0.0107 |
| openai/gpt-5.6-terra-pro | `effort: none` | 0 | **not supported** | $0.0061 |
| deepseek/deepseek-v4-pro-0813 | `enabled: false` | 0 | yes | $0.0004 |
| x-ai/grok-4.3 | `effort: none` | 0 | yes | $0.0004 |
| thinkingmachines/inkling | `effort: none` | 0 | yes | $0.0005 |
| qwen/qwen3.7-max | `effort: none` | 0 | yes | $0.0005 |
| moonshotai/kimi-k3 | `enabled: false` | 0 | yes | $0.0013 |
| mistralai/mistral-medium-3-5 | `effort: none` | 0 | yes | $0.0006 |

Gemini 3.1 Pro cannot satisfy Chris's spec on OpenRouter: it thought for 814 tokens to
produce 48, and its output added hedging ("is observed to be associated"). No newer
Google Pro model is listed. Everything below the first row meets the spec.

**Output-perplexity probe (2026-09-01, GPT-2 as reference LM, 3 paragraphs per model,
same anchor, thinking off, T=0.2; `runs/b1/ppl-probe.json`):** qwen3.7-max 145.9 ·
gpt-5.6-terra-pro 137.1 · kimi-k3 131.3 · gemini-3.1-pro 124.8 · mistral-medium-3-5
117.2 · deepseek-v4-pro-0813 110.3 · grok-4.3 96.3 · inkling 76.8 (unpolished drafts
121.7). Direction only — the within-model spread is wider than the between-model gaps.

**Chris's decision 2026-09-01: `qwen/qwen3.7-max` is the polisher default** (highest
perplexity, thinking off, temperature honoured, $0.0005/paragraph). Challengers for this
sitting: **kimi-k3** and **deepseek-v4-pro-0813** (distinct engines, meet the spec) plus
**gemini-3.1-pro-preview** as the prior reference. The blind ranking can still overturn
the default — that is what the sitting is for. Observation, not a measurement: with the probe's
topic-matched anchor, five of eight outputs pulled a phrase from the anchor ("repeatedly
described in the literature as a discrete event") and one attributed the draft's claim
to the anchor's author — exactly the leak research/11 warned of, and exactly what
`leak_vs_anchor` and the guard's attribution check exist to catch.

**Procedure:**
1. `python3 tools/meld.py --selftest`, then `--dry-run` with the real files; eyeball
   the assembled prompts.
2. Run all 7 arms × the draft paragraphs on the default model:
   `python3 tools/meld.py --draft runs/b1/draft.md --anchor runs/b1/anchors/anchor1.md --out runs/b1/qwen`
3. Repeat for the challengers through the same harness (`--model moonshotai/kimi-k3`,
   `--model deepseek/deepseek-v4-pro-0813`, `--model google/gemini-3.1-pro-preview`;
   distinct engines resist homogenisation, research/14).
4. Matched-anchor condition: for each anchor, run the same arms with
   `--draft runs/b1/draft-matched-N.md --anchor runs/b1/anchors/anchorN.md --out runs/b1/<model>-matched`.
   The blind ranking decides between matched and unmatched — do not assume either.
5. Check `results.jsonl` diagnostics: `leak_vs_anchor` high → arm is copying the
   anchor (discard); `copy_vs_draft` ≈ 1.0 → arm did nothing; `reasoning_tokens`
   must be 0 (or the model's floor) — thinking on is a different arm, not noise.
6. `python3 tools/meld.py --blind runs/b1/gemini` (and per model dir). Chris ranks in
   `blind_sheet.md` WITHOUT opening `key.json`. The unmelded draft is hidden in each
   set — if it doesn't rank last, the arms are not earning their cost.
7. Unblind, tally, pick winner. Do NOT iterate on prompt wording beyond the seed arms —
   prompt elaboration measures below the do-nothing baseline (research/11).
8. Freeze: write `tools/meld-v1.json` {model, arm_id, temperature, thinking,
   anchor_match: matched|unmatched, date}; copy the 3–5 best (draft, anchor, output)
   rows into `tools/regression/` as named .json files. If **matched** wins, the
   anchor picker (select the author paragraph by form + topic from the corpus) becomes
   a build item before T4; if unmatched wins, `state/anchors/` stays as designed.

**Gate:** winner beats the unmelded baseline in Chris's blind ranking; leakage columns
clean; meld-v1.json + regression triples committed.

**Record in BUILD.md:** winner, blind-rank tally, any arm that failed the leakage check,
whether the known-bad control was detected.
