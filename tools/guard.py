#!/usr/bin/env python3
"""B2 guard stack — Gate G4 (DESIGN.md §5; design basis research/12).

Usage:  python3 tools/guard.py --skeleton s.md --output o.md [--sources src.md]
            [--author-span a.md] [--witness] [--entailment minicheck|alignscore|none]
        python3 tools/guard.py --selftest

Verdict policy (in code, never in a model):
  PASS only if: no typed FAIL finding, no UNCHECKABLE alignment, multiset diffs
  clean, mechanics lock clean, entailment (when a backend is wired) clean.
  UNCHECKABLE is a FAIL, never a pass.

Layers:
  0  alignment      skeleton claim <-> output sentence, content-word overlap;
                    unaligned output sentence = UNCHECKABLE
  1  typed diff     factwash.inspect (adopted, Apache-2.0) when importable, plus
                    supplements it lacks: booster-insert, condition-drop,
                    investigation-subtype hedges (tools/guard_lexicon.json).
                    Windows are the measured ones: hedges = matched sentence +-1;
                    negation/attribution = matched sentence alone.
  1b multiset diff  citations / numbers / capitalized-entity multisets must match
                    exactly (deterministic).
  1c mechanics lock author-written spans: contractions and idiosyncratic
                    punctuation/spacing are protected tokens; normalization = FAIL.
  2  witness        one sentence, two booleans (hedged? attributed?) + quoted
                    markers span-validated; skeleton side witnessed once, cached in
                    <state>/witness_cache.json; OpenRouter, off unless --witness.
                    Never returns a verdict — it only enriches the source-side
                    marker inventory.
  3  entailment     AlignScore/MiniCheck wrapper; backend 'none' declares
                    not_checked (never silently passes). Model install is a
                    test-phase task.

Never built (frozen): any certainty-score gate. Pairwise certainty judge is
--diagnostic only and is not implemented here (test-phase diagnostics live with the
grader).
"""
import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

LEX = json.loads((Path(__file__).parent / "guard_lexicon.json").read_text())
CITE_RE = re.compile(
    r"\(([A-Z][A-Za-z\-']+(?:\s+(?:et al\.|&\s*[A-Z][A-Za-z\-']+))?),?\s+(\d{4}[a-z]?)\)")
NUM_RE = re.compile(r"(?<![\w.])\d+(?:\.\d+)?%?")
ENTITY_RE = re.compile(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+|[A-Z]{2,})\b")

try:
    import factwash  # adopted layer-1 core (venv: .venv/bin/python)
except ImportError:
    factwash = None


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def content_words(s: str) -> set:
    stop = {"the", "a", "an", "of", "to", "in", "and", "or", "is", "are", "was",
            "that", "this", "it", "for", "on", "with", "as", "by", "be"}
    return {w for w in re.findall(r"[a-z']+", s.lower()) if w not in stop and len(w) > 2}


def find_markers(sent: str, classes=("hedges", "investigation", "attribution",
                                     "conditions", "boosters", "negations")) -> Counter:
    """Typed marker multiset for one sentence; word-boundary, longest-phrase-first."""
    low = " " + re.sub(r"\s+", " ", sent.lower()) + " "
    found = Counter()
    for cls in classes:
        for cue in sorted(LEX[cls], key=len, reverse=True):
            n = len(re.findall(r"(?<![a-z'])" + re.escape(cue) + r"(?![a-z])", low)) \
                if cue != "n't" else low.count("n't")
            if n:
                found[(cls, cue)] += n
    return found


def align(skeleton_claims: list[str], out_sents: list[str], thresh=0.25):
    """claim index -> [output sentence indices]; plus unaligned output sentences."""
    pairs, used = {}, set()
    for ci, claim in enumerate(skeleton_claims):
        cw = content_words(claim)
        matches = [si for si, s in enumerate(out_sents)
                   if cw and len(cw & content_words(s)) / len(cw) >= thresh]
        pairs[ci] = matches
        used.update(matches)
    unaligned = [si for si in range(len(out_sents)) if si not in used]
    return pairs, unaligned


