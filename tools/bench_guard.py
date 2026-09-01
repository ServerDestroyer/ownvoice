#!/usr/bin/env python3
"""T1 guard benchmark — runs the seed library through the G4 stack and reports
per-class recall against research/12's acceptance criteria.

Usage:  .venv/bin/python tools/bench_guard.py --seeds tools/seeds --out runs/t1 \\
            [--entailment minicheck|none] [--witness]
        python3 tools/bench_guard.py --selftest

Each seed is one (original, seeded) paragraph pair differing only in the epistemic
language of the main claim. The benchmark presents it to the gate exactly as a tick
does: skeleton = the original paragraph, one claim per line; output = the seeded
paragraph. A defect seed should FAIL; the TRUE-PARAPHRASE controls should PASS.

Two recalls are reported per class, and the difference matters:
  recall_epistemic  the typed marker diff (layer 1) fired — the number research/12's
                    expectations refer to (~0.9 in-lexicon, ~0.6 out-of-lexicon with
                    the witness, ~0.94 polarity)
  recall_gate       the guard returned FAIL for ANY reason, including alignment
                    UNCHECKABLE, a multiset diff, or entailment. Higher than
                    recall_epistemic, and inflated by incidental catches, so it is
                    never the headline number.
Reporting only recall_gate would credit the hedge diff for catches made by the
citation multiset. Every seed records which layers fired.

Entailment does double duty (research/12): it is layer 3 of the gate AND the seed
filter — a seed the entailment layer already vetoes is not testing the named blind
spot. POLARITY-FLIP is exempt: it is the harness control, and entailment is meant
to see it.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guard import guard, sentences  # noqa: E402

# research/12 "Acceptance". None = report, do not threshold.
ACCEPTANCE = {
    "POLARITY-FLIP": ("recall_epistemic", 1.0, "control: harness is broken if this fails"),
    "CONDITION-DROP": ("recall_epistemic", 1.0, "closed class"),
    "HEDGE-DROP-IN-LEX": ("recall_epistemic", 5 / 6, "base case, must be caught"),
    "TRUE-PARAPHRASE": ("false_positive_rate", 0.0, "false-positive control, 0 flags of 2"),
    "HEDGE-DROP-OUT-LEX": (None, None, "report only — decides whether the witness is wired"),
    "EVIDENTIAL-REFRAME": (None, None, "report only — the measured real-world mechanism"),
    "ATTRIBUTION-DROP": (None, None, "report only — lowest-recall class"),
    "BOOSTER-INSERT": (None, None, "report only — the insertion direction"),
}
EPISTEMIC_PROPERTIES = {"hedge", "attribution", "condition", "booster", "polarity",
                        "certainty"}


def layers(findings: list[dict]) -> dict:
    """Which layer produced each fail, so a catch is attributable to a detector."""
    out = defaultdict(list)
    for f in findings:
        if f.get("severity") != "fail":
            continue
        p, t = f.get("property"), f.get("type")
        if p in EPISTEMIC_PROPERTIES or f.get("engine") == "factwash":
            out["epistemic"].append(f"{t}:{p}")
        elif p == "entailment":
            out["entailment"].append(f"{t}:{p}")
        elif p in ("citation", "number", "entity"):
            out["multiset"].append(f"{t}:{p}")
        elif p in ("alignment", "claim"):
            out["alignment"].append(f"{t}:{p}")
        elif p == "mechanics":
            out["mechanics"].append(f"{t}:{p}")
        else:
            out["other"].append(f"{t}:{p}")
    return dict(out)


def as_skeleton(paragraph: str) -> str:
    """The locked skeleton the gate diffs against: one claim per line."""
    return "\n".join("- " + s for s in sentences(paragraph))


def run_seed(seed: dict, entail: str, use_witness: bool, state: Path) -> dict:
    rep = guard(as_skeleton(seed["original"]), seed["seeded"], "", "",
                use_witness, entail, state)
    fired = layers(rep["findings"])
    return {"class": seed["class"], "verdict": rep["verdict"], "layers": fired,
            "caught_epistemic": "epistemic" in fired,
            "entailment_clean": "entailment" not in fired,
            "not_checked": rep["not_checked"],
            "original": seed["original"], "seeded": seed["seeded"]}


def tabulate(results: list[dict]) -> dict:
    by_class = defaultdict(list)
    for r in results:
        by_class[r["class"]].append(r)
    table, verdicts = {}, {}
    for cls, (_, _, _) in ACCEPTANCE.items():
        rows = by_class.get(cls, [])
        n = len(rows)
        if not n:
            table[cls] = {"n": 0}
            continue
        epi = sum(r["caught_epistemic"] for r in rows)
        gate = sum(r["verdict"] == "FAIL" for r in rows)
        ent = sum(not r["entailment_clean"] for r in rows)
        stat, floor, note = ACCEPTANCE[cls]
        raw = {"recall_epistemic": epi / n, "recall_gate": gate / n,
               "false_positive_rate": gate / n}
        m = {"n": n, "recall_epistemic": round(epi / n, 3),
             "recall_gate": round(gate / n, 3),
             "recall_entailment": round(ent / n, 3),
             "false_positive_rate": round(gate / n, 3),
             "admitted_entailment_clean": sum(r["entailment_clean"] for r in rows),
             "note": note}
        if stat:
            m["floor"], m["stat"] = round(floor, 3), stat
            # compare unrounded — round(5/6,3)=0.833 < 5/6 would fail a class that met it
            passed = (raw[stat] <= floor + 1e-9) if stat == "false_positive_rate" \
                else (raw[stat] >= floor - 1e-9)
            m["acceptance"] = "PASS" if passed else "FAIL"
            verdicts[cls] = m["acceptance"]
        else:
            m["acceptance"] = "report-only"
        table[cls] = m
    return {"per_class": table,
            "acceptance": "PASS" if all(v == "PASS" for v in verdicts.values())
                          else "FAIL",
            "thresholded": verdicts}


def _table(summary: dict) -> list[str]:
    lines = ["| class | n | recall (epistemic layer) | recall (gate, any layer) "
             "| entailment alone | floor | acceptance |",
             "|---|---|---|---|---|---|---|"]
    for cls, m in summary["per_class"].items():
        if not m.get("n"):
            lines.append(f"| {cls} | 0 | — | — | — | — | NO SEEDS |")
            continue
        key = "false_positive_rate" if cls == "TRUE-PARAPHRASE" else "recall_epistemic"
        head = (f"{m['false_positive_rate']:.2f} (false-positive rate)"
                if cls == "TRUE-PARAPHRASE" else f"{m['recall_epistemic']:.2f}")
        floor = "—" if "floor" not in m else (
            f"<= {m['floor']:.2f}" if key == "false_positive_rate"
            else f">= {m['floor']:.2f}")
        lines.append(f"| {cls} | {m['n']} | {head} | {m['recall_gate']:.2f} "
                     f"| {m['recall_entailment']:.2f} | {floor} | {m['acceptance']} |")
    lines += ["", f"**Thresholded acceptance: {summary['acceptance']}** "
                  f"({', '.join(f'{k}={v}' for k, v in summary['thresholded'].items())})"]
    return lines


def to_markdown(summary: dict, meta: dict, admitted: dict | None = None) -> str:
    lines = [f"# T1 — guard benchmark ({meta['seeds']} seeds)", "",
             f"- entailment backend: `{meta['entailment']}`",
             f"- witness: {meta['witness']}",
             f"- seed generator: {meta['generator']}",
             f"- classes declared `not_checked` by the gate: "
             f"{', '.join(meta['not_checked']) or 'none'}", "",
             "## All seeds", ""] + _table(summary)
    if admitted is not None:
        lines += ["", "## Entailment-admitted seeds only", "",
                  "research/12 validation 3: a seed the entailment layer already "
                  "vetoes is not testing the named blind spot and must be discarded "
                  "or reclassified. POLARITY-FLIP is exempt — it is the harness "
                  "control and entailment is meant to see it. A class that empties "
                  "here is a class the entailment layer already covers.", ""]
        lines += _table(admitted)
    lines += ["", "Report-only classes are not thresholded by design (research/12): "
                  "30 items sizes the direction, not the rate."]
    return "\n".join(lines) + "\n"


def main(seed_dir: Path, out_dir: Path, entail: str, use_witness: bool):
    files = sorted(seed_dir.glob("*.json"))
    if not files:
        sys.exit(f"no seeds in {seed_dir} — generate them first "
                 "(tools/seed_defects.py --pool ... or --ingest ...)")
    seeds = [json.loads(f.read_text()) for f in files]
    out_dir.mkdir(parents=True, exist_ok=True)

    results = [run_seed(s, entail, use_witness, out_dir / "state") for s in seeds]

    # Stamp the entailment filter back onto the library (research/12 validation 3).
    # POLARITY-FLIP is exempt: entailment is supposed to see a flipped claim.
    if entail != "none":
        for f, s, r in zip(files, seeds, results):
            s["entailment_checked"] = True
            s["entailment_clean"] = r["entailment_clean"] or s["class"] == "POLARITY-FLIP"
            f.write_text(json.dumps(s, indent=1))

    excluded = [r for s, r in zip(seeds, results)
                if entail != "none" and not r["entailment_clean"]
                and s["class"] != "POLARITY-FLIP"]
    summary = tabulate(results)
    admitted = tabulate([r for r in results if r not in excluded]) \
        if entail != "none" else None
    meta = {"seeds": len(seeds), "entailment": entail,
            "witness": "measured" if use_witness else "not_measured (needs OPENROUTER_API_KEY)",
            "generator": seeds[0].get("generator", "?"),
            "not_checked": sorted({p for r in results for p in r["not_checked"]}),
            "entailment_excluded": len(excluded)}
    (out_dir / "bench.json").write_text(json.dumps(
        {"meta": meta, "summary": summary, "admitted": admitted,
         "results": results}, indent=1))
    (out_dir / "recall.md").write_text(to_markdown(summary, meta, admitted))
    print(to_markdown(summary, meta, admitted))
    if excluded:
        print(f"NOTE: {len(excluded)} seed(s) vetoed by entailment and therefore not "
              f"testing the named blind spot — see bench.json", file=sys.stderr)
    return 0 if summary["acceptance"] == "PASS" else 1


def selftest():
    assert as_skeleton("A may hold. B is true.") == "- A may hold.\n- B is true."

    f = [{"severity": "fail", "type": "DROPPED", "property": "hedge"},
         {"severity": "fail", "type": "MISSING", "property": "citation"},
         {"severity": "info", "type": "NOT_CHECKED", "property": "entailment"}]
    L = layers(f)
    assert L["epistemic"] == ["DROPPED:hedge"] and L["multiset"] == ["MISSING:citation"]
    assert "entailment" not in L  # info is not a fail

    # a catch made only by the citation diff must NOT count as epistemic recall
    assert not layers([{"severity": "fail", "type": "MISSING",
                        "property": "citation"}]).get("epistemic")

    rows = [{"class": "HEDGE-DROP-IN-LEX", "caught_epistemic": True, "verdict": "FAIL",
             "entailment_clean": True}] * 5 + \
           [{"class": "HEDGE-DROP-IN-LEX", "caught_epistemic": False, "verdict": "PASS",
             "entailment_clean": False}]
    s = tabulate(rows)
    assert s["per_class"]["HEDGE-DROP-IN-LEX"]["recall_epistemic"] == round(5 / 6, 3)
    assert s["per_class"]["HEDGE-DROP-IN-LEX"]["acceptance"] == "PASS"  # floor is 5/6
    # entailment recall is counted independently of the typed diff
    assert s["per_class"]["HEDGE-DROP-IN-LEX"]["recall_entailment"] == round(1 / 6, 3)

    rows = [{"class": "HEDGE-DROP-IN-LEX", "caught_epistemic": True, "verdict": "FAIL",
             "entailment_clean": True}] * 4 + \
           [{"class": "HEDGE-DROP-IN-LEX", "caught_epistemic": False, "verdict": "FAIL",
             "entailment_clean": True}] * 2
    assert tabulate(rows)["per_class"]["HEDGE-DROP-IN-LEX"]["acceptance"] == "FAIL", \
        "gate-level FAILs must not rescue a class the epistemic layer missed"

    # false-positive control: any flag is a failure
    fp = [{"class": "TRUE-PARAPHRASE", "caught_epistemic": True, "verdict": "FAIL",
           "entailment_clean": True},
          {"class": "TRUE-PARAPHRASE", "caught_epistemic": False, "verdict": "PASS",
           "entailment_clean": True}]
    t = tabulate(fp)["per_class"]["TRUE-PARAPHRASE"]
    assert t["false_positive_rate"] == 0.5 and t["acceptance"] == "FAIL"
    clean = [{"class": "TRUE-PARAPHRASE", "caught_epistemic": False, "verdict": "PASS",
              "entailment_clean": True}] * 2
    assert tabulate(clean)["per_class"]["TRUE-PARAPHRASE"]["acceptance"] == "PASS"

    assert sum(1 for v in ACCEPTANCE.values() if v[0]) == 4  # 4 thresholded classes
    print("selftest ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="tools/seeds")
    ap.add_argument("--out", default="runs/t1")
    ap.add_argument("--entailment", default="none",
                    choices=["none", "alignscore", "minicheck"])
    ap.add_argument("--witness", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    else:
        sys.exit(main(Path(a.seeds), Path(a.out), a.entailment, a.witness))
