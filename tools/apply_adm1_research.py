#!/usr/bin/env python3
"""Merge research-revised region records (data/adm1_research/<id>.json) into admin1.json.

Input schema: {id, summary, sources: [{url, summary}], outOfScopeNotes?,
tangentialFactors?, localsOnly?}  (real names allowed - these are dossier fields).

Hard checks: id exists & dossier; summary non-empty; sources same URL set & order
as current record, every source has url+summary strings; scope fields, when
present, are non-empty strings. Validated records replace summary/sources/scope
fields and get researched2=true (blind pass gate). --report shows progress;
--queue prints ids still needing research."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def urls_of(rec):
    return [s if isinstance(s, str) else s.get("url") for s in rec.get("sources", [])]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=str(ROOT / "data" / "adm1_research"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--queue", action="store_true")
    ap.add_argument("--queue-limit", type=int, default=None)
    args = ap.parse_args()

    admin1 = json.loads((ROOT / "data" / "admin1.json").read_text(encoding="utf-8"))
    dossier = {k: v for k, v in admin1.items() if v.get("dossier")}

    if args.report or args.queue:
        done = [k for k, v in dossier.items() if v.get("researched2")]
        todo = [k for k in dossier if k not in set(done)]
        if args.report:
            print(f"dossier regions: {len(dossier)} | researched: {len(done)} | todo: {len(todo)}")
        if args.queue:
            for k in (todo[:args.queue_limit] if args.queue_limit else todo):
                print(k)
        return 0

    inp = Path(args.inp)
    files = sorted(inp.glob("*.json"))
    ok = fail = 0
    for f in files:
        obj = json.loads(f.read_text(encoding="utf-8"))
        rid = obj.get("id") or f.stem
        rec = dossier.get(rid)
        if rec is None:
            print(f"[SKIP] {f.name}: not a dossier region id"); continue
        errs = []
        summ = str(obj.get("summary", "")).strip()
        if not summ: errs.append("empty summary")
        src = obj.get("sources")
        old_urls = urls_of(rec)
        if not isinstance(src, list) or len(src) != len(old_urls):
            errs.append(f"sources len {len(src) if isinstance(src, list) else 'missing'} != {len(old_urls)}")
        else:
            for i, s in enumerate(src):
                if not isinstance(s, dict) or not str(s.get("url", "")).strip() or not str(s.get("summary", "")).strip():
                    errs.append(f"source {i} malformed"); break
                if s.get("url") != old_urls[i]:
                    errs.append(f"source {i} url reordered/changed: {s.get('url')!r} != {old_urls[i]!r}"); break
        for k in ("outOfScopeNotes", "tangentialFactors", "localsOnly"):
            if k in obj and not str(obj[k]).strip():
                errs.append(f"{k} present but empty")
        if errs:
            print(f"\n[FAIL] {rec.get('name')} ({rid})")
            for e in errs: print("   -", e)
            fail += 1
            continue
        rec["summary"] = summ
        rec["sources"] = src
        for k in ("outOfScopeNotes", "tangentialFactors", "localsOnly"):
            if k in obj:
                rec[k] = str(obj[k]).strip()
            else:
                rec.pop(k, None)
        rec["researched2"] = True
        ok += 1
    if not args.dry_run and ok:
        tmp = Path(str(ROOT / "data" / "admin1.json") + ".tmp")
        tmp.write_text(json.dumps(admin1, indent=1, ensure_ascii=False), encoding="utf-8")
        tmp.replace(ROOT / "data" / "admin1.json")
    print(f"\nresearch merged: {ok} · failed: {fail}" + (" · dry run" if args.dry_run else ""))
    return 0 if fail == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
