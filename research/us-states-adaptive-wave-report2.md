# US-States Adaptive Wave — Full Report (Tranches 1–2, 2026-11-25)

Scope: all 56 regions (50 states + DC + 5 territories). USA federal record not
re-researched and not modified. `data/countries.json` untouched across both
tranches. Tranche 1 (12 regions) and tranche 2 (44 regions) are combined here;
the tranche-1 report remains at `research/us-states-adaptive-wave-report.md`.

## Headline (whole wave)

- **Regions completed: 56 / 56.** Remaining: 0.
- **Changed regions: 10** (Arizona, California, Colorado, Idaho, Kansas, Missouri,
  Nebraska, Vermont, Virginia, Washington). **Zero-change: 46.**
- **New sources verified: 10** (8 tranche-2 additions + 2 carried tranche-1 ACLU
  case pages — tranche-1 sync was dry-run only and its facts were applied and
  cascaded in tranche 2). **Quarantined: 0.**
- **Rerate pairs run: 20 attempted, 17 ok**, $0.145. Re-blind cost $0.015.
  **Total wave spend: $0.16.** Exa used: 0 / 150 (no Exa adapter in the worker
  toolset; DuckDuckGo returned HTTP 202 bot-challenge; Brave 429; Wikipedia 429
  late in tranche 2 — direct fetches of known trackers were the reliable path).
- **Validation:** `pytest tools/test_pipeline_invariants.py -q` → 11 passed
  (after sync + cascade). `data/countries.json` unmodified.

## Primary question: 2026 midterm trans / sex-and-gender ballot measures

**Seven states had 2026 statewide ballot measures on sex/gender subjects**
(tranche-1 Tier-1 states had none). Full 2026 tables (Ballotpedia, Nov 3 results)
were scanned for all 56 regions; measures on other subjects (tax, voter ID,
abortion-only, bonds, marijuana, infrastructure) are recorded per-region in the
manifests but are not trans ballot measures.

### Passed restrictions / expansions (Nov 3, 2026)
- **Arizona Proposition 318** (59%): restroom/locker/shower/private-space use
  designated by sex, in schools and athletic associations. NEW fact + source.
- **Colorado Propositions 134 and 135** (52% each): school sports separated by
  biological sex (co-ed excepted); surgeries prohibited for under-18s for
  treatment of a minor's perception of sex/gender. NEW facts + source.
- **Nebraska Initiative Measure 442** (68%): male/female/co-ed school sports
  teams; no male participation on female teams. NEW fact + source.
- **Washington Initiative 638** (56%): school and voluntary nonprofit athletics
  may not let biologically male students compete against females. Dossier already
  flagged this initiative as pending; the **result** is new. NEW fact + source.

### Passed protective measures
- **Vermont Proposal 4** (79%): constitutional bar on denying rights based on
  race, ethnicity, sex, religion, disability, sexual orientation, gender identity,
  gender expression, or national origin. NEW fact + source.
- **Virginia Question 2** (58%): repeals the one-man/one-woman marriage
  definition; bars denying a marriage licence based on sex, gender, or race.
  NEW fact + source.

### Defeated restriction (status quo preserved)
- **Missouri Amendment 3** (45%, defeated): would have banned abortion in most
  cases and gender transition procedures for under-18s. NEW fact + source.

### Negative results
- No 2026 statewide measures at all (Ballotpedia lists no 2026 section): Connecticut,
  Delaware, Illinois, Maine, Mississippi, New Jersey, New York, North Dakota
  (list redirects to historical content), Pennsylvania; DC + territories (page 404).
- 2026 measures on non-sex/gender subjects in all other states (recorded per manifest).
- Nevada's 2026 school-sports initiative failed to reach the ballot (considered,
  no operative change). Indiana's 2026 bathroom-ban bill was introduced only
  (considered, not enacted).

## Other material state changes found (tranche 2)

- **California:** budget appropriations bill passed 9 July 2026 includes $26 million
  for gender-affirming healthcare protections (federal litigation/liability
  damages). NEW fact. Source: Wikipedia `LGBTQ_rights_in_California` (fetched
  HTTP 200; **single-source** — search engines rate-limited so no second
  corroborating fetch; flagged in the review queue).
- **Idaho (update):** Ninth Circuit briefing in *Jackson-Edney v. Labrador* —
  state opening brief 28 Aug 2026, plaintiff-appellee opposition 9 Oct 2026,
  amicus briefs 16 Oct 2026; injunction still in place. Refresh verified.
- **Kansas (re-check):** ACLU case page still shows latest update Mar 6, 2026;
  Sept 29, 2026 preliminary-injunction hearing outcome still not posted.
  Key known gap for the next wave.
- Already-in-dossier (no change): Colorado HB 26-1322, Connecticut Oct-2026
  hate-crime consolidation, Maine Oct-2026 healthcare-data rule, North Carolina
  HB 805 (Jan-2026 two-sexes rule), South Dakota March-2026 birth-certificate
  ruling, Washington's I-638 pending flag (result added, above).

## Cascade (changed regions only: 10)

Zero-change regions (46): no stage downstream of research ran (zero-change fast
path).

