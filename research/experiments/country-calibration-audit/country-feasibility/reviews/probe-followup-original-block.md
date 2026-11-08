## Review

**Merge verdict: BLOCK for operational code only. This review is not permission to dispatch.**

Read-only inspection covered the named amendment, runner, tests, both archived dispatch/result pairs, original receipt, and previous recovery review. No edits, commands, API calls, or target scoring were performed. Paths below are relative to `research/experiments/country-calibration-audit/country-feasibility/`.

### Correct

- **Adaptive disclosure is explicit.** The amendment introduction and §7 correctly distinguish an outcome-contingent follow-up from original preregistration and limit what a short fixed-response success establishes.
- **Original failure remains a failure.** Archived `probes/probe-2/probe-result.json` records `status: stopped`, null content, length termination, and a known $0.00026475 charge. Probe 1 records completion and $0.00001551. Combined recorded spend is $0.00028026. Missing historical Gemini HTTP status is disclosed rather than backfilled.
- **Matched requests and finite slots:** `runner.py:178–240,1313–1332,2012–2065` define four total slots, two new requests at 2,000 output tokens, unchanged fixed non-country messages/settings otherwise, no fallback, and one dispatch per slot. Tests at `test_runner.py:2043–2105` inspect request settings and provenance.
- **Shared local budget and unknown liability:** `runner.py:944–1043,1259–1310,2037–2052,2128–2144` aggregate old/new probe costs with scoring costs, reserve before dispatch, reject non-finite costs, and block unknown/unreconciled charges. These controls are local, not a provider-side hard cap; byte/framing reservations are explicitly assumptions.
- **Receipt and review separation:** `runner.py:552–724,1080–1224,1710–1768` require a separate schema-v4 receipt, retain the archival schema-v3 receipt, pin original statuses and receipt-chain fields, reject a successful review of the failed original, and require eight hashed result/review entries before scoring. The original receipt explicitly attributes its procedural decision to AI rather than human sign-off.
- **Concurrency/crash protection:** execution acquires the exclusive lock before ledger/budget decisions (`runner.py:1771–1780`); incomplete probe evidence becomes unknown prior state (`1009–1016`). Tests include lock contention, process races, crash state, and incomplete probes.
- **Future failed-probe HTTP status:** `runner.py:2117–2144` records status only when transport actually returned one; transport exceptions remain without an invented status.
- The probe execution path writes evidence under its probe directory, not map data or score files. Scoring remains gated and disabled by default.

### Finding: P1 — Follow-up continues dispatching after a known first-follow-up failure

**Location:** `probe-followup-amendment.md` §2; `runner.py:1227–1256`; follow-up tests around `test_runner.py:2043–2144`.

The previous neutral recovery review condition 3 says: **“Require both to pass the new gate; any failure ends the phase.”** The requested review likewise explicitly asks for the stopping sequence if either fails.

The new amendment instead states that each follow-up gets its call **regardless of the other’s outcome**. The implementation permits this: `probe_dispatch_gate` checks only that earlier slots have terminal result files, not that `probe-3` completed. Thus:

1. `probe-3` returns a billed, known-charge failure.
2. Its terminal result exists and creates no unknown liability.
3. A subsequent `probe-4` invocation passes the ordering gate and can dispatch.

Blocking later scoring is not equivalent to stopping the follow-up phase. This creates an additional paid request after the predetermined success gate has already failed.

**Smallest fix:** require `probe-3` to have `status: completed` before allowing `probe-4`, and revise §2 to state that a failure prevents every remaining follow-up dispatch as well as scoring. Add a regression test using a known-charge `probe-3` failure, asserting zero transport and price-fetch calls for the subsequent `probe-4` invocation. Retain the four-slot/44-dispatch ceiling as a maximum, not a requirement to consume every slot.

### Validation limitations and residual risks

- Tests were inspected, **not executed**. The supervisor should run the amendment’s offline unittest and renderer-verification commands after correction. Current request-matching tests do not establish the required failure-stopping sequence.
- Stored historical hash strings and receipt-chain validation code were inspected; hashes were **not independently recomputed** in this tool-only review. Byte-for-byte historical immutability cannot be attested without a trusted prior-byte artifact or recomputation/comparison.
- No follow-up receipt or per-slot review artifacts appear in the inspected inventory. Their absence appropriately leaves execution/progression gated; this review supplies neither.
- Reviewer strings and bound review files provide attribution records, not cryptographic proof of reviewer identity, independence, or human participation.
- Remaining methodological risks include adaptation after failure, a tiny non-task-representative sample, provider variability, missing historical HTTP status, administrative token reservations, and local-only spending protection.