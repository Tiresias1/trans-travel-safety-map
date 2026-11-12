#!/usr/bin/env python3
"""Anchored single-rating v4 instrument.

Changes from the earlier single-rating runs:

* Combined-operating-regime synthesis. Federal/national and subnational law
  are assessed as one interacting traveller-facing regime, not as a parent
  baseline plus a local delta.
* Mandatory structured worksheet: eight operative factors, three synthetic-
  anchor comparisons, unknowns, and a combined-regime synthesis. The output
  is still one JSON object, but the visible analysis is now data, not a
  post-hoc paragraph.
* No parent score, no parent arithmetic, and no sovereign-neutralisation
  unless the dossier documents operative jurisdiction/pre-emption.
* Adult visitors and travelling families/minors are both in scope. The rater
  must distinguish documented exposure from documented protection and from
  not-documented/uncertain.
* One attempt per model/region; no retries; exact cost accounting; failed
  draws preserved. Credential handling remains in provider_models.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness as H           # noqa: E402
import provider_models as PM  # noqa: E402

ANCHORS_PATH = HERE.parent / "anchors" / "synthetic_anchors.md"
ANCHOR_IDS = tuple(re.findall(r"^### (0\.\d+-[A-E])$", ANCHORS_PATH.read_text(),
                              flags=re.M))
if len(ANCHOR_IDS) != 50:
    raise RuntimeError(f"expected 50 synthetic anchors, found {len(ANCHOR_IDS)}")

FACTOR_KEYS = (
    "entry_documents",
    "investigation_detention_custody",
    "federal_state_facilities",
    "care_services",
    "threat_framing_law_enforcement",
    "minors_guardians",
    "street_violence_police_response",
    "remedies_unknowns",
)

V3_OVERRIDE = """\
## V3 combined-operating-regime override

This instruction supersedes any earlier parent-baseline wording in the rubric.

Rate the **combined operative regime** the traveller actually encounters. For
subnational dossiers, the parent/national rules, subnational rules, and the
interactions among them form one system; do not estimate a parent score, do
not start from a parent baseline, and do not add or subtract a local premium
or discount. A state's public-accommodation, health-care, or equality law
does not cancel federal entry screening, federal facilities, federal
prosecution, federal detention, federal custody, or federal investigative
authority unless the dossier documents operative pre-emption, immunity, or
refusal by the relevant actor.

Trace interactions across sovereigns. An encounter can move between systems:
document discrepancy → investigation/fraud allegation → detention → birth-sex
custody or other placement; a care seeker or minor can become an investigated
subject; a state-authorized service can still lead into a federal
border/facility/custody exposure. Rate the final operative interaction, not
the most protective individual component.

Include adult visitors and travelling families/minors. When a rule is
age-dependent, describe its consequence for a minor and for a parent or
guardian. Do not infer federal rules from a state map, and do not infer that
a state ban does not exist merely because the jurisdiction is described as
protective.

For every factor, distinguish:
- **exposure**: documented traveller-facing harm or constraint;
- **protection**: documented operative traveller-facing mitigation;
- **interaction**: how that factor interacts with another actor, level of
  government, or stage in the journey;
- **status**: `documented`, `not_documented`, or `uncertain`.
If the dossier does not document a factor, say `not_documented`; never omit it
and never treat absence as safety.

