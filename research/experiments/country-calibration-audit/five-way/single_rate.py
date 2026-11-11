#!/usr/bin/env python3
"""Anchored single-rating instrument: ONE jurisdiction per call, rubric +
50 synthetic calibration anchors, NO parent score for admin1 regions.
One draw per (model, region). Model set: the seven cheap models incl.
meta/muse-ember (explicit operator instruction 2026-11-10). Thinking effort
medium uniformly; max_tokens 8000. One attempt per call; no retries; failed
draws preserved; Decimal ledger; local USD 10.00 per-run guard.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
FW = HERE
sys.path.insert(0, str(FW))
import harness as H           # noqa: E402
import provider_models as PM  # noqa: E402

OUT_TXT = ('Reply with only a single JSON object, no prose before or after it:\n'
           '{"rating": <float 0.0-1.0>, "explanation": "<your reasoning, <= 150 words>"}')
QUESTION = ("Rate the safety for a transgender visitor of the jurisdiction described "
            "in the dossier strictly according to the rubric above. The rating is on "
            "the rubric's 0.00-1.00 scale, higher is safer.")
HEAD = ("The jurisdiction is anonymised: its identity is withheld. Do NOT attempt to "
        "identify it and do not rely on guesses about which jurisdiction it is — rate "
        "the text provided.\n\n### ANONYMISED DOSSIER\n")


def sha(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()


def build(region_set: str):
    countries = H.load_countries()
    taxonomy = H.load_taxonomy()
    admin1 = H.load_admin1()
    scale = H._production_scale(taxonomy, admin1=False)
    anchors = H.load_calibration_anchors()
    admin1_sys = H.build_admin1_system(taxonomy)
    admin1_clause = re.search(
        r"Where local regimes vary within a division.*?national picture\.",
        admin1_sys, re.S).group(0).replace("\n", " ")

    def system(clause):
        return ("You are assessing risk to a transgender visitor — someone who is, "
                "or is discovered to be, trans. Be evidence-driven and explicit about "
                "uncertainty; absence of evidence is not evidence of safety.\n\n"
                "# Rubric\n\n" + scale + "\n\n" + H.RATING_RULES + "\n\n" + clause
                + "\n" + anchors + "\n---\n\n# Reference documentation: the "
                "outing-risk taxonomy\n\n" + taxonomy.strip()
                + "\n\n## Output format\n\n" + OUT_TXT)

    cells = []
    if region_set == "countries":
        sys_t = system(H.LOCAL_REGIME_CLAUSE)
        for iso3 in sorted(countries):
            user = (HEAD + H.render_country_dossier(iso3, countries)
                    + "\n\n## Question\n\n" + QUESTION + "\n")
            cells.append({"region": iso3, "kind": "country",
                          "system_sha256": sha(sys_t), "user_sha256": sha(user),
                          "_system": sys_t, "_user": user})
    else:
        sys_t = system(admin1_clause)
        for sid in sorted(admin1):
            rec = admin1[sid]
            if rec.get("iso3") != "USA" or not H._has_field(rec, "blindSummary"):
                continue  # US states/DC only; US territories are country cells
            parent = "USA"
            user = (HEAD + H.render_admin1_dossier(sid, parent, admin1, countries)
                    + "\n\n## Question\n\n" + QUESTION + "\n")
            cells.append({"region": f"{sid}:{rec.get('name')}", "kind": "admin1",
                          "system_sha256": sha(sys_t), "user_sha256": sha(user),
                          "_system": sys_t, "_user": user})
    return cells


def freeze() -> None:
    out = {}
    for s in ("countries", "admin1_USA"):
        key = "admin1" if s.startswith("admin1") else s
        cells = build(key)
        out[s] = [{"region": c["region"], "kind": c["kind"],
                   "system_sha256": c["system_sha256"],
                   "user_sha256": c["user_sha256"]} for c in cells]
    doc = {"kind": "single-rating-anchored",
           "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "models": PM.SINGLE_MODELS, "effort": "medium", "max_tokens": 8000,
           "draws_per_cell": 1, "parent_score": None,
           "sets": out}
    (HERE / "frozen").mkdir(exist_ok=True)
    (HERE / "frozen" / "single_rate_manifest.json").write_text(json.dumps(doc, indent=1))
    print(f"froze manifest: {len(out['countries'])} countries, "
          f"{len(out['admin1_USA'])} admin1")


def run(run_id: str, model_key: str, region_set: str, call_subset=None) -> int:
    manifest = json.loads((HERE / "frozen" / "single_rate_manifest.json").read_text())
    if model_key not in manifest["models"]:
        raise SystemExit(f"unknown model {model_key}")
    cells = build("admin1" if region_set.startswith("admin1") else "countries")
    frozen = manifest["sets"][region_set]
    assert [{"region": c["region"], "kind": c["kind"], "system_sha256": c["system_sha256"],
             "user_sha256": c["user_sha256"]} for c in cells] == frozen, "manifest drift"
    run_dir = HERE / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    total = Decimal("0.00")
    for idx, c in enumerate(cells, 1):
        if call_subset is not None and idx not in call_subset:
            continue
        if total >= Decimal("10.00"):
            print(f"STOP local guard at cell {idx}: {total}")
            return 3
        try:
            res = PM.call_single(model_key, c["_system"], c["_user"])
        except Exception as e:
            (run_dir / f"result-{idx:04d}.json").write_text(json.dumps(
                {"cell": idx, "region": c["region"], "status": "stopped",
                 "reason": f"transport failure: {type(e).__name__}: {e}"}, indent=1))
            print(f"STOP transport failure at cell {idx}: {type(e).__name__}")
            return 4
        raw = json.loads(res["raw_response"])
        msg = (raw.get("choices") or [{}])[0].get("message") or {}
        usage = res.get("usage") or {}
        if "cost_usd" not in usage:
            (run_dir / f"attempt-{idx:04d}.json").write_text(json.dumps(
                {"cell": idx, "raw_response": res["raw_response"]}, indent=1))
            (run_dir / f"result-{idx:04d}.json").write_text(json.dumps(
                {"cell": idx, "region": c["region"], "status": "stopped",
                 "reason": "unknown charge"}, indent=1))
            print(f"STOP unknown charge at cell {idx}")
            return 5
        total += Decimal(usage["cost_usd"])
        (run_dir / f"attempt-{idx:04d}.json").write_text(json.dumps(
            {"cell": idx, "region": c["region"], "model": model_key,
             "system_sha256": c["system_sha256"], "user_sha256": c["user_sha256"],
             "usage": usage, "raw_response": res["raw_response"]}, indent=1))
        parsed, perr = None, None
        try:
            p = json.loads((msg.get("content") or "").strip())
            r = float(p["rating"])
            assert 0.0 <= r <= 1.0 and isinstance(p["explanation"], str)
            parsed = {"rating": r, "explanation": p["explanation"]}
        except Exception as e:
            perr = f"{type(e).__name__}: {e}"
        (run_dir / f"result-{idx:04d}.json").write_text(json.dumps(
            {"cell": idx, "region": c["region"], "model": model_key,
             "status": "ok" if parsed else "rejected", "cost_usd": usage["cost_usd"],
             "parsed": parsed, "parse_error": perr}, indent=1))
        print(f"cell {idx:04d} {model_key}/{c['region']}: "
              + ("ok " + f"{parsed['rating']:.2f}" if parsed else "rejected"))
    (run_dir / "ledger.json").write_text(json.dumps(
        {"run_id": run_id, "model": model_key, "set": region_set,
         "total_usd": str(total), "cells_done": sum(1 for f in run_dir.glob('result-*.json'))},
        indent=1))
    print(f"done: exact cost {total} USD")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["freeze", "run"])
    ap.add_argument("--run-id")
    ap.add_argument("--model")
    ap.add_argument("--set", dest="region_set")
    ap.add_argument("--calls", default=None, help="subset e.g. 1-120 or 3,7")
    a = ap.parse_args()
    if a.command == "freeze":
        freeze(); return 0
    subset = None
    if a.calls:
        subset = set()
        for part in a.calls.split(","):
            if "-" in part:
                lo, hi = part.split("-"); subset.update(range(int(lo), int(hi) + 1))
            else:
                subset.add(int(part))
    return run(a.run_id, a.model, a.region_set, subset)


if __name__ == "__main__":
    sys.exit(main())
