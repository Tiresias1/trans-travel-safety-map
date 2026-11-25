# Pipeline invariants — do not regress

These rules encode defects found and fixed in Nov 2026. Every pipeline stage
(research, summary generation, blinding, initial rating, pairwise adjustment,
data sync) must respect them. `tools/test_pipeline_invariants.py` enforces the
machine-checkable ones; the rest are binding process rules.

## 1. Sync by record id, never by name
Scores are written to `data/admin1.json` / `data/countries.json` keyed by the
record's unique id (sid / ISO3). **Never match on display name.** Two divisions
named "Florida" exist (USA and Uruguay); a name-keyed sync pasted US Florida's
rating into Uruguay's Florida. Any sync helper that joins on `name` is a bug.

## 2. Dependencies are ADM1 regions under their parent regime
Territories/dependencies (US, French, British, Danish, Dutch, NZ, Australian,
etc.) are **not independent countries** for rating purposes. They are rated
like other ADM1 regions: parent regime + local differences, with explicit
caveats about which parts of the parent regime actually apply to them.
Their dossiers MUST carry the parent's full operative layer (e.g. US federal
Executive Order / passport / custody block), not a one-line mention. A dossier
parity check (parent-layer keyword counts comparable to a sibling state's
dossier) is required before any dependency pairwise run. The first US-territory
run violated this and inflated territories to ~0.7 against states at ~0.3–0.5.

## 3. Operative parent override for occupied regions
De jure boundaries are kept for display, but rating uses the **operative**
regime. Records may carry `operativeParent` (ISO3) + `operativeParentNote`.
Currently: Crimea, Sevastopol, Donetsk, Luhansk → `RUS`. Any rating stage must
render the `operativeParent`'s national framework, not the de jure parent's.
Occupied-region dossiers must contain real local evidence (occupation
practices), not "scored toward X" stubs.

## 4. Source text carries facts only
`sources[].summary` and `blindSourceSummaries[]` must never mention: the map's
score/rating for any record, why a source was included ("for this record…",
"the claim this record relies on", "baseline behind the score"), or obsolete
score values. External indices' own scores (ILGA, MAP, F&M, Spartacus…) are
fine. Regex sweeps are insufficient — paraphrases require an LLM audit pass
(see `research/source-meta-llm-audit.json` for the audit format).

## 5. Rating discipline (encoded in the v4+ system directive)
- Absence of trans-specific evidence is NOT safety. When the LGB signal is
  severe (capital law, documented executions, armed-group enforcement,
  taboo/stigma, no recourse), it IS the operative signal.
- Legal ambiguity does not create safety; de facto authorities (e.g. armed
  groups controlling territory) count as the operative regime.
- A discovered/outed visitor cannot be assumed invulnerable because they deny
  same-sex conduct.
- Parent-level instruments apply to every division unless affirmative evidence
  shows they do not reach this division; absence of a division-level record
  is NOT evidence of non-application, and 'not inherited' reasoning is
  forbidden (the haiku absence-as-safety case).
- Anchor checks must span the scale (≥1 anchor ≤0.25 and ≥1 ≥0.75).

## 6. Pairwise calibration rules
- One model per pairing; per-region least-used model balancing so no single
  judge dominates a region's comparisons.
- Decaying running-average updates: 0.20 (updates 1–20), 0.08 (21–25),
  0.05 (26+). Never parent-score-plus-delta arithmetic.
- One attempt per cell/pairing; failed draws are gaps, never retried;
  continuations dispatch only never-attempted cells.
- Single-writer guard per run directory; concurrent writers corrupt
  pair-history (happened twice; verify `ps` before relaunch).
- Corrupt seeds are repaired by reseeding from sibling median (or parent
  score for dependencies) + a fresh pairwise pass, not by hand-editing scores.

## 7b. Blinding (2026-11-21 overhaul)
- **Primary blinding is model-based rewriting** (`five-way/blind_rewrite.py`):
  a writer model rewrites each source field into its blind mirror with
  explicit `this division` / `this country` placeholders and NO demonyms
  or institutions. Regex demonym/institution matching is a post-hoc
  failsafe flag only (the leak gate), never the primary transform and
  never a silent fix — residual hits are listed for a model/manual pass.