Use the anchors as diagnostic comparisons, not labels. Compare the operative
features to at least three synthetic-anchor levels and explain what makes the
case lower, similar to, or higher than each chosen anchor.
"""

QUESTION = ("Rate the safety for a transgender visitor — including an adult "
            "travelling alone and an adult travelling with a minor, as "
            "applicable — strictly according to the rubric and both the "
            "documented jurisdiction profile and its combined operative "
            "regime. Use the whole dossier. The rating is on the rubric's "
            "0.00-1.00 scale, higher is safer.")
HEAD = ("The jurisdiction is anonymised: its identity is withheld. Do NOT attempt "
        "to identify it, and do not substitute guessed real-world identity, "
        "prior scores, or outside knowledge for the facts and operative rules "
        "in the dossier below. Rate only the evidence provided here.\n\n"
        "### ANONYMISED DOSSIER\n")

OUT_TXT = """\
Reply with only one JSON object, no prose before or after it, with exactly
this shape:
{
  "rating": <float 0.0-1.0>,
  "explanation": "<combined-regime synthesis, <= 150 words>",
  "factor_matrix": {
    "entry_documents": {"exposure": "...", "protection": "...", "interaction": "...", "status": "documented|not_documented|uncertain"},
    "investigation_detention_custody": {"exposure": "...", "protection": "...", "interaction": "...", "status": "documented|not_documented|uncertain"},
    "federal_state_facilities": {"exposure": "...", "protection": "...", "interaction": "...", "status": "documented|not_documented|uncertain"},
    "care_services": {"exposure": "...", "protection": "...", "interaction": "...", "status": "documented|not_documented|uncertain"},
    "threat_framing_law_enforcement": {"exposure": "...", "protection": "...", "interaction": "...", "status": "documented|not_documented|uncertain"},
    "minors_guardians": {"exposure": "...", "protection": "...", "interaction": "...", "status": "documented|not_documented|uncertain"},
    "street_violence_police_response": {"exposure": "...", "protection": "...", "interaction": "...", "status": "documented|not_documented|uncertain"},
    "remedies_unknowns": {"exposure": "...", "protection": "...", "interaction": "...", "status": "documented|not_documented|uncertain"}
  },
  "anchor_checks": [
    {"anchor_id": "0.35-A", "comparison": "..."},
    {"anchor_id": "0.55-B", "comparison": "..."},
    {"anchor_id": "0.75-C", "comparison": "..."}
  ],
  "synthesis": "<how the documented exposures and protections interact in practice>"
}
Every factor must be present. Each factor value is an object with exactly the
four keys above. Use `not_documented` and write `Not documented.` in any
field the dossier does not support. Keep each factor value concise (at most
about 60 words per field), each anchor comparison at most about 80 words,
and the synthesis at most about 150 words. `anchor_checks` must contain at
least three different synthetic-anchor IDs."""


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def build(region_set: str):
    """Build the frozen v4 cell prompts without issuing provider calls."""
    countries = H.load_countries()
    taxonomy = H.load_taxonomy()
    admin1 = H.load_admin1()
    scale = H._production_scale(taxonomy, admin1=False)
    anchors = H.load_calibration_anchors()

    combined_clause = """\
## Combined-regime instruction

