# Scotland dossier-parity audit (uk-nations-fix-20261124 follow-up)

**Question.** In the UK nations fix pilot all models rated Scotland highest
(draw mean 0.519, final 0.506, +0.068 above the GBR parent 0.438) while
England/NI/Wales converged to the parent. Scotland's summary is much longer
(3,724 chars vs England 2,210 / NI 2,490 / Wales 1,511). Is Scotland genuinely
safer (devolved protections) or does its dossier over-document protections /
under-document restrictions versus the other three nations (dossier-asymmetry
bias)?

**Verdict (summary). (c) Mixed — genuine divergence, inflated by asymmetry.
Do NOT sync Scotland's 0.506 pilot final as-is; repair dossiers and re-rate.**
Scotland's Hate Crime and Public Order (Scotland) Act 2021 naming gender
identity as a protected characteristic plus the 2009 sentencing enhancement
are real, operative, Scotland-only criminal-law protections (criminal law is
devolved) and they justify *some* upward divergence. But the size of the
observed gap is not supported by balanced dossiers: (1) England and Wales
document **no** operative hate-crime statute naming transgender people, so
Scotland's protection looks unique when the dossiers never show the
counterparts; (2) Scotland's division dossier documents **nothing operative**
about single-sex services for a visitor — the everyday-visitor restriction
England leads with — even though Scotland is the litigation's origin
jurisdiction; (3) Scotland's lead summary carries ~1.7× England's and ~2.7×
Wales's sentence count. Repair list in §6; re-rate after repair. Estimated
split: roughly half genuine legal divergence, half asymmetry (see §5).

No provider calls were made; no data files were written. All comparisons are
direct text comparison of rendered dossiers.

---

## 1. Method and pre-flight verification

- Rendered all four nation dossiers with the current harness,
  `harness.render_admin1_dossier(record_id, "GBR", admin1, countries)`
  (parent framework + blind division fields, neutralized in renderer), plus
  the GBR country reference `harness.render_country_dossier("GBR", …,
  include_regimes=True)`.
- **Single-render: confirmed.** All four nations have a non-empty
  `blindSummary`, so the harness dossier is the one rendering and
  `build_dossier` returns the base (no local-evidence append).
- **Neutralized: confirmed.** `find_identity_leaks(...) == []` for every
  nation dossier (and for the GBR country dossier); `assert_user_text_clean`
  passed on every nation dossier. Leak-gate result is `[]` as expected.
- **Blind out-of-scope rendered:** the `DELIBERATELY NOT COUNTED` section
  (from `blindOutOfScope`) is present in all four nation dossiers.
- **Parent framework is byte-identical across the four nation dossiers**
  (12,549 chars each, verified by string equality). Every UK-level fact in
  the parent framework — the For Women Scotland ruling, the August 2026
  equality-body code, the NHS ward/blocker/hormone material, the transport-
  police and 25 June 2025 police search guidance, the prison-custody
  litigation — reaches all four dossiers equally. **The entire Scotland
  question is therefore about the division-level sections only**
  (`### DIVISION EVIDENCE` onward), which is what this audit codes.
- Claim coding: every sentence of each nation's `blindSummary` +
  `blindTangential` (the visitor-facing division sections) was coded
  **P** (protective: makes a trans visitor safer), **R** (restrictive:
  restricts/exposes a trans visitor), **M** (mixed: protective and
  restrictive content in one sentence), or **N** (neutral/contextual/
  methodological). `blindSourceSummaries`, `blindLocalsOnly` and
  `blindOutOfScope` were coded separately for repetition and placement
  effects (§3.3). Quotes below are verbatim from the rendered (neutralized)
  dossiers.

A note on the task's "protective-detail words (11 vs 4/3/1)": I could not
reproduce that metric under any lexical definition I tried (`protect*`,
`protect*|rights`, `allow|support|friendly|enabl*`, on `blindSummary`,
unblinded `summary`, or all blind division fields). Under `protect*` counts
England actually leads (6 vs Scotland 3 across all division fields) because
England's ruling text repeatedly invokes "protection against
discrimination." The 11/4/3/1 ordering is therefore not a lexical effect; the
transparent replacement is the sentence-level coding in §3, which does show
Scotland with the most protective *statute detail* (but also the most
restrictive detail).

