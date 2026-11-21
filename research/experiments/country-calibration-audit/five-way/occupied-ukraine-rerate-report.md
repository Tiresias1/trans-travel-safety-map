# Occupied-Ukraine rerate under the Russian parent regime — report (occupied-ukraine-rerate-20261119)

## Logistics

- Script: `occupied_ukraine_rerate.py`; run artifacts: `runs/occupied-ukraine-rerate-20261119/`; aggregate: `analysis/occupied_ukraine_rerate.json`.
- Bug fixed: the four occupied regions are UKR records, so the global run rendered the UKRAINIAN parent framework + a tiny stub. Here each is assessed under the RUSSIAN operative regime plus its local occupation evidence.
- Dossiers: the RUS national-framework block exactly as rendered by `harness.render_admin1_dossier` for RUS admin1 records (verified identical across all 83 RUS dossiers) PLUS the region's own neutralized local evidence (its freshly researched `blindSummary` through `global_adm1_iterative.neutralize`). Partner (B) dossiers are byte-identical to the global run's.
- Seed: 20261119; 32 pairings, exactly 8 per region (focal order = regions x8, seeded shuffle). A = occupied region, B = Russian partner.
- Initial score per region: RUS country score from `data/countries.json` = 0.168481. Partner pool: RUS ADM1 final scores from `analysis/global_adm1_iterative.json` (83 regions), frozen. Candidate partners: nearest 3 by focal's current running score, tie-break region id; no immediate repeat of the same unordered pair when an alternative exists.
- Effort: medium via `provider_models.call_v4`; exactly one model per pairing, per-focal least-used across the seven models (ties by seeded shuffle); attempts per pairing: 1; retries: none; failed draws recorded with no score update. Models (7): mimo, deepseek, qwen, glm, haiku, luna, muse.
- Updates: occupied region ONLY, alpha 0.2 for updates 1-8 (`0.80*old + 0.20*new`); partners never updated.
- Base v4 system sha256: `c5814409d66a4f21e4674fe9377ca4e21d875ff82c3643fbc03870db7d77e3a5`; directive-augmented system sha256: `3f6af3f8f757a108afe5d87362d576cf6cbe7308a9e4d4f97a8f6a29facc5e56` (bounded anti-absence-as-safety directive, pinned).
- Single-writer guard: refuses to launch if another `occupied_ukraine_rerate.py` process is running. Resume-safe: completed iterations are never re-called. Site data not modified.

## Dossier-parity check

- RUS framework block sha256: `21ef8951ce056ecfabf73a5d988cc283f4a811630844d84c69372bc586f99966`; identical across all 83 RUS admin1 dossiers; each occupied dossier embeds exactly this block (framework parity: True).
- Russian operative-regime content present: propaganda law: True; extremism designation: True; 2023 transition ban: True.

| Region | Local words | Occupation evidence | Differentiator | Identity leaks |
|---|---|---|---|---|
| Autonomous Republic of Crimea | 231 | True | True | 0 |
| Sevastopol | 152 | True | True | 0 |
| Donetsk Oblast | 206 | True | True | 0 |
| Luhansk Oblast | 194 | True | True | 0 |

## Final scores (seeded at the RUS country score)

- OK pairings: 30; rejected/failed: 2 (failures recorded, no update).

| Region | Seed (RUS) | Final | Drift | Updates | Previous (UKR-framework) score |
|---|---|---|---|---|---|
| Autonomous Republic of Crimea | 0.168481 | 0.104707 | -0.063774 | 7 | 0.226286 |
| Sevastopol | 0.168481 | 0.092691 | -0.075790 | 8 | 0.191809 |
| Donetsk Oblast | 0.168481 | 0.100325 | -0.068156 | 7 | 0.190846 |
| Luhansk Oblast | 0.168481 | 0.092376 | -0.076105 | 8 | 0.27883 |

## Per-model ratings (A = occupied region)

