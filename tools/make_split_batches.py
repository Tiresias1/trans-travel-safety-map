#!/usr/bin/env python3
"""W2 four-field split batcher: records whose visible fields lack the rule-6 split.
Packet: full current visible text (summary + any tangential/localsOnly/outOfScope),
surviving source claims, freshness. Lanes restructure into 4 fields + blind mirrors.
Usage: make_split_batches.py [--per 8] [--count N]"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
per = int(sys.argv[sys.argv.index('--per')+1]) if '--per' in sys.argv else 8
cnt = int(sys.argv[sys.argv.index('--count')+1]) if '--count' in sys.argv else 2000
A = json.load(open(ROOT/'data/admin1.json'))
C = json.load(open(ROOT/'data/countries.json'))
fresh = {}
for f in (ROOT/'data/freshness').glob('*.json'):
    try:
        for x in json.load(open(f)).get('results', []):
            fresh.setdefault(x.get('who'), []).append(x)
    except Exception:
        pass
def pkt(who, rec):
    return {"who": who, "name": rec.get('name'),
            "current_summary": rec.get('summary') or '',
            "current_tangential": rec.get('tangentialFactors') or '',
            "current_localsOnly": rec.get('localsOnly') or '',
            "current_outOfScope": rec.get('outOfScopeNotes') or '',
            "sources": [{"url": (s.get('url') if isinstance(s, dict) else s),
                         "title": (s.get('title') if isinstance(s, dict) else None),
                         "claim": (s.get('summary') if isinstance(s, dict) else None)}
                        for s in (rec.get('sources') or [])],
            "freshness_all": fresh.get(who, [])[:5]}
ents = []
for r in A.values():
    if r.get('dossier') and not r.get('tangentialFactors'):
        ents.append((f"{r['iso3']}/{r['name']}", r))
for k, r in C.items():
    if not r.get('tangentialFactors'):
        ents.append(("country:"+k, r))
B = ROOT/'data/split_batches'; B.mkdir(exist_ok=True)
made = 0
for i in range(0, min(len(ents), per*cnt), per):
    made += 1
    json.dump({"records": [pkt(w, r) for w, r in ents[i:i+per]]},
              open(B/f's{made:03d}.json', 'w'), ensure_ascii=False, indent=1)
print(f"{made} split batches of {per} | entities needing split: {len(ents)}")