# OwnVoice — session protocol

This repo is built **one step per session**. In every session:

1. Read [BUILD.md](BUILD.md) — the **test track** (T1–T6) is the execution order; the
   steps/ notes hold per-step procedure detail and DESIGN.md §10 the gates. Do the
   single T-step Chris names, or the first unblocked one. **Before starting, check the
   step's "Needs" column: if anything listed isn't in hand, say so and stop — never
   start a session that can't finish.** Do not start a second step, even if the first
   finishes early.
2. Honor the frozen decisions listed in BUILD.md — they came from an adversarial
   review ([reviews/](reviews/)) and four research spikes ([spikes/](spikes/)); do not
   relitigate them inside a build session.
3. Research citations like `research/NN` refer to the corpus in the separate
   Humanising-Realtime repo at `/home/chris/coding/Humanising-Realtime/research/`.
4. On finish: update BUILD.md (status + step log), commit, push. Leave the next step
   for the next session.

Style: tools are stdlib-first Python in `tools/`, each with a `--selftest`. Markdown
end to end; no spaces in filenames. This system is not detector evasion — detector
scores are diagnostics only, never targets (DESIGN P-4).

Run tools through **`tools/py`**, never `.venv/bin/python` directly. This is NixOS: the
manylinux wheels (numpy, torch) cannot find `libstdc++.so.6` or `libcuda.so.1` on the
default search path, and Triton shells out to a `/sbin/ldconfig` that does not exist.
`tools/py` sets the three variables that fix it, from the running system generation.
