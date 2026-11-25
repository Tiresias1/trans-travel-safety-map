# US-States Adaptive Wave — Tranche 1 Report (2026-11-25)

Scope: Tier 1 (12 highest-churn states) of the 56-region wave. USA federal record not
re-researched and not modified. `data/countries.json` untouched; `data/admin1.json`
untouched (sync is dry-run only; coordinator applies).

## Headline

- **Regions completed: 12 / 56** (Tier 1). Remaining: 44 (Tier 2-4).
- **Changed regions: 2** (Idaho, Kansas). **Zero-change: 10.**
- **New sources verified: 2** (ACLU case pages). **Quarantined: 0.**
- **Rerate pairs run: 0** (cost $0). Cascade S3+ queued, not run (needs model/API access).
- **Spend: $0 / $10 tranche. Exa used: 0 / 150** (no Exa adapter in repo/worker toolset;
  DuckDuckGo and Bing bot/geo-blocked; Brave returned HTTP 429; direct fetches used —
  see "Engine note").

## Primary question: 2026 midterm trans ballot measures / referenda

**No Tier-1 state had a trans-related statewide ballot measure in 2026.** Ballotpedia
`<State>_ballot_measures` pages (fetched for all 12, Nov 3 results) show the full 2026
tables: Idaho (psychedelics, English, abortion Prop 1 — defeated 44%), Kansas
(citizenship voting, Supreme Court elections), Florida (budget, property tax), Tennessee
(bail, property tax), Louisiana (tax, bail, term limits), Arkansas (citizenship voting,
firearms, infrastructure bond), West Virginia (citizenship voting), Montana (judicial
selection, initiative power, campaign finance), Utah (ballot-process amendments),
Alabama (elections, schools, bail). **Texas and South Carolina have no 2026 measures page
(HTTP 404)** — no statewide 2026 measures. This negative result is itself a completed
primary-target check for Tier 1.

## Per-region changes found

### Idaho — CHANGED (baselineContentHash d19c97d5b12aa720)
The October dossier predates/misses the HB 752 litigation posture. Verified new facts
(ACLU of Idaho case page, quote-level confirmed):
- June 16, 2026: federal judge granted preliminary injunction + provisional class-action
  status in *Jackson-Edney v. Labrador*. The restroom portion of HB 752 is blocked
  (trans people may use restrooms consistent with gender identity, except a multi-user
  restroom remains enforceable against when a single-user restroom is available on the
  same floor). The changing-room portion is not blocked.
- July 16, 2026: Idaho filed notice of appeal; the injunction remains in place.
- Penalty escalation omitted from the dossier: second offence is a felony (up to five
  years), not only a first-offence misdemeanour.
New source: `https://www.acluidaho.org/en/cases/jackson-edney-v-labrador` (verified pass).

### Kansas — CHANGED (baselineContentHash 2d6bd7a318a5c84d)
Verified new facts (ACLU of Kansas case page):
- Douglas County district court denied a temporary restraining order on March 10, 2026.
- April 6, 2026: amended petition added four plaintiffs (six total).
- Evidentiary hearing on the SB 244 preliminary-injunction motion was scheduled for
  September 29, 2026; **outcome is the tranche's key known gap** (ACLU pages still show
  "scheduled"; Kansas Reflector blocked by Cloudflare; Brave rate-limited).
New source: `https://www.aclukansas.org/en/cases/doe-v-state-of-kansas` (verified pass).

### Zero-change (10): Florida, Texas, Tennessee, Louisiana, Arkansas, West Virginia,
### Montana, Utah, South Carolina, Alabama
Ballotpedia 2026 tables clean; Wikipedia dated-2026 scans show no new material beyond
what the October dossiers already carry (checked: Tennessee's April 2026 Riley Gaines
Act, Montana's SB 437 + April 15, 2026 affirmance, West Virginia's 4th Circuit 2026
reversal — all already in the dossiers). Considered-and-rejected (not operative for a
visitor, recorded in manifests): Florida's sodomy-law repeal effective Oct 1, 2026;
Texas Children's Hospital settlement (May 2026). Louisiana's Benton incident has no
found fall-2026 follow-up; news sweep queued.

## Sources: added / quarantined / promoted

- **Added (verified, entering sync plan): 2** — the two ACLU case pages above.
- **Fetched-and-used (registry, candidate): 26 total** — 12 Ballotpedia state pages +
  12 Wikipedia state pages (no-change evidence) + 2 ACLU case pages.
- **Quarantined: 0.** Every fetched source resolved (HTTP 200) and matched its claims.
- **Promotion candidates:** per-URL schema yields **0** (each tracker URL is per-state).
  Pattern-level candidates for coordinator review (in `data/source_registry.json`):
  Ballotpedia `<State>_ballot_measures` (fruitful in 12/12) and Wikipedia
  `LGBTQ_rights_in_<State>` (12/12). **No auto-promotion performed.**

## Cascade stages run (with hash evidence)

