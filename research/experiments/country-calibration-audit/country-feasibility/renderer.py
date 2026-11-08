#!/usr/bin/env python3
"""Offline, deterministic renderer/validator for the country-feasibility pilot.

PREPARATION ONLY - nothing here has been run against a model and nothing here can be.
This module:

  1. derives the SINGLE-country system prompts from the frozen reviewed pairwise
     candidates by literal exact-string edits from ledger.json (fail closed: every
     before-block must match exactly once in its source, else nothing is written);
  2. renders the pilot-only evidence packets for USA/GBR/NPL/VAT by structural
     path-level whitelist of the five blind fields, applying the ledger's packet
     edits (the GBR third-party index score/rank exclusions) fail-closed;
  3. builds the two balanced randomized blocks (32 core + 8 sentinel rows = the
     40-attempt ceiling, interleaved, seed frozen) and the 40 provider-visible
     user messages;
  4. validates everything (no score/band/rank/anchor or sub-national division values,
     no tested COUNTRY_NAMES literals, invariants of the converted prompts, schedule balance,
     sentinel identity);
  5. freezes bytes + hashes under frozen/ and re-verifies them read-only.

There is deliberately NO provider execution path: no network client, no credential
handling, no API-call code, no scoring loop, no writes to data/ or tools/ or UI,
and no national score writes anywhere.

    python3 renderer.py --build    # scope precondition, then derive/render/freeze
    python3 renderer.py --verify   # read-only: re-derive + byte checks + tamper test
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import subprocess
import sys
from collections import Counter
from itertools import groupby
from pathlib import Path

sys.dont_write_bytecode = True  # never write bytecode outside this dir on import
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
AUDIT = "research/experiments/country-calibration-audit"
EXP = AUDIT + "/country-feasibility"
DATA = "data/countries.json"

ISOS = ("USA", "GBR", "NPL", "VAT")
WHITELIST = ("blindSummary", "blindSourceSummaries", "blindTangential",
             "blindLocalsOnly", "blindOutOfScope")
# Exclusion is enforced solely by the WHITELIST read above; the excluded-key
# rationale table lives in evidence-map.md (kept as documentation, not code,
# so it cannot silently drift from behaviour).
COUNTRY_NAMES = ("United States", "USA", "United Kingdom", "Nepal", "Vatican")
MODELS = ("deepseek/deepseek-v4.1-flash", "google/gemini-3.8-flash")
VARIANTS = ("A", "B")
SEED = 20261121
CORE_LABEL = "DOSSIER"
NEUTRAL_LABEL = "NEUTRAL-7"      # preselected neutral dossier label (before outputs)
NEUTRAL_CASE = "USA"             # preselected sentinel case (before outputs)
EMPTY_BODY = ("This dossier is intentionally empty. It contains no evidence, facts, "
              "dates, sources or context about any jurisdiction.")
ATTEMPT_CEILING = 40
CORE_CALLS, SENTINEL_CALLS = 32, 8
# requested settings (frozen; NOT provider-guaranteed) and PROPOSED ceilings.
REQUESTED_SETTINGS = {"temperature": 1.0, "top_p": 1.0, "max_output_tokens": 2000}
PROPOSED_CAPS = {
    "attempt_ceiling_including_failures": 40,
    "per_call_max_input_tokens": 20000,
    "per_call_max_output_tokens": 2000,
    "aggregate_max_input_tokens": 800000,
    "aggregate_max_output_tokens": 80000,
    "aggregate_max_usd_including_failures": 10.00,
    "stop_on_unknown_billing_usage": True,
    "retries_selected_for_output": 0,
    "enforced_by_this_code": False,
    "note": "PROPOSED settings only - renderer.py does not enforce them. "
            "The only observed fact is the byte measurement "
            "max_input_bytes_per_call_observed in this manifest (max UTF-8 bytes over "
            "BOTH prompt variants crossed with all 40 messages). Nothing here converts "
            "bytes into token counts or money: no provider tokenizer or price list was "
            "consulted, so the token and USD figures are unvalidated proposals, not "
            "enforced limits or a cost ceiling. The disabled-by-default runner "
            "(runner.py) enforces them only under an explicit --execute flag with a "
            "reviewed, hash-bound preflight receipt. Dispatch capacity is reserved "
            "under the PRE-OUTCOME reservation amendment recorded in "
            "reservation_amendment (see budget-amendment.md); this original proposal "
            "stays recorded unchanged and remains an in-run stop rule on billed "
            "native tokens",
}

# --------------------------------------------------------------------------- #
# Pre-outcome reservation amendment (administrative, pre-registered; see
# budget-amendment.md). Adopted while zero attempts had ever been dispatched.
# --------------------------------------------------------------------------- #
# Unit = one administrative input reservation unit = UTF-8 bytes of the frozen
# system prompt + user message, plus a fixed 128-unit chat-framing allowance per
# call. These are reservations under stated tokenizer/framing assumptions: they
# are NOT proven provider-native token bounds and NOT a provider-enforced spend
# limit. The USD 10.00 ceiling stays a locally enforced budget.
RESERVATION_PER_CALL_UNITS = 70_000
RESERVATION_AGGREGATE_UNITS = 2_400_000
RESERVATION_FRAMING_UNITS_PER_CALL = 128
# The original proposed input caps (recorded in PROPOSED_CAPS above) are
# preserved verbatim and never reinterpreted silently:
PRESERVED_PROPOSED_INPUT_CAPS = {"per_call_max_input_tokens": 20_000,
                                 "aggregate_max_input_tokens": 800_000}
PROMPT_FORBIDDEN = ("score_a", "score_b", "labelled A and B", "rate **each**",
                    "Two dossiers", "the complete dossiers", "order of presentation",
                    "forcing unequal scores", "When one dossier",
                    "SCOPING: when one dossier", "imprisonment or execution")
PROMPT_REQUIRED = ("near-certain imprisonment and likely execution",
                   "Do not give credit for passing, stealth, silence or avoidance.",
                   "Intermediate points have no fixed definitions.",
                   "carry VERY LOW WEIGHT", "Real weight.", "carries REAL WEIGHT",
                   "10b.", '"status": "ok", "score": <float 0.0-1.0>',
                   '"status": "insufficient_evidence" and "score": null')
RESULTS: list = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f"  :: {detail}"))


def die(msg):
    print(f"FAIL  {msg}")
    sys.exit(1)


def report():
    bad = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS)} checks: {len(RESULTS) - len(bad)} passed, {len(bad)} failed")
    sys.exit(0 if not bad else 1)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load(p) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def apply_once(text, before, after, where):
    """Literal exact-string replacement; fail closed unless exactly one match."""
    n = text.count(before)
    if n != 1:
        die(f"fail-closed apply-once [{where}]: expected exactly 1 literal match, found {n}")
    return text.replace(before, after, 1)


# --------------------------------------------------------------------------- #
# 1. Single-country prompt derivation (pairwise task framing + output contract)
# --------------------------------------------------------------------------- #

def derive_prompts(ledger):
    out = {}
    for v in VARIANTS:
        src = ROOT / ledger["source_prompts"][v]
        t = src.read_text(encoding="utf-8")
        for e in ledger["prompt_edits"]:
            if e["scope"] == "shared":
                t = apply_once(t, e["before"], e["after"], f"{e['id']}/{v}")
            else:
                t = apply_once(t, e["before"][v], e["after"][v], f"{e['id']}/{v}")
        out[v] = t
    return out


def validate_prompts(cands):
    for v, t in cands.items():
        bad = [s for s in PROMPT_FORBIDDEN if s in t]
        check(f"[{v}] pairwise remnants and two-score contract gone", not bad, str(bad))
        missing = [s for s in PROMPT_REQUIRED if s not in t]
        check(f"[{v}] scale/endpoint/weight invariants and single-score schema present",
              not missing, str(missing))
        check(f"[{v}] abstention option explicit (status+null, no forced midpoint)",
              "Never resolve a missing or empty dossier to a midpoint" in t)
    check("[A] discovery probability is not an independent contribution",
          "is not an independent contribution to this score" in cands["A"]
          and "is not an independent contribution to this score" not in cands["B"])
    check("[B] state-engineered discovery may contribute independently",
          "engineering discovery" in cands["B"] and "engineering discovery" not in cands["A"])
    # output contract byte-identical across variants (shared experimental extension)
    oa, ob = (cands[v][cands[v].index("## Output format"):] for v in VARIANTS)
    check("single-score output contract byte-identical in A and B", oa == ob)


# --------------------------------------------------------------------------- #
# 2. Pilot-only evidence packets (structural path-level whitelist + ledger edits)
# --------------------------------------------------------------------------- #

def clean(s) -> str:
    """Same deterministic rendering as the production dossier renderer:
    strip tags, collapse whitespace."""
    s = re.sub(r"<[^>]+>", " ", str(s))
    return re.sub(r"\s+", " ", s).strip()


def pilot_fields(iso, data, ledger):
    """Whitelist view: ONLY the five blind paths of ONE country record are read.
    Every other path (score, band, rank, provenance, anchors, sub-national
    aggregates, named fields, source URLs) is excluded structurally by key
    whitelist, not filtered by prose regex."""
    rec = data[iso]
    fields = {k: rec[k] for k in WHITELIST}
    for e in ledger["packet_edits"]:
        if e["iso"] == iso:
            fields[e["field"]] = apply_once(
                fields[e["field"]], e["before"], e["after"], e["id"])
    return fields


def render_packet_from_fields(f) -> str:
    parts = [f"### ASSESSMENT\n{clean(f['blindSummary'])}"]
    items = [clean(x) for x in f["blindSourceSummaries"] if str(x).strip()]
    parts.append("### SOURCE EVIDENCE\n" + "\n".join(f"- {x}" for x in items))
    parts.append(f"### SECONDARY / SITUATIONAL FACTORS\n{clean(f['blindTangential'])}")
    parts.append(f"### AFFECTS RESIDENTS MORE THAN VISITORS\n{clean(f['blindLocalsOnly'])}")
    parts.append(f"### DELIBERATELY NOT COUNTED\n{clean(f['blindOutOfScope'])}")
    return "\n\n".join(parts)


def render_packet(iso, data, ledger) -> str:
    return render_packet_from_fields(pilot_fields(iso, data, ledger))


def validate_packets(packets, data, ledger):
    src = Path(__file__).read_text(encoding="utf-8")
    check("renderer reads only the whitelisted blind paths",
          "for k in WHITELIST" in src)
    check("sub-national division file is never referenced by this renderer",
          ("adm" + "1") not in src.lower())
    for iso in ISOS:
        rec = data[iso]
        pkt = packets[iso]
        vals = [v for v in (rec["score"], rec.get("nationalFrameworkScore"),
                            rec.get("band")) if v is not None]
        hits = [str(v) for v in vals
                if re.search(r"\b%s\b" % re.escape(str(v)), pkt)]
        check(f"{iso} packet carries no published score/band value", not hits, str(hits))
        anc = [a for a in (rec.get("anchorRefs") or [])
               if re.search(r"\b%s\b" % re.escape(a), pkt)]
        check(f"{iso} packet carries no frozen country anchor", not anc, str(anc))
        check(f"{iso} packet built only from the five whitelisted fields",
              set(pilot_fields(iso, data, ledger)) == set(WHITELIST))
    blob = "\n".join(packets.values())
    check("no tested COUNTRY_NAMES literal in any packet (case captions deliberately "
          "retained; identity may still be inferred - evidence-map section 5)",
          not [n for n in COUNTRY_NAMES
               if re.search(r"\b%s\b" % re.escape(n), blob)], "name literal present")
    # GBR pilot-only view: explicit third-party index scores/ranks gone, facts kept
    g = packets["GBR"]
    leaked = [s for s in ("22nd", "third steepest", "86% score", "45%",
                          "9th in 2020", "66% and concern", "down from 1st")
              if s in g]
    check("GBR packet excludes explicit third-party index scores and ranks",
          not leaked, str(leaked))
    kept = [s for s in ("hostile climate on trans rights", "steepest",
                        "86% of national respondents") if s in g]
    check("GBR packet preserves the associated substantive facts", len(kept) == 3,
          str(kept))
    # edits touched GBR only: other packets byte-equal to raw five-field assembly
    for iso in ("USA", "NPL", "VAT"):
        rec = data[iso]
        raw = {k: rec[k] for k in WHITELIST}
        check(f"{iso} packet untouched by ledger packet edits",
              packets[iso] == render_packet_from_fields(raw))
    check("ledger packet edits target GBR only",
          {e["iso"] for e in ledger["packet_edits"]} == {"GBR"})


# --------------------------------------------------------------------------- #
# 3. Two balanced randomized blocks + 40 provider-visible user messages
# --------------------------------------------------------------------------- #

def sentinel_assignments():
    """Predeclared before outputs: complementary sentinel (model, variant)
    assignments so each block stays balanced (10/10 variant, 10/10 family) and
    the run covers every (model, variant) once per sentinel kind."""
    m0, m1 = MODELS
    return {
        1: {"empty": [(m0, "A"), (m1, "B")], "neutral_label": [(m0, "B"), (m1, "A")]},
        2: {"empty": [(m0, "B"), (m1, "A")], "neutral_label": [(m0, "A"), (m1, "B")]},
    }


def block_rows(block, draw, assign):
    rows = []
    for iso in ISOS:
        for m in MODELS:
            for v in VARIANTS:
                rows.append({"block": block, "draw": draw, "case": iso,
                             "sentinel": "core", "model": m, "variant": v,
                             "label": CORE_LABEL, "fresh_context": True})
    for kind, cells in assign[block].items():
        for m, v in cells:
            rows.append({"block": block, "draw": draw,
                         "case": NEUTRAL_CASE if kind == "neutral_label" else "",
                         "sentinel": kind, "model": m, "variant": v,
                         "label": NEUTRAL_LABEL if kind == "neutral_label" else CORE_LABEL,
                         "fresh_context": True})
    return rows


def block_ok(rows) -> bool:
    if len(rows) != 20:
        return False
    if Counter(r["variant"] for r in rows) != Counter({"A": 10, "B": 10}):
        return False
    if Counter(r["model"] for r in rows) != Counter({MODELS[0]: 10, MODELS[1]: 10}):
        return False
    if Counter(r["sentinel"] for r in rows) != Counter(
            {"core": 16, "empty": 2, "neutral_label": 2}):
        return False
    idx = [i for i, r in enumerate(rows) if r["sentinel"] != "core"]
    if any(b - a == 1 for a, b in zip(idx, idx[1:])):
        return False  # sentinels interleaved with core, never adjacent
    run = max(len(list(g)) for _, g in groupby(r["variant"] for r in rows))
    return run <= 2  # randomized, bounded runs of one variant


def order_block(rows, block):
    for attempt in range(400):
        pool, out = rows[:], []
        rng = random.Random(SEED + 100 * block + attempt)
        rv, rn, ok = None, 0, True
        while pool:
            def eligible(r):
                if r["sentinel"] != "core" and out and out[-1]["sentinel"] != "core":
                    return False
                return not (r["variant"] == rv and rn >= 2)
            elig = [r for r in pool if eligible(r)]
            if not elig:
                ok = False
                break
            pick = rng.choice(elig)
            pool.remove(pick)
            if pick["variant"] == rv:
                rn += 1
            else:
                rv, rn = pick["variant"], 1
            out.append(pick)
        if ok and block_ok(out):
            return out
    die("schedule: no balanced interleaving found for the frozen seed")


def build_schedule():
    assign = sentinel_assignments()
    sched, call = [], 0
    for block, draw in ((1, 1), (2, 2)):
        for r in order_block(block_rows(block, draw, assign), block):
            call += 1
            r["call"] = call
            sched.append(r)
    return sched


def validate_schedule(sched):
    check("schedule: 40 attempts = 32 core + 8 sentinels, two blocks of 20",
          len(sched) == ATTEMPT_CEILING
          and sum(r["sentinel"] == "core" for r in sched) == CORE_CALLS
          and sum(r["sentinel"] != "core" for r in sched) == SENTINEL_CALLS
          and [r["call"] for r in sched] == list(range(1, 41)))
    cells = {(r["case"], r["model"], r["variant"], r["draw"])
             for r in sched if r["sentinel"] == "core"}
    want = {(c, m, v, d) for c in ISOS for m in MODELS for v in VARIANTS for d in (1, 2)}
    check("schedule: every country x family x variant x draw cell exactly once",
          cells == want and len(cells) == CORE_CALLS)
    check("schedule: both blocks balanced (10/10 variant, 10/10 family, sentinels interleaved)",
          all(block_ok([r for r in sched if r["block"] == b]) for b in (1, 2)))
    em = {(r["model"], r["variant"]) for r in sched if r["sentinel"] == "empty"}
    nm = {(r["model"], r["variant"]) for r in sched if r["sentinel"] == "neutral_label"}
    check("sentinels: 4 empty + 4 neutral, one per family x variant each",
          em == nm == {(m, v) for m in MODELS for v in VARIANTS})
    check("sentinels: neutral-label case and neutral label preselected before outputs",
          NEUTRAL_CASE in ISOS and NEUTRAL_LABEL != CORE_LABEL
          and all(r["case"] == NEUTRAL_CASE and r["label"] == NEUTRAL_LABEL
                  for r in sched if r["sentinel"] == "neutral_label"))
    check("schedule: fresh context per attempt, no outcome-based retries",
          all(r["fresh_context"] for r in sched)
          and PROPOSED_CAPS["retries_selected_for_output"] == 0)
    check("schedule: exact frozen model ids only",
          {r["model"] for r in sched} == set(MODELS))


def message_for(row, packets):
    body = EMPTY_BODY if row["sentinel"] == "empty" else packets[row["case"]]
    return f"{row['label']}\n\n{body}"


def build_messages(sched, packets):
    return [{**{k: r[k] for k in ("call", "block", "draw", "case",
                                  "sentinel", "model", "variant", "label")},
             "message": message_for(r, packets),
             "message_sha256": sha(message_for(r, packets).encode())}
            for r in sched]


def validate_messages(msgs, packets, sched):
    check("user messages: one frozen message per scheduled attempt",
          len(msgs) == ATTEMPT_CEILING
          and [m["call"] for m in msgs] == [r["call"] for r in sched])
    empty = [m["message"] for m in msgs if m["sentinel"] == "empty"]
    check("empty dossier: one anonymous message, states no evidence, no COUNTRY_NAMES "
          "literal",
          len(set(empty)) == 1 and EMPTY_BODY in empty[0]
          and not [n for n in COUNTRY_NAMES if n in empty[0]])
    neut = [m for m in msgs if m["sentinel"] == "neutral_label"]
    core_same = f"{CORE_LABEL}\n\n{packets[NEUTRAL_CASE]}"
    check("neutral-label sentinel: identical evidence bytes, only the dossier label changed",
          len(neut) == 4
          and all(m["message"].replace(NEUTRAL_LABEL, CORE_LABEL, 1) == core_same
                  and m["message"].startswith(NEUTRAL_LABEL + "\n\n") for m in neut))
    core = [m for m in msgs if m["sentinel"] == "core"]
    check("core messages: exact frozen packet bytes under the core label "
          "(repeats byte-identical within cell)",
          all(m["message"] == f"{CORE_LABEL}\n\n{packets[m['case']]}" for m in core))
    check("no tested COUNTRY_NAMES literal in any provider-visible message (identity "
          "may be inferred from the evidence itself)",
          not [n for n in COUNTRY_NAMES
               if any(n in m["message"] for m in msgs)])


# --------------------------------------------------------------------------- #
# 4. Scope precondition, freeze, verify
# --------------------------------------------------------------------------- #

def scope_precondition():
    out = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                         capture_output=True, text=True)
    if out.returncode != 0:
        die("git status failed: " + out.stderr.strip()[:80])
    lines = [l for l in out.stdout.splitlines() if l.strip()]
    staged = [l for l in lines if l[0] not in " ?"]
    modified = [l for l in lines if l[0] == "M" or l[1] == "M"]
    outside = [l[3:] for l in lines if not l[3:].startswith(AUDIT + "/")]
    check("no staged files", not staged, str(staged[:6]))
    check("no tracked file modified", not modified, str(modified[:6]))
    check("no writes outside the country-calibration-audit directory", not outside,
          str(outside[:6]))


def reservation_plan(sched, msgs, prompt_bytes):
    """Per-call administrative reservation units (UTF-8 bytes + framing units).

    Byte-for-byte the same unit arithmetic as runner.build_plan, so an
    independent recomputation reproduces the exact plan numbers.
    """
    return [prompt_bytes[row["variant"]] + len(msg["message"].encode("utf-8"))
            + RESERVATION_FRAMING_UNITS_PER_CALL
            for row, msg in zip(sched, msgs)]


def evidence_snapshot_status(current_sha, current_commit, man):
    """Content-hash equality is the reproducibility test; HEAD identity is only
    historical provenance. A code/docs-only advance of HEAD with identical
    recorded content must NOT fail --verify; content drift still must."""
    ok = current_sha == man["evidence_snapshot"]["sha256"]
    recorded = man.get("git_commit")
    if current_commit == recorded:
        return ok, ""
    note = (f" HEAD advanced to {str(current_commit)[:8]} (provenance only); "
            f"recorded freeze commit {str(recorded)[:8]} retained; "
            f"content sha256 {'identical' if ok else 'DRIFTED'}")
    return ok, note


def freeze(cands, packets, sched, msgs, ledger, dm):
    frozen = HERE / "frozen"
    prompt_bytes = {v: len(cands[v].encode()) for v in VARIANTS}
    plan_units = reservation_plan(sched, msgs, prompt_bytes)
    fits = (max(plan_units) <= RESERVATION_PER_CALL_UNITS
            and sum(plan_units) <= RESERVATION_AGGREGATE_UNITS)
    check("reservation amendment: exact plan fits the pre-outcome ceilings",
          fits, f"plan max={max(plan_units)} sum={sum(plan_units)}")
    if not fits:
        die("reservation amendment does not fit the exact plan; nothing written")
    (frozen / "packets").mkdir(parents=True, exist_ok=True)
    for v in VARIANTS:
        (frozen / f"single_{v.lower()}.txt").write_text(cands[v], encoding="utf-8")
    for iso, text in packets.items():
        (frozen / "packets" / f"{iso}.txt").write_text(text, encoding="utf-8")
    sched_b = (json.dumps(sched, indent=1, ensure_ascii=False) + "\n").encode()
    (frozen / "schedule.json").write_bytes(sched_b)
    msgs_b = (json.dumps(msgs, indent=1, ensure_ascii=False) + "\n").encode()
    (frozen / "user_messages.json").write_bytes(msgs_b)

    def fmeta(rel):
        b = (HERE / rel).read_bytes()
        return {"sha256": sha(b), "bytes": len(b)}

    src_meta = {ledger["source_prompts"][v]: sha((ROOT / ledger["source_prompts"][v]).read_bytes())
                for v in VARIANTS}
    # observed worst-case call input: max UTF-8 bytes over BOTH derived prompt
    # variants (the system prompts actually sent) crossed with ALL 40 frozen
    # messages - not the pairwise source prompts and not variant A alone
    max_in_bytes = max(prompt_bytes[v] + len(m["message"].encode())
                       for v in VARIANTS for m in msgs)
    manifest = {
        "experiment": EXP,
        "version": "single-country-v1 (derived; NOT byte-identical to the pairwise originals)",
        "git_commit": dm["commit"],
        "evidence_snapshot": {
            "path": DATA, "sha256": dm["sha"], "git_commit": dm["commit"],
            "note": "per-record source dates and limitations are retained inside the "
                    "packets; all other record paths (score, band, rank, provenance, "
                    "anchors, sub-national aggregates, named fields, source URLs) are "
                    "excluded by structural path-level whitelist"},
        "source_prompts": src_meta,
        "derived_prompts": {f"single_{v.lower()}.txt": fmeta(f"frozen/single_{v.lower()}.txt")
                            for v in VARIANTS},
        "ledger_sha256": sha((HERE / "ledger.json").read_bytes()),
        "ledger_ids": [e["id"] for e in ledger["prompt_edits"]]
                   + [e["id"] for e in ledger["packet_edits"]],
        "packets": {iso: fmeta(f"frozen/packets/{iso}.txt") for iso in ISOS},
        "neutral_sentinel": {"case": NEUTRAL_CASE, "neutral_label": NEUTRAL_LABEL,
                             "core_label": CORE_LABEL,
                             "rule": "identical evidence bytes; only the dossier label differs"},
        "empty_sentinel": {"label": CORE_LABEL, "body_sha256": sha(EMPTY_BODY.encode()),
                           "abstention": "output contract permits status=insufficient_evidence "
                                         "with score=null; no score is forced"},
        "models": list(MODELS),
        "requested_settings": REQUESTED_SETTINGS,
        "requested_settings_note": "requested, not provider-guaranteed",
        "proposed_caps": PROPOSED_CAPS,
        "reservation_amendment": {
            "id": "pre-outcome-reservation-amendment-1",
            "status": "pre-outcome: recorded before any attempt has ever been "
                      "dispatched; no receipt exists and no run has been made",
            "unit": "administrative input reservation unit = UTF-8 bytes of the "
                    "frozen system prompt + user message, plus a fixed "
                    f"{RESERVATION_FRAMING_UNITS_PER_CALL}-unit chat-framing "
                    "allowance per call",
            "not_claims": ["not a proven provider-native token bound",
                           "not a provider-enforced spend limit",
                           "the USD 10.00 ceiling is enforced locally by runner.py, "
                           "not by the provider account"],
            "per_call_input_reservation_units": RESERVATION_PER_CALL_UNITS,
            "aggregate_input_reservation_units": RESERVATION_AGGREGATE_UNITS,
            "plan_max_per_call_units": max(plan_units),
            "plan_aggregate_units": sum(plan_units),
            "plan_reproduce": "renderer.reservation_plan over the frozen schedule "
                              "+ user messages; independently reproduced by "
                              "runner.build_plan",
            "preserved_original_proposal": PRESERVED_PROPOSED_INPUT_CAPS,
            "preserved_design": ["40 attempts incl. failures", "frozen prompts, "
                                 "packets, schedule and order", "exact pre-registered "
                                 "models", "frozen requested settings", "zero retries",
                                 "USD 10.00 aggregate local ceiling incl. failures"],
            "rationale": "the byte+framing plan (66 611 max / 2 316 208 aggregate) "
                         "did not fit the original 20 000/800 000 proposal; an "
                         "explicit, reviewable reservation-only amendment keeps the "
                         "design and the spend ceiling unchanged instead of silently "
                         "raising or reinterpreting a cap",
            "document": "budget-amendment.md"},
        "seed": SEED, "blocks": 2,
        "core_calls": CORE_CALLS, "sentinel_calls": SENTINEL_CALLS,
        "attempt_ceiling": ATTEMPT_CEILING,
        "max_input_bytes_per_call_observed": max_in_bytes,
        "schedule_file_sha256": sha(sched_b),
        "user_messages_file_sha256": sha(msgs_b),
        "preflight": "preflight.md - claim-level source preflight is REQUIRED before "
                     "any provider execution; a signed preflight_receipt.json "
                     "(schema v2) binding these exact hashes plus runner.py, "
                     "budget-amendment.md and the independent evidence/budget "
                     "reviews is the runner's hard gate",
        "live_code": "none executed - no model call has ever been made and this renderer "
                     "cannot make one; runner.py is disabled by default and requires both "
                     "an explicit --execute flag and a hash-bound reviewed preflight "
                     "receipt; no national score writes",
    }
    (frozen / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    check("frozen prompts, packets, schedule, messages and manifest written under experiment dir",
          True)


def verify_frozen(cands, packets, sched, msgs, ledger, dm):
    mpath = HERE / "frozen" / "manifest.json"
    if not mpath.exists():
        check("frozen manifest present", False, "missing - run --build first")
        return None
    man = load(mpath)
    for v in VARIANTS:
        name = f"single_{v.lower()}.txt"
        disk = (HERE / "frozen" / name).read_bytes()
        check(f"frozen {name}: bytes match manifest hash and fresh re-derivation",
              sha(disk) == man["derived_prompts"][name]["sha256"]
              and disk == cands[v].encode())
    for iso in ISOS:
        disk = (HERE / "frozen" / "packets" / f"{iso}.txt").read_bytes()
        check(f"frozen packet {iso}: bytes match manifest hash and fresh re-render",
              sha(disk) == man["packets"][iso]["sha256"]
              and disk == packets[iso].encode())
    sb = (HERE / "frozen" / "schedule.json").read_bytes()
    ub = (HERE / "frozen" / "user_messages.json").read_bytes()
    check("frozen schedule: bytes match manifest hash and fresh rebuild",
          sha(sb) == man["schedule_file_sha256"] and json.loads(sb) == sched)
    check("frozen user messages: bytes match manifest hash and fresh rebuild",
          sha(ub) == man["user_messages_file_sha256"] and json.loads(ub) == msgs)
    check("ledger bytes match manifest",
          sha((HERE / "ledger.json").read_bytes()) == man["ledger_sha256"])
    ok, note = evidence_snapshot_status(dm["sha"], dm["commit"], man)
    check("evidence snapshot content unchanged since freeze" + note, ok,
          f"content sha256 {dm['sha'][:16]} vs recorded "
          f"{man['evidence_snapshot']['sha256'][:16]}")
    am = man.get("reservation_amendment") or {}
    pb = {v: len(cands[v].encode()) for v in VARIANTS}
    units = reservation_plan(sched, msgs, pb)
    check("reservation amendment: pre-outcome ceilings unchanged, exact plan fits, "
          "original 20 000/800 000 proposal preserved",
          am.get("per_call_input_reservation_units") == RESERVATION_PER_CALL_UNITS
          and am.get("aggregate_input_reservation_units") == RESERVATION_AGGREGATE_UNITS
          and am.get("plan_max_per_call_units") == max(units)
          and am.get("plan_aggregate_units") == sum(units)
          and max(units) <= RESERVATION_PER_CALL_UNITS
          and sum(units) <= RESERVATION_AGGREGATE_UNITS
          and am.get("preserved_original_proposal") == PRESERVED_PROPOSED_INPUT_CAPS
          and {k: man["proposed_caps"][k]
               for k in PRESERVED_PROPOSED_INPUT_CAPS} == PRESERVED_PROPOSED_INPUT_CAPS,
          f"plan max={max(units)} sum={sum(units)}")
    check("source pairwise prompts unchanged since freeze",
          all(sha((ROOT / rel).read_bytes()) == h
              for rel, h in man["source_prompts"].items()))
    return man


def dir_fingerprint():
    """sha256 of every file under this experiment dir (bytecode caches ignored);
    used by --verify to prove the whole run modified nothing."""
    return {str(p.relative_to(HERE)): sha(p.read_bytes())
            for p in sorted(HERE.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


def tamper_selftest(man):
    if man is None:
        check("tamper self-test (in-memory, no writes)", False, "no manifest")
        return
    bad = bytearray((HERE / "frozen" / "single_a.txt").read_bytes())
    bad[100] ^= 0x01
    p = sha(bytes(bad)) == man["derived_prompts"]["single_a.txt"]["sha256"]
    bad2 = bytearray((HERE / "frozen" / "packets" / "GBR.txt").read_bytes())
    bad2[50] ^= 0x01
    g = sha(bytes(bad2)) == man["packets"]["GBR"]["sha256"]
    sch = json.loads((HERE / "frozen" / "schedule.json").read_text(encoding="utf-8"))
    sch[0]["variant"] = "A" if sch[0]["variant"] == "B" else "B"
    s = sha((json.dumps(sch, indent=1, ensure_ascii=False) + "\n").encode()) \
        == man["schedule_file_sha256"]
    check("tamper self-test: modified prompt, packet and schedule all rejected in memory",
          not (p or g or s))


def check_static():
    src = Path(__file__).read_text(encoding="utf-8")
    test = HERE / "test_renderer.py"
    blob = src + (test.read_text(encoding="utf-8") if test.exists() else "")
    tokens = ("ur" + "llib", "re" + "quests", "sock" + "et", "api" + "_key",
              "API" + "_KEY", "Bear" + "er ", "call" + "_api")
    bad = [t for t in tokens if t in blob]
    check("no network client, credential or provider execution code in renderer/tests",
          not bad, str(bad))
    write_token = "(ROOT / DATA)" + ".wri" + "te"
    check("no score-write path: renderer only writes under its own experiment dir",
          write_token not in src and 'HERE / "frozen"' in src)


def data_meta():
    b = (ROOT / DATA).read_bytes()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    return {"sha": sha(b), "commit": commit, "data": json.loads(b.decode("utf-8"))}


def main():
    args = set(sys.argv[1:])
    if "--build" in args:
        mode = "build"
    elif "--verify" in args:
        mode = "verify"
    else:
        print("usage: renderer.py --build (derive + render + freeze, scope-checked) | "
              "--verify (read-only re-derivation, byte checks, tamper self-test)")
        sys.exit(2)
    fp_before = dir_fingerprint() if mode == "verify" else None
    if mode == "build":
        scope_precondition()
        if any(not ok for _, ok in RESULTS):
            die("scope precondition failed; nothing written")
    ledger = load(HERE / "ledger.json")
    cands = derive_prompts(ledger)
    validate_prompts(cands)
    dm = data_meta()
    packets = {iso: render_packet(iso, dm["data"], ledger) for iso in ISOS}
    validate_packets(packets, dm["data"], ledger)
    sched = build_schedule()
    validate_schedule(sched)
    msgs = build_messages(sched, packets)
    validate_messages(msgs, packets, sched)
    check_static()
    if mode == "build":
        if all(ok for _, ok in RESULTS):
            freeze(cands, packets, sched, msgs, ledger, dm)
            scope_precondition()
        else:
            die("freeze skipped: at least one check failed; nothing written")
    else:
        man = verify_frozen(cands, packets, sched, msgs, ledger, dm)
        tamper_selftest(man)
        check("verify mode wrote nothing (whole experiment-dir fingerprint unchanged)",
              dir_fingerprint() == fp_before)
    report()


if __name__ == "__main__":
    main()