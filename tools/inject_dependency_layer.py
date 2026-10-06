#!/usr/bin/env python3
"""Country-mode dependency injector: territories inherit their parent's layer.

Systematic replacement for hand-editing dependency dossiers (2026-10-05):
every dependent territory's dossier must state, plainly, which parts of the
parent's regime it stands under and which do not reach it. The text is
TEMPLATED: one semantic body per dependency class, rendered twice — visible
with real names, blind with fixed vocabulary — so neither can leak the other's
vocabulary.

Usage: python3 tools/inject_dependency_layer.py [--only ASM,FLK] [--dry]
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
C_PATH = ROOT / "data" / "countries.json"

PARENT_NAME = {"USA": "the United States", "GBR": "the United Kingdom",
               "FRA": "France", "NLD": "the Netherlands", "DNK": "Denmark",
               "NZL": "New Zealand"}

# Template bodies. {P} = parent name (visible) / "the parent nation" (blind).
# {PD} = parent's foreign-affairs department (visible) / "the parent nation's
# foreign-affairs department" (blind). {T} = territory (visible) / "this
# state/province" (blind).
US_FULL_FEDERAL = ("{T} stands under the full {P} federal regime: {P} travel "
 "documents reflect sex assigned at birth and the X marker has been eliminated "
 "(January 2025 executive order), so a trans visitor arriving on {P} documents "
 "faces that mismatch at entry; airport screening follows federal procedure; the "
 "order halting federal funding for gender-affirming care reaches federally "
 "funded institutions here, so care access during a visit cannot be assumed; and "
 "in February 2025 {PD} additionally announced visa denials for trans athletes "
 "seeking entry for women's sports.")

UK_NOT_EXTEND = ("{P}'s Equality Act 2010, its 2025 single-sex-services code and "
 "the April 2025 Supreme Court 'For Women Scotland' ruling do not extend to {T} "
 "— they govern Great Britain, and no Order in Council extends them; local "
 "ordinances govern instead. The UK Gender Recognition Act 2004 does not itself "
 "extend, though local ordinances may recognise its certificates. {P} passport "
 "policy follows UK passport holders wherever they travel and does not change "
 "local law.")

UK_NOT_EXTEND_SIMPLE = ("{P}'s Equality Act 2010 and its 2025 single-sex-services "
 "code do not automatically extend to {T}; local law governs, with {P} measures "
 "extendable only by Order in Council.")

FR_EXTENDS = ("{T} stands under {P}'s national law as in the metropole: identity "
 "documents, criminal law, the anti-discrimination statute and the marriage "
 "regime apply here as in {P} proper.")

FR_NOT_FULL = ("Full {P} metropolitan law does not extend to {T} unchanged; the "
 "territory legislates locally on many matters, with {P} responsible for "
 "documents and justice.")

NL_EXTENDS = ("{T} stands under {P}'s national criminal law and document rules "
 "as they apply here.")

DK_EXTENDS = ("{T} stands under {P}'s national criminal law and document rules "
 "as they apply here.")

NZ_PASSPORTS = ("{P} nationality and passport rules apply to {T}; local criminal "
 "law governs conduct.")

DEPEND = {
    "ASM": ("USA", US_FULL_FEDERAL), "GUM": ("USA", US_FULL_FEDERAL),
    "VIR": ("USA", US_FULL_FEDERAL), "MNP": ("USA", US_FULL_FEDERAL),
    "PRI": ("USA", US_FULL_FEDERAL),
    "FLK": ("GBR", UK_NOT_EXTEND),
    "GIB": ("GBR", UK_NOT_EXTEND_SIMPLE), "BMU": ("GBR", UK_NOT_EXTEND_SIMPLE),
    "CYM": ("GBR", UK_NOT_EXTEND_SIMPLE), "VGB": ("GBR", UK_NOT_EXTEND_SIMPLE),
    "AIA": ("GBR", UK_NOT_EXTEND_SIMPLE), "MSR": ("GBR", UK_NOT_EXTEND_SIMPLE),
    "TCA": ("GBR", UK_NOT_EXTEND_SIMPLE), "SHN": ("GBR", UK_NOT_EXTEND_SIMPLE),
    "PCN": ("GBR", UK_NOT_EXTEND_SIMPLE), "GGY": ("GBR", UK_NOT_EXTEND_SIMPLE),
    "IMN": ("GBR", UK_NOT_EXTEND_SIMPLE), "JEY": ("GBR", UK_NOT_EXTEND_SIMPLE),
    "GLP": ("FRA", FR_EXTENDS), "MTQ": ("FRA", FR_EXTENDS),
    "GUF": ("FRA", FR_EXTENDS), "REU": ("FRA", FR_EXTENDS),
    "PYF": ("FRA", FR_NOT_FULL), "NCL": ("FRA", FR_NOT_FULL),
    "MYT": ("FRA", FR_EXTENDS), "BLM": ("FRA", FR_EXTENDS),
    "CUW": ("NLD", NL_EXTENDS), "ABW": ("NLD", NL_EXTENDS),
    "BES": ("NLD", NL_EXTENDS),
    "FRO": ("DNK", DK_EXTENDS), "GRL": ("DNK", DK_EXTENDS),
    "COK": ("NZL", NZ_PASSPORTS), "NIU": ("NZL", NZ_PASSPORTS),
}

ALREADY = re.compile(
    r"stand[s]? under|federal (?:entry|documents|regime)|executive order|"
    r"Equality Act 2010|do(?:es)? not (?:automatically )?extend|Order in Council|"
    r"national framework|parent'?s? (?:law|statute|code)|{P}'s? (?:Equality|national)",
    re.I)


def render(tpl: str, iso: str, blind: bool) -> str:
    parent = DEPEND[iso][0]
    subs = {"{P}": "the parent nation" if blind else PARENT_NAME[parent],
            "{T}": "this state/province" if blind else C_NAME.get(iso, iso),
            "{PD}": "the parent nation's foreign-affairs department" if blind
                    else f"the {PARENT_NAME[parent]} State Department"}
    for k, v in subs.items():
        tpl = tpl.replace(k, v)
    if blind:
        tpl = tpl.replace(" federal ", " national ")
        tpl = tpl.replace("federally funded", "nationally funded")
        tpl = tpl.replace("federal regime", "national regime")
        tpl = tpl.replace("the territory legislates locally",
                                "the state/province legislates locally")
    return tpl


C_NAME: dict[str, str] = {}


def main():
    global C_NAME
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    only = {x.strip().upper() for x in args.only.split(",") if x.strip()}
    C = json.loads(C_PATH.read_text())
    C_NAME = {iso: r.get("name", iso) for iso, r in C.items()}
    changed = 0
    for iso, r in sorted(C.items()):
        if iso not in DEPEND:
            continue
        if only and iso not in only:
            continue
        summ = str(r.get("summary", ""))
        already = ALREADY.pattern.replace("{P}", re.escape(PARENT_NAME[DEPEND[iso][0]]))
        if re.search(already, summ, re.I):
            continue
        vis = render(DEPEND[iso][1], iso, blind=False)
        bl = render(DEPEND[iso][1], iso, blind=True)
        r["summary"] = f"<p>{vis}</p>" + summ
        bl0 = str(r.get("blindSummary") or "")
        r["blindSummary"] = f"<p>{bl}</p>" + bl0
        changed += 1
        print(("would inject " if args.dry else "injected ") + iso)
    if not args.dry and changed:
        C_PATH.write_text(json.dumps(C, ensure_ascii=False, indent=1), encoding="utf-8")
    print(("would touch " if args.dry else "updated ") + f"{changed} dependencies")


if __name__ == "__main__":
    main()