A correction to the pilot framing: **six**, not seven, models rated
Scotland in OK calls (luna ×2, muse ×2, haiku, deepseek, mimo, qwen; glm
never rated Scotland). Scotland was nonetheless the higher-rated dossier in
**all 8** OK calls it appeared in; mean Scotland rating 0.51875 (n=8), final
0.5057 after alpha updates from seed 0.4527. The unanimity claim holds for
every model that saw Scotland; the "all seven" wording overstates coverage
by one model.

---

## 2. Per-nation claim inventories (division evidence)

### 2.1 Scotland — protective claims (P)

| # | Claim | Evidence (rendered dossier) |
|---|---|---|
| S-P1 | Hate-crime statute names gender identity, in force | "Hate crime in this division is governed by the hate crime and public order act of 2021, passed by the legislature of this division in March 2021 by 82 votes to 32, given royal assent a month later and brought into force on 1 April 2024." |
| S-P2 | Gender identity listed as protected characteristic | "It lists gender identity as a protected characteristic." |
| S-P3 | Older sentencing enhancement (2009) | "Earlier legislation of this division enacted in 2009 provides penalty enhancements where an offence is motivated by the victim's gender identity." |
| S-P4 | Search accommodation on request | "Where a person's lived gender differs from their sex at birth, efforts will be made to provide an officer of that lived gender on request." |
| S-P5 | Former prison placement by gender identity (superseded — see §2.1 R) | "The guidance had allowed some trans prisoners to be held in establishments matching their gender identity rather than their sex at birth." |
| S-P6 | (Out-of-scope, discounted) X-marker announcement 2018 | "The devolved government's 2018 announcement of an 'X' sex descriptor on identity documents and a minimum transition age of 16 is recorded as an announcement; the inventory does not record whether either was implemented…" |

Scotland also carries two levels of hate-crime statistics no other nation
has: prosecution charges (7,115 total, trans aggravation 104, up 21% from
86; sexual-orientation aggravation 2,062) and police-recorded crimes (8,538;
top per-10,000 rates ~32.25; 62% race aggravator). Both are raw counts with
no trans-specific per-capita rate — correctly caveated in the dossier.

### 2.2 Scotland — restrictive claims (R)

| # | Claim | Evidence |
|---|---|---|
| S-R1 | GRR reform blocked; reformed procedure NOT in force | "The government of this country blocked the bill under section 35 of this country's devolution legislation of 1998 while it awaited royal assent, the first time that power has been used to overturn legislation of this division, so the reformed procedure the legislature legislated for is not in force in this division." |
| S-R2 | Searches on biological-sex basis (custody + stop-and-search) | "The police service published interim guidance on 25 June 2025 providing that searches involving the removal of more than a jacket, gloves, headgear or footwear are conducted on the basis of biological sex, in both custody and stop-and-search contexts." |
| S-R3 | Prison trans-custody guidance struck down 19 June 2026 | "On 19 June 2026, in a challenge to ministers of this division, a judge of this division's highest civil court struck down the prison service's non-statutory guidance on trans custody as unlawful, holding that sex segregation in prisons must rest on a lawful basis." |

So Scotland does **not** hide its restrictions: it documents the s35 block,
the search rule, and the prison ruling, each with dates and legal basis, and
repeats them in `blindLocalsOnly`. What it omits is the *everyday
single-sex-services* consequence (§4.1).

### 2.3 England — protective claims (P)

Only one genuinely protective division sentence:

| # | Claim | Evidence |
|---|---|---|
| E-P1 | Senior judge: ruling should not reduce discrimination protection | "The senior judge giving the ruling stated that it should not be read as reducing the statute's protection against discrimination for transgender people." |