- **Single-render rule**: `blindSummary` is a blinded rewrite of
  `summary`, not additional evidence. Each fact renders exactly once in
  a dossier. `harness.render_admin1_dossier` is the one rendering for
  records with a `blindSummary` (it neutralizes every blind field it
  renders through the shared `harness.neutralize`, so an unneutralized
  blind field can never reach a prompt); callers must NOT append
  summary-derived local evidence for such records. Records without a
  `blindSummary` get exactly one appended `neutralize(summary)`-only
  block. Never `neutralize(summary + blindSummary)`.
- **Demonym/institution term lists** are canonical in `harness.py`
  (`division_identity_terms` / `country_identity_terms`: programmatic
  derivation from record + parent names plus the manual exception
  tables there — English demonyms are irregular). The leak gate
  (`harness.find_identity_leaks` over rendered dossiers) fails closed
  by listing offenders.

## 7. Non-dossier regions: knowledge-based rating, not mean arithmetic
The old "national mean ± delta" filler is discredited: it produced absurd
extremes (Iran 0.10 − 0.08 → 0.02 "imminent execution" for tourist islands).
Non-dossier regions are rated by `meta/muse-ember` using internal knowledge,
**unblinded** (region identity, parent score, full unblinded parent dossier)
plus the synthetic anchors, because the task is precisely to apply knowledge
of the country. The model must write a brief dossier-style justification of
the local differences from the national baseline (conservatism, rule of law,
urban/rural, tourism, enforcement geography) which becomes the region's
summary. This single-model exception is deliberate and documented; dossier
regions keep the multi-model panel.

## 8. Drift discipline (2026-11-24)

Within-country pairwise runs once drifted as a closed loop: the UK nations
ended ~0.055 above their parent (median ~0.492 vs GBR 0.438) from ~70%
seed legacy plus ~30% closed-loop drift. Pairings were within-ISO3 only,
so each group's fixed point was its own draw mean — structurally
unclosable, with zero cross-scale pairings to pull it back toward the
parent. The UK nations fix pilot repaired that instance (parent-anchored
reseed + format-parity pairwise); the rules below prevent recurrence on a
from-scratch rerun.

- **(a) No closed loops.** Every ADM1 pairwise run MUST include
  parent-anchor pairings: a fixed fraction (`PARENT_ANCHOR_FRACTION > 0`,
  e.g. 0.20 — every 5th pairing) pairs the focal ADM1 against the parent
  country dossier rendered in the identical ADM1 template (parent
  framework + neutralized parent-local evidence;
  `harness.render_parent_anchor_dossier`). The parent anchor is
  partner-only: its state is its current country score and it is NEVER
  updated by these pairings. Default `PARENT_ANCHOR_FRACTION = 0.0`
  preserves legacy behavior for old runs; that default is NOT a licence
  for new runs. The fraction and resulting anchor count are recorded in
  run scope/report/ledger.
- **(b) Seeds must be parent-current with provenance.** Any run that
  starts from shipped scores documents per-record provenance (seed value
  + source field/run + parent score at build time) in its scope
  (`scope.seed_provenance`). ESTIMATED records (no local differentiator)
  are seeded at the CURRENT parent score
  (`--seed-estimated-at-parent`), never at a historical national scale.
- **(c) Drift check before any sync.** Run
  `five-way/check_drift.py` (report-only by default; `--strict` fails)
  over `data/admin1.json` + `data/countries.json`: per ISO3 it reports
  median ADM1 score vs parent score and max |region − parent|, flagging
  groups whose median deviation exceeds 0.03 (configurable). A flagged
  group is not synced until the drift is explained or re-anchored.
- **Slot/model independence.** A/B slot assignment uses a dedicated
  seeded RNG, independent of model assignment (the old A=focal rule
  correlated model with slot).

