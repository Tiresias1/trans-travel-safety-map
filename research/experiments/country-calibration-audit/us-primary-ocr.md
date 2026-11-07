# Primary-text OCR report: 24 Feb 2025 State cable + Dec 2025 Bondi NSPM-7 memo

Read-only evidence task. No repository writes, no model calls. Files written: `/tmp` only.
Report written to `/tmp/kort-us-primary-ocr.md` (duplicated to the run's authoritative output path).

## 0. Tools: what worked and what failed

| Tool | Status | Use |
|---|---|---|
| `curl` | worked | PDF/HTML downloads |
| `pdftoppm` (poppler) | worked | 300 dpi PNG rasterization of image-only PDFs |
| `tesseract` 5.5.3 (leptonica 1.87.0) | **not installed initially**; installed with `sudo dnf install -y tesseract` (Fedora 43, no `apt-get` present) | OCR of both PDFs (`--psm 4` primary, `--psm 3`/`--psm 6` for cross-check of key lines) |
| `pdftotext` / `pdfinfo` | worked | text-layer extraction attempt (returned ~0 chars on image-only copies → confirmed image-only); full text extraction on the indybay and docs.house.gov renditions |
| `python3` + PyMuPDF (`fitz`) | present, not needed for OCR (no text layer) | availability probe only |
| `pypdf` | **failed — ModuleNotFoundError** | not installable within budget; superseded by tesseract |
| `pytesseract`, `easyocr`, `ocrmypdf` | **failed — not installed** | superseded by tesseract CLI |
| Search engines: DuckDuckGo html/lite, Mojeek, Google, Ecosia, Startpage | **failed — bot-blocked / zero results** | replaced |
| Brave Search | worked once, then bot-blocked | found the GovExec URL |
| Yahoo Search (`search.yahoo.com/search?p=`) | **worked** (main discovery channel) | found LA Times URL, indybay + docs.house.gov + ca-times PDF URLs, ran enforcement searches |
| web.archive.org CDX API | **failed — 502/504 Gateway Timeouts** on latimes.com domain queries | replaced by Yahoo |

OCR cross-validation: the image-only copies (Washington Examiner host; ca-times.brightspotcdn.com host) were OCR'd
with tesseract; the text-based renditions of the same memo (indybay.org, docs.house.gov) were extracted with
`pdftotext`. Every quoted memo passage below appears **identically in both OCR output and the independent text
rendition**, so memo quotes are double-sourced. The cable has only one copy (image-only); its quotes rest on
tesseract OCR of two passes (psm 4 full text; psm 3/6 re-read of the SWS25 paragraph), which agreed word-for-word.

## 1. Downloads (all in /tmp)

| File | Source URL | Format |
|---|---|---|
| `kort-cable.pdf` (548,747 B, 2 pp) | `https://iptp-production.s3.amazonaws.com/media/documents/2025.2.24_DOS_Guidance_for_Visa_Adjudicators_EO_14201_22Keeping_Men_Out_of_Wom_VhPai1S.pdf` (URL recovered from `https://immpolicytracking.org/policies/eo-potus-orders-state-and-dhs-to-review-visas-of-transgender-athletes-under-ina/`) | **image-only** (pdftotext → 0 chars) |
| `kort-memo-we.pdf` (801,930 B, 6 pp) | `https://www.washingtonexaminer.com/wp-content/uploads/2025/12/Attorney_General_Bondi_Memorandum_re_NSPM-7_AG_Guidance_12.4.2025.pdf` | **image-only** (pdftotext → 6 chars) |
| `kort-memo-lat.pdf` (801,930 B, 6 pp) | `https://ca-times.brightspotcdn.com/6a/6c/c5feff2a460baba3db6b96ded309/attorney-general-bondi-memorandum-re-nspm-7-ag-guidance-12-4-2025.pdf` (URL recovered from the LA Times article HTML) | **image-only** (md5 differs from WE copy; same size; OCR applies to this class) |
| `kort-memo-indybay.pdf` (162,727 B, 7 pp) | `https://www.indybay.org/uploads/2025/12/09/bondi_memo_on_countering_domestic_terrorism_and_organized_political_violence.pdf` | **has text layer** (16,601 chars; reformatted/HTML-to-PDF rendition, footnotes moved to end) |
| `kort-memo-house.pdf` (143,697 B, 7 pp) | `https://docs.house.gov/meetings/JU/JU00/20260211/118951/HHRG-119-JU00-20260211-SD032.pdf` | **has text layer** (16,601 chars, identical text to indybay rendition) |
| OCR outputs | `kort-cable-ocr.txt`, `kort-memo-ocr.txt`, `indybay.txt`, `latimes.html/.txt`, `govexec.html/.txt` | — |
| Not obtained | `assets1.cbsnewsstatic.com` copy — full URL not recovered within bounded search; **not needed**, since three other named/authoritative copies were downloaded and two agree character-for-character | — |

Also downloaded and set aside: `https://www.justice.gov/ag/media/1415691/dl` = a *different* AG memo
("Attorney General Memorandum, Ending Political Violence Against ICE", 29 Sept 2025) — not the NSPM-7 memo.

---

## 2. State Department cable, 24 Feb 2025 — VERBATIM (OCR, image-only PDF)

Document: **"Guidance for Visa Adjudicators on Executive Order 14201 'Keeping Men Out of Women's Sports'"**,
2 pages. Page numbers below = PDF page numbers (cable paragraphs 1–6 on p. 1, 7–12 on p. 2).

### Header (p. 1)
> "MRN: ATE 1557
> Date/DTG: Feb 24, 2025 / 241824Z FEB 25
> From: SECSTATE WASHDC
> Action: ALL DIPLOMATIC AND CONSULAR POSTS COLLECTIVE Immediate
> E.O.: 13526
> Tags: CVIS, CMGT
> Captions: SENSITIVE
> Reference: A) 25 STATE 11402 / B) 25 STATE 5974
> Subject: Guidance for Visa Adjudicators on Executive Order 14201 "Keeping Men Out of Women's Sports""

