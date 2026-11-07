# Pilot 2 — pre-registered country-comparison pilot (non-publishing)

Design: `research/experiments/country-calibration-audit/terra-method-review.md` §3, followed exactly. Model: `deepseek/deepseek-v4.1-flash` (production rater), settings identical to `pilot.py`. **Diagnostics only — no score interpretation, no published value changed, no optional evidence-contrast block run.** Repo writes were confined to `research/experiments/country-calibration-audit/`; no commits; `data/` never touched.

Run window: 2026-11-07 12:18:20 → 12:30:53 UTC. All artifacts are in `research/experiments/country-calibration-audit/`; this report is the findings copy.

## 1. Design conformance

| Block | Composition (24 calls each) | Shuffle |
|---|---|---|
| 1 | 18 matrix cells at draw 1 + 3 isolated draw 1 + 3 copy (A-first, draw 1) | seeded shuffle (seed 20261107+b) |
| 2 | 18 matrix cells at draw 2 + 3 isolated draw 2 + 3 copy (B-first, draw 1) | idem |
| 3 | 18 matrix cells at draw 3 + 3 isolated draw 3 + 3 copy (A-first, draw 2) | idem |
| 4 | 18 matrix cells at draw 4 + 3 isolated draw 4 + 3 copy (B-first, draw 2) | idem |

