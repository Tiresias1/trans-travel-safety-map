#!/usr/bin/env python3
"""Build freshness-search batches from data/staleness_queue.json (T1 first).

Groups tier-1 stale-risk claims by jurisdiction, packs <=8 jurisdictions per
batch, prints lane JS for a workflow launch and writes data/fresh_batches/.
Lanes web-search current status per claim and write data/freshness/<batch>.json.
Usage: python3 tools/make_freshness_batches.py [--max-batches N]
"""
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
q = json.load(open(ROOT / "data/staleness_queue.json"))
B = ROOT / "data/fresh_batches"; B.mkdir(parents=True, exist_ok=True)
t1 = [x for x in q if x["tier"] == "T1"]
bywho = {}
for x in t1:
    for w in x["who"].split(","):
        bywho.setdefault(w, []).append(x)
# oldest-first jurisdictions, cap entries per jurisdiction at 6
ordered = sorted(bywho, key=lambda w: min((e.get("published") or "0000") for e in bywho[w]))
batches, cur, cur_n = [], [], 0
for w in ordered:
    ent = sorted(bywho[w], key=lambda e: e.get("published") or "0000")[:6]
    batch_items = {"who": w, "entries": ent}
    if cur and (cur_n >= 8 or cur_n + len(ent) > 40):
        batches.append(cur); cur, cur_n = [], 0
    cur.append(batch_items); cur_n += len(ent)
if cur:
    batches.append(cur)
mb = int(sys.argv[sys.argv.index("--max-batches") + 1]) if "--max-batches" in sys.argv else len(batches)
made = 0
js = []
for i, b in enumerate(batches[:mb], 1):
    fn = B / f"fb{i:02d}.json"
    json.dump(b, open(fn, "w"), ensure_ascii=False, indent=1)
    js.append(f'  {{key:"fb{i:02d}",agent:"worker",task: RULES + "data/fresh_batches/fb{i:02d}.json"}}')
    made += 1
print(",\n".join(js))
print(f"\n// {made} batches written of {len(batches)} total; T1 entries covered: {sum(len(x['entries']) for bch in batches for x in bch)}", file=sys.stderr)

# lane RULES header (paste into the workflow launch):
RULES_DOC = '''
You are a freshness-search lane (trans-travel-safety-map, /home/meme/kóði/kort).
Read the batch file given. It lists jurisdictions ("who" = country:ISO or
ISO/Region) each with stale-risk entries {url,title,published,claim}. For EACH
jurisdiction: web_search "<name> transgender <key law/policy from claims> current
status 2026" (use data/countries.json name for country:ISO; admin1 name for
region) — ONE to THREE searches per jurisdiction max. For EACH entry decide:
confirmed-current (claim still true; may cite an equal-or-newer source),
superseded (status changed — record the NEW fact + best source {url,title,date}),
unknown (no usable result — say what you searched). Do not edit any repo file
except your output. Write data/freshness/<batch-basename>.json:
{results:[{who,url,status,fact_note(<=180 chars),newer:[{url,title,date}]}]}.
Return one line per jurisdiction: "<who>: <n>confirmed/<n>superseded/<n>unknown — <headline>".
'''
