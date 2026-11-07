# US dossier repair — final proposal (review fixes F1–F5 applied; change list applied under gates)

Inputs: `research/experiments/country-calibration-audit/us-repair-proposal-v2.md` (approved direction,
five reviewer corrections applied) and `us-primary-ocr.md` (primary-text verification).
Scope: `data/countries.json` → `USA` object: the 8 claim occurrences (v2 §3 items 1a–1c, 2a–2e) plus
two flagged scope-expansion replacements (C9/C10, §2). Status: this document incorporates the blocking
review's fixes F1–F5 (`terra-fidelity-review.md`); the §2 change list has been applied to
`data/countries.json` under the review's application gates — text edits to that one file only,
nothing staged, no commits, no score changes, no UI changes. Binding user convention applied: all user-visible and blind record text is clean
verified prose stating the facts as the account itself — no attribution scaffolding, no citation-gap
markers, no methodology wording. The secondary-vs-primary discrepancy for the two source-summary
fields is recorded only in the backend/dev provenance note (§3).

## 1. Final before/after text — the 8 occurrences

All text shown rendered; in the raw JSON every `"` inside a string value is written `\"`, exactly as
the current sentences already are. For 1a, 1b, 2a, 2b, 2d, 2e the AFTER text carries the v2
text over with the blocking review's corrections applied on top (F1 literal tag, F2 blind
anonymisation, F4 instruction-not-outcome wording); every v2 fact, number, date and name is kept
unless a fix corrects it. For the two source-summary fields (1c, 2c) the v2 A/B variants are resolved
into a single final text under the binding convention: clean verified prose stating the corrected
account itself, attribution prefixes dropped (F3), with the secondary-vs-primary discrepancy moved
to §3.

### 1a. `USA.summary` (line 402) — claim 1, visa/fraud bar

**BEFORE (current file, verbatim):**
> In February 2025 the State Department announced a ban on trans athletes entering the United States to compete in women's sports, flagging visa applicants with an internal marking and treating any applicant listing a gender other than assigned sex as grounds for a permanent ban on grounds of fraud.

**AFTER (final):**
> In February 2025 the State Department announced a ban on trans athletes entering the United States to compete in women's sports, and its 24 February 2025 cable instructs posts to add the case-note tag #sws25 to cases refused under INA 221(g), 214(b) or 212(a)(6)(C)(i), or pending an advisory opinion, pursuant to this Executive Order. Where there is a discrepancy in an applicant's documents or electronic records, or other evidence casting reasonable doubt on the applicant's sex, the cable instructs officers to refuse the case under INA 221(g) and request additional evidence; where an applicant is suspected of wilfully misrepresenting sex or purpose of travel, the officer should consider whether the misrepresentation is material such that it supports an ineligibility finding under INA 212(a)(6)(C)(i) — the fraud ground, whose consequence is a permanent, lifetime exclusion from the United States, for which limited waiver possibilities exist — a finding that requires all four elements, so a gender-marker discrepancy never automatically produces that bar.

(The sentence following in the field — multiple-foreign-governments response, March/April 2025 — is
untouched.)

### 1b. `USA.blindSummary` (line 501) — claim 1, blind register

**BEFORE (current file, verbatim):**
> In February 2025 the foreign ministry announced a ban on trans athletes entering the country to compete in women's sports, flagging visa applicants with an internal marking and treating any applicant listing a gender other than assigned sex as grounds for a permanent ban on grounds of fraud.

**AFTER (final):**
> In February 2025 the foreign ministry announced a ban on trans athletes entering the country to compete in women's sports, and its 24 February 2025 cable instructs posts to add the case-note tag — the same text in all cases refused or pending an advisory opinion under the February 2025 executive order. Where there is a discrepancy in an applicant's documents or records, or other evidence casting reasonable doubt on the applicant's sex, the cable instructs officers to refuse the case and request additional evidence; where an applicant is suspected of wilfully misrepresenting sex or purpose of travel, the adjudicating officer should consider whether the misrepresentation is material such that it supports a permanent, lifetime ineligibility finding under the immigration code's fraud ground — a finding that requires all four elements, for which limited waiver possibilities exist, and which is never automatic.

### 1c. `USA.sources[15].summary` (line 469) — claim 1, source field (v2 A/B pick resolved:
convention applied, single final text; F3 drops the attribution prefix)

**BEFORE (current file, verbatim — this is the whole field value):**
> Wikipedia: 5 Feb 2025 EO 'Keeping Men Out of Women's Sports'; State Department announced (25 Feb 2025) banning trans athletes from entering the US to compete in women's sports, flagging visa applicants 'SWS25', and a permanent ban on applicants listing a gender other than assigned sex as 'fraud'.

