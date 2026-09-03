# U2 — ship readiness, and what is still untested (2026-09-03)

The repo went public at **github.com/ServerDestroyer/ownvoice** (MIT). This record says
what was checked before that, what was fixed, and — more usefully — what is still not
verified. Read the last section before trusting anything here on a new machine.

## The audit

45 agents across five dimensions actually cloned the repo into scratch directories and
tried to become a new user: fresh-clone portability, machine-specific assumptions,
secrets and content, first-hour docs, and second-author assumptions. Every finding was
checked by two independent verifiers whose default was to refute. **10 confirmed
(5 blockers, 5 majors), 10 refuted.** All 10 confirmed are fixed.

### The one that mattered

Three findings converged on the same wound: **the polisher ran voiceless and nobody was
told.** With no anchors, `tock` still called the API for every paragraph, sending a
prompt that read "make this text … sound like the text from" followed by nothing — a
paid rewrite toward no one, producing plausible prose with no voice target at all. A new
user would have hit this immediately, because nothing turned the required
`author-corpus/` into anchors and `--anchors` accepted an empty directory in silence.

Now `setup_paper` exits when `--anchors` resolves to no files (and globs `*.md`, so the
corpus directory works directly as the source), and `tock` raises before the sweep
rather than spending the budget.

### The rest, fixed

- **`tools/py` exited 127 on any clone.** It exec'd `.venv/bin/python`, which is
  gitignored, and hardcoded two NixOS-only paths — for the exact command every doc
  prescribes. It now adds each `/run` path only if it exists and falls back to the
  system python. Verified on a copy of the working tree with no `.venv`.
- **The guard dropped two of its four layers on any machine without the model cache,
  and the sitting never said so** — which reads as a clean pass. `tick` now prints
  `NOT CHECKED (no detector ran)` with the list.
- **`OWNVOICE_WITNESS=0` did nothing when set in `.env`.** The documented way to stop
  sentences leaving the machine was read from the environment only, and `.env` is the
  one config file the docs point at. It is now read like the API key.
- **No data-handling disclosure.** The README now has "What leaves your machine":
  what goes to OpenRouter, what never leaves, and that with no key there are no network
  calls at all.
- **`intake/standin/README.md` was false in two places** — it claimed the author corpus
  was empty and that everything in the directory was synthetic. It is one real document
  by a real person, and it now says so and says to replace it.
- **`CLAUDE.md` shipped a cancelled build protocol** (one T-step per session, a local
  path, a private-repo pointer). Rewritten as the rules that are not style preferences.

### Verified before publishing

- **No secret has ever been committed.** `.env` was never tracked in any commit; no
  credential pattern appears anywhere in history; `.env.example` holds only a
  placeholder.
- **The README's install commands were executed, not assumed.** The nine selftests and
  the citation gate pass under plain system `python3` with no venv and no dependencies.
  Both optional-extra git URLs resolve and build their metadata (factwash 0.5.0,
  minicheck 0.1.0).
- **The quickstart runs verbatim**, including the empty-anchors case.

## Still untested — read this before relying on it

1. **No human has ever run a sitting.** `tick.py` has been read closely, corrected in
   seven places, unit-tested and smoke-run with scripted input, but no person has sat
   in front of it. U1b exists for exactly this and has not been done.
2. **No real paper has been through the pipeline.** Everything is verified on
   `intake/standin/`, which is synthetic by construction.
3. **Only Linux has been tested**, and only on NixOS with Python 3.13.15. macOS and
   Windows are untried. Nothing is known to be OS-specific after the `tools/py` fix,
   but "not known to be" is not "tested".
4. **The full optional install has never been done from scratch.** The git URLs resolve
   and build metadata; nobody has installed torch, transformers and the 5.9 GB of
   weights on a clean machine and confirmed the entailment layer then runs.
5. **The cost figure is a probe, not a paper.** $0.0005/paragraph comes from single
   paragraphs across eight models. No one has totalled a real paper.
6. **Two people sharing one clone is unexamined.** The termbase, learnings store, seed
   library and witness cache are not per-user, and nothing has been audited for
   collisions.
7. **The 2-AFC voice calibration has never produced a real number.** It runs, its catch
   trial is correct, and no author has yet answered it about their own writing.
8. **The guard's warning classes carry unmeasured false-positive rates on real drafts.**
   Their recall is measured on 30 seeded sentence-for-sentence rewrites
   (`steps/T1-guard-benchmark.md`); the rate at which they fire spuriously on prose
   written from a skeleton is not.

## Refuted, so nobody re-raises them

Ten findings did not survive verification. The instructive ones: that a private repo is
itself a defect (it is a normal access decision); that the pushed `SKILL.md` referenced
a missing `setup_paper.py` (it did not — that reviewer manufactured the error by running
a command the pushed docs never gave); and that the already-fixed entailment-severity
bug lacked a regression test (the value is a literal constant with no path to change it).
