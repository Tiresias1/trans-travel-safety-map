# Independent hash / record verification — country-feasibility probes

Read-only local verification. No edits, no network, no provider calls, no scoring,
no credential output. Base directory (relative paths below):
`/home/meme/kóði/kort/research/experiments/country-calibration-audit/country-feasibility/`

Hashing method: SHA-256 over UTF-8 bytes. Request hashes recomputed with the exact
runner serialization `sha(json.dumps(payload, sort_keys=True).encode("utf-8"))`
(`runner.py:2110–2112`), Python 3.14.8, default separators `", "` / `": "`,
`ensure_ascii=True`. File SHAs computed over raw file bytes.

## 1. Request SHA-256 recomputation (all four match their `dispatch.json`)

| slot | recorded `request_sha256` | recomputed | match |
|---|---|---|---|
| probe-1 | `605a8dedf6721c0e7b23c8fa71b652b26356b206d87d96725efbd30efa99ff11` | `605a8dedf6721c0e7b23c8fa71b652b26356b206d87d96725efbd30efa99ff11` | YES |
| probe-2 | `b09d104f2484d35482bc52da303dcefd4a1c7f1271807084e072109ac159a33d` | `b09d104f2484d35482bc52da303dcefd4a1c7f1271807084e072109ac159a33d` | YES |
| probe-3 | `c1ae299ed7510d42093f9eabecb61d89aad65ec84f02a7cbcabe2d74b625ffce` | `c1ae299ed7510d42093f9eabecb61d89aad65ec84f02a7cbcabe2d74b625ffce` | YES |
| probe-4 | `34f6cb28d1490f5c1f52e1778b6cfba63d6609eb17f027632b4dbb85d569d8e6` | `34f6cb28d1490f5c1f52e1778b6cfba63d6609eb17f027632b4dbb85d569d8e6` | YES |

Serialization-sensitivity controls (do NOT match, confirming the recorded hashes are
specifically the sorted, default-separator form):
probe-1 unsorted `3295230dc60e162f0bee715c40608c510c81ff1386c428b3a552eb49023675dc`,
compact `ced9ed745312abf57e906012db53952ffd948092ffb5142eea080843f285bdb3`;
probe-2 unsorted `6944104a03097367277802b8ecab08f3bab15dd5bf6b174aa431f597993e0bf2`,
compact `fe172c19eba05972f0a56dab775b70a9d7e3bec2d985fb0490fc1e2a062339f1`;
probe-3 unsorted `ba06da85db137fd2037e616039ba9fe6a4bd0064ec6e7292c552a26cd285a733`,
compact `e7b6ae09ccf4e757382ac202eaef1e18f4e9d36ea30971b7d354b09faed9337d`;
probe-4 unsorted `b3cbb2de486a5d5b7ae1f3aed48fd8ab62ca1ba2f81923cba193cc204ca2f36e`,
compact `a15e59833dd28b5d91664eb5091ae8d71c533c9fd046817ea305352977b706af`.

## 2. File SHA-256 (raw bytes)

| file | sha256 |
|---|---|
| `probes/probe-1/dispatch.json` | `7ac4dd6319b1533ae563fb94d01422801d08d597e6dcf2e595deec4677ab3da1` |
| `probes/probe-1/probe-result.json` | `5b3bb14a03d36f11a1b5990971f60bc9102de99a8daa53a087e392fecd907ef2` |
| `probes/probe-2/dispatch.json` | `7ef49398c1bfa53aa028e3109fb45f79587183cefde4d571f118a30ec4a3bdcf` |
| `probes/probe-2/probe-result.json` | `3a55716757b6aafc9122995196f1e0df8544eab52ff62a0e3e3d0b6930ee4b19` |
| `probes/probe-3/dispatch.json` | `a41b376e7c0ba6bca22b7ae5d992ceba30ec9ffe113df71c613f334e0170b7e3` |
| `probes/probe-3/probe-result.json` | `3557d8f8f5866032686944ab7381ff34009625f6ed66304110bb9ff21c33c0a8` |
| `probes/probe-4/dispatch.json` | `9a62d935b6e3d2a998642d296aa7d3076628ea8354ee3860bc8f2c6cef406f54` |
| `probes/probe-4/probe-result.json` | `88e89f431dba67fee364048d5496d4b8905fa4168d65c9d05572cbf21e0db9f4` |

