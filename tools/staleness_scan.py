#!/usr/bin/env python3
"""Build data/staleness_queue.json from data/source_manifest.json: which
time-sensitive claims rest on old or undated sources?

Entry = (jurisdiction, url) where the source is undated or older than CUTOFF
and its claim (or citing claim) is legal/institutional — the class of fact that
goes stale. Tier 1 = criminalisation/ban/ruling claims (freshness search wave
starts here); tier 2 = other legal/institutional.

Usage: python3 tools/staleness_scan.py
"""
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
man = json.load(open(ROOT / "data/source_manifest.json"))
CUTOFF = "2024-09-27"        # >12 months before the 2026-09 edition
LEGAL_RE = re.compile(r"\b(act|law|bill|ban|criminalis|criminaliz|decriminalis|decriminaliz|"
                      r"marriage|court|ruling|judgment|verdict|policy|policing|arrest|"
                      r"protection|ordinance|order|passed|voided|struck|revoked|"
                      r"constitution|supreme|penal|code|guidance|directive|minister|"
                      r"president|governor|suspended|injunction|shelved|withdraw)\w*\b", re.I)
CRIM_RE = re.compile(r"criminalis|criminaliz|decriminalis|decriminaliz|ban\b|banned|sodomy|"
                     r"marriage|court|ruling|struck|voided|revoked|constitution|supreme|penal", re.I)

q = []
for url, e in man.items():
    claims = [c.get("claim", "") for c in e.get("region_claims", [])]
    text = " ".join(claims) or (e.get("title") or "")
    if not text or not LEGAL_RE.search(text):
        continue
    pub = e.get("published")
    if pub and pub >= CUTOFF:
        continue
    who = ",".join(sorted(set(e.get("jurisdictions") or []))[:4])
    q.append({"who": who, "url": url, "title": (e.get("title") or "")[:90],
              "published": pub, "tier": "T1" if CRIM_RE.search(text) else "T2",
              "claim": text[:160],
              "why": "undated" if not pub else f"dated {pub}"})
q.sort(key=lambda x: (x["tier"], x["published"] or "0000", x["who"]))
json.dump(q, open(ROOT / "data/staleness_queue.json", "w"), ensure_ascii=False, indent=1)
from collections import Counter
t1 = [x for x in q if x["tier"] == "T1"]
print(f"staleness queue: {len(q)} (T1 legal-status claims: {len(t1)}, T2 other legal: {len(q)-len(t1)})")
print(f"  undated: {sum(1 for x in q if not x['published'])}, pre-{CUTOFF[:4]}: {sum(1 for x in q if x['published'])}")
juris = Counter()
for x in t1:
    for w in x["who"].split(","):
        juris[w] += 1
print("  top T1 holders:", juris.most_common(10))
