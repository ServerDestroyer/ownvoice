#!/usr/bin/env python3
"""B5 grounding prepass — one-time whole-paper citation grounding (DESIGN.md §4).

Usage:  python3 tools/prepass.py --paper intake/<p>/paper/paper.md \\
            --sources intake/<p>/sources --state state
        python3 tools/prepass.py --mark-bad <source.md> --state state   (fan-out)
        python3 tools/prepass.py --selftest

Outputs: state/grounding-ledger.json  citation -> {locator, resolves, source, sections[]}
         state/holds-report.md        unresolvable citations + top-3 candidate passages
Fan-out: --mark-bad sets GROUNDING_STALE on every citing section in state/board.json.

Locators are committee-verifiable positions: if <source>.locators.json exists
(paragraph index -> published page/section, per the intake README's mapping notes),
that mapping is used; otherwise the ledger records the paragraph but flags
needs_mapping — never a bare private line number (P-5).
"""
import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

# (Author, 2020) / (Author et al., 2020) / (Author & Other, 2020) / (Author 2020)
CITE_RE = re.compile(
    r"\(([A-Z][A-Za-z\-']+(?:\s+(?:et al\.|&\s*[A-Z][A-Za-z\-']+))?),?\s+(\d{4}[a-z]?)\)")
# narrative form: Author (2020) / Author et al. (2020) / Author & Other (2020)
NARRATIVE_RE = re.compile(
    r"\b([A-Z][A-Za-z\-']+(?:\s+(?:et al\.|(?:&|and)\s+[A-Z][A-Za-z\-']+))?)"
    r"\s+\((\d{4}[a-z]?)\)")
# degenerate: "X markdown line N" / "see X.md line N"
DEGEN_RE = re.compile(r"\b([\w\-]+\.md)\s+line\s+(\d+)", re.I)


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


class BM25:
    """Paragraph-level BM25 over the markdown sources. ~stdlib; no vector DB (§7.4)."""

    def __init__(self, k1=1.5, b=0.75):
        self.k1, self.b, self.docs = k1, b, []  # docs: (source, para_idx, tokens, raw)

    def add(self, source: str, paras: list[str]):
        for i, p in enumerate(paras):
            self.docs.append((source, i, tokenize(p), p))

    def finish(self):
        self.df = Counter(t for _, _, toks, _ in self.docs for t in set(toks))
        self.avgdl = sum(len(t) for _, _, t, _ in self.docs) / max(len(self.docs), 1)

    def search(self, query: str, n=3):
        q = tokenize(query)
        N = len(self.docs)
        scored = []
        for src, idx, toks, raw in self.docs:
            tf = Counter(toks)
            s = 0.0
            for t in q:
                if t not in tf:
                    continue
                idf = math.log(1 + (N - self.df[t] + 0.5) / (self.df[t] + 0.5))
                s += idf * tf[t] * (self.k1 + 1) / (
                    tf[t] + self.k1 * (1 - self.b + self.b * len(toks) / self.avgdl))
            if s > 0:
                scored.append((s, src, idx, raw))
        return sorted(scored, key=lambda x: -x[0])[:n]


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def sections_of(paper_text: str) -> list[tuple[str, str]]:
    """Split paper markdown into (section_id, body) on ## headings."""
    parts = re.split(r"^##\s+(.+)$", paper_text, flags=re.M)
    if len(parts) == 1:
        return [("_preamble", paper_text)]
    out = []
    for i in range(1, len(parts), 2):
        sid = re.sub(r"\W+", "-", parts[i].strip().lower()).strip("-")
        out.append((sid, parts[i + 1]))
    return out


# never split a "sentence" inside "et al." or after an initial ("Alvarez, R. Smith"),
# or a narrative "Nakamura et al. (2019)" is torn in half and never extracted
SENT_SPLIT = re.compile(r"(?<!al\.)(?<![A-Z]\.)(?<=[.!?])\s+")


