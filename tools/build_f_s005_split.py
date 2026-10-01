#!/usr/bin/env python3
"""Build data/split_out/f-s005.json (four-field split + blind mirrors) from the s005 batch.
Merge-first write after each record (loads existing file, appends, dumps).
Self-gate: python3 tools/check_blind.py --file data/split_out/f-s005.json
"""
import json
from pathlib import Path

OUT = Path('data/split_out/f-s005.json')

recs = []

# --------------------------------------------------------------------------
# 1. country:JOR
recs.append(dict(
who='country:JOR',
summary=("<p>Jordan demands real caution from trans visitors — the safest of the Levantine Arab states by a clear margin, but on a "
 "deteriorating trajectory. Same-sex intimacy was decriminalised in 1951, and courts have granted legal gender recognition in "
 "individual cases (the 2014 Court of Cassation ruling — though justified by reclassifying the plaintiff as intersex). There is "
 "no statute criminalising gender expression itself.</p>"
 "<p>The deterioration is documented: Cairo 52 reports a notable rise in targeting of transgender individuals and spaces by both "
 "security forces and civilians, using Ottoman/British-era morality laws; Jordanian security forces coerced queer community spaces "
 "into complete cessation of activities; the 2023 cybercrime law (“inciting immorality”) gives authorities a digital tool against "
 "LGBT expression; and gender-affirming surgery is criminalised for trans people (Article 8, Medical and Health Liability Law) "
 "while permitted for intersex people. In 2021 security forces arrested 14 people at a private party.</p>"
 "<p>For a visitor: no legal exposure for gender expression per se, but morality-law discretion, shuttered community "
 "infrastructure, and family-society hostility make outing dangerous.</p>"),
tangentialFactors=("<p>Neighbour-country comparison frames the mechanism: a 2024 human-rights report documents that several "
 "neighbouring states do not explicitly criminalise same-sex relations in some cases, yet authorities “legally” harass LGBT people "
 "via public-morality and debauchery laws — alternative legal avenues substitute for formal criminalisation, so decriminalisation "
 "on paper does not equal safety; the same mechanism operates in this country through morality-law discretion.</p>"
 "<p>Regional activism context from 2018: despite repression and stigma, LGBT people across the region are speaking out, building "
 "alliances and regional movements; a report annex catalogues the laws used to punish same-sex conduct and gender expression "
 "across the region.</p>"),
localsOnly=("<p>The criminalisation of gender-affirming surgery (Article 8, the medical liability law) and the case-by-case "
 "recognition rulings are resident-facing.</p>"
 "<p>Transgender residents lack a general legal-recognition pathway — recognition comes only through individual court cases — and "
 "cannot access sex-reassignment procedures domestically; the 2014 case involved a plaintiff who underwent such procedures "
 "abroad.</p>"),
outOfScopeNotes=("Unresolved: whether morality-law and cybercrime enforcement targets visitors in practice or is applied mainly to "
 "residents, and how border screening treats transgender travellers given the absence of a general legal-recognition pathway for "
 "them.\n"
 "Unverified: the current sources record no documented incidents involving trans visitors specifically; the documented "
 "deterioration trajectory runs through 2024."),
blindSummary=("<p>This nation demands real caution from trans visitors — the safest by a clear margin, but on a deteriorating "
 "trajectory. Same-sex intimacy was decriminalised in 1951, and courts have granted legal gender recognition in individual cases "
 "(the 2014 ruling of the courts — though justified by reclassifying the plaintiff as intersex). There is no statute criminalising "
 "gender expression itself.</p>"
 "<p>The deterioration is documented: a notable rise in targeting of transgender individuals and spaces by both security forces "
 "and civilians, using historic-era morality laws; national security forces coerced queer community spaces into complete cessation "
 "of activities; the 2023 cybercrime law (“inciting immorality”) gives authorities a digital tool against LGBT expression; and "
 "gender-affirming surgery is criminalised for trans people (Article 8, the medical liability law) while permitted for intersex "
 "people. In 2021 security forces arrested 14 people at a private party.</p>"
 "<p>For a visitor: no legal exposure for gender expression per se, but morality-law discretion, shuttered community "
 "infrastructure, and family-society hostility make outing dangerous.</p>"),
blindTangential=("<p>Neighbour-country comparison frames the mechanism: a 2024 human-rights report documents that several "
 "neighbouring states do not explicitly criminalise same-sex relations in some cases, yet authorities “legally” harass LGBT people "
 "via public-morality and debauchery laws — alternative legal avenues substitute for formal criminalisation, so decriminalisation "
 "on paper does not equal safety; the same mechanism operates in this nation through morality-law discretion.</p>"
 "<p>Regional activism context from 2018: despite repression and stigma, LGBT people across the region are speaking out, building "
 "alliances and regional movements; a report annex catalogues the laws used to punish same-sex conduct and gender expression "
 "across the region.</p>"),
blindLocalsOnly=("<p>The criminalisation of gender-affirming surgery (Article 8, the medical liability law) and the case-by-case "
 "recognition rulings are resident-facing.</p>"
 "<p>Transgender residents lack a general legal-recognition pathway — recognition comes only through individual court cases — and "
 "cannot access sex-reassignment procedures domestically; the 2014 case involved a plaintiff who underwent such procedures "
 "abroad.</p>"),
blindOutOfScope=("Unresolved: whether morality-law and cybercrime enforcement targets visitors in practice or is applied mainly to "
 "residents, and how border screening treats transgender travellers given the absence of a general legal-recognition pathway for "
 "them.\n"
 "Unverified: the current sources record no documented incidents involving trans visitors specifically; the documented "
 "deterioration trajectory runs through 2024."),
blindSourceSummaries=[
 "A country profile by a regional documentation group: new legislation curtails LGBTQ+ speech and digital access; security forces "
 "coerced queer community spaces into closing, pushing transgender and queer people to leave; intersex people can change legal "
 "gender markers but transgender people cannot, and gender-affirming healthcare is penalised for providers under medical-liability "
 "law.",
 "A profile by an international rights organisation (updated 12 Mar 2026): same-sex relations are NOT criminalised — this nation "
 "abolished the historic-era ban in 1951; no clear legal pathway for trans people to change gender markers (allowed 'in some "
 "cases'); gender-affirming surgery permitted for intersex people but criminalised for transgender people under Article 8 of the "
 "medical health-liability law (25) of 2018.",
 "A national rights report chapter (11 Jan 2024): authorities limited civic space in 2023 and enacted a new cybercrime law "
 "undermining free speech and privacy online; peaceful dissidents and journalists arrested and harassed under vague, abusive "
 "laws, with intrusive digital surveillance — the environment shaping online expression for visitors and locals alike.",
 "A regional documentation group's analysis of a 2014 court case: national legislation criminalises sex reassignment with "
 "penalties up to 10 years' imprisonment (except intersex cases); the plaintiff sought name and gender change from male to female "
 "in official records after undergoing hormone therapy and surgery abroad, since such procedures are unavailable domestically.",
 "An international rights report (6 Jun 2024): in this nation and neighbouring states, same-sex relations are not explicitly "
 "criminalised in some cases, yet authorities “legally” harass LGBT people via public-morality and debauchery laws — alternative "
 "legal avenues substitute for formal criminalisation, so decriminalisation on paper does not equal safety.",
 "A 2018 report on regional activism: despite repression and stigma, LGBT people across the region are speaking out, building "
 "alliances and regional movements; it includes an annex of laws used to punish same-sex conduct and gender expression across "
 "the region, with this nation among them.",
 "An international rights report (4 Dec 2023): national authorities systematically targeted LGBT rights activists in a "
 "coordinated crackdown on free expression and assembly around gender and sexuality; officials smeared activists online by "
 "sexual orientation and social-media users posted their photos with messages inciting violence — two LGBT organisation "
 "directors cited official intimidation.",
],
notes=("Split from current_summary and the seven source claims: visitor-risk core (decriminalisation baseline, morality-law and "
 "cybercrime enforcement mechanisms, security-force pressure on queer spaces, no gender-expression statute) to summary; "
 "neighbour-comparison (HRW pattern across several states) and 2018 regional-activism framing to tangentialFactors; surgery "
 "criminalisation, case-by-case recognition practice and domestic unavailability of procedures to localsOnly; visitor-application "
 "of the enforcement mechanisms and border-screening questions to outOfScopeNotes. current_tangential was empty; "
 "current_localsOnly and current_outOfScope preserved."),
))

