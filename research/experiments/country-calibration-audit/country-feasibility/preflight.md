# Claim-level source preflight

**Effective exploratory status (2026-11-08):** The coordinating assistant has
adopted the narrowly scoped feasibility-only amendment in
`evidence-preflight-amendment.md`, with the independent evidence reviews and
unresolved claims documented in `preflight-signoff.md`. This does not satisfy the
comprehensive gate or approve publication, travel advice, rankings, or production
scores. All receipt, budget, provider-probe and execution gates still apply.
The original pre-outcome proposal and status below are retained as historical
context; statements that the amendment was not yet adopted describe that earlier
stage, not the present status. `probe-review-policy.md` separately records the
pre-outcome eligibility amendment for independently reviewed operational probes;
unknown-charge reconciliation still requires operator review.

> **NOTICE — historical comprehensive gate vs. proposed amendment (read
> first).** The procedure below is the **historical comprehensive gate**: it
> requires an independent reviewer to map and verify **EVERY material claim** in
> each exact frozen packet, with a distinct claim-level sign-off. **That gate has
> NOT been performed, satisfied or completed** — no claim-level sign-off
> (`preflight-signoff.md`) exists, no receipt exists, every item below remains
> open, and nothing here may be presented as done. Separately,
> `evidence-preflight-amendment.md` records a **proposed, pre-outcome, narrower
> exploratory gate for the exact frozen 4-country non-publishing feasibility
> diagnostic ONLY**, conditional on explicit uncertainty, on the original stricter
> comprehensive gate remaining in force for any publication, and on no scores,
> rankings or travel advice being validated. That amendment is recorded but **not
> adopted**; its bytes and the durable local copy of the independent follow-up
> review (`reviews/evidence-preflight-followup.md`) are bound by `runner.py`'s
> existing receipt bindings, and no receipt exists. Neither document is execution
> or production approval.

**Status: REQUIRED and NOT YET PERFORMED.** No provider call — not one of the 40
frozen attempts, not a probe — may be dispatched until an independent reviewer
completes this preflight against the **exact frozen packets**
(`frozen/packets/*.txt`, hashes in `frozen/manifest.json`) and records sign-off.
The only dispatch-capable code in this directory (`runner.py`) is **disabled by
default**: it refuses to run without an explicit `--execute` flag **and** a signed
`preflight_receipt.json` whose `bindings` must equal the SHA-256 of every frozen
input, of `runner.py`, of `budget-amendment.md`, of `probe-amendment.md`, of
`evidence-preflight-amendment.md` (the feasibility-only amendment), of
**this exact procedure (`preflight.md`)**, of **the distinct claim-level sign-off
artifact (`preflight-signoff.md`, whose bytes are bound — it does not exist yet)**,
of `data/countries.json` and of the
independent evidence/budget reviews plus the local follow-up review
(`reviews/evidence-preflight-followup.md`) at the moment of review. Any drift in a single
byte invalidates the receipt. The gate remains a human/procedural hard stop.

**Snapshot refresh (commit `80c573a5`, HEAD):** the frozen packets were rebuilt from
the current snapshot, which carries the US MAP facility-category correction (MAP
equality map, data as of **7 November 2026**) and the corrected **19 March 2025**
Florida restroom arrest (two new dated source entries: Fla. Stat. § 553.865 (2025)
and Equality Florida, 1 Apr 2025). GBR/NPL/VAT packets are byte-identical to the
prior `4ce04e50` refresh; the two GBR index-score exclusion edits are preserved
byte-for-byte (ledger unchanged, before-blocks re-verified unique in the fresh
source); the A/B prompts and the neutral-label schedule are byte-identical (only
the USA packet, the USA-derived user messages and the manifest hashes changed).
Refresh status of listed items:

* **VAT V1** — source and packet now read "it is unknown whether a trans-specific rule
governs access to single-sex facilities" (the affirmative claim is gone); still
**pending** claim-level confirmation here.
* **NPL N3** — source and packet now read "decision publicly reported in July 2024 …
applies to her alone" with a new dated source entry; still **pending** confirmation.
* **GBR** — anonymisation updates landed ("Goodwin v the country", court-instance
wording); K1/K4 and all other items stand unchanged.
* **USA U3 (facility counts)** — **CORRECTED IN THE SNAPSHOT, still PENDING at
claim level.** See the USA section: the categories now partition the mapped set.

All items below remain open until a reviewer signs off claim-by-claim. **The
experiment is NOT ready for API calls** (preflight unperformed; every item below,
including the corrected U3, is unconfirmed at claim level; no receipt, no
claim-level sign-off artifact, no probe observation or probe review exists; and
this worker creates or signs none — see Cross-cutting). The pre-dispatch budget
reservation itself now fits the amended ceilings; the remaining gates are
evidentiary (claim-level sign-off, hashed probe evidence + human probe review,
signed receipt), not arithmetic).

