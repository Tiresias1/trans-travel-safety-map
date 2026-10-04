#!/usr/bin/env python3
"""Prison-housing research batcher: records lacking trans-prisoner-placement data.
Usage: make_prison_batches.py [--per 6] [--count N]"""
import json, sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
per = int(sys.argv[sys.argv.index('--per')+1]) if '--per' in sys.argv else 6
cnt = int(sys.argv[sys.argv.index('--count')+1]) if '--count' in sys.argv else 500
C = json.load(open(ROOT/'data/countries.json'))
A = json.load(open(ROOT/'data/admin1.json'))
def already(rec):
    blob = json.dumps({k: rec.get(k) for k in ('summary','tangentialFactors','localsOnly','outOfScopeNotes')})
    return bool(re.search(r'(trans|gender)(.{0,80})?(prison|jail|custod|incarcerat)|(prison|jail|custod|incarcerat)(.{0,80})?(trans|gender)', blob, re.I)) \
        or any(re.search(r'trans|gender', str((s.get('summary') if isinstance(s,dict) else s) or ''), re.I) and
               re.search(r'prison|jail|custod|incarcerat|facility|placement', str((s.get('summary') if isinstance(s,dict) else s) or ''), re.I)
               for s in (rec.get('sources') or []))
def pkt(who, rec):
    return {"who": who, "name": rec.get('name'),
            "summary": str(rec.get('summary',''))[:1100],
            "sources": [{"url": s.get('url') if isinstance(s,dict) else s,
                         "summary": s.get('summary') if isinstance(s,dict) else None}
                        for s in (rec.get('sources') or [])][:8]}
ents = []
for k, r in C.items():
    if not already(r) and (r.get('summary') or r.get('sources')):
        ents.append(("country:"+k, r))
for r in A.values():
    if r.get('dossier') and not already(r):
        ents.append((f"{r['iso3']}/{r['name']}", r))
B = ROOT/'data/prison_batches'; B.mkdir(exist_ok=True)
made = 0
for i in range(0, min(len(ents), per*cnt), per):
    made += 1
    json.dump({"records": [pkt(w, r) for w, r in ents[i:i+per]]},
              open(B/f'p{made:03d}.json','w'), ensure_ascii=False, indent=1)
print(f"{made} prison-research batches of {per} | entities needing prison-housing data: {len(ents)}")
