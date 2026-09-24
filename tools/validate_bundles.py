#!/usr/bin/env python3
"""Validate blindSummary fields on admin1 records (blind region bundles).

Deterministic (no API): for each parent ISO3 given (or --all = every parent that
has at least one blindSummary), checks that EVERY scored unit of that parent has
a blindSummary and that none of them leaks:
  - the region's own name / core name token, the parent country's name,
    or known demonyms
  - deviation-space wording (national-score refs, tiers, 0.xx numbers)
  - named-institution/bill fingerprints (HF 146, COPFS, Holyrood, ...)
Exits non-zero on any FAIL. Warnings do not fail.

Usage: python3 tools/validate_bundles.py USA GBR | --all
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PARENT_TOKENS = {
    "USA": ["united states", "us", "u.s.", "usa", "american", "americas", "america"],
    "GBR": ["united kingdom", "uk", "britain", "british", "england", "wales",
            "scotland", "great britain"],
    "MYS": ["malaysia", "malaysian"], "IDN": ["indonesia", "indonesian"],
    "NGA": ["nigeria", "nigerian"], "IND": ["india", "indian"],
    "CAN": ["canada", "canadian"], "AUS": ["australia", "australian"],
    "DEU": ["germany", "german"], "FRA": ["france", "french"],
    "ESP": ["spain", "spanish"], "ITA": ["italy", "italian"],
    "POL": ["poland", "polish"], "NLD": ["netherlands", "dutch"],
    "TUR": ["turkey", "turkish", "turkiye"], "RUS": ["russia", "russian"],
    "ZAF": ["south africa", "south african"], "BRA": ["brazil", "brazilian"],
    "MEX": ["mexico", "mexican"], "ARG": ["argentina", "argentine"],
    "CHL": ["chile", "chilean"], "COL": ["colombia", "colombian"],
    "PER": ["peru", "peruvian"], "PHL": ["philippines", "filipino"],
    "KOR": ["south korea", "korean"],
}
BANNED_RES = [
    (r"\b0\.\d{1,2}\b", "score-like number"),
    (r"national (?:score|floor|ceiling|average|baseline)", "national-score reference"),
    (r"(?:above|below|against|versus|vs\.?)\s+the\s+national", "national comparison"),
    (r"\b(?:Most Protective|high-risk band|low-risk band|elevated[- ]risk band)\b",
     "tier label"),
    (r"\bwell (?:above|below)\b", "deviation-space phrasing"),
    (r"\bHate Crime and Public Order\b|\bHF \d+\b|\bCOPFS\b|\bHolyrood\b",
     "named institution/bill fingerprint"),
]
MAX_LEN, MIN_LEN = 2400, 120


def tokens_for(rec_name: str, parent_iso: str):
    toks = {rec_name.lower()}
    core = re.sub(r"^(state|province|region|oblast|krai|republic|prefecture|department|"
                  r"special capital region|autonomous)\s+of\s+", "", rec_name.lower())
    core = re.sub(r"\s+(oblast|krai|republic|state|prefecture|province|governorate|"
                  r"department|region|voivodeship|emirate|canton|special administrative|"
                  r"special region|capital territory)$", "", core).strip()
    if core and len(core) > 3:
        toks.add(core)
    return toks | set(PARENT_TOKENS.get(parent_iso, []))


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    admin1 = json.loads((ROOT / "data" / "admin1.json").read_text(encoding="utf-8"))
    countries = json.loads((ROOT / "data" / "countries.json").read_text(encoding="utf-8"))
    with_bundles = {r["iso3"] for r in admin1.values() if str(r.get("blindSummary","")).strip()}
    if sys.argv[1] == "--all":
        isos = sorted(with_bundles)
        if not isos:
            print("no blindSummary fields found yet"); return 0
    else:
        isos = [a.upper() for a in sys.argv[1:]]
    fails = warns = 0
    for iso in isos:
        units = {sid: r for sid, r in admin1.items() if r.get("iso3") == iso}
        if not units:
            print(f"[warn] {iso}: no admin1 units"); continue
        parent_name = (countries.get(iso, {}).get("name") or "").lower()
        missing = []
        for sid, r in sorted(units.items(), key=lambda x: x[1]["name"]):
            txt = str(r.get("blindSummary", "")).strip()
            if not txt:
                missing.append(r["name"]); continue
            probs = []
            for tok in tokens_for(r["name"], iso) | ({parent_name} if parent_name else set()):
                if tok and re.search(r"\b" + re.escape(tok) + r"\b", txt.lower()):
                    probs.append(f"IDENTITY-LEAK {tok!r}")
            for pat, why in BANNED_RES:
                m = re.search(pat, txt, re.I)
                if m:
                    probs.append(f"{why}: {m.group(0)!r}")
            hard = [p for p in probs if p.startswith(("IDENTITY-LEAK", "too"))]
            soft = [p for p in probs if p not in hard]
            if len(txt) < MIN_LEN: hard.append(f"too short ({len(txt)})")
            if len(txt) > MAX_LEN: hard.append(f"too long ({len(txt)})")
            if hard:
                print(f"[FAIL] {iso} {r['name']}: " + "; ".join(hard)); fails += 1
            if soft:
                print(f"[warn] {iso} {r['name']}: " + "; ".join(soft)); warns += 1
        if missing:
            print(f"[FAIL] {iso}: {len(missing)} units without blindSummary: "
                  f"{missing[:6]}" + ("…" if len(missing) > 6 else ""))
            fails += 1
        print(f"  {iso}: {len(units)-len(missing)}/{len(units)} validated")
    print(f"\nvalidate_bundles: {fails} FAIL, {warns} warnings")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
