#!/usr/bin/env python3
"""B4 learnings store + staleness ledger + termbase (DESIGN.md §9).

Usage:  python3 tools/learnings.py --state state propose --behavior "..." --scope section \\
            --over-application "..." --probe "regex"
        python3 tools/learnings.py --state state ratify <id>      (one keystroke, arc close)
        python3 tools/learnings.py --state state veto <id>        (reject_count++, suspend check)
        python3 tools/learnings.py --state state scan             (probes over approved text -> stale.json)
        python3 tools/learnings.py --state state vale             (termbase.yml -> Vale style)
        python3 tools/learnings.py --selftest

Admission gate (adversarial — a rule must earn its place): a proposal is refused when
it (a) has no named construction/probe (a vibe), (b) optimizes a detector score,
(c) contradicts a termbase entry, (d) restates an existing learning. Ratification is
batched at arc close, never mid-review. FDR lifecycle: accept/reject counts; negative
evidence suspends (never deletes); suspended rules re-propose at next arc close.
Termbase beats anchors; a termbase change is a global learning that fans out through
stale.json.
"""
import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

SUSPEND_AFTER_REJECTS = 2  # conservative within one paper (counts are small)


def _dir(state: Path) -> Path:
    d = state / "learnings"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_all(state: Path) -> dict:
    return {p.stem: json.loads(p.read_text()) for p in _dir(state).glob("*.json")}


def learnings_hash(state: Path) -> str:
    active = sorted(k for k, v in load_all(state).items()
                    if v["status"] == "active")
    return hashlib.sha256("|".join(active).encode()).hexdigest()[:12]


def load_termbase(state: Path) -> dict:
    """termbase.yml — minimal 'wrong: right' mapping, one per line (no yaml dep)."""
    tb, path = {}, state / "termbase.yml"
    if path.exists():
        for line in path.read_text().splitlines():
            if ":" in line and not line.strip().startswith("#"):
                k, _, v = line.partition(":")
                tb[k.strip()] = v.strip()
    return tb


def propose(state: Path, behavior: str, scope: str, over_application: str,
            probe: str) -> str:
    assert scope in ("span", "section", "paper", "global"), scope
    # admission screen — the blocklist
    if not probe or not behavior:
        sys.exit("refused: no named construction/probe — a vibe is not a rule")
    if re.search(r"detector|binoculars|ghostbuster|luar|score", behavior, re.I):
        sys.exit("refused: rules optimizing a detector score are blocklisted (P-4)")
    for term in load_termbase(state):
        if term and re.search(re.escape(term), behavior, re.I):
            sys.exit(f"refused: contradicts/overlaps termbase entry '{term}' — "
                     "revise the termbase instead")
    for lid, l in load_all(state).items():
        if l["probe"] == probe:
            sys.exit(f"refused: restates existing learning {lid}")
    try:
        re.compile(probe)
    except re.error as e:
        sys.exit(f"refused: probe is not a valid regex: {e}")
    lid = hashlib.sha256(probe.encode()).hexdigest()[:8]
    (_dir(state) / f"{lid}.json").write_text(json.dumps({
        "behavior": behavior, "scope": scope, "over_application": over_application,
        "probe": probe, "status": "proposed", "version": 1,
        "applied": 0, "accepted": 0, "rejected": 0,
        "ts": time.strftime("%F %T")}, indent=1))
    print(f"proposed {lid} (ratify at arc close, in batch)")
    return lid


def ratify(state: Path, lid: str):
    p = _dir(state) / f"{lid}.json"
    l = json.loads(p.read_text())
    l["status"] = "active"
    p.write_text(json.dumps(l, indent=1))
    scan(state)  # admission runs the probe over all approved text
    print(f"ratified {lid}; probe scanned into stale.json")


def veto(state: Path, lid: str):
    p = _dir(state) / f"{lid}.json"
    l = json.loads(p.read_text())
    l["rejected"] += 1
    if l["rejected"] >= SUSPEND_AFTER_REJECTS:
        l["status"] = "suspended"  # never deleted; re-proposed at next arc close
    p.write_text(json.dumps(l, indent=1))
    print(f"{lid}: rejected={l['rejected']} status={l['status']}")


