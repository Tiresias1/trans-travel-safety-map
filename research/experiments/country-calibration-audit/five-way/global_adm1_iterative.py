#!/usr/bin/env python3
"""Global ADM1 iterative pairwise anchored calibration (medium effort).

Scope: every ADM1 record in data/admin1.json with a current numeric score
(iterativeScore if present, else score), EXCLUDING the US-territory
dependency records already handled (ASM/GUM/VIR/MNP) but INCLUDING US
states (redo with the v2 discipline). Comparisons are within ISO3 only:
ADM1 regions compete with siblings in the same country.

Starts from current per-record scores in data/admin1.json. Reuses the
combined A/B anchored pairwise machinery (normal v4 rubric/system/anchors,
A/B anonymised, rate both while keeping partner in mind; dossiers via
harness.render_admin1_dossier (parent framework + blind division fields)
PLUS local evidence built from the unblinded `summary` (plus `blindSummary`
where present), run through the name/score neutralizer below for every
record before rendering, so no record/country names, ISO3 codes or scores
leak. Supervisor decision D+C hybrid (2026-11-17, after iterations 1-9
showed parent-only dossiers are identical within ISO3 for estimated
records): if a record's neutralized local evidence has no local
differentiator vs the parent/generic frame (see has_local_differentiator),
that record is excluded from pairing, recorded as no-differentiator, and
receives no score update. Iterations 1-9 (parent-only dossiers) are kept;
the neutralized-summary + no-differentiator rule applies from iteration
10 on resume.

The v4 system text is augmented by the bounded anti-absence-as-safety
directive appended verbatim (DIRECTIVE below): when trans-specific data is
absent but the LGB signal is severe (capital law, documented executions,
armed-group enforcement, taboo/stigma, no recourse), the LGB signal IS the
operative signal and must be weighted as such; legal ambiguity does NOT
create safety; de facto authorities count as operative regime;
discovered/outs trans visitors cannot be assumed invulnerable because they
deny same-sex conduct; absence of a documented exact pathway is not
mitigating evidence.

Loops 4800 pairings (seeded, deterministic, seed 20261117):
  - pick a random focal ADM1 (seeded RNG) from focal-eligible records
    (ISO3 groups with at least 2 included records; singleton ISO3 records
    have no within-ISO3 partner and are never focal/partner, so they stay
    at their initial score);
  - candidate partners are the nearest max(10% of that country's ADM1
    regions, 3) by CURRENT running score within ISO3 (int(0.10*n_iso),
    minimum 3, capped at n_iso-1), tie-break region id;
  - pick uniformly among candidates (seeded RNG), excluding an immediate
    repeat of the same unordered pair unless there is no other candidate;
  - pick exactly ONE model per pairing with per-ADM1 model-balancing: for
    the focal ADM1, choose the least-used model for that record so far,
    where usage counts pairings in which the record participated in either
    slot; ties are broken by seeded shuffle (dedicated model RNG);
  - call the model once via provider_models.call_v4 at medium effort;
    one attempt per pairing, no retries; if a call fails, record it and
    continue without updating scores.

After each OK pairing, update BOTH participants with the decaying
running-average schedule (per-ADM1 update number, 1-indexed):
  updates 1-20:  0.80*old + 0.20*new
  updates 21-25: 0.92*old + 0.08*new
  updates 26+:   0.95*old + 0.05*new

A is the focal ADM1, B is the partner (mapping recorded only outside the
prompt). Saves runs/global-adm1-iterative-20261117/ artifacts
(attempt/content/result per iteration, ledger, pair-history.json) and
aggregate analysis/global_adm1_iterative.json plus
global-adm1-iterative-report.md. Resume-safe: completed iterations
(pair-history.json) are never re-called. Single-writer guard: before
launching, verify no other global_adm1_iterative.py process is running;
if one is, stop and report the PID instead of launching. The credential
is read only by provider_models. Does not write site data or
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

import provider_models as PM  # noqa: E402
import single_rate_v4 as V4  # noqa: E402
import nh_ri_comparison as NHRI  # noqa: E402
import harness as H  # noqa: E402

RUN_ID_DEFAULT = "global-adm1-iterative-20261117"
AGGREGATE_PATH = HERE / "analysis" / "global_adm1_iterative.json"
REPORT_PATH = HERE / "global-adm1-iterative-report.md"
N_ITERATIONS = 4800
SEED = 20261117
EXCLUDED_ISO3 = frozenset({"ASM", "GUM", "VIR", "MNP"})

# Generic admin-division words that are not distinctive name tokens.
_NAME_STOP = frozenset({"province", "region", "district", "autonomous",
                        "north", "south", "east", "west", "central", "new",
                        "state", "city", "county", "prefecture", "governorate",
                        "territory", "division", "proper", "island", "capital"})


def neutralize(text: str, rec_name: str, iso3: str, parent_name: str,
               score_values=()) -> str:
    """Name/score neutralizer for summary-derived local evidence.

    Replaces the record name and its distinctive tokens with
    "this division", the parent country name / ISO3 with "this country",
    removes score-like numbers (0.xx/1.0 and any explicit score values),
    and strips score-referencing phrases. HTML is cleaned first.
    """
    t = H.clean(text)
    if not t:
        return ""
    for name, repl in ((rec_name, "this division"), (parent_name, "this country")):
        if name:
            t = re.sub(re.escape(name), repl, t, flags=re.I)
    if iso3:
        t = re.sub(rf"\b{re.escape(iso3)}\b", "this country", t, flags=re.I)
    if rec_name:
        for tok in re.findall(r"[A-Za-zÀ-ɿ]{4,}", rec_name):
            low = tok.lower()
            if low in _NAME_STOP:
                continue
            if parent_name and low in parent_name.lower():
                continue
            t = re.sub(rf"\b{re.escape(tok)}\b", "this division", t, flags=re.I)
    for v in score_values:
        if v is not None:
            t = re.sub(rf"\b{re.escape(str(v))}\b", "", t)
    t = re.sub(r"\b[01]\.\d+\b", "", t)
    t = re.sub(r"\bnational score\b", "national assessment", t, flags=re.I)
    t = re.sub(r"\bnational level\b", "national assessment", t, flags=re.I)
    t = re.sub(r"\bnational picture\b", "national assessment", t, flags=re.I)
    t = re.sub(r"\(\s*\)", "", t)
    t = re.sub(r"\s+", " ", t).strip(" .,;")
    return t


def has_local_differentiator(local_neutralized: str, parent_text: str) -> bool:
    """True iff neutralized local evidence differentiates from parent frame.

    Requires >=20 words and <=90% of its >=4-letter word set to already
    appear in the parent framework text. Short generic templates such as
    "Assessed relative to the national assessment." fail the word count.
    """
    words = local_neutralized.split()
    if len(words) < 20:
        return False
    local_set = {w.lower().strip(".,;:") for w in words if len(w) >= 4}
    if not local_set:
        return False
    parent_set = {w.lower().strip(".,;:")
                  for w in H.clean(parent_text).split() if len(w) >= 4}
    if parent_set and len(local_set & parent_set) / len(local_set) > 0.90:
        return False
    return True

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
    "(4) Absence of a documented exact pathway is not mitigating evidence."
)


def check_single_writer() -> list[int]:
    """PIDs of other global_adm1_iterative.py processes (excluding self)."""
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
            if any(p == "global_adm1_iterative.py"
                   or p.endswith("/global_adm1_iterative.py")
                   for p in parts):
                pids.append(pid)
    return sorted(pids)


def alpha_for_update(update_number: int) -> float:
    """Step size for an ADM1 record's update_number-th update (1-indexed)."""
    if update_number <= 20:
        return 0.20
    if update_number <= 25:
        return 0.08
    return 0.05


