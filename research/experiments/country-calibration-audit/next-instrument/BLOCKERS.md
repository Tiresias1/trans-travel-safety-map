# Blocking issues for parent review — next-instrument (recorded, deliberately not resolved here)

These were raised by the independent review
(`.../outputs/b37c950e-a9a3-4250-8990-12b5dcfdc986/audit/next-instrument-review.md`)
and by the task contract. They are engineering-blockers and methodology
questions that this experiment must NOT resolve on its own. Nothing below has
been "fixed" by picking a rubric or changing what the scale means; no numeric
scoring outcome is claimed, produced, or validated by this instrument.

1. **Rubric divergence (comparability verdict: not comparable with current
   production scores).** The national prompts carry 12 condensed rules
   (`CURATED_RULES`), not the 21-rule `RATING_RULES` of rubric r2026-11-13.
   The region prompt **omits the rating rules entirely** — so the national
   baseline and the local delta would be produced under different rubrics.
   Specific dropped clauses (from the review): the band-implication clause
   ("no criminalisation is not a floor"); the survey-prevalence tier; the
   engineered-discovery half of rule 10b (probability of outing raised by
   state measures is itself rated); the no-penalty-for-small-jurisdiction
   clause (relevant to VAT); rule 13's factor-kind ranking and the
   protective-operating-regimes clause (relevant to protective regions); the
   full five-tier precedence ladder; the past-snapshot clause. The condensed
   scale text also *invents* a "no remembered score" restriction with no
   production counterpart, and the instrument stamps only `INSTRUMENT_VERSION`
   — no `rubricVersion`. **Restoring, versioning, or explicitly accepting this
   divergence is a methodology decision for the parent.** It must not be
   solved by copying the production rules blindly, because of issue 2.

2. **The original production prompt's probability-of-outing contradiction.**
   The taxonomy states the score integrates *probability of being outed ×
   severity if outed*; rating rule 9 says *severity dominates probability of
   outing*; rule 10b says rate *what happens if outed, not the probability*,
   yet also rates engineered discovery as part of the exposure. These three
   statements do not fully agree in the current production prompt. The
   contradiction is inherited-from-production, unresolved, and recorded here
   so it is neither silently copied into a new instrument nor silently
   "fixed" by condensation. Parent must decide.

3. **Unvalidated additive / interval-scale assumption.** `local_estimate =
   candidate_national_baseline + local_delta` assumes the 0.00–1.00 scale is
   an interval scale (translation-invariant), while the scale's own bands are
   declared "orientation only". The engineering fix in this pass only makes
   the computation **fail closed outside [0.0, 1.0] without clamping**; the
   assumption itself remains unvalidated and must be reviewed before any run.

4. **Bagmati provenance issue.** Bagmati's record has no region-specific
   sources: its `sources` are the same three country-level Nepal URLs shared
   by every NPL unit (identical to Karnali's "country-level, never local"
   list). Mechanically enforced now: the local-evidence allowlist contains
   only the region's own record text, the URLs are rendered under a
   "COUNTRY-LEVEL RECORD SOURCES — NOT LOCAL EVIDENCE" heading, and citing
   them as local evidence is rejected by validation. The underlying provenance
   problem (there is no sourced local evidence beyond one descriptive
   sentence) remains and needs a human decision.

5. **Blind identity leaks.** The national dossiers are *name-withheld*, not
   identity-stripped at content level: GBR is identifiable ("NHS",
   "For Women Scotland v Scottish Ministers"), USA ("executive order signed
   20 January 2025", "K-12"), VAT ("1889 code", "sovereign state in 1929"),
   NPL ("Sunil Babu Pant", "Muluki Ain"). No mechanical leak gate analogous
   to `tools/check_blind.py` runs here; the forbidden-key scan only excludes
   scores/aggregates. Read "identity withheld" as "name withheld".

6. **Absent substantive fact-verification.** Tests here prove structural
   properties (schema, scale bounds, evidence-allowlist membership,
   determinism, write/network confinement). They do not verify that any
   dossier claim is true, dated correctly, or faithfully summarised from its
   source; no claim-level verification exists anywhere in this experiment.
   This exercise **cannot and does not validate truth**, and no result from it
   may be read as validating any published or candidate score.

7. **Provider execution removed.** The live `execute` path and its network
   code were deleted unconditionally (old guard flags/env vars still fail
   closed). Re-enabling it requires the methodological review above plus a
   separate explicit implementation review.
