#!/usr/bin/env python3
"""Low-end anchor-extension experiment (preregistered 2026-11-13).

Measures 40 targets 12 times each: 2 calls per existing anchor (BLR, CIV, VAT,
ESP) plus 2 calls per new low-end anchor (UGA 0.090, NER 0.093). Records every
per-anchor estimate so between-anchor disagreement and leave-one-anchor-out can be
inspected. Writes /tmp/lowend_results.jsonl; does NOT modify published data.

Usage: python3 tools/lowend_experiment.py --targets /tmp/lowend_targets.json
"""
from __future__ import annotations
import argparse, json, random, statistics, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import blind_pairwise as BP  # noqa

MODEL = "deepseek/deepseek-v4.1-flash"
A4 = {"BLR": 0.100, "CIV": 0.297, "VAT": 0.600, "ESP": 0.840}
A6_EXTRA = {"UGA": 0.090, "NER": 0.093}
REPEATS = 2


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
    ap.add_argument("--targets", default="/tmp/lowend_targets.json")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default="/tmp/lowend_results.jsonl")
    args = ap.parse_args()
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    taxonomy = (ROOT / "research" / "outing-risk-taxonomy.md").read_text()
    system_text = BP.build_system_prompt(taxonomy)
    aa = api_args()
    spec = json.loads(Path(args.targets).read_text())
    ladder = {**A4, **A6_EXTRA}
    print(f"targets: {len(spec['countries'])} countries + {len(spec['divisions'])} divisions "
          f"| anchors: {list(ladder)} | {REPEATS} calls per anchor", flush=True)

    def block_for(kind, key, rec):
        if kind == "country":
            return BP.dossier(rec), rec.get("name")
        parent = C.get(rec.get("parentIso3") or rec.get("iso3"))
        fw = BP.render_parent_bundle(parent) if parent else ""
        body = BP.render_region_bundle(rec) if rec.get("blindSummary") else (
            str(rec.get("summary", "")) + "\n\n" + str(rec.get("modelContext", "")))
        return (f"### FRAMEWORK IMPOSED BY THE ENCOMPASSING STATE\n{fw}\n\n"
                f"### THE DIVISION'S OWN CONTENT\n{body}"), rec.get("name")

    def measure(item):
        kind, key = item["kind"], item["key"]
        if kind == "country":
            rec = C.get(key)
        else:
            rec = A.get(key)
        if not rec:
            return None
        tblock, _name = block_for(kind, key, rec)
        per_anchor = []
        for aid, ascore in ladder.items():
            for _r in range(REPEATS):
                anchor = C.get(aid)
                if not anchor:
                    continue
                flip = random.random() < 0.5
                anc_block = BP.dossier(anchor)
                if flip:
                    head = f"## DOSSIER A\n\n{anc_block}\n\n## DOSSIER B\n\n{tblock}"
                    mapping = "score_a rates DOSSIER A (a country), score_b rates DOSSIER B"
                else:
                    head = f"## DOSSIER A\n\n{tblock}\n\n## DOSSIER B\n\n{anc_block}"
                    mapping = "score_a rates DOSSIER A, score_b rates DOSSIER B (a country)"
                user = ("Rate the two dossiers below on the 0.00-1.00 trans-visitor "
                        "outing-risk scale.\n\n" + head +
                        "\n\nReply with only the JSON object described in the output "
                        "format, where " + mapping + ".")
                try:
                    resp = BP.call_api(aa, system_text, user)
                    sa, sb, _w, _u = BP.parse_scores(resp, aa.api)
                except Exception:
                    continue
                t_r, a_r = (sb, sa) if flip else (sa, sb)
                per_anchor.append({"anchor": aid, "anchorScore": ascore,
                                   "estimate": round(ascore + (t_r - a_r), 6),
                                   "targetRating": t_r, "anchorRating": a_r})
        if not per_anchor:
            return None
        def mean_for(ids):
            vals = [p["estimate"] for p in per_anchor if p["anchor"] in ids]
            return statistics.mean(vals) if vals else None
        out = {"kind": kind, "key": key, "n": len(per_anchor),
               "perAnchor": per_anchor,
               "A4": mean_for(A4), "A6": mean_for(ladder)}
        if kind == "country":
            out["framework"] = C[key].get("nationalFrameworkScore")
            out["name"] = C[key].get("name")
        else:
            out["parent"] = A[key].get("parentIso3") or A[key].get("iso3")
            out["name"] = A[key].get("name")
            out["published"] = A[key].get("score")
        return out

    items = [{"kind": "country", "key": k} for k in spec["countries"]] + \
            [{"kind": "division", "key": k} for k in spec["divisions"]]
    done = 0
    with open(args.out, "a", encoding="utf-8") as fh, ThreadPoolExecutor(args.workers) as ex:
        futs = [ex.submit(measure, it) for it in items]
        for f in as_completed(futs):
            r = f.result(); done += 1
            if r:
                fh.write(json.dumps(r) + "\n"); fh.flush()
            if done % 5 == 0:
                print(f"  {done}/{len(items)} measured", flush=True)
    print("EXPERIMENT DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