def window(sents: list[str], idxs: list[int], radius: int) -> str:
    take = sorted({j for i in idxs for j in range(max(0, i - radius),
                                                  min(len(sents), i + radius + 1))})
    return " ".join(sents[j] for j in take)


def typed_diff(claim: str, out_sents: list[str], matched: list[int],
               src_extra_markers: Counter | None = None) -> list[dict]:
    """Directional typed diff for one aligned claim. Windows per research/12."""
    findings = []
    src = find_markers(claim)
    if src_extra_markers:
        src = src + src_extra_markers
    hedge_out = find_markers(window(out_sents, matched, 1),
                             ("hedges", "investigation"))
    tight_out = find_markers(window(out_sents, matched, 0),
                             ("attribution", "conditions", "negations"))
    boost_out = find_markers(window(out_sents, matched, 0), ("boosters",))

    def dropped(cls, out_counter):
        return [(c, cue) for (c, cue), n in src.items()
                if c == cls and out_counter[(c, cue)] < n]

    for c, cue in dropped("hedges", hedge_out) + dropped("investigation", hedge_out):
        findings.append({"type": "DROPPED", "property": "hedge", "cue": cue,
                         "claim": claim, "severity": "fail"})
    for c, cue in dropped("attribution", tight_out):
        findings.append({"type": "DROPPED", "property": "attribution", "cue": cue,
                         "claim": claim, "severity": "fail"})
    for c, cue in dropped("conditions", tight_out):
        findings.append({"type": "DROPPED", "property": "condition", "cue": cue,
                         "claim": claim, "severity": "fail"})
    src_neg = sum(n for (c, _), n in src.items() if c == "negations")
    out_neg = sum(n for (c, _), n in tight_out.items() if c == "negations")
    if (src_neg > 0) != (out_neg > 0):
        findings.append({"type": "REVERSED", "property": "polarity", "claim": claim,
                         "severity": "fail"})
    src_boost = {cue for (c, cue) in src if c == "boosters"}
    for (c, cue), n in boost_out.items():
        if cue not in src_boost:
            findings.append({"type": "ADDED", "property": "booster", "cue": cue,
                             "claim": claim, "severity": "fail"})
    return findings


def factwash_diff(claim: str, matched_text: str) -> list[dict]:
    """factwash per aligned claim (it is calibrated for single-claim writes;
    whole-document input misattributes cues across claims)."""
    if factwash is None:
        return [{"type": "NOT_CHECKED", "property": "factwash",
                 "note": "factwash not importable — run under .venv/bin/python",
                 "severity": "info"}]
    r = factwash.inspect(claim, matched_text)
    return [{"type": c.type, "property": c.property, "evidence": c.evidence,
             "severity": "fail", "engine": "factwash"} for c in r.changes]


def multiset_diff(certified: str, output: str) -> list[dict]:
    findings = []
    for name, rx in (("citation", CITE_RE), ("number", NUM_RE), ("entity", ENTITY_RE)):
        a = Counter(m.group(0) if name != "citation" else m.group(0)
                    for m in rx.finditer(certified))
        b = Counter(m.group(0) for m in rx.finditer(output))
        if name == "entity":  # entities certified at G3 = those in the skeleton
            missing = a - b
            extra = Counter()
        else:
            missing, extra = a - b, b - a
        for tok, n in missing.items():
            findings.append({"type": "MISSING", "property": name, "token": tok,
                             "count": n, "severity": "fail"})
        for tok, n in extra.items():
            findings.append({"type": "INVENTED", "property": name, "token": tok,
                             "count": n, "severity": "fail"})
    return findings


