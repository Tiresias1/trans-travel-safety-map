# Current status — 2026-11-08

This file supersedes the older handoff and roundup where they disagree. Those
files preserve historical work and assumptions; they are not current scoring
authority.

## Rules and publication state

- Country scores must be assessed independently, never calculated from
  ADM1 scores. Regional assessments should start with the full national
  comparison and then consider local differences. A national-to-regional spread
  is a diagnostic, not a target for recentering.
- No country score, ordering or frozen numeric anchor is a target. The
  currently displayed values are historical; no replacement methodology has
  been validated or deployed. A score of 0.00 means near-certain imprisonment
  and likely execution for an outed trans visitor; intermediate points have no
  fixed precise meanings. Do not credit passing, silence or avoidance.
- `tools/build_data.py` no longer reapplies the historical USA override,
  reaggregates national scores from divisions, mirrors territory scores into
  country scores, or synchronizes sparse regions to national scores. The
  anchored calibration and settlement mutation paths were retired. Other score
  writers still exist; containment is not a validated scoring algorithm.
- The historical USA override does not reproduce the archived encounter mean.
  It must not be represented as reproduced, or as a target for a new method.
- Commit `cd936cd8` updated the public About text and methodology to describe
  the limitations of the historical scores. No score was changed; the previous
  public document is preserved as a non-authoritative historical archive.

## Country feasibility diagnostics

`country-feasibility/` contains the closed v1 experiment, frozen inputs,
reviews, operational probes, receipts and the failed country attempt. Four
operational probes were dispatched, including the original truncated Gemini
probe and two explicitly adaptive follow-ups. The first full country call
stopped at the 2,000-token output limit with empty assistant content; the other
39 planned cells were not dispatched. No final country score resulted from v1.
Its partial provider reasoning contained provisional numerical judgments that
were visible to reviewers; this is a source of adaptation bias, not a result.

`country-feasibility-v2/` is a separately registered, adaptive 20-cell
feasibility design. It preserves the same core inputs, uses a larger output
allowance and requires independent score-blind review between calls. The first
call returned a completed response, but reported more reasoning tokens than
completion tokens. The predeclared usage-consistency rule stopped the run;
19 cells were not attempted. No runner-accepted score or comparison resulted,
and this version must not be resumed or retried.

The separate post-hoc analysis of the failed v2 response omits its numeric score
and cannot authorize another call. Its independent semantic review found both
supported references and material attribution and uncertainty problems; see
`country-feasibility-v2/analysis/`. In particular, it identified a conflation
of personal rhetoric and supporters' threats with official government action,
and ambiguity around missing visitor-specific evidence. This is one failed
attempt, not a representative country assessment.

Exact provider-reported costs for the four probes plus the v1 and v2 country
attempts total $0.002622058. This excludes independent reviewer usage and older
experiments. A later read-only provider lookup matched the failed v2 call's
charge but did not resolve its token-count inconsistency, and its upstream
cost differed from the saved response. It also returned a dated model identifier
rather than the requested alias. The relationship between those identifiers is
not established. See the v2 analysis metadata.
The $10 guard was local and postpaid, not a provider-enforced hard limit.
Preserve all failures, raw responses, costs and source limitations.

## Earlier findings and open work

The corrected pairwise pilot shows order and draw sensitivity; it does not
establish a reliable country ordering. See `next-instrument/pilot2-correction-note.md`.
The ADM1 shadow runs are diagnostic only: additive scale assumptions, evidence
double counting and sparse-local-evidence handling remain unresolved.
`rule-contrasts/` cannot isolate a discovery-probability effect from the other
harms bundled into its test case.

Comprehensive claim-level source verification, reliable blinding, a coherent
country-to-ADM1 interface and valid uncertainty handling remain open. The 628
staged text rewrites and 36 display-summary cases remain unreviewed and
unapplied. Do not publish experimental scores or infer safety from missing
evidence.
