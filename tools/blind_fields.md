# Blind-anonymisation: field spec, model prompt, runbook

`tools/blind_pairwise.py` asks a rating model to score two jurisdictions **without knowing
which they are**. Every record in `data/countries.json` therefore needs identity-stripped
duplicates of its research content.

Design principle: **1:1 mapping, minimal modification.** Each anonymised field is a rewrite
of exactly one source field. The lightweight model is *not* asked to restructure, classify,
summarise, or judge — only to remove identifying detail while preserving every risk-relevant
fact. Re-bucketing the research into new semantic categories would invite it to drop or
distort evidence, and would import its own biases into the blind rating.

---

## Field mapping

| Anonymised field | ← Source field | Records | Type |
|---|---|---|---|
| `blindSummary` | `summary` | 233 | string |
| `blindOutOfScope` | `outOfScopeNotes` | 232 | string |
| `blindSourceSummaries` | `sources[].summary` | 233 | **array of strings**, same order & length as `sources` |
| `blindLocalsOnly` | `localsOnly` | 119 | string (omit the field entirely where the source is absent) |
| `blindTangential` | `tangentialFactors` | 114 | string (omit the field entirely where the source is absent) |

`blindSourceSummaries` is the richest input — ~2,900 chars per record on average vs ~750 for
`summary`, 478k chars in total. It carries most of the concrete evidence (counts, penalties,
enforcement patterns, named cases), so it must be anonymised, not discarded.

## Fields that must NEVER reach the rating model

| Field | Why |
|---|---|
| `name` | Identifies directly |
| `score`, `band`, `rank` | Would anchor the rating — the whole point is an independent read |
| `comparisons` | **Doubly disqualified**: names other jurisdictions *and* their scores, and it hands the model pre-made pairwise conclusions, which is exactly what the pairwise exercise is supposed to generate independently |
| `sources[].url` | Domains and paths identify the country instantly (`.ws`, `/samoa/`, outlet names) |
| `anchorRefs` | ISO codes |
| `researchedAt` | Not risk-relevant |

---

## Anonymisation rules

1. **Jurisdiction name** → "the country" / "the territory" / "the jurisdiction".
2. **Capital and city names** → "the capital", "the largest city", "a provincial town".
3. **Named organisations, NGOs, agencies, media outlets** → "a national trans advocacy
   organisation", "the interior ministry", "a regional human-rights body", "the constitutional
   court", "a national newspaper".
4. **Named individuals and named legal cases** → "a trans woman", "a documented case",
   "a constitutional-court ruling". **Keep the substance** — what happened, the outcome,
   the penalty, the year.
5. **Statute names and article numbers** → "a penal-code provision", "a morality statute",
   "a colonial-era sodomy law", "an anti-propaganda law". **Keep penalties, keep whether
   they are enforced, keep sentence lengths** — those are the risk-relevant facts.
6. **Other countries named in the text** (including in `sources[].summary`, which often
   mentions regional neighbours or comparator states) → "a neighbouring state",
   "a regional peer". Delete any comparative score references entirely.
