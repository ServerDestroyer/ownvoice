#!/usr/bin/env python3
"""T2 — prepass gate (BUILD.md test track; spec: steps/B5-grounding-prepass.md).

Writes a deterministic synthetic set (20 distinct citations, 5 seeded-broken),
runs tools/prepass.py end to end, and asserts the gate:
  - all 15 resolvable citations resolve, to the right source, with the right locator
  - all 5 broken citations land in the holds report with >=1 candidate each,
    and the topical near-miss surfaces the topically-close source as a candidate
  - fan-out marks exactly the citing sections GROUNDING_STALE

Run:  python3 tools/gate_prepass.py
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from prepass import run_prepass, mark_bad  # noqa: E402

T2 = ROOT / "runs/t2"
SRC = T2 / "sources"
STATE = T2 / "state"

# 15 resolvable sources: filename -> (paragraph-0 with surname+year, paragraph-1)
SOURCES = {
    "smithers2020.md": (
        "Smithers (2020) measured turnout effects of deliberative minipublics "
        "across 40 municipalities.",
        "The turnout gains persisted two election cycles."),
    "jonquil2019.md": (
        "Jonquil (2019) surveyed platform moderation practices on civic forums.",
        "Moderation transparency predicted sustained participation."),
    "browning2021.md": (
        "Browning (2021) reports legitimacy gains from procedural fairness in "
        "participatory budgeting.",
        "Perceived fairness mattered more than allocation outcomes."),
    "nakamura2019.md": (
        "Nakamura et al. (2019) traced information cascades in online assemblies.",
        "Early speakers anchored the cascade direction."),
    "osei-virtanen2021.md": (
        "Osei and Virtanen (2021) compared sortition panels with elected councils.",
        "Sortition panels showed lower polarization on identical dockets."),
    "halloran2020a.md": (
        "Halloran (2020a) documents agenda capture in citizen assemblies.",
        "Facilitator rotation reduced capture incidence."),
    "delacroix2017.md": (
        "Delacroix (2017) analysed referendum wording effects on approval rates.",
        "Double negatives depressed comprehension scores."),
    "whitfield2018.md": (
        "Whitfield (2018) studied volunteer retention in local civic tech projects.",
        "Recognition rituals outperformed stipends for retention."),
    "moreau2022.md": (
        "Moreau (2022) evaluated deliberation quality metrics for online panels, "
        "including argument repertoire and reciprocity coding.",
        "Reciprocity coding was the most reliable quality metric."),
    "tanaka2016.md": (
        "Tanaka (2016) examined quorum rules in neighbourhood associations.",
        "Lower quorums increased meeting frequency but not decision quality."),
    "lindqvist2023.md": (
        "Lindqvist (2023) benchmarked consensus algorithms for participatory "
        "decision platforms.",
        "Approval voting variants scaled best past 200 participants."),
    "adeyemi2015.md": (
        "Adeyemi (2015) mapped civic trust trajectories after corruption scandals, "
        "extending the earlier framework of Okonkwo (2014).",
        "Trust recovery took a median of six years."),
    "petrov2019.md": (
        "Petrov (2019) measured translation effects in multilingual assemblies.",
        "Relay interpretation doubled clarification requests."),
    "castellanos2020.md": (
        "Castellanos (2020) studied rural broadband effects on e-participation.",
        "Participation rose only where facilitation was also funded."),
    "bergstrom2014.md": (
        "Bergstrom et al. (2014) modelled attrition in multi-round deliberations.",
        "Attrition concentrated between rounds two and three."),
}

# committee-verifiable locator maps for 5 of the 15 (paragraph 0 holds the claim)
LOCATORS = {
    "smithers2020": "p. 3",
    "jonquil2019": "pp. 112-114",
    "browning2021": "sec. 4.2",
    "whitfield2018": "p. 27",
    "petrov2019": "p. 9",
}

GOOD = ["(Smithers, 2020)", "(Jonquil, 2019)", "(Browning, 2021)",
        "(Nakamura et al., 2019)", "(Osei & Virtanen, 2021)", "(Halloran, 2020a)",
        "(Delacroix, 2017)", "(Whitfield, 2018)", "(Moreau, 2022)", "(Tanaka, 2016)",
        "(Lindqvist, 2023)", "(Adeyemi, 2015)", "(Petrov, 2019)",
        "(Castellanos, 2020)", "(Bergstrom et al., 2014)"]
# seeded-broken: absent author; wrong-year near-miss (Okonkwo is 2014 in-corpus);
# topical near-miss (deliberation quality metrics = moreau2022's topic);
# degenerate private line reference; absent author with plausible year
BROKEN_SENTENCES = [
    "Vance (2016) reported similar effects among field organizers.",
    "Trust trajectories were first formalized here (Okonkwo, 2018).",
    "Deliberation quality metrics such as argument repertoire and reciprocity "
    "coding were validated for online panels (Marsh et al., 2022).",
    "The facilitator's observation appears in field-notes.md line 40.",
    "A recent replication confirmed the attrition pattern (Ito, 2025).",
]

PAPER = f"""## Intro
Deliberative minipublics raise turnout {GOOD[0]}. Civic forums depend on moderation
transparency {GOOD[1]}. Nakamura et al. (2019) show information cascades shape
assembly outcomes.
Attrition follows a predictable curve {GOOD[14]}. {BROKEN_SENTENCES[2]}

