# Hash-gate / receipt verification — country-feasibility (read-only)

Base dir: `/home/meme/kóði/kort/research/experiments/country-calibration-audit/country-feasibility/`
Method: SHA-256 over raw file bytes (Python 3, `hashlib`), request hashes recomputed with the
runner serialization `sha256(json.dumps(request, sort_keys=True).encode())`. Runner functions
invoked via `PYTHONDONTWRITEBYTECODE=1 python3` importing `runner` in-process (no `--execute`,
no network, no writes, no scoring, no provider calls). Repo HEAD = `80c573a5fe205a21c34657cdbfedb0dfda2f2aab`
= `frozen/manifest.json.git_commit` = `source_commit` of both v4 receipts (match).

## Files Retrieved
1. `scoring_observation_receipt.json` (44 lines) — the v4 receipt under audit; 8-entry `probe_evidence`, 35 `bindings`.
2. `reviews/probe-slot-attestations.json` (58 lines) — four per-slot attestations with `probe_result_sha256` + `raw_response_sha256`.
3. `reviews/probe-hash-audit.md` (192 lines) — independent hash audit (bound as `independent-probe-hash-audit`).
4. `runner.py` lines 164-315 (constants/labels), 439-520 (lock/bindings), 567-735 (`verify_receipt`, `verify_probe_observation`), 959-1290 (`prior_run_state`, `prior_gate`, `total_dispatch_violation`, `original_probe_evidence_gate`, `scoring_probe_gate`), 1750-1845 (execution path), 1937/2096 (header redaction).
5. `probes/probe-{1..4}/{dispatch.json,probe-result.json,review.json}` — 12 archived records.
6. `preflight_receipt.json` (v3 archival), `probe_followup_receipt.json` (v4), `ledger.json`, `frozen/*`.

## 1. `scoring_observation_receipt.json` bindings — 35/35 MATCH
Recomputed every binding against current bytes (review labels resolved exactly as
`runner.py:294-315` `REVIEW_BINDINGS` does; `data/countries.json` at repo root):
**ok=35, mismatch=0, missing=0**. Key set is identical to `runner.current_bindings()` output
(`set(receipt.bindings) == set(runner.current_bindings(...))` → True).
Notable verified values:
- `frozen/manifest.json` `a55962ac1eba5458b3de517bdeb768f55db3a3ab6f20c10d887ab78e8692b756`
- `ledger.json` `3e3b20bc52f933f5e6928078ebf4dd067093ae1eaf0c8fedee5677811b778f43`
- `runner.py` `1a3db45e0b0e7af7f62ac74117616cfe3bae8d7eafc24a1b8add7f1dbbe767d4`
- `preflight_receipt.json` `262c698e5ddc6a104a86a6cca5eda7219c4832bb353c31e14040431b8a032600`
- `independent-probe-hash-audit` `c414b3725f79416249129e1ce418e10ab2f8157a42ce27d316d24175e677d4b7` (== current `reviews/probe-hash-audit.md`)
- `independent-probe-slot-attestations` `1285c867386c8dbfccc43b884029f8c5495d894bae6d30fca70bf5e026c6b7a0` (== current `reviews/probe-slot-attestations.json`)
- `data/countries.json` `c4a2c8339b0d389a42d8b90ec48bafab209d511185ab10e19789d29de4baebce`

## 2. Frozen input bytes — MATCH manifest and receipt
`runner.verify_frozen(manifest, root, data_path)` → OK (no exception).
Independently recomputed: `single_a.txt` `de747210956d…cc46`, `single_b.txt` `7dfdeba76b96…0ee8`,
`schedule.json` `b40d6bd87301…5f47`, `user_messages.json` `eb37081737f8…2f14`,
`packets/USA.txt` `1ba052e91d93…c1cf`, `GBR.txt` `8290d08753ea…b31c`,
`NPL.txt` `2d8bcf42f158…815b`, `VAT.txt` `1800643dd8eb…2fc1`,
`ledger.json` `3e3b20bc52f9…8f43` — all equal the manifest-declared hashes and the receipt bindings.

