#!/usr/bin/env python3
"""Non-dossier knowledge-rating waves for the six other panel models.

Generalizes nondossier_muse.py (run nondossier-muse-20261119, 1219 regions)
to --model {mimo,deepseek,qwen,glm,haiku,luna} with an explicit --run-id.
EVERYTHING else is identical by construction: the prompt builders, scope
selection, output contract, and validation (including the fixed adjectival-
"prompt" regex) are imported from nondossier_muse, not re-implemented.

PIPELINE_INVARIANTS rule 7: non-dossier regions are rated from internal
knowledge, UNBLINDED (region identity, parent score, full unblinded parent
dossier) plus the v4 synthetic anchors, v4 rubric verbatim, the bounded
anti-absence DIRECTIVE, and the non-dossier override. The muse pass is the
documented single-model exception; these waves extend the same instrument
to the rest of the panel for the later comparison/merge pass (which is a
separate stage — this script never merges bases and never writes site data).

Frozen scope: frozen/nondossier_muse_manifest.json remains the single frozen
manifest. Cells are rebuilt from live data exactly as in nondossier_muse and
refused on any drift of the region set or prompt-bearing fields (identity,
parent name, parent score, system/user hashes); the frozen estimated/
no_differentiator flags stay authoritative for the run's artifacts.

One attempt per region via provider_models.call_v4(model, ...) at medium
effort, max_tokens 16000; no retries; failed draws are gaps. Exact Decimal
cost accounting, stop on unknown charge, local MAX_USD guard per run.
Resume-safe: any region with a persisted result file is skipped on relaunch.
Single-writer guard PER RUN-ID (not per script): the six waves may run
concurrently in distinct run directories, but a second runner targeting the
same run-id is refused. Artifacts: runs/<run-id>/attempt-XXXX.json,
content-XXXX.txt, result-XXXX.json, ledger.json; aggregate
analysis/nondossier_<model>.json. Credentials stay inside provider_models.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import nondossier_muse as NM   # noqa: E402  (shared prompt/scope/validation)
import provider_models as PM   # noqa: E402
import single_rate_v4 as V4    # noqa: E402

MODELS = ("mimo", "deepseek", "qwen", "glm", "haiku", "luna")
MANIFEST_PATH = NM.MANIFEST_PATH          # frozen/nondossier_muse_manifest.json
MAX_USD = NM.MAX_USD
RUNNER_SCRIPTS = ("nondossier_panel.py", "nondossier_muse.py")


def aggregate_path(model: str) -> Path:
    return HERE / "analysis" / f"nondossier_{model}.json"


def runner_run_id(parts: list[str]) -> str | None:
    """Run-id targeted by a nondossier runner argv, or None if not a runner.

    nondossier_muse.py defaults to its own RUN_ID_DEFAULT when --run-id is
    absent; nondossier_panel.py requires --run-id, so an argv without it is
    not yet a live writer for any run-id.
    """
    script = None
    for p in parts:
        base = p.rsplit("/", 1)[-1]
        if base in RUNNER_SCRIPTS:
            script = base
    if script is None:
        return None
    for i, p in enumerate(parts):
        if p == "--run-id" and i + 1 < len(parts):
            return parts[i + 1]
        if p.startswith("--run-id="):
            return p.split("=", 1)[1]
    if script == "nondossier_muse.py":
        return NM.RUN_ID_DEFAULT
    return None


def check_single_writer(run_id: str) -> list[int]:
    """PIDs of other nondossier runner processes targeting this run-id."""
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
            if runner_run_id(parts) == run_id:
                pids.append(pid)
    return sorted(pids)


def _do_one(run_dir: Path, idx: int, cell: dict, model: str) -> dict:
    suffix = f"{idx:04d}"
    labels = {"region": cell["region"], "iso3": cell["iso3"], "name": cell["name"]}
    try:
        res = PM.call_v4(model, cell["_system"], cell["_user"])
    except Exception as e:  # one attempt; preserve failure, no retry
        doc = dict(labels, cell=idx, status="transport_failure", attempts=1,
                   reason=f"{type(e).__name__}: {e}")
        (run_dir / f"result-{suffix}.json").write_text(
            json.dumps(doc, indent=1), encoding="utf-8")
        return doc
    usage = res.get("usage") or {}
    (run_dir / f"attempt-{suffix}.json").write_text(json.dumps(dict(
        labels, cell=idx, model=model, model_id=PM.SINGLE_MODELS[model],
        effort="medium", attempts=1, system_sha256=cell["system_sha256"],
        user_sha256=cell["user_sha256"], usage=usage,
        raw_response=res["raw_response"]), indent=1), encoding="utf-8")
    try:
        _raw = json.loads(res["raw_response"])
    except Exception:
        _raw = {}
    if isinstance(_raw, dict) and (_raw.get("error") or not _raw.get("choices")):
        # Provider error (e.g. 504 timeout): no usage, no charge, no output.
        # Record as a gap and CONTINUE; do not halt the run.
        doc = dict(labels, cell=idx, status="transport_failure", attempts=1,
                   usage=usage,
                   reason=f"ProviderError: {(_raw.get('error') or {}).get('message', 'no choices')}")
        (run_dir / f"result-{suffix}.json").write_text(
            json.dumps(doc, indent=1), encoding="utf-8")
        return doc
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
        parsed = NM.parse_nondossier(content)
    except Exception as e:  # preserve the failed draw; never retry
        perr = f"{type(e).__name__}: {e}"
    doc = dict(labels, cell=idx, model=model,
               model_id=PM.SINGLE_MODELS[model],
               status="ok" if parsed else "rejected", attempts=1,
               cost_usd=usage["cost_usd"], usage=usage,
               parent_score=cell["parent_score"], parsed=parsed, parse_error=perr)
    (run_dir / f"result-{suffix}.json").write_text(
        json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    return doc


def _aggregate(run_id: str, run_dir: Path, cells: list, manifest: dict,
               model: str) -> dict:
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
        "instrument": f"nondossier-knowledge-{model}-v4 (unblinded, rule 7)",
        "model": model, "model_id": PM.SINGLE_MODELS[model],
        "effort": "medium", "attempts_per_region": 1,
        "frozen_manifest": "frozen/nondossier_muse_manifest.json",
        "system_sha256": manifest["system_sha256"],
        "scope": manifest["scope"],
        "n_regions": len(cells),
        "status_counts": dict(statuses),
        "total_usd": str(total),
        "distribution": distribution,
        "regions": entries,
    }


def run(model: str, run_id: str) -> int:
    others = check_single_writer(run_id)
    if others:
        print(f"single-writer guard: run-id {run_id} already has a runner, "
              f"PID(s)={others}; refusing to launch", flush=True)
        return 2
    if not MANIFEST_PATH.is_file():
        print(f"no frozen manifest at {MANIFEST_PATH}; the muse freeze is "
              "the scope source for the panel waves", flush=True)
        return 2
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    cells, system, _ = NM.build_cells()
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
          f"model={model} ({PM.SINGLE_MODELS[model]}), effort=medium, "
          f"one attempt per region; system_sha256={V4.sha(system)}", flush=True)
    stopped = None
    for idx, cell in enumerate(cells, 1):
        if (run_dir / f"result-{idx:04d}.json").is_file():
            continue
        if total >= MAX_USD:
            stopped = f"local budget guard {MAX_USD} USD reached at cell {idx}"
            print(f"STOP {stopped}", flush=True)
            break
        res = _do_one(run_dir, idx, cell, model)
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
    aggregate = _aggregate(run_id, run_dir, cells, manifest, model)
    agg_path = aggregate_path(model)
    agg_path.write_text(json.dumps(aggregate, indent=1, ensure_ascii=False)
                        + "\n", encoding="utf-8")
    (run_dir / "ledger.json").write_text(json.dumps({
        "run_id": run_id, "model": model,
        "model_id": PM.SINGLE_MODELS[model], "effort": "medium",
        "n_regions": len(cells), "status_counts": aggregate["status_counts"],
        "total_usd": str(total), "stopped": stopped,
        "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, indent=1) + "\n", encoding="utf-8")
    print(f"done: {aggregate['status_counts']}; exact cost {total} USD; "
          f"aggregate {agg_path}", flush=True)
    return 0 if stopped is None else 5


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=MODELS, required=True)
    ap.add_argument("--run-id", required=True)
    a = ap.parse_args()
    return run(a.model, a.run_id)


if __name__ == "__main__":
    sys.exit(main())