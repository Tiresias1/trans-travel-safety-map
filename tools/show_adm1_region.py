#!/usr/bin/env python3
"""Print one admin1 region's current record for a research worker (read-only)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def main():
    if len(sys.argv) < 2:
        print("usage: show_adm1_region.py <region-id>", file=sys.stderr); return 2
    rid = sys.argv[1]
    d = json.loads((ROOT / "data" / "admin1.json").read_text(encoding="utf-8"))
    c = json.loads((ROOT / "data" / "countries.json").read_text(encoding="utf-8"))
    rec = d.get(rid)
    if not rec:
        print(f"error: unknown region id {rid!r}", file=sys.stderr); return 2
    iso = rec.get("iso3")
    par = c.get(iso, {})
    print(f"region id: {rid}")
    print(f"iso3: {iso}")
    print(f"name: {rec.get('name')}")
    print(f"estimated: {rec.get('estimated')}")
    print("\n## CURRENT SUMMARY\n" + str(rec.get("summary", "")).strip())
    srcs = rec.get("sources") or []
    print("\n## SOURCE URLS (order preserved)")
    for s in srcs:
        print("- " + (s if isinstance(s, str) else s.get("url", "?")))
    for k, label in (("outOfScopeNotes", "COUNTRY out-of-scope"),
                     ("tangentialFactors", "COUNTRY tangential"),
                     ("localsOnly", "COUNTRY locals-only")):
        v = par.get(k)
        if v:
            print(f"\n## {label}\n{str(v).strip()}")
    md = ROOT / "research" / "admin1" / f"{iso}.md"
    print("\n(research dossier for this country: " + str(md) + ")")
    return 0

if __name__ == "__main__":
    sys.exit(main())
