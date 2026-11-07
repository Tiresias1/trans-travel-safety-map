## Review

**Recommendation:** separate country measurement, national-to-ADM1 construction, and cross-jurisdiction validation into bounded diagnostic lanes. Freeze published scores during diagnosis, including the user-approved US **0.33**. Do not choose a method by whether it reproduces that value—or 0.264.

### Correct: evidence and constraints worth preserving

- Countries must remain independently assessed. Regional restrictions/protections may inform their evidence dossiers through a reviewed general method, but ADM1 scores must never become country inputs.
- The production ADM1 mismatch is concrete: `tools/anchored_calibrate.py:124–165` supplies national prose, compares the combined division dossier against foreign anchors, and averages `anchor score + (division rating − anchor rating)`. It does **not** start from the independently assessed parent score.
- National evidence is also asymmetrical: `tools/blind_pairwise.py:911–928` omits the parent’s out-of-scope field and limits source summaries to eight, whereas country `dossier()` includes those fields and all source summaries (`:699–736`).
- The prior US reviews are substantive contrary evidence to treating 0.264 as settled: three single assessments recommended higher scores and one lower. Their shared dossier, visible identities and existing scores limit independence, not relevance. `research/experiments/country-calibration-audit/prior-us-reviews.md`, §§1–3, documents both the recommendations and the dissent. Claude’s 0.30–0.35 suggestion is not a confidence interval; the later target-directed Sol consultation is not independent confirmation.

## Prioritized development handoff

### 1. Freeze and reconstruct before experimenting

Preserve scores and archive durable copies of the original review prompts, outputs, and historical dossier/rubric versions. Treat the historical reconstruction in `adm1-trace.md` as documented evidence, not as a newly reproduced run.

For each pilot, retain exact rendered requests, responses, orientation, model/settings, input hashes, evidence dates, usage, failures, and derivation. Current anchored code drops exceptions silently (`tools/anchored_calibrate.py:153–156`); its newer per-anchor checkpoint fields still do not preserve complete requests or failure evidence.

Maintain separate developer-facing provenance for the approved US override and archived encounter mean. HANDOFF reports a verification failure for their difference; do not relabel that difference as successful reproduction or silently overwrite the override.

### 2. Diagnose country-comparison bias with controlled contrasts

Begin with claim-level inspection of archived US encounters, including A/B orientation, before purchasing further calls. Classify discrepancies as possible evidence scope, dossier omission, interpretation, comparator dependence, order, or random variation—not one presumed root cause.

Resolve or explicitly mark material scope uncertainties, particularly the broad visa-fraud claim identified in `HANDOFF.md`. Separate national/local authority, visitors/residents, and conditional/unconditional exposure. Neither automatically soften nor amplify unresolved evidence.

**Suggested bounded pilot, subject to budget approval:**

- Retain USA–PRY as a sensitivity case; USA–GBR and GBR–NPL as direct contrasts.
- Include a comparator selected by a documented evidence-coverage/structural criterion, rather than its desired ranking.
- Repeat both presentation orders for each chosen pair; one call per order cannot separate order from draw variation.
- Use identical dossiers, rubric and model settings throughout the initial block.
- Add isolated country assessments on a small shared subset to test dependence on pairing.
- Only subsequently test one changed factor at a time: identity visibility, existing-score visibility, or a reviewed dossier correction. Do not combine all three.

Set the call/token budget and stopping/review policy before execution. HANDOFF’s pilot token totals show that even a small matrix can be expensive; avoid a full factorial or broad multi-model rerating initially.

These contrasts can diagnose sensitivity. They cannot establish factual accuracy merely through agreement.

### 3. Enforce an explicit national-to-ADM1 interface

A promising candidate is:

1. Complete and freeze an independent national assessment.
2. Supply its **full comparison level and supporting national evidence** to ADM1 assessment.
3. Evaluate only documented local changes in legal authority, implementation and protection.
4. Derive ADM1 outputs without any reverse path into country scoring.

Distinguish national assessment from local increments explicitly, including where the national evidence already discusses regional variation. Otherwise the same restrictions can be counted twice.

Test this candidate in shadow mode rather than restoring the superseded in-country lane wholesale. `ADMIN1_RULES` expresses national-plus-local intent (`tools/blind_pairwise.py:424–449`), but that alone does not validate the old implementation or its legal-hierarchy assumptions.

**Controls and contrasts:**

- National dossier with no local additions: test unintended national re-rating.
- Identical local evidence under different anonymous division labels: test label effects.
- California/Texas: contrasting local evidence under one unchanged national baseline.
- England: different national/devolved architecture.
- Bagmati: thin-evidence handling, not evidence that a small local dossier implies safety or danger.

The documented production trace covers these examples in `adm1-trace.md`, §§1–3. No expected ordering or numerical gap should be specified.

### 4. Test comparability without imposing numerical agreement

Use a small bridge sample assessed through both the candidate ADM1 construction and direct comparisons against countries and foreign ADM1s. Include differing constitutional structures and evidence completeness.

Report:

- Within-condition repeat dispersion and directional disagreement.
- Order and comparator sensitivity.
- Changes under individually controlled evidence treatments.
- Consistency of reasoning about the same national exposure across divisions.
- Direct-versus-derived discrepancies and failures.
- Evidence uncertainty separately from model-response variability.

A roughly near-national ADM1 average can trigger investigation, but must not trigger recentering, shrinkage or country revision. Choice of averaging convention itself introduces assumptions; do not silently select population or visitor weights.

## Designs that may fail

- **Frozen foreign-anchor ladder:** limits moving-reference drift, but its additive difference formula assumes comparable numeric intervals and sufficiently stable comparator effects. Sharing anchors does not prove shared bias cancels. Test rather than assume.
- **National baseline plus local adjustment:** enforces directionality and limits churn, but can transmit national error and double-count regional evidence. Full context and independent bridge checks remain necessary.
- **Independent absolute ADM1 rerating:** useful as a diagnostic, but can repeatedly reinterpret national factors and recreate the current construction mismatch.
- **Majority vote or target-matching:** model agreement is not independent factual validation; tuning until US reaches a preferred score is circular.
- **Endpoint extrapolation:** “not near-certain imprisonment and likely execution” does not determine an intermediate rating. Do not invent intermediate anchors.
- **Mechanical consistency repairs:** forcing every division below its parent, enforcing an average, or case-patching anomalous countries would violate the intended design.

## Review gates and rollout safeguards

Return these decisions to the user/reviewers:

1. How national country evidence should summarize regional variation without numerical aggregation.
2. Whether the proposed national-baseline/local-change interface captures the intended assessment.
3. Comparator-selection rationale, affordable replication budget, and acceptable unresolved uncertainty.
4. Which discrepancies warrant evidence repair, further diagnosis, or an approved method change.

Require evidence review first, neutral method review second, and explicit pilot approval third. Reviewers should receive the full prior US evidence, including dissent, without a requested score outcome. Keep shadow outputs separate, version changes, retain rollback artifacts, and roll out only an approved bounded subset. No UI development labels, stealth credit, general-crime additions, or automatic historical re-derivation.

**Merge verdict: OK with notes — methodological handoff only, not approval of current scoring or a production rollout.**

### Limitations

Read-only review; no edits, commands or model calls. Inspected the three requested documents and relevant current source sections. Historical execution claims and prior model quotations rely on the supplied traces; original session outputs, source-law claims, archived logs and published data were not independently revalidated. No ranking or new rating is established.