# US dossier repair proposal — v2 (PROPOSAL ONLY, not applied)

Supersedes `research/experiments/country-calibration-audit/us-repair-proposal.md` (v1).
Scope: `data/countries.json` → `USA` object only. **No repository file has been edited, created or staged
by this task.** This document is written to `/tmp` and is a draft for reviewer/user approval.

Evidence base:
- `research/experiments/country-calibration-audit/us-primary-ocr.md` — primary text: 24 Feb 2025 State cable
  (OCR of image-only PDF, three agreeing tesseract passes), 4 Dec 2025 Bondi NSPM-7 memo (OCR + two
  independent text renditions agreeing character-for-character).
- `research/experiments/country-calibration-audit/us-claims-scope.md` — citation-chain verdicts; also holds
  the **verbatim May 2026 Counterterrorism Strategy quote** (§b2, direct primary source, whitehouse.gov PDF
  May 2026, pp. 4, 5, 7).
- `research/experiments/country-calibration-audit/terra-method-review.md` §1 — the concrete gaps corrected in
  this v2 (change log in §4 below).

**v2 changes vs v1, in one line each** (all five Terra corrections applied; see §4 for the per-item table):
1a now states the permanent/lifetime consequence of a fraud-ground finding explicitly (without claiming
automaticity); every SWS25 tag description (1a–1c) now carries the cable's own
**"pursuant to this Executive Order"** scope; 2d/2e now carry the full offense alternative
("…listed in section 2 of this guidance or other offenses against the United States"); the over-narrowing
"only as" phrasing in 2a–2c is replaced by an explicit description of **both** appearances of "radical
gender ideology"; the 2d/2e May 2026 strategy clause now conveys the primary text's actual scope; and
`sources[14].summary` / `sources[15].summary` are given as **two clearly-labelled variants (A and B)** —
no attribution convention is chosen here (§5).

---

## 1. Summary table

| # | Claim | Field (line) | Before (gist) | After (gist, v2) | Primary-text basis |
|---|---|---|---|---|---|
| 1a | Visa / fraud bar | `USA.summary` (402) | "flagging visa applicants with an internal marking and treating any applicant listing a gender other than assigned sex as grounds for a permanent ban on grounds of fraud" | SWS25 = case-note tag **pursuant to this Executive Order** on cases refused INA 221(g)/214(b)/212(a)(6)(C)(i) or pending an AO; discrepancy or reasonable doubt → INA 221(g) refusal + evidence request; suspected wilful material misrepresentation → possible INA 212(a)(6)(C)(i) finding, **stated as a permanent/lifetime exclusion**, on all four elements, **not automatic** | Cable ¶6, ¶7, ¶8 |
| 1b | Visa / fraud bar | `USA.blindSummary` (501) | same sentence, blind register | same narrowing + order qualifier + permanent/lifetime consequence, blind register (no State/INA names) | Cable ¶6, ¶7, ¶8 |
| 1c | Visa / fraud bar | `USA.sources[15].summary` (469) | "flagging visa applicants 'SWS25', and a permanent ban on applicants listing a gender other than assigned sex as 'fraud'" | **TWO VARIANTS (A / B), user must pick** — A: strict Wikipedia synopsis + citation-gap marker; B: attributed synthesis "Wikipedia asserts X; primary supports Y" (both include tag scope + four-element condition) | Cable ¶6, ¶7, ¶8; us-claims-scope "citation-support gap" |
| 2a | FBI cash bounties | `USA.summary` (402) | "cash bounties … identification and arrest of transgender activists … describing such activists as 'domestic terrorist groups'" | cash reward system for info leading to ID/arrest of **individuals in the leadership of** domestic terrorist organizations conspiring to commit the violations listed in §2 of the guidance **or other offenses against the United States**; "radical gender ideology" described by **both** of its memo appearances, never as a reward criterion | Memo p. 6 §8 (verbatim, double-sourced); p. 2 §1 |
| 2b | FBI cash bounties | `USA.blindSummary` (501) | same, blind register | same narrowing, both appearances, blind register | same |
| 2c | FBI cash bounties | `USA.sources[14].summary` (464) | same with "Attorney General Pam Bondi" | **TWO VARIANTS (A / B), user must pick** — A: strict Wikipedia synopsis + gap marker; B: attributed synthesis; both include the full offense alternative and both appearances | same |
| 2d | FBI cash bounties | `USA.localsOnly` (520) | "cash bounties … transgender activists … 'radical gender ideology'", trailing May 2026 clause short | same narrowing **+ full "or other offenses against the United States" alternative**; May 2026 clause rewritten to the strategy's actual scope (violent secular political groups; ideology triad; listed with anarchists/anti-fascists; disagreement disclaimer) | Memo p. 6 §8; us-claims-scope §b2 (verbatim May 2026 quotes) |
| 2e | FBI cash bounties | `USA.blindLocalsOnly` (521) | same, blind register | same narrowing, full offense alternative (blind register: "the country"), strategy scope clause, blind register | same |
| 3 | Memo date check | all USA fields | — | **no field says 5 Dec** → no change required (unchanged from v1 §d) | Memo p. 1: "December 4, 2025" |
| 4 | Repeat/adjacent overstatements | see §8 | — | listed only; archived rating logs are immutable history, no changes proposed | — |

Nothing else in the `USA` object (`outOfScopeNotes`, `blindOutOfScope`, `tangentialFactors`, `blindTangential`,
`comparisons`, `sources[16].summary`, `sources[17].summary`, `blindSourceSummaries` (12 entries, none matching),
`scoreProvenance`, `provisionalCalibration`, `rank`, `anchorRefs`) contains either claim.
Line numbers re-verified against the current file for this v2 (402, 464, 469, 501, 520, 521, and the
out-of-scope ASM occurrence at 18029).

