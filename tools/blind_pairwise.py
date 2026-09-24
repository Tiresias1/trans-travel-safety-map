#!/usr/bin/env python3
"""Blind pairwise score refinement for the Trans Travel Safety Map.

Runs `--num-pairs` blind head-to-head ratings. For each pair the tool:

  1. picks two countries at random (only those with complete `blind*` fields);
  2. sends the rating model an **identity-stripped** dossier for each — no names,
     no scores, no bands, no ranks, no source URLs, no comparator references;
  3. asks it to rate both on the 0.00–1.00 trans-visitor-outing-risk scale;
  4. nudges the stored scores toward the model's ratings using the
     absolute-percent → absolute-shift → differential-weighting scheme below.

The dossier is built from the 1:1 anonymised mirrors of the research fields
(`blindSummary`, `blindOutOfScope`, `blindSourceSummaries`, `blindLocalsOnly`,
`blindTangential`). `comparisons` is never sent — it names other jurisdictions
with their scores, and handing the model pre-made pairwise conclusions would
defeat the purpose of generating independent ones. See tools/blind_fields.md.

Update maths (per pair, with originals a0/b0 and model ratings ra/rb).
All three weighting parameters may be given either as a scalar or as a
`START-END` ramp that interpolates linearly across the run (pair 1 gets START,
the last pair gets END). Ramping high→low makes the run coarse-to-fine: large
corrections early while the map is still rough, gentle settling as it converges.

    step 1  absolute percent   a1 = a0 + P_abs * (ra - a0)          [P_abs = 0.05]
                               b1 = b0 + P_abs * (rb - b0)
    step 2  absolute shift     a2 = a1 ± min(S_abs, |ra - a1|)      [S_abs = 0.004]
                               b2 = b1 ± min(S_abs, |rb - b1|)
    step 3  differential       gap   = (rb - ra) - (b2 - a2)
                               delta = P_diff * gap                 [P_diff = 0.10]
                               a3 = a2 - delta/2 ;  b3 = b2 + delta/2
    clamps                     each score is confined to the corridor between its
                               own original value and its own model rating, then
                               to [0.0, 1.0]. A score can therefore never overshoot
                               the direction the model indicated.

Ramp example (defaults suggested for a long run):

    --absolute-weighting-percent   0.15-0.015
    --absolute-weighting-shift     0.012-0.0012
    --differential-weighting-percent 0.25-0.03

Note on the worked example in the brief: it states ratings 0.2/0.7 (a rated gap of
0.5) but then computes with a gap of 0.4 and a difference of 0.117. This
implementation uses the stated *formula* (P_diff × (rated_gap − current_gap), split
equally), which is unambiguous.

Prompt caching: everything fixed — role, scale, band definitions, the full
outing-risk taxonomy, and the rating rules — is sent as a single `system` text
block carrying `cache_control: {"type": "ephemeral"}`. The block is built once per
process and is byte-identical for every request, so the provider can serve it from
cache for the whole run. Only the two dossiers vary, and they live in the `user`
message. Use `--no-cache` if the endpoint rejects `cache_control`.

Usage:
    python3 tools/blind_pairwise.py --api-key KEY --num-pairs 10000
    python3 tools/blind_pairwise.py --api-key KEY --num-pairs 20 --workers 4
    python3 tools/blind_pairwise.py --dry-run --num-pairs 2      # inspect prompts
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COUNTRIES = ROOT / "data" / "countries.json"
TAXONOMY = ROOT / "research" / "outing-risk-taxonomy.md"

# 1:1 anonymised mirrors of the source fields. See tools/blind_fields.md.
# REQUIRED must all be present for a record to be pairable; OPTIONAL are included
# when present (they are absent from many source records).
REQUIRED_BLIND = ("blindSummary", "blindOutOfScope", "blindSourceSummaries")
OPTIONAL_BLIND = ("blindLocalsOnly", "blindTangential")
BLIND_FIELDS = REQUIRED_BLIND + OPTIONAL_BLIND

# --------------------------------------------------------------------------- #
# Fixed prompt (cached)
# --------------------------------------------------------------------------- #

RATING_RULES = """\
## Rating rules (read carefully — these are the corrections that matter most)

1. **Rate the traveler, not the resident.** A visitor uses their home passport and will
   never apply for legal gender recognition in the country you are rating. Domestic
   self-ID regimes, gender-recognition certificates, marriage equality, adoption rights,
   conversion-therapy bans, intersex-surgery bans, employment anti-discrimination law and
   transition-healthcare infrastructure are therefore **climate signals at most** — they
   hint at how trans-respecting institutions are, but they never offset an active
   traveler-facing restriction. Never treat them as protections.

2. **General-LGB criminalisation is a secondary, situational factor.** A sodomy statute
   reaches only the fraction of trans visitors whose relationships are read as same-sex
   under birth-sex legal status, or whom police extort using it. Weight it at roughly
   0.01–0.03 of the scale unless there is documented trans-specific enforcement (arrests
   for gender expression, "impersonation"/"posing" charges, extortion of visibly trans
   people). It is never a primary score driver on its own. That said, if there is no
   trans-related climate signals to go on, you may have no choice but to use data about
   LGB criminalisation as a weak proxy for trans.

3. **Burden-of-proof symmetry.** A documented positive (an institutionalised third-gender
   tradition, a court ruling protecting gender expression, functioning hate-crime
   recourse) counts for at least as much as a documented negative. Do not treat one
   jurisdiction's *absence* of documented incidents as stronger evidence than another's
   *presence* of documented acceptance or documented abuse. Absence of evidence in a
   closed or under-researched state is not safety, and it is not danger either — rate what
   the record actually supports and say so.

4. **No regional or cultural pattern-matching.** Do not adjust a rating because of which
   part of the world the facts sound like. Two dossiers with identical facts must receive
   identical ratings regardless of implied geography. If you notice yourself inferring the
   country, deliberately discount that inference and rate the facts.

5. **Derive, don't anchor.** Work from the severity ladder and the axis evidence to a
   number. Do not start from a vague impression of "this sounds like a safe/unsafe place"
   and then decorate it.

6. **Laws on the books vs. enforcement.** An unenforced statute a comparably small factor.
   A statute with documented arrests, convictions, or police practice is a quite large one.
   Note which you are looking at.

