#!/usr/bin/env python3
"""Shadow-only ADM1 national-baseline + local-difference construction test.

Per research/experiments/country-calibration-audit/terra-method-review.md §4.
NON-PUBLISHING: never writes data/ or tools/, never commits. All artifacts land
under adm1-shadow/ next to this script. Published country and division scores are
read only — as the frozen baseline INPUT or as a diagnostic comparison that is
never a target.

Interface under test:
  1. FULL national comparison dossier: the blind national bundle including
     blindOutOfScope and ALL blindSourceSummaries (deliberately uncapped, unlike
     production render_parent_bundle which omits out-of-scope and caps at 8) plus
     the frozen published national level stated explicitly as a FIXED INPUT NOT
     TO BE RE-RATED (USA 0.330 for CA/TX, GBR 0.443529 for England,
     NPL 0.559643 for Bagmati; recorded per run).
  2. A separate LOCAL evidence bundle (the division's own blind bundle; Bagmati
     has no blind bundle, so its raw division record is used, marked as such).
  3. The model assesses only the SIGNED LOCAL DIFFERENCE vs the national
     comparison. Each departure links specific local evidence, its visitor
     applicability, and whether the fact already appears in the national bundle
     (inherited national exposure must not be re-counted).
  4. Two shadow candidates computed externally per call:
       additive = national baseline + delta               (raw, logged unclamped)
       bounded  = clamp(additive, 0.02, 0.98)             (explicit alternative;
                                                           every hit is logged)
Model: deepseek/deepseek-v4.1-flash, production system prompt from
tools/blind_pairwise.build_system_prompt (byte-identical, sha recorded).

Cells (2 draws each): California, Texas, England, Bagmati; no-new-local-evidence
control; evidence-duplication control; California order flip; California
identifying-label contrast.
"""
import hashlib
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))

# Production default prompt only: no diagnostic replay flags.
for _v in ("STRIP_RULE_10B", "RESTORE_ARCHIVED_WORDING", "REVERT_ENDPOINT"):
    import os as _os
    _os.environ.pop(_v, None)

import blind_pairwise as BP                      # noqa: E402
from encounter_replay import api_args            # noqa: E402

OUT_DIR = Path(__file__).resolve().parent
PROMPT_DIR = OUT_DIR / "prompts"
RAW_DIR = OUT_DIR / "raw"
RESULTS = OUT_DIR / "results.ndjson"
META = OUT_DIR / "metadata.json"
SUMMARY = OUT_DIR / "summary.json"

BOUNDED_LO, BOUNDED_HI = 0.02, 0.98   # explicit bounded alternative: clamp range
DELTA_CONSISTENCY_TOL = 0.03          # |sum(departure contributions) - local_delta|
# Predeclared retry policy (after run1 showed reasoning-budget exhaustion and one
# malformed JSON; run1 artifacts kept as *_run1.*): at most ONE retry per call,
# only when attempt 1 is empty, truncated or unparseable. The retry gets a larger
# completion budget so a truncation failure is not simply repeated; both attempts
# are retained and reported (terra-method-review.md §3 guidance applied here).
MAX_ATTEMPTS = 2
RETRY_MAX_OUTPUT_TOKENS = 16000

C = json.loads((ROOT / "data" / "countries.json").read_text(encoding="utf-8"))
A = json.loads((ROOT / "data" / "admin1.json").read_text(encoding="utf-8"))
TAXONOMY = (ROOT / "research" / "outing-risk-taxonomy.md").read_text(encoding="utf-8")
SYSTEM = BP.build_system_prompt(TAXONOMY)
SYSTEM_SHA = hashlib.sha256(SYSTEM.encode()).hexdigest()

DIVISIONS = {}  # (iso3, name) -> record
for _k, _r in A.items():
    if _r.get("iso3") and _r.get("name"):
        DIVISIONS[(_r["iso3"], _r["name"])] = _r

