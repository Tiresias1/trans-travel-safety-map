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

Usage (RETIRED 2026-11-13 - see main()): every scoring invocation is
refused with a nonzero exit before any data read, network call, checkpoint
write, or --apply. --help remains available. The ANCHOR_CALIBRATION
constants below remain importable for tools/build_manifest.py's historical
audit only; they are HISTORICAL RECORD and are not usable to calculate
scores.
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# (Local imports of blind_pairwise/build_data were removed together with the
#  retired runner body — nothing left in this module needs them.)

MODEL = "deepseek/deepseek-v4.1-flash"
# FROZEN ANCHOR CALIBRATION (2026-11-13, per review).
# HISTORICAL RECORD ONLY - NOT USABLE TO CALCULATE SCORES. This constants
# block is kept solely so tools/build_manifest.py can report the historical
# audit trail; the anchored CLI refuses every scoring invocation (see main()).
# These are the constants the division pass was actually computed with. They are
# frozen: the anchors' *displayed* country scores have since moved (BLR 0.100 ->
# 0.057, CIV 0.297 -> 0.280, ESP 0.840 -> 0.869) because national scores were
# re-aggregated from divisions, and substituting those would (a) silently change
# every division score and (b) swap in values partly derived from the very
# divisions being calibrated (circular). The pass is therefore versioned as
# calibrated to the country-score version below, and a replacement ladder must be
# decided on independent validation, not on this drift.
ANCHOR_CALIBRATION = {
    "version": "anchors-2026-11-13-v1",
    "countryScoreVersion": "r2026-11-12-pairwise",
    "anchors": {"BLR": 0.100, "CIV": 0.297, "VAT": 0.600, "ESP": 0.840},
    "note": "chosen by matching target scale positions to the nearest scored "
            "country; not independent validation — see review 2026-11-13",
}
DEFAULT_ANCHORS = list(ANCHOR_CALIBRATION["anchors"])
FROZEN_ANCHOR_SCORES = ANCHOR_CALIBRATION["anchors"]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="RETIRED: anchored calibration no longer computes scores; "
                    "every invocation is refused with a nonzero exit "
                    "(--help shows usage only).")
    ap.add_argument("--anchors", nargs="*", default=DEFAULT_ANCHORS)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--ckpt", default="/tmp/anchored_results.jsonl",
                    help="append-only checkpoint; existing rows are skipped on restart")
    ap.add_argument("--repeats", type=int, default=1,
                    help="independent ratings per anchor (variance drops as 1/n)")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--scope", choices=("divisions", "countries"), default="divisions",
                    help="countries mode measures country dossiers with the same "
                         "anchor ladder — the bridge sample the review asks for")
    args = ap.parse_args()
    # RETIRED (2026-11-13): anchored calibration - foreign-anchor score
    # calculation - is frozen until a replacement method is independently
    # validated. This refusal runs immediately after argument parsing (so
    # --help still works) and BEFORE any data read, any provider/network
    # call, any checkpoint append, and any --apply write. Every invocation
    # that reaches this line is a scoring invocation, so all of them exit
    # nonzero with no side effects.
    print("RETIRED: tools/anchored_calibrate.py no longer computes scores.",
          file=sys.stderr)
    print("  Every scoring invocation is refused before any data read, "
          "network call, checkpoint write, or --apply.", file=sys.stderr)
    print("  The frozen ANCHOR_CALIBRATION constants remain importable for "
          "build_manifest's historical audit only; they are HISTORICAL "
          "RECORD, not a usable scoring ladder.", file=sys.stderr)
    print("  A replacement method requires independent validation before "
          "any runner is restored.", file=sys.stderr)
    # (The historical runner body - target selection, anchor-ladder
    #  estimation, checkpointing and --apply writes - was removed here:
    #  retired code must not be reachable by any flag combination.)
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
