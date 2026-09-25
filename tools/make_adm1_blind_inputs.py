#!/usr/bin/env python3
"""Extract payload for ADM1-region blind pass v2 (mirrors countries schema).

Payload keys: id, iso3, name, summary, sourceSummaries, and (when present on
the record) outOfScopeNotes / tangentialFactors / localsOnly. Selection:
dossier regions that are researched2 and not yet blindV2.

Usage:
    python3 tools/make_adm1_blind_inputs.py --only <ID> --out /tmp/x.jsonl
    python3 tools/make_adm1_blind_inputs.py                 # all to-be-blinded
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def payload_of(rid, rec):
    p = {"id": rid, "iso3": rec.get("iso3"), "name": rec.get("name"),
         "summary": (rec.get("summary") or "").strip()}
    sums = []
    for s in rec.get("sources") or []:
        if isinstance(s, dict):
            sums.append(str(s.get("summary", "")).strip())
    p["sourceSummaries"] = sums
    for k in ("outOfScopeNotes", "tangentialFactors", "localsOnly"):
        v = str(rec.get(k, "")).strip()
        if v:
            p[k] = v
    return p

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--admin1-file", default=str(ROOT / "data" / "admin1.json"))
    ap.add_argument("--only", default=None)
    ap.add_argument("--out", default=str(ROOT / "data" / "blind_inputs" / "adm1_blind_payloads.jsonl"))
    args = ap.parse_args()
    admin1 = json.loads(Path(args.admin1_file).read_text(encoding="utf-8"))
    if args.only:
        rec = admin1.get(args.only)
        if not rec:
            print(f"error: unknown id {args.only!r}", file=sys.stderr); return 2
        need = [(args.only, rec)]
    else:
        need = [(k, v) for k, v in admin1.items()
                if v.get("dossier") and v.get("researched2") and not v.get("blindV2")]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for rid, rec in need:
            fh.write(json.dumps({"id": rid, "payload": payload_of(rid, rec)},
                                ensure_ascii=False) + "\n")
    print(f"wrote {len(need)} payloads -> {out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