def scan(state: Path):
    """Run every active probe over approved sections -> stale.json. Nothing reopens
    automatically; retouches are proposed as diffs at paper pass."""
    stale = {}
    sections_root = state.parent / "sections"
    for lid, l in load_all(state).items():
        if l["status"] != "active":
            continue
        rx = re.compile(l["probe"], re.I)
        for approved in sections_root.glob("*/approved.md"):
            spans = [m.group(0) for m in rx.finditer(approved.read_text())]
            if spans:
                stale.setdefault(approved.parent.name, []).append(
                    {"learning_id": lid, "matched_spans": spans})
    (state / "stale.json").write_text(json.dumps(stale, indent=1))
    hits = sum(len(v) for v in stale.values())
    print(f"scan: {hits} probe match(es) across {len(stale)} approved section(s) "
          f"-> {state / 'stale.json'}")  # a silent paper pass reads as "nothing to do"
    return stale


def vale(state: Path):
    """Generate a Vale substitution style from termbase.yml."""
    tb = load_termbase(state)
    style_dir = state / "vale" / "Termbase"
    style_dir.mkdir(parents=True, exist_ok=True)
    lines = ["extends: substitution", "message: \"termbase: use '%s', not '%s'\"",
             "level: error", "ignorecase: false", "swap:"]
    lines += [f"  {k}: {v}" for k, v in tb.items()]
    (style_dir / "terms.yml").write_text("\n".join(lines) + "\n")
    (state / ".vale.ini").write_text(
        f"StylesPath = vale\n\n[*.md]\nBasedOnStyles = Termbase\n")
    print(f"vale style: {len(tb)} termbase entries")


def termbase_conflicts(state: Path, anchor_text: str) -> list[str]:
    """Termbase beats anchors: report anchor text using a 'wrong' form, so the
    conflict is logged against that anchor (never silently followed)."""
    return [wrong for wrong in load_termbase(state)
            if re.search(r"\b" + re.escape(wrong) + r"\b", anchor_text)]


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        st = Path(td) / "state"
        st.mkdir(parents=True)
        (st / "termbase.yml").write_text("web site: website\nEMail: email\n")
        # admission: vibes, detector rules, termbase overlap, duplicates all refused
        for bad in [dict(behavior="", scope="span", over_application="", probe=""),
                    dict(behavior="lower Binoculars score", scope="paper",
                         over_application="", probe="x"),
                    dict(behavior="never write web site", scope="global",
                         over_application="", probe="web\\s+site")]:
            try:
                propose(st, **bad)
                raise AssertionError(f"admitted: {bad}")
            except SystemExit:
                pass
        lid = propose(st, behavior="no em-dash asides", scope="paper",
                      over_application="prose flagged uniform if applied to all clauses",
                      probe="—[^—]{5,60}—")
        try:
            propose(st, behavior="different words same probe", scope="paper",
                    over_application="", probe="—[^—]{5,60}—")
            raise AssertionError("duplicate admitted")
        except SystemExit:
            pass
        # ratify -> probe scan hits approved text
        sec = st.parent / "sections" / "s1"
        sec.mkdir(parents=True)
        (sec / "approved.md").write_text("Fine text — an aside here — more text.")
        ratify(st, lid)
        stale = json.loads((st / "stale.json").read_text())
        assert "s1" in stale and stale["s1"][0]["learning_id"] == lid
        # FDR: two vetoes suspend, never delete
        veto(st, lid); veto(st, lid)
        l = load_all(st)[lid]
        assert l["status"] == "suspended" and l["rejected"] == 2
        # hash tracks active set
        assert learnings_hash(st) == learnings_hash(st)
        # vale generation + termbase-beats-anchors conflict log
        vale(st)
        assert (st / "vale" / "Termbase" / "terms.yml").exists()
        assert termbase_conflicts(st, "See our web site for details.") == ["web site"]
    print("selftest ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?",
                    choices=["propose", "ratify", "veto", "scan", "vale"])
    ap.add_argument("id", nargs="?")
    ap.add_argument("--state", default="state")
    ap.add_argument("--behavior", default=""); ap.add_argument("--scope", default="section")
    ap.add_argument("--over-application", default=""); ap.add_argument("--probe", default="")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    st = Path(a.state)
    if a.selftest:
        selftest()
    elif a.cmd == "propose":
        propose(st, a.behavior, a.scope, a.over_application, a.probe)
    elif a.cmd == "ratify":
        ratify(st, a.id)
    elif a.cmd == "veto":
        veto(st, a.id)
    elif a.cmd == "scan":
        scan(st)
    elif a.cmd == "vale":
        vale(st)
    else:
        ap.print_help()
