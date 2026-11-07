#!/usr/bin/env python3
"""Next-instrument - non-publishing country + ADM1 candidate pilot runner.

This is a bounded, reviewable EXPERIMENT, not a production method. It never
publishes, never writes outside this directory, and never calls an external
model/API on its default path.

Design contract (each clause is enforced by test_instrument.py):

  * Writes stay inside research/experiments/country-calibration-audit/
    next-instrument/ (dry-run output roots are constrained here).
  * `dry-run` is deterministic and offline: it renders every prompt, saves
    evidence snapshots, and records sha256 hashes into a timestamp-free
    manifest. No network module is imported on that path.
  * Provider execution (`execute`) was UNCONDITIONALLY REMOVED before any
    methodological review: the network code no longer exists in this module,
    and old invocations - including the former --allow-provider flag and
    NEXT_INSTRUMENT_ALLOW_PROVIDER=reviewed - always fail closed. See
    BLOCKERS.md.
  * No fixed national score and no published score anywhere in inputs or
    prompts; no foreign-country score anchors. The national estimate comes
    from this instrument's own national phase ("candidate national
    assessment"); every local estimate is candidate_national_baseline +
    local_difference where BOTH numbers are read from shadow results only.
    The country phase never receives region scores or ADM1 aggregates.
  * The country/region scores are assessed independently against the agreed
    scale (0.00 = near-certain imprisonment AND likely execution; 1.00
    aspirational; bands orientation only; no invented intermediate anchors;
    no credit for passing); no value in this instrument is tuned to any
    published number or desired country ordering.
  * Single-dossier contracts only: the national phase asks for exactly one
    `score`; the region phase asks for exactly one `local_delta`. The
    production two-dossier `score_a`/`score_b` contract is deliberately not
    reused for either phase.
  * Fail closed: a missing candidate national baseline, missing model
    output, unparseable output, NaN/Infinity, an out-of-scale number, or a
    schema violation yields NO estimate - an error record instead.

Phases and stable IDs (fixed here, verified against data/ at load time):
  national  NAT-<ISO3>-d<draw>    subjects USA, GBR, NPL, VAT - identity-
                                  stripped blind dossier, country name withheld
  region    REG-<region_id>-d<draw>
      USA-CA   California         sourced-blind  (own blind evidence bundle)
      USA-TX   Texas              sourced-blind  (own blind evidence bundle)
      NPL-BAG  Bagmati            sourced-raw    (no blind bundle; raw record
                                                 text, evidence-linked path)
      NPL-KAR  Karnali            knowledge-only (genuinely thin evidence:
                                                 deliberately identified,
                                                 explicitly uncertain model-
                                                 knowledge assessment; model
                                                 knowledge kept separate from
                                                 sourced local evidence)

Usage:
    python3 instrument.py dry-run [--out DIR] [--national-results FILE]
    python3 instrument.py assemble --results FILE --out FILE
    python3 instrument.py execute --endpoint URL --model NAME --allow-provider
        (additionally requires NEXT_INSTRUMENT_ALLOW_PROVIDER=reviewed;
         never run without that separate review)
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]  # .../kort

COUNTRIES_PATH = ROOT / "data" / "countries.json"
ADMIN1_PATH = ROOT / "data" / "admin1.json"
TAXONOMY_PATH = ROOT / "research" / "outing-risk-taxonomy.md"

# --------------------------------------------------------------------------- #
# Instrument identity and planned settings (settings, not scores)
# --------------------------------------------------------------------------- #

INSTRUMENT_ID = "country-adm1-next-instrument"
INSTRUMENT_VERSION = "0.1.0"
SCALE_CONTRACT = (
    "0.00 = near-certain imprisonment and likely execution; 1.00 = aspirational "
    "acceptance limit; bands orientation only; no intermediate anchors; no "
    "anchor countries; no credit for passing"
)
PLANNED_MODEL = "deepseek/deepseek-v4.1-flash"  # candidate rater, needs review
PLANNED_SETTINGS = {
    "api_dialect": "openai-chat-completions",
    "reasoning_effort": "high",
    "max_tokens": 11000,
    "temperature_sent": False,
}
N_NATIONAL_DRAWS = 2
N_REGION_DRAWS = 2
MAX_CALLS = 16                      # 4 countries x 2 + 4 regions x 2
IN_TOKEN_CAP = 640_000              # candidate caps, proposed for review
OUT_TOKEN_CAP = 256_000
WORST_CASE_IN_CALL = 40_000
WORST_CASE_OUT_CALL = 16_000

COUNTRY_IDS = ("USA", "GBR", "NPL", "VAT")

REGION_SPECS = (
    {"region_id": "USA-CA", "admin1_key": "66186276B43071933723331",
     "country_id": "USA", "name": "California", "evidence_path": "sourced-blind"},
    {"region_id": "USA-TX", "admin1_key": "66186276B29106115751815",
     "country_id": "USA", "name": "Texas", "evidence_path": "sourced-blind"},
    {"region_id": "NPL-BAG", "admin1_key": "38925275B1624743257395",
     "country_id": "NPL", "name": "Bagmati", "evidence_path": "sourced-raw"},
    {"region_id": "NPL-KAR", "admin1_key": "38925275B76883637113030",
     "country_id": "NPL", "name": "Karnali", "evidence_path": "knowledge-only"},
)

# Input-field policy: a country input is built from this whitelist ONLY, so no
# score, rank, anchor ladder or ADM1 aggregate can enter a country prompt.
COUNTRY_DOSSIER_FIELDS = ("blindSummary", "blindTangential",
                          "blindSourceSummaries", "blindLocalsOnly",
                          "blindOutOfScope")
REGION_BLIND_FIELDS = COUNTRY_DOSSIER_FIELDS
FORBIDDEN_INPUT_KEYS = (
    "score", "band", "rank", "countryRank", "worldRank", "divisionSpread",
    "anchorRefs", "derivedFrom", "comparisons", "nationalFrameworkScore",
    "provisionalCalibration", "scoreProvenance", "ratedAt", "ratedBy",
    "unitsInCountry", "estimated_score",
)


class ConfigError(Exception):
    """Data/record mismatch: stop instead of guessing."""


class FailClosed(Exception):
    """A required input or output is missing: produce no number."""


class ValidationError(Exception):
    """Model output failed the schema/scale contract."""


class ProviderDisabledError(Exception):
    """Provider execution attempted without the review gate."""


# --------------------------------------------------------------------------- #
# Loaders (read-only)
# --------------------------------------------------------------------------- #

@functools.lru_cache(maxsize=1)
def load_countries() -> dict:
    return json.loads(COUNTRIES_PATH.read_text(encoding="utf-8"))


@functools.lru_cache(maxsize=1)
def load_admin1() -> dict:
    return json.loads(ADMIN1_PATH.read_text(encoding="utf-8"))


@functools.lru_cache(maxsize=1)
def load_taxonomy() -> str:
    return TAXONOMY_PATH.read_text(encoding="utf-8")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def strip_html(text) -> str:
    text = re.sub(r"<[^>]+>", " ", str(text or ""))
    return re.sub(r"\s+", " ", text).strip()


def region_record(spec: dict) -> dict:
    rec = load_admin1().get(spec["admin1_key"])
    if not rec:
        raise ConfigError(f"admin1 key missing: {spec['admin1_key']}")
    if rec.get("name") != spec["name"] or rec.get("iso3") != spec["country_id"]:
        raise ConfigError(
            f"stable-ID mismatch for {spec['region_id']}: data has "
            f"{rec.get('iso3')}/{rec.get('name')}, spec has "
            f"{spec['country_id']}/{spec['name']}")
    return rec


def country_record(iso3: str) -> dict:
    rec = load_countries().get(iso3)
    if not rec:
        raise ConfigError(f"country missing: {iso3}")
    return rec


def assert_no_forbidden_keys(obj, where: str) -> None:
    if isinstance(obj, dict):
        bad = [k for k in obj if k in FORBIDDEN_INPUT_KEYS]
        if bad:
            raise FailClosed(f"forbidden input keys {bad} leaked into {where}")
        for v in obj.values():
            assert_no_forbidden_keys(v, where)
    elif isinstance(obj, list):
        for v in obj:
            assert_no_forbidden_keys(v, where)


# --------------------------------------------------------------------------- #
# Evidence snapshots (whitelisted; canonical JSON; no numeric outcomes)
# --------------------------------------------------------------------------- #

def country_snapshot(iso3: str) -> dict:
    rec = country_record(iso3)
    fields = {k: rec.get(k) for k in COUNTRY_DOSSIER_FIELDS}
    snap = {
        "snapshot_version": 1,
        "subject_kind": "country",
        "country_id": iso3,
        "dossier_mode": "identity-stripped-blind",
        "fields": fields,
        "content_counts": {
            "blind_source_summaries": len(rec.get("blindSourceSummaries") or []),
        },
    }
    assert_no_forbidden_keys(snap, f"country snapshot {iso3}")
    return snap


def region_snapshot(spec: dict) -> dict:
    rec = region_record(spec)
    base = {
        "snapshot_version": 1,
        "subject_kind": "admin1_region",
        "region_id": spec["region_id"],
        "country_id": spec["country_id"],
        "name": spec["name"],
        "admin1_key": spec["admin1_key"],
        "evidence_path": spec["evidence_path"],
    }
    if spec["evidence_path"] == "sourced-blind":
        fields = {k: rec.get(k) for k in REGION_BLIND_FIELDS}
        base.update({
            "bundle_style": "blind-record",
            "fields": fields,
            "local_evidence_allowlist": list(rec.get("blindSourceSummaries") or []),
            "record_sources": list(rec.get("sources") or []),
            "data_flags": {"estimated": bool(rec.get("estimated")),
                           "blind_bundle": bool(rec.get("blindSummary"))},
        })
    elif spec["evidence_path"] == "sourced-raw":
        # No blind bundle exists for this unit: raw record text, identity
        # visible. The record's `sources` are COUNTRY-level links shared by
        # every unit of this country (Bagmati provenance issue) - they are
        # recorded as country-level context and can never be listed or cited
        # as local evidence. The only provided local evidence is the region's
        # own record text.
        record_text = strip_html(rec.get("summary"))
        base.update({
            "bundle_style": "raw-record",
            "fields": {"summary": rec.get("summary"),
                       "outOfScopeNotes": rec.get("outOfScopeNotes")},
            "local_evidence_allowlist": ([record_text] if record_text else []),
            "country_level_sources_not_local": list(rec.get("sources") or []),
            "data_flags": {"estimated": bool(rec.get("estimated")),
                           "blind_bundle": bool(rec.get("blindSummary"))},
        })
    elif spec["evidence_path"] == "knowledge-only":
        # Genuinely thin: no region-specific sourced evidence at all. The
        # record's sources are country-level links shared by every unit of
        # this country; they are recorded as country-level context, never as
        # local evidence, so the local-evidence allowlist is EMPTY.
        base.update({
            "bundle_style": "identified-knowledge",
            "record_text_unverified": strip_html(rec.get("summary")),
            "country_level_sources_not_local": list(rec.get("sources") or []),
            "local_evidence_allowlist": [],
            "data_flags": {"estimated": bool(rec.get("estimated")),
                           "blind_bundle": bool(rec.get("blindSummary"))},
        })
    else:
        raise ConfigError(f"unknown evidence_path: {spec['evidence_path']}")
    assert_no_forbidden_keys(base, f"region snapshot {spec['region_id']}")
    return base


def canonical_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1) + "\n"


# --------------------------------------------------------------------------- #
# Shared scale text (agreed scale; endpoints and band edges only)
# --------------------------------------------------------------------------- #

SCALE_TEXT = """\
## The scale

