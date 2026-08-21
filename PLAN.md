# Development Plan — Trans Travel Safety Map: August 2026

## 1. Project Overview

A static web page titled **"Trans Travel Safety Map: August 2026"** featuring a zoomable,
colour-coded world map showing the risk to a **transgender visitor** in each country and
(first-level) administrative division. The score measures risk *specifically due to being
discovered/known to be trans*, relative to common everyday situations, and is **not** a
general travel-safety score and **not** a general LGBTQ score.

### Key product requirements (from the brief)

| Requirement | Implementation summary |
|---|---|
| Zoomable world map, title "Trans Travel Safety Map: August 2026" | Leaflet.js map, HTML `<h1>` title |
| Colour-coded by score (continuous gradient, dark red at 0.0 → light blue at 1.0, with the five named band colours at band centres) | Choropleth fill colour interpolated per region's exact score (§5.1) |
| Scores = risk to a discovered-to-be-trans **visitor**, relative to everyday things | Scoring rubric (§5) enforced in research protocol (§4) |
| Exclude non-trans risks (incl. other LGBTQ risks) from the score | Explicit rule in rubric; non-trans risks may be *mentioned* in text, clearly flagged |
| Visitor focus, not resident focus | Rubric items oriented to visitor exposure (§5.2) |
| Toggle button: countries ↔ first-level admin divisions | UI toggle swapping two GeoJSON layers |
| **De jure** borders (NOT Natural Earth default, which is de facto) | geoBoundaries gbOpen + manual de jure patches (§3) |
| Zoom via button **and** scroll wheel | Leaflet default controls + `scrollWheelZoom: true` |
| Click → infobox popup with score (2 dp), international rank, risk text | Leaflet popup bound per feature, populated from data JSON |
| Research via web search (20 results, fetch all URLs, follow-ups allowed), not internal knowledge | Research protocol (§4) |
| Free hosting | GitHub Pages (§2.2) |

---

## 2. Technical Stack

### 2.1 Frontend
- **Map library: Leaflet.js** (v1.9.x, via CDN or vendored). Free, no API key, lightweight.
  - `L.map` with `zoomControl: true` (the +/- buttons) and `scrollWheelZoom: true`.
  - No basemap tiles required for correctness — the choropleth polygons themselves can sit
    on a plain background. **Optional:** a light neutral basemap (e.g. CARTO Positron, free
    with attribution) for geographic context; keep polygon fills opaque enough that band
    colours read clearly. Decision: ship without basemap first (fewer external deps, no
    tile-usage-policy concerns), add Positron only if usability testing wants context.
- **Vanilla HTML/CSS/JS.** No build step required. This keeps hosting trivial and lets
  subsequent models edit files directly.
- Data layers loaded as **GeoJSON** (or TopoJSON + `topojson-client` if file size demands
  it; measure first — simplified country polygons ≈ 1–2 MB, simplified ADM1 ≈ 3–6 MB,
  which is acceptable; TopoJSON cuts this roughly in half).

