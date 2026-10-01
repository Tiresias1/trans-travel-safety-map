#!/usr/bin/env python3
# Worker build script for data/split_out/s059.json (batch s059, 8 TUR records).
# Writes merge-first after each record (loads existing file, appends, dumps).
import json, sys
from pathlib import Path

OUT = Path('data/split_out/s059.json')

records = []

# ---------------------------------------------------------------------------
# Shared core phrases
CORE_SUMMARY_INTRO = ("No province-specific measure, incident or institution concerning transgender visitors is "
 "documented for {name} in this edition's audited sources: what governs a trans visitor is the national picture, "
 "and no local authority is recorded adding bans or enforcement programs of its own.")
CORE_RISK = ("As documented nationally, the visitor risk assessment: a draft judicial package leaked in October "
 "2025 would carry prison terms of up to three years for conduct deemed contrary to biological sex and general "
 "morality, up to four years for participation in same-sex engagement or marriage ceremonies (same-sex marriage "
 "is not recognised, so such ceremonies are symbolic \u2014 the partner-travel exposure), raise the gender-care "
 "age floor to twenty-five with mandatory infertility conditions, and remove civil-status recognition of gender "
 "change. The principal national LGBTI report (February 2026) called the previous year's hostility explicit state "
 "policy, with three hate-motivated killings in which trans victims were over-represented, 89 ill-treatment cases "
 "mostly tied to breaking up gatherings, and 313 detentions; pride assemblies have been banned in the largest city "
 "and other cities in most years since 2015.")
CORE_OUTSCOPE = ("The October 2025 package is a leaked draft, so its enactment outcome is unresolved. No "
 "province-specific measure, incident or institution is documented for {name}: the absence describes the record, "
 "not a guarantee, so neither a more protective nor a more hostile local regime can be established, and the "
 "recorded absence of provincial divergence is not evidence that no divergence exists. No source addresses "
 "border-screening, document or identity-check practice for trans visitors to this province, and no marriage or "
 "partner-travel information specific to this province is recorded beyond the national recognition rules.")

def vis(p): return '<p>' + p + '</p>'

# ---------------------------------------------------------------------------
# 1. TUR/Rize
r = {}
r['who'] = 'TUR/Rize'
r['summary'] = vis(CORE_SUMMARY_INTRO.format(name='Rize')) + vis(CORE_RISK)
r['tangentialFactors'] = vis(
 "Parent-nation policy turbulence: the October 2025 package is a leaked draft rather than enacted law; Human "
 "Rights Watch described it as one of the most alarming rollbacks of rights in decades, and activists held a press "
 "conference in the largest city on 28 October 2025 against the provisions targeting LGBT people. The monitoring "
 "counts \u2014 one organisation closed, three hate-motivated killings with trans victims over-represented, 89 "
 "ill-treatment cases and 313 detentions \u2014 were logged countrywide rather than per province, so they describe "
 "national practice, not provincial choice. Enforcement and litigation flux: in June 2025 blanket bans against the "
 "pride marches brought over 90 arbitrary detentions and prosecutions of 92 people continuing at year's end; three "
 "draft law packages targeting LGBTI people were made public during 2025 but were not submitted to parliament, and "
 "a court in a western city ordered the dissolution of a young LGBTI association in December 2025.")
r['localsOnly'] = vis(
 "Resident-facing facts from the national overview: openly LGBTQ people are barred from military service \u2014 "
 "conscripts who declare their homosexuality are classed under a 'psychosexual illness' definition, must provide "
 "photographic proof, and risk their 'unfit report' leaking publicly \u2014 and transgender people have been able "
 "to change their legal gender since 1988. In June 2025 the national medicines agency banned the prescription and "
 "supply of hormones for gender-affirming procedures for people under 21. No province-specific resident data is "
 "recorded for Rize: no cultural-role, birth-register or resident-discrimination fact appears in the attached "
 "sources for this province.")
r['outOfScopeNotes'] = vis(CORE_OUTSCOPE.format(name='Rize'))
r['blindSummary'] = vis(CORE_SUMMARY_INTRO.format(name='this province')) + vis(
 "As documented nationally, the visitor risk assessment: a draft judicial package leaked in October 2025 would "
 "carry prison terms of up to three years for conduct deemed contrary to biological sex and general morality, up "
 "to four years for participation in same-sex engagement or marriage ceremonies (same-sex marriage is not "
 "recognised, so such ceremonies are symbolic \u2014 the partner-travel exposure), raise the gender-care age floor "
 "to twenty-five with mandatory infertility conditions, and remove civil-status recognition of gender change. The "
 "principal national LGBTI report (February 2026) called the previous year's hostility explicit national policy, "
 "with three hate-motivated killings in which trans victims were over-represented, 89 ill-treatment cases mostly "
 "tied to breaking up gatherings, and 313 detentions; pride assemblies have been banned in the largest city and "
 "other cities in most years since 2015.")
r['blindTangential'] = vis(
 "Parent-nation policy turbulence: the October 2025 package is a leaked draft rather than enacted law; a "
 "rights-monitoring organisation described it as one of the most alarming rollbacks of rights in decades, and "
 "activists held a press conference against the provisions targeting LGBT people. The monitoring counts \u2014 one "
 "organisation closed, three hate-motivated killings with trans victims over-represented, 89 ill-treatment cases "
 "and 313 detentions \u2014 were logged countrywide rather than per province, so they describe national practice, "
 "not provincial choice. Enforcement and litigation flux: in June 2025 blanket bans against the pride marches "
 "brought over 90 arbitrary detentions and prosecutions of 92 people continuing at year's end; three draft law "
 "packages targeting LGBTI people were made public during 2025 but were not submitted to parliament, and a court "
 "ordered the dissolution of a young LGBTI association in December 2025.")
r['blindLocalsOnly'] = vis(
 "Resident-facing facts from the national overview: openly LGBTQ people are barred from military service \u2014 "
 "conscripts who declare their homosexuality are classed under a 'psychosexual illness' definition, must provide "
 "photographic proof, and risk their 'unfit report' leaking publicly \u2014 and transgender people have been able "
 "to change their legal gender since 1988. In June 2025 the national medicines agency banned the prescription and "
 "supply of hormones for gender-affirming procedures for people under 21. No province-specific resident data is "
 "recorded for this province: no cultural-role, birth-register or resident-discrimination fact appears in the "
 "attached sources for this province.")
