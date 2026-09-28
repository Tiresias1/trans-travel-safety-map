#!/usr/bin/env python3
"""Build per-jurisdiction relevance-audit packets from data/source_manifest.json.

Writes data/relevance_packets/<WHO>.json per jurisdiction:
 { who, iso3, name, score, summary_text, sources: [{url, title, published,
   status, cached, claim_summary}] }
Lanes read packets + the cached article text and judge each URL for on-topic-
ness and support. Usage: python3 tools/make_relevance_packets.py [WHO ...]
(default: all jurisdictions in the manifest)."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
PDIR = ROOT / "data/relevance_packets"; PDIR.mkdir(parents=True, exist_ok=True)

def strip(s): return " ".join(re.sub(r"<[^>]+>", " ", str(s or "")).split())

man = json.load(open(ROOT / "data/source_manifest.json"))
c = json.load(open(ROOT / "data/countries.json"))
a = json.load(open(ROOT / "data/admin1.json"))

packets = {}
def put(who, iso3, name, score, summary, srcs):
    p = packets.setdefault(who, {"who": who, "iso3": iso3, "name": name,
                                 "score": score, "summary_text": strip(summary), "sources": []})
    for s in srcs:
        u = s.get("url") if isinstance(s, dict) else s
        e = man.get(u)
        if not e: continue
        p["sources"].append({"url": u, "title": e["title"], "published": e["published"],
                             "status": e["status"], "cached": e["cached"],
                             "claim_summary": (s.get("summary") if isinstance(s, dict) else None)})

for iso, r in c.items():
    put(f"country:{iso}", iso, r["name"], r.get("score"), r.get("summary"), r.get("sources") or [])
for sid, r in a.items():
    if r.get("dossier"):
        put(f"{r['iso3']}/{r['name']}", r["iso3"], r["name"], r.get("score"),
            r.get("summary"), r.get("sources") or [])

want = set(sys.argv[1:]) if len(sys.argv) > 1 else set(packets)
n = 0
for who, p in packets.items():
    if who in want:
        (PDIR / (re.sub(r"[^A-Za-z0-9_.-]", "_", who) + ".json")).write_text(
            json.dumps(p, ensure_ascii=False, indent=1))
        n += 1
print(f"{n} packets written ({len(packets)} total jurisdictions)")
