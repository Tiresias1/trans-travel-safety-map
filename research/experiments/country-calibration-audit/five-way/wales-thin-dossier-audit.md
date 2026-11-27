# Wales thin-dossier audit — why Wales drew highest (0.521) in scotland-gap-round3

Date: 2026-11-27. Run audited: `runs/scotland-gap-round3-20261125/`
(report `scotland-gap-round3-report.md`, results `result-*.json`, rater
outputs `content-*.txt`). Dossiers reconstructed by rendering live
`data/admin1.json` / `data/countries.json` through
`harness.render_admin1_dossier` (Wales/Scotland/NI blind fields are
byte-identical to the round-3 snapshot in
`runs/scotland-gap-round3-20261125/pre-repair-data.json`; England/GBR
differ only by the round-3 structural fix, which moved England-only
facts from the GBR parent into England's division evidence — verified
by diff). No provider calls, no data writes, no test reruns.

## Verdict (one paragraph)

Wales's top draw is **mostly a dossier-asymmetry artifact, with a
genuine but much smaller protective core**. The parent (GBR) framework
— identical in all four nation dossiers — already carries every
tier-1 restrictive fact (biological-sex searches, struck-down prison
guidance, in-force single-sex-spaces code, foreign-certificate
non-acceptance). What differs is the *division layer*: Scotland's and
England's division evidence **restates those restrictions
divisionally and adds further operative restrictions**, while Wales's
division evidence **adds zero new restrictive operative facts and only
protective/neutral material**. Raters therefore read Scotland/England
as parent-restrictions ×2 (local specificity = intensity) and Wales
as parent + protective gloss. Two of eleven Wales draws explicitly
convert absence into a premium despite clause 5; the other nine mostly
cite *presence of protections* — but those protections are themselves
overstated in the dossier (a concluded action plan presented as a
standing programme, consultation-stage school guidance presented as an
operative duty, a never-enacted conversion ban). Wales **is**
genuinely the least restrictive of the four on devolved *delivery*
(no Holyrood-style toilet rule, no devolved prison/search guidance of
its own, school-toilet flexibility, an adult clinic since 2019), so
Wales > Scotland/NI on climate/recourse is directionally plausible —
but by Wales's own dossier admission the visitor-facing tier-1
exposures are identical, so the true edge is a small
recourse/climate premium (roughly the +0.03–0.04 seen head-to-head vs
the GBR country reference), not the +0.13 over England / +0.04 over
Scotland the finals show. **Recommendation: dossier repairs first**
(four specific repairs below, with sources); a rubric thin-data
discount is second-best and would needlessly penalise genuinely
protective thin dossiers; "accept Wales as genuinely safest" is not
supported.

## 1. What the numbers actually are

Wales OK draws (n=11, across all seven models — deepseek ×3, haiku ×2,
luna ×2, qwen/glm/muse/mimo ×1 each): mean **0.521** (sd 0.050,
range 0.44–0.61). For comparison, same-run means: Scotland 0.476
(n=16), England 0.387 (n=11), Northern Ireland 0.508 (n=11), GBR
country reference 0.500 (n=9). Finals after reseed+updates: Wales
0.519604, NI 0.483573, Scotland 0.480219, England 0.392163.

Same-call Wales margins (the cleanest evidence, since both dossiers
share the parent framework):

| Pairing | Calls | Wales − partner |
|---|---|---|
| Wales vs GBR (country format) | iters 9, 19, 29 | +0.03, +0.04, +0.03 (mean +0.033) |
| Wales vs Scotland | iters 12, 22, 32 | +0.08, +0.07, +0.04 (mean +0.063) |
| Wales vs England | iters 5, 25 | +0.11, +0.09 (mean +0.100) |
| Wales vs NI | iters 7, 17, 27 | +0.12, −0.10, +0.06 (mean +0.027, sign flips) |

