#!/usr/bin/env python3
"""Rerate the four Russian-occupied Ukrainian regions under the RUSSIAN
parent regime (one seeded pass, 32 pairings).

Bug being fixed: Crimea, Sevastopol, Donetsk Oblast and Luhansk Oblast are
UKR records in data/admin1.json, so the global ADM1 run rendered them under
the UKRAINIAN parent framework plus a tiny stub. Their operative regime is
the RUSSIAN one. This script reassesses each exactly once under:

  dossier = the RUSSIAN national-framework block (exactly as rendered by
  harness.render_admin1_dossier for RUS admin1 records, verified identical
  across all RUS dossiers) PLUS the region's own neutralized local
  occupation evidence (its freshly researched blindSummary, run through
  global_adm1_iterative.neutralize). Construction is fail-closed: the
  framework must contain the Russian propaganda-law / extremism-designation
  / transition-ban content, the local evidence must contain occupation
  evidence and pass the local-differentiator rule, and an identity-leak
  scan must find no region/country names or ISO3 codes.

Mechanics (reusing global_adm1_iterative machinery):
  - system text: v4 system + bounded anti-absence-as-safety DIRECTIVE
    (pinned sha256 3f6af3f8f757a108afe5d87362d576cf6cbe7308a9e4d4f97a8f6a29facc5e56);
  - combined A/B format (nh_ri_comparison instructions), A = occupied
    region, B = Russian partner; partner dossiers are byte-identical to the
    global run's (parent framework + blind fields + neutralized
    summary+blindSummary local evidence via global build_context);
  - seed: each occupied region starts at the RUS country score from
    data/countries.json (iterativeScore if present, else score);
  - partner pool: RUS ADM1 regions' FINAL scores from
    analysis/global_adm1_iterative.json, frozen (never updated);
  - 32 seeded pairings (seed 20261119), exactly 8 per region: the focal
    order is the four regions repeated 8 times, shuffled by the seeded RNG
    (first draw); partner = nearest 3 RUS regions by current running score
    of the focal (tie-break region id), picked uniformly, no immediate
    repeat of the same unordered pair when an alternative exists;
  - exactly ONE model per pairing via provider_models.call_v4 at medium
    effort: per-focal least-used model across the seven models (ties by
    seeded shuffle, dedicated model RNG seeded seed+99);
  - one attempt per pairing, no retries; failures recorded, no update;
  - only the occupied region (A) is updated: alpha 0.20 for updates 1-8
    (0.80*old + 0.20*new); partners stay frozen.

Artifacts: runs/occupied-ukraine-rerate-20261119/ (attempt/content/result
per iteration, dossiers.json, ledger.json, pair-history.json), aggregate
analysis/occupied_ukraine_rerate.json, report
occupied-ukraine-rerate-report.md. Resume-safe: completed iterations
(pair-history.json) are never re-called. Single-writer guard: refuses to
launch if another occupied_ukraine_rerate.py process is running. The
credential is read only by provider_models. Does not write site data or
data/admin1.json.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import single_rate_v4 as V4  # noqa: E402
import harness as H  # noqa: E402
import global_adm1_iterative as G  # noqa: E402

RUN_ID_DEFAULT = "occupied-ukraine-rerate-20261119"
AGGREGATE_PATH = HERE / "analysis" / "occupied_ukraine_rerate.json"
REPORT_PATH = HERE / "occupied-ukraine-rerate-report.md"
GLOBAL_AGGREGATE_PATH = HERE / "analysis" / "global_adm1_iterative.json"
SEED = 20261119
N_ITERATIONS = 32
PAIRINGS_PER_REGION = 8
ALPHA = 0.20  # updates 1-8 (all updates in this run)
CANDIDATE_K = 3
EXPECTED_SYSTEM_SHA = "3f6af3f8f757a108afe5d87362d576cf6cbe7308a9e4d4f97a8f6a29facc5e56"
OPERATIVE_PARENT = "RUS"

# The four occupied UKR records, in fixed order (focal-order shuffle is seeded).
OCCUPIED_IDS = (
    "14850775B24260608407062",  # Autonomous Republic of Crimea
    "14850775B70667807354554",  # Sevastopol
    "14850775B15615817748403",  # Donetsk Oblast
    "14850775B31033086218351",  # Luhansk Oblast
)

FRAMEWORK_SEP = "\n\n### DIVISION EVIDENCE"
LOCAL_HEADER = "\n\n### DIVISION LOCAL EVIDENCE\n"

# Identity-leak scan for the constructed occupied dossiers (fail closed).
_LEAK_RE = re.compile(
    r"\b(?:russ\w*|ukrain\w*|crimea\w*|sevastopol\w*|donetsk\w*|luhansk\w*"
    r"|DPR|LPR|UKR|RUS|kyiv|kiev)\b", re.I)


def check_single_writer() -> list[int]:
    """PIDs of other occupied_ukraine_rerate.py processes (excluding self)."""
    pids = []
    proc = Path("/proc")
    if proc.is_dir():
        for entry in proc.iterdir():
            if not entry.name.isdigit():
                continue
            pid = int(entry.name)
            if pid == __import__("os").getpid():
                continue
            try:
                raw = (entry / "cmdline").read_bytes()
            except OSError:
                continue
            if not raw:
                continue
            parts = [p.decode("utf-8", "replace") for p in raw.split(b"\x00") if p]
            # Only python interpreters count: wrappers (timeout/bash/grep)
            # carry the script name as a plain argument but are not runners.
            argv0 = Path(parts[0]).name if parts else ""
            if not (argv0.startswith("python")):
                continue
            if any(p == "occupied_ukraine_rerate.py"
                   or p.endswith("/occupied_ukraine_rerate.py")
                   for p in parts):
                pids.append(pid)
    return sorted(pids)


def candidates_for(focal: str, running_scores: dict, partner_scores: dict):
    """Nearest CANDIDATE_K frozen RUS partners by focal's running score."""
    others = sorted(partner_scores,
                    key=lambda r: (abs(partner_scores[r] - running_scores[focal]), r))
    return others[:CANDIDATE_K]