# --------------------------------------------------------------------------- #
# Frozen inputs (read-only): published national levels and published division
# scores. Division scores are used ONLY as a diagnostic spread, never a target.
# --------------------------------------------------------------------------- #
BASELINES = {"USA": 0.330, "GBR": 0.443529, "NPL": 0.559643}
# Display form used in prompts so the level is stated exactly as approved
# (0.330, not 0.33). The ISO in BASELINE_SOURCE is recorded in metadata/report
# only — it must NOT appear in the prompt, which stays anonymised.
BASELINE_DISPLAY = {"USA": "0.330", "GBR": "0.443529", "NPL": "0.559643"}
BASELINE_SOURCE = {
    "USA": "data/countries.json USA.score = 0.330 (user-approved frozen published national score)",
    "GBR": "data/countries.json GBR.score = 0.443529 (frozen published national score)",
    "NPL": "data/countries.json NPL.score = 0.559643 (frozen published national score)",
}
PUBLISHED_DIVISION = {          # diagnostic comparison only
    "California": 0.380584,
    "Texas": 0.185559,
    "England": 0.485382,
    "Bagmati": 0.555559,
}

# --------------------------------------------------------------------------- #
# Cells
# --------------------------------------------------------------------------- #
CASES = [
    dict(cell="CA_primary", role="case", division="California", iso="USA",
         local="blind", order="national-first", label="withheld", draws=2),
    dict(cell="TX_primary", role="case", division="Texas", iso="USA",
         local="blind", order="national-first", label="withheld", draws=2),
    dict(cell="ENG_primary", role="case", division="England", iso="GBR",
         local="blind", order="national-first", label="withheld", draws=2),
    dict(cell="BAG_primary", role="case", division="Bagmati", iso="NPL",
         local="fallback", order="national-first", label="withheld", draws=2),
    dict(cell="CTRL_no_local", role="control-no-new-evidence", division=None,
         iso="USA", local="empty", order="national-first", label="withheld",
         draws=2,
         note="national bundle only, zero local additions; delta near zero is a "
              "diagnostic expectation, not a rule"),
    dict(cell="CTRL_dup", role="control-duplication", division=None, iso="USA",
         local="dup", order="national-first", label="withheld", draws=2,
         note="local bundle contains a fact verbatim from the national bundle; "
              "must not count as a new local departure"),
    dict(cell="CA_orderflip", role="order-contrast", division="California",
         iso="USA", local="blind", order="local-first", label="withheld",
         draws=2, note="same inputs as CA_primary, dossier blocks swapped"),
    dict(cell="CA_label_ident", role="label-contrast", division="California",
         iso="USA", local="blind", order="national-first", label="identifying",
         draws=2, note="same inputs as CA_primary, division labelled by name"),
]

# A national source summary used verbatim as the "local" fact in CTRL_dup:
# unambiguously a national-level fact that also sits in the national bundle.
NATIONAL_DUP_SOURCE_IDX = 4

ALLOWED_JSON_KEYS = {"local_delta", "departures", "inherited_national_exposure",
                     "uncertainty", "notes"}


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(s or ""))).strip()


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


# --------------------------------------------------------------------------- #
# Bundle renderers
# --------------------------------------------------------------------------- #
def render_full_national(rec):
    """The FULL blind national comparison dossier: everything production's
    render_parent_bundle leaves out (blindOutOfScope) and no 8-item cap on
    source summaries."""
    parts = []
    if rec.get("blindSummary"):
        parts.append("### NATIONAL ASSESSMENT\n" + clean(rec["blindSummary"]))
    if rec.get("blindTangential"):
        parts.append("### SECONDARY / SITUATIONAL FACTORS (national)\n"
                     + clean(rec["blindTangential"]))
    if rec.get("blindLocalsOnly"):
        parts.append("### AFFECTS RESIDENTS MORE THAN VISITORS (national)\n"
                     + clean(rec["blindLocalsOnly"]))
    if rec.get("blindOutOfScope"):
        parts.append("### OUT OF SCOPE FOR THE NATIONAL SCORE (exclusions, shown in full)\n"
                     + clean(rec["blindOutOfScope"]))
    ss = [clean(x) for x in (rec.get("blindSourceSummaries") or []) if clean(x)]
    parts.append(f"### SOURCE EVIDENCE — COMPLETE, UNCAPPED LIST ({len(ss)} items)\n"
                 + "\n".join(f"- {x}" for x in ss))
    return "\n\n".join(parts)