## What the preflight must do (per the independent review)

1. **Claim-by-claim mapping.** For every material claim in each frozen packet:
   map it to the archived source entry / named original; classify restrictions as
   *proposal or rhetoric*, *operative rule*, or *observed practice*; record
   *population*, *geography*, *effective date*, *trigger*, *visitor reach* and
   *remedy*. Verify the rendered packet bytes against the archived sources — not
   the prose repairs alone.
2. **Blocking conditions:** any material unsupported claim, unresolved
   contradictory scope/date/status statement, lost qualification, score/ranking
   leakage (re-check the GBR exclusions), or truncation in the rendered packet.
3. **Non-blocking:** unknown incidence or thin evidence alone — label it unknown
   and allow abstention (the output contract already permits
   `status: insufficient_evidence, score: null`). Do not require any particular
   ordering or equal evidence volume across the four cases.
4. **Stopping:** on any input contradiction or source ambiguity that cannot be
   safely resolved, stop; fix under a new frozen version (rebuild + re-hash),
   never mid-run. Never improvise scoring rules.

## Exact remaining discrepancies requiring review

Verified against the current snapshot (commit `80c573a5…`) during the refresh;
"resolved-in-snapshot" items were re-checked here and still need preflight
confirmation against the originals.

### United Kingdom (GBR)

* **K1 — third-party rainbow-index numeric scores/ranks (pilot view only).**
  `blindSummary` and `blindTangential` carry explicit index ranks/scores
  (`1st/86% 2015`, `9th/66% 2020`, `22nd/45% 2025`, `third steepest`). They are
  excluded from the provider packet by ledger edits `GBR_index_summary` /
  `GBR_index_tangential` (see `evidence-map.md`), **but the underlying index
  claims are not thereby verified** — preflight must check them against the
  ILGA-Europe 2026 findings page and the ranking publication, and confirm the
  pilot view is the version frozen.
* **K2 — regional vs national reach.** Scottish Prison Service ruling (regional),
  "One state/province police service" interim guidance of 25 Jun 2025 (regional),
  national transport police strip-search change (GB-wide), EHRC single-sex-spaces
  code (national, with one region on different legislation still assessing).
  Verify the packet nowhere presents regional rules as national or vice versa.
* **K3 — proposal vs implementation.**
  (a) "Trans hospital patients are to be banned from female- and male-only wards
  under plans announced … October 2023" plus a constitution consultation — verify
  implementation status as of the research date;
  (b) `blindSourceSummaries[7]` (JURIST) says "revisions to the equality statute
  risk …", while `blindOutOfScope` states the UN warning concerns the code in
  force "not enacted amendments to the national equality act" — resolve this
  phrasing tension before sign-off;
  (c) the legal challenge to the code (pre-action stage) and its outcome remain
  disclosed as unresolved — keep it that way.
* **K4 — identifiable case names.** "Joelle" (blindSummary + blindOutOfScope),
  "For Women Scotland v Scottish Ministers", "Goodwin", "Corbett" are retained
  (they are not index scores/ranks and are substantive legal facts). Preflight
  must verify them against the named originals and make an explicit decision that
  provider input may carry them; they are also the source of the recorded
  identity leak.
* **K5 — disclosed retrieval failures.** One regional police force policy and the
  EHRC detailed-guidance page returned HTTP 403 at research time; the packet says
  so. Verify no claim silently rests on unretrievable content.
* **K6 — entry/custody/visitor treatment.** The packet states these sources do
  not establish particular entry or custody rules or how individual visitors will
  be treated; verify this unknown is not upgraded anywhere (resolved-in-snapshot,
  re-confirm).

### Nepal (NPL)

* **N1 — ground-level account date.** The review flagged a named-vs-blind date
  disagreement; the current snapshot reads **November 2024** consistently in
  `summary`, `outOfScopeNotes`, `blindOutOfScope`, `blindSourceSummaries[3]` and
  the source (Kathmandu Post, 17 Nov 2024). Re-verify all five against the
  original; any disagreement is blocking (resolved-in-snapshot, re-confirm).
* **N2 — historical recognition examinations vs current visitor screening.**
  "surgery abroad plus in-country medical evaluations including intrusive
  post-operative genital exams" is pre-30-Aug-2024 **resident marker-change**
  practice; verify the packet keeps it historical and resident-scoped and that
  nothing can be read as current visitor document screening at entry.
