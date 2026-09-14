# Blind-anonymisation fields — spec + model prompt

`tools/blind_pairwise.py` asks a model to rate two countries **without knowing which
they are**. To make that possible, every record in `data/countries.json` needs
identity-stripped duplicates of its research content.

## Fields to add (per country record)

| Field | Content | Source fields it replaces |
|---|---|---|
| `blindProfile` | Identity-free **structural** context that genuinely affects traveler risk: regime type, state capacity, armed-conflict status, legal tradition family, surveillance intensity, tourism exposure, urban/rural split, population scale (order of magnitude only). **Never** region, continent, neighbours, language, ethnicity, or named religions. | (new — distilled, not a rewrite) |
| `blindSeverity` | Per-axis severity placement using the taxonomy's 1–5 ladder for axes A–K, each with a one-line evidence note. Axes with no evidence get `n/e` (no evidence) rather than being omitted — absence of evidence is itself data. | `summary` |
| `blindNarrative` | The substantive risk narrative: what actually happens to a trans visitor, what is documented, how consistently law is enforced, what protections exist. All identifiers genericised. | `summary`, `localsOnly`, `tangentialFactors` |
| `blindExcluded` | What was deliberately **not** counted and why (resident-facing, general-LGB, general crime). Keeps the rating model from double-counting. | `outOfScopeNotes`, `localsOnly`, `tangentialFactors` |

## Fields that must NEVER be sent to the rating model

`name`, `score`, `band`, `rank`, `comparisons` (names other countries *and* scores),
`sources` (URLs and outlet names identify the country instantly), `anchorRefs`
(ISO codes), `researchedAt`, `outOfScopeNotes` (often names the country).

## Anonymisation rules

1. **Country/territory name** → "the country" / "the territory" / "the jurisdiction".
2. **Capital and city names** → "the capital", "the largest city", "a provincial town".
3. **Named organisations, NGOs, agencies** → "a national trans advocacy organisation",
   "the interior ministry", "a regional human-rights body", "the constitutional court".
4. **Named individuals and named legal cases** → "a trans woman", "a documented case",
   "a constitutional-court ruling". Keep the *substance* (what happened, the outcome).
5. **Statute names and article numbers** → "a penal-code provision", "a morality statute",
   "a colonial-era sodomy law", "an anti-propaganda law". Keep **penalties and whether
   they are enforced** — those are the risk-relevant facts.
