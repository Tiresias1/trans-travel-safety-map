# country-feasibility-v2 — stage-one protocol and preflight

**Status: prepared offline; NOT executed. No preflight receipt exists. No live
call has been made and none is authorized by this document. The independent
methodology, code and evidence reviews this protocol requests are absent until
produced; `runner.py` refuses fail-closed until a reviewed receipt binds them.**
Prepared in `research/experiments/country-calibration-audit/country-feasibility-v2/`
at repo commit `80c573a5`, after the closed v1 run. Nothing under
`country-feasibility/`, `rule-contrasts/`, `data/`, `tools/` or the UI was
edited; v1 files remain byte-identical (verified by tree digest in tests).

## 1. Chronology, adaptation and disclosures

- **v1 is closed.** `country-feasibility-20261108-v1` attempted exactly one of
  40 cells (USA, variant B, `deepseek/deepseek-v4.1-flash`, core). It returned
  **no final score**: empty assistant content, `finish_reason: length`. The run
  stopped; 39 cells were never attempted; its zero-retry contract is neither
  resumed nor amended. Its failed attempt, four prior probes, amendments,
  reviews and costs are preserved unchanged.
- **Partial-reasoning exposure (disclosed).** The preserved v1 failure record
  contains provider partial reasoning text with **provisional numerical
  musings**, visible to reviewers. No such provisional number is reproduced in
  any v2 material, and none was used to select countries, models, prompt
  wording, schedule, sentinels or settings. Exposure to that text is an
  adaptation-bias risk that preregistration here limits but does not erase;
  every attempt and configuration of v2 must be reported, successful or not.
- **Explicitly adaptive stage.** v2 is designed after inspecting the v1
  failure and the independent semantic, data and recovery reviews. It is a new
  version (new directory, manifest, receipt) and cannot satisfy or retroactively
  amend v1. Success means predeclared operational and evidence-fidelity
  criteria only. **No desired score, band or ordering is stated anywhere.**
- **Review advice incorporated** from the independent recovery review and its
  accounting addendum: exact Decimal reconstruction of prior charges, smallest
  useful bounded stage, one predeclared settings change, no causal claim about
  it, disclosure of partial-reasoning exposure, and independent pre-dispatch
  methodology/code/evidence review as a hard gate.

## 2. Stage-one design (frozen before any outcome exists)

Exactly **20 attempts maximum** (`frozen/schedule.json`, fixed offline; never
re-randomized or reordered after any dispatch):

- **16 core cells**: 4 countries (USA, GBR, NPL, VAT) × 2 exact model ids
  (`deepseek/deepseek-v4.1-flash`, `google/gemini-3.8-flash`) × 2 reviewed
  prompt variants (A, B) × **1 draw**.
- **4 anonymous empty-dossier sentinels**: model × variant (case `""`,
  `DOSSIER` label), for abstention/empty-evidence behavior under the unchanged
  output contract. **Context-aware semantic rule (mechanical): an EMPTY
  dossier must return `status: insufficient_evidence` with `score: null`;
  any other output stops the run fail-closed.** Core cells keep the unchanged
  contract (`score: null` remains permitted there; no score is ever forced).
- One fixed **randomized interleaved** order in **2 balanced blocks of 10**
  (generation method, seed `country-feasibility-v2-stage1` and constraints are
  recorded inside `frozen/schedule.json`; each block: 8 core + 2 sentinels,
  every country exactly 2 core, every model 5 rows, every variant 5 rows,
  sentinels not at block edges and not adjacent, country pairs non-adjacent).

**What this reduced design cannot do (stated limits):** one draw per cell
**cannot estimate within-cell repeat variance**; without neutral-label
(NEUTRAL-7) cells it **cannot test label invariance**; and nothing in this
stage **validates country rankings** or comparative calibration. It is a
feasibility diagnostic only, producing preserved research outputs — never
production ratings.

**Selection freeze:** countries, models, prompt candidates (the reviewed v1
A/B single-country prompts), schedule, sentinel family and settings are fixed
in the frozen files and this manifest *before any v2 outcome exists* and may
not be changed after dispatch begins.