def render_local(rec, division_name, label):
    tag = f"'{division_name}'" if label == "identifying" else "(identity withheld)"
    head = f"### THE DIVISION'S OWN EVIDENCE (division: {tag})\n"
    if rec is None:
        return head + ("This division's local bundle is EMPTY. No local evidence "
                       "of any kind is provided in this run.")
    if rec.get("blindSummary"):
        parts = []
        parts.append(clean(rec["blindSummary"]))
        if rec.get("blindTangential"):
            parts.append("[Secondary factors] " + clean(rec["blindTangential"]))
        if rec.get("blindLocalsOnly"):
            parts.append("[Resident-facing] " + clean(rec["blindLocalsOnly"]))
        if rec.get("blindOutOfScope"):
            parts.append("[Out of scope locally] " + clean(rec["blindOutOfScope"]))
        ss = [clean(x) for x in (rec.get("blindSourceSummaries") or []) if clean(x)]
        if ss:
            parts.append(f"Evidence on this division ({len(ss)} items):\n"
                         + "\n".join(f"- {x}" for x in ss))
        return head + "\n\n".join(parts)
    # Production mixed-lane fallback for divisions with no blind bundle: the
    # division's own summary. Identity is NOT stripped here; stated explicitly.
    urls = rec.get("sources") or []
    body = clean(rec.get("summary"))
    if urls:
        body += ("\n\n[Recorded sources, no local summaries available: "
                 + "; ".join(str(u) for u in urls) + "]")
    return head + ("NOTE: no anonymised blind bundle exists for this division; its "
                   "raw division record is used and identity is not stripped.\n\n"
                   + body)


# --------------------------------------------------------------------------- #
# Prompt
# --------------------------------------------------------------------------- #
def build_user_prompt(case):
    iso = case["iso"]
    baseline = BASELINES[iso]
    disp = BASELINE_DISPLAY[iso]
    nat_rec = C[iso]
    div = case["division"]
    div_rec = DIVISIONS.get((iso, div)) if div else None
    if div and div_rec is None:
        raise KeyError(f"division record not found: {iso} {div}")

    if case["local"] == "dup":
        dup_fact = clean(nat_rec["blindSourceSummaries"][NATIONAL_DUP_SOURCE_IDX])
        local_text = ("### THE DIVISION'S OWN EVIDENCE (division: (identity withheld))\n"
                      "The division's local bundle consists of:\n"
                      f"- {dup_fact}")
    elif case["local"] == "empty":
        local_text = render_local(None, None, "withheld")
    else:
        local_text = render_local(div_rec, div,
                                  case["label"] if case["label"] == "identifying"
                                  else "withheld")

    fixed_block = (
        "# SHADOW ADM1 EVALUATION — local difference vs a fixed national level\n"
        "(non-publishing evaluation run; no score is produced or changed here)\n\n"
        "NOTE: the generic two-dossier output format described in your instructions\n"
        "does NOT apply to this run. The JSON schema at the end of this message is\n"
        "the only valid output. Do not output score_a/score_b.\n\n"
        "## 1. FIXED INPUT — NATIONAL LEVEL = "
        f"{disp}\n"
        "The number above is the published national score for the country whose full\n"
        "national dossier appears in this message. It is a FROZEN INPUT to this\n"
        "evaluation, explicitly NOT a number to be re-rated: do not re-derive it, do\n"
        "not propose a revised national level, and do not output any national score.\n"
        "Everything national is already priced into this level.\n"
    )

    national_block = (
        "\n## 2. FULL NATIONAL COMPARISON DOSSIER (anonymised, complete — including "
        "out-of-scope exclusions and ALL source summaries)\n\n"
        "Facts in this dossier are what the fixed national level already covers. They "
        "are INHERITED NATIONAL EXPOSURE for every division of this country: if the "
        "local bundle below repeats a fact that already appears here, do NOT count it "
        "again as a local departure.\n\n"
        + render_full_national(nat_rec)
    )

    local_block = (
        "\n\n## 3. LOCAL EVIDENCE BUNDLE (the division's own bundle, separate from the "
        "national dossier)\n\n" + local_text
    )

    task_block = f"""
## 4. Your task: assess ONLY the signed local difference (delta) relative to the national comparison

- `local_delta` is signed and on the same 0.00–1.00 scale (higher safer):
  positive = the local evidence makes THIS DIVISION safer for a transgender visitor
  than the fixed national level {disp}; negative = riskier; 0 = no documented local
  difference. The shadow score (computed externally, never by you) is
  `{disp} + local_delta`.
- For EVERY departure from the national level, state:
  * `fact`: what genuinely differs locally;
  * `local_evidence`: the specific item in the local bundle that supports it (quote or close reference);
  * `direction`: "safer" or "riskier";
  * `magnitude`: a POSITIVE number — how many points this departure contributes (safer adds, riskier subtracts);
  * `visitor_applicability`: whether this fact reaches a transgender VISITOR under the
    rating rules (resident-facing law or policy is climate signal at most and must not
    move the visitor delta);
  * `already_in_national_bundle`: true if this same fact already appears in the national
    dossier above; if true it is inherited national exposure and must normally be
    `counted_in_delta: false` — repetition is not a new local departure;
  * `counted_in_delta`: whether this departure is included in your `local_delta`.
- A region-specific IMPLEMENTATION may still warrant a departure if its difference from
  the national comparison is documented; mere duplication of a national fact does not.
- Do not re-rate national factors (federal law, border and passport friction, national
  enforcement climate): they are inside the fixed level already.
- Weigh departures by the rubric: severity, laws on the books vs enforcement, documented
  patterns over single incidents. If local evidence is thin or absent, say so in
  `uncertainty` and let `local_delta` be small or 0 rather than inventing a departure —
  note that a zero delta from missing evidence is a diagnostic, not proof of equality.
- List in `inherited_national_exposure` the national-dossier facts you deliberately did
  NOT re-count (or key inherited exposures that frame the delta).

## 5. Output format for this run (replaces the generic output format)

Reply with ONLY one single JSON object, no prose before or after it:

{{"local_delta": <float, signed, e.g. -0.14 or 0.03>,
  "departures": [{{"fact": "...", "local_evidence": "...", "direction": "safer"|"riskier", "magnitude": <positive float>, "visitor_applicability": "...", "already_in_national_bundle": true|false, "counted_in_delta": true|false}}],
  "inherited_national_exposure": ["..."],
  "uncertainty": "...",
  "notes": "..."}}

Do NOT output score_a/score_b, any absolute re-rating of the country or division, or
any revised national level.
"""

    if case["order"] == "local-first":
        head, national_part, local_part = fixed_block, national_block, local_block
        # swap only the two dossier blocks; everything else stays byte-identical
        user_text = head + local_part + national_part + task_block
    else:
        user_text = fixed_block + national_block + local_block + task_block
    return user_text