A second protective-leaning item is argument, not holding (M): "government
lawyers said a blanket rule housing trans prisoners by sex at birth would
breach human rights and create an unacceptable suicide risk" (5 Feb 2026
hearing; outcome undocumented). England's hate-crime content is statistics
only: 115,990 police-recorded hate crimes (year ending March 2025), trans
strand "fell 11%", survey estimate ~176,000. **No English hate-crime statute,
no protected-characteristic listing, no sentencing-enhancement law is named
anywhere in England's division evidence.**

### 2.4 England — restrictive claims (R)

| # | Claim | Evidence |
|---|---|---|
| E-R1 | For Women Scotland: biological-sex definitions | "'Woman' and 'sex' in the equality statute mean biological woman and biological sex, so a gender recognition certificate does not entitle a trans woman to the statute's sex-based protections." |
| E-R2 | EHRC code: birth-certificate requests | "The code advises that services and businesses may ask a person for a birth certificate where there is 'genuine concern' about biological sex…" |
| E-R3 | EHRC code: sport exclusion | "…and that trans people may be excluded from single-sex sport 'when necessary' for safety." |
| E-R4 | Operative-visitor framing | "This is the operative guidance a trans visitor encounters at venues, transport and services." |
| E-R5 | Custody by biological sex; no Article 8 right | "Prison and custody decisions in this division are governed by the same country-wide ruling, under which Article 8 of the regional human-rights convention confers no automatic right to accommodation with the opposite biological sex." |

England's division dossier is ~80% restrictive by word count (§3) and repeats
this restrictive core four times (summary, 5 source summaries, tangential,
locals-only). England also omits any mention of the Gender Recognition Act
process, the GRR reform bill, or s35 from its division evidence (covered only
in the shared parent framework).

### 2.5 Northern Ireland — protective / restrictive claims

- **P (NI-P1, genuine devolved protection):** "A May 2021 judgment of this
  division's courts made a binding ruling in the region that gender dysphoria
  based on an individual's mental dynamic is no longer legally required…" —
  binding, NI-only, the only ruling of its kind in the country
  (tangential). This is the strongest *medical-criteria* protection in any
  of the four dossiers, and only NI documents it.
- **P (NI-P2, historical):** withdrawn 2019 guidance "had recommended that
  trans pupils be allowed to use changing rooms matching their gender
  identity" (past tense — replaced by the withdrawal below).
- **P (locals-only):** 1999 regulations protect people undergoing gender
  reassignment in employment/vocational training.
- **R (NI-R1):** "In December 2025 other parties in the executive blocked the
  justice minister's plan to add transgender people as a protected
  characteristic in this division's new hate-crime legislation." Tangential:
  "this division's hate-crime statute may proceed without gender identity as
  a protected characteristic." — NI thus documents the *negative* counterpart
  of Scotland's S-P1/S-P2.
- **R (NI-R2):** "In September 2025 guidance supporting transgender pupils
  was withdrawn from the regional education authority's website after the
  education minister requested its removal…" (removing gender-identity
  changing-room access).
- **R (uncertainty):** equality legislation separate; ruling impact "still
  assessing"; single-sex position "should be treated as unsettled."
