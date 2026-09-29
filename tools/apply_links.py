#!/usr/bin/env python3
"""W1 merge: drop keep=false (floor=2 else refuse), rewrite claims (exact or prefix URL
match), append verified adds (dedup), refresh needsIntake. Usage: apply_links.py"""
import json, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
C = json.load(open(ROOT/'data/countries.json')); A = json.load(open(ROOT/'data/admin1.json'))
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
for f in sorted((ROOT/'data/link_out').glob('*.json')):
    try: d = json.load(open(f))
    except Exception: continue
    who = d.get('who'); rec = resolve(who)
    if not rec or not isinstance(rec.get('sources'), list): skip += 1; continue
    srcs = [dict(s) if isinstance(s, dict) else {'url': s} for s in rec['sources']]
    have = [s['url'] for s in srcs]
    keep_urls = {}
    for v in d.get('verdicts') or []:
        m = find(v.get('url'), have)
        if m is None: continue
        keep_urls[m] = v
    if not keep_urls: skip += 1; continue
    kept = []
    for s in srcs:
        v = keep_urls.get(s['url'])
        if v is None or v.get('keep'):
            if v and v.get('rewritten_summary'): s['summary'] = v['rewritten_summary']
            kept.append(s)
    if len(kept) < 2:
        rec['needsIntake'] = True; print(f"[floor] {who}: kept {len(kept)} -> intake queue"); ap += 1; continue
    hset = {s['url'] for s in kept}
    for a in d.get('adds') or []:
        if a.get('verified') and a.get('url') and not find(a['url'], hset):
            kept.append({k: a[k] for k in ('url','title','published','summary') if a.get(k)})
            hset.add(a['url'])
    rec['sources'] = kept
    rec['needsIntake'] = bool(d.get('needs_intake'))
    ap += 1
for p, obj in ((ROOT/'data/countries.json', C), (ROOT/'data/admin1.json', A)):
    t = p.with_suffix('.json.tmp'); t.write_text(json.dumps(obj, ensure_ascii=False, indent=1)); os.replace(t, p)
print(f"W1 merged: {ap} records, {skip} skipped")
