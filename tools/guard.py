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
import importlib.util
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
    """Prose sentences. Markdown furniture (heading hashes, list markers) is stripped
    but the TEXT of those lines is kept: deleting heading lines outright meant an
    assertion written as "## Retrofits improve comfort" reached no layer at all and
    survived the polish unchecked. Only "et al." suppresses a split — a lookbehind for
    any capital-plus-period also merged sentences ending in US. / EU. / NHS. with the
    next one, hiding a fabricated sentence from the UNCHECKABLE check (2026-09-01)."""
    prose = re.sub(r"(?m)^\s*#{1,6}\s*", "", text.strip())
    prose = re.sub(r"(?m)^\s*(?:[-*•]|\d+[.)])\s+", "", prose)
    return [s.strip() for s in re.split(r"(?<!et al\.)(?<=[.!?])\s+", prose.strip()) if s.strip()]


NARR_CITE_RE = re.compile(
    r"\b([A-Z][A-Za-z\-']+(?:\s+(?:et al\.|(?:&|and)\s+[A-Z][A-Za-z\-']+))?)\s+\((\d{4}[a-z]?)\)")


def citations(text: str) -> Counter:
    """Canonical 'Author, 2020' keys for BOTH forms — (Author, 2020) and Author (2020).
    A citation that changed form between skeleton and prose is preserved, not missing."""
    keys = [f"{a}, {y}" for a, y in CITE_RE.findall(text)]
    keys += [f"{re.sub(r"'s$", '', a).replace(' and ', ' & ')}, {y}" for a, y in NARR_CITE_RE.findall(text)]
    return Counter(keys)


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
    """claim index -> [best output sentence index]; plus unaligned output sentences.

    One claim aligns to its ONE best-overlapping sentence (ties: all tied). The
    earlier form kept every sentence above the threshold, so in connected prose a
    claim was compared against a union of three or four sentences and every
    negation, booster or attribution cue in any of them counted against it —
    the bulk of the false positives on the first end-to-end pass (2026-09-01)."""
    pairs, used = {}, set()
    for ci, claim in enumerate(skeleton_claims):
        cw = content_words(claim)
        scored = [(len(cw & content_words(s)) / len(cw), si) for si, s in enumerate(out_sents)] if cw else []
        best = max((sc for sc, _ in scored), default=0.0)
        matches = [si for sc, si in scored if sc >= thresh and sc == best]
        pairs[ci] = matches
        used.update(matches)
    unaligned = [si for si in range(len(out_sents)) if si not in used]
    return pairs, unaligned


def window(sents: list[str], idxs: list[int], radius: int) -> str:
    take = sorted({j for i in idxs for j in range(max(0, i - radius),
                                                  min(len(sents), i + radius + 1))})
    return " ".join(sents[j] for j in take)


HEDGE_CLASSES = ("hedges", "investigation")  # Szeged's investigation subtype is a
                                             # real hedge in a paper (research/12)


def _count(counter: Counter, classes) -> int:
    return sum(n for (c, _), n in counter.items() if c in classes)


def typed_diff(claim: str, out_sents: list[str], matched: list[int],
               src_extra_markers: Counter | None = None,
               out_extra_markers: Counter | None = None) -> tuple[list[dict], dict]:
    """Directional typed diff for one aligned claim. Windows per research/12.

    *Typed* means the diff is over marker CLASSES, not cue identities — research/12
    specifies a typed directional change set and says in terms 'never a bare set
    difference'. Swapping one hedge for another of the same class ('may' -> 'could',
    'appears to' -> 'seems to') leaves the class count intact and is a paraphrase,
    not a DROPPED hedge; diffing cue identities flags every such paraphrase, which
    is what the TRUE-PARAPHRASE control exists to catch (T1 caught it).

    A change of strength WITHIN a class is therefore not detected here, and is
    declared not_checked rather than silently passed: never gate on a certainty
    score (research/12 finding 4 — the strongest published classifier saturates on
    exactly these pairs).

    Returns (findings, preserved) where preserved[property] is True when that
    class survived the write; the caller uses it to demote factwash findings that
    are artefacts of a lexicon gap our supplement covers."""
    findings = []
    # Witness cues merge by UNION, not sum, on BOTH sides (T1b defect): summing
    # double-counts cues the lexicon already found (identical text self-flags), and
    # witnessing only the source makes every preserved out-of-lexicon hedge read as
    # dropped — the same bare-cue-diff failure mode T1 fixed in the lexicon layer.
    src = find_markers(claim)
    if src_extra_markers:
        src = src | src_extra_markers
    # The count stage sees ONE sentence and the hedge identity stage sees +-1. A
    # "radius" knob that widened the count stage to +-1 was added 2026-09-01 to quiet
    # false positives on prose written from a skeleton, and removed the same day: it
    # is the exact configuration measured at in-lexicon hedge recall 0.17 (see
    # dropped() below), it also fed the polarity and booster checks a three-sentence
    # window and manufactured false REVERSED/ADDED findings, and the float case it
    # claimed to fix is already handled by the identity stage against `wide`.
    tight = find_markers(window(out_sents, matched, 0))
    wide = find_markers(window(out_sents, matched, 1), HEDGE_CLASSES)
    if out_extra_markers:
        tight = tight | out_extra_markers
        wide = wide | Counter({k: n for k, n in out_extra_markers.items()
                               if k[0] in HEDGE_CLASSES})

    def dropped(classes, prop, out_wide=None):
        """Two-stage, and both stages are load-bearing.

        Count stage (matched sentence only): the class must have shrunk. A source
        sentence is one sentence, so it is compared against one sentence — counting
        the whole +-1 window here lets a neighbour's hedges mask a real deletion
        (measured: in-lexicon recall 1.00 -> 0.17 on T1's seeds).

        Identity stage (+-1 for hedges): a cue still present nearby has floated, not
        gone — which is the only thing the wider window is for (research/12:
        'hedges float across sentence boundaries')."""
        deficit = _count(src, classes) - _count(tight, classes)
        if deficit <= 0:
            return
        look = out_wide if out_wide is not None else tight
        gone = [cue for (c, cue), n in src.items()
                if c in classes and look[(c, cue)] < n]
        for cue in gone[:deficit]:
            findings.append({"type": "DROPPED", "property": prop, "cue": cue,
                             "claim": claim, "severity": "fail"})

    dropped(HEDGE_CLASSES, "hedge", wide)
    dropped(("attribution",), "attribution")
    dropped(("conditions",), "condition")

    src_neg, out_neg = _count(src, ("negations",)), _count(tight, ("negations",))
    if (src_neg > 0) != (out_neg > 0):
        findings.append({"type": "REVERSED", "property": "polarity", "claim": claim,
                         "severity": "fail"})

    surplus = _count(tight, ("boosters",)) - _count(src, ("boosters",))
    if surplus > 0:
        new = [cue for (c, cue), n in tight.items()
               if c == "boosters" and n > src[(c, cue)]]
        for cue in new[:surplus]:
            findings.append({"type": "ADDED", "property": "booster", "cue": cue,
                             "claim": claim, "severity": "fail"})

    emitted = {f["property"] for f in findings}
    preserved = {p: p not in emitted
                 for p in ("hedge", "attribution", "condition", "polarity", "booster")}
    return findings, preserved


# factwash's property name -> the classes our supplemented lexicon covers for it.
FACTWASH_PROPERTY_MAP = {"certainty": ("hedge", "booster"),
                         "attribution": ("attribution",),
                         "polarity": ("polarity",),
                         "condition": ("condition",)}


def factwash_diff(claim: str, matched_text: str,
                  preserved: dict | None = None) -> list[dict]:
    """factwash per aligned claim (it is calibrated for single-claim writes;
    whole-document input misattributes cues across claims).

    A factwash finding is demoted to `info` when our own typed diff shows every
    class it maps to survived the write. factwash's HEDGE lexicon is built for
    memory writes: it carries 'may ' and 'could be' but not bare 'could', so
    'may facilitate' -> 'could facilitate' reads to it as a stripped hedge. That is
    the coverage gap tools/guard_lexicon.json exists to close (research/12: retune
    factwash, do not rebuild it). The demotion is symmetric and can only fire when
    the supplement positively shows the class intact — a genuine drop takes the
    class count with it and stays a FAIL."""
    if factwash is None:
        return [{"type": "NOT_CHECKED", "property": "factwash",
                 "note": "factwash not importable — run under .venv/bin/python",
                 "severity": "info"}]
    out = []
    for c in factwash.inspect(claim, matched_text).changes:
        ours = FACTWASH_PROPERTY_MAP.get(c.property, ())
        demote = bool(ours) and preserved is not None and \
            all(preserved.get(k, False) for k in ours)
        f = {"type": c.type, "property": c.property, "evidence": c.evidence,
             "severity": "info" if demote else "fail", "engine": "factwash"}
        if demote:
            f["demoted"] = "class count preserved under the academic-register supplement"
        out.append(f)
    return out


NUM_WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
             "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20,
             "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
             "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000}  # not "one": determiner/pronoun


def _digits(text: str) -> str:
    """'thirty days' and '30 days' are the same number (adjust-in-use 2026-09-01)."""
    return re.sub(r"\b(" + "|".join(NUM_WORDS) + r")\b",
                  lambda m: str(NUM_WORDS[m.group(1).lower()]), text, flags=re.I)


def apply_gate(rep: dict, gate: set) -> dict:
    """Restrict which finding classes may FAIL at this stage; every other failing
    finding becomes a warning for the author's sitting (never dropped). The gate is
    a set of (type, property) pairs."""
    for f in rep["findings"]:
        if f["severity"] == "fail" and (f["type"], f.get("property")) not in gate:
            f["severity"] = "warn"
            f["gated"] = "warn-only at this stage"
    fails = [f for f in rep["findings"] if f["severity"] == "fail"]
    rep["warnings"] = sum(f["severity"] == "warn" for f in rep["findings"])
    rep["verdict"] = "FAIL" if fails else "PASS"
    return rep


def multiset_diff(skeleton: str, output: str, sources: str = "") -> list[dict]:
    """Two directions, two reference sets (first end-to-end pass, 2026-09-01):
    MISSING  = in the locked skeleton but not in the output (a claim's number,
               citation or named entity was lost) — the skeleton is the reference,
               never the sources: a section does not have to repeat every figure
               its sources contain.
    INVENTED = in the output but in neither skeleton nor sources (a number or
               citation with no certified origin). Entities are not checked for
               invention: ordinary prose introduces capitalised phrases freely."""
    findings = []
    certified = skeleton + "\n" + sources
    for name, rx in (("citation", None), ("number", NUM_RE), ("entity", ENTITY_RE)):
        if name == "citation":
            sk, cert, out = citations(skeleton), citations(certified), citations(output)
        else:
            norm = _digits if name == "number" else (lambda t: t)
            sk = Counter(m.group(0) for m in rx.finditer(norm(skeleton)))
            cert = Counter(m.group(0) for m in rx.finditer(norm(certified)))
            out = Counter(m.group(0) for m in rx.finditer(norm(output)))
        missing = sk - out
        extra = Counter() if name == "entity" else out - cert
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


MODEL_DIR = os.environ.get(
    "OWNVOICE_MODEL_DIR", str(Path(__file__).parent.parent / ".models"))
_SCORER = {}  # backend -> loaded model; 770M, load once per process


def _scorer(backend: str):
    """Lazy singleton. MiniCheck-Flan-T5-Large (770M) is the wired backend (T1).

    Runs on CPU by default, measured at ~0.2 s/pair and ~5 s to load — ample for a
    gate that sees a few hundred pairs per tick. The GPU path is blocked on this
    box, not by VRAM (16 GB is plenty): torch 2.13 routes a T5 attention op to a
    Triton kernel, and Triton JIT-compiles its CUDA glue with gcc against Python
    headers that NixOS does not ship in the system profile. Set
    OWNVOICE_ENTAIL_DEVICE=auto to try the GPU once those exist."""
    if backend not in _SCORER:
        if backend != "minicheck":
            sys.exit(f"entailment backend '{backend}' not installed — only "
                     "'minicheck' is wired (T1); AlignScore's pins do not build "
                     "on py3.13")
        if not importlib.util.find_spec("minicheck"):
            sys.exit("entailment backend 'minicheck' requested but the package is not "
                     "importable by this interpreter. Install the optional guard extras "
                     "(see README), or pass --entailment none to run the lexicon layer "
                     "alone.")
        if os.environ.get("OWNVOICE_ENTAIL_DEVICE", "cpu") == "cpu":
            os.environ["CUDA_VISIBLE_DEVICES"] = ""  # before torch initialises cuda
        from minicheck.minicheck import MiniCheck
        _SCORER[backend] = MiniCheck(model_name="flan-t5-large",
                                     cache_dir=MODEL_DIR)
    return _SCORER[backend]


def entailment(skeleton: str, output: str, sources: str, backend: str) -> list[dict]:
    """Bidirectional entailment (DESIGN §5 layer 1), MiniCheck-Flan-T5-Large.

    skeleton -> text: every locked meaning item must be asserted by the output
                      (catches dropped concepts).
    text -> skeleton+sources: every output sentence must be supported by the
                      certified material (catches invention).
    'none' declares itself not_checked; it never silently passes."""
    if backend == "none":
        return [{"type": "NOT_CHECKED", "property": "entailment",
                 "note": "no backend wired; pass --entailment minicheck",
                 "severity": "info"}]
    scorer = _scorer(backend)
    claims = [c.strip("-* \t") for c in skeleton.strip().splitlines() if c.strip()]
    out_sents = sentences(output)
    findings = []
    # Detector, not policy: every entailment finding is a "fail" here. On real
    # section prose MiniCheck marks sentences that restate skeleton claims as
    # unsupported (p 0.27-0.38) — the premise is a whole skeleton plus sources, far
    # from the single-claim setting T1 measured it in — so tock demotes it to a
    # warning via apply_gate. That demotion belongs in ONE place: severity here is
    # what bench_guard.py counts as a detection (it filters on severity == "fail"),
    # so downgrading at this layer silently rewrote 7 seeds' entailment_clean flags
    # and inverted research/12 validation 3 (caught 2026-09-01).
    sev = "fail"
    if claims and output.strip():  # direction 1: is each locked item asserted?
        lab, prob, _, _ = scorer.score(docs=[output] * len(claims), claims=claims)
        for claim, ok, p in zip(claims, lab, prob):
            if not ok:
                findings.append({"type": "MISSING", "property": "entailment",
                                 "claim": claim, "prob": round(float(p), 4),
                                 "severity": sev, "engine": "minicheck"})
    ref = (skeleton + "\n" + sources).strip()
    if out_sents and ref:  # direction 2: is each written sentence supported?
        lab, prob, _, _ = scorer.score(docs=[ref] * len(out_sents), claims=out_sents)
        for sent, ok, p in zip(out_sents, lab, prob):
            if not ok:
                findings.append({"type": "INVENTED", "property": "entailment",
                                 "sentence": sent, "prob": round(float(p), 4),
                                 "severity": sev, "engine": "minicheck"})
    return findings


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
        from meld import call, OPENROUTER  # reuse the OpenRouter client + retry
        # Off OpenRouter (the P1 via OmniRoute) the witness is qwen3.8-flash with
        # thinking off, Chris's choice 2026-10-06; OpenRouter keeps the measured default.
        raw = call(model, "", WITNESS_PROMPT.format(sent=sent), 0.0,
                   thinking="default" if OPENROUTER else "off")
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


def entail_default() -> str:
    """MiniCheck runs iff its weights are already in MODEL_DIR — never triggers a
    download. T1 measured it complementary to the lexicon gate (4/4 attribution
    drops, 0.00 of hedge drops), so the production path should not leave it off.
    OWNVOICE_ENTAIL=none forces it off; OWNVOICE_ENTAIL=minicheck forces it on."""
    forced = os.environ.get("OWNVOICE_ENTAIL", "").strip()
    if forced:
        return forced
    if not any(Path(MODEL_DIR).glob("models--lytang--MiniCheck*")):
        return "none"
    # Weights on disk are not enough — the package must be importable in THIS
    # interpreter. Gating on the weights alone raised a bare ModuleNotFoundError out
    # of a T5 attention import for anyone whose python lacks minicheck, which is the
    # first thing a second machine does (2026-09-03).
    return "minicheck" if importlib.util.find_spec("minicheck") else "none"


def witness_available() -> bool:
    """The witness defaults ON wherever a key exists: measured out-of-lexicon hedge
    recall 0.33 -> 1.00 at 0.00 false positives for ~$0.005 per 30 paragraphs
    (steps/T1b-witness-measurement.md). OWNVOICE_WITNESS=0 forces it off."""
    sys.path.insert(0, str(Path(__file__).parent))
    from meld import dotenv
    env = dotenv()
    # Read the switch the same way the key is read. It was environment-only, so
    # setting OWNVOICE_WITNESS=0 in .env — the one config file the docs point at, and
    # the documented way to stop sentences leaving the machine — did nothing at all.
    off = (os.environ.get("OWNVOICE_WITNESS") or env.get("OWNVOICE_WITNESS", "")).lower()
    if off in ("0", "off", "false", "no"):
        return False
    return bool(os.environ.get("OPENROUTER_API_KEY") or env.get("OPENROUTER_API_KEY"))


def guard(skeleton: str, output: str, sources: str = "", author_span: str = "",
          use_witness="auto", entail_backend="auto", state=Path("state"),
          witness_model="google/gemini-3.1-flash-lite") -> dict:
    if use_witness == "auto":
        use_witness = witness_available()
    if entail_backend == "auto":
        entail_backend = entail_default()
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
        extra = out_extra = None
        if use_witness:
            extra = witness_sentence(claim, cache, witness_model)
            out_extra = Counter()
            for si in pairs[ci]:
                out_extra += witness_sentence(out_sents[si], cache, witness_model)
        typed, preserved = typed_diff(claim, out_sents, pairs[ci], extra, out_extra)
        findings += typed
        findings += factwash_diff(claim, window(out_sents, pairs[ci], 1), preserved)
    for si in unaligned:
        # A fail here, as a detector: an output sentence no claim covers is exactly
        # what "never silently passes" means. Connected prose legitimately carries
        # linking sentences, so tock demotes this to a warning through apply_gate —
        # policy lives there, never in the detector (see entailment() above).
        findings.append({"type": "UNCHECKABLE", "property": "alignment",
                         "sentence": out_sents[si], "severity": "fail"})
    findings += multiset_diff(skeleton, output, sources)
    if author_span:
        findings += mechanics_lock(author_span, output)
    findings += entailment(skeleton, output, sources, entail_backend)
    # research/12: change types with no detector are declared on every report,
    # because a report listing only what it found reads as "nothing else happened".
    findings.append({"type": "NOT_CHECKED", "property": "certainty_gradation",
                     "note": "strength change within a marker class (may -> likely) "
                             "and BROADENED/WEAKENED scope have no detector by "
                             "design; the human is the backstop at G5",
                     "severity": "info"})

    if use_witness and cache:
        state.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(cache, indent=1))

    fails = [f for f in findings if f["severity"] == "fail"]
    warns = [f for f in findings if f["severity"] == "warn"]
    not_checked = sorted({f["property"] for f in findings if f["type"] == "NOT_CHECKED"})
    return {"verdict": "FAIL" if fails else "PASS", "findings": findings,
            "warnings": len(warns),  # for the author's sitting; never gate
            "not_checked": not_checked}  # a report listing only what it found
                                         # reads as "nothing else happened"