| Stage | Idaho | Kansas | Zero-change (10) |
|---|---|---|---|
| S1 research / S2 cache+manifest | DONE (2 rounds; `research/fetched/*.txt+.meta`) | DONE | DONE (rounds run, nothing new) |
| S3-S5 re-blind + check_blind | QUEUED — needs model/API access, not run | QUEUED | NOT RUN (zero-change fast path) |
| S6-S7 dossier + consolidate | QUEUED (draft facts in `sync-plan.json`) | QUEUED | NOT RUN |
| S8 pairwise rerate | QUEUED — coordinator approval + API cost | QUEUED | NOT RUN |
| Baselines | d19c97d5b12aa720 | 2d6bd7a318a5c84d | recorded per manifest |

**Rerate doubles: 0 pairs, $0.** No scores changed. No manual score edits.

## Coordinator review queue

1. **Pattern promotions** (above) — decide whether Ballotpedia/Wikipedia state pages
   become `common`.
2. **Apply sync?** `research/us-states-wave/sync.py` is dry-run by default; `--apply`
   adds the 2 sources + 6 summary sentences to Idaho/Kansas only, after re-checking
   baseline hashes. Blind fields then go stale: S3/S4 re-blind must run before any S6+.
3. **Kansas gap:** authorize the round-3 lead (Doe v. State hearing outcome) once search
   capacity returns.
4. **Territories:** PR/GU/VI/MP/AS shapeID confirmation + parent-layer parity check
   still outstanding (Tier 4 precondition from Phase 1).

## Remaining work (44 regions)

Tier 3 (remaining states, alphabetical) — same protocol (Ballotpedia table scan +
Wikipedia dated scan + ACLU tracker). Tier 2 (any certified 2026 trans measures found
in Tier 3 sweeps). Tier 4 territories + DC. Engine note: direct fetches of known
trackers were the reliable path (DDG/Bing blocked, Brave 429, no Exa adapter); news
sweeps remain the weak leg — Budget for Brave retry cooldowns or Exa access in a
later tranche.

## Files

- `research/us-states-wave/manifests/*.manifest.json` (12, idempotent)
- `research/us-states-wave/sync.py` + `sync-plan.json` (dry-run; coordinator applies)
- `research/us-states-wave/search.py`, `fetch.py`, `build_outputs.py`
- `data/source_registry.json` (created; 26 sources, 0 quarantined)
- `research/fetched/<sha16>.{txt,meta}` (36 fetches, same layout as `fetch_all_sources.py`)
- `research/us-states-wave/ledger.json` (spend $0, Exa 0/150)

Validation: `pytest tools/test_pipeline_invariants.py -q` → 11 passed. `data/countries.json`
and `data/admin1.json` unmodified; nothing staged.

---

# Tranche 2 Report (2026-11-25) — appended

Full combined report: `research/us-states-adaptive-wave-report2.md` (the
authoritative whole-wave report). Salient tranche-2 facts:

- **Regions: 44 completed → 56/56 total. Changed in tranche 2: 8** (Arizona,
  California, Colorado, Missouri, Nebraska, Vermont, Virginia, Washington).
  **Zero-change: 36** in tranche 2 (46 across the wave, incl. tranche 1).
- **2026 ballot measures on sex/gender subjects found in 7 states:** Arizona
  Prop 318 (restroom, passed 59%), Colorado Props 134/135 (sports + surgeries,
  passed 52% each), Missouri Amendment 3 (transition procedures for minors,
  defeated 45%), Nebraska Initiative 442 (sports, passed 68%), Vermont
  Proposal 4 (equality amendment, passed 79%), Virginia Question 2 (marriage,
  passed 58%), Washington Initiative 638 (sports, passed 56%; result new,
  dossier had flagged it pending). Tranche-1 Tier-1 had none.
- **California:** July 9, 2026 budget bill includes $26M for gender-affirming
  healthcare protections (single-source Wikipedia; flagged for second source).
- **Cascade fully run for the 10 changed regions** (tranche-1 Idaho/Kansas
  included; their tranche-1 sync was dry-run only and is now applied):
  sync applied → model re-blind (50 calls, $0.015) → renders (0 identity leaks)
  → pairwise rerate (20 attempted / 17 ok, $0.145; 10 scores updated).
  `check_blind` BANNED fires on raw blind fields corpus-wide (pre-existing,
  incl. untouched Alaska); listed, not regex-fixed. Invariants: 11 passed.
  `data/countries.json` untouched.
- **Sources:** 10 added/verified (7 Ballotpedia + 1 Wikipedia + 2 ACLU carried),
  100 registry candidates, 0 quarantined. Promotion candidates (pattern-level,
  coordinator queue): Ballotpedia state ballot-measure pages, Wikipedia state
  LGBTQ-rights pages. **Spend: $0.16. Exa: 0/150** (no adapter; DDG 202,
  Brave 429, Wikipedia 429 late in tranche).
- **Known gaps:** Kansas *Doe v. State* hearing outcome still unposted;
  territories country/admin1 duplication + USVI shapeID confirmation outstanding.

New files: `research/us-states-wave/{fetch2.py,fetch2-results.json,build_outputs2.py,sync2.py,sync-plan2.json,cascade_reblind.py,cascade-rewrites.jsonl,cascade-backup.json,cascade_rerate.py,rerate-results.jsonl,rerate-ledger.json,ledger.json}`, `research/us-states-wave/renders/` (10), `research/us-states-wave/manifests/` (46 total, idempotent), `data/source_registry.json` (updated, 100 sources).
