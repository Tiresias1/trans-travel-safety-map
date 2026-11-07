# Independent methodological review

This is a read-only review of the supplied audit artifacts. I made no model calls or edits. The recommendations are for small, reviewed shadow pilots; they do not authorize score changes or rollout. Published country and ADM1 scores remain frozen, including the user-approved USA score of 0.330. Neither 0.330 nor 0.264 is a target for method selection.

## 1. Evidence repair

### Supported by evidence

- The proposed direction is **substantially supported, but the exact replacements need revision before application**. The State cable’s sex-at-birth and fraud provisions are written generally, not only for athletes. A document discrepancy or reasonable doubt leads to a 221(g) refusal and evidence request; suspected misrepresentation calls for consideration of materiality and the four elements of the fraud ground. The cable does not say that a mismatch automatically produces a permanent bar. Its tag instruction covers specified refused or advisory-opinion-pending cases **pursuant to the executive order**, not all refused or pending cases. The cable evidence is OCR of one image-only copy; the bounded search found no enforcement outcome, which is not proof that none occurred. [`us-primary-ocr.md` §§2, 4, 6]
- The memo directs a prospective reward system for information leading to identification and arrest of leaders of domestic terrorist organizations that conspire to commit specified violations **or other offenses against the United States**. It does not name trans activists as such. Its undefined “radical gender ideology” language appears within violence-related framing; that framing does not establish that implementation cannot chill lawful advocacy. The memo evidence is corroborated across the scan and text renditions. [`us-primary-ocr.md` §3; `us-claims-scope.md` §b]
- The proposal’s exact text has material loose ends:
  - 1a does not explicitly tell readers that a fraud-ground ineligibility finding can be permanent; 1b and 1c do. All three tag descriptions omit the order-specific qualifier.
  - 2d/2e omit the reward directive’s “or other offenses” alternative. Their unchanged May 2026 clause does not convey that the primary strategy describes **violent secular political groups** with the listed ideology. The term is verbatim, but the shortened paraphrase needs a separate scope check. [`us-repair-proposal.md` §b; `us-claims-scope.md` §b2]
  - “Only as” in 2a–2c risks making the memo’s wording more exclusive than its two appearances support: one describes certain Antifa-aligned extremists; the other describes violent extremist groups more generally. [`us-primary-ocr.md` §3, Q8]

### Recommendation

Use a **source-faithful attribution convention** for `USA.sources[14].summary` and `[15].summary`: distinguish what Wikipedia actually asserts from what the underlying primary document supports. Do not silently rewrite a Wikipedia-only summary as though the corrected primary account were Wikipedia’s claim. Either explicitly attribute the disputed secondary claim and its correction, or add/reference the primary source and label the field as a synthesis of both, consistent with the schema. Preserve the secondary source’s claim where it is being reported *as a claim*, not as established fact.

Before applying any approved repair:

1. Check each replacement against the relevant primary passage, including population, conditions, date, actor, legal mechanism, remedy and operative status. Preserve the general visa scope and the real potential permanent consequence without claiming automaticity.
2. Correct the tag’s **pursuant-to-this-order** scope; retain the reward directive’s full offense alternative; separately verify the May strategy clause and its violent-group qualifier.
3. Compare named and blind counterparts for factual equivalence and unintended identifying labels. Check all affected live fields and citations, including the now-outdated primary-document caveat; do not rewrite immutable archived ratings.
4. Independently review the rendered before/after text and source attribution, validate JSON and references, and verify that no score or unrelated claim changed. Numeric-token checks alone are insufficient. Review any related out-of-scope occurrence, such as the flagged American Samoa source summary, separately. [`us-repair-proposal.md` §§b, e; `HANDOFF.md`]

### Uncertain / needs decision by the user

- The schema’s intended meaning for a source `summary`—strict source synopsis versus attributed synthesis—needs a user-approved convention before editing. A current primary source, enforcement case, later guidance or authoritative correction could change the wording; none should be inferred from the bounded search.
- No application is recommended until the revised text and source handling pass substantive review.

## 2. Rating-language pattern

### Supported by evidence

