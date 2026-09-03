# Stet

*stet* — the proofreader's mark meaning **let it stand**.

Stet walks a long-form paper, section by section, from machine-written prose into prose
a human wants to read, in the author's own voice — while proving the meaning did not
change. Your meaning stands. The writing gets your voice back.

It is generic across any templated long-form document — dissertation, thesis, grant
proposal, journal article. The per-paper template is the mandatory spine that keeps the
work from drifting.

**This is not detector evasion.** Detector and voice scores are used only to order
candidate rewrites; they never open a gate and are never optimisation targets. The
author is the sole meaning authority, and no section is finished until the author says
so.

## The problem it solves

Ask any model to "improve" a paragraph and it will quietly change what you claimed.
Measured, in the research this design is built from: rewriting inflates certainty by
37–75%, and 16–27% of correct content regresses. "May contribute" becomes
"contributes". An attribution disappears. A negation flips. The text reads better and
says something you did not mean.

Stet's answer is not a better prompt. It is a gate:

1. The author locks a **meaning skeleton** for each section — the claims it must carry.
2. Prose is generated **from that skeleton**, never by editing a previous draft, so
   errors cannot compound across retries.
3. A **meaning guard** diffs the prose against the locked claims and reports every
   dropped hedge, dropped attribution, flipped polarity, added booster, missing
   citation and unsupported number.
4. The **polisher** rewrites each paragraph toward samples of the author's own writing,
   one paragraph at a time.
5. The **author** reviews with the guard's findings in front of them, and approves.

## Install

Core requires **Python 3.13** (the only version tested) and **nothing else** — the
pipeline is standard library only. Clone and verify:

```bash
git clone <this repo> stet && cd stet
for t in intake_check prepass setup_paper board meld guard tock tick learnings; do
  python3 tools/$t.py --selftest
done
python3 tools/gate_prepass.py     # end-to-end citation-grounding gate
```

All nine should print `selftest ok`.

### The polisher (needed to rewrite anything)

The polisher calls [OpenRouter](https://openrouter.ai). Copy `.env.example` to `.env`
and set `OPENROUTER_API_KEY`. The frozen configuration lives in `tools/meld-v1.json`.

Measured cost at the frozen model: about **$0.0005 per paragraph**, so a typical
section runs to a few cents.

### Optional: the two heavy guard layers

The guard has three layers. The lexicon layer is stdlib and always on. Two more are
optional:

```bash
python3 -m venv .venv
.venv/bin/pip install "factwash @ git+https://github.com/collapseindex/factwash"
.venv/bin/pip install "minicheck @ git+https://github.com/Liyan06/MiniCheck"
```

MiniCheck pulls torch and transformers, and downloads roughly **5.9 GB** of model
weights into `.models/` on first use.

**Without them nothing silently passes.** The guard reports those layers as
`not_checked` in every report, so you always know what was and was not verified. That
is the design rule: a report listing only what it found would read as "nothing else
happened".

If you install them, run tools with `.venv/bin/python`. On NixOS use the bundled
`tools/py` wrapper instead — it sets the library paths that manylinux wheels need
there, and it is useful on that platform only.

## Try it in five minutes

Synthetic material ships with the repo, so you can watch the whole loop before
supplying a paper of your own. It contains deliberately broken citations, so you also
see the grounding gate do its job.

```bash
mkdir -p my-anchors        # 2-4 paragraphs of YOUR OWN writing, one file each
python3 tools/setup_paper.py --intake intake/standin --work runs/demo --anchors my-anchors
python3 tools/board.py --state runs/demo/state
```

Everything in `intake/standin/` is invented — the paper, all five cited works, every
citation. It is scaffolding for exercising the pipeline, not scholarship.

## Using it on your own paper

Build an intake directory with four parts, all markdown, no spaces in filenames:

```text
intake/<paper>/
  paper/           your paper, as it currently stands
  sources/         every cited work as markdown (+ optional <name>.locators.json
                   mapping paragraph index -> published page/section)
  template/        section order, per-section requirements, and per-section
                   id / type / arc  (see below)
  author-corpus/   your own writing — the voice the polisher aims at
```

Every template section must carry three lines, because routing is by declared type and
never by a score:

```markdown
## 1. Introduction
- **id:** `introduction`
- **type:** argumentative      # or procedural / administrative / boilerplate
- **arc:** 1                   # 3-5 consecutive sections per arc
- **requirements:** what this section must establish.
```

Then the loop, one arc at a time:

```bash
python3 tools/setup_paper.py --intake intake/<paper> --work runs/<paper> --anchors <dir>
python3 tools/tock.py --state runs/<paper>/state          # machine: skeleton, draft, guard, polish
python3 tools/tick.py --state runs/<paper>/state --arc 1  # you: verify, adjudicate, approve
```

`tock` is the machine half and runs unattended between sittings. `tick` is yours and is
interactive — it verifies meaning for the next arc, adjudicates unresolved citations,
and puts finished prose in front of you with the guard's findings attached. Sittings are
capped at 90 minutes and blocks at 50, because review quality collapses past that.

## What the guard gates, and what it only reports

**Blocks the section:** a missing claim, a missing or invented citation, an invented
number, or a citation you cut reappearing in the prose. Omission and fabrication.

**Reported as warnings for your judgement:** dropped hedges and attributions, reversed
polarity, added boosters, unalignable sentences, entailment failures. These classes were
measured on sentence-for-sentence rewrites, and drafting from a skeleton legitimately
restructures sentences, so they carry false positives — but you see every one of them at
approval time, with the cue and the claim it belongs to.

The guard's detection is measured, not asserted: `tools/bench_guard.py` runs a 30-seed
library with per-class acceptance floors. See `steps/T1-guard-benchmark.md` and
`steps/T1b-witness-measurement.md`.

## Honest limitations

- **Voice has a ceiling.** Prompt-based voice transfer plateaus well below human
  authorship scores. The promise is *clean prose that sounds more like you*, not
  indistinguishable authorship. It improves as your corpus of hand-edits grows.
- **Voice metrics need a corpus.** Below roughly 50,000 words and 40 documents they run
  trend-only. Stet says so instead of reporting a confident number.
- **A topic-mismatched anchor transplants sentence shapes**, not just tone. Anchor
  leakage is measured per candidate, and it is one of the things worth your eye.
- **It has never processed a real paper.** The pipeline is verified end to end on
  synthetic material, the guard is benchmarked, and the interactive sitting has been
  smoke-tested — but no complete real paper has gone through it yet.

## Repository

- `DESIGN.md` — the normative spec: gates G0–G7, invariants I1–I8, the state machine.
- `BUILD.md` — the working board, frozen decisions, and the adjustment log.
- `steps/` — one record per build and test step, including the measured benchmarks.
- `tools/` — the CLI. Every tool has `--selftest`.
- `.claude/skills/walkthrough/` — a [Claude Code](https://claude.com/claude-code) skill
  that drives the loop conversationally. Optional; the CLI is complete without it.
- `reviews/`, `spikes/` — the adversarial design review and four research spikes.

Stet is designed to be adjusted while in use. When something is wrong in a real
session: fix it, add the test that would have caught it, and log it in BUILD.md. Any
change that loosens a gate must re-run the benchmark before it counts.