def mechanics_lock(author_span: str, output: str) -> list[dict]:
    """Author-written spans: contractions and idiosyncratic punctuation are
    protected tokens (research/14). Any normalization = FAIL."""
    findings = []
    protected = re.findall(r"[A-Za-z]+'[a-z]+", author_span)          # contractions
    protected += re.findall(r"(?:—|–|\.\.\.|;|!|\?)", author_span)     # punctuation habits
    need, have = Counter(protected), Counter(
        re.findall(r"[A-Za-z]+'[a-z]+|—|–|\.\.\.|;|!|\?", output))
    for tok, n in (need - have).items():
        findings.append({"type": "NORMALIZED", "property": "mechanics", "token": tok,
                         "count": n, "severity": "fail"})
    return findings


def entailment(skeleton: str, output: str, sources: str, backend: str) -> list[dict]:
    """Bidirectional entailment wrapper. Backends are heavy local models
    (AlignScore 355M / MiniCheck 770M, clones in the Humanising-Realtime repo);
    installing them is a test-phase task. 'none' declares itself, never passes."""
    if backend == "none":
        return [{"type": "NOT_CHECKED", "property": "entailment",
                 "note": "no backend wired; install AlignScore/MiniCheck (test phase)",
                 "severity": "info"}]
    sys.exit(f"entailment backend '{backend}' not installed yet — "
             "clone+install from Humanising-Realtime/sources/repos/ (test phase)")


WITNESS_PROMPT = (
    "Answer about exactly this one sentence, nothing else.\n"
    'Sentence: "{sent}"\n'
    "Q1: Is any claim in it hedged (uncertain, qualified)? true/false.\n"
    "Q2: Is any claim in it attributed to a source or person? true/false.\n"
    "Reply as JSON: {{\"hedged\": bool, \"attributed\": bool, "
    "\"markers\": [exact words from the sentence that made you answer true]}}")


def witness_sentence(sent: str, cache: dict, model: str) -> Counter:
    """Layer 2: two booleans + span-validated markers -> extra source-side markers.
    Never a verdict. Cached per sentence (the skeleton is written once, re-read
    every tick)."""
    if sent in cache:
        ans = cache[sent]
    else:
        sys.path.insert(0, str(Path(__file__).parent))
        from meld import call  # reuse the OpenRouter client + retry
        raw = call(model, "", WITNESS_PROMPT.format(sent=sent), 0.0)
        try:
            ans = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
        except Exception:
            return Counter()  # discarded; deterministic verdict stands
        ans["markers"] = [m for m in ans.get("markers", [])
                          if m.lower() in sent.lower()]  # span-validate
        cache[sent] = ans
    extra = Counter()
    for m in ans.get("markers", []):
        if ans.get("hedged"):
            extra[("hedges", m.lower())] += 1
        if ans.get("attributed"):
            extra[("attribution", m.lower())] += 1
    return extra


def guard(skeleton: str, output: str, sources: str = "", author_span: str = "",
          use_witness=False, entail_backend="none", state=Path("state"),
          witness_model="google/gemini-3.1-flash-lite") -> dict:
    claims = [c.strip("-* \t") for c in skeleton.strip().splitlines() if c.strip()]
    out_sents = sentences(output)
    pairs, unaligned = align(claims, out_sents)

    cache_file = state / "witness_cache.json"
    cache = json.loads(cache_file.read_text()) if cache_file.exists() else {}

    findings = []
    for ci, claim in enumerate(claims):
        if not pairs[ci]:
            findings.append({"type": "MISSING", "property": "claim", "claim": claim,
                             "severity": "fail"})
            continue
        extra = witness_sentence(claim, cache, witness_model) if use_witness else None
        findings += typed_diff(claim, out_sents, pairs[ci], extra)
        findings += factwash_diff(claim, window(out_sents, pairs[ci], 1))
    for si in unaligned:
        findings.append({"type": "UNCHECKABLE", "property": "alignment",
                         "sentence": out_sents[si], "severity": "fail"})
    findings += multiset_diff(skeleton + "\n" + sources, output)
    if author_span:
        findings += mechanics_lock(author_span, output)
    findings += entailment(skeleton, output, sources, entail_backend)

    if use_witness and cache:
        state.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(cache, indent=1))

    fails = [f for f in findings if f["severity"] == "fail"]
    not_checked = sorted({f["property"] for f in findings if f["type"] == "NOT_CHECKED"})
    return {"verdict": "FAIL" if fails else "PASS", "findings": findings,
            "not_checked": not_checked}  # a report listing only what it found
                                         # reads as "nothing else happened"


