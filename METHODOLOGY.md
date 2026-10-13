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

**The visitor/resident boundary cuts both ways.** The *absence* of resident-facing
machinery — no legal gender recognition regime, no national anti-discrimination or
hate-crime statute — is likewise a resident gap, not a visitor exposure: the visitor's
documents are issued and carried from their home country and never touch the
destination's gender-marker process. A missing LGR regime raises open questions for
edge cases (which documents get believed at entry, how detention would place someone),
but an open question is not an exposure: it weighs almost nothing where the dossier
answers the visitor-facing questions, and merely holds the score back where it leaves
them open. Factor kinds rank as: documented traveler-facing exposures (targeting,
enforced criminal statutes, universal-exposure measures) heaviest; open questions far
lighter; resident-machinery absence lightest — a local-attitudes cue the sources
usually already cover. Relatedly, institutional failure is exposure *evidence*, not an
offset: oversight bodies that issue repeated findings without remedying a practice
corroborate an unremedied exposure ("the traveller has recourse" does not soften a
violation the record shows recurring), and survey-measured discrimination prevalence
at scale is a primary everyday-exposure signal for the settings surveyed. A protection
is credited only when the dossier documents it as in force — an advocacy submission's
stated aims are not law.

Two standing corrections encode hard-won lessons:

- **Sexuality law is not trans law.** A same-sex-conduct statute is a *secondary*
  factor for trans visitors: it matters only through how it is actually used — as a
  police lever against visibly gender-nonconforming people, or as license for
  hostility toward them. Trans-specific primary factors (gender-expression law and
  enforcement, document and screening practice, facilities and custody, care access,
  trans-specific violence and its handling, documented social acceptance) dominate.
  A documented tolerant society with an unrepealed, dead-letter sexuality statute is
  not the same risk tier as a state that enforces against gender-nonconforming people.
- **Severity dominates probability.** Every trans person carries some outing probability;
  what separates 0.9 from 0.2 is mostly what happens *after* the outing, and whether the
  state is perpetrator, bystander, or protector.

## Evidence standards

1. **Research-driven, never memory-driven.** Every jurisdiction was assessed from web
   research: a 14-dimension coverage matrix (criminalisation, expression, documents,
   entry/visa, screening, facilities, custody, care access incl. youth care, violence,
   discrimination, state/media hostility, partner recognition, youth & education, social
   climate) drove source collection; extracted claims must share verbatim text with
   their source (anti-fabrication gate). Each popup lists its sources with per-source
   summaries.
2. **Wikipedia baseline.** Every country and researched division with an LGBTQ-rights
   or trans-rights Wikipedia article carries that article as a source; on-topic sources
   cited by those articles were harvested and verified through the intake lane
   (dead/irrelevant leads dropped, never guessed).
3. **Laws on the books vs. enforcement.** An unenforced statute is a small factor;
   documented arrests, convictions, or police practice is a large one.
4. **Individual incidents are weighed by what they prove, not how shocking they are.**
   Most crime never makes news; a single report barely moves a medium/large country.
   Incidents count when patterned, state-implicated, met with impunity or
   victim-prosecution, or in very small jurisdictions — and a *good* institutional
   response (convictions, public outcry, reform) counts as positive evidence.
5. **Burden-of-proof symmetry.** A documented positive counts as much as a documented
   negative. Absence of evidence is not evidence of absence — in either direction.
6. **Rule of law mediates.** Protections + hostile public → the rating depends on
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

## Blind pairwise refinement and settlement

Scores are stress-tested by an automated blind process (`tools/blind_pairwise.py`):

1. Each jurisdiction's research was **anonymised** into blind mirror fields: no names,
   no scores, no source URLs, no comparator references, no region-identifying terms —
   validated by automated leak checks (per-item, agency-noun, state-leak and
   meta-narrative gates) before use.
2. Over multiple full passes of **randomised head-to-head pairs** (2026 edition: a
   3,500-pair countries pass and a 9,500-pair division pass, re-run at 3,600 pairs
   after rule recalibration), a rating model that never saw which jurisdictions it was
   reading scored each anonymised dossier independently against the scale and rules
   above (presentation order randomised to cancel position bias; update steps ramp
   coarse-to-fine across each pass).
