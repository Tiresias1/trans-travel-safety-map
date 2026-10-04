#!/usr/bin/env python3
"""Emit rework bundles for records that gained verified prison-housing adds.
Each bundle: [who] -> {prison_adds:[...]} for the summary-extension lanes.
Usage: make_prison_rework.py --out data/prison_rework/vis01.json
"""
import json, glob, sys, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
bundles = {}
for f in glob.glob(str(ROOT/'data/prison_bundles/*.json')):
    d = json.load(open(f))
    bundles.setdefault(d['who'], []).extend(d['add'])
C = json.load(open(ROOT/'data/countries.json'))
A = json.load(open(ROOT/'data/admin1.json'))
recs = {**{f'country:{k}': (r, C, k) for k, r in C.items()},
        **{f"{r['iso3']}/{r['name']}": (r, A, None) for r in A.values() if r.get('dossier')}}
out = []
for who, adds in sorted(bundles.items()):
    r, src, _ = recs.get(who, (None, None, None))
    if not r: continue
    srcs = [s.get('url') if isinstance(s, dict) else s for s in (r.get('sources') or [])]
    present = [a for a in adds if a.get('url') in srcs]
    if present:
        out.append({"who": who, "current_summary": str(r.get('summary','')),
                     "prison_adds": present})
json.dump({"records": out}, open(ROOT/'data/prison_rework_vis.json','w'), ensure_ascii=False, indent=1)
print(f"{len(out)} records flagged for summary+blind rework (have prison adds in sources)")
