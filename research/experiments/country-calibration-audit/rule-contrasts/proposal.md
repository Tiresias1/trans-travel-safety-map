# Two candidate prompt variants for investigation

**Status:** read-only proposal; neither variant is selected or validated. No production files were changed and no scoring calls were made. Source quotations below were re-read from the current files.

Each complete candidate consists of **the shared replacements plus its variant-specific replacements** below; all other text remains unchanged. “Before” blocks are verbatim source passages. These are text-replacement proposals, not an applied diff.

## 1. What the alternatives mean

| Factor | A — Conditional-consequence | B — Institutional-exposure |
|---|---|---|
| Consequences once trans status is known | Included | Included |
| Frequency of harmful treatment once known, enforcement and remedy | Included | Included |
| Coercive disclosure, intrusive examination, registration burden, onward dissemination | Included as harms/practices in themselves | Included as harms/practices in themselves |
| State-engineered increase in discovery probability, **without another difference in treatment** | Recorded separately; not an independent scalar input | Included as a separate institutional exposure |
| Personal ability to pass, conceal, remain silent, avoid facilities or change itinerary | No mitigating credit | No mitigating credit |
| General outing probability from appearance, social cues or traveller characteristics | Not a scalar input | Not a scalar input |
| Conditional events | Assess documented triggers; do not assume occurrence | Same |
| Geography, datedness, operation, consequence and effective remedy | Required | Required |

The distinction is deliberately narrow: **does documented state-engineered discovery have an independent rating contribution beyond the harms of the practice and consequences after discovery?** Neither candidate uses a probability-times-severity formula.

---

## 2. Shared replacements for both candidates

### S1 — Add explicit scope discipline and preserve undefined intermediates

`tools/blind_pairwise.py:181–183`

**Before**
```text
10. 0.00 means a trans visitor who is outed faces near-certain imprisonment and likely execution.
    1.00 means law and society fully accept trans people with no discrimination or judgement
    (within the bounds of reason in that no society is 100 percent homogenous).
```

**After**
```text
10. 0.00 means a trans visitor who is outed faces near-certain imprisonment and likely execution.
    1.00 means law and society fully accept trans people with no discrimination or judgement
    (within the bounds of reason in that no society is 100 percent homogenous).
    Intermediate points have no fixed definitions. Do not infer equal intervals or
    mandatory numerical gaps from the severity ladder, evidence categories or band labels.
    For each material exposure or protection, identify its documented geography,
    effective date, institutional scope, trigger, visitor relevance, consequences and
    operating remedy. Distinguish policy coverage from encountering its trigger and
    from suffering its consequences. Missing information is uncertainty, not proof of
    either safety or harm. Do not give credit for passing, stealth, silence or avoidance.
```

### S2 — Replace universal occurrence with scoped coverage

`tools/blind_pairwise.py:276–283`

**Before**
```text
    - **Universal-exposure measures** — policies or practices that reach every trans
      visitor, every crossing, every time: facility-access restrictions (bathroom bills),
      document/ID-examination mismatches, mandatory marker disclosure, surveillance or
      registration of visibly trans people. These are a continuous, inescapable exposure
      for all travellers to the jurisdiction. Their weight is not diluted by the fact that
      most exposures resolve without arrest — the possibility is carried by everyone.
```

**After**
```text
    - **Broadly applicable institutional measures** — facility-access restrictions,
      document checks, mandatory marker disclosure, surveillance or registration.
      Establish whom each measure covers, where and when it operates, and what
      triggers it. Universal coverage within a specified domain does not establish
      universal encounter or harm. Few prosecutions do not by themselves establish
      little burden: exclusion, intrusive examination, disclosure and service denial
      may themselves be consequences. Apply rules 9 and 10b to discovery probability.
```

### S3 — Remove the worst-feature ranking mandate and stealth justification

Replace the passage in `tools/blind_pairwise.py:297–317` below.

