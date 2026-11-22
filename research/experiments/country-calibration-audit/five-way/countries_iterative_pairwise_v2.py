#!/usr/bin/env python3
"""Iterative pairwise anchored calibration for countries, v2 (medium effort).

Starts from the 233 country cells in frozen/single_rate_v4_manifest.json
(`sets.countries`) and initial scores from
analysis/countries_iterative_pairwise.json (`final_running_scores`).
Reuses the combined A/B anchored pairwise machinery
(normal v4 rubric/system/anchors, A/B anonymised, rate both while keeping
partner in mind).

The v4 system text is augmented by a short directive appended verbatim
(DIRECTIVE below): severe LGB signals are operative when trans-specific data
is absent, de facto armed-group enforcement is operative, denied same-sex
conduct does not imply invulnerability, absence of a documented exact
pathway is not mitigating evidence, and parent-level instruments apply to every
division unless affirmative evidence shows they do not reach this division
(absence of a division-level record is NOT evidence of non-application, and
'not inherited' reasoning is forbidden).

Loops 720 pairings (seeded, deterministic):
  - pick a random focal country (seeded RNG);
  - candidate partners are the nearest 23 countries by CURRENT running score,
    tie-break by country code;
  - pick uniformly among candidates (seeded RNG), excluding an immediate
    repeat of the same unordered pair unless there is no other candidate;
  - pick exactly ONE model per pairing with per-country balancing: for the
    focal (A) country, choose the least-used model for that country so far,
    where usage counts pairings in which the country participated in either
    slot; ties are broken by seeded shuffle (dedicated model RNG);
  - call the model once via provider_models.call_v4 at medium effort;
    one attempt per pairing, no retries; if a call fails, record it and
    continue without updating scores.

After each OK pairing, update BOTH participants with the running-average
schedule (per-country update number, 1-indexed):
  updates 1-20:  0.80*old + 0.20*new
  updates 21-25: 0.92*old + 0.08*new
  updates 26+:   0.95*old + 0.05*new

A is the focal country, B is the partner (mapping recorded only outside the
prompt). Saves runs/countries-iterative-pairwise-v2-20261116/ artifacts
(attempt/content/result per iteration, ledger, pair-history.json) and
aggregate analysis/countries_iterative_pairwise_v2.json plus
countries-iterative-pairwise-v2-report.md. Resume-safe: completed iterations
(pair-history.json) are never re-called.
The credential is read only by provider_models. Does not write live site
scores or data/countries.json.
"""
from __future__ import annotations

import argparse
import json
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

RUN_ID_DEFAULT = "countries-iterative-pairwise-v2-20261116"
V1_AGGREGATE_PATH = HERE / "analysis" / "countries_iterative_pairwise.json"
AGGREGATE_PATH = HERE / "analysis" / "countries_iterative_pairwise_v2.json"
REPORT_PATH = HERE / "countries-iterative-pairwise-v2-report.md"
N_ITERATIONS = 720
SEED = 20261116
N_COUNTRIES = 233
CANDIDATE_K = max(int(0.10 * N_COUNTRIES), 5)  # = 23

DIRECTIVE = (
    "\n\n## Additional methodological directive\n\n"
    "(1) When trans-specific data is absent but the LGB signal is severe "
    "(capital law, documented executions, armed-group enforcement, "
    "taboo/stigma, no recourse), the LGB signal IS the operative signal and "
    "must be weighted as such; legal ambiguity does NOT create safety. "
    "(2) In regions where a non-state armed group is the de facto authority, "
    "treat its enforcement as the operative regime. "
    "(3) A trans person discovered/outs by a hostile actor cannot be assumed "
    "invulnerable because they deny same-sex conduct. "
    "(4) Absence of a documented exact pathway is not mitigating evidence. "
    "(5) Parent-level instruments apply to every division unless affirmative "
    "evidence shows they do not reach this division; absence of a "
    "division-level record is NOT evidence of non-application, and "
    "'not inherited' reasoning is forbidden."
)


