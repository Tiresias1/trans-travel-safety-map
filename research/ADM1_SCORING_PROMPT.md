# ADM1 Initial-Scoring Prompt (for the lightweight model)

**How this is used:** paste everything below the line into the model, once per country
(or as one autonomous batch — the model must do one country at a time and validate each
before moving on). Dossiers from the research phase live in `research/admin1/<ISO3>.md`.
The USA is already scored (exemplar — read `data/admin1.json` USA records to see the
quality bar) and must not be re-scored.

---

## Mission

Assign initial risk scores to first-level administrative divisions (states/provinces/
regions) of one country at a time, from its research dossier, for a map scoring the risk
to a **transgender visitor** if discovered/outed. Work in the repo root
`/home/meme/kóði/kort`.

For each country `<ISO3>`:

1. Read `research/admin1/<ISO3>.md` (the dossier).
2. Run `python3 tools/adm1_list.py <ISO3> --format md` — this gives the exact unit names,
   shapeIDs, the national score, and the excluded units (never score those).
3. Score the units per the rules below. **Only create a record for a unit whose evidence
   puts it ≥0.02 away from the national score.** Units with no sub-national signal get no
   record — the frontend automatically shows them at the national score. Do not pad.
4. Write one JSONL file `data/admin1_scores/<ISO3>.jsonl`, one record per line:

```json
{"shapeID": "<from adm1_list>", "name": "<exact name from adm1_list>", "score": 0.44, "summary": "<p>...</p>", "sources": ["https://...", "https://..."], "researchedAt": "<today>"}
```

5. Validate and merge:
   `python3 tools/apply_admin1_scores.py --in data/admin1_scores/<ISO3>.jsonl --dry-run`
   then without `--dry-run`. Fix any FAILs. Then `python3 tools/build_data.py` must pass.
6. Commit: `git add -A && git commit -m "ADM1 initial scores: <ISO3> (<n> units)"`.

## The scale

0.00–1.00, **higher = safer**. 0.00 = a discovered trans visitor faces near-certain
imprisonment/execution; 1.00 = full societal and legal acceptance (no jurisdiction
reaches it). Bands: <0.20 Do Not Travel · 0.20–0.40 High Risk · 0.40–0.60 Elevated ·
0.60–0.80 Reduced · ≥0.80 Low. Two-decimal precision.

Spectrum anchors (current map values): ISL 0.91 · NLD 0.79 · GBR 0.48 · USA 0.36 ·
TUR 0.15 · EGY 0.13 · AFG 0.02.

## Scoring rules

1. **The national score is your centre of gravity.** It already prices in everything
   national: federal law, border/passport friction, the national enforcement climate.
   A unit's score = national score ± sub-national deviation justified by dossier
   evidence. Say explicitly in the summary how far and why it deviates.
2. **Traveler-facing only.** What a visitor encounters: facilities/bathroom exposure,
   expression criminalisation, police behaviour, violence patterns, enforcement of
   bans (a ban blocked in court is much smaller than a ban being enforced). NOT
   resident-facing: healthcare bans, school policies, ID-marker rules for
   state-issued documents, sports bans — these are climate at most, small weight.
3. **Enforcement > statute.** Documented enforcement (arrests, trespass warnings,
   bounty suits filed) is a large factor. An unenacted or court-blocked statute is a
   small one. A statute with criminal penalties reaching private businesses (gas-station
   restrooms) is larger than one covering only schools.
4. **The single-incident rule.** Lone incidents barely move a score unless patterned,
   state-implicated, met with impunity or victim-prosecution. A *good* institutional
   response (conviction of an attacker, civil-rights finding, charges dismissed) is
   positive evidence and counts.
5. **Violence data: use rates, not raw counts.** Per-capita killing/incident rates from
   the dossier's datasets move scores; total counts mostly track population.
6. **Severity dominates probability** — but at sub-national level within one country,
   probability differences (enforcement vs no enforcement) are often what separates
   units. Use both.
7. **No flattening.** Units with materially different evidence must get materially
   different scores; units sharing evidence (a bloc/tier) may share a score with a
   shared justification, with small deltas for unit-specific facts. Every summary must
   contain a pairwise-style justification: vs the national score, and vs at least one
   named sibling unit where informative.
8. **Expected spread:** documented state-law federations can span ±0.15 or more around
   the national score (the USA spans 0.24–0.52 around 0.36). Unitary countries with
   only city-level culture notes span ±0.05. Never invent spread the dossier doesn't
   support; never compress spread it does.
9. **Two-decimal scores; band computed automatically** — do not write a band field.

## Summary field requirements

1–4 `<p>` paragraphs, ≤2500 chars, for the public popup. State the concrete evidence
(statute + year + penalty + enforcement status; datasets + rates; named institutional
responses), then the deviation from the national score and one sibling comparison. No
scores other than the national anchor and sibling references. Copy 2–5 source URLs from
the dossier's bullets — only URLs that support claims you actually make.

## Worked example (from the scored USA exemplar)

- **Idaho 0.24** (national 0.36): strictest criminal facility ban in the country,
  reaching private businesses, felony on second offence; partially court-blocked but in
  effect where no gender-neutral option exists; four legislative rounds 2023–2026.
  Well below national; below Florida (0.31) whose ban is narrower and whose first
  arrest was dismissed.
- **Florida 0.31**: criminal-trespass exposure in state buildings; first-in-nation
  arrest (charges dismissed — mixed-leaning-positive response); named travel advisories;
  BUT violence rate below the worst-law average (3.7/100k). Law worse than national,
  street violence better — nets modestly below.
- **Minnesota 0.52**: statutory non-cooperation with out-of-state anti-trans enforcement
  (blocks warrants/arrests/extradition) — the strongest shield in the country; no
  negative state-specific finding. Clearly above national; above California (0.48),
  which pairs the strongest legal floor with the highest incident volume.

## Country order

Process in this order (richest dossiers first): **MEX, CAN, GBR, AUS, BRA, IND, DEU,
ESP, COL, ARG, ITA, POL, NGA, IDN, MYS, TUR, RUS, ZAF, FRA, PHL, PER, CHL, KOR.**
(USA is done; CHN/TZA/IRQ exceptions are done.) If a dossier turns out too thin to
deviate any unit ≥0.02, write an empty JSONL, note it in the commit, and move on —
inheritance is the correct outcome, not forced records.