**Before**
```text
    Universal-exposure measures and organised targeting both outrank scattered incidents,
    baseline-elevated violence, or unenforced statutes.
    PRECEDENCE LADDER (use this to compare two dossiers, not intuition): rank the worst
    documented feature of each jurisdiction and compare tiers, not impressions:
      (1) state-imposed universal exposure with no working remedy — facility exclusion
          by birth sex, custody placement by birth sex, strip-search by birth sex,
          documents that cannot be made to match, care denial in emergency;
      (2) state-tolerated or state-directed targeting — police extortion, raids, arrests
          for presentation, official calls for exclusion;
      (3) documented societal hostility with THIN OR NO recourse — harassment and
          discrimination that the traveller has no realistic way to remedy;
      (4) dated or scattered incidents — a decade-old case, isolated events;
      (5) paper protections not shown to operate.
    A dossier whose worst feature is tier 1 rates MATERIALLY below one whose worst
    feature is tier 3. Societal disapproval — "locals may not accept you as trans" — is
    tier 3 language at most, and it does NOT cancel a tier-1 exposure: the traveller can
    often pass, avoid, or leave a disapproving society, but cannot pass a strip-search,
    choose her own cell, or talk her way out of a ward ban. State-imposed exposures
    follow her and are enforced by the institutions themselves. Two dossiers with the same number
    of documented murders but different surrounding signals (near-baseline violence vs.
    organised sweeps) must receive different ratings, and the reasoning should say why.
```

**After**
```text
    Distinguish operative institutional restrictions without working remedy;
    state-tolerated or state-directed targeting; societal hostility without realistic
    recourse; dated or scattered incidents; and protections not shown to operate.
    These distinctions guide evidence assessment, not automatic rankings or numerical
    gaps. Compare severity, documented frequency, coverage, triggers, datedness and
    remedy across the complete dossiers. Polite social life does not erase an
    institutional restriction, and an institutional restriction does not erase
    documented societal harm. Do not discount hostility because a traveller could
    pass, avoid it or leave. Equal incident counts can support different assessments
    where the evidence distinguishes background violence from organised targeting;
    explain the distinction rather than forcing unequal scores.
```

This retains the substantive categories but removes the unconditional ranking rule. Without this replacement, scope-qualified conditional events could still force an overall ranking by their worst possible consequence.

### S4 — Replace rule 15’s inevitability claim

`tools/blind_pairwise.py:318–323`

**Before**
```text
15. **Universal-exposure measures are traveller-facing by definition.** When a rule or
    practice applies to everyone presenting as a gender different from their documents —
    bathrooms, changing rooms, custody placement, checkpoints, hospital wards — the
    exposure is unavoidable for the outed or outable traveller regardless of how often it
    is enforced against locals. Rate the possibility everyone carries, not the
    prosecutions that actually happened.
```

**After**
```text
15. **Institutional coverage and conditional events are distinct.** A rule covering
    people whose presentation differs from their documents may reach visitors, but
    establish its actual scope. Custody placement requires detention; ward placement
    requires admission; a document-mismatch rule requires the specified mismatch.
    Being outed does not establish these additional triggers. Assess the documented
    treatment when applicable and evidence about its operation. Neither assume every
    visitor encounters it nor mitigate it by recommending concealment or avoidance.
```

### S5 — Preserve three distinct social/institutional categories without automatic weight

`tools/blind_pairwise.py:360–361`

**Before**
```text
          The person is an ODDITY, not a threat. Very low weight: it is uncomfortable,
          not dangerous, and it rarely escalates.
```

**After**
```text
          The person is treated as an ODDITY, not a threat. Distinguish discomfort
          from intimidation or danger; do not infer escalation without evidence.
```

`tools/blind_pairwise.py:366–371`

**Before**
```text
      (c) STATE THREAT-FRAMING — the law and institutions themselves treat trans
          people as a threat: excluding them from women's spaces on the premise of
          risk, placing them in cells by birth sex, stripping them in front of the sex
          they are not, restricting their access to emergency care. Tier 1 weight
          under rule 15, regardless of how polite street-level life is.
```

**After**
```text
      (c) STATE THREAT-FRAMING — officials, law or institutions portray trans people
          as threats. Distinguish official rhetoric from operative institutional
          treatment: facility exclusion, custody placement, intrusive searches or
          care restrictions may have additional, documented consequences. Establish
          each claim's scope, date, trigger and operation; do not infer a policy's
          motive solely from its existence or treat rhetoric alone as proof of
          implementation. Polite street-level life does not cancel documented
          institutional harm.
```

Keep rule 19(b)’s distinction between threat-framing and curiosity, including the possibility of confrontation or violence. The replacement does not require hostile treatment to be impolite or require harm before an operative restriction counts.

### S6 — Remove mandatory intermediate placement

`tools/blind_pairwise.py:402–411`

