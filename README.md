# Trans Travel Safety Map: August 2026

A zoomable, colour-coded world map scoring the risk to **transgender visitors** —
people who are, or may be discovered to be, trans — in every country and major
first-level administrative division.

**Live site:** served from this repository via GitHub Pages (static site, no build
step required).

## What the score means
- **0.00 (dark red)** = acute danger to a discovered trans visitor … **1.00 (light
  blue)** = among the safest environments. The fill colour is a continuous gradient;
  the five named bands (Do Not Travel / High Risk / Elevated Risk / Reduced Risk /
  Low Risk) label and summarise it.
- The score covers everyday exposure of a *visitor*: presence in public, bathrooms
  and facilities, documents and border crossings, police interactions, arrest risk
  (including placement in a gender-mismatched facility), harassment and violence,
  and medication access. It deliberately **excludes** general travel risks (crime,
  disease, conflict) and resident-only issues, though both may be mentioned in a
  region's popup as context.
- Scores are derived from **web research**: for each region, a search is performed,
  up to 20 result pages are fetched and read, and findings are summarised with
  sources. See `research/` for every country's notes; each popup lists its sources.

## Boundaries (de jure)
Boundaries follow **internationally recognised (de jure) positions**, not lines of
current control — e.g. Crimea and occupied territories render within Ukraine. Every
contested-area decision is documented in [`tools/patch_dejure.md`](tools/patch_dejure.md).

- Countries: geoBoundaries gbOpen (CC BY 4.0), patched per the policy above.
- First-level divisions: geoBoundaries gbOpen ADM1 (CC BY 4.0).
- Western Sahara polygon derived from the de jure Morocco/W.Sahara boundary line.

## Repository layout
```
index.html, css/, js/      the Leaflet map app (vanilla JS)
boundaries/                 countries.geojson (233 units), admin1.geojson (3,245 units)
data/countries.json         scores, ranks, summaries, sources per country
data/admin1.json            per-division scores (research in progress)
research/                   per-country research notes + anchors.md + PROGRESS.md
tools/                      boundary pipeline, data build/validation, de jure policy
```

## Pipeline
```
raw geoBoundaries downloads → tools/merge_adm0.py (de jure patches)
  → tools/promote_units.py (HKG/MAC/PRI) → mapshaper simplify → boundaries/countries.geojson
gbOpen ADM1 → tools/merge_adm1.py → mapshaper simplify → boundaries/admin1.geojson
research notes → data/countries.json / data/admin1.json → tools/build_data.py
  (validation + competition ranking) → data/meta.json
```

## Status
- ✅ Phase 0–1: site, pipeline, de jure boundaries, toggle, popups, gradient legend
- ✅ Phase 2: 15 calibration anchors researched and frozen (`research/anchors.md`)
- ⏳ Phase 3: remaining ~180 countries (see `research/PROGRESS.md`)
- ⏳ Phase 4: ADM1 tiers (USA states, etc.)
- Methodology details: [`PLAN.md`](PLAN.md)

*Informational research, not personalised advice. Conditions change; verify with
current official travel advisories before travelling.*