**AFTER (final):**
> 5 Feb 2025 EO 'Keeping Men Out of Women's Sports'; State Department announced (25 Feb 2025) banning trans athletes from entering the US to compete in women's sports; the State Department's 24 February 2025 cable instructs posts to add the case-note tag #sws25 to cases refused under INA 221(g), 214(b) or 212(a)(6)(C)(i), or pending an advisory opinion, pursuant to this Executive Order; where there is a discrepancy in an applicant's documents or electronic records, or other evidence casting reasonable doubt on the applicant's sex, the cable instructs officers to refuse the case under INA 221(g) and request additional evidence; where an applicant is suspected of wilfully misrepresenting sex or purpose of travel, the officer should consider whether the misrepresentation is material such that it supports an ineligibility finding under INA 212(a)(6)(C)(i), whose consequence is a permanent, lifetime exclusion from the United States, for which limited waiver possibilities exist, on all four elements — never automatic.

(The secondary-vs-primary discrepancy behind this rewrite is recorded only in §3, backend/dev,
not-for-display; the JSON value written is exactly the AFTER text above.)

### 2a. `USA.summary` (line 402) — claim 2, cash-reward directive

**BEFORE (current file, verbatim):**
> In December 2025 the attorney general instructed the FBI to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," describing such activists as "domestic terrorist groups."

**AFTER (v2 final):**
> In December 2025 the attorney general instructed the FBI to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 of the guidance or other offenses against the United States; the same memorandum uses the phrase "radical gender ideology" twice — once among the extreme viewpoints it says animate "certain Antifa-aligned extremists" "with a willingness to use violence against law-abiding citizenry," and once in a list of political and social agendas attributed to "violent extremist groups" more generally — and never as a criterion for the reward.

(The following sentence — the May 2026 Counterterrorism Strategy quote — is verbatim-verified and
retained as-is.)

### 2b. `USA.blindSummary` (line 501) — claim 2, blind register

**BEFORE (current file, verbatim):**
> In December 2025 the national justice department instructed a national law-enforcement agency to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what it called "radical gender ideology," describing such activists as "domestic terrorist groups."

**AFTER (v2 final):**
> In December 2025 the national justice department instructed a national law-enforcement agency to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 of the guidance or other offenses against the country; the same memorandum uses the phrase "radical gender ideology" twice — once among the extreme viewpoints it says animate actors "with a willingness to use violence against law-abiding citizenry," and once in a list of political and social agendas attributed to violent extremist groups more generally — and never as a criterion for the reward.

### 2c. `USA.sources[14].summary` (line 464) — claim 2, source field (v2 A/B pick resolved:
convention applied, single final text; replaces the claim sentence and its article-title attribution
prefix (F3), rest of field unchanged)

**BEFORE (current file, verbatim — claim sentence with its field prefix):**
> Persecution of transgender people under the second Trump administration (Wikipedia): In December 2025 Attorney General Pam Bondi instructed the FBI to begin offering cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," describing such activists as "domestic terrorist groups."

**AFTER (final):**
> In December 2025 Attorney General Pam Bondi instructed the FBI to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 of this guidance or other offenses against the United States; the same memorandum uses the phrase "radical gender ideology" twice — once among the extreme viewpoints it says animate "certain Antifa-aligned extremists" "with a willingness to use violence against law-abiding citizenry," and once in a list of political and social agendas attributed to "violent extremist groups" more generally — and never as a criterion for the reward.

(The secondary-vs-primary discrepancy behind this rewrite is recorded only in §3, backend/dev,
not-for-display.) Everything else in the field is unchanged: the Wikipedia survey prefix and the
prison/ICE-custody material before this sentence (only this sentence's article-title attribution
prefix is dropped, F3) and the May 2026 strategy sentence onward after it.

### 2d. `USA.localsOnly` (line 520) — claim 2 + May 2026 strategy clause

**BEFORE (current file, verbatim):**
> In December 2025 the attorney general instructed the FBI to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," and the May 2026 counterterrorism strategy framed "radically pro-transgender" ideology as a security threat.

**AFTER (v2 final):**
> In December 2025 the attorney general instructed the FBI to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire to commit the violations listed in section 2 of her guidance or other offenses against the United States, and the May 2026 counterterrorism strategy stated that national counterterrorism activities would "prioritize the rapid identification and neutralization of violent secular political groups whose ideology is anti-American, radically pro-transgender, and anarchist" — a category the same document lists alongside "Violent Left-Wing Extremists, including Anarchists and Anti-Fascists" — while stating that counterterrorism powers "will not be used to target our fellow Americans who simply disagree with us."

