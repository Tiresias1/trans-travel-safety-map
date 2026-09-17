#!/usr/bin/env python3
"""List ADM1 units for a country, for the research hand-off prompt.

Usage:
    python3 tools/adm1_list.py USA
    python3 tools/adm1_list.py USA --format md      # paste-ready bullet list
    python3 tools/adm1_list.py --counts             # units per country, sorted

Flags units that are themselves scored at country level on the map (e.g. US
territories like PRI/GUM, or HKG/MAC inside CHN if present) — those must be
EXCLUDED from ADM1 research to avoid double-scoring.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("iso3", nargs="?", help="country ISO3 code")
    ap.add_argument("--format", choices=("plain", "md"), default="plain")
    ap.add_argument("--counts", action="store_true",
                    help="list unit counts per country and exit")
    ap.add_argument("--admin1", default=str(ROOT / "boundaries" / "admin1.geojson"))
    ap.add_argument("--countries", default=str(ROOT / "data" / "countries.json"))
    args = ap.parse_args()

    g = json.loads(Path(args.admin1).read_text(encoding="utf-8"))
    countries = json.loads(Path(args.countries).read_text(encoding="utf-8"))
    country_isos = set(countries)

    feats = [f["properties"] for f in g["features"]]
    if args.counts:
        from collections import Counter
        c = Counter(p["iso3"] for p in feats)
        for iso, n in c.most_common():
            nm = countries.get(iso, {}).get("name", iso)
            print(f"{iso} {n:4d}  {nm}")
        return 0
    if not args.iso3:
        print("error: give an ISO3 (or --counts)", file=sys.stderr)
        return 2

    iso = args.iso3.upper()
    units = [p for p in feats if p["iso3"] == iso]
    if not units:
        print(f"error: no ADM1 units for {iso}", file=sys.stderr)
        return 2

    # Promoted units: territories that this project scores at country level even
    # though geoBoundaries lists them inside a parent's ADM1 (US territories,
    # HK/Macau/Taiwan inside CHN). The set is small, finite and project-specific,
    # so it is an explicit whitelist per parent — generic heuristics misfire
    # (Missouri's US-MO code looks like Macau; Inner Mongolia token-matches
    # Mongolia; the US state of Georgia exact-matches the country Georgia).
    PROMOTED_BY_PARENT = {
        "USA": {"PRI": "PR", "GUM": "GU", "VIR": "VI", "ASM": "AS", "MNP": "MP"},
        "CHN": {"HKG": "HK", "MAC": "MO", "TWN": "TW"},
    }
    STOP = {"special", "administrative", "region", "province", "municipality",
            "commonwealth", "united", "states", "of", "the", "and", "autonomous"}

    def name_tokens(s: str) -> set:
        return {t for t in re.split(r"[^a-z0-9]+", s.lower())
                if len(t) > 2 and t not in STOP}

    promoted_wanted = {k: countries[k]["name"] for k in PROMOTED_BY_PARENT.get(iso, {})
                       if k in countries}
    suffix_to_iso = {suf: k for k, suf in PROMOTED_BY_PARENT.get(iso, {}).items()
                     if k in countries}
    promoted_tokens = {k: name_tokens(nm) for k, nm in promoted_wanted.items()}

    def promoted(code: str, name: str) -> str | None:
        if not promoted_wanted:
            return None
        if "-" in code:  # well-formed 3166-2 code: suffix rule (exact)
            return suffix_to_iso.get(code.split("-", 1)[1].upper())
        # degenerate code (CHN units all carry code 'CHN'): token containment
        # against the whitelisted promoted names only
        toks = name_tokens(name)
        for k, ptoks in promoted_tokens.items():
            if ptoks and ptoks <= toks:
                return k
        return None

    parent_score = countries.get(iso, {}).get("score")

    print(f"# {iso} — {countries.get(iso, {}).get('name', '?')} "
          f"(national score {parent_score}) · {len(units)} ADM1 units")
    excluded = []
    for p in sorted(units, key=lambda x: x["name"]):
        nm = p["name"]
        hit = promoted(p.get("code", ""), nm)
        if hit:
            excluded.append((nm, p["shapeID"], hit))
            continue
        if args.format == "md":
            print(f"- {nm} (`{p['shapeID']}`)")
        else:
            print(f"{p['shapeID']}\t{nm}")
    if excluded:
        print(f"\nEXCLUDED {len(excluded)} unit(s) already scored at country level "
              f"— do NOT research these as ADM1:", file=sys.stderr)
        for nm, sid, hit in excluded:
            print(f"  {nm}  ({sid})  -> country record {hit}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
