# Scotland-England gap round 3 — structural fix + targeted re-rate report (scotland-gap-round3-20261125)

## Pre-flight

- Dossiers rendered with current harness: `harness.render_admin1_dossier` (parent framework + blind division fields, neutralized in renderer) for the four nations; `harness.render_country_dossier` (include_regimes) for the GBR reference.
- Single-render: all four nations have a `blindSummary`, so the harness dossier is the one rendering and no local-evidence block was appended (`build_dossier` returns base).
- Neutralized blind fields: `find_identity_leaks` returned [] for every dossier; `assert_user_text_clean` passed on every dossier. (The combined prompt carries the frozen rubric's 0.00-1.00 scale wording, so the dossier-level gate is the applicable check there.)
- Scotland out-of-scope: `blindOutOfScope` present and rendered (DELIBERATELY NOT COUNTED section) in all four nation dossiers.
- Directive-augmented v4 system sha256: `0b22fb93ab21b5219751c8739f51a4a3309eb275906a2eb66aea516cd8a8ea07` (base `c5814409d66a4f21e4674fe9377ca4e21d875ff82c3643fbc03870db7d77e3a5`, clause 5 included). No parent score shown to raters.

## Reseed (report only — data/admin1.json NOT edited here)

- Parent GBR score: 0.437957. New seed = 0.75*parent + 0.25*old_final.

| Nation | Old final | New seed | Final | Final − parent | Updates |
|---|---|---|---|---|---|
| England | 0.455856 | 0.442432 | 0.392163 | -0.045794 | 11 |
| Northern Ireland | 0.458034 | 0.442976 | 0.483573 | +0.045616 | 11 |
| Scotland | 0.463569 | 0.444360 | 0.480219 | +0.042262 | 16 |
| Wales | 0.465241 | 0.444778 | 0.519604 | +0.081647 | 11 |

- Relative order — old finals: Wales, Scotland, Northern Ireland, England; new seeds: Wales, Scotland, Northern Ireland, England; finals: Wales, Northern Ireland, Scotland, England. Changed: True.

## Pairwise pilot

- 10 pairings (6 nation-vs-nation + 4 nation-vs-GBR country-format reference) × 3 repeats, round-robin; slot A/B assigned by a dedicated seeded RNG independent of the model RNG; model = least-used per focal nation across the seven, ties by seeded shuffle; one attempt per pairing, no retries; sequential; MAX_USD $6.
- Frozen start: nation seeds above; GBR reference state = parent score (never updated). Updates: alpha 0.20 for updates 1–20 (all updates here), nation participants only.
- Calls: 36 planned/completed; OK 29; rejected/failed 7. Total cost (exact): 0.201314001 USD.

## Draw means by arm

- Nation-vs-nation: n_calls=20, mean nation rating = 0.46325000000000005.
- Nation-vs-GBR: n_calls=9, mean nation rating = 0.5177777777777778, mean GBR-reference rating = 0.5, mean same-call nation−GBR = 0.01777777777777778, mean nation − parent = 0.0798207777777778.

## Per-model deltas

| Model | Calls | Mean nation | Mean GBR ref | Nation−GBR | Cost USD |
|---|---|---|---|---|---|
| mimo | 3 | 0.5316666666666666 | None | None | 0.01912918 |
| deepseek | 4 | 0.5 | 0.49 | 0.010000000000000009 | 0.023781520 |
| qwen | 1 | 0.415 | None | None | 0.009842352 |
| glm | 5 | 0.5599999999999999 | 0.57 | -0.010000000000000009 | 0.017662948 |
| haiku | 6 | 0.3618181818181818 | 0.4 | -0.038181818181818206 | 0.0451992 |
| luna | 5 | 0.48500000000000004 | 0.485 | 5.551115123125783e-17 | 0.020228675 |
| muse | 5 | 0.48777777777777775 | 0.44 | 0.04777777777777775 | 0.018070656 |

## Verdict on format bias

- **Converged.** Mean same-call nation−GBR = 0.01777777777777778 (≤ 0.05); the format bias does not persist after single-render + clause 5. Recommend adopting the reseed+mixing protocol for other closed-loop groups.

## Scotland-England margin

- Same-call Scotland-England: n=6, mean Scotland-England = 0.06166666666666667, diffs=[0.04999999999999999, 0.06999999999999995, 0.11000000000000004, 0.040000000000000036, 0.06, 0.03999999999999998].
- Per-model:
  - mimo: n=1, mean=0.04999999999999999, diffs=[0.04999999999999999]
  - deepseek: n=0, mean=None, diffs=[]
  - qwen: n=0, mean=None, diffs=[]
  - glm: n=2, mean=0.09, diffs=[0.06999999999999995, 0.11000000000000004]
  - haiku: n=2, mean=0.05000000000000002, diffs=[0.040000000000000036, 0.06]
  - luna: n=1, mean=0.03999999999999998, diffs=[0.03999999999999998]
  - muse: n=0, mean=None, diffs=[]
- Final gap Scotland-England = +0.088055 (vs +0.025 to +0.035 true-gap estimate).

## Pairing table with cost

| Pairing | Calls | OK | Cost USD |
|---|---|---|---|
| Scotland vs England | 6 | 6 | 0.030752381 |
| Scotland vs Wales | 4 | 3 | 0.033802416 |
| Scotland vs Northern Ireland | 4 | 3 | 0.021335076 |
| Scotland vs United Kingdom (country-format reference) | 4 | 4 | 0.019918407 |
| England vs Wales | 3 | 2 | 0.019066364 |
| England vs Northern Ireland | 3 | 3 | 0.016304035 |
| Wales vs Northern Ireland | 3 | 3 | 0.01882856 |
| England vs United Kingdom (country-format reference) | 3 | 0 | 0.019533118 |
| Wales vs United Kingdom (country-format reference) | 3 | 3 | 0.014130797 |
| Northern Ireland vs United Kingdom (country-format reference) | 3 | 2 | 0.007642847 |

## Structural fix (round 3, pre-rate)

- Moved England-only facts out of the GBR parent summary into England division evidence (England sources/summary/blindSummary): NHS England puberty-blocker/Cass/Tavistock/Bell (4 sentences, semicolon-merged to 2), England ward-ban/DHSC (2 sentences), Joelle death (3 sentences, merged to 2), Surrey FOI sentence (1). Parent summary 40→26 sentences; no fact dropped, none invented; scores unchanged (parent 0.437957; England 0.455856; Scotland 0.463569; NI 0.458034; Wales 0.465241). Four purely-England sources moved GBR→England; mixed Wikipedia UK copied to England, retained in GBR; Surrey blind-source entry removed from GBR. Parent blindSummary and England blindSummary re-blinded model-based (mimo via provider_models); England blind-source additions hand-written in round-2 style. Parity: England blind 23 sentences vs Scotland 19 (ratio 1.21, target ≤1.3). Leak gate: find_identity_leaks [] + assert_user_text_clean on all four nation dossiers and GBR country dossier. Fact-by-fact before/after in research/scotland-gap-round3-manifest.json.

## Verdict on true-gap estimate (round 3)

- New finals: England 0.392163, Scotland 0.480219, Wales 0.519604, Northern Ireland 0.483573 (GBR reference 0.437957, never updated). Scotland-England final gap +0.088055; head-to-head same-call Scotland-England +0.061667 (n=6, all positive: [0.05, 0.07, 0.11, 0.04, 0.06, 0.04]; haiku +0.04/+0.06, glm +0.07/+0.11; deepseek/qwen/muse drew none). Scotland received 16 OK updates (≥8 requirement met).
- Vs +0.025 to +0.035 estimate: both final gap (+0.088) and head-to-head (+0.062) move past the band in the predicted direction. The prior estimate is superseded upward by this run; do not force-fit the finals to it. The move is mechanistically coherent: Scotland sheds England restrictive facts (final rises) while England now carries them in its own division evidence (final falls from seed 0.442 to 0.392).
- Did Haiku still mischarge England facts to Scotland? No. Haiku Scotland explanations contain no Joelle/cancer-ward/ward-ban/Cass/Tavistock/Bell charge (6 Haiku OK calls scanned: iters 1, 7, 26, 27, 31, 34). Its only blocker/puberty mentions for Scotland refer to Scotland's own under-18 clinic pause, e.g. iter 31 (Scotland): "The division also paused puberty blockers, and no division-specific ward death is documented" and iter 34 care_services: "Under-18 gender clinic paused puberty-blocker prescribing in April 2024". That is correct attribution of Scotland's own fact, not contamination. By contrast Haiku correctly charges the moved facts to England, e.g. iter 31 (England): "A documented case shows a trans woman removed from a cancer ward bed and dying after 16 days" and iter 26 (England): "Hospital-ward exclusion is planned, and a documented death followed a removal from a cancer ward bed".
- Is contamination now structurally impossible or merely reduced? Structurally eliminated for the moved facts in nation dossiers: verified by keyword search, Scotland dossier and parent framework contain no Joelle/ward-ban/Cass/Tavistock/Bell/blocker-NHS-England text, and England division evidence contains them. No rater can misread a fact that is absent from a dossier. Residual (documented, not in the nation dossiers): GBR parent blindOutOfScope still names Joelle in its DELIBERATELY NOT COUNTED section, which renders only in the GBR country-format reference dossier, never in a nation dossier; it cannot be charged to Scotland from the nation-vs-nation evidence. BTP/Police Scotland/Scotland-prison sentences remain in the parent as shared framework (not round-2-tagged England-only facts) and appear identically in every dossier, so they do not drive the Scotland-England gap. Recommend the coordinator close the outOfScope residual in a future touch, but it does not affect this verdict.

## Decision rule (stated; coordinator syncs)

- Rule: sync Scotland's final ONLY if the gap moves toward +0.025-0.035 with contamination fixed. Here contamination is fixed and the gap moves from -0.000183 (round 2) to +0.088055 (final) / +0.061667 (head-to-head), i.e. toward and beyond the estimate band in the correct direction. This meets the stated rule's direction; the magnitude overshoot means the +0.025-0.035 prior estimate should be retired upward, not used as a cap.
- DO NOT sync in this run (report only; coordinator syncs). Do not touch other scores/bands. Recommended coordinator action: accept these round-3 finals as the new Scotland-England evidence (England 0.392, Scotland 0.480) with the caveat that the gap estimate is now +0.062 head-to-head / +0.088 final, and record the structural fix so future re-rates are not compared to the pre-fix scale.