6. **Currencies** → keep amounts only if they express severity (e.g. "a fine equivalent to
   several months' wages"); otherwise drop.
7. **Neighbouring/ comparator countries named in the text** → "a neighbouring state",
   "a regional peer". Delete comparative score references entirely.
8. **Region-identifying culture terms** → genericise ("a customary village-council system",
   "an indigenous third-gender tradition recognised in customary law") **but keep the fact**
   that such a tradition exists and how institutionalised it is — that is a genuine
   risk-relevant positive.
9. **Religions** → "religious-law-derived morality provisions", "a state religion influences
   the penal code". Do not name the religion.
10. **Dates** → keep years and relative recency ("since 2022", "in the last two years").
    These matter for trajectory. Never keep a date that uniquely identifies an event
    already tied to a named case.
11. **Counts, frequencies, sentence lengths, enforcement patterns** → **always keep verbatim**.
    These are the substance of the rating.
12. **Do not add, infer, or embellish facts.** Do not soften or intensify severity. If the
    source text is ambiguous, keep it ambiguous.
13. **Do not leak via style**: avoid distinctive phrasing, quotations with unique wording,
    and acronyms that expand to identifying names.
14. Length targets: `blindProfile` ≤ 120 words, `blindSeverity` ≤ 250 words,
    `blindNarrative` ≤ 350 words, `blindExcluded` ≤ 120 words.

## Self-check before returning

- Could a reader name the country from this text alone? If yes, genericise further.
- Is every *risk-relevant* fact still present? If no, you over-scrubbed — restore it.
- Are penalties, enforcement frequency, counts, and dates intact?

---

## Prompt to give the lightweight model

> You are anonymising research records for a blind comparative rating exercise. Your job is
> to strip every detail that could identify which country a record describes, while
> preserving **every fact that bears on risk**.
>
> Context: these records assess the risk to a **transgender visitor** if they are discovered
> or outed. The rating model that will read your output must judge risk from facts alone,
> with no idea which country it is looking at. Regional stereotypes are exactly what we are
> trying to eliminate, so identity leakage defeats the purpose — but over-scrubbing destroys
> the signal, which is equally bad.
>
> For the record I give you, produce four fields:
>
> 1. `blindProfile` — identity-free structural context that genuinely affects traveler risk:
>    regime type, state capacity, armed-conflict status, legal-tradition family, surveillance
>    intensity, tourism exposure, urban/rural split, population scale (order of magnitude).
>    Never region, continent, neighbours, language, ethnicity, or named religions. ≤ 120 words.
> 2. `blindSeverity` — for each axis A–K of the taxonomy below, give a severity level 1–5
>    (or `n/e` if no evidence) plus a one-line evidence note. Absence of evidence must be
>    recorded as `n/e`, not omitted. ≤ 250 words.
> 3. `blindNarrative` — what actually happens to a trans visitor there: documented incidents,
>    enforcement consistency, protections, predation patterns. ≤ 350 words.
> 4. `blindExcluded` — what was deliberately not counted, and why (resident-facing,
>    general-LGB, general crime). ≤ 120 words.
>
> **Anonymisation rules** [paste rules 1–14 above]
>
> **Taxonomy axes**: A border/transit/security screening · B documents & everyday bureaucracy ·
> C gendered spaces & facilities (incl. hospital-ward placement) · D public presence & social
> reaction · E violence & predation (incl. dating-app ambushes, blackmail) · F police
> interaction · G law & criminal exposure if outed · H arrest/detention/prison placement ·
> I health & medication (HRT import, emergency care, insurance) · J family & diaspora
> exposure · K state/media climate (probability modifier).
>
> **Severity ladder**: 5 catastrophic (state/honour killing, death penalty applied, torture in
> custody, lethal violence with impunity) · 4 severe (imprisonment esp. misgendered facility,
> sexual violence in detention, forced medical procedures, deportation to danger, denial of
> life-saving care) · 3 major (arrest & prosecution, violent public assault, blackmail/
> extortion, forced outing, denial of entry/stranding, medication confiscation) · 2 moderate
> (police harassment/humiliation, service discrimination, invasive searches, intimidation) ·
> 1 minor (staring, invasive curiosity, misgendering, occasional service friction).
>
> Return **only** a JSON object with exactly those four keys, values as strings. No prose
> outside the JSON.
>
> RECORD:
> ```json
> {paste the record's `summary`, `outOfScopeNotes`, `comparisons`, `localsOnly`,
>  `tangentialFactors` — but NOT `name`, `score`, `band`, `rank`, `sources`, `anchorRefs`}
> ```

**Important**: when you paste the record in, remove `name` and `sources` — the lightweight
model must not see them either, or it may echo identifying text back. `comparisons` may be
included (it carries calibration reasoning) but the model must be told to delete all
comparator names and scores per rule 7.

---

# Running the refinement tool

`tools/blind_pairwise.py` — blind pairwise rating + score drift.

## Prerequisite

Every country record needs the four `blind*` fields populated (see prompt above).
The tool refuses to start if none exist, and by default only pairs countries that have
**all four**. Use `--allow-partial-blind` to include records with some fields present.

## Typical invocation

```bash
python3 tools/blind_pairwise.py \
  --api-key "$KEY" \
  --baseurl https://token-plan.ap-southeast-1.maas.aliyuncs.com/apps/anthropic \
  --api anthropic-messages \
  --model qwen3.8-flash \
  --num-pairs 10000 \
  --differential-weighting-percent 0.1 \
  --absolute-weighting-percent 0.05 \
  --absolute-weighting-shift 0.004 \
  --reasoning-tokens 3000 \
  --workers 4
```

## Useful flags

| Flag | Default | Purpose |
|---|---|---|
| `--dry-run` | off | Build and print prompts, make **no** API calls. Use this first. |
| `--no-write` | off | Call the API and write the audit log, but leave `countries.json` untouched. Good for a calibration trial. |
| `--seed N` | none | Reproducible pair selection. |
| `--workers N` | 1 | Concurrency. State updates are lock-guarded; scores drift as the run proceeds, so later pairs see earlier results (intended). |
| `--save-every N` | 25 | Checkpoint `countries.json` every N successful pairs. |
| `--log PATH` | `data/blind-pairwise-<ts>.jsonl` | Per-pair audit record: both ISOs, presentation order, model ratings, every intermediate step, token usage, the model's `why`. |
| `--no-cache` | off | Omit `cache_control` if the endpoint rejects it. |
| `--retries` / `--backoff` / `--timeout` | 4 / 1.5s / 180s | Retry on 429/5xx/network errors with exponential backoff. |
| `--auth-style` | `both` | Send `x-api-key`, `Authorization: Bearer`, or both. |
| `--endpoint-suffix` | `/v1/messages` | Adjust if the proxy path differs. |
| `--max-output-tokens` | 1024 | Output budget on top of `--reasoning-tokens`. |

## Caching behaviour

The fixed prompt (role, scale, band definitions, the complete `outing-risk-taxonomy.md`,
the ten rating rules, the output format — ~17.4k chars / ~4.3k tokens) is sent as **one**
`system` text block with `cache_control: {"type":"ephemeral"}`. It is built once per process
and is byte-identical on every request, which is what the provider needs to serve cache hits.
Only the two dossiers vary, in the `user` message. The log reports `cache_read_input_tokens`
per call so you can confirm hits; a healthy run shows cache-read ≈ system-prompt size on
every pair after the first.

To maximise hit rate: run with a stable `--baseurl`/`--model`, keep the run inside the
provider's cache TTL by not pausing for long, and avoid editing `research/outing-risk-taxonomy.md`
mid-run (any change to that file changes the cached block and invalidates it).

## After a run

```bash
python3 tools/build_data.py     # refresh bands, ranks, meta.json
git diff data/countries.json    # review drift
```

Scores are stored at full precision (6 dp) and displayed at 2 dp. Ranks are computed at
2 dp so sub-cent drift does not produce a ranking the UI cannot show.

## Score-update semantics

See the module docstring for the full derivation. Two properties worth knowing:

- **Corridor clamp**: a country's score can never leave the interval between its own
  previous value and its own model rating. If the model says "lower", it moves down and
  cannot overshoot the model's number; if "higher", likewise. Combined with the `[0,1]`
  clamp, no single pair can push a score anywhere the model did not indicate.
- **Differential step is sign-agnostic**: it moves the *gap* toward the rated gap, so it
  narrows scores the model rated closer together and widens scores it rated further apart,
  splitting the movement equally between the two.

### Note on the worked example in the brief

The brief's example rates the pair 0.2 / 0.7 (a rated gap of **0.5**) but then computes
step 3 with "a rated difference of 0.4" and "0.4 − 0.223 = 0.117" (which is 0.177).
This implementation follows the stated *formula* — `P_diff × (rated_gap − current_gap)`,
split equally — which gives 0.27715 / 0.52785 for that example rather than the brief's
0.28515 / 0.51985. Steps 1 and 2 reproduce the brief exactly (0.295 → 0.291, 0.51 → 0.514).
If the 0.4 figure was intentional rather than a slip, say so and I will add a
`--differential-target` override.
