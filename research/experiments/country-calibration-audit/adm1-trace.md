# ADM1 production scoring trace — what was actually supplied for CA/TX/England/Bagmati

Read-only evidence gathering in `/home/meme/kóði/kort` (started from
`research/experiments/country-calibration-audit/HANDOFF.md`). No files modified, no
models called, no scores touched.

## 1. Production path that actually produced the four stored scores

All four division scores come from the **anchored lane** (`tools/anchored_calibrate.py`),
not from the mixed or in-country lanes:

- `data/admin1.json` records all carry `derivedFrom.mode == "anchored"`,
  `anchors: ["BLR","CIV","VAT","ESP"]`, `ratedBy: deepseek/deepseek-v4.1-flash`,
  `rubricVersion: r2026-11-12`:
  - Texas `66186276B29106115751815` score 0.185559; California `66186276B43071933723331`
    score 0.380584; England `14339913B95766344400054` score 0.485382;
    Bagmati `38925275B1624743257395` score 0.555559 (`estimated: true`, `ratedAt: null`).
- Archived lane output `data/measurement_logs/anchored_results.jsonl.gz` (3,241 rows,
  keys only `sid`/`est`/`n`) contains exactly these rows:
  Texas `est 0.185559 n=8`, California `est 0.38058385714285714 n=7`,
  Bagmati `est 0.555559 n=8`, England `est 0.4853817142857143 n=7` — each equals the
  stored score after 6-decimal rounding and the apply-time clamp
  (`anchored_calibrate.py:205-206`, clamp `[0.02, 0.98]`; none of the four is near a clamp).