def candidate_k_for(n_iso: int) -> int:
    """Nearest max(10% of that country's ADM1 regions, 3), capped at n-1."""
    return min(max(int(0.10 * n_iso), 3), max(n_iso - 1, 0))


def candidates_for(focal: str, scores: dict, groups: dict, iso_of: dict):
    """Nearest k siblings within ISO3 by current score, tie-break region."""
    iso = iso_of[focal]
    k = candidate_k_for(len(groups[iso]))
    others = [r for r in groups[iso] if r != focal]
    others.sort(key=lambda r: (abs(scores[r] - scores[focal]), r))
    return others[:k]


def pick_partner(rng: random.Random, focal: str, scores: dict,
                 groups: dict, iso_of: dict, prev_pair):
    cands = candidates_for(focal, scores, groups, iso_of)
    if not cands:
        raise RuntimeError(f"no within-ISO3 partner for {focal}")
    if prev_pair is not None and len(cands) > 1:
        filtered = [c for c in cands if frozenset((focal, c)) != prev_pair]
        if filtered:
            cands = filtered
    return rng.choice(cands)


def pick_model_balanced(model_rng: random.Random, focal: str,
                        model_usage: dict, models: list) -> str:
    """Least-used model for focal so far; ties broken by seeded shuffle.

    model_usage[region] is a Counter over models counting pairings in which
    the region participated (either slot) by assigned model.
    """
    counts = model_usage[focal]
    minimum = min(counts.get(m, 0) for m in models)
    tied = [m for m in models if counts.get(m, 0) == minimum]
    model_rng.shuffle(tied)
    return tied[0]


