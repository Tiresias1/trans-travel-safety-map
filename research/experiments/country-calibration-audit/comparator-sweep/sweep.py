#!/usr/bin/env python3
"""Comparator sweep: does our blinded dossier wording skew model reads?

For each of 3 models (Sonnet 5.5, Terra 6.1:floor, Gemini 3.8 — all
reasoning effort "low"), each of GBR and NPL, two conditions in SEPARATE
queries:
  A = the instrument's blinded country dossier (blinded fields + blinded
      subnational-regimes paragraph), explicitly told not to unblind;
  B = just the country name (fully unblinded, no dossier);
three questions per cell, each its own call:
  q1 safety for a trans traveller under the production rubric (rubric given);
  q2 societal risk to an outed trans traveller, independent of law;
  q3 political hostility toward trans people, irrespective of laws/attitudes.

36 calls total, one attempt each, no retries. Full responses preserved.
Offline `freeze` records exact prompt hashes before any dispatch.
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
import harness as H  # noqa: E402  (offline helpers: rubric, dossiers)

KEY_FILE = Path("/tmp/.openrouter_key")
URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS_URL = "https://openrouter.ai/api/v1/models"
# Model ids resolved against the live OpenRouter list on 2026-11-08. The
# operator's "Terra 6.1:floor" names a routing preference of the assistant
# runtime (:floor = cheapest route); OpenRouter offers no ":floor" variant for
# this model, so the un-suffixed Terra 6.1 API id is used EXPLICITLY and
# recorded — no model family is substituted. Resolution hard-stops on any
# missing id rather than substituting.
MODELS = {"sonnet": "anthropic/claude-sonnet-5.5",
          "terra": "openai/gpt-6.1-terra",
          "gemini": "google/gemini-3.8-flash"}
COUNTRIES = [("GBR", "United Kingdom"), ("NPL", "Nepal")]
CONDITIONS = ["A", "B"]
QUESTIONS = ["q1", "q2", "q3"]
MAX_TOKENS = 8000
MAX_USD = Decimal("5.00")

OUTPUT_FORMAT = """
## Output format