7. **Individual incidents: weigh what they prove, not how shocking they are.** Most crime
   never makes international news; a single reported incident — even a severity-5 one — is
   very weak evidence about the *rate* of violence in a medium or large country, and on its
   own should barely move a rating. Selection bias is real: where anti-trans violence is
   routine, each incident often attracts less coverage than a rare shocking case elsewhere.
   What elevates an incident to score-relevant evidence:
   - it is part of a documented pattern (repeats, counts, "systemic"/"widespread" findings);
   - the state is implicated (police or prison custody, officials as perpetrators,
     state-linked actors);
   - the state's *response* is itself damning (refusal to investigate, prosecuting the
     victim, documented impunity for perpetrators);
   - the jurisdiction is very small, so one case carries real statistical weight.
   Conversely, the response can be **positive** evidence: prosecution and conviction of
   attackers, public outcry, sympathetic coverage, or institutional reform after an incident
   signal that society and the state treat anti-trans violence as unacceptable. Prefer
   patterns, counts, enforcement frequency and institutional behaviour over single
   anecdotes, while still counting anecdotes.

8. **General crime, terrorism, war and natural hazards are out of scope** unless they
   independently raise trans-specific risk (e.g. collapse of police protection for a
   group that is already targeted, or militia targeting of gender-nonconforming people).

9. **Severity dominates probability of outing.** Every trans person carries some baseline
   probability of being outed. What separates say 0.9 from 0.2 is mostly what happens *after*
   the outing, and whether the state is the perpetrator, a bystander, or a protector. That said,
   deliberate efforts by the state to out trans people ramp up the risk of outing, and thus
   the odds of adverse consequences to a trans traveler.

10. 0.00 means a trans visitor who is discovered faces near-certain imprisonment or execution.
    1.00 means law and society fully accept trans people with no discrimination or judgement
    (within the bounds of reason in that no society is 100 percent homogenous).

11. **Rule of law partially mediates between paper protections and street reality.** Where legal
    protections coexist with public hostility, a partial factor to consider for the rating
    is whether the legal system actually works for trans people: are attackers prosecuted,
    are protections enforced, are complaints taken seriously? Strong rule of law discounts
    public hostility somewhat; a complete lack of rule of law makes paper protections
    near-worthless. Where law and society are aligned in acceptance, rule of law is for the most
    part just a general-travelers issue, not a trans issue. Where law is well against trans people,
    rule of law actually turns into a liability, particularly if the public is hostile as well.
    
12. Where the dossier is silent about institutions — some jurisdictions simply lack much data —
    assume neither dysfunction nor perfection (an absense of evidence is not evidence of absense);
    just work with the data that you have available to you.
"""

ADMIN1_RULES = """\
## Sub-national rating rules (these apply in addition to everything above)

Both dossiers are first-level administrative divisions (states, provinces, regions) of
the **same country**, whose national profile is given above. Rate each division as the
national score plus or minus the sub-national deviation its own dossier supports.

1. **Do not re-rate national factors.** Federal/national law, border and passport
   friction, and the national enforcement climate are already priced into the national
   score and are identical for both divisions. Only what genuinely differs between the
   two divisions should move your scores, and only by as much as the dossier supports.

2. **Legal hierarchy — who can actually override whom.** Where the rule of law is strong
   and a region has *not* been explicitly granted autonomy over the relevant subject,
   regions cannot override national law: a regional statute, decree or resolution
   conflicting with national law is signalling and political climate, not operative risk.
   Where the rule of law is weak, regional and local authorities can bend national law in
   practice — in **either** direction (harsher enforcement than the national standard, or
   de-facto tolerance despite hostile national law). Weigh regional practice accordingly,
   and say in your reasoning which case you judged applies.

3. **Autonomy that is real counts.** A region with genuine devolved power over the
   subject (its own criminal law, its own courts, its own policing) can legitimately
   diverge widely from the national score. A region whose only lever is symbolic
   declarations cannot.

4. **Enforcement beats statute.** A court-blocked ban is a small factor; a ban with
   documented arrests, trespass warnings, or filed bounty suits is a large one. Documented
   institutional responses (conviction of attackers, charges dismissed, civil-rights
   findings) are positive evidence.  At the same time, remember: absense of evidence is
   not evidence of absense.

5. **Equal scores are correct when the dossiers warrant them.** Two divisions sharing the
   same tier evidence and no division-specific facts should receive the same score. Do not
   invent a difference to look decisive.

6. **Documentation density is not danger; under-documentation is not safety.** Documented
   incidents, arrests and recorded attacks concentrate where visible trans people and
   reporting infrastructure exist — overwhelmingly, major cities. A no-signal division is
   not safer: it inherits the national climate, including its social conservatism and its
   unreported informal violence, exactly. Rate a documented city *below* an undocumented
   division only when its record shows structural hostility beyond the national climate
   (local ordinances or enforcement campaigns, vigilante patterns met with impunity,
   religious-authority governance). A pile of documented city incidents is usually also
   evidence of the city where out LGBT people actually live — weigh the visibility, the
   anonymity of scale, the community resources and the tourism economy on the other side
   of the ledger.
"""

ANCHOR_ISOS = ("ISL", "NLD", "GBR", "USA", "TUR", "EGY", "AFG")


def build_admin1_system_prompt(taxonomy_text: str, parent: dict, parent_iso: str,
                               countries: dict) -> str:
    """System prompt for in-country sub-national pairs.

    The parent country is deliberately NOT blinded: the rater needs full national
    context to judge deviations from it. Everything here is constant for the whole
    run (one run = one country), so it stays cacheable.
    """
    anchors = " · ".join(
        f"{countries[i]['name']} {countries[i]['score']:.2f}"
        for i in ANCHOR_ISOS if i in countries)

    def clean(s):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(s or ""))).strip()

    ctx = [f"### NATIONAL ASSESSMENT\n{clean(parent.get('summary'))}"]
    if parent.get("tangentialFactors"):
        ctx.append("### NATIONAL SECONDARY / SITUATIONAL FACTORS\n"
                   + clean(parent["tangentialFactors"]))
    if parent.get("localsOnly"):
        ctx.append("### AFFECTS RESIDENTS MORE THAN VISITORS\n"
                   + clean(parent["localsOnly"]))
    if parent.get("outOfScopeNotes"):
        ctx.append("### NOT FACTORED INTO THE NATIONAL SCORE\n"
                   + clean(parent["outOfScopeNotes"]))
    national_context = "\n\n".join(ctx)

    return f"""\
You are an expert assessor of travel risk for transgender people. You will be given two
anonymised dossiers, labelled A and B. Each describes one first-level administrative
division of a single country, identified below. Rate each division on the same 0.00–1.00
scale, for a **transgender visitor** discovered or outed there.

You are not told either division's existing score. Derive both from the dossiers.

## The country

