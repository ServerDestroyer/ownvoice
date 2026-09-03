# intake/standin — worked example, for exercising the pipeline

The paper, all five cited works, and the template here are **synthetic**: written so the
pipeline can be run end to end without a real manuscript. No cited work exists. Nothing
here is scholarship — do not quote any of it anywhere.

**One exception, and it is not synthetic.** `author-corpus/` holds a real document by a
real person (the DAGS whitepaper, Christopher Colantuono, 2019), because the polisher
needs genuine human writing to aim at and invented prose would defeat the point.
**Replace it with your own writing before using this as a template for your paper** —
otherwise the polisher is rewriting toward someone else's voice, which is precisely the
failure the tool exists to prevent.

| Part | What it is |
|------|------------|
| `paper/paper.md` | three sections — two contrasting (argumentative + procedural) for the arc-batched arm, one argumentative for the serial control |
| `sources/` | five source works; two carry `*.locators.json` sidecars (committee-verifiable page/section), three deliberately do not, so the ledger's `needs_mapping` path is exercised |
| `template/standin-template.md` | section order, per-section requirements, section **types** (routing is by type, never by score) |
| `author-corpus/` | one real document by a real author — see the note above; replace it with your own |

## Deliberate defects (do not "fix" them — they are the test)

1. **`(Whitfield, 2017)`** and **`(Nakamura & Ellis, 2016)`** resolve to nothing. They
   must land in `state/holds-report.md` with ranked candidate passages.
2. **`(see pretorius2018.md line 412)`** is a private line-number citation with no
   published locator — a citation only its author can check. The grounder must hold it
   for re-grounding to a page or section a reader could verify.
3. **Three sources have no locator sidecar**, so their ledger entries must carry
   `needs_mapping: true` rather than a bare paragraph number (DESIGN P-5).
4. `(Okafor, 2022a)` exercises the letter-suffixed year form.

Seeded prose defects for the review sittings are *not* pre-injected here: `tick.py`
injects them from `tools/seeds/` at run time. Knowing that defects are present, without
knowing which items carry them, is what keeps a review from becoming a rubber stamp.
