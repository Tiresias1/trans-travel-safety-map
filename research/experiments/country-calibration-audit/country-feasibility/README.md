# Country-feasibility pilot (pre-registered, offline preparation only)

Preparation only. This directory contains **no credentials, and no model call has
ever been made**; no running provider is configured. The only dispatch-capable
code (`runner.py`) is **disabled by default**: without an explicit `--execute`
flag **and** a reviewed, hash-bound `preflight_receipt.json` (schema v3) it never
reads a credential, never opens a socket and never writes a byte — and even with
both it still refuses while live provider behavior is recorded as unobserved, while
an experiment-wide `.execution.lock` is held by someone else, while any prior run
or probe leaves an unreconciled liability or an unknown (crash-incomplete) state,
while any predeclared cell was already attempted, or until **both** pre-registered
non-country probes are dispatched, successful and independently reviewed (see
`probe-review-policy.md`). Nothing outside
`research/experiments/country-calibration-audit/` is touched, nothing is staged or
committed, and **no national score is written anywhere** (no code here can write to
`data/`, `tools/` or the UI).

The pilot is an **instrument-and-evidence acceptance test** following the independent
review (`…/outputs/deb1bb5b-…/country-pilot/review.md`): can two prompt variants and
two model families return *valid, evidence-grounded single-country outputs* for four
purposively chosen cases? It cannot establish validated country values, convergence to
truth, an independent discovery effect, blinding, rankings, or any confirmation of the
published map.

## Design (frozen; 40-attempt ceiling)

* **Core: 32 calls** = 4 cases (USA, GBR, NPL, VAT — purposive stress sample, not a
  representative or calibration sample) × 2 frozen candidate variants (A/B) × 2 distinct
  model families × 2 repeat draws, using **one frozen, source-reviewed dossier version
  per case across every core condition** (the reviewed revision only; originals are not
  scored — repair effects are not crossed with model/variant effects).
* **Empty-dossier sentinels: 4** = one explicitly empty, **anonymous** dossier × 2
  families × 2 variants. No `COUNTRY_NAMES` literal appears in it (a name would test
  memory, not absence of information). Expected behaviour is uncertainty/abstention via
  `status: insufficient_evidence, score: null` — the output contract allows abstention
  and never forces a score, a midpoint or a prior.
* **Neutral-label sentinels: 4** = **preselected before any output: case USA, dossier
  label `NEUTRAL-7`** (schedule `frozen/schedule.json`), × 2 families × 2 variants.
  Evidence bytes are identical to the USA core packet; **only the neutral dossier label
  differs** (unit-tested). This tests **gross arbitrary-label sensitivity only** — not
  effect size and not country blinding. A named-versus-anonymous information-policy test
  is deliberately **not** mixed in; it would be a separately approved follow-up.
* **Ceiling: 40 attempted requests** (32 + 4 + 4), counting provider failures and
  malformed/truncated outputs; no favourable-output retries, no post-result expansion.
  Pre-registered separately (`probe-amendment.md`): at most **2 tiny fixed
  non-country probes** (one per model, no retry) precede scoring, giving a combined
  **42-dispatch ceiling**; probes share the same USD 10 ledger and are hashed/archived
  under `probes/<slot>/`, never mixed with the 40 scoring results. The 40 scoring
  cells, prompts, packets, order and rubric are unchanged by this.
* **Two balanced randomized blocks** (seed `20261121`, frozen in `frozen/schedule.json`):
  block 1 = draw 1 of all 16 core cells + 4 sentinels; block 2 = draw 2 of all 16 cells +
  4 sentinels; 20 attempts each. Randomized within each block, interleaved (sentinels
  never adjacent, ≤2 consecutive attempts of one variant), balanced 10/10 per variant and
  per family in each block, complementary sentinel (family × variant) assignments across
  blocks. Fresh context per attempt; no shared conversational context, browsing or other
  countries' evidence; one country's packet per attempt and no other countries' data.
* **Model families (exact API ids):** `deepseek/deepseek-v4.1-flash`,
  `google/gemini-3.8-flash`. **Requested settings** (frozen; requested, not
  provider-guaranteed): `temperature 1.0, top_p 1.0, max_output_tokens 2000`.

## Predeclared ceilings — PROPOSED settings, not enforced

Recorded in `frozen/manifest.json → proposed_caps` with
`enforced_by_this_code: false` (the renderer never enforces them). The
**disabled** `runner.py` is the only code that would enforce them, and only after
its two hard gates; it reserves worst-case usage before every dispatch, accounts
all billed usage including failures, and **stops and reports rather than raising a
cap**:

* attempts: **40** (failures count);
* per call: **20 000 input / 2 000 output tokens**; aggregate **800 000 input /
  80 000 output tokens**;
* monetary: **USD 10.00 aggregate, including failed requests**;
* stop on unknown billing usage, ceiling exhaustion, model substitution/version drift
  or context overflow — never silently truncate evidence;
* observed input size (a measured fact, `frozen/manifest.json →
  max_input_bytes_per_call_observed`): **66 483 UTF-8 bytes** — the maximum over BOTH
  derived prompt variants crossed with all 40 messages. Nothing here converts bytes
  into tokens or money: **no provider tokenizer or price list was consulted**, so the
  token and USD figures above are unvalidated proposals, not a cost ceiling; exact
  provider tokenization stays unknown until then.

**Pre-outcome reservation amendment (adopted; see `budget-amendment.md`):** the
byte+framing plan needs **66 611 units/call** and **2 316 208 units** over the 40
attempts, which did not fit the original 20 000/800 000 proposal. Before any attempt
was ever dispatched, administrative **input reservation ceilings of 70 000 units per
request and 2 400 000 units aggregate** were pre-registered (manifest →
`reservation_amendment`, `budget-amendment.md`, `runner.py` constants — all three
must agree or execution refuses). The original 20 000/800 000 proposal is **kept
verbatim** in `proposed_caps` and remains an **in-run stop rule on billed native
tokens**; the aggregate output reservation (80 000) fits exactly.

**Honest labels:** one reservation unit = one UTF-8 byte of the frozen prompt +
message plus a fixed 128-unit chat-framing allowance per call. These are
administrative reservations **under stated tokenizer/framing assumptions — not
proven provider-native token bounds and not a provider-enforced spend limit** (the
earlier “strict upper bound” wording is qualified accordingly). The **USD 10.00
ceiling is enforced locally** by the runner (reservations + postpaid accounting),
not by the provider account; at previously observed catalogue prices the full
reservation is a planning estimate of ≈ **USD 1.21** (≈ USD 2.31 under the budget
review’s all-to-the-expensive-model bound), while execution always fetches **fresh**
prices, refuses unknown/negative/non-finite ones and counts every failure against
the $10 ceiling.

## Prompt conversion (fail-closed, no regex prose surgery)

`frozen/single_a.txt` / `single_b.txt` are derived from the complete reviewed pairwise
candidates (`rule-contrasts/frozen/candidate_{a,b}.txt`) by **8 literal, count-asserted
edits** recorded machine-readably in `ledger.json` (before/after strings; every
before-block must match exactly once in its source at apply time or the build aborts):

* `T1_opening` + `T2_task_line` — pairwise task framing → one anonymised dossier; the
  A/B conditional-consequence vs state-engineered-discovery task difference is preserved
  verbatim;
* `T3`–`T6`, `T8` — the remaining instructions that *require a partner dossier or a
  forced difference* (rule 3 partner sentence, rule 4 two-dossier sentence, rule 14
  cross-dossier compare and forced-unequal-scores sentences, rule 12's pairwise
  SCOPING sentence) rewritten to single-jurisdiction equivalents preserving their
  substantive rules;
* `T7_output_contract` — the two-score contract replaced by a **single-score JSON
  schema**: `status` ∈ {`ok`, `insufficient_evidence`}, `score` float or `null`,
  evidence-based `why`, plus the five bounded diagnostic fields
  (`evidence_ids`, `discovery`, `direct_harms`, `scope_triggers`, `uncertainty` —
  explanations, **not additive numerical components**); byte-identical in A and B
  (shared experimental extension).

**Preserved untouched:** the 0.00 endpoint = near-certain imprisonment **and** likely
execution; no credit for passing/stealth/silence/avoidance; intermediate points
undefined; curiosity/social friction **VERY LOW WEIGHT**; societal and state
threat-framing **REAL WEIGHT**; rule 10b; every other substantive rule and every A/B
variant difference (unit-tested by masking the seven inherited variant sites plus T2).
Rule 12's parent arithmetic is retained per the preserve-all-substantive-rules contract
but is **dormant**: none of the four cases is a dependent territory, no parent-regime
section is ever supplied, and the packets contain no ADM1/division instructions or
values. Derived prompts are **separately versioned** (`single-country-v1` in
`frozen/manifest.json`) and make no byte-identity claim against the pairwise originals.