(Header OCR of "WASHDCG" vs "WASHDC" is ambiguous in the scan — minor, non-substantive.)

### Q1: Who is covered — all visa applicants vs athletes?

**¶1 SUMMARY (p. 1):**
> "All visa-issuing posts should carefully review and follow this guidance effective immediately."

**¶3 (p. 1) — sports-purpose travel, any visa class:**
> "These changes will preclude biologically male athletes from participating in women's sporting events, including sports exchanges, in the United States; therefore, visa applications related to this purpose of travel under any visa class warrant additional scrutiny. Adjudicators should refer to previous guidance regarding sex markers, which states that a visa must bear the applicant's sex at birth (Ref A)."

**¶4 (p. 1) — athletes:**
> "In the case of an athlete applying for any classification of visa for the purpose of participating in a sports competition, you should confirm that the sponsoring organization permits participation by members of the applicant's sex as defined by E.O. 14168 …"

**¶5 (p. 1) — athletes, 221(g):**
> "For all visa classifications in which an applicant's primary purpose of travel is to participate in an athletic activity or program, this includes demonstrating that his or her participation will be permitted by the organizer. If the applicant is otherwise eligible for the visa but you are not satisfied that such participation is permissible, you may refuse the application under INA section 221(g) and request additional evidence. Like all applicants, if the applicant's stated purpose of travel or responses to questions regarding his or her intended activity casts doubt on credibility or qualification for the visa, you should refuse the applicant under INA section 214(b) if applicable to the visa classification."

**¶6 (p. 1) — general: applies to *all* immigrant and nonimmigrant visa applications:**
> "As explained in Ref A, both immigrant and nonimmigrant visa applications request that an applicant identify their sex as either male or female. Moreover, all visas must reflect an applicant's sex at birth. To verify an applicant's sex, you should generally rely upon the documents provided by the applicant (including passport or birth certificate). If there is a discrepancy either in the applicant's documents or in electronic consular records, or if other evidence casts reasonable doubt on the applicant's sex, you should refuse the case under 221(g) and request additional evidence to demonstrate sex at birth. Typically, a timely-registered birth certificate with a sex marker will suffice for this purpose."

