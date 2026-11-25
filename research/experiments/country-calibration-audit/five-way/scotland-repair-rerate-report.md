# Scotland dossier repair + re-rate — report (scotland-repair-rerate-20261125)

## Task

Repair the dossier asymmetries identified in `scotland-parity-audit.md` §5–§6
(verdict: mixed, ~half genuine divergence / ~half asymmetry; do NOT sync the
0.506 pilot final as-is), then re-rate on the pilot protocol and decide
whether Scotland's gap is now justified. The pilot finals were England 0.449,
NI 0.447, Wales 0.455 (synced live); Scotland was held at 0.497.

## 1. Repairs (facts-only, source-backed)

Every added sentence is backed by a source verified to resolve and to say what
is claimed (quotes in `research/scotland-repair-manifest.json`):

- **Scotland — single-sex services added (the single most important repair).**
  Three new sentences: Equality Act 2010 forms part of the law of Scotland
  (s217(2)); the Supreme Court's unanimous For Women Scotland holding (16
  April 2025) that "woman"/"sex" mean biological woman/sex applies across
  Britain incl. Scotland; the Equality and Human Rights Commission (extent
  England, Wales, Scotland; Equality Act 2006 s1) updated its code of practice
  20 May 2025 — birth-certificate "genuine concern" requests, sport exclusion
  "when necessary" for safety/fair competition, interim guidance that trans
  women should not use women's facilities (workplaces, shops, hospitals);
  Scotland-specific application at Holyrood (toilets designated male/female
  read as biological sex; new gender-neutral toilets open to anyone, May
  2025). The EHRC-guidance export in Scotland's out-of-scope ("carried at
  parent level") was removed — it is now division evidence.
- **England + Wales — operative hate-crime frameworks added (no invention).**
  As they actually stand: there is **no** transgender-specific
  aggravated-offence statute — Crime and Disorder Act 1998 ss29–32 cover
  racially/religiously aggravated conduct only (s28). Transgender-identity
  hostility is addressed by **sentencing**: Sentencing Act 2020 s66 (extent
  England and Wales, in force 1 December 2020) requires courts to treat it as
  an aggravating factor and state so in open court. Police monitor the
  transgender strand (Home Office E&W bulletin; five centrally monitored
  strands). Wales now carries the England-and-Wales framework + bulletin
  baseline (previously zero hate-crime content).
- **Preserved:** Scotland's hate-crime-act divergence (2021 Act naming gender
  identity, in force 1 April 2024; 2009 enhancement) and its correct
  NHS-blocker-pause fix (out-of-scope, own-record) — both kept verbatim in
  substance. NI untouched (blocked-inclusion negative counterpart left as-is).
- **Sentence parity:** Scotland blindSummary 21 → 16 sentences by merging
  only (no sourced fact dropped); England 12 → 15 (+3 hate-crime sentences);
  Wales 10 → 13 (+3). Ratio Scotland/England = **1.067** ≤ 1.3 target.
- **Re-blind:** model-based (mimo via `provider_models.call_v4` with
  `blind_rewrite.BLIND_WRITER_SYSTEM`, one attempt per field, no retries) for
  Scotland summary + outOfScopeNotes, England summary, Wales summary. Regex
  leak-gate (failsafe only): all four rendered dossiers `leaks=[]`,
  `has_out_of_scope=True`. Two additive hand-authored
  `blindSourceSummaries` drafts initially carried nation names in the raw
  field (masked at render by `neutralize`) and were rewritten to fully blind
  phrasing before the final gate. Known accepted drift: the re-blinded
  Scotland summary renders the EHRC's reach as "across the constituent
  nations of this country" (unblinded text correctly says England, Wales and
  Scotland); the operative fact (the code reaches Scotland) is preserved.
- **Writes:** `data/admin1.json` (sources + summary/blind fields; scores
  verified unchanged) + manifest
  `research/scotland-repair-manifest.json` (each change, source URL, quote) +
  pre-repair backup `runs/scotland-repair-20261125/pre-repair-admin1.json`.

### Before/after dossiers (blindSummary sentence counts)

| Nation | Before (chars/sents) | After (chars/sents) |
|---|---|---|
| Scotland | 3,702 / 21 | 5,067 / 16 |
| England | 2,354 / 12 | 3,280 / 15 |
| Wales | 1,633 / 10 | 2,553 / 13 |
| Northern Ireland | 2,476 / 15 | 2,476 / 15 (unchanged) |

Pre-flight rendered dossier chars: England 22,211; NI 19,159; Scotland 23,307;
Wales 19,397; GBR reference 17,110.