# --------------------------------------------------------------------------
# 2. country:VEN
recs.append(dict(
who='country:VEN',
summary=("<p>Venezuela demands real caution from trans visitors. Nothing about gender expression is criminalised, but Venezuela "
 "has achieved no meaningful legal recognition for LGBTIQ+ people: no legal gender recognition, no anti-discrimination law "
 "covering gender identity, no hate-crime statute. Since the disputed July 2024 election, activists document unprecedented "
 "persecution of the LGBTQ community amid the broader repression wave, and arbitrary detention powers are used broadly against "
 "perceived dissidents.</p>"
 "<p>The capital, Caracas, has a small visible scene, and trans women have historically been a visible part of urban life, but "
 "the economic collapse means healthcare (including HRT access) is severely degraded, police are predatory toward everyone, and "
 "there is no institutional recourse. The risk profile for a visitor is less about trans-specific targeting and more about the "
 "combination of zero legal protection, arbitrary state power, and high general violence.</p>"),
tangentialFactors=("<p>The disputed July 2024 election is a political-context factor rather than a trans-specific one: the "
 "persecution activists describe runs alongside the wider repression wave, and the main opposition presidential candidate fled "
 "the country on 7 September 2024.</p>"
 "<p>Legislative and policy flux: an equal-marriage bill was set to be presented to the National Assembly in early 2014, with no "
 "later enactment recorded; and the regional asylum agency maintains a dedicated LGBTIQ+ conditions profile used for "
 "international protection decisions.</p>"),
localsOnly=("<p>The degraded healthcare, including HRT access, is resident-facing, and the post-2024 persecution wave primarily "
 "affects resident activists and communities.</p>"
 "<p>Resident-facing political facts: a 2023 poll recorded a majority of the public supporting equal rights for the LGBTIQ+ "
 "population, with most respondents familiar with the term; a transgender candidate ran for the national legislature in 2015; "
 "and an openly gay parliamentarian was declared a prisoner of conscience in 2015.</p>"),
outOfScopeNotes=("Unresolved: whether arbitrary detention and the wider repression wave would touch a trans visitor in practice, "
 "since the documented persecution is tied to the political crisis rather than trans-specific enforcement; general humanitarian "
 "and repression context affects all travellers, and the assessment reflects the trans-specific protection vacuum.\n"
 "Unverified: the current sources record no documented incidents specifically involving trans visitors."),
blindSummary=("<p>This nation demands real caution from trans visitors. Nothing about gender expression is criminalised, but the "
 "nation has achieved no meaningful legal recognition for LGBTIQ+ people: no legal gender recognition, no anti-discrimination "
 "law covering gender identity, no hate-crime statute. Since the disputed July 2024 election, activists document unprecedented "
 "persecution of the LGBTQ community amid the broader repression wave, and arbitrary detention powers are used broadly against "
 "perceived dissidents.</p>"
 "<p>The capital has a small visible scene, and trans women have historically been a visible part of urban life, but the economic "
 "collapse means healthcare (including HRT access) is severely degraded, police are predatory toward everyone, and there is no "
 "institutional recourse. The risk profile for a visitor is less about trans-specific targeting and more about the combination "
 "of zero legal protection, arbitrary official power, and high general violence.</p>"),
blindTangential=("<p>The disputed July 2024 election is a political-context factor rather than a trans-specific one: the "
 "persecution activists describe runs alongside the wider repression wave, and the main opposition presidential candidate fled "
 "the nation on 7 September 2024.</p>"
 "<p>Legislative and policy flux: an equal-marriage bill was set to be presented to the national legislature in early 2014, with "
 "no later enactment recorded; and the regional asylum agency maintains a dedicated LGBTIQ+ conditions profile used for "
 "international protection decisions.</p>"),
blindLocalsOnly=("<p>The degraded healthcare, including HRT access, is resident-facing, and the post-2024 persecution wave "
 "primarily affects resident activists and communities.</p>"
 "<p>Resident-facing political facts: a 2023 poll recorded a majority of the public supporting equal rights for the LGBTIQ+ "
 "population, with most respondents familiar with the term; a transgender candidate ran for the national legislature in 2015; "
 "and an openly gay parliamentarian was declared a prisoner of conscience in 2015.</p>"),
blindOutOfScope=("Unresolved: whether arbitrary detention and the wider repression wave would touch a trans visitor in practice, "
 "since the documented persecution is tied to the political crisis rather than trans-specific enforcement; general humanitarian "
 "and repression context affects all travellers, and the assessment reflects the trans-specific protection vacuum.\n"
 "Unverified: the current sources record no documented incidents specifically involving trans visitors."),
blindSourceSummaries=[
 "A news report (10 Sep 2024): LGBTQ people in this nation face unprecedented persecution after the disputed July 2024 election; "
 "the opposition presidential candidate fled the country on 7 Sep 2024 — persecution of LGBTQ people tied to the political "
 "crisis.",
 "A regional asylum agency country-focus profile (reference period through 2025): a dedicated LGBTIQ+ conditions profile of this "
 "nation used for international protection decisions.",
 "NOTE: a national guide on this country returned no extractable text at fetch time (image-based file).",
 "A news report (8 Aug 2015): this nation's first transgender candidate ran for the elected national legislature — a landmark "
 "trans political candidacy.",
 "A 2023 poll (2-3 Mar 2023): a majority of the public agrees the LGBTIQ+ population should have the same rights as other "
 "citizens; most know the term; some think same-sex orientation is innate.",
 "A blog record (31 Jan 2014): an equal-marriage bill was set to be presented to the elected national legislature that week — a "
 "legislative push with no later enactment recorded.",
 "A news report (13 Dec 2015): an international rights organisation declared the nation's first openly gay parliamentarian a "
 "prisoner of conscience held in custody — documented persecution of an openly gay politician.",
],
notes=("Split from current_summary and the seven source claims: the protection-vacuum visitor assessment and trans-specific risk "
 "profile to summary; disputed-election political-crisis context, 2014 equal-marriage bill flux and the asylum-agency baseline to "
 "tangentialFactors; degraded healthcare, post-2024 persecution impact, 2023 poll data and resident political visibility to "
 "localsOnly; detention-wave application to visitors and incident absence to outOfScopeNotes. current_tangential was empty; "
 "current_localsOnly and current_outOfScope preserved."),
))

