# Evidence map — pilot-only evidence view (country-feasibility)

**Snapshot:** `data/countries.json` at commit `80c573a5fe205a21c34657cdbfedb0dfda2f2aab`,
sha256 `c4a2c8339b0d389a42d8b90ec48bafab209d511185ab10e19789d29de4baebce`
(5,687,197 bytes). Frozen in `frozen/manifest.json → evidence_snapshot`.
Refreshed at HEAD: the US MAP facility-category correction (data as of 7 November
2026) and the corrected 19 March 2025 arrest are in the USA record; GBR/NPL/VAT are
byte-identical to the earlier `4ce04e50` refresh;
the two GBR pilot-only edits in section 3 are preserved byte-for-byte (ledger
unchanged, before-blocks re-verified unique and after-blocks absent in the fresh
source). Per-record research dates are retained inside the packets where the source
text carries them (UK 2026-10-16, USA 2026-10-01, NPL 2026-10-01, VAT 2026-10-04).

## 1. Structural path-level inclusion / exclusion

**Included — a whitelist of exactly five blind paths per record**
(`renderer.py → pilot_fields`, asserted by build checks and unit tests):

| path | rendered as |
|---|---|
| `blindSummary` | `### ASSESSMENT` |
| `blindSourceSummaries` | `### SOURCE EVIDENCE` (one bullet per item) |
| `blindTangential` | `### SECONDARY / SITUATIONAL FACTORS` |
| `blindLocalsOnly` | `### AFFECTS RESIDENTS MORE THAN VISITORS` |
| `blindOutOfScope` | `### DELIBERATELY NOT COUNTED` |

**Excluded — every other key of the four records, structurally (key whitelist, not
prose filtering):**

| excluded paths | reason |
|---|---|
| `score`, `band`, `rank`, `nationalFrameworkScore` | published map values — no targets, published scores or expected ordering may enter inputs |
| `scoreProvenance`, `rubricVersion`, `ratedBy`, `ratedAt`, `derivedFrom`, `provisionalCalibration` | score provenance and rating metadata |
| `anchorRefs`, `comparisons` | frozen country anchors and pre-made pairwise conclusions naming other jurisdictions with their scores |
| `divisionSpread`, `derivedFrom` | sub-national score aggregates (ADM1 lane) |
| `summary`, `outOfScopeNotes`, `tangentialFactors`, `localsOnly` | named-field duplicates that predate blind review (carry real names/countries) |
| `sources` | source URLs/provenance blocks — their dates and substance are already carried inside `blindSourceSummaries` text |
| `name`, `researchedAt`, `needsIntake` | identity label and record workflow metadata; snapshot provenance lives in `frozen/manifest.json`, not in provider input |

Only ONE country record is read per packet; no other country's data can enter
(the renderer indexes `data[iso]` for the scheduled case only, and the unit test
`test_packet_edits_touch_gbr_only` shows the three untouched packets are byte-equal
to a raw five-field assembly of their own record).

## 2. Proof: no ADM1 (sub-national) values are supplied

1. The renderer's only record access is `{k: rec[k] for k in WHITELIST}` — the
   sub-national division score file is never opened (the renderer source contains
   no reference; asserted by the build self-check and by unit test
   `test_whitelist_no_published_values_no_country_names`).
2. `divisionSpread` / `derivedFrom` aggregates are excluded by the key whitelist.
3. No per-division score value appears in any frozen packet (score values of the
   four cases are asserted absent packet-wide at build, verify and test time).
4. Sub-national *names* appearing in source prose (e.g. "Scotland" inside a case
   caption, US state/province policy tallies) are substantive source facts, not
   score values, and are deliberately retained.

## 3. GBR pilot-only prose edits (evidence-preserving, exact, fail-closed)

The UK blind packet contained explicit third-party numeric index scores/ranks in
two sentences. Both were replaced by literal, count-asserted edits recorded in
`ledger.json` (ids `GBR_index_summary`, `GBR_index_tangential`) — no other packet
and no other sentence is touched.

### Edit 1 — `GBR.blindSummary` (ledger id `GBR_index_summary`)

**Before (verbatim source):**
> Regional rainbow-index rankings show the country falling from 1st in the subregion with an 86% score in 2015 to 9th in 2020 with 66% and concern about a hostile climate on trans rights, then 22nd in 2025 with 45%, the third steepest drop in the subregion.