def selftest():
    sk = "- The drug may reduce symptoms (Smith, 2020).\n- Uptake was 40% in the trial."
    ok = "The drug may reduce symptoms (Smith, 2020). Uptake was 40% in the trial."
    r = guard(sk, ok)
    assert r["verdict"] == "PASS", r["findings"]
    assert "entailment" in r["not_checked"]

    # in-lexicon hedge drop
    r = guard(sk, "The drug reduces symptoms (Smith, 2020). Uptake was 40% in the trial.")
    assert any(f["type"] == "DROPPED" and f["property"] == "hedge"
               for f in r["findings"]) and r["verdict"] == "FAIL"

    # booster insert (the class factwash lacks)
    r = guard(sk, "The drug may clearly reduce symptoms (Smith, 2020). "
                  "Uptake was 40% in the trial.")
    assert any(f["type"] == "ADDED" and f["property"] == "booster"
               for f in r["findings"]), r["findings"]

    # polarity flip
    sk2 = "- The effect was not significant."
    r = guard(sk2, "The effect was significant.")
    assert any(f["property"] == "polarity" for f in r["findings"])

    # citation moved/dropped + invented number
    r = guard(sk, "The drug may reduce symptoms. Uptake was 40% in the trial, "
                  "rising to 60% (Jones, 2019).")
    props = {(f["type"], f["property"]) for f in r["findings"]}
    assert ("MISSING", "citation") in props and ("INVENTED", "citation") in props
    assert ("INVENTED", "number") in props

    # UNCHECKABLE on an unalignable output sentence — a fail, never a pass
    r = guard(sk, ok + " Quantum flux inverts the polymer lattice.")
    assert any(f["type"] == "UNCHECKABLE" for f in r["findings"])
    assert r["verdict"] == "FAIL"

    # mechanics lock: author's contraction + em-dash survive or FAIL
    r_m = mechanics_lock("It doesn't work — at all.", "It does not work, at all.")
    assert {f["token"] for f in r_m} == {"doesn't", "—"}
    assert mechanics_lock("It doesn't work — at all.", "It doesn't work — at all.") == []

    # true paraphrase of a hedge is not flagged (both cues in lexicon, both present)
    r = guard("- X may contribute to Y.", "X could play a part in Y.")
    hedge_drops = [f for f in r["findings"]
                   if f["type"] == "DROPPED" and f["property"] == "hedge"]
    assert not any(f["cue"] == "could" for f in hedge_drops)

    # witness span-validation: markers not in the sentence are discarded
    fake_cache = {"s": {"hedged": True, "attributed": False, "markers": ["may"]}}
    assert witness_sentence("s", fake_cache, "m")[("hedges", "may")] == 1

    print("selftest ok" + ("" if factwash else "  (factwash absent — builtin diff only)"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skeleton"); ap.add_argument("--output")
    ap.add_argument("--sources", default=""); ap.add_argument("--author-span", default="")
    ap.add_argument("--witness", action="store_true")
    ap.add_argument("--entailment", default="none",
                    choices=["none", "alignscore", "minicheck"])
    ap.add_argument("--state", default="state")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    elif a.skeleton and a.output:
        rep = guard(Path(a.skeleton).read_text(), Path(a.output).read_text(),
                    Path(a.sources).read_text() if a.sources else "",
                    Path(a.author_span).read_text() if a.author_span else "",
                    a.witness, a.entailment, Path(a.state))
        print(json.dumps(rep, indent=1))
        sys.exit(0 if rep["verdict"] == "PASS" else 1)
    else:
        ap.print_help()
