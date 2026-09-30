#!/usr/bin/env python3
"""W1 batcher: relevance+claim-upgrade packets, countries or admin1.
Claim summaries are deliberately EXCLUDED from packets (content-filter bait);
merges fall back to the record's own claim when a lane returns null.
Usage: make_link_batches.py [--per 8] [--count N] [--admin1]"""
import json, sys, hashlib, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
per = int(sys.argv[sys.argv.index('--per')+1]) if '--per' in sys.argv else 8
cnt = int(sys.argv[sys.argv.index('--count')+1]) if '--count' in sys.argv else 8
adm = '--admin1' in sys.argv
fresh = {}
for f in (ROOT/'data/freshness').glob('*.json'):
    try:
        for x in json.load(open(f)).get('results', []):
            fresh.setdefault(x.get('who'), []).append(x)
    except Exception:
        pass
def pkt(who, rec):
    srcs = []
    for s in rec.get('sources') or []:
        u = s['url'] if isinstance(s, dict) else s
        k = hashlib.sha256(u.encode()).hexdigest()[:16]
        cp = f'research/fetched/{k}.txt'
        entry = {"url": u}
        if isinstance(s, dict):
            if s.get('title'): entry["title"] = s['title']
            if s.get('published'): entry["published"] = s['published']
        entry["cached"] = cp if os.path.exists(ROOT/cp) else None
        srcs.append(entry)
    return {"who": who, "name": rec.get('name'),
            "summary": str(rec.get('summary',''))[:1600],
            "sources": srcs, "freshness": fresh.get(who, [])[:5]}
C = json.load(open(ROOT/'data/countries.json'))
A = json.load(open(ROOT/'data/admin1.json'))
if adm:
    ents = [(f"{r['iso3']}/{r['name']}", r) for r in A.values() if r.get('dossier')]
else:
    ents = [(f"country:{k}", v) for k, v in sorted(C.items())]
B = ROOT/'data/link_batches'; B.mkdir(exist_ok=True)
made = 0
for i in range(0, min(len(ents), per*cnt), per):
    made += 1
    json.dump({"records": [pkt(w, r) for w, r in ents[i:i+per]]},
              open(B/f'b{made:03d}.json','w'), ensure_ascii=False, indent=1)
print(f"{made} batches of {per} | total entities {len(ents)} | fresh-facts matched {sum(1 for w,_ in ents if w in fresh)}")
