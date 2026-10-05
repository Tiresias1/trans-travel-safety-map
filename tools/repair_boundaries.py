#!/usr/bin/env python3
"""Repair invalid geometries in boundaries/*.geojson (shapely make_valid).

The geoBoundaries simplified sources ship with self-intersecting rings on some
large countries (CHN, USA, ...). Renderers draw invalid topology with
flickering slivers and ghost overlaps. This tool normalises every geometry via
shapely.make_valid, keeps only polygon parts with real area, preserves all
properties, and writes back. Idempotent.

Usage: python3 tools/repair_boundaries.py [countries|admin1|both]
"""
import json, sys
from pathlib import Path
from shapely.geometry import mapping, shape
from shapely.ops import unary_union
from shapely.validation import make_valid

ROOT = Path(__file__).resolve().parent.parent

def _polygonize(g):
    if g.geom_type == "Polygon":
        return [g]
    if g.geom_type == "MultiPolygon":
        return list(g.geoms)
    if g.geom_type == "GeometryCollection":
        out = []
        for sub in g.geoms:
            out.extend(_polygonize(sub))
        return out
    return []  # Point, LineString, etc.: drop

def repair(path: Path) -> None:
    gj = json.loads(path.read_text())
    repaired = 0
    for f in gj["features"]:
        g = shape(f["geometry"])
        if not g.is_valid:
            repaired += 1
            g = make_valid(g)
        parts = _polygonize(g)
        parts = [p for p in parts if p.area > 1e-7]  # drop sliver debris
        if len(parts) == 1:
            g = parts[0]
        elif len(parts) > 1:
            g = unary_union(parts)
        else:
            g = mpty = __import__("shapely.geometry", fromlist=["Polygon"]).Polygon()
        f["geometry"] = mapping(g)
    path.write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
    n = len(gj["features"])
    print(f"{path.name}: repaired {repaired}; {n} features")

if __name__ == "__main__":
    which = sys.argv[1:] or ["countries", "admin1"]
    for w in which:
        repair(ROOT / "boundaries" / f"{w}.geojson")