# --------------------------------------------------------------------------- #
# Parsing and guard checks
# --------------------------------------------------------------------------- #
def extract_json(text):
    """First balanced JSON object containing local_delta (fences tolerated)."""
    for m in re.finditer(r"\{", text or ""):
        depth, instr, esc = 0, False, False
        for i in range(m.start(), len(text)):
            ch = text[i]
            if instr:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    instr = False
                continue
            if ch == '"':
                instr = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    cand = text[m.start():i + 1]
                    if "local_delta" in cand:
                        try:
                            return json.loads(cand)
                        except json.JSONDecodeError:
                            break
        # keep scanning from next '{'
    return None


def guard_checks(raw_text, parsed, baseline, case):
    """Return flag lists. National-re-rating guard: the model must not output a
    revised national level (or pairwise/absolute scores)."""
    rerate, double_count, missed_dup, other = [], [], [], []
    extra_keys = sorted(set(parsed) - ALLOWED_JSON_KEYS) if parsed else []
    for k in extra_keys:
        kl = k.lower()
        if "score_a" in kl or "score_b" in kl:
            rerate.append(f"extra key `{k}` (pairwise score output)")
        elif "national" in kl and any(w in kl for w in ("score", "level", "rating")):
            v = parsed.get(k)
            if isinstance(v, (int, float)) and abs(float(v) - baseline) <= 1e-9:
                other.append(f"extra key `{k}` echoes the fixed baseline {baseline}")
            else:
                rerate.append(f"extra key `{k}` proposes a national value {v!r}")
        elif any(w in kl for w in ("score", "level", "rating", "absolute")):
            other.append(f"extra key `{k}` = {parsed.get(k)!r} "
                         "(absolute/level output outside the agreed schema)")
    if re.search(r'"score_a"|"score_b"', raw_text or ""):
        rerate.append("raw output contains score_a/score_b")
    # prose: a revised national level that differs from the fixed input
    for rx in (r"(?:revised|new|actual|correct(?:ed)?|true|real)\s+national\s+"
               r"(?:score|level|rating)\s*(?:is|:|=|of|=)?\s*(-?\d+\.\d+)",
               r"national\s+(?:score|level|rating)[^.\n]{0,40}?(?:should\s+be|revised\s+to|"
               r"corrected\s+to|would\s+be|is\s+actually)\s+(-?\d+\.\d+)"):
        for m in re.finditer(rx, raw_text or "", re.I):
            val = float(m.group(1))
            if abs(val - baseline) > 1e-9:
                rerate.append(f"prose proposes revised national level {val} "
                              f"(fixed input {baseline})")
    # departure-level checks
    deps = parsed.get("departures") if isinstance(parsed, dict) else None
    nat_text = render_full_national(C[case["iso"]])
    nat_shingles = set()
    nat_tokens = nat_text.lower().split()
    for i in range(len(nat_tokens) - 7):
        nat_shingles.add(" ".join(nat_tokens[i:i + 8]))
    if isinstance(deps, list):
        for d in deps:
            if not isinstance(d, dict):
                continue
            if d.get("already_in_national_bundle") is True and d.get("counted_in_delta") is True:
                double_count.append(str(d.get("fact", ""))[:120])
            txt = f"{d.get('fact','')} {d.get('local_evidence','')}".lower()
            toks = txt.split()
            overlap = any(" ".join(toks[i:i + 8]) in nat_shingles
                          for i in range(max(0, len(toks) - 7)))
            if overlap and d.get("already_in_national_bundle") is False:
                missed_dup.append(str(d.get("fact", ""))[:120])
        if case["local"] == "empty" and deps:
            other.append("departures produced although the local bundle is empty "
                         "(fabricated local evidence?)")
    return {"extra_keys": extra_keys, "rerate_guard": sorted(set(rerate)),
            "double_count": double_count, "missed_duplication_suspect": missed_dup,
            "other": other}


