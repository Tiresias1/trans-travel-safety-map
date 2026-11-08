# Original methodology review (BLOCK)

## Review

**Merge verdict: BLOCK for execution approval in its present form.** The design is largely suitable for a bounded, research-only feasibility diagnostic, but it does not yet implement the requested semantic/methodology failure stop. This is not a recommendation about any numerical result or ordering.

Paths below are relative to `research/experiments/country-calibration-audit/`.

### Correct

- **Faithful failure and exposure disclosure.** `country-feasibility-v2/protocol.md` §1 explicitly closes v1, records one failed attempt with no final score and 39 unattempted cells, and discloses reviewers’ exposure to provisional numerical reasoning without reproducing those values. The archived v1 `runs/country-feasibility-20261108-v1/result.json` corroborates the stopped, one-attempt outcome. The claim that exposure did not influence subsequent choices is an attestation, not independently provable from frozen artifacts.
- **Explicit adaptation rather than continuation.** Protocol §§1–2 clearly identify a new adaptive stage, disavow retroactive satisfaction of v1, freeze choices before v2 outcomes, and require reporting unsuccessful attempts as well as successful ones.
- **Bounded balanced design without outcome targets.** Protocol §2 and `frozen/schedule.json` specify 16 country/model/A–B cells and four empty controls, one draw each, interleaved in two balanced blocks. `runner.py:613–728` checks composition, balance and message alignment. No country-specific desired numerical outcome was identified in the inspected design.
- **Limits appropriately disclosed.** Protocol §2 explicitly says within-cell repeat variance cannot be estimated, label invariance cannot be tested, and rankings are not validated. This is an operational diagnostic, not calibration validation.
- **Evidence reuse and conditionality are structurally protected.** `runner.py:688–728` checks messages against their pinned v1 source rows rather than constructing selected excerpts after outcomes. Both prompts distinguish being outed from detention, admission and document-mismatch triggers, prohibit concealment credit, and require uncertainty attribution. The preserved packet qualifications include unresolved law, proposed rather than implemented measures, and uncorroborated allegations; the v1 evidence review expressly limits its endorsement to feasibility.
- **Output allowance adaptation is disclosed conservatively.** Protocol §4 preserves temperature/top-p and absence of an explicit reasoning parameter while increasing the output allowance. It correctly disclaims causal inference from v1 failure and semantic validation from the separate pilot precedent. The reduced design and new operational safeguards are separately disclosed; “sole change” should be understood as the requested generation-setting change, not the entire experimental design.
- **No execution approval is implied.** Protocol §§7–8 require independent reviews and a bound receipt. This review itself supplies neither a receipt nor authorization.

### Finding — P1: Semantic failures do not stop the stage

**Location:** `country-feasibility-v2/runner.py:1336–1392`, `1740–1743`, `1784–1824`; `protocol.md` §§2, 5.

**Evidence:** `validate_output_contract` checks JSON structure, status/score compatibility and explanatory field types. It receives no sentinel/case context. The dispatch loop invokes `validate_response` and then records a validated response and continues; no intervening evidence-fidelity review or semantic gate exists.

Consequently, an empty-dossier control returning `status: "ok"` with an in-range score and populated explanation fields passes the implemented contract checks—even though the frozen prompt explicitly requires abstention for empty evidence. Likewise, structurally valid explanations that turn a proposed rule into an implemented restriction, treat conditional detention as universal exposure, or invent dossier evidence have no prescribed stop pathway before subsequent dispatch.

Protocol §5 enumerates operational, billing and integrity stops, but does not define semantic/methodology failure adjudication. Thus the requested semantic-stop requirement is not met. This also leaves the statement in §1 that success means predeclared “operational and evidence-fidelity criteria” incomplete: the evidence-fidelity decision process is unspecified.

**Smallest fix:** Before approval, define a score-independent semantic acceptance checklist and stopping authority. At minimum, automatically require empty controls to abstain; for dossier-dependent failures, prescribe an explicit review checkpoint before another dispatch, with fail-closed handling of uncertain adjudication. Preserve and report rejected outputs and every attempt; do not repair, replace or retry cells based on their results.

### Residual uncertainties and interpretation limits

- Exposure-related adaptation bias remains despite disclosure and freezing.
- One observation per cell cannot separate model/prompt differences from stochastic variation.
- Anonymized dossiers remain potentially recognizable; no neutral-label controls establish label invariance.
- Evidence fidelity is not evidence completeness. Existing source-quality and visitor-applicability uncertainties survive byte-identical reuse.
- A/B intentionally differ in their treatment of institutional discovery. Their outputs should remain distinguishable, not pooled as interchangeable measurements.
- No shell commands, tests or API calls were run. Hashes and schedule randomization were not independently recomputed. The working-tree diff tool reported no changes against reviewer-launch HEAD; this was an artifact review, not a review of a committed Git range.
- With the semantic gate added and independently reviewed, the proposed scope is reasonable **only as a bounded research feasibility diagnostic**, not as travel advice, ranking validation, or authorization to publish ratings.

