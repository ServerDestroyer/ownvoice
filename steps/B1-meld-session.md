# B1 — Meld session: freeze meld v1

**Objective:** find the winning (model, prompt, temperature) for the meld and freeze it
as `tools/meld-v1.json`, with regression triples.

**Needs from Chris (collect at session start):**
- `OPENROUTER_API_KEY=sk-...` dropped in the repo-root `.env` (gitignored; env var
  also works). Only live calls need it — selftest/dry-run/blind run without it.
- 2–4 anchor paragraphs of Chris's own writing (note each: written or spoken
  transcript). Save to `runs/b1/anchors/anchor1.md` etc. NOT topic-matched to the
  draft — topic-matched anchors measurably hurt (research/11).
- 5+ machine-drafted paragraphs to meld (any LLM output in academic register). Save to
  `runs/b1/draft.md`, blank-line separated.
- Confirmed OpenRouter model id for Gemini 3.1 Pro (default guess in meld.py is
  `google/gemini-3.1-pro` — verify against openrouter.ai/models before spending calls).

**Procedure:**
1. `python3 tools/meld.py --selftest`, then `--dry-run` with the real files; eyeball
   the assembled prompts.
2. Run all 6 arms × the draft paragraphs on Gemini 3.1 Pro:
   `python3 tools/meld.py --draft runs/b1/draft.md --anchor runs/b1/anchors/anchor1.md --model <id> --out runs/b1/gemini`
3. Repeat for 1–2 challenger models through the same harness (Chris picks; at least one
   non-Google engine — two architecturally distinct engines resist homogenisation,
   research/14).
4. Known-bad control: one run with a deliberately topic-matched anchor; the harness
   must show it ranking worse. If it doesn't, distrust the whole ranking.
5. Check `results.jsonl` leakage columns: `leak_vs_anchor` high → arm is copying the
   anchor (discard); `copy_vs_draft` ≈ 1.0 → arm did nothing.
6. `python3 tools/meld.py --blind runs/b1/gemini` (and per model dir). Chris ranks in
   `blind_sheet.md` WITHOUT opening `key.json`. The unmelded draft is hidden in each
   set — if it doesn't rank last, the arms are not earning their cost.
7. Unblind, tally, pick winner. Do NOT iterate on prompt wording beyond the seed arms —
   prompt elaboration measures below the do-nothing baseline (research/11).
8. Freeze: write `tools/meld-v1.json` {model, arm_id, temperature, date}; copy the 3–5
   best (draft, anchor, output) rows into `tools/regression/` as named .json files.

**Gate:** winner beats the unmelded baseline in Chris's blind ranking; leakage columns
clean; meld-v1.json + regression triples committed.

**Record in BUILD.md:** winner, blind-rank tally, any arm that failed the leakage check,
whether the known-bad control was detected.
