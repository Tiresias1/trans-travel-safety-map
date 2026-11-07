# ADM1 shadow report — national-baseline + local-difference interface (run and evaluated)

**Status:** shadow-only, non-publishing. No file under `data/` or `tools/` was written, nothing was staged or committed. Published country and division scores remain frozen; they were read only as the frozen baseline input or as a diagnostic comparison that is never a target.

**Method spec:** `research/experiments/country-calibration-audit/terra-method-review.md` §4. **Experiment directory:** `research/experiments/country-calibration-audit/adm1-shadow/` (script, prompts, raw outputs, results ndjson, metadata, summaries, logs — inventory in §11).
**Report date:** 2026-11-07. **Model:** `deepseek/deepseek-v4.1-flash` via OpenRouter chat-completions (`encounter_replay.api_args()` defaults: `reasoning: effort=high`, temperature not sent for reasoning models, `max_output_tokens=8000`, timeout 300 s, 3 transport retries).

---

## 1. Interface under test

Three inputs per call:

1. **FIXED NATIONAL LEVEL, stated explicitly as a frozen input not to be re-rated.** Baseline used per run:
   - California and Texas: **USA 0.330** (user-approved frozen published national score, `data/countries.json` `USA.score`, display "0.330" in the prompt),
   - England: **GBR 0.443529**,
   - Bagmati: **NPL 0.559643**,
   - both controls and both California contrast cells: **USA 0.330** (same national baseline for CA/TX as required, so the two states are a contrast under one baseline).
   The prompt says: "FROZEN INPUT … explicitly NOT a number to be re-rated: do not re-derive it, do not propose a revised national level, and do not output any national score." The ISO code is recorded only in `metadata.json`/this report, never in the prompt (dossiers stay anonymised).
2. **FULL national comparison dossier** — the blind national bundle rendered with everything production `render_parent_bundle` omits or truncates: `blindSummary`, `blindTangential`, `blindLocalsOnly`, **`blindOutOfScope` included**, and **ALL `blindSourceSummaries` uncapped** (USA 12, GBR 9, NPL 7 items; production caps at 8 and omits out-of-scope). The prompt frames these as inherited national exposure that must not be re-counted locally.
3. **Separate LOCAL evidence bundle** — the division's own blind bundle (`blindSummary`, `blindTangential`, `blindLocalsOnly`, `blindOutOfScope`, all local source summaries; CA 4, TX 5, ENG 5 items). Bagmati has **no blind bundle at all**, so its raw division record (production mixed-lane fallback) was used, explicitly marked "no anonymised blind bundle exists … identity is not stripped".

**Task asked of the model:** assess only the **signed local difference** (`local_delta`, higher safer) relative to the national comparison, with every departure carrying `fact`, `local_evidence` (specific bundle item), `direction`, `magnitude`, `visitor_applicability`, `already_in_national_bundle`, `counted_in_delta`, plus `inherited_national_exposure`, `uncertainty`, `notes`. Repetition of a national fact must be `counted_in_delta: false`; a documented region-specific *implementation* may still count.

**Prompt provenance:**
- System prompt: byte-identical production `tools/blind_pairwise.build_system_prompt(outing-risk-taxonomy.md)`, sha256 `700196113130bba3f86f1f07edb7420d51df51c4c3cd361c7eba41de04814c9e` (41,302 chars), diagnostic replay env flags (`STRIP_RULE_10B`, `RESTORE_ARCHIVED_WORDING`, `REVERT_ENDPOINT`) cleared. Rubric version `r2026-11-13`.
- The system prompt's generic `OUTPUT_FORMAT` (`score_a`/`score_b`) necessarily conflicts with a delta schema; the user prompt opens with an explicit override ("the generic two-dossier output format … does NOT apply to this run"). This is a deliberate interface deviation and is item R-9 below. User-prompt hashes (sha256/12): CA `8c9fc4c9b0d8`, TX `89cef4fbe4f9`, ENG `c03f82ea3d36`, BAG `08523b1a2c44`, CTRL_no_local `2350128b5703`, CTRL_dup `96c8dc05ccb8`, CA_orderflip `9bf7e48efb86`, CA_label_ident `d5866f0a2d83` — saved in `prompts/`.

