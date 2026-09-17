# Methodology — Trans Travel Safety Map (2026 Edition)

This document describes how every score on the map is produced. It is the canonical
public methodology; the working research artefacts it summarises live in `research/`.

## What the map measures

Each score answers one question: **how much risk does a transgender *visitor* face in
this jurisdiction if they are, or are discovered to be, trans?**

Scores run from **0.00 to 1.00, higher = safer**, in five named bands:

| Band | Range | Meaning |
|---|---|---|
| Do Not Travel | 0.00–0.19 | A discovered trans visitor faces near-certain imprisonment, execution, or comparable catastrophe |
| High Risk | 0.20–0.39 | Severe outcomes (arrest, detention, serious violence) are realistically possible |
| Elevated Risk | 0.40–0.59 | Meaningful risk of arrest, violence, or severe harassment; mitigation possible |
| Reduced Risk | 0.60–0.79 | Risk exists but institutions and social climate substantially limit it |
| Low Risk | 0.80–1.00 | Strong protections, functioning recourse, no documented pattern of trans-specific harm |

The score integrates **probability of being outed × severity if outed** across the
traveler-facing axes below. 1.00 is an aspirational limit no jurisdiction fully reaches.

## What is scored — and what is not

**Scored** (the A–K taxonomy; full version in
[`research/outing-risk-taxonomy.md`](research/outing-risk-taxonomy.md)):

- **A** Border, transit & security screening (document mismatches, scanners, device searches)
- **B** Documents & everyday bureaucracy (hotel check-in, SIM registration, ID spot-checks)
- **C** Gendered spaces (bathrooms, changing rooms, saunas, women-only transport, **hospital-ward placement**)
- **D** Public presence & social reaction (harassment, filming/doxxing, service refusals)
- **E** Violence & predation (hate violence, dating-app ambushes, blackmail — travelers are soft targets)
- **F** Police interaction (stops, harassment, entrapment, extortion; protector vs. perpetrator)
- **G** Law & criminal exposure if outed (expression/impersonation statutes, morality laws, propaganda laws)
- **H** Arrest, detention & prison placement (misgendered facilities, "verification" exams, deportation)
- **I** Health & medication (HRT import/customs, emergency care, insurance)
- **J** Family & diaspora exposure (visiting-relatives scenarios, forced "conversion")
- **K** State & media climate (a probability *modifier*, never a standalone driver)

**Not scored** (they may inform axis K as climate signals, but never drive a score):

- General LGB rights — marriage equality, adoption, LGB criminalisation *per se*
- Resident-only trans issues — domestic legal-gender-recognition regimes, transition
  healthcare access, employment law. A visitor uses their home passport and will never
  apply for the destination's LGR scheme.
- General crime, terrorism, disease, conflict — except where they independently amplify
  trans-specific risk (e.g. collapse of protection for an already-targeted group).

Two standing corrections encode hard-won lessons:

- **Same-sex-conduct statutes are situational** — they reach only the fraction of trans
  visitors whose relationships read as same-sex under birth-sex legal status, or whom
  police extort with them. Weight ≈ 0.01–0.03 unless trans-specific enforcement is
  documented. Never a primary driver alone.
- **Severity dominates probability.** Every trans person carries some outing probability;
  what separates 0.9 from 0.2 is mostly what happens *after* the outing, and whether the
  state is perpetrator, bystander, or protector.

## Evidence standards

1. **Research-driven, never memory-driven.** Every jurisdiction was assessed from web
   research: searches rotated across the A–K axes, primary sources fetched and read.
   Each popup lists its sources with per-source summaries.
2. **Laws on the books vs. enforcement.** An unenforced statute is a small factor;
   documented arrests, convictions, or police practice is a large one.
3. **Individual incidents are weighed by what they prove, not how shocking they are.**
   Most crime never makes news; a single report barely moves a medium/large country.
   Incidents count when patterned, state-implicated, met with impunity or
   victim-prosecution, or in very small jurisdictions — and a *good* institutional
   response (convictions, public outcry, reform) counts as positive evidence.