## 3. Eight probe-result / review SHA-256s — 8/8 MATCH
| file | recomputed SHA-256 | receipt `probe_evidence` | attestations |
|---|---|---|---|
| `probes/probe-1/probe-result.json` | `5b3bb14a03d36f11a1b5990971f60bc9102de99a8daa53a087e392fecd907ef2` | match | match (`probe_result_sha256`) |
| `probes/probe-1/review.json` | `260f7fef3aa2e12af3fa891e476e735943d2d197699b2796e8bb032cb466aff9` | match | n/a (see note) |
| `probes/probe-2/probe-result.json` | `3a55716757b6aafc9122995196f1e0df8544eab52ff62a0e3e3d0b6930ee4b19` | match | match |
| `probes/probe-2/review.json` | `202ab12e4f4e031eb5263f95fb5a01a61ed840dca72fcde31b1af9a609b03944` | match | n/a |
| `probes/probe-3/probe-result.json` | `3557d8f8f5866032686944ab7381ff34009625f6ed66304110bb9ff21c33c0a8` | match | match |
| `probes/probe-3/review.json` | `0b0a1929fbc84b2566ca41197cdccc66d27b6d51e0a68002f1f18ee5efeb3cb3` | match | n/a |
| `probes/probe-4/probe-result.json` | `88e89f431dba67fee364048d5496d4b8905fa4168d65c9d05572cbf21e0db9f4` | match | match |
| `probes/probe-4/review.json` | `08708339dc62631098cc422a39efc6b3685d127b2e6c8b53780919436de4e8ad` | match | n/a |

Also recomputed and matching:
- 4/4 request hashes (`605a8ded…`, `b09d104f…`, `c1ae299e…`, `34f6cb28…`) == each `dispatch.request_sha256` and == `reviews/probe-hash-audit.md` §1.
- 4/4 `raw_response` string hashes `12ddd307…`, `5e86f50f…`, `ee63cd91…`, `e666978e…` == attestations `raw_response_sha256` and audit §2.
- 4/4 dispatch file hashes `7ac4dd63…`, `7ef49398…`, `a41b376e…`, `9a62d935…` == audit §2 table.
- Each `review.json.probe_result_sha256` == the corresponding result file; each
  `review.json.review_source_sha256` `1285c867…` == current `reviews/probe-slot-attestations.json`.

**Note (evidence gap, not a mismatch):** `reviews/probe-hash-audit.md` contains **no**
`review.json` hashes — it explicitly states (lines 127, 183) that no `review.json` existed when
it was written. The four review hashes are therefore attested only by
`scoring_observation_receipt.json` (re-verified here against bytes) plus each review's internal
self-consistency; `probe-slot-attestations.json` carries `probe_result_sha256`/`raw_response_sha256`
only. Attestations `hash_source` points to an external session artifact
`…/outputs/2d35decd-6fa7-4a05-9aef-170d40152771/probe-final/hashes.md`, which exists (13465 bytes).

## 4. Four per-slot statements vs archived bytes — 4/4 CONSISTENT
- **probe-1** (`reviewed_ok`): request `deepseek/deepseek-v4.1-flash`, `max_tokens 64` ✓; raw provider `Relace` ✓; HTTP `200` ✓; finish `stop` / native `stop` ✓; content `{"probe": "ok"}` ✓; `status completed`, `retry false` ✓; usage 85/30 incl. 19 reasoning ✓ (`completion_tokens_details.reasoning_tokens=19`); cost `1.551e-05` = $0.00001551 ✓.
- **probe-2** (`reviewed_failure`): `google/gemini-3.8-flash`, `max_tokens 64` ✓; raw provider `Google` ✓; finish `length` / native `MAX_TOKENS` ✓; content `null` ✓; **`status` remains `stopped`, `http_status` key ABSENT (not inferred)** ✓; `errors ["probe: incomplete output - empty content"]`, `stop_reason` same, `retry false` ✓; usage 53/60, all 60 reasoning ✓; known charge `0.00026475` with `billed_on_failure.parsed=true` ✓ (not an unknown-charge case).
- **probe-3** (`reviewed_ok`): adaptive follow-up, `deepseek/…flash`, `max_tokens 2000` ✓; `dispatch.adapted_after.original_failure_slot = "probe-2"` ✓; `attempt_phase="adaptive_followup"` ✓; HTTP 200 / `stop` / content ok / completed ✓; usage 85/30 (19 reasoning) ✓; cost $0.00001551 ✓.
- **probe-4** (`reviewed_ok`): `google/gemini-3.8-flash`, `max_tokens 2000`, `adapted_after` → probe-2 ✓, dispatched 03:57:50 after probe-3 03:57:41 ✓; provider `Google`, HTTP 200, finish `stop` / native `STOP`, content ok, completed ✓; usage 53/154 incl. 148 reasoning ✓; cost $0.00061725 ✓; statement correctly does not supply probe-2's missing HTTP status.

