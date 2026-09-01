# intake/standin — development material for the dry run (T4)

Everything in this directory is **synthetic**. The paper, all five cited works, and the
template were written for OwnVoice development so the pipeline can be exercised end to
end without touching Paper 007. No cited work exists; do not quote any of it anywhere.

| Part | What it is |
|------|------------|
| `paper/paper.md` | three sections — two contrasting (argumentative + procedural) for the arc-batched arm, one argumentative for the serial control |
| `sources/` | five source works; two carry `*.locators.json` sidecars (committee-verifiable page/section), three deliberately do not, so the ledger's `needs_mapping` path is exercised |
| `template/standin-template.md` | section order, per-section requirements, section **types** (routing is by type, never by score) |
| `author-corpus/` | empty by design — fills from the T3 anchors; see its README |

## Deliberate defects (do not "fix" them — they are the test)

1. **`(Whitfield, 2017)`** and **`(Nakamura & Ellis, 2016)`** resolve to nothing. They
   must land in `state/holds-report.md` with ranked candidate passages.
2. **`(see pretorius2018.md line 412)`** is a private line-number citation with no
   published locator — the same defect class as Paper 007's 33 "Kelley markdown line N"
   citations. T4 rehearses the re-grounding that T6 must do for real.
3. **Three sources have no locator sidecar**, so their ledger entries must carry
   `needs_mapping: true` rather than a bare paragraph number (DESIGN P-5).
4. `(Okafor, 2022a)` exercises the letter-suffixed year form.

Seeded prose defects for the review sittings are *not* pre-injected here: `tick.py`
injects them from `tools/seeds/` at run time, which is the mechanic being measured.
