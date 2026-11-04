#!/usr/bin/env python3
"""Measurement manifest: one exact provenance record for the published data
(2026-11-12, from review recommendation A).

Reconciles counts, detects mixed-rubric scores, records how each record was
measured (instrument, model, rubric version, inheritance status, uncertainty),
and fails loudly on inconsistencies instead of letting them ship.

Usage: python3 tools/build_manifest.py [--check]
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="exit 1 on any inconsistency")
    args = ap.parse_args()
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    try:
        from blind_pairwise import RUBRIC_VERSION
    except Exception:
        RUBRIC_VERSION = "unknown"

    def rubric_of(r):
        return r.get("rubricVersion") or "unversioned"

    def instrument_of(r):
        d = r.get("derivedFrom") or {}
        if d.get("mode"):
            return d["mode"]
        if r.get("ratedBy"):
            return "pairwise"
        return "unknown"

    countries = Counter(instrument_of(r) for r in C.values())
    regions = Counter(instrument_of(r) for r in A.values())
    c_rubric = Counter(rubric_of(r) for r in C.values())
    r_rubric = Counter(rubric_of(r) for r in A.values())
    inherited = sum(1 for r in A.values() if r.get("inherited"))
    dossier = sum(1 for r in A.values() if r.get("dossier"))
    estimated = sum(1 for r in A.values() if r.get("estimated"))

    problems = []
    # counts must reconcile exactly
    if dossier + estimated != len(A):
        problems.append(f"dossier+estimated ({dossier}+{estimated}) != total ({len(A)})")
    # no mixed rubric in one published set
    if len(c_rubric) > 1:
        problems.append(f"countries carry {len(c_rubric)} rubric versions: {dict(c_rubric)}")
    if len(r_rubric) > 1:
        problems.append(f"divisions carry {len(r_rubric)} rubric versions: {dict(r_rubric)}")
    # every score must state its instrument
    if countries.get("unknown"):
        problems.append(f"{countries['unknown']} countries have no instrument recorded")
    if regions.get("unknown"):
        problems.append(f"{regions['unknown']} divisions have no instrument recorded")

    manifest = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rubricVersion": RUBRIC_VERSION,
        "counts": {
            "countries": len(C), "divisions": len(A),
            "dossierDivisions": dossier, "estimatedDivisions": estimated,
            "inheritedDivisions": inherited,
        },
        "instruments": {"countries": dict(countries), "divisions": dict(regions)},
        "rubricVersions": {"countries": dict(c_rubric), "divisions": dict(r_rubric)},
        "consistency": {"ok": not problems, "problems": problems},
        "notes": {
            "inherited": "Divisions with no sub-national signal take the national "
                         "score and are NOT independent evidence; they are excluded "
                         "from any aggregation over divisions.",
            "instruments": "Scores produced by different instruments (pairwise, "
                           "mixed, anchored, in-country) are not yet bridged and must "
                           "not be presented as one calibrated scale.",
        },
    }
    out = ROOT / "data" / "measurement_manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(manifest["counts"], indent=1))
    print("instruments:", manifest["instruments"])
    print("rubric versions:", manifest["rubricVersions"])
    if problems:
        print("CONSISTENCY PROBLEMS:")
        for p in problems:
            print("  -", p)
        if args.check:
            return 1
    else:
        print("consistency: OK — counts reconcile, one rubric version, instruments recorded")
    print("written:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