## Inputs: pilot-only evidence view

Exact per-country packets frozen under `frozen/packets/` from
`data/countries.json` @ `80c573a5` (sha256 in the manifest) — refreshed at HEAD with
the US MAP 7-Nov-2026 facility categories and the corrected 19-Mar-2025 arrest
(GBR/NPL/VAT unchanged since the independently reviewed source fixes), with the two
GBR pilot-only edits preserved byte-for-byte. Structural path-level
whitelist of the five blind fields; scores, bands, ranks, provenance, anchors,
sub-national aggregates, named fields and source URLs excluded; the GBR third-party
index score/rank sentences replaced through two exact, evidence-preserving edits
(before/after ledger + rationale in `evidence-map.md`). Limitations and source dates
are kept, never hidden. No targets, published scores, ADM1 score/aggregates, frozen
country anchors or expected ordering enter any input; no other country's data is
read.

## Predeclared controls, interpretation limits and stop rules

* **Timing/order/repeat:** two temporal blocks, randomized and interleaved as above;
  variant/family placement balanced rather than given separate time windows; repeat
  draws test exact-input repeatability only. Fresh session per attempt.
* **No statistical claims:** 2 draws per cell cannot separate stochastic variation from
  any effect or support a variance decomposition; two families are not replicate draws
  and draw-index matching is not common random numbers. Report each cell's two outputs,
  within-cell spread and failure statuses; compare A/B and families within country
  descriptively only. **No significance, equivalence, calibrated increments, stable
  rankings, pooling away disagreement, or causal claims.**
* **Identity leaks:** no tested `COUNTRY_NAMES` literal appears in packets or labels
  (that is the full extent of the enforced check), but case captions such as "For Women
  Scotland v Scottish Ministers" and country-specific legal detail are deliberately
  retained, so identity may still be inferred (see `evidence-map.md §5`). Blinding is
  not claimed; the neutral-label sentinel does not test it.
* **Model-family correlation:** the two families may share training evidence and
  providers may drift; family disagreement is not independent replication, and model
  substitution/version drift stops the run.
* **Hard stops:** claim-level source preflight is **REQUIRED before any provider
  execution** (`preflight.md`, with the exact remaining UK/NPL/VAT/USA discrepancies);
  stop on any unverified material dossier claim, unresolved contradiction or source
  ambiguity; fix under a new frozen version, never mid-run; never stop because numbers
  look convincing; never improvise scoring rules; unknown evidence is labelled unknown
  and abstention stays allowed.
* **Review order:** semantic/evidence failures reviewed before numerical differences;
  outputs are research-only records disconnected from publication/application tooling —
  no automated score publication, no production replacement.

## Offline checks (executed during preparation)

* `python3 renderer.py --build` — **52 checks** (scope precondition, fail-closed
  derivation, prompt invariants, packet whitelist/exclusions, schedule balance,
  sentinel identity, reservation-amendment fit, static no-network/no-score-write
  scans) then freezes.
* `python3 renderer.py --verify` — **58 checks**, read-only: fresh re-derivation vs
  on-disk frozen bytes vs manifest hashes, evidence-snapshot **content** stability
  (a code/docs-only advance of HEAD with identical content passes; the recorded
  commit stays as historical provenance and content drift still fails), source-prompt
  stability, reservation-amendment recheck, in-memory tamper self-test
  (prompt/packet/schedule), no writes.
* `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_renderer` — **16 tests**, all
  passing (fail-closed edits, scale invariants, schema/abstention, A/B preservation,
  whitelist/no-scores/no-names, GBR view, schedule determinism/balance, sentinels,
  no-network statics, reservation amendment, HEAD-provenance vs content drift).
* `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_runner` — **72 mocked tests**,
  all passing and fully offline: everything in the previous set (disabled-by-default
  with no network/credential/writes, receipt/hash mismatch, source drift, non-finite
  billing and caps, output-contract validation, failed-dispatch billing and
  liabilities, prior-run gates, model substitution, ceilings, path escape, the
  40-attempt successful mock run) **plus** — the experiment-wide execution lock
  (in-process contention, a real two-process race with exactly one winner, an early
  concurrent exit while the lock is held, and a crashed holder whose lock +
  incomplete run are never deleted and block until a human reconciles);
  pre-registered probe dispatch (fixed non-country payload, one call per slot, no
  overwrite, no retry, evidence only under `probes/<slot>/`, probe flag without
  `--execute` stays disabled); probe liabilities and probe charges blocking/feeding
  the shared USD 10 ledger; the 42-dispatch combined ceiling; scoring refused before
  any call until two reviewed successful probes exist; probe-evidence tampering and
  free-text observation records rejected; and content-bound `preflight.md` /
  `preflight-signoff.md` procedure + sign-off bytes — plus the shared-budget
  mid-run regression: reviewed probes with nonzero cost, an unexpectedly costly
  first scoring response stopping at exactly one dispatch (postpaid shared
  stop and pre-dispatch reservation stop), and a non-exceeded control, with
  run-local `result.json` totals and correct shared ledger sums.

