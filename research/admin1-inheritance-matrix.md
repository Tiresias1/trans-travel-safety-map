# Admin1 framework inheritance matrix (2026-10-05)

**Purpose.** A dossier region (ADM1 record with `dossier:true`) sits inside a parent
country. Every visitor physically under that parent stands under a set of *framework
features* — national documents/passport policy, border/entry/screening, national
criminalisation, national discrimination law, national age/consent rules — regardless
of which region they are in. Region dossiers must carry the applicable part of that
framework explicitly except where the region's own law displaces it ("home rule to the
contrary"). This file records, per parent, (A) which framework features reach every
region, (B) which reach most regions with known exceptions, and (C) known
region-specific divergences. It feeds the `inject_parent_layer` pass and the intake
lanes that write/refresh region dossiers.

The rule of thumb (LANE_SPECS rule 6/7): if the region changes nothing visitor-facing
beyond the framework, its dossier says so and the framework IS the risk layer; if it
adds or subtracts, both the framework and the delta are stated.

## Framework features (the vocabulary)
- `docs`      — national identity/passport documents and their marker policy (what
                the visitor carries and what entry control inspects)
- `border`    — national border/visa/entry rules, airport screening, entry bans
- `crimes`    — national criminalisation (sodomy/expression/propaganda laws) with penalties
- `nondisc`   — national anti-discrimination / equality law + hate-crime provisions
- `care`      — national age-of-consent/medical rules affecting trans visitors
- `facilities`— national rules on single-sex facilities a visitor encounters
- `marriage`  — national marriage/union regime relevant to partner travel
- `police`    — national policing posture toward trans/queer expression on the street

## Parent table

### USA (51 dossier regions)
- A (reaches all 51): `docs` (Jan 2025 EO: documents show birth sex, X marker gone),
  `border` (visa discretion incl. SWS25 sports-visa ban, airport screening),
  `nondisc` floor (Bostock interpretation contested but federal EEO floor exists),
  `facilities` (federal facilities clause of EO 14168)
- B: `marriage` (Obergefell national floor), `crimes` (no federal sodomy law)
- C (region-dependent, never assume): `police`, `facilities` at state level (SB 8
  Texas etc.), state criminal-trespass bathroom laws, state care bans, state
  non-discrimination repeal. Sharia-like divergence: none.

### MYS (16 regions)
- A (all 13 states + FT): `crimes` — every state prohibits "a man posing as a woman"
  under Sharia (max 3 yrs) — this is the national baseline and MUST be restated
- B: `nondisc` (none nationally), `docs`, `border`
- C: Kelantan/Terengganu/Kedah/Perlis (and the other Sharia states) may add stricter
  Islamic-enforcement layers, hudud-adjacent local bylaws; Sabah/Sarawak differ in
  native-custom + separate criminal administration — verify each.

### ESP (19 regions)
- A (all autonomous communities): `nondisc` + `docs` (2023 Trans Law: self-declared
  marker change, national), `crimes` (penal-code reform), `marriage` (national)
- C: regional dependencia/trans laws pre-date or mirror the national; no home rule
  removes the 2023 floor. Catalan/Aragonese regional laws may add.

### DEU (16 regions)
- A: `nondisc` (GG + AGG federal floor), `docs` (TSG/self-id national), `care`,
  `marriage` (national)
- C: Land-level education/police/care-facility rules; no Land can remove the federal
  floor.

### GBR (4 regions)
- A: `docs` (UK passport M/F only; X since 2015 dropped), `border` (UK entry rules),
  `marriage` (national), `crimes` (national)
- B: `facilities` — the single-sex-services rollback (2025 equality guidance) applies
  in England/Wales; differs in Scotland? verify.
- C: devolution — Northern Ireland (education guidance, gender self-id stalled),
  Scotland (GRR devolved), Wales (counseling consent). Each region dossier must name
  its devolved divergence.

### RUS (83 regions)
- A (all): `docs`, `care` (2023 ban on transition + care), `crimes` (propaganda/
  extremist-movement designation), `police` — the federal regime reaches every region
- C: Chechnya/Dagestan/Ingushetia add torture/abduction/extrajudicial risk beyond the
  federal baseline; Tatarstan etc. aligned with federal. Verify each.

### NGA (37 regions)
- A (all): `crimes` (SSMPA 14 yrs all visitors) — MUST restate per region
- B: `crimes` shariah in 12 northern states (adds caning/stoning-class penalties)
- C: northern Sharia states (Zamfara, Kano, Borno, Sokoto...) add strict Islamic law;
  southern states mostly federal SSMPA only; Lagos urban-globalised.

### IND (36 regions)
- A: `nondisc` (trans bill protections, constitutional reading), `crimes`
  (SS decriminalised 2018 but s.377 residual), `docs` (trans certificate scheme)
- C: state-level hijra/trans welfare boards differ; Kerala/Karnataka stronger;
  BJP-governed states may enforce more conservatively. Verify each.

### IDN (34 regions)
- A: `crimes`-ish (national security decree, anti-LGBT stance), `police` — federal
  stance reaches all; Aceh province imposes Sharia criminal code independently
- C: Aceh (Sharia enforcement), Papua (indigenous), Jakarta (cosmopolitan).

### CAN (13 regions)
- A: `nondisc` (CHRA + Criminal Code hate-crime), `docs`, `marriage`, `care`, `police`
- C: Quebec civil-code interplay, Alberta care-policy rollback (2024-25 craft), NB
  education policy — verify each.

### AUS (9 regions)
- A: `nondisc` (federal Sex Discrimination Act 1984), `docs`, `marriage`
- C: state-level exemptions (religion carve-outs), NSW/Qld bail/robbery residual law,
  WA/Vic identity docs differ. Verify.

### FRA (13) / ITA (5) / POL (16) / ZAF (9) / PER (26) / CHL (16) / COL (33) /
### ARG (23) / BRA (27) / MEX (32) / PHL (17) / KOR (17) / TUR (81)
- These are *unitary* or largely-uniform countries: the national framework in the
  parent dossier's summary reaches every region; region dossiers should state it once
  ("visitor stands under the national framework: ...") and delta on local
  enforcement/culture. KOR/MEX/PHL/TUR have meaningful regional variation — the
  region-level pairwise already captured it (MEX drug/state risk, TUR regional
  conservatism, PHL regional violence, KOR Seoul vs provinces).

## Operating rule for dossiers
Every dossier region's summary should contain a sentence of the form:
  "This region stands under the national framework: [framework items relevant to this
  parent from column A, plus any B items applicable here]; [region-specific delta]."
If the region's own law displaces an A item (rare; e.g. a region with its own
criminal code), say so explicitly — that is the home-rule exception, and it is exactly
what the pairwise rater needs to see.

## What this matrix does NOT decide
Which framework items are actually in force in __this__ parent today — that comes from
the parent dossier (data/countries.json), which is authoritative and re-paired. The
matrix only records the inheritance structure; the `inject_parent_layer` pass reads
the parent's live summary for the factual content.