0.00-1.00, continuous, **higher is safer**.

- **0.00** - a trans visitor who is outed faces near-certain imprisonment and
  likely execution: the absolute extreme of "do not visit".
- **1.00** - the aspirational limit: law and society fully accept trans people
  as their gender identity with zero discrimination or judgement. No
  jurisdiction reaches it perfectly; do not withhold high scores merely
  because a flawless record cannot be proven.

Bands (orientation only - you output a number, not a band):
[0.00, 0.20) Severe Risk - [0.20, 0.40) High Risk - [0.40, 0.60) Elevated
Risk - [0.60, 0.80) Reduced Risk - [0.80, 1.00] Low Risk.

Beyond these two endpoints and the band edges there are NO intermediate
anchors in this run: no published score, no remembered score, no anchor
country, no comparator jurisdiction appears anywhere in these inputs. Derive
every number from the documented facts and this scale description alone. A
jurisdiction receives no credit because a visitor could pass, stay silent or
avoid scrutiny; rate the consequences that follow discovery, not the
probability of staying undiscovered.
"""

SOCIAL_FRAMING_TEXT = """\
## Social friction, social hostility, state threat-framing - keep them apart

- **Curiosity / social friction**: staring, bemusement, awkward misgendering,
  conservative disapproval that treats the traveller as an oddity, not a
  threat. Uncomfortable, rarely dangerous, very low weight. Social
  conservatism by itself is NOT hostility: a conservative place with no
  documented targeting of trans visitors must not be rated as hostile.
- **Social hostility**: the traveller is framed as a threat or moral offender -
  a deceiver, a corrupting influence, a violator of religious or moral law.
  This can escalate to confrontation, ejection, violence or a police call.
  Real weight, but only where the evidence documents it.
- **State threat-framing**: the law and institutions themselves treat trans
  people as a threat - exclusion from women's spaces on a risk premise,
  custody by birth sex, strip-searches by birth sex, care denial. Tier-one
  weight regardless of how polite street life is.

Judge which one the evidence documents. Do not upgrade friction to hostility
because the prose is sympathetic; do not downgrade hostility to friction
because it is expressed politely. Name all three in your output fields.
"""

THIN_EVIDENCE_TEXT = """\
## Thin evidence