# Follow-up methodology review

## Review

**Merge verdict: OK with notes — the prior semantic-stop P1 is resolved for this bounded research-only diagnostic.** This is not execution approval, a signed receipt, publication authorization, or endorsement of any score.

Scope: focused read-only re-review of `research/experiments/country-calibration-audit/country-feasibility-v2/`, principally protocol §5A, semantic sidecars, continuation gates and associated tests.

### Correct

- **At most one scheduled cell per invocation.** `runner.py:2130–2139` selects `sched[k]` without a dispatch loop. `stage_sequence_gate` requires prior attempts to be the contiguous prefix `1..k` and refuses after 20 attempts (`runner.py:1290–1307`). No selection of a different next cell is offered.
- **Independent review is required before subsequent dispatch.** `execute` invokes the sequence and semantic-review gates before price fetching, credential loading and transport (`runner.py:2062–2099`). Successful calls terminate in `paused_pending_semantic_review`, except the final call, whose semantic disposition still requires review (§5A; `runner.py:2330–2350`).
- **Missing, unsuccessful or mismatched reviews block continuation.** `verify_prior_semantic_reviews` requires PASS, response and sidecar hashes, prompt/message bindings, rubric version, reviewer identity/session and a statement. Missing, FAIL, UNCERTAIN, malformed or mismatched records refuse; failed/partial attempts also refuse (`runner.py:1310–1433`).
- **Empty controls now have an automatic terminal semantic check.** The dispatch path invokes `validate_sentinel_semantics` before treating the response as successful (`runner.py:2251–2258`). Empty dossiers must return `insufficient_evidence` and a null score; core cells remain free to abstain. A failed sentinel is preserved through the failure-record path and cannot obtain an ordinary completed-answer review to continue.
- **The review input removes the score without selectively rewriting evidence.** `score_blind_sidecar` omits the numeric score key, preserves every other contract field verbatim, and records frozen dossier references (`runner.py:1147–1179`). Continuation recomputes the projection and checks sidecar equality and hashes (`runner.py:1334–1359`).
- **No retry or outcome substitution is introduced.** Attempts and sidecars use exclusive-create writes; raw responses and billing evidence are retained for successful and failed answers. The fixed prefix advances only after a valid review, not after regenerating or replacing an answer.
- **The semantic checklist addresses the original concern.** Protocol §5A requires source fidelity against the exact dossier and explicitly names invented evidence, proposed-to-implemented drift, conditional triggers treated as universal, concealment credit, uncertainty asserted as fact, and status/explanation contradiction. These criteria encompass source scope, attribution and uncertainty rather than preferred numerical results. Attribution review should retain the dossier’s distinctions between allegations, source reports and established findings.
- **Selection and blinding limitations are disclosed.** §5A expressly recognizes outcome-dependent stopping, unattempted cells after stopping, reviewer discretion/error and potentially recognizable dossiers. Thus a truncated stage is not represented as a balanced completed dataset or a confirmatory comparison.

### Tests inspected

The tests provide relevant offline coverage, although I did **not execute them**:

- `test_runner.py:1284–1360`: missing/FAIL/UNCERTAIN reviews, binding mismatches, leaked score/ranking keys, changed sidecars and prior failed answers block before price/credential/network access.
- `test_runner.py:1361` onward: non-prefix prior attempts refuse.
- `test_runner.py:1506–1575`: one invocation consumes exactly one scripted response, retains evidence and writes a score-free sidecar without authoring a review.
- `test_runner.py:1577–1662`: 20 separate invocations follow schedule order with intervening fixture reviews; a 21st invocation refuses.
- `test_runner.py:1792` onward: core abstention remains permitted, and a scoring empty sentinel terminally stops.

**No issues found.**

### Notes and residual risks

