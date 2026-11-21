#!/usr/bin/env python3
"""Knowledge-based non-dossier ADM1 rating pass (meta/muse-ember, unblinded).

PIPELINE_INVARIANTS rule 7: non-dossier regions are rated by meta/muse-ember
from internal knowledge, UNBLINDED (region identity, parent score, full
unblinded parent dossier) plus the v4 synthetic anchors. This single-model
exception is deliberate and documented; dossier regions keep the multi-model
panel. No national-mean ± delta arithmetic: the region inherits the parent
regime and the model rates how local conditions COMBINE with it.

Scope: every data/admin1.json record with estimated == True OR whose
"sid:name" key appears in analysis/global_adm1_iterative.json
scope.no_differentiator_regions, EXCLUDING the four US-territory dependency
records (ASM/GUM/VIR/MNP) and the four occupied Ukrainian regions (handled
by occupied_ukraine_rerate.py under the operative RUS regime). The scope
list and every prompt hash are frozen to frozen/nondossier_muse_manifest.json
before any provider call; `run` refuses on manifest drift. Drift is checked
on the region set and every prompt-bearing field (identity, parent name,
parent score, system/user hashes); the estimated/no_differentiator scope
flags are metadata that an external data sync may flip after freezing, so
the frozen manifest's flags stay authoritative for the run's artifacts.

Prompt (unblinded by design — the leak gate does not apply to this pass):
  1. the region's real name and country;
  2. the parent country's current score (iterativeScore if present, else
     score) from data/countries.json;
  3. the parent country's FULL unblinded dossier (`summary` from
     data/countries.json, HTML-cleaned);
  4. the v4 synthetic anchors via harness.load_calibration_anchors
     (single_rate_v4 repoints H.ANCHORS_PATH at synthetic_anchors_v4.md);
  5. the v4 rubric/system text verbatim (everything before its structured
     output-format section) plus the bounded anti-absence-as-safety
     DIRECTIVE from global_adm1_iterative, plus a non-dossier override that
     supersedes the blinded-pass clauses forbidding parent-score context
     and replaces the structured worksheet with this pass's output contract.

Output contract: one JSON object {rating: 0-1, basis: 60-140-word factual
dossier-style paragraph (public-summary prose: no score numbers, no record
meta, no rating-process mention), knowledge: "region-specific"|"parent-only"}.
Validation keeps the v4 tolerance convention: basis rejected outside 45-175
words, or if it carries score-shaped decimals or rating-process meta words.

One attempt per region via provider_models.call_v4("muse", ...) at medium
effort; no retries; failed draws are gaps. Exact Decimal cost accounting,
stop on unknown charge, local MAX_USD guard. Resume-safe: any region with a
persisted result file is skipped on relaunch. Single-writer guard: refuses
to launch if another nondossier_muse.py runner process is alive. Artifacts:
runs/<run-id>/attempt-XXXX.json, content-XXXX.txt, result-XXXX.json,
ledger.json; aggregate analysis/nondossier_muse.json. Credential handling
stays inside provider_models. Site data is never written.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import harness as H            # noqa: E402
import provider_models as PM   # noqa: E402
import single_rate_v4 as V4    # noqa: E402  (also repoints H.ANCHORS_PATH to v4)
from global_adm1_iterative import DIRECTIVE  # noqa: E402  (bounded anti-absence)

RUN_ID_DEFAULT = "nondossier-muse-20261119"
MANIFEST_PATH = HERE / "frozen" / "nondossier_muse_manifest.json"
AGGREGATE_PATH = HERE / "analysis" / "nondossier_muse.json"
GLOBAL_AGGREGATE_PATH = HERE / "analysis" / "global_adm1_iterative.json"
MODEL_KEY = "muse"
MAX_USD = Decimal("10.00")
EXCLUDED_ISO3 = frozenset({"ASM", "GUM", "VIR", "MNP"})
EXCLUDED_SIDS = frozenset({
    "14850775B24260608407062",   # Crimea
    "14850775B70667807354554",   # Sevastopol
    "14850775B15615817748403",   # Donetsk
    "14850775B31033086218351",   # Luhansk
})
BASIS_MIN_WORDS = 45    # instructed 60-140; v4-style validation tolerance
BASIS_MAX_WORDS = 175
KNOWLEDGE_VALUES = frozenset({"region-specific", "parent-only"})
# "prompt" only counts as rating-process meta when it refers to the prompt
# itself; the adjective/verb ("prompt remedy", "can prompt curiosity") is
# legitimate public-summary prose (three false rejections, 2026-11-21).
BASIS_META_RE = re.compile(
    r"\b(rating|rated|scores?|scored|rubric|anchors?|dossier)\b"
    r"|\bthis record\b|\bthe model\b|\b(?:the|this) prompt\b", re.I)
BASIS_SCORE_NUM_RE = re.compile(r"\b[01]\.\d+\b")

NONDOSSIER_OVERRIDE = """\
## Non-dossier knowledge-based override (this pass)