# --------------------------------------------------------------------------
# 3. country:BOL
recs.append(dict(
who='country:BOL',
summary=("<p>Bolivia is workable for trans visitors — on paper a legal pioneer within this region. The 2016 Gender Identity Law "
 "was ground-breaking: legal gender recognition on the basis of self-declared identity (an administrative process, no surgery), "
 "and gender identity is an explicitly protected ground in anti-discrimination law. The constitution also names gender "
 "identity.</p>"
 "<p>Implementation lags the statute: the first national LGBTQ+ survey (2024) reveals significant exclusion in health, "
 "education, employment, and housing; social conservatism is strong outside the two largest cities (La Paz and Santa Cruz); and "
 "bureaucrats often resist applying the Gender Identity Law. There is no documented pattern of police targeting of trans people "
 "as such, and no traveler-facing restriction — but also limited effective protection outside major cities.</p>"),
tangentialFactors=("<p>Regional legal flux: a January 2018 advisory opinion of the Inter-American Court of Human Rights advanced "
 "gender recognition in the region, and in December 2020 the national civil registry began recognising 'free unions' of "
 "same-sex couples — developments that sit alongside the 2016 self-identification law.</p>"
 "<p>Legislative mixing: trans-rights advances were passed alongside contradictory heteronormative legislation because both "
 "organised religion and LGBT activists were party constituents; and an international baseline count places only a small number "
 "of countries as fully allowing LGBT military service.</p>"),
localsOnly=("<p>The Gender Identity Law's administrative process, and its uneven implementation by bureaucrats, are "
 "resident-facing; the first national survey (2024) exclusion data describes residents' lives.</p>"
 "<p>Resident-facing military facts: reporting documents that gay soldiers face discrimination and sanctions within the armed "
 "forces, while rights activists demand openness.</p>"),
outOfScopeNotes=("Unresolved: whether the anti-discrimination guarantees are effectively enforced for visitors outside the "
 "largest cities, where limited protection is documented.\n"
 "Unverified: the current sources record no documented pattern of police targeting of trans visitors specifically; the survey "
 "exclusion data describes residents' daily lives rather than visitor incidents."),
blindSummary=("<p>This nation is workable for trans visitors — on paper a legal pioneer within its region. The 2016 gender-identity "
 "law was ground-breaking: legal gender recognition on the basis of self-declared identity (an administrative process, no "
 "surgery), and gender identity is an explicitly protected ground in anti-discrimination law. The constitution also names gender "
 "identity.</p>"
 "<p>Implementation lags the statute: the first national LGBTQ+ survey (2024) reveals significant exclusion in health, "
 "education, employment, and housing; social conservatism is strong outside the two largest cities; and bureaucrats often resist "
 "applying the gender-identity law. There is no documented pattern of police targeting of trans people as such, and no "
 "traveler-facing restriction — but also limited effective protection outside major cities.</p>"),
blindTangential=("<p>Regional legal flux: a January 2018 advisory opinion of the regional rights court advanced gender "
 "recognition in the region, and in December 2020 the national civil registry began recognising 'free unions' of same-sex "
 "couples — developments that sit alongside the 2016 self-identification law.</p>"
 "<p>Legislative mixing: trans-rights advances were passed alongside contradictory heteronormative legislation because both "
 "organised religion and LGBT activists were party constituents; and an international baseline count places only a small number "
 "of nations as fully allowing LGBT military service.</p>"),
blindLocalsOnly=("<p>The 2016 gender-identity law's administrative process, and its uneven implementation by bureaucrats, are "
 "resident-facing; the first national survey (2024) exclusion data describes residents' lives.</p>"
 "<p>Resident-facing military facts: reporting documents that gay soldiers face discrimination and sanctions within the armed "
 "forces, while rights activists demand openness.</p>"),
blindOutOfScope=("Unresolved: whether the anti-discrimination guarantees are effectively enforced for visitors outside the "
 "largest cities, where limited protection is documented.\n"
 "Unverified: the current sources record no documented pattern of police targeting of trans visitors specifically; the survey "
 "exclusion data describes residents' daily lives rather than visitor incidents."),
blindSourceSummaries=[
 "A comparative-politics article (April 2024) on the expansion of trans rights: this nation prohibits gender-identity "
 "discrimination and passed a ground-breaking gender-identity law (2016, allowing name and marker change) despite low voter "
 "support; trans activists leveraged access to ruling-party legislators; contradictory heteronormative laws passed alongside "
 "because both organised religion and LGBT activists were party constituents.",
 "NOTE: not retrievable at research time (site error); the underlying December 2024 article covers this nation's first virtual "
 "survey revealing the great exclusion of LGBTI people.",
 "A 2011 foreign-government human-rights report: general assessment (arbitrary deprivation of life, prison conditions, "
 "corruption); the LGBT section documents the constitutional anti-discrimination guarantee and societal discrimination.",
 "A news report (Jul 2017): after a national trans military ban, only a small number of nations are believed to fully legalise "
 "LGBT military service — an international baseline for whether trans visitors or soldiers face service exclusion; this nation "
 "is not singled out in the text.",
 "A legal-profile page: the constitution prohibits discrimination and guarantees bodily integrity (arts. 15(II) and 45(V)); "
 "superseded by post-2016 law: the 2016 gender-identity law (self-ID), a January 2018 opinion of the regional rights court, and "
 "December 2020 civil-registry 'free union' recognition for same-sex couples.",
 "A news report (25 Aug 2014, Spanish): homosexuality is taboo in this nation's armed forces — gay soldiers report "
 "discrimination and sanctions, given anonymously; a local collective and rights activists demand openness.",
],
notes=("Split from current_summary, current_* fields and source claims: the self-ID legal baseline and traveller-facing "
 "implementation limits to summary; Inter-American Court opinion, civil-registry 'free union' recognition, legislative mixing "
 "and the international military-service baseline to tangentialFactors; administrative-process mechanics, survey exclusion data "
 "and armed-forces discrimination to localsOnly; enforcement and targeting questions to outOfScopeNotes. freshness_all "
 "supersession (post-2016 law status) is reflected via the claims in summary and tangential fields. current_tangential was "
 "empty; current_localsOnly and current_outOfScope preserved."),
))

