#!/usr/bin/env python3
"""Region-vs-region head-to-head battery (2026-10-30).

Rates two divisions of the same country against each other in one call, names
withheld, both seen under the same national framework, with presentation order
randomised. Prints the mean ratings, the swing, and every rationale.

Usage:
  python3 tools/h2h_regions.py "New Mexico" "Colorado" [--pairs 14] [--iso3 USA]
"""
from __future__ import annotations
import argparse, json, random, statistics, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import blind_pairwise as BP  # noqa


def build_args(model: str):
    class A:
        pass
    a = A()
    a.api = "openai"
    a.baseurl = "https://openrouter.ai/api/v1"
    a.endpoint_suffix = "/chat/completions"
    a.auth_style = "bearer"
    a.api_key = Path("/tmp/.openrouter_key").read_text().strip()
    a.model = model
    a.max_output_tokens = 9000
    a.reasoning_tokens = 3000
    a.anthropic_version = "2023-06-01"
    a.no_cache = False
    a.timeout = 300
    a.retries = 3
    a.backoff = 2.0
    a.temperature = 0.3
    a.admin = False
    return a


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--iso3", default="USA")
    ap.add_argument("--pairs", type=int, default=14)
    ap.add_argument("--model", default="deepseek/deepseek-v4.1-flash")
    args = ap.parse_args()
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    def find(n):
        return next((r for r in A.values()
                     if r.get("iso3") == args.iso3 and r.get("name") == n), None)
    ra_, rb_ = find(args.a), find(args.b)
    if not ra_ or not rb_:
        sys.exit(f"not found: {[n for n, r in ((args.a, ra_), (args.b, rb_)) if not r]}")
    parent = C[args.iso3]
    framework = BP.render_parent_bundle(parent)
    system_text = BP.build_system_prompt(BP.TAXONOMY.read_text()) + BP.MIXED_SYSTEM_EXTRA if hasattr(BP, "MIXED_SYSTEM_EXTRA") else BP.build_system_prompt(BP.TAXONOMY.read_text())
    aa = build_args(args.model)
    rng = random.Random(20261030)
    ratings = {args.a: [], args.b: []}
    whys = []
    for i in range(args.pairs):
        flip = rng.random() < 0.5
        first, second = (rb_, ra_) if flip else (ra_, rb_)
        def block(r):
            return BP.render_region_bundle(r) if r.get("blindSummary") else (
                BP.dossier(r) if r.get("dossier") else
                (str(r.get("summary", "")) + "\n\n" + str(r.get("modelContext", ""))))
        user = (
            "Rate the two divisions below on the 0.00-1.00 trans-visitor outing-risk "
            "scale. Both stand under the same national framework, given once here.\n\n"
            f"### FRAMEWORK IMPOSED BY THE ENCOMPASSING STATE\n{framework}\n\n"
            f"### DIVISION A (identity withheld)\n{block(first)}\n\n"
            f"### DIVISION B (identity withheld)\n{block(second)}\n\n"
            "Reply with only the JSON object described in the output format, where "
            "score_a rates DIVISION A and score_b rates DIVISION B.")
        try:
            resp = BP.call_api(aa, system_text, user)
            sa, sb, why, _u = BP.parse_scores(resp, aa.api)
        except Exception as e:
            print(f"  [{i+1}] error: {str(e)[:90]}", flush=True)
            continue
        ratings[first["name"]].append(sa)
        ratings[second["name"]].append(sb)
        whys.append((first["name"], sa, second["name"], sb, why))
        print(f"  [{i+1}/{args.pairs}] {first['name']} {sa:.2f} vs {second['name']} {sb:.2f}",
              flush=True)
    print()
    for n, v in ratings.items():
        if v:
            print(f"{n:18} mean {statistics.mean(v):.3f}  sd {statistics.pstdev(v):.3f}  n={len(v)}")
    print()
    for f, sa, s2, sb, why in whys:
        print(f"--- {f} {sa:.2f} vs {s2} {sb:.2f}\n    {str(why)[:400]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