- Source-only signals: pipe-bomb attack on a trans woman's home (treated as
  hate crime), ~290 anti-LGB&T incidents/year (2013–17), funding-uplift
  defence. **No policing/custody content at all** (out-of-scope admits "No
  policing, custody, hate-crime prosecution or trans-specific violence data
  specific to the state/province appears in these sources").

### 2.6 Wales — protective / restrictive claims

- **P (WA-P1):** Action Plan aim: "making the state/province the most
  LGBTQ+ friendly jurisdiction in the region" (Feb 2023).
- **P (WA-P2):** conversion-practices ban: commitment + December 2022
  working group + May 2024 banning document.
- **P (WA-P3):** "The first gender identity clinic in the state/province
  opened in September 2019, ending the default referral of adults outside
  the state/province."
- **P (WA-P4, source/locals-only):** statutory school guidance obliging
  schools to challenge bullying on grounds of sex, gender reassignment and
  sexual orientation; overview source: "discrimination protections covering
  sexual orientation and gender identity."
- **R (WA-R1, structural):** "Devolved policy does not extend to legal gender
  recognition, equality legislation or prisons." + "set by the national
  framework rather than by the state/province's ministers."
- **R (WA-R2):** neighbouring GRR reform blocked (source + tangential: "the
  limit of what a devolved administration can legislate on gender
  recognition"); children's gender service: commissioners "had no plans to
  develop" one (locals-only).
- **Wales has zero hate-crime content** — no statute, no statistics, no
  incidents — in any division section.

---

## 3. Quantification

### 3.1 Size

| Nation | `summary` (unblinded) chars | `blindSummary` chars / words | Sents in blindSummary | Rendered dossier chars | Division section chars / words | Source items / chars |
|---|---|---|---|---|---|---|
| Scotland | 3,724 | 3,751 / 588 | 21 | 21,369 | 8,799 / 1,359 | 2 / 525 |
| England | 2,210 | 2,385 / 347 | 12 | 20,858 | 8,288 / 1,246 | 5 / 2,606 |
| Northern Ireland | 2,490 | 2,507 / 370 | 15 | 19,159 | 6,589 / 998 | 5 / 1,428 |
| Wales | 1,511 | 1,664 / 221 | 10 | 17,951 | 5,381 / 786 | 4 / 1,597 |

Parent framework (identical, all four): 12,549 chars. Rendered totals
converge (Scotland 21.4k vs England 20.9k) only because England's source
block (5 items, 2,606 chars) compensates for its shorter summary. The
*lead* division text raters read (`DIVISION EVIDENCE` = `blindSummary`)
does not converge: Scotland 588 words vs England 347, NI 370, Wales 221.
Words per sentence are similar (Scotland 28.0, England 28.9, NI 24.7,
Wales 22.1) — this is a sentence-count asymmetry (≈1.75× England, ≈2.7×
Wales), not a density asymmetry.

### 3.2 Claim-type coding (`blindSummary` + `blindTangential`, visitor-facing)

| Nation | Sents (words) | P sents (words) | R sents (words) | M sents (words) | N sents (words) |
|---|---|---|---|---|---|
| Scotland | 29 (791) | 5 (122) | 4 (175) | 2 (85) | 18 (409) |
| England | 16 (480) | 1 (23) | 4 (114) | 1 (55) | 10 (288) |
| Northern Ireland | 18 (466) | 4 (125) | 3 (86) | 0 (0) | 11 (255) |
| Wales | 14 (298) | 4 (105) | 4 (83) | 0 (0) | 6 (110) |

Reading: Scotland documents **both** sides most fully — highest protective
words (122, tied with NI's 125) *and* highest restrictive words (175). Its
rating advantage cannot be explained by hiding restrictions; it comes from
*which* protective facts it documents (operative statute with in-force date)
versus England's single judicial aside (23 words). England's P:R word ratio
is 1:5; Scotland's is 1:1.4.

### 3.3 Repetition and placement

- Scotland repeats its protective statute 4× (summary S-P1–S-P3, both source
  items, tangential, locals-only) and its restrictions 3× (summary,
  locals-only, parent framework). The 25 June 2025 search guidance appears
  **three times** in one rendered dossier (parent framework, division
  summary, locals-only).
- England repeats its restrictive core 4× (summary, 5 sources, tangential,
  locals-only) — symmetric repetition, opposite polarity.
- Misplaced facts: Scotland's own under-18 clinic puberty-blocker pause
  (April 2024, post-review) sits in `DELIBERATELY NOT COUNTED` — the
  discounted section — while the parent framework attributes the blocker
  pause to the national/England record. A Scotland-specific health fact is
  thus simultaneously buried and exported. Wales's "no children's service
  planned" sits in locals-only/sources, correctly placed as
  residents-relevant.
- Scotland's source block (2 items) is the thinnest despite the longest
  summary; England's (5 items) is the thickest. Source-block asymmetry
  partially offsets summary asymmetry in rendered length — but raters weigh
  the `DIVISION EVIDENCE` lead more heavily than source bullets.

---

## 4. Coverage matrix (division sections; parent framework is shared)

Legend: ● present with operative detail · ◐ present as pointer/deferral/
uncertainty only · ○ absent · ✕ present-but-discounted (out-of-scope/
locals-only placement).

| Checklist node | Scotland | England | NI | Wales |
|---|---|---|---|---|
| For Women Scotland ruling impact on single-sex services (toilets/changing/sport for a visitor) | ○ (division: silent; parent only: code in force 2026 + "one region… still assessing") | ● (E-R1–E-R4: definition + EHRC birth-cert/sport + "operative guidance") | ◐ ("unsettled", "still assessing" — no operative content) | ◐ (defers to national framework; "cannot alter") |
| GRR 2004 (process, medical criteria) | ◐ (proceeds under 2004 Act; no medical-criteria statement) | ○ (never mentions GRR in division evidence) | ● (2004 statute + May 2021 dysphoria-removal ruling) | ○ (defers; no GRR content) |
| GRR reform + s35 block | ● (bill 86–39, s35 block, first use, not in force) | ○ (absent from division evidence) | ◐ (records neighbour's block in tangential only) | ◐ (records neighbour's block in source + tangential) |
| EHRC / equality-body guidance (operative) | ○ in division (parent: Aug 2026 code only; out-of-scope pointer says carried at parent level) | ● (20 May 2025 code: genuine-concern + sport) | ○ (separate legislation noted; no code content) | ○ (no code content; defers nationally) |
| NHS / health devolution | ✕ (own clinic blocker pause in out-of-scope; ward position unstated) | ○ in division (parent carries NHS England material) | ◐ (funding uplift, source only) | ● (2019 clinic; no children's service) |
| Police / custody (searches, prisons) | ● (25 June 2025 search guidance + 19 June 2026 prison ruling, both with operative terms) | ● (custody by biological sex + Art 8; FOI search policy irretrievable — out-of-scope) | ○ (none; out-of-scope admits gap) | ○ (defers to national framework) |
| Hate-crime statute naming gender identity | ● (2021 Act + 2009 enhancement, votes, in-force date) | ○ (statistics only; no statute) | ●-negative (blocked inclusion, Dec 2025) | ○ (no hate-crime content at all) |
| Hate-crime statistics (trans-specific, with denominator) | ◐ (two series, exact counts, no trans per-capita rate — caveated) | ◐ (% change only, no absolute trans count — caveated) | ○ (raw ~100, caveated; + 290/yr source) | ○ (none) |
| Schools / education guidance | ○ (silent) | ○ (silent) | ● (withdrawal + prior inclusive guidance) | ● (statutory anti-bullying guidance) |
| Conversion-practice ban | ○ (silent) | ○ (silent) | ○ (silent) | ● (commitment + working group + 2024 document) |
| X marker / non-binary documents | ✕ (2018 announcement, unresolved, out-of-scope) | ○ (silent) | ○ (silent) | ○ (silent) |
| Same-sex marriage / civil partnerships (LGBT context) | ● (2014, votes, religious opt-out) | ○ (silent in division) | ● (2020 + civil partnerships, procedural detail) | ◐ (overview source only) |

**"Does EVERY nation's dossier address For Women Scotland?"** At the
*dossier* level (including the shared parent framework): yes — all four
render the ruling, the August 2026 code, and the "still assessing" region
caveat. At the *division-evidence* level, which is where nations differ:
England addresses it operatively; NI addresses it as uncertainty; Wales
defers; **Scotland — the origin jurisdiction — does not state any operative
single-sex-services consequence for a visitor in Scotland at all.** The
parent framework's "one region, on different equality legislation, is still
assessing the top-court ruling's impact" is the only Scotland-applicable
services statement, and it leaves the visitor to guess whether the EHRC
code's genuine-concern/sport provisions apply in Scotland. (In legal
reality the Equality Act 2010 and the EHRC apply in Scotland as well as
England; the dossier's "different equality legislation" framing — Scotland
has its own Equality Act provisions incorporated via the Scotland Act
regime — is exactly why the division dossier needed one operative sentence
and doesn't have it.)

---

## 5. Asymmetry analysis

### 5.1 Scotland's protective claims vs counterparts

- **S-P1/S-P2/S-P3 (Hate Crime Act 2021 + 2009 enhancement): NO counterpart
  in any other nation's dossier.** England's division evidence names no
  hate-crime statute; Wales names none; NI documents only its *blocked*
  inclusion. This is the single largest driver of the gap. It is *genuine*
  in that Scotland's statute is real and Scotland-only in form (devolved
  criminal law; the 2021 Act lists gender identity among its protected
  characteristics and has been in force since 1 April 2024). But the
  dossiers never show England/Wales's own operative aggravation law, so
  raters see a protection that exists in Scotland and a void elsewhere.
  The void is a documentation failure, not evidence of absence. Detail
  inflation compounds it: vote counts (82–32), royal-assent timing, and two
  statistical series (~6 sentences of protective context) establish
  thoroughness *about* the protection, which raters plausibly read as
  strength *of* the protection. No other nation's protective statute gets
  this treatment because no other nation's statute is documented.
- **S-P4 (search accommodation on request): partial counterpart.** England
  has no search-accommodation counterpart in division evidence (its
  equivalent police policy "could not be retrieved"); NI/Wales have none.
  Genuine Scotland-specific guidance, but also a one-sided-documentation
  artefact.
- **S-P5 (former prison placement):** Scotland documents a protection that
  no longer exists (struck down June 2026) in the same detail as its live
  protections. Raters may partially credit it. England's equivalent former
  position is documented only as argument. Net: small pro-Scotland detail
  asymmetry.
- **S-P6 (X marker):** properly discounted in out-of-scope; no rating
  effect expected. Correct handling — and a model for how S-P1's caveats
  are also handled.

### 5.2 Scotland's restrictive claims vs counterparts (under-documentation?)

Scotland documents its restrictions well on custody/police (S-R1–S-R3,
175 words — the most R words of any nation). It under-documents on:

1. **Single-sex services (the England comparison).** England leads its
   dossier with E-R1–E-R4 (biological definition + birth-certificate
   requests + sport exclusion + operative-visitor framing). Scotland's
   dossier contains **zero** division-level sentences about toilets,
   changing rooms, sport, or wards for a visitor in Scotland. A rater
   comparing "what happens to me at a venue/transport/service in this
   nation" gets a complete answer from England's dossier and no answer
   from Scotland's (beyond the shared parent text). On the dimension most
   likely to bite a visitor day-to-day, Scotland's dossier is the vaguest
   of the four. **This is Scotland's clearest under-documentation of a
   restriction.**
2. **GRC medical criteria.** NI documents that gender dysphoria based on
   mental dynamic is no longer legally required (binding, NI-only).
   Scotland's dossier never states Scotland's criteria (the GRR 2004
   diagnosis requirement still applies in Scotland; the blocked reform
   would have changed the process, not the diagnosis rule — the dossier
   doesn't say). Raters cannot see that NI's medical-criteria position is
   more protective than Scotland's.
3. **Health devolution.** Scotland's own clinic pause is buried in
   out-of-scope (§3.3); its ward position is never stated. Wales documents
   both clinic history and the children's-service gap. Scotland's
   residents-level health restrictions are thus discounted by placement.
4. **Schools.** NI and Wales document education guidance (withdrawal /
   statutory anti-bullying); Scotland and England are silent. Scotland's
   silence is a gap, though no Scotland school-guidance fact appears to
   have been researched (this is a research-coverage gap, not necessarily
   a dossier-writing failure).

### 5.3 Reverse asymmetries (other nations missing UK-level facts)

- **England omits s35/GRR-reform context entirely** from division evidence,
  while Scotland leads with it and Wales/NI record it in tangential/source.
  England's raters never learn that devolved gender-recognition reform can
  be blocked at UK level — a fact that contextualizes every nation's GRR
  position.
- **Wales omits hate-crime law and statistics entirely**; NI omits
  policing/custody entirely. Their dossiers' shortness (Wales 221-word
  summary, 10 sentences) reads as "nothing to report" rather than "nothing
  found" — the out-of-scope sections do admit the gaps, but a 10-sentence
  summary covering 4 protective + 1 restrictive claim cannot compete for
  rater attention with Scotland's 21-sentence summary.
- **EHRC applicability:** only England states the operative code content.
  Wales (where the EHRC does apply) never mentions it in division evidence;
  NI (where it does not — NI has its own equality commission) is correctly
  silent but never says so. Scotland's position is the most consequential
  silence (§4, §5.2.1).

### 5.4 Proportions

- **Genuine divergence (supported):** Scotland is the only nation whose
  dossier documents an operative devolved hate-crime statute naming gender
  identity with an in-force date; NI's dysphoria ruling is likewise genuine
  and Scotland-specific criminal-law devolution (police/prisons) is real.
  A Scotland premium over the parent is *justified in direction*.
- **Asymmetry-driven (inflation):** the +0.068 magnitude is inflated by
  (a) missing hate-crime counterparts in England/Wales (makes Scotland's
  protection look unique), (b) missing single-sex-services restrictions in
  Scotland (softens its restrictive side on the highest-frequency visitor
  encounters), (c) missing GRC medical-criteria comparison (hides NI's
  advantage), (d) summary length/sentence asymmetry (1.7–2.7×) and
  4× repetition of the protective statute. Roughly: **half the observed
  premium is genuine, half is dossier asymmetry.** The pilot final 0.506
  should not be synced; the direction (Scotland highest) would likely
  survive repair, the magnitude would likely shrink toward the other
  nations' +0.01–0.02 range.

---

## 6. Recommended repairs (then re-rate; do not sync 0.506)

1. **Add to Scotland (division evidence, visitor-facing):** 2–3 sentences
   stating the operative single-sex-services position for a visitor in
   Scotland (whether/how the August 2026 equality-body code, birth-certificate
   "genuine concern" requests, and sport exclusions apply in Scotland;
   toilets/changing-room position; hospital ward position). Source it;
   if the position is genuinely unsettled, say so with the same explicitness
   NI uses ("unsettled") rather than silence. *This is the single most
   important repair.*
2. **Add to Scotland:** one sentence on GRC medical criteria (gender-
   dysphoria diagnosis requirement under the 2004 Act; no NI-style removal
   ruling in Scotland). Add the same sentence, with NI's ruling, to the
   other three nations' dossiers for claim parity (NI already has it).
3. **Add to England and Wales:** the operative hate-crime aggravation law
   naming transgender identity (statute, protected characteristic, in-force/
   sentencing position) with the same granularity Scotland uses (statute +
   characteristic + date), or an explicit sourced statement of its absence
   in the form NI uses ("may proceed without gender identity as a protected
   characteristic"). **Add to NI:** the equivalent carried-forward position
   (the 2019 Justice Act aggravation position) so its blocked amendment has
   a baseline. Without this, Scotland's S-P1 remains a one-sided
   comparison.
4. **Add to England:** s35/GRR-reform context (1–2 sentences: reform bill
   passed, blocked under s35, reformed procedure not in force; devolved
   competence limits). Add to Wales/NI division-level EHRC-applicability
   sentences (applies / does not apply, one sentence each).
5. **Move Scotland's clinic puberty-blocker pause** out of
   `DELIBERATELY NOT COUNTED` into division evidence or locals-only with an
   explicit visitor-relevance note (minors' prescribing: residents-only,
   but state it in the right section). Add one sentence on Scotland's
   hospital ward position (see #1).
6. **Add to NI:** policing/custody position or keep the explicit gap
   admission (currently in out-of-scope — acceptable, but say it in the
   summary lead, not only in the discounted section). **Add to Wales:**
   hate-crime position (statute + any trans-specific statistics or an
   explicit "no trans-specific series published" statement).
7. **Trim Scotland (optional, low priority):** vote counts and royal-assent
   detail (82–32, 86–39) add no visitor-relevant content beyond "passed /
   blocked"; the second hate-crime statistical series can be cond
...[truncated 9113 chars]