def pick_partner(rng: random.Random, focal: str, running_scores: dict,
                 partner_scores: dict, prev_pair):
    cands = candidates_for(focal, running_scores, partner_scores)
    if not cands:
        raise RuntimeError(f"no RUS partner for {focal}")
    if prev_pair is not None and len(cands) > 1:
        filtered = [c for c in cands if frozenset((focal, c)) != prev_pair]
        if filtered:
            cands = filtered
    return rng.choice(cands)


def build_context():
    """System, dossiers, seeds, frozen partner pool, parity checks."""
    (system, base_system, g_regions, _focal_pool, _groups, iso_of,
     name_of, g_dossiers, _initial, models, manifest, _scope) = G.build_context()
    if V4.sha(system) != EXPECTED_SYSTEM_SHA:
        raise RuntimeError("directive-augmented v4 system sha drifted from "
                           f"{EXPECTED_SYSTEM_SHA}: {V4.sha(system)}")

    admin1 = H.load_admin1()
    countries = H.load_countries()

    # RUSSIAN national-framework block, exactly as rendered for RUS admin1
    # records by harness.render_admin1_dossier (via the global machinery).
    rus_regions = sorted(r for r in g_regions if iso_of[r] == OPERATIVE_PARENT)
    if not rus_regions:
        raise RuntimeError("no RUS regions in global context")
    frames = set()
    for r in rus_regions:
        d = g_dossiers[r]
        if not d.startswith("### PARENT NATIONAL FRAMEWORK"):
            raise RuntimeError(f"unexpected RUS dossier shape for {r}")
        frames.add(d.split(FRAMEWORK_SEP)[0])
    if len(frames) != 1:
        raise RuntimeError("RUS parent-framework blocks are not identical "
                           "across RUS admin1 dossiers")
    rus_framework = frames.pop()
    framework_sha = V4.sha(rus_framework)

    # Fail-closed content check: the Russian operative-regime content.
    low = rus_framework.lower()
    rus_content_checks = {
        "propaganda_law": "propaganda" in low,
        "extremism_designation": "extremist" in low,
        "transition_ban": ("gender reassignment surgery" in low
                           and "2023" in low),
    }
    if not all(rus_content_checks.values()):
        raise RuntimeError(f"RUS framework missing operative-regime content: "
                           f"{rus_content_checks}")

    raw_rus_score = countries[OPERATIVE_PARENT].get("iterativeScore")
    if raw_rus_score is None:
        raw_rus_score = countries[OPERATIVE_PARENT].get("score")
    if isinstance(raw_rus_score, bool) or not isinstance(raw_rus_score, (int, float)):
        raise RuntimeError("RUS country record has no numeric score")
    seed_score = float(raw_rus_score)

    # Frozen partner pool: RUS ADM1 final scores from the global aggregate.
    global_agg = json.loads(GLOBAL_AGGREGATE_PATH.read_text(encoding="utf-8"))
    partner_scores = {}
    for r in rus_regions:
        if r not in global_agg["final_running_scores"]:
            raise RuntimeError(f"RUS region {r} missing from global aggregate")
        partner_scores[r] = float(global_agg["final_running_scores"][r])

    # Occupied-region dossiers: RUS framework + neutralized local blindSummary.
    occupied = []
    dossiers = dict(g_dossiers)  # partner dossiers byte-identical to global run
    initial_scores = {}
    previous_global_scores = {}
    local_checks = {}
    for sid in OCCUPIED_IDS:
        rec = admin1.get(sid)
        if not isinstance(rec, dict) or rec.get("iso3") != "UKR":
            raise RuntimeError(f"occupied record {sid} is not a UKR record")
        name = rec.get("name")
        region = f"{sid}:{name}"
        blind = str(rec.get("blindSummary") or "")
        if not H.clean(blind):
            raise RuntimeError(f"{region} has no blindSummary local evidence")
        score_vals = [rec.get("score"), rec.get("iterativeScore"),
                      countries["UKR"].get("score"),
                      countries["UKR"].get("iterativeScore"),
                      countries[OPERATIVE_PARENT].get("score"),
                      countries[OPERATIVE_PARENT].get("iterativeScore")]
        local = G.neutralize(blind, name, "UKR",
                             countries["UKR"].get("name") or "", score_vals)
        dossier = rus_framework + LOCAL_HEADER + local
        leaks = sorted(set(m.group(0) for m in _LEAK_RE.finditer(dossier)))
        checks = {
            "local_words": len(local.split()),
            "occupation_evidence": "occup" in local.lower(),
            "local_differentiator": G.has_local_differentiator(local, rus_framework),
            "identity_leaks": leaks,
            "framework_sha256": V4.sha(dossier.split(LOCAL_HEADER)[0]),
        }
        if not checks["occupation_evidence"]:
            raise RuntimeError(f"{region}: local evidence lacks occupation content")
        if not checks["local_differentiator"]:
            raise RuntimeError(f"{region}: local evidence fails differentiator rule")
        if leaks:
            raise RuntimeError(f"{region}: identity leak in constructed dossier: {leaks}")
        if checks["framework_sha256"] != framework_sha:
            raise RuntimeError(f"{region}: framework parity broken")
        local_checks[region] = checks
        occupied.append(region)
        initial_scores[region] = seed_score
        prev = rec.get("iterativeScore")
        if prev is None:
            prev = rec.get("score")
        previous_global_scores[region] = prev
        dossiers[region] = dossier

    parity = {
        "rus_framework_sha256": framework_sha,
        "n_rus_dossiers_checked": len(rus_regions),
        "all_rus_framework_blocks_identical": True,
        "occupied_framework_parity": True,
        "rus_content_checks": rus_content_checks,
        "local_checks": local_checks,
        "dossier_rule": "RUS parent-framework block (render_admin1_dossier, "
                        "identical across all RUS dossiers) + neutralized "
                        "blindSummary local occupation evidence",
    }
    return (system, base_system, occupied, dossiers, initial_scores,
            previous_global_scores, partner_scores, models, manifest,
            name_of, parity, seed_score)