**After (pilot-only view):**
> Regional rainbow-index rankings show the country falling sharply in the subregion across the 2015, 2020 and 2025 assessments, with concern about a hostile climate on trans rights recorded in 2020 and the decline described as among the steepest drops in the subregion.

* **Removed:** the explicit index rank/score numbers — `1st`, `86% score`, `9th`,
  `66%`, `22nd`, `45%`, and the `third steepest` rank.
* **Preserved (substantive facts):** the rainbow-index is still named and
  attributed as the source of the trajectory; the three assessment years
  (2015/2020/2025); the documented concern about a hostile climate on trans rights
  (2020); the "among the steepest drops in the subregion" characterization.

### Edit 2 — `GBR.blindTangential` (ledger id `GBR_index_tangential`)

**Before (verbatim source):**
> … a regional rainbow-index ranking places it 22nd in the subregion in 2025 with 45%, down from 1st with 86% in 2015, described as the third steepest drop in the subregion from 2024.

**After (pilot-only view):**
> … a regional rainbow-index ranking places it far lower in the subregion in 2025 than in 2015, a decline described as among the steepest drops in the subregion from 2024.

* **Removed:** `22nd`, `45%`, `1st`, `86%` (index values), `third steepest` (rank).
* **Preserved:** the trajectory contrast with neighbouring jurisdictions, the
  markedly lower 2025-vs-2015 standing, the from-2024 steep-drop characterization.

### Deliberately NOT stripped (no broad numeric filtering)

* The 2019/2017 societal-acceptance **poll** figures (`86%`, `77%`) in
  `blindTangential` — separate substantive observations, not index scores/ranks.
* All dates, counts of documented measures, US state/province policy tallies,
  Nepal's curriculum "second in the region" (a source-stated fact, not an index
  score of the country), and every other number in all four packets.
* Qualitative rainbow-index references without numbers (e.g. the 2026
  legal-gender-recognition findings sentence) remain — they are substantive
  sourced assessments, and hiding them would erase facts.
* Verification: the build/verify checks assert the index numbers are absent from
  the frozen GBR packet and that `hostile climate on trans rights`, `steepest`
  and `86% of national respondents` remain; `USA/NPL/VAT` packets are byte-equal
  to their raw five-field assembly (unit-tested).

## 4. Limitations and source dates are not hidden

* Every packet ends with `### DELIBERATELY NOT COUNTED` (the `blindOutOfScope`
  field): unresolved litigation, HTTP 403 retrieval failures, single-sourced
  claims, missing denominators and "enforcement at entry/screening/facilities is
  not documented" all reach the provider verbatim.
* Source dates embedded in `blindSourceSummaries` ("Reporting (Feb 2026) …",
  "Broadcast reporting (19 Jun 2026) …") are retained byte-for-byte.
* The two GBR edits remove only numeric index score/rank tokens; no limitation,
  qualification or date was weakened.

## 5. Known identity leaks — blinding is NOT claimed

No tested `COUNTRY_NAMES` literal ("United States", "USA", "United Kingdom", "Nepal",
"Vatican") appears in packets or labels (unit-tested) — that is the full extent of the
enforced check, not a claim that geographic identity is absent. Identity may still be
inferred, because the evidence itself identifies the jurisdiction: UK case captions ("For Women Scotland v Scottish
Ministers", "Goodwin", "Corbett"), the named decedent "Joelle", "GRC", Nepal's
"Sunil Babu Pant" case, US executive-order detail, Vatican doctrine texts. This is
recorded as a **potential identity leak** in `README.md`. Consequences:

* the neutral-label sentinel tests only **gross arbitrary-label sensitivity**;
  it is not evidence of country blinding;
* a separate named-versus-anonymous information-policy test was deliberately
  **not** mixed into this design (per the independent review).

## 6. Frozen packet hashes

| packet | sha256 | bytes |
|---|---|---|
| `frozen/packets/USA.txt` | `1ba052e91d93ea72…` (rebuilt at 80c573a5: MAP 7 Nov 2026 categories, 19 Mar 2025 arrest) | see manifest |
| `frozen/packets/GBR.txt` | `8290d08753ea7c71…` | see manifest |
| `frozen/packets/NPL.txt` | `2d8bcf42f158273a…` | see manifest |
| `frozen/packets/VAT.txt` | `1800643dd8eb943f…` | see manifest |

Full hashes, byte counts and the ledger sha256 are in `frozen/manifest.json`;
`python3 renderer.py --verify` re-renders every packet from the snapshot and
re-checks every byte.