def extract_citations(body: str) -> list[tuple[str, str]]:
    """(citation, citing sentence) pairs — the sentence is the BM25 query for holds."""
    out = []
    for sent in SENT_SPLIT.split(body):
        for a, y in CITE_RE.findall(sent):
            out.append((f"{a}, {y}", sent))
        # narrative citations are as common as parenthetical ones in real papers;
        # missing them means an ungrounded claim never reaches the ledger or holds
        for a, y in NARRATIVE_RE.findall(sent):
            a = re.sub(r"'s$", "", a).replace(" and ", " & ")
            out.append((f"{a}, {y}", sent))
        for f, n in DEGEN_RE.findall(sent):
            out.append((f"{f} line {n}", sent))
    return out


def locator_for(src_path: Path, para_idx: int):
    locmap = src_path.with_suffix(".locators.json")
    if locmap.exists():
        m = json.loads(locmap.read_text())
        loc = m.get(str(para_idx))
        if loc:
            return {"published": loc, "needs_mapping": False}
    return {"published": None, "para": para_idx, "needs_mapping": True}


def run_prepass(paper: Path, sources_dir: Path, state: Path):
    state.mkdir(parents=True, exist_ok=True)
    index = BM25()
    src_files = sorted(p for p in sources_dir.rglob("*.md")
                       if p.name.lower() != "readme.md" and ".locators." not in p.name)
    for f in src_files:
        index.add(str(f), paragraphs(f.read_text(errors="replace")))
    index.finish()

    ledger, holds, contexts = {}, {}, {}
    for sid, body in sections_of(paper.read_text()):
        for cite, sentence in extract_citations(body):
            contexts.setdefault(cite, sentence)
            entry = ledger.setdefault(cite, {"locator": None, "resolves": False,
                                             "source": None, "sections": []})
            if sid not in entry["sections"]:
                entry["sections"].append(sid)
            if entry["resolves"]:
                continue
            # a citation resolves if a source doc contains the author surname + year
            surname = tokenize(cite)[0] if tokenize(cite) else ""
            year = (re.search(r"\d{4}", cite) or [""])[0] if re.search(r"\d{4}", cite) else ""
            hit = None
            for f in src_files:
                text = f.read_text(errors="replace")
                if surname and year and surname in tokenize(text) and year in text:
                    paras = paragraphs(text)
                    pi = next((i for i, p in enumerate(paras)
                               if surname in tokenize(p) and year in p), 0)
                    hit = (f, pi)
                    break
            if hit:
                entry["resolves"] = True
                entry["source"] = str(hit[0])
                entry["locator"] = locator_for(hit[0], hit[1])
    holds = []
    for cite, entry in ledger.items():
        if not entry["resolves"]:
            cands = index.search(f"{cite} {contexts.get(cite, '')}", n=3)
            holds.append((cite, entry["sections"],
                          [{"source": s, "para": i, "text": raw[:200]}
                           for _, s, i, raw in cands]))

    (state / "grounding-ledger.json").write_text(json.dumps(ledger, indent=1))
    lines = ["# Holds — unresolvable citations (tick-A block 2)\n"]
    for cite, secs, cands in holds:
        lines.append(f"\n## {cite}  (cited in: {', '.join(secs)})\n")
        for c in cands:
            lines.append(f"- candidate: {c['source']} ¶{c['para']}: {c['text']}…")
        if not cands:
            lines.append("- no candidate passages found")
    (state / "holds-report.md").write_text("\n".join(lines) + "\n")
    print(f"{sum(e['resolves'] for e in ledger.values())}/{len(ledger)} resolved; "
          f"{len(holds)} holds -> {state/'holds-report.md'}")
    return ledger, holds