**Shadow candidates computed externally per call (never by the model):**
- additive: `shadow = baseline + local_delta` — logged raw, never silently clamped;
- bounded alternative (defined explicitly): `clamp(baseline + local_delta, 0.02, 0.98)` — a hard bound that keeps the same national starting level (all three baselines lie strictly inside the range) and preserves the departure's sign until a boundary; **every** clamp is logged as a boundary hit.

## 2. Design

16 calls = 8 cells × 2 draws (`results.ndjson`; raw API responses in `raw/`):

| cell | division | baseline | dossier order | label | role |
|---|---|---|---|---|---|
| CA_primary | California | USA 0.330 | national→local | withheld | case |
| TX_primary | Texas | USA 0.330 | national→local | withheld | case (contrast with CA under one baseline) |
| ENG_primary | England | GBR 0.443529 | national→local | withheld | case (devolved architecture) |
| BAG_primary | Bagmati | NPL 0.559643 | national→local | withheld* | case (thin evidence; *identity not strippable) |
| CTRL_no_local | — | USA 0.330 | national→local | withheld | control (i): national bundle only, zero local additions |
| CTRL_dup | — | USA 0.330 | national→local | withheld | control (ii): local bundle = one verbatim national source item |
| CA_orderflip | California | USA 0.330 | **local→national** | withheld | order contrast (only the two dossier blocks swap) |
| CA_label_ident | California | USA 0.330 | national→local | **'California'** | label contrast |

**Retry policy (predeclared before the reported run):** at most one retry per call, only when attempt 1 is empty, truncated or unparseable; the retry gets `max_output_tokens=16000` so a reasoning-budget truncation is not simply repeated; both attempts retained. Origin and rationale are recorded in `metadata.json`; the first run without retries is archived intact as `*_run1.*` (see §10 F-1).

**Expectations (diagnostic, not rules):** control (i) delta near 0; control (ii) the duplicated fact must not count as a new departure; the model must never output a revised national level.

## 3. Headline results (run2, 16/16 parsed)

| cell | deltas (2 draws) | mean | spread | additive raw | bounded | boundary hits |
|---|---|---|---|---|---|---|
| CA_primary | +0.04, +0.05 | **+0.045** | 0.01 | 0.370, 0.380 | 0.370, 0.380 | 0 |
| TX_primary | −0.11, −0.13 (draw 2 via retry) | **−0.120** | 0.02 | 0.220, 0.200 | 0.220, 0.200 | 0 |
| ENG_primary | 0.00, −0.03 | **−0.015** | 0.03 | 0.443529, 0.413529 | same | 0 |
| BAG_primary | +0.03, +0.02 | **+0.025** | 0.01 | 0.589643, 0.579643 | same | 0 |
| CTRL_no_local | 0.00, 0.00 | 0.000 | 0.00 | 0.330, 0.330 | same | 0 |
| CTRL_dup | 0.00, 0.00 | 0.000 | 0.00 | 0.330, 0.330 | same | 0 |
| CA_orderflip | +0.03, +0.03 | +0.030 | 0.00 | 0.360, 0.360 | same | 0 |
| CA_label_ident | +0.10, +0.07 | +0.085 | 0.03 | 0.430, 0.400 | same | 0 |

All 16 additive values lie in [0.20, 0.589643] — far inside [0.02, 0.98], so **bounded = additive everywhere and the clamp never engaged** (0 boundary hits, 0 out-of-[0,1] values). The bounded candidate's behavior at a boundary is defined and logged but *not empirically exercised* — see §10 F-6.

Sign pattern: both states under USA 0.330 move apart as expected from their local dossiers (CA safer, TX riskier) while sharing one baseline; England hovers at/below zero; Bagmati drifts slightly positive on thin evidence.

## 4. Per-case detail

