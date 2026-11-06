## Bottom line

**The 0.028 gap merits an audit: it looks under-separated relative to the stated rubric, but the battery does not establish that the correct map gap is 0.20.** Direct numerical ratings and an anchored pairwise settlement are different instruments.

The strongest finding is **rubric sensitivity**, not an independently verified estimate of either country’s safety.

### 1. Is the existing gap defensible?

It remains possible, but it is not well supported by this experiment.

| Condition | Mean gap, individual | Mean gap, pairwise |
|---|---:|---:|
| Knowledge only | +0.086 | +0.150 |
| Articles | −0.030 | +0.050 |
| Articles, blinded | +0.056 | +0.154 |
| Full instructions | −0.206 | −0.154 |
| Full instructions, blinded | −0.078 | −0.182 |

Negative means Nepal safer. With full instructions, **18 of 20 model-condition results favour Nepal**, including all ten pairwise results. Crucially, the production rater itself produces pairwise gaps of −0.15 and −0.18 with instructions.

That supports investigating whether production scoring implements the rubric consistently. It does **not** justify replacing the map scores with battery averages.

### 2. What most plausibly explains the discrepancy?

**First: a rubric-to-production implementation mismatch.** The largest consistent intervention is supplying the full instructions. Possible failures include missing or diluted instructions, inconsistent rule-19 classification, or explanations that recognise institutional threats without giving them the specified weight.

**Second: reputation priors or generic “developed-country safety” heuristics.** Knowledge-only results favour the UK, especially for DeepSeek. However, blinding does not consistently remove that preference. Country-label bias alone therefore cannot explain the results; evidence interpretation and weighting matter too.

**Third: settlement or calibration compression.** Entirely plausible, but currently untested. Pairwise *direct-number* prompts are not the production pairwise instrument. Raw production comparisons could favour Nepal strongly while anchors or the comparison network compress the final distance.

**Dossier capture remains possible, not demonstrated.** Article-only results do not show that UK threat-framing is absent: models might see the relevant facts but weight them differently without the rubric. We need the actual dossiers and reasoning to distinguish omission from underweighting.

### 3. Prioritised actions

**1. Audit the actual production comparison.** Retrieve:

- Exact production prompts, dossiers, rubric placement, and model settings.
- Every Nepal–UK comparison, including order, raw outputs, and reasoning.
- Their comparisons against shared neighbours/anchors.
- Settlement objective, weights, transformations, residuals, and score uncertainty.

First locate the failure: **raw judgement, aggregation, or calibration**.

**2. Verify the decisive factual claims before rerating.** Request a sourced, dated claim table covering:

- Nepal’s recognition rights **in practice**, including requirements and documented police, border, detention, and harassment incidents.
- UK search/custody rules by jurisdiction, legal status, exceptions, and actual implementation.
- The precise scope of the 2025 ruling and subsequent single-sex-service policies.
- Foreign recognition: distinguish recognition for particular legal purposes from treatment of foreign passports.
- Youth-care restrictions and their relevance to short-term visitors.

Do not equate “applies if detained” with frequent exposure. Nor should lack of documented targeting establish its absence.

**3. Run a controlled production replay.** Use verified, scope-matched dossiers; swap order; repeat runs; compare existing instructions against an explicit rule-19 checklist. Require classifications of friction, hostility, and state threat-framing, plus exposure likelihood and severity. Avoid counting one policy repeatedly.

**4. Re-settle the map only after identifying the mechanism.** If raw comparisons already separate them, inspect calibration. If they do not, fix evidence or rubric adherence first.

### 4. Supported versus uncertain

**Supported:** rubric provision reliably changes these models’ relative assessments; production scores warrant investigation.

**Uncertain:** the precise real-world ranking and gap, factual scope of several cited policies, and where production loses separation. Model agreement is correlated evidence—not independent validation. The rubric’s weighting itself is also a methodological choice, distinct from empirically measured traveler risk.