- **(a) Pair matrix:** USA/GBR/NPL × PRY/FSM + USA–GBR, USA–NPL, NPL–GBR = 9 pairs × 2 orders × 4 draws = **72 calls** ✓. Each block contains one draw of every (pair × order) cell → balanced randomisation.
- **(b) Isolated controls:** single-dossier assessments, 4 draws each for USA/GBR/NPL = **12 calls** ✓.
- **(c) Identical-copy controls:** 2 orientations × 2 draws × 3 targets = **12 calls** ✓. Realisation of "A/B formatting reversed": the two dossier renders are byte-identical for USA/GBR/NPL (the `side` label only affects dependent-territory parent sections), so orientation is a genuine block-order reversal — *A-first* = `## DOSSIER A` block presented first, *B-first* = `## DOSSIER B` block first; content identical in both. This is the only way the two orientations yield distinct prompts and it matches the control's stated purpose ("position/label … instability"). Documented in `pilot2-metadata.json`.
- **Core 96 calls** total (96 logical keys, all attempted) ✓. **Optional evidence-contrast block: NOT RUN** ✓ (ceiling 112 untouched by it).
- **Settings identical to pilot.py:** `BP.build_system_prompt(research/outing-risk-taxonomy.md)` (system sha `700196113130bba3…` — byte-identical to pilot 1's metadata), `BP.dossier` rendering, `BP.call_api(api_args(), …)` → `call_api_openai`: `reasoning: {"effort": "high"}`, `max_tokens` 11000 (3000 reasoning budget + 8000 output), temperature 0.3 configured in `api_args` but not sent with reasoning enabled (call_api_openai default), rubric `r2026-11-13`. **Validation:** all 18 pilot-1 user prompts are byte-identical (same sha256) to the pilot-2 matrix prompts — inputs and prompt pipeline match pilot 1 exactly.
- **Isolated realisation:** same fixed system prompt (pre-registered settings), user prompt = one `## DOSSIER A` block, no comparator; `score_a` is the assessment, any incidental `score_b` recorded but ignored. Because the system prompt is the fixed two-dossier prompt, pair-vs-isolated differs in prompt condition as well as comparator — pre-registered caveat, carried into the analysis.
- **Concurrency:** 4. **Hard caps:** 96 calls / 112 attempts / 2.0M in / 0.8M out, enforced in-script with worst-case reservation before each attempt; the stop machinery never triggered.

### Artifacts (all under `research/experiments/country-calibration-audit/`)

- `pilot2.py` — runner (new file; `pilot.py` unmodified, mtime unchanged).
- `pilot2-results.ndjson` — 100 rows (96 logical calls, 100 attempts), per row: `key`, `pair`, `order`, `draw_index`, `block`, `shuffle_position` (randomisation record), `system_sha256`/`user_sha256`/`prompt_sha256` + `prompt_file`, `model`/`api_dialect`/`endpoint`/`temperature_setting`/`temperature_sent`/`reasoning`/`max_tokens`/`rubric_version`, `timestamp`, full `raw_response` + `raw_content` + `api_model`, `parsed_scores`, `scores`, `why` (rationale), `usage`, `status`, `error`, `attempt`, `retry_of` (failure/retry linkage).
- `pilot2-prompts/` — `system.txt` + 27 unique user prompts (18 matrix + 3 isolated + 6 copy), each row's file hash-verified against its recorded sha.
- `pilot2-metadata.json`, `pilot2.log` (incl. block-1 budget report), `pilot2-run.txt`, `pilot2-analyze.py`, `pilot2-analysis.json`, `pilot2-validate.py`.

## 2. Budget actually consumed

| Checkpoint | Input tokens | Output tokens | Attempts |
|---|---|---|---|
| **Block 1 (first 24 calls)** — logged in `pilot2.log` | **317,466 (15.9% of 2.0M)** | **93,644 (11.7% of 0.8M)** | 24 |
| Block-1 projection to 96 calls | ~1,269,864 | ~374,576 | 96 |
| **Run end** | **1,322,071 (66.1%)** | **391,029 (48.9%)** | 100/112 |

Caps were never approached; no stop condition (budget, ceiling, failure clustering) triggered. Block-1 log line: `[2026-11-07T12:21:09] BLOCK 1 BUDGET REPORT (first 24 calls): consumed 317466 input tokens (15.9% of 2000000) and 93644 output tokens (11.7% of 800000) over 24 attempts; block-1 projection to 96 calls: in~1269864 out~374576`.

## 3. Failures and missingness (reported honestly)

- **5 failed attempts across 4 of 96 logical calls (4.2%)**; **3 recovered on the single allowed retry**; **1 call fully missing**.
- **All five failures have the same mode:** `ValueError: no scores in response (stop_reason=length)` with empty message content — the model spent the entire 11,000-token budget on reasoning and emitted no JSON. No API/transport errors, no rate limits.
- Failed rows (both attempts logged, usage counted):

| row | block | attempt | retry_of | input | output | outcome |
|---|---|---|---|---|---|---|
| `c-GBR-bfirst-d1#a1` | 2 | 1 | — | 13,613 | 11,000 | recovered on retry |
| `m-NPL-GBR-d3#a1` | 3 | 1 | — | 13,507 | 11,000 | recovered on retry |
| `m-GBR-PRY-d4#a1` | 4 | 1 | — | 13,468 | 11,000 | **failed both attempts** |
| `m-GBR-PRY-d4#a2` | 4 | 2 | `m-GBR-PRY-d4#a1` | 13,468 | 11,000 | **missing cell** |
| `m-NPL-FSM-d4#a1` | 4 | 1 | — | 11,621 | 11,000 | recovered on retry |

- **Missing cell:** matrix pair GBR–PRY, order GBR first, draw 4 → that cell has **3/4 draws**; GBR's GBR–PRY pooled n=7 instead of 8. Every other cell is complete (4/4 matrix, 4/4 isolated, 2/2 per copy orientation).
- **Clustering check:** failures touch 3 matrix cells + 1 copy cell, blocks 2–4, mode identical (reasoning-length exhaustion, not condition content). GBR appears in 3 of the 4 failed keys — an observation worth keeping, but there is no condition-level cluster (the isolated condition had zero failures; matrix and copy both affected) and no cell fell below 3 draws, so balanced comparison was not prevented and the pre-registered stop-for-review rule did not fire. Run completed.

## 4. Distributions — per pair, pooled over both orders

n=8 except GBR in GBR–PRY (n=7). sd = sample sd; q1/median/q3 from inclusive quantiles.

| pair | country | n | mean | sd | min | q1 | median | q3 | max |
|---|---|---|---|---|---|---|---|---|---|
| USA,PRY | USA | 8 | 0.276 | 0.065 | 0.20 | 0.24 | 0.25 | 0.32 | 0.38 |
| USA,PRY | PRY | 8 | 0.461 | 0.028 | 0.43 | 0.45 | 0.46 | 0.47 | 0.52 |
| USA,FSM | USA | 8 | 0.214 | 0.097 | 0.12 | 0.14 | 0.20 | 0.24 | 0.42 |
| USA,FSM | FSM | 8 | 0.620 | 0.040 | 0.55 | 0.61 | 0.62 | 0.64 | 0.68 |
| GBR,PRY | GBR | 7 | 0.399 | 0.047 | 0.30 | 0.40 | 0.40 | 0.42 | 0.45 |
| GBR,PRY | PRY | 7 | 0.513 | 0.050 | 0.42 | 0.50 | 0.52 | 0.54 | 0.58 |
| GBR,FSM | GBR | 8 | 0.443 | 0.024 | 0.41 | 0.42 | 0.45 | 0.45 | 0.48 |
| GBR,FSM | FSM | 8 | 0.623 | 0.022 | 0.58 | 0.62 | 0.62 | 0.63 | 0.65 |
| NPL,PRY | NPL | 8 | 0.598 | 0.043 | 0.52 | 0.58 | 0.59 | 0.63 | 0.65 |
| NPL,PRY | PRY | 8 | 0.399 | 0.049 | 0.30 | 0.39 | 0.41 | 0.42 | 0.45 |
| NPL,FSM | NPL | 8 | 0.557 | 0.057 | 0.50 | 0.52 | 0.55 | 0.58 | 0.66 |
| NPL,FSM | FSM | 8 | 0.586 | 0.063 | 0.50 | 0.55 | 0.57 | 0.64 | 0.68 |
| USA,GBR | USA | 8 | 0.255 | 0.079 | 0.15 | 0.21 | 0.26 | 0.28 | 0.40 |
| USA,GBR | GBR | 8 | 0.477 | 0.038 | 0.44 | 0.46 | 0.47 | 0.48 | 0.55 |
| USA,NPL | USA | 8 | 0.235 | 0.031 | 0.18 | 0.22 | 0.23 | 0.25 | 0.28 |
| USA,NPL | NPL | 8 | 0.580 | 0.053 | 0.50 | 0.54 | 0.59 | 0.62 | 0.65 |
| NPL,GBR | NPL | 8 | 0.552 | 0.041 | 0.52 | 0.52 | 0.53 | 0.58 | 0.62 |
| NPL,GBR | GBR | 8 | 0.411 | 0.042 | 0.32 | 0.41 | 0.41 | 0.43 | 0.46 |

## 5. Per-cell distributions (within-cell variation) and order contrasts

Cell = one (pair × presentation order) cell, 4 draws (GBR-first GBR–PRY: 3). sd here is the within-cell sd used as "typical variation".

| pair | order | country | n | mean | sd | values |
|---|---|---|---|---|---|---|
| USA,PRY | USA>PRY | USA | 4 | 0.310 | 0.070 | 0.24, 0.26, 0.36, 0.38 |
| USA,PRY | USA>PRY | PRY | 4 | 0.463 | 0.040 | 0.43, 0.44, 0.46, 0.52 |
| USA,PRY | PRY>USA | USA | 4 | 0.242 | 0.042 | 0.20, 0.23, 0.24, 0.30 |
| USA,PRY | PRY>USA | PRY | 4 | 0.460 | 0.014 | 0.45, 0.45, 0.46, 0.48 |
| USA,FSM | USA>FSM | USA | 4 | 0.235 | 0.132 | 0.13, 0.15, 0.24, 0.42 |
| USA,FSM | USA>FSM | FSM | 4 | 0.605 | 0.037 | 0.55, 0.62, 0.62, 0.63 |
| USA,FSM | FSM>USA | USA | 4 | 0.193 | 0.056 | 0.12, 0.18, 0.22, 0.25 |
| USA,FSM | FSM>USA | FSM | 4 | 0.635 | 0.042 | 0.58, 0.63, 0.65, 0.68 |
| GBR,PRY | GBR>PRY | GBR | 3 | 0.413 | 0.011 | 0.40, 0.42, 0.42 |
| GBR,PRY | GBR>PRY | PRY | 3 | 0.523 | 0.025 | 0.50, 0.52, 0.55 |
| GBR,PRY | PRY>GBR | GBR | 4 | 0.388 | 0.063 | 0.30, 0.40, 0.40, 0.45 |
| GBR,PRY | PRY>GBR | PRY | 4 | 0.505 | 0.066 | 0.42, 0.50, 0.52, 0.58 |
| GBR,FSM | GBR>FSM | GBR | 4 | 0.443 | 0.022 | 0.41, 0.45, 0.45, 0.46 |
| GBR,FSM | GBR>FSM | FSM | 4 | 0.610 | 0.020 | 0.58, 0.62, 0.62, 0.62 |
| GBR,FSM | FSM>GBR | GBR | 4 | 0.443 | 0.029 | 0.42, 0.42, 0.45, 0.48 |
| GBR,FSM | FSM>GBR | FSM | 4 | 0.635 | 0.017 | 0.62, 0.62, 0.65, 0.65 |
| NPL,PRY | NPL>PRY | NPL | 4 | 0.600 | 0.063 | 0.52, 0.58, 0.65, 0.65 |
| NPL,PRY | NPL>PRY | PRY | 4 | 0.393 | 0.065 | 0.30, 0.40, 0.42, 0.45 |
| NPL,PRY | PRY>NPL | NPL | 4 | 0.595 | 0.019 | 0.58, 0.58, 0.60, 0.62 |
| NPL,PRY | PRY>NPL | PRY | 4 | 0.405 | 0.034 | 0.36, 0.40, 0.42, 0.44 |
| NPL,FSM | NPL>FSM | NPL | 4 | 0.565 | 0.044 | 0.50, 0.58, 0.58, 0.60 |
| NPL,FSM | NPL>FSM | FSM | 4 | 0.565 | 0.081 | 0.50, 0.52, 0.56, 0.68 |
| NPL,FSM | FSM>NPL | NPL | 4 | 0.550 | 0.074 | 0.50, 0.52, 0.52, 0.66 |
| NPL,FSM | FSM>NPL | FSM | 4 | 0.608 | 0.039 | 0.57, 0.58, 0.63, 0.65 |
| USA,GBR | USA>GBR | USA | 4 | 0.310 | 0.062 | 0.26, 0.28, 0.30, 0.40 |
| USA,GBR | USA>GBR | GBR | 4 | 0.470 | 0.035 | 0.44, 0.46, 0.46, 0.52 |
| USA,GBR | GBR>USA | USA | 4 | 0.200 | 0.050 | 0.15, 0.17, 0.22, 0.26 |
| USA,GBR | GBR>USA | GBR | 4 | 0.485 | 0.044 | 0.45, 0.47, 0.47, 0.55 |
| USA,NPL | USA>NPL | USA | 4 | 0.242 | 0.029 | 0.22, 0.22, 0.25, 0.28 |
| USA,NPL | USA>NPL | NPL | 4 | 0.600 | 0.044 | 0.55, 0.58, 0.62, 0.65 |
| USA,NPL | NPL>USA | USA | 4 | 0.228 | 0.036 | 0.18, 0.22, 0.25, 0.26 |
| USA,NPL | NPL>USA | NPL | 4 | 0.560 | 0.059 | 0.50, 0.52, 0.60, 0.62 |
| NPL,GBR | NPL>GBR | NPL | 4 | 0.568 | 0.050 | 0.52, 0.53, 0.60, 0.62 |
| NPL,GBR | NPL>GBR | GBR | 4 | 0.410 | 0.064 | 0.32, 0.41, 0.45, 0.46 |
| NPL,GBR | GBR>NPL | NPL | 4 | 0.537 | 0.029 | 0.52, 0.52, 0.53, 0.58 |
| NPL,GBR | GBR>NPL | GBR | 4 | 0.412 | 0.010 | 0.40, 0.41, 0.42, 0.42 |

Within-cell sd across all 36 cells: min 0.0096, median 0.042, max 0.132. Per target (mean of its 8 cells): **USA 0.0596, GBR 0.0347, NPL 0.0477**.

## 6. Order contrasts (mean target rating when first vs second)

Contrast = mean(first, A slot) − mean(second, B slot) for the focus country within a pair. "typ" = mean of the two cells' within-cell sds; **flag** = same-direction contrast (relative to that country's other pairs) whose magnitude exceeds typical within-cell variation — a diagnostic warning, not a calibrated effect estimate.

