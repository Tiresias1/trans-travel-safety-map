## Review

**OK — the previous P1 stopping-rule finding is resolved. No issues found.** This verdict covers only the focused operational-code re-review; it is **not execution authorization**.

- **Correct:** `runner.py:1254–1278` now requires an earlier follow-up’s terminal status to be `completed`. A known-charge failed `probe-3` therefore prevents `probe-4`. The gate runs before price fetch (`2057–2061`), credential loading, and transport.
- **Correct:** Scoring still requires all four slots and successful follow-ups (`runner.py:1158–1227`). Its gate precedes price fetching (`1815–1831`), so either follow-up failure blocks scoring.
- **Correct:** New integration tests cover a real mocked known-charge `probe-3` failure, zero subsequent price/credential/transport calls, preserved failure costs, and blocked scoring (`test_runner.py:2162–2218`). The successful control permits the predeclared `probe-4` (`2220–2243`); existing-slot refusal remains intact (`runner.py:1243–1244`). Tests also cover scoring refusal after either follow-up fails (`test_runner.py:2245–2272`).
- **Correct:** Amendment §2 now explicitly stops remaining follow-ups and scoring after failure; §3 identifies **44 as a maximum, not a target**. The historical `probe-2` failure remains explicitly disclosed, and its pinned `stopped` status is unchanged (`runner.py:189,1121–1123`).
- No new unsafe path was identified within this narrow correction.

**Residual limitation:** Tests were inspected, not executed. No edits, provider calls, or historical hash recomputation were performed.