### 2e. `USA.blindLocalsOnly` (line 521) — claim 2 + strategy clause, blind register

**BEFORE (current file, verbatim):**
> In December 2025 the national justice department instructed a national law-enforcement agency to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what it called "radical gender ideology," and the May 2026 counterterrorism strategy framed "radically pro-transgender" ideology as a security threat.

**AFTER (final):**
> In December 2025 the national justice department instructed a national law-enforcement agency to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire to commit the violations listed in section 2 of the guidance or other offenses against the country, and the May 2026 counterterrorism strategy stated that national counterterrorism activities would prioritize the rapid identification and neutralization of violent secular political groups whose ideology is hostile to the country, radically pro-transgender, and anarchist — a category the same document lists alongside violent left-wing extremists, including anarchists and anti-fascists — while stating that counterterrorism powers will not be used to target people who simply disagree with it.

## 2. Machine-applicable change list for `data/countries.json`

File: `data/countries.json` (top level = dict keyed by country code; `USA.sources` is a list).
Each entry: JSON field path, old string, new string. Strings are given as JSON string-literal
fragments exactly as they must appear in the file (inner double quotes escaped `\"`). Every old
string occurs exactly once in its field, so each is a self-contained find-and-replace unit.
Ten entries = the eight claim occurrences (C1–C8) plus two scope-expansion replacements (C9/C10),
both explicitly flagged (review gate item 4).

### C1 — field path `USA.summary` (line 402; claim 1 sentence)

**old:**
```
In February 2025 the State Department announced a ban on trans athletes entering the United States to compete in women's sports, flagging visa applicants with an internal marking and treating any applicant listing a gender other than assigned sex as grounds for a permanent ban on grounds of fraud.
```
**new:**
```
In February 2025 the State Department announced a ban on trans athletes entering the United States to compete in women's sports, and its 24 February 2025 cable instructs posts to add the case-note tag #sws25 to cases refused under INA 221(g), 214(b) or 212(a)(6)(C)(i), or pending an advisory opinion, pursuant to this Executive Order. Where there is a discrepancy in an applicant's documents or electronic records, or other evidence casting reasonable doubt on the applicant's sex, the cable instructs officers to refuse the case under INA 221(g) and request additional evidence; where an applicant is suspected of wilfully misrepresenting sex or purpose of travel, the officer should consider whether the misrepresentation is material such that it supports an ineligibility finding under INA 212(a)(6)(C)(i) — the fraud ground, whose consequence is a permanent, lifetime exclusion from the United States, for which limited waiver possibilities exist — a finding that requires all four elements, so a gender-marker discrepancy never automatically produces that bar.
```

### C2 — field path `USA.summary` (line 402; claim 2 sentence)

**old:**
```
In December 2025 the attorney general instructed the FBI to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what she called \"radical gender ideology,\" describing such activists as \"domestic terrorist groups.\"
```
**new:**
```
In December 2025 the attorney general instructed the FBI to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 of the guidance or other offenses against the United States; the same memorandum uses the phrase \"radical gender ideology\" twice — once among the extreme viewpoints it says animate \"certain Antifa-aligned extremists\" \"with a willingness to use violence against law-abiding citizenry,\" and once in a list of political and social agendas attributed to \"violent extremist groups\" more generally — and never as a criterion for the reward.
```

### C3 — field path `USA.blindSummary` (line 501; claim 1 sentence, blind register)

**old:**
```
In February 2025 the foreign ministry announced a ban on trans athletes entering the country to compete in women's sports, flagging visa applicants with an internal marking and treating any applicant listing a gender other than assigned sex as grounds for a permanent ban on grounds of fraud.
```
**new:**
```
In February 2025 the foreign ministry announced a ban on trans athletes entering the country to compete in women's sports, and its 24 February 2025 cable instructs posts to add the case-note tag — the same text in all cases refused or pending an advisory opinion under the February 2025 executive order. Where there is a discrepancy in an applicant's documents or records, or other evidence casting reasonable doubt on the applicant's sex, the cable instructs officers to refuse the case and request additional evidence; where an applicant is suspected of wilfully misrepresenting sex or purpose of travel, the adjudicating officer should consider whether the misrepresentation is material such that it supports a permanent, lifetime ineligibility finding under the immigration code's fraud ground — a finding that requires all four elements, for which limited waiver possibilities exist, and which is never automatic.
```

### C4 — field path `USA.blindSummary` (line 501; claim 2 sentence, blind register)

