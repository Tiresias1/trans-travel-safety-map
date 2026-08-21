#!/usr/bin/env python3
"""Post-simplification fixes: cut enclave microstates out of their neighbours
(buffered so the gap survives coarse zoom), drop null geometries."""
import json, sys
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

SRC = sys.argv[1] if len(sys.argv) > 1 else "boundaries/countries.geojson"
CUTS = {  # tiny -> list of neighbours to cut it from
    "VAT": ["ITA"], "MCO": ["FRA"],
}
BUF = 0.004  # ~400 m gap

g = json.load(open(SRC))
feats = [f for f in g["features"] if f.get("geometry") and f["geometry"].get("coordinates")]
by_iso = {f["properties"]["iso3"]: f for f in feats}
for tiny, neighbors in CUTS.items():
    if tiny not in by_iso:
        continue
    t = shape(by_iso[tiny]["geometry"]).buffer(BUF)
    for n in neighbors:
        if n in by_iso:
            s = shape(by_iso[n]["geometry"]).difference(t)
            by_iso[n]["geometry"] = mapping(s if s.is_valid else s.buffer(0))
    print(f"cut {tiny} from {neighbors}")
g["features"] = feats
json.dump(g, open(SRC, "w"))
print(f"postfixed {SRC}: {len(feats)} features")