## Background
Browning (2021) shows procedural fairness drives legitimacy. Osei and Virtanen
(2021) find sortition reduces polarization. Agenda capture is a documented risk {GOOD[5]}. Referendum wording alters
approval {GOOD[6]}. Turnout effects replicate across municipalities {GOOD[0]}.
{BROKEN_SENTENCES[1]}

## Methods
We follow volunteer retention protocols {GOOD[7]}. Quality is scored by reciprocity
coding {GOOD[8]}. Quorum rules follow prior work {GOOD[9]}. {BROKEN_SENTENCES[3]}
{BROKEN_SENTENCES[0]}

## Results
Consensus scaled per published benchmarks {GOOD[10]}. Trust recovery matched the
mapped trajectories {GOOD[11]}. Clarification requests doubled under relay
interpretation {GOOD[12]}. Broadband alone did not raise participation {GOOD[13]}.
Moderation transparency again predicted participation {GOOD[1]}. {BROKEN_SENTENCES[4]}
"""

EXPECT_RESOLVED = {
    "Smithers, 2020": "smithers2020.md", "Jonquil, 2019": "jonquil2019.md",
    "Browning, 2021": "browning2021.md", "Nakamura et al., 2019": "nakamura2019.md",
    "Osei & Virtanen, 2021": "osei-virtanen2021.md", "Halloran, 2020a": "halloran2020a.md",
    "Delacroix, 2017": "delacroix2017.md", "Whitfield, 2018": "whitfield2018.md",
    "Moreau, 2022": "moreau2022.md", "Tanaka, 2016": "tanaka2016.md",
    "Lindqvist, 2023": "lindqvist2023.md", "Adeyemi, 2015": "adeyemi2015.md",
    "Petrov, 2019": "petrov2019.md", "Castellanos, 2020": "castellanos2020.md",
    "Bergstrom et al., 2014": "bergstrom2014.md",
}
EXPECT_HELD = {"Vance, 2016", "Okonkwo, 2018", "Marsh et al., 2022",
               "field-notes.md line 40", "Ito, 2025"}


def write_fixture():
    SRC.mkdir(parents=True, exist_ok=True)
    for name, (p0, p1) in SOURCES.items():
        (SRC / name).write_text(f"{p0}\n\n{p1}\n")
    for stem, page in LOCATORS.items():
        (SRC / f"{stem}.locators.json").write_text(json.dumps({"0": page, "1": "n/a"}))
    (T2 / "paper.md").write_text(PAPER)


def main():
    write_fixture()
    t0 = time.perf_counter()
    ledger, holds = run_prepass(T2 / "paper.md", SRC, STATE)
    dt = time.perf_counter() - t0

    resolved = {c: e for c, e in ledger.items() if e["resolves"]}
    held = {c for c, e in ledger.items() if not e["resolves"]}
    assert len(ledger) == 20, f"expected 20 distinct citations, got {len(ledger)}"
    assert set(resolved) == set(EXPECT_RESOLVED), (
        set(EXPECT_RESOLVED) ^ set(resolved))
    assert held == EXPECT_HELD, held ^ EXPECT_HELD

    for cite, fname in EXPECT_RESOLVED.items():
        e = resolved[cite]
        assert e["source"].endswith(fname), (cite, e["source"])
        stem = fname[:-3]
        if stem in LOCATORS:
            assert e["locator"]["published"] == LOCATORS[stem], (cite, e["locator"])
            assert e["locator"]["needs_mapping"] is False
        else:
            assert e["locator"]["needs_mapping"] is True, (cite, e["locator"])

    assert set(ledger["Smithers, 2020"]["sections"]) == {"intro", "background"}
    assert set(ledger["Jonquil, 2019"]["sections"]) == {"intro", "results"}

    holds_by_cite = {c: cands for c, _, cands in holds}
    for cite in EXPECT_HELD:
        assert holds_by_cite.get(cite), f"hold without candidates: {cite}"
    marsh_srcs = {c["source"] for c in holds_by_cite["Marsh et al., 2022"]}
    assert any(s.endswith("moreau2022.md") for s in marsh_srcs), marsh_srcs

    stale = mark_bad(str(SRC / "jonquil2019.md"), STATE)
    assert stale == ["intro", "results"], stale

    print(f"T2 gate PASS — 15/15 resolved, 5/5 held, fan-out correct; "
          f"prepass runtime {dt:.2f}s on 20 citations / {len(SOURCES)} sources")


if __name__ == "__main__":
    main()
