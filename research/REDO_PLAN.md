# FULL REDO PLAN (2026-10-07) — pending user approval

The 2026-10-06/07 full run is voided by systemic bugs found during it and
during user review. Everything from summary regeneration onward reruns once
the system fixes below are verified. NO data fixes in the meantime.

## Systemic bugs found (and their system fixes)

1. Consolidation prompt propagated irrelevant/generic claims and let one
   sub-unit dominate national summaries.
   FIXED: relevance gate, representativeness rule, mechanical pre-filter,
   post-validation (consolidate_record.py; LANE_SPECS r2/r10).
2. Edit-narrative / pipeline jargon shipped in visible text and source claims
   ("earlier profile", "SUPERSEDED by freshness (rev ...)").
   FIXED: fleet purge + scanner over all fields + apply-time last-mile gate.
3. Blind vocabulary leaked into visible text (dependencies read like blind
   dossiers: "administering state").
   FIXED: LANE_SPECS r7.0 + apply-gate + mechanical de-anon in the generation
   retry loop.
4. Greedy regex vocabulary substitution corrupted blind text fleet-wide
   ("state" the verb, "state" the polity, 160 countries self-described as
   sub-units — which also made raters smear parent regimes across pairs).
   FIXED: regex prose surgery BANNED (LANE_SPECS r11); LLM-lane remediation
   (fix_blind_vocab_llm.py) wired into the generation gate; vocabulary rule
   by record kind (LANE_SPECS r12; consolidate prompt r7).
5. Agency proper nouns leaked into blind fields ("Department of Justice",
   "SWS25").
   FIXED: banned in prompts; hard-fail patterns in check_blind.
6. Countries-mode dependencies had no parent section: the rater priced a
   US-regime territory like an independent state (ASM ~0.65 vs USA 0.43),
   read DOJ employment enforcement as "courts protecting trans people", and
   never saw the US regime's full weight. A/B TESTED: with the parent section
   + RATING_RULES 12, ASM direct-pair rating drops 0.631 -> 0.535, and direct
   ASM-vs-Samoa pairs order correctly (ASM ~0.46-0.55 vs Samoa ~0.58-0.66).
   FIXED: DEP_PARENT + parent_section in countries mode (admin1 mixed mode
   already had it).
7. Partial convergence: wave maths under gentle ramps closes only ~40% of the
   gap per ~20 encounters; random sampling gave Scotland 7 encounters.
   FIXED: settlement pass (settle_scores.py) converging every entity to its
   encounter-weighted rater mean (tolerance 0.02, constant 12% weights).
8. USA research gap: the dossier carries NO federal custody/prison regime
   (BOP birth-sex housing, hormone denial in custody), no DOJ trans-hostile
   litigation posture (hospital-record subpoenas for trans youth), thin
   border-detention coverage. This is a RESEARCH requirement, not a point
   fix: it must be sourced and folded into the USA dossier in the redo
   (the parent section then propagates it to all US territories).
   TODO before redo: source harvest (Wikipedia persecution page + primary
   press/BOP/DOJ documents) -> intake queue for USA.
9. Rater under-propagation rule: RATING_RULES 12 added (territories stand
   under the parent's enforced regime; local tolerance does not neutralise it).

## Redo sequence (once user approves)

0. Score baseline: reset scores to pre-tour backup (/tmp/bak_*_pretour.json)
   or keep current — DECISION NEEDED. Scotland 0.65 / ASM best-guess resets
   per user instruction either way.
1. Research wave: USA federal custody/DOJ hostility sources (+ any other
   intake-queue items), gated into sources via the lanes.
2. Claim audit over all countries + dossier regions (tools/audit_claims.py).
3. Summary regeneration over all countries + dossier regions
   (tools/run_full_regen.py — gated pipeline, LLM-lane remediation).
4. Blind-vocabulary verification pass (fix_blind_vocab_llm.py fleet run).
5. Full countries pairwise: diff 0.08->0.01, abs% 0.07->0.006,
   abs-shift 0.004->0.0005 (user: double initial drift, tight finals),
   ~3,500 pairs (1.5x).
6. Full admin1 pairwise (633 dossier regions): same params, ~9,500 pairs.
7. Settlement pass: every entity to its rater mean (tol 0.02).
8. Build, full gates (233 + 3241 + changelog + grammar), deploy.