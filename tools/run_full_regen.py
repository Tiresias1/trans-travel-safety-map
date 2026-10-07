#!/usr/bin/env python3
"""Fleet dossier regeneration driver (2026-10-06 full-run phase 2).

Runs tools/consolidate_record.py (--apply) over every country and every
dossier-flagged ADM1 region, threaded. Each child run carries the full gate
chain (content gate -> blind gate -> fixed-vocab remediation -> retry x5);
failures are logged and the record is left untouched.

Usage: python3 tools/run_full_regen.py [--workers 8] [--only country:MLT ...]
"""
from __future__ import annotations
import argparse, json, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK = threading.Lock()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    targets = [f"country:{k}" for k in sorted(C)]
    targets += [f"{r['iso3']}/{r['name']}" for r in sorted(A.values(), key=lambda x: x.get("name", ""))
                if r.get("dossier")]
    if args.only:
        want = set(args.only)
        targets = [t for t in targets if t in want]
    print(f"regenerating {len(targets)} dossiers, {args.workers} workers", flush=True)

    done = fails = 0
    with ThreadPoolExecutor(args.workers) as ex:
        futs = {ex.submit(subprocess.run,
                          [sys.executable, "-u", str(ROOT / "tools" / "consolidate_record.py"),
                           "--who", w, "--apply"],
                          capture_output=True, text=True, timeout=900): w
                for w in targets}
        for f in as_completed(futs):
            w = futs[f]
            global_done = None
            try:
                p = f.result()
                ok = p.returncode == 0
            except Exception:
                ok = False
            with LOCK:
                done += 1
                if not ok:
                    fails += 1
                    tail = (p.stderr or p.stdout or "")[-220:].replace("\n", " ") if p else "timeout"
                    print(f"[FAIL] {w}: {tail}", flush=True)
                if done % 25 == 0:
                    print(f"... {done}/{len(targets)} ({fails} failed)", flush=True)
    print(f"REGEN DONE: {len(targets) - fails} ok, {fails} failed", flush=True)


if __name__ == "__main__":
    main()