The +0.033 vs GBR is the "protective gloss premium": it is what the
division layer adds when the partner is the bare parent. The larger
margins vs England (+0.10) and Scotland (+0.06) come from the
*partner's* division-layer restrictive facts, not from anything
positive in Wales beyond the same gloss. NI is the control case: it
is the thinnest dossier of all (3 sources) yet draws 0.508, and its
Wales margin flips sign — thinness alone does not mechanically
produce a top draw; **protective-only thinness** does (NI's division
layer contains real restrictive facts — blocked hate-crime inclusion,
withdrawn pupil guidance — that Wales's lacks).

## 2. Claim-by-claim dossier comparison

Coding: every sentence of each division `blindSummary` (the rendered
/division evidence as raters saw it; parent framework excluded since
it is identical across all four) classified as **restrictive-
enforcement** (documents an operative state restriction, exclusion,
or absence-of-protection), **protective** (documents an operative or
intended protection), or **neutral** (framing, history, data-status).

| Division layer | Sents | Restrictive | Protective | Neutral |
|---|---|---|---|---|
| Wales blindSummary (2,854 chars) | 14 | 3 (+1 historical) | 5 | 6 |
| Scotland blindSummary (5,896 chars) | 19 | 7–8 | 3–4 | 7–8 |
| England blindSummary post-repair (5,958 chars) | 22 | 11 | 3 | 8 |
| NI blindSummary (2,482 chars) | 15 | 3 | 1 | 11 |
| Division sources (blindSourceSummaries) | — | Wales 6, Scotland 4, England 12, NI 5 | | |
| Rendered total dossier (chars) | — | Wales 17,544; NI 16,754; Scotland 21,978; England 24,834 | | |

### Wales — the restrictive sentences (all three, quoted in full)

> "The marker rules, single-sex space enforcement and custody
> segregation a visitor encounters in this division are set by the
> national framework rather than by devolved ministers." (sent. 4)

> "For hate crime the operative framework in this division is the
> shared criminal law applying to this division and a neighbouring
> jurisdiction: the aggravated-offence provisions (sections 29 to 32
> of the 1998 aggravated-offence legislation) cover racially and
> religiously aggravated conduct only, so there is no
> transgender-specific aggravated-offence statute applying in this
> division." (sent. 11)

> "Under the 2004 gender recognition legislation, an applicant in this
> division must show they have or have had gender dysphoria, with a
> diagnosis report included in the application, and that requirement
> has not been removed there as it was in a neighbouring division in
> May 2021." (sent. 14)

Plus one historical restrictive sentence ("Transgender healthcare in
this division was historically delivered by referral to clinics in
this country's capital city."). **That is the entire restrictive
division layer.** No Wales-specific sentence about searches, custody
practice, hospital wards, toilets, sports, or school facilities
restricts anyone — because, per sentence 4, the dossier assigns all
of those to the national framework.

### Wales — the protective sentences (all five, quoted in full)

> "The devolved administration's LGBTQ+ action plan for this
> division, published in February 2023, states the aim of making this
> division the most LGBTQ+ friendly nation in Europe." (sent. 5)

> "It commits the devolved administration to pursue a
> division-specific ban on conversion practices; a working group on
> banning conversion practices was formed in December 2022 and the
> administration published its banning conversion practices document
> in May 2024." (sent. 6)

> "The first gender identity clinic in this division opened in
> September 2019, ending the default referral of adults from this
> division outside its borders." (sent. 8)

> "The devolved administration's LGBTQ+ action plan document for
> young people, posted in January 2026, forms part of the standing
> devolved inclusion programme." (sent. 9)

> "Section 66 of the 2020 sentencing legislation, in force across
> this division and the neighbouring jurisdiction since 1 December
> 2020, requires courts to treat an offence aggravated by hostility
> related to transgender identity as an aggravating factor and to
> state in open court that the offence is so aggravated." (sent. 12)

Only sentences 8 and 12 document an *operative* protection
(clinic; sentencing aggravator — both shared England&Wales law, the
latter also counted for England). Sentences 5, 6, 9 are **intent /
programme-existence** claims. The dossier's own `blindOutOfScope`
concedes the thin spots: "No policing, custody, hate-crime
prosecution or trans-specific violence data specific to the
state/province appears in these sources." and "Whether a
state/province-specific ban on conversion practices has been enacted,
and what it covers, is not established by these sources."

### The asymmetry, stated precisely

Scotland sentences 13, 15, 8 (blindSummary) are the same *kind* of
facts Wales omits divisionally: Police Scotland's biological-sex
search guidance ("searches involving the removal of more than a
jacket, gloves, headgear or footwear are conducted on the basis of
biological sex, in both custody and stop-and-search contexts"); the
SPS ruling ("struck down the prison service's non-statutory guidance
on trans custody as unlawful"); Holyrood toilets ("toilets designated
male or female would be interpreted as meaning biological sex").
England adds divisionally: the EHRC birth-certificate code, prison
allocation, the puberty-blocker pause + Tavistock closure + Bell
(3 sentences), the ward-ban plans (2 sentences), and the Joelle
death. Each of those is *additional evidence of the same national
regime operating*, yet raters systematically scored the dossier
containing more such sentences lower. Wales is the only nation whose
division layer cannot be double-counted, because it contains no
divisional restatement at all. **Wales is not under-documenting
restrictions that are known to apply divisionally in a distinct
Welsh form** (see §4 — prisons, policing standards, criminal law and
equality law genuinely are national; there is no Welsh ward ban,
no Welsh search policy, no Senedd toilet rule to report) — but the
dossier never says that affirmatively for the *devolved delivery*
domains (NHS Wales wards, South Wales/North Wales Police search
practice, Senedd facilities, school facilities), where silence is
what raters converted into safety. Scotland's dossier, by contrast,
*does* state its silences affirmatively ("No division-specific
national health service hospital-ward segregation policy or
announcement was found in the sources searched").

## 3. What raters cited — absence-as-safety leak, or presence-of-protections?

Both, in that order of importance. Counting the eleven Wales factor
matrices (`content-*.txt` / `result-*.json` `parsed` blocks):

**Explicit absence→premium (clause-5 violations, 2–3 draws).**

- iter 7 (haiku, 0.52): "Exposures are national and unaltered, and
  **no divisional hostile layer is documented, so the rating sits in
  the Elevated band above the national line**." — absence of a
  documented hostile layer is used to place Wales *above* the parent
  line. Direct leak.
- iter 32 (mimo, 0.59, the highest Wales draw): "No criminalisation,
  entry rule, registration duty or division-specific violence record
  is documented… **Absence of division-level hostility data in a
  well-documented rule-of-law state is mildly positive, not proof of
  safety.**" — the rater *names* the clause-5 rule and then admits a
  "mildly positive" premium for absence anyway. Leak, self-aware.
- iter 25 (muse, 0.52): "Its division evidence **documents no
  hospital ward-removal death, ward-ban plan, or division-specific
  birth-certificate code** beyond the national framework, and records
  a pro-LGBTQ+ action plan and local clinic." — used as the reason
  Wales sits above England. Comparing England's *documented* ward
  death against Wales's *undocumented* ward position and scoring the
  silence higher is absence-as-safety by comparison, even though the
  England ward facts are genuinely England-only.

**Correct clause-5 handling that still lands high (the majority).**

- iter 22 (deepseek, 0.50): "The absence of B-specific violence or
  entry data is not safety; it leaves those axes undocumented." —
  correct — yet the same synthesis explains Wales > Scotland by
  "it lacks A's local biological-sex toilet and prison-application
  layer", and B "adds no local toilet or prison application like
  Division A". Scotland's *documented* local application is charged
  as an exposure; Wales's *undocumented* equivalent is scored as
  non-exposure. Clause 5 forbids exactly this asymmetry ("absence of
  a division-level record is NOT evidence of non-application").
- iter 29 (luna, 0.52): "the absence of division-specific violence
  data are not evidence of safety for visitors; the latter remains
  undocumented." — correct — yet "B is somewhat safer than A because
  its local protection and recourse are more clearly documented",
  i.e. Wales wins on *documentation clarity of protections*.
- iter 12 (deepseek, 0.55): the most disciplined draw — "Devolved
  policy is comparatively supportive… but devolution does not reach
  facilities, custody, search or equality law, so these are climate
  signals, not traveller-facing offsets to the tier-1 exposures." —
  and still 0.55, +0.08 over Scotland in the same call, on the
  strength of those same "climate signals".

**Presence-of-protections citations (all eleven).** Every Wales
factor matrix credits the same four items: the s.66 sentencing
aggravator, the RRE school anti-bullying guidance (May 2025
consultation), the 2019 adult clinic, and the LGBTQ+ Action Plan /
inclusion programme. Two problems: (a) the s.66 aggravator is
England&Wales law and is *also* credited in England's dossier, so it
cannot explain Wales > England; (b) three of the four are
overstated (see §4 repairs) — the Action Plan had concluded, the
school guidance is consultation-stage, the conversion ban is
unenacted — yet raters repeatedly call them "documented and
operating" (iter 7), "operative" (iter 9: "a sentencing statute…
statutory school guidance… and a local gender-identity clinic since
2019… mitigate recourse and everyday friction"), and "statutory
school guidance mandating challenge of gender-reassignment bullying"
(iter 19, glm, the 0.61 outlier). The protective gloss is doing the
work; the absence premium is the margin on top.

Net assessment: clause 5 is *mostly* honoured in wording but
*routinely* breached in comparative effect — raters do not write
"absence = safety", they write "B documents no X" in the exposure
field and then score B above the dossier that documents X. That is
the leak, and it is structural (comparative pairwise design rewards
the thinner dossier), not a wording failure a rubric note alone
would fix.

## 4. Is Wales genuinely less restrictive on devolved matters?

Short answer: **on devolved delivery, yes modestly; on anything a
visitor actually meets, no.** Every claim below resolves to the
source named; dossier claims that research contradicts are flagged.

**Genuinely less restrictive (supports a small Wales premium).**

- *No Welsh equivalents of Scotland's devolved restrictive facts.*
  There is no Senedd toilet rule comparable to Holyrood's May 2025
  biological-sex interpretation, no Welsh prison-service guidance to
  strike down (prisons are HMPPS England & Wales; GOV.UK "Guidance
  on Prisoners who are Transgender" / member guidance applies to
  England and Wales — `gov.uk/government/publications/guidance-on-
  prisoners-who-are-transgender`), and no Welsh police search
  policy distinct from national practice. Wales's dossier sentence
  "Devolved policy does not extend to legal gender recognition,
  equality legislation or prisons" is *correct*.
- *School facilities.* The RRE statutory guidance (consultation
  May 2025, `gov.wales/.../rights-respect-equality-statutory-
  guidance.pdf`, §6.6) tells schools to let learners "choose which
  toilets they can use, for example by enabling learners to use a
  number of different toilets across the school site, or by
  providing some washrooms/toilets which are sex separate and some
  which are mixed provision" — genuinely more inclusive than NI's
  withdrawn guidance ("recommended that trans pupils be allowed to
  use changing rooms matching their gender identity", BBC 8 Sep
  2025, in NI dossier) and more flexible than a biological-sex
  mandate. But note: this is a *consultation* document (see repair
  R2), and the trans-specific national schools guidance (Action
  Plan Action 26) was still in draft in Jan 2026, "ready for a new
  Government in May 2026… fully up to date with the latest legal
  position and the finalised EHRC Code of Practice" (Welsh
  Government progress update 2024–2025, `gov.wales/lgbtq-action-plan-
  wales-progress-update`).
- *Adult healthcare access.* "The Welsh Gender Service was
  established in 2019" (Wikipedia, *LGBTQ rights in Wales*, citing
  BBC) — Wales ended default London referral for adults. Genuine,
  operative, visitor-adjacent (continuity of care).

**Not less restrictive (visitor-facing tier-1 exposures identical).**

- Single-sex spaces, searches, custody, recognition: all national,
  all admitted in Wales's own dossier. The EHRC code in force
  5 Aug 2026, BTP/Police Scotland search guidance, and the 19 June
  2026 SPS ruling reach Wales via the parent framework (plus
  HMPPS England & Wales prisoner policy: trans women housed in
  men's prisons if violent/sexual offence or male genitalia — see
  *Transgender rights in the United Kingdom*, "Transgender
  prisoners' rights"). Wales cannot opt out.
- *Children's healthcare* — Wales is arguably **more** exposed than
  the dossier suggests. The dossier buries this in
  `blindLocalsOnly`: "Public health commissioners in the state/
  province stated in March 2024 that they had no plans to develop a
  children's gender service, and parents of transgender children
  called for more help." Research confirms: WHSSC "stated in March
  2024 that they had no plans to develop a children's gender
  service in Wales" and families were "told they'd have to travel to
  London for the healthcare" (Wikipedia, *LGBTQ+ Action Plan for
  Wales*, citing BBC News 1 Mar 2024). Welsh children were thus
  routed into the England service that stopped puberty blockers in
  March 2024 (Cass/Tavistock closure — in England's dossier, and in
  *Transgender rights in the United Kingdom* for England & Wales
  Bell history). Raters *did* cite the missing children's service
  in the minors factor, but framed it as resident-facing; for a
  travelling family it is a care-denial exposure, and Wales has no
  countervailing provision Scotland lacks (Scotland's dossier notes
  its own under-18 clinic paused blockers in April 2024 in
  `blindOutOfScope`).
- *Conversion practices:* no ban enacted. Wikipedia (*LGBTQ+ Action
  Plan for Wales*): the May 2024 announcement was a Galop support
  service; "As of 2026, there have been no updates on the proposed
  service." The dossier's "commitment" language is accurate; any
  rater crediting an operative ban (none did explicitly, but the
  Action Plan's "aim" was credited as protection in iters 19/22)
  over-reads it.

**The decisive missing restrictive fact (dossier under-documents).**

The dossier records only that the Action Plan's "update page
addresses the judgment of 19 December 2025". The actual update (Welsh
Government, *LGBTQ+ Action Plan for Wales*, `gov.wales/lgbtq-action-
plan-wales`, "Supreme Court Judgment update: 19 December 2025")
reads, verbatim:

> "Following the UK Supreme Court ruling on 16 April 2025 in the
> case of For Women Scotland Ltd v The Scottish Ministers, where the
> LGBTQ+ Action Plan refers to "women" or "man", insofar as the Plan
> engages the Equality Act 2010, these references are to sex
> registered at birth. The plan is currently being reviewed in light
> of that judgment and further revisions will follow which will be
> the subject of engagement, before the revised plan is formally
> re-issued."

And the same page, "Update 18 June 2026: **The LGBTQ+ Action Plan
concluded at the end of the previous Senedd term.**" So the dossier's
"standing devolved inclusion programme" is a *concluded* plan under
review, whose own government has re-read its "women" as sex at
birth. That single fact — a devolved administration itself applying
the biological-sex interpretation to its inclusion programme — is
exactly the kind of divisional restrictive-operative sentence Wales's
layer lacks, and raters never saw it. It would not by itself reverse
the ranking, but it collapses the "protective devolved intent"
premium that all eleven draws rely on.

## 5. Recommendation: dossier repairs (facts + sources), not a rubric discount, not acceptance

**Do not accept** "Wales genuinely safest nation": on every
visitor-facing tier-1 axis (facilities, search, custody, documents)
Wales is by its own dossier identical to England/Scotland; the
residual genuine difference is climate/recourse delivery, worth
roughly the +0.03 same-call margin vs GBR, not the observed
+0.04–0.13.

**Do not apply a thin-data discount as the fix.** A rubric discount
would (a) penalise NI, whose thin dossier also contains real
protective law (May 2021 dysphoria ruling), and (b) leave the real
problem — overstated protections + missing restrictive fact +
asymmetric divisional restatement — untouched. The discount would
also be uncalibratable: Wales's thinness is *selective* (thick on
programmes, silent on delivery), not uniform.

**Repair the Wales dossier first** (each repair is a fact + a
resolving source; all sources fetched and verified during this audit):

- **R1 (restrictive, decisive).** Add the Welsh Government's 19 Dec
  2025 Supreme Court update verbatim (above) to the division
  plain summary + blindSummary, and the 18 June 2026 conclusion
  notice ("The LGBTQ+ Action Plan concluded at the end of the
  previous Senedd term"). Source: `https://www.gov.wales/
  lgbtq-action-plan-wales` (fetched 2026-11-27). This converts an
  aspirational protective claim into an operative restrictive fact
  and corrects "standing programme".
- **R2 (protective correction).** Downgrade the RRE school-guidance
  description: the May 2025 document is a *consultation* draft
  (`gov.wales/sites/default/files/consultations/2025-05/rights-
  respect-equality-statutory-guidance.pdf`), and the trans-specific
  schools guidance (Action 26) was still draft in Jan 2026 awaiting
  the May 2026 government and EHRC-Code alignment (progress update
  2024–2025, `gov.wales/lgbtq-action-plan-wales-progress-update`).
  Keep the §6.6 toilet-flexibility sentence — it is genuine — but
  stop raters reading consultation text as an operative duty.
- **R3 (protective correction).** State the conversion-practices
  position as unenacted + support service without updates as of
  2026 (Wikipedia *LGBTQ+ Action Plan for Wales*, citing Welsh
  Government 17 May 2024 pages already in the dossier). The dossier's
  `blindOutOfScope` already admits non-enactment; the blindSummary
  "commits… to pursue" should not be creditable as delivery.
- **R4 (restrictive, minors/care).** Promote the children's-service
  absence from `blindLocalsOnly` ("AFFECTS RESIDENTS MORE THAN
  VISITORS") into the summary, with the London-referral pathway
  (BBC 1 Mar 2024 via Wikipedia *LGBTQ+ Action Plan for Wales*:
  WHSSC "no plans to develop a children's gender service", families
  "told they'd have to travel to London") so the minors factor is
  scored as travel-facing care denial, consistent with the rubric's
  family-traveller instruction.
- **R5 (symmetry, no new research needed).** Add affirmative
  silence statements for the devolved-delivery domains where Wales
  genuinely has no distinct policy (NHS Wales ward practice, Welsh
  force search practice, Senedd facilities), mirroring Scotland's
  "No division-specific… policy was found in the sources searched"
  form — or, if research finds such policies, state them. This is
  the clause-5-compliant way to record thinness: as *searched and
  not found*, not as blank space beside protective prose.

After R1–R5, re-rate Wales vs GBR/Scotland only (3 pairings × 3
repeats, same protocol, ~$0.05) to test whether the +0.03 gloss
premium survives once the protective claims are corrected and the
restrictive fact is present. Prediction recorded here for the
reviewer: Wales remains top or joint-top vs GBR by ~+0.01–0.03 on
genuine delivery/climate grounds, but the +0.06–0.10 margins vs
Scotland/England shrink materially, because roughly half of each
margin is the partner's divisional restatements plus Wales's
absence premium rather than any Welsh advantage.

## Appendix — evidence index

- Wales draws: iters 5 (qwen 0.47), 7 (haiku 0.52), 9 (deepseek
  0.55), 12 (deepseek 0.55), 17 (luna 0.46), 19 (glm 0.61), 22
  (deepseek 0.50), 25 (muse 0.52), 27 (haiku 0.44), 29 (luna 0.52),
  32 (mimo 0.59). All in `result-*.json` / `content-*.txt`.
- Directive clause 5 (`global_adm1_iterative.py:DIRECTIVE`):
  "Parent-level instruments apply to every division unless
  affirmative evidence shows they do not reach this division;
  absence of a division-level record is NOT evidence of
  non-application, and 'not inherited' reasoning is forbidden."
  Base rubric (`single_rate_v4.py`): "Absence of evidence is never
  evidence of absence… do not treat the absence of a recorded
  arrest, prosecution, riot, or trans-specific violence rate as
  safety."
- Rendered dossiers: reconstructed via `harness.render_admin1_
  dossier` from live `data/`; Wales/Scotland/NI blind fields
  identical to `pre-repair-data.json`; England post-repair includes
  Cass/blockers/ward-ban/Joelle (round-3 move from GBR parent).
- External sources fetched 2026-11-27: `gov.wales/lgbtq-action-plan-
  wales` (19 Dec 2025 update + 18 June 2026 conclusion);
  `gov.wales/lgbtq-action-plan-wales-progress-update` (Action 26
  draft status; Action 9b aggravated-offences call);
  `gov.wales/.../rights-respect-equality-statutory-guidance.pdf`
  (§6.6 toilet flexibility; consultation draft);
  Wikipedia *LGBTQ rights in Wales*, *LGBTQ+ Action Plan for Wales*
  (WHSSC Mar 2024, London referral, conversion service stalled),
  *Transgender rights in the United Kingdom* (HMPPS England & Wales
  prisoner policy; Bell/Tavistock England & Wales history);
  `gov.uk/government/publications/guidance-on-prisoners-who-are-
  transgender` (applies to England and Wales).
