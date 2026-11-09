#!/usr/bin/env python3
"""Standalone single-country rubric ratings with/without the local-regime
machinery (user-requested 2026-11-08).

Cells: {USA, NPL, GBR} x {mimo-v2.6-flash, deepseek-v4.1-flash-1017} x
{S: clause + regimes paragraph, N: no clause, no paragraph} x 3 draws = 36
calls, one attempt each, no retries. Blinded dossiers (do-not-unblind), the
panel's scale + rules + taxonomy, single-rating JSON output. S carries the
v2 visitor-likelihood clause and the v2 SUBNATIONAL REGIMES paragraph.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
FW = HERE.parent / "five-way"
sys.path.insert(0, str(FW))
import harness as H  # noqa: E402

KEY_FILE = Path("/tmp/.openrouter_key")
URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS_URL = "https://openrouter.ai/api/v1/models"
MODELS = {"mimo": "xiaomi/mimo-v2.6-flash",
          "deepseek": "deepseek/deepseek-v4.1-flash-1017"}
COUNTRIES = ["USA", "NPL", "GBR"]
CONDITIONS = ["S", "N"]
DRAWS = 3
MAX_TOKENS = 8000
MAX_USD = Decimal("5.00")

ROLE = ("You are assessing risk to a transgender visitor — someone who is, or "
        "is discovered to be, trans. Be evidence-driven and explicit about "
        "uncertainty; absence of evidence is not evidence of safety.")
QUESTION = ("Rate the safety for a transgender visitor of the jurisdiction "
            "described in the dossier strictly according to the rubric above. "
            "The rating is on the rubric's 0.00-1.00 scale, higher is safer.")
OUTPUT_FORMAT = """
## Output format