r['blindOutOfScope'] = vis(CORE_OUTSCOPE.format(name='this province'))
r['blindSourceSummaries'] = [
 "Rights-organisation news release (29 October 2025): a leaked draft of a judicial-reform package would open the "
 "way for criminal charges against LGBT people, described as one of the most alarming rights rollbacks in decades; "
 "activists held a press conference on 28 October 2025 against the provisions targeting LGBT people. National "
 "framework; no province-specific provision is recorded.",
 "National overview page: homosexual conduct has not been a criminal offence since an 1858 penal code, transgender "
 "people have been able to change their legal gender since 1988, and no comprehensive law prohibits discrimination "
 "on grounds of sexual orientation or gender identity; openly LGBTQ people are barred from military service under "
 "an illness definition with photographic proof required and a risk of the resulting report leaking; same-sex "
 "marriage is not recognised; since 2015 authorities have banned pride events in the largest city and other cities "
 "in most years with tear gas, water cannons and mass detentions; the draft package's LGBTI-discriminatory "
 "provisions were removed from the package that passed in 2026, though a February 2026 press report described a "
 "proposed law criminalising publicly encouraging behaviour contrary to biological sex with one to three years in "
 "prison. National framework; no province-specific finding.",
 "Country report (2025/26): in June 2025 authorities issued blanket bans against the LGBTI and Trans pride marches "
 "in the largest city, police used unlawful force on peaceful protesters and over 90 people were arbitrarily "
 "detained; prosecutions of 92 people for participating in pride marches continued at year's end; in December 2025 "
 "a court ordered the dissolution of a young LGBTI association over 'obscene' images incompatible with society's "
 "moral values; three draft law packages targeting LGBTI people were made public during 2025 but were not submitted "
 "to parliament; and in June 2025 the national medicines agency banned the prescription and supply of hormones for "
 "gender-affirming procedures for people under 21. National enforcement climate; no province-specific finding."
]
r['notes'] = ("Split from current_summary plus three national source claims: province-level null finding and the "
 "visitor-facing national framework (draft-package penalties, ceremony exposure, care age floor, removal of "
 "civil-status recognition, enforcement reality with killings/ill-treatment/detentions and pride-ban practice) to "
 "summary; leaked-draft turbulence, alarming-rollback commentary, press conference, countrywide-count framing and "
 "enforcement/litigation flux to tangentialFactors; military-service bar, hormone-supply ban and no-province-data "
 "statement to localsOnly; unresolved draft, absence-not-guarantee and no border/documents-or-marriage modality "
 "caveats to outOfScopeNotes. current_tangential, current_localsOnly, current_outOfScope were empty.")
records.append(r)

# ---------------------------------------------------------------------------
# 2. TUR/Sakarya
r = {}
r['who'] = 'TUR/Sakarya'
r['summary'] = vis(CORE_SUMMARY_INTRO.format(name='Sakarya')) + vis(CORE_RISK.replace(
 "pride assemblies have been banned in the largest city and other cities in most years since 2015.",
 "pride assemblies in the largest city and other cities have been banned in most years since 2015."))
r['tangentialFactors'] = vis(
 "Parent-nation policy turbulence: the October 2025 package is a leaked draft rather than enacted law \u2014 the "
 "third set of LGBTI-targeting law proposals in 2025, after two earlier packages stalled in parliament \u2014 and "
 "fifteen LGBT groups plus the Turkish Medical Association objected to it; the leaked draft is a 66-page document "
 "amending the penal code, the civil code and six other laws, and its provisions, if adopted, would apply "
 "nationwide in every province. The monitoring counts \u2014 one organisation closed, three hate-motivated "
 "killings with trans victims over-represented, 89 ill-treatment cases and 313 detentions \u2014 were logged "
 "countrywide rather than per province, so they describe national practice, not provincial choice.")
r['localsOnly'] = vis(
 "Resident-facing facts from the national overview: legal gender change has been possible for transgender people "
 "since 1988 but requires a court's permission with the applicant at least 18, unmarried and holding a medical "
 "report from a state-designated hospital; openly LGBTQ people are barred from military service under a "
 "'psychosexual illness' definition. No province-specific resident data is recorded for Sakarya: no cultural-role, "
 "birth-register or resident-discrimination fact appears in the attached sources for this province.")
r['outOfScopeNotes'] = vis(CORE_OUTSCOPE.format(name='Sakarya'))
r['blindSummary'] = vis(CORE_SUMMARY_INTRO.format(name='this province')) + vis(
 "As documented nationally, the visitor risk assessment: a draft judicial package leaked in October 2025 would "
 "carry prison terms of up to three years for conduct deemed contrary to biological sex and general morality, up "
 "to four years for participation in same-sex engagement or marriage ceremonies (same-sex marriage is not "
 "recognised, so such ceremonies are symbolic \u2014 the partner-travel exposure), raise the gender-care age floor "
 "to twenty-five with mandatory infertility conditions, and remove civil-status recognition of gender change. The "
 "principal national LGBTI report (February 2026) called the previous year's hostility explicit national policy, "
 "with three hate-motivated killings in which trans victims were over-represented, 89 ill-treatment cases mostly "
 "tied to breaking up gatherings, and 313 detentions; pride assemblies in the largest city and other cities have "
 "been banned in most years since 2015.")
r['blindTangential'] = vis(
 "Parent-nation policy turbulence: the October 2025 package is a leaked draft rather than enacted law \u2014 the "
 "third set of LGBTI-targeting law proposals in 2025, after two earlier packages stalled in parliament \u2014 and "
 "fifteen local LGBT groups plus the national medical association objected to it; the leaked draft is a long "
 "document amending the penal code, the civil code and other laws, and its provisions, if adopted, would apply "
 "nationwide in every province. The monitoring counts \u2014 one organisation closed, three hate-motivated "
 "killings with trans victims over-represented, 89 ill-treatment cases and 313 detentions \u2014 were logged "
 "countrywide rather than per province, so they describe national practice, not provincial choice.")
r['blindLocalsOnly'] = vis(
 "Resident-facing facts from the national overview: legal gender change has been possible for transgender people "
 "since 1988 but requires a court's permission with the applicant at least 18, unmarried and holding a medical "
 "report from a national hospital; openly LGBTQ people are barred from military service under a 'psychosexual "
 "illness' definition. No province-specific resident data is recorded for this province: no cultural-role, "
 "birth-register or resident-discrimination fact appears in the attached sources for this province.")
r['blindOutOfScope'] = vis(CORE_OUTSCOPE.format(name='this province'))
r['blindSourceSummaries'] = [
 "Rights-organisation news release (29 October 2025): a leaked draft of an omnibus judicial package would amend "
 "the penal and civil codes to criminalise conduct 'contrary to biological sex and general morality' (up to three "
 "years; participation in same-sex ceremonies up to four years), raise the minimum age for gender-affirming care "
 "from 18 to 25 with mandatory infertility and multi-evaluation hurdles, and imprison providers (up to seven "
 "years) and patients (up to three years); fifteen LGBT groups and the national medical association object. "
 "National framework; no province-specific provision.",
 "National overview page, the framework that governs this province: homosexual conduct has been decriminalised "
 "since 1858, sex-reassignment surgery has been legal since 1988, but legal gender recognition still requires a "
 "court's permission with the applicant at least 18, unmarried and holding a medical report from a national "
 "hospital; the military bars homosexuals from service and treats homosexuality as an illness; the largest city's "
 "pride parade drew roughly one hundred thousand participants in 2013\u20132014 before the 2015\u20132018 parades "
 "were banned by local authorities. National framework; no province-specific rule recorded.",
 "Rights-organisation factsheet (November 2025) on the leaked proposals: a 66-page draft amending the penal code, "
 "civil code and six other laws leaked to media in mid-October 2025; the third set of proposed LGBTI-targeting "
 "amendments in 2025, the earlier two having stalled in parliament; it would raise the minimum age for legal "
 "gender recognition from 18 to 25 with further conditions, criminalise LGBTI people and those advocating for "
 "their rights, and severely restrict or make impossible access to gender-affirming healthcare. Nationwide "
 "proposals that would apply in every province including this one."
]
r['notes'] = ("Split from current_summary plus three national source claims: province-level null finding and the "
 "visitor-facing national framework (penalties, ceremony exposure, care age floor, recognition removal, "
 "enforcement reality) to summary; leaked-draft turbulence, stalled earlier packages, group objections and "
 "countrywide-count framing to tangentialFactors; court-approved gender-recognition process, military bar and "
 "no-province-data statement to localsOnly; unresolved draft, absence-not-guarantee and no border/documents-or-"
 "marriage modality caveats to outOfScopeNotes. current_tangential, current_localsOnly, current_outOfScope were "
 "empty.")