---

## 2. Exact current occurrences (verbatim, field name and line)

File: `data/countries.json`, object `USA`. Quotes are rendered; in the raw JSON embedded double quotes
appear escaped as `\"`, exactly as in the file. Unchanged from v1 §2.

### Claim 1 — visa / automatic permanent fraud ban

**A1. `USA.summary` (line 402), paragraph starting "Entry screening carries its own exposure.":**
> "In February 2025 the State Department announced a ban on trans athletes entering the United States to compete in women's sports, flagging visa applicants with an internal marking and treating any applicant listing a gender other than assigned sex as grounds for a permanent ban on grounds of fraud."

**A2. `USA.blindSummary` (line 501), same paragraph position:**
> "In February 2025 the foreign ministry announced a ban on trans athletes entering the country to compete in women's sports, flagging visa applicants with an internal marking and treating any applicant listing a gender other than assigned sex as grounds for a permanent ban on grounds of fraud."

**A3. `USA.sources[15].summary` (line 469; source = `Executive Order 14201`, Wikipedia), the claim sentence (rest of field unchanged):**
> "Wikipedia: 5 Feb 2025 EO 'Keeping Men Out of Women's Sports'; State Department announced (25 Feb 2025) banning trans athletes from entering the US to compete in women's sports, flagging visa applicants 'SWS25', and a permanent ban on applicants listing a gender other than assigned sex as 'fraud'."

### Claim 2 — FBI cash bounties on "transgender activists … domestic terrorist groups"

**B1. `USA.summary` (line 402), paragraph "Official hostility extends to advocacy and speech.":**
> "In December 2025 the attorney general instructed the FBI to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," describing such activists as "domestic terrorist groups.""

(The following sentence — the May 2026 Counterterrorism Strategy quote — is verbatim-verified and **not**
part of the 2a replacement; in 2a/2b/2c the sentence following the replaced one is retained as-is.)

**B2. `USA.blindSummary` (line 501), same paragraph:**
> "In December 2025 the national justice department instructed a national law-enforcement agency to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what it called "radical gender ideology," describing such activists as "domestic terrorist groups.""

**B3. `USA.sources[14].summary` (line 464; source = `Persecution of transgender people under the second Trump administration`, Wikipedia; the field begins "Wikipedia survey: EO 14168 …" and continues after the quoted sentence with the ICE-custody abuse sentence — the claim sentence only is replaced):**
> "Persecution of transgender people under the second Trump administration (Wikipedia): In December 2025 Attorney General Pam Bondi instructed the FBI to begin offering cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," describing such activists as "domestic terrorist groups.""

**B4. `USA.localsOnly` (line 520), paragraph "Service access has narrowed:":**
> "In December 2025 the attorney general instructed the FBI to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," and the May 2026 counterterrorism strategy framed "radically pro-transgender" ideology as a security threat."

**B5. `USA.blindLocalsOnly` (line 521), same paragraph:**
> "In December 2025 the national justice department instructed a national law-enforcement agency to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what it called "radical gender ideology," and the May 2026 counterterrorism strategy framed "radically pro-transgender" ideology as a security threat."

---

## 3. Proposed replacements (before → after, v2)

All text is shown as **rendered text**. When applied to `data/countries.json`, every `"` inside a string
value must be written in JSON as `\"`, as the current sentences already are.

### 1a. `USA.summary` — claim 1

**BEFORE:**
> In February 2025 the State Department announced a ban on trans athletes entering the United States to compete in women's sports, flagging visa applicants with an internal marking and treating any applicant listing a gender other than assigned sex as grounds for a permanent ban on grounds of fraud.

**AFTER (v2):**
> In February 2025 the State Department announced a ban on trans athletes entering the United States to compete in women's sports, and its 24 February 2025 cable instructs posts to add the case-note tag "SWS25" to cases refused under INA 221(g), 214(b) or 212(a)(6)(C)(i), or pending an advisory opinion, pursuant to this Executive Order. A discrepancy in an applicant's documents or electronic records, or other evidence casting reasonable doubt on the applicant's sex, leads to a refusal under INA 221(g) with a request for additional evidence; where an applicant is suspected of wilfully misrepresenting sex or purpose of travel, the officer should consider whether the misrepresentation is material such that it supports an ineligibility finding under INA 212(a)(6)(C)(i) — the fraud ground, whose consequence is a permanent, lifetime exclusion from the United States — a finding that requires all four elements, so a gender-marker discrepancy never automatically produces that bar.

v1→v2 deltas: (i) tag scope now ends "pursuant to this Executive Order"; (ii) the permanent/lifetime
consequence of the fraud-ground finding is now stated explicitly (Terra: 1a lacked it while 1b/1c had it);
(iii) "never automatically" keeps the no-automaticity distinction intact.

### 1b. `USA.blindSummary` — claim 1 (blind register: no "State Department", no "INA", no proper institution names)

**BEFORE:**
> In February 2025 the foreign ministry announced a ban on trans athletes entering the country to compete in women's sports, flagging visa applicants with an internal marking and treating any applicant listing a gender other than assigned sex as grounds for a permanent ban on grounds of fraud.

**AFTER (v2):**
> In February 2025 the foreign ministry announced a ban on trans athletes entering the country to compete in women's sports, and its 24 February 2025 cable instructs posts to add the case-note tag "SWS25" to cases refused or pending an advisory opinion under the February 2025 executive order. A discrepancy in an applicant's documents or records, or other evidence casting reasonable doubt on the applicant's sex, leads to a refusal with a request for additional evidence; where an applicant is suspected of wilfully misrepresenting sex or purpose of travel, the adjudicating officer should consider whether the misrepresentation is material such that it supports a permanent, lifetime ineligibility finding under the immigration code's fraud ground, which requires all four elements and is never automatic.