**{parent['name']}** ({parent_iso}) — national score **{parent['score']:.2f}**,
band: {parent.get('band', '')}. {len(parent.get('sources', []))} sources behind the
national assessment.

For scale orientation, current scores elsewhere on the map: {anchors}.

{national_context}

## The scale

0.00–1.00, continuous, **higher is safer**.

- **0.00** — A trans visitor who is outed faces near-certain imprisonment or execution.
- **1.00** — the aspirational limit: law and society fully accept trans people as their
  gender identity with zero discrimination or judgement. No jurisdiction reaches it
  perfectly, of course; do not withhold high scores merely because a flawless record
  cannot be proven.

Bands (orientation only — you output numbers): [0.00, 0.20) Do Not Travel ·
[0.20, 0.40) High Risk · [0.40, 0.60) Elevated Risk · [0.60, 0.80) Reduced Risk ·
[0.80, 1.00] Low Risk

{RATING_RULES}
{ADMIN1_RULES}
---

# Reference documentation: the outing-risk taxonomy

{taxonomy_text.strip()}

---

{OUTPUT_FORMAT}"""


OUTPUT_FORMAT = """\
## Output format

Reply with **only** a single JSON object, no prose before or after it:

{"score_a": <float 0.0-1.0>, "score_b": <float 0.0-1.0>, "why": "<= 40 words, the decisive axis-level differences"}

Both scores are on the same 0.00–1.00 scale described above, where **higher is safer**.
Give two decimal places. `score_a` rates dossier A, `score_b` rates dossier B. They may be
equal if the dossiers genuinely warrant it. Rate each on its merits against the scale —
do not force a difference, and do not let the order of presentation influence you.
"""


def build_system_prompt(taxonomy_text: str) -> str:
    """Assemble the fixed prompt. Built once per process → byte-identical → cacheable."""
    return f"""\
You are an expert assessor of travel risk for transgender people. You will be given two
anonymised research dossiers, labelled A and B. Each describes one jurisdiction. You do not
know which jurisdictions they are, and you must not try to guess: your rating must follow
from the documented facts alone.

Your task: rate **each** dossier on the scale below, independently, as the risk faced by a
**transgender visitor** to that jurisdiction if they are discovered or outed there.

## The scale

0.00–1.00, continuous, **higher is safer**.

- **0.00** — A trans visitor who is outed faces near-certain imprisonment or execution. The
  absolute extreme of "do not visit".
- **1.00** — the aspirational limit: law and society fully accept trans people as their
  gender identity with zero discrimination or judgement. No jurisdiction reaches it
  perfectly, of course; do not withhold high scores merely because a flawless record
  cannot be proven.

Bands (for orientation only — you output a number, not a band):
[0.00, 0.20) Do Not Travel · [0.20, 0.40) High Risk · [0.40, 0.60) Elevated Risk ·
[0.60, 0.80) Reduced Risk · [0.80, 1.00] Low Risk

The score integrates **probability of being outed** × **severity of what happens if outed**,
across every axis below.

{RATING_RULES}
---

# Reference documentation: the outing-risk taxonomy

{taxonomy_text.strip()}

---

{OUTPUT_FORMAT}"""


# --------------------------------------------------------------------------- #
# Dossier construction (variable, uncached part)
# --------------------------------------------------------------------------- #

def dossier(rec: dict) -> str:
    """Render the identity-stripped evidence for one jurisdiction.

    Order matters for readability but not for caching (this text is in the
    uncached user message). Source summaries carry most of the concrete
    evidence, so they are rendered individually rather than concatenated.
    """
    parts = []

    def clean(s: str) -> str:
        s = re.sub(r"<[^>]+>", " ", str(s))
        return re.sub(r"\s+", " ", s).strip()

    if rec.get("blindSummary"):
        parts.append(f"### ASSESSMENT\n{clean(rec['blindSummary'])}")

    ss = rec.get("blindSourceSummaries")
    if isinstance(ss, list) and ss:
        items = "\n".join(f"- {clean(x)}" for x in ss if str(x).strip())
        parts.append(f"### SOURCE EVIDENCE\n{items}")

    if rec.get("blindTangential"):
        parts.append("### SECONDARY / SITUATIONAL FACTORS\n"
                     f"{clean(rec['blindTangential'])}")
    if rec.get("blindLocalsOnly"):
        parts.append("### AFFECTS RESIDENTS MORE THAN VISITORS\n"
                     f"{clean(rec['blindLocalsOnly'])}")
    if rec.get("blindOutOfScope"):
        parts.append("### DELIBERATELY NOT COUNTED\n"
                     f"{clean(rec['blindOutOfScope'])}")

    return "\n\n".join(parts)


def admin1_dossier(rec: dict) -> str:
    """Sub-national dossier. Division names are NOT hidden — only scores are.

    The rater needs to know which region it is reading to weigh autonomy and legal
    hierarchy; hiding names would prevent that judgement. Source URLs are omitted
    (the summary carries their substance) to keep the uncached part small.
    """
    def clean(s):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(s or ""))).strip()

    parts = [f"### DIVISION\n{rec.get('name', '?')}"]
    if rec.get("summary"):
        parts.append(f"### ASSESSMENT\n{clean(rec['summary'])}")
    if rec.get("modelContext"):
        parts.append("### MODEL CONTEXT (general knowledge of this division — culture, "
                     "religiosity, rule of law, urbanism; NOT dossier-researched, weigh "
                     "as context)\n" + clean(rec["modelContext"]))
    if rec.get("outOfScopeNotes"):
        parts.append("### NOT FACTORED\n" + clean(rec["outOfScopeNotes"]))
    if rec.get("estimated"):
        parts.append("### DATA STATUS\nThis division's assessment is a flagged estimate "
                     "from national-level knowledge of its distinct legal system, not a "
                     "dedicated research dossier. Rate what it supports; do not treat "
                     "thin data as either safety or danger.")
    return "\n\n".join(parts)


def build_user_prompt(rec_a: dict, rec_b: dict) -> str:
    return f"""\
Rate the two dossiers below.

## DOSSIER A

{dossier(rec_a)}

## DOSSIER B

{dossier(rec_b)}

Reply with only the JSON object described in the output format."""


def build_admin1_user_prompt(rec_a: dict, rec_b: dict) -> str:
    return f"""\
Rate the two divisions of {rec_a.get('_parent_name', 'the country')} below.

## DIVISION A

{admin1_dossier(rec_a)}

## DIVISION B

{admin1_dossier(rec_b)}

