#!/usr/bin/env python3
"""W1b intake batcher: records needing real sources (needsIntake or needsQualityPass).
Usage: make_intake_batches.py [--per 5] [--count N]"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
per = int(sys.argv[sys.argv.index('--per')+1]) if '--per' in sys.argv else 5
cnt = int(sys.argv[sys.argv.index('--count')+1]) if '--count' in sys.argv else 5
C = json.load(open(ROOT/'data/countries.json'))
A = json.load(open(ROOT/'data/admin1.json'))
ents = []
for k, r in C.items():
    if r.get('needsIntake') or r.get('needsQualityPass'):
        ents.append(("country:"+k, r))
for r in A.values():
    if r.get('needsIntake') or r.get('needsQualityPass'):
        ents.append((f"{r['iso3']}/{r['name']}", r))
def pkt(who, rec):
    return {"who": who, "name": rec.get('name'), "iso3": rec.get('iso3'),
            "summary": str(rec.get('summary',''))[:1400],
            "existing_sources": [s['url'] if isinstance(s,dict) else s for s in (rec.get('sources') or [])][:12],
            "needs": "qualityPass" if rec.get('needsQualityPass') else "intake"}
B = ROOT/'data/intake_batches'; B.mkdir(exist_ok=True)
made = 0
for i in range(0, min(len(ents), per*cnt), per):
    made += 1
    json.dump({"records": [pkt(w, r) for w, r in ents[i:i+per]]},
              open(B/f'i{made:03d}.json','w'), ensure_ascii=False, indent=1)
print(f"{made} intake batches of {per} | queue: {len(ents)}")