def alpha_for_update(update_number: int) -> float:
    """Step size for a country's update_number-th update (1-indexed)."""
    if update_number <= 20:
        return 0.20
    if update_number <= 25:
        return 0.08
    return 0.05


def candidates_for(focal: str, scores: dict, k: int = CANDIDATE_K):
    """Nearest k other countries by current score, tie-break country code."""
    others = [r for r in scores if r != focal]
    others.sort(key=lambda r: (abs(scores[r] - scores[focal]), r))
    return others[:k]


def pick_partner(rng: random.Random, focal: str, scores: dict,
                 prev_pair, k: int = CANDIDATE_K):
    cands = candidates_for(focal, scores, k)
    if prev_pair is not None and len(cands) > 1:
        filtered = [c for c in cands if frozenset((focal, c)) != prev_pair]
        if filtered:
            cands = filtered
    return rng.choice(cands)


def pick_model_balanced(model_rng: random.Random, focal: str,
                        model_usage: dict, models: list) -> str:
    """Least-used model for focal so far; ties broken by seeded shuffle.

    model_usage[country] is a Counter over models counting pairings in which
    the country participated (either slot) by assigned model.
    """
    counts = model_usage[focal]
    minimum = min(counts.get(m, 0) for m in models)
    tied = [m for m in models if counts.get(m, 0) == minimum]
    model_rng.shuffle(tied)
    return tied[0]


def build_context():
    manifest = json.loads(
        (HERE / "frozen" / "single_rate_v4_manifest.json").read_text(encoding="utf-8"))
    frozen = manifest["sets"]["countries"]
    regions = [c["region"] for c in frozen]
    if len(regions) != 233:
        raise RuntimeError(f"expected 233 manifest countries cells, got {len(regions)}")
    frozen_by_region = {c["region"]: c for c in frozen}
    cells = V4.build("countries")
    cells = [c for c in cells if c["region"] in frozen_by_region]
    cell_by_region = {c["region"]: c for c in cells}
    if set(cell_by_region) != set(regions):
        raise RuntimeError("v4 country cells do not match the frozen manifest set")
    for c in cells:
        f = frozen_by_region[c["region"]]
        if f["user_sha256"] != c["user_sha256"] or f["system_sha256"] != c["system_sha256"]:
            raise RuntimeError(f"manifest drift for {c['region']}")
    systems = {c["_system"] for c in cells}
    if len(systems) != 1:
        raise RuntimeError("v4 system text differs between country cells")
    base_system = systems.pop()
    system = base_system + DIRECTIVE
    v1 = json.loads(V1_AGGREGATE_PATH.read_text(encoding="utf-8"))
    initial_scores = v1["final_running_scores"]
    if set(initial_scores) != set(regions):
        raise RuntimeError("v1 final_running_scores do not cover the 233 regions")
    dossiers = {r: NHRI._dossier_from_cell(cell_by_region[r]) for r in regions}
    models = list(manifest["models"].keys())
    if len(models) != 7:
        raise RuntimeError(f"expected 7 models, got {models}")
    return system, base_system, regions, dossiers, initial_scores, models, manifest


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

    raw = json.loads(res["raw_response"])
    msg = (raw.get("choices") or [{}])[0].get("message") or {}
    content = msg.get("content") or ""
    usage = res.get("usage") or {}
    attempt_path.write_text(json.dumps(
        {"iteration": iteration, "model": model_key,
         "model_id": PM.SINGLE_MODELS[model_key], "effort": "medium", "attempts": 1,
         "system_sha256": V4.sha(system), "combined_user_sha256": user_sha,
         "labels": labels, "usage": usage, "raw_response": res["raw_response"]},
        indent=1), encoding="utf-8")
    content_path.write_text(content, encoding="utf-8")
    if "cost_usd" not in usage:
        result_path.write_text(json.dumps(
            {"iteration": iteration, "model": model_key, "status": "stopped",
             "reason": "unknown charge", "usage": usage, "labels": labels,
             "attempts": 1}, indent=1), encoding="utf-8")
        return {"iteration": iteration, "model": model_key, "status": "stopped_unknown_charge"}

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