Reply with only the JSON object described in the output format."""


# --------------------------------------------------------------------------- #
# Update maths
# --------------------------------------------------------------------------- #

def shift_toward(cur: float, target: float, cap: float) -> float:
    """Move `cur` toward `target` by at most `cap`."""
    rem = target - cur
    if rem == 0:
        return cur
    step = rem if abs(rem) <= cap else (cap if rem > 0 else -cap)
    return cur + step


def clamp_corridor(v: float, orig: float, rated: float) -> float:
    lo, hi = min(orig, rated), max(orig, rated)
    return min(1.0, max(0.0, min(hi, max(lo, v))))


def parse_range(spec: str) -> tuple[float, float]:
    """Accept either a scalar ('0.1') or a start-end ramp ('0.25-0.03').

    A scalar becomes (v, v) so the ramp math degenerates to a constant.
    Negative ends must be written with the explicit separator, e.g. '0.1--0.1'.
    """
    s = str(spec).strip()
    # split on a hyphen that is NOT a leading minus sign
    m = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+(?:\.\d+)?)\s*", s)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        if lo < 0 or hi < 0:
            raise argparse.ArgumentTypeError(
                f"weighting values must be >= 0, got {spec!r}")
        return lo, hi
    try:
        v = float(s)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"expected a number or a 'start-end' range, got {spec!r}")
    if v < 0:
        raise argparse.ArgumentTypeError(
            f"weighting values must be >= 0, got {spec!r}")
    return v, v


def ramp(start: float, end: float, idx: int, total: int) -> float:
    """Linearly interpolate from `start` to `end` over the run.

    idx is 1-based. The first pair gets `start`, the last gets `end`. With
    total <= 1 the start value is used. Higher early / lower late means the
    run makes big corrections while the map is still coarse and settles into
    fine adjustments as it converges.
    """
    if total <= 1:
        return start
    t = (idx - 1) / (total - 1)
    return start + (end - start) * t


MIXED_SYSTEM_EXTRA = """

## This run: one region, one country

One dossier describes an **administrative region**, presented as a bundle: the legal
and social framework the encompassing state imposes on it (the state is anonymised,
as in every dossier here), plus what the region itself adds or subtracts — its own
statutes, institutions, enforcement record and culture. Where the region's dossier
mentions the encompassing state's current whole-country score, treat it as context
for the framework's severity — **not a floor, not a ceiling**: a region may clearly
outrank or outrank-out its state. Blocked attempts at better law are evidence about
the region's intent and climate; the laws actually in force remain what the visitor
stands under. Weight what is enforced.