**Before**
```text
    BAND IMPLICATION — "no criminalisation" is not a floor: a jurisdiction whose
    dossier documents universal-exposure practices (facility exclusion by birth
    sex, birth-sex custody placement with reported harm, border document friction
    for outed travellers) or discrimination prevalence at scale, WITHOUT a
    documented remedy that actually works (enforcement changing outcomes, not
    oversight findings recurring), sits in the Elevated Risk band even with no
    criminal statute on the books. "No criminalisation plus functioning
    institutions" does not anchor a jurisdiction at Reduced Risk; the documented
    exposures subtract through the band. Recourse reduces the deduction only
    where the record shows it working.
```

**After**
```text
    No criminalisation is not a numerical floor. Assess documented institutional
    restrictions, border friction and discrimination in their actual settings,
    including consequences and remedies. Functioning institutions mitigate only
    where the record shows them providing relevant protection or relief.
    None of these features mandates an intermediate band or numerical gap.
```

Also replace this exact substring in rule 21 (`395–398`):

**Before**
```text
    everyday-exposure signal for the settings the survey covers — the same tier
    as universal-exposure measures, not a background attitude note.
```

**After**
```text
    everyday-exposure signal for the settings the survey covers, subject to rule 17
    and documented visitor applicability, not merely a background attitude note.
```

### S7 — Remove prescribed spacing while retaining evidence distinctions

Within rule 13, `tools/blind_pairwise.py:247–271`, make these exact substring replacements:

**Before**
```text
only moderately below jurisdictions documenting both comparable acceptance AND
    working protections.
```

**After**
```text
below otherwise comparable jurisdictions documenting both comparable acceptance AND
    working protections, without a prescribed numerical gap.
```

**Before**
```text
A latent tangential statute
    plus open questions plus thin formal recourse hold the jurisdiction a step below
    the acceptance-with-protections tier — a step, not a tier.
```

**After**
```text
Assess a latent tangential statute,
    open questions and thin formal recourse without assigning them a prescribed
    step, tier or numerical gap.
```

**Before**
```text
PROTECTIVE OPERATING REGIMES raise a score materially above the parent average
```

**After**
```text
PROTECTIVE OPERATING REGIMES support a safer local assessment
```

**Before**
```text
visitor-facing restrictions sits well above the national line, and recorded
```

**After**
```text
visitor-facing restrictions supports a safer assessment than otherwise comparable
    conditions without those protections, and recorded
```

These changes do not discard working visitor protections; they remove unsupported magnitude prescriptions.

### S8 — Qualify structural extrapolation in both included texts

Insert immediately after the final thin-data rule’s heading sentence at `tools/blind_pairwise.py:412`:

**Before**
```text
13. **Weak signals extrapolate; "unknown" is not the midpoint.** When a dossier is thin,
```

**After**
```text
13. **Weak signals extrapolate; "unknown" is not the midpoint.** Missing domestic
    recognition machinery is a contextual signal only, subject to rule 1; do not
    infer a direct visitor exposure from it. Distinguish sourced claims from
    explicitly uncertain model inference and identify the basis of each inference.
    When a dossier is thin,
```

For the taxonomy, `research/outing-risk-taxonomy.md:188–194`:

**Before**
```text
## Thin-data extrapolation (2026-10-03 addition)
```

**After**
```text
## Thin-data extrapolation (2026-10-03 addition)
Missing domestic recognition machinery is a contextual signal only, not a direct
visitor exposure without evidence of visitor reach. Distinguish sourced claims
from explicitly uncertain model inference and identify each inference's basis.
```

The existing remainder still asks for extrapolation rather than a midpoint default; the added qualification prevents recognition absence from overriding rule 1.

### S9 — Align the taxonomy endpoint

`research/outing-risk-taxonomy.md:13`

**Before**
```text
0.0: Trans visitors have a high risk of being outed and outright executed for being trans. The absolute extreme end of "DO NOT VISIT"
```

**After**
```text
0.00: A trans visitor who is outed faces near-certain imprisonment and likely execution. The absolute extreme end of "DO NOT VISIT"
```

### S10 — Align taxonomy coverage and mitigation language

`research/outing-risk-taxonomy.md:171–175`

**Before**
```text
- **Universal-exposure measures** reach EVERY trans visitor every time: facility-access
  restrictions (bathroom bills), document/ID-marker mismatches at any checkpoint,
  mandatory marker disclosure, registration of visibly trans people. Continuous,
  inescapable exposure for all travellers — weight by the possibility everyone carries,
  not the prosecutions that actually happened.
```

