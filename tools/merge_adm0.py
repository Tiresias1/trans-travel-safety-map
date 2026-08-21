#!/usr/bin/env python3
"""Merge gbOpen ADM0 per-country files into one de-jure-resolved FeatureCollection.

Applies the patches documented in tools/patch_dejure.md, then a sequential
clip pass (later country in ORDER wins residual sliver overlaps).

Output: boundaries/countries_merged.geojson (properties: iso3, name)
"""
import glob, json, os, sys
from shapely.geometry import shape, mapping, box
from shapely.ops import unary_union
from shapely.validation import make_valid

RAW = "raw_adm0"
EXTRA = "raw_extra"
OUT = "boundaries/countries_merged.geojson"
MIN_AREA = 0.00004  # deg² (~0.4 km²): keep even Vatican-sized polygons

# Order for the generic clip pass: later = wins overlap slivers.
# Explicit ORDER entries only matter for pairs listed in patch_dejure.md.
CLIP_ORDER = [
    # (Everything not listed is alphabetical by default; these adjustments
    # encode the 'later wins' decisions — the LATER country keeps any overlap:
    #   RUS after JPN  (southern Kurils -> Russia)
    #   SSD after KEN  (Ilemi Triangle -> South Sudan)
    #   EGY after SDN  (Hala'ib Triangle -> Egypt)
    #   TWN after CHN  (Taiwan separate)
    #   ESH after MAR  (Western Sahara separate; Morocco loses its W.Sahara claim)
    #   ASM/GUM/MNP/VIR after USA (US territories separate from USA polygon)
    "JPN", "RUS",
    "KEN", "SSD",
    "SDN", "EGY",
    "CHN", "TWN",
    "MAR", "ESH",
    "USA", "ASM", "GUM", "MNP", "VIR",
]

def load():
    idx = json.load(open(f"{RAW}/index.json"))
    polys = {}
    for fp in sorted(glob.glob(f"{RAW}/*_ADM0.geojson")):
        iso = os.path.basename(fp)[:3]
        g = json.load(open(fp))
        geoms = []
        for f in g["features"]:
            if f.get("geometry") is None:
                continue
            s = shape(f["geometry"])
            if not s.is_valid:
                s = make_valid(s)
            # keep only polygonal parts
            if s.geom_type == "GeometryCollection":
                s = unary_union([p for p in s.geoms if p.geom_type in ("Polygon", "MultiPolygon")])
            if s.geom_type not in ("Polygon", "MultiPolygon"):
                continue
            if s.area > 0:
                geoms.append(s)
        if geoms:
            polys[iso] = unary_union(geoms)
    names = {iso: v["name"] for iso, v in idx.items()}
    return polys, names

def poly_or_none(s):
    if s is None or s.is_empty:
        return None
    if s.geom_type == "GeometryCollection":
        s = unary_union([p for p in s.geoms if p.geom_type in ("Polygon", "MultiPolygon")])
    return s if s.geom_type in ("Polygon", "MultiPolygon") and not s.is_empty else None