| pair | country | n first/second | mean first | mean second | contrast | sd first | sd second | typ | flag |
|---|---|---|---|---|---|---|---|---|---|
| USA,PRY | USA | 4/4 | 0.310 | 0.242 | **+0.068** | 0.070 | 0.042 | 0.056 | **YES** |
| USA,FSM | USA | 4/4 | 0.235 | 0.193 | +0.043 | 0.132 | 0.056 | 0.094 | no |
| USA,GBR | USA | 4/4 | 0.310 | 0.200 | **+0.110** | 0.062 | 0.050 | 0.056 | **YES** |
| USA,NPL | USA | 4/4 | 0.242 | 0.228 | +0.015 | 0.029 | 0.036 | 0.032 | no |
| GBR,PRY | GBR | 3/4 | 0.413 | 0.388 | +0.026 | 0.011 | 0.063 | 0.037 | no |
| GBR,FSM | GBR | 4/4 | 0.443 | 0.443 | 0.000 | 0.022 | 0.029 | 0.025 | no |
| USA,GBR | GBR | 4/4 | 0.470 | 0.485 | −0.015 | 0.035 | 0.044 | 0.040 | no |
| NPL,GBR | GBR | 4/4 | 0.410 | 0.412 | −0.003 | 0.064 | 0.010 | 0.037 | no |
| NPL,PRY | NPL | 4/4 | 0.600 | 0.595 | +0.005 | 0.063 | 0.019 | 0.041 | no |
| NPL,FSM | NPL | 4/4 | 0.565 | 0.550 | +0.015 | 0.044 | 0.074 | 0.059 | no |
| USA,NPL | NPL | 4/4 | 0.600 | 0.560 | +0.040 | 0.044 | 0.059 | 0.051 | no |
| NPL,GBR | NPL | 4/4 | 0.568 | 0.537 | +0.030 | 0.050 | 0.029 | 0.039 | no |
| USA,PRY | PRY | 4/4 | 0.463 | 0.460 | +0.003 | 0.040 | 0.014 | 0.027 | no |
| USA,FSM | FSM | 4/4 | 0.605 | 0.635 | −0.030 | 0.037 | 0.042 | 0.040 | no |
| GBR,PRY | PRY | 3/4 | 0.523 | 0.505 | +0.018 | 0.025 | 0.066 | 0.046 | no |
| GBR,FSM | FSM | 4/4 | 0.610 | 0.635 | −0.025 | 0.020 | 0.017 | 0.019 | **YES** (partner) |
| NPL,PRY | PRY | 4/4 | 0.393 | 0.405 | −0.013 | 0.065 | 0.034 | 0.050 | no |
| NPL,FSM | FSM | 4/4 | 0.565 | 0.608 | −0.043 | 0.081 | 0.039 | 0.060 | no |