SHA-256 of each archived `raw_response` string (UTF-8 of the stored value, including
its leading `"\n         \n"` prefix):

| slot | raw_response sha256 |
|---|---|
| probe-1 | `12ddd307756e8a45ff51c213bf58200cf4258276e54a41b0dbb99104b31f859b` |
| probe-2 | `5e86f50f2173b77bc3134a2c1cd123df3a0eb00afebf99a5c1791278b4f12225` |
| probe-3 | `ee63cd915b9649d751eaa8c9d069eee1997abea9b860e59a71a83ce2864a0440` |
| probe-4 | `e666978e0b9e9b14d3433eabb9379f8bfa8f8e4d8d94c80de2446d6ec6c6d223` |

No such digests existed in the archive before this run; these are newly computed
attestations (the prior review could not supply them — see §7).

## 3. Receipt hashes vs both records

| artifact | computed file sha256 | cited by |
|---|---|---|
| `preflight_receipt.json` (v3, archival) | `262c698e5ddc6a104a86a6cca5eda7219c4832bb353c31e14040431b8a032600` | probe-1 dispatch+result, probe-2 dispatch+result (all four fields identical); also bound inside `probe_followup_receipt.json` |
| `probe_followup_receipt.json` (v4) | `430103f6a6c79d98b783c94779cc23c7fe1620478af01a13f020af43ec1dc54f` | probe-3 dispatch+result, probe-4 dispatch+result (all four fields identical) |

Every `preflight_receipt_sha256` in `dispatch.json` equals the one in the matching
`probe-result.json` (4/4), and each equals the recomputed SHA of the file it names.

Other bound values, all recomputed and matching across every record that cites them:
- `frozen/manifest.json` = `a55962ac1eba5458b3de517bdeb768f55db3a3ab6f20c10d887ab78e8692b756` (4/4 dispatches + 2 receipts)
- `probe-amendment.md` = `be30bb2fd39c387043beff96f4830048c9a9118d22a3332e7c95a9914fd6bf3c` (4/4 dispatches + 2 receipts)
- `probe-followup-amendment.md` = `cb4366bd15a5f03c25ca8620def33494714325b182b6612909f2db4555af98cd` (probe-3, probe-4 dispatches + follow-up receipt)

Receipt `bindings` re-verification against current bytes:
- `preflight_receipt.json`: 16 path bindings OK, 8 `independent-*` review-label bindings OK (resolved to `reviews/*.md` via `runner.py:294–307`), `data/countries.json` OK at repo root
  `/home/meme/kóði/kort/data/countries.json` = `c4a2c8339b0d389a42d8b90ec48bafab209d511185ab10e19789d29de4baebce`.
  **1 mismatch: `runner.py` bound as `2e4e09f01e6585a8df8a382fa3c65af51a05442fe74a2f4c584a65309d3c54ac`, current file is `c9a227f1ff2657a2ea4d0cad77563592a9923c8eb13f2b745247c3ea6f6f0c42`.** Expected: the archival v3 receipt pins the runner as it was for the original phase; the runner was later amended for the follow-up phase (see §6).
- `probe_followup_receipt.json`: 19 path bindings OK, 11 `independent-*` review-label bindings OK, `data/countries.json` OK, and its `runner.py` binding `c9a227f1ff2657a2ea4d0cad77563592a9923c8eb13f2b745247c3ea6f6f0c42` matches current bytes. 0 mismatches.

## 4. Request parameters (exact)

