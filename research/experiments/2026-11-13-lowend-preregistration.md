# PREREGISTRATION — low-end anchor-extension experiment
Written before any target in this experiment was measured. 2026-11-13.

## Purpose
Reviewer hypothesis: the anchored estimator operates below its lowest anchor (0.100)
exactly where floor censoring is consequential. Test whether adding two low-end
references reduces floor dependence and comparator disagreement, and whether it improves
agreement with independent national-framework scores at the dangerous end.

## Additional reference countries (chosen BEFORE seeing target results)
Eligible frame: framework score < 0.100, blind dossier present, not an existing anchor,
never used as a validation target. Only three candidates existed:
  UGA Uganda       10 sources, 4,073 chars, framework 0.090
  NER Niger         7 sources, 5,066 chars, framework 0.093
  QAT Qatar         4 sources, 4,704 chars, framework 0.092
Selected on dossier completeness: **UGA (0.090) and NER (0.093)**. QAT rejected for
thinnest sourcing. Both are frozen at their framework scores, and neither may be a
validation target.
NOTED LIMITATION, recorded now: the frame contains no reference below 0.089, so this
experiment can only extend the ladder to ~0.09. If the low-end bias is driven by the
absence of anchors near 0.02-0.05, this design cannot fix it, and a null result will not
distinguish "anchors near 0.09 are sufficient" from "the ladder still stops too high".

## Targets (40)
Countries (20): randomly sampled from the remaining framework-score < 0.20 frame,
excluding the four existing anchors, UGA, NER, and all 40 countries used in the earlier
held-out bridge.
Divisions (20): two randomly selected divisions from each of ten parents —
  five parents with the highest floor-clamp incidence,
  five parents with framework score < 0.25 and less than 10% floor incidence.

## Design
Every target rated 12 times: 2 calls per existing anchor (BLR 0.100, CIV 0.297,
VAT 0.600, ESP 0.840) = 8, plus 2 calls per new anchor (UGA 0.090, NER 0.093) = 4.
Total 480 paired calls. Presentation order randomised. Names withheld.

Estimators compared, both prespecified, equal weight per anchor:
  A4 = mean over the four existing anchors of [anchor + (target - anchor_rating)]
  A6 = mean over all six anchors
Neither estimator is chosen after the fact.

## Preregistered outcomes (all reported, no selective reporting)
1. Country-level mean signed and absolute disagreement with independent framework scores,
   reported separately for framework < 0.20 and overall.
2. Raw (unclamped) and published floor incidence, before and after.
3. Between-anchor disagreement: sd of per-anchor estimates, and per-anchor residuals
   against framework score, for each of the six anchors individually.
4. Within-target repeat variability (the two calls per anchor).
5. Change in within-parent division differences.
6. Leave-one-anchor-out results for A4 and A6.

## Success criteria (declared in advance)
A6 would justify a production replacement only if ALL hold:
  (a) low-stratum (framework < 0.20) mean absolute disagreement falls below 0.020;
  (b) overall mean absolute disagreement does not worsen versus A4;
  (c) raw floor incidence falls materially (by at least half);
  (d) the improvement is not attributable to a single added anchor (i.e. it survives
      leave-one-anchor-out).
Uncertainty: bootstrap confidence intervals resampling by country, not by call.
These are compatibility criteria with framework ratings, not proof they are true.
