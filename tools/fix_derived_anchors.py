#!/usr/bin/env python3
"""Fix the derived-territory anchor drift (systemic bug found via the Isle of Man).

During the countries phase, jurisdictions with no independent evidence base were
scored "parent (X.XX) with delta ±Y" and their summaries recorded the derivation
verbatim. Parent scores then MOVED during blind-pairwise recalibration (United
Kingdom 0.66→0.48, United States 0.50→0.36, France 0.82→0.67, China 0.53→0.40,
New Zealand 0.84→0.75, Netherlands 0.88→0.79, Morocco 0.25→0.18) while the
derivations kept the stale base. Fix: re-anchor each derived jurisdiction to the
parent's CURRENT score plus its researched delta. Deltas are overridden (with
reason in the note) only where a post-research regime change is documented:
  - US territories: federal anti-trans escalation since 2025 now dominates; the
    old +0.0x deltas (PR/GUM/VIR/MNP above a 0.50 US) were researched before it.
  - Cayman Islands: same-sex-relationships Act upheld on appeal (Nov 2025).
  - Western Sahara: occupation securitisation below Morocco's own baseline.
  - American Samoa: sodomy law on the books + SCOTUS marriage carve-out.

Also syncs the admin1 records that mirror these jurisdictions (SYN-* units and
the HKG/MAC exception records under CHN). Idempotent via the 're-anchored' marker.
Run only when no pairwise process holds data/admin1.json.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from build_data import band_label  # noqa: E402

# iso3 -> (parent, delta, note)
TERR = {
    # ---- United Kingdom ----
    "GIB": ("GBR", +0.10, "own legal system; same-sex marriage and protections in force; none of the EHRC single-sex code machinery applies; small, safe, tourism-oriented"),
    "BMU": ("GBR", +0.04, "own legal system; marriage equality since 2017; church-going conservative society but functioning protections"),
    "CYM": ("GBR", -0.12, "own penal code criminalises same-sex intimacy and the 2022 same-sex-relationships ban was upheld on appeal (2025, Privy Council pending) — materially worse than the UK mainland; override of the old zero delta"),
    "VGB": ("GBR", -0.06, "own legal system; decriminalised; conservative tight-knit island society, thin institutional cover"),
    "AIA": ("GBR", -0.04, "own legal system; decriminalised 2019; very small, very quiet"),
    "MSR": ("GBR", -0.04, "archaic criminal provisions on the books (unenforced); tiny, isolated"),
    "TCA": ("GBR", -0.04, "own legal system; decriminalised; resort envelope plus conservative island society"),
    "FLK": ("GBR", +0.10, "own legal system; full equality since 2017; tiny, safe, orderly"),
    "SHN": ("GBR", +0.06, "own legal system; decriminalised; remote, church-conservative"),
    "PCN": ("GBR", -0.10, "descendant-community governance; Christian-conservative, no public LGBT life"),
    "GGY": ("GBR", +0.12, "Crown Dependency, own parliament and equality law covering gender identity; the UK EHRC single-sex code does not extend here"),
    "IMN": ("GBR", +0.14, "Crown Dependency, own parliament: own Gender Recognition Act (2009) and Equality Act (2017) protect gender reassignment; neither the EHRC code nor the England/Wales prison regime extends here; no local gender-care pathway (residents travel to the UK)"),
    # ---- France ----
    "GUF": ("FRA", -0.06, "full French law applies; but strong religious-conservative norms, high violent crime, few LGBT services"),
    "GLP": ("FRA", -0.05, "full French law applies; conservative Catholic/evangelical social norms dominate everyday life"),
    "MTQ": ("FRA", -0.05, "full French law applies; modest visible scene in Fort-de-France; traditional norms persist"),
    "REU": ("FRA", -0.04, "full French law applies; conservative Catholic community norms; active local associations"),
    "MYT": ("FRA", -0.14, "French law nominally applies but the most conservative social environment of the overseas departments; protections largely ineffective in practice"),
    "NCL": ("FRA", -0.02, "full French law applies; customary-authority areas socially conservative; Nouméa tolerant"),
    "PYF": ("FRA", +0.00, "full French law applies; historically tolerant Ma'ohi culture (mahuu third-gender presence); tourism economy"),
    "WLF": ("FRA", -0.08, "French civil/criminal code applies, but chiefly/mission governance dominates social life"),
    "BLM": ("FRA", -0.02, "full French law; small resort island, calm social climate"),
    # ---- United States (override: post-2025 federal escalation) ----
    "PRI": ("USA", -0.03, "full US federal law and policy apply, including the 2025–26 federal anti-trans measures; Catholic-conservative social norms; no local shield — old +0.08 delta predates the federal escalation"),
    "GUM": ("USA", -0.07, "full US federal law applies; deeply Catholic Chamorro society with strong church influence in local politics — old +0.06 delta predates the federal escalation"),
    "VIR": ("USA", -0.02, "full US federal law applies; conservative Baptist island culture; archaic code provisions survive the 2014 revision — old delta predates the federal escalation"),
    "ASM": ("USA", -0.18, "US nationals under customary Fa'a Samoa governance: sodomy law on the books, and the constitutional marriage definition was upheld against the SCOTUS marriage ruling (2024) — the least protective US territory"),
    "MNP": ("USA", -0.06, "full US federal law applies; heavily church-influenced Saipan/Tinian culture; contract-worker economy limits visibility — old delta predates the federal escalation"),
    # ---- Denmark / Netherlands ----
    "FRO": ("DNK", -0.04, "home rule with its own legislation; marriage equality came late (2017) after church-state friction; tight-knit conservative Lutheran society"),
    "GRL": ("DNK", -0.02, "self-rule; Danish human-rights framework applies; comparatively tolerant Inuit communities; policing capacity is the weak link"),
    "ABW": ("NLD", -0.08, "autonomous country within the Kingdom; Charter equality framework; Catholic community norms; tourism economy"),
    "CUW": ("NLD", -0.06, "autonomous country within the Kingdom; penal code modernised; Willemstad has the Caribbean's oldest organised community; conservative interior"),
    "BES": ("NLD", -0.10, "public bodies of the Netherlands — Dutch equality law applies directly but small, more religious island societies"),
    # ---- New Zealand ----
    "COK": ("NZL", -0.30, "free association with NZ; own penal code still criminalises male same-sex conduct (rarely enforced); church-dominated society; akava'ine traditional presence"),
    "NIU": ("NZL", -0.20, "free association with NZ; very small; no documented enforcement but no protections either"),
    # ---- China ----
    "HKG": ("CHN", +0.18, "own legal system under Basic Law: no criminalisation, ordinance protections and an active court arena; NSL-era chill on open activism; Pride continues under heavier police conditions"),
    "MAC": ("CHN", +0.10, "own legal system: decriminalised since 1995, no protection legislation, government anti-discrimination bills repeatedly shelved; conservative business-and-church climate"),
    # ---- Morocco (override: occupation context) ----
    "ESH": ("MAR", -0.07, "disputed territory under Moroccan administration: Morocco's criminal law applies plus occupation-era securitisation and no civil space — below even Morocco's own baseline"),
}

MARK = "re-anchored"
# CHN-parented admin1 records that mirror HKG/MAC country units
ADMIN1_MIRROR = {"HKG": "Hong Kong", "MAC": "Macao"}


def main() -> int:
    cp = ROOT / "data" / "countries.json"
    ap = ROOT / "data" / "admin1.json"
    c = json.loads(cp.read_text(encoding="utf-8"))
    a = json.loads(ap.read_text(encoding="utf-8"))
    today = date.today().isoformat()
    fixed = skipped = absent = 0
    for iso, (parent, delta, note) in TERR.items():
        rec = c.get(iso)
        if rec is None:
            absent += 1
            continue
        if MARK in (rec.get("summary") or ""):
            skipped += 1
            continue
        base = c[parent]["score"]
        score = round(min(1.0, max(0.0, base + delta)), 4)
        rec["summary"] = (
            f"<p>{rec['name']}: {note}. Scored as a dependent jurisdiction: the "
            f"parent framework governs what a visitor encounters, plus local "
            f"society and enforcement.</p>"
            f"<p><em>Score re-anchored {today}: {c[parent]['name']} "
            f"({base:.2f}) plus a local delta of {delta:+.2f}. This jurisdiction "
            f"was not covered by the dedicated state/province research passes.</em></p>")
        rec["score"] = score
        rec["researchedAt"] = today
        if "band" in rec:
            rec["band"] = band_label(score)
        # mirror admin1 records that carry this jurisdiction's score
        for sid, ar in a.items():
            hit = ar.get("iso3") == iso
            if not hit and iso in ADMIN1_MIRROR and ar.get("iso3") == "CHN":
                hit = ADMIN1_MIRROR[iso] in (ar.get("name") or "")
            if hit:
                ar["score"] = score
                ar["band"] = rec.get("band", ar.get("band"))
                ar["summary"] = (f"<p>This unit is a distinct jurisdiction scored at "
                                 f"country level (it has no separate state/province "
                                 f"assessment). {note}.</p>")
                ar["researchedAt"] = today
        fixed += 1
    print(f"re-anchored: {fixed} · already fixed: {skipped} · not on map: {absent}")
    for tmp, data in ((cp, c), (ap, a)):
        t = tmp.with_suffix(".json.tmp")
        t.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        os.replace(t, tmp)
    print("written (both files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
