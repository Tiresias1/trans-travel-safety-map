# Operational probe amendment (pre-registered, pre-result, non-scoring)

**Pre-outcome review-eligibility amendment:** `probe-review-policy.md` permits
an independently attributed model reviewer for successful operational probes.
The human-only probe-review references below describe the prior procedure;
the operator-review requirement for unknown-charge reconciliation is unchanged.

**Status: pre-registered BEFORE any live request.** No probe and no scoring
attempt has ever been dispatched from this directory; no receipt, sign-off or
probe review exists yet; this document is **not** authorization to execute and
contains **no results and no scores**. It pre-registers the small diagnostic the
user has already authorized, so that its attempts and charges can never sit
outside the experiment's ledger.

## 1. What is authorized: at most two tiny fixed probes

* **At most 2 probes total, one per pre-registered model** (`probe-1` →
  `deepseek/deepseek-v4.1-flash`, `probe-2` → `google/gemini-3.8-flash`),
  dispatched only by `runner.py --execute --probe --run-id probe-N`.
* **Fixed content, no retry:** the probe system/user messages are constants in
  `runner.py` (`PROBE_SYSTEM`, `PROBE_USER`) — a request to reply with a fixed
  `{"probe": "ok"}` JSON object. They contain **no jurisdiction, evidence,
  dossier or rating content**, no country names, no map scores and no rubric.
  Output allowance is fixed at 64 tokens (`PROBE_SETTINGS`). One dispatch per
  slot ever; a failure is recorded and stops — never retried.
* **Scope: transport / response schema / usage ONLY.** A probe measures whether
  the HTTPS endpoint answers, whether the response envelope, model identity and
  billed usage/cost parse as expected, and nothing else.

## 2. Combined attempt ceiling: 42 dispatches

`TOTAL_DISPATCH_CEILING = 42` = the **unchanged 40 frozen scoring attempts**
(all prompts, packets, schedule, order, neutral-label schedule and rubric
untouched) **+ at most 2 probes**. Every probe dispatch counts, including
failures and including a dispatch whose terminal record is lost to a crash.
The runner refuses before dispatch if the combined total would exceed 42.

## 3. One shared local budget ledger

Probe token usage and **actual billed costs** are recorded in
`probes/<slot>/probe-result.json` and aggregated by the same
`prior_run_state()` ledger that scoring uses:

* the **USD 10.00 local ceiling includes all probe charges** (failures
  included); scoring is refused if prior used + worst-case reservation would
  exceed it, and a probe is refused on the same terms. **Every in-run USD
  comparison also includes prior shared spend** (probes + earlier runs): both the
  pre-dispatch reservation check and the postpaid stop compare
  `run-local + prior + remaining reservation` against $10, while each
  `result.json` keeps its totals **run-local** so future ledger scans sum prior
  and run exactly once;
* an **unknown or unreconciled probe charge is a liability, never zero spend** —
  it blocks any scoring run and any further probe until a human-authored
  `probes/<slot>/reconciliation.json` exists;
* a crash between dispatch and terminal record leaves the slot unknown, which
  blocks everything until a human reconciles it; **evidence and locks are never
  deleted automatically**;
* **token usage** of probes is recorded in the same ledger fields
  (`used_input_tokens` / `used_output_tokens`, plus explicit
  `probe_used_*` / `scoring_used_*` splits) and is bounded by this
  pre-registered **probe token allowance**: at most
  `2 × (probe UTF-8 bytes + 128 framing units)` input units and
  `2 × 64 = 128` output tokens across both probes. Probe usage above that
  allowance refuses. The declared scoring ceilings (20 000/800 000 preserved
  proposal, 70 000/2 400 000 reservation units, 80 000 output) stay scoped to
  the **40 frozen scoring calls** — they are sized exactly for that schedule —
  while the **USD 10.00 ceiling and the 42-dispatch ceiling are the shared,
  experiment-wide constraints** covering probes and scoring together.

## 4. Evidence and review requirements (human-authored, never by this runner)

Before **any** scoring dispatch, all of the following must exist:

1. both probe slots dispatched with terminal `probe-result.json` having
   `status: "completed"` (successful envelope + usage validation);
2. a human `probes/<slot>/review.json` per slot with structured fields
   `status: "reviewed_ok"`, `probe_slot`, `reviewed_by`, `reviewed_at`,
   `statement` — a structured status, **not a free-text claim**;
3. a receipt (schema v3) whose `live_behavior.record.probe_evidence` is a
   **structured list of exact `{path, sha256}` entries** covering the four
   files `probes/{probe-1,probe-2}/{probe-result,review}.json`; the runner
   re-hashes those bytes and refuses on any drift.

The runner never creates, signs or manufactures a receipt, a preflight sign-off,
a probe review or any review status; those are human artifacts it only verifies.

## 5. Explicit non-claims

A probe proves only what was observed in that one call. It makes **no claim
about future provider behavior** (routing, pricing, overhead, availability), is
**no proof of any token bound** (administrative reservation units and the
conservative byte+framing arithmetic are unchanged), **no proof of scoring
validity or any score**, and confers no readiness on the claim-level source
preflight, which remains unperformed. There is still **no provider-side budget
boundary**: USD 10.00 is enforced locally by `runner.py` (reservations +
postpaid accounting), not by the provider account. No user or provider
configuration is created or modified; requests carry no force-cache and no
fallback directives; the pre-registered models, settings, zero-retry rule and
score schedule are unchanged.

## 6. Gate order (all fail-closed, one experiment-wide lock)

`--execute` → `--run-id` (`probe-1`/`probe-2` for `--probe`) → frozen hash
self-check → receipt schema v3 (procedure + sign-off content-bound) →
**exclusive `.execution.lock` acquired before any prior state or budget
decision and held through dispatch and finalization** → prior ledger
(unknown/unreconciled/overlap) → probe gates → budget → dispatch once →
terminal record → lock released. Contention on the lock refuses **before any
call**; a lock left by a crash requires explicit human inspection and removal.

## 7. Reproduction (offline)

```
cd research/experiments/country-calibration-audit/country-feasibility
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_renderer test_runner
python3 renderer.py --verify
python3 runner.py                 # disabled: usage + exit 2, no lock, no I/O
```
