# US dossier repair proposal — two overstated claims (PROPOSAL ONLY, not applied)

Scope: `data/countries.json` → `USA` object only. **No repository file has been edited or staged by this
task.** This document is a draft for reviewer approval.

Evidence base:
- `research/experiments/country-calibration-audit/us-primary-ocr.md` (primary text: 24 Feb 2025 State cable,
  OCR of image-only PDF, three agreeing tesseract passes; 4 Dec 2025 Bondi NSPM-7 memo, OCR + two independent
  text renditions agreeing character-for-character).
- `research/experiments/country-calibration-audit/us-claims-scope.md` (citation-chain verdicts).

## Summary table

| # | Claim | Field (line) | Before (gist) | After (gist) | Primary-text basis |
|---|---|---|---|---|---|
| 1a | Visa / fraud bar | `USA.summary` (402) | "flagging visa applicants with an internal marking and treating any applicant listing a gender other than assigned sex as grounds for a permanent ban on grounds of fraud" | SWS25 = case-note tag on refused/pending cases; discrepancy or reasonable doubt → INA 221(g) refusal + evidence request; suspected wilful material misrepresentation → possible INA 212(a)(6)(C)(i) finding on four elements incl. materiality, officer judgement, AO available | Cable ¶6, ¶7, ¶8 |
| 1b | Visa / fraud bar | `USA.blindSummary` (501) | same sentence, blind register | same narrowing, blind register (no INA/State names) | Cable ¶6, ¶7, ¶8 |
| 1c | Visa / fraud bar | `USA.sources[15].summary` (469) | "flagging visa applicants 'SWS25', and a permanent ban on applicants listing a gender other than assigned sex as 'fraud'" | refused/pending case-note tag; two-step path; permanent fraud bar only on wilful, material misrepresentation found on four elements | Cable ¶6, ¶7, ¶8 |
| 2a | FBI cash bounties | `USA.summary` (402) | "cash bounties … identification and arrest of transgender activists … describing such activists as 'domestic terrorist groups'" | cash reward system for info leading to ID/arrest of **individuals in the leadership of** domestic terrorist organizations conspiring to commit the violations listed in §2 of the guidance or other offenses against the US; "radical gender ideology" kept but scoped as one listed viewpoint of violent-willing "certain Antifa-aligned extremists" | Memo p. 6 §8 (verbatim, double-sourced); p. 2 §1 |
| 2b | FBI cash bounties | `USA.blindSummary` (501) | same, blind register | same narrowing, blind register | same |
| 2c | FBI cash bounties | `USA.sources[14].summary` (464) | same with "Attorney General Pam Bondi" | same narrowing, names kept | same |
| 2d | FBI cash bounties | `USA.localsOnly` (520) | "cash bounties … transgender activists … 'radical gender ideology'" | same narrowing; trailing May 2026 strategy clause kept verbatim | same |
| 2e | FBI cash bounties | `USA.blindLocalsOnly` (521) | same, blind register | same narrowing, blind register; trailing clause kept verbatim | same |
| 3 | Memo date check | all USA fields | — | **no field says 5 Dec** → no change required | Memo p. 1: "December 4, 2025" |
| 4 | Repeat/adjacent overstatements | see §5 | — | listed only; archived rating logs are immutable history, no changes proposed | — |

Nothing else in the `USA` object (`outOfScopeNotes`, `blindOutOfScope`, `tangentialFactors`, `blindTangential`,
`comparisons`, `sources[16].summary`, `sources[17].summary`, `blindSourceSummaries` (12 entries, none matching),
`scoreProvenance`, `provisionalCalibration`, `rank`, `anchorRefs`) contains either claim.

---

## (a) Exact current occurrences (verbatim, with field name and line)

File: `data/countries.json`, object `USA`.
Quotes below are the sentences exactly as rendered; in the raw JSON the embedded double quotes appear
escaped as `\"`, as they already are in the file.

### Claim 1 — visa / automatic permanent fraud ban