def build_context():
    manifest = json.loads(
        (HERE / "frozen" / "single_rate_v4_manifest.json").read_text(encoding="utf-8"))
    models = list(manifest["models"].keys())
    if len(models) != 7:
        raise RuntimeError(f"expected 7 models, got {models}")

    # v4 system: countries and admin1_USA cells share one system text.
    systems = set()
    for key in ("countries", "admin1"):
        for c in V4.build(key):
            systems.add(c["_system"])
    if len(systems) != 1:
        raise RuntimeError("v4 system text differs between cells")
    base_system = systems.pop()
    system = base_system + DIRECTIVE

    admin1 = H.load_admin1()
    countries = H.load_countries()

    initial_scores = {}
    iso_of = {}
    name_of = {}
    sid_of = {}
    n_total = len(admin1)
    n_excluded = 0
    for sid in sorted(admin1):
        rec = admin1[sid]
        iso = rec.get("iso3")
        if iso in EXCLUDED_ISO3:
            n_excluded += 1
            continue
        raw_score = rec.get("iterativeScore")
        if raw_score is None:
            raw_score = rec.get("score")
        if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)):
            continue
        region = f"{sid}:{rec.get('name')}"
        initial_scores[region] = float(raw_score)
        iso_of[region] = iso
        name_of[region] = rec.get("name")
        sid_of[region] = sid

    regions = sorted(initial_scores)
    # Parent framework text per ISO3 (blind fields only), for the
    # differentiator overlap check.
    parent_text = {}
    for iso, prec in countries.items():
        parts = [str(prec.get(f) or "") for f in
                 ("blindSummary", "blindTangential", "blindLocalsOnly")]
        ss = prec.get("blindSourceSummaries") or []
        parts.extend(str(x) for x in ss[:8])
        parent_text[iso] = " ".join(parts)

    # Local evidence for every record: `summary` plus `blindSummary` where
    # present, run through the name/score neutralizer before rendering.
    local_neutralized = {}
    differentiator = {}
    for region in regions:
        rec = admin1[sid_of[region]]
        iso = iso_of[region]
        parent_name = (countries.get(iso) or {}).get("name") or ""
        raw_parts = [str(rec.get("summary") or ""), str(rec.get("blindSummary") or "")]
        raw_parts = [p for p in raw_parts if H.clean(p)]
        score_vals = [rec.get("score"), rec.get("iterativeScore"),
                      (countries.get(iso) or {}).get("score"),
                      (countries.get(iso) or {}).get("iterativeScore")]
        local_neutralized[region] = neutralize(
            " ".join(raw_parts), name_of[region], iso, parent_name, score_vals)
        differentiator[region] = has_local_differentiator(
            local_neutralized[region], parent_text.get(iso, ""))

    no_differentiator = sorted(r for r in regions if not differentiator[r])
    diff_regions = [r for r in regions if differentiator[r]]
    # Pairing groups are differentiator-only: no-differentiator records are
    # excluded from pairing (no focal, no partner, no score update).
    groups: dict[str, list[str]] = {}
    for r in diff_regions:
        groups.setdefault(iso_of[r], []).append(r)
    for iso in groups:
        groups[iso].sort()
    focal_pool = [r for r in diff_regions if len(groups[iso_of[r]]) >= 2]

    dossiers = {}
    for region in regions:
        base = H.render_admin1_dossier(
            sid_of[region], iso_of[region], admin1, countries)
        dossiers[region] = (base + "\n\n### DIVISION LOCAL EVIDENCE\n"
                            + local_neutralized[region])

    scope = {
        "n_total_admin1_records": n_total,
        "n_excluded_territories": n_excluded,
        "n_included": len(regions),
        "n_iso3_included": len({iso_of[r] for r in regions}),
        "n_with_local_differentiator": len(diff_regions),
        "n_no_differentiator": len(no_differentiator),
        "no_differentiator_regions": no_differentiator,
        "n_focal_eligible": len(focal_pool),
        "n_singleton_iso3_records": len(diff_regions) - len(focal_pool),
        "excluded_iso3": sorted(EXCLUDED_ISO3),
        "dossier_rule": "render_admin1_dossier (parent+blind) plus neutralized "
                        "summary+blindSummary local evidence; differentiator "
                        ">=20 words and <=90% parent word-set overlap; "
                        "no-differentiator excluded from pairing from iter10",
    }
    return (system, base_system, regions, focal_pool, groups, iso_of,
            name_of, dossiers, initial_scores, models, manifest, scope)


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
    suffix = f"iter{iteration:04d}"
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