def main():
    polys, names = load()
    print(f"loaded {len(polys)} countries")

    # Patch 3: CHN loses Arunachal overlap and Taiwan
    chn = polys["CHN"]
    ind = polys["IND"]
    pak = polys["PAK"]
    twn = polys["TWN"]

    arunachal = box(91, 25.5, 98, 30)
    ovl = ind.intersection(chn)
    if not ovl.is_empty:
        arun_ovl = ovl.intersection(arunachal)
        if not arun_ovl.is_empty:
            chn = poly_or_none(chn.difference(arun_ovl))
            print(f"patch3: removed Arunachal overlap from CHN ({arun_ovl.area:.3f} deg²)")
    chn = poly_or_none(chn.difference(twn))
    print(f"patch1: removed TWN from CHN ({chn.area:.3f} deg² left)")
    polys["CHN"] = chn

    # Patch 2: IND loses Aksai Chin (kept in patched CHN)
    ind2 = poly_or_none(ind.difference(chn))
    if ind2 is not None:
        lost = ind.area - ind2.area
        print(f"patch2: IND lost {lost:.3f} deg² to CHN (Aksai Chin etc.)")
        polys["IND"] = ind2

    # Patch 4: IND loses Pakistan-administered Kashmir
    ind3 = poly_or_none(polys["IND"].difference(pak))
    if ind3 is not None:
        lost = polys["IND"].area - ind3.area
        print(f"patch4: IND lost {lost:.3f} deg² to PAK (Kashmir W of LoC)")
        polys["IND"] = ind3

    # Western Sahara: gbOpen Morocco (which claims W.Sahara) minus the territory
    # north of the de jure Morocco/W.Sahara boundary (parallel 27.66 N).
    # NE's own ESH/MAR polygons are split along the de facto berm and unusable.
    mar_raw = polys["MAR"]
    ws_box = box(-17.5, 20.5, -8.66, 27.66)
    esh = poly_or_none(mar_raw.intersection(ws_box))
    polys["ESH"] = esh
    names["ESH"] = "Western Sahara"
    print(f"ESH constructed from MAR claim view: {esh.area:.2f} deg² (mar was {mar_raw.area:.2f})")

    rest = sorted(k for k in polys if k not in CLIP_ORDER)
    order = []
    seen = set()
    for iso in CLIP_ORDER:
        if iso in polys and iso not in seen:
            order.append(iso); seen.add(iso)
    for iso in rest:
        if iso not in seen:
            order.append(iso); seen.add(iso)

    # Generic pairwise clip: for each pair that overlaps, earlier-in-order loses.
    from shapely.strtree import STRtree
    geoms = list(polys.values())
    keys = list(polys.keys())
    pos = {iso: i for i, iso in enumerate(order)}
    tree = STRtree(geoms)
    clips = {}
    for i, s in enumerate(geoms):
        for j in tree.query(s):
            if j == i:
                continue
            a, b = keys[i], keys[j]
            # the LATER one in `order` keeps the overlap; earlier loses it
            loser, winner = (a, b) if pos[a] < pos[b] else (b, a)
            clips.setdefault(loser, []).append(winner)
    print(f"pairs to clip: {sum(len(v) for v in clips.values())}")
    for loser, winners in sorted(clips.items()):
        cut = unary_union([polys[w] for w in winners])
        p = poly_or_none(polys[loser].difference(cut))
        if p is not None:
            polys[loser] = p
        else:
            print(f"WARN: {loser} vanished after clipping (winners: {winners})")

    feats = []
    for iso in sorted(polys):
        p = polys[iso]
        if p.geom_type == "Polygon":
            p = [p]
        else:
            p = list(p.geoms)
        big = [g for g in p if g.area > MIN_AREA]
        if not big:
            print(f"DROPPED (all parts < MIN_AREA): {iso}")
            continue
        g = unary_union(big) if len(big) > 1 else big[0]
        feats.append({
            "type": "Feature",
            "properties": {"iso3": iso, "name": names.get(iso, iso)},
            "geometry": mapping(g),
        })
    fc = {"type": "FeatureCollection", "features": feats}
    json.dump(fc, open(OUT, "w"))
    print(f"wrote {OUT}: {len(feats)} features, {os.path.getsize(OUT)/1e6:.1f} MB")

    # sanity: no remaining pairwise overlaps > 0.15 deg² among big polygons
    from shapely.strtree import STRtree
    gs = [shape(f["geometry"]) for f in feats]
    isos = [f["properties"]["iso3"] for f in feats]
    tree = STRtree(gs)
    print("post-check overlaps >0.15 deg²:")
    n = 0
    for i, s in enumerate(gs):
        for j in tree.query(s):
            if j <= i:
                continue
            if isos[i] == isos[j]:
                continue
            try:
                a = s.intersection(gs[j]).area
            except Exception:
                continue
            if a > 0.15:
                print(f"  {isos[i]}/{isos[j]}: {a:.3f}")
                n += 1
    print(f"  ({n} remaining)")

if __name__ == "__main__":
    main()