**¶7 (p. 2) — general: no athlete limitation:**
> "In cases where applicants are suspected of misrepresenting their purpose of travel or sex, you should consider whether the misrepresentation is material such that it supports an ineligibility finding under INA section 212(a)(6)(C)(i)."

**Scope verdict (cable):** The fraud-bar provision (¶7) and the sex-at-birth/221(g) provision (¶6) are written **generally, for all visa applicants** — the words "athlete"/"athletic" appear only in ¶¶3–5 (scrutiny, sponsor-permission, 221(g)/214(b) for sports-purpose travel). Nothing in ¶¶6–7 limits the fraud analysis to athletes. The cable's *opening frames* (title, ¶¶2–3) are about E.O. 14201 / women's sports, and ¶7's only worked example is an athlete. So: "all visa applicants are *within the text's scope*" is supported; "the cable is *only about* athletes" is not; "any applicant listing a non-assigned gender *will be* permanently banned" is **not supported** (see Q2/Q3).

### Q2: What triggers a 221(g) evidence request vs an INA 212(a)(6)(C)(i) finding?

**221(g) triggers (verbatim):**
- ¶5 (p. 1): athlete "otherwise eligible for the visa but you are not satisfied that such participation is permissible" → "you may refuse the application under INA section 221(g) and request additional evidence."
- ¶6 (p. 1): "If there is a discrepancy either in the applicant's documents or in electronic consular records, or if other evidence casts reasonable doubt on the applicant's sex, you should refuse the case under 221(g) and request additional evidence to demonstrate sex at birth."
- (Note: ¶5 also gives the separate 214(b) refusal route for credibility doubts.)

**212(a)(6)(C)(i) trigger (p. 2, ¶7 verbatim):**
> "7.(SBU) In cases where applicants are suspected of misrepresenting their purpose of travel or sex, you should consider whether the misrepresentation is material such that it supports an ineligibility finding under INA section 212(a)(6)(C)(i). There are four elements required to find an individual ineligible for a visa under INA 212(a)(6)(C)(i). See 9 FAM 302.9-4(B)(1):
> (1) The applicant made an affirmative act of misrepresentation;
> (2) The misrepresentation was willfully made;
> (3) The fact misrepresented is material; and
> (4) The applicant by using fraud or misrepresentation seeks to procure, has sought to procure, or has procured a visa, other documentation, admission into the United States, or other benefit provided under the INA."

**Scope verdict (trigger split):** a bare sex-document **discrepancy or reasonable doubt → 221(g) refusal + evidence request** (reversible, not the permanent bar); the **permanent fraud bar requires suspected *misrepresentation* plus all four elements**, of which materiality is element (3). The claim "listing a gender other than assigned sex *is grounds for* a permanent fraud ban" as an automatic consequence is **not supported by the primary text**; the primary text supports a two-step, suspicion-plus-elements path.

### Q3: Materiality language (verbatim, p. 2, ¶7)

> "you should consider whether the misrepresentation is material such that it supports an ineligibility finding under INA section 212(a)(6)(C)(i)"

> "(3) The fact misrepresented is material;"

> "Some common scenarios that may raise questions about an applicant's ineligibility under INA 212(a)(6)(C)(i) involve intentional, material misrepresentations related to an applicant's sex or purpose of travel at the time of any visa application and/or at the time admission to the United States is sought. For an applicant traveling to the United States for an athletic competition, for example, misrepresentation of sex may be material if it cut off a line of inquiry regarding whether the applicant is permitted to participate in the competition. You should consider such misrepresentations in accordance with guidance on INA section 212(a)(6)(C)(i) in 9 FAM 302.9-4, and may request an advisory opinion (AO) from L/CA/V/AL with questions regarding application of this ground in a given case."

**Scope verdict (materiality):** materiality is an explicit, required element with an athlete example ("*may be material if* …"). No automaticity.

### Q4: Case-by-case / discretion language

