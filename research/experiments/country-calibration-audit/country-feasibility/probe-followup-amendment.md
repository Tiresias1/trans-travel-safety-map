# Adaptive operational probe follow-up amendment (ADAPTIVE-AFTER-FAILURE; recorded after the original probe phase; non-scoring)

**Status: this is an ADAPTIVE, outcome-contingent amendment, not a
pre-outcome registration.** It is recorded **before any adaptive follow-up
dispatch** — no `probe-3` or `probe-4` request, result or receipt exists yet —
but it is recorded **after** the original two-probe phase and its failure were
observed. It is therefore preregistered *relative to the new observations only*,
it does **not** retroactively satisfy `probe-amendment.md`, and it is **not a
validated scoring method**. It creates no receipt, no review and no
authorization by itself: the independent review and the separately named amended
receipt required below must both exist before any follow-up dispatch or any
scoring attempt. This worker writes neither a receipt nor any review.

**Motivating fact (from the independent review
`…/outputs/146013c4-…/pilot-probes/recovery-review.md` and the archived
records): the original self-imposed no-retry protocol was executed as written
and one of its two probes FAILED.**

## 1. The executed original phase, reported truthfully

Both original probes were dispatched exactly once each under
`probe-amendment.md` (fixed non-country messages, `max_output_tokens: 64`, no
retry). Their archived bytes under `probes/probe-{1,2}/` are **immutable
original evidence** and are never edited, re-dispatched or re-labelled:

* **`probe-1` (`deepseek/deepseek-v4.1-flash`) — completed.** HTTP 200,
  `finish_reason: stop`, billed 85 input / 30 output tokens (19 reasoning),
  **$0.00001551**.
* **`probe-2` (`google/gemini-3.8-flash`) — FAILED.** `finish_reason: "length"`,
  null assistant content (all 60 reported completion tokens were reasoning
  tokens), `status: "stopped"`, billed 53 input / 60 output tokens,
  **$0.00026475 — a known charge, not an unknown-charge case**. The archived
  record contains **no HTTP status**; that field was not captured at dispatch
  time and is **never invented retrospectively**.
* Combined originals: **$0.00028026**, **138 input / 90 output tokens**.

`probe-2` remains a failure. Nothing in this amendment calls it successful,
replaces its status, retries its slot or treats the original no-retry rule as
having been met by any later call.

## 2. What is adaptively authorized: exactly two follow-up slots, one dispatch each

* **`probe-3` → `deepseek/deepseek-v4.1-flash`, `probe-4` →
  `google/gemini-3.8-flash`** — exactly **one additional fixed non-country probe
  for EACH original model** (matched two-model follow-up; neither model is
  selectively favoured).
* **Identical non-country messages and settings to the originals**
  (`PROBE_SYSTEM`, `PROBE_USER` constants in `runner.py`; `temperature 0.0`,
  `top_p 1.0`, `stream: false`, `usage.include: true`,
  `provider.allow_fallbacks: false`, no cache directives, same request
  whitelist) **except `max_tokens` / max output raised to the actual scoring
  setting `2000`** — the only changed parameter, chosen because the original
  failure was a 64-token output-allowance truncation.
* **One dispatch per slot ever. No automatic retries. No further slots.**
  Frozen order: `probe-3` before `probe-4`; each follow-up slot requires the
  terminal `probe-result.json` of every earlier slot first, **and `probe-4` may
  dispatch only while `probe-3`'s terminal record shows `status: "completed"`**.
  **Any follow-up failure ends the phase** — this corrects the earlier wording
  that let each slot dispatch regardless of the other's outcome: a failed
  follow-up (`probe-3` or `probe-4`) is recorded and independently reviewed as
  a failure, never retried and never replaced, and its failure **permanently
  blocks every remaining follow-up dispatch as well as all scoring**. After a
  known-charge `probe-3` failure the runner refuses a `probe-4` invocation
  **before any price fetch, credential read or transport call**, so no further
  paid request is created once the predetermined success gate has already
  failed. A failure may therefore leave slots permanently undischarged.
* Every follow-up dispatch record binds `probe-followup-amendment.md`,
  `probe-amendment.md`, `preflight_receipt.json` (archival), the manifest and a
  provenance pointer to the motivating `probe-2` failure.

