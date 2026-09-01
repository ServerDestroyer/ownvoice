#!/usr/bin/env python3
"""B1 meld harness — single-pass exemplar style transfer via OpenRouter (DESIGN.md §6).

Run arms:   python3 tools/meld.py --draft d.md --anchor a.md --out runs/b1 \\
                [--model google/gemini-3.1-pro] [--arms simple-rewrite,continuation]
Dry run:    add --dry-run (prints assembled prompts, no API calls)
Blind sheet: python3 tools/meld.py --blind runs/b1   (shuffled sheet + key.json)

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
SEEDS = json.loads((Path(__file__).parent / "meld_seeds.json").read_text())


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


def call(model: str, system: str, user: str, temperature: float) -> str:
    body = {"model": model, "temperature": temperature,
            "messages": ([{"role": "system", "content": system}] if system else [])
            + [{"role": "user", "content": user}]}
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {api_key()}",
                 "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)["choices"][0]["message"]["content"].strip()
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
            for arm in arms:
                system = (arm["system"] + "\n\n" + SEEDS["discipline_clause"]).strip()
                user = arm["user"].format(anchor=anchor, draft=para)
                if args.dry_run:
                    print(f"--- para {i} arm {arm['id']} ---\n[system] {system}\n[user] {user[:400]}...\n")
                    continue
                print(f"para {i} · {arm['id']} · {args.model}", file=sys.stderr)
                text = call(args.model, system, user, args.temperature)
                if arm.get("strip_anchor_prefix") and text.startswith(anchor[:60]):
                    text = text[len(anchor):].lstrip() if text.startswith(anchor) else text
                row = {"ts": time.strftime("%F %T"), "model": args.model, "arm": arm["id"],
                       "para": i, "anchor_file": args.anchor, "draft": para, "output": text,
                       "leak_vs_anchor": trigram_overlap(text, anchor),
                       "copy_vs_draft": trigram_overlap(text, para),
                       "temperature": args.temperature}
                f.write(json.dumps(row) + "\n")
                f.flush()
    if not args.dry_run:
        print(f"results -> {log}")


def blind(out_dir: str):
    """Blind-ranking sheet: per paragraph, shuffled candidates incl. the unmelded draft
    (the do-nothing baseline research/11 requires). Key kept in key.json."""
    out = Path(out_dir)
    rows = [json.loads(l) for l in (out / "results.jsonl").read_text().splitlines()]
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


def selftest():
    assert trigram_overlap("the quick brown fox jumps", "the quick brown fox sleeps") == 0.667
    assert trigram_overlap("a b", "a b c") == 0.0
    a = SEEDS["arms"][0]
    assert "{anchor}" in a["user"] and "{draft}" in a["user"]
    assert all("{draft}" in x["user"] for x in SEEDS["arms"])
    print("selftest ok")


if __name__ == "__main__":
    cfg = dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", default=cfg.get("MELD_DRAFT"))
    ap.add_argument("--anchor", default=cfg.get("MELD_ANCHOR"))
    ap.add_argument("--model", default=cfg.get("MELD_MODEL", "google/gemini-3.1-pro-preview"))
    ap.add_argument("--arms", default=cfg.get("MELD_ARMS", ""))
    ap.add_argument("--temperature", type=float, default=float(cfg.get("MELD_TEMPERATURE", 0.7)))
    ap.add_argument("--out", default=cfg.get("MELD_OUT", "runs/b1"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--blind", metavar="RUN_DIR")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest()
    elif args.blind:
        blind(args.blind)
    elif args.draft and args.anchor:
        run(args)
    else:
        ap.print_help()