# --------------------------------------------------------------------------
# 4. country:PRY
recs.append(dict(
who='country:PRY',
summary=("<p>Paraguay demands real caution from trans visitors — the most conservative country in its region. There is no legal "
 "gender recognition (ten lawsuits on trans name recognition remain pending, unresolved), no anti-discrimination law covering "
 "gender identity, and no hate-crime statute. AP documents that many LGBTQ+ people feel compelled to leave their hometowns "
 "due to discrimination, harassment, and gender-based violence; trans women face particular social rejection. Amnesty reports "
 "persistent structural discrimination and high gender-based violence.</p>"
 "<p>Nothing criminalises being trans, the capital, Asunción, has a small organised community, and there is no documented police "
 "targeting pattern — the risk is social hostility and a total protection vacuum rather than state persecution. Tourist traffic "
 "is low and there are no documented trans-visitor incidents.</p>"),
tangentialFactors=("<p>Regional legal framework: a January 2018 advisory opinion of the Inter-American Court of Human Rights "
 "holds that signatory states must allow same-sex marriage, and notes that this country alongside two neighbouring states "
 "recognises neither same-sex marriage nor unions; analysis after the ruling says the country must overcome difficulties "
 "adapting its laws to extend the right to marriage to everyone.</p>"
 "<p>Political climate: a ruling-party figure made reported anti-gay remarks in 2017, and the same period saw a push to burn "
 "books that do not promote 'traditional gender ideology' — elite-level hostility that colours public debate around LGBT "
 "issues.</p>"),
localsOnly=("<p>The ten pending gender-recognition lawsuits and the discrimination-law absence are resident-facing; the "
 "hometown-flight pattern describes residents.</p>"
 "<p>Resident-facing facts: the adoption statute does not explicitly bar same-sex couples or single people from adopting; two "
 "trans migrants were denied identity documents; and dozens of registered feminicides were documented in 2025.</p>"),
outOfScopeNotes=("Unresolved: the pending gender-recognition lawsuits have produced no final rulings, a communication before the "
 "international human-rights committee remains pending, and the discrimination-law absence is resident-facing so its direct "
 "application to visitors is untested.\n"
 "Unverified: no documented trans-visitor incidents appear in the current sources — tourist traffic is low, and recorded "
 "hostility is social rather than institutional persecution."),
blindSummary=("<p>This nation demands real caution from trans visitors — the most conservative country in its region. There is "
 "no legal gender recognition (ten lawsuits on trans name recognition remain pending, unresolved), no anti-discrimination law "
 "covering gender identity, and no hate-crime statute. As documented, many LGBTQ+ people feel compelled to leave their "
 "hometowns due to discrimination, harassment, and gender-based violence; trans women face particular social rejection. "
 "Persistent structural discrimination and high gender-based violence are documented.</p>"
 "<p>Nothing criminalises being trans, the capital has a small organised community, and there is no documented police targeting "
 "pattern — the risk is social hostility and a total protection vacuum rather than official persecution. Tourist traffic is low "
 "and there are no documented trans-visitor incidents.</p>"),
blindTangential=("<p>Regional legal framework: a January 2018 advisory opinion of the regional rights court holds that signatory "
 "states must allow same-sex marriage, and notes that this nation alongside two neighbouring states recognises neither same-sex "
 "marriage nor unions; analysis after the ruling says the nation must overcome difficulties adapting its laws to extend the "
 "right to marriage to everyone.</p>"
 "<p>Political climate: a ruling-party figure made reported anti-gay remarks in 2017, and the same period saw a push to burn "
 "books that do not promote 'traditional gender ideology' — elite-level hostility that colours public debate around LGBT "
 "issues.</p>"),
blindLocalsOnly=("<p>The ten pending gender-recognition lawsuits and the discrimination-law absence are resident-facing; the "
 "hometown-flight pattern describes residents.</p>"
 "<p>Resident-facing facts: the adoption statute does not explicitly bar same-sex couples or single people from adopting; two "
 "trans migrants were denied identity documents; and dozens of registered feminicides were documented in 2025.</p>"),
blindOutOfScope=("Unresolved: the pending gender-recognition lawsuits have produced no final rulings, a communication before the "
 "international human-rights committee remains pending, and the discrimination-law absence is resident-facing so its direct "
 "application to visitors is untested.\n"
 "Unverified: no documented trans-visitor incidents appear in the current sources — tourist traffic is low, and recorded "
 "hostility is social rather than institutional persecution."),
blindSourceSummaries=[
 "A news report (Sep 2025): for this nation's transgender women, survival often means leaving home — discrimination, "
 "harassment and gender-based violence push trans women out of hometowns into migration and sex work.",
 "An international rights organisation's country page (2025-26): trans people face obstacles to legal identity-document "
 "recognition — two trans migrants were denied identity documents; an event honouring a trans rights defender who died in "
 "March was banned; plus dozens of registered feminicides in 2025 and an April bill to merge the women's ministry into a family "
 "ministry.",
 "A reporting service used for asylum decisions: the judiciary had yet to issue final rulings on ten lawsuits filed by trans "
 "people for legal name recognition — the plaintiffs (suits since 2016) awaited a decision from an international human-rights "
 "committee on their communications.",
 "A news report (20 Oct 2017): a ruling-party figure made reported crude anti-gay remarks about his son marrying another man "
 "(he later apologised); the report frames a push to burn books that do not promote 'traditional gender ideology'.",
 "A regional news report (10 Jan 2018): a regional rights court advisory opinion holds that signatory states must allow "
 "same-sex marriage; notes that this nation and two neighbouring states recognise neither same-sex marriage nor unions — the "
 "ruling binds this nation as a party though local law lagged.",
 "A national news report (30 May 2017): adoption analysis — the adoption statute does not explicitly bar same-sex couples or "
 "single people from adopting, a legal gap allowing same-sex adoption amid a society that still resists.",
 "A national news analysis: after the regional rights court ruling, people in this nation must overcome difficulties adapting "
 "the laws to extend the right to marriage to everyone.",
],
notes=("Split from current_summary and source claims: the visitor risk assessment (protection vacuum, social hostility, no "
 "trans-visitor incidents) to summary; Inter-American marriage framework, elite-level rhetoric and book-burning push to "
 "tangentialFactors; pending lawsuits, adoption gap, denied identity documents and feminicide data to localsOnly; "
 "litigation-unresolved status and incident absence to outOfScopeNotes. current_tangential was empty; current_localsOnly and "
 "current_outOfScope preserved."),
))

