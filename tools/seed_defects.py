#!/usr/bin/env python3
"""B2 seed-defect generator — builds the ~30-item benchmark library (research/12 recipe).

Usage:  python3 tools/seed_defects.py --pool pool.md --out tools/seeds \\
            [--models m1,m2]      # two models that are NOT the meld engine, T=0.5
        python3 tools/seed_defects.py --selftest

Pool = paragraphs of Chris's writing / locked skeletons, blank-line separated; only
paragraphs containing at least one epistemic marker are eligible (Belem's filter).

Composition (stratified): 6 HEDGE-DROP-IN-LEX, 6 HEDGE-DROP-OUT-LEX, 4 ATTRIBUTION-DROP,
4 BOOSTER-INSERT, 3 EVIDENTIAL-REFRAME, 3 CONDITION-DROP, 2 POLARITY-FLIP (harness
control), 2 TRUE-PARAPHRASE (false-positive control). The last two are not optional.

Each generated seed is validated mechanically before acceptance:
  1. sentence count identical (edit stayed at sentence level)
  2. word-level edit distance small (minimality)
  3. bidirectional entailment PASSES — run in the test phase when a backend is
     installed; until then seeds are marked entailment_checked: false.
Chris labels direction (inflated/deflated/preserved) on all 30, blind to generator;
a blind second pass over ~12 gives the self-agreement bound.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guard import LEX, find_markers, sentences  # noqa: E402

COMPOSITION = [  # (class, n, instruction to the generator model)
    ("HEDGE-DROP-IN-LEX", 6,
     "Delete exactly one hedging word/phrase (e.g. 'may', 'could', 'appears', "
     "'suggests') so the main claim reads as certain. Change nothing else."),
    ("HEDGE-DROP-OUT-LEX", 6,
     "The paragraph hedges via a non-standard phrasing (e.g. 'our sense is', 'on the "
     "evidence available'). Remove that hedging phrasing so the claim reads as "
     "certain. Change nothing else."),
    ("ATTRIBUTION-DROP", 4,
     "Remove the attribution of the main claim to its source (e.g. 'Smith reports "
     "that X' -> 'X'). Change nothing else."),
    ("BOOSTER-INSERT", 4,
     "Insert exactly one booster (e.g. 'clearly', 'definitively', 'establishes') "
     "strengthening the main claim. Remove nothing."),
    ("EVIDENTIAL-REFRAME", 3,
     "Reframe who found the result without dropping any single cue word (e.g. 'We "
     "find X' -> 'Researchers have discovered X'). Keep all other content."),
    ("CONDITION-DROP", 3,
     "Remove a conditional qualifier (e.g. 'if the sample holds', 'under assumption "
     "A') from the main claim. Change nothing else."),
    ("POLARITY-FLIP", 2,
     "Flip the polarity of the main claim (negate it, or remove its negation). "
     "Change nothing else."),
    ("TRUE-PARAPHRASE", 2,
     "Paraphrase one epistemic marker with an equivalent one of the SAME strength "
     "(e.g. 'may contribute' -> 'could play a part'). Do not change certainty."),
]
PROMPT = ("Make a targeted minimal edit to this paragraph such that only the epistemic "
          "language of the main claim is affected. {instruction}\n"
          "Reply with ONLY the edited paragraph.\n\nParagraph:\n{para}")


def word_edit_distance(a: str, b: str) -> int:
    """Word-level Levenshtein on lowercased, depunctuated text (stdlib DP)."""
    wa = re.findall(r"[a-z0-9']+", a.lower())
    wb = re.findall(r"[a-z0-9']+", b.lower())
    prev = list(range(len(wb) + 1))
    for i, x in enumerate(wa, 1):
        cur = [i]
        for j, y in enumerate(wb, 1):
            cur.append(min(prev[j] + 1, cur[-1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def eligible(para: str) -> bool:
    return bool(find_markers(para))  # at least one epistemic marker


def valid_seed(original: str, edited: str, max_dist=8) -> tuple[bool, str]:
    if len(sentences(original)) != len(sentences(edited)):
        return False, "sentence count changed"
    d = word_edit_distance(original, edited)
    if d == 0:
        return False, "no edit made"
    if d > max_dist:
        return False, f"edit not minimal (word distance {d})"
    return True, ""


def generate(pool_path: Path, out_dir: Path, models: list[str]):
    from meld import call  # OpenRouter client, retry, .env key
    pool = [p for p in re.split(r"\n\s*\n", pool_path.read_text()) if p.strip()]
    pool = [p.strip() for p in pool if eligible(p)]
    if not pool:
        sys.exit("no eligible paragraphs (need at least one epistemic marker each)")
    out_dir.mkdir(parents=True, exist_ok=True)
    n_made = 0
    for cls, n, instruction in COMPOSITION:
        made = 0
        for i, para in enumerate(pool * 3):  # cycle pool until quota met
            if made >= n:
                break
            model = models[(n_made + made) % len(models)]
            edited = call(model, "", PROMPT.format(instruction=instruction, para=para),
                          0.5).strip()
            ok, why = valid_seed(para, edited)
            if not ok:
                print(f"  reject {cls}: {why}", file=sys.stderr)
                continue
            seed = {"class": cls, "original": para, "seeded": edited,
                    "generator": model, "temperature": 0.5,
                    "entailment_checked": False,  # test phase, when a backend exists
                    "label": None,  # Chris: inflated / deflated / preserved, blind
                    "ts": time.strftime("%F %T")}
            (out_dir / f"{cls.lower()}-{made + 1}.json").write_text(
                json.dumps(seed, indent=1))
            made += 1
        n_made += made
        print(f"{cls}: {made}/{n}")
    print(f"{n_made} seeds -> {out_dir}")


def selftest():
    assert word_edit_distance("the drug may work", "the drug does work") == 1
    assert word_edit_distance("a b c", "a b c") == 0
    assert eligible("The drug may reduce symptoms.")
    assert not eligible("The building has four floors.")
    ok, _ = valid_seed("X may hold. Y is true.", "X holds. Y is true.")
    assert ok
    ok, why = valid_seed("X may hold. Y is true.", "X holds.")
    assert not ok and "sentence count" in why
    ok, why = valid_seed("X may hold.", "X may hold.")
    assert not ok and "no edit" in why
    ok, why = valid_seed("A b c d e f g h i j.", "Z y x w v u t s r q.")
    assert not ok and "minimal" in why
    assert sum(n for _, n, _ in COMPOSITION) == 30
    print("selftest ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool"); ap.add_argument("--out", default="tools/seeds")
    ap.add_argument("--models", default="deepseek/deepseek-chat,meta-llama/llama-4-maverick")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    elif a.pool:
        generate(Path(a.pool), Path(a.out), a.models.split(","))
    else:
        ap.print_help()
