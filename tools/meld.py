#!/usr/bin/env python3
"""B1 meld harness — single-pass exemplar style transfer via OpenRouter (DESIGN.md §6).

Run arms:   python3 tools/meld.py --draft d.md --anchor a.md --out runs/b1 \\
                [--model google/gemini-3.1-pro] [--arms simple-rewrite,continuation]
Dry run:    add --dry-run (prints assembled prompts, no API calls)
Blind sheet: python3 tools/meld.py --blind runs/b1/qwen   (shuffled sheet + key.json)
Stage B:    python3 tools/meld.py --blind runs/b1/qwen,runs/b1/kimi --arms <winner> --out runs/b1/stageB
Tally:      python3 tools/meld.py --tally runs/b1/qwen,runs/b1/qwen-matched-1   (after ranks are filled)

Config: repo-root .env (gitignored; template in .env.example) — OPENROUTER_API_KEY
plus run defaults MELD_MODEL, MELD_TEMPERATURE, MELD_ARMS, MELD_OUT, MELD_DRAFT,
MELD_ANCHOR. CLI flags override .env; the key is only needed for live calls —
selftest/dry-run/blind never touch it.
Draft file = paragraphs separated by blank lines.
Every result row records the leakage diagnostics research/11 mandates:
trigram overlap output-vs-anchor (leak) and output-vs-draft (copy).
"""
import argparse
import json
import os
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

API = "https://openrouter.ai/api/v1/chat/completions"
MODELS = "https://openrouter.ai/api/v1/models"
SEEDS = json.loads((Path(__file__).parent / "meld_seeds.json").read_text())
EFFORT_ORDER = ["none", "minimal", "low", "medium", "high", "xhigh", "max"]
_MODELS: dict = {}
LAST_USAGE: dict = {}  # usage block of the most recent call (reasoning_tokens lives here)


def model_info(model: str) -> dict:
    """OpenRouter's live record for a model: supported_parameters, reasoning switch.
    One fetch per process; unknown model -> {} (caller falls back to sending everything)."""
    if not _MODELS:
        try:
            with urllib.request.urlopen(MODELS, timeout=60) as r:
                _MODELS.update({m["id"]: m for m in json.load(r)["data"]})
        except Exception as e:  # offline: behave as before the switch existed
            print(f"  models index unavailable ({e}); sending defaults", file=sys.stderr)
            _MODELS["_unavailable"] = {}
    return _MODELS.get(model, {})


def thinking_off(info: dict) -> dict | None:
    """Request fields that turn a model's thinking as far off as OpenRouter allows.
    Chris measured thinking off (or the lowest setting) as best for the polisher, and
    every model's default is 'medium' — so the polisher must say so explicitly.
    None when the model has no reasoning switch at all."""
    if "reasoning" not in info.get("supported_parameters", []):
        return None
    r = info.get("reasoning") or {}
    efforts = r.get("supported_efforts") or []
    if not r.get("mandatory"):
        return {"effort": "none"} if ("none" in efforts or not efforts) else {"enabled": False}
    return {"effort": min(efforts, key=EFFORT_ORDER.index)}  # mandatory: lowest it accepts


def is_prose(para: str) -> bool:
    """Only running prose goes through the polisher. Titles, headings, lists, tables,
    code, quotes, images, HTML and one-line captions pass through untouched (Chris's
    rule: 'titles, subsections, boxes, forms and diagrams should not go through')."""
    s = para.strip()
    if re.match(r"^(#|\||```|~~~|>|!\[|<|[-*+]\s|\d+[.)]\s|---|\*\*\*)", s):
        return False
    # ponytail: word-count heuristic for titles/captions; a real block classifier if T4 shows misses
    return "\n" in s or len(s.split()) >= 12


def dotenv() -> dict:
    """Repo-root .env as a dict (lines of KEY=value; quotes optional, # comments)."""
    env = Path(__file__).parent.parent / ".env"
    d = {}
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, _, v = line.partition("=")
            d[k.strip()] = v.strip().strip("'\"")
    return d


def api_key() -> str:
    """OPENROUTER_API_KEY from the environment, else .env. Only needed at call time."""
    key = os.environ.get("OPENROUTER_API_KEY") or dotenv().get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("no OPENROUTER_API_KEY in environment or .env — put OPENROUTER_API_KEY=sk-... in the repo-root .env")
    return key