## 3. Combined attempt ceiling: 44 dispatches

`TOTAL_DISPATCH_CEILING = 44` = **2 original probes (executed) + 2 adaptive
follow-up probes + the unchanged 40 frozen scoring attempts**. Every dispatch
counts, including failures and including a dispatch whose terminal record is
lost to a crash. **44 is a maximum, not a requirement**: the runner never
dispatches a slot merely to consume the ceiling, and under the stopping rule of
§2 a failure may leave the remaining follow-up slots (and the phase itself)
permanently undischarged. This **supersedes, for the amended phase only, the "42" clause**
in `probe-amendment.md` §2, the probe-gate sentence in `preflight.md`
("combined ceiling 42 dispatches (40 scoring + 2 probes)"), and the
"42-dispatch ceiling" reference in `budget-amendment.md` §3; those documents are
bound historical procedure and stay **byte-unchanged**. All other clauses of
`probe-amendment.md`, `probe-review-policy.md`, `preflight.md` and
`budget-amendment.md` remain in force, including the **zero-retry rule and the
40-attempt scoring schedule**.

## 4. One shared local budget ledger (unchanged USD 10.00 ceiling)

* **The USD 10.00 local ceiling includes every known original charge
  ($0.00028026), every future follow-up charge, all failures and all 40 scoring
  attempts.** Prior shared spend is included in every in-run USD comparison
  (pre-dispatch reservation and postpaid stop); `result.json` totals stay
  run-local so ledger scans sum exactly once. **Shared cost stops execution even
  when earlier probes have already spent** — a follow-up dispatch is refused
  when prior spend plus its worst-case reservation would exceed $10.
* **No provider-side hard spend guarantee exists**: USD 10.00 is enforced only
  locally by `runner.py`.
* **Unknown or unreconciled charges remain liabilities, never zero spend** —
  they block every probe and scoring run until the human-authored
  `probes/<slot>/reconciliation.json` exists (operator reconciliation
  requirement unchanged); a crash between dispatch and terminal record leaves
  the slot unknown and blocks everything; evidence and locks are never deleted
  automatically.
* **Declared probe allowances (input/output reservations):**
  * input: `4 × (fixed probe message bytes + 128 framing units)` = `4 × 374` =
    **1 496 administrative input units** — the four probes carry byte-identical
    messages;
  * output: **originals `64 + 64`**, **follow-ups `2000 + 2000`** → total probe
    output allowance **4 128 tokens** (reasoning counted inside reported
    completion usage, never treated as free capacity);
  * the scoring reservation ceilings (70 000/2 400 000 units, 80 000 output) and
    the preserved 20 000/800 000 proposal stay scoped to the 40 frozen scoring
    calls.

## 5. Runner gates for the amended phase (all fail-closed, one experiment-wide lock)

1. **Ledger recognizes all four slots and counts all costs**: any directory
   under `probes/` outside the four registered slots is an unknown prior state
   and blocks everything; all four slots' billed usage and cost aggregate into
   the same shared ledger.
2. **No probe may dispatch if an original or prior record is missing, unknown
   or unreconciled**: `prior_gate` (unknown crash-incomplete state,
   unreconciled liability, already-attempted cell) runs first; a follow-up slot
   additionally requires **both original slots present with terminal records**,
   their **archived, independently reviewed statuses pinned** (`probe-1:
   "completed"`, `probe-2: "stopped"` — the failed slot is never re-labelled a
   success and the completed slot is never re-labelled a failure), and their
   **receipt chain intact**: each original record's `preflight_receipt_sha256`
   must equal the SHA-256 of the untouched archival `preflight_receipt.json`,
   and each original dispatch must still carry the matching manifest and
   `probe-amendment.md` hashes. Frozen slot order forbids skipping, **and a
   follow-up slot additionally requires every earlier FOLLOW-UP slot to be
   `status: "completed"` — any follow-up failure ends the phase: no remaining
   follow-up may dispatch (refused before price fetch, credential read and
   transport) and scoring stays blocked**.
3. **No slot reuse, no retry loop**: exclusive-create directories, one dispatch
   per invocation, `retry: false` recorded, no code path re-dispatches an
   existing slot.