## 5. Receipt chains in dispatch records — UNCHANGED, historical hashes intact
- `preflight_receipt.json` file SHA = `262c698e5ddc6a104a86a6cca5eda7219c4832bb353c31e14040431b8a032600` (v3, archival) — **unchanged**; equals `preflight_receipt_sha256` in **probe-1 and probe-2 `dispatch.json` AND `probe-result.json` (4/4 identical)**.
- Adaptive **pre-dispatch** receipt `probe_followup_receipt.json` file SHA = `430103f6a6c79d98b783c94779cc23c7fe1620478af01a13f020af43ec1dc54f` (v4) — **unchanged**; equals `preflight_receipt_sha256` in **probe-3 and probe-4 `dispatch.json` AND `probe-result.json` (4/4 identical)**. It is chained by those follow-up records themselves; it is not (and need not be) a `bindings` key of either receipt — `scoring_observation_receipt.json` binds only `preflight_receipt.json` among receipt files, and the v3 archival receipt predates it.
- All 4 dispatches: `manifest_sha256` == current `frozen/manifest.json` `a55962ac…` (4/4);
  `probe_amendment_sha256` == `be30bb2fd39c…bf3c` (4/4); probe-3/4
  `probe_followup_amendment_sha256` == `cb4366bd15a5…f98cd` (2/2). `retry: false` in all 8 records.
- Archival receipt itself pins the historical runner `runner.py = 2e4e09f01e65…54ac` (≠ current `1a3db45e…`) — expected, historical-pin behaviour documented in the hash audit §3.

## 6. Statuses retained
probe-2 = `stopped` with **no `http_status` key** (failure disclosure `stop_reason`/`errors` present); probe-1/3/4 = `completed` with `http_status 200`. Both adaptive follow-ups completed. Exactly four probe dirs, three files each; no attempt/log/temp files; **no `runs/` directory, no `.execution.lock`** → no pre-existing runs, no stale lock, no duplicate slots.

