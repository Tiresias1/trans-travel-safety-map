# Analysis plan — committed before dispatch (2026-11-08)

Written before any model score from these schedules was read by the
coordinator, after the plumbing fix that made call 1 of
`fiveway-us-20261108` unparseable.

## Duplicate-draw rule (pre-committed)

`runs/fiveway-us-20261108/attempt-0001.json` holds one complete, contract-valid
five-way response for country schedule cell 1 (dispatched once, rejected only by
the adapter-envelope bug). The fixed schedules are re-dispatched in full as one
coherent wave under new run ids.

- **Primary analysis = the fresh full wave** (every cell drawn exactly once
  under the fixed plumbing).
- The preserved first draw of cell 1 is reported alongside as a **sensitivity
  duplicate**. It is never swapped in for the fresh draw, and no cell is
  chosen between draws on the basis of its value.
- If any further cell ever accumulates duplicate draws, the same rule applies:
  the wave used is declared first, all duplicates are reported, none is
  selected by value.

## Comparisons (diagnostic only; no value is a target)

- Country test: distribution of the locked country's 20 ratings (mean, sd,
  median, range) against the archived pairwise encounter mean and the isolated
  diagnostic — reported side by side, not merged.
- ADM1 test: per-unit repeat spread; mean of unit ratings vs the national
  framework read (the user's sanity criterion: unit mean should approximate the
  national picture — a gap is a bug signal, not a correction target).
- All outputs stay in research artifacts. Nothing is written to map data.

## Continuation rule (pre-committed 2026-11-08, before any score was read)

Wave 2 stopped at country cell 17 with `finish_reason: length` and empty
assistant content (the 11,000-token allowance was consumed by reasoning). An
empty draw carries no outcome, so there is nothing to select on.

- Undispatched cells (country 18–20) and the empty cell (17) are completed via
  the frozen schedule with `--calls`, same generation settings, new run id.
  Cell 17 is re-dispatched **at most once more**; a second empty draw makes it
  a reported failed cell. No cell is ever selected between draws by value.
- The ADM1 test runs regardless of country-run completion: its data is
  independent and its purpose (noise/consistency + the national-mean sanity
  check) does not depend on the country cells.
- Any further empty/length draw anywhere follows the same rule: preserve,
  report as failed draw, at most one re-dispatch, identical settings.
- Generation settings stay fixed at the declared values (model
  deepseek/deepseek-v4.1-flash, max_tokens 11000) across the whole study.

## Parent-rating variant (pre-committed 2026-11-08, before variant results)

Per user instruction: re-run the US ADM1 five-way with the national rating
provided alongside the national framework dossier, to test whether the +0.129
state-mean gap is missing anchoring.

- The rating given is **0.35** — the country five-way panel mean (0.346,
  rounded to the instrument's two-decimal convention). Chosen from the country
  wave, before any variant state result exists. Never adjusted afterwards.
- Same schedule cells as the no-rating wave (identical seed and slot draws);
  the ONLY prompt difference is one marked block carrying the parent rating.
  The leak gate narrowly exempts that marked block and nothing else.
- Readouts (diagnostic): state-mean shift vs 0.475, state-mean vs 0.35,
  per-state paired shifts, ordering stability. A pull toward 0.35 = anchoring
  gap; no pull = evidence-side divergence. Neither outcome retunes any value.

## GBR / NPL locked five-way runs (pre-committed 2026-11-08, before draws)

Per user instruction: run the country five-way with GBR and NPL locked in
every call, exactly like the US-locked design (locked country occupies its
percentile-band slot; four stratified random partners; identical rubric,
dossiers, diversity paragraphs, model and settings).

- Two schedules of 20 calls: GBR seed 20261110, NPL seed 20261111.
- Readouts (diagnostic): per-country draw distribution (mean, sd, median,
  range, mean CI), duplicate/sensitivity handling as before (wave = primary,
  every draw reported, none selected by value), cross-reference to the
  comparator sweep's dossier-condition q1 values and to the displayed values.
  Nothing is a target; no map writes.
- Empty/length draws: same rule — preserve, report as failed, at most one
  re-dispatch per cell, identical settings.

## Failed-draw rule amendment (pre-committed 2026-11-08, before GBR or
## parent-rating-variant values were inspected)

A draw that yields NO parseable outcome — empty content, length-exhaustion, or
a malformed-JSON contract violation — is a FAILED DRAW in the same class: it
carries no value to select on. It receives at most one re-dispatch under
identical settings; the failed draw is always reported. This extends the
existing empty-draw rule to contract-violation draws (GBR cell 6 produced
truncated JSON). Cells settled under this rule: ADM1-scored cell 20 (first
draw empty; gets its one re-dispatch — an earlier worker instruction that
denied it was over-strict and is superseded by this pre-commit), GBR cell 6
(first draw malformed; one re-dispatch).

## Diversity paragraphs v2 (2026-11-08, user-ordered regeneration)

v1 paragraphs (archived in frozen/diversity-v1/) blended record evidence with
model-knowledge generalizations and used standing labels (e.g. "institutionally
hostile provincial cities" from a one-city report). v2 regenerates all 233 with
claim-level grounding: every sentence tagged record-grounded or expectation in
the `basis`; no generalization from single events (scope words required); no
standing hostility labels; no invented geography; explicit thin-evidence
humility; nuance over flattening. v1 remains the text executed runs used.

## Instrument text v2 (pre-committed 2026-11-08, before any v2 run)

Per user: the country clause is replaced VERBATIM with the visitor-likelihood
wording ("...proportional to how likely trans visitors are to visit them...
weigh it so that the rating reflects the local regime impacts in addition to
the national picture"), and the regimes paragraphs are regenerated with
claim-level grounding (v2). Validation run: re-run the US-locked and NPL-locked
20-call waves (same design; UK stays cancelled) and compare to v1 results
(US 0.346±0.046, NPL 0.563±0.021). All draws reported; no value targets.
Note: visitor-likelihood weighting is model judgment — the corpus carries no
arrival statistics.
