# Claim-level extraction — 39 archived US country-level encounter ratings

Source (read-only): `research/experiments/country-calibration-audit/usa-archived.json` (39 rows),
orientation cross-checked against `data/measurement_logs/redo_c4.jsonl.gz` (3,600 lines; only the 7
rows needed for orientation were opened). Orientation warning taken from
`research/experiments/country-calibration-audit/HANDOFF.md`. No repository files were modified; no
model calls were made; the 29.5MB session file was not read. This report only extracts, maps and
classifies claims — it does not judge any score and proposes no changes.

## 1. Orientation convention applied

**Convention used:** the `why` text's A/B labels are *prompt display order*. The log record stores
`a` and `b` fields plus `flip`.

- `flip == false` → prompt **A = log field `a`**, prompt **B = log field `b`**
- `flip == true` → prompt order swapped: prompt **A = log field `b`**, prompt **B = log field `a`**

Since `usa_position` names the log field holding the USA, the USA's prompt label is:

`US_label = A` if `(usa_position == "a") XOR (flip == true)`, else `US_label = B`.

Equivalently: USA is prompt **A** in rows 69, 167, 177, 522, 686, 728, 1201, 1456, 1595, 1810,
1959, 2313, 2398, 2443, 2507, 2510, 2683, 2839, 3299, 3443, 3567 (21 rows); USA is prompt **B** in
rows 12, 497, 542, 1037, 1075, 1098, 1660, 1711, 2108, 2137, 2645, 2825, 3030, 3096, 3240,
3319, 3354, 3496 (18 rows). Every row resolved; no row required an 'orientation uncertain' mark.

**Verification — raw log fields plus content where orientation is unambiguous:**

| row | log fields | flip | US prompt label | content check (verbatim) |
|---|---|---|---|---|
| 12 (ERI) | a=ERI 0.15, b=USA 0.45 | false | **B** | B = "enforced hostile border/document regime and facility bans, but rule of law, hate-crime and employment protections, courts blocking orders" — unmistakably the US profile; A = "unrepealed morality statute … system reporting torture" = Eritrea. |
| 542 (TUN) | a=TUN 0.10, b=USA 0.48 | false | **B** | B = "national entry/document friction and some state facility bans, but courts block measures" = US; A = "active morality-law enforcement … forced anal exams" = Tunisia. |
| 167 (BDI) | a=BDI 0.22, b=USA 0.40 | true | **A** | flip swaps display order, so prompt A = log b = USA: A = "tier-1 universal exposures — facility bans, birth-sex custody, visa/document flagging"; B = "criminalisation, collapsed rule of law … presidential incitement" = Burundi. |
| 686 (PRY) | a=PRY 0.48, b=USA 0.38 | true | **A** | A = "visa fraud bans for marker mismatch, criminal bathroom bans, birth-sex custody rules, courts enforcing them" = US; B = "no visitor-facing restriction … lower-tier exposure" = Paraguay. |
| 1660 (ISR) | a=USA 0.18, b=ISR 0.60 | true | **B** | B = "state itself imposes universal exposure … allies advise against travel" = US; A = "strong legal recognition and courts working" = Israel. |
| 3496 (DNK) | a=USA 0.32, b=DNK 0.80 | true | **B** | B = "state-imposed universal exposures … fraud bans stranding travellers" = US; A = "X passports, self-ID" = Denmark. |
| 522 (MDG) | a=USA 0.42, b=MDG 0.29 | false | **A** | A = "tier-1 border fraud-flagging and state facility bans … working protections" = US; B = "latent criminalisation with total official impunity" = Madagascar. |

All four (usa_position × flip) quadrants are covered; the XOR rule reproduces the content reading in
every case. Cross-check: `usa-archived.json` row 686 `us_rating=0.38` matches the HANDOFF note
"Archived USA vs PRY was 0.38".

## 2. Scope-class rules used in §3

Each US-side exposure claim is split into claim units and assigned exactly one class:

- **N = national-only** — asserted at federal/country level or explicitly universal across the
  country, with no conditioning and no subnational marker (visa/passport/border/entry regime,
  X-marker/passport policy, immigration detention of foreigners, allied travel advisories,
  "universal"/"nationwide" exposure labels on document/border regimes).
- **S = state-or-local-only** — explicitly subnational: "state facility bans", "state bathroom bans",
  "state bounties", "criminal facility bans **in places**".
- **C = conditional** — the claim itself is trigger-bound: fraud/mismatch bans, "for trans applicants",
  or custody/detention treatment (exposure exists only once detained).
- **U = unclear scope** — governmental level or trigger not stated: bare "facility bans",
  "bathroom arrests/laws" without a level marker, "official/hostile-state threat-framing",
  bare "detentions", "bounties", "official hostility".

Note on vocabulary: the corpus itself distinguishes levels — rows 542 ("national entry/document
friction and **some state** facility bans") and 2313 ("hostile **national** visa/document rules,
**state** bathroom bans") contrast national vs state explicitly. Bare mentions elsewhere carry no
level marker, hence U rather than an inferred class. "state-imposed"/"hostile state"/"state-run" is
read as "the state apparatus" (level unstated) and does **not** by itself earn N or S.

## 3. Master table (39 rows)

| row i | partner | US rating | partner rating | exposure claims attributed to the US side | exposure claims attributed to partner | scope notes |
|---|---|---|---|---|---|---|
| 12 | ERI | 0.45 | 0.15 | (B) "enforced hostile border/document regime"; "facility bans" | (A) unrepealed morality statute enforced against foreigners/deportations; brutal custody; no recourse; hostile state; outing risks detention in a system reporting torture | US side carries a mitigation clause ("rule of law, hate-crime and employment protections, courts blocking orders"); no universal claim; facility level unstated |
| 69 | RWA | 0.15 | 0.32 | (A) "universal traveller exposure": passport/visa sex-marker regime; fraud-based bans; facility exclusion; custody abuse; official threat-framing | (B) criminalises nothing trans-specific; documented police identity-check harassment; arbitrary arrests with no recourse | explicit universal label bundling a fraud-conditional ban and a detention-conditional custody claim |
| 167 | BDI | 0.40 | 0.22 | (A) "tier-1 universal exposures" — facility bans; birth-sex custody; visa/document flagging; mitigation: "functioning courts and no anti-trans statute" | (B) criminalisation; collapsed rule of law; documented arrests; custodial death; presidential incitement; thin trans data | 2 of 3 "universal" components are conditional; one of only 19 universal rows carrying US-side mitigation |
| 177 | PAN | 0.25 | 0.62 | (A) "state-imposed universal exposure" — visa/document fraud flagging; facility bans with arrests; custody harm; official threat-framing | (B) no trans-specific offence; no documented targeting or facility bans; thin recourse; conservative attitudes | "state-imposed" level ambiguous; fraud flag conditional; first of two PAN rows (cf. 2825) |
| 497 | ROU | 0.20 | 0.60 | (B) "universal entry/document exposure"; visa fraud bans; bathroom arrests; abusive custody; state threat-framing | (A) no trans-specific offence; no documented police/border targeting or violence; working courts; hostile rhetoric; no gender-identity protections | universal label; bathroom arrests level unstated; custody conditional on detention |
| 522 | MDG | 0.42 | 0.29 | (A) "tier-1 border fraud-flagging and state facility bans" **but** "partial, court-challenged, and sit alongside working protections and no criminalisation" | (B) free of trans-specific statutes; latent criminalisation with total official impunity; unremedied societal hostility | tier-1 label coexists with a partial/challenged qualifier; national vs state contrast explicit |
| 542 | TUN | 0.48 | 0.10 | (B) "national entry/document friction and some state facility bans, but courts block measures, no criminalisation, partial hate-crime recourse" | (A) active morality-law enforcement against gender-nonconforming people; forced anal exams; birth-sex prison processing; no remedy — "near-extreme" | mildest severity word ("friction") for the same federal entry/document exposure other rows call tier-1/High Risk; only 2 US claim units in the whole corpus carry no conditional/unclear component here besides 12 |
| 686 | PRY | 0.38 | 0.48 | (A) visa fraud bans for marker mismatch; criminal bathroom bans; birth-sex custody rules; "courts enforcing them" | (B) no visitor-facing restriction; societal hostility with ignored complaints; resident-facing gaps; "lower-tier exposure" | explicitly conditional (document mismatch); courts described as enforcing — opposite of 522/542/12 |
| 728 | DEU | 0.25 | 0.66 | (A) traveller-facing visa/document fraud bans; state facility exclusions; custody abuse; official threat-framing | (B) no criminalisation; working anti-discrimination/equal-treatment recourse; prison-placement issue; isolated airport/sauna friction | explicit subnational "state facility exclusions"; fraud conditional |
| 1037 | HRV | 0.20 | 0.74 | (B) "state-imposed universal exposure" — passports reverted to birth sex; X markers ended; visa fraud bans; detentions; bathroom arrests; abusive custody; official threat-framing | (A) no traveller-facing bans; trans-aware search law; gender-identity hate-crime coverage; wide acceptance; uneven enforcement | 7-unit bundle mixing national instruments, level-unstated items and conditional items under one universal label |
| 1075 | IND | 0.32 | 0.62 | (B) border visa-fraud bans; X-marker refusal; detentions of foreigners; state bounties; custody harm — "tier-1 universal exposure, High Risk" | (A) no criminalisation or facility bans; scattered railway/airport police harassment; working court protections; "Reduced Risk" | only row using full risk-band vocabulary on the US side; bundles federal border items with subnational "state bounties" |
| 1098 | GNB | 0.10 | 0.46 | (B) "universal document/facility exclusion at borders"; custody harm; official threat-framing | (A) no traveller-facing restriction or trans-specific enforcement; dated stigma; weak rule of law | "at borders" nationalizes the facility component; who is excluded is unstated |
| 1201 | TON | 0.28 | 0.46 | (A) "active state entry/document hostility" — visa-fraud bans; detentions; allied advisories; criminal bathroom laws; abusive custody | (B) dormant sodomy/impersonation statutes; no documented enforcement; embedded third-gender tradition; one dated murder | "allied advisories" is a national-level signal; bathroom level unstated; first of two TON rows (cf. 2108) |
| 1456 | ISL | 0.16 | 0.86 | (A) traveler-facing visa fraud flagging; bathroom bans/arrests; custody abuse; hostile state framing | (B) protected facilities; hate-crime recourse; high acceptance; no documented trans-specific border or violence exposure | no universal label; bathroom/custody level unstated |
| 1595 | UKR | 0.28 | 0.62 | (A) traveller-facing document/visa fraud bans; facility exclusions; hostile custody | (B) no trans criminalisation; only dated violence and male-marker border friction; conservative social climate | facility/custody level unstated; no universal or mitigation language |
| 1660 | ISR | 0.18 | 0.60 | (B) "state itself imposes universal exposure" — entry fraud bans; facility exclusion; custodial abuse; activist bounties; "allies advise against travel" | (A) strong legal recognition and courts working; airport-outing ordeal plus societal violence with recourse | "state itself" level ambiguous; bounty level unstated; allied advisories national |
| 1711 | KWT | 0.22 | 0.35 | (B) "state-run border regime" bars/flags trans travellers (X markers, visa fraud bans); documented custody abuse — "tier-1 universal exposure" | (A) trans-specific 'imitating' law struck down by court; residual morality policing and official discrimination; "less severe" | universal label over fraud-conditional and custody-conditional components; partner explicitly graded "less severe" |
| 1810 | MKD | 0.18 | 0.45 | (A) state-imposed document/visa bans; facility exclusion enforced by arrest; official hostility | (B) no criminalisation or traveller-facing bans; documented societal hostility; thin recourse; weak hate-speech enforcement | trigger for "document/visa bans" unstated; facility-arrest level unstated |
| 1959 | LTU | 0.15 | 0.58 | (A) "state-imposed universal exposure" — passport/visa marker restrictions; fraud bans; bathroom laws and arrests; abusive custody; official threat-framing | (B) no entry restrictions or trans criminal law; resident-facing gaps; thin hate-crime recourse; social conservatism | bundle mixes national instruments with level-unstated bathroom items |
| 2108 | TON | 0.30 | 0.50 | (B) "state-imposed universal exposures" — visa/entry bans; facility exclusion; custody harm; bounties; "counterterrorism framing" | (A) unenforced sodomy and public-deception statutes; no documented police targeting; documented third-gender acceptance; rising hostility; thin recourse | "counterterrorism framing" has no defined referent or level; second TON row with different US wording (cf. 1201) |
| 2137 | AZE | 0.42 | 0.20 | (B) harsh border, facility and custody measures; **but** "courts grant relief and anti-discrimination protections operate, tempering exposure" | (A) recurring police raids with torture, forced exams, blackmail and murder with impunity; no legal recourse | explicit mitigation clause tempering the US exposure; levels unstated |
| 2313 | CMR | 0.36 | 0.14 | (A) "hostile national visa/document rules"; "state bathroom bans"; "severe custody risk"; "some legal/protective variation" | (B) sodomy law enforced against gender presentation; documented five-year sentences; police abuse; no recourse | clearest national-vs-state contrast in the corpus |
| 2398 | MYS | 0.34 | 0.26 | (A) "broad border/visa and bathroom exposure"; no general trans ban; some legal recourse | (B) criminalises gender nonconformity for Muslims and same-sex conduct; religious raids; custody sexual violence; no effective protection | "broad" scope word with no level marker; bathroom unit unclear |
| 2443 | GNQ | 0.26 | 0.36 | (A) "universal traveler-facing exposure": hostile passport/visa marker rules; fraud bans; facility arrests | (B) no explicit trans criminalisation or border restrictions; police/custody violence with impunity | universal label bundling a fraud-conditional ban; facility-arrest level unstated |
| 2507 | PRT | 0.18 | 0.82 | (A) traveler-facing visa/document fraud bans; bathroom criminalisation and arrests; abusive detention | (B) currently protects facilities and documents; no border exposure; rollback bills only at first reading | no universal label; bathroom level unstated; detention conditional |
| 2510 | LIE | 0.20 | 0.73 | (A) "enforced hostile document/visa regime" + "facility bans" said to "create universal traveller exposure"; abusive custody | (B) no criminalisation, facilities or border friction; dated official disapproval; resident-only recognition gaps | universal label spans document regime and level-unstated facility bans; first of two LIE rows (cf. 2683) |
| 2645 | SAU | 0.33 | 0.07 | (B) border visa/document fraud bans; facility bans; custodial abuse | (A) criminalises gender nonconformity itself; documented cross-dressing arrests, lashings; a trans woman dead in custody; expression-based enforcement reaching travellers | no universal, mitigation or tier language on either side; levels unstated |
| 2683 | LIE | 0.15 | 0.70 | (A) traveler-facing visa fraud bans; border flagging; official threat framing; custody abuse | (B) no criminalisation or facilities bans; resident-facing gaps; dated official disapproval | second LIE row, same US profile at a different rating and with milder wording (no "universal") |
| 2825 | PAN | 0.22 | 0.65 | (B) state-imposed passport and visa exposure; facility exposure; official threat framing; "materially lowering safety for trans visitors" | (A) no documented traveller-facing trans restriction or targeting; resident-facing gaps; climate signals | second PAN row (cf. 177) — universal label dropped; "facility exposure" level unstated |
| 2839 | POL | 0.17 | 0.55 | (A) "state-directed visa/document targeting"; facility restrictions; custody abuse reaching trans travellers | (B) no criminalisation or border bans; mainly societal hostility; thin hate-crime recourse; documented detention medication failure | "targeting" trigger unstated; custody conditional |
| 3030 | BTN | 0.22 | 0.48 | (B) "state-imposed universal exposure": passport X-marker ban; visa fraud flags; entry detentions; bathroom bans; custody abuse — "tier 1-2" | (A) no criminalisation; no visitor border/facility exposure; impunity for anti-trans violence; health-care discrimination — "tier 3" | tier labels on both sides; bundle mixes national entry items with level-unstated bathroom/custody |
| 3096 | BIH | 0.24 | 0.50 | (B) "visitor-facing universal exposure … under a hostile state regime": visa flagging/permanent bans; X-marker refusal; facility and custody harm | (A) no criminalisation; no documented border/facility/custody exposure to visitors; societal hostility; dated public-event violence | "permanent bans" trigger unstated; facility/custody level and trigger unstated |
| 3240 | ATG | 0.29 | 0.62 | (B) traveller-facing universal exposures: passport/visa marker bans; visa-fraud entry bans; detentions; bathroom-law arrests; abusive custody; state threat-framing | (A) no trans-specific criminal or border restriction; resident-only negatives; thin-data conservatism; functioning courts | 6-unit universal bundle: 2 conditional, 3 unclear, 1 national |
| 3299 | YEM | 0.45 | 0.12 | (A) hostile border/visa flagging; "some state bathroom bans"; custody harm; **but** "no trans criminalisation, working courts and broad legal protection" | (B) death-penalty courts; vigilante licence; no recourse for gender-nonconforming people | explicit subnational marker plus mitigation clause |
| 3319 | FSM | 0.21 | 0.58 | (B) documented traveller-facing state exposure: visa gender flagging and permanent bans; criminal bathroom rules; abusive immigration custody; official bounty-hunting of trans activists | (A) no criminalisation; no documented traveller targeting; dated societal stigma; resident-only LGR gap | "visa gender flagging" = trigger tied to marker content; bounty level unstated; immigration custody federal but detention-conditional |
| 3354 | GTM | 0.22 | 0.38 | (B) "nationwide passport/entry restrictions (X-marker ban, visa flagging, permanent bans)" plus "facility bans with documented arrests" — "tier-1 universal exposure" | (A) lacks criminalisation and visitor-targeting; thin recourse amid official hostility | only "nationwide" occurrence; facility component of unstated level inside a universal label |
| 3443 | WLF | 0.15 | 0.65 | (A) traveller-facing border/document fraud flags; X-marker ban; facility bans; hostile state framing | (B) protective parent regime — no criminalisation, anti-discrimination and hate-crime coverage — with exposure "largely conditional on detention or local social stigma" | only row containing the word "conditional", and it is attributed to the partner, not the US |
| 3496 | DNK | 0.32 | 0.80 | (B) "state-imposed universal exposures": document/visa mismatch; fraud bans stranding travellers; facility exclusion; birth-sex custody; "no working remedy" | (A) X passports, self-ID, no criminalisation; recourse gaps (hate-crime law omits gender identity); a custody-placement ruling | universal label over mismatch-conditioned bans and detention-conditional custody; "state-imposed" level ambiguous; "no working remedy" vs courts-blocking language elsewhere |
| 3567 | GUY | 0.23 | 0.55 | (A) "universal-exposure visa fraud ban for trans applicants"; criminal facility bans "in places"; official threat-framing; custody harm | (B) no trans-specific offence; cross-dressing law struck down; tolerant society; police extortion; thin recourse | only row where "universal" and an applicant-limited trigger sit in the same phrase; explicit subnational "in places" |

## 4. Claim-level classification of every US-side claim unit

Codes: **N** national-only, **S** state-or-local-only, **C** conditional, **U** unclear scope.

| row i | US label | classified claim units |
|---|---|---|
| 12 | B | N: border/document regime · U: facility bans |
| 69 | A | N: universal passport/visa sex-marker regime · C: fraud-based bans · C: custody abuse · U: facility exclusion · U: official threat-framing |
| 167 | A | U: facility bans (inside "tier-1 universal") · C: birth-sex custody · C: visa/document flagging |
| 177 | A | C: visa/document fraud flagging · C: custody harm · U: facility bans with arrests · U: official threat-framing |
| 497 | B | N: universal entry/document exposure · C: visa fraud bans · C: abusive custody · U: bathroom arrests · U: state threat-framing |
| 522 | A | C: border fraud-flagging · S: state facility bans |
| 542 | B | N: national entry/document friction · S: some state facility bans |
| 686 | A | C: visa fraud bans for marker mismatch · C: birth-sex custody rules · U: criminal bathroom bans |
| 728 | A | C: visa/document fraud bans · C: custody abuse · S: state facility exclusions · U: official threat-framing |
| 1037 | B | N: passports reverted to birth sex + X markers ended · C: visa fraud bans · C: abusive custody · U: detentions · U: bathroom arrests · U: official threat-framing |
| 1075 | B | N: X-marker refusal · N: detentions of foreigners · C: border visa-fraud bans · C: custody harm · S: state bounties |
| 1098 | B | N: universal document/facility exclusion at borders · C: custody harm · U: official threat-framing |
| 1201 | A | N: allied advisories · C: visa-fraud bans · C: abusive custody · U: detentions · U: criminal bathroom laws |
| 1456 | A | C: visa fraud flagging · C: custody abuse · U: bathroom bans/arrests · U: hostile state framing |
| 1595 | A | C: document/visa fraud bans · C: hostile custody · U: facility exclusions |
| 1660 | B | N: allies advise against travel · C: entry fraud bans · C: custodial abuse · U: facility exclusion · U: activist bounties |
| 1711 | B | N: X markers · C: visa fraud bans · C: documented custody abuse |
| 1810 | A | N: document/visa bans · U: facility exclusion enforced by arrest · U: official hostility |
| 1959 | A | N: passport/visa marker restrictions · C: fraud bans · C: abusive custody · U: bathroom laws and arrests · U: official threat-framing |
| 2108 | B | N: visa/entry bans · C: custody harm · U: facility exclusion · U: bounties · U: counterterrorism framing |
| 2137 | B | N: harsh border measures · C: custody measures · U: facility measures |
| 2313 | A | N: hostile national visa/document rules · C: severe custody risk · S: state bathroom bans |
| 2398 | A | N: broad border/visa exposure · U: bathroom exposure |
| 2443 | A | N: hostile passport/visa marker rules · C: fraud bans · U: facility arrests |
| 2507 | A | C: visa/document fraud bans · C: abusive detention · U: bathroom criminalisation and arrests |
| 2510 | A | N: enforced hostile document/visa regime · C: abusive custody · U: facility bans |
| 2645 | B | C: border visa/document fraud bans · C: custodial abuse · U: facility bans |
| 2683 | A | N: border flagging · C: visa fraud bans · C: custody abuse · U: official threat framing |
| 2825 | B | N: passport and visa exposure · U: facility exposure · U: official threat framing |
| 2839 | A | N: visa/document targeting · C: custody abuse · U: facility restrictions |
| 3030 | B | N: passport X-marker ban · N: entry detentions · C: visa fraud flags · C: custody abuse · U: bathroom bans |
| 3096 | B | N: X-marker refusal · C: visa flagging/permanent bans · C: custody harm · U: facility harm |
| 3240 | B | N: passport/visa marker bans · C: visa-fraud entry bans · C: abusive custody · U: detentions · U: bathroom-law arrests · U: state threat-framing |
| 3299 | A | N: hostile border/visa flagging · C: custody harm · S: some state bathroom bans |
| 3319 | B | C: visa gender flagging and permanent bans · C: abusive immigration custody · U: criminal bathroom rules · U: official bounty-hunting of trans activists |
| 3354 | B | N: nationwide passport/entry restrictions · C: visa flagging + permanent bans · U: facility bans with documented arrests |
| 3443 | A | N: X-marker ban · C: border/document fraud flags · U: facility bans · U: hostile state framing |
| 3496 | B | C: document/visa mismatch + fraud bans stranding travellers · C: birth-sex custody · U: facility exclusion |
| 3567 | A | C: visa fraud ban for trans applicants · C: custody harm · S: criminal facility bans in places · U: official threat-framing |

## 5. Counts per class (US-side claim units)

| class | claim units | rows containing ≥1 unit of the class |
|---|---|---|
| national-only (N) | **29** | 27 rows (1075 and 3030 have 2 each) |
| state-or-local-only (S) | **7** | 7 rows: 522, 542, 728, 1075, 2313, 3299, 3567 |
| conditional (C) | **57** | 34 rows (all rows except 12, 542, 1810, 2398, 2825) |
| unclear scope (U) | **50** | 33 rows (all rows except 522, 542, 1075, 1711, 2313, 3299) |
| **total** | **143** | 39 rows |

Per-row totals: N 29 + S 7 + C 57 + U 50 = 143 units across 39 rows (mean ≈ 3.7 units/row).

## 6. Flag (a) — same named exposure, materially different severity language

1. **Visa/document fraud flagging** described on a wide severity ladder for the same instrument:
   - 1075: "border visa-fraud bans … — **tier-1 universal exposure, High Risk**"
   - 3354: "nationwide passport/entry restrictions … **permanent bans**" + "tier-1 universal exposure"
   - 3096: "visa flagging/**permanent bans**"
   - 2313: "**hostile** national visa/document rules"
   - 542: "**national entry/document friction** … but courts block measures"
   - 522: "**tier-1** border fraud-flagging … but they are **partial, court-challenged**"
   Same exposure: "tier-1/High Risk/permanent bans" (1075, 3354, 3096) vs "friction"/"partial" (542, 522).
2. **Facility bans**: "facility exclusion **enforced by arrest**" (1810), "facility bans **with arrests**" (177), "facility bans **with documented arrests**" (3354), "facility **harm … under a hostile state regime**" (3096) vs "some state facility bans … **courts block measures**" (542), "state facility bans … **partial, court-challenged**" (522), "criminal facility bans **in places**" (3567), bare "facility bans" (12, 2510, 2645, 3443).
3. **Courts' role in the same exposure**: "**courts blocking orders**" (12), "**courts block measures**" (542), "**court-challenged**" (522), "**courts enforcing them**" (686), "**no working remedy**" (3496), vs "**functioning courts**"/"**working courts**"/"**some legal/protective variation**" as mitigation (167, 2313, 3299, 2137, 1075-partner side).
4. **Custody severity vocabulary**: "custody harm" (177, 2108, 1075, 3299) vs "**severe** custody risk" (2313) vs "**abusive** custody" (many) vs "**harsh** … custody measures" (2137) vs "**documented** custody abuse" (1711) vs "**tempering exposure**" mitigation (2137).
5. **Official threat-framing intensity**: "**counterterrorism framing**" (2108) vs "**official threat-framing**" (69, 177, 728, 1037, 1959, 2683, 3567) vs "**hostile state framing**" (1456, 3443) vs "**state threat-framing**" (497) vs bare "**official hostility**" (1810).
6. **Tier/risk-band vocabulary appears inconsistently**: "tier-1" (167, 522, 1075, 1711, 3354), "tier 1-2" (3030), and the only "High Risk"/"Reduced Risk" pair (1075) — while rows describing comparable US exposure carry no tier at all (12, 542, 2137, 2825, 3443).
7. **Repeat partners with different US severity wording** (rating differences noted only, not judged): LIE 2510 "universal traveller exposure" (0.20) vs 2683 no universal claim (0.15); PAN 177 "state-imposed universal exposure" (0.25) vs 2825 "passport, visa and facility exposure" (0.22); TON 1201 "active state entry/document hostility" (0.28) vs 2108 "state-imposed universal exposures" (0.30).

## 7. Flag (b) — universal vs conditional application

**Universal-asserting US claims (19 rows):** 69, 167, 177, 497, 1037, 1075, 1098, 1660, 1711, 1959, 2108, 2443, 2510, 3030, 3096, 3240, 3354, 3496, 3567 — each uses "universal" or (3354) "nationwide" of the US exposure.

- The corpus contains **no** literal "every visitor", "any applicant", "every", "any" or "all
  visitors" phrasing (verified by regex over all 39 `why` strings). Universality is expressed as
  "universal … exposure", "nationwide", and "traveller/visitor-facing".
- **All 19 universal rows also contain at least one conditional claim unit** (fraud/mismatch ban,
  custody, or detention). Examples of the tension inside one sentence: 3567 "**universal-exposure**
  visa fraud ban **for trans applicants**"; 69 "universal traveller exposure: … **fraud-based bans**
  … **custody abuse**"; 3496 "universal exposures — document/visa **mismatch**, fraud bans …
  **birth-sex custody**"; 3096 "visitor-facing universal exposure — visa flagging/**permanent bans** …
  **custody harm**".
- **Conditional application (34 rows, 57 units):** triggers named are document/visa mismatch
  (686 "for marker mismatch", 3496 "document/visa mismatch", 3496 "stranding"), visa application or
  marker content (3567 "for trans applicants", 3319 "visa gender flagging", 1075/3354/3096
  "permanent bans" with no stated trigger), and detention/custody (custody units in 30 rows; explicit
  "detention" words in 1037, 1075, 1201, 2507, 2839, 3030, 3240, 12-partner, 3443-partner).
- **Only one row uses the word "conditional" (3443) and it is applied to the partner**, not to the
  US: partner exposure "largely conditional on detention or local social stigma".
- **Mitigation asymmetry:** 8 rows carry a US-side mitigating clause (12, 167, 522, 542, 2137, 2313,
  2398, 3299), but only 1 of them (167) is also a universal-assertion row; the other 18 universal
  rows state the US exposure with no mitigating clause.

## 8. Five most scope-ambiguous claims (row id + verbatim fragment)

1. **Row 3567** — "*A: universal-exposure visa fraud ban for trans applicants*" — the only phrase
   that asserts universal exposure and names an applicant-limited trigger simultaneously; the
   governmental level (federal visa vs state) is never stated, and "universal" cannot hold literally
   for a ban addressed to visa applicants who are trans.
2. **Row 1075** — "*B: border visa-fraud bans, X-marker refusal, detentions of foreigners plus state
   bounties and custody harm — tier-1 universal exposure, High Risk*" — one "universal" tier-1 label
   spans federal border instruments and subnational "state bounties", plus detention-conditional
   custody; which travellers the universal label covers is not defined.
3. **Row 69** — "*A imposes universal traveller exposure: passport/visa sex-marker regime, fraud-based
   bans, facility exclusion, custody abuse and official threat-framing*" — universality asserted for
   a list containing two inherently triggered exposures (fraud ban, custody) and a level-unstated
   facility exclusion; no count, facility or level is specified for any component.
4. **Row 3496** — "*B: state-imposed universal exposures — document/visa mismatch, fraud bans
   stranding travellers, facility exclusion, birth-sex custody — no working remedy*" — "state-imposed"
   is ambiguous (US federal government vs US states), "universal" covers mismatch-conditioned and
   detention-conditioned items, and "no working remedy" contradicts the courts-blocking language of
   rows 12/522/542.
5. **Row 522** — "*A has tier-1 border fraud-flagging and state facility bans, but they are partial,
   court-challenged, and sit alongside working protections and no criminalisation*" — a "tier-1"
   severity label attached to exposures then scoped as partial and legally contested; "state facility
   bans" gives no number, jurisdiction or applicability, so the share of the exposure that actually
   binds is unknowable from the text.

## 9. Limits and residual risks

- Classification of claim units is interpretive; the N/S/C/U boundary for bare "facility bans",
  "bathroom arrests" and "threat-framing" rests on the absence of level markers, not on source
  documents. Where the dossier elsewhere contrasts "national" vs "state" (542, 2313), bare mentions
  could plausibly be either.
- I did not inspect the dossier sources behind any claim; this is a claim-text extraction, not a
  fact-check. Universal and conditional statements are recorded as written, not validated.
- Orientation was verified on 7 rows (all four quadrants) against raw log fields plus content; the
  remaining 32 rows use the same mechanical rule, which was content-checked on rows 12, 542, 167,
  686, 1660, 3496, 522 and spot-checked across the table (e.g. 497/1037 US-side visa/bathroom content
  vs Romania/Croatia partner content).
- Ratings are reproduced only to identify rows; no comparison of ratings is evaluated and no score is
  endorsed or questioned here.
- No repository files were written; the only artifact is this report at `/tmp/kort-us39-claims.md`.