## 7. Costs / usage in the shared experiment-wide ledger — INCLUDED
`runner.prior_run_state()` (the shared ledger across runs+probes) reads:
`runs=[]`, `attempted={}` (0 scoring attempts), `unknown=[]`, `unreconciled=[]`,
`used_usd=0.00091302`, `used_input=276`, `used_output=274`, `probe_dispatched=4`,
`probe_slots=[probe-1..4]`.
Independent sum of the four `used_usd` = `1.551e-05 + 0.00026475 + 1.551e-05 + 0.00061725 = 0.00091302` ✓
(includes probe-2's failure charge). Reservations sum 0.010339536 USD / 1496 input units / 4128 output tokens ✓ (audit §5 figures confirmed).
`ledger.json` (the prompt-edit ledger, distinct artifact) hash `3e3b20bc…` matches manifest + receipt ✓.

## 8. Credentials in logged records — NONE
8/8 `Authorization` entries in `probes/**/{dispatch,probe-result}.json` are `"[REDACTED]"`.
Literal scan of `probes/` and all three receipts for `Bearer `, `sk-or-`, `sk-`, `api_key`,
`OPENROUTER_API_KEY` values → **zero credential values**; only source-code references
(`runner.py:135`, and the deliberately separate real header built at `runner.py:1937/2096`
`"Bearer " + secret`, which is never written to any record). No secret was printed by this run.

## 9. Read-only runner gate results (exact)
| call | result |
|---|---|
| `runner.verify_frozen(manifest, root, data_path)` | OK (no exception) |
| `runner.verify_receipt(scoring_observation_receipt.json, bindings, manifest)` | **OK** (returns None) |
| `runner.verify_receipt(preflight_receipt.json …)` (archival as execution receipt) | REFUSAL code=3: `receipt_version must be 4; bindings key set differs (missing=[independent-followup-live-block, independent-followup-original-block, independent-original-probe-review, independent-probe-followup-review, independent-probe-hash-audit, independent-probe-protocol-review, independent-probe-slot-attestations, preflight_receipt.json, probe-followup-amendment.md], extra=[])` — expected: v3 archival is never accepted |
| `runner.verify_receipt(probe_followup_receipt.json, bindings, manifest)` | **REFUSAL code=3**: `preflight receipt rejected: bindings key set differs (missing=['independent-followup-live-block', 'independent-probe-hash-audit', 'independent-probe-protocol-review', 'independent-probe-slot-attestations'], extra=[])` — see blocker below |
| `runner.verify_probe_observation(scoring_observation_receipt.json, root)` | **OK** — all 8 evidence hashes verified against bytes; `original_failure {slot: probe-2, status: stopped}` equals archived `probe-2` status |
| `runner.verify_probe_observation(probe_followup_receipt.json, root)` | OK (no observation claimed → early return) |
| `runner.prior_gate(prior, sched)` | **OK (None — no refusal)**: no unknown state, no unreconciled liability, no attempted cells |
| `runner.scoring_probe_gate(prior, root, bindings)` | **OK (None)** — all four slots dispatched, original statuses pinned (probe-2 `stopped`), both follow-ups `completed`, all four `review.json` valid with expected statuses |
| `runner.original_probe_evidence_gate(root, bindings)` (supporting) | OK (None) |
| `runner.total_dispatch_violation(prior, ATTEMPT_CEILING=40)` | **OK (None)** — 0 prior scoring + 4 probes + 40 planned = 44 ≤ 44 |
| `runner.total_dispatch_violation(prior, 1)` | OK (None) |

## Blockers / discrepancies
1. **BLOCKER for default execution path (not for this audit):** `runner.RECEIPT_NAME` is
   `probe_followup_receipt.json` (`runner.py:166`), and **`verify_receipt` REFUSES it** — the
   current `REVIEW_BINDINGS` (runner.py:294-315) requires four review labels the receipt does
   not bind (`independent-probe-hash-audit`, `independent-probe-slot-attestations`,
   `independent-probe-protocol-review`, `independent-followup-live-block`). Any future run must
   therefore pass `--receipt scoring_observation_receipt.json` (which passes all gates) or the
   follow-up receipt must be reissued; running with defaults fails closed at `runner.py:1788`.
   `scoring_observation_receipt.json` also passes `verify_probe_observation`, which the follow-up
   receipt cannot (its `live_behavior.status` is `unobserved`).
2. **`reviews/probe-hash-audit.md` content is stale vs the current archive**, though its bound
   SHA `c414b372…` matches the receipt exactly: it states no `probes/*/review.json` exists
   (lines 127, 183 — they now exist and are receipt-bound), says "current runner.py =
   c9a227f1…" (current is `1a3db45e…`), and reports both receipts as `unobserved` (the scoring
   receipt now claims `observed_in_bounded_probe`). Its factual probe hashes all re-verify; it
   simply predates the review artifacts, so the four **review** SHA-256s have no independent
   audit-side attestation (they are attested only by the receipt, re-verified here).
3. Archival `preflight_receipt.json` pins `runner.py = 2e4e09f0…` ≠ current `1a3db45e…`
   (historical pin; expected, per audit §3).
4. Attestations' `hash_source` lives outside the repo (session artifact path); it exists today
   but is not content-bound by the receipt.

