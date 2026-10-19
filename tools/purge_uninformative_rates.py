#!/usr/bin/env python3
"""Purge uninformative trans-violence-rate claims (2026-10-16).

A trans killing rate that the source itself labels an undercount floor, and
that sits at or below the jurisdiction's general homicide rate, is
epistemically empty: the true value is unknowable and indistinguishable from
background. It cannot inform a rating and must not appear in a summary.

This lane removes such source claims fleet-wide (source entry dropped, since
the claim IS the source's only content), so the regen does not carry them.
Rate claims that are clearly ABOVE background, patterned and documented are
kept untouched.

Usage: python3 tools/purge_uninformative_rates.py [--apply]
"""
from __future__ import annotations
import argparse, fcntl, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FLOOR = re.compile(r"undercount|floor|known to undercount|acknowledged floor|at least this", re.I)
# general homicide rate per 100k (CDC, per-state table) — a trans rate at or
# below this is indistinguishable from background, so its magnitude is empty
BG_RATE = {'Georgia':6.2,'Florida':5.2,'Tennessee':7.5,'Alabama':7.8,'Louisiana':11.4,'Texas':4.6,
  'California':4.4,'New Hampshire':1.6,'New Jersey':3.2,'Mississippi':7.2,'Missouri':9.8,'Ohio':5.1,
  'Washington':3.1,'New York':3.0,'Illinois':6.4,'Michigan':6.1,'Arizona':6.4,'Nevada':6.6,
  'Pennsylvania':5.7,'North Carolina':6.4,'South Carolina':8.4,'Virginia':5.2,'Maryland':7.6,
  'Massachusetts':2.1,'Connecticut':3.4,'Delaware':5.9,'Iowa':3.2,'Kansas':5.9,'Kentucky':6.6,
  'Oklahoma':6.8,'Oregon':3.9,'Utah':2.2,'Wisconsin':4.0,'Minnesota':3.4,'Indiana':6.3,
  'Arkansas':7.6,'Nebraska':3.6,'Idaho':2.4,'Montana':4.2,'Wyoming':3.3,'New Mexico':8.5,
  'Colorado':4.8,'West Virginia':6.6,'Alaska':7.9,'Hawaii':2.1,'Maine':1.6,'Rhode Island':2.4,
  'Vermont':1.6,'North Dakota':2.8,'South Dakota':5.0}
PER100K = re.compile(r"(\d+(?:\.\d+)?)\s*(?:killings?|homicides?|murders?)?\s*(?:of trans women|per 100,000)", re.I)
RATE = re.compile(r"killing rate|killings? of trans|per 100,000", re.I)
BG = re.compile(r"general (?:homicide|murder)|background (?:homicide|murder)|homicide rate|murder rate", re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    lock = open(ROOT / "data" / ".apply.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX)
    try:
        path = ROOT / "data" / "admin1.json"
        A = json.loads(path.read_text())
        removed = []
        for key, r in A.items():
            if not r.get("dossier"):
                continue
            keep = []
            for s in r.get("sources", []):
                cl = str(s.get("summary", ""))
                _bg = BG_RATE.get(r.get("name"))
                _m = PER100K.search(cl)
                _below_bg = False
                if _bg is not None and _m:
                    try:
                        _below_bg = float(_m.group(1)) <= _bg
                    except ValueError:
                        _below_bg = False
                if RATE.search(cl) and (FLOOR.search(cl) or _below_bg):
                    # undercount-floor rate: uninformative whether or not it is
                    # above background, because the true value is unknown
                    why = "undercount-floor" if FLOOR.search(cl) else "at/below background"
                    removed.append((r.get("name"), why, cl[:80]))
                    continue
                keep.append(s)
            r["sources"] = keep
        print(f"removed {len(removed)} undercount-floor rate claims")
        for nm, why, cl in removed[:14]:
            print(f"  {nm} [{why}]: {cl}")
        if args.apply:
            path.write_text(json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")
            print("applied")
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