# --------------------------------------------------------------------------
# 5. country:GTM
recs.append(dict(
who='country:GTM',
summary=("<p>Guatemala demands real caution from trans visitors. Nothing criminalises being trans, but violence against LGBT "
 "people is severe and documented: Asociación Lambda's observatory recorded 147 cases of day-to-day violence and at least 29 "
 "murders of LGBTQIA+ people in 2022 — hundreds of incidents and dozens of deaths — with 35 victims saying they intended to "
 "flee the country. Guatemalan officials have "
 "explicitly excluded trans women from femicide-law protection on the grounds they are not “biological women.” There is no legal "
 "gender recognition and no SOGI hate-crime statute (a 2022 law actually increased penalties for “aggravated” LGBT visibility "
 "before being struck down).</p>"
 "<p>Congress has repeatedly advanced anti-LGBT initiatives (Law 5276, the 2022 “Life and Family Protection” bill, later "
 "shelved after protests). The community is organised (a local group such as Lambda, plus trans collectives) but under pressure. "
 "Tourist areas (Antigua, Atitlán) are accustomed to foreigners but not insulated from the general violence level.</p>"),
tangentialFactors=("<p>Regional legal framework: a 2017 advisory opinion of the Inter-American Court of Human Rights advanced "
 "gender recognition in four regional countries, including this one, with compliance still uncertain; a vociferous opposition "
 "movement defining gender in strictly binary terms is fomenting backlash in all four.</p>"
 "<p>Legislative flux: early-2022 bills sought to erase gender-identity protections and restrict legal recognition, and anti-trans "
 "initiatives have repeatedly advanced in the national legislature.</p>"),
localsOnly=("<p>The femicide-law exclusion of trans women and the absence of legal gender recognition are resident-facing; the "
 "documented violence toll — 147 recorded cases of day-to-day violence and at least 29 murders in 2022 (hundreds of incidents, "
 "dozens of deaths) — falls on residents.</p>"
 "<p>The organised community (a local group and trans collectives) operates under pressure from the repeated legislative "
 "attacks.</p>"),
outOfScopeNotes=("Unresolved: how the general violence level in communities outside the tourist areas applies to visitors is "
 "unquantified — general gang violence affects all travellers, and tourist areas are accustomed to foreigners but not "
 "insulated from it.\n"
 "Unverified: no documented trans-visitor incidents appear in the current sources, and the femicide-law exclusion is "
 "resident-facing though it signals institutional stance."),
blindSummary=("<p>This nation demands real caution from trans visitors. Nothing criminalises being trans, but violence against "
 "LGBT people is severe and documented: a local observatory recorded hundreds of cases of day-to-day violence and dozens of "
 "murders of LGBTQIA+ people in 2022, with victims saying they intended to flee the country. National officials have explicitly "
 "excluded trans women from femicide-law protection on the grounds they are not “biological women.” There is no legal gender "
 "recognition and no SOGI hate-crime statute (a 2022 law actually increased penalties for “aggravated” LGBT visibility before "
 "being struck down).</p>"
 "<p>The legislature has repeatedly advanced anti-LGBT initiatives (a 2022 family-protection bill, later shelved after "
 "protests). The community is organised, with a local group and trans collectives, but under pressure. Tourist areas are "
 "accustomed to foreigners but not insulated from the general violence level.</p>"),
blindTangential=("<p>Regional legal framework: a 2017 advisory opinion of the regional rights court advanced gender recognition "
 "in four regional nations, including this one, with compliance still uncertain; a vociferous opposition movement defining "
 "gender in strictly binary terms is fomenting backlash in all four.</p>"
 "<p>Legislative flux: early-2022 bills sought to erase gender-identity protections and restrict legal recognition, and anti-trans "
 "initiatives have repeatedly advanced in the national legislature.</p>"),
blindLocalsOnly=("<p>The femicide-law exclusion of trans women and the absence of legal gender recognition are resident-facing; "
 "the documented violence toll — hundreds of recorded cases of day-to-day violence and dozens of murders in 2022 — falls on "
 "residents.</p>"
 "<p>The organised community (a local group and trans collectives) operates under pressure from the repeated legislative "
 "attacks.</p>"),
blindOutOfScope=("Unresolved: how the general violence level in communities outside the tourist areas applies to visitors is "
 "unquantified — general gang violence affects all travellers, and tourist areas are accustomed to foreigners but not "
 "insulated from it.\n"
 "Unverified: no documented trans-visitor incidents appear in the current sources, and the femicide-law exclusion is "
 "resident-facing though it signals institutional stance."),
blindSourceSummaries=[
 "A reference article on transfemicide: documents killings of trans women; records that national governments have long excluded "
 "trans women from femicide protections — officials have justified this by stating that transgender women are not 'biological "
 "women' — the official exclusion underpinning the record's violence context.",
 "A foundation report (May 2024): the regional rights court's 2017 gender-identity opinion advanced legal gender recognition in "
 "four regional nations, but a vociferous opposition movement defining gender in strictly binary terms is fomenting backlash "
 "in all four.",
 "An international rights report (Jan 2022): documents legislative attacks on trans people, including bills that would erase "
 "gender-identity protections and restrict legal recognition.",
 "A regional news report (Jan 2018): regional nations including this one were urged to abide by the regional rights court "
 "ruling requiring marriage equality and gender recognition — compliance status uncertain.",
],
notes=("Split from current_summary and source claims: the documented violence and femicide-exclusion visitor assessment to "
 "summary; Inter-American gender-recognition framework and early-2022 anti-trans legislative flux to tangentialFactors; "
 "femicide-law exclusion, violence toll and community organisation to localsOnly; visitor-application of the violence level and "
 "incident absence to outOfScopeNotes. current_tangential was empty; current_localsOnly and current_outOfScope preserved."),
))

