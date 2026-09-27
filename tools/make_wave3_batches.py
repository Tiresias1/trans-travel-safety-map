#!/usr/bin/env python3
"""Regenerate data/wave3_batches/plan.json from packets minus region results.
Usage: python3 tools/make_wave3_batches.py [--lane-size 12] [--next N]"""
import json, os, sys, math
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
P, B, R = ROOT/'data/relevance_packets', ROOT/'data/wave3_batches', ROOT/'data/relevance_results'
size = float(sys.argv[sys.argv.index('--lane-size')+1]) if '--lane-size' in sys.argv else 12
done = {f for f in os.listdir(R) if not f.startswith('country_')}
byiso = {}
for f in os.listdir(P):
    if f.startswith('country_'): continue
    byiso.setdefault(json.load(open(P/f))['who'].split('/')[0], []).append(f)
batches, seq = [], 0
for iso in sorted(byiso, key=lambda k: -len(byiso[k])):
    donestems = {d[:-5] for d in done}
    files = [f for f in sorted(byiso[iso]) if f[:-5] not in donestems]
    n = max(1, math.ceil(len(files)/size))
    sz = math.ceil(len(files)/n) if files else 0
    for i in range(0, len(files), sz or 1):
        seq += 1
        batches.append({"id": f"b{seq:02d}", "packets": files[i:i+sz]})
B.mkdir(exist_ok=True)
json.dump(batches, open(B/'plan.json','w'), indent=1)
k = sys.argv.index('--next') + 1 if '--next' in sys.argv else None
nnext = int(sys.argv[k]) if k else None
out = batches[:nnext] if nnext is not None else batches
js = ",\n".join('  {key:"w3-%s",agent:"worker",task: RULES + "%s"}' % (b["id"], ", ".join(b["packets"])) for b in out)
print(js)
print(f"\n// plan: {len(batches)} pending batches, {sum(len(b['packets']) for b in batches)} pending packets", file=sys.stderr)