**A1. `USA.summary` (line 402), paragraph starting "Entry screening carries its own exposure."**
> "In February 2025 the State Department announced a ban on trans athletes entering the United States to compete in women's sports, flagging visa applicants with an internal marking and treating any applicant listing a gender other than assigned sex as grounds for a permanent ban on grounds of fraud."

**A2. `USA.blindSummary` (line 501), same paragraph position:**
> "In February 2025 the foreign ministry announced a ban on trans athletes entering the country to compete in women's sports, flagging visa applicants with an internal marking and treating any applicant listing a gender other than assigned sex as grounds for a permanent ban on grounds of fraud."

**A3. `USA.sources[15].summary` (line 469; source = `Executive Order 14201`, Wikipedia), entire field:**
> "Wikipedia: 5 Feb 2025 EO 'Keeping Men Out of Women's Sports'; State Department announced (25 Feb 2025) banning trans athletes from entering the US to compete in women's sports, flagging visa applicants 'SWS25', and a permanent ban on applicants listing a gender other than assigned sex as 'fraud'."

### Claim 2 — FBI cash bounties on "transgender activists … domestic terrorist groups"

**B1. `USA.summary` (line 402), paragraph "Official hostility extends to advocacy and speech.":**
> "In December 2025 the attorney general instructed the FBI to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," describing such activists as "domestic terrorist groups.""

(The following sentence — the May 2026 Counterterrorism Strategy quote — is verbatim-verified and is **not** changed.)

**B2. `USA.blindSummary` (line 501), same paragraph:**
> "In December 2025 the national justice department instructed a national law-enforcement agency to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what it called "radical gender ideology," describing such activists as "domestic terrorist groups.""

**B3. `USA.sources[14].summary` (line 464; source = `Persecution of transgender people under the second Trump administration`, Wikipedia):**
> "Persecution of transgender people under the second Trump administration (Wikipedia): In December 2025 Attorney General Pam Bondi instructed the FBI to begin offering cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," describing such activists as "domestic terrorist groups.""

**B4. `USA.localsOnly` (line 520), paragraph "Service access has narrowed:":**
> "In December 2025 the attorney general instructed the FBI to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," and the May 2026 counterterrorism strategy framed "radically pro-transgender" ideology as a security threat."

**B5. `USA.blindLocalsOnly` (line 521), same paragraph:**
> "In December 2025 the national justice department instructed a national law-enforcement agency to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what it called "radical gender ideology," and the May 2026 counterterrorism strategy framed "radically pro-transgender" ideology as a security threat."

---

## (b) Proposed replacements (before → after)

All before/after text below is shown as **rendered text** (plain quote marks). When applied to
`data/countries.json`, every `"` inside a string value must be written in JSON as `\"`, exactly as the
current sentences already are.

### 1a. `USA.summary` — claim 1

**BEFORE:**
> In February 2025 the State Department announced a ban on trans athletes entering the United States to compete in women's sports, flagging visa applicants with an internal marking and treating any applicant listing a gender other than assigned sex as grounds for a permanent ban on grounds of fraud.

**AFTER:**
> In February 2025 the State Department announced a ban on trans athletes entering the United States to compete in women's sports, and its 24 February 2025 cable instructs posts to add the case-note tag "SWS25" to cases refused under INA 221(g), 214(b) or 212(a)(6)(C)(i) or pending an advisory opinion. A discrepancy in an applicant's documents or electronic records, or other evidence casting reasonable doubt on the applicant's sex, leads to a refusal under INA 221(g) with a request for additional evidence; where an applicant is suspected of wilfully misrepresenting sex or purpose of travel, the officer should consider whether the misrepresentation is material such that it supports an ineligibility finding under INA 212(a)(6)(C)(i), which requires all four elements.

### 1b. `USA.blindSummary` — claim 1 (blind register: no "State Department", no "INA", no proper institution names)

**BEFORE:**
> In February 2025 the foreign ministry announced a ban on trans athletes entering the country to compete in women's sports, flagging visa applicants with an internal marking and treating any applicant listing a gender other than assigned sex as grounds for a permanent ban on grounds of fraud.