**old:**
```
In December 2025 the national justice department instructed a national law-enforcement agency to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what it called \"radical gender ideology,\" describing such activists as \"domestic terrorist groups.\"
```
**new:**
```
In December 2025 the national justice department instructed a national law-enforcement agency to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 of the guidance or other offenses against the country; the same memorandum uses the phrase \"radical gender ideology\" twice — once among the extreme viewpoints it says animate actors \"with a willingness to use violence against law-abiding citizenry,\" and once in a list of political and social agendas attributed to violent extremist groups more generally — and never as a criterion for the reward.
```

### C5 — field path `USA.sources[15].summary` (line 469; whole field value)

**old:**
```
Wikipedia: 5 Feb 2025 EO 'Keeping Men Out of Women's Sports'; State Department announced (25 Feb 2025) banning trans athletes from entering the US to compete in women's sports, flagging visa applicants 'SWS25', and a permanent ban on applicants listing a gender other than assigned sex as 'fraud'.
```
**new:**
```
5 Feb 2025 EO 'Keeping Men Out of Women's Sports'; State Department announced (25 Feb 2025) banning trans athletes from entering the US to compete in women's sports; the State Department's 24 February 2025 cable instructs posts to add the case-note tag #sws25 to cases refused under INA 221(g), 214(b) or 212(a)(6)(C)(i), or pending an advisory opinion, pursuant to this Executive Order; where there is a discrepancy in an applicant's documents or electronic records, or other evidence casting reasonable doubt on the applicant's sex, the cable instructs officers to refuse the case under INA 221(g) and request additional evidence; where an applicant is suspected of wilfully misrepresenting sex or purpose of travel, the officer should consider whether the misrepresentation is material such that it supports an ineligibility finding under INA 212(a)(6)(C)(i), whose consequence is a permanent, lifetime exclusion from the United States, for which limited waiver possibilities exist, on all four elements — never automatic.
```

### C6 — field path `USA.sources[14].summary` (line 464; claim sentence only; text before and
after this fragment in the field is unchanged)

**old:**
```
Persecution of transgender people under the second Trump administration (Wikipedia): In December 2025 Attorney General Pam Bondi instructed the FBI to begin offering cash bounties for information leading to the identification and arrest of transgender activists promoting what she called \"radical gender ideology,\" describing such activists as \"domestic terrorist groups.\"
```
**new:**
```
In December 2025 Attorney General Pam Bondi instructed the FBI to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 of this guidance or other offenses against the United States; the same memorandum uses the phrase \"radical gender ideology\" twice — once among the extreme viewpoints it says animate \"certain Antifa-aligned extremists\" \"with a willingness to use violence against law-abiding citizenry,\" and once in a list of political and social agendas attributed to \"violent extremist groups\" more generally — and never as a criterion for the reward.
```
(the field's next sentence, beginning "In May 2026 the White House's …", is untouched)

### C7 — field path `USA.localsOnly` (line 520; claim 2 + strategy sentence)

**old:**
```
In December 2025 the attorney general instructed the FBI to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what she called \"radical gender ideology,\" and the May 2026 counterterrorism strategy framed \"radically pro-transgender\" ideology as a security threat.
```
**new:**
```
In December 2025 the attorney general instructed the FBI to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire to commit the violations listed in section 2 of her guidance or other offenses against the United States, and the May 2026 counterterrorism strategy stated that national counterterrorism activities would \"prioritize the rapid identification and neutralization of violent secular political groups whose ideology is anti-American, radically pro-transgender, and anarchist\" — a category the same document lists alongside \"Violent Left-Wing Extremists, including Anarchists and Anti-Fascists\" — while stating that counterterrorism powers \"will not be used to target our fellow Americans who simply disagree with us.\"
```

### C8 — field path `USA.blindLocalsOnly` (line 521; claim 2 + strategy sentence, blind register)

**old:**
```
In December 2025 the national justice department instructed a national law-enforcement agency to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what it called \"radical gender ideology,\" and the May 2026 counterterrorism strategy framed \"radically pro-transgender\" ideology as a security threat.
```
**new:**
```
In December 2025 the national justice department instructed a national law-enforcement agency to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire to commit the violations listed in section 2 of the guidance or other offenses against the country, and the May 2026 counterterrorism strategy stated that national counterterrorism activities would prioritize the rapid identification and neutralization of violent secular political groups whose ideology is hostile to the country, radically pro-transgender, and anarchist — a category the same document lists alongside violent left-wing extremists, including anarchists and anti-fascists — while stating that counterterrorism powers will not be used to target people who simply disagree with it.
```

### C9 — field path `USA.outOfScopeNotes` (line 403; **SCOPE-EXPANSION ITEM** — beyond the original
eight-occurrence scope, added per review gate item 4 to resolve the outdated corroboration caveat
explicitly rather than silently)