Reply with only a single JSON object, no prose before or after it:
{"rating": <float 0.0-1.0>, "explanation": "<your reasoning, <= 120 words>"}
"""

ROLE = ("You are assessing risk to a transgender visitor — someone who is, or "
        "is discovered to be, trans. Be evidence-driven and explicit about "
        "uncertainty; absence of evidence is not evidence of safety.")

QUESTION_TEXT = {
    "q1": ("Rate the safety for a transgender visitor of {subject} strictly "
           "according to the rubric above. The rating is on the rubric's "
           "0.00-1.00 scale, higher is safer."),
    "q2": ("Independent of legal policy: how much risk does a transgender "
           "traveller face from society itself — the public, private actors, "
           "family and community — if the person is outed? Rate 0 to 1 where "
           "0 = extreme societal danger and 1 = effectively no societal risk. "
           "This question is about social behaviour only, not law or politics."),
    "q3": ("Irrespective of what laws are on the books or general social "
           "attitudes: rate the level of hostility from politicians — elected "
           "officials, governing parties, state leaders — toward trans people. "
           "Rate 0 to 1 where 0 = extreme political hostility and 1 = no "
           "political hostility."),
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _strip_regimes(dossier: str) -> str:
    marker = "### SUBNATIONAL REGIMES\n"
    if marker not in dossier:
        raise SystemExit("STOP: regimes section missing from dossier")
    head, _, rest = dossier.partition(marker)
    _, _, tail = rest.partition("\n\n")
    return head.rstrip() + "\n\n" + tail.lstrip()


def build_prompts(conditions=None) -> list[dict]:
    countries = H.load_countries()
    scale = H._production_scale(H.load_taxonomy(), admin1=False)
    rubric = scale + "\n\n" + H.RATING_RULES
    out = []
    for model_key, model_id in MODELS.items():
        for iso3, name in COUNTRIES:
            for cond in (conditions or CONDITIONS):
                for q in QUESTIONS:
                    if cond in ("A", "C"):
                        dossier = H.render_country_dossier(iso3, countries)
                        if cond == "C":
                            dossier = _strip_regimes(dossier)
                        body = ("The jurisdiction is anonymised: its identity is "
                                "withheld. Do NOT attempt to identify it and do "
                                "not rely on guesses about which jurisdiction it "
                                "is — rate the text provided.\n\n"
                                "### ANONYMISED DOSSIER\n" + dossier)
                        subject = "the jurisdiction described in the dossier"
                    else:
                        body = f"The jurisdiction is: {name}"
                        subject = name
                    if q == "q1":
                        system = (ROLE + "\n\n# Rubric\n\n" + rubric + OUTPUT_FORMAT)
                    else:
                        system = ROLE + OUTPUT_FORMAT
                    user = (body + "\n\n## Question\n\n"
                            + QUESTION_TEXT[q].format(subject=subject) + "\n")
                    out.append({
                        "call": len(out) + 1,
                        "model_key": model_key, "model": model_id,
                        "iso3": iso3, "condition": cond, "question": q,
                        "system_sha256": sha256_text(system),
                        "user_sha256": sha256_text(user),
                        "_system": system, "_user": user,
                    })
    return out


def freeze(conditions=None, out_name="calls.json") -> dict:
    calls = build_prompts(conditions)
    doc = {
        "kind": "comparator-sweep",
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_calls": len(calls),
        "models": MODELS, "countries": [c for c, _ in COUNTRIES],
        "conditions": list(conditions or CONDITIONS), "questions": QUESTIONS,
        "max_tokens": MAX_TOKENS, "reasoning_effort": "low",
        "calls": [{k: v for k, v in c.items() if not k.startswith("_")}
                  for c in calls],
    }
    (HERE / "frozen").mkdir(exist_ok=True)
    (HERE / "frozen" / out_name).write_text(json.dumps(doc, indent=1))
    return doc


def _exact(value) -> str:
    return format(Decimal(str(value)), "f")


def resolve_models() -> dict:
    """Resolve preferred ids against the live model list; never substitute."""
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    req = urllib.request.Request(MODELS_URL, headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json"})
    del key
    with urllib.request.urlopen(req, timeout=120) as resp:
        ids = {m["id"] for m in json.loads(resp.read())["data"]}
    resolved = {}
    for role, pref in MODELS.items():
        if pref in ids:
            resolved[role] = pref
            continue
        cands = sorted(i for i in ids if pref.split(":")[0] in i)
        raise SystemExit(
            f"STOP model resolution: preferred id {pref!r} not offered; "
            f"candidates {cands[:6]} — no silent substitution")
    return resolved


def run(run_id: str, calls_file: str = "calls.json",
        conditions=None) -> int:
    frozen = json.loads((HERE / "frozen" / calls_file).read_text())
    resolved = resolve_models()
    run_dir = HERE / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    prompts = build_prompts(conditions)
    assert [ {k: v for k, v in c.items() if not k.startswith("_")} for c in prompts ] == frozen["calls"], "frozen prompts drifted"
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
        except Exception as e:  # one attempt only — never retried
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
             "iso3": c["iso3"], "condition": c["condition"],
             "question": c["question"],
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
        print(f"call {c['call']:02d} {c['model_key']}/{c['iso3']}/{c['condition']}/{c['question']}: "
              + ("ok" if parsed else "unparsed"))
    (run_dir / "ledger.json").write_text(json.dumps(
        {"run_id": run_id, "total_usd": str(total),
         "max_usd": str(MAX_USD), "calls": len(prompts),
         "resolved_models": resolved}, indent=1))
    print(f"done: {len(prompts)} calls, exact cost {total} USD")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["freeze", "run", "dry-run"])
    ap.add_argument("--run-id")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--conditions", default=None,
                    help="comma list, e.g. 'C' for the regimes-paragraph ablation")
    ap.add_argument("--calls-file", default="calls.json")
    a = ap.parse_args()
    conds = tuple(a.conditions.split(",")) if a.conditions else None
    if a.command == "freeze":
        doc = freeze(conds, a.calls_file)
        print(f"froze {doc['n_calls']} calls -> frozen/{a.calls_file}")
        return 0
    if a.command == "dry-run":
        calls = build_prompts(conds)
        print(f"{len(calls)} calls; first user sha {calls[0]['user_sha256'][:16]}")
        return 0
    if not a.execute or not a.run_id:
        print("STOP: run requires --execute and --run-id")
        return 2
    return run(a.run_id, a.calls_file, conds)


if __name__ == "__main__":
    sys.exit(main())
