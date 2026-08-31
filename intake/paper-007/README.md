# Intake — Paper 007

`intake/<paper>/` is the generic per-paper intake shape — every paper the walkthrough
processes gets a directory like this one. `paper-007` is the first acceptance case
(build step B6): its assets arrive **when the product is built**, not during
development, which runs on stand-in material.

Drop the four DESIGN.md §3 inputs here (all markdown; no spaces in filenames). The B0
intake check runs against this directory.

```text
intake/paper-007/
  paper/            the original paper markdown (chapter/section files as they were drafted)
  sources/          every cited work as markdown — INCLUDING the Kelley markdown that the
                    "Kelley markdown line NNNN" citations point at (keep its exact line
                    numbering intact; it is the only key to re-grounding those 33 citations)
  template/         the CTU template as markdown: section order, per-section requirements,
                    and each section's type (argumentative / procedural / administrative)
  author-corpus/    the author's own writing for the anchor pool — written pieces and any
                    spoken transcripts, one document per file
```

Notes:
- If a source exists only as PDF/docx, put it in `sources/` anyway and name the format;
  conversion becomes a named B0 gap.
- For each source markdown, keep (or add at top) a note mapping it to the published
  edition (title, edition, ISBN/DOI) so grounding locators can be committee-verifiable
  (page/section of the real source, per DESIGN.md P-5).
- `author-corpus/` files should note whether the text is written or spoken-transcript,
  and roughly when it was produced.