**Same-direction summary (targets):**
- **USA: first>second in all 4/4 pairs; 2 of 4 exceed typical within-cell variation (USA–GBR +0.110 vs 0.056; USA–PRY +0.068 vs 0.056) → flagged** as a repeated same-direction order contrast larger than typical within-cell variation. USA also has the highest within-cell noise (up to 0.132 in USA–FSM A-first), which qualifies the other two contrasts.
- **NPL: first>second in all 4/4 pairs, but none exceed typical within-cell variation** (largest +0.040 vs 0.051) → direction consistent, magnitude within noise → not flagged.
- **GBR: mixed directions** (+, 0, −, −), none exceed → not flagged.
- Partner countries: FSM rates second>first in all 3 FSM pairs; GBR–FSM exceeds typical (−0.025 vs 0.019) → flagged as a partner-country diagnostic. PRY mixed, none exceed.
- The strict pre-registered warning (same-direction contrast exceeding within-cell variation in ≥3 of a target's 4 pairs) is **not met by any target**; USA meets direction (4/4) with 2/4 exceeding — reported as a partial diagnostic warning.
- Context: pilot 1's single-draw USA–PRY order contrast was 0.22 (0.35 vs 0.13) with order and draw confounded; with 4 draws per order the contrast shrinks to 0.068 — directly supporting the review's finding that order and draw variation were confounded.

## 7. Identical-copy controls (position/label sensitivity)

- **Within-call asymmetry (score_a − score_b when both slots hold the same dossier): exactly 0.00 in all 12 calls.** The model never differentiated identical inputs — no A/B label bias within a call.
- **Orientation (block order) shift of the shared self-assessment:**

| target | A-first values | A-first mean | B-first values | B-first mean | shift (A-first − B-first) |
|---|---|---|---|---|---|
| USA | 0.25, 0.38 (sd 0.092) | 0.315 | 0.42, 0.45 (sd 0.021) | 0.435 | **−0.120** |
| GBR | 0.45, 0.48 (sd 0.021) | 0.465 | 0.45, 0.55 (sd 0.071) | 0.500 | −0.035 |
| NPL | 0.55, 0.58 (sd 0.021) | 0.565 | 0.55, 0.60 (sd 0.035) | 0.575 | −0.010 |

- The whole self-assessment moves with presentation order of the identical copies: strongest for USA (−0.12, and the A-first draws spread 0.13), mild for GBR, negligible for NPL. With n=2 per orientation this flags label/order sensitivity for the USA self-pair as a diagnostic; it is not an accuracy statement, and synthetic copies are not independent evidence (per the pre-registration).

## 8. Isolated vs pair (combined-condition diagnostic)

| target | isolated values | iso mean ± sd | pair pooled mean ± sd (n=16) | iso − pair pooled | per-pair iso − pair (range) |
|---|---|---|---|---|---|
| USA | 0.30, 0.32, 0.33, 0.33 | 0.320 ± 0.014 | 0.245 ± 0.072 | **+0.075** | +0.044 (PRY) … +0.106 (FSM); all 4 positive |
| GBR | 0.45, 0.47, 0.47, 0.50 | 0.473 ± 0.021 | 0.434 ± 0.048 | **+0.039** | −0.005 (USA) … +0.074 (PRY); 3 of 4 positive |
| NPL | 0.58, 0.58, 0.63, 0.66 | 0.613 ± 0.040 | 0.572 ± 0.050 | **+0.041** | +0.015 (PRY) … +0.060 (GBR); all 4 positive |

All three targets rate higher without a comparator than pooled across pairs; per the pre-registration this is a **combined-condition difference** (the isolated prompt differs in condition as well as lacking a comparator), not proof of partner causation. Isolated draws are also the tightest cells for USA (sd 0.014 vs 0.072 pooled), consistent with the comparator adding variation for USA.

## 9. Partner contrasts vs observed within-cell variation

| target | mean vs PRY partners | mean vs FSM partners | contrast | typical within-cell sd | exceeds? |
|---|---|---|---|---|---|
| USA | 0.276 | 0.214 | +0.063 | 0.0596 | yes (marginal) |
| GBR | 0.399 | 0.443 | −0.044 | 0.0347 | yes |
| NPL | 0.598 | 0.558 | +0.040 | 0.0477 | no |

Direct target–target pooled gaps vs within-cell variation: USA–GBR −0.223 (typ 0.047), USA–NPL −0.345 (typ 0.054), NPL–GBR +0.141 (typ 0.041) — all far exceed within-cell variation and hold in both orders.

Per the review's interpretive framework: stable cross-order differences alongside low-to-moderate within-cell variation support pair/partner-context sensitivity; USA's high within-cell variation (0.06–0.13 in two cells) limits that conclusion for USA, while GBR and NPL cells are tighter (median sds 0.011–0.063). This is a sensitivity diagnostic only — nothing here measures absolute accuracy, and no pilot result changes a published score.

## 10. Rationale availability (diagnostics only)

95/95 successful calls carry a non-empty `why`; none truncated; length 163–344 chars (median 271). Rationales are retained verbatim per row for scope/mitigation review by a human reviewer; no rationale-level interpretation is offered here.

## 11. Limitations (as pre-registered)

- Small purposive pilot; PRY/FSM are purposive archived partners, not representative; four draws per cell are a feasibility choice, not a power guarantee.
- Isolated condition runs under the fixed two-dossier system prompt (settings frozen by the pre-registration), so pair-vs-isolated confounds prompt condition with comparator presence.
- Identical-copy orientation is realised as block-order reversal (documented in §1c); n=2 per orientation.
- Labels remain inferable from facts; model/version/settings recorded but the model may drift server-side.
- Failure mode (reasoning-length exhaustion) is a property of the 11,000-token cap shared with pilot 1; one cell lost its 4th draw.
- No threshold was chosen to reproduce any existing US number; no score was validated, changed, or published by this run.