def selftest():
    os.environ["OWNVOICE_WITNESS"] = "0"  # selftests are offline and deterministic
    os.environ["OWNVOICE_ENTAIL"] = "none"  # the entailment path has its own selftest
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

    # UNCHECKABLE on an unalignable output sentence — a fail in the detector, never
    # a pass; tock is what demotes it for connected prose (apply_gate)
    r = guard(sk, ok + " Quantum flux inverts the polymer lattice.")
    assert any(f["type"] == "UNCHECKABLE" for f in r["findings"])
    assert r["verdict"] == "FAIL"
    # apply_gate is the ONLY place a detection is demoted to a warning. This must be
    # tested with a report that CONTAINS the gated class: the first version of this
    # test gated on ("MISSING","claim") against a report that had none, so the gate
    # matched nothing and the assertion held under any policy at all (2026-09-01).
    drift = guard(sk, "The drug reduces symptoms. Uptake was 40% in the trial.")
    kinds = {(f["type"], f["property"]) for f in drift["findings"] if f["severity"] == "fail"}
    assert ("DROPPED", "hedge") in kinds and ("MISSING", "citation") in kinds, kinds
    g = apply_gate(json.loads(json.dumps(drift)), {("MISSING", "citation")})
    still_fail = {(f["type"], f["property"]) for f in g["findings"] if f["severity"] == "fail"}
    assert still_fail == {("MISSING", "citation")}, still_fail   # gated class survives
    assert g["verdict"] == "FAIL" and g["warnings"] >= 1
    demoted = [f for f in g["findings"]
               if (f["type"], f["property"]) == ("DROPPED", "hedge")]
    assert demoted and all(f["severity"] == "warn" and f.get("gated") for f in demoted)
    # an empty gate demotes everything; no finding is ever dropped
    g2 = apply_gate(json.loads(json.dumps(drift)), set())
    assert g2["verdict"] == "PASS" and len(g2["findings"]) == len(drift["findings"])
    assert not any(f["severity"] == "fail" for f in g2["findings"])
    # one claim aligns to its single best sentence, not to every sentence it overlaps
    pairs, _ = align(["The drug may reduce symptoms."],
                     ["The drug may reduce symptoms.", "The drug did not reduce costs."])
    assert pairs == {0: [0]}, pairs

    # mechanics lock: author's contraction + em-dash survive or FAIL
    r_m = mechanics_lock("It doesn't work — at all.", "It does not work, at all.")
    assert {f["token"] for f in r_m} == {"doesn't", "—"}
    assert mechanics_lock("It doesn't work — at all.", "It doesn't work — at all.") == []

    # TRUE-PARAPHRASE control (research/12): a same-class marker swap is a
    # paraphrase, not a drop. The old form of this test asserted the OUTPUT cue was
    # not reported dropped — which can never happen, since only source-side cues are
    # ever reported — so it passed while the gate flagged every paraphrase. T1's
    # benchmark caught that: false-positive rate 2/2.
    hedged = "- Informal lending networks may facilitate access to rural capital."
    for out_s in ["Informal lending networks could facilitate access to rural capital.",
                  "Informal lending networks might facilitate access to rural capital.",
                  "Informal lending networks possibly facilitate access to rural capital."]:
        r = guard(hedged, out_s)
        assert r["verdict"] == "PASS", (out_s, r["findings"])

    # ...and the swap must not blind the gate to a real drop in the same class
    r = guard(hedged, "Informal lending networks facilitate access to rural capital.")
    assert r["verdict"] == "FAIL" and any(
        f["type"] == "DROPPED" and f["property"] == "hedge" for f in r["findings"])

    # two hedges in, one out: the class count falls, so it still fires
    r = guard("- Informal lending networks may possibly facilitate rural capital access.",
              "Informal lending networks could facilitate rural capital access.")
    assert any(f["type"] == "DROPPED" and f["property"] == "hedge"
               for f in r["findings"]), r["findings"]

    # a hedged NEIGHBOUR must not mask a drop in the claim itself. Counting the
    # +-1 window instead of the matched sentence took in-lexicon recall to 0.17.
    sk_n = ("- Informal lending networks may facilitate access to rural capital.\n"
            "- Borrowers possibly rely on community reputation to secure credit.")
    assert guard(sk_n, "Informal lending networks facilitate access to rural capital. "
                       "Borrowers possibly rely on community reputation to secure "
                       "credit.")["verdict"] == "FAIL"
    # ...while a hedge that genuinely floated into the neighbouring sentence is
    # preserved — the whole reason the hedge window is +-1 (research/12)
    sk_f = ("- The estimator may recover consistent parameters under exogeneity.\n"
            "- Violation of exogeneity yields systematically biased estimates.")
    r = guard(sk_f, "The estimator recovers consistent parameters under exogeneity. "
                    "Violation of exogeneity may yield systematically biased estimates.")
    assert r["verdict"] == "PASS", r["findings"]

    # a same-strength booster swap is not an ADDED booster
    r = guard("- The audit clearly establishes the reporting failure.",
              "The audit certainly establishes the reporting failure.")
    assert not any(f["type"] == "ADDED" for f in r["findings"]), r["findings"]

    # within-class strength change is declared, never silently passed
    assert "certainty_gradation" in guard("- X may hold.", "X may hold.")["not_checked"]

    # witness span-validation: markers not in the sentence are discarded
    fake_cache = {"s": {"hedged": True, "attributed": False, "markers": ["may"]}}
    assert witness_sentence("s", fake_cache, "m")[("hedges", "may")] == 1

    # T1b defects, pinned: (1) witness quoting an in-lexicon cue must not
    # double-count it (identical text self-flagged before the union merge)
    s = "The drug may reduce symptoms."
    f, _ = typed_diff(s, [s], [0], Counter({("hedges", "may"): 1}),
                      Counter({("hedges", "may"): 1}))
    assert not f, f
    # (2) an out-of-lexicon hedge preserved under different phrasing is a
    # paraphrase, not a drop — witness runs on BOTH sides
    f, _ = typed_diff("Our sense is that X holds.", ["On the evidence, X holds."], [0],
                      Counter({("hedges", "our sense is"): 1}),
                      Counter({("hedges", "on the evidence"): 1}))
    assert not any(x["type"] == "DROPPED" for x in f), f
    # (3) an out-of-lexicon hedge genuinely dropped still fails
    f, _ = typed_diff("Our sense is that X holds.", ["X holds."], [0],
                      Counter({("hedges", "our sense is"): 1}), Counter())
    assert any(x["type"] == "DROPPED" and x["property"] == "hedge" for x in f), f

    print("selftest ok" + ("" if factwash else "  (factwash absent — builtin diff only)"))