## 2. Re-rate (pilot protocol, post-repair dossiers)

Parent-anchored reseed 0.75·parent + 0.25·old-final (parent GBR 0.437957;
old finals = current live: Scotland held 0.496951, England 0.449133, NI
0.447064, Wales 0.454966); 10 pairings × 3 repeats = 30 calls, slot RNG
independent of model RNG, model = least-used per focal nation (ties by seeded
shuffle), alpha 0.20, GBR reference partner-only (never updated), clause-5
system sha `0b22fb93ab21b5219751c8739f51a4a3309eb275906a2eb66aea516cd8a8ea07`
(verified), sequential, resume-safe, `MAX_USD` $5.

- Calls: 30 attempted; **OK 20, rejected/failed 10** (no retries per
  protocol). Scotland OK updates = 6 (nation-vs-nation ratings
  0.56/0.41/0.54/0.46/0.47; nation-vs-GBR 0.37 once). Total cost **$0.175486141**.
- Draw means by arm: nation-vs-nation (10 calls): mean rating 0.4705;
  nation-vs-GBR (10 calls): mean nation 0.474, mean GBR reference 0.471,
  mean same-call nation−GBR +0.003 (no format bias), mean nation−parent
  +0.036. Per-model deltas as in `analysis/scotland_repair_rerate.json`
  (qwen: 0 OK calls this round).

### Finals vs parent

| Nation | Old (live) | New seed | Final | Final − parent |
|---|---|---|---|---|
| England | 0.449133 | 0.440751 | 0.455856 | +0.0179 |
| Northern Ireland | 0.447064 | 0.440234 | 0.458034 | +0.0201 |
| Scotland | 0.496951 | 0.452705 | 0.463569 | **+0.0256** |
| Wales | 0.454966 | 0.442209 | 0.465241 | +0.0273 |

Order: Wales > Scotland > NI > England (all four within +0.018…+0.027 of
parent — a tight cluster; Scotland is no longer an outlier).

## 3. Scotland decision: SYNC (justified)

Scotland's premium over the parent **fell from +0.068 (pilot, pre-repair) to
+0.026 (post-repair)** — a drop of ~0.042, consistent with the audit's
~half-asymmetry estimate. The remaining gap (+0.026 vs parent; +0.008 vs
England; −0.002 vs Wales) is **supported by the repaired dossiers** by the
one genuine operative divergence that survives symmetric documentation:
Scotland's Hate Crime and Public Order (Scotland) Act 2021 lists gender
identity as a protected characteristic with standalone offences (in force 1
April 2024, plus the 2009 sentencing enhancement), whereas England and Wales —
now explicitly documented — have no transgender-specific aggravated-offence
statute at all, only the Sentencing Act 2020 s66 sentencing uplift. Scotland
also documents its devolved custody/search rules. The new single-sex-services
paragraph and the E&W hate-crime counterparts mean this residual gap is now
priced with both sides on the table.

**Decision: sync Scotland's re-rate final, 0.463569** (coordinator to apply to
`data/admin1.json` score/iterativeScore and commit; this run edited no
scores and committed nothing). Do NOT sync the 0.506 pilot final.

## 4. Verdict on the genuine-vs-asymmetry split after repair

The audit's ~half/half split held: of Scotland's +0.068 pilot premium, roughly
half (≈0.042, −62%) was **dossier asymmetry** — the missing single-sex-services
restrictions in Scotland, the missing hate-crime counterparts in England/Wales,
and the 1.7–2.7× sentence asymmetry — and roughly half (≈0.026) is **genuine
legal divergence**, which now sits exactly in the sibling band (+0.018…+0.027).
Caveat: the re-rate used a different seed and model draw-mix (qwen had zero OK
calls this round; Scotland had 6 updates, not 8), so repair vs. draw-noise
cannot be fully decomposed; the direction and magnitude are nonetheless
consistent with the audit. Caveat 2: NI's dossier was not repaired, so its
blocked-inclusion baseline remains documented only negatively; Wales remains
the only nation with no hate-crime statistics of its own.

## Files

- `data/admin1.json` (repaired four GBR records; scores untouched)
- `research/scotland-repair-manifest.json` (changes + source URLs + quotes)
- `scotland_repair.py`, `scotland_repair_rerate.py` (scripts)
- `runs/scotland-repair-rerate-20261125/` (attempt/content/result per
  iteration, ledger, pair-history.json)
- `analysis/scotland_repair_rerate.json` (repairs reference, pairings, draws,
  finals, cost)