**Finding: the exact phrase "case-by-case" does NOT appear anywhere in the cable** (grep over the full OCR of both pages returned zero hits; likewise "discretion"). The discretion that exists in the text is expressed as follows (all p. 2, ¶7):

> "you should consider whether the misrepresentation is material …"

> "You should consider such misrepresentations in accordance with guidance … and may request an advisory opinion (AO) from L/CA/V/AL with questions regarding application of this ground in a given case."

> "may raise questions about an applicant's ineligibility"

And on p. 1, ¶5: "**you may refuse** the application under INA section 221(g)" (permissive).

**Scope verdict (discretion):** the "case-by-case basis" formula the public saw is the **State Department press statement quoted by the Guardian**, not language from the cable itself. The cable itself is framed as instruction ("you should consider", "may request an advisory opinion") and never states the process is case-by-case, nor does it state any outcome is automatic. Do not attribute "case-by-case" to the primary document; do not attribute automaticity either.

### Q5: SWS25 tracking instruction (verbatim, p. 2, ¶8)

> "8. (SBU) Case Notes: Posts are instructed to include the following text in the case notes in all cases refused 221(g), 214(b), or (6)(C)(i) or pending an AO pursuant to this E.O.: #sws25 — please enter the text exactly without additional punctuation or spaces entered to allow for text searches. CA will also add the hot string "sws25" to the standard NIV Line AutoHotkey script."

Confirmed character-for-character in three independent tesseract passes (psm 3, 4, 6).

**Scope verdict (SWS25):** the code is a **tracking/note-tagging instruction**, attached to *all* cases refused under 221(g), **214(b)**, or (6)(C)(i) or pending an AO "pursuant to this E.O." — i.e. it is deliberately broader than fraud findings (it even tags ordinary 214(b) denials). It says nothing about outcomes; it is not itself a finding, denial, or penalty. Any dossier use of "SWS25" must reflect: tag ≠ adverse finding.

### Other cable items (context, p. 2)
- ¶9 Talking Points (cleared language for applicants) — E.O. 14201 and E.O. 14168 policy statements ("These sexes are immutable from birth.").
- ¶12: "Minimize considered."
- OCR uncertainty flags: header "SECSTATE WASHDCG" (trailing G may be scan artifact); ¶11 "sportsdiplomacy @state.gov" is an OCR line-break of `sportsdiplomacy@state.gov`. No passage was unreadable in the cable; all paragraphs 1–12 were recovered.

---

## 3. Bondi NSPM-7 implementation memorandum — VERBATIM

Document: **"Implementing National Security Presidential Memorandum-7: Countering Domestic Terrorism and
Organized Political Violence"**. Image-only copies are 6 pages; the indybay/docs.house.gov text renditions are
7 pages (same content, end-loaded footnotes). Page numbers below follow the **image-only scan** (as printed:
"Page 2"… "Page 6" running heads).

### Q6: Memo date as printed (p. 1, VERBATIM)

> "Office of the Attorney General
> Washington, D.C. 20530
> **December 4, 2025**
> MEMORANDUM FOR ALL FEDERAL PROSECUTORS / LAW ENFORCEMENT AGENCIES / DEPARTMENT OF JUSTICE GRANT-MAKING COMPONENTS
> FROM: THE ATTORNEY GENERAL
> SUBJECT: Implementing National Security Presidential Memorandum-7: Countering Domestic Terrorism and Organized Political Violence"

(OCR of the letterhead on p. 1 reads "Office of the Atternep General" — tesseract garble of "Attorney"; the
indybay and docs.house.gov text renditions both read "Office of the Attorney General". The date line itself
is clean in every copy.)

**Scope verdict (date):** the memo is dated **December 4, 2025** as printed — resolves the open 4-vs-5 Dec
contradiction in favour of 4 Dec; Pink News's "issued on 5 December" and LGBTQ Nation's "dated December 5"
are wrong (or refer to circulation), and Arnold & Porter's "December 4, 2025" matches the primary document.

### Q7: The cash-reward directive — exact operative sentence (p. 6, section 8, VERBATIM)

