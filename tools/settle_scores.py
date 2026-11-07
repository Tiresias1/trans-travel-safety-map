#!/usr/bin/env python3
"""Settlement pass (2026-10-06) — MUTATIONS RETIRED 2026-11-13.

(Historical description, kept for context: the pass WAS meant to make the
score equal the rater's honest verdict.) The wave maths converges only ~40%
of the gap per 20 encounters under gentle ramp parameters, and random
sampling gives some entities very few encounters (Scotland: 7). It:

  1. parses the wave logs and computes each entity's encounter-weighted mean
     rater rating;
  2. queues every entity with >= 3 encounters and |stored - mean| >= TOL
     (territory dossiers are always queued after a rating-rule change);
  3. [REMOVED] ran focused convergence pairs for each queued entity via
     blind_pairwise.py, rewriting scores — this path no longer exists.

Usage:
  python3 tools/settle_scores.py --plan      # read-only queue report (the
                                             # only surviving mode; default)
  --rebalance / --run (incl. --force-legacy-invariant) are RETIRED: refused
  with a nonzero exit immediately after argument parsing, before any data
  read for mutation, any provider call, or any write. The mutation
  implementations were deleted; see main(). Existing scores are preserved
  as historical inputs until a replacement method is independently
  validated.
"""
from __future__ import annotations
# REMOVED WITH THE RETIRED MUTATIONS (2026-11-13): subprocess/threading/time
# (provider settlement machinery), band_label (score rewrites) and
# ThreadPoolExecutor were deleted alongside --rebalance/--run; do not
# re-add them without independent validation of a replacement method.
import argparse, gzip, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOL = float(__import__("os").environ.get("SETTLE_TOL", "0.02"))
MIN_ENC = 3

# territories whose ratings change under RATING_RULES 12 (parent-regime rule)
TERRITORIES = {"ASM", "GUM", "VIR", "MNP", "PRI"}


def collect(logs: list[str]) -> dict[str, list[float]]:
    enc: dict[str, list[float]] = {}
    for lp in logs:
        p = Path(lp)
        if not p.exists():
            continue
        opener = gzip.open if str(p).endswith(".gz") else open
        with opener(p, "rt", encoding="utf-8") as fh:
            for line in fh:
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


def instrument_of(rec) -> str:
    """Canonical instrument name (see tools/instruments.py)."""
    from instruments import classify
    return classify(rec)


# Settlement applies only to scores whose declared instrument IS the encounter mean.
from instruments import SETTLEABLE as SETTLEABLE_INSTRUMENTS  # noqa: E402

SKIPPED: dict[str, int] = {}