When the dossier is thin, do not resolve the unknown toward 0.5 or toward
neutrality: extrapolate from the structural signals that do exist (the
criminalisation regime, rule of law, governance character, documented
treatment of the closest analogues, protective or community infrastructure)
and say which signals you used. Assume neither merit nor blame from silence
alone. Absence of documented incidents is not evidence of safety in a
thin-data record. Facts carry their date: weigh dated evidence as dated, and
let current signals carry the present-tense rating. An unsourced prevalence
word is not evidence; a prevalence figure without population, category and
period is noise.
"""

CURATED_RULES = """\
## Rating rules

1. **Rate the traveller, not the resident.** A visitor uses their home
   passport and never applies for this jurisdiction's gender-recognition
   machinery. Domestic recognition regimes, marriage equality, adoption or
   employment law are climate signals at most - never protections, and never
   offsets for a documented traveller-facing exposure. The boundary cuts both
   ways: the ABSENCE of resident-facing machinery is likewise a resident gap,
   not a visitor exposure, unless the record shows it reaching visitors.
2. **Sexuality law is secondary for trans visitors.** A sodomy statute weighs
   only through documented use as a police lever against gender-nonconforming
   people. Where the record documents a tolerant society alongside an
   unrepealed statute, the statute is tangential and must not out-vote the
   society.
3. **Burden-of-proof symmetry.** A documented positive counts for at least as
   much as a documented negative. Absence of evidence is not safety, and in a
   well-documented jurisdiction a silent record is a moderately positive
   signal; in a thin-data record it is not.
4. **No geographic pattern-matching.** Two dossiers with identical facts get
   identical ratings regardless of implied geography. If you notice yourself
   inferring the jurisdiction, discount that inference.
5. **Laws on the books vs enforcement.** An unenforced statute is a small
   factor; a statute with documented arrests or police practice is a large
   one. Note which you are weighing.
6. **Incidents: weigh what they prove, not how shocking they are.** A single
   incident is weak evidence of rate outside a very small jurisdiction.
   Patterns, counts, state implication, and a damning official response raise
   it; a positive official response is counter-evidence.
7. **General crime, terrorism, war and natural hazards are out of scope**
   unless they independently raise trans-specific risk.
8. **Severity dominates probability of outing.** What separates the ends of
   the scale is mostly what happens after discovery, and whether the state is
   perpetrator, bystander or protector. Universal-exposure measures and
   organised state/tolerated targeting outrank scattered incidents,
   baseline-level violence and unenforced statutes; rank the worst documented
   feature and compare tiers, not impressions.
9. **Rule of law mediates paper versus street reality - fully applied as a
   liability clause.** "Functioning courts and institutions" are NOT a
   mitigant when the documented exposure is those same institutions enforcing
   hostile policy; efficient enforcement of a hostile rule is exposure, not
   recourse.
10. **Violence needs a background rate.** Trans-specific killings matter only
    materially above the jurisdiction's general homicide rate, patterned and
    state-tolerated. Undercount floors are no evidence in either direction;
    raw counts without denominators carry no magnitude.
11. **Activist visibility is not danger; the local sphere is not the
    traveller sphere.** Court petitions, marches and domestic-rights news show
    civil society, not traveller exposure. High domestic-rights news volume is
    not a risk signal, and a low-violence, high-hospitality conservative
    society is not a dangerous destination.
12. **Institutional failure is exposure evidence, not an offset.** Repeated
    oversight findings that record an unremedied violation corroborate the
    violation. Credit a protection only where the record shows it in force.
"""

NATIONAL_OUTPUT_FORMAT = """\
## Output format

Reply with **only** a single JSON object, no prose before or after it:

{"score": <float 0.0-1.0>, "uncertainty": "<=60 words: what the evidence cannot settle>", "evidence_date": "<most recent date the key evidence carries, e.g. 2026-05 or 2025>", "visitor_applicability": "<=40 words: how this evidence applies, or fails to apply, to a foreign-passport trans visitor>", "social_friction": "<=30 words, or \\"none documented\\">", "social_hostility": "<=30 words, or \\"none documented\\">", "state_threat_framing": "<=30 words, or \\"none documented\\">", "why": "<=40 words: the decisive drivers>"}

This is a SINGLE-dossier contract: exactly one score field, named `score`.
There is no second dossier and there must be no `score_a` or `score_b` field.
Give the score to two decimal places. An unparseable, incomplete or
out-of-scale answer is discarded and recorded as a failure, so do not wrap the
object in Markdown fences or add commentary.
"""

REGION_OUTPUT_FORMAT = """\
## Output format

Reply with **only** a single JSON object, no prose before or after it:

{"assessment_mode": "sourced" or "model_knowledge", "region_id": "<the region_id given above>", "local_delta": <float, signed, higher safer>, "departures": [{"fact": "<one documented difference from the national assessment>", "local_evidence": "<the specific provided item supporting it, or \\"none provided\\">", "direction": "safer" or "riskier", "magnitude": <float>, "visitor_applicability": "<=30 words how it reaches a foreign-passport trans visitor>", "already_in_national_bundle": <true|false>, "counted_in_delta": <true|false>, "evidence_date": "<date the fact carries>", "uncertainty": "<=30 words>"}], "sourced_local_evidence": ["<repeat only items listed in the snapshot as provided local evidence>"], "knowledge_statements": [], "knowledge_confidence": "low" or "medium" or "n/a", "knowledge_is_unverified": <true|false>, "inherited_national_exposure": ["<national factors already priced into the national assessment and not re-counted here>"], "uncertainty": "<=60 words: what this assessment cannot settle, including evidence thinness>", "evidence_date": "<most recent date the key local evidence carries>", "visitor_applicability": "<=40 words>", "social_friction": "<=30 words, or \\"none documented\\">", "social_hostility": "<=30 words, or \\"none documented\\">", "state_threat_framing": "<=30 words, or \\"none documented\\">", "notes": "<=60 words>"}