**AFTER:**
> In February 2025 the foreign ministry announced a ban on trans athletes entering the country to compete in women's sports, and its 24 February 2025 cable instructs posts to add the case-note tag "SWS25" to refused or pending cases. A discrepancy in an applicant's documents or records, or other evidence casting reasonable doubt on the applicant's sex, leads to a refusal with a request for additional evidence; where an applicant is suspected of wilfully misrepresenting sex or purpose of travel, the adjudicating officer should consider whether the misrepresentation is material such that it supports a permanent ineligibility finding under the immigration code's fraud ground, which requires all four elements.

### 1c. `USA.sources[15].summary` — claim 1

**BEFORE:**
> Wikipedia: 5 Feb 2025 EO 'Keeping Men Out of Women's Sports'; State Department announced (25 Feb 2025) banning trans athletes from entering the US to compete in women's sports, flagging visa applicants 'SWS25', and a permanent ban on applicants listing a gender other than assigned sex as 'fraud'.

**AFTER:**
> Wikipedia: 5 Feb 2025 EO 'Keeping Men Out of Women's Sports'; State Department announced (25 Feb 2025) banning trans athletes from entering the US to compete in women's sports and tagging refused or pending cases with case note 'SWS25'; the underlying 24 Feb 2025 cable sends a document discrepancy or reasonable doubt about sex to a refusal under INA 221(g) with a request for evidence, and supports a permanent fraud bar under INA 212(a)(6)(C)(i) only where wilful, material misrepresentation is found on the four required elements.

### 2a. `USA.summary` — claim 2

**BEFORE:**
> In December 2025 the attorney general instructed the FBI to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," describing such activists as "domestic terrorist groups."

**AFTER (rendered):**
> In December 2025 the attorney general instructed the FBI to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 of the guidance or other offenses against the United States; the same memorandum lists adherence to "radical gender ideology" only as one of the extreme viewpoints of "certain Antifa-aligned extremists" "with a willingness to use violence against law-abiding citizenry."