# --------------------------------------------------------------------------
# 6. country:HND
recs.append(dict(
who='country:HND',
summary=("<p>Honduras is dangerous for trans visitors. It is the site of the hemisphere's defining transfemicide case: Vicky "
 "Hernández, a trans woman and activist shot dead in 2009, whose case reached the regional Inter-American Court of Human Rights "
 "— which in 2021 found the Honduran state itself responsible for her death and for failing to investigate it as a bias crime. "
 "The ruling ordered reforms (including legal gender recognition, which Honduras has partially implemented), but violence "
 "against LGBT people remains at levels Amnesty called “epidemic,” driving mass asylum-seeking.</p>"
 "<p>Nothing criminalises being trans, and the Vicky Hernández ruling created formal obligations; a name-change process exists. "
 "But gangs, security forces, and social actors all contribute to a documented pattern of violence against trans women in "
 "particular, and prosecution remains rare.</p>"
 "<p>For a visitor: no legal exposure, but outing-violence probability is among the highest in the region, outside the two "
 "largest countries.</p>"),
tangentialFactors=("<p>Regional comparison: a rights-law report groups this nation with neighbouring El Salvador among the "
 "world's highest rates of violence against women and LGBTI persons, and regional nations have long excluded trans women from "
 "femicide-justice frameworks — the pattern that made this case the leading one of its kind.</p>"
 "<p>Justice-system context: documented impunity is driven by under-reporting, lack of police and prosecutor training, "
 "insufficient resources, and intentional case mishandling — the enforcement backdrop for anyone assessing risk.</p>"),
localsOnly=("<p>The court-ordered legal-gender-recognition reform (partially implemented) and the name-change process are "
 "resident-facing; the epidemic-level violence and mass asylum-seeking describe residents' situation.</p>"
 "<p>Resident-facing documentation: trans people have faced police assault, extortion and worse for years, and politically "
 "visible trans people have faced threats and attacks, with at least one organiser seeking asylum abroad.</p>"),
outOfScopeNotes=("Unresolved: how the documented gang and security-force violence applies to short-stay visitors in tourist "
 "contexts is not quantified in the current sources — gang violence affects everyone.\n"
 "Unverified: no documented trans-visitor incidents appear in the current sources; the state-responsibility finding covers an "
 "individual case and signals institutional accountability rather than a visitor-specific enforcement pattern."),
blindSummary=("<p>This nation is dangerous for trans visitors. It is the site of a defining transfemicide case: a trans woman "
 "and activist shot dead in 2009, whose case reached the regional rights court — which in 2021 found the nation itself "
 "responsible for her death and for failing to investigate it as a bias crime. The ruling ordered reforms (including legal "
 "gender recognition, which this nation has partially implemented), but violence against LGBT people remains at epidemic "
 "levels, driving mass asylum-seeking.</p>"
 "<p>Nothing criminalises being trans, and the ruling created formal obligations; a name-change process exists. But gangs, "
 "security forces, and social actors all contribute to a documented pattern of violence against trans women in particular, and "
 "prosecution remains rare.</p>"
 "<p>For a visitor: no legal exposure, but outing-violence probability is among the highest in the region, outside the two "
 "largest countries.</p>"),
blindTangential=("<p>Regional comparison: a rights-law report groups this nation with a neighbouring nation among the world's "
 "highest rates of violence against women and LGBTI persons, and regional nations have long excluded trans women from "
 "femicide-justice frameworks — the pattern that made this case the leading one of its kind.</p>"
 "<p>Justice-system context: documented impunity is driven by under-reporting, lack of police and prosecutor training, "
 "insufficient resources, and intentional case mishandling — the enforcement backdrop for anyone assessing risk.</p>"),
blindLocalsOnly=("<p>The court-ordered legal-gender-recognition reform (partially implemented) and the name-change process are "
 "resident-facing; the epidemic-level violence and mass asylum-seeking describe residents' situation.</p>"
 "<p>Resident-facing documentation: trans people have faced police assault, extortion and worse for years, and politically "
 "visible trans people have faced threats and attacks, with at least one organiser seeking asylum abroad.</p>"),
blindOutOfScope=("Unresolved: how the documented gang and security-force violence applies to short-stay visitors in tourist "
 "contexts is not quantified in the current sources — gang violence affects everyone.\n"
 "Unverified: no documented trans-visitor incidents appear in the current sources; the responsibility finding covers an "
 "individual case and signals institutional accountability rather than a visitor-specific enforcement pattern."),
blindSourceSummaries=[
 "A reference article: a general concept article with substantial content on this nation — a rights-group finding that "
 "regional nations exclude transgender women from femicide legal frameworks, and this nation's leading transfemicide case at "
 "the regional rights court.",
 "A rights-law report: this nation and a neighbouring nation among the world's highest rates of violence against women and "
 "LGBTI persons; trans women especially face major obstacles to justice; impunity driven by under-reporting, lack of police and "
 "prosecutor training, insufficient resources, and intentional case mishandling.",
 "NOTE: not retrievable at research time (access error); the underlying news feature covers the region's LGBT people being "
 "terrorised at home and fleeing for their lives.",
 "An international rights report (May 2009): police rape, assault and extortion of trans people — the shape of transgender "
 "lives in this nation and relevant domestic laws.",
 "A dated news archive index 2004-2011: an August 2004 church protest at official recognition of three gay groups; 2009-10 "
 "items (a young LGBT activist murdered, post-coup abuses); 2005 marriage and adoption-ban coverage.",
 "A 2021 foreign-government human-rights report: significant rights issues include violence and threats against LGBTQI+ "
 "persons, extrajudicial killings, torture, corruption, and lack of accountability for gender-based violence.",
 "A news report (25 Sep 2017): a trans activist and local-group co-founder ran for the national legislature; context — a 2017 "
 "primary win, an earlier run, and another trans activist seeking asylum abroad after threats and attacks in the capital.",
],
notes=("Split from current_summary and source claims: the transfemicide-case-based visitor assessment (no legal exposure but "
 "high outing-violence probability) to summary; regional femicide-framework comparison and justice-system impunity drivers to "
 "tangentialFactors; LGR reform status, name-change process, police-violence documentation and resident political visibility "
 "to localsOnly; gang-violence application to visitors and incident absence to outOfScopeNotes. current_tangential was empty; "
 "current_localsOnly and current_outOfScope preserved."),
))

