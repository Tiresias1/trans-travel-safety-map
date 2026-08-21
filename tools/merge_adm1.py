#!/usr/bin/env python3
"""Merge gbOpen ADM1 per-country files into one FeatureCollection.

Output: boundaries/admin1_merged.geojson
Properties per feature: {shapeID, iso3, name}

Countries present in ADM0 but lacking ADM1 units get a synthetic unit
(shapeID = "SYN-<ISO3>") from the merged ADM0 geometry, so every clickable
country has an admin-layer record that falls back to the national score.
"""
import glob, json, os
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from shapely.validation import make_valid

RAW1 = "raw_adm1"
ADM0 = "boundaries/countries_merged.geojson"
OUT = "boundaries/admin1_merged.geojson"

def main():
    feats = []
    isos_with_adm1 = set()
    for fp in sorted(glob.glob(f"{RAW1}/*_ADM1.geojson")):
        iso = os.path.basename(fp)[:3]
        g = json.load(open(fp))
        n = 0
        for f in g["features"]:
            if not f.get("geometry"):
                continue
            p = f.get("properties", {})
            sid = p.get("shapeID") or f"{iso}-{n}"
            name = p.get("shapeName") or f"{iso} unit {n}"
            feats.append({
                "type": "Feature",
                "properties": {
                    "shapeID": sid,
                    "iso3": iso,  # country code from the gbOpen file group
                    "code": p.get("shapeISO") or None,  # subdivision ISO 3166-2 code
                    "name": name,
                },
                "geometry": f["geometry"],
            })
            n += 1
        if n:
            isos_with_adm1.add(iso)
        print(f"{iso}: {n} units", flush=True)

    adm0 = json.load(open(ADM0))
    syn = 0
    for f in adm0["features"]:
        iso = f["properties"]["iso3"]
        if iso not in isos_with_adm1:
            feats.append({
                "type": "Feature",
                "properties": {
                    "shapeID": f"SYN-{iso}",
                    "iso3": iso,
                    "name": f["properties"]["name"],
                },
                "geometry": f["geometry"],
            })
            syn += 1
    print(f"synthetic units added: {syn}")

    fc = {"type": "FeatureCollection", "features": feats}
    json.dump(fc, open(OUT, "w"))
    print(f"wrote {OUT}: {len(feats)} features, {os.path.getsize(OUT)/1e6:.1f} MB")

if __name__ == "__main__":
    main()
