#!/usr/bin/env python3
"""Merge a sources-fix bundle into a record (the process's ADD capability —
previously the pipeline could only prune). Bundle JSON:
  {drop:[urls], rewrite:[{url,summary}], add:[{url,title,published,summary}]}
Applies to country:ISO or ISO/Region records in countries.json/admin1.json.
Exact-URL discipline: drop only if present; rewrite only existing urls;
add skips duplicates (exact or prefix-matched). floor=2 enforced.
Usage: python3 tools/apply_sources_fix.py <bundle.json> --who <who>
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
bundle = json.load(open(sys.argv[1]))
who = sys.argv[sys.argv.index('--who')+1]
C = json.load(open(ROOT/'data/countries.json')); A = json.load(open(ROOT/'data/admin1.json'))
if who.startswith('country:'):
    rec, path = C.get(who[8:]), ROOT/'data/countries.json'
else:
    iso, nm = who.split('/',1)
    rec = next((x for x in A.values() if x.get('iso3')==iso and x.get('name')==nm), None)
    path = ROOT/'data/admin1.json'
assert rec is not None, f"no record for {who}"
def url_of(s): return s['url'] if isinstance(s, dict) else s
srcs = [dict(s) if isinstance(s, dict) else {'url': s} for s in (rec.get('sources') or [])]
kill = set(bundle.get('drop') or [])
before = len(srcs)
srcs = [s for s in srcs if not any(k == s['url'] or s['url'].startswith(k) or k.startswith(s['url']) for k in kill)]
n_drop = before - len(srcs)
for r in bundle.get('rewrite') or []:
    for s in srcs:
        if s['url'] == r['url']: s['summary'] = r['summary']
have = {s['url'] for s in srcs}
n_add = 0
for a in bundle.get('add') or []:
    if not a.get('verified'): print(f"  [intake] skipping unverified add {a.get('url','')[:60]}"); continue
    if any(a['url'] == h or a['url'].startswith(h) or h.startswith(a['url']) for h in have): continue
    srcs.append({k: a[k] for k in ('url','title','published','summary') if a.get(k)}); have.add(a['url']); n_add += 1
if len(srcs) < 2:
    sys.exit(f"REFUSING: would leave {len(srcs)} sources (floor=2)")
rec['sources'] = srcs
rec['needsIntake'] = False
tmp = path.with_suffix('.json.tmp')
tmp.write_text(json.dumps(C if who.startswith('country:') else A, ensure_ascii=False, indent=1))
import os; os.replace(tmp, path)
print(f"{who}: dropped {n_drop}, rewrote {len(bundle.get('rewrite') or [])}, added {n_add} -> {len(srcs)} sources")