# --------------------------------------------------------------------------
# 7. country:SLV
recs.append(dict(
who='country:SLV',
summary=("<p>El Salvador demands real caution from trans visitors — in an unusual transition. Historically it was among the "
 "world's most dangerous places for trans women (documented life expectancy of 35 years, among the lowest anywhere; the Camila "
 "Díaz Córdova case — a trans woman deported from the US and killed — became the first hate-crime homicide prosecution of its "
 "kind). Since 2022, President Bukele's gang crackdown collapsed the national homicide rate by ~98% (107 to 1.9 per 100k), "
 "dramatically reducing the gang violence that drove much anti-trans predation.</p>"
 "<p>The trade-off is a state of exception (an exceptional security regime) with mass arbitrary detention (tens of thousands "
 "imprisoned, over 75,000 reported, minimal due process) — a risk mechanism that falls on anyone police decide to target, "
 "including gender-nonconforming people, with no effective recourse. There is no legal gender recognition law (administrative "
 "name change only), no SOGI hate-crime statute, and no institutional protection infrastructure.</p>"),
tangentialFactors=("<p>Regional comparison: a 2020 human-rights report groups this nation with two neighbouring nations as "
 "failing to effectively address violence and entrenched discrimination against LGBT people, driving asylum claims abroad.</p>"
 "<p>Legislative and research context: 2015 legal-code reforms made bias-motivated killings punishable by long prison "
 "sentences; a 2024 longitudinal study profiles homicides against LGBTI+ people across two decades; and the first conviction "
 "came in 2020 — legal milestones that do not by themselves change the practical visitor risk.</p>"),
localsOnly=("<p>The administrative name-change-only process and the absent legal-gender-recognition law are resident-facing; "
 "the historical life-expectancy figure and the killing case described in the summary are resident-facing too.</p>"),
outOfScopeNotes=("Unresolved: whether the exceptional security regime is applied to trans visitors in practice — its "
 "trans-specific application is a risk mechanism, not a documented pattern, and the regime affects all travellers.\n"
 "Unverified: the sources document no trans-visitor incidents, and the historic danger figures describe residents' experience "
 "before the recent crackdown."),
blindSummary=("<p>This nation demands real caution from trans visitors — in an unusual transition. Historically it was among "
 "the world's most dangerous places for trans women (documented life expectancy among the lowest anywhere; a trans woman "
 "deported and killed became the first hate-crime homicide prosecution of its kind). Since 2022, a government gang crackdown "
 "collapsed the national homicide rate by ~98%, dramatically reducing the gang violence that drove much "
 "anti-trans predation.</p>"
 "<p>The trade-off is an exceptional security regime with mass arbitrary detention (tens of thousands imprisoned, minimal due "
 "process) — a risk mechanism that falls on anyone police decide to target, including gender-nonconforming people, with no "
 "effective recourse. There is no legal gender recognition law (administrative name change only), no SOGI hate-crime statute, "
 "and no institutional protection infrastructure.</p>"),
blindTangential=("<p>Regional comparison: a 2020 human-rights report groups this nation with two neighbouring nations as "
 "failing to effectively address violence and entrenched discrimination against LGBT people, driving asylum claims abroad.</p>"
 "<p>Legislative and research context: 2015 legal-code reforms made bias-motivated killings punishable by long prison "
 "sentences; a 2024 longitudinal study profiles homicides against LGBTI+ people across two decades; and the first conviction "
 "came in 2020 — legal milestones that do not by themselves change the practical visitor risk.</p>"),
blindLocalsOnly=("<p>The administrative name-change-only process and the absent legal-gender-recognition law are resident-facing; "
 "the historical life-expectancy figure and the killing case described in the summary are resident-facing too.</p>"),
blindOutOfScope=("Unresolved: whether the exceptional security regime is applied to trans visitors in practice — its "
 "trans-specific application is a risk mechanism, not a documented pattern, and the regime affects all travellers.\n"
 "Unverified: the sources document no trans-visitor incidents, and the historic danger figures describe residents' experience "
 "before the recent crackdown."),
blindSourceSummaries=[
 "A news analysis (9 Mar 2020): prosecution of the death of a transgender woman as a hate crime — activists called it an "
 "advance toward this nation's first hate-crime homicide conviction while documenting continuing discrimination and abuse of "
 "LGBTQ citizens.",
 "A peer-reviewed journal article (2024): builds a profile of crimes, victims and perpetrators of homicides against LGBTI+ "
 "people in this nation across 2000-2020.",
 "An international rights report (7 Oct 2020): this nation with two neighbouring states fails to effectively address violence "
 "and entrenched discrimination against LGBT people, driving asylum claims abroad; documents obstacles to obtaining "
 "protection.",
 "An international rights report (Jan 2021): violence and discrimination against LGBT people in this nation — a full report "
 "with recommendations to the president, the top government lawyer, elected legislators and ministries.",
 "An international rights report (31 Jul 2020): a judge found three police officers guilty of the January 2019 killing of a "
 "transgender woman and sentenced each to 20 years; the July 2020 judgment is the first homicide conviction in this nation for "
 "killing a transgender person.",
 "A news report (9 Sep 2015): the elected national legislature approved legal-code reforms so killings motivated by sexual "
 "orientation, race, ethnicity, political affiliation or gender draw 30-60 years under Article 129 — enhanced hate-crime "
 "penalties.",
],
notes=("Split from current_summary and source claims: the transition-driven visitor assessment (homicide-crackdown trade-off, "
 "exceptional-regime risk) to summary; regional HRW grouping, 2015 legal-code reform and 2024 longitudinal dataset to "
 "tangentialFactors; name-change-only process and resident danger figures to localsOnly; exception-regime application to "
 "visitors and incident absence to outOfScopeNotes. current_tangential was empty; current_localsOnly and current_outOfScope "
 "preserved."),
))