records.append(r)

# ---------------------------------------------------------------------------
# 3. TUR/Samsun
r = {}
r['who'] = 'TUR/Samsun'
r['summary'] = vis(CORE_SUMMARY_INTRO.format(name='Samsun')) + vis(CORE_RISK.replace(
 "pride assemblies have been banned in the largest city and other cities in most years since 2015.",
 "pride assemblies in the largest city and other cities have been banned in most years since 2015."))
r['tangentialFactors'] = vis(
 "Parent-nation policy turbulence: the October 2025 package is a leaked draft rather than enacted law \u2014 the "
 "third set of LGBTI-targeting law proposals in 2025, after two earlier packages stalled in parliament \u2014 and "
 "fifteen LGBT groups plus the Turkish Medical Association objected to it; the leaked draft is a 66-page document "
 "amending the penal code, the civil code and six other laws, and its provisions, if adopted, would apply "
 "nationwide in every province. The monitoring counts \u2014 one organisation closed, three hate-motivated "
 "killings with trans victims over-represented, 89 ill-treatment cases and 313 detentions \u2014 were logged "
 "countrywide rather than per province, so they describe national practice, not provincial choice.")
r['localsOnly'] = vis(
 "Resident-facing facts from the national overview: legal gender change has been possible for transgender people "
 "since 1988 but requires a court's permission with the applicant at least 18, unmarried and holding a medical "
 "report from a state-designated hospital; openly LGBTQ people are barred from military service under a "
 "'psychosexual illness' definition. No province-specific resident data is recorded for Samsun: no cultural-role, "
 "birth-register or resident-discrimination fact appears in the attached sources for this province.")
r['outOfScopeNotes'] = vis(CORE_OUTSCOPE.format(name='Samsun'))
r['blindSummary'] = vis(CORE_SUMMARY_INTRO.format(name='this province')) + vis(
 "As documented nationally, the visitor risk assessment: a draft judicial package leaked in October 2025 would "
 "carry prison terms of up to three years for conduct deemed contrary to biological sex and general morality, up "
 "to four years for participation in same-sex engagement or marriage ceremonies (same-sex marriage is not "
 "recognised, so such ceremonies are symbolic \u2014 the partner-travel exposure), raise the gender-care age floor "
 "to twenty-five with mandatory infertility conditions, and remove civil-status recognition of gender change. The "
 "principal national LGBTI report (February 2026) called the previous year's hostility explicit national policy, "
 "with three hate-motivated killings in which trans victims were over-represented, 89 ill-treatment cases mostly "
 "tied to breaking up gatherings, and 313 detentions; pride assemblies in the largest city and other cities have "
 "been banned in most years since 2015.")
r['blindTangential'] = vis(
 "Parent-nation policy turbulence: the October 2025 package is a leaked draft rather than enacted law \u2014 the "
 "third set of LGBTI-targeting law proposals in 2025, after two earlier packages stalled in parliament \u2014 and "
 "fifteen local LGBT groups plus the national medical association objected to it; the leaked draft is a long "
 "document amending the penal code, the civil code and other laws, and its provisions, if adopted, would apply "
 "nationwide in every province. The monitoring counts \u2014 one organisation closed, three hate-motivated "
 "killings with trans victims over-represented, 89 ill-treatment cases and 313 detentions \u2014 were logged "
 "countrywide rather than per province, so they describe national practice, not provincial choice.")
r['blindLocalsOnly'] = vis(
 "Resident-facing facts from the national overview: legal gender change has been possible for transgender people "
 "since 1988 but requires a court's permission with the applicant at least 18, unmarried and holding a medical "
 "report from a national hospital; openly LGBTQ people are barred from military service under a 'psychosexual "
 "illness' definition. No province-specific resident data is recorded for this province: no cultural-role, "
 "birth-register or resident-discrimination fact appears in the attached sources for this province.")
r['blindOutOfScope'] = vis(CORE_OUTSCOPE.format(name='this province'))
r['blindSourceSummaries'] = [
 "Rights-organisation news release (29 October 2025): a leaked draft of an omnibus judicial package would amend "
 "the penal and civil codes to criminalise conduct 'contrary to biological sex and general morality' (up to three "
 "years; participation in same-sex ceremonies up to four years), raise the minimum age for gender-affirming care "
 "from 18 to 25 with mandatory infertility and multi-evaluation hurdles, and imprison providers (up to seven "
 "years) and patients (up to three years); fifteen LGBT groups and the national medical association object. "
 "National framework; no province-specific provision.",
 "National overview page, the framework that governs this province: homosexual conduct has been decriminalised "
 "since 1858, sex-reassignment surgery has been legal since 1988, but legal gender recognition still requires a "
 "court's permission with the applicant at least 18, unmarried and holding a medical report from a national "
 "hospital; the military bars homosexuals from service and treats homosexuality as an illness; the largest city's "
 "pride parade drew roughly one hundred thousand participants in 2013\u20132014 before the 2015\u20132018 parades "
 "were banned by local authorities. National framework; no province-specific rule recorded.",
 "Rights-organisation factsheet (November 2025) on the leaked proposals: a 66-page draft amending the penal code, "
 "civil code and six other laws leaked to media in mid-October 2025; the third set of proposed LGBTI-targeting "
 "amendments in 2025, the earlier two having stalled in parliament; it would raise the minimum age for legal "
 "gender recognition from 18 to 25 with further conditions, criminalise LGBTI people and those advocating for "
 "their rights, and severely restrict or make impossible access to gender-affirming healthcare. Nationwide "
 "proposals that would apply in every province including this one."
]
r['notes'] = ("Split from current_summary plus three national source claims: province-level null finding and the "
 "visitor-facing national framework (penalties, ceremony exposure, care age floor, recognition removal, "
 "enforcement reality) to summary; leaked-draft turbulence, stalled earlier packages, group objections and "
 "countrywide-count framing to tangentialFactors; court-approved gender-recognition process, military bar and "
 "no-province-data statement to localsOnly; unresolved draft, absence-not-guarantee and no border/documents-or-"
 "marriage modality caveats to outOfScopeNotes. current_tangential, current_localsOnly, current_outOfScope were "
 "empty.")
records.append(r)

# ---------------------------------------------------------------------------
# 4. TUR/Siirt
r = {}
r['who'] = 'TUR/Siirt'
r['summary'] = vis(CORE_SUMMARY_INTRO.format(name='Siirt')) + vis(CORE_RISK)
r['tangentialFactors'] = vis(
 "Parent-nation policy turbulence: the October 2025 package is a leaked draft rather than enacted law, and "
 "fifteen LGBT groups plus the Turkish Medical Association objected to it. The monitoring counts \u2014 one "
 "organisation closed, three hate-motivated killings with trans victims over-represented, 89 ill-treatment cases "
 "and 313 detentions \u2014 were logged countrywide rather than per province, so they describe national practice, "
 "not provincial choice. Enforcement and litigation flux: pride events have also been repeatedly blocked by "
 "provincial governors, including simultaneous bans in three cities on 14 June 2019; in June 2025 blanket bans "
 "against the pride marches brought over 90 arbitrary detentions and prosecutions of 92 people continuing at "
 "year's end; three draft law packages targeting LGBTI people were made public during 2025 but were not submitted "
 "to parliament, and a court in a western city ordered the dissolution of a young LGBTI association in December "
 "2025.")
