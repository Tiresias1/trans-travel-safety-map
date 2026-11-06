# Where the pipeline loses Nepal–UK separation (root cause)

## The instruments
- **Raw country judgement** (redo_c4 pairwise, rater deepseek-v4.1-flash):
  - UK ~0.42–0.46. The `why` fields explicitly apply rule 19 tier-1: "state-imposed
    birth-sex ward, strip-search and prison rules plus hostile media (tier 1)",
    "tier-1 universal exposures: birth-sex strip-search, prison and hospital ward
    placement by sex, one care-denial death". This is CORRECT.
  - Nepal ~0.55.
  - => gap ~ -0.11. Matches the rubric battery (Nepal clearly safer).
- **nationalFrameworkScore**: NPL 0.5596, GBR 0.4435 => gap -0.116. (≈ raw judgement.)
- **Published country score** = "destination summary: mean of measured divisions":
  - NPL 0.5018 (mean of 7 provinces), GBR 0.4744 (mean of 16 units) => gap -0.028.

## The compression (ROOT CAUSE)
The published score OVERRIDES the correct country judgement with a mean of divisions,
and that mean compresses the gap:
- NPL division mean 0.502 is **-0.058 BELOW** its framework 0.560
  (provinces vary 0.45-0.56; Province 2 0.452, Lumbini 0.451 pull down; Bagmati 0.556,
   Gandaki 0.561 sit near the framework).
- GBR division mean 0.474 is **+0.031 ABOVE** its framework 0.444
  (every division >= 0.461; England 0.485, Wales 0.481, Scotland 0.478, NI 0.461).

Mechanism: the UK's **national tier-1 exposure** (birth-sex strip-search, prison/ward
placement, Cass, foreign-GRC refusal) is UK-wide policy, correctly scored at the country
level, but **under-propagated to the sub-national divisions** (England etc. score above
the country judgement). Nepal's provinces diverge downward on local enforcement gaps.
Averaging divisions therefore pulls Nepal down and the UK up, converging them.

## Secondary issue
The UK's "mean of 16 divisions" conflates **UK-proper** (England/Wales/Scotland/NI,
mean 0.476) with **12 Overseas Territories / Crown Dependencies** (Gibraltar, Falklands,
Isle of Man, Cayman, Pitcairn, Turks & Caicos, Guernsey, St Helena, BVI, Bermuda,
Montserrat, Anguilla 0.386). "UK" mixes London/Edinburgh with Anguilla/Pitcairn — a
travel destination should not be the mean of these. (UK-proper alone is 0.476, so this
conflation is a design issue but not the main cause of the Nepal gap.)

## Gradient of separation
battery (rubric) -0.206  >  framework/raw judgement -0.116  >  published (div mean) -0.028

## Where the failure sits (Sol's triage)
- Raw judgement: **correct** (rule 19 tier-1 applied to UK).
- Aggregation/reaggregation: **WHERE IT IS LOST** (div mean overrides the country
  judgement; national tier-1 not propagated to divisions).
- Calibration: secondary (divergence of divisions from framework).

## Fix direction (not yet applied)
Ensure the national tier-1 exposure is carried by every division (so UK divisions reflect
the UK-wide policy), OR make the published country score respect the country-level
judgement rather than blindly averaging divisions. Also de-conflate UK-proper from its
overseas territories. Verify against the rubric battery before re-settling.