1. **Independence and blinding remain procedural trust boundaries.** The runner verifies review artifacts, not the actual identity or independence of their authors. Protocol §5A’s assertion that “a PASS can never be forged” should be read narrowly as *the runner does not author PASS records*, not as authentication or tamper-proof storage.
2. **Score-free structure is not guaranteed cognitive blinding.** Verbatim explanation fields could themselves mention numerical values or evaluative comparisons; raw scored responses remain accessible separately. Reviewers must avoid inspecting them or judging preferred outcomes. The code cannot prove that they did so.
3. **Semantic review remains judgment-based.** The checklist is predeclared, but the runner verifies a PASS attestation rather than independently determining factual fidelity. Apply the same source-scope and uncertainty standards to every answer, irrespective of its implication.
4. **Stopping can create informative missingness.** Retain and report the attempted prefix, rejected answers, review decisions and all unattempted cells. Do not infer model or prompt superiority from a selectively completed prefix.
5. **This was static review only.** No provider calls, edits, shell commands or tests were performed. The bounded working-tree inspection listed the v2 artifacts as untracked; no committed range was reviewed.

# Independent semantic-checkpoint and cache consultation

## Review

**Recommendation:** For this non-publishing feasibility exercise, use **predeclared balanced batches with independent, fail-closed semantic review before the next batch**, plus automatic empty-dossier abstention checks after each response. The existing two frozen blocks of ten are the smallest process change. They are defensible **only if explicitly accepting that a material semantic error can be followed by the remaining calls within its block**. If the requirement is literally “no call after any material semantic error,” review each dossier-dependent answer before the next dispatch instead.

This is methodological advice, not execution approval, a receipt, or publication authority. No live calls, shell commands, tests, or edits were made.

### Evidence and present gap

- `country-feasibility-v2/protocol.md` §2 already freezes 20 attempts in two balanced blocks of ten, with no retries or outcome-driven reordering. It explicitly disclaims ranking validation and within-cell variance estimation.
- The supplied `method-review.md`, finding “Semantic failures do not stop the stage,” identifies the missing evidence-fidelity gate and recommends automatic sentinel enforcement plus independent review before another dispatch.
- The inspected `runner.py:1788–1806` records a response and checks cost/output ceilings without an intervening semantic checkpoint. The supplied code review independently describes the structurally oriented output validation.
- `protocol.md` §5 currently requires stopping on any cached/cache-write tokens. `runner.py:1421–1431` implements that stop, describing nonzero counts as a “hidden cache charge.” Such counts alone do not establish either a user-requested cache directive or an undisclosed charge.

The semantic gap is real. **Per-answer independent review is one remedy, not the only scientifically defensible remedy.** Batch review would require an explicit pre-dispatch amendment; it does not satisfy the method reviewer’s literal per-answer recommendation as written.

### Comparing the checkpoint designs

| Design | Material-error stopping | Selection bias and independence | Cost/time and information |
|---|---|---|---|
| **Every answer reviewed before the next call** | Strongest: no later dispatch after a detected semantic failure. Uncertain adjudication must also hold dispatch. | Does not eliminate outcome-dependent truncation. Independence requires a reviewer who did not generate the answer or implement the decision rule, applying frozen criteria. | Most review interruptions; can save generation costs after early failure. Early stopping may leave highly unbalanced evidence. |
| **Frozen balanced batches, checkpoint before next batch** | Stops between batches, not within them. A failure in the first answer may be followed by nine further calls in the existing block. | Fixed boundaries avoid discretionary “review now” choices. Survival into batch two still depends on batch-one outcomes. Balance reduces composition problems but does not make the completed sample unbiased. | Fewer interruptions; a completed first block supplies broader diagnostic coverage. Risks spending tokens on later answers after an undetected failure. |
| **Automatic checks each answer, independent semantic review at fixed batch boundaries** | Immediate stops for machine-checkable violations; delayed stops for dossier interpretation errors. | Same conditional-survival limitation as batch review. Automation is not independent semantic adjudication. | Best fit for modest work if delayed semantic detection is acceptable; requires honest separation of structural and semantic acceptance. |

The third design is the recommended implementation of the second. Do not add adaptive batch sizes or selectively review “surprising” scores: those introduce discretion without a clear feasibility benefit.

### Smallest defensible process

1. **Freeze the decision rule before dispatch.** Retain the current schedule, prompts, single draws, and maximum attempt count. Declare checkpoints after calls 10 and 20; the final checkpoint determines the stage’s semantic disposition even though no further batch follows. Do not change batch boundaries after seeing outputs.

2. **Enforce automatic empty-dossier abstention immediately.** A sentinel must return `status: insufficient_evidence` and `score: null`; otherwise stop before the next dispatch. Independent review must still check whether its explanation invents evidence or makes unsupported substantive claims. Correct status fields alone do not establish valid abstention.