### 4.1 California (baseline USA 0.330) — deltas +0.04, +0.05
- **Evidence-linked justifications:** the counted departure in both draws is the Sept-2022 sanctuary/shield law for transgender youth care that explicitly covers "families who travel to the state/province for it" (draw 1 counted only this, +0.04; draw 2 also counted identity-based prison housing, +0.02, against −0.01 for the 198-incident raw count: 0.04+0.02−0.01 = 0.05). Draw 1 listed 5 departures but counted only 1: the prison policy ("resident-facing … climate signal at most"), the 198 anti-LGBTQ incidents and the city hate-crime rise ("not trans-specific … no per-visitor rate"), and the July-2026 "safest laws" band ("methodology unstated") were all presented and declined.
- **Inherited vs local:** 0 departures flagged `already_in_national_bundle=true` (correct — CA's counted facts are genuinely state-level); inherited lists (6–7 items) name the federal document/visa regime, nationwide bathroom-ban pattern, national custody harms, bounty/counterterrorism framing, and "state/province-level variance already reflected in the fixed national level".
- **Flags:** double-count 0, omission 0 (inherited lists never empty), delta-consistency "consistent" in both draws, guard clean.

### 4.2 Texas (baseline USA 0.330, same national dossier as CA) — deltas −0.11, −0.13
- **Evidence-linked justifications:** draw 1: enforced women's-privacy restroom statute keyed to birth-certificate sex (+ID checks 6 Dec 2025, fines) −0.06; state trans-homicide record 44 killings 2008–2025 ≈7.6/100k −0.02; local visibility rollback (rescinded city ordinance, suspended Pride) −0.02; correctional surgery exclusion −0.01 → −0.11. Draw 2: facilities statute −0.08, active school-district enforcement inquiry −0.02, visibility rollback −0.02, dormant sodomy statute −0.01 → −0.13. Both draws declined to count the statutory-definition act (resident-facing document law, "visitor uses home passport").
- **Inherited vs local:** the statutory-definition act and the no-anti-discrimination gap were marked inherited/not counted in both draws; **the one flip is the top-"Do Not Travel"/44-killings fact** — draw 1 counted it as local (`already_in_national_bundle: false`), draw 2 marked it `true` and uncounted ("the top-tier assessment is already [in the national dossier]"). Bundle check (§10 F-3): the 44-killings/7.6-rate text is **not** in the national bundle; the national bundle has only a generic "four such units flagged" risk-map item that never names this unit — draw 2's inheritance call is likely an **over-inheritance (omission of a genuine local departure)**.
- **Flags:** automated double-count 0, missed-duplication 0, delta-consistency "consistent" in both draws, guard clean ("National level 0.330 is left untouched" — echo of the input, not a re-rating).

### 4.3 England (baseline GBR 0.443529, devolved architecture) — deltas 0.00, −0.03
- **Evidence-linked justifications:** draw 1 declined *every* departure: "The local bundle adds no England-only fact: every item is either explicitly national (Supreme Court ruling, EHRC code, interior-department bulletin) or duplicated from the national dossier" → 0.00, with the explicit caveat "a diagnostic of evidentiary duplication, not proof that England is equal to the national level". Draw 2 counted exactly one departure: the EHRC code of 20 May 2025's operative provisions (birth-certificate demands on "genuine concern", exclusion from single-sex sport) as an England-facing daily implementation → −0.03; the 19 June 2026 prison-housing judgment was marked inherited/not counted ("the same biological-sex logic is already national").
- **Inherited vs local:** inherited lists (6 items each) cover the April-2025 biological-sex ruling family, strip-search policy, prison litigation, NHS ward policy, rainbow-index decline, GRA machinery (resident-facing).
- **Flags:** **no automated flag fired, but manual review finds the EHRC-code judgment flipped between draws** (§10 F-3): draw 1 `already_in_national_bundle: true`, draw 2 `false` + counted. The specific 20 May 2025 code text is *not* in the national bundle, but an Aug-2026 "equality-watchdog guidance on single-sex spaces in force" item is, so both readings are arguable — this is precisely the case-by-case duplication judgment the method review says cannot be mechanical. The flip alone accounts for the cell's 0.03 spread.

### 4.4 Bagmati (baseline NPL 0.559643, thin evidence) — deltas +0.03, +0.02
- **Evidence-linked justifications:** one counted departure in each draw: the Kathmandu-valley meti/third-gender organising hub, "Blue Diamond legacy", available services → modest safer delta with visitor applicability ("an outed traveller in this division has local trans organisations, peer networks and services to turn to"). Draw 2 additionally listed the three recorded source URLs and marked them `already_in_national_bundle: true`, uncounted (they are national-level Nepal items).
- **Inherited vs local:** inherited lists (8 and 6 items) enumerate the national non-criminalisation, resident-facing legal recognition, ground-level harassment, official-hostility climate, costly/scarce care, capital drop-in centre ("national community infrastructure already priced in"), border/passport friction.
- **Flags:** none automated; both draws explicitly caveat the thinness — draw 2: "the hub characterisation is a single descriptive statement without counts, dates or locations, so the positive delta is kept [small]". Residual concern: the positive drift persists across draws from a single qualitative sentence (**thin-evidence drift**, §10 F-5), and this cell is necessarily non-blind.

### 4.5 Controls
- **(i) No-new-local-evidence (national bundle only, zero local additions):** delta **0.00, 0.00**; zero departures in both draws; inherited lists of 8 and 7 items; uncertainty text explicitly states "A zero delta here is a diagnostic of missing evidence, not proof that the division matches the national level" and notes "the shadow score therefore remains 0.330". Diagnostic expectation met without the model inventing local facts (fabrication flag never fired).
- **(ii) Evidence-duplication (local bundle = one verbatim national source item):** delta **0.00, 0.00**. Both draws listed the item but flagged it `already_in_national_bundle: true`, `counted_in_delta: false`, magnitude 0 — draw 2: "textually identical to an item already present in the national dossier … with zero differentiating evidence, the correct delta is zero rather than an inferred positive". **Must-not-count requirement satisfied in 2/2 draws**; double-count flags 0.

## 5. Order and label contrasts (California, 2 draws each)

- **Order effect:** national-first mean +0.045 (0.04, 0.05) vs local-first mean +0.030 (0.03, 0.03) → **−0.015**. Same sign both orders; the difference (0.015) is at/below the ENG within-cell spread (0.03) and only modestly above CA's own (0.01). With n=2 per cell this is not distinguishable from draw noise — a weak order signal at most.
- **Label effect:** identity-withheld mean +0.045 vs identifying ('California') mean **+0.085** (0.10, 0.07) → **+0.040**, larger than either CA within-cell spread. Mechanism visible in the outputs: under the identifying label the model *counted more local protections* — the prison identity-based housing policy was counted (+0.04 in label draw 1; +0.02 in primary draw 2) but declined as climate-only in primary draw 1 — and the name appears inside departure text ("California is a sanctuary state…", "families who travel to California"). Suggestive of identity-conditioned uplift for a known-protective state; n=2, so a signal to investigate, not an effect estimate.

## 6. National re-rating guard

**0 violations across all 33 recorded outputs (run1 16 + run2 16 + 1 retry).** Checked three ways: (1) parsed-JSON key whitelist — every output contained exactly the five agreed keys, `extra_keys` empty in all 16 run2 rows; (2) regex scan of raw text for any "revised/new/actual/corrected national level/score" numerals differing from the fixed baseline, and for `score_a`/`score_b`; (3) an independent post-hoc grep over every raw file in `raw/` and `raw_run1/` — NONE. Inputs echoing the baseline ("National level 0.330 is left untouched", "the shadow score therefore remains 0.330") were correctly not flagged. No absolute division level field was requested or emitted outside the schema.

## 7. Boundary handling

`additive_raw`, `bounded`, `clamped`, `boundary_hit`, `out_of_unit_scale` logged per row in `results.ndjson`. Observed: 0 clamps, 0 boundary hits, 0 out-of-[0,1] raw values; nearest approach to a boundary was 0.20 (TX draw 2) vs the 0.02 floor. Nothing was silently clamped — but the clamp path is untested by observation.

## 8. Diagnostic comparison with published division scores (never a target)

Published scores (`data/admin1.json`, rubric r2026-11-12, rated 2026-10-28) vs shadow additive mean:

| division | shadow additive mean | published | gap (shadow − published) |
|---|---|---|---|
| California | 0.375000 | 0.380584 | −0.005584 |
| Texas | 0.210000 | 0.185559 | +0.024441 |
| England | 0.428529 | 0.485382 | −0.056853 |
| Bagmati | 0.584643 | 0.555559 | +0.029084 |

**Mean gap −0.002228; gap range [−0.056853, +0.029084].** Signs are mixed, so there is no uniform directional bias visible. This spread is an investigation signal only: the published numbers came from different lanes (anchored/mixed, no fixed national level shown, no delta schema, r2026-11-12 rubric), so the gap measures *method* difference by construction, not error in either method. England's −0.057 is the largest and is traceable to the EHRC inheritance flip (§4.3): published England sits +0.0419 above its national level while both shadow draws sit at or below it. Nothing here feeds back into any score.

## 9. What the model judged inherited vs local (summary)

- **Counted as local:** CA sanctuary/shield law (4/4 CA-family draws), CA prison identity-based housing (3/4), CA incident counts (2/4, small), TX facilities statute + enforcement + visibility rollback + sodomy signal (all TX draws), TX homicide/tier record (1/2), ENG EHRC operative code (1/2), BAG organising-hub sentence (2/2).
- **Judged inherited / not re-counted:** the entire federal document/visa/entry regime, nationwide bathroom-ban pattern, national custody harms, bounty/counterterrorism framing (US cells); the April-2025 biological-sex ruling family, strip-search and prison litigation, NHS ward policy (ENG); NPL decriminalisation, resident-facing recognition, national hostility and capital infrastructure (BAG). Every cell produced a non-empty `inherited_national_exposure` list (6–12 items) — **no inherited-exposure omission in the outputs**.
- **Explicitly declined as resident-facing (visitor-applicability working):** statutory-definition/marker bans, prison surgery funding, hate-crime statute gaps, GRA machinery, raw incident counts without denominators.

## 10. Failure modes (reported honestly)

- **F-1 First full run was 13/16 parseable.** Archived as `results_run1.ndjson` + `raw_run1/`: `TX_primary d2` — reasoning consumed the entire 11,000-token completion budget (`reasoning: 11000`, `finish: length`, content empty); `CA_orderflip d1` — reasoning 10,425 + 2,300 chars of content, JSON cut mid-string (`finish: length`); `CTRL_no_local d2` — `finish: stop` but content truncated mid-string with an unescaped `"X"` quote breaking the JSON. The one-retry policy in §2 was fixed *after diagnosing this run and before the reported run*, and is documented as such in `metadata.json`; it is not tuned per cell.
- **F-2 The reported run still needed one retry:** `TX_primary d2` attempt 1 hit the identical reasoning exhaustion (11,000/11,000, empty content); attempt 2 succeeded within the raised 19,000-token cap (11,945 reasoning + 6,997 content). 17 attempts total, 1 retry, 0 unparseable in the final dataset. Both attempts retained (`raw/TX_primary_draw2_attempt1.json`, `…_attempt2.json`).
- **F-3 Inheritance judgments flip between draws — the largest methodological finding.** Same cell, same inputs: England's EHRC-code departure was `already_in_national_bundle: true`/uncounted in draw 1 but `false`/counted (−0.03) in draw 2; Texas's homicide/top-tier departure was counted as local in draw 1 but marked inherited/uncounted in draw 2. Bundle comparison shows TX's fact is genuinely local (national bundle has only an anonymous "four units" item) and ENG's is a genuine borderline (national bundle lacks the 20 May 2025 specifics but carries an Aug-2026 watchdog-guidance item). Both draws of both cells can therefore be criticised in opposite directions; inheritance is **not stable across draws**.
- **F-4 The automated double-count/missed-duplication detector fired 0 times while manual review found two judgment instabilities.** The detector uses verbatim 8-word shingle overlap against the national bundle; paraphrased duplicates pass unseen. Zero automated flags must not be read as "no double counting". (It did correctly stay silent where text genuinely differed.)
- **F-5 Label sensitivity exceeds draw noise:** +0.040 identifying-vs-withheld (§5), with more departures counted under the label. Identity knowledge changed *which facts were counted*, not just magnitudes.
- **F-6 The bounded alternative was never exercised:** no boundary hit in 16 calls, so this run establishes only that the clamp is *defined and logged*, not that boundary behavior is acceptable. Deltas would need to be extreme (e.g. < −0.31 under USA 0.330) to touch it — a design property worth stating: for baselines mid-scale, the clamp mainly guards pathological deltas.
- **F-7 Bagmati's thin evidence still produced a consistent positive delta** (+0.02/+0.03) from one qualitative sentence, explicitly caveated but nonzero; combined with its non-blind fallback bundle, this cell cannot separate thin-evidence drift from label leakage.
- **F-8 Prompt-format tension:** the production system prompt demands `score_a`/`score_b`; the user prompt overrides it. Compliance was 33/33 (0 pairwise outputs), but the override is an interface change that needs user review before any production consideration.
- **F-9 Reasoning burn is highly variable** (360–12,600+ reasoning tokens per call) and dominated completion cost; the delta JSON schema induces far longer reasoning than the production two-float schema, which is why truncation (F-1/F-2) appeared at all.
- **F-10 Sample limits:** 2 draws per cell, purposive four-case selection, one model. Order effect (−0.015) is below cross-cell noise; the label effect (+0.040) exceeds within-cell spread but rests on 4 calls. None of this establishes that any delta, division score, or the interface is *correct* — the review's own verdict (feasibility + failure modes, not validation) stands.
- **F-11 Diagnostic gaps vs published scores are mixed-sign with England the outlier** (§8) — an investigation signal about the EHRC/inheritance judgment, not evidence either number is wrong.

## 11. Artifacts and commands

Artifacts (all under `research/experiments/country-calibration-audit/adm1-shadow/`):
- `adm1_shadow.py` — script (dry-run/smoke/full modes; renderers, guards, candidates, summaries)
- `prompts/system_prompt.txt` + `prompts/user__<cell>.txt` (8 user prompts, hashes in §1)
- `raw/` 17 files (16 calls + 1 retry attempt, full API responses incl. usage/finish_reason), `raw_run1/` 16 files (archived first run)
- `results.ndjson` (16 rows: baseline, guards, candidates, attempts, usage), `results_run1.ndjson` (archived)
- `metadata.json` (design, baselines with sources, retry policy, hashes), `metadata_run1.json`
- `summary.json` (per-cell stats, contrasts, diagnostic spread, totals), `summary_run1.json`
- `run1.log`, `run2.log`

Usage: run1 223,138 prompt + 78,373 completion tokens (US$0.074); run2 238,682 + 93,110 (US$0.093, incl. the retry); total ≈ US$0.17 for 33 attempts.

Commands run (key): `python3 …/adm1_shadow.py --dry-run` (prompt render/hash check — passed twice), `python3 -m py_compile …/adm1_shadow.py` (passed), `python3 …/adm1_shadow.py --smoke` (1 real call — passed: delta 0.04 schema-clean), `python3 …/adm1_shadow.py --workers 3` (run1 — completed with 3 parse failures, archived), same command again (run2 — **16/16 parsed**), `git status --porcelain` / `git diff --cached --name-only` before and after (unchanged: only the 4 pre-existing modified files and the untracked `country-calibration-audit/` dir; **0 staged**; no file in `data/` or `tools/` modified — `find data -newermt "2 hours ago"` empty; `tools/__pycache__` untouched), plus independent guard grep and bundle-overlap probes (§6, §4.3/§4.2).

## 12. Verdict

**Feasibility: yes — with a specific unresolved instability.** The frozen-baseline + local-delta interface ran cleanly end-to-end: controls behaved exactly as diagnostic expectations (0.00 / 0.00, duplication not counted 2/2), the national re-rating guard held in 33/33 outputs, inherited-exposure lists were always populated, deltas stayed evidence-linked and small (|Δ| ≤ 0.13), and additive vs bounded agreed everywhere. The interface's weak point is exactly the one the method review predicted: **whether a local fact is "already national" is case-by-case and draw-unstable** (England, Texas), and the automated detector cannot see paraphrased duplication. A label effect (+0.04) and thin-evidence positive drift (Bagmati) were also observed. No result here changes any published score; the published-vs-shadow spread (mean gap −0.002, range −0.057…+0.029) is diagnostic only.

```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Implemented exactly the §4 shadow interface: full uncapped national dossier incl. blindOutOfScope, frozen baselines stated per run (USA 0.330 CA/TX, GBR 0.443529 ENG, NPL 0.559643 BAG), separate local bundle, signed-delta task with evidence/visitor-applicability/inheritance fields, additive + explicit clamp(0.02,0.98) candidates with raw/bounded/boundary logging, 4 cases + 2 required controls + order and label contrasts, 2 draws each (16 calls). All writes confined to research/experiments/country-calibration-audit/adm1-shadow/ (plus this report at the authoritative path); data/ and tools/ untouched (git status identical before/after, find data -newermt empty), no commits, 0 staged files."
    },
    {
      "id": "criterion-2",
      "status": "satisfied",
      "evidence": "Independent-reviewable evidence: results.ndjson (16 rows with per-call guards, attempts, usage), raw/ (17 full API responses incl. the failed retry attempt 1), raw_run1/ + results_run1.ndjson (archived first run with 3 failures), prompts/ (byte-identical production system prompt sha 70019611…, 8 user prompts), metadata.json (baselines with sources, retry policy, hashes), summary.json (stats, contrasts, diagnostic spread), run1.log/run2.log; report documents per-case deltas, inherited-vs-local judgments, guard checks (0/33 violations, three independent checks), boundary hits (0), order/label contrasts, honest failure modes F-1..F-11."
    }
  ],
  "changedFiles": [
    "research/experiments/country-calibration-audit/adm1-shadow/adm1_shadow.py",
    "research/experiments/country-calibration-audit/adm1-shadow/prompts/system_prompt.txt",
    "research/experiments/country-calibration-audit/adm1-shadow/prompts/user__CA_primary.txt",
    "research/experiments/country-calibration-audit/adm1-shadow/prompts/user__TX_primary.txt",
    "research/experiments/country-calibration-audit/adm1-shadow/prompts/user__ENG_primary.txt",
    "research/experiments/country-calibration-audit/adm1-shadow/prompts/user__BAG_primary.txt",
    "research/experiments/country-calibration-audit/adm1-shadow/prompts/user__CTRL_no_local.txt",
    "research/experiments/country-calibration-audit/adm1-shadow/prompts/user__CTRL_dup.txt",
    "research/experiments/country-calibration-audit/adm1-shadow/prompts/user__CA_orderflip.txt",
    "research/experiments/country-calibration-audit/adm1-shadow/prompts/user__CA_label_ident.txt",
    "research/experiments/country-calibration-audit/adm1-shadow/results.ndjson",
    "research/experiments/country-calibration-audit/adm1-shadow/results_run1.ndjson",
    "research/experiments/country-calibration-audit/adm1-shadow/metadata.json",
    "research/experiments/country-calibration-audit/adm1-shadow/metadata_run1.json",
    "research/experiments/country-calibration-audit/adm1-shadow/summary.json",
    "research/experiments/country-calibration-audit/adm1-shadow/summary_run1.json",
    "research/experiments/country-calibration-audit/adm1-shadow/run1.log",
    "research/experiments/country-calibration-audit/adm1-shadow/run2.log",
    "research/experiments/country-calibration-audit/adm1-shadow/raw/ (17 API response files)",
    "research/experiments/country-calibration-audit/adm1-shadow/raw_run1/ (16 archived API response files)"
  ],
  "testsAddedOrUpdated": [],
  "commandsRun": [
    {
      "command": "python3 research/experiments/country-calibration-audit/adm1-shadow/adm1_shadow.py --dry-run",
      "result": "passed",
      "summary": "Renders and hashes all 8 user prompts + system prompt; no API calls; output-sha stable across two runs; confirmed no ISO identity strings and exact baseline display (0.330/0.443529/0.559643) in prompts"
    },
    {
      "command": "python3 -m py_compile research/experiments/country-calibration-audit/adm1-shadow/adm1_shadow.py",
      "result": "passed",
      "summary": "Script compiles"
    },
    {
      "command": "python3 research/experiments/country-calibration-audit/adm1-shadow/adm1_shadow.py --smoke",
      "result": "passed",
      "summary": "One real OpenRouter call: local_delta 0.04, exact schema keys, no guard flags, US$0.0009"
    },
    {
      "command": "python3 research/experiments/country-calibration-audit/adm1-shadow/adm1_shadow.py --workers 3  (run1)",
      "result": "failed",
      "summary": "16 calls completed, 0 API errors, but 3 unparseable outputs (2 reasoning-budget truncations at 11000/11000 tokens, 1 malformed/truncated JSON); archived as *_run1.* and reported as F-1"
    },
    {
      "command": "python3 research/experiments/country-calibration-audit/adm1-shadow/adm1_shadow.py --workers 3  (run2, predeclared single-retry policy)",
      "result": "passed",
      "summary": "16/16 cells parsed (17 attempts, 1 retry); 0 errors, 0 rerate-guard hits, 0 boundary hits, 0 out-of-scale values; summary.json written"
    },
    {
      "command": "git status --porcelain && git diff --cached --name-only && find data -maxdepth 1 -newermt '2 hours ago'",
      "result": "passed",
      "summary": "No staged files (0), repo state identical before/after (4 pre-existing modified files, 1 untracked dir), no data/ file modified in the run window, tools/__pycache__ untouched"
    },
    {
      "command": "independent guard grep over raw/*.json and raw_run1/*.json (33 outputs) + bundle-overlap probes for England EHRC item and Texas risk-map item",
      "result": "passed",
      "summary": "Guard: NONE (no pairwise-score keys, no revised national level); bundle probes established the F-3 manual findings the shingle detector missed"
    }
  ],
  "validationOutput": [
    "run2 totals: calls=16, errors=0, parse_errors=0, retries_used=1, attempts_total=17, rerate_guard_hits=0, boundary_hits=0, out_of_unit_scale=0",
    "deltas: CA +0.04/+0.05, TX -0.11/-0.13, ENG 0.00/-0.03, BAG +0.03/+0.02, CTRL_no_local 0.00/0.00, CTRL_dup 0.00/0.00, CA_orderflip +0.03/+0.03, CA_label_ident +0.10/+0.07",
    "controls: no-new-evidence delta=0 both draws with zero departures; duplication control delta=0 with duplicated fact flagged already_in_national_bundle=true, counted_in_delta=false in 2/2 draws",
    "contrasts: order effect -0.015 (below cross-cell noise), label effect +0.040 (exceeds within-cell spread)",
    "diagnostic spread vs published (never a target): mean gap -0.002228, range [-0.056853, +0.029084]; CA -0.0056, TX +0.0244, ENG -0.0569, BAG +0.0291",
    "guard: 0 national re-rating violations across 33 outputs via key-whitelist + regex + independent grep"
  ],
  "residualRisks": [
    "Inheritance judgment (already_in_national_bundle) flips between draws on the same cell (England EHRC code, Texas homicide/tier) — double-counting vs omission risk not closed by this run",
    "Automated missed-duplication detector uses verbatim shingles only and missed both manual findings — 0 automated flags is not proof of no double counting",
    "Label effect +0.040 (identity withheld vs 'California') with n=2 per cell — identity-conditioned uplift suspected, not established",
    "Bagmati cell is necessarily non-blind (no blind bundle exists) and shows thin-evidence positive drift +0.02/+0.03",
    "Bounded clamp(0.02,0.98) never exercised — 0 boundary hits; boundary behavior untested empirically",
    "System prompt's production OUTPUT_FORMAT (score_a/score_b) conflicts with the delta schema; user-prompt override complied 33/33 but is an unreviewed interface deviation",
    "Reasoning-budget exhaustion truncated 3 of 33 outputs; retry policy fixed post-run1 and documented, still a recurring cost/failure risk at n larger scale",
    "2 draws per cell, 4 purposive cases, one model — no power, no generalisation; gaps vs published scores mix method differences with error"
  ],
  "noStagedFiles": true,
  "diffSummary": "New shadow-experiment directory only: 1 python script, 9 prompt files, 33 raw API responses (17 run2 + 16 archived run1), 2 results ndjson, 2 metadata, 2 summary, 2 logs; plus this report. No existing repo file modified, nothing staged or committed, data/ and tools/ untouched.",
  "reviewFindings": [
    "no blockers: task scope implemented without widening (shadow dir + report only)",
    "note: report written only to the authoritative runtime path; the task's alternative research/.../adm1-shadow-report.md path was per instruction superseded",
    "note for reviewer: run1 (3/16 unparseable) is retained beside run2 rather than deleted — both attempts/datasets are auditable"
  ],
  "manualNotes": "No code-test suite exists for this research script (testsAddedOrUpdated empty by design); validation is dry-run hash stability + smoke call + full-run parse coverage (16/16) + independent guard grep + git/find write-scope checks, all listed in commandsRun. Total experiment cost ~US$0.17 for 33 attempts. Key qualitative finding to carry forward: the frozen-baseline delta interface is feasible and the controls/guard behave, but per-fact inheritance judgments are draw-unstable (England, Texas) and need a case-by-case duplication review process, not a mechanical rule — exactly the caveat terra-method-review.md §4 flags under 'uncertain / needs decision by the user'."
}
```