def delta_consistency(parsed, delta):
    """Compare local_delta with the sum of counted departure magnitudes."""
    if not isinstance(parsed, dict) or delta is None:
        return None, "no parse"
    deps = parsed.get("departures")
    if not isinstance(deps, list) or not deps:
        return 0.0, ("no departures listed" if abs(delta) <= 1e-9 else
                     "delta without listed departures")
    total, sign_anomalies = 0.0, 0
    for d in deps:
        if not isinstance(d, dict) or not d.get("counted_in_delta", True):
            continue
        mag = d.get("magnitude")
        if not isinstance(mag, (int, float)):
            continue
        mag = float(mag)
        direction = str(d.get("direction", "")).lower()
        if direction == "riskier" and mag < 0:
            sign_anomalies += 1
        if direction == "safer" and mag < 0:
            sign_anomalies += 1
        total += -abs(mag) if direction == "riskier" else (
            abs(mag) if direction == "safer" else mag)
    diff = abs(total - delta)
    note = "consistent" if diff <= DELTA_CONSISTENCY_TOL else \
        f"|sum({total:.3f}) - delta({delta:.3f})| = {diff:.3f} > {DELTA_CONSISTENCY_TOL}"
    if sign_anomalies:
        note += f"; {sign_anomalies} departure(s) with sign conflicting direction"
    return total, note


def candidates(baseline, delta):
    raw = baseline + delta
    bounded = min(BOUNDED_HI, max(BOUNDED_LO, raw))
    return dict(additive_raw=round(raw, 6), bounded=round(bounded, 6),
                clamped=bool(bounded != raw),
                boundary_hit=bool(raw < BOUNDED_LO or raw > BOUNDED_HI),
                out_of_unit_scale=bool(raw < 0.0 or raw > 1.0))


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
def _api_for_attempt(attempt):
    aa = api_args()
    if attempt > 1:
        aa.max_output_tokens = RETRY_MAX_OUTPUT_TOKENS
    return aa


