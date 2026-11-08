# Trans Travel Safety Map

A static, zoomable map of historical estimates of trans-specific risk to
visitors across countries and first-level divisions.

**Site:** https://tiresias1.github.io/trans-travel-safety-map/

**Methodology:** [METHODOLOGY.md](METHODOLOGY.md)

## Reading the map

Scores are approximate comparisons, not probabilities or personalised travel
advice. The intended scenario is a visitor who is identified as trans; passing,
silence and avoidance do not earn a place credit. Higher values indicate lower
estimated risk.

Exactly **0.00** means that an outed trans visitor faces near-certain
imprisonment **and** likely execution. No other point has a defined precise
consequence. The colour bands are display groupings, not calibrated safety
thresholds.

Evidence varies by place. Sources are linked in popups where provided, and
missing evidence is not proof of safety or danger. Some division scores inherit
the national score; some historical country scores incorporate regional
aggregates or manual adjustments. National and local values should not be
read as precise, independently validated comparisons.

## Boundaries and data

Boundaries represent de jure legal claims rather than lines of current control.
Boundary decisions are documented in [`tools/patch_dejure.md`](tools/patch_dejure.md).
Country and first-level boundaries use geoBoundaries gbOpen (CC BY 4.0), with
Natural Earth material for Western Sahara.

- `index.html`, `css/`, `js/`: the Leaflet map application
- `boundaries/`: country and first-level geometries
- `data/`: scores, summaries, sources and metadata
- `research/`: research notes, historical methods and experiments
- `tools/`: data validation and boundary tooling

The map and project data are dedicated to the public domain under CC0 1.0;
boundary data retain their upstream licences. Conditions change, so consult
current, relevant sources before travelling.
