#!/usr/bin/env python3
"""Filter-safe freshness batches: lanes get ONLY jurisdiction names, source
urls/titles/dates and a topic CATEGORY — never raw claim text (provider content
filters reject graphic source passages). Full detail stays in
data/staleness_queue.json, keyed by (who,url), for my side only.
Usage: python3 tools/make_fresh_batches_safe.py [--per-batch 8] [--out N]"""
import json, sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
q = [x for x in json.load(open(ROOT/'data/staleness_queue.json')) if x['tier']=='T1']
C = json.load(open(ROOT/'data/countries.json')); A = json.load(open(ROOT/'data/admin1.json'))
names = {f"country:{k}": v['name'] for k, v in C.items()}
for r in A.values():
    if r.get('dossier'): names[f"{r['iso3']}/{r['name']}"] = r['name']
CATS = [
    (r'criminalis|sodomy|decriminali|penal|prison', 'criminalisation-status'),
    (r'marriage|partnership', 'marriage-recognition'),
    (r'hate[- ]crime|aggravat', 'hate-crime-protection'),
    (r'bathroom|toilet|facility|single-sex|changing room', 'facility-access'),
    (r'healthcare|care[- ]ban|hormon|surgery|gender[- ]affirm', 'healthcare-access'),
    (r'act|law|bill|ordinance|policy|decree|directive|order|ruling|court|verdict|struck|voided|banned|ban\b', 'legal-status'),
]
def cat(text):
    for rx, c in CATS:
        if re.search(rx, text or '', re.I): return c
    return 'general-lgbt-rights-status'
bywho = {}
for x in q:
    for w in x['who'].split(','):
        bywho.setdefault(w, []).append(x)
order = sorted(bywho, key=lambda w: min((e.get('published') or '0000') for e in bywho[w]))
pb = int(sys.argv[sys.argv.index('--per-batch')+1]) if '--per-batch' in sys.argv else 8
outn = int(sys.argv[sys.argv.index('--out')+1]) if '--out' in sys.argv else 8
B = ROOT/'data/fresh_batches'; B.mkdir(exist_ok=True)
batches, cur = [], []
for w in order:
    ent = sorted(bywho[w], key=lambda e: e.get('published') or '0000')[:6]
    cur.append({"who": w, "name": names.get(w, w), "topic": cat(" ".join(e.get('claim','') for e in ent)),
                "entries": [{"url": e['url'], "title": (e.get('title') or '')[:80], "published": e.get('published')} for e in ent]})
    if len(cur) >= pb: batches.append(cur); cur = []
if cur: batches.append(cur)
made = 0
for i, b in enumerate(batches[:outn], 1):
    (B/f'sf{i:02d}.json').write_text(json.dumps(b, ensure_ascii=False, indent=1)); made += 1
print(f"{made} safe batches written ({sum(len(b) for b in batches[:outn])} jurisdictions); total {len(batches)}")