> "Further, because information from within an organization is often necessary to effectively dismantle large, criminal enterprises, **the FBI shall establish a cash reward system for information that leads to the successful identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 of this guidance or other offenses against the United States.**"

**Exactly which population it targets:** *individuals in the leadership of domestic terrorist organizations*
that conspire to commit the violations listed in §2 of the memo (or other offenses against the US).
Full-sentence scope qualifiers: "in the leadership of", "domestic terrorist organizations", "that conspire
with others to commit violations of the provisions of law listed in section 2 of this guidance or other
offenses against the United States".

**Scope verdict (bounty):** **narrower than "cash bounties on trans activists."** The operative sentence
targets organization *leadership* of *conspiring* domestic terrorist organizations. The words
"transgender", "trans", and "trans activists" appear **zero times in the memo** (grep: 0 hits in OCR and in
both text renditions). The only gender-adjacent term is the viewpoint phrase "radical gender ideology"
(Q8). Wikipedia's "described such activists as 'domestic terrorist groups'" is unsupported by the primary
text — the memo describes *organizations* as domestic terrorist organizations and never links bounties to
gender identity or trans advocacy as such. Also note the directive is prospective/administrative
("shall establish a cash reward system"): no reward amount, no named target, no posted bounty in the
document.

### Q8: "Radical gender ideology" — how defined/exemplified (VERBATIM; appears exactly twice)

**Occurrence 1 (p. 2, section 1):**
> "For some culpable actors, such as certain Antifa-aligned extremists, their animating principle is adherence to the types of extreme viewpoints on immigration, radical gender ideology, and anti-American sentiment listed below, with a willingness to use violence against law-abiding citizenry to serve those beliefs."

**Occurrence 2 (p. 2, section 1 — the "listed below" list):**
> "Particularly dangerous are those acts committed by violent extremist groups that threaten both citizens' safety and our country's ability to self-govern. These domestic terrorists use violence or the threat of violence to advance political and social agendas, including opposition to law and immigration enforcement; extreme views in favor of mass migration and open borders; **adherence to radical gender ideology, anti-Americanism, anti-capitalism, or anti-Christianity**; support for the overthrow of the United States Government; hostility towards traditional views on family, religion, and morality; and an elevation of violence to achieve policy outcomes, such as political assassinations."

**Scope verdict ("radical gender ideology"):** **never defined** in the memo; it is exemplified only as an
item in a list of "extreme viewpoints"/"political and social agendas" attributed to actors described as
"violent extremist groups"/"certain Antifa-aligned extremists" **"with a willingness to use violence
against law-abiding citizenry to serve those beliefs."** No protected group, no trans people, no gender
nonconforming persons, and no visa/immigration category is named as a target. Both occurrences are
conditioned on the violence qualifier in their framing sentence.

### Q9: "Domestic terrorist organizations" — how defined (VERBATIM)

The memo does **not** supply a free-standing definition of "domestic terrorist organization." What it says:

**Section 1 (p. 1) — domestic *terrorism* defined by statute:**
> "In general terms, domestic terrorism is criminal conduct that occurs primarily inside the territory of the United States and that involves acts dangerous to human life that appear to be intended to intimidate a civilian population; influence the policy of government by intimidation or coercion; or affect the conduct of government by mass destruction, assassination, or kidnapping. 18 U.S.C. § 2331(5); see also 6 U.S.C. § 101(18) …"

**Section 2 heading (p. 2):**
> "Common Characteristics of Domestic Terrorists and Organizations"

> "Many of these domestic terrorists and domestic terrorist organizations are united by an anti-fascist platform that justifies violence and any other means necessary to combat perceived 'fascism.'"

**Section 5 (p. 5) — the list directive:**
> "Pursuant to Section 3 of NSPM-7, in the course of and as a result of the investigations directed by NSPM-7, the FBI, in coordination with its partners on the JTTFs, and consistent with applicable law, shall compile a list of groups or entities engaged in acts that may constitute domestic terrorism as defined by 18 U.S.C. § 2331(5) and provide that list to the Deputy Attorney General."

