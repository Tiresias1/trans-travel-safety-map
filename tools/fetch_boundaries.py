#!/usr/bin/env python3
"""Fetch geoBoundaries gbOpen simplified GeoJSON for all countries.

Usage: fetch_boundaries.py ADM0|ADM1 [outdir]
Downloads each country's *_simplified.geojson from the wmgeolab GitHub release,
writes raw files to raw/<ISO>_<ADM>.geojson and an index.json of metadata.
"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

API = "https://www.geoboundaries.org/api/current/gbOpen/ALL/{adm}/"

def fetch(adm, outdir):
    os.makedirs(outdir, exist_ok=True)
    meta = json.loads(subprocess.run(
        ["curl", "-s", "--max-time", "120", API.format(adm=adm)],
        capture_output=True, text=True, check=True).stdout)
    index = {}
    for m in meta:
        iso, name = m["boundaryISO"], m["boundaryName"]
        url = m["simplifiedGeometryGeoJSON"]
        dest = os.path.join(outdir, f"{iso}_{adm}.geojson")
        index[iso] = {"name": name, "url": url, "file": dest,
                      "boundaryID": m["boundaryID"],
                      "license": m["boundaryLicense"]}
        if not os.path.exists(dest) or os.path.getsize(dest) < 100:
            subprocess.run(["curl", "-sL", "--max-time", "300", url, "-o", dest], check=True)
    with open(os.path.join(outdir, "index.json"), "w") as f:
        json.dump(index, f, indent=1)
    print(f"{adm}: {len(index)} entries")

if __name__ == "__main__":
    adm = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else f"raw_{adm.lower()}"
    fetch(adm, outdir)