**Execution granularity (pre-registered before outcomes):** each `--execute`
invocation dispatches **at most ONE next scheduled cell** under the shared
lock, appends its immutable evidence, and then pauses until an independent
reviewer records a **PASS** for that answer (§5A). The 20-cell schedule, both
A/B variants and every ordering rule above are untouched — only the spacing
between calls changes. **Disclosed limitations of this strict path:**
stopping is **outcome-dependent** (the observed sample truncates at the first
failed review or failed call), **partial outputs** are expected (a stopped
stage leaves unattempted cells — absence of data is not absence of effect),
and neither is cured by predeclaration. No publication of scores, rankings or
"unbiased comparisons" follows from any subset of survivors.

## 3. Inputs and rubric preservation (unchanged)

- The **exact v1 single-country prompt bytes** (`frozen/single_a.txt`,
  `frozen/single_b.txt`, SHA `de747210…`/`7dfdeba7…`) and the **exact v1
  evidence-message bytes** (embedded per row in `frozen/user_messages.json`,
  each row cross-checked against the pinned v1 `user_messages.json` source
  row). The runner verifies byte-identity **both ways**: on-disk bytes must
  match the manifest, and the manifest's recorded prompt hashes must equal the
  pinned v1 originals — so a prompt **plus** manifest co-tamper also refuses.
- **Data-only evidence**: `data/countries.json` (pinned SHA `c4a2c833…`)
  through the reviewed path-whitelist derivation already used by v1. **No
  published scores, no bands/ranks/provenance values and no sub-national
  (ADM1) data are inputs. No new or edited evidence.**
- **Rubric unchanged** (byte-identical prompts), explicitly preserving:
  **0.00 means a trans visitor who is outed faces near-certain imprisonment AND
  likely execution**; **no passing/stealth/concealment credit** (and no credit
  for silence or avoidance); **`unknown` intermediates are never resolved
  toward the midpoint or toward safety** — absence of evidence is not safety.
- Output contract unchanged: bare JSON, `status ∈ {ok, insufficient_evidence}`,
  finite `score` in [0,1] or `score: null`, plus `why`, `evidence_ids`,
  `discovery`, `direct_harms`, `scope_triggers`, `uncertainty`.

## 4. The single predeclared generation-settings change (+ transport-only note)

v1 requested `temperature 1.0, top_p 1.0, max_output_tokens 2000` and no
explicit reasoning parameter. v2 preserves all of that **except
`max_output_tokens: 2000 → 11000`**, the **sole generation-settings change**,
and still requests **no explicit reasoning parameter** (because v1 had none).
Basis: the prior, *separate* pilot2 instrument obtained **95/96 parseable
logical calls at an 11000-token allowance** — operational precedent for
choosing one cap once, **explicitly not a guarantee of success, not proof that
the 2000 cap caused the v1 failure, and not semantic validation**. 11000 is
the maximum billed output per call **including any reasoning tokens**. Limits
will not be raised again based on how outputs look; any further adaptation
requires a separately bounded, disclosed, reviewed version.

**Transport-only adjustment (not a generation setting):** the chat-request
socket timeout is predeclared as **300 s** (v1 used 30 s; the price-fetch
fetch stays 30 s). Recorded because the pinned `call-001` took **28 s for
only 2000 completion tokens** and still ended `length` — an 11000-token
non-streaming response plausibly needs minutes of server-side silence, and a
30 s abort would return no raw body → unknown charge → permanent
unreconciled liability. Timeout behavior stays **fail-closed**: a socket
timeout raises a transport-error refusal, stops the stage before any further
dispatch, and an unknown charge remains an unreconciled liability.

## 5. Dispatch protocol and immediate stop conditions

- Fixed HTTPS endpoint `https://openrouter.ai/api/v1/chat/completions`
  (prices from the fixed `/models` endpoint after all gates); **exact model
  ids; sequential fresh system+user contexts built only from frozen bytes; one
  attempt per predeclared cell; ZERO retries; no fallback model list; no
  force-cache directive; no dynamic input; predeclared 300 s chat-request
  timeout (transport-only, §4); **ONE cell per invocation with the
  per-answer semantic checkpoint of §5A before any later call.**
- **Cache policy (frozen per the separate semantic-process consult):** the
  request **never carries cache-control directives** and the runner never
  warms, forces or busts cache. **Provider-initiated cache READ tokens are
  accepted** when the reported usage/cost arithmetic is valid (`cached_tokens
  ≤ prompt_tokens`, integers, consistent totals, finite cost within the
  reservation) and are **logged in full as an execution condition — with no
  reproducibility or uncached-performance claim** (token counts alone do not
  identify provenance; provider cache state is uncontrolled). Any nonzero
  **cache WRITE** count **stops the stage**: write billing cannot be
  reconciled with the advertised prices this runner fetches, so it is never
  assumed free.
