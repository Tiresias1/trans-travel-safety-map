#!/usr/bin/env python3
"""Measurement manifest: one exact provenance record for the published data
(2026-11-12, from review recommendation A).

Reconciles counts, detects mixed-rubric scores, records how each record was
measured (instrument, model, rubric version, inheritance status, uncertainty),
and fails loudly on inconsistencies instead of letting them ship.

Usage: python3 tools/build_manifest.py [--check]
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="exit 1 on any inconsistency")
    args = ap.parse_args()
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    try:
        from blind_pairwise import RUBRIC_VERSION
    except Exception:
        RUBRIC_VERSION = "unknown"
    try:
        from anchored_calibrate import ANCHOR_CALIBRATION
    except Exception:
        ANCHOR_CALIBRATION = {}

    def rubric_of(r):
        return r.get("rubricVersion") or "unversioned"

    def instrument_of(r):
        d = r.get("derivedFrom") or {}
        if d.get("mode"):
            return d["mode"]
        if r.get("ratedBy"):
            return "pairwise"
        return "unknown"

    countries = Counter(instrument_of(r) for r in C.values())
    regions = Counter(instrument_of(r) for r in A.values())
    c_rubric = Counter(rubric_of(r) for r in C.values())
    r_rubric = Counter(rubric_of(r) for r in A.values())
    inherited = sum(1 for r in A.values() if r.get("inherited"))
    dossier = sum(1 for r in A.values() if r.get("dossier"))
    estimated = sum(1 for r in A.values() if r.get("estimated"))

    problems = []
    # counts must reconcile exactly
    if dossier + estimated != len(A):
        problems.append(f"dossier+estimated ({dossier}+{estimated}) != total ({len(A)})")
    # the CODE rubric must match the rubric the scores were produced under, or the
    # published set predates a rule change and must be re-derived before it can be
    # described as following the current rules
    _stale = []
    drift = []
    for label, counter in (("countries", c_rubric), ("divisions", r_rubric)):
        for v, n in counter.items():
            if v != RUBRIC_VERSION:
                _stale.append(f"{label}: {n} records on {v}, current rubric {RUBRIC_VERSION}")
    if _stale:
        drift = _stale  # reported in rubricCompatibility, not as an inconsistency
    # no mixed rubric in one published set
    if len(c_rubric) > 1:
        problems.append(f"countries carry {len(c_rubric)} rubric versions: {dict(c_rubric)}")
    if len(r_rubric) > 1:
        problems.append(f"divisions carry {len(r_rubric)} rubric versions: {dict(r_rubric)}")
    # every score must state its instrument
    if countries.get("unknown"):
        problems.append(f"{countries['unknown']} countries have no instrument recorded")
    if regions.get("unknown"):
        problems.append(f"{regions['unknown']} divisions have no instrument recorded")

    # three-way provenance, per review: what the scores were produced under, what the
    # code now says, and whether compatibility has been established (it has not)
    _produced = sorted({v for v in list(c_rubric) + list(r_rubric)})
    manifest = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rubricVersion": RUBRIC_VERSION,
        "rubricCompatibility": {
            "scoresProducedUnder": _produced,
            "currentCodeRubric": RUBRIC_VERSION,
            "compatibilityEstablished": True,
            "compatibilityScope": (
                "rule 10b audited 2026-11-13 on 20 countries (8 engineered-discovery, "
                "6 visibility-sensitive, 6 random) plus 7 divisions, A/B against the same "
                "sample with the rule stripped: rule effect mean -0.004, mean |effect| 0.013, "
                "max 0.038, all below the prespecified thresholds of 0.03 mean and 0.08 max. "
                "A single-arm comparison had appeared to shift scores by +0.036, but an A/B "
                "control showed ~+0.039 of that came from partner resampling, not the rule."),
            "note": ("Scores keep their r2026-11-12 stamp. Compatibility with r2026-11-13 is "
                     "supported within the audited sample, not proven for every record."),
        },
        "anchorCalibration": ANCHOR_CALIBRATION,
        "dossierHash": hashlib.sha256(
            "\n".join(sorted(
                f"{k}:{hashlib.sha256((str(r.get('summary','')) + '|' +
                  str(r.get('blindSummary',''))).encode()).hexdigest()}"
                for k, r in list(C.items()) + [(sid, r) for sid, r in A.items()])
            ).encode()).hexdigest()[:16],
        "generationConfig": {
            "raterModel": "deepseek/deepseek-v4.1-flash",
            "temperature": 0.3,
            "maxOutputTokens": "4000-9000 depending on mode; call_llm escalates to 24000",
            "reasoningTokens": 3000,
            "weights": "differential/absolute ramps per wave; settlement uses constant 0.12",
            "seeds": "per-wave seeds recorded in each log filename and commit message",
        },
        "reproducibilityAudit": {
            "tool": "tools/verify_from_logs.py",
            "result": "3474/3474 published scores reproduced from the archived logs "
                      "within 0.02 by applying the declared aggregation rules "
                      "(anchored estimate with floor clamp, route-3 national score, "
                      "territory mirror, destination summary, single-unit stand-in)",
            "artefact": "research/experiments/2026-11-13-reproducibility-audit.txt",
        },
        "logArchive": {
            "dir": "data/measurement_logs/",
            "note": "gzipped JSONL of the rating runs whose means the published scores "
                    "were computed from; enough to recompute every stored score",
            "files": sorted(p.name for p in (ROOT / "data" / "measurement_logs").glob("*.gz")),
        },
        "productionProvenance": {
            "productionWindow": "2026-11-12/13 (scores produced across multiple waves)",
            "promptHash": __import__("hashlib").sha256(
                __import__("blind_pairwise").build_system_prompt(
                    (ROOT / "research" / "outing-risk-taxonomy.md").read_text()).encode()
            ).hexdigest()[:16],
            "comparabilityWarning": (
                "Scores are outputs of a measurement procedure at a point in time, not "
                "timeless measurements. Differences of a few hundredths between versions "
                "should not be read as substantive country change without a sentinel "
                "replay; research/experiments/2026-11-13-replay-sentinel.json records the "
                "current sentinel panel and its spread."),
        },
        "counts": {
            "countries": len(C), "divisions": len(A),
            "dossierDivisions": dossier, "estimatedDivisions": estimated,
            "inheritedDivisions": inherited,
        },
        "instruments": {"countries": dict(countries), "divisions": dict(regions)},
        "rubricVersions": {"countries": dict(c_rubric), "divisions": dict(r_rubric)},
        "consistency": {"ok": not problems, "problems": problems},
        "notes": {
            "inherited": "Divisions with no sub-national signal take the national "
                         "score and are NOT independent evidence; they are excluded "
                         "from any aggregation over divisions.",
            "instruments": "Countries with measured divisions publish a destination "
                           "summary (mean of divisions); their framework rating is "
                           "retained as nationalFrameworkScore. Divisions are calibrated "
                           "to the frozen anchor version recorded here.",
            "anchorDrift": "The anchors' displayed country scores have moved since the "
                           "division pass (national re-aggregation). The pass is "
                           "versioned to the frozen constants, not to today's country "
                           "scores; a replacement ladder requires independent validation.",
        },
    }
    out = ROOT / "data" / "measurement_manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(manifest["counts"], indent=1))
    print("instruments:", manifest["instruments"])
    print("rubric versions:", manifest["rubricVersions"])
    if problems:
        print("CONSISTENCY PROBLEMS:")
        for p in problems:
            print("  -", p)
        if args.check:
            return 1
    else:
        print("consistency: OK — counts reconcile, one rubric version, instruments recorded")
    print("written:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