Assess all levels of government and all journey stages as one combined
operative regime. Include the parent/national framework and the local/division
evidence as mutually interacting components. Do not estimate or use a parent
score and do not calculate a parent-plus-local score.
"""

    def system():
        return ("You are assessing risk to a transgender visitor, including "
                "an adult travelling alone and an adult travelling with a "
                "minor where relevant. Be evidence-driven and explicit about "
                "uncertainty; absence of evidence is not evidence of safety.\n\n"
                "# Rubric\n\n" + scale + "\n\n" + H.RATING_RULES + "\n\n"
                + V3_OVERRIDE + "\n" + combined_clause + "\n" + anchors
                + "\n---\n\n# Reference documentation: the outing-risk "
                "taxonomy\n\n" + taxonomy.strip()
                + "\n\n## Output format\n\n" + OUT_TXT)

    cells = []
    if region_set == "countries":
        sys_t = system()
        for iso3 in sorted(countries):
            user = (HEAD + H.render_country_dossier(iso3, countries)
                    + "\n\n## Question\n\n" + QUESTION + "\n")
            cells.append({"region": iso3, "kind": "country",
                          "system_sha256": sha(sys_t), "user_sha256": sha(user),
                          "_system": sys_t, "_user": user})
    else:
        sys_t = system()
        for sid in sorted(admin1):
            rec = admin1[sid]
            if rec.get("iso3") != "USA" or not H._has_field(rec, "blindSummary"):
                continue  # US states/DC only; US territories are country cells
            user = (HEAD + H.render_admin1_dossier(sid, "USA", admin1, countries)
                    + "\n\n## Question\n\n" + QUESTION + "\n")
            cells.append({"region": f"{sid}:{rec.get('name')}", "kind": "admin1",
                          "system_sha256": sha(sys_t), "user_sha256": sha(user),
                          "_system": sys_t, "_user": user})
    return cells


def freeze() -> None:
    out = {}
    for public_set, key in (("countries", "countries"), ("admin1_USA", "admin1")):
        cells = build(key)
        out[public_set] = [
            {"region": c["region"], "kind": c["kind"],
             "system_sha256": c["system_sha256"],
             "user_sha256": c["user_sha256"]}
            for c in cells
        ]
    doc = {
        "kind": "single-rating-anchored-v4-structured",
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "models": PM.SINGLE_MODELS,
        "effort": "medium",
        "max_tokens": 16000,
        "draws_per_cell": 1,
        "parent_score": None,
        "parent_baseline_arithmetic": False,
        "factor_keys": list(FACTOR_KEYS),
        "minimum_anchor_checks": 3,
        "sets": out,
    }
    (HERE / "frozen").mkdir(exist_ok=True)
    (HERE / "frozen" / "single_rate_v4_manifest.json").write_text(
        json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"froze v4 manifest: {len(out['countries'])} countries, "
          f"{len(out['admin1_USA'])} admin1")


def _word_count(text: str) -> int:
    return len(text.split())


def _extract_json_text(content: str) -> str:
    """Extract the JSON payload from a markdown code fence if one was used."""
    text = content.strip()
    fence = re.match(r"^```(?:json)?\s*\n(.*?)\n```$", text, flags=re.S | re.I)
    if fence:
        return fence.group(1).strip()
    return text


def parse_v4(content: str) -> dict:
    """Parse and validate the mandatory v4 structured output."""
    if not isinstance(content, str):
        raise ValueError("content is not text")
    parsed = json.loads(_extract_json_text(content))
    if not isinstance(parsed, dict):
        raise ValueError("output is not one JSON object")
    # Some raters label the required combined-regime summary `exposure`, a
    # name already used inside the factor matrix. Accept that one alias and
    # normalise it, rather than discard an otherwise complete structured
    # worksheet.
    summary_key = None
    if "explanation" in parsed:
        summary_key = "explanation"
        expected_keys = {"rating", "explanation", "factor_matrix",
                         "anchor_checks", "synthesis"}
    elif "exposure" in parsed:
        summary_key = "exposure"
        expected_keys = {"rating", "exposure", "factor_matrix",
                         "anchor_checks", "synthesis"}
    if summary_key is None or set(parsed) != expected_keys:
        raise ValueError("output keys do not match the v4 schema")
    try:
        rating = float(parsed["rating"])
    except (TypeError, ValueError) as exc:
        raise ValueError("rating is not numeric") from exc
    if not 0.0 <= rating <= 1.0:
        raise ValueError("rating outside [0,1]")
    summary = parsed[summary_key]
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("explanation is missing")
    if _word_count(summary) > 180:
        raise ValueError("explanation exceeds the v4 word budget")
    if not isinstance(parsed["synthesis"], str) or not parsed["synthesis"].strip():
        raise ValueError("synthesis is missing")
    if _word_count(parsed["synthesis"]) > 220:
        raise ValueError("synthesis exceeds the v4 word budget")

    matrix = parsed["factor_matrix"]
    if not isinstance(matrix, dict) or set(matrix) != set(FACTOR_KEYS):
        raise ValueError("factor_matrix does not cover the required factors")
    for key, value in matrix.items():
        if not isinstance(value, dict) or set(value) != {
                "exposure", "protection", "interaction", "status"}:
            raise ValueError(f"factor {key} has the wrong fields")
        if value["status"] not in {"documented", "not_documented", "uncertain"}:
            raise ValueError(f"factor {key} has an invalid status")
        for field in ("exposure", "protection", "interaction"):
            if not isinstance(value[field], str) or not value[field].strip():
                raise ValueError(f"factor {key}.{field} is missing")

    checks = parsed["anchor_checks"]
    if not isinstance(checks, list) or len(checks) < 3:
        raise ValueError("anchor_checks needs at least three entries")
    anchor_ids = []
    for check in checks:
        if not isinstance(check, dict) or set(check) != {"anchor_id", "comparison"}:
            raise ValueError("anchor check has the wrong fields")
        if check["anchor_id"] not in ANCHOR_IDS:
            raise ValueError(f"unknown anchor id {check['anchor_id']!r}")
        if not isinstance(check["comparison"], str) or not check["comparison"].strip():
            raise ValueError("anchor comparison is missing")
        anchor_ids.append(check["anchor_id"])
    if len(set(anchor_ids)) != len(anchor_ids):
        raise ValueError("anchor_checks repeats an anchor id")

    return {
        "rating": rating,
        "explanation": summary,
        "summary_key_used": summary_key,
        "factor_matrix": matrix,
        "anchor_checks": checks,
        "synthesis": parsed["synthesis"],
    }


def _ledger_total(run_dir: Path) -> Decimal:
    total = Decimal("0")
    for path in run_dir.glob("result-*.json"):
        try:
            result = json.loads(path.read_text(encoding="utf-8"))
            total += Decimal(str(result["cost_usd"]))
        except (KeyError, TypeError, ValueError, InvalidOperation):
            continue
    return total


def run(run_id: str, model_key: str, region_set: str, call_subset=None) -> int:
    manifest = json.loads(
        (HERE / "frozen" / "single_rate_v4_manifest.json").read_text())
    if model_key not in manifest["models"]:
        raise SystemExit(f"unknown model {model_key}")
    cells = build("admin1" if region_set.startswith("admin1") else "countries")
    frozen = manifest["sets"][region_set]
    assert [{"region": c["region"], "kind": c["kind"],
             "system_sha256": c["system_sha256"],
             "user_sha256": c["user_sha256"]} for c in cells] == frozen, \
        "manifest drift"
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
            res = PM.call_v4(model_key, c["_system"], c["_user"])
        except Exception as e:
            (run_dir / f"result-{idx:04d}.json").write_text(json.dumps(
                {"cell": idx, "region": c["region"], "status": "stopped",
                 "reason": f"transport failure: {type(e).__name__}: {e}"},
                indent=1), encoding="utf-8")
            print(f"STOP transport failure at cell {idx}: {type(e).__name__}")
            return 4
        raw = json.loads(res["raw_response"])
        msg = (raw.get("choices") or [{}])[0].get("message") or {}
        usage = res.get("usage") or {}
        if "cost_usd" not in usage:
            (run_dir / f"attempt-{idx:04d}.json").write_text(json.dumps(
                {"cell": idx, "raw_response": res["raw_response"]}, indent=1),
                encoding="utf-8")
            (run_dir / f"result-{idx:04d}.json").write_text(json.dumps(
                {"cell": idx, "region": c["region"], "status": "stopped",
                 "reason": "unknown charge"}, indent=1), encoding="utf-8")
            print(f"STOP unknown charge at cell {idx}")
            return 5
        total += Decimal(usage["cost_usd"])
        (run_dir / f"attempt-{idx:04d}.json").write_text(json.dumps(
            {"cell": idx, "region": c["region"], "model": model_key,
             "system_sha256": c["system_sha256"], "user_sha256": c["user_sha256"],
             "usage": usage, "raw_response": res["raw_response"]}, indent=1),
            encoding="utf-8")
        parsed, perr = None, None
        try:
            parsed = parse_v4(msg.get("content") or "")
        except Exception as e:  # preserve the failed draw; never retry
            perr = f"{type(e).__name__}: {e}"
        (run_dir / f"result-{idx:04d}.json").write_text(json.dumps(
            {"cell": idx, "region": c["region"], "model": model_key,
             "status": "ok" if parsed else "rejected",
             "cost_usd": usage["cost_usd"],
             "parsed": parsed, "parse_error": perr}, indent=1,
            ensure_ascii=False), encoding="utf-8")
        print(f"cell {idx:04d} {model_key}/{c['region']}: "
              + ("ok " + f"{parsed['rating']:.2f}" if parsed else "rejected"))
    if total == 0:
        total = _ledger_total(run_dir)
    (run_dir / "ledger.json").write_text(json.dumps(
        {"run_id": run_id, "model": model_key, "set": region_set,
         "total_usd": str(total),
         "cells_done": sum(1 for f in run_dir.glob('result-*.json'))},
        indent=1), encoding="utf-8")
    print(f"done: exact cost {total} USD")
    return 0


def _parse_subset(spec: str | None) -> set[int] | None:
    if not spec:
        return None
    subset = set()
    for part in spec.split(","):
        if "-" in part:
            lo, hi = part.split("-", 1)
            subset.update(range(int(lo), int(hi) + 1))
        else:
            subset.add(int(part))
    return subset


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["freeze", "run"])
    ap.add_argument("--run-id")
    ap.add_argument("--model")
    ap.add_argument("--set", dest="region_set")
    ap.add_argument("--calls", help="subset e.g. 1-120 or 3,7")
    a = ap.parse_args()
    if a.command == "freeze":
        freeze()
        return 0
    return run(a.run_id, a.model, a.region_set, _parse_subset(a.calls))


if __name__ == "__main__":
    sys.exit(main())