(Quoted fragments are substrings of the memo: "certain Antifa-aligned extremists" and "with a willingness to use violence against law-abiding citizenry" both appear verbatim in p. 2 §1; the sentence's own full stop follows the closing quotation mark.)

### 2b. `USA.blindSummary` — claim 2 (blind register: "national justice department", "a national law-enforcement agency", no "FBI", no "Antifa", "the country")

**BEFORE:**
> In December 2025 the national justice department instructed a national law-enforcement agency to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what it called "radical gender ideology," describing such activists as "domestic terrorist groups."

**AFTER (rendered):**
> In December 2025 the national justice department instructed a national law-enforcement agency to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 of the guidance or other offenses against the country; the same memorandum lists adherence to what it calls "radical gender ideology" only as one of the extreme viewpoints held by actors "with a willingness to use violence against law-abiding citizenry."

### 2c. `USA.sources[14].summary` — claim 2 (names kept: "Attorney General Pam Bondi", "FBI")

**BEFORE:**
> Persecution of transgender people under the second Trump administration (Wikipedia): In December 2025 Attorney General Pam Bondi instructed the FBI to begin offering cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," describing such activists as "domestic terrorist groups."

**AFTER (rendered):**
> Persecution of transgender people under the second Trump administration (Wikipedia): In December 2025 Attorney General Pam Bondi instructed the FBI to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 of her guidance or other offenses against the United States; the same memorandum lists adherence to "radical gender ideology" only as one of the extreme viewpoints of "certain Antifa-aligned extremists" "with a willingness to use violence against law-abiding citizenry."

### 2d. `USA.localsOnly` — claim 2 (second clause kept verbatim)

**BEFORE:**
> In December 2025 the attorney general instructed the FBI to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," and the May 2026 counterterrorism strategy framed "radically pro-transgender" ideology as a security threat.

**AFTER (rendered):**
> In December 2025 the attorney general instructed the FBI to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire to commit the violations listed in section 2 of her guidance, and the May 2026 counterterrorism strategy framed "radically pro-transgender" ideology as a security threat.

### 2e. `USA.blindLocalsOnly` — claim 2 (second clause kept verbatim)

**BEFORE:**
> In December 2025 the national justice department instructed a national law-enforcement agency to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what it called "radical gender ideology," and the May 2026 counterterrorism strategy framed "radically pro-transgender" ideology as a security threat.

**AFTER (rendered):**
> In December 2025 the national justice department instructed a national law-enforcement agency to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire to commit the violations listed in section 2 of the guidance, and the May 2026 counterterrorism strategy framed "radically pro-transgender" ideology as a security threat.

---

## (c) What survives verbatim, what is removed, what is added — and why

### Claim 1 (visa / fraud bar)

**Survives verbatim (kept facts):**
- "In February 2025 the State Department announced a ban on trans athletes entering the United States to compete in women's sports" — kept in 1a; 1b keeps the blind equivalents ("the foreign ministry … entering the country"); 1c keeps "State Department announced (25 Feb 2025) banning trans athletes …".
- "trans athletes", "women's sports", "February 2025" / "25 Feb 2025", "5 Feb 2025 EO 'Keeping Men Out of Women's Sports'" (1c).
- The **permanent fraud bar mechanism itself** — INA 212(a)(6)(C)(i) as a real, documented risk reachable in any visa case where sex or purpose of travel is allegedly misrepresented — kept and now stated with its primary-text trigger.
- The internal marking — kept, renamed precisely to what the cable says it is: the case-note tag `#sws25`.

**Removed words and why (primary quotes):**
- "treating any applicant listing a gender other than assigned sex as grounds for a permanent ban on grounds of fraud" (and 1c's "a permanent ban on applicants listing a gender other than assigned sex as 'fraud'").
  - Cable ¶6: "If there is a discrepancy either in the applicant's documents or in electronic consular records, or if other evidence casts reasonable doubt on the applicant's sex, you should refuse the case under 221(g) and request additional evidence to demonstrate sex at birth." → a bare discrepancy yields a **reversible 221(g) refusal + evidence request**, not a permanent bar.
  - Cable ¶7: "In cases where applicants are suspected of misrepresenting their purpose of travel or sex, you should consider whether the misrepresentation is material such that it supports an ineligibility finding under INA section 212(a)(6)(C)(i)" plus the four enumerated elements, incl. "(3) The fact misrepresented is material". → the permanent bar requires suspicion **plus** all four elements, with officer judgement ("you should consider").
  - us-claims-scope verdict (a): automaticity "not supported"; "listing a gender other than assigned sex" ≠ the documented trigger.
- "flagging visa applicants with an internal marking" / "flagging visa applicants 'SWS25'" → replaced with case-note tag on refused/pending cases.
  - Cable ¶8: "Posts are instructed to include the following text in the case notes in all cases refused 221(g), 214(b), or (6)(C)(i) or pending an AO pursuant to this E.O.: #sws25". The tag attaches to refused/pending **cases**, not to applicants generally, and "tag ≠ adverse finding" (us-primary-ocr §Q5).

**Added words and why:**
- "24 February 2025 cable" — the primary document's own date (header "Date/DTG: Feb 24, 2025"), added so the mechanism is anchored to the document rather than to the press announcement.
- "cases refused under INA 221(g), 214(b) or 212(a)(6)(C)(i) or pending an advisory opinion" — verbatim scope of cable ¶8; keeps the real breadth of the tracking instruction (it even tags ordinary 214(b) denials) instead of implying applicants are flagged up front.
- The two-step sentence ("discrepancy/reasonable doubt → 221(g) refusal + request for evidence; suspected wilful material misrepresentation → officer considers materiality → possible 212(a)(6)(C)(i) finding, four elements") — direct rendering of cable ¶6/¶7; adds no new risk, only the primary text's own conditions.
- No "case-by-case" wording is added anywhere: us-primary-ocr §Q4 records that phrase as the **State Department press line, not cable language**, and forbids attributing it (or automaticity) to the primary document. The replacement uses the cable's own "should consider whether the misrepresentation is material".

**Risk deliberately NOT softened:** the permanent ineligibility finding remains in every replacement; the sentence still tells a trans traveller that alleged misrepresentation of sex can reach a lifetime bar. us-claims-scope verdict (a): "the documented risk … is real and is not being downplayed here."

### Claim 2 (FBI cash bounties)

**Survives verbatim (kept facts):**
- "In December 2025" — kept (memo printed date is 4 December 2025; the month-level statement stays correct).
- "the attorney general instructed the FBI" (2a/2c/2d; blind register kept in 2b/2e) — memo: "the FBI shall establish" from the Attorney General.
- "cash" reward for "information leading to the identification and arrest" — kept, restated in the memo's own words ("a cash reward system for information that leads to the successful identification and arrest").
- Names kept where they already appear: "Attorney General Pam Bondi" (2c); "her"/"she" pronouns (2a, 2c, 2d).
- The quoted term "radical gender ideology" — kept in every occurrence, re-scoped, not deleted.
- The trailing May 2026 Counterterrorism Strategy sentence/clause — **untouched** in all fields (us-claims-scope verdict (b2): quote is verbatim-verified primary-source language).

**Removed words and why (primary quotes):**
- "transgender activists" as the bounty population.
  - Memo p. 6 §8 (double-sourced): "…individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 of this guidance or other offenses against the United States."
  - us-primary-ocr §Q7: "transgender", "trans", "trans activists" appear **zero times in the memo** (grep, OCR + both text renditions).
- "promoting what she called 'radical gender ideology'" as the selection criterion for bounties.
  - us-primary-ocr §Q8: the phrase appears twice, never as a bounty criterion; occurrence 1: "For some culpable actors, such as certain Antifa-aligned extremists, their animating principle is adherence to the types of extreme viewpoints on immigration, radical gender ideology, and anti-American sentiment listed below, with a willingness to use violence against law-abiding citizenry to serve those beliefs."
- "describing such activists as 'domestic terrorist groups'".
  - The memo never calls activists or any persons "domestic terrorist groups"; it describes **organizations** ("domestic terrorist organizations") and gives no belief-only predicate (§Q9: criminal-conduct based, 18 U.S.C. § 2331(5), with an express First Amendment footnote). us-claims-scope (b1): "overstates scope on both ends".

**Added words and why:**
- "individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 … or other offenses against the United States" — verbatim scope qualifiers from the operative sentence; this is the narrowing the primary text establishes.
- "only as one of the extreme viewpoints of 'certain Antifa-aligned extremists' 'with a willingness to use violence against law-abiding citizenry'" — keeps the documented gender-ideology risk in place but at the scope the memo gives it (one listed viewpoint, violence-conditioned), quoting the memo so the phrase cannot be read as a bounty trigger.
- "establish a cash reward system" — the memo's operative verb phrase; also captures that the directive is prospective/administrative (no reward amount, no named target, no posted bounty in the document, §Q7).

**Risk deliberately NOT softened:** cash rewards for identifying/arresting organisation leaders remain stated as a real instruction ("shall establish"), and the gender-ideology viewpoint remains quoted; us-primary-ocr §4c documents real NSPM-7 enforcement (June 2026 sentences/indictments; four antifa-aligned FTO designations) on the counterterrorism track.

---

## (d) Memo date check (4 vs 5 December)

- Primary: memo letterhead reads **"December 4, 2025"** (us-primary-ocr §Q6, clean in every copy; resolves the 4-vs-5 contradiction — Pink News "issued on 5 December" and LGBTQ Nation "dated December 5" are wrong or refer to circulation).
- Repository check (`grep -E "December 5|5 December|Dec\.? 5\b"` over `data/countries.json`, plus a regex walk of the whole `USA` subtree for `4/5 December`, `Dec 4/5`, `2025-12-04/05`, `12-4-2025`): **14 matches file-wide, all unrelated** (UK civil-partnership 5 Dec 2005, Chilean civil unions 5 Dec 2018, Brazil/Gibraltar marriage dates, etc.). **No field — USA or any other country — dates the Bondi memo 5 December.**
- The USA fields say only "In December 2025", which is correct.
- **Result: no date error to fix; no change proposed.** (If a future edit wants day-level precision, the correct value is 4 December 2025.)

---

## (e) Additional sentences repeating the overstatements (listed, not yet changed beyond (b))

### In `USA` fields of `data/countries.json` (covered by the replacements above)

1. `USA.summary` (402) — "…flagging visa applicants with an internal marking…" repeats the SWS25-as-applicant-flag overstatement inside the claim-1 sentence → covered by 1a.
2. `USA.blindSummary` (501) — same clause → covered by 1b.
3. `USA.localsOnly` (520) — "…offer cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology,"…" repeats the population overstatement **without** the "domestic terrorist groups" clause → covered by 2d.
4. `USA.blindLocalsOnly` (521) — same, blind → covered by 2e.
5. `USA.sources[14].summary` (464) — repeats claim 2 verbatim → covered by 2c.
6. `USA.sources[15].summary` (469) — repeats claim 1 verbatim → covered by 1c.
7. `USA.outOfScopeNotes` (403) / `USA.blindOutOfScope` (502): "…the December 2025 cash-bounty instruction, and the May 2026 counterterrorism strategy language are drawn from a single encyclopedic source in this inventory and are not independently corroborated here; the underlying primary documents should be checked before relying on them." — **not an overstatement**, so no change proposed; noted only because the primary documents have now been read (memo OCR'd from three copies), so this caveat may be reported as satisfied by the reviewer's decision. Left untouched here to stay inside the approved scope.

### Outside the `USA` object — flagged only, **no change proposed in this proposal**

- `data/countries.json` line 18029 — **ASM** (American Samoa) `sources[12].summary`: "…EO 14201 (sports; State Dept visa ban with SWS25 marking)." Same SWS25 mischaracterisation (case-note tag presented as a "visa ban … marking"), but it is not a `USA` field; flagged for a possible follow-up ticket.
- `data/consolidate_out/USA_*.rejected.json` (Connecticut, District of Columbia, Georgia, Kansas, Maine …) contain both overstatements in `summary`/`blindSummary`/`tangentialFactors`. These are **rejected consolidation drafts**, not rendered dossier content; flagged only — no change proposed.
- Archived rating logs / experiment outputs — **immutable history, explicitly no changes proposed**, per task instruction. They contain the same overstatement family in rating rationale text, e.g.:
  - `research/experiments/country-calibration-audit/usa-archived.json` rows 69/177/3496/3096/3354: "visa fraud bans", "visa flagging/permanent bans", "fraud bans stranding travellers", "tier-1 universal exposure", "state-imposed universal exposure — visa/document fraud flagging…", "activist bounties".
  - `research/experiments/country-calibration-audit/pilot-results.ndjson`: "state-imposed universal exposure — passport/visa fraud bans…", "state-imposed visa fraud bans on trans applicants…".
  - `research/experiments/country-calibration-audit/us39-claims.md` tables (rows 69, 167, 1075, 3496 …): "'universal traveller exposure': … fraud-based bans", "tier-1 universal exposures — facility bans, birth-sex custody, visa/document flagging".
  - These are records of what raters wrote at the time; rewriting them would falsify the audit trail. The only rendered-text fixes needed are (b) 1a–1c and 2a–2e.
- `tools/blind_pairwise.py` rubric text ("state-imposed universal exposure with no working remedy — facility exclusion…") is generic rating-rules language, not a claim about the US fraud bar; no change proposed.

---

## Constraints observed

- No repository file edited, created, or staged by this task (proposal written to `/tmp` only).
- No model calls; local file reads and grep only.
- Every number, date, name and documented risk outside the two overstatements is carried over unchanged
  (e.g. the May 2026 verbatim strategy quote, "four elements", "24 February 2025", "25 Feb 2025",
  "Pam Bondi", "December 2025", the permanent fraud bar itself).
- No methodology/meta language added to the dossier fields; the only structural addition is the primary
  text's own operative conditions.