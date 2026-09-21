#!/usr/bin/env python3
"""Validate and merge initial ADM1 scores (from the scoring hand-off) into
data/admin1.json.

Input: JSONL, one record per line. The `iso3` key is optional — when omitted it is
read from the boundary data via shapeID (that is also what gets written):
  {"shapeID": "...", "name": "Jalisco", "score": 0.44,
   "summary": "<p>...</p>", "sources": ["https://...", ...],
   "researchedAt": "2026-09-18", "estimated": false}

Checks (record skipped on failure, run continues):
  - shapeID exists in boundaries/admin1.geojson; name matches that unit exactly
  - score is a number in [0,1]
  - summary: 1-4 <p> paragraphs, <= 2500 chars
  - sources: non-empty list of http(s) URL strings
  - record does not already exist (use --force to overwrite, e.g. USA re-runs)

Band is computed automatically. After merging, run tools/build_data.py.

Usage:
    python3 tools/apply_admin1_scores.py --in data/admin1_scores/MEX.jsonl --dry-run
    python3 tools/apply_admin1_scores.py --in data/admin1_scores/MEX.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from build_data import band_label  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", required=True, help="JSONL file of scored units")
    ap.add_argument("--admin1-file", default=str(ROOT / "data" / "admin1.json"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="overwrite existing records")
    args = ap.parse_args()

    geo = json.loads((ROOT / "boundaries" / "admin1.geojson").read_text(encoding="utf-8"))
    by_id = {f["properties"]["shapeID"]: f["properties"] for f in geo["features"]}

    path = Path(args.admin1_file)
    admin1 = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    ok = skipped = over = 0
    for ln, line in enumerate(Path(args.inp).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"[FAIL] line {ln}: bad JSON: {e}")
            skipped += 1
            continue

        fails = []
        sid = r.get("shapeID")
        props = by_id.get(sid or "")
        if props is None:
            fails.append(f"shapeID not in boundary data: {sid!r}")
        else:
            if r.get("name") != props["name"]:
                fails.append(f"name {r.get('name')!r} != boundary name {props['name']!r}")
        if r.get("iso3") and r["iso3"] != props["iso3"]:
            fails.append(f"iso3 {r['iso3']!r} != boundary iso3 {props['iso3']!r}")
        sc = r.get("score")
        if not isinstance(sc, (int, float)) or isinstance(sc, bool) or not (0 <= sc <= 1):
            fails.append(f"score invalid: {sc!r}")
        summ = r.get("summary", "")
        n_p = summ.count("<p") + summ.count("<P")
        if not (1 <= n_p <= 4) or len(summ) > 2500:
            fails.append(f"summary must be 1-4 <p> paragraphs <=2500 chars "
                         f"(got {n_p} paras, {len(summ)} chars)")
        srcs = r.get("sources")
        if (not isinstance(srcs, list) or not srcs
                or not all(isinstance(u, str) and u.startswith("http") for u in srcs)):
            fails.append("sources must be a non-empty list of http(s) URLs")

        if sid in admin1 and not args.force:
            fails.append("record already exists (use --force to overwrite)")

        if fails:
            print(f"[FAIL] line {ln} ({r.get('name', sid)}):")
            for f in fails:
                print(f"   - {f}")
            skipped += 1
            continue

        rec = {
            "iso3": props["iso3"],
            "name": props["name"],
            "score": round(float(sc), 6),
            "band": band_label(float(sc)),
            "summary": summ,
            "sources": srcs,
            "researchedAt": r.get("researchedAt") or date.today().isoformat(),
        }
        if r.get("estimated"):
            rec["estimated"] = True
        if r.get("outOfScopeNotes"):
            rec["outOfScopeNotes"] = r["outOfScopeNotes"]
        if sid in admin1:
            over += 1
        admin1[sid] = rec
        ok += 1

    print(f"\nvalidated OK: {ok} ({over} overwritten) · skipped: {skipped}")
    if args.dry_run:
        print("dry run — nothing written")
        return 0 if skipped == 0 else 1
    if ok:
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(admin1, indent=1, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
        print(f"wrote {len(admin1)} total records to {path}")
        print("next: python3 tools/build_data.py")
    return 0 if skipped == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