- `tools/verify_from_logs.py:40` `PRODUCTION_LOGS = ["redo_c4", "anchored_results"]` and
  `data/measurement_manifest.json` (`productionBasis`: "countries from redo_c4 only,
  divisions from anchored_results"; `evidentialLevels.fromArchivedAnchoredEstimate: 2413`)
  declare divisions' production basis as this archive.
- The run matches commit `3d3fb7a2` ("divisions anchored to a fixed 4-anchor ladder
  (3241 divisions, 8 paired estimates each)", 2026-11-03). The archived row shape
  (`{"sid","est","n"}` with no `perAnchor`) matches that commit's writer; HEAD's writer
  (`anchored_calibrate.py:172-175`) would have written `perAnchor` too.

## 2. What the production prompt actually contained (anchored lane)

Prompt assembly at run time (code identical between `770509e6` and `3d3fb7a2`, verified
by `git diff`; HEAD differs only in later additions, see §6):

- **System prompt**: `BP.build_system_prompt(taxonomy)` (`anchored_calibrate.py:87`;
  `blind_pairwise.py:599-636`). This is the fully **blind** prompt: no country name, no
  parent, no numeric score of any kind, only the 0.00–1.00 scale, `RATING_RULES`,
  taxonomy, output format. `ADMIN1_RULES` is **not** included here (it is injected only
  into `build_admin1_system_prompt`, `blind_pairwise.py:534-535`).
- **User prompt** (`anchored_calibrate.py:137-152`): two dossiers, random `flip` each call:
  - Division side: `"### FRAMEWORK IMPOSED BY THE ENCOMPASSING STATE\n{fw}"` where
    `fw = BP.render_parent_bundle(parent)` (`anchored_calibrate.py:131`), then
    `"### THE DIVISION'S OWN CONTENT\n{block(r)}"` (line 142). `block()` (lines 118-121)
    uses `render_region_bundle(r)` when the division has a `blindSummary`, else falls back
    to `summary + "\n\n" + modelContext`.
  - `render_parent_bundle` (`blind_pairwise.py:911-928`) renders **text only**:
    parent `blindSummary`, `[Secondary factors] blindTangential`,
    `[Resident-facing] blindLocalsOnly`, and at most **8** `blindSourceSummaries`
    (`ss[:8]`, line 925). It carries **no country name and no numeric score**, and it
    **omits `blindOutOfScope` entirely** and truncates source evidence beyond 8 items.
  - Anchor side: `BP.dossier(anchor)` (line 140; `blind_pairwise.py:699-736`) — the anchor
    country's full blind dossier (assessment, all source summaries, tangential,
    residents-only, deliberately-not-counted), also without name or score.
- **Numeric level actually supplied to the model: none.** No number from the parent
  country (USA/GBR/NPL) enters the prompt anywhere.
- **Numeric baseline of the result**: `estimate = FROZEN_ANCHOR_SCORES[aid] + (div_r − anc_r)`,
  averaged over calls (`anchored_calibrate.py:159-160`, run-time version
  `float(anchor["score"]) + (div_r − anc_r)` at `3d3fb7a2`). Frozen ladder
  (`anchored_calibrate.py:45-53`): BLR 0.100, CIV 0.297, VAT 0.600, ESP 0.840.
  Corroboration: `git show 770509e6:data/countries.json` and `git show 3d3fb7a2:data/countries.json`
  (the two commits flanking the run) both give BLR 0.099706, CIV 0.2968, VAT 0.600385,
  ESP 0.840345 — matching the frozen constants. HEAD now shows BLR 0.056809,
  CIV 0.280367, ESP 0.869177 (re-aggregation drift, documented in the code comment).
- So the answer to the framing question: **production ADM1 scores neither start from a
  numerical national (parent) rating nor from a pure full-dossier read.** They start from
  **four fixed numeric anchor-country scores** plus **paired differences from full-dossier
  A/B comparisons** in which the parent contributes only partial blinded text. The parent's
  own numeric national score (USA 0.264359 at run time, now 0.330; GBR 0.443529;
  NPL 0.559643) is used **nowhere** in computing these four division scores.

## 3. Per-division: what national text and what numeric national level was supplied

| Division | Parent text supplied (run-time fields, byte-identical to HEAD — verified) | Parent numeric level supplied | Division-side content |
|---|---|---|---|
| California (USA) | USA `blindSummary` (7,831 ch) + `blindTangential` (1,868) + `blindLocalsOnly` (3,160) + **first 8 of 12** `blindSourceSummaries`; `blindOutOfScope` omitted; country unnamed | **none** (anchored prompt); ladder = BLR/CIV/VAT/ESP constants | `render_region_bundle`: `blindSummary` 2,393 + tangential 912 + locals 830 + out-of-scope 874 + 4 source summaries |
| Texas (USA) | same USA bundle | **none** | `blindSummary` 4,456 + tangential 1,341 + locals 4,130 + out-of-scope 971 + 5 source summaries |
| England (GBR) | GBR `blindSummary` (7,142) + tangential (899) + locals (957) + **first 8 of 9** source summaries | **none** | `blindSummary` 2,353 + tangential 913 + locals 1,440 + out-of-scope 843 + 5 source summaries |
| Bagmati (NPL) | NPL `blindSummary` (6,345) + tangential (842) + locals (2,549) + all **7** source summaries | **none** | **fallback path**: Bagmati has **no `blindSummary`, no `modelContext`, no blind fields at all**, `estimated: true` — `block()` rendered only `summary` (319 chars) followed by an empty `modelContext` string (`anchored_calibrate.py:118-121`) |

Verified: for all four divisions and all three parent countries, the rendered text fields
in `data/admin1.json` / `data/countries.json` at HEAD are byte-identical to
`git show 3d3fb7a2:data/admin1.json` and `...:data/countries.json` (string-equality check
per field). So the *variable* part of the anchored prompt is reconstructible exactly from
current data.

`n` values: California n=7, England n=7 → one of the 8 planned calls (4 anchors ×
`--repeats 2`) failed and was silently dropped (`anchored_calibrate.py:154-156`);
Texas and Bagmati n=8. (Repeats=2 is inferred from `n` and the commit message; CLI
arguments were not archived.)

## 4. Superseded lanes that were actually executed for these divisions (for contrast)

These are **not** the production basis (manifest excludes them), but they are real logged
executions, and one of them *did* see a numeric national level:

1. **In-country `--admin1` mode, 2026-09-21..24** (`data/blind-pairwise-admin1-USA-*.jsonl`,
   `-GBR-*.jsonl`; rows keyed `a`/`b` = division sids, `parent`, `rated_a/rated_b`, `why`,
   `steps`, `usage`, `ts`; **no prompt text archived**). California/Texas rows: 21+2 hits in
   `...-USA-20260921-232644.jsonl`; England: 40 rows across the three GBR files.
   - Prompt: `build_admin1_system_prompt` (`blind_pairwise.py:476-545`), introduced by
     commit `34644a75` (2026-09-21 23:12, "parent country unblinded (name+national
     score+full national assessment...)"). It supplies the **parent's name**, the
     **numeric national score** on line 510 (`national score **{parent['score']:.2f}**`,
     band, source count), the **full unblinded** national `summary`/`tangentialFactors`/
     `localsOnly`/`outOfScopeNotes` (lines 488-497), and `ADMIN1_RULES`, whose preamble
     instructs "Rate each division as the national score plus or minus the sub-national
     deviation" (lines 424-431).
   - Numeric level actually shown then: countries.json at those dates —
     `git rev-list --before 2026-09-22` → USA **0.361527** → displayed "0.36";
     GBR at 2026-09-24 → **0.482145** → displayed "0.48".
   - Internal contradiction to note: line 510 shows the national number, then line 514
     says "No existing scores are given in this run".
   - **No NPL/Nepal file exists** in `data/blind-pairwise-admin1-*` — this lane never
     covered Bagmati.
2. **Mixed mode** (`--regions-vs-countries`), waves `redo_admin1` (Oct 10-11),
   `us_states_wave` (Oct 16), `redo_a4` (Oct 28): logged rows for our divisions —
   California 14/17/18, Texas 15/15/14, England 10/0/16, **Bagmati 0 rows anywhere**
   (name+sid scan of every log: Bagmati appears only in `anchored_results`).
   - Prompt: `build_system_prompt + MIXED_SYSTEM_EXTRA` (`blind_pairwise.py:1314`,
     extra at 853-869: "**No existing scores are given anywhere in this run** — not the
     region's, not the encompassing state's, not the comparator's") plus
     `build_mixed_user_prompt` (951-978) with `render_parent_bundle` under
     "### FRAMEWORK IMPOSED BY THE ENCOMPASSING STATE". Since commit `0514057b`
     (2026-09-27, "parent score line removed … kills asymmetric anchoring") this prompt
     contains **no numeric level** — not parent's, not comparator's.
   - Numeric baselines existed only in the update math, not the prompt:
     `compute_update_mixed(r0, c0, …)` (`blind_pairwise.py:873-897`, called at 1511)
     starts the division from its own stored score `r0` and freezes the comparator country
     at its stored `c0`. Example logged rows: California vs FRA (`redo_a4`) `r0 0.509375`,
     `rated_r 0.38`, `rated_c 0.62`, `r_new 0.472291`; England vs AUT
     `r0 0.456875, rated_r 0.40, rated_c 0.75, r_new 0.440908`; Texas vs JAM
     (`us_states_wave`) `r0 0.295097 → r_new 0.306139`.
3. **`tools/in_country_calibrate.py`** (stage 2 sets `division_score = country_score + offset`,
   i.e. a numeric-national anchoring design): source and a `.pyc` exist, but **no output
   artifacts or logs for it were found anywhere in the repo** — no evidence it was run.
4. Nothing in `data/measurement_logs/*` has `mode == "admin1"`; the in-country lane's
   outputs live only in the `data/blind-pairwise-admin1-*` files (Sep), later superseded.

## 5. What code merely intends (design ≠ execution)

- `ADMIN1_RULES` + `build_admin1_system_prompt` (`blind_pairwise.py:424-545`) *intend*
  in-country rating anchored on the named parent's numeric national score. That design was
  executed only in the superseded Sep 21-24 wave; **none of the four production scores came
  from it**.
- HANDOFF's requirement ("ADM1 blind comparisons should start with the full national
  comparison level") is **not** what the production anchored prompt does: the parent enters
  as partial blinded prose (no name, no score, out-of-scope section dropped, sources capped
  at 8), and the numeric start is the foreign anchor ladder, not any national level.
- `MIXED_SYSTEM_EXTRA` and `render_parent_bundle` docstrings ("derive from bundle alone")
  match the mixed design, but mixed ratings were contrast ratings whose numeric baseline was
  each division's own prior score — superseded by the anchored pass anyway.
- Frozen-anchor comment (`anchored_calibrate.py:37-49`) asserts the pass computed with
  0.100/0.297/0.600/0.840; corroborated by flanking commits (§2), though uncommitted
  working-tree state during the run cannot be excluded.

## 6. Limitations and unknowns

- **No prompt/request/response text is archived for any lane.** `anchored_results` rows are
  `sid`/`est`/`n` only — no timestamps, model string, repeats, `flip` orientation,
  per-anchor ratings, or usage. Mixed and admin1 logs store `why`, ratings, `steps`, `usage`
  but not inputs. Inputs are reconstructible only from code + data versions.
- **Exact run-time system prompt is not byte-reproducible from HEAD.** After the run:
  rule 10b added (`3e1ba1db`, Nov 5) then stripped by default (`_strip_rule_10b`);
  endpoint wording changed ("or"→"and" execution; `_revert_endpoint`);
  rule-1/rule-6 wording changed (`_restore_archived_wording`, env-gated, default off —
  `ca403edf` records the relaxation was introduced *after* the wave). HEAD
  `RUBRIC_VERSION = "r2026-11-13"` (`blind_pairwise.py:899`) while records are stamped
  `r2026-11-12`. Reconstruct from `git show 3d3fb7a2:tools/blind_pairwise.py` instead.
- **Stale provenance fields**: CA/TX/England `ratedAt = 2026-10-28` is the last *mixed*
  wave stamp (`_stamp_rater`, `blind_pairwise.py:902-907`); `anchored_calibrate --apply`
  writes only `score/band/ratedBy/derivedFrom` (lines 205-214), so `ratedAt` does **not**
  date the anchored run. Bagmati `ratedAt` is null (it never appeared in any mixed wave).
  Stored `derivedFrom` lacks `anchorVersion`/`anchorScores` that HEAD's apply would write —
  the applied run predates that addition.
- **Date oddity**: `anchored_calibrate.py` docstring says "2026-11-05" but the producing
  commit `3d3fb7a2` is dated 2026-11-03; the archived file's mtime (checkout artifact) says
  Nov 5. Run date within Nov 1-3 window per commits; exact wall-clock call timestamps were
  never logged.
- **Randomness not logged**: `flip` (`anchored_calibrate.py:138`) and repeat count per
  anchor are unrecorded, so per-anchor paired readings cannot be recovered from the archive
  (HEAD's `perAnchor` field would have allowed it; the archived rows predate it).
- Two divisions lost one call each (n=7) with no record of which anchor failed.
- `verify_from_logs.py` was **not run** here (read-only mandate); HANDOFF records its last
  run as `AUDIT: FAIL, exit 1` solely because of the USA 0.330 country-level override —
  that failure says nothing about these four division rows, but division reconciliation was
  not re-executed in this pass.
- No claim is made about whether any of these levels are *correct* — only what was supplied.

## Start Here

Open `tools/anchored_calibrate.py` lines 118-160 (prompt assembly + estimate formula) first,
then `tools/blind_pairwise.py:911-928` (`render_parent_bundle`, the exact national text)
and `data/measurement_logs/anchored_results.jsonl.gz` (the production evidence rows).