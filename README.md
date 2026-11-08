# Trans Travel Safety Map

A zoomable, colour-coded world map estimating risk to **transgender visitors** —
people who are, or may be discovered to be, trans — in every country and, where
evidence supports it, in first-level administrative divisions.

**Live site:** https://tiresias1.github.io/trans-travel-safety-map/ (GitHub Pages,
static, no build step).

**Full methodology: [`METHODOLOGY.md`](METHODOLOGY.md)** — what a score means,
the risk taxonomy, and how evidence is weighed. Also linked from the site's
About dialog.

## What the score means

- **0.00 (dark red)** = a discovered trans visitor faces near-certain
  imprisonment **and** likely execution — both, not either. **1.00 (light blue)**
  = the safe end of the index. No other point has a defined precise consequence;
  the five named bands (Severe / High / Elevated / Reduced / Low Risk) are
  display groupings, not calibrated thresholds.
- The score is **conditional on discovery**: it rates what happens to a visitor
  identified as trans, not the odds of identification. Passing, silence and
  avoidance earn no credit.
- Covers the visitor's everyday exposure: public presence, bathrooms and
  facilities, documents and border crossings, police interactions, arrest and
  detention (including gender-mismatched placement), harassment and violence,
  medication. Deliberately excludes general travel risks and resident-only
  issues, except where they bear directly on a trans visitor's safety.
- Evidence depth varies by place. Popups list sources where provided and flag
  open questions; where a region has no local evidence it carries the national
  score and the popup says so. Missing evidence is not proof of safety or
  danger.

## Boundaries (de jure)

Internationally recognised legal claims, not lines of current control — Crimea
and occupied territories render within Ukraine; Kashmir along the Line of
Control. Contested-area decisions: [`tools/patch_dejure.md`](tools/patch_dejure.md).

- Countries and first-level divisions: geoBoundaries gbOpen / ADM1 (CC BY 4.0),
  countries patched per that policy; Western Sahara polygon from the de jure
  Morocco/W.Sahara boundary line.

## Repository layout

```
index.html, css/, js/       the Leaflet map app (vanilla JS)
boundaries/                 country and ADM1 geometries
data/                       scores, summaries, sources, metadata
research/                   research notes, taxonomy, dossiers
tools/                      boundary pipeline
METHODOLOGY.md              canonical public methodology
```

*Informational research, not personalised advice. Conditions change; verify
with current official travel advisories before travelling.*
