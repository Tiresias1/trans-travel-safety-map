# Pre-outcome reservation amendment (administrative, pre-registered)

**Status: PRE-OUTCOME.** This amendment was recorded while **zero attempts had ever
been dispatched**: no receipt exists, no `runs/` directory exists, no provider has
been contacted from this directory, and no outcome of any kind is available. It is a
reservation-only change and is **not** execution authorization.

## 1. What changes

| | value | unit |
|---|---|---|
| Per-request input reservation ceiling | **70,000** | administrative reservation units |
| Aggregate input reservation ceiling | **2,400,000** | administrative reservation units |

**Unit definition (stated assumptions):** one administrative input reservation unit =
one UTF-8 byte of the frozen system prompt + user message, plus a fixed **128-unit**
chat-framing allowance per call (role framing / chat template / response envelope).
The exact plan, reproduced independently by `renderer.reservation_plan` and
`runner.build_plan` over the frozen schedule and user messages, is:

* worst-case per request: **66,611 units** (66,483 observed UTF-8 bytes + 128);
* aggregate over the 40 frozen calls: **2,316,208 units**.

Both fit the new ceilings with margin (3,389 and 83,792 units respectively).

## 2. What is explicitly **not** claimed

* These are **administrative reservation units under the tokenizer/framing
  assumptions above — NOT proven provider-native token bounds.** The byte count is at
  least the token count *only if* the provider bills solely for the serialized message
  text plus ≤ 128 units of framing. Provider-side template overhead beyond that, or
  billing for anything outside our serialization, breaks the assumption; the runner
  stops fail-closed if billed input exceeds the reservation. (The earlier wording
  "strict token upper bound" is qualified accordingly.)
* These are **NOT a provider-enforced spend limit.** The **USD 10.00 aggregate
  ceiling, including all failures, is enforced locally** by `runner.py` through
  pre-dispatch reservations and postpaid accounting. No account-side budget, key
  permission or other provider/user configuration is created or modified by this
  amendment. A hard dollar guarantee would require a verified provider-side budget
  boundary for the scoped credential; none exists, so none is claimed. Known local
  bound: billed cost can overshoot the local ceiling by at most one call if provider
  billing exceeds the pre-fetched-price worst case (independent code review, P2).

## 3. What is deliberately preserved unchanged

* All **40** frozen scoring attempts (failures counted; probes are separately
  pre-registered in `probe-amendment.md` and included in the combined
  **42-dispatch** ceiling), prompts, packets, schedule and order, neutral-label and
  empty-dossier sentinels;
* exact pre-registered models and frozen requested settings; **zero retries**;
* the **USD 10.00 aggregate local ceiling** including failures;
* the **original proposal** `per_call_max_input_tokens: 20000` /
  `aggregate_max_input_tokens: 800000`, recorded verbatim in
  `frozen/manifest.json → proposed_caps`. The amendment supersedes those two entries
  **for dispatch reservation only**; they remain recorded and remain an **in-run stop
  rule**: the runner still stops if *billed native* input tokens exceed 20,000 per
  call or 800,000 in aggregate.

Rationale: the byte+framing plan did not fit the original proposal. Silently raising a
cap would have been invisible to review, so the change is pre-registered here, in
`frozen/manifest.json → reservation_amendment`, and in `runner.py` constants — all
three must agree or execution refuses.

## 4. Price estimate (conditional planning only)

* At the **previously observed catalogue prices supplied with this amendment
  instruction**, the full reservation costs approximately **USD 1.21**. Those price
  values are *not* archived in this directory and were not re-derived here; treat the
  figure as a supplied planning estimate, not a measurement made by this code.
* The independent budget review's conservative bound — assigning all 2.4 million
  input units and all 80,000 output tokens to the more expensive model — is
  approximately **USD 2.31**.
* Both are conditional planning estimates, **not billing guarantees**. At execution
  the runner fetches **fresh** catalogue prices over fixed HTTPS with an explicit
  30-second timeout, refuses unknown, negative or non-finite prices, recomputes the
  worst-case reservation against the same USD 10.00 ceiling, and counts every failure
  against it.

## 5. Reproduction

```
cd research/experiments/country-calibration-audit/country-feasibility
python3 renderer.py --verify      # re-derives plan units and re-checks the amendment
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_renderer test_runner
```

## 6. What this document is not

Not a preflight receipt, not a reviewer signature, not provider-execution
authorization, and not evidence about provider behavior. Execution additionally
requires: claim-level preflight sign-off (`preflight.md`), an independent review of
the amended implementation, and a signed `preflight_receipt.json` (schema v2) binding
the fresh hashes of the frozen inputs, `runner.py`, this amendment, the independent
evidence review and the independent budget review — none of which this worker creates
or signs.