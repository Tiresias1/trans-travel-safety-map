#!/usr/bin/env python3
"""Audit shared national claims copy-pasted into sibling ADM1 records.

Fingerprints region sources[] claims; claims appearing in >=3 sibling regions
are candidate national-source misattributions. For each (claim, region) pair
an LLM judgment decides: does the claim contain facts specific to THIS region
(region name, cities, institutions, provincial law)? National-only claims are
removed from the region record (they are redundant with the parent bundle in
the pairwise prompt, and national news belongs in the country record).

Usage: python3 tools/audit_shared_claims.py [--apply] [--workers 4]
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from consolidate_record import call_llm  # noqa


def fingerprint(groups: dict, A: dict, min_regions: int = 3) -> list:
    for key, r in A.items():
        if not isinstance(r, dict) or not r.get("dossier"):
            continue
        parent = r.get("parentIso3") or r.get("iso3")
        for s in r.get("sources", []):
            if not isinstance(s, dict):
                continue
            cl = re.sub(r"\s+", " ", str(s.get("summary", ""))).strip().lower()
            if not cl:
                continue
            norm = re.sub(r"[0-9]+", "N", cl)
            h = hashlib.md5(norm.encode()).hexdigest()[:10]
            groups.setdefault(h, []).append((key, r, s, parent))
    out = [items for items in groups.values() if len(items) >= min_regions]
    out.sort(key=lambda items: -len(items))
    return out


def region_specific(rec: dict, claim: str) -> str | None:
    """Returns 'specific' | 'national' | 'partial:...' | None on error."""
    rname = rec.get("name", "")
    out = call_llm(
        "You audit source claims for jurisdiction-specific content.",
        f"""A region record for {rname} carries the source claim below. Decide whether
the claim contains information SPECIFIC to {rname} itself (its cities,
institutions, provincial/state law, local events, local officials) or whether
it is a country-wide/national item that says nothing about {rname} in
particular. Mentioning the country alone is NOT region-specific. If it mixes
both, return "partial".

CLAIM: {claim[:1400]}

Return ONLY JSON: {{"verdict": "specific|national|partial"}}""")
    if isinstance(out, dict):
        v = str(out.get("verdict", "")).lower()
        if v in ("specific", "national", "partial"):
            return v
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    shared = fingerprint({}, A)
    if args.limit:
        shared = shared[: args.limit]
    pairs = []
    for items in shared:
        for key, r, s, parent in items:
            pairs.append((key, r, s))
    print(f"shared groups: {len(shared)} | (claim, region) pairs to audit: {len(pairs)}", flush=True)
    removed = kept = 0
    def one(p):
        key, r, s = p
        try:
            v = region_specific(r, str(s.get("summary", "")))
            return key, r, s, v, ""
        except Exception as e:
            return key, r, s, None, str(e)[:100]
    with ThreadPoolExecutor(args.workers) as ex:
        futs = [ex.submit(one, p) for p in pairs]
        done = 0
        for f in as_completed(futs):
            key, r, s, v, err = f.result()
            done += 1
            if err:
                print(f"[FAIL] {r.get('name')}: {err}", flush=True)
            elif v == "national":
                srcs = r.get("sources", [])
                r["sources"] = [x for x in srcs if x is not s]
                removed += 1
            else:
                kept += 1
            if done % 50 == 0:
                print(f"... {done}/{len(pairs)} removed={removed} kept={kept}", flush=True)
    print(f"AUDIT DONE: removed {removed}, kept {kept} of {len(pairs)} pairs", flush=True)
    if args.apply:
        (ROOT / "data" / "admin1.json").write_text(
            json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")
        print("applied", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())