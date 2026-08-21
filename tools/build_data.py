#!/usr/bin/env python3
"""Build data/*.json from research notes, compute ranks, validate.

Reads:  data/countries.json (hand/data-model maintained), data/admin1.json
        (optional), boundaries/*.geojson (for key coverage checks)
Writes: data/meta.json; augments records with rank fields.

Validation rules (fail loudly):
- score in [0,1], exactly 2 decimals
- band consistent with score
- summary non-empty, 1-4 <p> paragraphs, <= 2500 chars
- sources non-empty unless inherited
- every boundary polygon key has a data record (warning only — research in
  progress) and every data record matches a polygon (error)
"""
import json, os, re, sys

BANDS = [
    (0.2, "Do Not Travel"),
    (0.4, "High Risk"),
    (0.6, "Elevated Risk"),
    (0.8, "Reduced Risk"),
    (1.01, "Low Risk"),
]
GRADIENT_ANCHORS = [
    [0.0, "#67000d"], [0.1, "#d73027"], [0.3, "#fc8d59"], [0.5, "#fee08b"],
    [0.7, "#91cf60"], [0.9, "#1a9850"], [1.0, "#a8dbe8"],
]

def band_label(score):
    for mx, label in BANDS:
        if score < mx:
            return label
    return BANDS[-1][1]

def valid_summary(s):
    if not s:
        return False
    if len(s) > 2500:
        return False
    n_p = s.count("<p") + s.count("<P")
    return 1 <= n_p <= 4

def check_record(iso, r, errors, inherited_ok=False):
    if not isinstance(r.get("score"), (int, float)):
        errors.append(f"{iso}: missing score")
        return
    sc = r["score"]
    if not (0 <= sc <= 1):
        errors.append(f"{iso}: score out of range: {sc}")
    if round(sc, 2) != sc:
        errors.append(f"{iso}: score not 2dp: {sc}")
    if "band" in r and r["band"] != band_label(sc):
        errors.append(f"{iso}: band mismatch: {r['band']} vs {band_label(sc)}")
    if not valid_summary(r.get("summary", "")):
        errors.append(f"{iso}: bad summary")
    if not r.get("sources") and not (inherited_ok and r.get("inherited")):
        errors.append(f"{iso}: no sources")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(r.get("researchedAt", ""))):
        errors.append(f"{iso}: bad/missing researchedAt")

def add_ranks(d, total, key="rank"):
    """competition ranking: ties share best rank"""
    items = sorted(d.items(), key=lambda kv: -kv[1]["score"])
    prev = None; rank = 0
    for i, (k, r) in enumerate(items, 1):
        if prev is None or r["score"] != prev:
            rank = i; prev = r["score"]
        r[key] = rank
    return d

def main():
    errors, warnings = [], []

    countries = json.load(open("data/countries.json"))
    geo = json.load(open("boundaries/countries.geojson"))
    geo_isos = {f["properties"]["iso3"] for f in geo["features"]}

    for iso, r in countries.items():
        check_record(iso, r, errors)
    missing = geo_isos - set(countries)
    if missing:
        warnings.append(f"{len(missing)} polygons without data (research in progress), e.g. {sorted(missing)[:8]}")
    orphans = set(countries) - geo_isos
    if orphans:
        errors.append(f"records without polygons: {sorted(orphans)}")

    add_ranks(countries, len(countries))
    json.dump(countries, open("data/countries.json", "w"), indent=1, ensure_ascii=False)

    admin1 = {}
    if os.path.exists("data/admin1.json"):
        admin1 = json.load(open("data/admin1.json"))
        geo1 = json.load(open("boundaries/admin1.geojson"))
        geo1_ids = {f["properties"]["shapeID"] for f in geo1["features"]}
        for sid, r in admin1.items():
            check_record(sid, r, errors, inherited_ok=True)
        if set(admin1) - geo1_ids:
            errors.append(f"admin1 records without polygons: {sorted(set(admin1) - geo1_ids)[:8]}")
        n_missing = len(geo1_ids - set(admin1))
        warnings.append(f"{n_missing} admin1 polygons without data")
        add_ranks(admin1, len(admin1), key="worldRank")
        # within-country ranks
        by_country = {}
        for sid, r in admin1.items():
            by_country.setdefault(r["iso3"], []).append((sid, r))
        for iso, lst in by_country.items():
            lst.sort(key=lambda kv: -kv[1]["score"])
            prev = None; rank = 0; total = len(lst)
            for i, (sid, r) in enumerate(lst, 1):
                if prev is None or r["score"] != prev:
                    rank = i; prev = r["score"]
                r["countryRank"] = rank
                r["unitsInCountry"] = total
        json.dump(admin1, open("data/admin1.json", "w"), indent=1, ensure_ascii=False)

    meta = {
        "generatedAt": "2026-08-21",
        "methodologyVersion": "1.0",
        "bandEdges": [0.2, 0.4, 0.6, 0.8, 1.0],
        "bandLabels": [b[1] for b in BANDS],
        "gradientAnchors": GRADIENT_ANCHORS,
        "totalCountries": len(countries),
        "totalAdmin1": len(admin1),
        "disputedBoundaryNotes": "tools/patch_dejure.md",
    }
    json.dump(meta, open("data/meta.json", "w"), indent=1)

    for w in warnings:
        print("WARN:", w)
    if errors:
        print("\n".join("ERROR: " + e for e in errors))
        sys.exit(1)
    print(f"OK: {len(countries)} countries, {len(admin1)} admin1 units; ranks written; meta written")

if __name__ == "__main__":
    main()