r['localsOnly'] = vis(
 "Resident-facing facts from the national overview: openly LGBTQ people are barred from military service under a "
 "'psychosexual illness' definition; transgender people have been able to change their legal gender since 1988; "
 "and in June 2025 the national medicines agency banned the prescription and supply of hormones for "
 "gender-affirming procedures for people under 21. No province-specific resident data is recorded for Siirt: no "
 "cultural-role, birth-register or resident-discrimination fact appears in the attached sources for this "
 "province.")
r['outOfScopeNotes'] = vis(CORE_OUTSCOPE.format(name='Siirt'))
r['blindSummary'] = vis(CORE_SUMMARY_INTRO.format(name='this province')) + vis(
 "As documented nationally, the visitor risk assessment: a draft judicial package leaked in October 2025 would "
 "carry prison terms of up to three years for conduct deemed contrary to biological sex and general morality, up "
 "to four years for participation in same-sex engagement or marriage ceremonies (same-sex marriage is not "
 "recognised, so such ceremonies are symbolic \u2014 the partner-travel exposure), raise the gender-care age floor "
 "to twenty-five with mandatory infertility conditions, and remove civil-status recognition of gender change. The "
 "principal national LGBTI report (February 2026) called the previous year's hostility explicit national policy, "
 "with three hate-motivated killings in which trans victims were over-represented, 89 ill-treatment cases mostly "
 "tied to breaking up gatherings, and 313 detentions; pride assemblies have been banned in the largest city and "
 "other cities in most years since 2015.")
r['blindTangential'] = vis(
 "Parent-nation policy turbulence: the October 2025 package is a leaked draft rather than enacted law, and "
 "fifteen local LGBT groups plus the national medical association objected to it. The monitoring counts \u2014 "
 "one organisation closed, three hate-motivated killings with trans victims over-represented, 89 ill-treatment "
 "cases and 313 detentions \u2014 were logged countrywide rather than per province, so they describe national "
 "practice, not provincial choice. Enforcement and litigation flux: pride events have also been repeatedly "
 "blocked by provincial governors, including simultaneous bans in three cities in June 2019; in June 2025 blanket "
 "bans against the pride marches brought over 90 arbitrary detentions and prosecutions of 92 people continuing at "
 "year's end; three draft law packages targeting LGBTI people were made public during 2025 but were not submitted "
 "to parliament, and a court ordered the dissolution of a young LGBTI association in December 2025.")
r['blindLocalsOnly'] = vis(
 "Resident-facing facts from the national overview: openly LGBTQ people are barred from military service under a "
 "'psychosexual illness' definition; transgender people have been able to change their legal gender since 1988; "
 "and in June 2025 the national medicines agency banned the prescription and supply of hormones for "
 "gender-affirming procedures for people under 21. No province-specific resident data is recorded for this "
 "province: no cultural-role, birth-register or resident-discrimination fact appears in the attached sources for "
 "this province.")
r['blindOutOfScope'] = vis(CORE_OUTSCOPE.format(name='this province'))
r['blindSourceSummaries'] = [
 "Rights-organisation news release (29 October 2025): a leaked draft of an omnibus judicial package would amend "
 "the penal and civil codes to criminalise conduct 'contrary to biological sex and general morality' (up to three "
 "years; participation in same-sex ceremonies up to four years), raise the minimum age for gender-affirming care "
 "from 18 to 25 with mandatory infertility and multi-evaluation hurdles, and imprison providers (up to seven "
 "years) and patients (up to three years); fifteen LGBT groups and the national medical association object. "
 "National framework; no province-specific provision.",
 "National overview page, the framework a trans visitor stands under in this province: homosexuality was "
 "decriminalised in 1858, legal gender change has been possible since 1988, but same-sex marriage is not "
 "recognised and LGBTQ people are barred from serving openly in the military; pride events have been repeatedly "
 "blocked by governors, including the 2015\u20132018 parades in the largest city and simultaneous bans in three "
 "cities on 14 June 2019; a proposal to criminalise publicly encouraging behaviour contrary to biological sex "
 "with a one-to-three-year prison sentence was ultimately not included in the 2026 package. This provincial "
 "record makes no province-specific claim; the page supports the national-framework claims.",
 "Country report (2025/26): in June 2025 blanket bans were issued against the pride marches, police used unlawful "
 "force, over 90 people were arbitrarily detained, and prosecutions of 92 people continued at year's end; in "
 "December 2025 a court ordered the dissolution of a young LGBTI association over 'obscene' images incompatible "
 "with society's moral values; three draft law packages targeting LGBTI people were made public in 2025 \u2014 "
 "criminalising LGBTI identity expression and consensual same-sex relations and making legal gender recognition "
 "nearly impossible \u2014 though they were not submitted to parliament. No province-specific incident documented."
]
r['notes'] = ("Split from current_summary plus three national source claims: province-level null finding and the "
 "visitor-facing national framework (penalties, ceremony exposure, care age floor, recognition removal, "
 "enforcement reality) to summary; leaked-draft turbulence, group objections, governor-blocked pride history and "
 "enforcement/litigation flux to tangentialFactors; military bar, gender-change pathway, hormone-supply ban and "
 "no-province-data statement to localsOnly; unresolved draft, absence-not-guarantee and no border/documents-or-"
 "marriage modality caveats to outOfScopeNotes. current_tangential, current_localsOnly, current_outOfScope were "
 "empty.")
records.append(r)

# ---------------------------------------------------------------------------
# 5. TUR/Sinop
r = {}
r['who'] = 'TUR/Sinop'
r['summary'] = vis(CORE_SUMMARY_INTRO.format(name='Sinop')) + vis(CORE_RISK)
r['tangentialFactors'] = vis(
 "Parent-nation policy turbulence: the October 2025 package is a leaked draft rather than enacted law, and "
 "fifteen LGBT groups plus the Turkish Medical Association objected to it. The monitoring counts \u2014 one "
 "organisation closed, three hate-motivated killings with trans victims over-represented, 89 ill-treatment cases "
 "and 313 detentions \u2014 were logged countrywide rather than per province, so they describe national practice, "
 "not provincial choice. Enforcement and litigation flux: pride events have also been repeatedly blocked by "
 "provincial governors, including simultaneous bans in three cities on 14 June 2019; in June 2025 blanket bans "
 "against the pride marches brought over 90 arbitrary detentions and prosecutions of 92 people continuing at "
 "year's end; and a court in a western city ordered the dissolution of a young LGBTI association in December "
 "2025.")
r['localsOnly'] = vis(
 "Resident-facing facts from the national overview: openly LGBTQ people are barred from military service under a "
 "'psychosexual illness' definition; transgender people have been able to change their legal gender since 1988; "
 "and in June 2025 the national medicines agency banned the prescription and supply of hormones for "
 "gender-affirming procedures for people under 21. No province-specific resident data is recorded for Sinop: no "
 "cultural-role, birth-register or resident-discrimination fact appears in the attached sources for this "
 "province.")
r['outOfScopeNotes'] = vis(CORE_OUTSCOPE.format(name='Sinop'))
r['blindSummary'] = vis(CORE_SUMMARY_INTRO.format(name='this province')) + vis(
 "As documented nationally, the visitor risk assessment: a draft judicial package leaked in October 2025 would "
 "carry prison terms of up to three years for conduct deemed contrary to biological sex and general morality, up "
 "to four years for participation in same-sex engagement or marriage ceremonies (same-sex marriage is not "
 "recognised, so such ceremonies are symbolic \u2014 the partner-travel exposure), raise the gender-care age floor "
 "to twenty-five with mandatory infertility conditions, and remove civil-status recognition of gender change. The "
 "principal national LGBTI report (February 2026) called the previous year's hostility explicit national policy, "
 "with three hate-motivated killings in which trans victims were over-represented, 89 ill-treatment cases mostly "
 "tied to breaking up gatherings, and 313 detentions; pride assemblies have been banned in the largest city and "
 "other cities in most years since 2015.")
