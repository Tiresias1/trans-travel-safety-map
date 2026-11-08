# Independent evidence audit — refreshed country-feasibility packets

**Verdict: OK with notes — FEASIBILITY assessment only.**

The previously identified blocking wording has been corrected in the **exact frozen packets**. Remaining evidence gaps constrain interpretation but do not, by themselves, prevent a small methodological feasibility pilot. This is **not** approval of factual completeness, travel guidance, any score/ranking, or provider execution.

**Scope:** Read-only inspection of `frozen/packets/{USA,GBR,NPL,VAT}.txt`, the prior audit, current `data/countries.json` at the supplied offsets, the manifest and relevant ledger material. Independently inspected HRW, MAP and Florida legislation. No edits, scoring or model calls. Comparison was manual, not a recomputed byte/hash verification.

## 1. Verified claims

| Claim | Status | Exact evidence and reasoning |
|---|---|---|
| NPL contradicted ruling date corrected | **supported** | Frozen NPL `ASSESSMENT` now says **“In a decision publicly reported in July 2024”**; resident section likewise says **“publicly reported in July 2024.”** Current `blindSummary` and `blindLocalsOnly` agree. [HRW, 31 July 2024](https://www.hrw.org/news/2024/07/31/nepal-supreme-court-rules-trans-woman-woman) reports the judgment and says **“the order only applies to Kapali, meaning others will have to petition courts.”** The packet no longer invents a 30 August ruling date or universal implementation. High confidence. |
| GBR Goodwin respondent corrected | **supported** | Frozen `ASSESSMENT`: **“Goodwin v the country (2002), in which … [the court] found the country in breach.”** Current named field says `Goodwin v United Kingdom`; current blind field matches the packet. The prior internally contradictory neighbouring-jurisdiction substitution is gone. High confidence in correction/parity. |
| GBR Outer House authority corrected | **supported** | Frozen `ASSESSMENT`: **“Outer House, a first-instance division of the regional supreme civil court.”** Current blind field agrees; named field specifies `Outer House, Court of Session`. The prior claim that the Outer House itself was “the top civil court” is removed. High confidence in correction/parity. |
| VAT facilities absence re-scoped to unknown | **supported** | Frozen `ASSESSMENT`: **“it is unknown whether a trans-specific rule governs access to single-sex facilities.”** Current named/blind fields agree. Frozen source evidence adds **“neither trans-specific danger nor trans-specific safety can be inferred.”** This closes the prior unsupported affirmative legal-absence claim without claiming either safety or danger. High confidence. |
| USA MAP categories and date corrected | **supported** | Frozen `ASSESSMENT` explicitly dates the map **“7 November 2026”** and gives disjoint groups **9 + 9 other + 3**, plus 29 without mapped bans; source evidence agrees. Independently fetched [MAP’s underlying HTML](https://mapresearch.org/equality-map/bans-on-transgender-people-using-public-bathrooms-and-facilities-according-to-their-gender-identity/) contains **“(9 states + 1 territory)”**, **“(9 states)”**, **“(29 states + 4 territories + D.C.)”**, and **“Data as of November 7, 2026.”** Its private-settings note names Florida, Idaho, Kansas, Montana, Ohio and Wyoming, matching the packet’s six. The prior live-tracker discrepancy is not reproduced in this inspection. |
| USA conditional offence retained, not blanket arrest | **supported** | Frozen text says **“the statutory trigger is trespass, not automatic arrest”** and requires willful entry **and refusal to depart when asked**, subject to exemptions. [Florida §553.865(11)(b)](https://www.flsenate.gov/Laws/Statutes/2025/553.865) actually says **“refuses to depart when asked”** and excludes the building’s governmental employees. This is appropriately conditional. High confidence. |
| Critical corrections reached frozen packets, not merely current data | **supported** | All correction excerpts above were read directly in the frozen files and then compared with current blind fields. GBR’s index-number removal remains a deliberate packet transformation, not accidental drift. No substantive mismatch found in the inspected fields. |

## 2. Contradicted claims

**No remaining decision-critical contradiction established in the refreshed correction wording.**

The prior NPL date, Goodwin attribution and Outer House rank defects are no longer present. This conclusion does not independently validate every unchanged assertion.

## 3. Weak / unclear / unsupported claims

- **USA custody assertions — unclear; nonblocking for feasibility.** Frozen `ASSESSMENT` still leads with **“Custody and detention carry documented harm”**, but `DELIBERATELY NOT COUNTED` expressly states that the conversion-therapy-style policies and immigration-custody abuse claims **“are drawn from a single encyclopedic source … and are not independently corroborated here.”** They remain allegations/source reports, not independently established findings in this audit.
- **NPL political claims — unclear; nonblocking for feasibility.** Current source inventory bundles the October 2024 rally, April 2026 leader video and supporter threats into Wikipedia coverage. Frozen `ASSESSMENT` preserves **“not official government acts”** and calls the video **“reported personal video.”** The historical 2008 platform change explicitly **“does not establish the parties’ present-day stance”** and concerns gay rather than trans-specific rights. These qualifications prevent an automatic inference of current state persecution, but original-source corroboration remains missing.
- **VAT categorical legal/prison-policy absences — missing evidence at primary-law level; nonblocking within this narrow pilot.** Frozen `ASSESSMENT` retains **“There is no trans-specific prisoner-placement policy”**, no marker-change mechanism and no SOGI discrimination law. The inventory does not demonstrate an exhaustive primary-law search. Treat these as the limits of this inventory, not certified universal negatives. Facilities access, importantly, is now explicitly unknown.
- **GBR planned ward restrictions — implementation unclear, correctly framed.** Frozen text says **“under plans announced … at an October 2023 party conference”** and describes a consultation. It must not be interpreted as proof that a blanket ward ban was implemented. Joelle’s account is attributed to the clinic/mother, with proceedings unresolved.

## 4. Material source-quality concerns

1. **VAT remains legally thin:** institutional doctrine and encyclopedic summaries are not a complete account of operative state law. The packet correctly distinguishes doctrine from visitor-binding rules.
2. **NPL and USA retain bundled encyclopedic claims.** Their presence is acceptable for testing evidence handling, not for treating all included claims as verified.
3. **Source dates are retained, but metadata is uneven:** USA’s MAP snapshot is November 2026 while `researchedAt` remains October 2026. Prefer the explicit claim-level date; the record-level timestamp is not a uniform evidence cutoff.
4. MAP readable extraction omitted important legend data. Inspecting raw HTML resolved that extraction limitation; the initial automated `source_check` returned missing evidence rather than validation.

## 5. Missing evidence

- No shell/execution tool was available: **manifest hashes and renderer verification were not independently recomputed**. Manifest identifies snapshot commit `80c573a5…`; file contents visibly contain the requested corrections. Git history/HEAD identity was not independently verified.
- No exhaustive Vatican primary-law review.
- No independent corroboration of NPL’s recent political allegations or USA’s prison/immigration-abuse assertions.
- No independent re-audit of every unchanged UK 2026 development. Prior-audit conclusions were not treated as newly verified external evidence.

These are bounded limitations, not grounds to restart the entire research exercise.

## 6. Material contradictions

**Residual scoping tension, not a feasibility blocker:** USA `AFFECTS RESIDENTS MORE THAN VISITORS` still includes **“In immigration custody, transgender men have reported forced labour…”** This placement can understate relevance to noncitizen visitors. However, the same allegation is separately present in `ASSESSMENT`, and its lack of independent corroboration is explicitly disclosed. No visitor-facing evidence has disappeared; downstream interpretation must not exclude immigration custody merely because of that heading.

**Preserved distinctions:** GBR recognition restrictions are attributed to the index assessment while **“Certificates continue to be issued”** remains explicit; UK equality-code warnings are distinguished from enacted statutory amendments. VAT’s absence of documented custody cases is explicitly **“not a finding that no trans person has ever been held in pre-trial detention.”**

## 7. Implications for the original conclusion

**OK for FEASIBILITY only.** The prior actual blockers—contradicted date, garbled case respondent, overstated court level, unsupported facilities certainty and undated/ambiguous MAP partition—have been repaired in the frozen inputs.

Remaining uncertainty should test whether the instrument preserves conditionality, attribution and abstention. It must not be converted into either safety or danger. In particular:

- resident document procedures are not visitor entry examinations;
- conditional offences/custody exposure are not blanket arrest rules;
- proposed UK ward restrictions are not proven implemented restrictions;
- institutional doctrine is not automatically visitor-binding law;
- uncorroborated allegations are not independently verified facts.

No score or ranking is selected or endorsed.