4. **Scoring gate (does NOT require success for the original failed probe):**
   * all four slots dispatched with terminal records;
   * **all original evidence present and preserved with the original failure
     truthfully disclosed** (`probe-1` completed as archived, `probe-2` stopped
     with its failure disclosure and receipt chain intact — tampering with
     either archived status refuses);
   * **BOTH follow-up slots successful (`status: "completed"`) AND
     independently reviewed**, plus the original reviews: `probe-1`
     `review.json` with `status: "reviewed_ok"`; `probe-2` `review.json` with
     `status: "reviewed_failure"` — an independent review **confirming the
     recorded failure**; a `reviewed_ok` success attestation for the failed
     original slot is rejected; `probe-3`/`probe-4` `review.json` with
     `status: "reviewed_ok"`. All reviews carry structured `probe_slot`,
     `reviewed_by`, `reviewed_at`, `statement`.
5. **Amended observation receipt**: the receipt in force for execution is the
   **separately named** `probe_followup_receipt.json` (**schema v4**), bound to
   the amended `runner.py`, this amendment, `probe-amendment.md`,
   `probe-review-policy.md`, the independent reviews **and the bytes of the
   original receipt**. When it claims `observed_in_bounded_probe`, its
   structured record must hash-bind **exactly eight entries — the exact old and
   new results and the attributed reviews**: `probes/{probe-1,probe-2,probe-3,
   probe-4}/{probe-result,review}.json`, plus a structured
   `original_failure: {slot, status}` disclosure that must match the archived
   `probe-2` bytes. **The original `preflight_receipt.json` (schema v3) stays
   archival, immutable evidence**: it is never re-signed, never edited, never
   used as the execution receipt, and its hash is pinned by the new receipt and
   by the original probe records. The runner never creates any receipt or
   review.
6. **Integrity controls unchanged**: exclusive `.execution.lock` acquired
   before any prior state or budget decision (contention refuses before any
   call; crash locks require human removal), no overlapping dispatch, no score
   writes anywhere, frozen-input hash self-check before anything else,
   disabled-by-default (no credential read, no socket, no write without
   `--execute` + a valid amended receipt), credential only from the
   environment, exact pre-registered model ids, fixed request whitelist.
7. **HTTP status**: any future failed probe records `http_status` **iff a
   response status was actually received**; a transport failure records none;
   historical records are never backfilled (`probe-2` has none and that absence
   stays disclosed).

## 6. Required independent review and new receipt (human/reviewer artifacts, never by this runner)

Before any `probe-3`/`probe-4` dispatch: (a) this amendment must exist;
(b) an independent review of it — amendment, gates, accounting, fixed requests
and stopping rules, validated offline — must exist as
`reviews/probe-followup-review.md`; (c) `probe_followup_receipt.json`
(schema v4) must exist, binding (a), (b), the amended `runner.py` and the
archival receipt bytes. Before any progression to scoring: all four attempts
must be independently inspected with request/response and evidence hashes
recomputed by the reviewer, the eight-entry observation record and
`original_failure` disclosure signed into the receipt, and the four structured
slot reviews present as specified in §5. The runner creates none of these
artifacts.

## 7. Explicit non-claims

This amendment is **adaptive-after-failure**: the increased allowance was
chosen after observing a failure, so no result under it is a pre-outcome
confirmation. A follow-up success would show only that one short fixed-response
request succeeded at the configured allowance on the observed endpoint; it would
**not** establish that the allowance caused the original failure (the calls
occur at different times; provider behavior can vary) and would **not** predict
full-length country-rating behavior — a 2 000-token ceiling does not make a
tiny response a full-length workload. Nothing here validates any score, any
ranking, any model choice, any price or the scoring methodology; the 40-cell
scoring schedule, prompts, packets, candidate rubric, model names and
zero-scoring-retry rule are unchanged and still gated by the claim-level
source preflight. Residual risks kept explicit: adaptive selection of this
follow-up condition, an extremely small operational sample, the missing
historical `probe-2` HTTP status, local-only budget protection, and the absence
of any provider-side spend cap. **Independent review and a new receipt remain
required; no authorization is inferred from this document.**

## 8. Reproduction (offline)

```
cd research/experiments/country-calibration-audit/country-feasibility
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_renderer test_runner
python3 renderer.py --verify
python3 runner.py                 # disabled: usage + exit 2, no lock, no I/O
```
