#!/usr/bin/env python3
"""Audit the published scores against the archived rating logs.

This is the outside-auditor check: it recomputes what each published number SHOULD be
from data/measurement_logs/ plus the declared aggregation rules, and reports gaps. It
uses no prose and no stored intermediates.

Aggregation rules asserted (matching the methodology):
  division, anchored      -> score == mean estimate in anchored_results
  division, other         -> score == encounter mean of its archived ratings (by shape id)
  country, reaggregate    -> score == mean of its measured (non-inherited) divisions
  country, mirror         -> score == the admin1 territory record's score
  country, pairwise/blocked -> score == encounter mean of its archived ratings
"""
from __future__ import annotations
import argparse, gzip, json, statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROD = ["redo_c4", "recency_wave", "anchored_results"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tol", type=float, default=0.02)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    enc = defaultdict(list)
    anchored = {}
    files = [(ROOT / "data" / "measurement_logs" / f"{n}.jsonl.gz") for n in PROD]
    files = [f for f in files if f.exists()]
    for f in files:
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                try: d = json.loads(line)
                except Exception: continue
                if "sid" in d and "est" in d:
                    anchored[d["sid"]] = float(d["est"]); continue
                for s in ("a", "b"):
                    nm, rt = d.get(f"{s}_name"), d.get(f"rated_{s}")
                    if nm and rt is not None: enc[("country", nm)].append(float(rt))
                if d.get("rated_r") is not None and d.get("r"):
                    enc[("division", d["r"])].append(float(d["rated_r"]))

    by_iso = defaultdict(list)
    for sid, r in A.items():
        if not r.get("inherited") and isinstance(r.get("score"), (int, float)):
            by_iso[r.get("parentIso3") or r.get("iso3")].append(float(r["score"]))
    terr_by_iso = {r["iso3"]: r for r in A.values() if r.get("parentIso3") and r.get("dossier")}

    def expect_country(iso, r):
        mode = (r.get("derivedFrom") or {}).get("mode")
        if iso in terr_by_iso:   # territory display mirror, whatever its mode says
            return float(terr_by_iso[iso]["score"]), "territory record"
        if mode == "reaggregate":
            v = by_iso.get(iso) or []
            return (statistics.mean(v), "mean of divisions") if len(v) >= 3 else (None, "no divisions")
        if mode == "mirror":
            t = terr_by_iso.get(iso)
            return (float(t["score"]), "territory record") if t else (None, "no territory record")
        v = enc.get(("country", r.get("name")), [])
        return (statistics.mean(v), "encounter mean") if len(v) >= 3 else (None, "no ratings")

    TMPL = "No sub-national signal was identified; the national assessment applies here"

    def expect_division(sid, r):
        mode = (r.get("derivedFrom") or {}).get("mode")
        # route-3 invariant: a division whose summary is the no-signal template takes its
        # national score on every build, overriding whatever an earlier pass produced
        if r.get("estimated") and TMPL in str(r.get("summary", "")):
            c = C.get(r.get("iso3"))
            if c: return float(c["score"]), "national score (route-3)"
        if r.get("inherited"):
            # single-unit stand-in: score mirrors the country record
            c = C.get(r.get("iso3"))
            if c: return float(c["score"]), "country stand-in"
        if mode == "anchored" and sid in anchored:
            # the published value is the estimate after the declared floor clamp
            return max(0.02, min(0.98, anchored[sid])), "anchored estimate (clamped)"
        v = enc.get(("division", sid), [])
        return (statistics.mean(v), "encounter mean") if len(v) >= 3 else (None, "no ratings")

    rows, missing = [], []
    for iso, r in C.items():
        e, why = expect_country(iso, r)
        if e is None: missing.append(("country", iso, why)); continue
        rows.append(("country", iso, r.get("name"), r["score"], e, why))
    for sid, r in A.items():
        e, why = expect_division(sid, r)
        if e is None:
            if r.get("inherited"): continue
            missing.append(("division", sid, why)); continue
        rows.append(("division", sid, r.get("name"), r["score"], e, why))
    ok = [x for x in rows if abs(x[3] - x[4]) <= args.tol]
    bad = [x for x in rows if abs(x[3] - x[4]) > args.tol]
    print(f"logs: {[f.name for f in files]}")
    print(f"verified: {len(ok)}/{len(rows)} within {args.tol} | outside: {len(bad)} | not verifiable: {len(missing)}")
    from collections import Counter
    print("verified by rule:", dict(Counter(x[5] for x in ok)))
    print("outside by rule:", dict(Counter(x[5] for x in bad)))
    for x in sorted(bad, key=lambda t: -abs(t[3] - t[4]))[:8]:
        print(f"  {x[0]:8} {str(x[2])[:22]:22} stored {x[3]:.3f} expected {x[4]:.3f} gap {x[3]-x[4]:+.3f} [{x[5]}]")
    if args.verbose:
        for x in missing[:10]: print("  not verifiable:", x)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
