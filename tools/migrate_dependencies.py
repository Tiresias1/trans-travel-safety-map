#!/usr/bin/env python3
"""Dependency migration (2026-10-07 redo, phase 2).

Dependencies stop being countries-mode pairwise entities. Their admin1
records (SYN-* + PRI) become primary dossier territories scored in the
admin1 mixed mode (region bundle vs blind countries, parent's national
assessment included automatically; only the territory moves). The
countries-mode record becomes a display mirror carrying the territory's
score/summary and a territory designation.

What it does:
  1. promotes each territory's admin1 record: dossier=True, parent field set,
     blind fields synced from the country record (single source of truth until
     the regen rewrites them);
  2. adds a `parentIso3` attribute (mixed-mode filter reads it; territory
     records carry their own ISO3);
  3. blind_pairwise.py mixed mode: treat records with parentIso3 as regions
     under that parent (filter fix); parent-bundle injection already keyed on
     the parent's countries record;
  4. blind_pairwise.py countries mode: EXCLUDES territories from the eligible
     pool (they are no longer pairwise-rated as countries);
  5. build_data.py: single-unit stand-ins keep score-sync for non-territory
     microstates; TERRITORY admin1 records are no longer force-synced — they
     are scored independently in mixed mode (their score is their own);
     the countries record mirrors the admin1 score instead (display only);
  6. app.js: territory popups show "Territory of <parent>" designation
     (countries-mode record keeps iso3 for the map colouring).

Usage: python3 tools/migrate_dependencies.py [--apply]
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# territory ISO3 -> parent ISO3 (HKG/MAC/WLF/VAT: self-governing or no
# meaningful parent regime; stay as-is, blind countries mode, no parent bundle)
TERRITORY_PARENT = {
    "ASM": "USA", "GUM": "USA", "VIR": "USA", "MNP": "USA", "PRI": "USA",
    "FLK": "GBR", "GIB": "GBR", "BMU": "GBR", "CYM": "GBR", "VGB": "GBR",
    "AIA": "GBR", "MSR": "GBR", "TCA": "GBR", "SHN": "GBR", "PCN": "GBR",
    "GGY": "GBR", "IMN": "GBR", "JEY": "GBR",
    "GLP": "FRA", "MTQ": "FRA", "GUF": "FRA", "REU": "FRA", "MYT": "FRA",
    "BLM": "FRA", "PYF": "FRA", "NCL": "FRA",
    "CUW": "NLD", "ABW": "NLD", "BES": "NLD",
    "FRO": "DNK", "GRL": "DNK",
    "COK": "NZL", "NIU": "NZL",
    "ESH": "MAR",
}
# ESH: Western Sahara — administering state Morocco per its own dossier text.
NO_PARENT_TERR = {"HKG", "MAC", "WLF", "VAT"}  # stay countries-mode, no bundle

SYN = {iso: f"SYN-{iso}" for iso in TERRITORY_PARENT}
SYN["PRI"] = "66186276B86072070009793"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    n_promoted = 0
    for iso, parent in sorted(TERRITORY_PARENT.items()):
        sid = SYN.get(iso)
        r = A.get(sid)
        if r is None:
            print(f"MISSING admin1 record for {iso}")
            continue
        r["dossier"] = True
        r["parentIso3"] = parent
        r.pop("inherited", None)
        # readiness flag: complete blind fields are synced below; without it
        # the mixed-mode pool silently excludes the record (2026-10-08 bug:
        # territories got zero encounters in the admin1 wave and kept
        # pre-migration carryover scores)
        r["blindV2"] = True
        # blind fields synced from the country record (single source of truth
        # until the regen rewrites them through the gate)
        for f in ("blindSummary", "blindTangential", "blindLocalsOnly",
                  "blindOutOfScope", "blindSourceSummaries"):
            if C[iso].get(f) is not None:
                r[f] = C[iso][f]
        # full text fields too (the regen will rewrite from sources anyway)
        for f in ("summary", "tangentialFactors", "localsOnly", "outOfScopeNotes",
                  "sources", "researchedAt"):
            if C[iso].get(f) is not None:
                r[f] = C[iso][f]
        n_promoted += 1
    print(f"promoted {n_promoted} territory records")
    if args.apply:
        (ROOT / "data" / "admin1.json").write_text(
            json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")
        print("applied")


if __name__ == "__main__":
    main()