3. **Dependent territories are scored in a dedicated mixed mode**, never as
   countries-mode pairwise entities: the rater sees the territory's own anonymised
   dossier plus the parent state's anonymised national framework as the regime imposed
   on it ("A dependent territory stands under its parent's enforced regime" — local
   tolerance does not neutralise parent rules enforced at the border, in funded
   facilities, or through the document regime; the parent regime belongs to that
   dossier alone and never leaks across pairs). The countries-mode record is a display
   mirror of the territory's own score.
4. **A settlement pass enforces the convergence invariant**: every jurisdiction's
   stored score must equal its encounter-weighted rater mean (tolerance 0.02 on the
   0–1 scale), topped up with focused pair runs until it does. After the 2026 edition's
   final pass, all but two dozen jurisdictions converged in the main pass itself.

Every pair is logged with both ratings, the reasoning, and the exact update arithmetic.
The rating rulebook itself is public: see `tools/blind_pairwise.py` (rules 1–16,
including the sexuality-law secondary rule, the visitor/resident boundary, severity
ladders, the parent-regime rule, and the institutional-failure rule).

## Boundaries

**De jure** — internationally recognised legal claims, not lines of current control
(Crimea and occupied territories are shown within Ukraine; Kashmir along the Line of
Control; etc.). Patches are documented in `tools/patch_dejure.md`. Base data:
[geoBoundaries](https://www.geoboundaries.org/) gbOpen (CC BY 4.0), with the Western
Sahara polygon from Natural Earth (public domain).

### Sub-national (first-level divisions)

Divisions are handled on three routes, in descending order of evidence:

1. **Data-rich** (24 researched countries, `research/admin1/*.md`): a research pass
   collects per-division evidence under the same single-incident and burden-of-proof
   rules; initial scores are assigned from the dossiers; then an **in-country blind
   pairwise pass** (`blind_pairwise.py --admin1 --country ISO3`) refines them — division
   *scores* hidden, division names shown, the **parent country deliberately unblinded**
   (name, national score, full national assessment and spectrum anchors in the cached
   system prompt) so deviations are judged with national context. Sub-national rules:
   don't re-rate national factors; where rule of law is strong and no explicit autonomy
   exists, regional statutes cannot override national law (signalling, not operative
   risk); where rule of law is weak, regional practice can bend national law in either
   direction; enforcement beats statute.
2. **Different legal systems** in otherwise data-poor countries (Chechnya, Xinjiang,
   Tibet, Zanzibar, Iraqi Kurdistan): flagged model estimates (`"estimated": true`,
   marked in the popup), scored relative to the national score with a written
   justification.
3. **Dependent territories** (31, e.g. Puerto Rico, Faroe Islands, Aruba, Western
   Sahara): full dossiers in their own right, scored in the mixed mode described above
   — territory dossier + parent's enforced national framework, division names withheld
   from the rater. Their popups are labelled "Territory of <parent>".
4. **Everything else**: no record — the division inherits the national score, and the
   popup says so. Inheritance is the honest answer where no sub-national evidence
   exists; forced estimates from thin data cause more harm than good.

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
| `research/admin1/<ISO>.md` | Per-country sub-national research dossiers |
| `research/ADM1_RESEARCH_PROMPT.md` | Hand-off prompt: sub-national research pass |
| `research/ADM1_SCORING_PROMPT.md` | Hand-off prompt: initial division scoring |
| `research/reanalysis-2026-08-21.md` | Systematic re-weighting pass (sodomy-as-situational etc.) |
| `research/audit-2026-08-21.md` | Random-sample pairwise audit |
| `data/countries.json` | Scores, summaries, sources, anonymised dossiers |
| `data/admin1.json` | Per-division scores (keyed by geoBoundaries shapeID) |
| `tools/blind_pairwise.py` | Blind pairwise refinement driver (countries, `--admin1`, and mixed territory modes) |
| `tools/wiki_universal_sweep.py` | Wikipedia coverage sweep (LGBTQ-rights article per jurisdiction + cited-source harvest) |
| `tools/settle_scores.py` | Settlement pass (converge scores to rater means) |
| `tools/blind_fields.md` | Anonymisation spec + prompts |
| `tools/build_data.py` | Validation, ranks, `data/meta.json` |

## License

The map, its scores, and all project data files (`data/*.json`) are dedicated to the
**public domain (CC0 1.0)** — free of copyright restrictions, no attribution required.
Boundary geometry retains its upstream licences: geoBoundaries gbOpen (CC BY 4.0) and
Natural Earth (public domain), as noted in the README.
