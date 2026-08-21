#!/usr/bin/env python3
"""Promote special ADM1 units to country-level units in the countries layer.

Hong Kong + Macao (from CHN ADM1) and Puerto Rico (from USA ADM1) have legal
regimes distinct enough from their parent state that visitors should see them
scored separately in the COUNTRIES view.

Reads:  boundaries/countries_merged.geojson, raw_adm1/CHN_ADM1.geojson,
        raw_adm1/USA_ADM1.geojson
Writes: boundaries/countries_promoted.geojson
"""
import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from shapely.validation import make_valid

PROMOTIONS = [  # (source ISO, ADM1 shapeName match, new ISO3, new name)
    ("CHN", "Hong Kong Special Administrative Region", "HKG", "Hong Kong"),
    ("CHN", "Macau Special Administrative Region", "MAC", "Macao"),
    ("USA", "Puerto Rico", "PRI", "Puerto Rico"),
]

def main():
    countries = json.load(open("boundaries/countries_merged.geojson"))

    by_iso = {f["properties"]["iso3"]: f for f in countries["features"]}
    new_feats = []
    for src_iso, match, new_iso, new_name in PROMOTIONS:
        g = json.load(open(f"raw_adm1/{src_iso}_ADM1.geojson"))
        hits = [f for f in g["features"]
                if f.get("properties", {}).get("shapeName") == match]
        if not hits:
            print(f"NOT FOUND: {src_iso} / {match}")
            continue
        # union in case of multiple parts
        parts = [shape(f["geometry"]) for f in hits]
        s = unary_union(parts)
        if not s.is_valid:
            s = make_valid(s)
        src = shape(by_iso[src_iso]["geometry"])
        remainder = src.difference(s)
        if remainder.is_valid is False:
            remainder = make_valid(remainder)
        by_iso[src_iso]["geometry"] = mapping(remainder)
        new_feats.append({
            "type": "Feature",
            "properties": {"iso3": new_iso, "name": new_name},
            "geometry": mapping(s),
        })
        print(f"promoted {new_name} ({new_iso}), area {s.area:.3f} deg²; "
              f"parent {src_iso} now {remainder.area:.3f} deg²")

    countries["features"].extend(new_feats)
    json.dump(countries, open("boundaries/countries_promoted.geojson", "w"))
    print(f"wrote boundaries/countries_promoted.geojson: "
          f"{len(countries['features'])} features")

if __name__ == "__main__":
    main()