**old:**
```
The Wikipedia-sourced claims about Federal Bureau of Prisons conversion-therapy-style policies, ICE forced labour and abuse, the December 2025 cash-bounty instruction, and the May 2026 counterterrorism strategy language are drawn from a single encyclopedic source in this inventory and are not independently corroborated here; the underlying primary documents should be checked before relying on them.
```
**new:**
```
The Federal Bureau of Prisons conversion-therapy-style policies and the ICE forced labour and abuse claims are drawn from a single encyclopedic source in this inventory and are not independently corroborated here. The December 2025 cash-bounty instruction and the May 2026 counterterrorism strategy language are documented in primary documents reviewed in an audit. A bounded search as of November 2026 found no documented instance of the permanent fraud ground under INA 212(a)(6)(C)(i) being imposed for a gender-marker discrepancy and no posted reward; whether and how these directives are implemented in practice is not established by the documents.
```

### C10 — field path `USA.blindOutOfScope` (line 502; **SCOPE-EXPANSION ITEM** — blind counterpart
of C9, same scope flag)

**old:**
```
The encyclopedic-source claims about corrections-bureau conversion-therapy-style policies, immigration-custody forced labour and abuse, the December 2025 cash-bounty instruction, and the May 2026 counterterrorism strategy language are drawn from a single encyclopedic source in this inventory and are not independently corroborated here; the underlying primary documents should be checked before relying on them.
```
**new:**
```
The corrections-bureau conversion-therapy-style policies and the immigration-custody forced labour and abuse claims are drawn from a single encyclopedic source in this inventory and are not independently corroborated here. The December 2025 cash-bounty instruction and the May 2026 counterterrorism strategy language are documented in primary documents reviewed in an audit. A bounded search as of November 2026 found no documented instance of the permanent fraud ground under the immigration code being imposed for a gender-marker discrepancy and no posted reward; whether and how these directives are implemented in practice is not established by the documents.
```

Each old string is asserted to occur exactly once in its field immediately before application (the
whole operation aborts on any mismatch). After application, `data/countries.json` must be re-parsed
as JSON and compared against the pre-application parse: only the ten §2 field values (eight distinct
USA fields) may differ — no other field, number, score, or country object is touched.

## 3. Backend/dev provenance note (not for display)

<!-- ============================================================
     BACKEND / DEV PROVENANCE NOTE — NOT FOR DISPLAY
     Do not render this block in user-visible output, blind
     records, or any dossier surface. Backend provenance only.
     ============================================================ -->

**Provenance (backend/dev only — NOT FOR DISPLAY):** The two Wikipedia-derived source-summary fields
(`USA.sources[15].summary`, entry for Executive Order 14201; `USA.sources[14].summary`, entry for
*Persecution of transgender people under the second Trump administration*) are secondary summaries
whose original claim sentences overstate the underlying primary texts read during this audit:

1. **`sources[15]` (secondary claim vs primary).** The secondary summary described an applicant-level
   internal marking and a permanent fraud ban as the automatic consequence of listing a gender other
   than assigned at birth. Primary (24 Feb 2025 State cable, OCR-verified, `us-primary-ocr.md` ¶¶6–8,
   Q2, Q5): the #sws25 string is a case-note tag applied to cases refused under INA 221(g), 214(b) or
   212(a)(6)(C)(i), or pending an advisory opinion, "pursuant to this E.O." (tag ≠ finding); a bare
   document discrepancy or reasonable doubt yields a reversible 221(g) refusal + evidence request;
   the permanent, lifetime fraud ground under INA 212(a)(6)(C)(i) requires suspected wilful,
   material misrepresentation found on all four enumerated elements — no automaticity.
2. **`sources[14]` (secondary claim vs primary).** The secondary summary described cash bounties on
   "transgender activists" who were "describing[d] … as 'domestic terrorist groups.'" Primary
   (4 Dec 2025 Bondi NSPM-7 memo, double-sourced OCR, `us-primary-ocr.md` Q7–Q9): the directive is
   "the FBI shall establish a cash reward system for information that leads to the successful
   identification and arrest of individuals in the leadership of domestic terrorist organizations
   that conspire with others to commit violations of the provisions of law listed in section 2 of
   this guidance or other offenses against the United States"; the strings "transgender"/"trans"
   appear zero times in the memo; "radical gender ideology" appears exactly twice (Q8), both as a
   listed viewpoint framed by willingness to use violence, never as a reward criterion; "domestic
   terrorist organizations" is tied to 18 U.S.C. § 2331(5) criminal conduct with an express First
   Amendment footnote (Q9).