v1→v2 delta: the order-specific qualifier is added (lowercase "executive order", matching the blind register
already used in `blindSummary`); permanent consequence and four elements kept from v1.

### 1c. `USA.sources[15].summary` — claim 1 — **TWO VARIANTS, user picks (see §5)**

**BEFORE (unchanged):**
> Wikipedia: 5 Feb 2025 EO 'Keeping Men Out of Women's Sports'; State Department announced (25 Feb 2025) banning trans athletes from entering the US to compete in women's sports, flagging visa applicants 'SWS25', and a permanent ban on applicants listing a gender other than assigned sex as 'fraud'.

**AFTER — VARIANT A (strict source synopsis + inline citation-support-gap marker):**
> Wikipedia: 5 Feb 2025 EO 'Keeping Men Out of Women's Sports'; State Department announced (25 Feb 2025) banning trans athletes from entering the US to compete in women's sports, flagging visa applicants 'SWS25', and a permanent ban on applicants listing a gender other than assigned sex as 'fraud'. [Citation-support gap: this permanent-ban assertion is broader than the reference Wikipedia cites for it; the underlying 24 Feb 2025 State cable supports a case-note tag on cases refused under INA 221(g), 214(b) or 212(a)(6)(C)(i), or pending an advisory opinion, pursuant to this Executive Order, and a permanent fraud bar under INA 212(a)(6)(C)(i) only where wilful, material misrepresentation is found on all four elements — no automaticity.]

**AFTER — VARIANT B (attributed synthesis: "Wikipedia asserts X; the underlying primary text supports Y"):**
> Wikipedia: 5 Feb 2025 EO 'Keeping Men Out of Women's Sports'; State Department announced (25 Feb 2025) banning trans athletes from entering the US to compete in women's sports. Wikipedia asserts that applicants listing a gender other than assigned sex are subject to a permanent ban 'on grounds of fraud' and that applicants were flagged 'SWS25'; this wording is broader than its cited reference. The underlying 24 Feb 2025 cable supports something narrower and conditional: the case-note tag 'SWS25' goes on cases refused under INA 221(g), 214(b) or 212(a)(6)(C)(i), or pending an advisory opinion, pursuant to this Executive Order; a document discrepancy or reasonable doubt about sex produces an INA 221(g) refusal with a request for evidence; and the permanent bar under INA 212(a)(6)(C)(i) requires suspected wilful, material misrepresentation found on all four elements — it is never automatic.

### 2a. `USA.summary` — claim 2

**BEFORE:**
> In December 2025 the attorney general instructed the FBI to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," describing such activists as "domestic terrorist groups."

**AFTER (v2, rendered):**
> In December 2025 the attorney general instructed the FBI to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 of the guidance or other offenses against the United States; the same memorandum uses the phrase "radical gender ideology" twice — once among the extreme viewpoints it says animate "certain Antifa-aligned extremists" "with a willingness to use violence against law-abiding citizenry," and once in a list of political and social agendas attributed to "violent extremist groups" more generally — and never as a criterion for the reward.

v1→v2 delta: the "only as one of the extreme viewpoints of 'certain Antifa-aligned extremists'" construction is
replaced by an explicit description of **both** memo appearances (us-primary-ocr Q8: occurrence 1 = Antifa-aligned
extremists' animating principle; occurrence 2 = the "listed below" list attributed to violent extremist groups
more generally), plus the flat statement that the phrase is never a reward criterion.

### 2b. `USA.blindSummary` — claim 2 (blind register: "national justice department", "a national law-enforcement agency", no "FBI", no "Antifa", "the country")

**BEFORE:**
> In December 2025 the national justice department instructed a national law-enforcement agency to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what it called "radical gender ideology," describing such activists as "domestic terrorist groups."

**AFTER (v2, rendered):**
> In December 2025 the national justice department instructed a national law-enforcement agency to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 of the guidance or other offenses against the country; the same memorandum uses the phrase "radical gender ideology" twice — once among the extreme viewpoints it says animate actors "with a willingness to use violence against law-abiding citizenry," and once in a list of political and social agendas attributed to violent extremist groups more generally — and never as a criterion for the reward.

(Blind register keeps the country out: "against the country" for "against the United States"; "Antifa" is
not used, so occurrence 1 is described by its violence-conditioned framing rather than the Antifa label.)

### 2c. `USA.sources[14].summary` — claim 2 — **TWO VARIANTS, user picks (see §5)** (names kept: "Attorney General Pam Bondi", "FBI"; replacement applies to the claim sentence only, rest of field unchanged)

**BEFORE (unchanged):**
> Persecution of transgender people under the second Trump administration (Wikipedia): In December 2025 Attorney General Pam Bondi instructed the FBI to begin offering cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," describing such activists as "domestic terrorist groups."

**AFTER — VARIANT A (strict source synopsis + inline attribution marker):**
> Persecution of transgender people under the second Trump administration (Wikipedia): In December 2025 Attorney General Pam Bondi instructed the FBI to begin offering cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," describing such activists as "domestic terrorist groups." [Attribution marker: this claim exceeds its cited reference and the underlying 4 December 2025 memorandum, which was read in full — the memorandum directs a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 of this guidance or other offenses against the United States, and never mentions trans activists; "radical gender ideology" appears only as a listed viewpoint.]