**First Amendment footnote (p. 2, footnote 2, VERBATIM):**
> "The United States Government does not investigate, collect, or maintain information on U.S. persons solely for the purpose of monitoring activities protected by the First Amendment. No investigation may be opened based solely on activities protected by the First Amendment or the lawful exercise of rights secured by the Constitution or laws of the United States."

(Also p. 1, footnote 1: the guidance "may not be relied upon to create, any right or benefit … enforceable at law …")

**Scope verdict (DTO definition):** defined only by cross-reference — domestic terrorism per 18 U.S.C.
§ 2331(5) (criminal-conduct based), with the organization list to be compiled by the FBI ("groups or
entities engaged in acts that **may constitute** domestic terrorism"). There is no designation power
created in the memo text itself, and no ideological-belief-only predicate: the framing repeatedly ties to
violence/criminal conduct, with an express First Amendment footnote.

**Other operative directives (for context, all VERBATIM from the scan):** 14-day Antifa files review (p. 5,
§4: "all federal law enforcement agencies are directed to review their files and holdings for Antifa and
Antifa-related intelligence"); 30-day reporting cadence (§5); grant prioritization (§6); 60-day Antifa
intelligence bulletin (§7); tip-line/"citizen journalists" media updates (§8, p. 6); sentencing enhancement
"under U.S.S.G. § 3A1.4" (p. 4).

**OCR caveat:** p. 5 §4 renders "JTTFs" once as "JITFs" (tesseract garble; the text renditions read
"JTTFs"). Footnote 5's "Berkley" spelling appears in the source rendering; NPR's original says
"Berkeley" — treat as source/OCR-level typo, non-substantive. No memo passage was unreadable; all 6 scanned
pages were recovered and corroborated against two independent text renditions.

**Date/population verdict combined:** memo dated **December 4, 2025**; cash-reward population = leaders of
conspiring domestic terrorist organizations (plus the surrounding Antifa-aligned-extremism framework);
"transgender activists" as such are not mentioned anywhere in the document.

---

## 4. Bounded follow-up: post-May-2026 enforcement evidence

Queries actually run (Yahoo Search unless noted): `"SWS25"`; `SWS25 visa State Department tracking`;
`"212(a)(6)(C)(i)" gender marker visa permanent bar 2026`; `"212(a)(6)(C)(i)" transgender 2026`;
`transgender visa "fraud bar" denied 2026`; `site:govexec.com "NSPM-7"` (Brave);
`"Justice Department drafting a list of domestic terrorists"`; `"NSPM-7" bondi memorandum 12-4-2025 pdf`.

### 4a. INA 212(a)(6)(C)(i) permanent bar for a gender-marker mismatch — NOT FOUND
No search result (all of them) documents an actual §212(a)(6)(C)(i) permanent bar imposed on any person for
a gender-marker mismatch. Exact-string `"SWS25"` returns **only scale-model product pages**
(Summit Racing "pxo-sws25", Zoukei-Mura "SWS25" Bf 109 G-4 kits) — **zero visa/enforcement hits**. The
§212(a)(6)(C)(i) queries return generic practitioner/waiver pages (fedlaws.org, ina212.com, messersmithlaw,
USCIS policy manual) and 2025 news (Guardian 25 Feb 2025, CNBC-TV18, visaguide.world, LGBTQ Nation
Feb/Aug 2025) — **no 2026 enforcement outcome, no case count, no named respondent**.
**Verdict: still no evidence of any documented permanent fraud bar imposed on a gender basis, and no SWS25
outcome data, as of this bounded search.** (Absence-of-evidence from ~10 targeted queries; not proof of
non-existence.)

### 4b. LA Times, 11 Dec 2025 — READ IN FULL
Michael Wilner and Ana Ceballos, "Justice Department drafting a list of 'domestic terrorists'",
Dec. 11, 2025 3 AM PT, `https://www.latimes.com/politics/story/2025-12-11/justice-department-drafting-list-of-domestic-terrorists`
(article HTML fetched, 8,409 chars of body text; no paywall block on the HTML).

What it establishes (VERBATIM):
> "WASHINGTON — Justice Department leadership has directed the FBI to 'compile a list of groups or entities engaged in acts that may constitute domestic terrorism' by the start of next year, and to establish a 'cash reward system' that incentivizes individuals to report on their fellow Americans, according to a memo reviewed by The Times."

> "Law enforcement agencies are directed in the memo, dated Dec. 4, to identify 'domestic terrorists' who use violence, or the threat of violence, to advance political and social agendas, including 'adherence to radical gender ideology, anti-Americanism, anti-capitalism, or anti-Christianity.'"

Standfirst: "A Justice Department memo calls for a 'cash reward system' that would encourage Americans to report suspected domestic terrorist activity. The memo says domestic terrorism could be inspired by a number of things, such as 'opposition to law and immigration enforcement' or support for 'radical gender ideology.' The memo focuses on what it calls antifa-aligned extremism and omits mentions of rising domestic threats, such as violent white supremacy."

> "Only in a footnote of the memo does the Justice Department acknowledge that the U.S. government cannot 'investigate, collect, or maintain information on U.S. persons solely for the purpose of monitoring activities protected by the First Amendment.'"

Expert quotes: Mary McCord (former acting AAG for National Security): "I think this causes a chilling impact, because it definitely seems to be directing enforcement toward particular points of view." Thomas Brzozowski (former DOJ counsel for domestic terrorism): "People will inform because they want to get paid."

**Scope verdict:** LA Times corroborates the memo's date (Dec. 4), the list directive and the cash-reward
system, and frames the gender-ideology phrase as one item among listed inspiration "causes" — it does
**not** establish bounties on trans activists, and it reports only drafting/implementation directives, not
enforcement outcomes. Nothing in the article concerns visas, SWS25, or §212(a)(6)(C)(i).

### 4c. GovExec, July 2026 — READ IN FULL
Melinda Haas (University of Pittsburgh), originally The Conversation, "How a little-known Trump directive
reshaped the government's counterterrorism approach", **COMMENTARY, July 19, 2026**, republished by
Government Executive: `https://www.govexec.com/defense/2026/07/trump-directive-reshaped-governments-counterterrorism-approach/414869/`
(fetched in full).

What it establishes (VERBATIM excerpts):
> "A little-noticed presidential national security directive is now the legal engine behind a wave of terrorism prosecutions against left-wing protesters."

> "That architecture is National Security Presidential Memorandum/NSPM-7, issued on Sept. 25, 2025, which for the first time appeared to authorize preemptive law-enforcement measures against Americans based not on whether they are planning to commit violence but for their political or ideological beliefs."

> "Nearly a year later, that blueprint has moved from paper into practice. The Justice Department has built task forces staffed by counterterrorism prosecutors. The FBI has set up its own NSPM-7 mission center to oversee investigations into left-wing movements, including a joint effort with the IRS to investigate nonprofit groups."

> "Former Attorney General Pam Bondi's December 2025 implementation memo went further, ordering a five-year review of agency files on antifa."

> "In Texas, eight defendants tied to a 'North Texas Antifa Cell' were sentenced in June 2026 for a 2025 armed confrontation at the Prairieland immigration detention center. One man received 100 years … In Minnesota, 15 members and associates of a group called Direct Action Minnesota were indicted in June 2026 on conspiracy and assault charges."

> "The State Department designated four antifa-aligned groups as foreign terrorist organizations. But antifa is a decentralized movement, not a formal group with a roster. … U.S. law has no formal domestic terrorist organization category."

> "Domestic terrorism itself is not a chargeable offense. Prosecutors have instead leaned on older statutes such as material support for terrorism and conspiracy laws …"

> "NSPM-7 also allows the attorney general to propose groups for designation as 'domestic terrorist organizations.'" … "The memorandum identifies 'anti-Christian,' 'anti-capitalism' or 'anti-American' views as potential indicators that a group or person will commit domestic terrorism."

> "The memorandum claims that political violence originates with 'anti-fascist' groups that hold the following views: 'support for the overthrow of the United States Government; extremism on migration, race, and gender; and hostility towards those who hold traditional American views on family, religion, and morality.'"

**Scope verdict:** GovExec/Conversation establishes (as expert commentary, not government data) that NSPM-7
implementation has produced **real prosecutions and sentences (June 2026)** and an FTO designation push —
i.e. enforcement of the *counterterrorism* track is documented. It establishes **nothing** about visa
§212(a)(6)(C)(i) enforcement or SWS25; no mention of visas/gender-marker bars. Note: the quoted NSPM-7
phrase "extremism on migration, race, and gender" is GovExec's quotation of the September NSPM-7 — not of
the Bondi memo (the Bondi memo's parallel phrase is "radical gender ideology", quoted above).

### 4d. Follow-up verdict
- Documented §212(a)(6)(C)(i) permanent bar for gender-marker mismatch: **none found** (bounded search).
- SWS25 outcome data: **none found**; the literal tag returns no news/policy hits at all.
- Post-May-2026 enforcement evidence exists **only for the NSPM-7/antifa prosecution track**
  (GovExec July 2026: June 2026 sentences/indictments; four antifa-aligned FTO designations).
- LA Times 11 Dec 2025 and GovExec July 19 2026 both fetched and quoted above.

---

## 5. Per-claim short scope verdicts (primary text in hand)

1. **"Listing a gender other than assigned sex on a visa application is grounds for a permanent fraud ban"**
   — **partly supported, materially overstated.** Cable ¶¶6–7 are on their face general (all visa
   applicants, all visa classes), not athlete-limited [primary]. But the fraud bar requires suspicion of
   *misrepresentation* + all four elements incl. materiality, evaluated by the officer ("you should
   consider"; AO available); a plain document discrepancy yields a 221(g) refusal + evidence request, not a
   permanent bar [primary]. The cable contains **no** "case-by-case" phrase (that's the DOS press line) and
   **no** automatic-ban language. SWS25 is a case-note tag for 221(g)/214(b)/(6)(C)(i)/AO cases, not a
   finding [primary].
2. **"FBI cash bounties on transgender activists described as domestic terrorist groups"**
   — **narrower than stated.** Operative sentence targets "individuals in the leadership of domestic
   terrorist organizations that conspire with others to commit violations of the provisions of law listed
   in section 2 … or other offenses against the United States" [primary, double-sourced]. "Transgender"
   appears zero times; "radical gender ideology" appears twice, only as a listed viewpoint of
   violent-willing Antifa-aligned extremists [primary]. Memo printed date: **December 4, 2025** [primary] —
   resolves the 4-vs-5 Dec contradiction.
3. **Post-May-2026 enforcement** — no gender-marker §212(a)(6)(C)(i) bar and no SWS25 data found; NSPM-7
   prosecution track documented by GovExec (July 19, 2026); LA Times (Dec 11, 2025) corroborates memo
   content and date only.

## 6. Limitations
- Cable quotes rest on **OCR of a single image-only copy** (IPTP-hosted); three tesseract passes agreed on
  the key paragraphs, but no second independent copy of the cable was obtained, and the header line
  "WASHDCG" has a possible stray character. Marks of uncertainty: header "WASHDCG"; nothing else.
- The `assets1.cbsnewsstatic.com` memo copy URL was not recovered (three other copies were: ca-times
  image-only, indybay text, docs.house.gov text) — no impact, content corroborated 3×.
- The memo's image-only hosts were verified image-only (pdftotext → 6 chars) as the prior run reported;
  the indybay/docs.house.gov copies are *renditions* (footnotes relocated), so page numbering for the memo
  quotes follows the original 6-page scan.
- Enforcement search is bounded (~10 queries, several engines bot-blocked); "no results found" ≠ "none
  exists". LA Times HTML body was read; embedded comments/video transcript not examined. GovExec article
  read as rendered text (it is an expert COMMENTARY, not an official data source).
- No repository files were created or modified; all artifacts in `/tmp`.