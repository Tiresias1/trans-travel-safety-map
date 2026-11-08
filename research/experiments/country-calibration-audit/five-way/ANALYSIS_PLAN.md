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
