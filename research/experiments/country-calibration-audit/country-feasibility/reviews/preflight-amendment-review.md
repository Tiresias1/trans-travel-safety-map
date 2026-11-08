# Focused review — exploratory-preflight amendment

**OK with notes as a proposed procedural amendment—not execution authorization.** The documentation accurately distinguishes the bounded audit from exhaustive verification. The existing execution block remains intact; adoption and sign-off are still outstanding.

## 1. Verified claims

- **Scope is accurately represented.** `evidence-preflight-amendment.md` §1 calls the review a **“prioritized audit of decision-critical corrections, scope, attribution and uncertainty preservation”**, explicitly stating it **“did not independently verify every material claim”** or recompute hashes. This matches my original review and follow-up.
- **No false completion/publication approval.** Revised `preflight.md` states the comprehensive gate **“has NOT been performed, satisfied or completed.”** Amendment §3 says outputs **“cannot substantiate destination scores, rankings, orderings, travel advice or country comparisons.”**
- **Material uncertainty is retained.** Amendment §2 explicitly identifies USA custody allegations as **“source allegations, not established findings”**; unverified NPL political claims; incomplete VAT primary-law coverage; unestablished UK ward-ban implementation; conditional-trigger limitations; and identity leakage. Its catch-all includes **“corroboration of every unchanged assertion”**, so the list does not falsely certify everything else.
- **Actual amendment/review contents are bound.** In `runner.py`, `binding_paths()` resolves the amendment to the module’s actual `evidence-preflight-amendment.md`, and `REVIEW_BINDINGS` includes the durable local follow-up. `current_bindings()` hashes `path.read_bytes()` and refuses missing files. `verify_receipt()` requires an exact binding-key set and exact hash equality—not merely matching filenames.
- **Other gates remain required in the inspected code.** `preflight-signoff.md`, the procedure, frozen inputs, data, runner and existing reviews remain bound. Receipt validation still requires `preflight.status == "signed_off"`, the specified distinct sign-off artifact, and provider-semantics documentation. No exploratory bypass was introduced in these inspected paths.

## 2. Contradicted claims

**No material contradiction with my prior findings.** The amendment does not retroactively call my audit exhaustive or treat its feasibility-only judgment as a completed preflight.

## 3. Weak / unclear / unsupported claims

- **Adoption is not yet operationally resolved.** The amendment is explicitly **“recorded but not adopted.”** The runner still describes `preflight-signoff.md` as a **“claim-level decision artifact”**, while the historical procedure still demands comprehensive verification. This is conservative, not a bypass—but future adoption must clearly specify what the exploratory sign-off attests to. A narrower sign-off must not falsely attest that comprehensive verification occurred.
- **Human scope approval is not semantically enforced by hashes.** Binding documents proves receipt consistency with bytes; it does not establish reviewer independence, truthful adoption, or evidentiary adequacy. The documentation appropriately calls this a human/procedural gate.
- **No independent attestation of the amendment’s “zero attempts” or stated copied-file SHA.** I inspected the local follow-up text and binding implementation, but did not recompute hashes or inspect every execution record.

## 4. Material source-quality concerns

The amendment preserves the previously identified source limitations rather than resolving them. USA single-source custody assertions, NPL political allegations and VAT legal absences remain unsuitable as independently established destination facts. No new external source audit was needed for this procedural review.

## 5. Missing evidence / test limitations

I inspected test source covering procedure/sign-off content tampering, missing sign-off, incorrect receipt references, and generic receipt/hash drift. **I did not execute tests.** I did not establish dedicated regression coverage specifically mutating/removing the new amendment and follow-up-review bindings.

Before relying on that particular regression claim, confirm tests demonstrate refusal—with zero transport calls—for:
1. amendment-byte drift;
2. follow-up-review-byte drift;
3. either new binding omitted or its file missing.

This is a validation limitation, not evidence that the inspected generic binding mechanism fails.

## 6. Material contradictions and remaining blockers

**No new substantive blocker found in the proposed amendment.** Existing blockers remain:

- explicit independent adoption/scope sign-off before outcomes;
- exact-input/hash verification and fresh receipt;
- an unambiguous sign-off that distinguishes exploratory approval from the unsatisfied comprehensive gate;
- resolution of any discovered material contradiction, attribution error, lost qualification, misleading certainty, truncation or prohibited leakage;
- all existing budget, probe and execution requirements.

Retained identifiable case names still require an explicit blinding/scope decision; merely listing that open issue does not decide it.

## 7. Implications

The proposal faithfully implements the substance of my follow-up: disclosed uncertainty may be used to test instrument behavior, but not silently upgraded into fact, safety, danger or validated country comparisons. The required output review and new-frozen-version rule are appropriate.

**OK with notes for the amendment’s accuracy and conservative binding design. Execution remains blocked pending adoption and the other required gates.** Do not describe this review as exhaustive source verification, test execution, a signed receipt, or authorization to dispatch.