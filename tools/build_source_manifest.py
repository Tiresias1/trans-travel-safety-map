#!/usr/bin/env python3
"""Build data/source_manifest.json: every source URL on the map with its
cached title, publication date, and the jurisdictions citing it.
Requires research/fetched/*.meta from tools/fetch_all_sources.py."""
import json, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
FDIR = ROOT / "research" / "fetched"

def key(u): return hashlib.sha256(u.encode()).hexdigest()[:16]

c = json.load(open(ROOT / "data/countries.json"))
a = json.load(open(ROOT / "data/admin1.json"))
man = {}
def add(u, who, src_summary):
    u = u.get("url") if isinstance(u, dict) else u
    if not (isinstance(u, str) and u.startswith("http")): return
    e = man.setdefault(u, {"jurisdictions": [], "region_claims": [], "title": None,
                           "published": None, "status": None, "cached": None})
    e["jurisdictions"].append(who)
    if src_summary: e["region_claims"].append({"by": who, "claim": src_summary})
    k = key(u)
    mp = FDIR / f"{k}.meta"
    if mp.exists():
        try: m = json.loads(mp.read_text())
        except Exception: return
        e.update({"title": m.get("title") or e["title"], "published": m.get("published") or e["published"],
                  "status": m.get("status"), "cached": f"research/fetched/{k}.txt",
                  "published_src": m.get("published_src"), "fetchedAt": m.get("fetchedAt")})
for iso, r in c.items():
    for s in r.get("sources") or []:
        add(s, f"country:{iso}", s.get("summary") if isinstance(s, dict) else None)
for sid, r in a.items():
    if not r.get("dossier"): continue
    for s in r.get("sources") or []:
        add(s, f"{r['iso3']}/{r['name']}", s.get("summary") if isinstance(s, dict) else None)
undated = sum(1 for e in man.values() if not e["published"] and e["status"] == "ok")
stale = sum(1 for e in man.values() if e["published"] and e["published"] < "2024")
json.dump(man, open(ROOT / "data/source_manifest.json", "w"), ensure_ascii=False, indent=1)
print(f"{len(man)} URLs | with date: {sum(1 for e in man.values() if e['published'])} "
      f"| ok-but-undated: {undated} | stale(<2024): {stale} | unreachable: {sum(1 for e in man.values() if e['status'] != 'ok')}")