- **Predeclared routing**: provider must be `Relace` for DeepSeek and `Google`
  for Gemini (the providers observed in all five reviewed prior records);
  anything else or a missing attribution is unexpected routing → stop.
- **Strict validation stops the whole stage immediately** (first-stop; every
  attempt and the decoded response text — UTF-8 with replacement, so exact
  response text but not byte-exact transport bytes — preserved once, tentative
  values never interpreted) on any of:
  1. failed/empty/truncated/invalid output (including non-`stop`
     `finish_reason`, non-strict JSON, contract violations, `score` outside
     [0,1] or non-finite);
  2. API error (HTTP ≠ 200 or an `error` object);
  3. provider mismatch (model substitution) or unexpected routing;
  4. unknown or inconsistent billing/usage: missing/non-finite/zero cost for
     billed tokens, `total ≠ prompt+completion`, `is_byok ≠ false`, **cache
     WRITE tokens or cache counts exceeding `prompt_tokens` (unreconcilable
     cache accounting — see the cache policy above; valid cache READs do not
     stop)**, missing or inconsistent **reasoning-count semantics**. The
     bound `reasoning_tokens ≤ billed completion` (with `reasoning_tokens`
     present and ≥ 0) is a **predeclared fail-closed assumption, not an
     observation**: the pinned v1 failure record itself reported
     `reasoning_tokens 2504 > completion_tokens 2000`, which is exactly why
     inconsistent counts stop the run instead of being reconciled silently;
  5. **empty-dossier sentinel semantic failure (TERMINAL)**: a
     `sentinel: empty` cell returning anything other than
     `status: insufficient_evidence` with `score: null` (context-aware
     mechanical check; core cells may abstain or score under the unchanged
     contract);
  6. reservation/budget/integrity breach (billed input > byte+framing
     reservation, billed output > 11000, billed cost > the call's worst-case
     reservation, aggregate ceilings, attempt/dispatch/USD ceilings);
  7. receipt, lock, hash or other integrity failure (stale/incomplete state).
- On failure the invocation stops terminally before any further dispatch of
  this stage; there is no retry, regeneration or replacement cell and no
  fallback. An unparseable charge is an **unreconciled liability** (never
  treated as zero) and blocks any further v2 dispatch.

## 5A. STRICT per-answer semantic checkpoint (pre-registered before outcomes)