**After**
```text
- **Broadly applicable institutional measures** include facility restrictions,
  document checks, mandatory marker disclosure and registration. Establish their
  geography, effective dates, covered population, triggers, consequences and remedies.
  Universal coverage within a domain does not establish universal encounter or harm.
  Few prosecutions do not establish absence of exclusion, intrusion or disclosure harm.
  Do not mitigate these measures by crediting passing, stealth or avoidance.
```

Two further exact bullet replacements avoid treating silence or merely theoretical protection as established mitigation (`135–140`):

**Before**
```text
- No documented trans killings (or enforcement works)
- Hate-crime law covering GI (recourse — theoretical but real)
- Functional institutions (police/courts will act, even imperfectly)
```

**After**
```text
- Evidence about trans-specific violence and effective responses; absence of reports alone is not established safety
- Hate-crime law covering GI, distinguishing formal availability from documented operation
- Functional institutions where the record supports relevant protection or relief
```

---

## 3. Variant-specific wording

### Variant A — Conditional-consequence

#### A1 — Replace rule 9

`tools/blind_pairwise.py:175–179`

**Before**
```text
9. **Severity dominates probability of outing.** Every trans person carries some baseline
probability of being outed. What separates say 0.9 from 0.2 is mostly what happens *after*
the outing, and whether the state is the perpetrator, a bystander, or a protector. That said,
deliberate efforts by the state to out trans people ramp up the risk of outing, and thus
the odds of adverse consequences to a trans traveler.
```

For literal replacement, retain the source’s four-space indentation on continuation lines.

**After**
```text
9. **Assess consequences conditional on trans status being known.** Consider severity,
    documented frequency of harmful treatment once known, institutional conduct and
    effective protection. Do not estimate or multiply by the probability of becoming
    known. Distinguish knowledge of trans status from additional event triggers.
```

#### A2 — Replace rule 10b

`tools/blind_pairwise.py:185–195`

**Before**
```text
10b. **The score is what happens if the traveller is outed, not the probability of being
    outed.** Do not give a jurisdiction credit because a visitor could pass, stay silent, or
    avoid scrutiny: that is a property of the traveller and the itinerary, not of the place,
    and it evaporates the moment a passport is checked, an emergency happens, or a stranger
    takes an interest. Conversely, do not add a penalty merely because a jurisdiction is
    small or highly visible. Rate the consequences that follow discovery. Where a dossier
    shows that discovery itself is engineered — mandatory marker disclosure, registration,
    surveillance, checkpoint checking — that raising of discovery probability is itself part
    of the exposure and is rated.
```

**After**
```text
10b. **Do not credit concealment or rate discovery probability.** Give no credit for
    passing, stealth, silence or avoidance, and no penalty merely for small size or
    visibility. Record state-engineered discovery separately. Include documented
    coercion, intrusive examination, registration burdens, dissemination and subsequent
    treatment as harms or institutional practices in themselves. An increase in the
    probability of discovery alone is not an independent contribution to this score.
    Do not count the same practice or consequence twice.
```

#### A3 — Replace the product sentence

`tools/blind_pairwise.py:625–626`

**Before**
```text
The score integrates **probability of being outed** × **severity of what happens if outed**,
across every axis below.
```

**After**
```text
Assess consequences conditional on trans status being known, across the applicable
axes below. Discovery probability is not a multiplier or an independent score input;
apply rules 9 and 10b to discovery practices and their harms.
```

#### A4 — Taxonomy discovery language

Replace the complete paragraph at `research/outing-risk-taxonomy.md:5`:

**Before**
```text
Two dimensions always apply: **probability of being outed** (documents routinely checked? scanners? social cues? police spot-checks?) and **severity if outed** (discretion-tolerant society vs. catastrophic consequences).  But do consider that every trans person always bears some probability of being outed, even if there's no "surveilance"; consequences are a more important aspect than percentage.  Also keep in mind the difference between laws on the books vs. how consistently they're enforced.
```

**After**
```text
Assess severity and documented frequency of harmful treatment conditional on trans
status being known, including whether the state perpetrates harm, tolerates it or
provides effective protection. Record discovery practices, but do not score discovery
probability itself. Coercion, intrusive examination, registration burdens, dissemination
and subsequent treatment can be harms in themselves. Distinguish laws on the books
from operation and enforcement, and known status from additional event triggers.
```

`research/outing-risk-taxonomy.md:159–160`

**Before**
```text
2. Score = probability-of-outing × severity-if-outed, integrated across the axes the
   country's situation makes salient.
```

**After**
```text
2. Assess applicable axes conditional on trans status being known. Do not multiply
   by discovery probability; apply the discovery-practice distinction stated above.
```

