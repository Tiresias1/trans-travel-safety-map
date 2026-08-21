# Research Progress Tracker

Source of truth for what has been researched. A country is ☑ when its research note
exists at `research/countries/<ISO3>.md` AND its entry (summary, score, sources,
researchedAt) is in `data/countries.json`. Anchors are FROZEN — see anchors.md.

## Phase / Status
- [x] Phase 0: scaffolding + deploy pipeline (site works end-to-end)
- [x] Phase 1: boundaries finalised (de jure patches verified; HKG/MAC/PRI promoted)
- [x] Phase 2: anchor calibration (15 anchors) — frozen in research/anchors.md
- [ ] Phase 3: all countries (~180 remaining — batches below)
- [ ] Phase 4: ADM1 tiers
- [ ] Phase 5: frontend completion (mostly done; mobile QA + perf pass pending)
- [ ] Phase 6: polish & ship (README done; CI validation pending)

## Calibration anchors (DONE 2026-08-21)
☑ MLT 0.94 ☑ ISL 0.95 ☑ ESP 0.90 ☑ NLD 0.88 ☑ DEU 0.85 ☑ JPN 0.82 ☑ THA 0.77
☑ GBR 0.74 ☑ BRA 0.55 ☑ USA 0.52 ☑ MEX 0.50 ☑ RUS 0.12 ☑ BRN 0.07 ☑ SAU 0.05
☑ AFG 0.02

## Countries (Phase 3) — suggested batches (mark ☑ with score when done)
Batch 1 — Western/Central Europe: ☐ PRT ☐ IRL ☐ BEL ☐ FRA ☐ CHE ☐ AUT ☐ ITA
☐ LUX ☐ NLD-done-as-anchor etc.
Batch 2 — Nordics/Baltics/East EU: ☐ DNK ☐ NOR ☐ SWE ☐ FIN ☐ EST ☐ LVA ☐ LTU
☐ POL ☐ CZE ☐ SVK ☐ HUN ☐ ROU ☐ BGR ☐ GRC ☐ HRV ☐ SVN ☐ SRB ☐ XKX ☐ BIH ☐ MKD
☐ ALB ☐ MDA ☐ UKR ☐ BLR ☐ CYP
Batch 3 — Americas: ☐ CAN ☐ ARG ☐ CHL ☐ URY ☐ CUB ☐ DOM ☐ CRI ☐ PAN ☐ GTM
☐ HND ☐ SLV ☐ NIC ☐ JAM ☐ TTO ☐ BHS ☐ COL ☐ PER ☐ ECU ☐ BOL ☐ PRY ☐ VEN
☐ GUY ☐ SUR ☐ BLZ (+ territories as needed)
Batch 4 — East/SE Asia & Oceania: ☐ TWN ☐ KOR ☑ JPN-anchor ☐ CHN ☐ HKG ☐ MAC
☐ MNG ☐ PRK ☐ VNM ☐ LAO ☐ KHM ☐ MMR ☐ MYS ☐ SGP ☐ IDN ☐ PHL ☐ TLS ☐ BRN-anchor
☐ PAK ☐ BGD ☐ LKA ☐ NPL ☐ BTN ☐ MDV ☐ AUS ☐ NZL ☐ FJI ☐ PNG (+ Pacific)
Batch 5 — South/Central Asia & Middle East: ☐ IND ☐ IRN ☐ IRQ ☐ TUR ☐ ISR
☐ PSE ☐ JOR ☐ LBN ☐ SYR ☐ KWT ☐ QAT ☐ BHR ☐ OMN ☐ YEM ☐ ARE ☐ AFG-anchor
☐ SAU-anchor ☐ KAZ ☐ UZB ☐ TKM ☐ KGZ ☐ TJK ☐ ARM ☐ AZE ☐ GEO
Batch 6 — Africa: ☐ ZAF ☐ NAM ☐ BWA ☐ ZWE ☐ ZMB ☐ MWI ☐ MOZ ☐ TZA ☐ KEN
☐ UGA ☐ RWA ☐ BDI ☐ ETH ☐ ERI ☐ SOM ☐ SDN ☐ SSD ☐ DJI ☐ EGY ☐ LBY ☐ TUN
☐ DZA ☐ MAR ☐ ESH ☐ MRT ☐ MLI ☐ NER ☐ TCD ☐ SEN ☐ GMB ☐ GNB ☐ GIN ☐ SLE
☐ LBR ☐ CIV ☐ GHA ☐ TGO ☐ BEN ☐ NGA ☐ CMR ☐ CAF ☐ GAB ☐ COG ☐ COD ☐ AGO
☐ ZWE etc. (+ island states)

## Difficulty assessment (honest, for planning) — 2026-08-21
Overall: remaining work is almost all research VOLUME, not hard engineering. ~800-1000
tool calls total across Phase 3 + 4; spans many sessions; batch several countries per turn.

- Phase 6 (ship): EASY — CI schema workflow + GitHub Pages `git push`; site already static/self-contained.
- Phase 5 (frontend): EASY — ~90% done; 360px mobile QA + perf check + minor polish.
- Phase 3 (~180 countries): mostly EASY-MEDIUM per country; tail of data-poor microstates = HARD (scarcity, not complexity).
  * Easy: ~60-80 (W Europe, Nordics, CAN/AUS/NZ, URY/ARG/CHL/CRI, TWN/KOR/SGP) — ~3-4 calls each.
  * Medium: ~50-60 (E Europe/Balkans, rest of LatAm, SE Asia, S Asia, open Middle East, S/E Africa) — ~4-6 calls.
  * Medium-Hard: ~30-40 (IRN, UGA death-penalty, N Nigeria sharia, MRT, YEM, SYR, IRQ, Central Asia, Gulf) — legally clear from HRW/Cairo52/ILGA, needs follow-ups.
  * Hard (source scarcity): ~10-15 microstates (Pacific, Caribbean, San Marino/Andorra/Monaco/Liechtenstein, tiny African states, PRK) — inference-based + low-confidence caveat.
  Meta-risk: consistency drift over 180 entries → mitigated by anchor comparison rule + final consistency pass.
- Phase 4 (ADM1 ~3,245 units): BIMODAL — the hard part is small.
  * EASY bulk: ~3,000 Tier-C inherited via a generator script (no research; build_data ranks pass).
  * Medium-Hard: ~15 Tier-A countries. USA EASY-M (Erin Reed map = skeleton). CAN/AUS/UK/DEU/ESP/JPN/ARG Medium. IND/NGA/IDN/RUS-Caucasus/SAU/ARE HARD (true subnational legal divergence, thin English sources).

## ADM1 (Phase 4) — tier assignments from country notes
Tier A confirmed so far: USA (state laws vary criminal↔protective — Erin Reed map
July 2026 is the core source), MEX (CDMX 0.62-ish vs Tabasco low), DEU (eastern
Länder lower), RUS (North Caucasus group, Tier B).
Tier B groups: RUS-North-Caucasus; consider IND/NIR states, NGA sharia states,
IDN Aceh.
Tier C: inherit with disclosure line (default for countries with no variance notes).
