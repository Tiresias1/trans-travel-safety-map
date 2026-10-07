#!/usr/bin/env python3
"""Settlement pass (2026-10-06): make the score EQUAL the rater's honest verdict.

The wave maths converges only ~40% of the gap per 20 encounters under gentle
ramp parameters, and random sampling gives some entities very few encounters
(Scotland: 7). This pass:

  1. parses the wave logs and computes each entity's encounter-weighted mean
     rater rating;
  2. queues every entity with >= 3 encounters and |stored - mean| >= TOL
     (territory dossiers are always queued after a rating-rule change);
  3. runs focused convergence pairs for each queued entity with CONSTANT
     weights (p_abs 0.12 of the remaining gap per encounter -> convergence in
     ~16 encounters), via blind_pairwise.py's existing machinery.

Usage:
  python3 tools/settle_scores.py --plan      # print the queue, run nothing
  python3 tools/settle_scores.py --run       # execute the settlement runs
"""
from __future__ import annotations
import argparse, json, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOL = 0.02
MIN_ENC = 3
SETTLE_PAIRS = 16

# territories whose ratings change under RATING_RULES 12 (parent-regime rule)
TERRITORIES = {"ASM", "GUM", "VIR", "MNP", "PRI"}


def collect(logs: list[str]) -> dict[str, list[float]]:
    enc: dict[str, list[float]] = {}
    for lp in logs:
        p = Path(lp)
        if not p.exists():
            continue
        for line in p.open():
            try:
                d = json.loads(line)
            except Exception:
                continue
            # countries mode: both sides rated
            if d.get("a_name") and d.get("rated_a") is not None and d.get("a_new") is not None:
                enc.setdefault(d["a_name"], []).append(float(d["rated_a"]))
            if d.get("b_name") and d.get("rated_b") is not None and d.get("b_new") is not None:
                enc.setdefault(d["b_name"], []).append(float(d["rated_b"]))
            # mixed mode: only the region side moves and is rated
            if d.get("r_name") and d.get("rated_r") is not None and d.get("r_new") is not None:
                enc.setdefault(f"region:{d['parent']}:{d['r_name']}",
                               []).append(float(d["rated_r"]))
    return enc


def build_queue(enc, C, A):
    import statistics
    queue = []
    for name, ratings in sorted(enc.items()):
        if len(ratings) < MIN_ENC:
            continue
        mean = statistics.mean(ratings)
        if name.startswith("region:"):
            _, iso, rname = name.split(":", 2)
            rec = next((x for x in A.values()
                        if x.get("iso3") == iso and x.get("name") == rname), None)
            if not rec:
                continue
            gap = abs(float(rec["score"]) - mean)
            # all dossier regions re-checked; territories flagged separately
            if gap >= TOL:
                queue.append({"kind": "region", "iso": iso, "name": rname,
                              "stored": rec["score"], "mean": mean,
                              "n": len(ratings), "gap": round(gap, 3)})
        else:
            rec = next((x for x in C.values() if x.get("name") == name), None)
            if not rec:
                continue
            iso = next((k for k, v in C.items() if v is rec), None)
            gap = abs(float(rec["score"]) - mean)
            if gap >= TOL or (iso in TERRITORIES):
                queue.append({"kind": "country", "iso": iso, "name": name,
                              "stored": rec["score"], "mean": mean,
                              "n": len(ratings), "gap": round(gap, 3),
                              "rule12": iso in TERRITORIES})
    return queue


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", nargs="*",
                    default=["/tmp/tour_countries.jsonl", "/tmp/tour_admin1.jsonl"])
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    enc = collect(args.logs)
    queue = build_queue(enc, C, A)
    print(f"settlement queue: {len(queue)} entities "
          f"({sum(1 for q in queue if q.get('rule12'))} rule-12 territories)")
    for q in sorted(queue, key=lambda x: -x["gap"])[:40]:
        tag = "RULE12 " if q.get("rule12") else ""
        print(f"  {tag}{q['kind']:7} {q['name'][:32]:32} stored {q['stored']:.3f} "
              f"mean {q['mean']:.3f} gap {q['gap']:.3f} (n={q['n']})")
    if args.plan or not args.run:
        return
    print("running settlement...", flush=True)
    key_env = (ROOT / ".openrouter_key")
    import os
    key = os.environ.get("OPENROUTER_KEY", "")
    fails = 0
    done = 0
    def run_one(q):
        w = ["python3", "-u", str(ROOT / "tools" / "blind_pairwise.py"),
             "--api", "openai", "--baseurl", "https://openrouter.ai/api/v1",
             "--endpoint-suffix", "/chat/completions", "--auth-style", "bearer",
             "--api-key", key, "--model", "xiaomi/mimo-v2.6-flash",
             "--num-pairs", str(SETTLE_PAIRS),
             "--differential-weighting-percent", "0.01",
             "--absolute-weighting-percent", "0.12",
             "--absolute-weighting-shift", "0.0005",
             "--workers", "2", "--seed", "77",
             "--log", f"/tmp/settle_{q['kind']}_{q['iso']}_{q['name'][:12]}.jsonl".replace(" ", "_").replace("/", "_")]
        if q["kind"] == "country":
            w += ["--focus", q["iso"]]
        else:
            w += ["--regions-vs-countries", "--regions-parent", q["iso"],
                  "--regions-unit-exact", "--regions-unit", q["name"]]
        try:
            p = subprocess.run(w, capture_output=True, text=True, timeout=1800)
            ok = p.returncode == 0
            return q, ok, (p.stdout or "")[-160:].replace("\n", " ")
        except Exception as e:
            return q, False, str(e)[:160]
    with ThreadPoolExecutor(args.workers) as ex:
        futs = [ex.submit(run_one, q) for q in queue]
        for f in as_completed(futs):
            q, ok, tail = f.result()
            done += 1
            if not ok:
                fails += 1
                print(f"[FAIL] {q['name']}: {tail}", flush=True)
            if done % 10 == 0:
                print(f"... {done}/{len(queue)} settled ({fails} failed)", flush=True)
    print(f"SETTLEMENT DONE: {len(queue) - fails} ok, {fails} failed", flush=True)


if __name__ == "__main__":
    main()