r['blindTangential'] = vis(
 "Parent-nation policy turbulence: the October 2025 package is a leaked draft rather than enacted law, and "
 "fifteen local LGBT groups plus the national medical association objected to it. The monitoring counts \u2014 "
 "one organisation closed, three hate-motivated killings with trans victims over-represented, 89 ill-treatment "
 "cases and 313 detentions \u2014 were logged countrywide rather than per province, so they describe national "
 "practice, not provincial choice. Enforcement and litigation flux: pride events have also been repeatedly "
 "blocked by provincial governors, including simultaneous bans in three cities in June 2019; in June 2025 blanket "
 "bans against the pride marches brought over 90 arbitrary detentions and prosecutions of 92 people continuing at "
 "year's end; and a court ordered the dissolution of a young LGBTI association in December 2025.")
r['blindLocalsOnly'] = vis(
 "Resident-facing facts from the national overview: openly LGBTQ people are barred from military service under a "
 "'psychosexual illness' definition; transgender people have been able to change their legal gender since 1988; "
 "and in June 2025 the national medicines agency banned the prescription and supply of hormones for "
 "gender-affirming procedures for people under 21. No province-specific resident data is recorded for this "
 "province: no cultural-role, birth-register or resident-discrimination fact appears in the attached sources for "
 "this province.")
r['blindOutOfScope'] = vis(CORE_OUTSCOPE.format(name='this province'))
r['blindSourceSummaries'] = [
 "Rights-organisation news release (29 October 2025): a leaked draft of an omnibus judicial package would amend "
 "the penal and civil codes to criminalise conduct 'contrary to biological sex and general morality' (up to three "
 "years; participation in same-sex ceremonies up to four years), raise the minimum age for gender-affirming care "
 "from 18 to 25 with mandatory infertility and multi-evaluation hurdles, and imprison providers (up to seven "
 "years) and patients (up to three years); fifteen LGBT groups and the national medical association object. "
 "National framework; no province-specific provision.",
 "National overview page, the framework a trans visitor stands under in this province: homosexuality was "
 "decriminalised in 1858, legal gender change has been possible since 1988, but same-sex marriage is not "
 "recognised and LGBTQ people are barred from serving openly in the military; pride events have been repeatedly "
 "blocked by governors, including the 2015\u20132018 parades in the largest city and simultaneous bans in three "
 "cities on 14 June 2019; a proposal to criminalise publicly encouraging behaviour contrary to biological sex "
 "with a one-to-three-year prison sentence was ultimately not included in the 2026 package. This provincial "
 "record makes no province-specific claim; the page supports the national-framework claims.",
 "Country report (2025/26): in June 2025 blanket bans were issued against the pride marches, police used unlawful "
 "force, over 90 people were arbitrarily detained, and prosecutions of 92 people continued at year's end; in "
 "December 2025 a court ordered the dissolution of a young LGBTI association over 'obscene' images incompatible "
 "with society's moral values; three draft law packages targeting LGBTI people were made public in 2025 \u2014 "
 "criminalising LGBTI identity expression and consensual same-sex relations and making legal gender recognition "
 "nearly impossible \u2014 though they were not submitted to parliament. No province-specific incident documented."
]
r['notes'] = ("Split from current_summary plus three national source claims: province-level null finding and the "
 "visitor-facing national framework (penalties, ceremony exposure, care age floor, recognition removal, "
 "enforcement reality) to summary; leaked-draft turbulence, group objections, governor-blocked pride history and "
 "enforcement/litigation flux to tangentialFactors; military bar, gender-change pathway, hormone-supply ban and "
 "no-province-data statement to localsOnly; unresolved draft, absence-not-guarantee and no border/documents-or-"
 "marriage modality caveats to outOfScopeNotes. current_tangential, current_localsOnly, current_outOfScope were "
 "empty.")
records.append(r)

# ---------------------------------------------------------------------------
# 6. TUR/Sivas
r = {}
r['who'] = 'TUR/Sivas'
r['summary'] = vis(CORE_SUMMARY_INTRO.format(name='Sivas')) + vis(CORE_RISK)
r['tangentialFactors'] = vis(
 "Parent-nation policy turbulence: the October 2025 package is a leaked draft rather than enacted law, and the "
 "package that passed in 2026 did not carry the LGBTI-discriminatory provisions, leaving only symbolic same-sex "
 "weddings possible; fifteen LGBT groups plus the Turkish Medical Association objected to the draft, and early "
 "2026 press reports described the government considering legislation criminalising public advocacy of behaviour "
 "contrary to biological sex. Enforcement and litigation flux: three activists were remanded on 29 June 2025 "
 "under the assembly law and released on 8 August pending trial, while prosecutions of 92 people continued at "
 "year's end; a court in a western city ordered the dissolution of a young LGBTI association in December 2025. "
 "The monitoring counts \u2014 one organisation closed, three hate-motivated killings with trans victims "
 "over-represented, 89 ill-treatment cases and 313 detentions \u2014 were logged countrywide rather than per "
 "province, so they describe national practice, not provincial choice; the country ranked 47th of 49 in a 2026 "
 "regional LGBTI-rights league table, near the bottom among regional neighbours.")
r['localsOnly'] = vis(
 "Resident-facing facts from the national overview: openly LGBTQ people are barred from military service, where a "
 "health regulation defines homosexuality as a 'psychosexual illness' and conscripts who declare it must provide "
 "photographic proof, with the resulting 'unfit report' able to leak and fuel later discrimination in public "
 "life; transgender people have been able to change their legal gender since 1988 with sex-reassignment surgery, "
 "medical examination and court permission; same-sex marriage, civil unions and domestic partnerships are not "
 "recognised. No province-specific resident data is recorded for Sivas: no cultural-role, birth-register or "
 "resident-discrimination fact appears in the attached sources for this province.")
r['outOfScopeNotes'] = vis(CORE_OUTSCOPE.format(name='Sivas'))
r['blindSummary'] = vis(CORE_SUMMARY_INTRO.format(name='this province')) + vis(
 "As documented nationally, the visitor risk assessment: a draft judicial package leaked in October 2025 would "
 "carry prison terms of up to three years for conduct deemed contrary to biological sex and general morality, up "
 "to four years for participation in same-sex engagement or marriage ceremonies (same-sex marriage is not "
 "recognised, so such ceremonies are symbolic \u2014 the partner-travel exposure), raise the gender-care age floor "
 "to twenty-five with mandatory infertility conditions, and remove civil-status recognition of gender change. The "
 "principal national LGBTI report (February 2026) called the previous year's hostility explicit national policy, "
 "with three hate-motivated killings in which trans victims were over-represented, 89 ill-treatment cases mostly "
 "tied to breaking up gatherings, and 313 detentions; pride assemblies have been banned in the largest city and "
 "other cities in most years since 2015.")
