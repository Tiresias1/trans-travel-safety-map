#!/usr/bin/env python3
"""Replay archived encounters to separate pipeline drift from sample-size effects.

For a country, extract the exact partner list it faced in a production wave from the
wave log, then re-rate those same pairs now. Two comparisons follow:

  full  : mean over the archived partner set, re-rated now  -> historical reproducibility
  subset: mean over random k-sized subsets of the same set -> sample-size / context effect

If full-set replays rise but subsets match them, the difference is pipeline/rater drift.
If subsets rise relative to the full-set replay, sample size is implicated.

Usage: python3 tools/encounter_replay.py --iso KEN --log /tmp/redo_c4.jsonl [--k 8]
"""
from __future__ import annotations
import argparse, json, random, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import blind_pairwise as BP  # noqa

MODEL = "deepseek/deepseek-v4.1-flash"


def api_args():
    class A: pass
    a = A()
    a.api = "openai"; a.baseurl = "https://openrouter.ai/api/v1"
    a.endpoint_suffix = "/chat/completions"; a.auth_style = "bearer"
    a.api_key = Path("/tmp/.openrouter_key").read_text().strip()
    a.model = MODEL; a.max_output_tokens = 8000; a.reasoning_tokens = 3000
    a.anthropic_version = "2023-06-01"; a.no_cache = True
    a.timeout = 300; a.retries = 3; a.backoff = 2.0; a.temperature = 0.3; a.admin = False
    a.regions_parent = None; a.regions_vs_countries = False; a.countries_file = None
    a.dry_run = False
    return a


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", required=True)
    ap.add_argument("--log", default="/tmp/redo_c4.jsonl")
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--subsets", type=int, default=3)
    ap.add_argument("--old-rubric", action="store_true",
                    help="strip rule 10b (the condition the stored scores were produced under)")
    args = ap.parse_args()
    if args.old_rubric:
        import os
        os.environ["STRIP_RULE_10B"] = "1"
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    target = C[args.iso]
    tname = target["name"]
    partners = []
    for line in open(args.log):
        d = json.loads(line)
        if d.get("a_name") == tname and d.get("b_name"):
            partners.append(d["b_name"])
        elif d.get("b_name") == tname and d.get("a_name"):
            partners.append(d["a_name"])
    partners = [p for p in partners if p in {c["name"] for c in C.values()}]
    if not partners:
        sys.exit(f"no archived encounters for {tname}")
    taxonomy = (ROOT / "research" / "outing-risk-taxonomy.md").read_text()
    system_text = BP.build_system_prompt(taxonomy)
    aa = api_args()
    def rate_pair(partner_name):
        p = next(c for c in C.values() if c["name"] == partner_name)
        flip = random.random() < 0.5
        tb, pb = BP.dossier(target), BP.dossier(p)
        if flip:
            head = f"## DOSSIER A\n\n{pb}\n\n## DOSSIER B\n\n{tb}"
            m = "score_a rates DOSSIER A, score_b rates DOSSIER B"
        else:
            head = f"## DOSSIER A\n\n{tb}\n\n## DOSSIER B\n\n{pb}"
            m = "score_a rates DOSSIER A, score_b rates DOSSIER B"
        user = ("Rate the two dossiers below on the 0.00-1.00 trans-visitor outing-risk "
                "scale.\n\n" + head + "\n\nReply with only the JSON object described in the "
                "output format, where " + m + ".")
        try:
            resp = BP.call_api(aa, system_text, user)
            sa, sb, _w, _u = BP.parse_scores(resp, aa.api)
        except Exception:
            return None
        return (sb if flip else sa)
    full = [x for x in (rate_pair(p) for p in partners) if x is not None]
    rng = random.Random(11)
    subs = []
    for _ in range(args.subsets):
        pick = rng.sample(partners, min(args.k, len(partners)))
        v = [x for x in (rate_pair(p) for p in pick) if x is not None]
        if v: subs.append(statistics.mean(v))
    out = {"iso": args.iso, "name": tname, "stored": target["score"],
           "archivedN": len(partners), "replayedN": len(full),
           "replayFull": statistics.mean(full) if full else None,
           "subsetMeans": [round(x, 4) for x in subs],
           "rubric": "old(10b stripped)" if args.old_rubric else "current"}
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
