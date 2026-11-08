## Review

**No issues found.** The shared-probe-spend P1 is resolved within this focused review.

- **Both comparisons include prior spend:** `ceiling_violation` adds validated `prior_usd` to run-local spend before reserving remaining calls (`runner.py:732–773`); the scoring loop passes it on every iteration (`:1572–1584`). The postpaid check also compares `used["usd"] + prior_usd` against the cap (`:1678–1684`).
- **No ledger double-counting:** result `used_usd` remains run-local (`runner.py:1704`). Tests explicitly rescan the shared ledger and assert combined totals.
- **Regression coverage is appropriate:** `SharedBudgetMidRun` tests a valid $8.10 first scoring response after $2 probe spend, asserting exactly one scoring dispatch and a $10.10 shared-budget stop (`test_runner.py:1660–1681`). A separate case checks pre-dispatch reservation refusal at $9.90 shared spend (`:1683–1697`). The non-exceeded control asserts all 40 calls complete and the ledger totals $4, not $6 (`:1699–1714`).
- **No adjacent regression identified:** the exclusive lock still encloses prior-state reads and scoring execution (`runner.py:1475–1493`). Failed-response billing and unknown-liability handling remain separate from these USD comparison changes; failure still terminates dispatch.

**Notes:** Tests were inspected, not executed. A billed call can still cross the local threshold before accounting stops further calls; this fix does not establish a provider-side hard spend guarantee.

**OK with notes. This is not permission to score.**