# author-corpus — fills from the T3 anchors

The stand-in bundle has no author corpus of its own, and should not have one: in T4
Chris *is* the author, so the anchor pool is Chris's own prose, collected at T3 into
`runs/b1/anchors/`.

At T4 setup, copy (do not move) 2-4 of those anchors here and into `state/anchors/` per
the walkthrough skill's setup step 4. Until then `tools/intake_check.py` reports one
blocking gap on this directory, which is correct and expected — the bundle is complete
apart from the input only Chris can supply.

The corpus will sit far below the 50k-word / 40-doc calibration floor. That is fine for
a dry run: voice metrics run trend-only (DESIGN §3.4) and T4 measures the loop, not
voice.