def run_call(case, draw):
    user_text = case["_user"]
    row = dict(cell=case["cell"], role=case["role"], division=case["division"],
               iso3=case["iso"], national_baseline=BASELINES[case["iso"]],
               baseline_source=BASELINE_SOURCE[case["iso"]],
               order=case["order"], label=case["label"], local=case["local"],
               draw=draw, system_sha256=SYSTEM_SHA, user_sha256=sha(user_text),
               timestamp=datetime.now(timezone.utc).isoformat(),
               model=api_args().model, error=None, attempts=[])
    t0 = time.time()
    content, parsed, delta, raw_path, usage, finish = "", None, None, None, None, None
    api_model = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = BP.call_api(_api_for_attempt(attempt), SYSTEM, user_text)
        except Exception as e:                                # noqa: BLE001
            row["attempts"].append(
                dict(attempt=attempt, error=f"{type(e).__name__}: {str(e)[:400]}"))
            if attempt == MAX_ATTEMPTS:
                row.update(error=row["attempts"][-1]["error"],
                           elapsed_s=round(time.time() - t0, 1))
                return row
            continue
        msg = (resp.get("choices") or [{}])[0].get("message") or {}
        content = msg.get("content") or ""
        if isinstance(content, list):
            content = "".join(b.get("text", "") for b in content
                              if isinstance(b, dict))
        finish = (resp.get("choices") or [{}])[0].get("finish_reason")
        usage = resp.get("usage")
        api_model = resp.get("model")
        raw_path = RAW_DIR / f"{case['cell']}_draw{draw}_attempt{attempt}.json"
        raw_path.write_text(json.dumps(
            {"timestamp": row["timestamp"], "cell": case["cell"], "draw": draw,
             "attempt": attempt, "model": api_model, "usage": usage,
             "content": content, "finish_reason": finish, "id": resp.get("id"),
             "max_output_tokens": _api_for_attempt(attempt).max_output_tokens},
            ensure_ascii=False, indent=1), encoding="utf-8")
        parsed = extract_json(content or "")
        m = re.search(r'"local_delta"\s*:\s*(-?\d+(?:\.\d+)?)', content or "")
        salv = float(m.group(1)) if m else None
        delta = (float(parsed["local_delta"])
                 if isinstance(parsed, dict)
                 and isinstance(parsed.get("local_delta"), (int, float)) else None)
        parse_ok = parsed is not None and delta is not None
        row["attempts"].append(dict(
            attempt=attempt, finish_reason=finish,
            raw_path=str(raw_path.relative_to(OUT_DIR)),
            content_len=len(content),
            reasoning_tokens=((usage or {}).get("completion_tokens_details") or {}).get("reasoning_tokens"),
            completion_tokens=(usage or {}).get("completion_tokens"),
            usage=usage, parse_ok=parse_ok,
            salvaged_local_delta=(salv if not parse_ok else None), error=None))
        if parse_ok:
            break
    row.update(elapsed_s=round(time.time() - t0, 1), api_model=api_model,
               usage=usage, raw_path=str(raw_path.relative_to(OUT_DIR)) if raw_path else None,
               raw_sha256=sha(content or ""), retry_used=len(row["attempts"]) > 1)
    if parsed is None or delta is None:
        row.update(parse_error=f"no valid JSON with local_delta after "
                               f"{len(row['attempts'])} attempt(s)",
                   parsed=None, local_delta=None,
                   salvaged_local_delta=row["attempts"][-1].get("salvaged_local_delta"),
                   flags=guard_checks(content or "", None, BASELINES[case["iso"]], case))
        return row
    flags = guard_checks(content, parsed, BASELINES[case["iso"]], case)
    csum, cnote = delta_consistency(parsed, delta)
    cand = candidates(BASELINES[case["iso"]], delta)
    deps = parsed.get("departures") if isinstance(parsed.get("departures"), list) else []
    row.update(parsed={k: parsed.get(k) for k in sorted(parsed)},
               local_delta=delta, departure_count=len(deps),
               departures=[d for d in deps if isinstance(d, dict)],
               inherited_national_exposure=parsed.get("inherited_national_exposure"),
               uncertainty=parsed.get("uncertainty"), notes=parsed.get("notes"),
               delta_sum_of_departures=csum, delta_consistency=cnote,
               flags=flags, **cand)
    return row


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="render and hash all prompts, no API calls")
    ap.add_argument("--smoke", action="store_true",
                    help="one real API call (CA_primary draw 1); prints the parsed "
                         "result; writes prompts/ and raw/ only, never results.ndjson")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()

    if RESULTS.exists() and not (args.dry_run or args.smoke):
        raise SystemExit(f"{RESULTS} exists; refusing to mix runs "
                         "(delete it deliberately to re-run)")

    for case in CASES:
        case["_user"] = build_user_prompt(case)

    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (PROMPT_DIR / "system_prompt.txt").write_text(SYSTEM, encoding="utf-8")
    for case in CASES:
        (PROMPT_DIR / f"user__{case['cell']}.txt").write_text(
            case["_user"], encoding="utf-8")

    meta = dict(
        purpose="Shadow-only ADM1 national-baseline interface test "
                "(terra-method-review.md §4). Non-publishing: no score is written "
                "to data/ or tools/; no commits.",
        model=api_args().model,
        api=dict(baseurl=api_args().baseurl, endpoint=api_args().endpoint_suffix,
                 dialect=api_args().api, reasoning="effort=high (temperature not sent "
                 "for reasoning models)", max_output_tokens=api_args().max_output_tokens,
                 timeout_s=api_args().timeout, retries=api_args().retries),
        system_prompt_sha256=SYSTEM_SHA,
        system_prompt_chars=len(SYSTEM),
        system_prompt_note="byte-identical tools/blind_pairwise.build_system_prompt("
                           "outing-risk-taxonomy.md); diagnostic replay env flags cleared",
        rubric_version=BP.RUBRIC_VERSION,
        bounded_alternative=f"clamp(additive, {BOUNDED_LO}, {BOUNDED_HI}); every "
                            "boundary hit logged, never silent",
        baselines={k: dict(value=v, display=BASELINE_DISPLAY[k], source=BASELINE_SOURCE[k])
                   for k, v in BASELINES.items()},
        published_division_scores_diagnostic_only=PUBLISHED_DIVISION,
        diagnostic_warning="published division scores are compared only as a "
                           "diagnostic spread (mean gap, range), never as a target",
        cells=[{k: v for k, v in c.items() if not k.startswith("_")} for c in CASES],
        draws_per_cell=2,
        retry_policy=dict(max_attempts=MAX_ATTEMPTS,
                          trigger="attempt 1 empty, truncated or unparseable",
                          retry_max_output_tokens=RETRY_MAX_OUTPUT_TOKENS,
                          both_attempts_retained_and_reported=True,
                          origin="run1 (archived as *_run1.*) produced 2 reasoning-"
                                 "budget truncations and 1 malformed JSON; policy "
                                 "fixed before this run, not tuned per cell"),
        total_calls=sum(c["draws"] for c in CASES),
        generated=datetime.now(timezone.utc).isoformat(),
    )

    if args.dry_run:
        META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        for case in CASES:
            print(f"{case['cell']:16s} user_chars={len(case['_user']):6d} "
                  f"user_sha={sha(case['_user'])[:12]} baseline={BASELINES[case['iso']]}")
        print(f"system_sha={SYSTEM_SHA} chars={len(SYSTEM)}")
        print("DRY RUN OK: prompts written, no API calls")
        return 0

    if args.smoke:
        case = CASES[0]
        row = run_call(case, 1)
        print(json.dumps({k: row.get(k) for k in
                          ("cell", "local_delta", "additive_raw", "bounded",
                           "boundary_hit", "flags", "error", "parse_error",
                           "usage")}, indent=2, ensure_ascii=False))
        if row.get("parsed"):
            print("parsed keys:", sorted(row["parsed"]))
        return 0

    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    jobs = [(c, d) for c in CASES for d in range(1, c["draws"] + 1)]
    rows = []
    with RESULTS.open("x", encoding="utf-8") as fh, \
            ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_call, c, d): (c["cell"], d) for c, d in jobs}
        for i, fut in enumerate(as_completed(futs), 1):
            row = fut.result()
            rows.append(row)
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            print(f"{i}/{len(jobs)} {row['cell']} d{row['draw']} "
                  f"delta={row.get('local_delta')} err={row.get('error')} "
                  f"parse={row.get('parse_error')}", flush=True)

    summary = build_summary(rows)
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                       encoding="utf-8")
    print("DONE", flush=True)
    return 0


