#!/usr/bin/env python3
"""Resume ADM1 downloads with retries; skip files that exist and parse as JSON."""
import json, os, subprocess, glob, sys

outdir = "raw_adm1"
# get index from the API again
meta = json.loads(subprocess.run(
    ["curl", "-s", "--max-time", "180",
     "https://www.geoboundaries.org/api/current/gbOpen/ALL/ADM1/"],
    capture_output=True, text=True, check=True).stdout)
print("API entries:", len(meta))
fails = []
for m in meta:
    iso = m["boundaryISO"]
    dest = os.path.join(outdir, f"{iso}_ADM1.geojson")
    ok = False
    if os.path.exists(dest) and os.path.getsize(dest) > 100:
        try:
            json.load(open(dest)); ok = True
        except Exception:
            pass
    if ok: continue
    for attempt in range(4):
        r = subprocess.run(["curl", "-sL", "--max-time", "300",
                            m["simplifiedGeometryGeoJSON"], "-o", dest])
        if r.returncode == 0 and os.path.exists(dest):
            try:
                json.load(open(dest)); ok = True; break
            except Exception:
                pass
    if not ok:
        fails.append(iso); print("FAIL", iso, flush=True)
print("done. failures:", fails)
json.dump({m["boundaryISO"]: {"name": m["boundaryName"],
                              "boundaryID": m["boundaryID"]}
           for m in meta}, open(os.path.join(outdir, "index.json"), "w"), indent=1)