7. **Currencies** → keep the amount only where it expresses severity ("a fine equivalent to
   several months' wages"); otherwise drop the figure and keep the fact that a fine applies.
8. **Region-identifying culture terms** → genericise the label but **keep the fact and its
   degree of institutionalisation**: "an indigenous third-gender tradition recognised in
   customary law, whose members are eligible for chiefly titles and land inheritance".
   That is a genuine risk-relevant positive and must survive.
9. **Religions** → "religious-law-derived morality provisions", "a state religion influences
   the penal code". Do not name the religion.
10. **Dates** → keep years and relative recency ("since 2022", "in the last two years").
    Trajectory matters. Drop a date only if it uniquely pins an already-identifiable event.
11. **Counts, frequencies, sentence lengths, enforcement patterns, numbers of arrests or
    convictions** → **always keep verbatim.** This is the substance of the rating.
12. **Do not add, infer, or embellish. Do not soften or intensify severity.** If the source is
    ambiguous, keep it ambiguous. If the source is speculative, keep it speculative.
13. **Do not leak through style**: avoid distinctive phrasing, verbatim quotations with unique
    wording, and acronyms that expand to identifying names.
14. **Preserve length roughly.** Do not compress aggressively — the rater needs the detail.
    Aim for 80–110% of the original field length.
15. Where a source field is absent for a record, **omit the corresponding blind field**;
    do not invent content or write "none".
16. **Never reproduce the record's own rating.** Band labels ("Low Risk", "Reduced Risk",
    "Elevated Risk", "High Risk", "Do Not Travel"), the numeric score, and any rank
    ("ranked 48th") must not appear in the blind text — they would anchor the rater,
    which is the exact thing blinding exists to prevent. Describe the *facts*; let the
    rater derive the number. If the source text opens with "X is Reduced Risk for trans
    visitors", rewrite it as a factual claim about the jurisdiction without the label.
    Decimals that are genuine facts ("a 2.5-year sentence", "1.5 thousand people") are fine.

## Self-check before returning

- Could a reader name the jurisdiction from this text alone? If yes, genericise further.
- Does the text contain a band label, the record's own score, or a rank? If yes, remove it.
- Is every risk-relevant fact still present? If no, you over-scrubbed — restore it.
- Are penalties, enforcement frequency, counts, and years intact?
- Did you keep the same number of entries in `blindSourceSummaries` as in `sources`?

---

## Prompt for the lightweight model

> You are anonymising research records for a blind comparative rating exercise. Your only job
> is to strip every detail that could identify which jurisdiction a record describes, while
> preserving **every fact that bears on risk**.
>
> Context: these records assess the risk to a **transgender visitor** if they are discovered or
> outed. A rating model will read your output and must judge risk from facts alone, with no
> idea which jurisdiction it is looking at. Regional stereotypes are exactly what we are
> trying to eliminate, so identity leakage defeats the purpose — but over-scrubbing destroys
> the signal, which is equally bad.
>
> For the record I give you, return one JSON object with these keys, each an anonymised
> rewrite of the correspondingly-named input field:
>
> - `blindSummary` ← `summary`
> - `blindOutOfScope` ← `outOfScopeNotes`
> - `blindSourceSummaries` ← `sourceSummaries` (an **array**; return the same number of
>   entries, in the same order, each anonymised)
> - `blindLocalsOnly` ← `localsOnly` (omit this key if the input has no such field)
> - `blindTangential` ← `tangentialFactors` (omit this key if the input has no such field)
>
> **Anonymisation rules**
> [paste rules 1–16 above]
>
> Return **only** the JSON object. No prose, no markdown fences, no commentary.
>
> RECORD:
> ```json
> {paste the payload produced by tools/make_blind_inputs.py}
> ```

---

# Pipeline

## 1. Extract inputs

```bash
python3 tools/make_blind_inputs.py                 # writes data/blind_inputs/payloads.jsonl
python3 tools/make_blind_inputs.py --only WSM TON  # specific records
python3 tools/make_blind_inputs.py --emit-prompt    # print the instruction block to paste
```

Each JSONL line is `{"iso": "...", "n": <index>, "payload": {...}}`. **Pass only `payload`
to the model** — `iso` and `n` are routing metadata for you, and must not be shown to the
model. The payload contains only the five allowed source fields, with `sources[].url`
already stripped.

## 2. Collect outputs

Save the model's replies as JSONL, one object per line:

```json
{"iso": "WSM", "blindSummary": "...", "blindOutOfScope": "...", "blindSourceSummaries": ["...", "..."], "blindLocalsOnly": "...", "blindTangential": "..."}
```

(or one `<ISO>.json` file per record in a directory — both are accepted).

## 3. Validate and merge