`research/outing-risk-taxonomy.md:103–105`

**Before**
```text
### K. State & media climate (probability modifier, not standalone)
- Government/media demonization campaigns raising likelihood & severity of all axes
- Surveillance states (device/social monitoring raising discovery probability)
```

**After**
```text
### K. State & media climate (context and documented effects, not a discovery multiplier)
- Government/media demonization: distinguish rhetoric from documented treatment and consequences
- Surveillance: record discovery practices and their harms; do not score increased discovery probability alone
```

### Variant B — Institutional-exposure

Apply the same shared changes, but use these replacements instead of A1–A4.

#### B1 — Replace rule 9’s same original passage

**After**
```text
9. **Assess consequences and documented institutional discovery exposure.** Consider
    severity, documented frequency of harmful treatment, institutional conduct and
    effective protection. Separately consider documented state-engineered discovery.
    Do not estimate a traveller's personal chance of passing or use a probability-times-
    severity formula. Distinguish knowledge of trans status from additional event triggers.
```

#### B2 — Replace rule 10b’s same original passage

**After**
```text
10b. **Do not credit concealment; distinguish institutional discovery from personal
    visibility.** Give no credit for passing, stealth, silence or avoidance, and no
    penalty merely for small size or visibility. Documented mandatory disclosure,
    targeted registration, surveillance or checkpoint practices may independently
    increase institutional exposure by engineering discovery. Establish their scope,
    operation and triggers rather than assuming every visitor encounters them.
    Include coercion, intrusion, registration burdens, dissemination and subsequent
    treatment where documented. Identify the discovery contribution separately and
    do not count the same practice or consequence twice.
```

#### B3 — Replace the same product sentence

**After**
```text
Assess consequences when trans status is known and, separately, documented
state-engineered discovery exposure across the applicable axes below. Do not use a
probability-times-severity formula or credit personal concealment; apply rules 9 and 10b.
```

Also replace the task qualification at `tools/blind_pairwise.py:608`:

**Before**
```text
**transgender visitor** to that jurisdiction if they are discovered or outed there.
```

**After**
```text
**transgender visitor** to that jurisdiction: consequences when discovered or outed,
together with documented state-engineered discovery exposure under rules 9 and 10b.
```

Without this change, B would still begin by defining a purely conditional task.

#### B4 — Replace the same taxonomy paragraph, guidance item and K passage

**After — introductory paragraph**
```text
Assess consequences when trans status is known and, separately, documented
state-engineered discovery exposure. Mandatory disclosure, targeted registration,
surveillance or checkpoint practices may contribute independently where their scope,
operation and triggers are documented. Do not estimate personal passing probabilities
or use a probability-times-severity formula. Include documented harms of the practices
and subsequent treatment without double counting. Distinguish laws on the books from
operation and enforcement, and known status from additional event triggers.
```

**After — researcher guidance item 2**
```text
2. Assess applicable axes for consequences when known and documented state-engineered
   discovery exposure. Keep their contributions distinct; do not multiply probabilities
   or credit personal concealment.
```

**After — K heading and first two bullets**
```text
### K. State & media climate (context, documented effects and institutional discovery)
- Government/media demonization: distinguish rhetoric from documented treatment and consequences
- Surveillance: assess documented state-engineered discovery under the stated scope and trigger requirements
```

---

## 4. Remaining conflicts and boundaries

These proposals are **not safe to copy into every production lane without further review**:

1. **Literal quotation correction:** A1’s displayed “before” paragraph above normalizes continuation indentation for readability; the actual source includes four spaces on each continuation line. All wording is unchanged. Any implementation should use the literal source block, not whitespace-insensitive prose surgery.

2. **Rule 12 still imposes parent-relative magnitude and arithmetic.**  
   `tools/blind_pairwise.py:220–232` requires material separation, starts at the parent score and constrains position against its average. This is outside the proposed isolated-country diagnostic. It must not be represented as validated by either discovery alternative. A broader deployment would require replacing its prescribed magnitude/arithmetic while retaining inheritance of **actually applicable** rules and evidence.

3. **The separate ADM1 prompt remains additive and overstates identical applicability.**  
   `tools/blind_pairwise.py:427–434` says national score plus deviation and that national factors are identical across divisions. Neither country candidate establishes this. A local diagnostic must supply the complete national assessment, check each claim’s local applicability, and compare direct local assessment with explicit-difference assessment—not silently reuse that instruction.