`us39-claims.md` reports 143 interpretively classified US-side units: 57 conditional and 50 unclear-scope. Nineteen rows use “universal” or “nationwide”; all 19 also contain at least one unit classified conditional. Eight rows contain a US-side mitigating clause. Rows 12, 522, 542, 686 and 3496 use materially different court/remedy language; the report also records varying visa and facility severity language. These are **classification and wording observations**, not source validation. “Nationwide,” a national rule, and “every visitor suffers the consequence” are not interchangeable; a risk may be geographically nationwide yet triggered for an individual. Different court statements may concern different measures, jurisdictions or dates rather than necessarily contradicting one another. [`us39-claims.md` §§5–9]

The pattern raises a credible concern about the **interpretability and consistency** of those encounter rationales. It does not establish a directional score bias, the correct US score, or that every encounter is unreliable. Brief rationales may omit considerations that affected a rating; the archive alone does not show their full causal influence.

### Recommendation

Test competing explanations, retaining contrary examples:

- **Instruction/rubric:** inspect the exact historical and current prompts for whether they distinguish scope, trigger, legal status and mitigation. In a controlled shadow contrast, hold dossier, model and pair fixed and compare the existing prompt with a reviewed instruction requesting those facts *per exposure*, not a new severity scale.
- **Model/draw behavior:** repeat identical requests in both orders. If wording and scores vary within a fixed cell, the pattern cannot be attributed solely to the partner or dossier. Record model/version and settings.
- **Dossier effects:** compare the frozen original with a separately reviewed repaired dossier, changing only the identified evidence passages. Trace whether those specific claims persist or change in rationales; do not assume a score change is caused by a single sentence when several fields change together.
- **Partner context:** compare the same target across repeated, counterbalanced partners while holding the target dossier fixed. Examine whether emphasis changes with the comparator’s actual exposure profile, and whether target factual claims remain accurate.
- **Courts:** source-check each cited measure by instrument, jurisdiction, date, order and status before calling claims contradictory. A court can block one measure while another remains enforceable.

### Uncertain / needs decision by the user

A replicated pattern under fixed inputs, with source-inaccurate claims persisting after repair, would strengthen concern about model/instruction behavior; disappearance after a narrowly isolated evidence repair would strengthen the dossier explanation. Neither establishes numerical accuracy without independent validation. The user should review any proposed prompt change before it is tested; no change is authorized for production.

## 3. Country-comparison pilot

### Supported by evidence

The existing bounded pilot used current production-style prompts, not an exact archived replay. It made one call per order; USA–PRY yielded 0.35 versus 0.13 for the USA in opposite orders, so order and draw variation are confounded. One of 18 calls failed. The archive’s USA range of 0.10–0.48 covers 36 partners and likewise does not isolate causes. [`HANDOFF.md`, “Country audit” and “Pilot”]

PRY and FSM were selected *before* the pilot as archived shared partners: PRY for USA/NPL and FSM for USA/GBR. They are purposive, not representative. [`pilot.py`]

### Recommendation

Pre-register and seek review of the following **non-publishing** pilot; freeze the dossiers, prompt version, endpoint definition, model settings and analysis plan before calls.

1. **Pair matrix:** USA, GBR and NPL against PRY and FSM, plus the three direct target–target pairs: nine pairs. Run **four independent draws per order**, randomized in balanced blocks: 72 calls. Repeats estimate within-cell variation; both orders estimate presentation effects within a pair. Analyze each country in each pair, not merely pooled averages.
2. **Isolated-country controls:** four independent single-dossier assessments each for USA, GBR and NPL: 12 calls. Use the same evidence and scoring task without a comparator. This is a different prompt condition, so a pair-versus-isolated difference is diagnostic of the combined condition, not proof of partner causation alone.
3. **Matched-exposure controls:** for each target, pair two identical copies of its frozen blinded dossier, reversing A/B formatting and taking two draws per orientation: 12 calls. These test position/label and self-comparison instability, not real-country accuracy. Do not present synthetic copies as independent evidence.
4. **Optional evidence contrast:** only after repair review, use two preselected USA pairs, original versus repaired USA dossier, both orders and two draws per cell: 16 additional calls. Change no other inputs. Keep this analysis separate from the baseline matrix.

The core is **96 calls**, with a hard ceiling of **112** if the optional contrast is approved. Before launch, obtain an approved monetary cap and hard aggregate ceilings of **2 million input and 0.8 million output tokens**, including retries; stop rather than silently exceed them. The previous 17 successful calls already consumed at least 228,589 input and 70,267 output tokens, so actual cost should be checked after the first balanced block. [`HANDOFF.md`]