def build_queue(enc, C, A):
    import statistics
    SKIPPED.clear()
    queue = []
    for name, ratings in sorted(enc.items()):
        if len(ratings) < MIN_ENC:
            continue
        mean = statistics.mean(ratings)
        if name.startswith("region:"):
            _, iso, rname = name.split(":", 2)
            rec = next((x for x in A.values()
                        if x.get("iso3") == iso and x.get("name") == rname), None)
            # route-3 / converted regions inherit the national score and are
            # settled no further
            if not rec or not rec.get("dossier"):
                continue
            # INSTRUMENT GUARD (added 2026-11-13): settlement enforces the
            # invariant "score == encounter mean". That invariant only applies
            # where the encounter mean IS the instrument. Anchored-calibrated
            # divisions are scored anchor + mean(deviation from fixed anchors),
            # and their logs are contrast ratings against random partner
            # countries (measured within-region correlation with partner rating
            # -0.39). Settling them to encounter means would replace a calibrated
            # estimate with a contrast-contaminated one and destroy the
            # calibration. Anchored entities are therefore never queued here;
            # their invariant is "score == anchorRating", audited by
            # tools/verify_from_logs.py.
            instr = instrument_of(rec)
            if instr not in SETTLEABLE_INSTRUMENTS:
                SKIPPED[instr] = SKIPPED.get(instr, 0) + 1
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
            instr = instrument_of(rec)
            if instr not in SETTLEABLE_INSTRUMENTS:
                SKIPPED[instr] = SKIPPED.get(instr, 0) + 1
                continue   # see instrument guard above
            gap = abs(float(rec["score"]) - mean)
            if gap >= TOL or (iso in TERRITORIES):
                _p3 = rec.get("parentIso3")
                if not _p3 and iso in TERRITORIES:
                    _p3 = next((x.get("parentIso3") for x in A.values()
                                if x.get("iso3") == iso and x.get("parentIso3")), None)
                queue.append({"kind": "country", "iso": iso, "name": name,
                              "parentIso3": _p3,
                              "stored": rec["score"], "mean": mean,
                              "n": len(ratings), "gap": round(gap, 3),
                              "rule12": iso in TERRITORIES})
    return queue


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", nargs="*",
                    # Production basis, matching tools/verify_from_logs.py. The older
                    # defaults included superseded runs whose country ratings no longer
                    # represent the published scores, which manufactured ~450 phantom
                    # queue entries (the same class of error as the recency_wave bug).
                    default=["data/measurement_logs/redo_c4.jsonl.gz",
                             "data/measurement_logs/anchored_results.jsonl.gz"])
    ap.add_argument("--plan", action="store_true",
                    help="print the read-only settlement queue (default behaviour; "
                         "the only mode that still exists)")
    ap.add_argument("--rebalance", action="store_true",
                    help="RETIRED: refused with a nonzero exit. This mutation "
                         "rewrote scores to encounter means and is disabled "
                         "until a replacement method is independently validated")
    ap.add_argument("--run", action="store_true",
                    help="RETIRED: refused with a nonzero exit. This mutation "
                         "spawned provider runs and rewrote scores; disabled")
    ap.add_argument("--force-legacy-invariant", action="store_true",
                    help="RETIRED: accepted for command-line compatibility but "
                         "re-enables NOTHING; --run is refused regardless")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    # RETIRED MUTATIONS (2026-11-13): both score-mutation modes are refused
    # immediately after parsing --help is handled inside parse_args - BEFORE
    # any data file is read for mutation, before collect()/build_queue() run,
    # before any provider subprocess could be spawned, and before any data
    # write. Exit code 2 signals the retired mutation. Only the read-only
    # plan below remains available.
    if args.rebalance or args.run:
        print("RETIRED: settlement mutations are disabled "
              "(--rebalance and --run).", file=sys.stderr)
        if args.force_legacy_invariant:
            print("  --force-legacy-invariant re-enables NOTHING; --run is "
                  "refused regardless.", file=sys.stderr)
        print("  No scores are modified and no provider is run. Read-only "
              "--plan remains available.", file=sys.stderr)
        print("  Until a new method is independently validated, existing "
              "scores are preserved as historical inputs.", file=sys.stderr)
        return 2
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    enc = collect(args.logs)
    queue = build_queue(enc, C, A)
    print(f"settlement queue: {len(queue)} entities "
          f"({sum(1 for q in queue if q.get('rule12'))} rule-12 territories)")
    print(f"excluded by instrument guard (fail-closed): {dict(sorted(SKIPPED.items()))}")
    for q in sorted(queue, key=lambda x: -x["gap"])[:40]:
        tag = "RULE12 " if q.get("rule12") else ""
        print(f"  {tag}{q['kind']:7} {q['name'][:32]:32} stored {q['stored']:.3f} "
              f"mean {q['mean']:.3f} gap {q['gap']:.3f} (n={q['n']})")
    # RETIRED (2026-11-13): the --rebalance and --run implementations that
    # lived here (score rewrites to encounter means; provider settlement
    # subprocesses, including the --force-legacy-invariant path) were
    # REMOVED. They are unreachable: both flags are refused with exit 2
    # immediately after argument parsing. What remains is the read-only
    # plan above.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
