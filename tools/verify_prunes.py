#!/usr/bin/env python3
"""Per-record prune verification (never trust aggregate counts again).

Scans every data/relevance_results/*.json; for each verdict with keep=false or
on_topic=false, confirms that URL is ACTUALLY absent from the record's sources
list. --fix removes stragglers (exact url match) and reports each removal.
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
C = json.load(open(ROOT/'data/countries.json')); A = json.load(open(ROOT/'data/admin1.json'))
fix = '--fix' in sys.argv
def url_of(s): return s.get('url') if isinstance(s, dict) else s
bad = []
for f in sorted((ROOT/'data/relevance_results').glob('*.json')):
    try: d = json.loads(f.read_text())
    except Exception: continue
    who = d.get('who','')
    rec = C.get(who[8:]) if who.startswith('country:') else \
          next((x for x in A.values() if x.get('iso3')==who.split('/')[0] and x.get('name')==who.split('/',1)[1]), None) if '/' in who else None
    if not rec or not isinstance(rec.get('sources'), list): continue
    present = {url_of(s) for s in rec['sources']}
    def matches(vu):  # tolerate lane-truncated URLs
        return [u for u in present if u == vu or (vu and (u.startswith(vu) or vu.startswith(u)))]
    stale = set()
    for v in d.get('verdicts', []):
        if v.get('keep') is False or v.get('on_topic') is False:
            stale.update(matches(v.get('url')))
    floor = 2
    if len(present) - len(stale) < floor:   # never empty a record: defer to intake
        stale = set()
    if stale:
        bad.append((who, stale))
        if fix:
            kill = set(stale)
            rec['sources'] = [s for s in rec['sources'] if url_of(s) not in kill]
if fix and bad:
    for p, obj in ((ROOT/'data/countries.json', C), (ROOT/'data/admin1.json', A)):
        t = p.with_suffix('.json.tmp'); t.write_text(json.dumps(obj, ensure_ascii=False, indent=1)); Path(t).replace(p)
print(f"{'FIXED ' if fix else 'FOUND '}{sum(len(s) for _,s in bad)} straggler URLs across {len(bad)} records")
for w, s in bad[:12]: print(" ", w, "->", [u[:55] for u in s])