r['blindTangential'] = vis(
 "Parent-nation policy turbulence: the October 2025 package is a leaked draft rather than enacted law, and the "
 "package that passed in 2026 did not carry the LGBTI-discriminatory provisions, leaving only symbolic same-sex "
 "weddings possible; fifteen local LGBT groups plus the national medical association objected to the draft, and "
 "early 2026 press reports described the government considering legislation criminalising public advocacy of "
 "behaviour contrary to biological sex. Enforcement and litigation flux: three activists were remanded on 29 June "
 "2025 under the assembly law and released on 8 August pending trial, while prosecutions of 92 people continued "
 "at year's end; a court ordered the dissolution of a young LGBTI association in December 2025. The monitoring "
 "counts \u2014 one organisation closed, three hate-motivated killings with trans victims over-represented, 89 "
 "ill-treatment cases and 313 detentions \u2014 were logged countrywide rather than per province, so they describe "
 "national practice, not provincial choice; the country ranked near the bottom of a 2026 regional LGBTI-rights "
 "league table among regional neighbours.")
r['blindLocalsOnly'] = vis(
 "Resident-facing facts from the national overview: openly LGBTQ people are barred from military service, where a "
 "health regulation defines homosexuality as a 'psychosexual illness' and conscripts who declare it must provide "
 "photographic proof, with the resulting 'unfit report' able to leak and fuel later discrimination in public "
 "life; transgender people have been able to change their legal gender since 1988 with sex-reassignment surgery, "
 "medical examination and court permission; same-sex marriage, civil unions and domestic partnerships are not "
 "recognised. No province-specific resident data is recorded for this province: no cultural-role, birth-register "
 "or resident-discrimination fact appears in the attached sources for this province.")
r['blindOutOfScope'] = vis(CORE_OUTSCOPE.format(name='this province'))
r['blindSourceSummaries'] = [
 "Rights-organisation news release (29 October 2025): a leaked draft of an omnibus judicial package would amend "
 "the penal and civil codes to criminalise conduct 'contrary to biological sex and general morality' (up to three "
 "years; participation in same-sex ceremonies up to four years), raise the minimum age for gender-affirming care "
 "from 18 to 25 with mandatory infertility and multi-evaluation hurdles, and imprison providers (up to seven "
 "years) and patients (up to three years); fifteen LGBT groups and the national medical association object. "
 "National framework; no province-specific provision.",
 "National overview page, the framework every province stands under: homosexuality has not been a criminal "
 "offence since 1858, transgender people have been able to change their legal gender since 1988 with surgery, "
 "medical examination and court permission, and no comprehensive law prohibits discrimination on grounds of "
 "sexual orientation or gender identity; openly LGBTQ people are barred from military service under an illness "
 "definition with photographic proof and a leakable report; same-sex marriage, civil unions and domestic "
 "partnerships are not recognised; when the package passed in 2026 the anti-LGBTQ provisions were removed "
 "leaving only symbolic same-sex weddings; pride events have been banned in the largest city and other cities "
 "since 2015 with police using tear gas, water cannons and mass detentions; early-2026 press reports described "
 "legislation criminalising public advocacy of behaviour contrary to biological sex, and a 2026 regional rights "
 "ranking placed the country near the bottom of its regional table. National framework; no province-specific "
 "finding.",
 "Country report (2025/26): in June 2025 blanket bans against the pride marches, police use of unlawful force and "
 "over 90 arbitrary detentions; three activists were remanded on 29 June 2025 under the assembly law and released "
 "on 8 August pending trial, while prosecutions of 92 people continued at year's end; in December 2025 a court "
 "ordered the dissolution of a young LGBTI association. The record evidences the national enforcement climate of "
 "blanket bans plus case-by-case prosecutions that applies to provincial authorities everywhere."
]
r['notes'] = ("Split from current_summary plus three national source claims: province-level null finding and the "
 "visitor-facing national framework (penalties, ceremony exposure, care age floor, recognition removal, "
 "enforcement reality) to summary; leaked-draft turbulence, 2026 package outcome, group objections, advocacy-law "
 "reports, remands and ranking-with-neighbours to tangentialFactors; military-service bar, gender-recognition "
 "process, partnership non-recognition and no-province-data statement to localsOnly; unresolved draft, "
 "absence-not-guarantee and no border/documents-or-marriage modality caveats to outOfScopeNotes. "
 "current_tangential, current_localsOnly, current_outOfScope were empty.")
records.append(r)

# ---------------------------------------------------------------------------
# 7. TUR/Tekirdağ (model estimate)
r = {}
r['who'] = 'TUR/Tekirda\u011f'
r['summary'] = vis(
 "Model estimate (route 3, best-knowledge delta): positioned in the orbit of the country's largest city; scored "
 "relative to the national score (0.15) for Turkey. No province-specific measure, incident or institution "
 "concerning transgender visitors is documented for Tekirda\u011f; what a trans visitor here stands under is the "
 "national framework.") + vis(CORE_RISK)
r['tangentialFactors'] = vis(
 "Parent-nation policy turbulence: the October 2025 package is a leaked draft rather than enacted law, and the "
 "package that passed in 2026 did not carry the LGBTI-discriminatory provisions, leaving only symbolic same-sex "
 "weddings possible; fifteen LGBT groups plus the Turkish Medical Association objected to the draft, and early "
 "2026 press reports described the government considering legislation criminalising public advocacy of behaviour "
 "contrary to biological sex. Enforcement and litigation flux: in June 2025 blanket bans against the pride "
 "marches produced over 90 arbitrary detentions and prosecutions of 92 people continuing at year's end, with "
 "three activists remanded on 29 June 2025 under the assembly law and released on 8 August pending trial; a court "
 "in a western city ordered the dissolution of a young LGBTI association in December 2025. The monitoring counts "
 "\u2014 one organisation closed, three hate-motivated killings with trans victims over-represented, 89 "
 "ill-treatment cases and 313 detentions \u2014 were logged countrywide rather than per province, so they describe "
 "national practice, not provincial choice; the country ranked 47th of 49 in a 2026 regional LGBTI-rights league "
 "table, near the bottom among regional neighbours.")
r['localsOnly'] = vis(
 "Resident-facing facts from the national overview: openly LGBTQ people are barred from military service, where a "
 "health regulation defines homosexuality as a 'psychosexual illness' and conscripts who declare it must provide "
 "photographic proof, with the resulting 'unfit report' able to leak and fuel later discrimination in public "
 "life; transgender people have been able to change their legal gender since 1988 with sex-reassignment surgery, "
 "medical examination and court permission; same-sex marriage, civil unions and domestic partnerships are not "
 "recognised. No province-specific resident data is recorded for Tekirda\u011f: no cultural-role, birth-register "
 "or resident-discrimination fact appears in the attached sources for this province.")
r['outOfScopeNotes'] = vis(
 "The record is a model estimate: the underlying best-knowledge delta and route-3 method are not independently "
 "verifiable from this record, and no provincial enforcement series exists to check against. The October 2025 "
 "package is a leaked draft, so its enactment outcome is unresolved. No province-specific measure, incident or "
 "institution is documented for Tekirda\u011f; the recorded absence of provincial documentation is not evidence "
 "that no divergence exists. No source addresses border-screening, document or identity-check practice for trans "
 "visitors to this province, and no marriage or partner-travel information specific to this province is recorded "
 "beyond the national recognition rules.")