def run(run_id: str, dry_run: bool = False, seed: int = SEED,
        n_iterations: int = N_ITERATIONS) -> int:
    others = check_single_writer()
    if others:
        print(f"single-writer guard: global_adm1_iterative.py already running, PID(s)={others}; refusing to launch", flush=True)
        return 2
    (system, base_system, regions, focal_pool, groups, iso_of,
     name_of, dossiers, initial_scores, models, manifest, scope) = build_context()
    print(f"base_system_sha256={V4.sha(base_system)} system_sha256={V4.sha(system)} "
          f"included={scope['n_included']} differentiator={scope['n_with_local_differentiator']} "
          f"no_differentiator={scope['n_no_differentiator']} "
          f"focal_eligible={scope['n_focal_eligible']} "
          f"iso3={scope['n_iso3_included']} singletons={scope['n_singleton_iso3_records']} "
          f"models={models} seed={seed}", flush=True)
    if dry_run:
        rng = random.Random(seed)
        model_rng = random.Random(seed + 99)
        model_usage = {r: Counter() for r in regions}
        focal = rng.choice(focal_pool)
        partner = pick_partner(rng, focal, initial_scores, groups, iso_of, None)
        model_key = pick_model_balanced(model_rng, focal, model_usage, models)
        print(f"dry run: scope={scope}; first focal={focal} (iso={iso_of[focal]}, "
              f"candidate_k={candidate_k_for(len(groups[iso_of[focal]]))}) "
              f"partner={partner} model={model_key}; no provider calls made", flush=True)
        return 0

    run_dir = HERE / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    pair_history_path = run_dir / "pair-history.json"

    scores = dict(initial_scores)
    update_counts = {r: 0 for r in regions}
    per_region_history = {r: [] for r in regions}
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
        per_region_history = hist["per_region_history"]
        rng = _rng_state_from_json(hist["rng_state"])
        model_rng = _rng_state_from_json(hist["model_rng_state"])
        model_usage = {r: Counter(hist["model_usage"][r]) for r in regions}
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
        focal = rng.choice(focal_pool)
        partner = pick_partner(rng, focal, scores, groups, iso_of, prev_pair)
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
            "A_iso3": iso_of[a_region], "B_iso3": iso_of[b_region],
            "A_name": name_of[a_region], "B_name": name_of[b_region],
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
                    "region": region, "name": name_of[region], "iso3": iso_of[region],
                    "update_number": update_counts[region], "alpha": alpha,
                    "rating": rating, "old_score": old, "new_score": new,
                })
                per_region_history[region].append({
                    "iteration": iteration,
                    "partner_region": b_region if region == a_region else a_region,
                    "partner_name": name_of[b_region if region == a_region else a_region],
                    "model": model_key, "rating": rating, "alpha": alpha,
                    "old_score": old, "new_score": new,
                    "update_number": update_counts[region],
                })
                scores[region] = new
        iterations.append(entry)
        summary.append({k: entry[k] for k in ("iteration", "model", "status", "A_region", "B_region")}
                       | ({"cost_usd": entry["cost_usd"]} if "cost_usd" in entry else {}))
        pair_history_path.write_text(json.dumps({
            "run_id": run_id, "seed": seed,
            "n_iterations_planned": n_iterations,
            "scope": scope,
            "models": models,
            "model_balancing": "per-focal least-used (participations, either slot); ties by seeded shuffle",
            "system_sha256": V4.sha(system),
            "base_system_sha256": V4.sha(base_system),
            "running_scores": scores, "update_counts": update_counts,
            "per_region_history": per_region_history,
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
        "instrument": "single-rating-anchored-v4-structured (combined A/B, iterative pairwise)",
        "effort": "medium",
        "attempts_per_pairing": 1,
        "seed": seed,
        "scope": scope,
        "candidate_rule": "nearest max(int(0.10*n_iso3),3) capped at n_iso3-1 siblings within ISO3 by current running score, tie-break region id",
        "models": models,
        "model_balancing": "for each focal, least-used model for that ADM1 so far "
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

    adm1 = {}
    for r in regions:
        adm1[r] = {
            "name": name_of[r],
            "iso3": iso_of[r],
            "region": r,
            "initial_score": initial_scores[r],
            "final_score": scores[r],
            "drift_final_minus_initial": scores[r] - initial_scores[r],
            "update_count": update_counts[r],
            "no_differentiator": r in set(scope.get("no_differentiator_regions", [])),
            "update_history": per_region_history[r],
            "model_usage": model_usage_serial[r],
        }
    drifts = [scores[r] - initial_scores[r] for r in regions]
    updated_drifts = [scores[r] - initial_scores[r] for r in regions if update_counts[r] > 0]
    drift_summary = {
        "n_included": len(regions),
        "n_updated": len(updated_drifts),
        "mean_drift": sum(drifts) / len(drifts),
        "mean_abs_drift": sum(abs(d) for d in drifts) / len(drifts),
        "max_abs_drift": max(abs(d) for d in drifts),
        "min_drift": min(drifts),
        "max_drift": max(drifts),
        "mean_drift_updated_only": (sum(updated_drifts) / len(updated_drifts)) if updated_drifts else 0,
        "mean_abs_drift_updated_only": (sum(abs(d) for d in updated_drifts) / len(updated_drifts)) if updated_drifts else 0,
        "max_abs_drift_updated_only": max((abs(d) for d in updated_drifts), default=0),
        "min_drift_updated_only": min(updated_drifts) if updated_drifts else 0,
        "max_drift_updated_only": max(updated_drifts) if updated_drifts else 0,
    }
    max_shares, ranges = [], []
    for r in regions:
        counts = [model_usage_serial[r][m] for m in models]
        tot = sum(counts)
        if tot:
            max_shares.append(max(counts) / tot)
            ranges.append(max(counts) - min(counts))
    balance_summary = {
        "n_with_participations": len(max_shares),
        "mean_max_model_share": sum(max_shares) / len(max_shares) if max_shares else 0,
        "max_max_model_share": max(max_shares) if max_shares else 0,
        "mean_model_count_range": sum(ranges) / len(ranges) if ranges else 0,
        "max_model_count_range": max(ranges) if ranges else 0,
    }
    aggregate = {
        "run_id": run_id,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "instrument": "single-rating-anchored-v4-structured (combined A/B, iterative pairwise)",
        "effort": "medium",
        "seed": seed,
        "scope": scope,
        "candidate_rule": "nearest max(int(0.10*n_iso3),3) capped at n_iso3-1 siblings within ISO3 by current running score, tie-break region id",
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
        "adm1": adm1,
        "pair_history": iterations,
    }
    AGGREGATE_PATH.write_text(json.dumps(aggregate, indent=1, ensure_ascii=False),
                              encoding="utf-8")

    # Report: logistics + drift summary only.
    lines = []
    lines.append(f"# Global ADM1 iterative pairwise anchored calibration — report ({run_id})")
    lines.append("")
    lines.append("## Logistics")
    lines.append("")
    lines.append(f"- Script: `global_adm1_iterative.py`; run artifacts: `runs/{run_id}/`; "
                 f"aggregate: `analysis/global_adm1_iterative.json`.")
    lines.append(f"- Scope: {scope['n_total_admin1_records']} ADM1 records in `data/admin1.json` "
                 f"with a current numeric score, minus {scope['n_excluded_territories']} "
                 f"US-territory dependency records ({', '.join(scope['excluded_iso3'])}) "
                 f"= {scope['n_included']} included across {scope['n_iso3_included']} ISO3; "
                 f"{scope['n_with_local_differentiator']} have a local differentiator, "
                 f"{scope['n_no_differentiator']} are no-differentiator (neutralized local "
                 f"evidence <20 words or >90% parent-frame overlap; excluded from pairing, "
                 f"recorded in aggregate `scope.no_differentiator_regions`, no score update); "
                 f"{scope['n_singleton_iso3_records']} differentiator records are singleton "
                 f"within ISO3 and never focal/partner (stay at initial score); "
                 f"focal-eligible: {scope['n_focal_eligible']}. US states included. "
                 f"Iterations 1-9 used parent-only dossiers (kept); neutralized-summary "
                 f"rule applies from iteration 10.")
    lines.append(f"- Dossiers: parent framework + blind division fields via "
                 f"`harness.render_admin1_dossier`, plus neutralized local evidence "
                 f"(`summary` plus `blindSummary` where present) for every record "
                 f"through `neutralize()` (record/country names and ISO3 -> "
                 f"this division/this country; score-like numbers removed).")
    lines.append(f"- Planned pairings: {n_iterations}; completed: {len(iterations)}.")
    lines.append(f"- Seed: {seed}; focal ADM1 random; candidate partners: nearest "
                 f"max(10% of that country's ADM1 regions, 3) by current running score within ISO3 "
                 f"(capped at n_iso3-1), tie-break region id; no immediate repeat of the same "
                 f"unordered pair when an alternative exists.")
    lines.append(f"- Effort: medium via `provider_models.call_v4`; exactly one model per pairing, "
                 f"chosen by per-ADM1 least-used model (participations in either slot) with seeded "
                 f"tie-break; attempts per pairing: 1; retries: none; failed draws recorded with "
                 f"no score update. Models ({len(models)}): {', '.join(models)}.")
    lines.append(f"- Update schedule (both participants, per-ADM1 update number): updates 1-20 "
                 f"`0.80*old + 0.20*new`; 21-25 `0.92*old + 0.08*new`; 26+ `0.95*old + 0.05*new`.")
    lines.append(f"- Base v4 system sha256: `{V4.sha(base_system)}`; directive-augmented system "
                 f"sha256: `{V4.sha(system)}`. Directive: severe LGB signal is operative when "
                 f"trans-specific data is absent; legal ambiguity does not create safety; de facto "
                 f"authorities count; discovered/outs visitors are not assumed invulnerable for "
                 f"denying same-sex conduct; absence of a documented exact pathway is not "
                 f"mitigating evidence.")
    lines.append(f"- Initial scores: `iterativeScore` if present, else `score`, per record from "
                 f"`data/admin1.json` (site data not overwritten).")
    lines.append(f"- Single-writer guard: `global_adm1_iterative.py` refuses to launch if another "
                 f"such process is running (reports PID).")
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
    lines.append("## Drift summary (final minus initial)")
    lines.append("")
    lines.append(f"- Included records: {drift_summary['n_included']}; updated: {drift_summary['n_updated']}.")
    lines.append(f"- Mean drift (all included): {drift_summary['mean_drift']:.6f}")
    lines.append(f"- Mean absolute drift (all included): {drift_summary['mean_abs_drift']:.6f}")
    lines.append(f"- Max absolute drift (all included): {drift_summary['max_abs_drift']:.6f}")
    lines.append(f"- Min drift (all included): {drift_summary['min_drift']:.6f}")
    lines.append(f"- Max drift (all included): {drift_summary['max_drift']:.6f}")
    lines.append(f"- Mean drift (updated only): {drift_summary['mean_drift_updated_only']:.6f}")
    lines.append(f"- Mean absolute drift (updated only): {drift_summary['mean_abs_drift_updated_only']:.6f}")
    lines.append(f"- Max absolute drift (updated only): {drift_summary['max_abs_drift_updated_only']:.6f}")
    lines.append(f"- Min drift (updated only): {drift_summary['min_drift_updated_only']:.6f}")
    lines.append(f"- Max drift (updated only): {drift_summary['max_drift_updated_only']:.6f}")
    lines.append("")
    lines.append("## Model-usage balance")
    lines.append("")
    lines.append(f"- Records with participations: {balance_summary['n_with_participations']}.")
    lines.append(f"- Mean largest-model share per record: {balance_summary['mean_max_model_share']:.4f}")
    lines.append(f"- Max largest-model share per record: {balance_summary['max_max_model_share']:.4f}")
    lines.append(f"- Mean model-count range per record: {balance_summary['mean_model_count_range']:.3f}")
    lines.append(f"- Max model-count range per record: {balance_summary['max_model_count_range']}")
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"done: ok={n_ok} rejected={n_rejected} exact cost {total} USD; "
          f"artifacts in {run_dir}; aggregate {AGGREGATE_PATH}; report {REPORT_PATH}", flush=True)
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
