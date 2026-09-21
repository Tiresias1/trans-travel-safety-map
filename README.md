# Trans Travel Safety Map — 2026 Edition

A zoomable, colour-coded world map scoring the risk to **transgender visitors** —
people who are, or may be discovered to be, trans — in every country (233
jurisdictions) and, where evidence supports it, in first-level administrative
divisions.

**Live site:** https://tiresias1.github.io/trans-travel-safety-map/ (GitHub Pages,
static, no build step).

**Full methodology: [`METHODOLOGY.md`](METHODOLOGY.md)** — the risk taxonomy,
evidence standards, calibration rules, and the blind pairwise refinement process.
Also linked from the site's About dialog.

## What the score means

- **0.00 (dark red)** = a discovered trans visitor faces near-certain imprisonment or
  execution … **1.00 (light blue)** = full legal and social acceptance. Continuous
  gradient; five named bands (Do Not Travel / High Risk / Elevated Risk / Reduced
  Risk / Low Risk) label it.
- Covers the *visitor's* everyday exposure: public presence, bathrooms and facilities,
  documents and border crossings, police interactions, arrest and detention (including
  gender-mismatched placement), harassment and violence, medication. Deliberately
  **excludes** general travel risks and resident-only issues (though both may appear in
  a popup as context under "Not factored into the score").
- **Research-driven, not memory-driven**: every jurisdiction was assessed from fetched
  primary sources; each popup lists them with summaries. The whole map was then refined
  through 10,000 **blind pairwise comparisons** — evidence presented anonymously to a
  rating model, without names or prior scores.
- **Updated annually.** This edition reflects research through September 2026.

## Boundaries (de jure)

Internationally recognised legal claims, not lines of current control — Crimea and
occupied territories render within Ukraine; Kashmir along the Line of Control. Every
contested-area decision is documented in [`tools/patch_dejure.md`](tools/patch_dejure.md).

- Countries: geoBoundaries gbOpen (CC BY 4.0), patched per that policy.
- First-level divisions: geoBoundaries gbOpen ADM1 (CC BY 4.0).
- Western Sahara polygon derived from the de jure Morocco/W.Sahara boundary line.

## Repository layout

```
index.html, css/, js/       the Leaflet map app (vanilla JS)
boundaries/                 countries.geojson (233), admin1.geojson (3,245)
data/countries.json         scores, summaries, sources, anonymised dossiers
data/admin1.json            per-division scores (keyed by shapeID)
data/meta.json              bands, gradient anchors, edition, repoUrl
research/                   per-country notes, anchors, audits, ADM1 dossiers
research/admin1/            sub-national research dossiers (24 countries)
tools/                      boundary pipeline, build/validation, blind-pairwise suite
METHODOLOGY.md              canonical public methodology
```

## Data pipeline

```
raw geoBoundaries → tools/merge_adm0.py (de jure patches) → tools/promote_units.py
  (HKG/MAC/PRI + territories to country level) → mapshaper simplify → boundaries/*.geojson
research (hand + lightweight-model passes) → data/countries.json
  → tools/blind_pairwise.py (blind pairwise refinement, 2 runs, 10k pairs)
  → tools/build_data.py (validation + competition ranking) → data/meta.json
sub-national: research/admin1/*.md dossiers → initial scores (tools/apply_admin1_scores.py)
  → tools/blind_pairwise.py --admin1 --country <ISO3> (in-country, parent-context pairs)
```

CI (`.github/workflows/validate.yml`) runs the validator and fails if committed data
is out of sync with `tools/build_data.py` output.

## Status

- ✅ Site, de jure boundaries, toggle, popups, gradient legend, mobile CSS
- ✅ 233/233 jurisdictions researched, hand-calibrated (15 frozen anchors, 6 calibration
  rules), reanalysed, and blind-pairwise-refined (10,000 pairs over 2 runs)
- ✅ Annual-edition branding + public methodology (`METHODOLOGY.md`)
- ⏳ Sub-national layer: 24-country research dossiers complete; USA divisions scored and
  in refinement; remaining countries being scored from dossiers; divisions without
  sub-national evidence inherit their national score (popup says so)

*Informational research, not personalised advice. Conditions change; verify with
current official travel advisories before travelling.*
