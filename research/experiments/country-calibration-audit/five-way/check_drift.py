#!/usr/bin/env python3
"""Drift monitor: per-ISO3 median ADM1 score vs parent score.

Report-only by default (exit 0 even when groups flag); pass --strict to
fail (exit 1) when any ISO3 group's median deviation exceeds the
threshold, for future from-scratch runs that must not sync drifted data.
Pure stdlib + json; fast; reads data/admin1.json + data/countries.json
by record id / ISO3, never by name. No data files are written.

Usage:
    python3 check_drift.py [--threshold 0.03] [--strict]
                           [--admin1 PATH] [--countries PATH] [--json PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]  # kort/
DEFAULT_ADMIN1 = ROOT / "data" / "admin1.json"
DEFAULT_COUNTRIES = ROOT / "data" / "countries.json"
DEFAULT_THRESHOLD = 0.03


def _score(rec):
    """iterativeScore if numeric, else score; None when neither is numeric."""
    if not isinstance(rec, dict):
        return None
    for field in ("iterativeScore", "score"):
        value = rec.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        return float(value)
    return None


def compute_drift(admin1: dict, countries: dict, threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Per-ISO3 median/max deviation of ADM1 scores vs the parent score.

    Returns {"threshold": ..., "rows": [...], "flagged": [...]} where each
    row is {iso3, n, median, parent_score, median_deviation,
    max_abs_deviation, flagged}. Rows are sorted by descending
    |median_deviation|. ISO3 groups with no parent score or no scored
    ADM1 records are skipped.
    """
    groups: dict[str, list[float]] = {}
    for rec in admin1.values():
        if not isinstance(rec, dict):
            continue
        iso = rec.get("iso3")
        score = _score(rec)
        if iso is None or score is None:
            continue
        groups.setdefault(str(iso), []).append(score)
    rows = []
    for iso in sorted(groups):
        parent = _score(countries.get(iso))
        if parent is None:
            continue
        values = groups[iso]
        med = float(median(values))
        rows.append({
            "iso3": iso,
            "n": len(values),
            "median": med,
            "parent_score": parent,
            "median_deviation": med - parent,
            "max_abs_deviation": max(abs(v - parent) for v in values),
            "flagged": abs(med - parent) > threshold,
        })
    rows.sort(key=lambda r: (-abs(r["median_deviation"]), r["iso3"]))
    return {"threshold": threshold, "rows": rows,
            "flagged": [r["iso3"] for r in rows if r["flagged"]]}


def _load(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise SystemExit(f"{path} must be a JSON object")
    return doc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                    help="flag ISO3 groups with |median - parent| above this (default 0.03)")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 when any group flags (default: report-only, exit 0)")
    ap.add_argument("--admin1", type=Path, default=DEFAULT_ADMIN1)
    ap.add_argument("--countries", type=Path, default=DEFAULT_COUNTRIES)
    ap.add_argument("--json", type=Path, default=None,
                    help="also write the full report as JSON to this path")
    args = ap.parse_args(argv)
    report = compute_drift(_load(args.admin1), _load(args.countries), args.threshold)
    print(f"drift check: threshold={args.threshold} "
          f"iso3_groups={len(report['rows'])} flagged={len(report['flagged'])}")
    for row in report["rows"]:
        mark = "FLAG" if row["flagged"] else "    "
        print(f"{mark} {row['iso3']} n={row['n']} median={row['median']:.4f} "
              f"parent={row['parent_score']:.4f} "
              f"median_dev={row['median_deviation']:+.4f} "
              f"max_abs_dev={row['max_abs_deviation']:.4f}")
    print(f"flagged_iso3: {','.join(report['flagged']) if report['flagged'] else '(none)'}")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    if args.strict and report["flagged"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