| Stage | Status | Evidence |
|---|---|---|
| S2 cache + manifest | DONE (all 56; `research/fetched/<sha16>.{txt,meta}`) | fetch2-results.json, manifests/ |
| Sync (sources + summary facts) | APPLIED via `sync2.py --apply` (dry-run printed first; baseline hashes matched) | sync-plan2.json; only the 10 changed regions touched; scores untouched at sync |
| S3/S4 model re-blind (provider_models) | DONE — 10 regions × 4 field pairs + 1 new-source blind entry each = 50 calls, $0.015; originals in `cascade-backup.json` | cascade-rewrites.jsonl |
| check_blind gate | **BANNED fires on raw blind fields — pre-existing corpus-wide** (untouched Alaska fails too; before/after banned-line counts comparable: AZ 4→4, CA 1→2, CO 2→2, ID 1→3, KS 2→3, MO 3→2, NE 3→3, VT 2→2, VA 2→2, WA 2→1). Residuals LISTED, not regex-fixed (per blind_rewrite precedent); the render-path `neutralize()` is the operative failsafe. | recorded in ledger.json |
| S6 dossier render + leak scan | DONE — 10 renders, `find_identity_leaks` = 0 leaks for all 10 | renders/, rerate-ledger.json |
| S7 consolidate | Facts entered at sync (facts-only, report voice) | data/admin1.json |
| S8 pairwise rerate | 20 pairings attempted (per region: USA parent anchor + nearest-score state; A=focal), 17 ok, 3 rejected (parse failures, one attempt each, no retries), $0.145. Score rule: established schedule alpha=0.20/update, recalibration draws numbered from 1. 10 scores updated (moves ≤0.03). | rerate-results.jsonl, rerate-ledger.json |

Score changes: Arizona 0.4696→0.4397, California 0.4379→0.4330,
Colorado 0.4960→0.4814, Idaho 0.2963→0.2971, Kansas 0.3034→0.2907,
Missouri 0.3668→0.3748, Nebraska 0.3837→0.3708, Vermont 0.5439→0.5433,
Virginia 0.4681→0.4825, Washington 0.4136→0.4183. No manual score edits.

## Sources: verified / quarantined / promotion candidates

- **Added and verified (10):** 7 Ballotpedia state ballot-measure pages
  (Arizona, Colorado, Missouri, Nebraska, Vermont, Virginia, Washington),
  Wikipedia `LGBTQ_rights_in_California`, 2 ACLU case pages (Idaho, Kansas —
  carried from tranche 1, refreshed and re-verified).
- **Fetched-and-used (registry, candidate): 100 source entries total** in
  `data/source_registry.json` (26 tranche-1 + 74 tranche-2; Ballotpedia +
  Wikipedia per-region pages used as 2026-table / dated-scan evidence).
- **Quarantined: 0.** Every fetched source resolved and matched its claims.
- **Promotion candidates (coordinator review queue — NOT auto-promoted):**
  1. Ballotpedia `<State>_ballot_measures` pattern (fruitful across the wave).
  2. Wikipedia `LGBTQ_rights_in_<State>` pattern (fruitful across the wave).
  3. Any per-URL source fruitful in ≥3 regions: none (all per-state URLs).

## Coordinator review queue

1. **Pattern promotions** (above) — decide whether the two tracker patterns
   become `common` in the registry.
2. **California second source:** the $26M budget fact rests on a single
   Wikipedia page (search capacity was rate-limited). Confirm or downgrade.
3. **Kansas gap:** authorize a round-3 search for the *Doe v. State* hearing
   outcome once search capacity returns.
4. **check_blind corpus baseline:** raw blind fields fail `check_blind` BANNED
   corpus-wide (including untouched regions); the render `neutralize()` /
   leak-scan path is clean. Decide whether check_blind should gate on rendered
   text instead, or the corpus blind fields need a repair lane.
5. **Territories:** Puerto Rico / Guam / American Samoa / Northern Mariana
   Islands exist as admin1 records AND as country records (PRI/GUM/ASM/MNP);
   US Virgin Islands has no admin1 record (shapeID confirmation outstanding).
   Method §7 parity check still owed. No country records were modified.
6. **Rerate depth:** 1–2 draws per changed region by design; more draws would
   tighten the 10 updated scores if the coordinator wants them.

## Files

- `research/us-states-wave/manifests/*.manifest.json` (46: 44 tranche-2 +
  Idaho/Kansas carried; idempotent)
- `research/us-states-wave/fetch2.py` + `fetch2-results.json` (fetch evidence)
- `research/us-states-wave/build_outputs2.py` (manifest/registry/sync builder)
- `research/us-states-wave/sync2.py` + `sync-plan2.json` (applied via `--apply`)
- `research/us-states-wave/cascade_reblind.py` + `cascade-rewrites.jsonl` +
  `cascade-backup.json` (original blind fields preserved)
- `research/us-states-wave/cascade_rerate.py` + `rerate-results.jsonl` +
  `rerate-ledger.json` + `renders/` (10 dossiers)
- `research/us-states-wave/ledger.json` (spend $0.16, Exa 0/150)
- `data/source_registry.json` (100 candidates, 0 quarantined)
- `data/admin1.json` (10 changed regions only: sources, summaries, blind fields,
  scores). `data/countries.json` untouched. Nothing staged by this worker.