## Files

* `renderer.py` — offline deterministic builder/validator (`--build`, `--verify`).
* `test_renderer.py` — 16 targeted unit tests.
* `runner.py` — provider runner, **disabled by default** (`--execute` + signed
  `preflight_receipt.json` schema-v3 gates + experiment-wide lock; `--probe` for the
  two pre-registered probes; never executed).
* `test_runner.py` — 72 mocked, deterministic offline tests for the runner gates.
* `probe-amendment.md` — pre-registered operational probe amendment (2 probes, 42
  combined dispatches, shared USD 10 ledger, evidence/review requirements).
* `budget-amendment.md` — pre-outcome reservation amendment (70 000/2 400 000 units)
  with the honest unit/ceiling labels and the preserved original proposal.
* `evidence-preflight-amendment.md` — pre-outcome exploratory-procedure amendment
  for the exact frozen 4-country non-publishing **feasibility diagnostic only**:
  records what the independent review checked vs. left unchecked, stop rules and
  output-misuse review; **not** a receipt, sign-off or execution/production
  approval; the comprehensive claim-level gate in `preflight.md` stays in force.
* `reviews/evidence-review.md`, `reviews/budget-review.md`,
  `reviews/evidence-preflight-followup.md` — durable local copies of the
  independent reviews (the follow-up is byte-identical to the reviewer's
  written-preflight follow-up artifact) that the receipt binds.
* `preflight_receipt.json` — **deliberately absent until a reviewer signs it**
  (schema v3: binds the frozen inputs, `runner.py`, all three amendments, the exact
  `preflight.md` procedure, the distinct `preflight-signoff.md` claim-level
  artifact, `data/countries.json`, the independent reviews, and — when observing —
  hashed probe evidence; documents semantics instead of claiming `verified`).
* `preflight-signoff.md` — the coordinating assistant's feasibility-only
  procedural decision; its bytes must be bound and it is explicitly not human
  approval or a finding that all claims were verified.
* `runs/<run-id>/`, `probes/<slot>/` — created only by a successful gated run or
  probe; neither exists today (nor does `.execution.lock`).
* `ledger.json` — machine-readable before/after ledger (8 prompt edits + 2 packet edits).
* `preflight.md` — REQUIRED claim-level preflight + exact remaining discrepancies.
* `evidence-map.md` — path-level exclusions, GBR edits, ADM1/no-leak proofs.
* `frozen/single_a.txt`, `frozen/single_b.txt` — derived single-country prompts + hashes.
* `frozen/packets/{USA,GBR,NPL,VAT}.txt` — exact evidence packets + hashes.
* `frozen/schedule.json` — two-block 40-attempt schedule (seed frozen);
  `frozen/user_messages.json` — the 40 provider-visible messages + per-message sha256;
  `frozen/manifest.json` — snapshot, prompts, packets, schedule, settings, proposed
  ceilings, hashes.

## What is deliberately absent

No credentials, no results files, no scoring or score-writing path, no force-cache
or fallback requests, no CLI key parameter, no retries, no probe, no receipt, no
sign-off and no writes outside a new `runs/<run-id>/` or `probes/<slot>/` (the
`runs/`/`probes/` containers and the transient `.execution.lock` are created
alongside them; the lock is released only by its own holder and never deleted on
contention). `runner.py` exists but has never been executed: it needs the
`--execute` flag and a signed schema-v3 `preflight_receipt.json`; the receipt must
*document* provider request/response/usage/price semantics with sources, list the
residual assumptions, and record live behavior as **unobserved** (scoring then
still refuses) or as a structured, hash-bound two-probe observation — there is
deliberately **no `verified` flag** to fill in and no free-text observation is
accepted. Its byte+framing reservation is an administrative estimate, not a proven
native-token bound, and the $10 ceiling is local, not provider-enforced.