def build_summary(rows):
    def stats(vals):
        if not vals:
            return None
        mean = sum(vals) / len(vals)
        return dict(n=len(vals), values=vals, mean=round(mean, 4),
                    min=min(vals), max=max(vals), spread=round(max(vals) - min(vals), 4))

    cells = {}
    for c in CASES:
        cr = sorted([r for r in rows if r["cell"] == c["cell"]],
                    key=lambda r: r["draw"])
        deltas = [r["local_delta"] for r in cr if r.get("local_delta") is not None]
        cells[c["cell"]] = dict(
            role=c["role"], division=c["division"], iso3=c["iso"],
            baseline=BASELINES[c["iso"]], order=c["order"], label=c["label"],
            local=c["local"], note=c.get("note"),
            calls=len(cr), errors=[r.get("error") for r in cr if r.get("error")],
            parse_errors=[r.get("parse_error") for r in cr if r.get("parse_error")],
            attempts_per_call=[len(r.get("attempts") or []) for r in cr],
            salvaged_deltas=[r.get("salvaged_local_delta") for r in cr
                             if r.get("salvaged_local_delta") is not None],
            retry_used=[r.get("retry_used") for r in cr if r.get("retry_used")],
            delta_stats=stats(deltas),
            additive_raw=[r.get("additive_raw") for r in cr],
            bounded=[r.get("bounded") for r in cr],
            boundary_hits=[r.get("boundary_hit") for r in cr],
            out_of_unit_scale=[r.get("out_of_unit_scale") for r in cr],
            rerate_guard=[f for r in cr for f in (r.get("flags") or {}).get("rerate_guard", [])],
            double_count=[f for r in cr for f in (r.get("flags") or {}).get("double_count", [])],
            missed_duplication=[f for r in cr for f in (r.get("flags") or {}).get("missed_duplication_suspect", [])],
            other_flags=[f for r in cr for f in (r.get("flags") or {}).get("other", [])],
            delta_consistency=[r.get("delta_consistency") for r in cr],
            departure_counts=[r.get("departure_count") for r in cr],
        )

    def cm(cell):
        s = cells[cell]["delta_stats"]
        return s["mean"] if s else None

    contrasts = dict(
        order_effect_CA=dict(primary_mean=cm("CA_primary"),
                             orderflip_mean=cm("CA_orderflip"),
                             difference=round((cm("CA_orderflip") or 0) -
                                              (cm("CA_primary") or 0), 4)
                             if None not in (cm("CA_orderflip"), cm("CA_primary")) else None),
        label_effect_CA=dict(primary_mean=cm("CA_primary"),
                             identifying_mean=cm("CA_label_ident"),
                             difference=round((cm("CA_label_ident") or 0) -
                                              (cm("CA_primary") or 0), 4)
                             if None not in (cm("CA_label_ident"), cm("CA_primary")) else None),
        controls=dict(
            no_new_local_evidence=dict(
                expected="delta near 0 (diagnostic expectation, not a rule)",
                observed=cells["CTRL_no_local"]["delta_stats"]),
            duplication=dict(
                expected="duplicated national fact not counted as new departure",
                observed=cells["CTRL_dup"]["delta_stats"],
                double_count_flags=cells["CTRL_dup"]["double_count"]),
        ),
    )

    # Diagnostic spread vs published division scores — NEVER a target.
    diag = {}
    for name, cell in (("California", "CA_primary"), ("Texas", "TX_primary"),
                       ("England", "ENG_primary"), ("Bagmati", "BAG_primary")):
        s = cells[cell]["delta_stats"]
        if not s:
            diag[name] = None
            continue
        shadow_add = round(BASELINES[cells[cell]["iso3"]] + s["mean"], 6)
        pub = PUBLISHED_DIVISION[name]
        diag[name] = dict(shadow_additive_mean=shadow_add, published=pub,
                          gap_shadow_minus_published=round(shadow_add - pub, 6))
    gaps = [d["gap_shadow_minus_published"] for d in diag.values() if d]
    diagnostic_spread = dict(
        per_case=diag,
        mean_gap=round(sum(gaps) / len(gaps), 6) if gaps else None,
        gap_range=[round(min(gaps), 6), round(max(gaps), 6)] if gaps else None,
        warning="diagnostic spread only; never a target, never fed back into any score",
    )

    return dict(generated=datetime.now(timezone.utc).isoformat(),
                model=api_args().model, system_sha256=SYSTEM_SHA,
                rubric_version=BP.RUBRIC_VERSION, cells=cells, contrasts=contrasts,
                diagnostic_spread=diagnostic_spread,
                totals=dict(calls=len(rows),
                            errors=sum(1 for r in rows if r.get("error")),
                            parse_errors=sum(1 for r in rows if r.get("parse_error")),
                            retries_used=sum(1 for r in rows if r.get("retry_used")),
                            attempts_total=sum(len(r.get("attempts") or []) for r in rows),
                            salvaged_after_final_attempt=sum(
                                1 for r in rows
                                if r.get("salvaged_local_delta") is not None),
                            rerate_guard_hits=sum(len((r.get("flags") or {}).get("rerate_guard", []))
                                                  for r in rows),
                            boundary_hits=sum(1 for r in rows if r.get("boundary_hit")),
                            out_of_unit_scale=sum(1 for r in rows if r.get("out_of_unit_scale"))))


if __name__ == "__main__":
    raise SystemExit(main())
