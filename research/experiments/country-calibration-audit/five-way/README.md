# five-way — offline 5-way comparison harness

One call rates **five blinded dossiers at once** and answers with one strict JSON
object holding five `{slot, score, why}` entries. Two schedule modes:

* **country mode** — five countries per call, drawn one per overlapping percentile
  band of the current scores in `data/countries.json`; US-locked mode forces ISO3
  `USA` into its own band's slot in every call.
* **admin1 mode** — five divisions of ONE country per call, identities withheld.

Deliverables: `harness.py`, `test_harness.py`, `README.md`. Nothing else is
written by this experiment except `frozen/` (schedules, diversity input) and —
only during an explicitly enabled run — `runs/<run-id>/`.

## Offline guarantees (by construction)

* `harness.py` contains **no network, credential or provider-call code** at all
  (a test scans the source for banned tokens); it imports only the stdlib plus
  the constants of `tools/blind_pairwise.py`.
* The runner is **disabled by default**: `run` refuses with exit 2 unless both
  `--execute` **and** `--provider package.module:function` are given. Without
  them no schedule is read, nothing is written, no network or credentials are
  touched. Dispatch happens through the injected adapter only.
* Schedule builders write only under this directory's `frozen/`. Tests write
  only to temporary directories. No `data/` writes, no commits, no staging.
* Diagnostic prompt hooks (`STRIP_RULE_10B`, `REVERT_ENDPOINT`,
  `RESTORE_ARCHIVED_WORDING`) are refused: the five-way harness always builds
  the production r2026-11-13 rules as-is.

## Layout

```
five-way/
  harness.py               # everything below, offline
  test_harness.py          # unittest suite (50 tests)
  README.md                # this file
  frozen/diversity/        # INPUT: blinded subnational-regimes batches (read-only here)
      batch-*.json         #   each file: {"<ISO3>": {"iso3", "diversity",
                           #     "blindDiversity", "basis"}, ...}
  frozen/schedule_country.json        # written by schedule-country
  frozen/schedule_admin1_<ISO3>.json  # written by schedule-admin1
  runs/<run-id>/           # only during --execute: attempt-NNNN.json (raw
                           #   response preserved), result-NNNN.json, ledger.json
  accounting.lock          # the ONE shared lock (transient, O_EXCL)
```

`frozen/diversity/` is a required input for country schedules. The loader merges
every `*.json` batch, requires a non-empty `blindDiversity` string per ISO3, and
reads **only** that field — the plain `diversity` text never enters a prompt. A
selected country missing its paragraph stops the build with an explicit error
**before anything is written** (fail closed; no substitute draw).

## Sampling (country mode)

* Percentiles are computed over **every** record in `data/countries.json`:
  average-rank, `p = 100 * avg_rank / (n - 1)`, zero-based ranks, tied scores
  share the average rank, closed intervals `lo <= p <= hi`. Endpoints land on
  0.0/100.0 when unique. The exact method string is recorded in the schedule.
* Bands, in draw order: `[0,30] [20,50] [35,65] [50,80] [70,100]`. They overlap
  on purpose; each call draws **one country per band from the eligible pool
  minus countries already selected in that call**, so no country appears twice
  in one call. Empty pool ⇒ `HarnessError`, nothing written.
* Eligible pool: blind-complete, non-territory records (production parity —
  dependent territories rate in the mixed lane only): `blindSummary`,
  `blindSourceSummaries`, `blindOutOfScope` (the latter only when
  `outOfScopeNotes` is non-empty), mirroring `tools/blind_pairwise.py`.
* **US-locked mode** (`us_locked=True`, default): `USA` occupies the slot of the
  **first band (in draw order) whose range contains its percentile**; the other
  four bands each draw one country excluding `USA`. (Today USA's percentile
  falls only in `[20,50]`; the first-band rule is the deterministic tie-break
  for future drift into the overlap regions.)
* The five band-order picks are then shuffled into display slots 1–5. The seed,
  RNG identity (`random.Random` / MT19937, Python version) and per-call slot map
  are recorded in the schedule; identical `(data, seed)` ⇒ byte-identical
  schedule (tested).

## Admin1 mode

* Eligible divisions of one parent: `iso3` matches, numeric score present, and
  the three required blind fields non-empty (production parity). Fewer than five
  eligible ⇒ refuse.