This instruction supersedes the earlier clauses that forbid parent-score
context and blind identification. This is the documented rule-7 non-dossier
pass: the region's real identity, its parent country's current national
rating, and the parent's full unblinded dossier ARE provided, and you must
use your internal knowledge of this specific region and country. There is
no region-specific research dossier; your knowledge is the local evidence.

The region inherits the parent's national regime. Rate how the region's
local conditions — social conservatism, rule of law, urban/rural character,
tourism, enforcement geography, and known local exceptions — COMBINE with
that inherited regime for a transgender visitor conditional on discovery
or being outed there. This is NOT arithmetic on the parent score: never
add or subtract a fixed delta, and never push a restrictive country's
regions toward the execution end by subtraction. Regions with lighter
enforcement, tourist-facing economies, or documented local tolerance can
sit ABOVE the national baseline; regions with harsher local enforcement,
armed-group control, or deeper conservatism can sit below it. The parent
score anchors the regime; only real local differences move the rating.

Use internal knowledge of the specific named region. If you have no
region-specific knowledge beyond the national picture, say so in the basis,
rate at the inherited parent regime, set knowledge to "parent-only", and
invent no local detail. If you do have region-specific knowledge, set
knowledge to "region-specific" and state the concrete local differences
(or the absence of known differences) in the basis.

Calibrate internally against the synthetic anchors across the full scale
before rating: consider at least one anchor at or below 0.25 and at least
one at or above 0.75, and place the combined regime relative to them. The
anchors are fictional reference points, not evidence about any real place.
"""

OUT_TXT = """\
## Output format

