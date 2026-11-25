#!/usr/bin/env python3
"""Dry-runnable sync of tranche-1 verified changes into data/admin1.json.
Default: dry-run (prints diff plan, writes nothing). --apply performs the write
after a fresh baseline-hash check; coordinator runs --apply after review.
Never touches data/countries.json. Scores are never modified here.
Usage: python3 research/us-states-wave/sync.py [--apply] [--plan research/us-states-wave/sync-plan2.json]
"""
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--plan", default=str(ROOT / "research" / "us-states-wave" / "sync-plan2.json"))
    args = ap.parse_args()

    plan = json.loads(Path(args.plan).read_text())
    admin_path = ROOT / "data" / "admin1.json"
    admin = json.loads(admin_path.read_text())

    for r in plan["regions"]:
        sid = r["shapeID"]
        rec = admin.get(sid)
        if rec is None:
            print(f"{r['region']}: MISSING shapeID {sid}")
            sys.exit(1)
        existing = {(s.get("url") if isinstance(s, dict) else s) for s in rec.get("sources", [])}
        print(f"--- {r['region']} ({sid}) baselineHash={r['baselineContentHash']}")
        for a in r["addSources"]:
            tag = "ADD (already present, skip)" if a["url"] in existing else "ADD"
            print(f"    source [{tag}]: {a['url']}")
        print(f"    summaryFactsToAppend: {len(r['appendSummaryFacts'])}")
        for f in r["appendSummaryFacts"]:
            print(f"      + {f[:150]}...")
        print(f"    cascade: {r['cascade'][:110]}...")

    if not args.apply:
        print("\nDRY-RUN: no files written. Re-run with --apply (coordinator, after review) to write.")
        return

    import hashlib
    for r in plan["regions"]:
        rec = admin[r["shapeID"]]
        payload = json.dumps({"sources": rec.get("sources"), "summary": rec.get("summary"),
                              "blindSummary": rec.get("blindSummary")}, sort_keys=True)
        h = hashlib.sha256(payload.encode()).hexdigest()[:16]
        if h != r["baselineContentHash"]:
            print(f"ABORT {r['region']}: baseline hash drift ({h} != {r['baselineContentHash']})")
            sys.exit(1)
        existing = {(s.get("url") if isinstance(s, dict) else s) for s in rec.get("sources", [])}
        for a in r["addSources"]:
            if a["url"] not in existing:
                rec.setdefault("sources", []).append({"url": a["url"], "summary": a["summary"]})
        for f in r["appendSummaryFacts"]:
            if f not in rec.get("summary", ""):
                sep = "" if rec.get("summary", "").endswith("</p>") else "</p>"
                rec["summary"] = rec.get("summary", "") + sep + "<p>" + f + "</p>"
    admin_path.write_text(json.dumps(admin, indent=1), encoding="utf-8")
    print("APPLIED: data/admin1.json updated for changed regions only; scores untouched; "
          "blind fields now stale and queued for S3/S4 re-blind (must re-blind before any S6+ use).")


if __name__ == "__main__":
    main()