| slot | request `model` | `max_tokens` | temp | top_p | stream | usage | provider |
|---|---|---|---|---|---|---|---|
| probe-1 | `deepseek/deepseek-v4.1-flash` | 64 | 0.0 | 1.0 | false | `{"include": true}` | `{"allow_fallbacks": false}` |
| probe-2 | `google/gemini-3.8-flash` | 64 | 0.0 | 1.0 | false | `{"include": true}` | `{"allow_fallbacks": false}` |
| probe-3 | `deepseek/deepseek-v4.1-flash` | 2000 | 0.0 | 1.0 | false | `{"include": true}` | `{"allow_fallbacks": false}` |
| probe-4 | `google/gemini-3.8-flash` | 2000 | 0.0 | 1.0 | false | `{"include": true}` | `{"allow_fallbacks": false}` |

Models match `MODELS = ("deepseek/deepseek-v4.1-flash", "google/gemini-3.8-flash")`
(`runner.py:138`) and `PROBE_SLOT_MODELS` (`runner.py:181–182`). Request `model`
equals each result's `returned_model` (4/4). Message texts are byte-identical across
all four requests (fixed `PROBE_SYSTEM` / `PROBE_USER`, `runner.py:192–194`) and
contain no country/jurisdiction/evidence content. `dispatch.json` `model` field
equals `request.model` in all four.

## 5. Result statuses, finish reasons, content, usage, cost

| slot | status | http_status | finish (raw) | native finish | assistant content | returned provider | reasoning_tokens |
|---|---|---|---|---|---|---|---|
| probe-1 | `completed` | 200 | `stop` | `stop` | `{"probe": "ok"}` | Relace | 19 |
| probe-2 | `stopped` | *absent* | `length` | `MAX_TOKENS` | `null` | Google | 60 |
| probe-3 | `completed` | 200 | `stop` | `stop` | `{"probe": "ok"}` | Relace | 19 |
| probe-4 | `completed` | 200 | `stop` | `STOP` | `{"probe": "ok"}` | Google | 148 |

- Every raw envelope parses as one JSON object with `object: "chat.completion"`,
  exactly one choice, and a `usage` block (4/4).
- Raw usage == recorded usage, and `used_usd` == raw `cost`, in all 4 records.
- `cost_details.prompt + cost_details.completions == cost` exactly (Decimal
  comparison) in all 4 raw envelopes; `total_tokens == prompt + completion` in all 4.
- probe-2 failure record: `errors: ["probe: incomplete output - empty content"]`,
  `stop_reason` identical, `billed_on_failure.parsed: true` with 53/60/113 and
  $0.00026475 — consistent with the raw envelope. `retry: false` in all four.

Charges per slot: probe-1 $0.00001551 (5.1e-07 + 1.5e-05); probe-2 $0.00026475
(3.975e-05 + 0.000225); probe-3 $0.00001551 (5.1e-07 + 1.5e-05);
probe-4 $0.00061725 (3.975e-05 + 0.0005775).

### Totals across all four actual charges
- **Total billed USD: `0.00091302`** (exact Decimal sum; = $0.00091302)
- **Total tokens: prompt 276 + completion 274 = 550 total** (per-slot totals 115, 113, 115, 207)
- Remaining of the local $10 ceiling considering these charges: **$9.99908698**
- Total recorded reservations: `0.010339536` USD (5.5362e-05 + 0.00057255 + 0.001153074 + 0.00855855); reserved input 4 × 374 = 1496 units; reserved output 64+64+2000+2000 = 4128 tokens (equals `PROBE_OUTPUT_ALLOWANCE_TOKENS`, `runner.py:232–233`).

## 6. Duplicate slots / extra runs

- `probes/` contains exactly four directories: `probe-1`, `probe-2`, `probe-3`,
  `probe-4`. Each contains exactly two files (`dispatch.json`, `probe-result.json`).
  No `review.json`, no `reconciliation.json`, no attempt/log/temp files anywhere
  under `probes/`.
- No `runs/` directory exists in this experiment and no run attempt files exist —
  **zero scoring runs**, consistent with `git status` showing only untracked
  experiment dirs. No extra or duplicate dispatch artifacts found.