Reply with only one JSON object, no prose before or after it, with exactly
this shape:
{
  "rating": <float 0.0-1.0, higher is safer>,
  "basis": "<one factual dossier-style paragraph, 60-140 words>",
  "knowledge": "region-specific" | "parent-only"
}
The basis becomes this region's public summary. Write it as factual prose
about the place for a trans visitor: state what the assessment rests on —
the inherited national regime plus the specific local differences, or the
absence of known local differences. Do NOT include score numbers, do NOT
write "this record" or similar record meta, and do NOT mention the rating
process, rubric, anchors, or that a model wrote it. If you have no
region-specific knowledge, the basis must say that no region-specific
information distinguishes it from the national picture, without inventing
local detail."""


def check_single_writer() -> list[int]:
    """PIDs of other nondossier_muse.py python processes (excluding self)."""
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
            if any(p == "nondossier_muse.py" or p.endswith("/nondossier_muse.py")
                   for p in parts):
                pids.append(pid)
    return sorted(pids)


def parent_current_score(prec: dict) -> float:
    raw = prec.get("iterativeScore")
    if raw is None:
        raw = prec.get("score")
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise RuntimeError(f"parent has no numeric score: {raw!r}")
    return float(raw)


def v4_rubric_text() -> str:
    """The v4 system text verbatim up to (excluding) its output-format block."""
    cells = V4.build("countries")
    systems = {c["_system"] for c in cells}
    if len(systems) != 1:
        raise RuntimeError("v4 system text differs between cells")
    full = systems.pop()
    marker = "\n\n## Output format\n\n"
    if marker not in full:
        raise RuntimeError("v4 output-format marker not found")
    return full.split(marker, 1)[0]


def build_system() -> str:
    return (v4_rubric_text() + DIRECTIVE + "\n\n" + NONDOSSIER_OVERRIDE
            + "\n\n" + OUT_TXT)


def build_user(name: str, iso3: str, parent_name: str, parent_score: float,
               parent_summary: str) -> str:
    summary = H.clean(parent_summary)
    if not summary:
        raise RuntimeError(f"{iso3}: parent summary is empty")
    return (
        "### REGION (identity provided — knowledge-based, unblinded assessment)\n"
        f"Region: {name}\n"
        f"Country: {parent_name} ({iso3})\n\n"
        "### PARENT COUNTRY CURRENT NATIONAL RATING\n"
        f"{parent_score} on the rubric's 0.00-1.00 scale, higher is safer.\n\n"
        "### PARENT COUNTRY DOSSIER (full, unblinded)\n"
        f"{summary}\n\n"
        "## Task\n"
        f"Rate {name} ({parent_name}) for a transgender visitor conditional on "
        "discovery, following the non-dossier knowledge-based override: the "
        "inherited national regime combined with this region's local conditions "
        "as you know them. Reply with only the JSON object described in the "
        "output format.\n")


def scope_regions(admin1: dict, countries: dict, no_diff_keys: set) -> list[dict]:
    out = []
    for sid, rec in admin1.items():
        key = f"{sid}:{rec.get('name')}"
        estimated = rec.get("estimated") is True
        no_diff = key in no_diff_keys
        if not (estimated or no_diff):
            continue
        iso3 = rec.get("iso3")
        if iso3 in EXCLUDED_ISO3 or sid in EXCLUDED_SIDS:
            continue
        prec = countries.get(iso3)
        if not isinstance(prec, dict):
            raise RuntimeError(f"{key}: no parent country record for {iso3}")
        out.append({
            "region": key, "sid": sid, "name": rec.get("name"), "iso3": iso3,
            "parent_name": prec.get("name"),
            "parent_score": parent_current_score(prec),
            "estimated": estimated, "no_differentiator": no_diff,
        })
    out.sort(key=lambda r: (r["iso3"], r["name"], r["sid"]))
    return out


def build_cells():
    admin1 = H.load_admin1()
    countries = H.load_countries()
    global_doc = json.loads(GLOBAL_AGGREGATE_PATH.read_text(encoding="utf-8"))
    no_diff_keys = set(global_doc["scope"]["no_differentiator_regions"])
    regions = scope_regions(admin1, countries, no_diff_keys)
    system = build_system()
    system_sha = V4.sha(system)
    cells = []
    for r in regions:
        user = build_user(r["name"], r["iso3"], r["parent_name"],
                          r["parent_score"], countries[r["iso3"]].get("summary"))
        cells.append(dict(r, system_sha256=system_sha, user_sha256=V4.sha(user),
                          _system=system, _user=user))
    return cells, system, no_diff_keys


def freeze() -> None:
    cells, system, no_diff_keys = build_cells()
    n_est = sum(1 for c in cells if c["estimated"])
    n_nd = sum(1 for c in cells if c["no_differentiator"])
    n_both = sum(1 for c in cells if c["estimated"] and c["no_differentiator"])
    doc = {
        "kind": "nondossier-knowledge-muse-v4",
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": MODEL_KEY, "model_id": PM.SINGLE_MODELS[MODEL_KEY],
        "effort": "medium", "max_tokens": 16000,
        "draws_per_region": 1, "retries": False,
        "unblinded": True,
        "single_model_exception": "PIPELINE_INVARIANTS rule 7 (deliberate, documented)",
        "rubric_version": H.RUBRIC_VERSION,
        "system_sha256": V4.sha(system),
        "anchors_sha256": H.sha256_file(H.ANCHORS_PATH),
        "directive_sha256": V4.sha(DIRECTIVE),
        "basis_word_bounds_validation": [BASIS_MIN_WORDS, BASIS_MAX_WORDS],
        "basis_word_bounds_instructed": [60, 140],
        "sources": {
            "data/admin1.json": H.sha256_file(H.ADMIN1_PATH),
            "data/countries.json": H.sha256_file(H.COUNTRIES_PATH),
            "analysis/global_adm1_iterative.json": H.sha256_file(GLOBAL_AGGREGATE_PATH),
            "research/outing-risk-taxonomy.md": H.sha256_file(H.TAXONOMY_PATH),
        },
        "scope": {
            "rule": "estimated == True OR sid:name in global_adm1_iterative "
                    "scope.no_differentiator_regions; excluding ASM/GUM/VIR/MNP "
                    "records and the four occupied Ukrainian sids",
            "excluded_iso3": sorted(EXCLUDED_ISO3),
            "excluded_sids": sorted(EXCLUDED_SIDS),
            "n_no_differentiator_keys": len(no_diff_keys),
            "n_regions": len(cells),
            "n_estimated": n_est, "n_no_differentiator": n_nd, "n_both": n_both,
            "n_iso3": len({c["iso3"] for c in cells}),
        },
        "regions": [{k: c[k] for k in
                     ("region", "sid", "name", "iso3", "parent_name",
                      "parent_score", "estimated", "no_differentiator",
                      "system_sha256", "user_sha256")} for c in cells],
    }
    MANIFEST_PATH.parent.mkdir(exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                             encoding="utf-8")
    print(f"froze manifest: {len(cells)} regions across {doc['scope']['n_iso3']} "
          f"countries (estimated={n_est}, no_differentiator={n_nd}, both={n_both}); "
          f"system_sha256={doc['system_sha256']}")


def parse_nondossier(content: str) -> dict:
    if not isinstance(content, str):
        raise ValueError("content is not text")
    parsed = json.loads(V4._extract_json_text(content))
    if not isinstance(parsed, dict) or set(parsed) != {"rating", "basis", "knowledge"}:
        raise ValueError("output keys do not match {rating, basis, knowledge}")
    try:
        rating = float(parsed["rating"])
    except (TypeError, ValueError) as exc:
        raise ValueError("rating is not numeric") from exc
    if not 0.0 <= rating <= 1.0:
        raise ValueError("rating outside [0,1]")
    basis = parsed["basis"]
    if not isinstance(basis, str) or not basis.strip():
        raise ValueError("basis is missing")
    words = len(basis.split())
    if words < BASIS_MIN_WORDS or words > BASIS_MAX_WORDS:
        raise ValueError(f"basis word count {words} outside "
                         f"[{BASIS_MIN_WORDS},{BASIS_MAX_WORDS}]")
    m = BASIS_SCORE_NUM_RE.search(basis)
    if m:
        raise ValueError(f"basis carries score-shaped number {m.group(0)!r}")
    m = BASIS_META_RE.search(basis)
    if m:
        raise ValueError(f"basis carries rating-process meta {m.group(0)!r}")
    if parsed["knowledge"] not in KNOWLEDGE_VALUES:
        raise ValueError(f"knowledge must be one of {sorted(KNOWLEDGE_VALUES)}")
    return {"rating": rating, "basis": basis.strip(),
            "knowledge": parsed["knowledge"]}


def _do_one(run_dir: Path, idx: int, cell: dict) -> dict:
    suffix = f"{idx:04d}"
    labels = {"region": cell["region"], "iso3": cell["iso3"], "name": cell["name"]}
    try:
        res = PM.call_v4(MODEL_KEY, cell["_system"], cell["_user"])
    except Exception as e:  # one attempt; preserve failure, no retry
        doc = dict(labels, cell=idx, status="transport_failure", attempts=1,
                   reason=f"{type(e).__name__}: {e}")
        (run_dir / f"result-{suffix}.json").write_text(
            json.dumps(doc, indent=1), encoding="utf-8")
        return doc
    usage = res.get("usage") or {}
    (run_dir / f"attempt-{suffix}.json").write_text(json.dumps(dict(
        labels, cell=idx, model=MODEL_KEY, model_id=PM.SINGLE_MODELS[MODEL_KEY],
        effort="medium", attempts=1, system_sha256=cell["system_sha256"],
        user_sha256=cell["user_sha256"], usage=usage,
        raw_response=res["raw_response"]), indent=1), encoding="utf-8")
    if "cost_usd" not in usage:
        doc = dict(labels, cell=idx, status="stopped_unknown_charge", attempts=1,
                   usage=usage)
        (run_dir / f"result-{suffix}.json").write_text(
            json.dumps(doc, indent=1), encoding="utf-8")
        return doc
    try:
        raw = json.loads(res["raw_response"])
        content = ((raw.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    except Exception as e:
        doc = dict(labels, cell=idx, status="rejected", attempts=1,
                   cost_usd=usage["cost_usd"], usage=usage,
                   parse_error=f"raw-response parse: {type(e).__name__}: {e}")
        (run_dir / f"result-{suffix}.json").write_text(
            json.dumps(doc, indent=1), encoding="utf-8")
        return doc
    (run_dir / f"content-{suffix}.txt").write_text(content, encoding="utf-8")
    parsed, perr = None, None
    try:
        parsed = parse_nondossier(content)
    except Exception as e:  # preserve the failed draw; never retry
        perr = f"{type(e).__name__}: {e}"
    doc = dict(labels, cell=idx, model=MODEL_KEY,
               model_id=PM.SINGLE_MODELS[MODEL_KEY],
               status="ok" if parsed else "rejected", attempts=1,
               cost_usd=usage["cost_usd"], usage=usage,
               parent_score=cell["parent_score"], parsed=parsed, parse_error=perr)
    (run_dir / f"result-{suffix}.json").write_text(
        json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    return doc


def _aggregate(run_id: str, run_dir: Path, cells: list, manifest: dict) -> dict:
    entries, total = [], Decimal("0")
    statuses = Counter()
    knowledge = Counter()
    for idx, cell in enumerate(cells, 1):
        path = run_dir / f"result-{idx:04d}.json"
        if not path.is_file():
            statuses["missing"] += 1
            continue
        res = json.loads(path.read_text(encoding="utf-8"))
        statuses[res["status"]] += 1
        if "cost_usd" in res:
            total += Decimal(res["cost_usd"])
        entry = {k: cell[k] for k in ("region", "sid", "name", "iso3",
                                      "parent_name", "parent_score",
                                      "estimated", "no_differentiator")}
        entry["status"] = res["status"]
        entry["cost_usd"] = res.get("cost_usd")
        parsed = res.get("parsed")
        if parsed:
            entry.update(rating=parsed["rating"], basis=parsed["basis"],
                         knowledge=parsed["knowledge"],
                         delta_vs_parent=parsed["rating"] - cell["parent_score"])
            knowledge[parsed["knowledge"]] += 1
        else:
            entry.update(rating=None, basis=None, knowledge=None,
                         delta_vs_parent=None, parse_error=res.get("parse_error")
                         or res.get("reason"))
        entries.append(entry)
    ok = [e for e in entries if e["rating"] is not None]
    deltas = [e["delta_vs_parent"] for e in ok]
    hist = Counter()
    for e in ok:
        hist[min(int(e["rating"] * 10), 9)] += 1
    distribution = {
        "n_ok": len(ok),
        "mean_rating": sum(e["rating"] for e in ok) / len(ok) if ok else None,
        "histogram_decile": {f"{i/10:.1f}-{(i+1)/10:.1f}": hist.get(i, 0)
                             for i in range(10)},
        "knowledge_counts": dict(knowledge),
        "n_above_parent": sum(1 for d in deltas if d > 0.005),
        "n_below_parent": sum(1 for d in deltas if d < -0.005),
        "n_at_parent": sum(1 for d in deltas if abs(d) <= 0.005),
        "mean_delta_vs_parent": sum(deltas) / len(deltas) if deltas else None,
        "mean_abs_delta_vs_parent": (sum(abs(d) for d in deltas) / len(deltas))
                                    if deltas else None,
        "max_delta_vs_parent": max(deltas) if deltas else None,
        "min_delta_vs_parent": min(deltas) if deltas else None,
    }
    return {
        "run_id": run_id,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "instrument": "nondossier-knowledge-muse-v4 (unblinded, rule 7)",
        "model": MODEL_KEY, "model_id": PM.SINGLE_MODELS[MODEL_KEY],
        "effort": "medium", "attempts_per_region": 1,
        "system_sha256": manifest["system_sha256"],
        "scope": manifest["scope"],
        "n_regions": len(cells),
        "status_counts": dict(statuses),
        "total_usd": str(total),
        "distribution": distribution,
        "regions": entries,
    }


def run(run_id: str) -> int:
    others = check_single_writer()
    if others:
        print(f"single-writer guard: nondossier_muse.py already running, "
              f"PID(s)={others}; refusing to launch", flush=True)
        return 2
    if not MANIFEST_PATH.is_file():
        print("no frozen manifest; run `freeze` first", flush=True)
        return 2
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    cells, system, _ = build_cells()
    prompt_keys = ("region", "sid", "name", "iso3", "parent_name",
                   "parent_score", "system_sha256", "user_sha256")
    live = [{k: c[k] for k in prompt_keys} for c in cells]
    frozen = [{k: r[k] for k in prompt_keys} for r in manifest["regions"]]
    if live != frozen or manifest["system_sha256"] != V4.sha(system):
        print("manifest drift: rebuilt cells differ from frozen manifest; "
              "refusing to run", flush=True)
        return 2
    # Scope flags may be flipped by an external data sync after freezing;
    # the frozen manifest remains authoritative for the run's metadata.
    for c, r in zip(cells, manifest["regions"]):
        c["estimated"] = r["estimated"]
        c["no_differentiator"] = r["no_differentiator"]
    run_dir = HERE / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    total = Decimal("0")
    skipped = 0
    for idx in range(1, len(cells) + 1):
        path = run_dir / f"result-{idx:04d}.json"
        if path.is_file():
            skipped += 1
            res = json.loads(path.read_text(encoding="utf-8"))
            if "cost_usd" in res:
                total += Decimal(res["cost_usd"])
    print(f"scope={len(cells)} regions, {skipped} already completed; "
          f"model={MODEL_KEY} ({PM.SINGLE_MODELS[MODEL_KEY]}), effort=medium, "
          f"one attempt per region; system_sha256={V4.sha(system)}", flush=True)
    stopped = None
    for idx, cell in enumerate(cells, 1):
        if (run_dir / f"result-{idx:04d}.json").is_file():
            continue
        if total >= MAX_USD:
            stopped = f"local budget guard {MAX_USD} USD reached at cell {idx}"
            print(f"STOP {stopped}", flush=True)
            break
        res = _do_one(run_dir, idx, cell)
        if "cost_usd" in res:
            total += Decimal(res["cost_usd"])
        status = res["status"]
        if status == "stopped_unknown_charge":
            stopped = f"unknown charge at cell {idx}"
            print(f"STOP {stopped}", flush=True)
            break
        if idx % 25 == 0 or status != "ok":
            rating = (res.get("parsed") or {}).get("rating")
            print(f"  {idx}/{len(cells)} {cell['region']}: {status}"
                  + (f" {rating:.2f}" if rating is not None else "")
                  + f" (running cost {total} USD)", flush=True)
    aggregate = _aggregate(run_id, run_dir, cells, manifest)
    AGGREGATE_PATH.write_text(json.dumps(aggregate, indent=1, ensure_ascii=False)
                              + "\n", encoding="utf-8")
    (run_dir / "ledger.json").write_text(json.dumps({
        "run_id": run_id, "model": MODEL_KEY,
        "model_id": PM.SINGLE_MODELS[MODEL_KEY], "effort": "medium",
        "n_regions": len(cells), "status_counts": aggregate["status_counts"],
        "total_usd": str(total), "stopped": stopped,
        "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, indent=1) + "\n", encoding="utf-8")
    print(f"done: {aggregate['status_counts']}; exact cost {total} USD; "
          f"aggregate {AGGREGATE_PATH}", flush=True)
    return 0 if stopped is None else 5


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["freeze", "run"])
    ap.add_argument("--run-id", default=RUN_ID_DEFAULT)
    a = ap.parse_args()
    if a.command == "freeze":
        freeze()
        return 0
    return run(a.run_id)


if __name__ == "__main__":
    sys.exit(main())
