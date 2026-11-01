#!/usr/bin/env python3
"""Anchored absolute calibration for divisions (2026-11-05).

Mixed-mode division ratings are CONTRAST ratings: within a region, the rating
correlates -0.39 (median) with the rating the same call gave the partner, and
region means correlate -0.44 with the mean level of the partners drawn. With
~12 encounters that bias swamps real differences, so divisions sharing a strong
parent framework collapsed together (US states) and their ordering was partly
partner luck.

This lane removes partner variance by rating every division against the SAME
small ladder of anchor countries, spanning the scale. Each pair yields a paired
difference on one scale:

    estimate_anchor = anchor_score + (rating_division - rating_anchor)

and the division's score is the mean of those estimates. Because every division
sees the same anchors, the contrast bias is a constant across divisions and
cancels in comparison.

Usage:
  python3 tools/anchored_calibrate.py --only USA/Mississippi USA/Alabama
  python3 tools/anchored_calibrate.py --apply [--workers 5]
"""
from __future__ import annotations
import argparse, fcntl, json, random, statistics, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import blind_pairwise as BP  # noqa
from build_data import band_label  # noqa

MODEL = "deepseek/deepseek-v4.1-flash"
DEFAULT_ANCHORS = ["BLR", "CIV", "VAT", "ESP"]   # ~0.10 / 0.30 / 0.60 / 0.84


def api_args():
    class A:
        pass
    a = A()
    a.api = "openai"; a.baseurl = "https://openrouter.ai/api/v1"
    a.endpoint_suffix = "/chat/completions"; a.auth_style = "bearer"
    a.api_key = Path("/tmp/.openrouter_key").read_text().strip()
    a.model = MODEL; a.max_output_tokens = 8000; a.reasoning_tokens = 3000
    a.anthropic_version = "2023-06-01"; a.no_cache = True
    a.timeout = 300; a.retries = 3; a.backoff = 2.0; a.temperature = 0.3; a.admin = False
    return a


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchors", nargs="*", default=DEFAULT_ANCHORS)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--repeats", type=int, default=1,
                    help="independent ratings per anchor (variance drops as 1/n)")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    taxonomy = (ROOT / "research" / "outing-risk-taxonomy.md").read_text()
    system_text = BP.build_system_prompt(taxonomy)
    aa = api_args()
    targets = [(sid, r) for sid, r in A.items()
               if str(r.get("summary", "")).strip() and isinstance(r.get("score"), (int, float))]
    if args.only:
        want = set(args.only)
        targets = [(sid, r) for sid, r in targets
                   if f"{r.get('iso3')}/{r.get('name')}" in want or r.get("name") in want]
    if args.limit:
        targets = targets[: args.limit]
    print(f"divisions: {len(targets)} | anchors: {args.anchors}", flush=True)

    def block(r):
        if r.get("blindSummary"):
            return BP.render_region_bundle(r)
        txt = str(r.get("summary", "")) + "\n\n" + str(r.get("modelContext", ""))
        return txt

    def estimate(item):
        sid, r = item
        parent_iso = r.get("parentIso3") or r.get("iso3")
        parent = C.get(parent_iso)
        fw = BP.render_parent_bundle(parent) if parent else ""
        ests = []
        for aid in args.anchors * args.repeats:
            anchor = C.get(aid)
            if not anchor:
                continue
            flip = random.random() < 0.5
            div_block = f"### FRAMEWORK IMPOSED BY THE ENCOMPASSING STATE\n{fw}\n\n### THE DIVISION'S OWN CONTENT\n{block(r)}"
            anc_block = BP.dossier(anchor)
            if flip:
                head = (f"## DOSSIER A\n\n{anc_block}\n\n## DOSSIER B\n\n{div_block}")
                mapping = "score_a rates DOSSIER A (a country), score_b rates DOSSIER B (a division)"
            else:
                head = (f"## DOSSIER A\n\n{div_block}\n\n## DOSSIER B\n\n{anc_block}")
                mapping = "score_a rates DOSSIER A (a division), score_b rates DOSSIER B (a country)"
            user = ("Rate the two dossiers below on the 0.00-1.00 trans-visitor outing-risk scale.\n\n"
                    + head + "\n\nReply with only the JSON object described in the output format, where "
                    + mapping + ".")
            try:
                resp = BP.call_api(aa, system_text, user)
                sa, sb, _why, _u = BP.parse_scores(resp, aa.api)
            except Exception:
                continue
            div_r, anc_r = (sb, sa) if flip else (sa, sb)
            ests.append(float(anchor["score"]) + (div_r - anc_r))
        if not ests:
            return sid, None, 0
        return sid, statistics.mean(ests), len(ests)

    results = []
    with ThreadPoolExecutor(args.workers) as ex:
        futs = [ex.submit(estimate, t) for t in targets]
        done = 0
        for f in as_completed(futs):
            sid, est, n = f.result()
            done += 1
            if est is None:
                continue
            results.append((sid, est, n))
            if done % 25 == 0:
                print(f"  {done}/{len(targets)} estimated", flush=True)
    print(f"estimated {len(results)}/{len(targets)}", flush=True)
    for sid, est, n in sorted(results, key=lambda t: -t[1]):
        rr = A.get(sid, {})
        print(f"  {rr.get('iso3','')}/{str(rr.get('name',''))[:26]:26} {est:.3f} (n={n}, "
              f"stored {float(rr.get('score', 0)):.3f})", flush=True)
    if args.apply and results:
        lock = open(ROOT / "data" / ".apply.lock", "w")
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            A = json.loads((ROOT / "data" / "admin1.json").read_text())
            for sid, est, n in results:
                rec = A.get(sid)
                if not rec:
                    continue
                sc = max(0.02, min(0.98, est))
                rec["score"] = round(sc, 6)
                rec["band"] = band_label(sc)
                rec["ratedBy"] = MODEL
                rec["derivedFrom"] = {"mode": "anchored", "anchors": args.anchors,
                                      "anchorRating": round(est, 6)}
            (ROOT / "data" / "admin1.json").write_text(
                json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")
            print("applied", flush=True)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
            lock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