Reply with only a single JSON object, no prose before or after it:
{"rating": <float 0.0-1.0>, "explanation": "<your reasoning, <= 120 words>"}
"""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_prompts(models=None) -> list[dict]:
    countries = H.load_countries()
    taxonomy = H.load_taxonomy()
    scale = H._production_scale(taxonomy, admin1=False)
    rubric = scale + "\n\n" + H.RATING_RULES
    out = []
    for model_key, model_id in (models or MODELS).items():
        for iso3 in COUNTRIES:
            for cond in CONDITIONS:
                for draw in range(1, DRAWS + 1):
                    dossier = H.render_country_dossier(
                        iso3, countries, include_regimes=(cond == "S"))
                    system = (ROLE + "\n\n# Rubric\n\n" + rubric + "\n")
                    if cond == "S":
                        system += "\n" + H.LOCAL_REGIME_CLAUSE + "\n"
                    system += ("\n---\n\n# Reference documentation: the "
                               "outing-risk taxonomy\n\n" + taxonomy.strip()
                               + "\n" + OUTPUT_FORMAT)
                    body = ("The jurisdiction is anonymised: its identity is "
                            "withheld. Do NOT attempt to identify it and do "
                            "not rely on guesses about which jurisdiction it "
                            "is — rate the text provided.\n\n"
                            "### ANONYMISED DOSSIER\n" + dossier)
                    user = body + "\n\n## Question\n\n" + QUESTION + "\n"
                    out.append({
                        "call": len(out) + 1,
                        "model_key": model_key, "model": model_id,
                        "iso3": iso3, "condition": cond, "draw": draw,
                        "system_sha256": sha256_text(system),
                        "user_sha256": sha256_text(user),
                        "_system": system, "_user": user,
                    })
    return out


def freeze(out_name="standalone_calls.json", models=None) -> dict:
    calls = build_prompts(models)
    doc = {
        "kind": "standalone-ratings",
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_calls": len(calls),
        "models": models or MODELS, "countries": COUNTRIES,
        "conditions": {"S": "v2 clause + v2 regimes paragraph",
                       "N": "no clause, no regimes paragraph"},
        "draws_per_cell": DRAWS,
        "max_tokens": MAX_TOKENS, "reasoning_effort": "low",
        "calls": [{k: v for k, v in c.items() if not k.startswith("_")}
                  for c in calls],
    }
    (HERE / "frozen").mkdir(exist_ok=True)
    (HERE / "frozen" / out_name).write_text(json.dumps(doc, indent=1))
    return doc


def _exact(value) -> str:
    return format(Decimal(str(value)), "f")


def resolve_models(models=None) -> dict:
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    req = urllib.request.Request(MODELS_URL, headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json"})
    del key
    with urllib.request.urlopen(req, timeout=120) as resp:
        ids = {m["id"] for m in json.loads(resp.read())["data"]}
    resolved = {}
    for role, pref in (models or MODELS).items():
        if pref in ids:
            resolved[role] = pref
            continue
        cands = sorted(i for i in ids if pref.split(":")[0] in i)
        raise SystemExit(
            f"STOP model resolution: preferred id {pref!r} not offered; "
            f"candidates {cands[:8]} — no silent substitution")
    return resolved


def run(run_id: str, calls_file: str = "standalone_calls.json",
        models=None) -> int:
    frozen = json.loads((HERE / "frozen" / calls_file).read_text())
    resolved = resolve_models(models)
    prompts = build_prompts(models)
    assert [{k: v for k, v in c.items() if not k.startswith("_")}
            for c in prompts] == frozen["calls"], "frozen prompts drifted"
    run_dir = HERE / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    total = Decimal("0.00")
    for c in prompts:
        if total >= MAX_USD:
            print(f"STOP local guard reached at call {c['call']}: {total}")
            return 3
        body = json.dumps({
            "model": resolved[c["model_key"]],
            "max_tokens": MAX_TOKENS,
            "reasoning": {"effort": "low"},
            "messages": [{"role": "system", "content": c["_system"]},
                         {"role": "user", "content": c["_user"]}],
        }).encode("utf-8")
        req = urllib.request.Request(URL, data=body, method="POST", headers={
            "Authorization": "Bearer " + key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                raw = resp.read().decode("utf-8", "replace")
        except Exception as e:
            (run_dir / f"result-{c['call']:03d}.json").write_text(json.dumps(
                {"call": c["call"], "status": "stopped",
                 "reason": f"transport failure: {type(e).__name__}: {e}"}, indent=1))
            print(f"STOP transport failure at call {c['call']}: {type(e).__name__}")
            return 4
        doc = json.loads(raw)
        usage = doc.get("usage") or {}
        cost = usage.get("cost")
        if not isinstance(cost, (int, float)):
            (run_dir / f"attempt-{c['call']:03d}.json").write_text(json.dumps(
                {"call": c["call"], "raw_response": raw}, indent=1))
            (run_dir / f"result-{c['call']:03d}.json").write_text(json.dumps(
                {"call": c["call"], "status": "stopped",
                 "reason": "unknown charge: usage.cost missing"}, indent=1))
            print(f"STOP unknown charge at call {c['call']}")
            return 5
        total += Decimal(_exact(cost))
        (run_dir / f"attempt-{c['call']:03d}.json").write_text(json.dumps(
            {"call": c["call"], "model": resolved[c["model_key"]],
             "iso3": c["iso3"], "condition": c["condition"], "draw": c["draw"],
             "system_sha256": c["system_sha256"], "user_sha256": c["user_sha256"],
             "usage": {"cost_usd": _exact(cost),
                       "input_tokens": usage.get("prompt_tokens"),
                       "output_tokens": usage.get("completion_tokens")},
             "raw_response": raw}, indent=1))
        content = (doc.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        parsed, perr = None, None
        try:
            p = json.loads(content.strip())
            r = float(p["rating"])
            assert 0.0 <= r <= 1.0 and isinstance(p["explanation"], str)
            parsed = {"rating": r, "explanation": p["explanation"]}
        except Exception as e:
            perr = f"{type(e).__name__}: {e}"
        (run_dir / f"result-{c['call']:03d}.json").write_text(json.dumps(
            {"call": c["call"], "status": "ok" if parsed else "unparsed",
             "cost_usd": _exact(cost), "parsed": parsed, "parse_error": perr},
            indent=1))
        print(f"call {c['call']:02d} {c['model_key']}/{c['iso3']}/{c['condition']}/d{c['draw']}: "
              + ("ok" if parsed else "unparsed"))
    (run_dir / "ledger.json").write_text(json.dumps(
        {"run_id": run_id, "total_usd": str(total), "max_usd": str(MAX_USD),
         "calls": len(prompts), "resolved_models": resolved}, indent=1))
    print(f"done: {len(prompts)} calls, exact cost {total} USD")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["freeze", "run", "dry-run"])
    ap.add_argument("--run-id")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--calls-file", default="standalone_calls.json")
    ap.add_argument("--models", default=None,
                    help="comma list role:id to override the default model set")
    a = ap.parse_args()
    models = None
    if a.models:
        models = dict(item.split(":", 1) for item in a.models.split(","))
    if a.command == "freeze":
        doc = freeze(a.calls_file, models)
        print(f"froze {doc['n_calls']} calls -> frozen/{a.calls_file}")
        return 0
    if a.command == "dry-run":
        calls = build_prompts()
        print(f"{len(calls)} calls; first user sha {calls[0]['user_sha256'][:16]}")
        return 0
    if not a.execute or not a.run_id:
        print("STOP: run requires --execute and --run-id")
        return 2
    return run(a.run_id, a.calls_file, models)


if __name__ == "__main__":
    sys.exit(main())
