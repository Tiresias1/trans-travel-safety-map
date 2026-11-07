# Correction note — pilot2 order-contrast error and its empirical limits

This is a note, not a rewrite: `pilot2-report.md` and `pilot2-analysis.json`
are left exactly as they are, and this file records what a reader of the
pilot2 report should correct in their head. The corrected numbers live in the
working-tree `pilot2-analysis.json` produced by the parent's fixes to
`pilot2-analyze.py`, with the check now added in `pilot2-validate.py`.

**Section 6's sign error for second-listed countries.** The original analysis
picked the "first" and "second" presentation groups for each country using the
pair key itself, so for the country listed *second* in a pair it swapped the
two groups: the row called "first" was actually the draw in which that country
was presented second. Every such row has its contrast sign inverted and its
first/second counts swapped — 9 of the 18 rows (PRY in all three of its pairs,
FSM in all three, GBR in USA–GBR and NPL–GBR, and NPL in USA–NPL). For
example, GBR in USA–GBR was reported as −0.015 (0.470 first vs 0.485 second)
and is corrected to +0.015 (0.485 vs 0.470); NPL in USA–NPL flips from +0.040
to −0.040; the partner flag on GBR–FSM flips from −0.025 to +0.025. USA's four
rows are unaffected because USA is always first-listed. The downstream
summaries change accordingly: GBR goes from "mixed directions" to three
positive and one zero, and NPL's "first > second in all four pairs" becomes
three of four. The strict pre-registered warning (same-direction contrast
exceeding within-cell variation in at least three of a target's four pairs) is
still not met by any target after the correction.

**The identical-copy controls are confounded with run time.** The A-first
orientation ran only in blocks 1 and 3 (12:18–12:19 and 12:24–12:25 UTC) and
the B-first orientation only in blocks 2 and 4 (12:21–12:23 and 12:27–12:29),
never interleaved, with two draws per orientation. The report's section 7
"orientation shift" — most strikingly USA's −0.120 — therefore cannot be
separated from time, drift, or block order. It should be read as
position/label *or* time sensitivity, not as a measured label effect.

**The earlier robustness claim for the UK/Nepal ordering was too strong.**
`ROUNDUP.md` said the relative ordering NPL > GBR > USA is "stable everywhere
far beyond noise", and the report's direction statistics partly supported
that. After the sign correction the direction patterns change (GBR and NPL
both), and the same-instrument copy controls show self-ratings drifting by up
to 0.120 (USA) and 0.035 (GBR) within a single run. What actually survives,
re-checked directly against `pilot2-results.ndjson`, is narrower: the pooled
per-country gaps in section 9 — which come from per-cell means and were never
affected by the sign bug — hold with the same sign in both presentation orders
(NPL exceeds GBR by +0.1575 and +0.125 in the two orders; USA sits below both
in both orders) and exceed typical within-cell variation. That is an
order-robust *pooled gap*, not evidence that the instrument, the direction
patterns, or any absolute level is robust. With four draws per cell, one
model, and one run, nothing here validates any score, and no pilot2 number
should be treated as confirming or refuting a published value.
