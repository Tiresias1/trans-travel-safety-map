#!/usr/bin/env python3
"""Florida (Uruguay, sid 27058087B4606463382645) score seed repair.

The record's old score 0.40 came from a name-collision bug (US Florida's
rating was pasted into it). The global ADM1 run gave it only 2 updates
(final 0.5112), still ~0.2 below its Uruguayan siblings (~0.71-0.81), so
the seed itself is corrupt. This script reseeds it exactly once and
recalibrates against frozen siblings, reusing the global_adm1_iterative
machinery: same directive-augmented v4 system text (bounded
anti-absence-as-safety DIRECTIVE), same neutralized dossiers
(render_admin1_dossier + neutralized summary/blindSummary local evidence),
same combined A/B pairwise format, provider_models.call_v4 at medium.

Procedure:
  1. Seed Florida URY at the MEDIAN of the other 18 Uruguay ADM1
     final_running_scores from analysis/global_adm1_iterative.json
     (iso3 URY, excluding Florida itself). The seed value is recorded.
  2. Run 8 seeded pairings (seed 20261119): A = Florida URY, B = nearest
     sibling by current running score within the global run's URY
     pairing group (nearest max(int(0.10*n_iso),3) candidates, tie-break
     region id, no immediate unordered-pair repeat when an alternative
     exists). Sibling scores are FROZEN at their global-run finals; only
     Florida's running score moves, so candidate ranking follows it.
     Exactly one model per pairing: least-used across the seven models
     for this reseed run so far, ties broken by seeded shuffle.
  3. One attempt per pairing, no retries; failed draws are recorded and
     cause no score update.
  4. Update ONLY Florida with the standard schedule (alpha 0.20 for
     updates 1-8). B ratings are recorded but never applied.

Artifacts: runs/ury-florida-reseed-20261119/ (attempt/content/result per
pairing, ledger.json, pair-history.json) and aggregate
analysis/ury_florida_reseed.json (seed, per-pairing results, final score,
cost). Resume-safe: completed pairings in pair-history.json are never
re-called, so the 8 draws happen exactly once. Single-writer guard:
refuses to launch if global_adm1_iterative.py or another
ury_florida_reseed.py python process is running. The credential is read
only by provider_models. Does not write site data or data/admin1.json.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import global_adm1_iterative as GA  # noqa: E402
import single_rate_v4 as V4  # noqa: E402

RUN_ID_DEFAULT = "ury-florida-reseed-20261119"
AGGREGATE_PATH = HERE / "analysis" / "ury_florida_reseed.json"
SOURCE_AGGREGATE_PATH = HERE / "analysis" / "global_adm1_iterative.json"
FLORIDA_SID = "27058087B4606463382645"
FLORIDA_REGION = f"{FLORIDA_SID}:Florida"
ISO3 = "URY"
N_PAIRINGS = 8
SEED = 20261119


def check_writer(script_name: str) -> list[int]:
    """PIDs of other python processes running script_name (excluding self)."""
    pids = []
    proc = Path("/proc")
    if proc.is_dir():
        for entry in proc.iterdir():
            if not entry.name.isdigit():
                continue
            pid = int(entry.name)
            if pid == os.getpid():
                continue
            try:
                raw = (entry / "cmdline").read_bytes()
            except OSError:
                continue
            if not raw:
                continue
            parts = [p.decode("utf-8", "replace") for p in raw.split(b"\x00") if p]
            argv0 = Path(parts[0]).name if parts else ""
            if not argv0.startswith("python"):
                continue
            if any(p == script_name or p.endswith("/" + script_name)
                   for p in parts):
                pids.append(pid)
    return sorted(pids)


def load_sibling_finals() -> tuple[dict, dict]:
    """Frozen URY sibling finals + source provenance from the global run."""
    agg = json.loads(SOURCE_AGGREGATE_PATH.read_text(encoding="utf-8"))
    if FLORIDA_REGION not in agg["final_running_scores"]:
        raise SystemExit(f"{FLORIDA_REGION} missing from global-run aggregate")
    sibling_finals = {}
    for region, meta in agg["adm1"].items():
        if meta["iso3"] == ISO3 and region != FLORIDA_REGION:
            sibling_finals[region] = agg["final_running_scores"][region]
    if len(sibling_finals) != 18:
        raise SystemExit(f"expected 18 URY siblings, got {len(sibling_finals)}")
    provenance = {
        "source_aggregate": str(SOURCE_AGGREGATE_PATH.relative_to(HERE)),
        "source_created": agg["created"],
        "source_run_id": agg["run_id"],
        "florida_pre_global_run_score": agg["initial_scores"][FLORIDA_REGION],
        "florida_global_run_final_score": agg["final_running_scores"][FLORIDA_REGION],
        "florida_global_run_update_count": agg["update_counts"][FLORIDA_REGION],
    }
    return sibling_finals, provenance


def run(run_id: str, dry_run: bool = False, seed: int = SEED,
        n_pairings: int = N_PAIRINGS) -> int:
    for script in ("global_adm1_iterative.py", "ury_florida_reseed.py"):
        others = check_writer(script)
        if others:
            print(f"single-writer guard: {script} already running, PID(s)={others}; "
                  f"refusing to launch", flush=True)
            return 2
    (system, base_system, regions, focal_pool, groups, iso_of,
     name_of, dossiers, initial_scores, models, manifest, scope) = GA.build_context()
    if FLORIDA_REGION not in groups.get(ISO3, []):
        raise SystemExit(f"{FLORIDA_REGION} not in the global-run URY pairing group")
    sibling_finals, provenance = load_sibling_finals()
    seed_value = statistics.median(sibling_finals.values())

    # Candidate ranking uses the global run's URY pairing group (17
    # differentiator-eligible siblings; Canelones/Maldonado are
    # no-differentiator and excluded from pairing there). The median seed
    # above uses all 18 siblings as specified.
    scores = dict(sibling_finals)
    scores[FLORIDA_REGION] = seed_value
    candidate_k = GA.candidate_k_for(len(groups[ISO3]))

    print(f"base_system_sha256={V4.sha(base_system)} system_sha256={V4.sha(system)} "
          f"florida={FLORIDA_REGION} seed_value={seed_value!r} "
          f"(median of {len(sibling_finals)} frozen URY sibling finals) "
          f"pairing_group_size={len(groups[ISO3])} candidate_k={candidate_k} "
          f"models={models} seed={seed} n_pairings={n_pairings}", flush=True)
    if dry_run:
        rng = random.Random(seed)
        model_rng = random.Random(seed + 99)
        model_usage = {FLORIDA_REGION: Counter()}
        partner = GA.pick_partner(rng, FLORIDA_REGION, scores, groups, iso_of, None)
        model_key = GA.pick_model_balanced(model_rng, FLORIDA_REGION, model_usage, models)
        print(f"dry run: sibling_finals={sibling_finals}; "
              f"candidates={GA.candidates_for(FLORIDA_REGION, scores, groups, iso_of)}; "
              f"first partner={partner} model={model_key}; "
              f"no provider calls made", flush=True)
        return 0

    run_dir = HERE / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    pair_history_path = run_dir / "pair-history.json"

    update_count = 0
    update_history = []
    model_usage = {FLORIDA_REGION: Counter()}
    iterations = []
    total = Decimal("0")
    rng = random.Random(seed)
    model_rng = random.Random(seed + 99)

    if pair_history_path.exists():
        hist = json.loads(pair_history_path.read_text(encoding="utf-8"))
        if hist.get("seed") != seed or hist.get("run_id") != run_id:
            raise SystemExit("existing pair-history.json does not match this run/seed; refusing to resume")
        if hist.get("seed_value") != seed_value:
            raise SystemExit("existing pair-history.json seed_value differs from current median; refusing to resume")
        iterations = hist["iterations"]
        scores = dict(hist["running_scores"])
        update_count = hist["update_count"]
        update_history = hist["update_history"]
        rng = GA._rng_state_from_json(hist["rng_state"])
        model_rng = GA._rng_state_from_json(hist["model_rng_state"])
        model_usage = {FLORIDA_REGION: Counter(hist["model_usage"][FLORIDA_REGION])}
        total = Decimal(hist.get("total_usd", "0"))
        print(f"resuming: {len(iterations)} completed pairings kept, "
              f"{n_pairings - len(iterations)} remaining", flush=True)

    def write_history():
        pair_history_path.write_text(json.dumps({
            "run_id": run_id, "seed": seed,
            "n_pairings_planned": n_pairings,
            "florida_region": FLORIDA_REGION,
            "seed_value": seed_value,
            "sibling_finals_frozen": sibling_finals,
            "models": models,
            "system_sha256": V4.sha(system),
            "base_system_sha256": V4.sha(base_system),
            "running_scores": scores,
            "update_count": update_count,
            "update_history": update_history,
            "model_usage": {FLORIDA_REGION: dict(model_usage[FLORIDA_REGION])},
            "rng_state": GA._rng_state_to_json(rng),
            "model_rng_state": GA._rng_state_to_json(model_rng),
            "total_usd": str(total),
            "iterations": iterations,
        }, indent=1, ensure_ascii=False), encoding="utf-8")

    for iteration in range(len(iterations) + 1, n_pairings + 1):
        prev_pair = None
        if iterations:
            last = iterations[-1]
            prev_pair = frozenset((last["A_region"], last["B_region"]))
        partner = GA.pick_partner(rng, FLORIDA_REGION, scores, groups, iso_of, prev_pair)
        a_region, b_region = FLORIDA_REGION, partner  # A=Florida, B=frozen sibling
        model_key = GA.pick_model_balanced(model_rng, FLORIDA_REGION, model_usage, models)
        model_usage[FLORIDA_REGION][model_key] += 1
        user_text = GA.combined_user(dossiers, a_region, b_region)
        result = GA._do_one(run_dir, iteration, model_key, a_region, b_region,
                            system, user_text)
        entry = {
            "iteration": iteration, "model": model_key,
            "A_region": a_region, "B_region": b_region,
            "A_iso3": ISO3, "B_iso3": ISO3,
            "A_name": name_of[a_region], "B_name": name_of[b_region],
            "B_frozen_score": sibling_finals[b_region],
            "status": result["status"],
            "combined_user_sha256": V4.sha(user_text),
        }
        if "cost_usd" in result:
            entry["cost_usd"] = result["cost_usd"]
            total += Decimal(result["cost_usd"])
        if result["status"] == "ok":
            entry["A_rating"] = result["A_rating"]
            entry["B_rating"] = result["B_rating"]  # recorded only; sibling frozen
            entry["difference_B_minus_A"] = result["difference_B_minus_A"]
            update_count += 1
            alpha = GA.alpha_for_update(update_count)
            old = scores[FLORIDA_REGION]
            new = (1 - alpha) * old + alpha * result["A_rating"]
            entry["update"] = {
                "region": FLORIDA_REGION, "name": name_of[FLORIDA_REGION],
                "iso3": ISO3, "update_number": update_count, "alpha": alpha,
                "rating": result["A_rating"], "old_score": old, "new_score": new,
            }
            update_history.append({
                "iteration": iteration, "partner_region": b_region,
                "partner_name": name_of[b_region], "model": model_key,
                "rating": result["A_rating"], "alpha": alpha,
                "old_score": old, "new_score": new,
                "update_number": update_count,
            })
            scores[FLORIDA_REGION] = new
        iterations.append(entry)
        write_history()
        print(f"  {iteration}/{n_pairings} partner={name_of[b_region]} model={model_key} "
              f"status={result['status']} "
              + (f"A_rating={result['A_rating']} florida_score={scores[FLORIDA_REGION]!r} "
                 if result["status"] == "ok" else "")
              + f"running cost {total} USD", flush=True)

    n_ok = sum(1 for e in iterations if e["status"] == "ok")
    n_rejected = len(iterations) - n_ok
    status_by_model = {}
    cost_by_model = {}
    ratings_by_model = {}
    for e in iterations:
        status_by_model.setdefault(e["model"], Counter())[e["status"]] += 1
        if "cost_usd" in e:
            cost_by_model[e["model"]] = cost_by_model.get(e["model"], Decimal("0")) + Decimal(e["cost_usd"])
        if e["status"] == "ok":
            ratings_by_model.setdefault(e["model"], []).append(e["A_rating"])
    ledger = {
        "run_id": run_id,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "instrument": "single-rating-anchored-v4-structured (combined A/B, seeded reseed recalibration)",
        "effort": "medium",
        "attempts_per_pairing": 1,
        "seed": seed,
        "florida_region": FLORIDA_REGION,
        "florida_sid": FLORIDA_SID,
        "seed_value": seed_value,
        "seed_rule": "median of the other 18 URY ADM1 final_running_scores in analysis/global_adm1_iterative.json",
        "provenance": provenance,
        "sibling_finals_frozen": sibling_finals,
        "candidate_rule": "nearest max(int(0.10*n_iso3),3) capped at n_iso3-1 siblings within the global-run URY pairing group by current running score (siblings frozen), tie-break region id",
        "models": models,
        "model_balancing": "least-used model for this reseed run so far; ties by seeded shuffle",
        "system_sha256": V4.sha(system),
        "base_system_sha256": V4.sha(base_system),
        "n_pairings_planned": n_pairings,
        "n_pairings": len(iterations),
        "n_ok": n_ok,
        "n_rejected": n_rejected,
        "status_by_model": {m: dict(c) for m, c in status_by_model.items()},
        "cost_by_model_usd": {m: str(v) for m, v in cost_by_model.items()},
        "total_usd": str(total),
        "update_schedule": "Florida only, per-update number: updates 1-20 0.80*old+0.20*new (all 8 here); siblings frozen",
        "final_score": scores[FLORIDA_REGION],
        "summary": [{k: e[k] for k in ("iteration", "model", "status", "A_region", "B_region")}
                    | ({"cost_usd": e["cost_usd"]} if "cost_usd" in e else {})
                    for e in iterations],
    }
    (run_dir / "ledger.json").write_text(
        json.dumps(ledger, indent=1, ensure_ascii=False), encoding="utf-8")

    aggregate = {
        "run_id": run_id,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "instrument": ledger["instrument"],
        "effort": "medium",
        "seed": seed,
        "florida_region": FLORIDA_REGION,
        "florida_sid": FLORIDA_SID,
        "seed_value": seed_value,
        "seed_rule": ledger["seed_rule"],
        "provenance": provenance,
        "sibling_finals_frozen": sibling_finals,
        "candidate_rule": ledger["candidate_rule"],
        "models": models,
        "model_balancing": ledger["model_balancing"],
        "model_usage": {m: int(model_usage[FLORIDA_REGION].get(m, 0)) for m in models},
        "system_sha256": V4.sha(system),
        "base_system_sha256": V4.sha(base_system),
        "n_pairings": len(iterations),
        "n_ok": n_ok,
        "n_rejected": n_rejected,
        "status_by_model": ledger["status_by_model"],
        "florida_ratings_by_model": ratings_by_model,
        "cost_by_model_usd": ledger["cost_by_model_usd"],
        "total_usd": str(total),
        "update_schedule": ledger["update_schedule"],
        "update_count": update_count,
        "update_history": update_history,
        "final_score": scores[FLORIDA_REGION],
        "drift_final_minus_seed": scores[FLORIDA_REGION] - seed_value,
        "pair_history": iterations,
    }
    AGGREGATE_PATH.write_text(json.dumps(aggregate, indent=1, ensure_ascii=False),
                              encoding="utf-8")
    print(f"done: seed_value={seed_value!r} ok={n_ok} rejected={n_rejected} "
          f"final_score={scores[FLORIDA_REGION]!r} exact cost {total} USD; "
          f"artifacts in {run_dir}; aggregate {AGGREGATE_PATH}", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default=RUN_ID_DEFAULT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--n-pairings", type=int, default=N_PAIRINGS)
    a = ap.parse_args()
    return run(a.run_id, dry_run=a.dry_run, seed=a.seed, n_pairings=a.n_pairings)


if __name__ == "__main__":
    sys.exit(main())