r['blindSummary'] = vis(
 "Model estimate (route 3, best-knowledge delta): positioned in the orbit of the country's largest city; scored "
 "relative to the national score (0.15) for the parent nation. No province-specific measure, incident or "
 "institution concerning transgender visitors is documented for this province; what a trans visitor here stands "
 "under is the national framework.") + vis(
 "As documented nationally, the visitor risk assessment: a draft judicial package leaked in October 2025 would "
 "carry prison terms of up to three years for conduct deemed contrary to biological sex and general morality, up "
 "to four years for participation in same-sex engagement or marriage ceremonies (same-sex marriage is not "
 "recognised, so such ceremonies are symbolic \u2014 the partner-travel exposure), raise the gender-care age floor "
 "to twenty-five with mandatory infertility conditions, and remove civil-status recognition of gender change. The "
 "principal national LGBTI report (February 2026) called the previous year's hostility explicit national policy, "
 "with three hate-motivated killings in which trans victims were over-represented, 89 ill-treatment cases mostly "
 "tied to breaking up gatherings, and 313 detentions; pride assemblies have been banned in the largest city and "
 "other cities in most years since 2015.")
r['blindTangential'] = vis(
 "Parent-nation policy turbulence: the October 2025 package is a leaked draft rather than enacted law, and the "
 "package that passed in 2026 did not carry the LGBTI-discriminatory provisions, leaving only symbolic same-sex "
 "weddings possible; fifteen local LGBT groups plus the national medical association objected to the draft, and "
 "early 2026 press reports described the government considering legislation criminalising public advocacy of "
 "behaviour contrary to biological sex. Enforcement and litigation flux: in June 2025 blanket bans against the "
 "pride marches produced over 90 arbitrary detentions and prosecutions of 92 people continuing at year's end, "
 "with three activists remanded on 29 June 2025 under the assembly law and released on 8 August pending trial; a "
 "court ordered the dissolution of a young LGBTI association in December 2025. The monitoring counts \u2014 one "
 "organisation closed, three hate-motivated killings with trans victims over-represented, 89 ill-treatment cases "
 "and 313 detentions \u2014 were logged countrywide rather than per province, so they describe national practice, "
 "not provincial choice; the country ranked near the bottom of a 2026 regional LGBTI-rights league table among "
 "regional neighbours.")
r['blindLocalsOnly'] = vis(
 "Resident-facing facts from the national overview: openly LGBTQ people are barred from military service, where a "
 "health regulation defines homosexuality as a 'psychosexual illness' and conscripts who declare it must provide "
 "photographic proof, with the resulting 'unfit report' able to leak and fuel later discrimination in public "
 "life; transgender people have been able to change their legal gender since 1988 with sex-reassignment surgery, "
 "medical examination and court permission; same-sex marriage, civil unions and domestic partnerships are not "
 "recognised. No province-specific resident data is recorded for this province: no cultural-role, birth-register "
 "or resident-discrimination fact appears in the attached sources for this province.")
r['blindOutOfScope'] = vis(
 "The record is a model estimate: the underlying best-knowledge delta and route-3 method are not independently "
 "verifiable from this record, and no provincial enforcement series exists to check against. The October 2025 "
 "package is a leaked draft, so its enactment outcome is unresolved. No province-specific measure, incident or "
 "institution is documented for this province; the recorded absence of provincial documentation is not evidence "
 "that no divergence exists. No source addresses border-screening, document or identity-check practice for trans "
 "visitors to this province, and no marriage or partner-travel information specific to this province is recorded "
 "beyond the national recognition rules.")
r['blindSourceSummaries'] = [
 "Rights-organisation news release (29 October 2025): a leaked draft of an omnibus judicial package would amend "
 "the penal and civil codes to criminalise conduct 'contrary to biological sex and general morality' (up to three "
 "years; participation in same-sex ceremonies up to four years), raise the minimum age for gender-affirming care "
 "from 18 to 25 with mandatory infertility and multi-evaluation hurdles, and imprison providers (up to seven "
 "years) and patients (up to three years); fifteen LGBT groups and the national medical association object. "
 "National framework; no province-specific provision.",
 "National overview page, the framework every province stands under: homosexuality has not been a criminal "
 "offence since 1858, transgender people have been able to change their legal gender since 1988 with surgery, "
 "medical examination and court permission, and no comprehensive law prohibits discrimination on grounds of "
 "sexual orientation or gender identity; openly LGBTQ people are barred from military service under an illness "
 "definition with photographic proof and a leakable report; same-sex marriage, civil unions and domestic "
 "partnerships are not recognised; when the package passed in 2026 the anti-LGBTQ provisions were removed "
 "leaving only symbolic same-sex weddings; pride events have been banned in the largest city and other cities "
 "since 2015 with police using tear gas, water cannons and mass detentions; early-2026 press reports described "
 "legislation criminalising public advocacy of behaviour contrary to biological sex, and a 2026 regional rights "
 "ranking placed the country near the bottom of its regional table. National framework; no province-specific "
 "finding.",
 "Country report (2025/26): in June 2025 blanket bans against the pride marches, police use of unlawful force and "
 "over 90 arbitrary detentions; three activists were remanded on 29 June 2025 under the assembly law and released "
 "on 8 August pending trial, while prosecutions of 92 people continued at year's end; in December 2025 a court "
 "ordered the dissolution of a young LGBTI association. The record evidences the national enforcement climate "
 "that applies to provincial authorities everywhere, including near the largest city."
]
r['notes'] = ("Split from current_summary (model-estimate stub) plus three national source claims: estimate framing "
 "and the visitor-facing national framework to summary; leaked-draft turbulence, 2026 package outcome, group "
 "objections, remands, ranking-with-neighbours and countrywide-count framing to tangentialFactors; military bar, "
 "gender-recognition process, partnership non-recognition and no-province-data statement to localsOnly; "
 "estimate-unverifiable, unresolved draft, absence-not-guarantee and no border/documents-or-marriage modality "
 "caveats to outOfScopeNotes. current_tangential, current_localsOnly, current_outOfScope were empty.")
records.append(r)

# ---------------------------------------------------------------------------
# 8. TUR/Tokat
r = {}
r['who'] = 'TUR/Tokat'
r['summary'] = vis(
 "No trans-specific statute, enforcement pattern or incident documentation exists for Tokat; that absence is "
 "recorded as absence of documented divergence \u2014 not as evidence of local permissiveness: the nationwide "
 "framework governs here as in every province. As documented nationally: a judicial package leaked in October "
 "2025 would make conduct judged contrary to biological sex or general morality punishable by up to three years, "
 "criminalise same-sex engagement or marriage ceremonies (up to four years), and bar gender-affirming care under "
 "age twenty-five behind a permanent-infertility assessment, with patients and providers exposed to prosecution; "
 "civil-society groups and the national medical association protested, and an established human-rights court "
 "precedent is invoked against it.") + vis(
 "Practical safety: the 2025 report of the country's longest-running LGBTI monitoring body describes hostility "
 "becoming explicit state policy, with 'family' directives to public institutions, the first closure of an LGBTI "
 "organisation in years, and hundreds of recorded rights violations including three hate-motivated killings and "
 "89 torture or ill-treatment cases; since 2015 authorities have banned pride assemblies in the largest city and "
 "other cities in most years with tear gas, water cannons and mass detentions against participants, and the "
 "largest city's pride was again banned for a tenth consecutive year \u2014 a framework under which any visible "
 "LGBT assembly in this province would be policed.")
r['tangentialFactors'] = vis(
 "Parent-nation policy turbulence: the October 2025 package is a leaked draft rather than enacted law, and an "
 "established human-rights court precedent is invoked against it; the recorded violation counts \u2014 six "
 "right-to-life cases including three hate-motivated killings, 89 torture or ill-treatment violations, 313 "
 "deprivations of liberty with 299 detention decisions, and expression violations rising from 216 to 540 \u2014 "
 "are country-wide figures from the monitoring body with no provincial breakdown. National climate: government "
 "and conservative opposition politicians' discriminatory speech, denigrating LGBT communities on the pretext of "
 "promoting family values, has been documented as putting LGBT people at risk \u2014 a national hatred-climate "
 "factor rather than a Tokat-specific finding.")