Adopted **per-answer, not batched**, per the independent method review's
literal requirement ("a score-independent semantic checkpoint BEFORE every
subsequent dispatch") and the semantic-process consult's stricter option.
Batch review was explicitly rejected for this stage.

**Flow (enforced by `runner.py`, fail-closed, before price fetch, credential
read or any network access):**

1. **One call per invocation.** Prior attempts must be exactly the contiguous
   prefix `{1..k}` of the frozen schedule (no skip, no reorder, no rerun —
   re-dispatching an attempted cell is impossible); the invocation may
   dispatch only call `k+1`, and only while `k < 20` and `5 + k + 1 ≤ 25`.
2. **Score-blind sidecar.** Right after a successful answer the runner writes
   `runs/<run-id>/semantic-inputs/call-NNN.json`: the output **without the
   numeric `score` key** — `status`, `why`, `evidence_ids`, `discovery`,
   `direct_harms`, `scope_triggers`, `uncertainty` copied **verbatim (no
   prose rewriting, no rounding, no selection)** — plus the exact frozen
   dossier reference (`system_prompt_sha256`, `user_message_sha256`,
   `source_v1_call`). The full raw response (with score) is preserved
   separately as evidence; reviewers are pointed at the sidecar.
3. **Independent review record** — written **only by a human/model reviewer**,
   never by this runner (no code path writes `semantic-reviews/`; a PASS can
   never be forged or auto-authored) at
   `runs/<run-id>/semantic-reviews/call-NNN.json`:
   `{review_version: 1, verdict: PASS|FAIL|UNCERTAIN, response_sha256,
   sidecar_sha256, user_message_sha256, system_prompt_sha256,
   rubric_version (= RUBRIC_VERSION, the pinned single_a/single_b hashes),
   reviewer: {name, session}, reviewed_at, statement}`. The reviewer checks
   **source fidelity against the exact frozen dossier** (invented evidence,
   proposed→implemented drift, conditional triggers as universal, concealment
   credit, uncertainty asserted as fact, status/explanation contradiction)
   **without any preferred numerical value or ranking** — reviews carrying a
   `score`/`rank`/`band` key are rejected structurally.
4. **Gate.** Every earlier completed output must have a review whose hashes
   **recompute equal** to the preserved attempt/sidecar bytes. The gate
   **re-reads the immutable frozen inputs for that call** (the schedule row,
   the exact message bytes re-hashed, and both prompt files re-hashed against
   their pinned v1 digests) and requires the attempt record's
   `user_message_sha256`/`system_prompt_sha256`/`source_v1_call`, the
   sidecar's `frozen_dossier` bindings and the review's message/prompt hashes
   **all to equal those frozen digests** — never merely to agree with each
   other inside the writable `runs/` directory — plus the attempt's
   `preflight_receipt_sha256` must equal the current invocation's receipt
   hash (the receipt binds `frozen/schedule.json`, `frozen/user_messages.json`
   and both prompt files, so the whole chain is receipt-anchored).
   **Additionally, the gate strictly re-parses each preserved raw provider
   response, validates the extracted assistant content under the existing
   frozen output contract, and requires it to equal the record's
   `parsed_output` exactly *before* the score-blind sidecar is derived** —
   so record/sidecar/review cannot diverge from the stored raw output while
   `raw_response` stays unchanged; malformed, missing or mismatched raw
   output stops the stage before price/credential/network access. A
   mutually consistent edit of record + sidecar + review therefore still
   refuses.

   **Precise guarantee and non-cryptographic limit (integrity, not a new
   semantic classifier or rating rule):** the gate detects any *inconsistent*
   edit among the writable attempt/sidecar/review artifacts relative to the
   preserved raw-response text and the receipt-bound frozen inputs. It is
   **not** cryptographic authentication — SHA-256 values are equality
   cross-checks, not signatures or MACs; an actor able to rewrite `runs/`
   could rewrite `raw_response` and its recorded hash consistently, and the
   reviews and receipt remain self-asserted artifacts (disclosed in §7).
   **Missing, FAIL, UNCERTAIN, tampered, or a prior FAILED/partial
   attempt blocks ALL later calls** (the stage pauses or ends; recovery
   requires a new, separately disclosed and reviewed version — never a
   retry). Acceptance never depends on any model score. The verified reviewer
   identity/session and review hashes are recorded in the next `run.json`.
5. A successful final (20th) call ends dispatching; the stage's disposition
   is determined by the independent review of that answer — no batch follows.

**Limitations (disclosed, not curable here):** per-answer stopping is
**outcome-dependent**; **partial outputs** (unattempted cells) are the normal
state after any stop; reviews are human/model judgments that reduce but do
not eliminate discretion or error; dossiers may be recognizable (anonymization
is imperfect). None of this authorizes publication, ratings, rankings or
travel advice.

## 6. Accounting, budgets and lock

- **Prior liability, exact:** reconstructed with `decimal.Decimal` directly
  from the four original `probes/probe-N/probe-result.json` files and v1
  `attempts/call-001.json` `billed_on_failure`:
  0.00001551 + 0.00026475 + 0.00001551 + 0.00061725 + 0.001080256 =
  **USD 0.001993276** (276+13376 = 13 652 input, 274+2000 = 2 274 output
  tokens, 5 dispatches). Provider response ids are pinned and **deduplicated**;
  every consumed record's raw SHA-256 is independently re-checked; missing,
  unknown, duplicated or drifted records stop before dispatch. v1's *rounded*
  summary fields (0.00108 + 0.000913 = 0.001993) are display-only and never
  used for budgeting. v1 data is never written.
- **Combined limits:** all **5 previous dispatches + at most 20 new = 25**
  maximum; all costs — prior exact decimals plus new charges — against the
  **same USD 10.00 locally enforced guard**. There is **no provider-side hard
  spend guarantee**; the guard is checked between calls only, so **one
  in-flight (postpaid) call can overshoot the local guard before the next
  check** — an accepted, disclosed risk bounded per call by the reservation
  arithmetic. Unknown prices or usage refuse rather than guess.
- **Input reservation:** UTF-8 bytes of frozen prompt+message **+ a fixed
  128-unit chat-framing allowance per call** — an **assumption stated for
  conservative accounting, explicitly NOT a guaranteed provider tokenizer
  bound** (predeclared plan: 66 609 units max per call, 1 112 686 aggregate;
  ceilings 70 000 / 1 400 000). Billed input above its reservation stops.
- **Output budgets kept separate, exact integers, never merged or rounded:**
  historical v1/probe budgets (80 000 aggregate scoring proposal; 4 128 probe
  allowance; 2 274 output tokens actually used) vs the **new v2 reservation of
  220 000 tokens (20 × 11 000)**.
- **One shared exclusive lock:** `../country-feasibility/.execution.lock` —
  the same file and `O_EXCL` mechanism the v1 runner used — acquired **before
  any ledger or prior state is read**, held through dispatch and
  finalization. Contention or a stale lock refuses before any call; only its
  own holder ever removes it; it is the sole permitted transient write outside
  this v2 directory. Stale or incomplete run state fails closed: never
  overwritten, never retried, evidence never deleted.

## 7. Preflight checklist for independent reviewers (receipt schema 1)

Execution requires `preflight_receipt_v2.json` (absent until reviewed) with:

1. `receipt_version: 1`, `receipt_kind:
   "country-feasibility-v2-stage1-execution-receipt"`;
2. `preflight: {status: "signed_off", document: "protocol.md", reviewed_by,
   reviewed_at, statement}` — non-empty;
3. `prior_accounting: {total_usd: "0.001993276", dispatches: 5,
   input_tokens: 13652, output_tokens: 2274, record_ids: [the five pinned
   provider ids]}`;
4. `bindings` — exact label → SHA-256 map, no more and no fewer, over:
   - **inputs**: `frozen/manifest.json`, `frozen/schedule.json`,
     `frozen/user_messages.json`, `frozen/single_a.txt`, `frozen/single_b.txt`;
   - **protocol**: `protocol.md`;
   - **code**: `runner.py`, `test_runner.py`;
   - **source data**: `data/countries.json` and all 26 pinned `v1/…` source
     records (v1 frozen inputs, ledger, v1 runner, the v1 run record, the
     failed attempt, and every probe dispatch/result/review);
   - **independent reviews (absent until produced)**:
     `independent-methodology-review` → `reviews/methodology-review.md`,
     `independent-code-review` → `reviews/code-review.md`,
     `independent-evidence-review` → `reviews/evidence-review.md`.

Reviewers should verify: schedule balance/interleave and pre-outcome freeze;
byte-identity of prompts/messages to v1 **including the prompt+manifest
co-tamper cross-check**; the sole generation-settings change and the
transport-only timeout disclosure (300 s / 30 s); **the §5A checkpoint (one
call per invocation, sidecar score-blindness, review schema, hash rebinding,
verdict handling, no review-writing code path)**; all stop conditions
(including the empty-sentinel terminal rule, the reasoning-count assumption
and the cache policy above); Decimal prior accounting against the raw
records; ceiling arithmetic (20/25/USD 10/11 000/220 000/70 000/1 400 000)
**aggregated across invocations**; the shared lock path and release semantics
**including the two-process contention/race results**; test coverage and
offline-only test execution; and the disclosures in §1–§2. Binding bytes is
not execution approval and weakens no gate.

**Open blockers (explicitly unresolved, not invented here):**

1. The §5A checkpoint is implemented only as a fail-closed **dispatch gate**.
   The actual per-answer **review verdicts do not exist yet** — each is a
   separate human/model judgment under independent consultation, recorded
   with real reviewer identity/session; nothing in this repo may substitute
   for, forge or auto-author one. Any receipt must bind the independent
   methodology/code/evidence reviews of this very design.
2. **Cache policy** now follows the separate consult (§5): no directives,
   valid provider-initiated reads accepted and logged without reproducibility
   claims, cache-write billing that cannot be reconciled with advertised
   prices stops the stage. Any future relaxation needs its own disclosed,
   reviewed amendment and must not be done reactively after a stop.
3. The three review artifacts bound by the receipt
   (`reviews/methodology-review.md`, `reviews/code-review.md`,
   `reviews/evidence-review.md`) and `preflight_receipt_v2.json` itself remain
   absent; dispatch must stay impossible until they exist and verify.

## 8. Honest stop

This worker creates no receipt, no review and no live call. If the required
independent reviews and receipt cannot be produced, `runner.py` must remain
unexecuted — stop honestly rather than weaken a gate. No production score
publication is contemplated from this stage under any outcome.