def trigram_overlap(a: str, b: str) -> float:
    """Fraction of a's word trigrams also present in b."""
    def tri(t):
        w = re.findall(r"[a-z']+", t.lower())
        return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}
    ta, tb = tri(a), tri(b)
    return round(len(ta & tb) / len(ta), 3) if ta else 0.0


def call(model: str, system: str, user: str, temperature: float,
         thinking: str = "default") -> str:
    """One chat completion. thinking='off' sends the model's lowest reasoning setting
    (see thinking_off); 'default' sends nothing and the model thinks at its default.
    Temperature is omitted for models that reject it (the gpt-5.6 family)."""
    info = model_info(model)
    body = {"model": model,
            "messages": ([{"role": "system", "content": system}] if system else [])
            + [{"role": "user", "content": user}]}
    if "temperature" in info.get("supported_parameters", ["temperature"]):
        body["temperature"] = temperature
    if thinking == "off" and (r := thinking_off(info)):
        body["reasoning"] = r
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {api_key()}",
                 "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.load(r)
                LAST_USAGE.clear()
                LAST_USAGE.update(data.get("usage") or {})
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:  # ponytail: blanket retry, 3 tries then raise
            if attempt == 2:
                raise
            print(f"  retry after error: {e}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))


def paragraphs(path: Path) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", path.read_text()) if p.strip()]


def run(args):
    draft_paras = paragraphs(Path(args.draft))
    anchor = Path(args.anchor).read_text().strip()
    arms = [a for a in SEEDS["arms"] if not args.arms or a["id"] in args.arms.split(",")]
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    log = out / "results.jsonl"
    with log.open("a") as f:
        for i, para in enumerate(draft_paras):
            if not is_prose(para):
                print(f"para {i} · not prose, passes through untouched", file=sys.stderr)
                continue
            for arm in arms:
                system = (arm["system"] + "\n\n" + SEEDS["discipline_clause"]).strip()
                user = arm["user"].format(anchor=anchor, draft=para)
                if args.dry_run:
                    print(f"--- para {i} arm {arm['id']} ---\n[system] {system}\n[user] {user[:400]}...\n")
                    continue
                print(f"para {i} · {arm['id']} · {args.model}", file=sys.stderr)
                text = call(args.model, system, user, args.temperature, args.thinking)
                if arm.get("strip_anchor_prefix") and text.startswith(anchor[:60]):
                    text = text[len(anchor):].lstrip() if text.startswith(anchor) else text
                row = {"ts": time.strftime("%F %T"), "model": args.model, "arm": arm["id"],
                       "para": i, "anchor_file": args.anchor, "draft": para, "output": text,
                       "leak_vs_anchor": trigram_overlap(text, anchor),
                       "copy_vs_draft": trigram_overlap(text, para),
                       "temperature": args.temperature, "thinking": args.thinking,
                       "reasoning_tokens": (LAST_USAGE.get("completion_tokens_details") or {})
                       .get("reasoning_tokens")}
                f.write(json.dumps(row) + "\n")
                f.flush()
    if not args.dry_run:
        print(f"results -> {log}")


def blind(dirs: str, arms: str = "", out_dir: str = ""):
    """Blind-ranking sheet: per paragraph, shuffled candidates incl. the unmelded draft
    (the do-nothing baseline research/11 requires). Key kept in key.json.
    Stage A: one run dir (all arms, one model). Stage B: comma-separated run dirs
    (one per model) filtered to the winning --arms, written to --out."""
    srcs = [Path(d) for d in dirs.split(",")]
    out = Path(out_dir) if out_dir else srcs[0]
    out.mkdir(parents=True, exist_ok=True)
    keep = set(arms.split(",")) if arms else None
    rows = [json.loads(l) for s in srcs for l in (s / "results.jsonl").read_text().splitlines()]
    rows = [r for r in rows if not keep or r["arm"] in keep]
    by_para = {}
    for r in rows:
        by_para.setdefault(r["para"], {"draft": r["draft"], "cands": []})["cands"].append(r)
    sheet, key = ["# Blind ranking — mark each candidate 1 (best) .. n; note any that don't sound like you\n"], {}
    for p, d in sorted(by_para.items()):
        items = [{"label": None, "text": c["output"], "who": f'{c["arm"]}|{c["model"]}'} for c in d["cands"]]
        items.append({"label": None, "text": d["draft"], "who": "UNMELDED-BASELINE"})
        random.shuffle(items)
        sheet.append(f"\n## Paragraph {p}\n")
        for j, it in enumerate(items):
            lab = f"P{p}-{chr(65 + j)}"
            key[lab] = it["who"]
            sheet.append(f"**{lab}**  (rank: __ )\n\n> {it['text']}\n")
    (out / "blind_sheet.md").write_text("\n".join(sheet))
    (out / "key.json").write_text(json.dumps(key, indent=1))
    print(f"sheet -> {out/'blind_sheet.md'}   key (don't peek) -> {out/'key.json'}")


def tally(dirs: str):
    """Unblind filled sheets: mean rank per (arm|model) across paragraphs and dirs.
    Reads '(rank: N)' from each blind_sheet.md; unfilled rows are skipped."""
    scores = {}
    for d in dirs.split(","):
        d = Path(d)
        key = json.loads((d / "key.json").read_text())
        for lab, rank in re.findall(r"\*\*(P\d+-[A-Z])\*\*\s+\(rank:\s*(\d+)\s*\)", (d / "blind_sheet.md").read_text()):
            scores.setdefault(key[lab], []).append(int(rank))
    if not scores:
        sys.exit("no filled ranks found — write the number in each '(rank: __ )'")
    print(f"{'candidate':45} {'mean rank':>9} {'n':>3}   (1 = best)")
    for who, v in sorted(scores.items(), key=lambda kv: sum(kv[1]) / len(kv[1])):
        print(f"{who:45} {sum(v) / len(v):9.2f} {len(v):3}")


def selftest():
    assert trigram_overlap("the quick brown fox jumps", "the quick brown fox sleeps") == 0.667
    assert trigram_overlap("a b", "a b c") == 0.0
    a = SEEDS["arms"][0]
    assert a["id"] == "humanizing-polisher", "Chris's arm is the interim default"
    assert "{anchor}" in a["user"] and "{draft}" in a["user"]
    assert all("{draft}" in x["user"] for x in SEEDS["arms"])
    # thinking switch: mandatory -> lowest allowed; optional -> none / enabled:false; absent -> None
    assert thinking_off({"supported_parameters": ["reasoning"], "reasoning": {
        "mandatory": True, "supported_efforts": ["high", "medium", "low"]}}) == {"effort": "low"}
    assert thinking_off({"supported_parameters": ["reasoning"], "reasoning": {
        "mandatory": False, "supported_efforts": ["high", "none"]}}) == {"effort": "none"}
    assert thinking_off({"supported_parameters": ["reasoning"], "reasoning": {
        "mandatory": False, "supported_efforts": ["xhigh", "high"]}}) == {"enabled": False}
    assert thinking_off({"supported_parameters": ["temperature"]}) is None
    # prose filter: only running prose is polished
    assert is_prose("This is a real paragraph of running prose with more than twelve words in it.")
    assert is_prose("Short line one.\nShort line two, hard-wrapped prose.")
    for block in ("# Heading", "## 2.1 Subsection", "| a | b |\n|---|---|", "```py\nx\n```",
                  "- bullet one", "1. numbered", "> box text", "![fig](f.png)", "<div>",
                  "Figure 3: caption"):
        assert not is_prose(block), block
    print("selftest ok")


if __name__ == "__main__":
    cfg = dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", default=cfg.get("MELD_DRAFT"))
    ap.add_argument("--anchor", default=cfg.get("MELD_ANCHOR"))
    ap.add_argument("--model", default=cfg.get("MELD_MODEL", "qwen/qwen3.7-max"))
    ap.add_argument("--arms", default=cfg.get("MELD_ARMS", ""))
    ap.add_argument("--temperature", type=float, default=float(cfg.get("MELD_TEMPERATURE", 0.2)))
    ap.add_argument("--thinking", default=cfg.get("MELD_THINKING", "off"), choices=["off", "default"],
                    help="off = model's lowest reasoning setting (Chris's finding); default = model default")
    ap.add_argument("--out", default=cfg.get("MELD_OUT", "runs/b1"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--blind", metavar="RUN_DIR[,RUN_DIR...]",
                    help="build a blind sheet; several dirs + --arms + --out = cross-model Stage B sheet")
    ap.add_argument("--tally", metavar="RUN_DIR[,RUN_DIR...]", help="unblind filled sheets")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
    elif args.tally:
        tally(args.tally)
    elif args.blind:
        blind(args.blind, args.arms, args.out if "," in args.blind else "")
    elif args.draft and args.anchor:
        run(args)
    else:
        ap.print_help()