r['localsOnly'] = vis(
 "Resident-facing: because marriage eligibility is determined by the gender recorded in the civil registry "
 "rather than by trans status, a person who has legally changed registered gender may marry a partner of the "
 "opposite registered gender, while same-sex marriage, civil unions and adoption remain unavailable; legal gender "
 "change has been possible since 1988 with surgery and court approval, and no comprehensive law prohibits "
 "discrimination on grounds of sexual orientation or gender identity. No province-specific resident data is "
 "recorded for Tokat: no cultural-role, birth-register or resident-discrimination fact appears in the attached "
 "sources for this province.")
r['outOfScopeNotes'] = vis(
 "The October 2025 package is a leaked draft, so its enactment outcome is unresolved, and no provincial "
 "enforcement series exists: the nationwide framework is the whole documented picture for Tokat, and the "
 "recorded absence of provincial divergence is not evidence that no divergence exists. No source addresses "
 "border-screening, document or identity-check practice for trans visitors to this province, and no marriage or "
 "partner-travel information specific to this province is recorded beyond the national recognition and ceremony "
 "rules.")
r['blindSummary'] = vis(
 "No trans-specific statute, enforcement pattern or incident documentation exists for this province; that "
 "absence is recorded as absence of documented divergence \u2014 not as evidence of local permissiveness: the "
 "nationwide framework governs here as in every province. As documented nationally: a judicial package leaked in "
 "October 2025 would make conduct judged contrary to biological sex or general morality punishable by up to "
 "three years, criminalise same-sex engagement or marriage ceremonies (up to four years), and bar gender-affirming "
 "care under age twenty-five behind a permanent-infertility assessment, with patients and providers exposed to "
 "prosecution; civil-society groups and the national medical association protested, and an established "
 "human-rights court precedent is invoked against it.") + vis(
 "Practical safety: the 2025 report of the country's longest-running LGBTI monitoring body describes hostility "
 "becoming explicit national policy, with 'family' directives to public institutions, the first closure of an "
 "LGBTI organisation in years, and hundreds of recorded rights violations including three hate-motivated "
 "killings and 89 torture or ill-treatment cases; since 2015 authorities have banned pride assemblies in the "
 "largest city and other cities in most years with tear gas, water cannons and mass detentions against "
 "participants, and the largest city's pride was again banned for a tenth consecutive year \u2014 a framework "
 "under which any visible LGBT assembly in this province would be policed.")
r['blindTangential'] = vis(
 "Parent-nation policy turbulence: the October 2025 package is a leaked draft rather than enacted law, and an "
 "established human-rights court precedent is invoked against it; the recorded violation counts \u2014 six "
 "right-to-life cases including three hate-motivated killings, 89 torture or ill-treatment violations, 313 "
 "deprivations of liberty with 299 detention decisions, and expression violations rising from 216 to 540 \u2014 "
 "are country-wide figures from the monitoring body with no provincial breakdown. National climate: government "
 "and conservative opposition politicians' discriminatory speech, denigrating LGBT communities on the pretext "
 "of promoting family values, has been documented as putting LGBT people at risk \u2014 a national hatred-climate "
 "factor rather than a province-specific finding.")
r['blindLocalsOnly'] = vis(
 "Resident-facing: because marriage eligibility is determined by the gender recorded in the civil registry "
 "rather than by trans status, a person who has legally changed registered gender may marry a partner of the "
 "opposite registered gender, while same-sex marriage, civil unions and adoption remain unavailable; legal gender "
 "change has been possible since 1988 with surgery and court approval, and no comprehensive law prohibits "
 "discrimination on grounds of sexual orientation or gender identity. No province-specific resident data is "
 "recorded for this province: no cultural-role, birth-register or resident-discrimination fact appears in the "
 "attached sources for this province.")
r['blindOutOfScope'] = vis(
 "The October 2025 package is a leaked draft, so its enactment outcome is unresolved, and no provincial "
 "enforcement series exists: the nationwide framework is the whole documented picture for this province, and "
 "the recorded absence of provincial divergence is not evidence that no divergence exists. No source addresses "
 "border-screening, document or identity-check practice for trans visitors to this province, and no marriage or "
 "partner-travel information specific to this province is recorded beyond the national recognition and ceremony "
 "rules.")
r['blindSourceSummaries'] = [
 "Rights-organisation news release (29 October 2025): a leaked draft of an omnibus judicial package would "
 "criminalise conduct 'contrary to biological sex and general morality' under a penal-code article (up to three "
 "years), raise the minimum age for gender-affirming care to 25, expose trans people, care providers, "
 "civil-society organisations and journalists to charges, and penalise same-sex engagement or marriage "
 "ceremonies (up to four years). National framework; no province-specific provision.",
 "National overview page: transgender people have been able to change their legal gender since 1988 with surgery "
 "and court approval; no comprehensive law prohibits discrimination on grounds of sexual orientation or gender "
 "identity; same-sex marriage, civil unions and adoption are unavailable; because marriage eligibility is "
 "determined by the gender recorded in the civil registry rather than by trans status, a person who has legally "
 "changed registered gender may marry a partner of the opposite registered gender; when the package passed in "
 "2026 the discriminating provisions were removed, making only symbolic same-sex weddings possible; since 2015 "
 "authorities have banned pride events in the largest city and other cities in most years with tear gas, water "
 "cannons and mass detentions against those who attempt to assemble. This page supplies the framework under "
 "which any visible LGBT assembly in this province would be policed.",
 "Annual country report (covering 2024): the government and conservative opposition parties regularly use "
 "discriminatory speech amounting to hate speech against LGBT communities on the pretext of promoting family "
 "values, putting LGBT people at risk; the largest city's pride was banned for a tenth consecutive year, and "
 "many cities across the country impose similar bans, so provincial authorities operate within a nationwide "
 "pattern in which visible LGBT assembly is routinely banned and policed."
]
r['notes'] = ("Split from current_summary plus three national source claims: province-level absence framing and the "
 "visitor-facing national framework (penalties, ceremony exposure, care age floor, court-precedent invocation, "
 "enforcement reality with pride-ban framework) to summary; leaked-draft turbulence, monitoring counts and "
 "hatred-climate commentary to tangentialFactors; civil-registry marriage-eligibility rule, gender-change "
 "pathway, partnership non-recognition and no-province-data statement to localsOnly; unresolved draft, "
 "no-provincial-enforcement-series and no border/documents-or-marriage modality caveats to outOfScopeNotes. "
 "current_tangential, current_localsOnly, current_outOfScope were empty.")
records.append(r)

# ---------------------------------------------------------------------------
# Merge-first write after EACH record (keep other whos already in file).
for i, rec in enumerate(records):
    if OUT.exists():
        data = json.loads(OUT.read_text(encoding='utf-8'))
    else:
        data = {'rewrites': []}
    data['rewrites'] = [x for x in data['rewrites'] if x.get('who') != rec['who']]
    data['rewrites'].append(rec)
    data['rewrites'].sort(key=lambda x: x['who'])
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding='utf-8')
    print(f"wrote record {i+1}/{len(records)}: {rec['who']} (total {len(data['rewrites'])})")
print("done")