**AFTER — VARIANT B (attributed synthesis):**
> Persecution of transgender people under the second Trump administration (Wikipedia): Wikipedia asserts that in December 2025 Attorney General Pam Bondi instructed the FBI to begin offering cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," describing such activists as "domestic terrorist groups." The underlying 4 December 2025 memorandum supports something different: the FBI shall establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations of the provisions of law listed in section 2 of this guidance or other offenses against the United States; "transgender" appears nowhere in the memorandum, and "radical gender ideology" appears twice only as a listed viewpoint — once of "certain Antifa-aligned extremists" "with a willingness to use violence against law-abiding citizenry," and once in a list attributed to "violent extremist groups" — never as a reward criterion.

### 2d. `USA.localsOnly` — claim 2

**BEFORE:**
> In December 2025 the attorney general instructed the FBI to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what she called "radical gender ideology," and the May 2026 counterterrorism strategy framed "radically pro-transgender" ideology as a security threat.

**AFTER (v2, rendered):**
> In December 2025 the attorney general instructed the FBI to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire to commit the violations listed in section 2 of her guidance or other offenses against the United States, and the May 2026 counterterrorism strategy stated that national counterterrorism activities would "prioritize the rapid identification and neutralization of violent secular political groups whose ideology is anti-American, radically pro-transgender, and anarchist" — a category the same document lists alongside "Violent Left-Wing Extremists, including Anarchists and Anti-Fascists" — while stating that counterterrorism powers "will not be used to target our fellow Americans who simply disagree with us."

v1→v2 deltas: (i) the full offense alternative "or other offenses against the United States" added;
(ii) the formerly *unchanged* May 2026 clause is rewritten to the primary text's actual scope (Terra note):
targets = "violent secular political groups" with the ideology triad, listed with anarchists/anti-fascists,
with the document's own anti-targeting disclaimer retained. The three quoted fragments are verbatim from the
May 2026 whitehouse.gov strategy (us-claims-scope §b2: pp. 7, 5, 4). The sentence following in `summary`
(line 402) — which already carries the full verbatim strategy quote — is untouched.

### 2e. `USA.blindLocalsOnly` — claim 2

**BEFORE:**
> In December 2025 the national justice department instructed a national law-enforcement agency to offer cash bounties for information leading to the identification and arrest of transgender activists promoting what it called "radical gender ideology," and the May 2026 counterterrorism strategy framed "radically pro-transgender" ideology as a security threat.

**AFTER (v2, rendered):**
> In December 2025 the national justice department instructed a national law-enforcement agency to establish a cash reward system for information leading to the identification and arrest of individuals in the leadership of domestic terrorist organizations that conspire to commit the violations listed in section 2 of the guidance or other offenses against the country, and the May 2026 counterterrorism strategy stated that national counterterrorism activities would "prioritize the rapid identification and neutralization of violent secular political groups whose ideology is anti-American, radically pro-transgender, and anarchist" — a category the same document lists alongside violent left-wing extremists, including anarchists and anti-fascists — while stating that counterterrorism powers will not be used to target people who simply disagree with it.

(Blind register: "the country" for "the United States"; the taxonomy/disclaimer are paraphrased rather than
quoted because the verbatim wording names "Anti-Fascists" and "our fellow Americans"; the ideology triad
quote itself contains no country name and stays verbatim.)

---

## 4. Change log v1 → v2, per Terra review note item

File: all rows concern `data/countries.json` `USA` fields; **no change has been applied** — this is the
proposed delta only.

