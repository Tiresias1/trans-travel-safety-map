#!/usr/bin/env python3
"""Extract identity-free payloads for ADM1-region anonymisation.

Emits one JSONL line per estimated:false region (the units with real
research; everything else was general-knowledge only and needs no blinding):

    {"id": <admin1 id>, "n": <index>, "payload": {
        "id": ..., "iso3": ..., "name": ..., "summary": ..., "sourceSummaries": [...]}}

score / band / worldRank / countryRank / unitsInCountry / researchedAt /
modelContext / blindSummary / estimated are never included in the payload.

Usage:
    python3 tools/make_adm1_blind_inputs.py                 # all estimated:false
    python3 tools/make_adm1_blind_inputs.py --only <ID>     # one region
    python3 tools/make_adm1_blind_inputs.py --limit 8 --out /tmp/x.jsonl
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def payload_of(rid: str, rec: dict) -> dict:
    payload = {"id": rid, "iso3": rec.get("iso3"), "name": rec.get("name"),
               "summary": (rec.get("summary") or "").strip()}
    # sources in admin1 are bare URL strings (no per-source summaries); URLs are
    # identifying and must never reach the anonymising model or the rater.
    srcs = rec.get("sources") or []
    sums = [s.get("summary", "").strip() for s in srcs if isinstance(s, dict)]
    sums = [s for s in sums if s]
    if sums:
        payload["sourceSummaries"] = sums
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--admin1-file", default=str(ROOT / "data" / "admin1.json"))
    ap.add_argument("--only", default=None, help="restrict to one region id")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=str(ROOT / "data" / "blind_inputs" / "adm1_payloads.jsonl"))
    args = ap.parse_args()

    admin1 = json.loads(Path(args.admin1_file).read_text(encoding="utf-8"))
    need = [(rid, rec) for rid, rec in admin1.items() if rec.get("estimated") is False]
    if args.only:
        need = [(r, admin1[r]) for r in [args.only] if r in admin1]
        if not need:
            print(f"error: unknown region id {args.only!r}", file=sys.stderr)
            return 2
    if args.limit:
        need = need[:args.limit]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for n, (rid, rec) in enumerate(need, 1):
            fh.write(json.dumps({"id": rid, "n": n, "payload": payload_of(rid, rec)},
                                ensure_ascii=False) + "\n")
    print(f"wrote {len(need)} region payloads -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