def mark_bad(source: str, state: Path):
    ledger = json.loads((state / "grounding-ledger.json").read_text())
    board_path = state / "board.json"
    board = json.loads(board_path.read_text()) if board_path.exists() else {}
    stale = sorted({s for e in ledger.values() if e["source"] == source
                    for s in e["sections"]})
    for sid in stale:
        board.setdefault(sid, {})["status"] = "GROUNDING_STALE"
    board_path.write_text(json.dumps(board, indent=1))
    print(f"marked GROUNDING_STALE: {stale or 'none'}")
    return stale


def selftest():
    import tempfile
    # citation forms (regression: narrative citations were silently never extracted,
    # and "et al." split the sentence in two)
    forms = extract_citations(
        "Nakamura et al. (2019) argue X. As shown (Smith, 2020). "
        "Okafor's (2022a) note follows. Boateng & Sorensen (2021) disagree. "
        "The second season (2019) was warmer.")
    assert {c for c, _ in forms} == {"Nakamura et al., 2019", "Smith, 2020",
                                     "Okafor, 2022a", "Boateng & Sorensen, 2021"}, forms

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "sources").mkdir()
        # 3 sources; smith/jones/brown papers with distinct years
        (td / "sources/smith2020.md").write_text(
            "Study by Smith 2020 on turnout.\n\nSmith (2020) measured deliberation effects.")
        (td / "sources/jones2019.md").write_text(
            "Jones 2019 surveyed platforms.\n\nEngagement declined, Jones found in 2019.")
        (td / "sources/brown2021.md").write_text(
            "Brown 2021 reports legitimacy gains.\n\nProcedural fairness, per Brown 2021.")
        (td / "sources/brown2021.locators.json").write_text('{"0": "p. 12", "1": "p. 14"}')
        # paper: 3 sections; 20 citation instances, 5 distinct broken
        good = ["(Smith, 2020)", "(Jones, 2019)", "(Brown, 2021)"]
        bad = ["(Miller, 2018)", "(Chen, 2022)", "(Garcia, 2017)", "(Lee, 2023)",
               "(Okafor, 2015)"]
        body1 = " ".join(f"Turnout and deliberation claim {c}." for c in good * 3)          # 9
        body2 = " ".join(f"Platform engagement claim {c}." for c in good + bad[:3])         # 6
        body3 = " ".join(f"Legitimacy and fairness claim {c}."
                         for c in [good[0]] + bad[2:] + ["(Smith, 2020)"])                  # 5
        paper = td / "paper.md"
        paper.write_text(f"## Intro\n{body1}\n## Methods\n{body2}\n## Results\n{body3}\n")
        state = td / "state"
        ledger, holds = run_prepass(paper, td / "sources", state)
        resolved = [c for c, e in ledger.items() if e["resolves"]]
        held = [c for c, e in ledger.items() if not e["resolves"]]
        assert len(resolved) == 3 and len(held) == 5, (resolved, held)
        assert all(len(c) >= 1 for _, _, c in holds), "hold without candidates"
        assert ledger["Brown, 2021"]["locator"]["published"] == "p. 12"
        assert ledger["Smith, 2020"]["locator"]["needs_mapping"] is True
        assert set(ledger["Smith, 2020"]["sections"]) == {"intro", "methods", "results"}
        # fan-out: jones cited only in intro+methods
        stale = mark_bad(str(td / "sources/jones2019.md"), state)
        assert stale == ["intro", "methods"], stale
        # BM25 sanity: query with a source's own words ranks that source first
        idx = BM25(); idx.add("a", ["turnout deliberation study"]); idx.add("b", ["unrelated words here"])
        idx.finish()
        assert idx.search("deliberation turnout")[0][1] == "a"
    print("selftest ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper"); ap.add_argument("--sources")
    ap.add_argument("--state", default="state")
    ap.add_argument("--mark-bad", metavar="SOURCE")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    elif a.mark_bad:
        mark_bad(a.mark_bad, Path(a.state))
    elif a.paper and a.sources:
        run_prepass(Path(a.paper), Path(a.sources), Path(a.state))
    else:
        ap.print_help()
