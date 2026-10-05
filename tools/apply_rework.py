#!/usr/bin/env python3
"""Apply rework outputs to data/countries.json / data/admin1.json.

Lanes write data/rework_out/rNNN.json {rewrites:[{who,summary,blindSummary,
blindSourceSummaries,notes}]}. This tool validates (1-12 <p> paragraphs,
<=8000 chars, blind mirror non-empty, scores untouched) and applies by `who`
(country:ISO -> countries; ISO/Region -> admin1 record with that iso3+name).
Idempotent. Usage: python3 tools/apply_rework.py [--dry]
"""
import json, os, re, sys
from pathlib import Path
from datetime import date
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/rework_out"

def valid_summary(s):
    # 2026-10-05: caps raised from 2800/4 — dossiers must carry ALL sourced
    # claims (UI scrolls, no display cap). Match tools/build_data.py.
    if not s or len(s) > 8000: return False
    n = len(re.findall(r"<p[\s>]", s)); return 1 <= n <= 12

def main():
    dry = "--dry" in sys.argv
    C = json.load(open(ROOT / "data/countries.json"))
    A = json.load(open(ROOT / "data/admin1.json"))
    applied = skip = 0
    applied_set = set()
    log = []
    import argparse
    _ap = argparse.ArgumentParser()
    _ap.add_argument('--dir', default=None)
    _args = _ap.parse_known_args()[0]
    OUT = Path(_args.dir) if _args.dir else OUT
    # newest-mtime first so a per-record targeted rework (later) always wins
    for f in sorted(OUT.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
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
            if r.get("blindOnly"):
                if (who, "blind") in applied_set:
                    continue
                if not dry:
                    for bf in ("blindSummary","blindTangential","blindLocalsOnly",
                               "blindOutOfScope","blindSourceSummaries"):
                        if r.get(bf) is not None: tgt[bf] = r[bf]
                    tgt["researchedAt"] = __import__("datetime").date.today().isoformat()
                applied_set.add((who, "blind")); applied += 1
                log.append(f"{who}: blind mirrors re-derived ({r.get('notes','')[:40]})")
                continue
            if not valid_summary(r.get("summary", "")):
                print(f"[skip] {who}: bad summary ({len(r.get('summary',''))} chars)"); skip += 1; continue
            if not str(r.get("blindSummary", "")).strip():
                print(f"[skip] {who}: missing blindSummary"); skip += 1; continue
            bss = r.get("blindSourceSummaries")
            if not isinstance(bss, list) or not bss:
                print(f"[skip] {who}: blindSourceSummaries empty"); skip += 1; continue
            owns_b = (who, "blind") in applied_set
            owns_v = (who, "vis") in applied_set
            if owns_b and owns_v:
                continue  # later-applied file already owns both classes
            if not dry:
                applied_set.add((who, "vis")); applied_set.add((who, "blind"))
                for vf, bf in (("tangentialFactors","blindTangential"),
                               ("localsOnly","blindLocalsOnly"),
                               ("outOfScopeNotes","blindOutOfScope")):
                    if not owns_v and r.get(vf) is not None: tgt[vf] = r[vf]
                    if not owns_b and r.get(bf) is not None: tgt[bf] = r[bf]
                if not owns_v: tgt["summary"] = r["summary"]
                if not owns_b:
                    tgt["blindSummary"] = r["blindSummary"]
                    tgt["blindSourceSummaries"] = [str(x) for x in bss][:12]
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
