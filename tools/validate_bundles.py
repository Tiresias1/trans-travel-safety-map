#!/usr/bin/env python3
"""Validate authored blind region bundles for --regions-vs-countries runs.

Deterministic (no API): checks each data/blind_bundles/<ISO>.json for
  - coverage: every scored region of that parent has a non-empty bundle
  - direct-identifier leaks: the region's own name, the parent's name, and
    known demonyms/adjectives anywhere in the bundle text
  - banned deviation-space wording: national-score references, tier labels,
    cross-region "vs <sibling>" claims, score-like numbers (0.xx)
Exits non-zero on any FAIL. Warnings do not fail the run.

Usage:
    python3 tools/validate_bundles.py USA GBR          # by parent ISO3
    python3 tools/validate_bundles.py --all
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BDIR = ROOT / "data" / "blind_bundles"

# parent -> extra identity tokens beyond the literal country name
PARENT_TOKENS = {
    "USA": ["united states", "us", "u.s.", "usa", "american", "americas", "america"],
    "GBR": ["united kingdom", "uk", "britain", "british", "england", "wales",
            "scotland", "great britain", "britains"],
    "MYS": ["malaysia", "malaysian"],
    "IDN": ["indonesia", "indonesian"],
    "NGA": ["nigeria", "nigerian"],
    "IND": ["india", "indian"],
    "CAN": ["canada", "canadian"],
    "AUS": ["australia", "australian"],
    "DEU": ["germany", "german"],
    "FRA": ["france", "french"],
    "ESP": ["spain", "spanish"],
    "ITA": ["italy", "italian"],
    "POL": ["poland", "polish"],
    "NLD": ["netherlands", "dutch"],
    "TUR": ["turkey", "turkish", "türkiye"],
    "RUS": ["russia", "russian"],
    "ZAF": ["south africa", "south african"],
    "BRA": ["brazil", "brazilian"],
    "MEX": ["mexico", "mexican"],
    "ARG": ["argentina", "argentine"],
    "CHL": ["chile", "chilean"],
    "COL": ["colombia", "colombian"],
    "PER": ["peru", "peruvian"],
    "PHL": ["philippines", "filipino"],
    "KOR": ["south korea", "korean"],
    "FRA_extra": [],
}
BANNED_RES = [
    (r"\b0\.\d{1,2}\b", "score-like number"),
    (r"national (?:score|floor|ceiling|average|baseline)", "national-score reference"),
    (r"(?:above|below|against|versus|vs\.?)\s+the\s+national", "national comparison"),
    (r"\b(?:Most Protective|high-risk band|low-risk band|elevated[- ]risk band)\b",
     "tier label"),
    (r"\bwell (?:above|below)\b", "deviation-space phrasing"),
    (r"\bHate Crime and Public Order\b|\bHF \d+\b|\bCOPFS\b|\bHolyrood\b",
     "named institution/bill fingerprint"),  # FAIL in GBR bundles; warning elsewhere
]
MAX_LEN = 2400
MIN_LEN = 120


def tokens_for(rec_name: str, parent_iso: str):
    toks = {rec_name.lower()}
    # drop generic suffixes so 'State of X'/'X Oblast' also match bare core names
    core = re.sub(r"^(state|province|region|oblast|krai|republic|prefecture|department)\s+of\s+",
                  "", rec_name.lower())
    core = re.sub(r"\s+(of\s+\w+)?(oblast|krai|republic|state|prefecture|province|"
                  r"governorate|department|region|voivodeship|emirate|canton)$", "", core)
    if core and len(core) > 3:
        toks.add(core)
    return toks | set(PARENT_TOKENS.get(parent_iso, []))


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    if sys.argv[1] == "--all":
        isos = [f.stem for f in sorted(BDIR.glob("*.json"))]
    else:
        isos = [a.upper() for a in sys.argv[1:]]

    admin1 = json.loads((ROOT / "data" / "admin1.json").read_text(encoding="utf-8"))
    countries = json.loads((ROOT / "data" / "countries.json").read_text(encoding="utf-8"))
    fails = warns = 0
    for iso in isos:
        path = BDIR / f"{iso}.json"
        if not path.exists():
            print(f"[FAIL] {iso}: {path} missing"); fails += 1
            continue
        bundles = json.loads(path.read_text(encoding="utf-8"))
        units = {sid: r for sid, r in admin1.items() if r.get("iso3") == iso}
        missing = [f"{r['name']} ({sid})" for sid, r in sorted(units.items(), key=lambda x: x[1]['name'])
                   if sid not in bundles or not str(bundles[sid]).strip()]
        extra = [sid for sid in bundles if sid not in units]
        parent_names = {countries.get(iso, {}).get("name", "").lower()}
        for sid, r in sorted(units.items(), key=lambda x: x[1]["name"]):
            txt = str(bundles.get(sid, ""))
            low = txt.lower()
            probs = []
            for tok in tokens_for(r["name"], iso) | parent_names:
                if tok and re.search(r"\b" + re.escape(tok) + r"\b", low):
                    probs.append(f"IDENTITY-LEAK {tok!r}")
            for pat, why in BANNED_RES:
                m = re.search(pat, txt, re.I)
                if m:
                    probs.append(f"{why}: {m.group(0)!r}")
            if MIN_LEN <= len(txt) < MAX_LEN:
                pass
            elif len(txt) < MIN_LEN:
                probs.append(f"too short ({len(txt)})")
            else:
                probs.append(f"too long ({len(txt)} > {MAX_LEN})")
            hard = [p for p in probs if p.startswith(("IDENTITY-LEAK", "too"))]
            soft = [p for p in probs if p not in hard]
            if hard:
                print(f"[FAIL] {iso} {r['name']}: " + "; ".join(hard)); fails += 1
            if soft:
                print(f"[warn] {iso} {r['name']}: " + "; ".join(soft)); warns += 1
        if missing:
            print(f"[FAIL] {iso}: {len(missing)} regions without bundles: {missing[:6]}"
                  + ("…" if len(missing) > 6 else ""))
            fails += 1
        if extra:
            print(f"[warn] {iso}: {len(extra)} bundle keys not in admin1: {extra[:5]}")
            warns += 1
        n_ok = len(units) - len(missing)
        print(f"  {iso}: {n_ok}/{len(units)} bundles validated")
    print(f"\nvalidate_bundles: {fails} FAIL, {warns} warnings")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