## Residual risks
- Verification is local-byte only: nothing here attests provider-side behavior, billing
  reconciliation, token bounds, or scoring validity (per each dispatch's `scope` field).
- probe-1/probe-3 identical usage figures rely on distinct response ids/timestamps for
  non-duplication; probe-2 has no HTTP status (prior P1 open, honestly retained).
- No scoring, no edits, no network/provider calls were made; `git status` shows only the two
  untracked experiment dirs (nothing staged, no runs, no lock).

```acceptance-report
{
  "criteriaSatisfied": [
    {"id": "criterion-1", "status": "satisfied", "evidence": "All 35 receipt bindings, 8 frozen inputs, 8 probe-result/review hashes, 4 request hashes, 4 raw_response hashes, both receipt chains, all four per-slot statements, ledger totals and credential redaction independently recomputed; the five runner gates run read-only with exact outputs reported; one blocker (default receipt refused by verify_receipt) and residual risks listed."}
  ],
  "changedFiles": [],
  "testsAddedOrUpdated": [],
  "commandsRun": [
    {"command": "sha256sum over receipts, probes/*/{dispatch,probe-result,review}.json, reviews/*, frozen/*, ledger.json, runner.py", "result": "passed", "summary": "all 8 probe-result/review SHAs + both receipt SHAs + audit/attestation SHAs matched receipt and attestation records"},
    {"command": "python3 binding recompute (35 bindings of scoring_observation_receipt.json)", "result": "passed", "summary": "ok=35 mismatch=0 missing=0; key set equals runner.current_bindings()"},
    {"command": "runner.verify_frozen(manifest, root, data_path)", "result": "passed", "summary": "OK, no exception"},
    {"command": "runner.verify_receipt(scoring_observation_receipt.json, bindings, manifest)", "result": "passed", "summary": "OK"},
    {"command": "runner.verify_receipt(probe_followup_receipt.json, bindings, manifest)", "result": "failed", "summary": "REFUSAL code=3: bindings key set differs, missing 4 independent-* review labels (blocker for default execution path)"},
    {"command": "runner.verify_receipt(preflight_receipt.json as execution receipt)", "result": "failed", "summary": "REFUSAL code=3 expected: v3 archival receipt is never accepted as execution receipt"},
    {"command": "runner.verify_probe_observation(scoring_observation_receipt.json, root)", "result": "passed", "summary": "OK, 8/8 evidence hashes + original_failure probe-2/stopped verified against archived bytes"},
    {"command": "runner.prior_gate(prior, sched)", "result": "passed", "summary": "None - no unknown state, no unreconciled liability, no attempted cells"},
    {"command": "runner.scoring_probe_gate(prior, root, bindings)", "result": "passed", "summary": "None - 4 slots dispatched, probe-2 stopped retained, both follow-ups completed, 4 valid review.json"},
    {"command": "runner.total_dispatch_violation(prior, 40) and (prior, 1)", "result": "passed", "summary": "None both - 0+4+40=44 <= ceiling 44"},
    {"command": "runner.original_probe_evidence_gate(root, bindings)", "result": "passed", "summary": "None - receipt chain intact for probe-1/probe-2"},
    {"command": "grep credential patterns over probes/ and receipts", "result": "passed", "summary": "8/8 Authorization entries [REDACTED]; zero Bearer/sk- values in logged records"}
  ],
  "validationOutput": [
    "bindings: ok=35 mismatch=0 missing=0 total=35",
    "verify_receipt(scoring receipt): OK",
    "verify_receipt(followup receipt): REFUSAL code=3 missing=['independent-followup-live-block','independent-probe-hash-audit','independent-probe-protocol-review','independent-probe-slot-attestations']",
    "verify_probe_observation(scoring receipt): OK",
    "prior: runs=[] attempted={} unknown=[] unreconciled=[] used_usd=0.00091302 probe_dispatched=4",
    "prior_gate: None | scoring_probe_gate: None | total_dispatch_violation(40): None",
    "probe-2: status=stopped, http_status key absent; probe-1/3/4: completed, http_status=200"
  ],
  "residualRisks": [
    "probe-hash-audit.md bytes are bound correctly but its prose is stale (no review.json hashes, outdated current-runner hash, reports both receipts unobserved) - the four review SHA-256s have no audit-side attestation, only the receipt (re-verified here)",
    "archival preflight_receipt.json pins historical runner.py 2e4e09f0... != current 1a3db45e... (expected historical pin)",
    "attestations hash_source points to an external session artifact outside the repo/content-binding",
    "verification is local-byte only: no provider-side behavior, billing reconciliation or scoring validity attested",
    "probe-2 has no HTTP status (prior P1 open, honestly retained; failure disclosed via stop_reason/errors)"
  ],
  "noStagedFiles": true,
  "diffSummary": "No files changed; read-only audit (python run with PYTHONDONTWRITEBYTECODE=1, no --execute, no network). git status shows only the two untracked experiment directories.",
  "reviewFindings": [
    "blocker: runner.py:1788 - default receipt probe_followup_receipt.json is refused by verify_receipt (bindings key set missing 4 independent-* labels added after it was issued); scoring_observation_receipt.json passes every gate and must be passed via --receipt for any future run",
    "finding: reviews/probe-hash-audit.md lines 127/183 claim no probes/*/review.json and an outdated current runner hash - content stale though its bound SHA c414b372... matches",
    "no other blockers: 35/35 bindings, 8/8 result+review hashes, 4/4 statements, both receipt chains, ledger totals and redaction all verified"
  ],
  "manualNotes": "Nothing was edited, staged, or dispatched; no scoring performed. Ledger aggregation (prior_run_state) confirms all four reported charges (0.00091302 USD incl. probe-2 failure) and 276/274 tokens are in the shared experiment-wide ledger; no runs/ dir and no .execution.lock exist. The only actionable blocker is the default-receipt key-set drift in §9, which fails closed before any dispatch."
}
```