## Review

**Verdict: BLOCK provider execution pending the criteria below.** Read-only review; no edits, tests, or provider calls. Reviewed the named code/evidence reviews and current runner, caps, and preflight requirements. This is methodological approval of a proposed path only—not scoring authorization.

### Correct
- The current mismatch correctly blocks dispatch: `runner.py:345–361, 614–620` refuses reservations exceeding the manifest’s 20,000-per-call/800,000-total input caps (`frozen/manifest.json:77–85`).
- The independent evidence review supports **feasibility only**, retaining material source limitations and no preferred scores. Those limits must remain attached to interpretation.
- Reservations currently cover the **entire remaining schedule**, not merely the next request (`runner.py:382–405`). Calling this a rolling-next-call budget without changing the implementation would be inaccurate.

### Smallest safe path

**Pre-register a reservation-only amendment before any outcome**, preserving all 40 frozen attempts, prompts, packets, ordering, output limits, no retries, and the **unchanged $10 aggregate maximum including failures and probes**.

1. Set explicitly named *reservation ceilings*, for example **70,000 input units/call and 2,400,000 total**, conditional on an independently reproduced exact plan fitting both. Preserve the former caps and explain the amendment; do not silently reinterpret them. These are administrative reservation units, **not guaranteed native-token ceilings**.
2. Retain whole-schedule reservations and all existing fail-closed gates. This is smaller and less selection-prone than switching to next-call rolling accounting.
3. Recompute cost reservations using fresh, archived catalogue prices. At the supplied prices, even assigning all 2.4 million input units and 80,000 output tokens to the more expensive Gemini model gives approximately **$2.31**. That is a conditional planning estimate, not a billing guarantee.
4. Independently review the amended implementation and receipt, run offline tests, then seek explicit execution authorization. No score-driven packet shortening, schedule changes, model substitutions, or selective retries.

**Alternatives:** Reliable native counting is preferable only if available for the exact model, message serialization, and billable overhead; verify its coverage rather than substituting `o200k_base`. Rolling reservations can permit only a partial run and cannot guarantee that the next billed request stays under a native cap. A smaller, neutrally selected pilot is defensible under a new preregistration but changes the design; reducing attempt count alone does not fix the per-call mismatch.

### Guarantees versus estimates

- **Can enforce locally:** fixed dispatched payloads and sequence, dispatch-attempt limit, no automatic retries, reservation arithmetic, refusal before dispatch when known limits fail.
- **Cannot currently guarantee:** native input counts, chat/reasoning overhead, full completion of 40 attempts, provider routing behavior, or actual dollar charges remaining below $10 solely through postpaid response accounting.
- The reported **13,247 maximum / 464,464 total `o200k_base` estimates** demonstrate plausible feasibility only. Likewise, UTF-8 bytes plus 128 is conservative under particular tokenizer/framing assumptions—not a universal provider bound. The “strict token upper bound” label at `runner.py:364–365` needs qualification.
- A genuinely hard $10 spend guarantee requires a verified provider-side enforceable budget boundary covering the scoped credential/account, including in-flight charges. If unavailable, disclose that limitation and **do not authorize execution under an unconditional hard-$10 requirement**. A local margin reduces risk but does not prove the guarantee.

### Findings and blocking criteria

- **P1 — Non-finite billed cost bypasses fail-closed accounting.** `runner.py:568–570` accepts floating-point NaN: it is numeric and `NaN < 0` is false. Python’s default JSON decoder accepts `NaN`; adding it to `used["usd"]` makes both subsequent ceiling comparisons false (`:402, :735–736`). Smallest fix: require finite, nonnegative costs and finite, valid configured USD caps; test NaN/infinity and malformed billing before authorizing execution.
- **P1 — Receipt assertion exceeds available verification.** `verify_receipt` requires `provider_api_semantics.verified == true` (`runner.py:248–254`), while catalogue listings and official usage-accounting documentation do not establish exact live behavior. Do not populate that flag merely to unlock execution. Amend the receipt schema to distinguish **documented**, **observed in a bounded probe**, and **unverified assumptions**; independently review that change.
- **Execution blocker — Unknown or drifting billing/routing.** Missing, inconsistent, non-finite, or over-reservation usage/cost; price changes outside the approved envelope; unexpected model/provider identity; or unresolved chargeability must stop dispatch. Preserve the raw response and count the attempt even if validation fails. Unknown charges remain **unreconciled liabilities**, not zero spend; no new run may reset that ledger. Exact model equality alone does not verify backend-provider stability (`runner.py:556–560, 583`).

### Minimal non-scoring schema probe

Appropriate **only after separate explicit authorization** and the existing claim-level preflight prerequisite (`preflight.md:3–6`), or a formally approved procedural amendment—not as an informal exception.

Predeclare at most **one tiny, fixed, non-country request per model**, minimal output allowance, no retries, no scoring content, and strict schema/usage/model checks. Count every dispatched probe, including failures, in a separate operational ledger; count all probe charges against the same $10 maximum. Explicitly authorize **up to 42 total dispatches: two probes plus 40 scoring attempts**; otherwise probes consume the existing 40-attempt ceiling and the complete frozen schedule cannot run. Do not silently enlarge the attempt allowance.

A probe observes only those requests at that time. It does not verify full-packet overhead bounds, future pricing/routing, or every failure mode.

### Receipt binding

Bind hashes of the frozen inputs, revised manifest, runner, amendment, source-preflight decision, budget decision, and any probe request/response evidence; archive price timestamp, IDs, units, and source documentation. Current bindings cover frozen/source inputs but not all procedural documents (`runner.py:94–107, 229–263`). Record reviewer/date, exact authorization scope, outstanding assumptions, and stop rules. Label the receipt **procedural sign-off, not cryptographic authenticity or proof of future provider behavior**.

**Merge verdict: BLOCK execution; reservation-only amendment is the recommended next step.** No relaxation of spend safeguards or targeting of scores is justified.