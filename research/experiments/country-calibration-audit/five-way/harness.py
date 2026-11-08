#!/usr/bin/env python3
"""Offline five-way comparison harness for the country-calibration audit.

One call rates FIVE blinded dossiers at once and answers with one strict JSON
object holding five {slot, score, why} entries. Two schedule modes:

  * country mode  — five countries drawn once per call from five overlapping
    percentile bands of the current scores in data/countries.json (bands
    [0,30] [20,50] [35,65] [50,80] [70,100]; one country per band; no
    country twice inside one call); US-locked mode forces ISO3 USA into its
    own band's slot in every call. Each dossier carries the blinded
    SUBNATIONAL-REGIMES paragraph from frozen/diversity/ (field
    `blindDiversity`; the plain `diversity` text never enters a prompt) and
    the prompt instructs that where local regimes vary the country's rating
    reflects the mean local regime in addition to the national picture.
  * admin1 mode   — five divisions of ONE country, identities withheld; each
    division dossier carries the parent's blind national framework text
    (blindSummary/blindTangential/blindLocalsOnly/blindSourceSummaries,
    the sources capped at 8), NEVER the parent's score and NEVER the diversity
    paragraph.

Rubric consistency: the production rating rules (RATING_RULES), the scale
blocks and the taxonomy reference are reused verbatim from
tools/blind_pairwise.py, so the rubric stays r2026-11-13-consistent. Only the
five-way framing, the mean-local-regime instruction, the five-way output
contract and the shuffle are added. Existing scores never enter a prompt.

Offline guarantees (this file, by construction):
  * no network code, no credentials, no provider call implementation;
  * the runner is disabled by default — without an explicit --execute AND an
    injected --provider module:function adapter, `run` refuses before touching
    the filesystem;
  * schedule builders write only under this experiment's frozen/ directory;
  * tests write only to temporary directories.

Accounting (execute path only): exact Decimal cost accumulation from the
adapter's provider usage (`usage.cost_usd`), a locally enforced MAX_USD guard,
stop on unknown charge, ONE shared lock file, and every attempt persisted to
runs/<run-id>/ with the raw response preserved verbatim. Failures never retry.

Usage:
    python3 harness.py schedule-country --n-calls 10 --seed 20261119
    python3 harness.py schedule-country --n-calls 10 --seed 20261119 --no-us-lock
    python3 harness.py schedule-admin1 --iso3 USA --n-calls 5 --seed 20261119
    python3 harness.py verify --schedule frozen/schedule_country.json
    python3 harness.py run --schedule frozen/schedule_country.json --run-id r1
        # refuses (exit 2) unless --execute and --provider pkg.mod:func are given
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import random
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.dont_write_bytecode = True   # never write tools/__pycache__

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EXP = "research/experiments/country-calibration-audit/five-way"

# All paths are module globals so tests can repoint them at temporary fixtures.
COUNTRIES_PATH = ROOT / "data" / "countries.json"
ADMIN1_PATH = ROOT / "data" / "admin1.json"
TAXONOMY_PATH = ROOT / "research" / "outing-risk-taxonomy.md"
FROZEN_DIR = HERE / "frozen"
DIVERSITY_DIR = FROZEN_DIR / "diversity"
RUNS_DIR = HERE / "runs"
LOCK_PATH = HERE / "accounting.lock"

sys.path.insert(0, str(ROOT / "tools"))
import blind_pairwise as BP  # noqa: E402  (constants only; no I/O at import time)

# Production rubric pieces, reused verbatim (r2026-11-13).
RATING_RULES = BP.RATING_RULES
RUBRIC_VERSION = BP.RUBRIC_VERSION
REQUIRED_BLIND = BP.REQUIRED_BLIND
TERRITORY_ISOS = BP.TERRITORY_ISOS

# Diagnostic prompt hooks in tools/blind_pairwise.py change the rating rules'
# wording. The five-way harness must build the production rules as-is, so it
# refuses to run while any of them is set.
FORBIDDEN_ENV = ("STRIP_RULE_10B", "REVERT_ENDPOINT", "RESTORE_ARCHIVED_WORDING")

# Stratification: five closed percentile bands, in draw order.
BANDS = ((0, 30), (20, 50), (35, 65), (50, 80), (70, 100))
US_ISO3 = "USA"
SLOT_COUNT = 5

# Parent national framework shown with every ADM1 dossier (design enumeration;
# blindOutOfScope and every score/identity field are deliberately excluded).
PARENT_FRAMEWORK_FIELDS = ("blindSummary", "blindTangential", "blindLocalsOnly")
PARENT_FRAMEWORK_SOURCES_CAP = 8

# Division dossier content: the blind mirrors only. name / summary /
# modelContext / outOfScopeNotes are unblinded identity-carrying fields and
# never enter a prompt.
ADM1_DIVISION_FIELDS = ("blindSummary", "blindSourceSummaries", "blindTangential",
                        "blindLocalsOnly", "blindOutOfScope")

SCHEDULE_KINDS = ("country", "admin1")
SCHEDULE_VERSION = 1
RESPONSE_KEYS = frozenset({"results"})
ENTRY_KEYS = frozenset({"slot", "score", "why"})
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_USD = Decimal("10.00")        # locally enforced guard (see README)
LOCK_HOLDER_PREFIX = "five-way:"


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #

class HarnessError(Exception):
    """Fail-closed input, frozen-artifact or state error."""


class RunnerDisabled(HarnessError):
    """The runner refused: no --execute (or no provider adapter)."""


class LockHeld(HarnessError):
    """The ONE shared accounting lock is held by another holder."""


class UnknownCharge(HarnessError):
    """Provider usage cannot be priced exactly — stop the run."""


class BudgetExceeded(HarnessError):
    """The local USD guard has been reached — stop the run."""


class OutputRejected(HarnessError):
    """The model response violates the five-way output contract — stop."""


class StopRun(HarnessError):
    """Execution stop (e.g. the provider adapter failed). Never retried."""


# --------------------------------------------------------------------------- #
# Small utilities
# --------------------------------------------------------------------------- #

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean(value) -> str:
    """Strip HTML tags and collapse whitespace (production dossier cleaner)."""
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fmt_decimal(value: Decimal) -> str:
    """Plain (non-scientific) exact decimal string for persisted accounting."""
    return format(value, "f")


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def write_json(path: Path, doc) -> None:
    atomic_write(path, (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))


def check_diag_env() -> None:
    on = [v for v in FORBIDDEN_ENV if os.environ.get(v)]
    if on:
        raise HarnessError(
            f"diagnostic prompt hook(s) set ({', '.join(on)}); the five-way harness "
            "always builds the production r2026-11-13 rules — unset them and re-run")


def _require_int(value, name: str, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise HarnessError(f"{name} must be an integer >= {minimum}, got {value!r}")
    return value


# --------------------------------------------------------------------------- #
# Inputs (read-only)
# --------------------------------------------------------------------------- #

def load_countries() -> dict:
    if not Path(COUNTRIES_PATH).is_file():
        raise HarnessError(f"missing {COUNTRIES_PATH}")
    try:
        doc = json.loads(Path(COUNTRIES_PATH).read_text(encoding="utf-8"))
    except ValueError as e:
        raise HarnessError(f"{COUNTRIES_PATH} is not valid JSON: {e}")
    if not isinstance(doc, dict) or not doc:
        raise HarnessError(f"{COUNTRIES_PATH} must be a non-empty object")
    return doc


def load_admin1() -> dict:
    if not Path(ADMIN1_PATH).is_file():
        raise HarnessError(f"missing {ADMIN1_PATH}")
    try:
        doc = json.loads(Path(ADMIN1_PATH).read_text(encoding="utf-8"))
    except ValueError as e:
        raise HarnessError(f"{ADMIN1_PATH} is not valid JSON: {e}")
    if not isinstance(doc, dict) or not doc:
        raise HarnessError(f"{ADMIN1_PATH} must be a non-empty object")
    return doc


def load_taxonomy() -> str:
    if not Path(TAXONOMY_PATH).is_file():
        raise HarnessError(f"missing {TAXONOMY_PATH}")
    return Path(TAXONOMY_PATH).read_text(encoding="utf-8")


def _load_diversity_dir() -> dict:
    """Merge every frozen/diversity/*.json batch into {ISO3: record}.

    Each batch file is an object keyed by ISO3 whose values carry at least a
    non-empty `blindDiversity` string. The plain `diversity` field (and any
    other field) is ignored here — only blinded text is ever read.
    """
    if not Path(DIVERSITY_DIR).is_dir():
        raise HarnessError(
            f"missing diversity directory {DIVERSITY_DIR}; frozen/diversity/ must "
            "hold the blinded SUBNATIONAL-REGIMES batches (field blindDiversity)")
    merged: dict[str, str] = {}
    files = sorted(Path(DIVERSITY_DIR).glob("*.json"))
    if not files:
        raise HarnessError(f"{DIVERSITY_DIR} contains no *.json diversity batches")
    for path in files:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as e:
            raise HarnessError(f"{path} is not valid JSON: {e}")
        if not isinstance(doc, dict):
            raise HarnessError(f"{path} must be an object keyed by ISO3")
        for key, rec in doc.items():
            if not isinstance(rec, dict):
                raise HarnessError(f"{path}: entry {key!r} is not an object")
            blind = rec.get("blindDiversity")
            if not isinstance(blind, str) or not blind.strip():
                raise HarnessError(f"{path}: entry {key!r} has no non-empty blindDiversity")
            iso3 = str(key).upper()
            if iso3 in merged and merged[iso3] != clean(blind):
                raise HarnessError(f"conflicting blindDiversity for {iso3} in {path}")
            merged[iso3] = clean(blind)
    return merged


def load_diversity(iso3: str) -> str:
    """The blinded subnational-regimes paragraph for one country (fail closed)."""
    merged = _load_diversity_dir()
    if iso3 not in merged:
        raise HarnessError(
            f"no blindDiversity paragraph for {iso3} under {DIVERSITY_DIR}; "
            "populate frozen/diversity/ before building the schedule")
    return merged[iso3]


# --------------------------------------------------------------------------- #
# Percentile bands and eligibility
# --------------------------------------------------------------------------- #

def percentile_ranks(countries: dict) -> dict[str, float]:
    """Average-rank percentile over every record in data/countries.json.

    p = 100 * avg_rank / (n - 1) with ranks zero-based; tied scores share the
    average rank. Inclusive endpoints: the lowest record sits at 0.0 and the
    highest at 100.0 (when unique). Band membership uses lo <= p <= hi.
    """
    scored = []
    for iso3, rec in countries.items():
        raw = (rec or {}).get("score")
        if isinstance(raw, bool) or raw is None or str(raw).strip() == "":
            raise HarnessError(f"{iso3}: missing numeric score for stratification")
        try:
            value = float(raw)
        except (TypeError, ValueError):
            raise HarnessError(f"{iso3}: non-numeric score {raw!r}")
        if not math.isfinite(value):
            raise HarnessError(f"{iso3}: non-finite score {raw!r}")
        scored.append((iso3, value))
    n = len(scored)
    if n < 2:
        raise HarnessError("need at least two scored records to form percentile bands")
    scored.sort(key=lambda kv: kv[1])
    ranks: dict[str, float] = {}
    i = 0
    while i < n:
        j = i
        while j < n and scored[j][1] == scored[i][1]:
            j += 1
        avg_rank = (i + (j - 1)) / 2.0
        pct = 100.0 * avg_rank / (n - 1)
        for k in range(i, j):
            ranks[scored[k][0]] = pct
        i = j
    return ranks


def _has_field(rec: dict, field: str) -> bool:
    value = rec.get(field)
    if isinstance(value, list):
        return bool(value) and all(str(x).strip() for x in value)
    return bool(str(value or "").strip())


def eligible_countries(countries: dict) -> list[str]:
    """Blind-complete, non-territory ISO3s, sorted (production parity)."""
    out = []
    for iso3 in sorted(countries):
        if iso3 in TERRITORY_ISOS:
            continue
        rec = countries[iso3]
        required = [f for f in REQUIRED_BLIND
                    if not (f == "blindOutOfScope"
                            and not str(rec.get("outOfScopeNotes", "")).strip())]
        if all(_has_field(rec, f) for f in required):
            out.append(iso3)
    if not out:
        raise HarnessError("no eligible countries (blind fields missing?)")
    return out


def eligible_divisions(admin1: dict, iso3: str) -> list[str]:
    """Scored, blind-complete division record ids of ONE parent, sorted."""
    out = []
    for rid in sorted(admin1):
        rec = admin1[rid]
        if rec.get("iso3") != iso3:
            continue
        score = rec.get("score")
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            continue
        required = [f for f in REQUIRED_BLIND
                    if not (f == "blindOutOfScope"
                            and not str(rec.get("outOfScopeNotes", "")).strip())]
        if all(_has_field(rec, f) for f in required):
            out.append(rid)
    return out


def bands_containing(pct: float) -> list[int]:
    return [b for b, (lo, hi) in enumerate(BANDS) if lo <= pct <= hi]


def _draw_call(rng: random.Random, eligible: list[str],
               pcts: dict[str, float], us_locked: bool) -> tuple[list, dict]:
    """One call: one country per band without overlap, then shuffle to slots.

    Returns (selection in band order, slot_map display-slot 1..5 -> entry).
    US-locked: USA occupies the FIRST band whose range contains its percentile;
    the other four bands each draw one country excluding USA.
    """
    selected: dict[int, str] = {}
    if us_locked:
        if US_ISO3 not in eligible:
            raise HarnessError(f"US-locked mode requires {US_ISO3} in the eligible pool")
        hits = bands_containing(pcts[US_ISO3])
        if not hits:
            raise HarnessError(f"{US_ISO3} percentile {pcts[US_ISO3]:.4f} falls in no band")
        selected[hits[0]] = US_ISO3
    for band, (lo, hi) in enumerate(BANDS):
        if band in selected:
            continue
        pool = [iso for iso in eligible
                if lo <= pcts[iso] <= hi and iso not in selected.values()]
        if not pool:
            raise HarnessError(
                f"band [{lo},{hi}] has no eligible country left "
                f"(selected so far: {sorted(selected.values())})")
        pool.sort()
        selected[band] = rng.choice(pool)
    selection = [{"band": list(BANDS[b]), "iso3": selected[b],
                  "forced_usa": us_locked and selected[b] == US_ISO3}
                 for b in range(len(BANDS))]
    entries = [dict(e) for e in selection]
    rng.shuffle(entries)
    slot_map = {str(s): entries[s - 1] for s in range(1, SLOT_COUNT + 1)}
    return selection, slot_map


# --------------------------------------------------------------------------- #
# System prompts (production rubric reused verbatim)
# --------------------------------------------------------------------------- #

def _production_scale(taxonomy: str, admin1: bool) -> str:
    """The exact production `## The scale` block, cut from the production
    system prompt so wording can never drift from tools/blind_pairwise.py."""
    if admin1:
        dummy = {"name": "?", "score": 0.0, "sources": []}
        full = BP.build_admin1_system_prompt(taxonomy, dummy, "ZZZ", {})
    else:
        full = BP.build_system_prompt(taxonomy)
    start = full.index("## The scale")
    end = full.index(RATING_RULES, start)
    return full[start:end].rstrip()


def _taxonomy_section(taxonomy: str) -> str:
    return ("---\n\n# Reference documentation: the outing-risk taxonomy\n\n"
            + taxonomy.strip() + "\n")


FIVE_WAY_OUTPUT_FORMAT = """\
## Output format

Reply with **only** a single JSON object, no prose before or after it:

{"results": [
  {"slot": 1, "score": <float 0.0-1.0>, "why": "<= 40 words, the decisive differences"},
  {"slot": 2, "score": <float 0.0-1.0>, "why": "<= 40 words, the decisive differences"},
  {"slot": 3, "score": <float 0.0-1.0>, "why": "<= 40 words, the decisive differences"},
  {"slot": 4, "score": <float 0.0-1.0>, "why": "<= 40 words, the decisive differences"},
  {"slot": 5, "score": <float 0.0-1.0>, "why": "<= 40 words, the decisive differences"}
]}

The object has exactly one key, "results", holding exactly five entries — one per
dossier, with `slot` matching the dossier number (1-5) and every slot appearing
exactly once. All scores are on the same 0.00-1.00 scale described above,
**higher is safer**; give two decimal places. Rate each dossier on its own merits
against the scale — do not force a difference, and do not let the order of
presentation or the other dossiers influence a rating.
"""


def build_country_system(taxonomy: str | None = None) -> str:
    check_diag_env()
    taxonomy = load_taxonomy() if taxonomy is None else taxonomy
    scale = _production_scale(taxonomy, admin1=False)
    return f"""\
You are an expert assessor of travel risk for transgender people. You will be given five
anonymised research dossiers, numbered 1 to 5. Each describes one jurisdiction. You do not
know which jurisdictions they are, and you must not try to guess: your rating must follow
from the documented facts alone.

Your task: rate **each** dossier on the scale below, independently, as the risk faced by a
**transgender visitor** to that jurisdiction if they are discovered or outed there.

{scale}

{RATING_RULES}

## Five-way comparison

Rate all five dossiers in a single response, one entry per dossier.

Where local regimes vary within a jurisdiction, the country's rating should reflect the
mean local regime in addition to the national picture. Each dossier carries a blinded
SUBNATIONAL REGIMES paragraph; weigh it so that the rating reflects the mean local
regime in addition to the national picture.

{_taxonomy_section(taxonomy)}
---

{FIVE_WAY_OUTPUT_FORMAT}"""


def build_admin1_system(taxonomy: str | None = None) -> str:
    check_diag_env()
    taxonomy = load_taxonomy() if taxonomy is None else taxonomy
    scale = _production_scale(taxonomy, admin1=True)
    return f"""\
You are an expert assessor of travel risk for transgender people. You will be given five
anonymised dossiers, numbered 1 to 5. Each describes one first-level administrative
division of the SAME country. Identities are withheld: you are not told which country or
which divisions these are, and you must not try to guess. No existing score for any
jurisdiction is provided — derive every number from the documented facts and the scale
description alone.

Your task: rate **each** dossier on the scale below, independently, as the risk faced by a
**transgender visitor** there if they are discovered or outed there.

{scale}

{RATING_RULES}

## Five-way comparison

Rate all five dossiers in a single response, one entry per dossier.

Where local regimes vary within a division, the division's rating should reflect the mean
local regime in addition to the national picture. Each dossier carries the same blinded
national-framework context plus that division's own evidence; weigh local-regime variation
so that the division's rating reflects the mean local regime in addition to the national
picture.

{_taxonomy_section(taxonomy)}
---

{FIVE_WAY_OUTPUT_FORMAT}"""


# --------------------------------------------------------------------------- #
# Dossiers and user prompts (identity-stripped)
# --------------------------------------------------------------------------- #

def render_country_dossier(iso3: str, countries: dict) -> str:
    """Blinded country dossier: blind mirrors + the blinded regimes paragraph.

    Never includes: name, ISO3, score, band, rank, `comparisons`, `sources`
    URLs, `summary` (unblinded) or any other non-blind field.
    """
    rec = countries.get(iso3)
    if not isinstance(rec, dict):
        raise HarnessError(f"no country record for {iso3}")
    parts = [f"### ASSESSMENT\n{clean(rec.get('blindSummary'))}"]
    parts.append(f"### SUBNATIONAL REGIMES\n{load_diversity(iso3)}")
    ss = rec.get("blindSourceSummaries")
    if isinstance(ss, list) and ss:
        items = "\n".join(f"- {clean(x)}" for x in ss if str(x).strip())
        if items:
            parts.append(f"### SOURCE EVIDENCE\n{items}")
    if _has_field(rec, "blindTangential"):
        parts.append("### SECONDARY / SITUATIONAL FACTORS\n"
                     + clean(rec.get("blindTangential")))
    if _has_field(rec, "blindLocalsOnly"):
        parts.append("### AFFECTS RESIDENTS MORE THAN VISITORS\n"
                     + clean(rec.get("blindLocalsOnly")))
    if _has_field(rec, "blindOutOfScope"):
        parts.append("### DELIBERATELY NOT COUNTED\n" + clean(rec.get("blindOutOfScope")))
    return "\n\n".join(parts)


# --------------------------------------------------------------------------- #
# Fail-closed prompt leak gate (2026-11-08): no rendered user prompt may carry
# score references or numeric score-like values. System rubric text is exempt.
# --------------------------------------------------------------------------- #

LEAK_PATTERNS = (
    re.compile(r"\bnational score\b", re.I),
    re.compile(r"\bsub-?national score\b", re.I),
    re.compile(r"\bscores?\b[^.]{0,40}\b\d+\.\d"),
    re.compile(r"\b\d+\.\d+\b[^.]{0,30}\bscores?\b"),
    # bare two-decimal 0.xx-style values are score-shaped. Exempt: explicit
    # percentages and rate figures carrying a denominator ("per 100,000",
    # "per a small population") — the rubric REQUIRES denominators for rates.
    re.compile(r"\b0\.\d\d\b(?!(?:\s+\S+){0,4}\s+per\b)(?!\s*(?:percent|per\s*cent|%))"),
)


def assert_user_text_clean(user_text: str, context: str = "user prompt") -> None:
    for pat in LEAK_PATTERNS:
        m = pat.search(user_text)
        if m:
            raise HarnessError(
                f"prompt leak gate ({context}): score-bearing text at "
                f"{user_text[max(0, m.start()-60):m.end()+40]!r}")


def build_country_user(slot_map: dict, countries: dict) -> str:
    blocks = []
    for slot in range(1, SLOT_COUNT + 1):
        iso3 = slot_map[str(slot)]["iso3"]
        blocks.append(f"## DOSSIER {slot}\n\n{render_country_dossier(iso3, countries)}")
    user_text = ("Rate the five dossiers below.\n\n" + "\n\n".join(blocks)
                 + "\n\nReply with only the JSON object described in the output format.")
    assert_user_text_clean(user_text, "country")
    return user_text


def render_admin1_dossier(record_id: str, parent_iso: str,
                          admin1: dict, countries: dict) -> str:
    """Blinded division dossier with the parent's blind national framework.

    The framework is exactly the four design-enumerated fields, sources capped
    at 8; the diversity paragraph, the parent's score/identity and the
    division's own name/summary/modelContext never appear.
    """
    rec = admin1.get(record_id)
    if not isinstance(rec, dict) or rec.get("iso3") != parent_iso:
        raise HarnessError(f"no division record {record_id!r} under {parent_iso}")
    parent = countries.get(parent_iso)
    if not isinstance(parent, dict):
        raise HarnessError(f"no parent country record for {parent_iso}")

    framework = []
    for field in PARENT_FRAMEWORK_FIELDS:
        if _has_field(parent, field):
            label = {"blindSummary": "ASSESSMENT",
                     "blindTangential": "SECONDARY / SITUATIONAL FACTORS",
                     "blindLocalsOnly": "AFFECTS RESIDENTS MORE THAN VISITORS"}[field]
            framework.append(f"{label}\n{clean(parent.get(field))}")
    ss = parent.get("blindSourceSummaries")
    if isinstance(ss, list) and ss:
        items = [clean(x) for x in ss[:PARENT_FRAMEWORK_SOURCES_CAP] if str(x).strip()]
        if items:
            framework.append("SOURCE EVIDENCE (first "
                             f"{PARENT_FRAMEWORK_SOURCES_CAP})\n"
                             + "\n".join(f"- {x}" for x in items))

    parts = ["### PARENT NATIONAL FRAMEWORK "
             "(shared context for every dossier — no score is given)\n\n"
             + "\n\n".join(framework)]
    evidence = [f"### DIVISION EVIDENCE\n{clean(rec.get('blindSummary'))}"]
    ss = rec.get("blindSourceSummaries")
    if isinstance(ss, list) and ss:
        items = "\n".join(f"- {clean(x)}" for x in ss if str(x).strip())
        if items:
            evidence.append(f"### SOURCE EVIDENCE\n{items}")
    for field, label in (("blindTangential", "### SECONDARY / SITUATIONAL FACTORS"),
                         ("blindLocalsOnly", "### AFFECTS RESIDENTS MORE THAN VISITORS"),
                         ("blindOutOfScope", "### DELIBERATELY NOT COUNTED")):
        if _has_field(rec, field):
            evidence.append(f"{label}\n{clean(rec.get(field))}")
    if rec.get("estimated"):
        evidence.append("### DATA STATUS\nThis division's assessment is a flagged "
                        "estimate from national-level knowledge of its distinct legal "
                        "system, not a dedicated research dossier. Rate what it "
                        "supports; do not treat thin data as either safety or danger.")
    parts.extend(evidence)
    return "\n\n".join(parts)


def build_admin1_user(slot_map: dict, parent_iso: str,
                      admin1: dict, countries: dict) -> str:
    blocks = []
    for slot in range(1, SLOT_COUNT + 1):
        rid = slot_map[str(slot)]["record_id"]
        blocks.append(f"## DOSSIER {slot}\n\n"
                      + render_admin1_dossier(rid, parent_iso, admin1, countries))
    user_text = ("Rate the five dossiers below.\n\n" + "\n\n".join(blocks)
                 + "\n\nReply with only the JSON object described in the output format.")
    assert_user_text_clean(user_text, "admin1")
    return user_text


# --------------------------------------------------------------------------- #
# Schedule builders (write only under frozen/)
# --------------------------------------------------------------------------- #

def country_schedule_path() -> Path:
    return Path(FROZEN_DIR) / "schedule_country.json"


def admin1_schedule_path(iso3: str) -> Path:
    return Path(FROZEN_DIR) / f"schedule_admin1_{str(iso3).upper()}.json"


def _source_pins(kinds: tuple[str, ...]) -> dict[str, str]:
    pins = {"research/outing-risk-taxonomy.md": sha256_file(TAXONOMY_PATH),
            "tools/blind_pairwise.py": sha256_file(Path(BP.__file__)),
            "data/countries.json": sha256_file(COUNTRIES_PATH)}
    if "admin1" in kinds:
        pins["data/admin1.json"] = sha256_file(ADMIN1_PATH)
    return pins


def _source_paths() -> dict[str, Path]:
    return {"research/outing-risk-taxonomy.md": TAXONOMY_PATH,
            "tools/blind_pairwise.py": Path(BP.__file__),
            "data/countries.json": Path(COUNTRIES_PATH),
            "data/admin1.json": Path(ADMIN1_PATH)}


def _rng_metadata(seed: int) -> dict:
    return {"module": "random.Random", "algorithm": "MT19937",
            "seed": seed, "python": sys.version.split()[0]}


def _validate_schedule_args(n_calls, seed) -> tuple[int, int]:
    return _require_int(n_calls, "n_calls"), _require_int(seed, "seed", minimum=0)


def make_country_schedule(n_calls, seed, us_locked: bool = True) -> dict:
    """Build (and write) frozen/schedule_country.json.

    Stratified five-country draws (one per overlapping percentile band, no
    repeat inside a call; US-locked forces USA into its own band's slot),
    dossiers shuffled into display slots, per-call slot map + system/user
    message hashes recorded. Fails closed before writing anything.
    """
    check_diag_env()
    n_calls, seed = _validate_schedule_args(n_calls, seed)
    countries = load_countries()
    taxonomy = load_taxonomy()
    pcts = percentile_ranks(countries)
    eligible = eligible_countries(countries)
    rng = random.Random(seed)
    system_text = build_country_system(taxonomy)

    calls, diversity_shas = [], {}
    for idx in range(1, n_calls + 1):
        selection, slot_map = _draw_call(rng, eligible, pcts, bool(us_locked))
        for entry in selection:
            iso3 = entry["iso3"]
            if iso3 not in diversity_shas:
                diversity_shas[iso3] = sha256_text(load_diversity(iso3))
        user_text = build_country_user(slot_map, countries)
        calls.append({"call": idx, "selection": selection, "slot_map": slot_map,
                      "system_sha256": sha256_text(system_text),
                      "user_sha256": sha256_text(user_text)})

    doc = {"kind": "country", "version": SCHEDULE_VERSION, "seed": seed,
           "rng": _rng_metadata(seed), "n_calls": n_calls,
           "us_locked": bool(us_locked), "bands": [list(b) for b in BANDS],
           "percentile_method": "average-rank over all records in data/countries.json: "
                                "p = 100 * avg_rank / (n - 1), zero-based ranks, tied "
                                "scores share the average rank; band membership is "
                                "lo <= p <= hi (closed intervals)",
           "rubric_version": RUBRIC_VERSION,
           "sources": _source_pins(("country",)),
           "diversity_blind_sha256": diversity_shas,
           "calls": calls}
    write_json(country_schedule_path(), doc)
    return doc


def make_admin1_schedule(iso3, n_calls, seed) -> dict:
    """Build (and write) frozen/schedule_admin1_<ISO3>.json.

    Five divisions of ONE country drawn per call (no repeat inside a call),
    identities withheld in the prompts, per-call slot map + message hashes.
    Fails closed before writing anything.
    """
    check_diag_env()
    iso3 = str(iso3).upper().strip()
    if not re.fullmatch(r"[A-Z]{3}", iso3):
        raise HarnessError(f"iso3 must be three letters, got {iso3!r}")
    n_calls, seed = _validate_schedule_args(n_calls, seed)
    countries = load_countries()
    admin1 = load_admin1()
    taxonomy = load_taxonomy()
    if iso3 not in countries:
        raise HarnessError(f"no country record for {iso3}")
    pool = eligible_divisions(admin1, iso3)
    if len(pool) < SLOT_COUNT:
        raise HarnessError(
            f"{iso3} has {len(pool)} eligible divisions; five-way needs at least "
            f"{SLOT_COUNT} (scored + blind-complete records only)")
    rng = random.Random(seed)
    system_text = build_admin1_system(taxonomy)

    calls = []
    for idx in range(1, n_calls + 1):
        drawn = rng.sample(pool, SLOT_COUNT)
        entries = [{"record_id": rid} for rid in drawn]
        rng.shuffle(entries)
        slot_map = {str(s): entries[s - 1] for s in range(1, SLOT_COUNT + 1)}
        user_text = build_admin1_user(slot_map, iso3, admin1, countries)
        calls.append({"call": idx, "selection": [e["record_id"] for e in entries],
                      "slot_map": slot_map,
                      "system_sha256": sha256_text(system_text),
                      "user_sha256": sha256_text(user_text)})

    doc = {"kind": "admin1", "version": SCHEDULE_VERSION, "seed": seed,
           "rng": _rng_metadata(seed), "n_calls": n_calls, "iso3": iso3,
           "us_locked": False,
           "percentile_method": "not applicable (one country's divisions; "
                                "simple random draws without replacement inside a call)",
           "rubric_version": RUBRIC_VERSION,
           "sources": _source_pins(("admin1",)),
           "calls": calls}
    write_json(admin1_schedule_path(iso3), doc)
    return doc


# --------------------------------------------------------------------------- #
# Schedule gates (read-only)
# --------------------------------------------------------------------------- #

def load_schedule(path) -> dict:
    p = Path(path)
    if not p.is_file():
        raise HarnessError(f"missing schedule {p}")
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        raise HarnessError(f"{p} is not valid JSON: {e}")
    if not isinstance(doc, dict):
        raise HarnessError(f"{p}: schedule must be a JSON object")
    return doc


def validate_schedule_doc(doc: dict) -> None:
    if doc.get("version") != SCHEDULE_VERSION:
        raise HarnessError(f"schedule version {doc.get('version')!r} != {SCHEDULE_VERSION}")
    kind = doc.get("kind")
    if kind not in SCHEDULE_KINDS:
        raise HarnessError(f"unknown schedule kind {kind!r}")
    if isinstance(doc.get("seed"), bool) or not isinstance(doc.get("seed"), int):
        raise HarnessError("schedule seed missing or not an integer")
    n_calls = doc.get("n_calls")
    if isinstance(n_calls, bool) or not isinstance(n_calls, int) or n_calls < 1:
        raise HarnessError("schedule n_calls invalid")
    calls = doc.get("calls")
    if not isinstance(calls, list) or len(calls) != n_calls:
        raise HarnessError("schedule calls list missing or length mismatch")
    if doc.get("rubric_version") != RUBRIC_VERSION:
        raise HarnessError(f"schedule rubric {doc.get('rubric_version')!r} != "
                           f"current {RUBRIC_VERSION!r}")
    if not isinstance(doc.get("sources"), dict) or not doc["sources"]:
        raise HarnessError("schedule source pins missing")
    for label, want in doc["sources"].items():
        if not isinstance(want, str) or not SHA_RE.match(want):
            raise HarnessError(f"bad source pin for {label!r}")
    slots_expected = {str(s) for s in range(1, SLOT_COUNT + 1)}
    for pos, call in enumerate(calls, start=1):
        if call.get("call") != pos:
            raise HarnessError(f"call {pos}: index mismatch")
        if not isinstance(call.get("system_sha256"), str) or \
                not SHA_RE.match(call["system_sha256"]):
            raise HarnessError(f"call {pos}: bad system_sha256")
        if not isinstance(call.get("user_sha256"), str) or \
                not SHA_RE.match(call["user_sha256"]):
            raise HarnessError(f"call {pos}: bad user_sha256")
        slot_map = call.get("slot_map")
        if not isinstance(slot_map, dict) or set(slot_map) != slots_expected:
            raise HarnessError(f"call {pos}: slot_map keys must be exactly "
                               f"{sorted(slots_expected)}")
        if kind == "country":
            isos = [slot_map[s].get("iso3") for s in sorted(slots_expected)
                    if isinstance(slot_map[s], dict)]
            if len(isos) != SLOT_COUNT or len(set(isos)) != SLOT_COUNT \
                    or not all(isinstance(i, str) for i in isos):
                raise HarnessError(f"call {pos}: five distinct ISO3s required")
            if doc.get("us_locked") and US_ISO3 not in isos:
                raise HarnessError(f"call {pos}: US-locked schedule missing {US_ISO3}")
        else:
            rids = [slot_map[s].get("record_id") for s in sorted(slots_expected)
                    if isinstance(slot_map[s], dict)]
            if len(rids) != SLOT_COUNT or len(set(rids)) != SLOT_COUNT \
                    or not all(isinstance(i, str) for i in rids):
                raise HarnessError(f"call {pos}: five distinct record ids required")
        selection = call.get("selection")
        if not isinstance(selection, list) or len(selection) != SLOT_COUNT:
            raise HarnessError(f"call {pos}: selection must list five draws")


def verify_schedule_sources(doc: dict) -> None:
    paths = _source_paths()
    for label, want in doc["sources"].items():
        if label not in paths:
            raise HarnessError(f"unknown source pin {label!r}")
        path = paths[label]
        if not Path(path).is_file():
            raise HarnessError(f"pinned source missing: {path}")
        got = sha256_file(path)
        if got != want:
            raise HarnessError(
                f"source drift: {label} sha256 {got} != pinned {want}; "
                "rebuild the schedule against the current bytes")


def rebuild_messages(doc: dict) -> list[tuple[str, str]]:
    """Re-derive (system, user) for every call from the recorded slot map."""
    kind = doc["kind"]
    taxonomy = load_taxonomy()
    if kind == "country":
        countries = load_countries()
        system_text = build_country_system(taxonomy)
        return [(system_text, build_country_user(c["slot_map"], countries))
                for c in doc["calls"]]
    admin1 = load_admin1()
    countries = load_countries()
    parent_iso = doc.get("iso3")
    if not isinstance(parent_iso, str):
        raise HarnessError("admin1 schedule missing iso3")
    system_text = build_admin1_system(taxonomy)
    return [(system_text, build_admin1_user(c["slot_map"], parent_iso, admin1, countries))
            for c in doc["calls"]]


def verify_schedule_hashes(doc: dict) -> list[str]:
    problems = []
    try:
        rebuilt = rebuild_messages(doc)
    except HarnessError as e:
        return [str(e)]
    for call, (system_text, user_text) in zip(doc["calls"], rebuilt):
        if sha256_text(system_text) != call["system_sha256"]:
            problems.append(f"call {call['call']}: system message hash mismatch")
        if sha256_text(user_text) != call["user_sha256"]:
            problems.append(f"call {call['call']}: user message hash mismatch")
    return problems


def run_schedule_gates(path) -> dict:
    """All static (no-write, no-network) gates; returns the schedule doc."""
    doc = load_schedule(path)
    validate_schedule_doc(doc)
    verify_schedule_sources(doc)
    problems = verify_schedule_hashes(doc)
    if problems:
        raise HarnessError("schedule message verification failed: "
                           + "; ".join(problems[:4]))
    return doc


# --------------------------------------------------------------------------- #
# Output contract
# --------------------------------------------------------------------------- #

class _NonJsonConstant(Exception):
    pass


def _reject_constant(name: str):
    raise _NonJsonConstant(name)


def parse_five_way_response(text) -> list[dict]:
    """Strict JSON: {"results": [5 x {slot, score, why}]}, slots 1..5 once each,
    scores finite floats in [0, 1]. Any violation raises OutputRejected."""
    if not isinstance(text, str) or not text.strip():
        raise OutputRejected("response is empty or not a string")
    try:
        doc = json.loads(text.strip(), parse_constant=_reject_constant)
    except _NonJsonConstant as e:
        raise OutputRejected(f"non-JSON constant {str(e)!r} in response")
    except ValueError as e:
        raise OutputRejected(f"response is not one strict JSON object: {e}")
    if not isinstance(doc, dict):
        raise OutputRejected(f"top level must be a JSON object, got {type(doc).__name__}")
    if "choices" in doc:
        # Provider envelope (e.g. an OpenAI-style chat completion body): unwrap
        # the assistant message strictly. The raw envelope is what gets
        # preserved; the parse target is the message content.
        try:
            content = doc["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise OutputRejected(f"provider envelope has no assistant content: {e}")
        if not isinstance(content, str) or not content.strip():
            raise OutputRejected("provider envelope has empty assistant content")
        try:
            doc = json.loads(content.strip(), parse_constant=_reject_constant)
        except _NonJsonConstant as e:
            raise OutputRejected(f"non-JSON constant {str(e)!r} in response")
        except ValueError as e:
            raise OutputRejected(f"assistant content is not one strict JSON object: {e}")
        if not isinstance(doc, dict):
            raise OutputRejected(
                f"assistant content must be a JSON object, got {type(doc).__name__}")
    if set(doc) != RESPONSE_KEYS:
        raise OutputRejected(f"top-level keys must be exactly {{'results'}}, got {sorted(doc)}")
    results = doc["results"]
    if not isinstance(results, list):
        raise OutputRejected("'results' must be a list of five entries")
    if len(results) != SLOT_COUNT:
        raise OutputRejected(f"'results' must hold exactly {SLOT_COUNT} entries, "
                             f"got {len(results)}")
    entries: dict[int, dict] = {}
    for pos, entry in enumerate(results):
        if not isinstance(entry, dict):
            raise OutputRejected(f"entry {pos}: must be a JSON object")
        if set(entry) != ENTRY_KEYS:
            raise OutputRejected(f"entry {pos}: keys must be exactly "
                                 f"{sorted(ENTRY_KEYS)}, got {sorted(entry)}")
        slot = entry["slot"]
        if type(slot) is not int or not 1 <= slot <= SLOT_COUNT:
            raise OutputRejected(f"entry {pos}: slot must be an integer 1..{SLOT_COUNT}, "
                                 f"got {slot!r}")
        if slot in entries:
            raise OutputRejected(f"duplicate slot {slot}")
        score = entry["score"]
        if type(score) not in (int, float):
            raise OutputRejected(f"slot {slot}: score must be a JSON number, "
                                 f"got {score!r}")
        if not math.isfinite(score) or not 0.0 <= score <= 1.0:
            raise OutputRejected(f"slot {slot}: score {score!r} outside [0, 1]")
        why = entry["why"]
        if not isinstance(why, str) or not why.strip():
            raise OutputRejected(f"slot {slot}: 'why' must be a non-empty string")
        entries[slot] = entry
    if sorted(entries) != list(range(1, SLOT_COUNT + 1)):
        raise OutputRejected(f"slots must cover 1..{SLOT_COUNT} exactly once, "
                             f"got {sorted(entries)}")
    return [entries[s] for s in range(1, SLOT_COUNT + 1)]


# --------------------------------------------------------------------------- #
# Accounting: ONE shared lock + exact Decimal ledger
# --------------------------------------------------------------------------- #

def acquire_lock(path, holder: str) -> Path:
    """Atomic O_EXCL create of the ONE shared accounting lock.

    Held BEFORE any ledger or runs/<run-id> state is read and through dispatch.
    Contention refuses before any call; this code never deletes a lock it did
    not acquire.
    """
    path = Path(path)
    payload = json.dumps({"holder": holder, "pid": os.getpid(),
                          "runner": "five-way-harness", "acquired_at": utcnow()},
                         indent=1) + "\n"
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        try:
            existing = path.read_text(encoding="utf-8").strip()[:300]
        except OSError:
            existing = "<unreadable>"
        raise LockHeld(f"shared accounting lock is held: {path} ({existing}); "
                       "contention refuses before any call — a human must inspect "
                       "and remove it, this runner never deletes a foreign lock")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(payload)
    return path


def release_lock(path, holder: str) -> None:
    """Remove ONLY a lock whose payload names this holder and pid."""
    path = Path(path)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return                                   # unreadable/not ours: never delete
    if doc.get("holder") == holder and doc.get("pid") == os.getpid():
        try:
            path.unlink()
        except OSError:
            pass


def classify_usage(usage) -> tuple[Decimal, int | None, int | None]:
    """Exact cost + optional token counts from provider usage.

    Unknown/malformed charge information raises UnknownCharge — the run stops;
    there is no retry selected by outcome.
    """
    if not isinstance(usage, dict):
        raise UnknownCharge(f"usage missing or not an object: {usage!r}")
    if "cost_usd" not in usage:
        raise UnknownCharge("usage.cost_usd missing — charge unknown, stopping")
    raw = usage["cost_usd"]
    try:
        if isinstance(raw, bool):
            raise InvalidOperation
        if isinstance(raw, float):
            cost = Decimal(str(raw))
        elif isinstance(raw, int):
            cost = Decimal(raw)
        elif isinstance(raw, str):
            cost = Decimal(raw.strip())
        else:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        raise UnknownCharge(f"usage.cost_usd is not an exact decimal: {raw!r}")
    if not cost.is_finite() or cost < 0:
        raise UnknownCharge(f"usage.cost_usd not a finite non-negative decimal: {raw!r}")
    tokens: list[int | None] = []
    for key in ("input_tokens", "output_tokens"):
        value = usage.get(key)
        if value is None:
            tokens.append(None)
        elif isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise UnknownCharge(f"usage.{key} must be a non-negative integer, "
                                f"got {value!r}")
        else:
            tokens.append(value)
    return cost, tokens[0], tokens[1]


class Ledger:
    """Exact-Decimal run ledger. The caller must hold the shared lock."""

    def __init__(self, path, max_usd: Decimal = MAX_USD):
        self.path = Path(path)
        self.max_usd = Decimal(max_usd)
        if self.path.is_file():
            try:
                doc = json.loads(self.path.read_text(encoding="utf-8"))
            except ValueError as e:
                raise HarnessError(f"corrupt ledger {self.path}: {e}")
            if not isinstance(doc, dict) or not isinstance(doc.get("entries"), list):
                raise HarnessError(f"corrupt ledger {self.path}: bad shape")
            self.doc = doc
        else:
            self.doc = {"entries": [], "total_usd": "0",
                        "input_tokens": 0, "output_tokens": 0}

    @property
    def total(self) -> Decimal:
        return Decimal(self.doc["total_usd"])

    def check_budget(self) -> None:
        if self.total >= self.max_usd:
            raise BudgetExceeded(
                f"local USD guard: recorded cost {self.total} >= max {self.max_usd} "
                "— stopping before the next call (guard is enforced locally only)")

    def add_usage(self, usage, call: int) -> Decimal:
        cost, in_tok, out_tok = classify_usage(usage)
        entry = {"call": call, "at": utcnow(), "cost_usd": fmt_decimal(cost),
                 "input_tokens": in_tok, "output_tokens": out_tok}
        entries = self.doc["entries"] + [entry]
        total = sum((Decimal(e["cost_usd"]) for e in entries), Decimal("0"))
        in_sum = sum(e["input_tokens"] or 0 for e in entries)
        out_sum = sum(e["output_tokens"] or 0 for e in entries)
        new_doc = {"entries": entries, "total_usd": fmt_decimal(total),
                   "input_tokens": in_sum, "output_tokens": out_sum}
        write_json(self.path, new_doc)           # exact before visible
        self.doc = new_doc
        return cost


# --------------------------------------------------------------------------- #
# Runner (disabled by default; caller is injected — no network code here)
# --------------------------------------------------------------------------- #

def _attempt_path(run_dir: Path, call: int) -> Path:
    return run_dir / f"attempt-{call:04d}.json"


def _result_path(run_dir: Path, call: int) -> Path:
    return run_dir / f"result-{call:04d}.json"


def execute_schedule(path, run_id, caller, *, runs_dir=None, lock_path=None,
                     max_usd=None, call_subset=None) -> dict:
    """Dispatch calls of a frozen schedule through an injected adapter.

    `call_subset` (optional set of call numbers) limits which cells THIS
    invocation dispatches — used for transparent continuations after a
    failed draw. The schedule itself stays the frozen full document and all
    gates still verify in full; a subset never alters, renumbers or re-draws
    any cell.

    `caller(system_text, user_text)` must return
    {"raw_response": str, "usage": {"cost_usd": ..., "input_tokens": ...,
    "output_tokens": ...}}. There is exactly one attempt per call — a rejected
    score, an unknown charge, a budget stop or an adapter failure ends the run
    without retry. Raw responses are preserved verbatim under runs/<run-id>/.

    Static gates (run_id, schedule schema, source pins, message hashes) run
    BEFORE the shared lock; ledger and run state are touched only under it.
    """
    runs_dir = RUNS_DIR if runs_dir is None else Path(runs_dir)
    lock_path = LOCK_PATH if lock_path is None else Path(lock_path)
    max_usd = MAX_USD if max_usd is None else Decimal(max_usd)

    # ---- static gates: no writes, no network, no credentials ---------------
    if not isinstance(run_id, str) or not RUN_ID_RE.match(run_id):
        raise HarnessError(f"invalid run id {run_id!r}")
    doc = run_schedule_gates(path)

    # ---- ONE shared lock before any ledger/run-dir state -------------------
    holder = LOCK_HOLDER_PREFIX + run_id
    acquire_lock(lock_path, holder)
    try:
        run_dir = runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        ledger = Ledger(run_dir / "ledger.json", max_usd)
        messages = rebuild_messages(doc)
        completed = 0
        for call, (system_text, user_text) in zip(doc["calls"], messages):
            call_no = call["call"]
            if call_subset is not None and call_no not in call_subset:
                continue
            ledger.check_budget()
            try:
                res = caller(system_text, user_text)
            except Exception as e:               # adapter failure: stop, never retry
                write_json(_attempt_path(run_dir, call_no),
                           {"run_id": run_id, "call": call_no, "at": utcnow(),
                            "status": "error", "error": repr(e)})
                write_json(_result_path(run_dir, call_no),
                           {"call": call_no, "status": "stopped",
                            "reason": f"provider adapter failed: {e!r}"})
                raise StopRun(f"call {call_no}: provider adapter failed: {e!r}")
            if not isinstance(res, dict) or not isinstance(res.get("raw_response"), str):
                write_json(_attempt_path(run_dir, call_no),
                           {"run_id": run_id, "call": call_no, "at": utcnow(),
                            "status": "error", "adapter_result": repr(res)[:2000]})
                raise StopRun(f"call {call_no}: provider adapter returned a "
                              "malformed result (no raw_response string)")
            usage = res.get("usage")
            # Raw response preserved verbatim before any interpretation.
            write_json(_attempt_path(run_dir, call_no),
                       {"run_id": run_id, "call": call_no, "at": utcnow(),
                        "system_sha256": call["system_sha256"],
                        "user_sha256": call["user_sha256"],
                        "raw_response": res["raw_response"],
                        "usage": usage if isinstance(usage, dict) else repr(usage)})
            try:
                cost = ledger.add_usage(usage, call_no)
            except UnknownCharge as e:
                write_json(_result_path(run_dir, call_no),
                           {"call": call_no, "status": "stopped",
                            "reason": str(e)})
                raise UnknownCharge(f"call {call_no}: {e}")
            if ledger.total >= ledger.max_usd:
                write_json(_result_path(run_dir, call_no),
                           {"call": call_no, "status": "stopped", "cost_usd": fmt_decimal(cost),
                            "reason": f"local USD guard reached ({ledger.total} >= "
                                      f"{ledger.max_usd})"})
                raise BudgetExceeded(
                    f"local USD guard reached after call {call_no}: "
                    f"{ledger.total} >= {ledger.max_usd} (local-only guard)")
            try:
                parsed = parse_five_way_response(res["raw_response"])
            except OutputRejected as e:
                write_json(_result_path(run_dir, call_no),
                           {"call": call_no, "status": "rejected",
                            "cost_usd": fmt_decimal(cost), "reason": str(e)})
                raise OutputRejected(f"call {call_no}: {e}")
            write_json(_result_path(run_dir, call_no),
                       {"call": call_no, "status": "ok", "cost_usd": fmt_decimal(cost),
                        "parsed": parsed})
            completed += 1
        return {"run_id": run_id, "calls_completed": completed,
                "total_usd": fmt_decimal(ledger.total), "max_usd": str(max_usd)}
    finally:
        release_lock(lock_path, holder)


def load_provider(spec: str):
    """Resolve a `module:function` adapter (execute path only)."""
    if not isinstance(spec, str) or ":" not in spec:
        raise RunnerDisabled("--provider must look like 'package.module:function'")
    mod_name, _, attr = spec.partition(":")
    try:
        module = importlib.import_module(mod_name)
        func = getattr(module, attr)
    except (ImportError, AttributeError) as e:
        raise RunnerDisabled(f"cannot load provider adapter {spec!r}: {e}")
    if not callable(func):
        raise RunnerDisabled(f"provider adapter {spec!r} is not callable")
    return func


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def parse_call_subset(spec: str) -> frozenset[int]:
    """'17-20' or '17,18,19,20' -> frozenset of positive call numbers."""
    out: set[int] = set()
    try:
        parts = str(spec).split(",")
    except Exception as e:
        raise HarnessError(f"invalid --calls spec: {e!r}")
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, _, hi = part.partition("-")
            try:
                lo_i, hi_i = int(lo.strip()), int(hi.strip())
            except ValueError:
                raise HarnessError(f"invalid --calls range {part!r}")
            lo_i = _require_int(lo_i, "calls range start", minimum=1)
            hi_i = _require_int(hi_i, "calls range end", minimum=1)
            if hi_i < lo_i:
                raise RunnerDisabled(f"invalid --calls range {part!r}")
            out.update(range(lo_i, hi_i + 1))
        else:
            try:
                n = int(part)
            except ValueError:
                raise HarnessError(f"invalid --calls entry {part!r}")
            out.add(_require_int(n, "calls entry", minimum=1))
    if not out:
        raise RunnerDisabled("--calls selected no cells")
    return frozenset(out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="harness.py",
        description="Offline five-way comparison harness (no network, no credentials; "
                    "the runner is disabled by default)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("schedule-country", help="write frozen/schedule_country.json")
    p.add_argument("--n-calls", type=int, required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--no-us-lock", action="store_true",
                   help="do not force USA into every call")

    p = sub.add_parser("schedule-admin1",
                       help="write frozen/schedule_admin1_<ISO3>.json")
    p.add_argument("--iso3", required=True)
    p.add_argument("--n-calls", type=int, required=True)
    p.add_argument("--seed", type=int, required=True)

    p = sub.add_parser("verify", help="read-only: re-verify source pins and "
                                      "message hashes of a frozen schedule")
    p.add_argument("--schedule", required=True)

    p = sub.add_parser("run", help="dispatch a schedule (refuses without --execute)")
    p.add_argument("--schedule", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--execute", action="store_true",
                   help="actually dispatch; absent => refusal before any write")
    p.add_argument("--provider", default=None,
                   help="with --execute: adapter as package.module:function")
    p.add_argument("--calls", default=None,
                   help="with --execute: dispatch only these cells, e.g. "
                        "'17-20' or '17,18,19,20' (transparent continuation "
                        "after a failed draw; the frozen schedule is still "
                        "verified in full and no cell is renumbered)")

    args = parser.parse_args(argv)
    try:
        if args.command == "schedule-country":
            doc = make_country_schedule(args.n_calls, args.seed,
                                        us_locked=not args.no_us_lock)
            print(f"wrote {country_schedule_path()}: {doc['n_calls']} calls, "
                  f"seed {doc['seed']}, us_locked={doc['us_locked']}")
            return 0
        if args.command == "schedule-admin1":
            doc = make_admin1_schedule(args.iso3, args.n_calls, args.seed)
            print(f"wrote {admin1_schedule_path(doc['iso3'])}: "
                  f"{doc['n_calls']} calls, seed {doc['seed']}, parent {doc['iso3']}")
            return 0
        if args.command == "verify":
            run_schedule_gates(args.schedule)
            print(f"ok: {args.schedule} — schema, source pins and message hashes "
                  "all verify (read-only run)")
            return 0
        if args.command == "run":
            if not args.execute:
                raise RunnerDisabled(
                    "refused: the runner is disabled by default. Without --execute "
                    "no schedule is read, nothing is written, no network or "
                    "credentials are touched.")
            if not args.provider:
                raise RunnerDisabled(
                    "refused: --execute requires an explicit adapter via "
                    "--provider package.module:function (this harness ships no "
                    "network or credential code)")
            caller = load_provider(args.provider)
            subset = parse_call_subset(args.calls) if args.calls else None
            summary = execute_schedule(args.schedule, args.run_id, caller,
                                       call_subset=subset)
            print(f"run {summary['run_id']}: {summary['calls_completed']} calls, "
                  f"exact cost {summary['total_usd']} USD "
                  f"(guard {summary['max_usd']})")
            return 0
        raise RunnerDisabled(f"unknown command {args.command!r}")
    except RunnerDisabled as e:
        print(str(e), file=sys.stderr)
        return 2
    except HarnessError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())