### 2.2 Hosting — GitHub Pages
- **Choice: GitHub Pages**, deploying the repo root (or `/docs`) of a public repo.
  - Rationale: free, zero-config for static sites, HTTPS included, and the git repo doubles
    as a public, versioned archive of the research data (each country's score + sources),
    which suits a project whose value is its dataset.
  - Backup option if bandwidth/build-minutes ever matter: **Cloudflare Pages** (unlimited
    bandwidth on free tier, 500 builds/month). Migration is trivial since the site is static.
- Deployment: `git push` → Pages serves the branch. No CI needed initially; optionally add
  a GitHub Action that validates `data/*.json` against the schema (§6) before deploy.

### 2.3 Repository layout

```
kort/
├── PLAN.md                     # this file
├── index.html                  # the whole app shell
├── css/style.css
├── js/
│   ├── app.js                  # map init, layer toggle, popups, legend
│   └── data-loader.js          # fetches & merges boundaries + scores
├── boundaries/
│   ├── countries.geojson       # ADM0, de-jure-patched, simplified
│   └── admin1.geojson          # ADM1, simplified
├── data/
│   ├── countries.json          # scores/ranks/summaries per country (§6)
│   ├── admin1.json             # scores/summaries per ADM1 unit
│   └── meta.json               # generated-at, methodology version, rank table
├── research/
│   ├── countries/<ISO3>.md     # per-country research notes + sources + draft text
│   └── admin1/<ISO3>/<unit>.md # per-unit research notes
└── tools/
    ├── fetch_boundaries.sh     # downloads geoBoundaries gbOpen ADM0/ADM1
    ├── patch_dejure.md         # documented manual boundary patches (§3.3)
    ├── simplify.sh             # mapshaper commands
    └── build_data.py           # merges research/ → data/, computes ranks, validates
```

---

## 3. Boundary Data (de jure requirement)

### 3.1 Source: geoBoundaries gbOpen
- Download **gbOpen** ADM0 and ADM1 from geoboundaries.org. License **CC-BY 4.0** — add an
  attribution line on the page: *"Boundary data: geoBoundaries (CC BY 4.0)."*
- gbOpen is the open-license release and its ADM1 is global — exactly what the toggle needs.
- **Avoid the CGAZ product** for this use: it follows US State Department dispute handling
  and simplifies geometry; and **avoid Natural Earth defaults**, which are de facto (the
  brief's explicit caution: default Natural Earth shows Russian-occupied parts of Ukraine
  as Russia).

### 3.2 De jure patch policy
Even gbOpen needs a documented audit. Create `tools/patch_dejure.md` listing every known
disputed/contested area and the chosen de jure treatment, with a source per entry. Working
rules:

1. **Default:** internationally (broadly UN-membership / ICJ / treaty) recognised de jure
   boundaries. Where "de jure" is itself contested (two states each with a legal claim),
   pick the most widely recognised position, record the alternative in the notes file, and
   add a one-line caveat in that territory's infobox text.
2. **Known cases to handle explicitly** (non-exhaustive; verify each with a quick search
   before patching):
   - **Ukraine:** include Crimea, and all of Donetsk/Luhansk/Zaporizhzhia/Kherson oblasts,
     as Ukraine. (This is the headline case the brief calls out.)
   - **Cyprus:** Republic of Cyprus as the de jure whole island (note Northern Cyprus as
     de facto separate in the popup text).
   - **Georgia:** Abkhazia and South Ossetia as Georgia.
   - **Moldova:** Transnistria as Moldova.
   - **Serbia/Kosovo:** de jure contested (Serbia claims it; >100 UN members recognise
     Kosovo). Decide and document; recommendation: show Kosovo as a separate unit with an
     explicit caveat note, since treating it as Serbia misleads visitors on the ground.
   - **Israel/Palestine:** document the chosen treatment (recommendation: Israel within
     internationally recognised lines + West Bank & Gaza as Palestine units, with caveats).
   - **India/Pakistan/China (Kashmir, Aksai Chin, Arunachal Pradesh):** genuinely
     overlapping de jure claims — document the chosen lines and caveat heavily.
   - **Morocco/Western Sahara:** document choice (recommendation: Western Sahara shown
     separately per UN non-self-governing-territory status, with caveat).
   - **Somalia/Somaliland, Armenia/Azerbaijan (Nagorno-Karabakh — post-2023 status),
     Yemen, South China Sea islands, Taiwan** (de jure contested: PRC claim vs. ROC
     administration — recommend showing Taiwan as its own scored unit with caveat, since
     visitor risk there is governed by Taiwan's own laws).
3. Implementation: after downloading gbOpen, diff its geometry against the table above;
   where gbOpen is already de jure, do nothing; where not, patch geometry (e.g. reassign
   the Crimea polygon's ISO to UKR) using `mapshaper`/manual GeoJSON edit, and log the
   patch in `patch_dejure.md`.

### 3.3 Simplification
- Use **mapshaper** (`-simplify 5% keep-shapes`) to bring ADM0 to ≈1–2 MB and ADM1 to
  ≈3–6 MB. Verify no polygons vanish (`keep-shapes`) and spot-check small states
  (Singapore, Bahrain, Caribbean micro-states, Gulf states) remain clickable.
- Ensure every polygon carries stable join keys: ADM0 → `ISO_A3`/`shapeISO`; ADM1 →
  geoBoundaries `shapeID` (store the gbOpen release version in `meta.json`).

---

## 4. Research Protocol (per-country, then per-ADM1)

> **Core rule:** scores and texts must be based on web research, not model priors. Every
> score must be traceable to fetched sources recorded in `research/`.

### 4.1 Country research loop (~195 countries)
For each country, in a sensible order (start with large/high-traffic and high-variance
countries to establish calibration anchors early — see §5.3):

1. **Search.** One primary query such as
   `"<country> transgender traveler safety if outed bathrooms prison passport"` —
   retrieve **20 results**. The query set must surface the **six traveler-outing axes
   of §5.2**, not general-LGB news. Mix axes across follow-up queries, e.g.:
   - `"<country> trans tourist passport X gender marker entry denied border"`  (axis 1)
   - `"<country> transgender harassment violence public transphobia incidents"`  (axis 2)
   - `"<country> transgender bathroom law legal use facilities toilets"`  (axis 3)
   - `"<country> transgender police stopped documents detained trans"`  (axis 4)
   - `"<country> transgender prisoner placement women's prison detained"`  (axis 5)
   - `"<country> import hormones HRT customs prescription transgender traveler"`  (axis 6)
   Only fall back to general "LGBTQ rights" / ILGA-Rainbow-Map queries when the axis
   queries return thin results — and treat those general hits as weak climate signals
   (§5.2), never as the score basis. **Do not rely on a single preexisting map or index**
   (ILGA Rainbow Map, Spartacus, Equaldex, FRA): search in every case, fetch the URLs,
   and weigh primary sources over indices.
2. **Fetch all 20 URLs.** Read each fetched page. (Pages that 404/paywall: note and move
   on; if fewer than ~8 usable pages remain, run follow-up searches to backfill.)
3. **Follow-ups** when: sources conflict; only LGBTQ-general info found (need trans-
   specific); country is small/under-covered; or something in the sources suggests a
   trans-specific law/practice worth confirming (e.g. "cross-dressing" statutes,
   entry bans, forced testing).
4. **Write research note** `research/countries/<ISO3>.md`:
   - Bulleted key findings, each with its source URL.
   - 1–4 paragraph **summary** of the risk to a trans *visitor* (this becomes the infobox
     text — see §7.2 for tone/format rules).
   - Provisional score + rationale, referencing the rubric (§5) and at least one anchor
     country comparison (§5.3).
5. **Record data** into `data/countries.json` (schema §6). Ranks are computed globally
   later, not per-country.

### 4.2 Source-quality guidance
Prefer **trans-traveler-specific primary sources** over general LGBT indices:
- Government travel advisories with a trans/gender-marker section (US State Dept., UK
  FCDO, Canada, Australia Smartraveller, Germany AA, etc.) — these directly address
  border/document/axis-1 risk to travelers.
- Trans-specific country reporting: Transgender Europe (TGEU), ILGA World's *trans*
  legal maps, Human Rights Watch / Amnesty country pages when they discuss trans
  detention, prison placement, police abuse, or bathroom restrictions.
- News of incidents involving trans *travelers/visitors* (border detentions, bathroom
  arrests, prison-placement cases) — the most on-topic evidence.
- Local trans-rights orgs for the violence/police/prison axes.

Use **ILGA World / Equaldex / Human Dignity Trust legal maps only to locate the legal
provisions**, then confirm each provision against its primary source (statute text,
court ruling, news). **Do not use** the ILGA-Europe Rainbow Map %, the Spartacus Gay
Travel Index, Equaldex overall %, or FRA general LGBTIQ survey as score inputs (§5.2):
they are general/resident-LGB policy-completeness metrics, not trans-traveler-outing
risk. Weight recent (≤3 years) material higher; the map is dated "August 2026" so flag
anything sourced older than ~2022 as "verify recency".

### 4.3 ADM1 research loop
gbOpen yields ~3,500+ ADM1 units globally — researching each individually is infeasible.
Tiered approach:

- **Tier A — full per-unit research** (own search cycle per unit): countries with strong
  subnational legal/cultural variation and high traveller volume. Minimum set: **USA
  (states+DC), Canada (provinces/territories), Australia (states/territories), Mexico
  (states), Brazil (states), India (states/UTs), Russia (federal subjects — collapse
  where sources allow grouping), China (provinces), Germany (Länder), Spain (autonomous
  communities), UK (nations), UAE (emirates), Saudi Arabia (provinces if variation
  found), Indonesia (provinces), Nigeria (states), Argentina (provinces), Japan
  (prefectures if variation found), Italy (regions if variation found)**. During country
  research, note for each country whether subnational variation is real; promote/demote
  tiers accordingly and record the decision.
- **Tier B — grouped research**: research regions/clusters (e.g. "Russian North Caucasus",
  "Prairie provinces") and apply one score to the group, noting the grouping in the text.
- **Tier C — inherit**: units with no evidence of meaningful divergence inherit the
  country score, with infobox text = country text plus a line: *"No evidence of
  subnational variation found; shown at national score."* Default to Tier C **only**
  when country research gave no indication of divergence.
- Every Tier A/B unit still gets a `research/admin1/<ISO3>/<unit>.md` note; when
  writing/scoring units, explicitly use the parent country's research note as context
  (per the brief).

### 4.4 Consistency & calibration passes
- After ~15 anchor countries are scored (§5.3), do a **calibration pass**: re-read all
  scores so far and adjust to be mutually consistent.
- After all countries: a **global consistency pass** — sort by score, read adjacent
  entries' summaries, and fix inversions ("X scored below Y but its text sounds worse").
- Repeat a lighter version after Tier A ADM1 units.

---

## 5. Scoring Rubric (0.00–1.00, higher = safer)

### 5.1 Colour gradient and bands
The map fill colour is a **continuous gradient** over the full 0.00–1.00 score range,
not five discrete colours. Each risk band keeps its label (used in the legend, infobox,
and data), with the band's representative colour located at the **centre** of its range:

| Band | Score range | Label | Centre colour (hex, at centre score) |
|---|---|---|---|
| 1 | 0.00–0.199 | **Do Not Travel** | `#d73027` red (centre 0.1) |
| 2 | 0.20–0.399 | **High Risk** | `#fc8d59` orange (centre 0.3) |
| 3 | 0.40–0.599 | **Elevated Risk** | `#fee08b` yellow (centre 0.5) |
| 4 | 0.60–0.799 | **Reduced Risk** | `#91cf60` light green (centre 0.7) |
| 5 | 0.80–1.00 | **Low Risk** | `#1a9850` green (centre 0.9) |

The two ends of the scale extend past the outermost centres to end-members:
- **0.00 → dark red** `#67000d`
- **1.00 → light blue** `#a8dbe8`

A region's fill colour is computed by **piecewise-linear interpolation** (in RGB) across
these seven anchor points:

| Score | Colour |
|---|---|
| 0.00 | `#67000d` dark red |
| 0.10 | `#d73027` red |
| 0.30 | `#fc8d59` orange |
| 0.50 | `#fee08b` yellow |
| 0.70 | `#91cf60` light green |
| 0.90 | `#1a9850` green |
| 1.00 | `#a8dbe8` light blue |

(Boundary convention for band membership: [0.00,0.20), [0.20,0.40), [0.40,0.60),
[0.60,0.80), [0.80,1.00]. A score of exactly 0.20 is in band 2, etc. State this in
`meta.json`. The band label still governs the legend and infobox wording; only the fill
colour is continuous.)

### 5.2 What the score measures
Risk **to a visitor** arising **specifically from being (discovered to be) trans**, across
everyday situations. The score must be driven by evidence on these **six traveler-outing
axes** — every research note must address each axis where evidence exists:

1. **Border & documents** — entry/visa treatment of a passport carrying a *changed* or
   `X` gender marker; device and social-media checks at the border; risk of questioning,
   detention, or denial of entry for trans reasons.
2. **Public presence & outing reaction** — the reaction if the traveler is visibly or
   becomes known to be trans in public: harassment, misgendering, violence, and social
   hostility *specifically toward trans people* (not general LGB).
3. **Bathrooms & gendered facilities** — the legal right *and* social safety to use
   gendered facilities (toilets, locker rooms, changing rooms, baths/onsen) matching
   gender; any criminal or civil exposure from doing so.
4. **Police interaction** — treatment if stopped or questioned: document checks that
   force outing, extortion/bribery, police harassment or violence targeting trans
   people, and whether police protect or worsen the situation.
5. **Arrest & detention / prison placement** — if arrested (even for an unrelated minor
   offence), whether the person is placed by birth sex or by gender, the risk of abuse in
   a cross-gender or misgendered facility, and detention conditions for trans people.
6. **Medication & healthcare continuity** — carrying HRT / gender-affirming medication
   through customs (legality, prescription requirements, seizure risk); access to
   emergency trans-relevant healthcare.

**Non-scoring signals (cite only as weak *hostility/climate* context, clearly labelled
as such — never as score drivers):**
- General LGB rights — same-sex marriage, civil unions, adoption, blood donation, LGB
  military service, and general "LGBTQ-friendliness" indices are NOT the topic.
- General LGBT policy-completeness metrics — **ILGA Rainbow Map %, the Spartacus Gay
  Travel Index, Equaldex overall scores, and the FRA general LGBTIQ survey** measure a
  broad LGB+ policy basket and often weight resident/family/LGB items; do **not** map them
  to the 0–1 score and do not let them create fine differentials. Use them at most as one
  social-climate signal among many.
- **Resident-facing trans law** — the destination's *domestic* legal-gender-recognition
  regime for its own residents (self-ID vs judicial vs medical-gatekept), its transition-
  healthcare system infrastructure, employment-discrimination law, conversion-therapy
  bans, intersex infant-surgery bans, and adoption/name rules for residents — these affect
  *residents*, not a short visitor's outing risk. (A domestic self-ID law is only a weak
  proxy for social acceptance, which bears on axis 2.) Where the *destination's*
  recognition of *foreign* documents is unclear, that is axis 1 and is score-relevant.

**Excluded outright** (mention only in the popup's out-of-scope section): general
crime/terrorism/health risks affecting everyone; LGB-specific risks not applicable to
trans people. Every research note must state when a signal was used only as a hostility
proxy, and must surface low-confidence axes where trans-traveler-specific evidence is
thin.

### 5.3 Anchors (relative scale)
Scores must make sense **relatively**, not just absolutely. The first countries researched
are calibration anchors. Suggested initial anchors — **these are placeholders to be set by
actual research in Phase 2, not predetermined scores** (the numbers below are starting
hypotheses only and MUST be revised from evidence):

| Anchor (hypothesis) | Why it's an anchor |
|---|---|
| Malta / Iceland / Spain / Netherlands ≈ 0.85–0.95 | Strong legal protection + social acceptance; define the top of scale |
| USA (national view) ≈ 0.55–0.70 | Sharp subnational split — anchors mid-scale and motivates Tier A |
| Brazil ≈ 0.35–0.50 | Legal protections but very high recorded anti-trans violence — anchors "law vs. practice" gap |
| Russia ≈ 0.10–0.25 | "Propaganda" laws, designated-extremist LGBTQ movement, document bans |
| Saudi Arabia / Afghanistan / Brunei ≈ 0.00–0.10 | Criminalisation of gender nonconformity / morality policing; define the bottom |

After research, fix final anchor values, record them in `research/anchors.md`, and require
every subsequent score rationale to name ≥1 anchor comparison ("riskier than Brazil
(0.42) because…, safer than Russia (0.18) because…").

### 5.4 Ranking
- **International rank** = position of the country's score among all scored countries,
  sorted descending, **ties share the best rank** (standard competition ranking: 1, 2, 2,
  4…). Computed by `tools/build_data.py`, stored in `data/meta.json` + denormalised into
  each country record for fast popups.
- ADM1 units get two ranks: rank among ADM1 units **worldwide**, and rank within their
  country (shown secondarily in the popup).

---

## 6. Data Schema

`data/countries.json`:
```json
{
  "FRA": {
    "name": "France",
    "score": 0.78,
    "rank": 24,
    "band": "Reduced Risk",
    "summary": "<p>…1–4 paragraphs…</p>",
    "outOfScopeNotes": "General crime risk low; pickpocketing in Paris affects all tourists.",
    "sources": ["https://…", "…"],
    "researchedAt": "2026-08-14",
    "anchorRefs": ["ESP", "DEU"]
  }
}
```
`data/admin1.json` keyed by geoBoundaries `shapeID`:
```json
{
  "shapeID": "…", "iso3": "USA", "name": "Texas", "tier": "A",
  "score": 0.41, "worldRank": 812, "countryRank": 44, "band": "Elevated Risk",
  "summary": "…", "inherited": false, "sources": ["…"], "researchedAt": "…"
}
```
`data/meta.json`: `{ generatedAt, methodologyVersion, gbOpenVersion, bandEdges,
bandLabels, gradientAnchors, totalCountries, totalAdmin1, disputedBoundaryNotesUrl }`,
where `gradientAnchors` is the seven-point score→hex table from §5.1 (the interpolation
itself is a pure function of this list, implemented once in `js/app.js`).

Validation rules (enforced by `tools/build_data.py`):
- score ∈ [0,1], exactly 2 decimals; band consistent with score; every boundary polygon
  has a data record and vice versa (fail the build on orphan keys); `sources` non-empty
  unless `inherited: true`; summary 1–4 paragraphs (≤ ~2,500 chars) of safe HTML
  (`<p>`, `<em>`, `<a rel="noopener">` only — sanitise).

---

## 7. Frontend Specification

### 7.1 Page structure
- `<h1>Trans Travel Safety Map: August 2026</h1>`; subtitle line: *"Risk to transgender
  visitors if known/discovered to be trans. Research-based scores; click a region for
  details."*
- Controls row: **Countries | Admin Divisions** toggle (segmented button), legend, and a
  small "Methodology / About" link opening a modal summarising §4–§5, the de jure
  boundary policy + attribution, and the data date.

### 7.2 Map behaviour
- Leaflet map, world view at init (`setView([20, 0], 2)`), `worldCopyJump: true`,
  `maxBounds` slightly beyond the world, `minZoom: 2`.
- Zoom: Leaflet's +/- control **and** scroll wheel (`scrollWheelZoom: true`), plus
  double-click and pinch by default.
- Two `L.geoJSON` layers (countries, admin1); toggle button swaps which is added to the
  map; current mode persisted in the URL hash (`#view=admin1`) for shareability.
- Styling: fill from the gradient function (§5.1) applied to the region's exact score,
  `fillOpacity ≈ 0.75`, 1px darker border (border = a darkened variant of the fill);
  hover → highlight (thicker border / brighter fill) with tooltip showing name + score;
  no-data polygons → grey `#999` with "Not yet assessed" popup.
- **Click → popup infobox** containing, in order:
  1. Region name (+ country name for ADM1)
  2. **Score** to two decimals, e.g. `0.41`, plus band label with a colour chip
     rendered in the region's exact gradient colour (not the band's centre colour)
  3. **International rank**, e.g. `Rank 44 of 195 countries` (ADM1: `Rank 812 of ~3,600
     divisions · 44 of 51 in the United States`)
  4. The 1–4 paragraph risk text (from `summary`)
  5. Divider, then (smaller, muted) out-of-scope notes if any, clearly labelled
     *"Not factored into score:"*
  6. Collapsible source list + "Researched: <date>" line
- Popup max-height with internal scroll; popups must work identically in both modes.

### 7.3 Legend & accessibility
- Fixed legend bottom-right: a **continuous colour bar** rendered from the same
  seven-anchor gradient (a `<canvas>`/CSS gradient strip, e.g. 160×12 px) with tick
  labels at 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, plus the five band names with their ranges
  (`0.00–0.20 Do Not Travel`, …) and a grey swatch for "No data". This shows both the
  gradient and the discrete band labels in one compact element.
- Colour chips also given text labels (never colour alone); keyboard-focusable toggle and
  popups; `prefers-reduced-motion` respected; mobile: tap = popup, pinch zoom works,
  controls collapse sensibly (test at 360px width).

### 7.4 Performance
- Lazy-load `admin1.geojson` only on first toggle to Admin mode (show a spinner).
- `fetch` JSON with `cache: "force-cache"`; gzip/brotli via Pages. Target: initial load
  < 2.5 MB, interactive < 3 s on mid mobile.

---

## 8. Execution Phases (checklist for subsequent models)

**Phase 0 — Scaffolding**
- [ ] Init repo; `index.html` + Leaflet displaying an unstyled world layer from
      gbOpen ADM0; deploy to GitHub Pages to prove the pipeline end-to-end.
- [ ] `tools/fetch_boundaries.sh`, `tools/simplify.sh`; record gbOpen version.

**Phase 1 — Boundaries finalised**
- [ ] Build `tools/patch_dejure.md` table; verify each disputed case with a search;
      apply patches; spot-check map visually (Crimea in Ukraine, etc.).
- [ ] Produce final `boundaries/countries.geojson` + `boundaries/admin1.geojson`;
      verify join keys; confirm every polygon appears in a feature-name audit.

**Phase 2 — Calibration research (~15 anchor countries)**
- [ ] Run §4.1 loop on the anchor set; write notes; score; run calibration pass;
      freeze `research/anchors.md`.

**Phase 3 — All countries**
- [ ] §4.1 loop for remaining countries (work in batches; commit `research/` notes
      per batch). Track progress in a checklist file `research/PROGRESS.md`
      (195 countries; mark each ☐/☑).
- [ ] Global consistency pass; compute ranks; generate `data/countries.json` +
      `meta.json`.

**Phase 4 — ADM1**
- [ ] Finalise tier list from country-research notes; Tier A full research; Tier B
      grouped; Tier C inherit; ADM1 consistency pass; generate `data/admin1.json`.

**Phase 5 — Frontend completion**
- [ ] Choropleth styling, legend, toggle, popups per §7; methodology modal;
      attribution; URL-hash state; mobile QA; performance pass (lazy admin1).

**Phase 6 — Polish & ship**
- [ ] Schema validation in a GitHub Action; README with methodology summary +
      license/attribution; final deploy; manual QA sweep of ~20 random popups
      against their research notes.

### Effort notes
The research phases dominate: ~195 country loops + several hundred Tier-A/B ADM1 loops,
each ≈ one search + ~20 fetches + write-up. Subsequent models should work in resumable
batches and never regenerate finished research without cause; `research/PROGRESS.md` is
the source of truth for what is done.

---

## 9. Risks & Mitigations
| Risk | Mitigation |
|---|---|
| Researcher drift: scores inconsistent across batches | Anchor system (§5.3) + two consistency passes (§4.4); every score cites an anchor comparison |
| "De jure" itself contested (Kashmir, Kosovo, Taiwan, W. Sahara) | Documented policy table + in-popup caveats (§3.2) — the policy, not silence, is the deliverable |
| Small/under-covered countries yield thin sources | Backfill follow-up searches (§4.1 step 3); if still thin, score with explicit low-confidence note in text |
| gbOpen ADM1 misaligned with real Tier-A needs (e.g. missing city-level for city-states) | Allow ADM2 override for named cases, documented in `patch_dejure.md` |
| GeoJSON size on slow connections | TopoJSON conversion + lazy ADM1 load (§7.4) |
| Legal caution: publishing safety scores per country | Factual, sourced, dated ("August 2026"), with methodology modal and per-region source lists; standard travel-advisory-style disclaimer in About modal |
