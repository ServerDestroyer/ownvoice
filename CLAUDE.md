# OwnVoice — session protocol

This repo is built **one step per session**. In every session:

1. Read [BUILD.md](BUILD.md) (the state board) and the step's spec in
   [DESIGN.md](DESIGN.md) §10. Do the single open step Chris names (or the first
   unblocked one). Do not start a second step, even if the first finishes early.
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
