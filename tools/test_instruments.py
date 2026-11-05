#!/usr/bin/env python3
"""Regression tests for tools/instruments.py.

Each case here is a real misclassification that reached the published manifest before it was
caught, so these lock the fixes in. Run: python3 tools/test_instruments.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from instruments import (classify, ANCHORED, DESTINATION_SUMMARY,
                         COUNTRY_MEAN, MIRROR, UNKNOWN)

CASES = [
    # 1. "anchor-ladder floor" in framework-rating prose must NOT read as anchored (12 records)
    ({"scoreProvenance": "framework rating: no destination summary, because "
                         "endpoint-clamping: 10/13 divisions at the anchor-ladder floor.",
      "derivedFrom": {"mode": "pairwise"}}, COUNTRY_MEAN),
    # 2. "no destination summary" must NOT read as a destination summary (same 12 records)
    ({"scoreProvenance": "framework rating: no destination summary, because "
                         "endpoint-clamping: 3/6 divisions at the anchor-ladder floor.",
      "derivedFrom": {"mode": "pairwise"}}, COUNTRY_MEAN),
    # ordinary cases
    ({"scoreProvenance": "destination summary: mean of 3 measured divisions; they range "
                         "0.80 to 0.85 (sd 0.02)", "derivedFrom": {"mode": "reaggregate"}},
     DESTINATION_SUMMARY),
    ({"scoreProvenance": "mirrors the territory's own record",
      "derivedFrom": {"mode": "mirror"}}, MIRROR),
    ({"scoreProvenance": "", "derivedFrom": {"mode": "anchored", "anchorRating": 0.5}},
     ANCHORED),
    ({"scoreProvenance": "framework rating (no measured division set)"}, COUNTRY_MEAN),
    # fail closed
    ({"scoreProvenance": "", "derivedFrom": {}}, UNKNOWN),
]


def main() -> int:
    fails = 0
    for rec, want in CASES:
        got = classify(rec)
        ok = got == want
        if not ok:
            fails += 1
            print(f"FAIL: expected {want!r}, got {got!r} for {rec.get('scoreProvenance')!r}")
    print(f"instrument classification regression tests: {len(CASES) - fails}/{len(CASES)} pass")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