| Iter | Model | Region | A rating | B partner | B rating |
|---|---|---|---|---|---|
| 1 | muse | Autonomous Republic of Crimea | 0.13 | Mari El | 0.23 |
| 2 | deepseek | Sevastopol | 0.1 | Murmansk Oblast | 0.18 |
| 3 | muse | Sevastopol | 0.08 | Kaliningrad | 0.17 |
| 4 | glm | Sevastopol | 0.04 | Ulyanovsk Oblast | 0.12 |
| 5 | mimo | Donetsk Oblast | rejected | Chukotka Autonomous Okrug | — |
| 6 | glm | Luhansk Oblast | 0.07 | Mari El | 0.17 |
| 7 | muse | Donetsk Oblast | 0.1 | Mari El | 0.19 |
| 8 | haiku | Autonomous Republic of Crimea | 0.08 | Chukotka Autonomous Okrug | 0.12 |
| 9 | haiku | Donetsk Oblast | 0.07 | Kaliningrad | 0.17 |
| 10 | deepseek | Autonomous Republic of Crimea | rejected | Udmurtia | — |
| 11 | muse | Luhansk Oblast | 0.08 | Khanty-Mansiysk Autonomous Okrug – Ugra | 0.19 |
| 12 | deepseek | Luhansk Oblast | 0.05 | Penza Oblast | 0.1 |
| 13 | mimo | Autonomous Republic of Crimea | 0.11 | Leningrad oblast | 0.17 |
| 14 | haiku | Sevastopol | 0.07 | Voronezh Oblast | 0.12 |
| 15 | haiku | Luhansk Oblast | 0.12 | Republic of Karelia | 0.15 |
| 16 | mimo | Sevastopol | 0.1 | Samara Oblast | 0.17 |
| 17 | qwen | Autonomous Republic of Crimea | 0.11 | Penza Oblast | 0.17 |
| 18 | mimo | Luhansk Oblast | 0.13 | Astrakhan Oblast | 0.22 |
| 19 | luna | Donetsk Oblast | 0.08 | Penza Oblast | 0.16 |
| 20 | luna | Autonomous Republic of Crimea | 0.08 | Ryazan Oblast | 0.13 |
| 21 | qwen | Sevastopol | 0.08 | Volgograd Oblast | 0.15 |
| 22 | luna | Sevastopol | 0.07 | Altai Krai | 0.16 |
| 23 | glm | Donetsk Oblast | 0.07 | Bryansk Oblast | 0.17 |
| 24 | qwen | Sevastopol | 0.08 | Jewish Autonomous Oblast | 0.16 |
| 25 | glm | Autonomous Republic of Crimea | 0.08 | Krasnoyarsk Krai | 0.13 |
| 26 | qwen | Autonomous Republic of Crimea | 0.07 | Omsk Oblast | 0.15 |
| 27 | qwen | Donetsk Oblast | 0.08 | Vologda Oblast | 0.18 |
| 28 | qwen | Luhansk Oblast | 0.07 | Krasnoyarsk Krai | 0.17 |
| 29 | luna | Luhansk Oblast | 0.06 | Samara Oblast | 0.11 |
| 30 | deepseek | Donetsk Oblast | 0.07 | Bashkortostan | 0.17 |
| 31 | mimo | Donetsk Oblast | 0.1 | North Ossetia–Alania | 0.15 |
| 32 | qwen | Luhansk Oblast | 0.06 | Moscow Oblast | 0.16 |

## Cost

- Total cost (exact): 0.1493430125 USD.

| Model | OK | Rejected/failed | Cost USD |
|---|---|---|---|
| mimo | 4 | 1 | 0.017072428 |
| deepseek | 3 | 1 | 0.018221746 |
| qwen | 7 | 0 | 0.049755422 |
| glm | 4 | 0 | 0.0146666275 |
| haiku | 4 | 0 | 0.0263544 |
| luna | 4 | 0 | 0.011897505 |
| muse | 4 | 0 | 0.011374884 |

