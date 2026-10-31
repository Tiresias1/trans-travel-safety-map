#!/usr/bin/env python3
"""Two-stage division calibration (2026-10-30).

Problem: divisions rated against random COUNTRY comparators are anchored by the
parent framework, which dominates the rating. Divisions sharing one framework
(US states, Mongolian aimags) therefore collapse together, and partner sampling
adds noise of the same size as the real differences.

Stage 1 (relative): pair divisions of the SAME country against each other. The
framework is identical on both sides, so it cancels and the rater compares
division content to division content. Collect per-division mean ratings.
Stage 2 (anchor): centre the offsets (mean 0) and set

    division_score = country_score + centred_offset

so the country's divisions average to its national score and keep their real
internal spread.

Usage: python3 tools/in_country_calibrate.py [--pairs-per-div 8] [--workers 3]
       [--apply] [--only USA MNG ...]
"""
from __future__ import annotations
import argparse, fcntl, json, statistics, subprocess, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from build_data import band_label  # noqa

MODEL = "deepseek/deepseek-v4.1-flash"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs-per-div", type=int, default=8)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    key = Path("/tmp/.openrouter_key").read_text().strip()
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    by_country = defaultdict(list)
    for sid, r in A.items():
        iso = r.get("parentIso3") or r.get("iso3")
        if iso in C and str(r.get("summary", "")).strip() and isinstance(r.get("score"), (int, float)):
            by_country[iso].append(sid)
    todo = [(iso, ids) for iso, ids in by_country.items() if len(ids) >= 3]
    if args.only:
        todo = [(i, ids) for i, ids in todo if i in set(args.only)]
    todo.sort(key=lambda t: -len(t[1]))
    print(f"countries: {len(todo)} | divisions: {sum(len(ids) for _, ids in todo)}", flush=True)
    results = {}
    for iso, ids in todo:
        n = max(40, len(ids) * args.pairs_per_div // 2)
        log = f"/tmp/inc_{iso}.jsonl"
        w = [sys.executable, "-u", str(ROOT / "tools" / "blind_pairwise.py"),
             "--api", "openai", "--baseurl", "https://openrouter.ai/api/v1",
             "--endpoint-suffix", "/chat/completions", "--auth-style", "bearer",
             "--api-key", key, "--model", MODEL, "--max-output-tokens", "4000",
             "--admin1", "--country", iso, "--num-pairs", str(n),
             "--differential-weighting-percent", "0.02", "--absolute-weighting-percent",
             "0.05", "--absolute-weighting-shift", "0.0005", "--workers", "2",
             "--seed", "99", "--no-write", "--log", log]
        try:
            p = subprocess.run(w, capture_output=True, text=True, timeout=7200)
        except Exception as e:
            print(f"  {iso}: FAILED {str(e)[:60]}", flush=True)
            continue
        enc = defaultdict(list)
        try:
            for line in open(log):
                d = json.loads(line)
                if d.get("rated_a") is not None and d.get("a"):
                    enc[d["a"]].append(float(d["rated_a"]))
                if d.get("rated_b") is not None and d.get("b"):
                    enc[d["b"]].append(float(d["rated_b"]))
        except Exception:
            pass
        if len(enc) < 3:
            print(f"  {iso}: no usable ratings ({len(enc)} divisions)", flush=True)
            continue
        results[iso] = {k: statistics.mean(v) for k, v in enc.items()}
        lo = min(results[iso].values()); hi = max(results[iso].values())
        print(f"  {iso}: {len(enc)} divisions rated, spread {lo:.2f}-{hi:.2f}", flush=True)
    print(f"stage 1 done for {len(results)} countries", flush=True)
    print("country      divisions  spread(sd)  national", flush=True)
    for iso, m in sorted(results.items()):
        print(f"  {iso:4} {len(m):9d}  {statistics.pstdev(list(m.values())):.3f}    "
              f"{C[iso]['score']:.3f}", flush=True)
    if args.apply and results:
        lock = open(ROOT / "data" / ".apply.lock", "w")
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            A = json.loads((ROOT / "data" / "admin1.json").read_text())
            n = 0
            for iso, m in results.items():
                nat = float(C[iso]["score"])
                vals = list(m.values())
                mu = statistics.mean(vals)
                for sid, mean in m.items():
                    rec = A.get(sid)
                    if not rec:
                        continue
                    sc = max(0.01, min(0.99, nat + (mean - mu)))
                    rec["score"] = round(sc, 6)
                    rec["band"] = band_label(sc)
                    rec["ratedBy"] = MODEL
                    rec["derivedFrom"] = {"parent": iso, "parentScore": round(nat, 6),
                                          "offset": round(mean - mu, 6)}
                    n += 1
            (ROOT / "data" / "admin1.json").write_text(
                json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"anchored {n} divisions to their national score", flush=True)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
            lock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
