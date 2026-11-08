## Review

**No issues found.** The probe-review eligibility amendment is explicit and consistent with the bounded recommendation.

- **Honest adoption and scope:** `probe-review-policy.md` attributes adoption to the coordinating AI, permits a fresh independent model session only for successful non-country operational probes, and requires honest model/session attribution, actual response inspection, findings, and response hashes. It expressly excludes source truth, methodological approval, publication, and future-provider guarantees.
- **Historical wording is superseded explicitly:** the opening notices in `probe-amendment.md` and `preflight.md` explain the eligibility change rather than silently treating AI review as human approval.
- **Content bindings are present:** `runner.py:181–221` binds the policy, procedure, sign-off, amendments, and durable independent reviews—including the probe-policy review. Existing structured observation evidence binds probe results and reviews by hash.
- **Success and liability gates remain separate:** `scoring_probe_gate` requires both successful probe results and attributed structured reviews (`runner.py:960–996`); unresolved liabilities remain blocked earlier by `prior_gate` (`:927–937`). The policy retains authoritative billing evidence and operator review for unknown-charge reconciliation.
- **No false human approval:** `preflight-signoff.md` explicitly identifies its decision as the coordinating AI’s procedural decision, not human sign-off or a cryptographic signature. Its separate source-scope amendment is not validated by this probe-policy review.

### Notes

Reviewer independence, model/session identity, response-hash recording, and authoritative reconciliation evidence remain **procedural obligations**: `scoring_probe_gate` validates non-empty attribution fields, not the reviewer’s actual identity or independence. The coordinator must check that the archived review satisfies the bound policy; merely filling `reviewed_by` is insufficient.

The retained historical preflight text contains obsolete statements, but the prominent effective-status notice explicitly identifies them as historical. Do not quote those statements as current readiness evidence.

No missing binding or contradiction was identified in this change that would make future accounting unsafe. No tests, edits, secrets, or provider calls were performed.

**OK with notes — procedural review only, not permission to execute or score.**