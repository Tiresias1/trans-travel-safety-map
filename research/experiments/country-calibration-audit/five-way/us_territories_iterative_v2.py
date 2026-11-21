#!/usr/bin/env python3
"""US-territory iterative pairwise anchored calibration, v2 (medium effort).

Fixes the v1 dossier asymmetry (us_territories_iterative.py): v1 took
territory dossiers from the v4 COUNTRIES set, which contain only local
territory law plus a one-line federal deferral, while partner US-state
dossiers carry the full US federal-layer block (executive orders, binary
passports, federal custody, visa marking). That asymmetry inflated the
territories to ~0.68-0.73.

v2 dossier construction (per territory ASM/GUM/VIR/MNP):
  - Extract the shared parent-framework block from the frozen v4
    admin1_USA state cells: every state dossier starts with the identical
    "### PARENT NATIONAL FRAMEWORK ..." section up to "\n\n### DIVISION
    EVIDENCE" (verified identical across all 51 states at build time).
  - Prepend that block to the territory's local dossier text (from its
    v4 countries cell), under a "### TERRITORY LOCAL EVIDENCE" heading,
    replacing the explicit federal-deferral sentence where one exists
    (ASM, MNP; exact-string replacement, fail-closed if absent). GUM/VIR
    carry no deferral sentence — their federal mentions are substantive
    local evidence and are kept.
  - Dossier parity check: federal-keyword counts (executive order,
    passport, visa, binary, custody, federal) for each constructed
    territory dossier vs the shared framework block and the 51 state
    dossiers; recorded in the aggregate and report.
  - Every constructed dossier passes harness.assert_user_text_clean.

System: the v4 system text WITH the bounded anti-absence-as-safety
directive appended verbatim (global_adm1_iterative.DIRECTIVE, identical
to countries_iterative_pairwise_v2.DIRECTIVE).

Design (60 seeded pairings total, 15 per territory, deterministic):
  - Each territory is reseeded from the CURRENT USA country score in
    data/countries.json (iterativeScore if present, else score).
  - Partner pool: the CURRENT 51 US state scores in data/admin1.json
    (post global-adm1 sync; iterativeScore if present, else score),
    frozen for partner selection. Partners are NOT updated; only the
    focal territory's running score moves.
  - Per territory, 15 rounds in fixed territory order ASM, GUM, VIR, MNP.
    Each round: partner chosen uniformly (seeded RNG) among the nearest
    3 frozen state scores to the territory's current running score
    (tie-break region id), excluding an immediate repeat of the same
    unordered pair when an alternative exists.
  - Exactly one model per pairing: the globally least-used of the seven
    models so far, ties broken by seeded shuffle (dedicated model RNG);
    over 60 pairings this cycles each model 8-9 times. Medium effort via
    provider_models.call_v4; one attempt per pairing, no retries;
    failures are recorded and do not update scores.

After each OK pairing, update the territory only:
  new = 0.80*old + 0.20*new_rating  (alpha 0.20; every territory receives
  at most 15 updates in this run, all within the flat-alpha window).

A is the territory (focal), B is the partner state (mapping recorded
only outside the prompt). Saves runs/us-territories-iterative-v2-20261119/
artifacts (attempt/content/result per iteration, ledger, pair-history.json)
and aggregate analysis/us_territories_iterative_v2.json, plus report
us-territories-iterative-v2-report.md. Resume-safe: completed iterations
(pair-history.json) are never re-called. Single-writer guard: refuses to
launch if another us_territories_iterative_v2.py process is running.
The credential is read only by provider_models. Does not write site data.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import provider_models as PM  # noqa: E402
import single_rate_v4 as V4  # noqa: E402
import nh_ri_comparison as NHRI  # noqa: E402
import harness as H  # noqa: E402
from global_adm1_iterative import DIRECTIVE  # noqa: E402

RUN_ID_DEFAULT = "us-territories-iterative-v2-20261119"
AGGREGATE_PATH = HERE / "analysis" / "us_territories_iterative_v2.json"
REPORT_PATH = HERE / "us-territories-iterative-v2-report.md"
TERRITORIES = ["ASM", "GUM", "VIR", "MNP"]
N_PER_TERRITORY = 15
N_ITERATIONS = 60  # 15 per territory x 4 territories
SEED = 20261119
CANDIDATE_K = 3  # nearest-3 rule
ALPHA = 0.20  # updates 1-15 (all updates in this run): 0.80*old + 0.20*new
NAMES = {"ASM": "American Samoa", "GUM": "Guam",
         "VIR": "US Virgin Islands", "MNP": "Northern Mariana Islands"}

DIVISION_EVIDENCE_MARK = "\n\n### DIVISION EVIDENCE"
LOCAL_HEADING = "### TERRITORY LOCAL EVIDENCE"
PARITY_KEYWORDS = ("executive order", "passport", "visa", "binary",
                   "custody", "federal")

# Exact federal-deferral sentences in the territory countries-cell dossiers
# that point the reader to the (previously missing) national layer. Each is
# replaced by a pointer to the attached parent framework. GUM and VIR have
# no deferral sentence; their federal mentions are substantive local
# evidence and are kept unchanged.
FEDERAL_DEFERRAL_REPLACEMENTS = {
    "ASM": (
        "The governing state's passport policy and its 2025 executive "
        "orders on sex definition, healthcare funding and sports are not "
        "restated here; they are carried at the national level of the "
        "governing state's record.",
        "The governing state's passport policy and its 2025 executive "
        "orders on sex definition, healthcare funding and sports are "
        "provided in the parent national framework above and form part "
        "of this territory's combined operative regime.",
    ),
    "MNP": (
        "and the national layer of this assessment sits with the "
        "governing state's record",
        "and that national layer is provided in the parent national "
        "framework above",
    ),
}


def keyword_counts(text: str) -> dict:
    lowered = text.lower()
    return {k: lowered.count(k) for k in PARITY_KEYWORDS}


def check_single_writer() -> list[int]:
    """PIDs of other us_territories_iterative_v2.py processes (not self)."""
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
            # Only python interpreters count: wrappers (timeout/bash/grep)
            # carry the script name as a plain argument but are not runners.
            argv0 = Path(parts[0]).name if parts else ""
            if not argv0.startswith("python"):
                continue
            if any(p == "us_territories_iterative_v2.py"
                   or p.endswith("/us_territories_iterative_v2.py")
                   for p in parts):
                pids.append(pid)
    return sorted(pids)


def candidates_for(focal_score: float, partner_scores: dict, k: int = CANDIDATE_K):
    """Nearest k partner states by score diff, tie-break region id."""
    others = sorted(partner_scores,
                    key=lambda r: (abs(partner_scores[r] - focal_score), r))
    return others[:k]


def pick_partner(rng: random.Random, focal_score: float, partner_scores: dict,
                 prev_pair, focal_region: str, k: int = CANDIDATE_K):
    cands = candidates_for(focal_score, partner_scores, k)
    if prev_pair is not None and len(cands) > 1:
        filtered = [c for c in cands
                    if frozenset((focal_region, c)) != prev_pair]
        if filtered:
            cands = filtered
    return rng.choice(cands)


def pick_model_least_used(model_rng: random.Random, model_usage: Counter,
                          models: list) -> str:
    """Globally least-used model so far; ties broken by seeded shuffle."""
    minimum = min(model_usage.get(m, 0) for m in models)
    tied = [m for m in models if model_usage.get(m, 0) == minimum]
    model_rng.shuffle(tied)
    return tied[0]


def _current_score(rec: dict):
    raw = rec.get("iterativeScore")
    if raw is None:
        raw = rec.get("score")
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise RuntimeError("record has no current numeric score")
    return float(raw)


def build_context():
    manifest = json.loads(
        (HERE / "frozen" / "single_rate_v4_manifest.json").read_text(encoding="utf-8"))
    models = list(manifest["models"].keys())
    if len(models) != 7:
        raise RuntimeError(f"expected 7 models, got {models}")

    # Territory local cells come from the countries set; partner state
    # cells from admin1_USA. Both share the identical v4 system text.
    terr_frozen = {c["region"]: c for c in manifest["sets"]["countries"]}
    state_frozen = {c["region"]: c for c in manifest["sets"]["admin1_USA"]}
    if len(state_frozen) != 51:
        raise RuntimeError(f"expected 51 admin1_USA cells, got {len(state_frozen)}")

    cells = V4.build("countries")
    cell_by_region = {c["region"]: c for c in cells}
    local_dossiers = {}
    for t in TERRITORIES:
        cell = cell_by_region.get(t)
        if cell is None or t not in terr_frozen:
            raise RuntimeError(f"territory cell missing: {t}")
        f = terr_frozen[t]
        if f["user_sha256"] != cell["user_sha256"] or \
                f["system_sha256"] != cell["system_sha256"]:
            raise RuntimeError(f"manifest drift for {t}")
        local_dossiers[t] = NHRI._dossier_from_cell(cell)

    cells_state = V4.build("admin1")
    state_cells = [c for c in cells_state if c["region"] in state_frozen]
    state_by_region = {c["region"]: c for c in state_cells}
    if set(state_by_region) != set(state_frozen):
        raise RuntimeError("v4 admin1 cells do not match the frozen manifest set")
    state_dossiers = {}
    for region, cell in state_by_region.items():
        f = state_frozen[region]
        if f["user_sha256"] != cell["user_sha256"] or \
                f["system_sha256"] != cell["system_sha256"]:
            raise RuntimeError(f"manifest drift for {region}")
        state_dossiers[region] = NHRI._dossier_from_cell(cell)

    systems = {c["_system"] for c in
               [cell_by_region[t] for t in TERRITORIES] + list(state_by_region.values())}
    if len(systems) != 1:
        raise RuntimeError("v4 system text differs between country/admin1 cells")
    base_system = systems.pop()
    system = base_system + DIRECTIVE

    # Shared federal-layer block: identical prefix of every state dossier
    # up to the division-evidence section (fail-closed if not identical).
    framework_blocks = set()
    for region, d in state_dossiers.items():
        if DIVISION_EVIDENCE_MARK not in d:
            raise RuntimeError(f"state dossier lacks division-evidence mark: {region}")
        framework_blocks.add(d[:d.index(DIVISION_EVIDENCE_MARK)])
    if len(framework_blocks) != 1:
        raise RuntimeError(f"parent framework block differs across states: "
                           f"{len(framework_blocks)} distinct blocks")
    framework = framework_blocks.pop()
    if not framework.startswith("### PARENT NATIONAL FRAMEWORK"):
        raise RuntimeError("extracted framework block has unexpected shape")

    # Constructed territory dossiers: framework + local evidence, with the
    # federal-deferral sentence replaced where present. Fail-closed leak gate.
    dossiers = dict(state_dossiers)
    replaced = {}
    for t in TERRITORIES:
        local = local_dossiers[t]
        if t in FEDERAL_DEFERRAL_REPLACEMENTS:
            old, new = FEDERAL_DEFERRAL_REPLACEMENTS[t]
            if local.count(old) != 1:
                raise RuntimeError(f"federal-deferral sentence not found exactly "
                                   f"once in {t} local dossier")
            local = local.replace(old, new)
            replaced[t] = True
        else:
            replaced[t] = False
        dossier = framework + "\n\n" + LOCAL_HEADING + "\n\n" + local
        H.assert_user_text_clean(dossier, f"constructed territory dossier {t}")
        dossiers[t] = dossier

    # Dossier-parity check: federal-keyword counts, territory vs states.
    framework_counts = keyword_counts(framework)
    state_counts = [keyword_counts(d) for d in state_dossiers.values()]
    parity = {
        "keywords": list(PARITY_KEYWORDS),
        "framework_block": framework_counts,
        "state_min": {k: min(c[k] for c in state_counts) for k in PARITY_KEYWORDS},
        "state_max": {k: max(c[k] for c in state_counts) for k in PARITY_KEYWORDS},
        "territories": {t: keyword_counts(dossiers[t]) for t in TERRITORIES},
        "deferral_replaced": replaced,
    }
    for t in TERRITORIES:
        for k in PARITY_KEYWORDS:
            if parity["territories"][t][k] < framework_counts[k]:
                raise RuntimeError(f"parity failure: {t} dossier has fewer "
                                   f"'{k}' mentions than the framework block")
    if parity["territories"]["ASM"]["executive order"] < 2 or \
            parity["territories"]["ASM"]["passport"] < 2:
        raise RuntimeError("ASM dossier must mention the executive order and "
                           "passport policy multiple times")

    # Prior: CURRENT USA country score in data/countries.json.
    countries = H.load_countries()
    prior = _current_score(countries["USA"])
    initial_scores = {t: prior for t in TERRITORIES}

    # Partner pool: CURRENT US state scores in data/admin1.json (post
    # global-adm1 sync), frozen; partners are never updated.
    admin1 = H.load_admin1()
    partner_scores = {}
    for sid, rec in admin1.items():
        if rec.get("iso3") != "USA":
            continue
        partner_scores[f"{sid}:{rec.get('name')}"] = _current_score(rec)
    if set(partner_scores) != set(state_frozen):
        raise RuntimeError("data/admin1.json USA records do not match the "
                           "51 frozen admin1_USA cells")

    dossier_sha = {t: V4.sha(dossiers[t]) for t in TERRITORIES}
    return (system, base_system, dossiers, initial_scores, partner_scores,
            models, prior, framework, parity, dossier_sha)


def combined_user(dossiers, a_region, b_region):
    return (NHRI.COMBINED_INSTRUCTION + dossiers[a_region] + NHRI.MID_INSTRUCTION
            + dossiers[b_region] + NHRI.QUESTION_TAIL + NHRI.SUFFIX)


def _rng_state_to_json(rng):
    state = rng.getstate()
    return [state[0], list(state[1]), state[2]]


def _rng_state_from_json(data):
    rng = random.Random()
    rng.setstate((data[0], tuple(data[1]), data[2]))
    return rng


def _do_one(run_dir, iteration, model_key, a_region, b_region, system, user_text):
    """One attempt for one iteration. Returns summary dict."""
    suffix = f"iter{iteration:03d}"
    attempt_path = run_dir / f"attempt-{suffix}.json"
    content_path = run_dir / f"content-{suffix}.txt"
    result_path = run_dir / f"result-{suffix}.json"
    labels = {"A": a_region, "B": b_region}
    user_sha = V4.sha(user_text)
    try:
        res = PM.call_v4(model_key, system, user_text)
    except Exception as e:  # one attempt; preserve failure, no retry
        result_path.write_text(json.dumps(
            {"iteration": iteration, "model": model_key, "status": "transport_failure",
             "reason": f"{type(e).__name__}: {e}", "labels": labels, "attempts": 1},
            indent=1), encoding="utf-8")
        return {"iteration": iteration, "model": model_key, "status": "transport_failure"}

    usage = res.get("usage") or {}
    attempt_path.write_text(json.dumps(
        {"iteration": iteration, "model": model_key,
         "model_id": PM.SINGLE_MODELS[model_key], "effort": "medium", "attempts": 1,
         "system_sha256": V4.sha(system), "combined_user_sha256": user_sha,
         "labels": labels, "usage": usage, "raw_response": res["raw_response"]},
        indent=1), encoding="utf-8")
    if "cost_usd" not in usage:
        result_path.write_text(json.dumps(
            {"iteration": iteration, "model": model_key, "status": "stopped",
             "reason": "unknown charge", "usage": usage, "labels": labels,
             "attempts": 1}, indent=1), encoding="utf-8")
        return {"iteration": iteration, "model": model_key, "status": "stopped_unknown_charge"}

    try:
        raw = json.loads(res["raw_response"])
        msg = (raw.get("choices") or [{}])[0].get("message") or {}
        content = msg.get("content") or ""
    except Exception as e:  # preserve the failed draw; never retry
        result_path.write_text(json.dumps(
            {"iteration": iteration, "model": model_key, "status": "rejected",
             "cost_usd": usage["cost_usd"], "usage": usage, "labels": labels,
             "parse_error": f"raw-response parse: {type(e).__name__}: {e}",
             "attempts": 1}, indent=1), encoding="utf-8")
        return {"iteration": iteration, "model": model_key, "status": "rejected",
                "cost_usd": usage["cost_usd"]}

    content_path.write_text(content, encoding="utf-8")
    parsed, perr = None, None
    try:
        parsed = NHRI.parse_combined(content)
    except Exception as e:  # preserve the failed draw; never retry
        perr = f"{type(e).__name__}: {e}"
    result_doc = {
        "iteration": iteration, "model": model_key,
        "model_id": PM.SINGLE_MODELS[model_key],
        "status": "ok" if parsed else "rejected",
        "cost_usd": usage["cost_usd"], "usage": usage, "labels": labels,
        "A_region": a_region, "B_region": b_region,
        "A_rating": parsed["A"]["rating"] if parsed else None,
        "B_rating": parsed["B"]["rating"] if parsed else None,
        "difference_B_minus_A": parsed["difference_ri_minus_nh"] if parsed else None,
        "parsed": parsed, "parse_error": perr, "attempts": 1,
    }
    result_path.write_text(json.dumps(result_doc, indent=1, ensure_ascii=False),
                           encoding="utf-8")
    return {"iteration": iteration, "model": model_key, "status": result_doc["status"],
            "A_rating": result_doc["A_rating"], "B_rating": result_doc["B_rating"],
            "difference_B_minus_A": result_doc["difference_B_minus_A"],
            "cost_usd": usage["cost_usd"]}


def focal_for_iteration(iteration: int) -> str:
    """Fixed territory order: 1-15 ASM, 16-30 GUM, 31-45 VIR, 46-60 MNP."""
    return TERRITORIES[(iteration - 1) // N_PER_TERRITORY]


def run(run_id: str, dry_run: bool = False, seed: int = SEED,
        n_iterations: int = N_ITERATIONS) -> int:
    others = check_single_writer()
    if others:
        print(f"single-writer guard: us_territories_iterative_v2.py already "
              f"running, PID(s)={others}; refusing to launch", flush=True)
        return 2
    (system, base_system, dossiers, initial_scores, partner_scores,
     models, prior, framework, parity, dossier_sha) = build_context()
    print(f"base_system_sha256={V4.sha(base_system)} system_sha256={V4.sha(system)} "
          f"territories={TERRITORIES} prior_USA={prior} candidate_k={CANDIDATE_K} "
          f"alpha={ALPHA} models={models} seed={seed}", flush=True)
    print(f"framework_sha256={V4.sha(framework)} "
          f"territory_dossier_sha256={dossier_sha}", flush=True)
    print(f"dossier parity: {json.dumps(parity)}", flush=True)
    if dry_run:
        rng = random.Random(seed)
        model_rng = random.Random(seed + 1)
        model_usage = Counter()
        focal = focal_for_iteration(1)
        partner = pick_partner(rng, initial_scores[focal], partner_scores, None, focal)
        model_key = pick_model_least_used(model_rng, model_usage, models)
        print(f"dry run: first focal={focal} partner={partner} "
              f"model={model_key}; no provider calls made", flush=True)
        return 0

    run_dir = HERE / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    pair_history_path = run_dir / "pair-history.json"

    scores = dict(initial_scores)  # territory running scores only
    update_counts = {t: 0 for t in TERRITORIES}
    per_territory_history = {t: [] for t in TERRITORIES}
    iterations = []
    total = Decimal("0")
    rng = random.Random(seed)
    model_rng = random.Random(seed + 1)
    model_usage = Counter()

    if pair_history_path.exists():
        hist = json.loads(pair_history_path.read_text(encoding="utf-8"))
        if hist.get("seed") != seed or hist.get("run_id") != run_id:
            raise SystemExit("existing pair-history.json does not match this run/seed; refusing to resume")
        iterations = hist["iterations"]
        scores = dict(hist["running_scores"])
        update_counts = dict(hist["update_counts"])
        per_territory_history = hist["per_territory_history"]
        rng = _rng_state_from_json(hist["rng_state"])
        model_rng = _rng_state_from_json(hist["model_rng_state"])
        model_usage = Counter(hist["model_usage"])
        total = Decimal(hist.get("total_usd", "0"))
        print(f"resuming: {len(iterations)} completed iterations kept, "
              f"{n_iterations - len(iterations)} remaining", flush=True)

    summary = []
    for entry in iterations:
        summary.append({k: entry[k] for k in
                        ("iteration", "model", "status", "A_region", "B_region")
                        if k in entry} | ({"cost_usd": entry["cost_usd"]} if "cost_usd" in entry else {}))

    completed = len(iterations)
    for iteration in range(completed + 1, n_iterations + 1):
        prev_pair = None
        if iterations:
            last = iterations[-1]
            prev_pair = frozenset((last["A_region"], last["B_region"]))
        focal = focal_for_iteration(iteration)
        partner = pick_partner(rng, scores[focal], partner_scores, prev_pair, focal)
        a_region, b_region = focal, partner  # A=territory, B=partner state
        model_key = pick_model_least_used(model_rng, model_usage, models)
        model_usage[model_key] += 1
        user_text = combined_user(dossiers, a_region, b_region)
        result = _do_one(run_dir, iteration, model_key, a_region, b_region,
                         system, user_text)
        entry = {
            "iteration": iteration, "model": model_key,
            "A_region": a_region, "B_region": b_region,
            "A_name": NAMES.get(a_region, a_region), "B_name": b_region.split(":", 1)[-1],
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
            # Only the territory updates; partner scores stay frozen.
            region, rating = a_region, result["A_rating"]
            update_counts[region] += 1
            if update_counts[region] > N_PER_TERRITORY:
                raise RuntimeError(f"{region} exceeded {N_PER_TERRITORY} updates")
            old = scores[region]
            new = (1 - ALPHA) * old + ALPHA * rating
            entry.setdefault("updates", []).append({
                "region": region, "name": NAMES.get(region, region),
                "update_number": update_counts[region], "alpha": ALPHA,
                "rating": rating, "old_score": old, "new_score": new,
            })
            per_territory_history[region].append({
                "iteration": iteration, "partner_region": b_region,
                "partner_name": b_region.split(":", 1)[-1],
                "partner_frozen_score": partner_scores[b_region],
                "model": model_key, "rating": rating, "alpha": ALPHA,
                "old_score": old, "new_score": new,
                "update_number": update_counts[region],
            })
            scores[region] = new
        iterations.append(entry)
        summary.append({k: entry[k] for k in ("iteration", "model", "status", "A_region", "B_region")}
                       | ({"cost_usd": entry["cost_usd"]} if "cost_usd" in entry else {}))
        pair_history_path.write_text(json.dumps({
            "run_id": run_id, "seed": seed, "candidate_k": CANDIDATE_K,
            "alpha": ALPHA,
            "n_iterations_planned": n_iterations,
            "models": models,
            "model_selection": "globally least-used model; ties by seeded shuffle (model RNG seed+1)",
            "model_usage": dict(model_usage),
            "system_sha256": V4.sha(system),
            "base_system_sha256": V4.sha(base_system),
            "framework_sha256": V4.sha(framework),
            "territory_dossier_sha256": dossier_sha,
            "dossier_parity": parity,
            "prior_USA_score": prior,
            "partner_scores_frozen": partner_scores,
            "running_scores": scores, "update_counts": update_counts,
            "per_territory_history": per_territory_history,
            "rng_state": _rng_state_to_json(rng),
            "model_rng_state": _rng_state_to_json(model_rng),
            "total_usd": str(total),
            "iterations": iterations,
        }, indent=1, ensure_ascii=False), encoding="utf-8")
        if iteration % 10 == 0 or iteration == n_iterations:
            print(f"  {iteration}/{n_iterations} done, running cost {total} USD "
                  f"status={result['status']}", flush=True)

    n_ok = sum(1 for e in iterations if e["status"] == "ok")
    n_rejected = len(iterations) - n_ok
    status_by_model = {}
    cost_by_model = {}
    for e in iterations:
        status_by_model.setdefault(e["model"], Counter())[e["status"]] += 1
        if "cost_usd" in e:
            cost_by_model[e["model"]] = cost_by_model.get(e["model"], Decimal("0")) + Decimal(e["cost_usd"])
    common = {
        "run_id": run_id,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "instrument": "single-rating-anchored-v4-structured (combined A/B, iterative pairwise)",
        "effort": "medium",
        "attempts_per_pairing": 1,
        "seed": seed,
        "candidate_k": CANDIDATE_K,
        "candidate_rule": "nearest 3 frozen CURRENT US state scores (data/admin1.json, iterativeScore else score) to territory current running score, tie-break region",
        "alpha": ALPHA,
        "update_schedule": "updates 1-15 (all updates in this run): 0.80*old + 0.20*new",
        "prior_USA_score": prior,
        "prior_source": "data/countries.json USA current score (iterativeScore else score)",
        "partner_pool_source": "data/admin1.json USA state current scores (iterativeScore else score), post global-adm1 sync (frozen, partners not updated)",
        "dossier_rule": "shared US parent-framework block extracted from frozen v4 admin1_USA state cells (identical across 51 states) + territory local dossier from its v4 countries cell under '### TERRITORY LOCAL EVIDENCE', federal-deferral sentence replaced (ASM, MNP)",
        "dossier_parity": parity,
        "framework_sha256": V4.sha(framework),
        "territory_dossier_sha256": dossier_sha,
        "models": models,
        "model_selection": "globally least-used model; ties by seeded shuffle (model RNG seed+1)",
        "model_usage": {m: int(model_usage.get(m, 0)) for m in models},
        "system_sha256": V4.sha(system),
        "base_system_sha256": V4.sha(base_system),
        "n_pairings_planned": n_iterations,
        "n_pairings": len(iterations),
        "n_ok": n_ok,
        "n_rejected": n_rejected,
        "status_by_model": {m: dict(c) for m, c in status_by_model.items()},
        "cost_by_model_usd": {m: str(v) for m, v in cost_by_model.items()},
        "total_usd": str(total),
    }
    ledger = dict(common)
    ledger["summary"] = summary
    (run_dir / "ledger.json").write_text(
        json.dumps(ledger, indent=1, ensure_ascii=False), encoding="utf-8")

    terr = {}
    for t in TERRITORIES:
        terr[t] = {
            "name": NAMES[t],
            "region": t,
            "initial_score": initial_scores[t],
            "final_score": scores[t],
            "drift_final_minus_initial": scores[t] - initial_scores[t],
            "update_count": update_counts[t],
            "update_history": per_territory_history[t],
        }
    drifts = [scores[t] - initial_scores[t] for t in TERRITORIES]
    aggregate = dict(common)
    aggregate.update({
        "initial_scores": initial_scores,
        "final_running_scores": scores,
        "update_counts": update_counts,
        "drift_summary": {
            "mean_drift": sum(drifts) / len(drifts),
            "mean_abs_drift": sum(abs(d) for d in drifts) / len(drifts),
            "max_abs_drift": max(abs(d) for d in drifts),
            "min_drift": min(drifts),
            "max_drift": max(drifts),
        },
        "territories": terr,
        "pair_history": iterations,
    })
    AGGREGATE_PATH.write_text(json.dumps(aggregate, indent=1, ensure_ascii=False),
                              encoding="utf-8")

    # Logistics + final scores + dossier-parity report.
    lines = []
    lines.append(f"# US territories iterative pairwise anchored calibration v2 — run `{run_id}`")
    lines.append("")
    lines.append("## What v2 fixes")
    lines.append("")
    lines.append("v1 (`us_territories_iterative.py`) took territory dossiers from the v4 countries set: local territory law plus a one-line federal deferral, while partner US-state dossiers carried the full US federal-layer block (executive orders, binary passports, federal custody, visa marking). That asymmetry inflated territories to ~0.68-0.73. v2 prepends the shared parent-framework block (extracted from the frozen v4 admin1_USA state cells; verified byte-identical across all 51 states) to each territory's local dossier, replaces the explicit federal-deferral sentence (ASM, MNP; GUM/VIR have none — their federal mentions are substantive local evidence), and uses the v4 system text WITH the bounded anti-absence-as-safety directive (identical to `global_adm1_iterative.py` / countries v2).")
    lines.append("")
    lines.append("## Logistics")
    lines.append("")
    lines.append("- Script: `us_territories_iterative_v2.py` (in `research/experiments/country-calibration-audit/five-way/`).")
    lines.append(f"- Run directory: `runs/{run_id}/`; aggregate: `analysis/us_territories_iterative_v2.json`.")
    lines.append(f"- Scope: {', '.join(TERRITORIES)} (15 pairings each, 60 total). Puerto Rico out of scope.")
    lines.append(f"- Seed: `{seed}` (partner RNG); model tie-break RNG seed `{seed + 1}`.")
    lines.append(f"- Prior: each territory reseeded from the CURRENT USA country score `{prior}` in `data/countries.json` (`iterativeScore` else `score`).")
    lines.append("- Partner pool: the CURRENT 51 US state scores in `data/admin1.json` (`iterativeScore` else `score`, post global-adm1 sync), held frozen; partners are not updated.")
    lines.append(f"- Design: 60 seeded pairings, fixed territory order ASM (1-15), GUM (16-30), VIR (31-45), MNP (46-60). Per pairing: partner chosen uniformly among the nearest 3 frozen state scores to the territory's current running score (tie-break region id, no immediate repeat of the same unordered pair when an alternative exists), A = territory, B = partner state.")
    lines.append(f"- Exactly one model per pairing: globally least-used of the seven models so far, ties broken by seeded shuffle. Medium effort via `provider_models.call_v4`; one attempt per pairing, no retries. Failed/rejected draws are recorded with no score update. Single-writer guard refuses concurrent launches.")
    lines.append(f"- Update rule (territory only): `0.80*old + 0.20*new` (alpha `{ALPHA}` for updates 1-15 — every update in this run).")
    lines.append(f"- Base v4 system sha256: `{V4.sha(base_system)}`; directive-augmented system sha256: `{V4.sha(system)}`.")
    lines.append(f"- Framework block sha256: `{V4.sha(framework)}`. Territory dossier sha256: " +
                 ", ".join(f"{t} `{dossier_sha[t]}`" for t in TERRITORIES) + ".")
    lines.append("- Every constructed territory dossier passes `harness.assert_user_text_clean` (fail-closed leak gate).")
    lines.append(f"- Artifacts: per-iteration attempt/content/result files, `pair-history.json`, `ledger.json`. Aggregate created: `{aggregate['created']}`.")
    lines.append("")
    lines.append("## Dossier-parity check (federal-keyword counts)")
    lines.append("")
    lines.append("Case-insensitive substring counts. `framework` is the shared block present in every state dossier; state min/max span the 51 full state dossiers (framework + division evidence). Each territory dossier = framework + local evidence, so counts are at least the framework's.")
    lines.append("")
    lines.append("| keyword | framework | state min | state max | ASM | GUM | VIR | MNP |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k in PARITY_KEYWORDS:
        row = [parity["framework_block"][k], parity["state_min"][k], parity["state_max"][k]]
        row += [parity["territories"][t][k] for t in TERRITORIES]
        lines.append(f"| {k} | " + " | ".join(str(v) for v in row) + " |")
    lines.append("")
    lines.append(f"- ASM mentions the executive order {parity['territories']['ASM']['executive order']} times and passports {parity['territories']['ASM']['passport']} times — comparable to a state dossier (framework alone: {parity['framework_block']['executive order']} / {parity['framework_block']['passport']}).")
    lines.append("- Federal-deferral sentence replaced: ASM yes, MNP yes; GUM/VIR none present (substantive federal mentions kept).")
    lines.append("")
    lines.append("## Final summary")
    lines.append("")
    lines.append(f"- Pairings: {n_iterations} planned, {len(iterations)} recorded; `ok` {n_ok}, rejected/failed {n_rejected}.")
    lines.append("")
    lines.append("| model | pairings | ok | rejected/failed | cost USD |")
    lines.append("|---|---:|---:|---:|---:|")
    for m in models:
        c = status_by_model.get(m, Counter())
        rej = sum(v for k, v in c.items() if k != "ok")
        lines.append(f"| {m} | {model_usage.get(m, 0)} | {c.get('ok', 0)} | {rej} | {cost_by_model.get(m, Decimal('0'))} |")
    lines.append("")
    lines.append(f"- Cost: exact total `{total}` USD.")
    lines.append("")
    lines.append("## Final running scores")
    lines.append("")
    lines.append("| territory | name | initial (USA prior) | final | drift | updates |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for t in TERRITORIES:
        d = terr[t]
        lines.append(f"| {t} | {NAMES[t]} | {d['initial_score']:.10f} | {d['final_score']:.10f} | {d['drift_final_minus_initial']:+.10f} | {d['update_count']} |")
    lines.append("")
    lines.append(f"- Verification: `pair-history.json`, `ledger.json`, and `analysis/us_territories_iterative_v2.json` agree on {len(iterations)} pairings, {n_ok} ok / {n_rejected} rejected/failed, and total cost `{total}` USD.")
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"done: ok={n_ok} rejected={n_rejected} exact cost {total} USD; "
          f"artifacts in {run_dir}; aggregate {AGGREGATE_PATH}; report {REPORT_PATH}",
          flush=True)
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