def selftest_entailment(backend="minicheck"):
    """Layer-3 selftest — separate because it loads a 770M model (T1 wiring).

    Also pins the blind spot the whole typed diff exists for: a dropped hedge
    is entailment-clean, so entailment alone would pass it."""
    sk = "- The intervention may reduce dropout among first-year students."
    supported = "The intervention may reduce dropout among first-year students."
    invented = ("The intervention may reduce dropout among first-year students. "
                "It also eliminated all staff turnover at every participating site.")
    dropped = "The intervention was not evaluated."

    assert entailment(sk, supported, "", backend) == [], "clean text must not flag"

    f = entailment(sk, invented, "", backend)
    assert any(x["type"] == "INVENTED" for x in f), f

    f = entailment(sk, dropped, "", backend)
    assert any(x["type"] == "MISSING" for x in f), f

    # The named blind spot. research/12 asserts a dropped qualifier PASSES
    # bidirectional entailment ("the proposition survives and only the author's
    # commitment to it changed"). Measured here, MiniCheck does not pass it — it
    # scores the categorical rewrite unsupported at p~0.05. So this is deliberately
    # NOT asserted either way; tools/bench_guard.py measures how often entailment
    # catches each class across the 30 seeds. What IS invariant is that the typed
    # diff catches it on its own, whatever entailment says.
    hedge_dropped = "The intervention reduces dropout among first-year students."
    r = guard(sk, hedge_dropped, entail_backend=backend)
    assert r["verdict"] == "FAIL" and any(
        x["type"] == "DROPPED" and x["property"] == "hedge" for x in r["findings"])
    assert "entailment" not in r["not_checked"]
    print(f"entailment selftest ok  (backend={backend})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skeleton"); ap.add_argument("--output")
    ap.add_argument("--sources", default=""); ap.add_argument("--author-span", default="")
    ap.add_argument("--witness", action=argparse.BooleanOptionalAction, default=None,
                    help="source-side witness (default: on when OPENROUTER_API_KEY exists)")
    ap.add_argument("--entailment", default="auto",
                    choices=["auto", "none", "alignscore", "minicheck"],
                    help="default: minicheck when its weights are already in .models/")
    ap.add_argument("--state", default="state")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        if a.entailment not in ("none", "auto"):
            selftest_entailment(a.entailment)
    elif a.skeleton and a.output:
        rep = guard(Path(a.skeleton).read_text(), Path(a.output).read_text(),
                    Path(a.sources).read_text() if a.sources else "",
                    Path(a.author_span).read_text() if a.author_span else "",
                    "auto" if a.witness is None else a.witness,
                    a.entailment, Path(a.state))
        print(json.dumps(rep, indent=1))
        sys.exit(0 if rep["verdict"] == "PASS" else 1)
    else:
        ap.print_help()
