#!/usr/bin/env python3
"""B0 intake validator — checks an intake/<paper>/ directory against DESIGN.md §3.

Usage: python3 tools/intake_check.py intake/paper-007
Exit 0 = contract satisfied; exit 1 = gaps (each printed on its own line).
"""
import re
import sys
from pathlib import Path

CORPUS_WORD_FLOOR = 50_000  # research floor for calibrated voice metrics
CORPUS_DOC_FLOOR = 40

REQUIRED_DIRS = ("paper", "sources", "template", "author-corpus")


def words_in(path: Path) -> int:
    return len(re.findall(r"[A-Za-z']+", path.read_text(errors="replace")))


def check(root: Path) -> list[str]:
    gaps = []
    if not root.is_dir():
        return [f"intake directory missing: {root}"]

    for d in REQUIRED_DIRS:
        sub = root / d
        if not sub.is_dir():
            gaps.append(f"missing directory: {d}/")
            continue
        mds = list(sub.rglob("*.md"))
        # the shared README doesn't count as content
        mds = [m for m in mds if m.name.lower() != "readme.md"]
        if not mds:
            gaps.append(f"no markdown content in {d}/")

    for f in root.rglob("*"):
        if " " in f.name:
            gaps.append(f"filename contains spaces (breaks links): {f.relative_to(root)}")

    corpus = root / "author-corpus"
    if corpus.is_dir():
        docs = [m for m in corpus.rglob("*.md") if m.name.lower() != "readme.md"]
        total = sum(words_in(m) for m in docs)
        if docs and (total < CORPUS_WORD_FLOOR or len(docs) < CORPUS_DOC_FLOOR):
            gaps.append(
                f"author corpus below calibration floor ({total} words / {len(docs)} docs; "
                f"floor {CORPUS_WORD_FLOOR}/{CORPUS_DOC_FLOOR}) — voice metrics run uncalibrated, "
                "trend-only (DESIGN §3.4); not a blocker"
            )

    non_md = [f for f in root.rglob("*")
              if f.is_file() and f.suffix.lower() not in (".md", "") and f.name != ".gitkeep"]
    for f in non_md:
        gaps.append(f"non-markdown input needs conversion: {f.relative_to(root)}")
    return gaps


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        r = Path(td) / "p"
        assert check(r) == [f"intake directory missing: {r}"]
        for d in REQUIRED_DIRS:
            (r / d).mkdir(parents=True)
        gaps = check(r)
        assert len(gaps) == 4 and all("no markdown content" in g for g in gaps), gaps
        for d in REQUIRED_DIRS:
            (r / d / "a.md").write_text("hello world " * 10)
        (r / "paper" / "bad name.md").write_text("x")
        gaps = check(r)
        assert any("spaces" in g for g in gaps) and any("calibration floor" in g for g in gaps), gaps
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    problems = check(Path(sys.argv[1]))
    blockers = [g for g in problems if "not a blocker" not in g]
    for g in problems:
        print(("GAP:  " if "not a blocker" not in g else "NOTE: ") + g)
    print(f"{'FAIL' if blockers else 'PASS'}: {len(blockers)} blocking gap(s)")
    sys.exit(1 if blockers else 0)