**Disposition:** per the binding user convention, the claim sentences in both fields were rewritten
in place as clean verified prose stating the primary-verified account itself (change list §2, items
C5 and C6); no attribution scaffolding or citation-gap markers appear in the rendered fields. This
block is the *only* record of the secondary-vs-primary discrepancy and must stay backend-only.
Provenance tags: `secondary=wikipedia-articles`, `primary=us-cable-2025-02-24 (OCR, 1 copy,
3 agreeing passes)` + `us-memo-2025-12-04 (OCR + 2 independent text renditions, identical)`,
audit run = `country-calibration-audit`, proposal doc = `us-repair-proposal-v2.md` §1c/§2c/§5
(A/B pick resolved by convention).

## 4. Validation table vs primary quotes (`us-primary-ocr.md`)

Each edited passage (C1–C8) checked against the verbatim primary quotes recorded in
`us-primary-ocr.md` on all six dimensions. Verdict keys: **M** = matches primary; **K** = primary
requires this exact change (the old text failed this dimension).

**Evidence-location note (carried from v2 §9):** `us-primary-ocr.md` contains no May 2026 strategy
quote — its §4 is a post-May-2026 enforcement search. The strategy clause in C7/C8 is validated
against the verbatim May 2026 whitehouse.gov quotes in `us-claims-scope.md` §b2 (direct primary
source, pp. 4, 5, 7), recorded there alongside the `us-primary-ocr.md` memo/cable evidence.

### 4.1 Claim 1 passages (C1 `USA.summary`, C3 `USA.blindSummary`, C5 `sources[15].summary`)

| Dimension | Primary quote (`us-primary-ocr.md`) | C1 / C3 / C5 after-text | Verdict |
|---|---|---|---|
| **Population** | ¶6: "both immigrant and nonimmigrant visa applications … all visas must reflect an applicant's sex at birth"; scope verdict: ¶¶6–7 general, no athlete limitation | "an applicant's … sex" / "the applicant's sex" — no athlete limit, no person-category target | **M** |
| **Trigger** | ¶6: "If there is a discrepancy either in the applicant's documents or in electronic consular records, or if other evidence casts reasonable doubt on the applicant's sex, you should refuse the case under 221(g) and request additional evidence"; ¶7: suspected misrepresentation → "you should consider whether the misrepresentation is material" + four elements (Q2, Q3) | discrepancy/doubt → the cable instructs officers to refuse the case under 221(g) and request additional evidence (the instructed step stated as an instruction, not an outcome — F4); suspected wilful material misrepresentation → consideration of 212(a)(6)(C)(i) finding on all four elements; permanent consequence stated with the limited waiver possibilities that exist (F4 nuance); "never automatically" / "never automatic" kept | **K** (old text claimed automatic ground; primary has two-step suspicion-plus-elements path) |
| **Trigger (tag scope)** | ¶8: "in all cases refused 221(g), 214(b), or (6)(C)(i) or pending an AO pursuant to this E.O.: #sws25" (Q5: "tag ≠ adverse finding") | C1/C5: literal token #sws25 on cases refused under INA 221(g), 214(b) or 212(a)(6)(C)(i), or pending an AO, "pursuant to this Executive Order"; blind C3 describes the tag without the literal token ("the case-note tag"), "under the February 2025 executive order" (F1) | **K** (old text: applicant-level flagging) |
| **Consequence** | ¶7 four-element fraud ground (permanent bar under INA 212(a)(6)(C)(i)); Q2: bare discrepancy is reversible; `us-claims-scope.md` claim (a): limited waiver possibilities exist | permanent, lifetime exclusion / ineligibility finding stated in all three after-texts; 221(g) step shown as reversible; no automaticity; limited waiver possibilities stated so relief is not implied impossible (F4 nuance) | **K** (old C1 text asserted automatic permanent ban; after-text keeps the real permanent risk, drops only automaticity) |
| **Actor** | header: "From: SECSTATE WASHDC" / "Action: ALL DIPLOMATIC AND CONSULAR POSTS" (Q1 header) | C1: "the State Department … its 24 February 2025 cable"; C3: "the foreign ministry … its 24 February 2025 cable"; C5: "the State Department's 24 February 2025 cable" | **M** (blind register carries no State/INA institution names beyond the established convention) |
| **Date** | header "Date/DTG: Feb 24, 2025"; EO 14201 5 Feb 2025; announcement 25 Feb 2025 | "24 February 2025", "February 2025", "25 Feb 2025", "5 Feb 2025" all carried verbatim | **M** |
| **Operative status** | ¶1 "should carefully review and follow this guidance effective immediately"; ¶7 "you should consider" (Q4: no "case-by-case", no automatic-ban language) | instruction verbs ("instructs posts to add", "instructs officers to refuse … and request additional evidence", "should consider"); the instructed step is stated as an instruction, not as an outcome (F4); no "case-by-case" wording introduced | **M** |