For every attempted call retain exact prompt and dossier snapshots or immutable references plus hashes, orientation, randomization block, model/API settings, timestamp, raw response, parsed scores and rationale, usage, failures and retry linkage. Blind reviewers to condition where practical. Retain failed and unparseable outputs; predefine at most one retry per failed cell within the cap, report both attempts and missingness, and stop for review if failures cluster by condition or prevent balanced comparison.

Report distributions and paired order contrasts by pair; compare partner contrasts against observed within-cell variation, and examine rationale-level scope and mitigation. A repeated same-direction order contrast larger than typical within-cell variation is a diagnostic warning, not a calibrated effect estimate. Stable partner differences across orders alongside low within-cell variation support partner-context sensitivity; high within-cell variation limits both conclusions. Identical-copy asymmetry flags label/order sensitivity. Review after the first balanced block and after completion; stop for material prompt/input drift, budget exhaustion, clustered failures, or evidence-scope errors. No pilot result directly changes a published score.

### Uncertain / needs decision by the user

Four draws per cell are a feasibility choice, not a power guarantee. The user must approve budget, sample and any evidence/prompt contrast. A small purposive pilot cannot generalize to all countries or validate an absolute score; a broader reviewed design may be needed if results are ambiguous. No threshold should be chosen to reproduce either existing US number.

## 4. ADM1 construction

### Supported by evidence

The production anchored lane supplied partial blinded national text and division text, compared them with four foreign country anchors, and computed each estimate from an anchor score plus a paired rating difference. It did **not** supply or start from the parent’s numeric score. National out-of-scope text was omitted and source summaries were capped at eight. The archived production results lack per-anchor judgments and prompt text; the trace reconstructs inputs from code and data versions rather than observing every request. A superseded in-country lane did show a national number, but was not the production basis for the traced divisions. [`adm1-trace.md` §§2–6]

### Recommendation

Evaluate a **shadow-only national-baseline interface**:

1. Supply the full national comparison dossier, including its exclusions and source summaries, and the frozen published national numeric level. Supply a separate local evidence bundle. State explicitly that the national level is an input to hold fixed, not a number to re-rate.
2. Ask for a documented **local difference relative to that national comparison**, with each proposed departure linked to local evidence, applicability, uncertainty and whether the national dossier already includes the fact. Include inherited national exposure without treating its repetition as a new local effect. A region-specific implementation may still warrant a departure if its difference from the national comparison is documented; mere duplication does not.
3. Evaluate an externally computed additive candidate, `shadow division = frozen national level + assessed local difference`, alongside a separately reviewed bounded alternative **only if** its semantics preserve the same national starting level and local-departure interpretation. Do not assume additivity is intrinsically correct on an intermediate-undefined scale. Log raw and bounded results and boundary handling; never silently clamp away a problem. No foreign anchor ladder or ADM1 aggregate may alter the national level.
4. Use California, Texas, England and Bagmati as initial cases, with repeated assessments and both evidence-rich and thin-evidence cases. Add a no-new-local-evidence control and an evidence-duplication control. Test national number shown versus withheld *as a diagnostic contrast*, not as the proposed production interface; test anonymized versus identifying labels where feasible. Hold the parent dossier and numeric baseline fixed in the primary condition.
5. Review for unintended national re-rating, label/identity effects, double-counting, inherited-risk omission, thin-evidence drift, inconsistent local applicability, numerical boundary effects and changes caused by dossier truncation. A zero-difference control is a diagnostic expectation to investigate, not a rule that missing evidence proves equality.

Across jurisdictions, report distributions of documented departures, uncertainty, evidence coverage, repeat variation, boundary hits and national-to-ADM1 spread, alongside case-level explanations. Compare like-for-like exposure profiles where evidence permits. A spread or mean gap is an **investigation signal**, never a target to recenter, force agreement or feed back into the country score. Preserve potentially genuine differences.

### Uncertain / needs decision by the user

The user must approve the exact interface, treatment of incomplete local evidence, bounded alternative and shadow sample before calls. The full national level may already summarize uneven regional facts without quantifying their contribution; preventing double-counting therefore requires case-by-case evidence review, not mechanical subtraction. A successful pilot would establish feasibility and reveal failure modes, not establish that any current ADM1 or national value is correct.

## Review verdict

**OK with notes** for the diagnostic direction; **do not apply the exact repair text or roll out a scoring method yet**. The main residual risks are source-field attribution, the specific wording gaps above, limited causal identification from small model pilots, and incomplete archived production requests.