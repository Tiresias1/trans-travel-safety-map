## Review

**Merge verdict: BLOCK application of the proposal as written.** The central corrections are sound, but the exact tag, blind text, source-field presentation and operative-status wording need adjustment first.

### Passage-by-passage assessment

- **1a, 1b and 1c — visa:** The general applicant scope, distinction between a 221(g) refusal and a fraud finding, four required elements and non-automatic permanent consequence are supported by `us-primary-ocr.md` §§2 Q1–Q3. They preserve the documented risk. However, all three misstate the literal case-note tag and present an instruction as an unconditional outcome; see findings below.
- **2a, 2b and 2c — reward:** The leadership population, conspiracy/offense qualifiers, directive to establish a system, and two violence-framed uses of “radical gender ideology” match `us-primary-ocr.md` §§3 Q7–Q8. They do not assert that a bounty was posted or that transgender advocacy itself was a reward criterion. The source-field presentation in 2c needs correction.
- **2d and 2e — reward and strategy:** The reward population and the strategy’s violence-linked, conjunctive description are supported by `us-primary-ocr.md` §3 Q7 and `us-claims-scope.md` §b2. The named passage preserves the strategy’s disclaimer without erasing its stated risk. The blind passage needs anonymisation.

### Findings and smallest fixes

1. **P1 — Literal case-note tag is wrong.** `us-repair-final.md` §§1a–1c and C1/C3/C5 call it `"SWS25"`. The cable instructs posts to enter **`#sws25`**, exactly, with no additional punctuation or spaces (`us-primary-ocr.md` §2 Q5). Use `#sws25` in all three passages, or describe it without purporting to quote its literal spelling.

2. **P1 — Blind passage identifies the country.** `us-repair-final.md` §2e/C8 quotes “anti-American” verbatim. That names the jurisdiction in a newly proposed blind passage, contrary to the blinding rules against jurisdiction names and identifying verbatim quotations (`tools/blind_fields.md` rules 1 and 13). Paraphrase it as “hostile to the country,” preserving the violence qualifier and all three conjunctive ideological characteristics. The existing blind summary also contains this identifying quotation, but it is not newly introduced by this proposal; record it separately.

3. **P1 — Source summaries retain attribution scaffolding and can misattribute the corrected account.** §1c/C5 begins “Wikipedia:” and §2c/C6 retains “(Wikipedia):”, although the replacements incorporate primary-cable and memorandum detail. Source summaries are visible in the popup (`js/app.js:236–243`). Under the binding convention, remove those prefixes from the replacement prose; the source entry’s existing URL identifies the linked source. Keep the discrepancy in backend provenance, not in the visible text. **Judgement:** the remaining Wikipedia link should not be represented as independently verifying every newly inserted primary detail; ensure provenance for the primary documents is retained somewhere genuinely backend-only.

4. **P1 — Visa wording asserts the instructed step as an outcome.** §§1a–1c say a discrepancy or doubt “leads to a refusal”; the cable says officers **“should refuse”** and request evidence (`us-primary-ocr.md` §2 Q2). The proposal’s §4.1 says no outcome is asserted, but its present-tense wording can imply actual or current enforcement. Say the cable **instructs officers to refuse** under 221(g) and request evidence. Retain the separately stated permanent fraud-ground risk and four-element test.

5. **P2 — The confirmation overstates what is unchanged.** §5 says no dates or numbers were introduced, including that “no day-level date was added.” The old passages lack the newly inserted **24 February 2025**, statutory numbers and “four elements” (§§1a–1c). These additions are evidence-supported; correct the confirmation rather than removing them. Its claim that both quoted ideology terms remain “in every occurrence” is also not literal: the reward-only passages and visa passages do not all contain both.

### Equivalence, provenance and application gate

The named/blind **substance** is otherwise close: the blind visa passage retains the permanent consequence and four elements, and the blind reward passages preserve the leadership and offense qualifiers. Fix the C8 identity leak above. The proposal’s §3 is explicitly marked backend-only and is not included in C1–C8; that separation is sound **if application copies only the replacement strings and does not publish the provenance block**.

Do not rely solely on the stated uniqueness counts. Immediately before applying:

1. Parse the current JSON; verify the country key, both source URLs and all eight target field paths.
2. For each field, decode the old fragment and assert **exactly one** occurrence in that field; abort the whole operation on any mismatch. Check revised §1 AFTER text against revised §2 replacements, including JSON escaping.
3. Apply only those replacements, reparse, and compare parsed before/after objects: only the six intended field values may change, with no scores, other fields or countries changed. Inspect the rendered named/source text and blind bundles.
4. Review the existing visible `outOfScopeNotes` and blind counterpart separately: they currently say the reward and strategy claims have not been independently corroborated and that primary documents should be checked (`data/countries.json:403,502`). They were outside the eight-replacement scope, but may become confusing alongside this primary-verified rewrite. Resolve that scope explicitly rather than silently changing them.

### Residual uncertainty

The cable evidence is OCR from one image-only copy, albeit with agreeing passes; the memo is corroborated by independent text renditions (`us-primary-ocr.md` §§0, 6). The bounded search found no documented gender-marker fraud-bar outcome or SWS25 outcome data; absence of results is not proof of absence. It also did not establish a posted or paid reward. A fraud-ground finding carries a permanent risk, but limited waiver possibilities exist (`us-claims-scope.md` claim (a)); avoid implying that relief is impossible. The source documents establish the directives and strategy text, not their present-day implementation or legal status.

No edits or model calls were made. Automated uniqueness, JSON round-trip and rendered-output checks were **not run** in this read-only review.