- Raw response `id`s are all distinct
  (`gen-1794106990-7PhsDMgoeYLY5Ey3xTWC`, `gen-1794106994-0siK3sXrXESUBEhvbyAa`,
  `gen-1794110261-QsQTj3oz7EAh67YH2wwb`, `gen-1794110270-0TMzHxo7IM8DnbBoLgJS`),
  so the four archived responses are four distinct provider transactions, not
  duplicated bytes. probe-1 and probe-3 are byte-different despite identical
  usage numbers (same fixed prompt, different ids/created timestamps).
- Dispatch timestamps are monotonic and non-overlapping per phase:
  03:03:10, 03:03:14 (originals), 03:57:41, 03:57:50 (follow-ups),
  each finishing 2–3 s later. `retry: false` in all four.
- Original-phase records (`probe-1`/`probe-2`) lack the `attempt_phase` key that
  current `runner.py:2087` writes for originals — they were archived under the
  earlier protocol; follow-up records carry `attempt_phase: "adaptive_followup"`
  and the `adapted_after` block, as the current runner requires.

## 7. Credential redaction

All 8 logged header records (`dispatch.json` + `probe-result.json` × 4 slots) contain
`"Authorization": "[REDACTED]"` — 8 `Authorization` lines found, 8 redacted.
Literal searches of `probes/` and both receipts for `Bearer `, `sk-or-`, and `sk-`
returned **zero** matches. No credential value was printed or persisted during this
verification; the base64 blobs inside probe-2/probe-4 `reasoning.encrypted` fields
are provider reasoning ciphertext, not credentials.

## 8. Comparison against the prior review

Prior review: `/home/meme/.pi/agent/sessions/--home-meme-kóði-kort--/subagent-artifacts/outputs/1ad1ab13-f702-429d-8019-d015437bb17f/pilot-probes/review.md`

| value | prior review stated | recomputed now | match |
|---|---|---|---|
| probe-1 request hash | `605a8dedf6721c0e7b23c8fa71b652b26356b206d87d96725efbd30efa99ff11` | same | YES |
| probe-2 request hash | `b09d104f2484d35482bc52da303dcefd4a1c7f1271807084e072109ac159a33d` | same | YES |
| original receipt SHA | `262c698e5ddc6a104a86a6cca5eda7219c4832bb353c31e14040431b8a032600` | same | YES |

Probe-1/2 **result-file hashes**: the prior review archived **no** probe-result or
raw-response digests (it explicitly recorded "No response digest is archived … I
cannot honestly supply a newly computed response hash"), so there is no prior value
to compare against. This report supplies the first computed values (§2). The prior
review's substantive facts re-verified here: probe-2 `stopped` / `length` /
`MAX_TOKENS` / null content / missing `http_status`, probe-1 `completed` / `stop` /
`{"probe": "ok"}`, token counts 85/30/115 and 53/60/113, costs $0.00001551 and
$0.00026475, two-slot reservation subtotal $0.000627912 — all confirmed unchanged.

## Discrepancies / residual risks

1. **Archival receipt vs current runner**: `preflight_receipt.json` binds
   `runner.py = 2e4e09f0…`, current file is `c9a227f1…`. This is the expected
   consequence of the post-failure runner amendment (the v4 receipt binds the
   current bytes correctly), but it means the v3 receipt is only verifiable
   against the historical runner, which is not retained in this working tree.
2. **probe-2 has no archived `http_status`** (prior review P1 still open) — the
   failure branch of the then-current runner stored the raw body only.
3. **No `probes/*/review.json` exists for any of the four slots** — the structured
   slot-review gate (`runner.py:1207–1229`) is still unsatisfied; both receipts
   still carry `live_behavior.status: "unobserved"`.
4. Receipts bind `data/countries.json`, which lives at the repo root
   (`/home/meme/kóði/kort/data/countries.json`), not inside the experiment dir;
   hash matches, but path resolution depends on `ROOT` (`runner.py:2230`).
5. probe-1/probe-3 identical usage figures are plausible (identical fixed prompt,
   same model) but this cannot distinguish two provider-side transactions beyond
   the distinct response ids/timestamps archived here.
6. Request hashes authenticate the request payload only; nothing here attests
   provider-side behavior, token bounds, or scoring validity (scope per dispatch).