def run(run_id: str, dry_run: bool = False, seed: int = SEED,
        n_iterations: int = N_ITERATIONS) -> int:
    system, base_system, regions, dossiers, initial_scores, models, manifest = build_context()
    print(f"base_system_sha256={V4.sha(base_system)} system_sha256={V4.sha(system)} "
          f"countries={len(regions)} candidate_k={CANDIDATE_K} models={models} seed={seed}")
    if dry_run:
        rng = random.Random(seed)
        model_rng = random.Random(seed + 99)
        model_usage = {r: Counter() for r in regions}
        focal = rng.choice(regions)
        partner = pick_partner(rng, focal, initial_scores, None)
        model_key = pick_model_balanced(model_rng, focal, model_usage, models)
        print(f"dry run: first focal={focal} partner={partner} model={model_key}; "
              f"no provider calls made")
        return 0

    run_dir = HERE / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    pair_history_path = run_dir / "pair-history.json"

    scores = dict(initial_scores)
    update_counts = {r: 0 for r in regions}
    per_country_history = {r: [] for r in regions}
    model_usage = {r: Counter() for r in regions}
    iterations = []
    total = Decimal("0")
    rng = random.Random(seed)
    model_rng = random.Random(seed + 99)

    if pair_history_path.exists():
        hist = json.loads(pair_history_path.read_text(encoding="utf-8"))
        if hist.get("seed") != seed or hist.get("run_id") != run_id:
            raise SystemExit("existing pair-history.json does not match this run/seed; refusing to resume")
        iterations = hist["iterations"]
        scores = dict(hist["running_scores"])
        update_counts = dict(hist["update_counts"])
        per_country_history = hist["per_state_history"]
        rng = _rng_state_from_json(hist["rng_state"])
        model_rng = _rng_state_from_json(hist["model_rng_state"])
        model_usage = {r: Counter(hist["model_usage"][r])
                       for r in regions}
        total = Decimal(hist.get("total_usd", "0"))
        print(f"resuming: {len(iterations)} completed iterations kept, "
              f"{n_iterations - len(iterations)} remaining")

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
        focal = rng.choice(regions)
        partner = pick_partner(rng, focal, scores, prev_pair)
        a_region, b_region = focal, partner  # A=focal, B=partner
        model_key = pick_model_balanced(model_rng, focal, model_usage, models)
        for r in (a_region, b_region):
            model_usage[r][model_key] += 1
        user_text = combined_user(dossiers, a_region, b_region)
        result = _do_one(run_dir, iteration, model_key, a_region, b_region,
                         system, user_text)
        entry = {
            "iteration": iteration, "model": model_key,
            "A_region": a_region, "B_region": b_region,
            "A_name": a_region.split(":", 1)[-1], "B_name": b_region.split(":", 1)[-1],
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
            for region, rating in ((a_region, result["A_rating"]),
                                   (b_region, result["B_rating"])):
                update_counts[region] += 1
                alpha = alpha_for_update(update_counts[region])
                old = scores[region]
                new = (1 - alpha) * old + alpha * rating
                entry.setdefault("updates", []).append({
                    "region": region, "name": region.split(":", 1)[-1],
                    "update_number": update_counts[region], "alpha": alpha,
                    "rating": rating, "old_score": old, "new_score": new,
                })
                per_country_history[region].append({
                    "iteration": iteration, "partner_region": b_region if region == a_region else a_region,
                    "partner_name": (b_region if region == a_region else a_region).split(":", 1)[-1],
                    "model": model_key, "rating": rating, "alpha": alpha,
                    "old_score": old, "new_score": new,
                    "update_number": update_counts[region],
                })
                scores[region] = new
        iterations.append(entry)
        summary.append({k: entry[k] for k in ("iteration", "model", "status", "A_region", "B_region")}
                       | ({"cost_usd": entry["cost_usd"]} if "cost_usd" in entry else {}))
        pair_history_path.write_text(json.dumps({
            "run_id": run_id, "seed": seed, "candidate_k": CANDIDATE_K,
            "n_iterations_planned": n_iterations,
            "models": models,
            "model_balancing": "per-focal least-used (participations, either slot); ties by seeded shuffle",
            "system_sha256": V4.sha(system),
            "base_system_sha256": V4.sha(base_system),
            "running_scores": scores, "update_counts": update_counts,
            "per_state_history": per_country_history,
            "model_usage": {r: dict(model_usage[r]) for r in regions},
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
    model_usage_serial = {r: {m: int(model_usage[r].get(m, 0)) for m in models}
                          for r in regions}
    ledger = {
        "run_id": run_id,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "instrument": "single-rating-anchored-v4-structured (combined A/B, iterative pairwise v2)",
        "effort": "medium",
        "attempts_per_pairing": 1,
        "seed": seed,
        "candidate_k": CANDIDATE_K,
        "candidate_rule": "nearest max(int(0.10*233),5)=23 countries by current running score, tie-break country code",
        "models": models,
        "model_balancing": "for each focal, least-used model for that country so far "
                           "(participations in either slot); ties by seeded shuffle",
        "system_sha256": V4.sha(system),
        "base_system_sha256": V4.sha(base_system),
        "n_pairings_planned": n_iterations,
        "n_pairings": len(iterations),
        "n_ok": n_ok,
        "n_rejected": n_rejected,
        "status_by_model": {m: dict(c) for m, c in status_by_model.items()},
        "cost_by_model_usd": {m: str(v) for m, v in cost_by_model.items()},
        "total_usd": str(total),
        "update_schedule": {"updates_1_20": "0.80*old+0.20*new",
                            "updates_21_25": "0.92*old+0.08*new",
                            "updates_26_plus": "0.95*old+0.05*new"},
        "summary": summary,
    }
    (run_dir / "ledger.json").write_text(
        json.dumps(ledger, indent=1, ensure_ascii=False), encoding="utf-8")

    countries = {}
    for r in regions:
        countries[r] = {
            "name": r.split(":", 1)[-1],
            "region": r,
            "initial_score": initial_scores[r],
            "final_score": scores[r],
            "drift_final_minus_initial": scores[r] - initial_scores[r],
            "update_count": update_counts[r],
            "update_history": per_country_history[r],
            "model_usage": model_usage_serial[r],
        }
    drifts = [scores[r] - initial_scores[r] for r in regions]
    drift_summary = {
        "mean_drift": sum(drifts) / len(drifts),
        "mean_abs_drift": sum(abs(d) for d in drifts) / len(drifts),
        "max_abs_drift": max(abs(d) for d in drifts),
        "min_drift": min(drifts),
        "max_drift": max(drifts),
    }
    # Model-usage balance per country: summaries over countries.
    max_shares, ranges = [], []
    for r in regions:
        counts = [model_usage_serial[r][m] for m in models]
        tot = sum(counts)
        if tot:
            max_shares.append(max(counts) / tot)
            ranges.append(max(counts) - min(counts))
    balance_summary = {
        "mean_max_model_share": sum(max_shares) / len(max_shares) if max_shares else 0,
        "max_max_model_share": max(max_shares) if max_shares else 0,
        "mean_model_count_range": sum(ranges) / len(ranges) if ranges else 0,
        "max_model_count_range": max(ranges) if ranges else 0,
    }
    aggregate = {
        "run_id": run_id,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "instrument": "single-rating-anchored-v4-structured (combined A/B, iterative pairwise v2)",
        "effort": "medium",
        "seed": seed,
        "candidate_k": CANDIDATE_K,
        "candidate_rule": "nearest max(int(0.10*233),5)=23 countries by current running score, tie-break country code",
        "models": models,
        "model_balancing": "per-focal least-used (participations, either slot); ties by seeded shuffle",
        "model_usage": model_usage_serial,
        "model_usage_balance_summary": balance_summary,
        "system_sha256": V4.sha(system),
        "base_system_sha256": V4.sha(base_system),
        "n_pairings": len(iterations),
        "n_ok": n_ok,
        "n_rejected": n_rejected,
        "status_by_model": {m: dict(c) for m, c in status_by_model.items()},
        "cost_by_model_usd": {m: str(v) for m, v in cost_by_model.items()},
        "total_usd": str(total),
        "initial_scores": initial_scores,
        "final_running_scores": scores,
        "update_counts": update_counts,
        "drift_summary": drift_summary,
        "countries": countries,
        "pair_history": iterations,
    }
    AGGREGATE_PATH.write_text(json.dumps(aggregate, indent=1, ensure_ascii=False),
                              encoding="utf-8")

    # Report: logistics + drift summary + model-usage balance only.
    lines = []
    lines.append(f"# Countries iterative pairwise v2 — report ({run_id})")
    lines.append("")
    lines.append("## Logistics")
    lines.append("")
    lines.append(f"- Planned pairings: {n_iterations}; completed: {len(iterations)}.")
    lines.append(f"- Seed: {seed}; candidate_k: {CANDIDATE_K} (nearest 23 by current running score).")
    lines.append(f"- Effort: medium; attempts per pairing: 1; retries: none.")
    lines.append(f"- Models (7): {', '.join(models)}.")
    lines.append(f"- Model balancing: per focal country, least-used model for that country "
                 f"so far (participations in either slot); ties by seeded shuffle.")
    lines.append(f"- Base system sha256: `{V4.sha(base_system)}`; "
                 f"directive-augmented system sha256: `{V4.sha(system)}`.")
    lines.append(f"- Initial scores: v1 `final_running_scores` "
                 f"(`analysis/countries_iterative_pairwise.json`).")
    lines.append(f"- Run artifacts: `runs/{run_id}/`; aggregate: "
                 f"`analysis/countries_iterative_pairwise_v2.json`.")
    lines.append("")
    lines.append("## Cost and outcomes")
    lines.append("")
    lines.append(f"- OK: {n_ok}; rejected/failed: {n_rejected}.")
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
    lines.append("## Drift summary (final minus initial, 233 countries)")
    lines.append("")
    lines.append(f"- Mean drift: {drift_summary['mean_drift']:.6f}")
    lines.append(f"- Mean absolute drift: {drift_summary['mean_abs_drift']:.6f}")
    lines.append(f"- Max absolute drift: {drift_summary['max_abs_drift']:.6f}")
    lines.append(f"- Min drift: {drift_summary['min_drift']:.6f}")
    lines.append(f"- Max drift: {drift_summary['max_drift']:.6f}")
    lines.append("")
    lines.append("## Model-usage balance per country")
    lines.append("")
    lines.append(f"- Mean largest-model share per country: "
                 f"{balance_summary['mean_max_model_share']:.4f}")
    lines.append(f"- Max largest-model share per country: "
                 f"{balance_summary['max_max_model_share']:.4f}")
    lines.append(f"- Mean model-count range per country: "
                 f"{balance_summary['mean_model_count_range']:.3f}")
    lines.append(f"- Max model-count range per country: "
                 f"{balance_summary['max_model_count_range']}")
    lines.append("")
    lines.append("Full per-country model usage counts are in "
                 "`analysis/countries_iterative_pairwise_v2.json` "
                 "(`model_usage`, `countries.*.model_usage`). Summary counts "
                 "(participations in either slot):")
    lines.append("")
    lines.append("| Country | Total | " + " | ".join(models) + " | Max share |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in regions:
        counts = [model_usage_serial[r][m] for m in models]
        tot = sum(counts)
        share = (max(counts) / tot) if tot else 0
        lines.append(f"| {r} | {tot} | " + " | ".join(str(c) for c in counts)
                     + f" | {share:.3f} |")
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"done: ok={n_ok} rejected={n_rejected} exact cost {total} USD; "
          f"artifacts in {run_dir}; aggregate {AGGREGATE_PATH}; report {REPORT_PATH}")
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