* Each division dossier embeds the parent's blind national framework — exactly
  the four design-enumerated fields `blindSummary` / `blindTangential` /
  `blindLocalsOnly` / `blindSourceSummaries` with **sources capped at 8** — and
  then the division's own blind evidence. Never included: the parent's score,
  band, name, `blindOutOfScope`, the diversity paragraph; the division's `name`,
  `summary`, `modelContext`, `outOfScopeNotes` (all identity-carrying — e.g.
  `modelContext` starts with the division's name in the real data). The
  production `estimated` → "DATA STATUS" note is kept (identity-neutral).
* Prompt blinding is field-based, exactly like production: only `blind*` text is
  rendered, HTML-stripped and whitespace-collapsed.

## Prompts (rubric consistency)

Reused **verbatim** from `tools/blind_pairwise.py` (tested as substrings of the
production prompts):

* `RATING_RULES` — the "## Rating rules" section (r2026-11-13, rule 10b intact);
* the production `## The scale` block, cut live out of
  `BP.build_system_prompt` (country mode) / `BP.build_admin1_system_prompt`
  (admin1 mode) so wording can never drift;
* the full outing-risk taxonomy reference section.

Added, and only added: the five-way framing ("five dossiers, numbered 1 to 5",
identities withheld), the mean-local-regime instruction ("where local regimes
vary … the rating should reflect the mean local regime in addition to the
national picture" — country mode points at the blinded SUBNATIONAL REGIMES
paragraph, admin1 mode at the shared national framework), the shuffle, and the
five-way output contract. Existing scores never enter any prompt in either mode.

**Resolved ambiguity (main one):** the production `ADMIN1_RULES` block
("Sub-national rating rules") is *not* included in admin1 mode. Its text is
pairwise-specific ("identical for *both* divisions", "Two divisions …") and
references a national score the design forbids showing; the design specifies the
ADM1 addition as the mean-local-regime instruction and says "add only …". If the
user prefers production-ADMIN1-rule parity, it is a one-line inclusion in
`build_admin1_system`.

## Output contract

The model must return exactly:

```json
{"results": [
  {"slot": 1, "score": 0.42, "why": "…"},
  {"slot": 2, "score": 0.55, "why": "…"},
  {"slot": 3, "score": 0.31, "why": "…"},
  {"slot": 4, "score": 0.60, "why": "…"},
  {"slot": 5, "score": 0.77, "why": "…"}
]}
```

Validation is strict whole-text JSON (no markdown-fence tolerance, `NaN`/
`Infinity` rejected at parse, booleans rejected): top-level keys exactly
`results`; exactly five entries; keys exactly `{slot, score, why}`; `slot` an
integer 1–5 covering each slot exactly once; `score` a finite JSON number in
`[0, 1]`; `why` a non-empty string. Any violation raises `OutputRejected` and
**stops the run** — there are no retries selected by outcome, for output
failures, unknown charges, budget stops or adapter errors alike (exactly one
attempt per scheduled call).

## Accounting (execute path)

* Exact `Decimal` accumulation from provider usage: `usage.cost_usd` must be an
  exact non-negative decimal (string/int/float accepted, `NaN`/`Infinity`/
  booleans/garbage rejected); `input_tokens`/`output_tokens` optional but must
  be non-negative integers when present. Anything unpriceable raises
  `UnknownCharge` and stops the run with the attempt already persisted.
  Persisted amounts use plain (non-scientific) exact decimal strings.
* **No price table is invented here** — the adapter must report the exact
  charge it incurred.
* `MAX_USD = Decimal("10.00")` local guard (same constant as the closed
  country-feasibility runs): checked before each call and after each recorded
  charge. The guard is **enforced locally only** — it is not a provider-side
  spend limit, and one in-flight call can overshoot it by its own cost.
* **One shared lock file** (`accounting.lock`, atomic `O_EXCL`, payload records
  holder/pid): acquired after the static gates and before any ledger or
  `runs/<run-id>` state is read, held through dispatch, released only by its
  own holder. Contention refuses before any call; foreign locks are never
  deleted.
* Every attempt is written to `runs/<run-id>/attempt-NNNN.json` **with the raw
  response preserved verbatim before any interpretation**, plus the message
  hashes; `result-NNNN.json` records ok/rejected/stopped with the exact cost;
  `ledger.json` accumulates the run total.

## Schedule gates

`verify` (read-only) and the execute path both run, before any write or call:
schedule schema (version, kind, slot maps with five distinct entries, hash
shapes, rubric version), **source pins** (SHA-256 of `data/countries.json`,
`data/admin1.json` when applicable, `research/outing-risk-taxonomy.md`,
`tools/blind_pairwise.py` — any drift refuses and asks for a rebuild), and
**message re-derivation** (prompts rebuilt from the recorded slot maps must
hash-match the recorded `system_sha256`/`user_sha256`).

## Usage

```sh
# build schedules (writes only under frozen/)
python3 harness.py schedule-country --n-calls 10 --seed 20261119
python3 harness.py schedule-country --n-calls 10 --seed 20261119 --no-us-lock
python3 harness.py schedule-admin1 --iso3 USA --n-calls 5 --seed 20261119

# read-only verification
python3 harness.py verify --schedule frozen/schedule_country.json

# dispatch — refuses (exit 2) without --execute and --provider
python3 harness.py run --schedule frozen/schedule_country.json --run-id r1
python3 harness.py run --schedule frozen/schedule_country.json --run-id r1 \
    --execute --provider mypkg.adapter:call

# tests (offline; temp-dir writes only)
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_harness
```

Adapter contract: `call(system_text, user_text)` returns
`{"raw_response": str, "usage": {"cost_usd": …, "input_tokens": …,
"output_tokens": …}}`. The harness ships no adapter.

## Tests (50, all offline)

Coverage mapped to the required list: strata correctness (independent
percentile recomputation), no-overlap within a call, US-locked presence and
first-containing-band slot, seed determinism (same seed ⇒ identical schedule
incl. hashes; different seed ⇒ different draws), prompt exclusion rules (no
score/name/comparison leakage, plain-diversity text absent, no diversity
paragraph in ADM1 mode, parent score/name/blindOutOfScope absent, parent sources
capped at 8), output validation (21 invalid shapes + valid ordering), accounting
stop paths (unknown charge, budget guard, corrupt ledger, lock contention,
foreign-lock preservation, exact-Decimal totals), runner refusal without
`--execute` (and without `--provider`), one-attempt-no-retry behavior, raw
response preservation, gates-before-write, and a source scan proving no
network/credential code exists in `harness.py`.

## Residual notes

* Blinding is field-based like production: a handful of real records leak their
  own name inside `blind*` text (4/233 country records at build time). The
  harness does not add a scrubber — that would deviate from the production
  dossier behavior the rubric is calibrated against.
* Country schedules cannot be built until every eligible country's
  `blindDiversity` paragraph exists under `frozen/diversity/`; the build fails
  closed with the missing ISO3 until then.
* Schedule files are overwritten atomically on each builder invocation; same
  inputs produce byte-identical output, so re-running is a no-op in content.