`local_delta` is the region's signed difference from the candidate national
assessment (positive = safer than the national assessment, negative =
riskier); the region's absolute estimate is computed outside this model call.
A departure whose fact already appears in the national assessment must carry
`already_in_national_bundle: true` and `counted_in_delta: false`. For
`assessment_mode: "model_knowledge"` records: `departures` must be an empty
list, `knowledge_statements` must be non-empty, `knowledge_confidence` must be
"low" or "medium", `knowledge_is_unverified` must be true, and
`sourced_local_evidence` may only repeat provided snapshot items (a
knowledge-only record has none, so it must be empty). An unparseable,
incomplete or out-of-scale answer is discarded and recorded as a failure, so
do not wrap the object in Markdown fences or add commentary.
"""


# --------------------------------------------------------------------------- #
# System prompts (single-dossier contracts; not the production two-dossier one)
# --------------------------------------------------------------------------- #

def build_national_system_prompt() -> str:
    return (
        "You are an expert assessor of travel risk for transgender people.\n"
        "You will receive ONE anonymised dossier describing ONE jurisdiction. "
        "You do not know which jurisdiction it is and you must not try to "
        "guess: your rating must follow from the documented facts and the "
        "scale alone.\n\n"
        "Your task: rate **that one jurisdiction** on the scale below, "
        "independently, as the risk faced by a transgender visitor to it if "
        "they are discovered or outed there.\n\n"
        + SCALE_TEXT
        + "\nThe score integrates probability of being outed x severity of "
          "what happens if outed, across every axis below.\n\n"
        + CURATED_RULES
        + "\n" + SOCIAL_FRAMING_TEXT
        + "\n" + THIN_EVIDENCE_TEXT
        + "\n---\n\n# Reference documentation: the outing-risk taxonomy\n"
        + load_taxonomy().strip()
        + "\n\n---\n" + NATIONAL_OUTPUT_FORMAT
    )


def build_region_system_prompt() -> str:
    return (
        "You are an expert assessor of travel risk for transgender people.\n"
        "You will receive ONE dossier describing ONE first-level "
        "administrative region, together with the COMPLETE candidate "
        "national assessment for the country it belongs to. Your task is "
        "only the region's signed difference from that national assessment - "
        "not a new absolute score for the region, and never a new national "
        "score.\n\n"
        + SCALE_TEXT
        + "\n## The candidate national assessment is an input to hold fixed\n\n"
        "The national score you are shown was produced by this instrument's "
        "own national phase; it is NOT a published score and it is NOT to be "
        "re-rated. Do not echo a revised national number, do not propose a "
        "different national level, and do not output a national score. "
        "Sign convention: local_estimate = national_baseline + local_delta, "
        "positive = the region sits safer than its national assessment, "
        "negative = riskier.\n\n"
        "Only what genuinely differs between this region and the national "
        "assessment may move `local_delta`, and only as far as the region's "
        "own evidence supports. Federal/national law, border and passport "
        "friction and the national enforcement climate are already priced "
        "into the national assessment: a region-local repetition of them goes "
        "into `inherited_national_exposure` with "
        "`already_in_national_bundle: true` and `counted_in_delta: false` - "
        "repetition is never double-counted. A region-specific "
        "IMPLEMENTATION "
        "or enforcement of a national rule may still count as a genuine "
        "difference when the record documents it as operative locally.\n\n"
        "## Sub-national rules\n\n"
        "1. Legal hierarchy: where the rule of law is strong and the region "
        "has no real devolved power over the subject, a regional statute "
        "conflicting with national law is signalling, not operative risk; "
        "where the rule of law is weak, regional practice can bend national "
        "law either way. Autonomy that is real (own criminal law, courts, "
        "policing) can legitimately diverge widely; symbolic declarations "
        "cannot.\n"
        "2. Enforcement beats statute: a court-blocked ban is a small factor, "
        "a ban with documented arrests or filed suits is a large one; "
        "documented institutional pushback is positive evidence.\n"
        "3. Documentation density is not danger: incidents concentrate where "
        "visible trans people and reporting infrastructure exist. An "
        "under-documented region is NOT safer - it carries the national "
        "climate including its conservatism and unreported informal violence. "
        "Rate a documented region below an undocumented one only for "
        "structural hostility beyond the national climate. Equal deltas are "
        "correct when the evidence warrants them; do not invent a difference "
        "to look decisive.\n"
        "4. Every departure must carry visitor applicability, its own "
        "evidence date, its uncertainty, and its inheritance/double-counting "
        "flags. `inherited_national_exposure` must be populated - name the "
        "national factors you deliberately did NOT re-count.\n\n"
        + SOCIAL_FRAMING_TEXT
        + "\n## Evidence classes - pick the one the prompt assigns to you\n\n"
        "### sourced\nThe region has its own provided evidence bundle. Every "
        "counted departure must point at a provided item; "
        "`assessment_mode` is \"sourced\".\n"
        "### model_knowledge (thin-evidence regions)\nThe region is named and "
        "has NO provided local evidence: you are asked for general model "
        "knowledge about that actual named region, and it is explicitly "
        "uncertain. Set `assessment_mode: \"model_knowledge\"`, "
        "`knowledge_confidence: \"low\"` (or \"medium\" if your recollection "
        "is unusually specific), `knowledge_is_unverified: true`, put the "
        "recollection itself in `knowledge_statements` with hedged wording, "
        "keep `departures` empty, and keep `sourced_local_evidence` empty - "
        "a knowledge guess is NEVER presented as verified fact and NEVER "
        "carries an invented citation. Do not automatically copy the "
        "national score either: say what you believe about this named region "
        "and how uncertain you are.\n\n"
        + THIN_EVIDENCE_TEXT
        + "\n---\n\n# Reference documentation: the outing-risk taxonomy\n"
        + load_taxonomy().strip()
        + "\n\n---\n" + REGION_OUTPUT_FORMAT
    )


# --------------------------------------------------------------------------- #
# User prompts
# --------------------------------------------------------------------------- #

def render_country_dossier(snap: dict) -> str:
    f = snap["fields"]
    parts = []
    if f.get("blindSummary"):
        parts.append("### ASSESSMENT\n" + strip_html(f["blindSummary"]))
    if f.get("blindTangential"):
        parts.append("### SECONDARY / SITUATIONAL FACTORS\n"
                     + strip_html(f["blindTangential"]))
    if f.get("blindLocalsOnly"):
        parts.append("### AFFECTS RESIDENTS MORE THAN VISITORS\n"
                     + strip_html(f["blindLocalsOnly"]))
    if f.get("blindOutOfScope"):
        parts.append("### DELIBERATELY NOT COUNTED\n"
                     + strip_html(f["blindOutOfScope"]))
    ss = f.get("blindSourceSummaries")
    if isinstance(ss, list) and ss:
        items = "\n".join("- " + strip_html(x) for x in ss if str(x).strip())
        parts.append("### SOURCE EVIDENCE (all items, uncapped)\n" + items)
    return "\n\n".join(parts)


def build_national_user_prompt(iso3: str) -> str:
    snap = country_snapshot(iso3)
    return (
        "Rate the jurisdiction described below.\n\n"
        "## DOSSIER (identity withheld)\n\n"
        + render_country_dossier(snap)
        + "\n\nReply with only the single JSON object described in the "
          "output format."
    )


def read_results_rows(results_path) -> list:
    """Parse a results NDJSON file; malformed lines fail closed instead of
    raising an unhandled traceback."""
    if results_path is None or not Path(results_path).exists():
        raise FailClosed(f"results file not found: {results_path}")
    rows = []
    for n, line in enumerate(Path(results_path).read_text(
            encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise FailClosed(f"malformed results line {n}: {e}") from None
    return rows


def national_baseline_from_rows(rows: list, country_id: str) -> dict:
    """Candidate national baseline from shadow-result rows ONLY.

    Fail closed on: duplicate call IDs, mixed run identity (rows carrying
    disagreeing run_id values), missing required national draws, or any
    invalid/missing model output. Never averages an incomplete or mixed run
    and never falls back to a published score.
    """
    cand = [r for r in rows
            if r.get("phase") == "national"
            and r.get("country_id") == country_id
            and r.get("status") == "ok"]
    if not cand:
        raise FailClosed(f"missing candidate national baseline for {country_id}")
    run_ids = {r.get("run_id") for r in cand if r.get("run_id") is not None}
    if len(run_ids) > 1:
        raise FailClosed(
            f"mixed run identity for {country_id}: run_ids {sorted(run_ids)}")
    ids = [r.get("call_id") for r in cand]
    if len(ids) != len(set(ids)):
        raise FailClosed(f"duplicate call_id in national rows for {country_id}")
    draws = {r.get("draw") for r in cand}
    expected = set(range(1, N_NATIONAL_DRAWS + 1))
    missing = sorted(expected - draws)
    if missing:
        raise FailClosed(
            f"missing required national draws for {country_id}: {missing} "
            f"(refusing to average an incomplete run)")
    ok_rows = []
    invalid = []
    for row in cand:
        try:
            ok_rows.append((row, validate_national(row.get("response"))))
        except ValidationError as e:
            invalid.append(f"{row.get('call_id')}: {e}")
    if invalid:
        raise FailClosed(
            f"invalid national model output for {country_id}: {invalid}")
    scores = [p["score"] for _, p in ok_rows]
    baseline = round(sum(scores) / len(scores), 6)
    if not math.isfinite(baseline):
        raise FailClosed(f"non-finite candidate national baseline for {country_id}")
    return {
        "country_id": country_id,
        "baseline": baseline,
        "scores": scores,
        "n_draws": len(scores),
        "source_call_ids": [r.get("call_id") for r, _ in ok_rows],
        "assessment": {
            "uncertainty": ok_rows[-1][1]["uncertainty"],
            "evidence_date": ok_rows[-1][1]["evidence_date"],
            "why": ok_rows[-1][1]["why"],
        },
    }


def national_result_for(country_id: str, results_path: Path) -> dict:
    """Read the candidate national baseline from shadow results only.

    Fail closed (see national_baseline_from_rows): duplicate call IDs, mixed
    run identity, missing draws, or invalid output -> raise. Nothing here
    ever falls back to a published score.
    """
    rows = read_results_rows(results_path)
    return national_baseline_from_rows(rows, country_id)


def render_region_evidence(spec: dict, snap: dict) -> str:
    if spec["evidence_path"] == "sourced-blind":
        f = snap["fields"]
        parts = ["### REGION RECORD (identity shown; autonomy judgement "
                 "requires the region's name)\n### DIVISION: " + spec["name"]
                 + f"  (region_id {spec['region_id']})"]
        if f.get("blindSummary"):
            parts.append("### LOCAL ASSESSMENT\n" + strip_html(f["blindSummary"]))
        ss = f.get("blindSourceSummaries")
        if isinstance(ss, list) and ss:
            items = "\n".join("- " + strip_html(x) for x in ss if str(x).strip())
            parts.append("### LOCAL SOURCE EVIDENCE (all items, uncapped)\n" + items)
        if f.get("blindTangential"):
            parts.append("### SECONDARY / SITUATIONAL FACTORS\n"
                         + strip_html(f["blindTangential"]))
        if f.get("blindLocalsOnly"):
            parts.append("### AFFECTS RESIDENTS MORE THAN VISITORS\n"
                         + strip_html(f["blindLocalsOnly"]))
        if f.get("blindOutOfScope"):
            parts.append("### DELIBERATELY NOT COUNTED\n"
                         + strip_html(f["blindOutOfScope"]))
        return "\n\n".join(parts)
    if spec["evidence_path"] == "sourced-raw":
        f = snap["fields"]
        parts = ["### DIVISION: " + spec["name"]
                 + f"  (region_id {spec['region_id']})",
                 "NOTE: no anonymised blind bundle exists for this region; "
                 "the raw record text is shown, identity not stripped."]
        if (snap.get("data_flags") or {}).get("estimated"):
            parts.append("### DATA STATUS\nThis region's record is a flagged "
                         "thin-evidence estimate: there is no dedicated "
                         "research dossier for it. Rate what the provided "
                         "text supports; do not treat thin data as either "
                         "safety or danger.")
        if f.get("summary"):
            parts.append("### LOCAL RECORD TEXT (the only provided local "
                         "evidence; the sole item you may list or cite as "
                         "local evidence)\n" + strip_html(f["summary"]))
        if f.get("outOfScopeNotes"):
            parts.append("### DELIBERATELY NOT COUNTED\n"
                         + strip_html(f["outOfScopeNotes"]))
        nat_src = snap.get("country_level_sources_not_local") or []
        if nat_src:
            items = "\n".join("- " + s for s in nat_src)
            parts.append("### COUNTRY-LEVEL RECORD SOURCES - NOT LOCAL "
                         "EVIDENCE\nThese are national links shared by every "
                         "region of this country. They must NOT be listed as "
                         "provided local evidence or cited as local evidence "
                         "in any departure:\n" + items)
        return "\n\n".join(parts)
    if spec["evidence_path"] == "knowledge-only":
        return (
            "### DIVISION: " + spec["name"]
            + f"  (region_id {spec['region_id']})\n\n"
            "DATA STATUS: this region has NO dedicated research dossier and NO "
            "provided local evidence. You are asked for a deliberately "
            "identified, explicitly uncertain model-knowledge assessment of "
            "this actual named region. The record note below is unverified "
            "route-3 estimate text, not verified local evidence:\n"
            + snap.get("record_text_unverified", "")
            + "\n\nProvided local evidence items: NONE. "
            "Country-level sources exist for this country but they are not "
            "local evidence for this region."
        )
    raise ConfigError(f"unknown evidence_path: {spec['evidence_path']}")


def build_region_user_prompt(spec: dict, national: dict) -> str:
    """Region prompt: complete candidate national assessment + local bundle.

    `national` must come from national_result_for() (shadow results only).
    """
    if not isinstance(national, dict) or "baseline" not in national:
        raise FailClosed("region prompt requires a candidate national baseline")
    snap = region_snapshot(spec)
    dossier = render_country_dossier(country_snapshot(national["country_id"]))
    evidence = render_region_evidence(spec, snap)
    allow = snap.get("local_evidence_allowlist") or []
    if allow:
        provided = "\n".join("- " + strip_html(x) for x in allow)
        provided_block = ("Provided local evidence items (the only items "
                          "you may list in `sourced_local_evidence`):\n"
                          + provided)
    else:
        provided_block = ("Provided local evidence items: NONE. "
                          "`sourced_local_evidence` must be an empty list.")
    return (
        "Assess the local difference for the region below.\n\n"
        "## THE CANDIDATE NATIONAL ASSESSMENT (input to hold fixed; produced "
        f"by this instrument's national phase, call(s) "
        f"{', '.join(national['source_call_ids'])} - NOT a published score "
        "and not to be re-rated here)\n"
        "- candidate national score: "
        f"{national['baseline']}\n"
        "- national uncertainty: "
        + national["assessment"]["uncertainty"] + "\n"
        "- national evidence date: "
        + national["assessment"]["evidence_date"] + "\n"
        "- national why: " + national["assessment"]["why"] + "\n\n"
        "### THE COMPLETE NATIONAL DOSSIER (the full national assessment "
        "this region is compared against)\n" + dossier + "\n\n"
        "## THE REGION'S OWN EVIDENCE\n" + evidence + "\n\n"
        + provided_block + "\n\n"
        "## TASK\n\n"
        f"Assess only {spec['name']}'s signed difference from the complete "
        "national assessment above: `local_delta` (positive = safer than the "
        "national assessment, negative = riskier). List every considered "
        "departure with its inheritance and double-counting flags; inherit "
        "national exposure you deliberately did not re-count; keep "
        "uncertainty, evidence dates and visitor applicability explicit.\n\n"
        "Reply with only the single JSON object described in the output "
        f"format, with \"assessment_mode\": \"{expected_mode(spec)}\" and "
        f"\"region_id\": \"{spec['region_id']}\"."
    )


def expected_mode(spec: dict) -> str:
    return ("model_knowledge" if spec["evidence_path"] == "knowledge-only"
            else "sourced")


# --------------------------------------------------------------------------- #
# Output validation (scale + schema; fail closed)
# --------------------------------------------------------------------------- #

def _reject_constant(name):
    raise ValidationError(f"invalid JSON constant: {name}")


def parse_model_json(text):
    if not isinstance(text, str) or not text.strip():
        raise ValidationError("empty model output")
    decoder = json.JSONDecoder(parse_constant=_reject_constant)
    idx = 0
    last_err = None
    while True:
        start = text.find("{", idx)
        if start < 0:
            raise ValidationError(last_err or "no JSON object in model output")
        try:
            obj, _ = decoder.raw_decode(text[start:])
        except (json.JSONDecodeError, ValidationError) as e:
            if isinstance(e, ValidationError):
                last_err = str(e)
            idx = start + 1
            continue
        if isinstance(obj, dict):
            return obj
        idx = start + 1


def _finite_number(value, lo, hi, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{field} is not a number: {value!r}")
    v = float(value)
    if not math.isfinite(v):
        raise ValidationError(f"{field} is not finite: {value!r}")
    if not (lo <= v <= hi):
        raise ValidationError(f"{field} out of scale [{lo}, {hi}]: {v}")
    return v


def _nonempty_str(value, field, maxlen=4000):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} missing or empty")
    if len(value) > maxlen:
        raise ValidationError(f"{field} too long")
    return value.strip()


NATIONAL_REQUIRED = ("score", "uncertainty", "evidence_date",
                     "visitor_applicability", "social_friction",
                     "social_hostility", "state_threat_framing", "why")

REGION_REQUIRED = ("assessment_mode", "region_id", "local_delta", "departures",
                   "sourced_local_evidence", "knowledge_statements",
                   "knowledge_confidence", "knowledge_is_unverified",
                   "inherited_national_exposure", "uncertainty",
                   "evidence_date", "visitor_applicability", "social_friction",
                   "social_hostility", "state_threat_framing", "notes")

DEPARTURE_REQUIRED = ("fact", "local_evidence", "direction", "magnitude",
                      "visitor_applicability", "already_in_national_bundle",
                      "counted_in_delta", "evidence_date", "uncertainty")


def validate_national(obj) -> dict:
    if not isinstance(obj, dict):
        raise ValidationError("national output is not an object")
    for key in NATIONAL_REQUIRED:
        if key not in obj:
            raise ValidationError(f"national output missing field: {key}")
    if "score_a" in obj or "score_b" in obj:
        raise ValidationError("two-dossier fields in single-dossier output")
    score = _finite_number(obj["score"], 0.0, 1.0, "score")
    out = {"score": score}
    for key in NATIONAL_REQUIRED[1:]:
        out[key] = _nonempty_str(obj[key], key)
    return out


def validate_region(obj, spec: dict, snapshot: dict) -> dict:
    if not isinstance(obj, dict):
        raise ValidationError("region output is not an object")
    for key in REGION_REQUIRED:
        if key not in obj:
            raise ValidationError(f"region output missing field: {key}")
    if "score_a" in obj or "score_b" in obj:
        raise ValidationError("two-dossier fields in single-dossier output")
    if obj["region_id"] != spec["region_id"]:
        raise ValidationError(
            f"region_id mismatch: got {obj['region_id']!r}, "
            f"expected {spec['region_id']!r}")
    mode = expected_mode(spec)
    if obj["assessment_mode"] != mode:
        raise ValidationError(
            f"assessment_mode mismatch: got {obj['assessment_mode']!r}, "
            f"expected {mode!r}")
    delta = _finite_number(obj["local_delta"], -1.0, 1.0, "local_delta")
    out = {
        "assessment_mode": mode,
        "region_id": obj["region_id"],
        "local_delta": delta,
        "sourced_local_evidence": obj["sourced_local_evidence"],
        "knowledge_statements": obj["knowledge_statements"],
        "knowledge_confidence": obj["knowledge_confidence"],
        "knowledge_is_unverified": obj["knowledge_is_unverified"],
        "inherited_national_exposure": obj["inherited_national_exposure"],
    }
    for key in ("uncertainty", "evidence_date", "visitor_applicability",
                "social_friction", "social_hostility", "state_threat_framing",
                "notes"):
        out[key] = _nonempty_str(obj[key], key)
    if not isinstance(out["inherited_national_exposure"], list) or not all(
            isinstance(x, str) and x.strip()
            for x in out["inherited_national_exposure"]):
        raise ValidationError("inherited_national_exposure must be a "
                              "non-empty list of strings")
    if not isinstance(out["sourced_local_evidence"], list) or not all(
            isinstance(x, str) for x in out["sourced_local_evidence"]):
        raise ValidationError("sourced_local_evidence must be a list of strings")
    if not isinstance(out["knowledge_statements"], list) or not all(
            isinstance(x, str) for x in out["knowledge_statements"]):
        raise ValidationError("knowledge_statements must be a list of strings")
    if not isinstance(obj["departures"], list):
        raise ValidationError("departures must be a list")
    # Fabrication guard for EVERY mode: evidence claims may only repeat items
    # actually provided in the snapshot (country-level URLs can never be
    # relabelled local evidence because they are not in the allowlist).
    allow = snapshot.get("local_evidence_allowlist") or []
    fake = [x for x in out["sourced_local_evidence"] if x not in allow]
    if fake:
        raise ValidationError(
            "record cites evidence not provided in the snapshot "
            f"(allowlist has {len(allow)} item(s)): {fake!r}")
    if mode == "model_knowledge":
        if out["knowledge_is_unverified"] is not True:
            raise ValidationError("knowledge-only record must set "
                                  "knowledge_is_unverified: true")
        if out["knowledge_confidence"] not in ("low", "medium"):
            raise ValidationError("knowledge-only record must declare "
                                  "knowledge_confidence low or medium")
        if not out["knowledge_statements"]:
            raise ValidationError("knowledge-only record needs "
                                  "knowledge_statements")
        if obj["departures"]:
            raise ValidationError("knowledge-only record must keep departures "
                                  "empty (no sourced departures exist)")
    out["departures"] = []
    for dep in obj["departures"]:
        if not isinstance(dep, dict):
            raise ValidationError("departure is not an object")
        for key in DEPARTURE_REQUIRED:
            if key not in dep:
                raise ValidationError(f"departure missing field: {key}")
        _nonempty_str(dep["fact"], "departure.fact")
        direction = dep["direction"]
        if direction not in ("safer", "riskier"):
            raise ValidationError(f"departure.direction invalid: {direction!r}")
        _finite_number(dep["magnitude"], 0.0, 1.0, "departure.magnitude")
        if not isinstance(dep["already_in_national_bundle"], bool):
            raise ValidationError("departure.already_in_national_bundle "
                                  "must be boolean")
        if not isinstance(dep["counted_in_delta"], bool):
            raise ValidationError("departure.counted_in_delta must be boolean")
        for key in ("local_evidence", "visitor_applicability", "evidence_date",
                    "uncertainty"):
            _nonempty_str(dep[key], f"departure.{key}")
        dep_ev = str(dep["local_evidence"]).strip()
        if dep_ev.lower() != "none provided" and dep_ev not in allow:
            raise ValidationError(
                "departure.local_evidence is not provided local evidence "
                f"(fabrication guard): {dep_ev[:160]!r}")
        out["departures"].append({
            "fact": str(dep["fact"]).strip(),
            "local_evidence": str(dep["local_evidence"]).strip(),
            "direction": direction,
            "magnitude": float(dep["magnitude"]),
            "visitor_applicability": str(dep["visitor_applicability"]).strip(),
            "already_in_national_bundle": dep["already_in_national_bundle"],
            "counted_in_delta": dep["counted_in_delta"],
            "evidence_date": str(dep["evidence_date"]).strip(),
            "uncertainty": str(dep["uncertainty"]).strip(),
        })
    return out


# --------------------------------------------------------------------------- #
# Call plan + dry-run (deterministic, offline)
# --------------------------------------------------------------------------- #

def plan_calls() -> list:
    calls = []
    for iso3 in COUNTRY_IDS:
        for d in range(1, N_NATIONAL_DRAWS + 1):
            calls.append({
                "call_id": f"NAT-{iso3}-d{d}",
                "phase": "national",
                "subject_id": iso3,
                "draw": d,
            })
    for spec in REGION_SPECS:
        for d in range(1, N_REGION_DRAWS + 1):
            calls.append({
                "call_id": f"REG-{spec['region_id']}-d{d}",
                "phase": "region",
                "subject_id": spec["region_id"],
                "draw": d,
            })
    if len(calls) > MAX_CALLS:
        raise FailClosed("call plan exceeds ceiling")
    return calls


def _write(path: Path, text: str) -> None:
    """All experiment writes go through here, confined to this directory
    (defense in depth: callers additionally constrain their roots; the test
    suite asserts both layers)."""
    dest = Path(path)
    if not dest.is_absolute():
        dest = HERE / dest
    dest = dest.resolve()
    here = str(HERE.resolve())
    if str(dest) != here and not str(dest).startswith(here + "/"):
        raise FailClosed(
            f"refusing to write outside the experiment directory: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")


def _constrain_out(out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = HERE / out_dir
    out_dir = out_dir.resolve()
    here = str(HERE.resolve())
    if str(out_dir) != here and not str(out_dir).startswith(here + "/"):
        raise FailClosed(
            f"refusing to write outside the experiment directory: {out_dir}")
    return out_dir


def dry_run(out_dir: Path, national_results=None) -> dict:
    """Render prompts + snapshots + hashes. No network, no model, no numbers
    invented here: region prompts render only when a national-results file
    supplies the candidate baseline; otherwise the call is recorded as
    pending (fail closed)."""
    out_dir = _constrain_out(out_dir)
    prompts = out_dir / "prompts"
    snaps = out_dir / "snapshots"

    nat_system = build_national_system_prompt()
    reg_system = build_region_system_prompt()
    _write(prompts / "system_national.txt", nat_system)
    _write(prompts / "system_region.txt", reg_system)

    baselines = {}
    if national_results:
        for iso3 in COUNTRY_IDS:
            try:
                baselines[iso3] = national_result_for(iso3, national_results)
            except FailClosed:
                pass  # region calls for that country stay pending below

    entries = []
    for call in plan_calls():
        if call["phase"] == "national":
            snap = country_snapshot(call["subject_id"])
            user = build_national_user_prompt(call["subject_id"])
            snap_file = f"snapshots/country_{call['subject_id']}.json"
            user_file = f"prompts/user_{call['call_id']}.txt"
            _write(out_dir / snap_file, canonical_json(snap))
            _write(out_dir / user_file, user)
            entries.append({
                **call,
                "evidence_path": "identity-stripped-blind",
                "snapshot_file": snap_file,
                "snapshot_sha256": sha(canonical_json(snap)),
                "user_prompt_file": user_file,
                "user_sha256": sha(user),
                "system_sha256": sha(nat_system),
                "status": "rendered",
            })
        else:
            spec = next(s for s in REGION_SPECS
                        if s["region_id"] == call["subject_id"])
            snap = region_snapshot(spec)
            snap_file = f"snapshots/region_{spec['region_id']}.json"
            _write(out_dir / snap_file, canonical_json(snap))
            national = baselines.get(spec["country_id"])
            if national is None:
                entries.append({
                    **call,
                    "evidence_path": spec["evidence_path"],
                    "snapshot_file": snap_file,
                    "snapshot_sha256": sha(canonical_json(snap)),
                    "user_prompt_file": None,
                    "user_sha256": None,
                    "system_sha256": sha(reg_system),
                    "status": "pending_national_baseline",
                })
            else:
                user = build_region_user_prompt(spec, national)
                user_file = f"prompts/user_{call['call_id']}.txt"
                _write(out_dir / user_file, user)
                entries.append({
                    **call,
                    "evidence_path": spec["evidence_path"],
                    "snapshot_file": snap_file,
                    "snapshot_sha256": sha(canonical_json(snap)),
                    "user_prompt_file": user_file,
                    "user_sha256": sha(user),
                    "system_sha256": sha(reg_system),
                    "status": "rendered",
                })

    manifest = {
        "instrument": {
            "id": INSTRUMENT_ID,
            "version": INSTRUMENT_VERSION,
            "scale_contract": SCALE_CONTRACT,
            "mode": "dry-run",
            "network": False,
            "provider_enabled": False,
        },
        "planned_execution": {
            "model": PLANNED_MODEL,
            "settings": PLANNED_SETTINGS,
            "max_calls": MAX_CALLS,
            "token_caps": {"input": IN_TOKEN_CAP, "output": OUT_TOKEN_CAP},
            "note": "candidate caps and rater require separate review before "
                    "any provider execution",
        },
        "inputs_sha256": {
            "data/countries.json": file_sha256(COUNTRIES_PATH),
            "data/admin1.json": file_sha256(ADMIN1_PATH),
            "research/outing-risk-taxonomy.md": file_sha256(TAXONOMY_PATH),
        },
        "systems": {"national": sha(nat_system), "region": sha(reg_system)},
        "national_baselines_read_from_results": {
            iso3: {"baseline": b["baseline"],
                   "source_call_ids": b["source_call_ids"]}
            for iso3, b in sorted(baselines.items())
        },
        "calls": entries,
    }
    _write(out_dir / "manifest.json", canonical_json(manifest))
    return manifest


# --------------------------------------------------------------------------- #
# Assemble: estimates from shadow results only (fail closed per row)
# --------------------------------------------------------------------------- #

def assemble(results_path: Path, out_path: Path) -> list:
    rows = read_results_rows(results_path)

    out_rows = []
    # 1) candidate national baselines: complete, deduplicated, single-run,
    #    validated national draws only - incomplete or mixed runs are
    #    reported as failures, never silently averaged.
    baseline_by_country = {}
    for iso3 in COUNTRY_IDS:
        try:
            info = national_baseline_from_rows(rows, iso3)
        except FailClosed as e:
            out_rows.append({
                "kind": "national_baseline",
                "country_id": iso3,
                "error": str(e),
            })
            continue
        baseline_by_country[iso3] = info["baseline"]
        out_rows.append({
            "kind": "national_baseline",
            "country_id": iso3,
            "candidate_national_score": info["baseline"],
            "scores": info["scores"],
            "n_draws": info["n_draws"],
            "source_call_ids": info["source_call_ids"],
            "provenance": "candidate national assessment from shadow "
                          "results (never a published score)",
        })

    # 2) region estimates: baseline + delta, both from shadow results only
    spec_by_id = {s["region_id"]: s for s in REGION_SPECS}
    for row in rows:
        if row.get("phase") != "region":
            continue
        rid = row.get("region_id")
        spec = spec_by_id.get(rid)
        base = {
            "kind": "region_estimate",
            "region_id": rid,
            "country_id": row.get("country_id"),
            "call_id": row.get("call_id"),
        }
        if spec is None:
            out_rows.append({**base, "error": "unknown region_id"})
            continue
        if row.get("country_id") not in (None, spec["country_id"]):
            out_rows.append({**base, "error": "country_id mismatch for "
                                              f"{rid}"})
            continue
        if row.get("status") != "ok":
            out_rows.append({**base, "error": row.get("error")
                             or "missing model output (status not ok)"})
            continue
        try:
            snap = region_snapshot(spec)
            parsed = validate_region(row.get("response"), spec, snap)
        except (ValidationError, ConfigError) as e:
            out_rows.append({**base, "error": str(e)})
            continue
        national_score = baseline_by_country.get(spec["country_id"])
        if national_score is None:
            out_rows.append({**base, "error": "missing candidate national "
                                              "baseline for "
                                              f"{spec['country_id']}"})
            continue
        estimate = round(national_score + parsed["local_delta"], 6)
        if not math.isfinite(estimate) or not (0.0 <= estimate <= 1.0):
            # P0 regression guard: never emit (and never clamp) an
            # out-of-scale estimate - an error record instead.
            out_rows.append({**base, "error":
                             f"computed local estimate {estimate} outside "
                             "the [0.0, 1.0] scale; rejected without "
                             "clamping"})
            continue
        out_rows.append({
            **base,
            "evidence_path": spec["evidence_path"],
            "candidate_national_score": national_score,
            "local_delta": parsed["local_delta"],
            "local_estimate": estimate,
            "assessment_mode": parsed["assessment_mode"],
            "uncertainty": parsed["uncertainty"],
            "evidence_date": parsed["evidence_date"],
            "source_call_ids": [row.get("call_id")],
        })

    _write(_constrain_out(out_path),
           "".join(json.dumps(r, ensure_ascii=False) + "\n"
                   for r in out_rows))
    return out_rows


# --------------------------------------------------------------------------- #
# Provider execution: UNCONDITIONALLY REMOVED before methodological review.
# No network code exists in this module; no flag or env var can re-enable it.
# --------------------------------------------------------------------------- #

def execute(*_args, **_kwargs) -> None:
    """The live provider path has been removed pending methodological review.

    Old invocations - including ones that set the former --allow-provider
    flag and NEXT_INSTRUMENT_ALLOW_PROVIDER=reviewed - must keep failing
    closed, so this stub raises unconditionally.
    """
    raise ProviderDisabledError(
        "provider execution was unconditionally disabled and its network "
        "code removed pending methodological review; no flag or environment "
        "variable can enable it (see BLOCKERS.md)")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="instrument.py",
                                 description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_dry = sub.add_parser("dry-run", help="offline deterministic render")
    p_dry.add_argument("--out", default=str(HERE / "out" / "dry-run"))
    p_dry.add_argument("--national-results", default=None,
                       help="optional shadow results file supplying the "
                            "candidate national baselines for region prompts")
    p_asm = sub.add_parser("assemble",
                           help="compute estimates from shadow results only")
    p_asm.add_argument("--results", required=True)
    p_asm.add_argument("--out", required=True)
    p_exe = sub.add_parser("execute",
                           help="REMOVED: always refuses, no network")
    p_exe.add_argument("--endpoint", required=True)
    p_exe.add_argument("--model", default=PLANNED_MODEL)
    p_exe.add_argument("--results", required=True)
    p_exe.add_argument("--allow-provider", action="store_true")
    args = ap.parse_args(argv)

    try:
        if args.cmd == "dry-run":
            nr = Path(args.national_results) if args.national_results else None
            manifest = dry_run(args.out, national_results=nr)
            rendered = sum(1 for c in manifest["calls"]
                           if c["status"] == "rendered")
            pending = sum(1 for c in manifest["calls"]
                          if c["status"] == "pending_national_baseline")
            print(f"DRY-RUN OK: {len(manifest['calls'])} planned calls, "
                  f"{rendered} rendered, {pending} pending national "
                  f"baseline; no network used; out={args.out}")
        elif args.cmd == "assemble":
            rows = assemble(args.results, args.out)
            print(f"ASSEMBLE OK: {len(rows)} rows -> {args.out}")
        elif args.cmd == "execute":
            execute(args.endpoint, args.model, args.results,
                    args.allow_provider)
            print("EXECUTE OK")
    except (FailClosed, ValidationError, ConfigError,
            ProviderDisabledError) as e:
        print(f"STOPPED ({type(e).__name__}): {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
