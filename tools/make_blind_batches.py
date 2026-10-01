#!/usr/bin/env python3
"""W3 blind-regen batcher: records whose blind mirrors fail rule 7/7e.
Packet: visible 4 fields + source claims. Lanes output blind mirrors ONLY
(via apply_rework blindOnly path), self-gated by check_blind --file.
Usage: make_blind_batches.py [--per 8] [--count N]"""
import json, sys, importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('cb', ROOT/'tools/check_blind.py')
cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
per = int(sys.argv[sys.argv.index('--per')+1]) if '--per' in sys.argv else 8
cnt = int(sys.argv[sys.argv.index('--count')+1]) if '--count' in sys.argv else 2000
C = json.load(open(ROOT/'data/countries.json'))
A = json.load(open(ROOT/'data/admin1.json'))
def pkt(who, rec):
    return {"who": who, "name": rec.get('name'),
            "visible": {k: rec.get(k) for k in ('summary','tangentialFactors','localsOnly','outOfScopeNotes')},
            "sources": [{"url": (s.get('url') if isinstance(s, dict) else s),
                         "claim": (s.get('summary') if isinstance(s, dict) else None)}
                        for s in (rec.get('sources') or [])]}
ents = []
for k, r in C.items():
    if not cb.check(r, k): ents.append(("country:"+k, r))
for r in A.values():
    if r.get('dossier') and not cb.check(r, f"{r['iso3']}/{r['name']}"):
        ents.append((f"{r['iso3']}/{r['name']}", r))
B = ROOT/'data/blind_batches'; B.mkdir(exist_ok=True)
made = 0
for i in range(0, min(len(ents), per*cnt), per):
    made += 1
    json.dump({"records": [pkt(w, r) for w, r in ents[i:i+per]]},
              open(B/f'v{made:03d}.json','w'), ensure_ascii=False, indent=1)
print(f"{made} blind-regen batches of {per} | records failing gate: {len(ents)}")