### 4.2 Claim 2 passages (C2 `USA.summary`, C4 `USA.blindSummary`, C6 `sources[14].summary`,
C7 `USA.localsOnly`, C8 `USA.blindLocalsOnly`)

| Dimension | Primary quote (`us-primary-ocr.md`) | C2 / C4 / C6 / C7 / C8 after-text | Verdict |
|---|---|---|---|
| **Population** | Q7: "individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 of this guidance or other offenses against the United States"; "transgender" = 0 hits (grep, OCR + both renditions) | same population stated in all five after-texts; "transgender activists" removed everywhere; blind C4/C8 use "against the country" for "against the United States" | **K** (old text named a population the memo never mentions) |
| **Trigger** | Q7: "a cash reward system for information that leads to the successful identification and arrest of …"; Q8: phrase never a criterion | reward for information leading to ID/arrest of org leadership; both "radical gender ideology" appearances described (Q8 occurrence 1 = Antifa-aligned extremists, occurrence 2 = list attributed to violent extremist groups more generally); "never as a criterion for the reward" | **K** (old text made the phrase a selection criterion and used "only as" exclusivity that two appearances do not support) |
| **Consequence** | Q7: "shall establish" is prospective/administrative — no reward amount, no named target, no posted bounty | "establish a cash reward system" — directive stated, no enforcement outcome or posted bounty claimed | **M** |
| **Actor** | memo: "FROM: THE ATTORNEY GENERAL" / "the FBI shall establish" (Q6, Q7) | C2/C6: "the attorney general instructed the FBI" with "Attorney General Pam Bondi" retained in C6; C7 "her guidance"; C4/C8 blind equivalents | **M** |
| **Date** | memo letterhead "December 4, 2025" (Q6); strategy May 2026 | "In December 2025" kept in all five (day-level precision not introduced; no field says 5 Dec — v2 §7); "May 2026" kept | **M** |
| **Operative status** | Q7 "shall establish"; strategy p. 7 "will also prioritize …" + p. 4 "will not be used to target …" (per `us-claims-scope.md` §b2, see evidence note) | directive stated as instruction, not an implemented bounty; strategy clause: "stated that … would \"prioritize …\"" with the "will not be used to target" disclaimer retained (C7 verbatim quotes; C8 blind paraphrase of country-naming fragments) | **M** |

### 4.3 Full-quote cross-check of the May 2026 clause (C7 verbatim fragments)

| C7 fragment | Verbatim source (`us-claims-scope.md` §b2, whitehouse.gov PDF) | Verdict |
|---|---|---|
| "prioritize the rapid identification and neutralization of violent secular political groups whose ideology is anti-American, radically pro-transgender, and anarchist" | p. 7 sentence, quoted character-for-character | **M** |
| "Violent Left-Wing Extremists, including Anarchists and Anti-Fascists" | p. 5 taxonomy line | **M** |
| "will not be used to target our fellow Americans who simply disagree with us" | p. 4 disclaimer | **M** |

### 4.4 Named vs blind equivalence (all pairs)

| Fact | Named | Blind | Equivalent? |
|---|---|---|---|
| #sws25 tag, order-qualified | C1/C5: literal token #sws25 + INA grounds + "pursuant to this Executive Order" | C3: tag described without the literal token ("the case-note tag"), "refused or pending an advisory opinion under the February 2025 executive order" (no INA numbers, no literal token in blind register) | yes |
| Permanent consequence + four elements + no automaticity | C1, C5 | C3: "permanent, lifetime ineligibility finding … all four elements … never automatic" | yes |
| Reward population + full offense alternative | C2/C6: "section 2 of the guidance/this guidance or other offenses against the United States"; C7: "her guidance … the United States" | C4/C8: "the country" | yes (register noun only) |
| Both "radical gender ideology" appearances | C2/C6 name Antifa-aligned extremists | C4 describes occurrence 1 by its violence framing (no "Antifa" label in blind register) | yes in substance |
| Strategy scope + disclaimer | C7 verbatim quotes | C8 ideology trio paraphrased — "hostile to the country" replaces the jurisdiction-naming fragment (F2), violence qualifier and all three conjunctive characteristics kept; taxonomy/disclaimer paraphrased (they name the country population) | yes in substance |