The other dossier describes a **country** in the usual way. Rate both on the same
absolute scale, from documented facts only: a region should score like the country
whose total bundle (framework + deviations + culture + rule of law) it most
resembles."""


def compute_update_mixed(a0: float, country_score: float, ra: float, rb: float,
                         p_abs: float, s_abs: float, p_diff: float) -> dict:
    """Region-only update: absolute terms toward the region's own rating, then the
    full differential correction against the comparator's TRUE stored score
    (the country never moves)."""
    a1 = a0 + p_abs * (ra - a0)
    a2 = shift_toward(a1, ra, s_abs)
    cur_gap = country_score - a2          # how much better country looks on the map
    rated_gap = rb - ra                   # how much better rater says country is
    delta = p_diff * (rated_gap - cur_gap)
    a3 = a2 + delta                       # region absorbs the whole correction
    a4 = min(1.0, max(0.0, a3))
    return {
        "a": {"orig": a0, "rated": ra, "pct": a1, "shift": a2,
              "diff": a3, "final": a4},
        "b": {"orig": country_score, "rated": rb, "frozen": True},
        "delta_diff": delta,
    }


def render_parent_bundle(parent: dict) -> str:
    """The encompassing state's blind profile, relabelled as the framework the
    region stands under."""
    def clean(s):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(s or ""))).strip()
    parts = []
    if parent.get("blindSummary"):
        parts.append(clean(parent["blindSummary"]))
    if parent.get("blindTangential"):
        parts.append("[Secondary factors] " + clean(parent["blindTangential"]))
    if parent.get("blindLocalsOnly"):
        parts.append("[Resident-facing] " + clean(parent["blindLocalsOnly"]))
    ss = parent.get("blindSourceSummaries")
    if isinstance(ss, list) and ss:
        items = "\n".join(f"- {clean(x)}" for x in ss[:8] if str(x).strip())
        parts.append("Evidence on the framework:\n" + items)
    return "\n\n".join(parts)


def build_mixed_user_prompt(region: dict, parent_rec: dict, country: dict,
                            flip: bool) -> str:
    rb_text = (region.get("_blindRegion") or "").strip()
    if not rb_text:  # fallback: use the record's own summary + model context
        def clean(t):
            return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(t or ""))).strip()
        rb_text = clean(region.get("summary")) + "\n\n" + clean(region.get("modelContext"))
    region_block = (
        f"An administrative region ('{region.get('name', '?')}') within the state "
        f"described below, which imposes that framework on it directly.\n\n"
        f"### FRAMEWORK IMPOSED BY THE ENCOMPASSING STATE\n"
        f"{render_parent_bundle(parent_rec)}\n\n"
        f"[The encompassing state's current whole-country score on this map: "
        f"{parent_rec.get('score', 0):.2f} — context for the framework's severity, "
        f"not a floor or ceiling for the region.]\n\n"
        f"### THE REGION'S OWN ADDITIONS AND SUBTRACTIONS\n{rb_text}")
    country_block = dossier(country)
    if flip:
        a_head, b_head = ("DOSSIER A — COUNTRY\n\n" + country_block,
                          "DOSSIER B — REGION (imposed framework + local bundle)\n\n" + region_block)
        mapping = ("score_a rates the COUNTRY, score_b rates the REGION")
    else:
        a_head = "DOSSIER A — REGION (imposed framework + local bundle)\n\n" + region_block
        b_head = "DOSSIER B — COUNTRY\n\n" + country_block
        mapping = "score_a rates the REGION, score_b rates the COUNTRY"
    return (f"Rate the two dossiers below.\n\n## {a_head}\n\n## {b_head}\n\n"
            f"Reply with only the JSON object described in the output format, where "
            f"{mapping}.")


def compute_update(a0: float, b0: float, ra: float, rb: float,
                   p_abs: float, s_abs: float, p_diff: float) -> dict:
    a1 = a0 + p_abs * (ra - a0)
    b1 = b0 + p_abs * (rb - b0)
    a2 = shift_toward(a1, ra, s_abs)
    b2 = shift_toward(b1, rb, s_abs)
    cur_diff = b2 - a2
    rated_diff = rb - ra
    delta = p_diff * (rated_diff - cur_diff)
    a3 = a2 - delta / 2.0
    b3 = b2 + delta / 2.0
    a4 = clamp_corridor(a3, a0, ra)
    b4 = clamp_corridor(b3, b0, rb)
    return {
        "a": {"orig": a0, "rated": ra, "pct": a1, "shift": a2,
              "diff": a3, "final": a4, "clamped": a3 != a4},
        "b": {"orig": b0, "rated": rb, "pct": b1, "shift": b2,
              "diff": b3, "final": b4, "clamped": b3 != b4},
        "delta_diff": delta,
    }


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #

def call_api(args, system_text: str, user_text: str, attempt: int = 0) -> dict:
    url = args.baseurl.rstrip("/") + args.endpoint_suffix
    body = {
        "model": args.model,
        "max_tokens": args.reasoning_tokens + args.max_output_tokens,
        "system": [{
            "type": "text",
            "text": system_text,
            **({} if args.no_cache else {"cache_control": {"type": "ephemeral"}}),
        }],
        "messages": [{"role": "user", "content": [{"type": "text", "text": user_text}]}],
    }
    if args.reasoning_tokens > 0:
        body["thinking"] = {"type": "enabled", "budget_tokens": args.reasoning_tokens}
    else:
        body["temperature"] = args.temperature

    headers = {"content-type": "application/json",
               "anthropic-version": args.anthropic_version}
    if args.auth_style in ("api-key", "both"):
        headers["x-api-key"] = args.api_key
    if args.auth_style in ("bearer", "both"):
        headers["Authorization"] = f"Bearer {args.api_key}"

    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as r:
            raw = r.read().decode("utf-8", "replace")
        return json.loads(raw)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:600]
        if e.code in (429, 500, 502, 503, 504) and attempt < args.retries:
            time.sleep(args.backoff * (2 ** attempt) + random.random())
            return call_api(args, system_text, user_text, attempt + 1)
        raise RuntimeError(f"HTTP {e.code}: {detail}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        if attempt < args.retries:
            time.sleep(args.backoff * (2 ** attempt) + random.random())
            return call_api(args, system_text, user_text, attempt + 1)
        raise RuntimeError(f"request failed: {e}") from None


JSON_RE = re.compile(r"\{[^{}]*\"score_a\"[^{}]*\}", re.S)
SCORE_A_RE = re.compile(r"\"score_a\"\s*:\s*(-?\d+(?:\.\d+)?)")
SCORE_B_RE = re.compile(r"\"score_b\"\s*:\s*(-?\d+(?:\.\d+)?)")
WHY_RE = re.compile(r"\"why\"\s*:\s*\"((?:[^\"\\]|\\.)*)")


def parse_scores(resp: dict) -> tuple[float, float, str, dict]:
    text = "".join(b.get("text", "") for b in resp.get("content", [])
                   if isinstance(b, dict) and b.get("type") == "text")
    usage = {k: resp.get("usage", {}).get(k) for k in
             ("input_tokens", "output_tokens", "cache_creation_input_tokens",
              "cache_read_input_tokens")}
    usage["stop_reason"] = resp.get("stop_reason")

    m = None
    for cand in JSON_RE.finditer(text):
        m = cand  # last well-formed candidate wins
    if m:
        obj = json.loads(m.group(0))
        sa, sb = float(obj["score_a"]), float(obj["score_b"])
        why = str(obj.get("why", ""))[:400]
    else:
        # salvage truncated output (hit max_tokens mid-JSON): the scores appear
        # before `why`, so they are usually intact even when the object isn't
        ma, mb = SCORE_A_RE.search(text), SCORE_B_RE.search(text)
        if not (ma and mb):
            raise ValueError(f"no scores in response (stop_reason="
                             f"{usage.get('stop_reason')}): {text[:200]!r}")
        sa, sb = float(ma.group(1)), float(mb.group(1))
        mw = WHY_RE.search(text)
        why = ("[truncated] " + (mw.group(1) if mw else ""))[:400]
        usage["salvaged"] = True
    for v in (sa, sb):
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"score out of range: {v}")
    return sa, sb, why, usage


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #

def band_label(s: float) -> str:
    for mx, lab in ((0.2, "Do Not Travel"), (0.4, "High Risk"), (0.6, "Elevated Risk"),
                    (0.8, "Reduced Risk"), (1.01, "Low Risk")):
        if s < mx:
            return lab
    return "Low Risk"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--api-key", default=os.environ.get("ANTHROPIC_API_KEY", ""))
    ap.add_argument("--baseurl",
                    default="https://token-plan.ap-southeast-1.maas.aliyuncs.com/apps/anthropic")
    ap.add_argument("--endpoint-suffix", default="/v1/messages")
    ap.add_argument("--api", default="anthropic-messages",
                    help="message API dialect (only anthropic-messages is implemented)")
    ap.add_argument("--model", default="qwen3.8-flash")
    ap.add_argument("--anthropic-version", default="2023-06-01")
    ap.add_argument("--auth-style", choices=("api-key", "bearer", "both"), default="both")
    ap.add_argument("--num-pairs", type=int, default=10000)
    ap.add_argument("--differential-weighting-percent", type=parse_range, default="0.1",
                    metavar="V|START-END",
                    help="how much of the rated gap to close per pair; a 'start-end' "
                         "range ramps across the run (default: 0.1 constant)")
    ap.add_argument("--absolute-weighting-percent", type=parse_range, default="0.05",
                    metavar="V|START-END",
                    help="fraction of the way toward the rated score per pair; "
                         "accepts a 'start-end' ramp (default: 0.05 constant)")
    ap.add_argument("--absolute-weighting-shift", type=parse_range, default="0.004",
                    metavar="V|START-END",
                    help="fixed nudge toward the rated score per pair; accepts a "
                         "'start-end' ramp (default: 0.004 constant)")
    ap.add_argument("--reasoning-tokens", type=int, default=3000)
    ap.add_argument("--rating-offset", type=float, default=0.0,
                    help="added to every model rating before the update. Default 0: "
                         "the model's absolute scale is trusted as-is. The 2026-09-15 "
                         "calibration trial measured a ~-0.05 uniform offset (slope "
                         "0.983); if the map's mean drifts down more than desired over "
                         "a long run, a positive offset normalises it back — a simple "
                         "post-hoc adjustment. Clamped so ratings stay in [0,1].")
    ap.add_argument("--max-output-tokens", type=int, default=1024)
    ap.add_argument("--temperature", type=float, default=1.0,
                    help="only used when --reasoning-tokens 0")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--focus", nargs="*", default=None,
                    help="restrict one side of every pair to these ISO3 codes (the "
                         "partner is drawn from all eligible countries) — for "
                         "re-rating specific records after a prompt change. Note the "
                         "partner's score also updates, as usual.")
    ap.add_argument("--retries", type=int, default=4)
    ap.add_argument("--backoff", type=float, default=1.5)
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--countries-file", default=str(COUNTRIES))
    ap.add_argument("--only-countries", nargs="*", default=None,
                    help="country mode: restrict the eligible pool to these ISO3s "
                         "(targeted reruns, e.g. dependent territories + their parents)")
    ap.add_argument("--admin1", action="store_true",
                    help="sub-national mode: pair first-level divisions of one country "
                         "instead of countries")
    ap.add_argument("--country", default=None,
                    help="with --admin1: the ISO3 whose divisions to pair")
    ap.add_argument("--regions-vs-countries", action="store_true",
                    help="mixed calibration mode: each pair = one admin1 region "
                         "(absolute blind bundle incl. its imposed framework) vs one "
                         "blind country; only the region moves")
    ap.add_argument("--regions-parent", nargs="+", default=None,
                    help="with --regions-vs-countries: ISO3s whose units form the "
                         "region pool")
    ap.add_argument("--bundles", default=None,
                    help="with --regions-vs-countries: JSON file {shapeID: "
                         "blindRegion text} authored for the region dossiers")
    ap.add_argument("--admin1-file", default=str(ROOT / "data" / "admin1.json"))
    ap.add_argument("--log", default=None, help="JSONL audit log path")
    ap.add_argument("--save-every", type=int, default=25)
    ap.add_argument("--no-cache", action="store_true",
                    help="omit cache_control (for endpoints that reject it)")
    ap.add_argument("--allow-partial-blind", action="store_true",
                    help="include countries missing some required blind* fields")
    ap.add_argument("--dry-run", action="store_true",
                    help="build prompts and print diagnostics; make no API calls")
    ap.add_argument("--no-write", action="store_true",
                    help="call the API and log, but do not modify countries.json")
    args = ap.parse_args()

    if args.api != "anthropic-messages":
        print(f"error: --api {args.api!r} is not implemented (only anthropic-messages)",
              file=sys.stderr)
        return 2
    if not args.dry_run and not args.api_key:
        print("error: --api-key is required (or set ANTHROPIC_API_KEY)", file=sys.stderr)
        return 2

    countries = json.loads(Path(args.countries_file).read_text(encoding="utf-8"))
    taxonomy = TAXONOMY.read_text(encoding="utf-8")

    # ---- admin1 (sub-national) mode: one country's divisions, in-country pairs ----
    admin1 = None
    parent_iso = None
    store_file = Path(args.countries_file)
    store = countries
    mixed = args.regions_vs_countries
    region_pool: list[str] = []
    if mixed:
        parents = {x.upper() for x in (args.regions_parent or [])}
        if not parents:
            print("error: --regions-vs-countries requires --regions-parent ISO3 [...]",
                  file=sys.stderr)
            return 2
        admin1 = json.loads(Path(args.admin1_file).read_text(encoding="utf-8"))
        store = admin1
        store_file = Path(args.admin1_file)
        if args.bundles:
            for sid, txt in json.loads(Path(args.bundles).read_text(encoding="utf-8")).items():
                if sid in admin1:
                    admin1[sid]["_blindRegion"] = txt
        region_pool = [sid for sid, r in admin1.items()
                       if r.get("iso3") in parents
                       and isinstance(r.get("score"), (int, float))
                       and str(r.get("summary", "")).strip()]
        if not region_pool:
            print(f"error: no admin1 units for parents {sorted(parents)}", file=sys.stderr)
            return 2
        system_text = build_system_prompt(taxonomy) + MIXED_SYSTEM_EXTRA
    elif args.admin1:
        if not args.country:
            print("error: --admin1 requires --country ISO3", file=sys.stderr)
            return 2
        parent_iso = args.country.upper()
        parent = countries.get(parent_iso)
        if parent is None:
            print(f"error: no country record for {parent_iso}", file=sys.stderr)
            return 2
        admin1 = json.loads(Path(args.admin1_file).read_text(encoding="utf-8"))
        store = admin1
        store_file = Path(args.admin1_file)
        system_text = build_admin1_system_prompt(taxonomy, parent, parent_iso, countries)
    else:
        system_text = build_system_prompt(taxonomy)

    def has_field(rec: dict, f: str) -> bool:
        v = rec.get(f)
        if isinstance(v, list):
            return bool(v) and all(str(x).strip() for x in v)
        return bool(str(v or "").strip())

    eligible = []
    partial = []
    if mixed:
        # comparator pool = blind-complete countries (the unit's own parent is
        # excluded per-pair, not here)
        for iso, rec in countries.items():
            if all(has_field(rec, f) for f in REQUIRED_BLIND):
                eligible.append(iso)
        if len(eligible) < 2:
            print("error: comparator country pool is empty", file=sys.stderr)
            return 2
    elif admin1 is not None:
        for sid, rec in admin1.items():
            if (rec.get("iso3") == parent_iso and isinstance(rec.get("score"), (int, float))
                    and str(rec.get("summary", "")).strip()):
                rec["_parent_name"] = parent["name"]
                eligible.append(sid)
        if len(eligible) < 2:
            print(f"error: only {len(eligible)} scored divisions for {parent_iso}.\n"
                  f"Score them first — see research/ADM1_SCORING_PROMPT.md, then\n"
                  f"  python3 tools/apply_admin1_scores.py --in data/admin1_scores/{parent_iso}.jsonl",
                  file=sys.stderr)
            return 2
    else:
        only = {o.upper() for o in args.only_countries} if args.only_countries else None
        for iso, rec in countries.items():
            if only and iso not in only:
                continue
            required_here = [f for f in REQUIRED_BLIND
                             if not (f == "blindOutOfScope"
                                     and not str(rec.get("outOfScopeNotes", "")).strip())]
            if all(has_field(rec, f) for f in required_here):
                eligible.append(iso)
            elif any(has_field(rec, f) for f in BLIND_FIELDS):
                partial.append(iso)
        if not eligible:
            print(f"error: no records have the required blind fields {REQUIRED_BLIND}.\n"
                  f"Populate them first:\n"
                  f"  python3 tools/make_blind_inputs.py            # extract payloads\n"
                  f"  <run the anonymising model — prompt in tools/blind_fields.md>\n"
                  f"  python3 tools/apply_blind_fields.py --in <outputs>\n",
                  file=sys.stderr)
            return 2
        if args.allow_partial_blind:
            eligible += partial
            eligible = sorted(set(eligible))

        if len(eligible) < 2:
            print(f"error: need at least 2 records with the required blind fields "
                  f"{REQUIRED_BLIND}, found {len(eligible)}.\n"
                  f"Populate more records first:\n"
                  f"  python3 tools/make_blind_inputs.py\n"
                  f"  <run the anonymising model — prompt in tools/blind_fields.md>\n"
                  f"  python3 tools/apply_blind_fields.py --in <outputs>\n"
                  f"  python3 tools/apply_blind_fields.py --in <outputs> --report\n",
                  file=sys.stderr)
            return 2

    rng = random.Random(args.seed)
    focus = None
    if args.focus:
        focus = [f.upper() for f in args.focus]
        bad = [f for f in focus if f not in eligible]
        if bad:
            print(f"error: --focus codes not eligible (missing blind fields?): {bad}",
                  file=sys.stderr)
            return 2
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    tag = f"admin1-{parent_iso}-" if args.admin1 else ""
    log_path = Path(args.log) if args.log else \
        ROOT / "data" / f"blind-pairwise-{tag}{ts}.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"system prompt: {len(system_text):,} chars "
          f"(~{len(system_text)//4:,} tokens) — {'NOT cached' if args.no_cache else 'cached'}")
    if mixed:
        nb = sum(1 for sid in region_pool if admin1[sid].get("_blindRegion"))
        print(f"mixed mode (regions vs countries): {len(region_pool)} regions "
              f"({nb} with authored blindRegion bundles) · comparators {len(eligible)} "
              f"countries · recommend --num-pairs {len(region_pool) * 25} for ~50 "
              f"encounters per region")
    elif admin1 is not None:
        print(f"admin1 mode: {parent['name']} ({parent_iso}) national "
              f"{parent['score']:.2f} · {len(eligible)} scored divisions · "
              f"this run gives ~{args.num_pairs*2/len(eligible):.1f} encounters each "
              f"(recommend --num-pairs {5*len(eligible)} for ~10)")
    else:
        print(f"eligible countries: {len(eligible)}"
              + (f" (+{len(partial)} partial)"
                 if partial and not args.allow_partial_blind else ""))
    print(f"pairs: {args.num_pairs} · workers: {args.workers} · model: {args.model} · "
          f"reasoning: {args.reasoning_tokens}")

    def fmt_rng(t: tuple[float, float]) -> str:
        return f"{t[0]:g}" if t[0] == t[1] else f"{t[0]:g}→{t[1]:g}"

    print("weighting (start→end over the run): "
          f"abs% {fmt_rng(args.absolute_weighting_percent)} · "
          f"abs-shift {fmt_rng(args.absolute_weighting_shift)} · "
          f"diff% {fmt_rng(args.differential_weighting_percent)}")
    if any(t[0] != t[1] for t in (args.absolute_weighting_percent,
                                  args.absolute_weighting_shift,
                                  args.differential_weighting_percent)):
        mid = max(1, args.num_pairs // 2)
        print(f"  at pair 1 / {mid} / {args.num_pairs}: "
              + " · ".join(
                  f"{ramp(*t, 1, args.num_pairs):.5f}/"
                  f"{ramp(*t, mid, args.num_pairs):.5f}/"
                  f"{ramp(*t, args.num_pairs, args.num_pairs):.5f}"
                  for t in (args.absolute_weighting_percent,
                            args.absolute_weighting_shift,
                            args.differential_weighting_percent)))
    print(f"log: {log_path}")

    lock = threading.Lock()
    stats = {"done": 0, "errors": 0, "cache_read": 0, "cache_write": 0,
             "in_tok": 0, "out_tok": 0, "moves": 0.0}
    t_start = time.time()

    def save():
        for rec in store.values():
            if isinstance(rec.get("score"), float):
                rec["band"] = band_label(rec["score"])
        # strip runtime helper keys (e.g. _parent_name) before writing
        dump = {k: {kk: vv for kk, vv in r.items() if not kk.startswith("_")}
                for k, r in store.items()}
        tmp = store_file.with_suffix(str(store_file.suffix) + ".tmp")
        tmp.write_text(json.dumps(dump, indent=1, ensure_ascii=False),
                       encoding="utf-8")
        tmp.replace(store_file)

    def one_pair(idx: int) -> None:
        if mixed:
            with lock:
                sid_r = rng.choice(region_pool)
                ur = admin1[sid_r]
                par = ur["iso3"]
                iso_c = rng.choice([c for c in eligible if c != par])
                r0 = float(ur["score"])
                c0 = float(countries[iso_c]["score"])
                flip = rng.random() < 0.5
            user_text = build_mixed_user_prompt(ur, countries[par], countries[iso_c], flip)
            if args.dry_run:
                print(f"\n{'='*78}\nPAIR {idx}: R={ur.get('name')} vs C={countries[iso_c]['name']}\n{'='*78}")
                print(user_text)
                with lock:
                    stats["done"] += 1
                return
            try:
                resp = call_api(args, system_text, user_text)
                s_first, s_second, why, usage = parse_scores(resp)
                ra, rb = (s_second, s_first) if flip else (s_first, s_second)
            except Exception as e:  # noqa: BLE001
                with lock:
                    stats["errors"] += 1
                    stats["done"] += 1
                entry = {"i": idx, "mode": "mixed", "error": str(e), "r": sid_r,
                         "r_name": ur.get("name"), "parent": par, "c": iso_c,
                         "ts": datetime.now(timezone.utc).isoformat()}
                with open(log_path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
                print(f"[{idx}] ERROR {sid_r}/{iso_c}: {e}", file=sys.stderr)
                return
            if args.rating_offset:
                ra = min(1.0, max(0.0, ra + args.rating_offset))
                rb = min(1.0, max(0.0, rb + args.rating_offset))
            p_abs = ramp(*args.absolute_weighting_percent, idx, args.num_pairs)
            s_abs = ramp(*args.absolute_weighting_shift, idx, args.num_pairs)
            p_diff = ramp(*args.differential_weighting_percent, idx, args.num_pairs)
            upd = compute_update_mixed(r0, c0, ra, rb, p_abs, s_abs, p_diff)
            upd["params"] = {"p_abs": p_abs, "s_abs": s_abs, "p_diff": p_diff,
                             "idx": idx, "total": args.num_pairs}
            with lock:
                store[sid_r]["score"] = round(upd["a"]["final"], 6)
                stats["done"] += 1
                stats["moves"] += abs(upd["a"]["final"] - r0)
                for k, src in (("cache_read", "cache_read_input_tokens"),
                               ("cache_write", "cache_creation_input_tokens"),
                               ("in_tok", "input_tokens"), ("out_tok", "output_tokens")):
                    if usage.get(src):
                        stats[k] += usage[src]
                done = stats["done"]
                if not args.no_write and done % args.save_every == 0:
                    save()
            entry = {"i": idx, "mode": "mixed",
                     "ts": datetime.now(timezone.utc).isoformat(),
                     "r": sid_r, "r_name": ur.get("name"), "parent": par,
                     "c": iso_c, "c_name": countries[iso_c]["name"], "flip": flip,
                     "rated_r": round(ra, 4), "rated_c": round(rb, 4), "why": why,
                     "r0": r0, "c0": c0, "r_new": upd["a"]["final"],
                     "steps": upd, "usage": usage}
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
            print(f"[{done}/{args.num_pairs}] {ur.get('name')} {r0:.3f}→"
                  f"{upd['a']['final']:.3f} (rated {ra:.2f} vs {countries[iso_c]['name'][:22]}"
                  f" stored {c0:.2f} rated {rb:.2f}) · {round(stats['moves']/max(1,done),4)}/move",
                  flush=True)
            return
        with lock:
            if focus:
                iso_a = rng.choice(focus)
                iso_b = rng.choice([c for c in eligible if c != iso_a])
            else:
                iso_a, iso_b = rng.sample(eligible, 2)
            a0 = float(store[iso_a]["score"])
            b0 = float(store[iso_b]["score"])
            flip = rng.random() < 0.5  # randomise presentation order (position bias)
        first, second = (iso_b, iso_a) if flip else (iso_a, iso_b)
        user_text = (build_admin1_user_prompt(store[first], store[second])
                     if admin1 is not None
                     else build_user_prompt(store[first], store[second]))
        label_a = store[iso_a].get("name", iso_a)
        label_b = store[iso_b].get("name", iso_b)

        if args.dry_run:
            print(f"\n{'='*78}\nPAIR {idx}: A={store[first].get('name', first)} vs "
                  f"B={store[second].get('name', second)} "
                  f"(stored {store[first]['score']:.4f} / "
                  f"{store[second]['score']:.4f} — hidden from model)\n{'='*78}")
            print(user_text)
            with lock:
                stats["done"] += 1
            return

        try:
            resp = call_api(args, system_text, user_text)
            s_first, s_second, why, usage = parse_scores(resp)
        except Exception as e:  # noqa: BLE001 — keep the run alive
            with lock:
                stats["errors"] += 1
                stats["done"] += 1
            entry = {"i": idx, "error": str(e), "a": iso_a, "b": iso_b,
                     "a_name": store[iso_a].get("name", iso_a),
                     "b_name": store[iso_b].get("name", iso_b),
                     "ts": datetime.now(timezone.utc).isoformat()}
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
            print(f"[{idx}] ERROR {iso_a}/{iso_b}: {e}", file=sys.stderr)
            return

        # map back from presentation order
        ra, rb = (s_second, s_first) if flip else (s_first, s_second)
        if args.rating_offset:
            ra = min(1.0, max(0.0, ra + args.rating_offset))
            rb = min(1.0, max(0.0, rb + args.rating_offset))
        # ramp the weighting parameters across the run: coarse early, fine late
        p_abs = ramp(*args.absolute_weighting_percent, idx, args.num_pairs)
        s_abs = ramp(*args.absolute_weighting_shift, idx, args.num_pairs)
        p_diff = ramp(*args.differential_weighting_percent, idx, args.num_pairs)
        upd = compute_update(a0, b0, ra, rb, p_abs, s_abs, p_diff)
        upd["params"] = {"p_abs": p_abs, "s_abs": s_abs, "p_diff": p_diff,
                         "idx": idx, "total": args.num_pairs}
        with lock:
            store[iso_a]["score"] = round(upd["a"]["final"], 6)
            store[iso_b]["score"] = round(upd["b"]["final"], 6)
            stats["done"] += 1
            stats["moves"] += abs(upd["a"]["final"] - a0) + abs(upd["b"]["final"] - b0)
            for k, src in (("cache_read", "cache_read_input_tokens"),
                           ("cache_write", "cache_creation_input_tokens"),
                           ("in_tok", "input_tokens"), ("out_tok", "output_tokens")):
                if usage.get(src):
                    stats[k] += usage[src]
            done = stats["done"]
            if not args.no_write and done % args.save_every == 0:
                save()

        entry = {
            "i": idx, "ts": datetime.now(timezone.utc).isoformat(),
            "a": iso_a, "b": iso_b, "flip": flip,
            "a_name": label_a, "b_name": label_b,
            **({"parent": parent_iso} if admin1 is not None else {}),
            "rated_a": ra, "rated_b": rb, "why": why,
            "a0": a0, "b0": b0,
            "a_new": upd["a"]["final"], "b_new": upd["b"]["final"],
            "steps": upd, "usage": usage,
        }
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        el = time.time() - t_start
        print(f"[{done}/{args.num_pairs}] {label_a} {a0:.4f}→{upd['a']['final']:.4f} "
              f"(rated {ra:.2f}) | {label_b} {b0:.4f}→{upd['b']['final']:.4f} "
              f"(rated {rb:.2f}) · {el/done:.1f}s/pair"
              + (f" · cache-hit {usage.get('cache_read_input_tokens')}"
                 if usage.get("cache_read_input_tokens") else ""))

    try:
        if args.workers <= 1:
            for i in range(1, args.num_pairs + 1):
                one_pair(i)
        else:
            with ThreadPoolExecutor(max_workers=args.workers) as ex:
                futs = [ex.submit(one_pair, i) for i in range(1, args.num_pairs + 1)]
                for f in as_completed(futs):
                    f.result()
    except KeyboardInterrupt:
        print("\ninterrupted — saving progress", file=sys.stderr)

    if not args.dry_run and not args.no_write:
        save()
        print("\nre-run tools/build_data.py to refresh ranks and meta.json")

    el = time.time() - t_start
    print(f"\ndone: {stats['done']} pairs in {el:.0f}s · errors: {stats['errors']} · "
          f"total score movement: {stats['moves']:.3f}")
    if stats["cache_read"] or stats["cache_write"]:
        print(f"tokens — cache read: {stats['cache_read']:,} · "
              f"cache write: {stats['cache_write']:,} · "
              f"uncached in: {stats['in_tok']:,} · out: {stats['out_tok']:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
