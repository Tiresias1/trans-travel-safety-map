#!/usr/bin/env python3
"""Stamp an `island` property on every boundary feature (countries + admin1).

A feature is `island: true` when it has no land-boundary neighbour at the SAME
level (country vs country; admin1 vs admin1) within a small tolerance
(GEOJSON gaps make raw `touches()` unreliable; we buffer by TOL degrees and
test `intersects`).

Used by the map to double dot-formation sensitivity for small islands only:
an island that renders a few pixels wide gets a dot at up to 2x the size
threshold a mainland unit would (small islands need more help to be visible).

Writes back to boundaries/*.geojson. Idempotent (overwrites the property).
"""
import json
import sys
from pathlib import Path
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parent.parent
TOL = 0.04  # degrees ~ approx 4 km; covers GEOJSON vertex gaps

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def stamp(path):
    gj = load(path)
    feats = gj["features"]
    geoms = []
    for i, f in enumerate(feats):
        g = shape(f["geometry"])
        if g.is_empty or g.area <= 0:
            geoms.append((i, None, None))
        else:
            geoms.append((i, g.buffer(TOL), f["properties"]))
    n_island = 0
    for i, g, props in geoms:
        if g is None:
            props["island"] = False
            continue
        has_neighbour = False
        for j, gj_, _ in geoms:
            if i == j or gj_ is None:
                continue
            if g.intersects(gj_):
                has_neighbour = True
                break
        props["island"] = not has_neighbour
        n_island += props["island"]
    out = Path(path)
    out.write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
    print(f"{path}: stamped island on {n_island}/{len(feats)} features")

if __name__ == "__main__":
    which = sys.argv[1:] or ["countries", "admin1"]
    for w in which:
        stamp(ROOT / "boundaries" / f"{w}.geojson")