Recorded separately per review finding 2: the pre-existing `USA.blindSummary` still quotes the
strategy fragment including the jurisdiction-naming term; it is not introduced by this proposal and
stays a separate follow-up.

### 4.5 Scope-expansion passages (C9 `USA.outOfScopeNotes`, C10 `USA.blindOutOfScope`)

Flagged scope-expansion items (review gate item 4), validated against `us-primary-ocr.md` §4
(bounded post-May-2026 search) and §0–§3: the directives' primary-document provenance (24 Feb 2025
cable, 4 Dec 2025 memorandum, published May 2026 strategy); no documented instance of the fraud
ground imposed for a gender-marker discrepancy and no posted reward found as of November 2026;
questions that genuinely still stand are kept (the corrections/immigration-custody claims remain
single-source here; implementation of the directives in practice is not established by the
documents). C10 is the blind-register counterpart of C9 with register nouns only.

## 5. Confirmation: dates/numbers/names vs primary evidence (corrected per review point 5)

**Confirmed, with the accounting corrected.** The previous version of this section claimed that no
day-level date was added and that all numbers were carried verbatim — an overstatement: the old
passages lack the inserted **24 February 2025** date, the statutory section numbers and **"four
elements"**. Those are new, evidence-supported additions (not carried-over text) and they stay;
this section now states additions vs carried-over accurately. Detail:

**Dates — carried verbatim from the old text (none removed, none altered):**
- "February 2025" (ban announcement), "25 Feb 2025" and "5 Feb 2025 EO 'Keeping Men Out of Women's
  Sports'" (C5, unchanged), "In December 2025" (memo; printed date is 4 December 2025 and no field
  says 5 Dec — v2 §7 check still stands, no date fix needed), "May 2026" (strategy).

**Dates — newly inserted, evidence-supported (old text lacked them):** "24 February 2025" (cable
date — matches header "Date/DTG: Feb 24, 2025") in C1/C3/C5. This is a day-level date added where
the old text had none; primary evidence requires it, so it is kept.

**Numbers — carried verbatim from the old text:** the years "2025"/"2026", line numbers (402, 464,
469, 501, 520, 521) and the field indices `sources[14]`/`sources[15]` — unchanged.

**Numbers — newly inserted, evidence-supported (old text lacked them):** "four elements"
(C1/C3/C5), INA sections "221(g)", "214(b)", "212(a)(6)(C)(i)" (C1/C5), "section 2" of the
guidance (C2/C4/C6/C7/C8) and "twice" (the memo's two "radical gender ideology" appearances, per
Q8's grep count). Each is quoted from the primary documents; none alters a figure the old text
carried.

**Names — all carried verbatim or handled by register:** "State Department", "FBI", "Attorney
General Pam Bondi" (C6, kept), "her"/"she" pronouns (C2/C6/C7), EO titles "Keeping Men Out of
Women's Sports" (C5), blind-register equivalents ("foreign ministry", "national justice
department", "a national law-enforcement agency", "the country") unchanged from the file's own
convention. Removed names/labels are exactly the ones the primary text does not support: the
"transgender activists" bounty population (memo: 0 hits) and "describing such activists as
'domestic terrorist groups'" (memo describes organizations, Q9) — their removal is required by
evidence, not a style choice.

**Quoted ideology terms — corrected claim (review point 5):** "radical gender ideology" remains in
every claim-2 passage where the old text contained it (C2/C4/C6/C7/C8), and "radically
pro-transgender" remains in both strategy passages (C7 verbatim; C8 inside the paraphrased,
identity-safe trio). The visa passages (C1/C3/C5) never contained either term and still do not. The
earlier claim that both terms remain "in every occurrence" was not literal and is dropped: neither
term appears in all ten passages, and no passage lost a term it originally had.

**Numbers/dates/names outside the 10 passages:** untouched — no other sentence in the six claim
fields, no other `USA` field except `outOfScopeNotes`/`blindOutOfScope` under the explicitly flagged
scope-expansion replacements C9/C10 (`tangentialFactors`, `blindTangential`, `comparisons`,
`scoreProvenance`, `rank`, … untouched), no other country object, no score, band, rubric or
UI text, and no archived log was modified (v2 §8 listed-only items stay listed-only; the ASM
occurrence at line 18029 remains a separate follow-up ticket).

**Task-level confirmations:** the corrected change list C1–C10 has been applied to
`data/countries.json` under the review's application gates — exactly the ten §2 replacements across
eight USA field values; `git diff --cached` empty (no staged files); no commits; no score changes;
no UI changes; `tools/build_data.py` and all scoring tools not run. Files written by this task: this
document and `data/countries.json`.