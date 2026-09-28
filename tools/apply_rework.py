#!/usr/bin/env python3
"""Apply rework outputs to data/countries.json / data/admin1.json.

Lanes write data/rework_out/rNNN.json {rewrites:[{who,summary,blindSummary,
blindSourceSummaries,notes}]}. This tool validates (1-4 <p> paragraphs,
<=2800 chars, blind mirror non-empty, scores untouched) and applies by `who`
(country:ISO -> countries; ISO/Region -> admin1 record with that iso3+name).
Idempotent. Usage: python3 tools/apply_rework.py [--dry]
"""
import json, os, re, sys
from pathlib import Path
from datetime import date
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/rework_out"

def valid_summary(s):
    if not s or len(s) > 2800: return False
    n = len(re.findall(r"<p[\s>]", s)); return 1 <= n <= 4

def main():
    dry = "--dry" in sys.argv
    C = json.load(open(ROOT / "data/countries.json"))
    A = json.load(open(ROOT / "data/admin1.json"))
    applied = skip = 0
    log = []
    for f in sorted(OUT.glob("*.json")):
        try:
            data = json.load(open(f))
        except Exception as e:
            print(f"[skip] {f.name}: unreadable {e}"); continue
        for r in data.get("rewrites", []):
            who = r.get("who", "")
            tgt = None
            if who.startswith("country:"):
                tgt = C.get(who[8:])
            elif "/" in who:
                iso, nm = who.split("/", 1)
                tgt = next((x for x in A.values()
                            if x.get("iso3") == iso and x.get("name") == nm), None)
            if tgt is None:
                print(f"[skip] {who}: no target record"); skip += 1; continue
            if not valid_summary(r.get("summary", "")):
                print(f"[skip] {who}: bad summary ({len(r.get('summary',''))} chars)"); skip += 1; continue
            if not str(r.get("blindSummary", "")).strip():
                print(f"[skip] {who}: missing blindSummary"); skip += 1; continue
            bss = r.get("blindSourceSummaries")
            if not isinstance(bss, list) or not bss:
                print(f"[skip] {who}: blindSourceSummaries empty"); skip += 1; continue
            if not dry:
                tgt["summary"] = r["summary"]
                tgt["blindSummary"] = r["blindSummary"]
                tgt["blindSourceSummaries"] = [str(x) for x in bss][:12]
                for k in ("blindTangential", "blindLocalsOnly", "blindOutOfScope"):
                    if r.get(k): tgt[k] = r[k]
                tgt["researchedAt"] = date.today().isoformat()
                tgt.pop("reworkPending", None)
            applied += 1
            log.append(f"{who}: {r.get('notes','')[:60]}")
    if not dry and applied:
        for path, obj in ((ROOT / "data/countries.json", C), (ROOT / "data/admin1.json", A)):
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1))
            os.replace(tmp, path)
    print(f"applied {applied} rewrites, skipped {skip} ({'dry' if dry else 'written'})")
    for l in log[:40]: print(" ", l)
    return 0

if __name__ == "__main__":
    sys.exit(main())