* **N3 — carried-forward "Kapali date" flag.** `blindSummary` says "30 August
  2024 … more than 50 lawsuits beginning in 2021"; verify the ruling date against
  the court/original report (article date conventions differ across sources).
* **N4 — deidentification parity.** Named fields name parties (party, NGO
  director, prime minister, petitioner); blind fields anonymise ("a non-governing
  party", "the elected head of government", "a trans law student"). Verify no
  fact was dropped or misattributed in deidentification, including the
  April-2026 video/death-threats account.
* **N5 — comparative/status claims.** "second in the region" (curriculum) and the
  April-2026 hostility instances being explicitly **not official government
  acts** — verify both against the originals.

### Vatican City (VAT)

* **V1 — affirmative legal-absence claim.** `blindSummary`: "No rule governs
  access to single-sex facilities for a trans visitor, and no document-amendment
  route exists for a resident or a visitor." Legal claims rest on
  secondary/encyclopedic sources — **no primary state-law instrument** is in
  `sources[]`. Verify against a primary legal text or scope the claim; blocking
  while unverified.
* **V2 — custody arrangements.** "operates no prison system … few cells for
  pre-trial detention … sentences served in a neighbouring jurisdiction"; the
  sole prison-axis source is a general encyclopedic article the record itself
  marks "used as a last resort". Verify actual custody arrangements, including
  the disclosed possibility of pre-trial detention under country authority.
  Outsourced custody must **not** be read as dependency: no parent-regime section
  is supplied and rule 12's parent logic stays dormant for this case.
* **V3 — blind/source count mismatch.** 4 blind summaries vs 7 source entries;
  composite blind entries mix doctrine claims (Dignitas Infinita, 2019 education
  document) with legal-recognition claims. Map each packet claim to its true
  source before sign-off.
* **V4 — entry/screening safety claims.** The review's original contradiction
  (affirmative "no policing / no bathroom inspections" vs undocumented
  enforcement) is **not present** in the current snapshot:
  `blindSourceSummaries[3]` says the sources "record no trans-specific practice
  at entry, at screening, or in access to facilities … neither trans-specific
  danger nor trans-specific safety can be inferred". Re-confirm this wording
  survives any rebuild and that `blindOutOfScope` keeps "Enforcement practice at
  entry, at screening, or in access to facilities … is not documented"
  (resolved-in-snapshot, re-confirm).
* **V5 — thin evidence.** No government human-rights report chapter for 2023 or
  2024 (disclosed in the packet). Thinness alone does not block: label unknown,
  abstention permitted.

### United States (USA)

* **U1 — domestic passport issuance vs foreign entry.** The packet separates the
  lanes (issuance: Feb-2025 X-marker stop, Nov-2025 Supreme Court, passports
  "confiscated or blocked at processing, leaving some stranded abroad"; entry:
  the 24 Feb-2025 consular cable's case-tag/refusal instructions, visa-issue
  detentions). Preflight must verify each claim sits in its correct lane and that
  no claim conflates citizen passport issuance with rules for foreign visitors'
  entry.
* **U2 — trans-athlete entry ban (Feb 2025).** Verify operative-vs-proposed
  status and scope as of the snapshot date.
* **U3 — subnational count arithmetic (revised at `80c573a5`).** `blindSummary`
  now follows the MAP equality map "data as of 7 November 2026": **9 states +
  Puerto Rico** (all government-owned buildings incl. K-12 and colleges), **9
  further states** (K-12 + at least some government-owned buildings), **3 states**
  (K-12 only), and **29 states + 4 territories + D.C. with no such ban in these
  categories**, so the state groups now partition the 50 states
  (9 + 9 + 3 + 29 = 50) and the territory groups are disjoint from them; the
  criminal-offence flag (4 states) is stated as an additional flag, not a
  partition class, and the Florida trigger is corrected to **trespass, not
  automatic arrest**, with the **19 March 2025** arrest (reported April 2025).
  **Still PENDING:** (a) confirm the counts and the "6 state/provinces … at least
  some private settings" note against the MAP page itself (data-as-of date
  7 November 2026 must match); (b) `blindTangential` still carries the separate,
  unchanged "state/province scorecards (2024 snapshot) show three … one … two"
  sentence — its source and arithmetic are untouched by this refresh and remain
  unexplained here; (c) confirm the new Fla. Stat. § 553.865(11)(b) rendering
  (willful entry + refusal to depart, exemptions in subsection (6)) and the
  Equality Florida arrest details (19 March 2025, second-degree misdemeanour,
  24 hours in the men's ward) against those two named sources.
  Blocking while unconfirmed.
* **U4 — advocacy "Do Not Travel" designation.** One advocacy publication
  (13 Jul 2026), not a government advisory, four units flagged — verify the
  attribution stays explicit (disclosed in the packet).
* **U5 — single-sourced and unresolved claims.** Corrections-bureau
  policies and immigration-custody abuse rest on a single encyclopedic source;
  the fraud-ground/permanent-ineligibility instruction's implementation is "not
  established by the documents". Verify corroboration or keep them explicitly
  single-sourced/unestablished.

### Cross-cutting

* Two independent reviewers preferred; disagreements retained and adjudicated
  without reference to desired scores.
* Semantic/evidence failures are reviewed **before** any numerical differences.
* Preflight sign-off is recorded before dispatching any of the frozen 40
  attempts; all failures and retries count against the proposed attempt ceiling
  (no favourable-output retries).
* Stop on unknown billing usage, model substitution/version drift, context
  overflow or ceiling exhaustion at run time; never silently truncate evidence.
* **Runner gate:** `runner.py` dispatches only with an explicit `--execute` flag and
  a reviewed `preflight_receipt.json` (**schema v3**) binding the exact SHA-256 of
  `frozen/manifest.json`, both prompts, all four packets, `frozen/schedule.json`,
  `frozen/user_messages.json`, `ledger.json`, `runner.py`, `budget-amendment.md`,
  `probe-amendment.md`, `evidence-preflight-amendment.md` (feasibility-only
  amendment), **`preflight.md` (procedure) and `preflight-signoff.md`
  (claim-level decision, content-bound — not a path string)**,
  `data/countries.json` **and the independent evidence and budget reviews plus
  the local follow-up review (`reviews/evidence-preflight-followup.md`)**. The
  receipt must *document* the provider usage/pricing semantics (with sources) and
  record the residual assumptions; it must report live behavior as `unobserved`
  (scoring then still refuses) or as an `observed_in_bounded_probe` whose `record`
  is a structured list of exact `{path, sha256}` entries over the four probe
  files — schema v3 has **no `verified` flag**, a legacy `verified: true` claim is
  rejected, and a free-text observation record is rejected. It reads no credential
  and opens no socket before every gate passes.
* **Concurrency gate (lock):** a single experiment-wide `.execution.lock` is
  acquired **before any prior state is read or any budget decision is taken** and
  held through dispatch and finalization. Contention refuses **before any call**;
  a lock or a run/probe directory left by a crash is **never deleted automatically**
  — it blocks everything until a human inspects it and reconciles the missing
  terminal record.
* **Probe gate (`probe-amendment.md`):** at most **2** tiny fixed non-country
  probes (one per model, no retry) may precede scoring; combined ceiling **42
  dispatches** (40 scoring + 2 probes); probe attempts, tokens and actual billed
  costs share the same USD 10.00 ledger; scoring additionally requires **both**
  probes completed, structurally independently reviewed (`review.json` with
  `status: reviewed_ok`) and hash-bound in the receipt, and refuses on any unknown
  or unreconciled probe charge.
* **Budget (pre-outcome amendment adopted; `budget-amendment.md`):** input
  reservation = UTF-8 bytes of the frozen prompt + message + a fixed 128-unit
  chat-framing allowance per call — **administrative reservation units under stated
  tokenizer/framing assumptions, not proven native-token bounds and not a
  provider-enforced spend limit**. The exact plan is **66 611 units/call** and
  **2 316 208 units** aggregate (observed worst case 66 483 bytes/call), which fits
  the pre-registered amendment ceilings of **70 000/2 400 000** but not the original
  20 000/800 000 proposal — that proposal stays recorded verbatim and still stops the
  run if *billed native* tokens exceed it. The **USD 10.00 ceiling is local**
  (reservation + postpaid accounting), including all failures; ≈ USD 1.21 at
  previously observed catalogue prices (≈ USD 2.31 at the budget review's
  conservative bound) is a planning estimate only — runtime fetches fresh prices and
  refuses unknown/negative/non-finite ones.
* **Run ledger:** a prior run's or probe's unreconciled liability (unknown billed
  cost), any unknown prior run/probe state, or any predeclared cell already
  attempted blocks a new run; reconciliation is a human record
  (`runs/<id>/reconciliation.json` or `probes/<slot>/reconciliation.json`) that
  this directory never writes.
* **Readiness:** none of the above is satisfied yet — the claim-level preflight is
  unperformed, every listed discrepancy (including the snapshot-corrected U3)
  remains unconfirmed, no claim-level sign-off artifact exists, live provider
  behavior is unobserved, no receipt / probe / probe review exists, and this
  worker creates or signs none — so these 40 attempts remain **blocked and not
  ready for API calls**.