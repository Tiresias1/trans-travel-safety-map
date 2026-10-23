#!/usr/bin/env python3
"""Relative derivation for dependent territories (2026-10-21).

Territory scores were coming from mixed-mode pairs against RANDOM country
comparators, while their parent was rated in countries mode against other
countries — two different scales, so a territory's score was not derived from
its parent at all (PR scored above USA despite a hostile local layer).

This lane rates each territory ONLY against its own parent (same call, same
scale), takes the mean offset, and sets:

    territory_score = parent_score + mean(rated_territory - rated_parent)

clamped to [0.01, 0.99]. Recorded with ratedBy/derivedFrom for traceability.

Usage: python3 tools/derive_territories.py [--pairs 16] [--workers 3] [--apply]
"""
from __future__ import annotations
import argparse, fcntl, json, statistics, subprocess, sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from build_data import band_label  # noqa

MODEL = "deepseek/deepseek-v4.1-flash"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", type=int, default=16)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    key = (Path("/tmp/.openrouter_key")).read_text().strip()
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    terr = [(k, r) for k, r in A.items()
            if r.get("parentIso3") and r.get("dossier")]
    print(f"territories: {len(terr)}", flush=True)

    def run_one(item):
        key_, r = item
        name, parent = r["name"], r["parentIso3"]
        log = f"/tmp/parentonly_{parent}_{name.replace(' ', '_')}.jsonl"
        w = [sys.executable, "-u", str(ROOT / "tools" / "blind_pairwise.py"),
             "--api", "openai", "--baseurl", "https://openrouter.ai/api/v1",
             "--endpoint-suffix", "/chat/completions", "--auth-style", "bearer",
             "--api-key", key, "--model", MODEL, "--max-output-tokens", "4000",
             "--allow-fallback", "--regions-vs-countries", "--regions-vs-parent-only",
             "--regions-parent", parent, "--regions-unit-exact", "--regions-unit", name,
             "--num-pairs", str(args.pairs), "--differential-weighting-percent", "0.02",
             "--absolute-weighting-percent", "0.12", "--absolute-weighting-shift", "0.0005",
             "--workers", "2", "--seed", "77", "--no-write", "--log", log]
        try:
            p = subprocess.run(w, capture_output=True, text=True, timeout=3600)
        except Exception as e:
            return key_, r, None, str(e)[:100]
        rs, cs = [], []
        try:
            for line in open(log):
                d = json.loads(line)
                if d.get("rated_r") is None or d.get("rated_c") is None:
                    continue
                rs.append(float(d["rated_r"]))
                cs.append(float(d["rated_c"]))
        except Exception as e:
            return key_, r, None, str(e)[:100]
        if len(rs) < 4:
            return key_, r, None, f"only {len(rs)} usable pairs"
        delta = statistics.mean([a - b for a, b in zip(rs, cs)])
        return key_, r, (delta, statistics.mean(rs), statistics.mean(cs), len(rs)), ""

    results = []
    with ThreadPoolExecutor(args.workers) as ex:
        futs = [ex.submit(run_one, t) for t in terr]
        for f in as_completed(futs):
            key_, r, res, err = f.result()
            if err:
                print(f"[FAIL] {r['name']}: {err}", flush=True)
                continue
            delta, rr, cr, n = res
            parent = C.get(r["parentIso3"], {})
            pscore = float(parent.get("score", 0.5))
            new = max(0.01, min(0.99, pscore + delta))
            results.append((key_, r["name"], r["parentIso3"], pscore, delta, new, n))
            print(f"  {r['name'][:28]:28} parent {pscore:.3f} delta {delta:+.3f} "
                  f"-> {new:.3f} (n={n}, rated {rr:.2f} vs {cr:.2f})", flush=True)
    print(f"derived {len(results)}/{len(terr)}", flush=True)
    if args.apply and results:
        lock = open(ROOT / "data" / ".apply.lock", "w")
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            A = json.loads((ROOT / "data" / "admin1.json").read_text())
            for key_, name, parent, pscore, delta, new, n in results:
                rec = A.get(key_)
                if not rec:
                    continue
                rec["score"] = round(new, 6)
                rec["band"] = band_label(new)
                rec["ratedBy"] = MODEL
                rec["derivedFrom"] = {"parent": parent, "parentScore": round(pscore, 6),
                                      "delta": round(delta, 6), "pairs": n}
            (ROOT / "data" / "admin1.json").write_text(
                json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")
            print("applied", flush=True)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
            lock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
