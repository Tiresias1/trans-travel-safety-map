#!/usr/bin/env python3
"""W1 merge: drop keep=false (floor=2 -> needsIntake instead), rewrite claims
(exact or prefix URL match), append verified adds (dedup). Accepts both output
schemas: {who, verdicts, adds} and {records:[{who, verdicts, adds}...]}.
Usage: apply_links.py"""
import json, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
C = json.load(open(ROOT/'data/countries.json'))
A = json.load(open(ROOT/'data/admin1.json'))

def resolve(who):
    if who and who.startswith('country:'): return C.get(who[8:])
    if who and '/' in who:
        iso, nm = who.split('/', 1)
        return next((x for x in A.values() if x.get('iso3')==iso and x.get('name')==nm), None)
    return None

def find(url, have):
    if not url: return None
    for h in have:
        if h == url: return h
    for h in have:
        if h.startswith(url) or url.startswith(h): return h
    return None

def merge_one(u, rec, stats):
    srcs = [dict(s) if isinstance(s, dict) else {'url': s} for s in rec['sources']]
    have = [s['url'] for s in srcs]
    by_url = {}
    for v in u.get('verdicts') or []:
        m = find(v.get('url'), have)
        if m is not None: by_url[m] = v
    if not by_url: return False
    kept = []
    for s in srcs:
        v = by_url.get(s['url'])
        if v is None or v.get('keep'):
            if v and v.get('rewritten_summary'): s['summary'] = v['rewritten_summary']
            if v: stats['checked'] += 1
            kept.append(s)
        else: stats['dropped'] += 1
    hset = {s['url'] for s in kept}
    for a in u.get('adds') or []:
        if a.get('verified') and a.get('url') and not find(a['url'], hset):
            kept.append({k: a[k] for k in ('url','title','published','summary') if a.get(k)})
            hset.add(a['url']); stats['added'] += 1
    if len(kept) < 2:
        rec['needsIntake'] = True
        stats['floor'] += 1
    else:
        rec['sources'] = kept
        rec['needsIntake'] = bool(u.get('needs_intake'))
    stats['ap'] += 1
    return True

stats = {'ap':0, 'skip':0, 'checked':0, 'dropped':0, 'added':0, 'floor':0}
for f in sorted((ROOT/'data/link_out').glob('*.json')):
    try: d = json.load(open(f))
    except Exception: continue
    for u in (d.get('records') or [d]):
        rec = resolve(u.get('who'))
        if rec is None or not isinstance(rec.get('sources'), list) or not (u.get('verdicts') or []):
            stats['skip'] += 1; continue
        merge_one(u, rec, stats)
for p, obj in ((ROOT/'data/countries.json', C), (ROOT/'data/admin1.json', A)):
    t = p.with_suffix('.json.tmp'); t.write_text(json.dumps(obj, ensure_ascii=False, indent=1)); os.replace(t, p)
print(f"W1 merged: {stats['ap']} records | verdicts landed {stats['checked']} | dropped {stats['dropped']} | added {stats['added']} | floor->intake {stats['floor']} | skipped {stats['skip']}")