# --------------------------------------------------------------------------
# 8. country:DOM
recs.append(dict(
who='country:DOM',
summary=("<p>The Dominican Republic demands real caution from trans visitors. Same-sex conduct is legal, and the 2024 "
 "Constitutional Court review of the remaining sodomy-law articles (210/260, which applied to police and armed-forces members) "
 "has resolved: the current criminal code does not prohibit same-sex relations — though the existence of these articles "
 "revealed the institutional culture. There is no legal gender recognition, no anti-discrimination law covering SOGI (Brazil, "
 "a foreign government, formally recommended one at the 2024 UPR review), and documented violence against trans women is high, "
 "particularly affecting the most marginalised.</p>"
 "<p>Tourist zones (Punta Cana, Puerto Plata) are heavily insulated resort enclaves with international norms; Santo Domingo, "
 "the capital, has a visible community and annual Pride caravan. Outside those bubbles, machista culture, police harassment of "
 "trans women (especially sex workers), and anti-Haitian (xenophobic) dynamics that compound for dark-skinned trans people are "
 "documented.</p>"),
tangentialFactors=("<p>National political climate: the 2015-2017 period saw organised opposition to an openly gay foreign "
 "ambassador, whose visible presence drew a documented backlash — attacks at the time on the local community and its "
 "visibility — and whose departure in 2017 left an advocacy void.</p>"
 "<p>Regional and international engagement: hundreds of activists (over 300) from the region attended an official-facing "
 "conference in 2017 in the capital, and accepted 2024 review recommendations covering discrimination based on sexual "
 "orientation and gender identity carry no documented domestic implementation.</p>"),
localsOnly=("<p>No legal gender recognition and no SOGI anti-discrimination law — resident-facing gaps; the sodomy-law articles "
 "applied to police and armed-forces members rather than civilians, and the 2024 review resolved them.</p>"),
outOfScopeNotes=("Unresolved: how the resort-versus-non-resort risk divide applies to trans visitors in practice is unquantified "
 "— tourist zones are heavily insulated, but the documented risk to trans women outside them is high for residents and untested "
 "for visitors.\n"
 "Unverified: no documented trans-visitor incidents appear in the current sources, and the accepted review recommendations "
 "have no documented domestic implementation."),
blindSummary=("<p>This nation demands real caution from trans visitors. Same-sex conduct is legal, and the 2024 "
 "constitutional-court review of the remaining sodomy-law articles (210/260, which applied to police and armed-forces members) "
 "has resolved: the current criminal code does not prohibit same-sex relations — though the existence of those articles "
 "revealed the institutional culture. There is no legal gender recognition, no anti-discrimination law covering SOGI (a "
 "foreign government formally recommended one at the 2024 review), and documented violence against trans women is high, "
 "particularly affecting the most marginalised.</p>"
 "<p>Tourist zones are heavily insulated resort enclaves with international norms; the capital has a visible community and "
 "annual Pride caravan. Outside those bubbles, machista culture, police harassment of trans women (especially sex workers), and "
 "xenophobic dynamics that compound for dark-skinned trans people are documented.</p>"),
blindTangential=("<p>National political climate: the 2015-2017 period saw organised opposition to an openly gay foreign "
 "ambassador, whose visible presence drew a documented backlash — attacks at the time on the local community and its "
 "visibility — and whose departure in 2017 left an advocacy void.</p>"
 "<p>Regional and international engagement: hundreds of activists (over 300) from the region attended an official-facing "
 "conference in 2017 in the capital, and accepted 2024 review recommendations covering discrimination based on sexual "
 "orientation and gender identity carry no documented domestic implementation.</p>"),
blindLocalsOnly=("<p>No legal gender recognition and no SOGI anti-discrimination law — resident-facing gaps; the sodomy-law "
 "articles applied to police and armed-forces members rather than civilians, and the 2024 review resolved them.</p>"),
blindOutOfScope=("Unresolved: how the resort-versus-non-resort risk divide applies to trans visitors in practice is unquantified "
 "— tourist zones are heavily insulated, but the documented risk to trans women outside them is high for residents and untested "
 "for visitors.\n"
 "Unverified: no documented trans-visitor incidents appear in the current sources, and the accepted review recommendations "
 "have no documented domestic implementation."),
blindSourceSummaries=[
 "An international rights report (30 Aug 2024): documented the constitutional-court challenge to sodomy-law remnants reaching "
 "only police and armed-forces members, with an amicus brief arguing equality and privacy violations. SUPERSEDED per resolved "
 "review: the review resolved — the current criminal code does not prohibit same-sex relations; still no anti-discrimination "
 "or marriage recognition.",
 "A review-tracking database: this nation accepted recommendations covering intersex persons' rights and discrimination based "
 "on sexual orientation and gender identity — accepted commitments with no domestic implementation detail shown.",
 "An international rights publication (31 Mar 2019): a visibility-day conversation with two activists, including a trans "
 "sex-worker organiser from this nation — a first-hand account of trans struggles in the country.",
 "A regional news report (1 Apr 2017): hundreds of activists from the region attended an LGBT and intersex political-engagement "
 "conference in the capital with national officials speaking — a marker of official-level engagement.",
 "A regional news report (27 Apr 2016): documents the backlash against an openly gay foreign ambassador after a public "
 "presentation with his husband in the capital in June 2015 — framed as attacks on the local community, showing an organised "
 "domestic opposition climate.",
 "A regional news report (3 Apr 2017): the openly gay foreign ambassador's departure left an advocacy void after two years of "
 "visible presence — a trailing marker of the polarised climate.",
],
notes=("Split from current_summary, freshness_all resolution and source claims: the visitor assessment (legal same-sex conduct, "
 "resolved sodomy-law review, SOGI protection gap, resort-versus-non-resort divide) to summary; national political climate and "
 "regional engagement to tangentialFactors; resident-facing legal gaps to localsOnly; resort-divide quantification and "
 "incident absence to outOfScopeNotes. current_tangential was empty; current_localsOnly and current_outOfScope preserved. The "
 "2024 sodomy-law review resolution per freshness_all is reflected in summary, localsOnly and the first source summary."),
))

# --------------------------------------------------------------------------
# Merge-first write after each record (keep other whos).
data = {'rewrites': []}
if OUT.exists():
    try:
        data = json.loads(OUT.read_text(encoding='utf-8'))
    except Exception:
        data = {'rewrites': []}
for r in recs:
    existing = [x for x in data['rewrites'] if x.get('who') != r['who']]
    existing.append(r)
    data['rewrites'] = existing
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
print(f"wrote {len(data['rewrites'])} records to {OUT}")