3. **Use a short, frozen, score-independent semantic checklist.** Material failures include:
   - invented evidence or materially false attribution to a dossier item;
   - proposed or unresolved measures represented as implemented facts;
   - conditional detention/document/admission triggers represented as universal consequences of being outed;
   - concealment, passing, silence, or avoidance credited against the frozen rubric;
   - uncertainty converted into an unsupported definite safety/harm assertion;
   - an explanation materially contradicting the output’s stated status.

   Do not make a numerical score, preferred country ordering, or disagreement with reviewer intuition a stop criterion. Review substantive fidelity against the actual frozen packet, not whether the reviewer likes the answer.

4. **Make the independent checkpoint a dispatch gate.** At each boundary, review every answer in the block against the relevant packet. Record output/input hashes, checklist disposition, cited passages, reviewer identity and timestamp. Require explicit approval bound to that block before dispatching the next one. Missing, failed, or uncertain review means no further calls. Do not rely solely on a narrative instruction to an otherwise uninterrupted loop.

5. **Preserve failures without favorable-result retries.** Retain every response, charge, review decision, and unattempted schedule row. A failed checkpoint terminates this stage; it does not trigger regeneration, replacement cells, schedule changes, or a fresh run seeking a pass. Any later version must disclose this stopped stage and receive separate review, rather than erase it.

6. **Report feasibility only.** Distinguish attempted, structurally valid, semantically accepted, rejected, and unattempted cells. Describe failure categories and bounded resource consumption. Do not treat surviving outputs as validated ratings or use a favorable subset to infer comparative country/model performance.

**Condition:** If the user requires immediate stopping for dossier-dependent material errors—not merely stopping once the scheduled review detects them—use the same checklist and records **after each answer**, before the next call. Batch review cannot offer that guarantee. If reviewer availability cannot support the chosen gate, stop rather than silently substitute self-review.

### Stopping is not the same as selection bias

Stopping can be an appropriate safety/resource decision while still making the observed sample outcome-dependent.

- Per-answer review truncates the fixed schedule at a semantic failure.
- Batch review allows a complete balanced first block but makes the second block conditional on passing the first.
- Neither creates a license to omit failed answers, report only approved outputs, or describe the completed subset as an unbiased comparison.
- Predeclaration limits discretionary selection; it does **not** remove conditioning on success.
- Independent review reduces investigator discretion but does not prove judgments correct. Reviewers need the packet and explanation. Where practical, hide scores and model/country labels not needed for adjudication; anonymization is imperfect because dossiers may be recognizable. Document unavoidable exposure rather than claim full blinding.

The incremental informational value of batch two is additional feasibility coverage, not confirmation of a desired score or ranking.

### No force-cache versus automatic provider caching

**A blanket stop on nonzero cached-token usage is not required by the described user rule “no force-cache.”** That rule concerns what the client requests or deliberately induces. Provider-initiated automatic prompt-cache reads can occur despite an unchanged request containing no cache directives. The supplied code review verifies that `build_request` sends no cache fields and disables fallback; it does not establish that the provider promises cache-free processing.

Recommended treatment, frozen before dispatch:

- Continue sending **no cache directives** and do not add cache warming, cache-busting probes, or retries to obtain a preferred cache condition.
- Permit valid reported automatic cache reads when accounting remains interpretable, while recording them as an execution condition—not as a semantic pass or failure.
- Keep fail-closed handling for invalid usage, unknown liabilities, violated reservations, and inconsistent billing. If automatic cache writes have pricing/accounting semantics that cannot be reconciled, stop for that uncertainty, not merely because caching occurred.
- Record exact request fields and hashes, timestamps, requested/returned model and provider, response ID, full raw usage including cache-read/write counts, prices used for reservations, actual charged cost, and any known routing/cache metadata. Preserve unavailable information as unknown; token counts alone do not identify cache provenance.
- Disclose that provider cache state is uncontrolled. This limits reproduction of latency and costs and precludes claims of uncached performance. Absence of cache directives does not establish identical backend conditions or deterministic answers.

A zero-cache stop remains defensible **only as an additional predeclared experimental constraint**, for example if uncached cost/latency is itself the measurement objective or accounting cannot accommodate the provider’s cache semantics. Neither objective is established here. Keeping it solely for “reproducibility” can instead yield arbitrary, provider-state-dependent truncation. Changing the current rule requires updating and reviewing §5 and its implementation before execution; it must not be relaxed reactively after a cache-triggered stop.

### Verdict and residual risks

**Process recommendation: OK with conditions; present artifacts are not execution approval.** The existing semantic-gate gap must be resolved and independently reviewed. The separate code-review findings remain outside this consultation’s revalidation and are not cleared here.

Residual risks include semantic-review error, unavoidable prior exposure, outcome-dependent truncation, uncontrolled backend/cache state, inherited evidence limitations, and the absence of repeated observations or label-invariance controls. None is cured by successful completion. Publication authority is not granted.