```bash
python3 tools/apply_blind_fields.py --in data/blind_outputs.jsonl --dry-run   # inspect first
python3 tools/apply_blind_fields.py --in data/blind_outputs.jsonl
```

Validation, all of which must pass before a record is written:

- required fields present and non-empty; `blindSourceSummaries` length matches `sources`
- **identity leak**: the record's own name, its ISO3, any source-URL domain, or **the name of
  any of the 233 jurisdictions** anywhere in the blind text → hard fail (rule 6: other
  countries' names leak by association)
- **demonym leak**: a capitalised token extending a jurisdiction name ("Samoan", "Chinese")
- **region leak**: continent / region / bloc / demonym terms ("European", "Pacific",
  "Caribbean", "Gulf", "Balkan") — the primary stereotype vector
- **rating leak**: the record's own band label, score, or a rank reference (rule 16)
- **review check**: capitalised proper-noun tokens not on a generic allowlist are reported as
  warnings for human eyeballing (does not block)
- length sanity: blind text within 40–200% of the source field length (guards against both
  over-scrubbing and padding)

Failures are reported per record and skipped; the run continues. Use `--report` to see a
summary of how many records are ready.

## 4. Run the pairwise refinement

```bash
python3 tools/blind_pairwise.py --dry-run --num-pairs 3          # eyeball dossiers for leaks
python3 tools/blind_pairwise.py --api-key "$KEY" --no-write --num-pairs 50   # calibration trial
python3 tools/blind_pairwise.py --api-key "$KEY" --num-pairs 10000 --workers 4
```

By default the tool pairs only records with **all** expected blind fields present
(`blindSummary`, `blindOutOfScope`, `blindSourceSummaries`); `blindLocalsOnly` and
`blindTangential` are included when present, since they are optional in the source data.
Use `--allow-partial-blind` to include records missing required fields.

---

# Running the refinement tool

## Typical invocation

```bash
python3 tools/blind_pairwise.py \
  --api-key "$KEY" \
  --baseurl https://token-plan.ap-southeast-1.maas.aliyuncs.com/apps/anthropic \
  --api anthropic-messages \
  --model qwen3.8-flash \
  --num-pairs 10000 \
  --differential-weighting-percent 0.25-0.03 \
  --absolute-weighting-percent 0.15-0.015 \
  --absolute-weighting-shift 0.012-0.0012 \
  --reasoning-tokens 3000 \
  --workers 4
```

## Weighting parameters ramp high → low

Each of the three weighting parameters accepts either a scalar (`0.05`) or a
`START-END` range (`0.15-0.015`). A range interpolates linearly across the run:
pair 1 gets START, the final pair gets END. This makes the run **coarse-to-fine** —
big corrections early while the map is still rough, gentle settling as it converges,
and no late-run oscillation from oversized single-pair moves.

Suggested ramps for a 10k-pair run (each is 2.5–10× the old constant default at the
start, decaying to ~¼–⅓ of it by the end):

| Parameter | Old constant | Suggested ramp |
|---|---|---|
| `--absolute-weighting-percent` | 0.05 | `0.15-0.015` |
| `--absolute-weighting-shift` | 0.004 | `0.012-0.0012` |
| `--differential-weighting-percent` | 0.1 | `0.25-0.03` |

The startup banner prints the resolved ramps and their values at pair 1 / mid / last;
every audit-log entry records the exact `params` used for that pair, so the whole run
is reproducible. Values must be ≥ 0; `START` may be lower than `END` if you ever want
an increasing ramp.

## Flags

| Flag | Default | Purpose |
|---|---|---|
| `--dry-run` | off | Build and print prompts, make **no** API calls. Use first. |
| `--no-write` | off | Call the API and write the audit log, but leave `countries.json` untouched. |
| `--seed N` | none | Reproducible pair selection. |
| `--absolute-weighting-percent` | `0.05` | Scalar or `START-END` ramp; fraction of the way toward the rated score per pair. |
| `--absolute-weighting-shift` | `0.004` | Scalar or `START-END` ramp; fixed nudge toward the rated score per pair. |
| `--differential-weighting-percent` | `0.1` | Scalar or `START-END` ramp; fraction of the rated-gap difference to close per pair. |
| `--workers N` | 1 | Concurrency. Updates are lock-guarded; scores drift as the run proceeds, so later pairs see earlier results (intended). |
| `--save-every N` | 25 | Checkpoint `countries.json` every N successful pairs. |
| `--log PATH` | `data/blind-pairwise-<ts>.jsonl` | Per-pair audit: both ISOs, presentation order, model ratings, every intermediate step, token usage, the model's `why`. |
| `--no-cache` | off | Omit `cache_control` if the endpoint rejects it. |
| `--retries` / `--backoff` / `--timeout` | 4 / 1.5s / 180s | Retry 429/5xx/network errors with exponential backoff. |
| `--auth-style` | `both` | Send `x-api-key`, `Authorization: Bearer`, or both. |
| `--endpoint-suffix` | `/v1/messages` | Adjust if the proxy path differs. |
| `--max-output-tokens` | 1024 | Output budget on top of `--reasoning-tokens`. |

## Caching behaviour

The fixed prompt (role, scale, band definitions, the complete `outing-risk-taxonomy.md`, the
ten rating rules, the output format — ~17.4k chars / ~4.3k tokens) is sent as **one** `system`
text block carrying `cache_control: {"type":"ephemeral"}`. It is built once per process and is
byte-identical on every request, which is what the provider needs to serve cache hits. Only the
two dossiers vary, in the `user` message. The log reports `cache_read_input_tokens` per call;
a healthy run shows cache-read ≈ system-prompt size on every pair after the first.

To maximise hit rate: keep `--baseurl`/`--model` stable, avoid long pauses (provider cache TTL),
and do not edit `research/outing-risk-taxonomy.md` mid-run — any change alters the cached block
and invalidates it.

**Cost note**: dossiers average ~4k chars each (~1k tokens), so each pair sends ~2k uncached
input tokens plus the cached system block. 10,000 pairs ≈ 20M uncached input tokens. Run the
`--no-write --num-pairs 50` trial first to check the model is neither systematically harsh nor
generous before committing to the full run.

## After a run

```bash
python3 tools/build_data.py     # refresh bands, ranks, meta.json
git diff data/countries.json    # review drift
```

Scores are stored at 6 dp and displayed at 2 dp. Ranks are computed at 2 dp so sub-cent drift
does not produce a ranking the UI cannot show.

## Score-update semantics

See the `tools/blind_pairwise.py` module docstring for the full derivation. Two properties:

- **Corridor clamp** — a score can never leave the interval between its own previous value and
  its own model rating. If the model says "lower", it moves down and cannot overshoot the
  model's number; if "higher", likewise. Combined with the `[0,1]` clamp, no single pair can
  push a score anywhere the model did not indicate.
- **Differential step is sign-agnostic** — it moves the *gap* toward the rated gap, narrowing
  scores the model rated closer together and widening scores it rated further apart, splitting
  the movement equally.

### Note on the worked example in the brief

The brief's example rates the pair 0.2 / 0.7 (rated gap **0.5**) but then computes step 3 with
"a rated difference of 0.4" and "0.4 − 0.223 = 0.117" (that subtraction is 0.177). This
implementation follows the stated *formula* — `P_diff × (rated_gap − current_gap)`, split
equally — giving 0.27715 / 0.52785 for that example rather than the brief's 0.28515 / 0.51985.
Steps 1 and 2 reproduce the brief exactly (0.295 → 0.291; 0.51 → 0.514). If the 0.4 figure was
intentional rather than a slip, say so and I will add a `--differential-target` override.
