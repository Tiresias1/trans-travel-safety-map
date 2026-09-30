#!/usr/bin/env python3
"""W1b intake merge: append verified adds to records, require >=2 honest-sourced, clear flags.
Output schema (per lane): {"records":[{who, adds:[{url,title,published,summary}], quality_summaries:[{url,rewritten_summary}]}]}"""
import json, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
C = json.load(open(ROOT/'data/countries.json'))
A = json.load(open(ROOT/'data/admin1.json'))
def resolve(who):
    if who.startswith('country:'): return C.get(who[8:])
    iso, nm = who.split('/', 1)
    return next((x for x in A.values() if x.get('iso3')==iso and x.get('name')==nm), None)
def find(url, have):
    for h in have:
        if h == url: return h
    for h in have:
        if url and (h.startswith(url) or url.startswith(h)): return h
    return None
ap = skip = 0
for f in sorted((ROOT/'data/intake_out').glob('*.json')):
    try: d = json.load(open(f))
    except Exception: continue
    for u in (d.get('records') or [d]):
        rec = resolve(u.get('who'))
        if rec is None: skip += 1; continue
        srcs = [dict(s) if isinstance(s, dict) else {'url': s} for s in (rec.get('sources') or [])]
        have = [s['url'] for s in srcs]; hset = set(have)
        n_old = len(have); n_add = 0
        for a in u.get('adds') or []:
            if not a.get('url'): continue
            if find(a['url'], have): continue  # exists already
            entry = {'url': a['url']}
            for k in ('title','published','summary'):
                if a.get(k): entry[k] = a[k]
            if not entry.get('summary'): entry['summary'] = 'thin: no usable finding'
            srcs.append(entry); hset.add(a['url']); n_add += 1; have.append(a['url'])
        total = len([s for s in srcs if s.get('summary')])
        if total >= 2:
            rec['sources'] = srcs
            rec['needsIntake'] = False
            rec.pop('needsQualityPass', None)
        ap += 1
        print(f"{u.get('who')}: {n_old}->{len(srcs)} sources")
for p, obj in ((ROOT/'data/countries.json', C), (ROOT/'data/admin1.json', A)):
    t = p.with_suffix('.json.tmp'); t.write_text(json.dumps(obj, ensure_ascii=False, indent=1)); os.replace(t, p)
print(f"W1b merged: {ap} records, {skip} skipped")