| Terra note (§1 of `terra-method-review.md`) | Fields affected | v1 wording | v2 wording | Where |
|---|---|---|---|---|
| "1a does not explicitly tell readers that a fraud-ground ineligibility finding can be permanent" | 1a | 1a ended at "…ineligibility finding under INA 212(a)(6)(C)(i), which requires all four elements" with no consequence stated | adds "— the fraud ground, whose consequence is a permanent, lifetime exclusion from the United States —" while retaining "requires all four elements … never automatically" (no-automaticity distinction kept) | §3 1a |
| "All three tag descriptions omit the order-specific qualifier" (tag instruction covers specified refused or AO-pending cases **pursuant to the executive order**, not all refusals) | 1a, 1b, 1c (both variants) | 1a: "cases refused under INA 221(g), 214(b) or 212(a)(6)(C)(i) or pending an advisory opinion"; 1b: "refused or pending cases"; 1c: "tagging refused or pending cases with case note 'SWS25'" — none said pursuant-to-order | 1a: "…, or pending an advisory opinion, pursuant to this Executive Order"; 1b: "…under the February 2025 executive order"; 1c A/B: "…, pursuant to this Executive Order" | §3 1a, 1b, 1c |
| "2d/2e omit the reward directive's 'or other offenses' alternative" | 2d, 2e | "…violations listed in section 2 of her guidance" / "…section 2 of the guidance" | "…listed in section 2 of her guidance **or other offenses against the United States**" (2d); "…listed in section 2 of the guidance **or other offenses against the country**" (2e, blind register) | §3 2d, 2e |
| "Their unchanged May 2026 clause does not convey that the primary strategy describes **violent secular political groups** with the listed ideology. The term is verbatim, but the shortened paraphrase needs a separate scope check." | 2d, 2e | "the May 2026 counterterrorism strategy framed 'radically pro-transgender' ideology as a security threat" | full-scope clause: priority against "violent secular political groups whose ideology is anti-American, radically pro-transgender, and anarchist", listed alongside anarchists/anti-fascists, plus the "simply disagree" disclaimer; all three quoted fragments verified against the verbatim primary quote | §3 2d, 2e; §9 |
| "'Only as' in 2a–2c risks making the memo's wording more exclusive than its two appearances support: one describes certain Antifa-aligned extremists; the other describes violent extremist groups more generally." | 2a, 2b, 2c (A and B) | "lists adherence to 'radical gender ideology' only as one of the extreme viewpoints of 'certain Antifa-aligned extremists' …" | "uses the phrase 'radical gender ideology' twice — once among the extreme viewpoints it says animate [Antifa-aligned extremists / violence-willing actors], and once in a list of political and social agendas attributed to violent extremist groups more generally — and never as a criterion for the reward" | §3 2a, 2b, 2c |
| Recommendation: source-faithful attribution convention for `sources[14]`/`[15]` — "needs a user-approved convention before editing"; do not silently rewrite a Wikipedia-only summary as the corrected primary account | 1c, 2c | one after-text each, presented as the Wikipedia field's content | **both variants labelled A (strict source synopsis + inline gap marker) and B (attributed synthesis)**; no convention chosen; pick list in §5 | §3 1c, 2c; §5 |
| Checklist 1: check each replacement against the primary passage — population, conditions, date, actor, legal mechanism, remedy, operative status; preserve general visa scope and real potential permanent consequence without claiming automaticity | all replacements | v1 §c rationale | v2 §9 validation table covers population / trigger / consequence / actor / date / operative status, and general-scope preservation (cable ¶¶6–7 are athlete-unlimited) | §9 |
| Checklist 2: correct tag scope; retain full offense alternative; verify May strategy clause and its violent-group qualifier | 1a–1c, 2d/2e | partially done in v1 | fully done in v2 (rows above) | §3 |
| Checklist 3: compare named and blind counterparts for factual equivalence and unintended identifying labels; check all affected live fields and citations, **including the now-outdated primary-document caveat**; do not rewrite immutable archived ratings | all + `outOfScopeNotes` | v1 §e noted the caveat | blind/named equivalence table added (§9); the `outOfScopeNotes`/`blindOutOfScope` single-encyclopedic-source caveat is again listed as now-satisfied-by-reviewer-decision and **left untouched** here; archived logs remain listed-only (§8) | §8, §9 |
| Checklist 4: independent review of rendered text and attribution, JSON/reference validation, verify no score or unrelated claim changed; review out-of-scope American Samoa occurrence separately | — | listed in v1 §e | unchanged and re-listed: reviewer steps pending, ASM occurrence (line 18029) flagged separately, no change proposed | §8 |
| "Memo date check" (v1 §d, retained) | all USA fields | no field dates the memo 5 Dec | unchanged: still no change proposed; correct value is 4 December 2025 | §7 |

---

## 5. `sources[14].summary` / `sources[15].summary` — the two variants and exactly what the user must pick

Terra's recommendation is to use a source-faithful attribution convention and explicitly says the schema's
intended meaning of a source `summary` (strict source synopsis vs attributed synthesis) "needs a
user-approved convention before editing". **No convention is chosen in this proposal.** Both variants are
given above so either can be applied without re-drafting:

- **Variant A — strict source synopsis + inline attribution marker.** The field states what the Wikipedia
  article actually asserts, verbatim in substance, followed by a bracketed marker noting that the assertion
  exceeds its cited reference (and, for `[14]`, that the underlying primary memo does not support it).
  Nothing Wikipedia "says" is rewritten; the gap is disclosed in-line.
- **Variant B — attributed synthesis.** The field explicitly separates the two layers: "Wikipedia asserts
  X" (kept as a reported claim) and "the underlying primary text supports Y" (the cable/memo account with
  tag scope, four-element condition, full offense alternative, both "radical gender ideology" appearances).
  This is a synthesis of secondary + primary inside the source field, labelled as such.

**Exactly what the user must pick between (the only decisions this proposal leaves open):**

1. **`USA.sources[15].summary` (line 469): Variant A or Variant B** — i.e. whether the rendered dossier
   shows Wikipedia's broad permanent-ban claim *with a citation-gap marker* (A), or a two-layer
   "Wikipedia asserts / primary supports" synthesis (B).
2. **`USA.sources[14].summary` (line 464): Variant A or Variant B** — i.e. whether the rendered dossier
   shows Wikipedia's "cash bounties on transgender activists / domestic terrorist groups" claim *with an
   attribution marker* (A), or a two-layer synthesis stating the memo's actual reward population and both
   "radical gender ideology" appearances (B).

(Independently per field → four combinations; A/A, A/B, B/A and B/B are all internally consistent.)

Consequences of the pick, stated so the choice is informed:
- **A** keeps the source field maximally faithful to the source but leaves the uncorrected overstatement
  visible in the rendered dossier, qualified only by the marker; the corrected mechanism then appears only in
  `summary` / `blindSummary` / `localsOnly` / `blindLocalsOnly`.
- **B** puts the correction into the source field (schema-interpretation choice: a source summary becomes a
  synthesis), so the corrected account is visible wherever source summaries are rendered, at the cost of the
  field no longer being a pure synopsis of that one article.
- Fields 1a, 1b, 2a, 2b, 2d, 2e are **not** affected by this pick and can be applied independently.

---

## 6. What survives verbatim, what is removed, what is added — and what is deliberately not softened

(Condensed from v1 §c; every fact, number, date and name carried over from v1 is unchanged in v2.)

**Survives verbatim (kept facts):**
- Claim 1: "In February 2025 the State Department announced a ban on trans athletes entering the United
  States to compete in women's sports" (blind equivalents in 1b); "25 Feb 2025"; "5 Feb 2025 EO 'Keeping
  Men Out of Women's Sports'" (1c); "trans athletes", "women's sports"; "24 February 2025 cable"; "four
  elements"; "24 February 2025" and the INA sections 221(g) / 214(b) / 212(a)(6)(C)(i); the case-note tag
  itself (`#sws25` / "SWS25").
