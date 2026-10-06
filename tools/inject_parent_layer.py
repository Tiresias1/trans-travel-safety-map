#!/usr/bin/env python3
"""Inject the parent framework layer into dossier-region summaries.

For every ADM1 dossier record, the visitor stands under the parent country's
framework (documents/passports, border/entry, national criminalisation,
national discrimination law, federal facilities clause). Research shows many
region dossiers (e.g. US states) omit this layer because they focus on state
law. This pass restates the applicable parent items so the readable dossier
carries them (and the pairwise rater sees them), per
research/admin1-inheritance-matrix.md column A.

Mechanical rule: for each parent, a fixed parent-layer <p> is injected at the
top of the region's summary ONLY IF the region summary does not already assert
a "stands under the national framework" sentence (checked for the parent's
keywords). Injection is claim-faithful: the text comes from the parent's LIVE
dossier and is identical across regions of the same parent. Blind mirrors get
the same injection with the fixed vocabulary applied (state/province, national,
parent) and must pass the blind gate.

Usage: python3 tools/inject_parent_layer.py [--parents USA,MYS] [--dry]
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
C = json.loads((ROOT / "data" / "countries.json").read_text())
A = json.loads((ROOT / "data" / "admin1.json").read_text())
A_PATH = ROOT / "data" / "admin1.json"

# parent -> universal framework sentence (column A). Written from each parent's
# live dossier claims; kept factual and identical across a parent's regions.
PARENT_LAYER = {
    "USA": ("Visitors stand under the national framework in every state: federal "
            "travel documents reflect sex assigned at birth and the X marker was "
            "eliminated (January 2025 executive order), so a trans visitor's "
            "documents can mismatch; airport screening and visa decisions follow "
            "national rules, including visa discretion over transgender athletes "
            "seeking entry for women's sporting events."),
    "MYS": ("Every state and the federal territory stand under the national "
            "framework: Sharia law prohibits a man posing as a woman across all "
            "states (up to three years' jail), so the criminalisation baseline "
            "applies to every visitor in every region."),
    "ESP": ("Visitors in every autonomous community stand under the national "
            "framework: the 2023 trans-equality law grants self-declared gender "
            "marker change and national anti-discrimination protections, and the "
            "penal-code reform protects against hate crimes."),
    "DEU": ("Visitors in every Land stand under the national framework: federal "
            "constitutional and equality protections apply nationwide, national "
            "identity documents and marriage law are uniform, and no Land can "
            "remove the federal floor."),
    "GBR": ("Visitors across the whole country stand under the national framework: "
            "passport/documents, entry rules, national marriage and criminal law "
            "are uniform; the single-sex-services rollback applies under the "
            "national equality framework (with devolved divergences in the "
            "regions below)."),
    "RUS": ("Visitors in every region stand under the national framework: since "
            "2023 legal gender recognition and gender-affirming care are banned "
            "nationwide, and the propaganda and 'extremist movement' laws apply "
            "in every region."),
    "NGA": ("Visitors in every state stand under the national framework: the "
            "Same-Sex Marriage (Prohibition) Act applies nationwide with up to "
            "14 years' imprisonment for all persons including tourists; "
            "additional Sharia criminal law applies in the northern states."),
    "CAN": ("Visitors in every province stand under the national framework: "
            "gender identity and expression are protected grounds under the "
            "Canadian Human Rights Act and the Criminal Code's hate-crime "
            "provisions, and marriage and identity documents are national."),
    "AUS": ("Visitors in every state stand under the national framework: "
            "gender identity is a protected ground under the federal Sex "
            "Discrimination Act, and marriage and federal documents are "
            "uniform nationwide."),
    "FRA": ("Visitors in every region stand under the national framework: "
            "national law on identity documents, anti-discrimination, marriage "
            "and criminal law applies uniformly across metropolitan and "
            "overseas regions."),
    "ITA": ("Visitors in every region stand under the national framework: "
            "national civil-law uniformities apply to identity, marriage and "
            "anti-discrimination protections nationwide."),
}

# fixed-vocabulary blind equivalent (LANE_SPECS 7): no country geography names,
# no "federal/territory/island" banned words; "national" instead of federal.
# Keep identical structure to the visible injection.
BLIND_LAYER = {
    "USA": ("Visitors stand under the national framework in every state/province: "
            "national travel documents reflect sex assigned at birth and the X "
            "marker was eliminated (January 2025 executive order), so a trans "
            "visitor's documents can mismatch; airport screening and visa "
            "decisions follow national rules, including visa discretion over "
            "transgender athletes seeking entry for women's sporting events."),
    "MYS": ("Every state/province and the national seat stand under the national "
            "framework: the religious-law system prohibits a man posing as a "
            "woman across all states/provinces (up to three years' jail), so the "
            "criminalisation baseline applies to every visitor in every region."),
    "ESP": ("Visitors in every autonomous state/province stand under the national "
            "framework: the 2023 trans-equality law grants self-declared gender "
            "marker change and national anti-discrimination protections, and the "
            "penal-code reform protects against hate crimes."),
    "DEU": ("Visitors in every state/province stand under the national framework: "
            "national constitutional and equality protections apply nationwide, "
            "national identity documents and marriage law are uniform, and no "
            "state/province can remove the national floor."),
    "GBR": ("Visitors across the whole country stand under the national framework: "
            "passport/documents, entry rules, national marriage and criminal law "
            "are uniform; the single-sex-services rollback applies under the "
            "national equality framework (with devolved divergences in the "
            "regions below)."),
    "RUS": ("Visitors in every region stand under the national framework: since "
            "2023 legal gender recognition and gender-affirming care are banned "
            "nationwide, and the propaganda and 'extremist movement' laws apply "
            "in every region."),
    "NGA": ("Visitors in every state/province stand under the national framework: "
            "the same-sex marriage prohibition act applies nationwide with up to "
            "14 years' imprisonment for all persons including tourists; "
            "additional religious-law criminal provisions apply in the north."),
    "CAN": ("Visitors in every province stand under the national framework: "
            "gender identity and expression are protected grounds under the "
            "national human-rights act and the criminal code's hate-crime "
            "provisions, and marriage and identity documents are national."),
    "AUS": ("Visitors in every state/province stand under the national framework: "
            "gender identity is a protected ground under the national sex "
            "discrimination act, and marriage and national documents are "
            "uniform nationwide."),
    "FRA": ("Visitors in every region stand under the national framework: "
            "national law on identity documents, anti-discrimination, marriage "
            "and criminal law applies uniformly across the country."),
    "ITA": ("Visitors in every region stand under the national framework: "
            "national civil-law uniformities apply to identity, marriage and "
            "anti-discrimination protections nationwide."),
}

# per-parent: check either of these signals to decide the region already states it
ALREADY = {
    "USA": r"stand[s]? under the national framework|federal travel documents|national framework",
    "MYS": r"stand[s]? under the national framework|every state and the federal",
    "ESP": r"stand[s]? under the national framework|national framework",
    "DEU": r"stand[s]? under the national framework|national framework",
    "GBR": r"stand[s]? under the national framework|national framework",
    "RUS": r"stand[s]? under the national framework|national framework",
    "NGA": r"stand[s]? under the national framework|national framework",
    "CAN": r"stand[s]? under the national framework|national framework",
    "AUS": r"stand[s]? under the national framework|national framework",
    "FRA": r"stand[s]? under the national framework|national framework",
    "ITA": r"stand[s]? under the national framework|national framework",
}


PARENT_NAMES = {"USA": "the United States", "MYS": "Malaysia", "ESP": "Spain",
               "DEU": "Germany", "GBR": "the United Kingdom", "RUS": "Russia",
               "NGA": "Nigeria", "CAN": "Canada", "AUS": "Australia",
               "FRA": "France", "ITA": "Italy"}


def inject(summary: str, blind: str, parent: str) -> tuple[bool, str, str]:
    vis = PARENT_LAYER.get(parent)
    if vis and parent in PARENT_NAMES:
        # rule 7.0: visible layer NAMES the parent; blind layer never does
        vis = vis.replace("the national framework", f"the {PARENT_NAMES[parent]} national framework", 1)
    bl = BLIND_LAYER.get(parent)
    if not vis:
        return False, summary, blind
    if re.search(ALREADY[parent], summary, re.I):
        return False, summary, blind
    new_vis = f"<p>{vis}</p>" + summary
    new_blind = f"<p>{bl}</p>" + (blind or summary)
    return True, new_vis, new_blind


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parents", default="", help="comma ISO3 list of parents to process")
    ap.add_argument("--dry", action="store_true", help="print what would change, write nothing")
    args = ap.parse_args()
    parents = [p.strip().upper() for p in args.parents.split(",") if p.strip()] or list(PARENT_LAYER)
    changed = 0
    for sid, r in A.items():
        if not r.get("dossier"):
            continue
        iso = r.get("iso3")
        if iso not in parents or iso not in PARENT_LAYER:
            continue
        ok, ns, nb = inject(str(r.get("summary", "")), str(r.get("blindSummary", "")), iso)
        if ok:
            changed += 1
            if args.dry:
                print(f"[dry] {iso}/{r['name']}: would inject")
            else:
                r["summary"] = ns
                if nb and r.get("blindSummary"):
                    r["blindSummary"] = nb
    if not args.dry:
        A_PATH.write_text(json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{'[dry] would touch' if args.dry else 'updated'} {changed} region dossiers "
          f"({parents})")


if __name__ == "__main__":
    main()