4. **Rule 20 overgeneralizes the separation between residents and visitors.**  
   `tools/blind_pairwise.py:374–384` says visitors do not enter family-related local spheres, while taxonomy axis J expressly includes family-visiting travellers. For a complete deployed prompt, replace the exact sentence:
   > `A visitor does not enter that sphere.`  
   with:
   > `Do not presume that visitors enter those settings; establish visitor relevance, including documented family-visiting or diaspora exposures.`

5. **Frequency instructions need conditional reading.**  
   Rule 14’s unchanged opening and extreme-outcome discussion (`274–296`) remain compatible with A only when frequency means harmful treatment **conditional on known status and stated triggers**, not frequency of becoming known. A’s replacement rule 9 makes this explicit. Reviewers should test whether models nevertheless revert to the old product interpretation.

6. **Diagnostic environment switches can invalidate both variants.**  
   `REVERT_ENDPOINT` can restore an “or execution” endpoint, and `STRIP_RULE_10B` can remove scope instructions (`tools/blind_pairwise.py:574–596`). Any future diagnostic must freeze the fully rendered prompt and prohibit these transformations. Preserve the conjunction in the endpoint.

7. **Unchanged instructions are not independently endorsed.**  
   In particular, rule 16’s categorical treatment of undercounts and background rates raises separate evidentiary questions. It is not changed here because altering it would confound the narrow discovery comparison. If a test dossier depends on that contested treatment, exclude it from this diagnostic or review it separately.

The band legend may remain as orientation under shared S1/S6; it supplies no mandatory intermediate placement. Continuous output and two decimal places still do **not** establish interval-scale meaning.

## 5. Sharply bounded diagnostic

**No live execution is authorized by this proposal.**

### Materials

Prepare six short fictional dossier pairs with realistic, internally consistent evidence. No country identities, existing scores, fixed anchors or intended ranking:

1. **Discovery-only contrast:** targeted mandatory disclosure versus confidential ordinary processing; subsequent treatment and all documented direct burdens explicitly held constant. This is the primary A/B distinction, although a truly harm-free discovery intervention is necessarily somewhat artificial.
2. **Intrusion contrast:** same discovery result, but one process includes a documented invasive examination. Both candidates should recognize the additional harm.
3. **Scope contrast:** identical restriction applies nationally versus only in a named institution; do not imply the institution is encountered by all visitors.
4. **Trigger contrast:** custody-placement rule versus an otherwise matched dossier with no such rule; explicitly state that detention frequency is unknown.
5. **Date/remedy contrast:** current operative restriction versus documented repeal with implemented relief; retain the historical incident in both.
6. **Social-category control:** curiosity versus threats, with no invented enforcement or violence. Add an official statement without implementation evidence to test whether rhetoric is automatically converted into an operative policy.

Add **two negative-control pairs**:
- identical evidence with only formatting/order changed;
- identical trans-specific evidence with an unrelated general-travel hazard added.

### Review and eventual run ceiling

- Two independent human reviewers first classify coverage, triggers, provenance and expected **reasoning distinctions**, without seeing scores or each other’s conclusions. Retain disagreement; a third reviewer adjudicates factual ambiguity, not desired ratings.
- Only after approval: eight pairs × two prompt variants × two independent model families × two presentation orders = **64 calls maximum**. Fresh contexts; interleave conditions and orders over time. No retries selected for favorable output.
- Preserve rendered prompts, model/settings, timestamps, all outputs and failures. Collect a separate structured rationale identifying included/excluded discovery effects, scope and uncertainty; do not silently expand the production output schema.

### Predeclared interpretation and failures

- **Semantic failure:** A independently penalizes discovery probability alone, or B credits personal stealth; either assumes custody, admission or mismatch merely because status is known.
- **Evidence failure:** invented enforcement, dates, remedies or geographic reach.
- **Control failure:** unrelated general danger drives trans-specific reasoning, or identical-copy/order variation obscures the claimed experimental contrast.
- **Inconclusive:** independent reviewers cannot agree what the controlled evidence changes, or numerical variation is comparable to the observed contrast.
- Compare rationale, direction, ties and repeat/order sensitivity first. Numerical differences are descriptive instrument outputs, not calibrated risk increments. Do not require a minimum gap, a target score, or any country ranking.

## Review verdict

**BLOCK** on production adoption of either variant as a validated methodology. **Suitable for further prompt review and a separately approved bounded diagnostic**, subject to literal replacement verification and the stated lane restrictions.