- Claim 2: "In December 2025" (memo printed date 4 December 2025); "the attorney general instructed the
  FBI" (named fields) with blind equivalents; "Attorney General Pam Bondi" (2c); "she"/"her" pronouns
  (2a/2c/2d); "establish a cash reward system"; the quoted term "radical gender ideology" kept in every
  occurrence (re-scoped, never deleted); the May 2026 strategy's verbatim ideology quote (in `summary`'s
  following sentence — untouched; in 2d/2e the clause is now built from verbatim fragments of the same
  primary text).
- Memo date check result (v1 §d): no field anywhere says 5 Dec; 14 file-wide matches all unrelated.

**Removed and why (primary quotes):**
- "treating any applicant listing a gender other than assigned sex as grounds for a permanent ban on
  grounds of fraud" — cable ¶6 gives a **reversible 221(g) refusal + evidence request** for a bare
  discrepancy; ¶7 requires suspicion **plus** all four elements with officer judgement ("you should
  consider"); us-claims-scope verdict (a): automaticity not supported.
- "flagging visa applicants with an internal marking" / "flagging applicants 'SWS25'" — cable ¶8 attaches
  the tag to **cases** ("in all cases refused 221(g), 214(b), or (6)(C)(i) or pending an AO pursuant to
  this E.O."), not to applicants up front; "tag ≠ adverse finding" (us-primary-ocr §Q5). v2 adds the
  pursuant-to-order qualifier Terra required.
- "transgender activists" as the bounty population — memo p. 6 §8 targets "individuals in the leadership of
  domestic terrorist organizations …"; "transgender"/"trans"/"trans activists" appear **zero times** in the
  memo (§Q7).
- "promoting what she called 'radical gender ideology'" as selection criterion — the phrase appears twice
  and never as a bounty criterion (§Q8, both quoted verbatim in §3).
- "describing such activists as 'domestic terrorist groups'" — the memo describes **organizations**
  ("domestic terrorist organizations") with a criminal-conduct predicate (18 U.S.C. § 2331(5)) and an
  express First Amendment footnote (§Q9); us-claims-scope (b1): "overstates scope on both ends".
- "only as one of the extreme viewpoints of 'certain Antifa-aligned extremists'" — over-exclusive per Terra;
  replaced by the two-appearance description (v2 §3 2a–2c).
- 2d/2e's short "framed 'radically pro-transgender' ideology as a security threat" — the term is verbatim
  but the paraphrase understated the scope (violent secular political groups; listed with anarchists/
  anti-fascists; disclaimer); v2 clause is built from verbatim primary fragments.

**Added and why:**
- Permanent/lifetime consequence named in 1a (Terra): the risk was already in 1b/1c and is a property of the
  fraud ground itself; naming it does not add a new claim, it removes an under-statement.
- "pursuant to this Executive Order" in 1a/1b/1c — cable ¶8's own qualifier.
- Full offense alternative in 2d/2e — memo p. 6 §8's own alternative.
- Strategy-scope clause in 2d/2e — verbatim fragments of the May 2026 primary document plus its disclaimer.
- No "case-by-case" wording anywhere (us-primary-ocr §Q4: that is the State Department press line, not
  cable language). No automaticity claimed anywhere.

**Risks deliberately NOT softened:**
- The permanent/lifetime ineligibility consequence remains in **every** claim-1 replacement (1a, 1b and both
  1c variants): a trans traveller is still told that alleged misrepresentation of sex or purpose of travel
  can reach a lifetime bar. us-claims-scope (a): "the documented risk … is real and is not being downplayed
  here." What is removed is only *automaticity*, which the primary text does not support.
- Cash rewards for identifying/arresting organisation leaders remain stated as a real instruction
  ("shall establish"); the gender-ideology viewpoint remains quoted; us-primary-ocr §4c documents real
  NSPM-7 enforcement (June 2026 sentences/indictments; four antifa-aligned FTO designations) on the
  counterterrorism track.
- The chilling-effect concern is untouched: us-primary-ocr records the LA Times expert quotes ("this causes a
  chilling impact…") and the memo's First Amendment footnote; nothing in v2 claims the violence-conditioned
  framing prevents chilling of lawful advocacy (Terra §1: that framing "does not establish that
  implementation cannot chill lawful advocacy").
- The bounded-search caveats stand: no documented §212(a)(6)(C)(i) gender-marker permanent bar and no SWS25
  outcome data were found — absence of evidence from ~10 queries, "not proof that none occurred"; the cable
  evidence is OCR of a single image-only copy.

---

## 7. Memo date check (4 vs 5 December) — carried over from v1, unchanged, no change proposed

- Primary: memo letterhead reads **"December 4, 2025"** (us-primary-ocr §Q6, clean in every copy; Pink News
  "issued on 5 December" and LGBTQ Nation "dated December 5" are wrong or refer to circulation).
- Repository check (v1 §d): 14 matches file-wide for December-5 patterns, all unrelated; **no field — USA or
  any other country — dates the Bondi memo 5 December**; the USA fields say only "In December 2025", correct.
- **Result: no date error to fix.** (Day-level precision, if ever wanted, = 4 December 2025.)

---

## 8. Additional occurrences: listed only, no change proposed (carried over from v1 §e verbatim in substance)

**In `USA` fields (covered by the replacements above):** `USA.summary` (402), `USA.blindSummary` (501),
`USA.localsOnly` (520), `USA.blindLocalsOnly` (521), `USA.sources[14].summary` (464),
`USA.sources[15].summary` (469) — each contains exactly one occurrence of its claim (verified for v2).

**`USA.outOfScopeNotes` (403) / `USA.blindOutOfScope` (502)** — the "single encyclopedic source … not
independently corroborated here" caveat: not an overstatement, left untouched to stay in scope; noted because
the primary documents have now been read (memo OCR'd from three copies, cable from one), so the reviewer may
record the caveat as satisfied — Terra checklist item 3 explicitly flags this "now-outdated
primary-document caveat" as a live field to check.

**Outside the `USA` object — flagged only, no change proposed:**
- `data/countries.json` line **18029** — ASM (American Samoa) `sources[12].summary`: "…EO 14201 (sports;
  State Dept visa ban with SWS25 marking)" — same SWS25 mischaracterisation; not a `USA` field; Terra
  checklist 4 says review it **separately** → suggested as a follow-up ticket, out of this proposal's scope.
- `data/consolidate_out/USA_*.rejected.json` — rejected consolidation drafts with both overstatements;
  flagged only.
- Archived rating logs / experiment outputs (`usa-archived.json` rows 69/177/3496/3096/3354;
  `pilot-results.ndjson`; `us39-claims.md` tables) — **immutable history, explicitly no changes proposed**;
  rewriting them would falsify the audit trail (Terra checklist 3).
- `tools/blind_pairwise.py` rubric text — generic rating-rules language, not a US fraud-bar claim; no change.

---

## 9. Validation of the v2 wording against the primary quotes

Checks run for this proposal: direct reads of `us-primary-ocr.md` (cable ¶¶1–12 verbatim; memo Q6–Q9
verbatim), `us-claims-scope.md` §b2 (verbatim May 2026 strategy quotes, **direct primary source,
whitehouse.gov PDF May 2026, pp. 4, 5, 7**) and `terra-method-review.md` §1; line-number and
occurrence-count checks against `data/countries.json` (`sed`/`awk`/`grep` on lines 402, 464, 469, 501, 520,
521, 18029: one occurrence of each claim per field; all six v1 field line numbers re-confirmed).

**File-location correction (honest note):** the task said to verify the May 2026 paraphrase against the
verbatim quote "in `us-primary-ocr.md`". `us-primary-ocr.md` contains **no** May 2026 strategy quote — its
§4 is a *post*-May-2026 enforcement search. The verbatim strategy quote lives in
`us-claims-scope.md` §b2, marked [direct, primary source]. The v2 2d/2e clause was therefore validated
against that verbatim quote (plus the strategy's taxonomy line and disclaimer, same section), which is the
stronger evidence anyway (fetched primary PDF, not a paraphrase).

### 9.1 Per-dimension validation table

| Dimension | Claim / replacement | v2 wording | Primary quote | Verdict |
|---|---|---|---|---|
| **Population** (claim 1) | 1a, 1b, 1c A/B | general: "an applicant's … sex", no athlete limit | cable ¶6 "both immigrant and nonimmigrant visa applications … all visas must reflect an applicant's sex at birth"; ¶7 no athlete limitation; scope verdict: ¶¶6–7 "written generally, for all visa applicants" | **Match** — general visa scope preserved (Terra checklist 1: "Preserve the general visa scope"); cable's *opening frames* are E.O. 14201/sports, which 1a keeps in its first clause |
| **Population** (claim 2) | 2a, 2b, 2c A/B, 2d, 2e | "individuals in the leadership of domestic terrorist organizations that conspire with others to commit violations …" | memo p. 6 §8 verbatim (double-sourced); "transgender" = 0 hits in the memo | **Match** — "transgender activists" removed everywhere; no person-category target added |
| **Trigger** (claim 1) | 1a, 1b, 1c A/B | discrepancy or reasonable doubt → 221(g) refusal + evidence request; suspected wilful misrepresentation + materiality + all four elements → possible 212(a)(6)(C)(i) finding; never automatic | ¶6 verbatim; ¶7 verbatim + four enumerated elements incl. "(3) The fact misrepresented is material"; §Q2/Q4 verdicts: no automaticity, no "case-by-case" attribution | **Match** — trigger split preserved; "never automatically" added in 1a/1b, "never automatic" in 1c both variants |
| **Trigger** (tag) | 1a, 1b, 1c A/B | tag on cases refused under INA 221(g), 214(b) or 212(a)(6)(C)(i), **or pending an advisory opinion, pursuant to this Executive Order** | ¶8 verbatim: "in all cases refused 221(g), 214(b), or (6)(C)(i) or pending an AO pursuant to this E.O.: #sws25"; Terra: "not all refused or pending cases" generally | **Match** — order-specific qualifier present in all three; blind 1b renders it as "under the February 2025 executive order" |
| **Trigger** (claim 2) | 2a, 2b, 2c A/B, 2d, 2e | reward for info leading to ID/arrest of org leadership; phrase never a criterion | §8 "shall establish a cash reward system for information that leads to the successful identification and arrest of …"; Q8: phrase never a criterion | **Match** |
| **Consequence** (claim 1) | 1a (new in v2), 1b, 1c A/B | "permanent, lifetime exclusion from the United States" / "permanent, lifetime ineligibility finding" / "permanent fraud bar under INA 212(a)(6)(C)(i)" | cable ¶7 "ineligibility finding under INA section 212(a)(6)(C)(i)" — the statute's fraud ground is the permanent bar the dossier claim was about; us-claims-scope (a): "the documented risk … is real"; us-primary-ocr §5: permanent bar requires suspicion + all four elements | **Match, no softening** — consequence now explicit in 1a as well; the 221(g) refusal step is correctly presented as the *reversible* precursor, not the bar; automaticity still denied |
| **Consequence** (claim 2) | 2a–2e | cash reward system established; no claim of any posted/paid reward | §Q7: "prospective/administrative … no reward amount, no named target, no posted bounty"; us-claims-scope b1: "no enforcement evidence" | **Match** — "establish a cash reward system" is prospective; no enforcement outcome claimed |
| **Actor** | 1a/1b (State cable); 2a–2e (AG→FBI); 2d/2e (strategy) | "the State Department … its 24 February 2025 cable" / blind "the foreign ministry … its cable"; "the attorney general instructed the FBI" / blind "the national justice department instructed a national law-enforcement agency"; "the May 2026 counterterrorism strategy" (named fields keep the quote's "national counterterrorism activities") | cable header "From: SECSTATE WASHDC", "Action: ALL DIPLOMATIC AND CONSULAR POSTS"; memo "FROM: THE ATTORNEY GENERAL" / "the FBI shall establish"; strategy = White House document | **Match** — blind register carries no proper institution or country names (no "State Department", "INA", "FBI", "Antifa", "United States", "Americans") |
| **Date** | all | "24 February 2025" cable; "February 2025" / "25 Feb 2025" announcement; "5 Feb 2025 EO"; "In December 2025" memo (printed 4 Dec 2025); "May 2026" strategy | cable header "Date/DTG: Feb 24, 2025"; EO 14201 of 5 Feb 2025; press announcement 25 Feb 2025; memo "December 4, 2025"; strategy May 2026 | **Match** — every date carried verbatim from v1; no 5 Dec introduced; §7 unchanged |
| **Operative status** | 1a–1c | cable instructs posts; refusal/consideration language | ¶1 "All visa-issuing posts should carefully review and follow this guidance effective immediately"; ¶7 "you should consider" | **Match** — instruction/consideration verbs, no "shall/must" invented, no outcome asserted |
| **Operative status** | 2a–2e | "establish a cash reward system" | §8 "shall establish" — prospective/administrative | **Match** — directive stated, not an implemented bounty |
| **Operative status** | 2d/2e strategy clause | "stated that national counterterrorism activities would 'prioritize …'" + disclaimer | strategy p. 7 "our national CT activities will also prioritize the rapid identification and neutralization of violent secular political groups whose ideology is anti-American, radically pro-transgender, and anarchist"; p. 5 taxonomy; p. 4 "Our counterterrorism powers will not be used to target our fellow Americans who simply disagree with us." | **Match** — paraphrase conveys scope (violent secular political groups; ideology triad; listed with anarchists/anti-fascists; disclaimer), quotes verbatim in 2d; scope claim "listed alongside" rests on p. 5 taxonomy line quoted in us-claims-scope §b2 |

### 9.2 Named vs blind equivalence (Terra checklist 3)

| Fact | Named (1a/2a/2d) | Blind (1b/2b/2e) | Equivalent? |
|---|---|---|---|
| Cable adds SWS25 tag, order-qualified | yes, "INA 221(g), 214(b) or 212(a)(6)(C)(i) … pursuant to this Executive Order" | yes, "refused or pending an advisory opinion under the February 2025 executive order" (ground numbers omitted — blind register has no INA) | yes |
| Permanent/lifetime consequence, four elements, no automaticity | yes | yes ("permanent, lifetime ineligibility finding under the immigration code's fraud ground") | yes |
| Reward population + full offense alternative | "…section 2 of the guidance or other offenses against the United States" / "her guidance" (2d) | "…section 2 of the guidance or other offenses against the country" | yes (only the register noun differs, per the established blind convention) |
| Both "radical gender ideology" appearances | occurrence 1 named ("certain Antifa-aligned extremists") | occurrence 1 described by its violence framing, Antifa label omitted | yes in substance; **register note**: the blind text cannot name Antifa, so occurrence 1 is identified by framing rather than label |
| Strategy scope + disclaimer | verbatim quotes incl. "Anti-Fascists", "our fellow Americans" | ideology quote verbatim; taxonomy/disclaimer paraphrased (they name the country population) | yes in substance |

### 9.3 What was checked and what remains for the reviewer

Checked here: wording vs primary quotes on all six dimensions (9.1), named/blind equivalence (9.2),
line numbers and one-occurrence-per-field counts, verbatim carry-over of v1's facts/numbers/dates/names
(§6), and that no repository file was written.
Remaining (reviewer steps, Terra checklist 4): independent read of the rendered before/after text; JSON
validation and reference checks after any approved application; confirmation that no score or unrelated
claim changed; separate review of the ASM occurrence; the user's A/B pick for §5.

---

## 10. Constraints observed

- **No repository file edited, created or staged by this task** (this proposal is written to `/tmp` only);
  no commits. Note for the record: `git status` shows pre-existing unstaged modifications
  (`data/measurement_manifest.json`, `research/experiments/2026-11-13-npl-gbr-battery/*`,
  `tools/build_manifest.py`) and an untracked `research/experiments/country-calibration-audit/` — none of
  them touched by this task, and **no staged files**.
- No model calls; local file reads and grep only.
- Every number, date, name and documented risk outside the two overstatements is carried over unchanged
  ("four elements", "24 February 2025", "25 Feb 2025", "5 Feb 2025", "Pam Bondi", "December 2025",
  "May 2026", "December 4, 2025", line numbers, the 14 file-wide date matches, 12 blind source summaries,
  three tesseract passes, June 2026 enforcement dates).
- Documented risks not softened (§6); no methodology/meta language added to the dossier fields — the only
  structural additions are the primary text's own operative conditions and, for the two source fields, the
  user-pending attribution variants.
- The only open decision is the §5 A/B pick for `sources[14].summary` and `sources[15].summary`.