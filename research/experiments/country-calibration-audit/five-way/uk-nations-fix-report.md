# UK nations fix pilot — report (uk-nations-fix-20261124)

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
| England | 0.495076 | 0.452237 | 0.449133 | +0.011176 | 9 |
| Northern Ireland | 0.502961 | 0.454208 | 0.447064 | +0.009107 | 9 |
| Scotland | 0.496951 | 0.452706 | 0.505662 | +0.067705 | 8 |
| Wales | 0.476133 | 0.447501 | 0.454966 | +0.017009 | 8 |

- Relative order — old finals: Northern Ireland, Scotland, England, Wales; new seeds: Northern Ireland, Scotland, England, Wales; finals: Scotland, Wales, England, Northern Ireland. Changed: True.

## Pairwise pilot

- 10 pairings (6 nation-vs-nation + 4 nation-vs-GBR country-format reference) × 3 repeats, round-robin; slot A/B assigned by a dedicated seeded RNG independent of the model RNG; model = least-used per focal nation across the seven, ties by seeded shuffle; one attempt per pairing, no retries; sequential; MAX_USD $5.
- Frozen start: nation seeds above; GBR reference state = parent score (never updated). Updates: alpha 0.20 for updates 1–20 (all updates here), nation participants only.
- Calls: 30 planned/completed; OK 22; rejected/failed 8. Total cost (exact): 0.196808690 USD.

## Draw means by arm

- Nation-vs-nation: n_calls=12, mean nation rating = 0.4595833333333333.
- Nation-vs-GBR: n_calls=10, mean nation rating = 0.48, mean GBR-reference rating = 0.48, mean same-call nation−GBR = 2.2204460492503132e-17, mean nation − parent = 0.042043.

## Per-model deltas

| Model | Calls | Mean nation | Mean GBR ref | Nation−GBR | Cost USD |
|---|---|---|---|---|---|
| mimo | 2 | 0.545 | 0.54 | 0.0050000000000000044 | 0.01272166 |
| deepseek | 5 | 0.455 | 0.45499999999999996 | 5.551115123125783e-17 | 0.030127835 |
| qwen | 2 | 0.4575 | None | None | 0.02026189 |
| glm | 1 | 0.5 | None | None | 0.00551487 |
| haiku | 5 | 0.4033333333333333 | 0.42 | -0.016666666666666663 | 0.0395192 |
| luna | 4 | 0.5114285714285715 | 0.48 | 0.03142857142857147 | 0.017852405 |
| muse | 3 | 0.4925 | 0.5 | -0.007500000000000007 | 0.0131591 |

## Verdict on format bias

- **Converged.** Mean same-call nation−GBR = 2.2204460492503132e-17 (≤ 0.05); the format bias does not persist after single-render + clause 5. Recommend adopting the reseed+mixing protocol for other closed-loop groups.

## Pairing table with cost

| Pairing | Calls | OK | Cost USD |
|---|---|---|---|
| England vs Northern Ireland | 3 | 2 | 0.019886004 |
| England vs Scotland | 3 | 3 | 0.019491835 |
| England vs Wales | 3 | 2 | 0.017111628 |
| Northern Ireland vs Scotland | 3 | 1 | 0.018864378 |
| Northern Ireland vs Wales | 3 | 3 | 0.02680303 |
| Scotland vs Wales | 3 | 1 | 0.020572794 |
| England vs United Kingdom (country-format reference) | 3 | 2 | 0.02843936 |
| Northern Ireland vs United Kingdom (country-format reference) | 3 | 3 | 0.015850455 |
| Scotland vs United Kingdom (country-format reference) | 3 | 3 | 0.014706736 |
| Wales vs United Kingdom (country-format reference) | 3 | 2 | 0.01508247 |