def run(run_id: str, dry_run: bool = False, seed: int = SEED,
        n_iterations: int = N_ITERATIONS) -> int:
    others = check_single_writer()
    if others:
        print(f"single-writer guard: occupied_ukraine_rerate.py already running, "
              f"PID(s)={others}; refusing to launch", flush=True)
        return 2
    (system, base_system, occupied, dossiers, initial_scores,
     previous_global_scores, partner_scores, models, manifest,
     name_of, parity, seed_score) = build_context()
    print(f"system_sha256={V4.sha(system)} base_system_sha256={V4.sha(base_system)} "
          f"rus_framework_sha256={parity['rus_framework_sha256']} "
          f"seed_score(RUS country)={seed_score} partners={len(partner_scores)} "
          f"models={models} seed={seed}", flush=True)
    for region in occupied:
        print(f"  occupied dossier {region}: sha256={V4.sha(dossiers[region])} "
              f"local_checks={parity['local_checks'][region]}", flush=True)

    # Focal schedule: each region exactly PAIRINGS_PER_REGION times, seeded
    # shuffle as the FIRST draw of the main RNG (recomputed identically on
    # resume; partner picks then continue from the restored RNG state).
    focal_order = [r for r in occupied for _ in range(PAIRINGS_PER_REGION)]
    rng = random.Random(seed)
    rng.shuffle(focal_order)
    model_rng = random.Random(seed + 99)

    if dry_run:
        scores = dict(initial_scores)
        usage = {r: Counter() for r in occupied}
        focal = focal_order[0]
        partner = pick_partner(rng, focal, scores, partner_scores, None)
        model_key = G.pick_model_balanced(model_rng, focal, usage, models)
        print(f"dry run: n_pairings={n_iterations} focal_order={focal_order}; "
              f"first pairing A={focal} B={partner} model={model_key}; "
              f"parity={parity['rus_content_checks']}; no provider calls made",
              flush=True)
        return 0

    run_dir = HERE / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    pair_history_path = run_dir / "pair-history.json"
    (run_dir / "dossiers.json").write_text(json.dumps({
        "seed": seed,
        "system_sha256": V4.sha(system),
        "dossier_parity": parity,
        "occupied_dossier_sha256": {r: V4.sha(dossiers[r]) for r in occupied},
        "occupied_dossiers": {r: dossiers[r] for r in occupied},
    }, indent=1, ensure_ascii=False), encoding="utf-8")

    scores = dict(initial_scores)
    update_counts = {r: 0 for r in occupied}
    per_region_history = {r: [] for r in occupied}
    model_usage = {r: Counter() for r in occupied}
    iterations = []
    total = Decimal("0")

    if pair_history_path.exists():
        hist = json.loads(pair_history_path.read_text(encoding="utf-8"))
        if hist.get("seed") != seed or hist.get("run_id") != run_id:
            raise SystemExit("existing pair-history.json does not match this "
                             "run/seed; refusing to resume")
        iterations = hist["iterations"]
        scores = dict(hist["running_scores"])
        update_counts = dict(hist["update_counts"])
        per_region_history = hist["per_region_history"]
        rng = G._rng_state_from_json(hist["rng_state"])
        model_rng = G._rng_state_from_json(hist["model_rng_state"])
        model_usage = {r: Counter(hist["model_usage"][r]) for r in occupied}
        total = Decimal(hist.get("total_usd", "0"))
        print(f"resuming: {len(iterations)} completed iterations kept, "
              f"{n_iterations - len(iterations)} remaining", flush=True)

    completed = len(iterations)
    for iteration in range(completed + 1, n_iterations + 1):
        prev_pair = None
        if iterations:
            last = iterations[-1]
            prev_pair = frozenset((last["A_region"], last["B_region"]))
        focal = focal_order[iteration - 1]
        partner = pick_partner(rng, focal, scores, partner_scores, prev_pair)
        a_region, b_region = focal, partner  # A=occupied focal, B=RUS partner
        model_key = G.pick_model_balanced(model_rng, focal, model_usage, models)
        model_usage[focal][model_key] += 1
        user_text = G.combined_user(dossiers, a_region, b_region)
        result = G._do_one(run_dir, iteration, model_key, a_region, b_region,
                           system, user_text)
        entry = {
            "iteration": iteration, "model": model_key,
            "A_region": a_region, "B_region": b_region,
            "A_name": name_of[a_region], "B_name": name_of[b_region],
            "A_operative_parent": OPERATIVE_PARENT, "B_iso3": OPERATIVE_PARENT,
            "status": result["status"],
            "combined_user_sha256": V4.sha(user_text),
        }
        if "cost_usd" in result:
            entry["cost_usd"] = result["cost_usd"]
            total += Decimal(result["cost_usd"])
        if result["status"] == "ok":
            entry["A_rating"] = result["A_rating"]
            entry["B_rating"] = result["B_rating"]
            entry["difference_B_minus_A"] = result["difference_B_minus_A"]
            # Update ONLY the occupied region; the RUS partner stays frozen.
            update_counts[a_region] += 1
            if update_counts[a_region] > PAIRINGS_PER_REGION:
                raise RuntimeError(f"{a_region} exceeded {PAIRINGS_PER_REGION} updates")
            old = scores[a_region]
            new = (1 - ALPHA) * old + ALPHA * result["A_rating"]
            entry["updates"] = [{
                "region": a_region, "name": name_of[a_region],
                "update_number": update_counts[a_region], "alpha": ALPHA,
                "rating": result["A_rating"], "old_score": old, "new_score": new,
            }]
            per_region_history[a_region].append({
                "iteration": iteration, "partner_region": b_region,
                "partner_name": name_of[b_region], "model": model_key,
                "rating": result["A_rating"], "alpha": ALPHA,
                "old_score": old, "new_score": new,
                "update_number": update_counts[a_region],
            })
            scores[a_region] = new
        iterations.append(entry)
        pair_history_path.write_text(json.dumps({
            "run_id": run_id, "seed": seed,
            "n_iterations_planned": n_iterations,
            "focal_order": focal_order,
            "models": models,
            "model_balancing": "per-focal least-used across the seven models; ties by seeded shuffle",
            "system_sha256": V4.sha(system),
            "base_system_sha256": V4.sha(base_system),
            "dossier_parity": parity,
            "running_scores": scores, "update_counts": update_counts,
            "per_region_history": per_region_history,
            "model_usage": {r: dict(model_usage[r]) for r in occupied},
            "rng_state": G._rng_state_to_json(rng),
            "model_rng_state": G._rng_state_to_json(model_rng),
            "total_usd": str(total),
            "iterations": iterations,
        }, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  {iteration}/{n_iterations} A={a_region} B={b_region} "
              f"model={model_key} status={result['status']} "
              f"running cost {total} USD", flush=True)

    n_ok = sum(1 for e in iterations if e["status"] == "ok")
    n_rejected = len(iterations) - n_ok
    status_by_model = {}
    cost_by_model = {}
    per_model_ratings = []
    for e in iterations:
        status_by_model.setdefault(e["model"], Counter())[e["status"]] += 1
        if "cost_usd" in e:
            cost_by_model[e["model"]] = (cost_by_model.get(e["model"], Decimal("0"))
                                         + Decimal(e["cost_usd"]))
        if e["status"] == "ok":
            per_model_ratings.append({
                "iteration": e["iteration"], "model": e["model"],
                "region": e["A_region"], "rating": e["A_rating"],
                "partner_region": e["B_region"], "partner_rating": e["B_rating"],
            })
    model_usage_serial = {r: {m: int(model_usage[r].get(m, 0)) for m in models}
                          for r in occupied}
    ledger = {
        "run_id": run_id,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "instrument": "single-rating-anchored-v4-structured (combined A/B, iterative pairwise)",
        "effort": "medium",
        "attempts_per_pairing": 1,
        "seed": seed,
        "occupied_regions": occupied,
        "operative_parent": OPERATIVE_PARENT,
        "seed_score_rus_country": seed_score,
        "candidate_rule": f"nearest {CANDIDATE_K} frozen RUS partners by focal running score, tie-break region id",
        "models": models,
        "model_balancing": "per-focal least-used across the seven models; ties by seeded shuffle",
        "system_sha256": V4.sha(system),
        "base_system_sha256": V4.sha(base_system),
        "dossier_parity": parity,
        "n_pairings_planned": n_iterations,
        "n_pairings": len(iterations),
        "n_ok": n_ok,
        "n_rejected": n_rejected,
        "status_by_model": {m: dict(c) for m, c in status_by_model.items()},
        "cost_by_model_usd": {m: str(v) for m, v in cost_by_model.items()},
        "total_usd": str(total),
        "update_schedule": {"updates_1_8": "0.80*old+0.20*new (occupied region only)"},
        "summary": [{k: e[k] for k in ("iteration", "model", "status",
                                       "A_region", "B_region") if k in e}
                    | ({"cost_usd": e["cost_usd"]} if "cost_usd" in e else {})
                    for e in iterations],
    }
    (run_dir / "ledger.json").write_text(
        json.dumps(ledger, indent=1, ensure_ascii=False), encoding="utf-8")

    regions_doc = {}
    for r in occupied:
        regions_doc[r] = {
            "name": name_of[r],
            "record_iso3": "UKR",
            "operative_parent": OPERATIVE_PARENT,
            "seed_score_rus_country": initial_scores[r],
            "final_score": scores[r],
            "drift_final_minus_seed": scores[r] - initial_scores[r],
            "previous_global_ukr_framework_score": previous_global_scores[r],
            "update_count": update_counts[r],
            "update_history": per_region_history[r],
            "model_usage": model_usage_serial[r],
            "dossier_sha256": V4.sha(dossiers[r]),
        }
    aggregate = {
        "run_id": run_id,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "instrument": "single-rating-anchored-v4-structured (combined A/B, iterative pairwise)",
        "effort": "medium",
        "seed": seed,
        "purpose": "rerate the four Russian-occupied Ukrainian regions under the "
                   "RUSSIAN operative parent regime plus local occupation evidence "
                   "(fixes the UKR-framework + stub rendering in the global run)",
        "occupied_regions": regions_doc,
        "partner_pool_frozen_scores": partner_scores,
        "partner_pool_source": "analysis/global_adm1_iterative.json final_running_scores (RUS only)",
        "candidate_rule": f"nearest {CANDIDATE_K} frozen RUS partners by focal running score, tie-break region id",
        "models": models,
        "model_balancing": "per-focal least-used across the seven models; ties by seeded shuffle",
        "system_sha256": V4.sha(system),
        "base_system_sha256": V4.sha(base_system),
        "dossier_parity": parity,
        "n_pairings": len(iterations),
        "n_ok": n_ok,
        "n_rejected": n_rejected,
        "status_by_model": {m: dict(c) for m, c in status_by_model.items()},
        "cost_by_model_usd": {m: str(v) for m, v in cost_by_model.items()},
        "total_usd": str(total),
        "per_model_ratings": per_model_ratings,
        "pair_history": iterations,
    }
    AGGREGATE_PATH.write_text(json.dumps(aggregate, indent=1, ensure_ascii=False),
                              encoding="utf-8")

    # Report: logistics + final scores + per-model ratings + cost + parity.
    lines = []
    lines.append(f"# Occupied-Ukraine rerate under the Russian parent regime — report ({run_id})")
    lines.append("")
    lines.append("## Logistics")
    lines.append("")
    lines.append(f"- Script: `occupied_ukraine_rerate.py`; run artifacts: `runs/{run_id}/`; "
                 f"aggregate: `analysis/occupied_ukraine_rerate.json`.")
    lines.append(f"- Bug fixed: the four occupied regions are UKR records, so the global "
                 f"run rendered the UKRAINIAN parent framework + a tiny stub. Here each "
                 f"is assessed under the RUSSIAN operative regime plus its local "
                 f"occupation evidence.")
    lines.append(f"- Dossiers: the RUS national-framework block exactly as rendered by "
                 f"`harness.render_admin1_dossier` for RUS admin1 records (verified "
                 f"identical across all {parity['n_rus_dossiers_checked']} RUS dossiers) "
                 f"PLUS the region's own neutralized local evidence (its freshly "
                 f"researched `blindSummary` through `global_adm1_iterative.neutralize`). "
                 f"Partner (B) dossiers are byte-identical to the global run's.")
    lines.append(f"- Seed: {seed}; {n_iterations} pairings, exactly {PAIRINGS_PER_REGION} "
                 f"per region (focal order = regions x{PAIRINGS_PER_REGION}, seeded "
                 f"shuffle). A = occupied region, B = Russian partner.")
    lines.append(f"- Initial score per region: RUS country score from "
                 f"`data/countries.json` = {seed_score}. Partner pool: RUS ADM1 final "
                 f"scores from `analysis/global_adm1_iterative.json` "
                 f"({len(partner_scores)} regions), frozen. Candidate partners: nearest "
                 f"{CANDIDATE_K} by focal's current running score, tie-break region id; "
                 f"no immediate repeat of the same unordered pair when an alternative exists.")
    lines.append(f"- Effort: medium via `provider_models.call_v4`; exactly one model per "
                 f"pairing, per-focal least-used across the seven models (ties by seeded "
                 f"shuffle); attempts per pairing: 1; retries: none; failed draws "
                 f"recorded with no score update. Models ({len(models)}): {', '.join(models)}.")
    lines.append(f"- Updates: occupied region ONLY, alpha {ALPHA} for updates 1-8 "
                 f"(`0.80*old + 0.20*new`); partners never updated.")
    lines.append(f"- Base v4 system sha256: `{V4.sha(base_system)}`; directive-augmented "
                 f"system sha256: `{V4.sha(system)}` (bounded anti-absence-as-safety "
                 f"directive, pinned).")
    lines.append(f"- Single-writer guard: refuses to launch if another "
                 f"`occupied_ukraine_rerate.py` process is running. Resume-safe: "
                 f"completed iterations are never re-called. Site data not modified.")
    lines.append("")
    lines.append("## Dossier-parity check")
    lines.append("")
    lines.append(f"- RUS framework block sha256: `{parity['rus_framework_sha256']}`; "
                 f"identical across all {parity['n_rus_dossiers_checked']} RUS admin1 "
                 f"dossiers; each occupied dossier embeds exactly this block "
                 f"(framework parity: {parity['occupied_framework_parity']}).")
    lines.append(f"- Russian operative-regime content present: "
                 f"propaganda law: {parity['rus_content_checks']['propaganda_law']}; "
                 f"extremism designation: {parity['rus_content_checks']['extremism_designation']}; "
                 f"2023 transition ban: {parity['rus_content_checks']['transition_ban']}.")
    lines.append("")
    lines.append("| Region | Local words | Occupation evidence | Differentiator | Identity leaks |")
    lines.append("|---|---|---|---|---|")
    for r in occupied:
        c = parity["local_checks"][r]
        lines.append(f"| {name_of[r]} | {c['local_words']} | {c['occupation_evidence']} "
                     f"| {c['local_differentiator']} | {len(c['identity_leaks'])} |")
    lines.append("")
    lines.append("## Final scores (seeded at the RUS country score)")
    lines.append("")
    lines.append(f"- OK pairings: {n_ok}; rejected/failed: {n_rejected} "
                 f"(failures recorded, no update).")
    lines.append("")
    lines.append("| Region | Seed (RUS) | Final | Drift | Updates | Previous (UKR-framework) score |")
    lines.append("|---|---|---|---|---|---|")
    for r in occupied:
        d = regions_doc[r]
        lines.append(f"| {d['name']} | {d['seed_score_rus_country']:.6f} "
                     f"| {d['final_score']:.6f} | {d['drift_final_minus_seed']:+.6f} "
                     f"| {d['update_count']} | {d['previous_global_ukr_framework_score']} |")
    lines.append("")
    lines.append("## Per-model ratings (A = occupied region)")
    lines.append("")
    lines.append("| Iter | Model | Region | A rating | B partner | B rating |")
    lines.append("|---|---|---|---|---|---|")
    for e in iterations:
        if e["status"] == "ok":
            lines.append(f"| {e['iteration']} | {e['model']} | {e['A_name']} "
                         f"| {e['A_rating']} | {e['B_name']} | {e['B_rating']} |")
        else:
            lines.append(f"| {e['iteration']} | {e['model']} | {e['A_name']} "
                         f"| {e['status']} | {e['B_name']} | — |")
    lines.append("")
    lines.append("## Cost")
    lines.append("")
    lines.append(f"- Total cost (exact): {total} USD.")
    lines.append("")
    lines.append("| Model | OK | Rejected/failed | Cost USD |")
    lines.append("|---|---|---|---|")
    for m in models:
        st = status_by_model.get(m, {})
        ok_m = st.get("ok", 0)
        rej_m = sum(v for k, v in st.items() if k != "ok")
        lines.append(f"| {m} | {ok_m} | {rej_m} | {cost_by_model.get(m, '0')} |")
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"done: ok={n_ok} rejected={n_rejected} exact cost {total} USD; "
          f"artifacts in {run_dir}; aggregate {AGGREGATE_PATH}; report {REPORT_PATH}",
          flush=True)
    for r in occupied:
        print(f"  FINAL {name_of[r]}: {scores[r]:.6f} "
              f"(seed {initial_scores[r]}, updates {update_counts[r]})", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default=RUN_ID_DEFAULT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--n-iterations", type=int, default=N_ITERATIONS)
    a = ap.parse_args()
    return run(a.run_id, dry_run=a.dry_run, seed=a.seed, n_iterations=a.n_iterations)


if __name__ == "__main__":
    sys.exit(main())