4. **Burden-of-proof symmetry.** A documented positive counts as much as a documented
   negative. Absence of evidence is not evidence of absence — in either direction.
5. **Rule of law mediates.** Protections + hostile public → the rating depends on
   whether the legal system actually works for trans people. Law and society aligned in
   acceptance → residual risk is general-travel risk, not trans-specific. Law *against*
   trans people + strong enforcement → rule of law becomes a liability.

## Calibration

Fifteen anchor jurisdictions were researched first and frozen
([`research/anchors.md`](research/anchors.md)); every subsequent score was justified
**pairwise** against at least one neighbour and one anchor. Six standing calibration
rules guard against known failure modes — regional flattening, anchored corrections
(nudging a score instead of deriving it from the analysis that refuted it),
over-weighting LGB statutes, and asymmetric burden of proof between regions.

## Blind pairwise refinement

After the hand-calibrated map was complete (233 jurisdictions), it was stress-tested by
an automated blind process (`tools/blind_pairwise.py`):

1. Each jurisdiction's research was **anonymised** (`tools/make_blind_inputs.py` →
   lightweight model → `tools/apply_blind_fields.py`): no names, no scores, no source
   URLs, no comparator references, no region-identifying terms — validated by automated
   leak checks before use.
2. Over **10,000 randomised head-to-head pairs**, a rating model that never saw which
   jurisdictions it was reading scored each anonymised dossier independently against
   the scale and rules above (presentation order randomised to cancel position bias).
3. Stored scores drifted toward the ratings in small, bounded steps (coarse early,
   fine late; a score can never overshoot the direction the rating indicated).
4. Two full passes were run; the second, after hardening the rating rules, showed a
   neutral rater bias (+0.005) and repaired the first pass's over-corrections.

The result is a hybrid: hand-researched dossiers → independent blind rating →
rule-hardened re-rating. Every pair is logged with both ratings, the reasoning, and
the exact update arithmetic (`data/blind-pairwise-*.jsonl`).

## Boundaries

**De jure** — internationally recognised legal claims, not lines of current control
(Crimea and occupied territories are shown within Ukraine; Kashmir along the Line of
Control; etc.). Patches are documented in `tools/patch_dejure.md`. Base data:
[geoBoundaries](https://www.geoboundaries.org/) gbOpen (CC BY 4.0), with the Western
Sahara polygon from Natural Earth (public domain).

## Update cycle

**Annual.** Conditions rarely change fast enough to justify more frequent full
re-research; special-case updates are possible for acute changes. Each edition states
its year; per-jurisdiction research dates appear in the data
(`researchedAt` in `data/countries.json`).

## Caveats

- This map is **informational research, not personalised advice**. Risk depends heavily
  on the individual (presentation, documentation, itinerary, companions), and conditions
  change. Verify against current official travel advisories before travelling.
- Small jurisdictions carry thin evidence bases; their popups and dossiers say so
  explicitly, and their scores warrant extra caution in both directions.
- Subnational variation can be large (e.g. United States, Mexico, Brazil, India,
  Indonesia, Nigeria). Where admin-division data is loaded, use the divisions view;
  where it is not yet researched, the national score is a rough average at best.

## Repository layout

| Path | Contents |
|---|---|
| `research/outing-risk-taxonomy.md` | The full A–K checklist and severity ladder |
| `research/anchors.md` | Frozen anchor table + calibration rules 1–6 |
| `research/countries/<ISO>.md` | Per-jurisdiction research notes |
| `research/reanalysis-2026-08-21.md` | Systematic re-weighting pass (sodomy-as-situational etc.) |
| `research/audit-2026-08-21.md` | Random-sample pairwise audit |
| `data/countries.json` | Scores, summaries, sources, anonymised dossiers |
| `tools/blind_pairwise.py` | Blind pairwise refinement driver |
| `tools/blind_fields.md` | Anonymisation spec + prompts |
| `tools/build_data.py` | Validation, ranks, `data/meta.json` |
