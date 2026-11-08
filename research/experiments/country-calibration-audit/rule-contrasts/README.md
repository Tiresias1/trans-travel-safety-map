# Rule-contrast prompt experiment (pre-registered, offline preparation only)

Preparation only. This directory ships **no live code, no credentials and no
provider/model calls**; nothing here has been executed against a model and **no
running provider is configured**. Nothing outside
`research/experiments/country-calibration-audit/rule-contrasts/` is touched, nothing
is committed, and no model scores exist anywhere in this directory (only the 0.00 /
1.00 scale endpoints are named).

## Pilot rationale

The read-only proposal (`proposal.md`, a byte-for-byte in-repo copy of the original
reviewer-proposal artifact; sha256 recorded in `frozen/manifest.json`)
offers two complete candidate prompts built from the production
`tools/blind_pairwise.py` system rules plus `research/outing-risk-taxonomy.md`:

* **Candidate A — conditional-consequence.** Rate consequences conditional on trans
  status being known. Documented state-engineered discovery is recorded separately and
  is *not* an independent scalar contribution.
* **Candidate B — institutional-exposure.** Same, but documented state-engineered
  discovery (mandatory disclosure, targeted registration, surveillance, checkpoint
  practices) may contribute *independently*, with scope, operation and triggers
  established.

The motivating question — **does documented state-engineered discovery have an
independent rating contribution beyond the harms of the practice and the consequences
after discovery?** — is deliberately **not answerable from these materials**: the pairs
cannot identify that independent effect (see P1 below), so they only probe how each
prompt handles discovery-related evidence. Both candidates count documented coercion, intrusive examination,
registration burden, dissemination and actual harms as harms in themselves; neither
uses a probability × severity formula; neither gives any credit for passing, stealth,
silence or avoidance; 0.00 still requires an outed visitor facing near-certain
imprisonment **and** likely execution. Intermediate points have no fixed definitions;
the inherited labeled band intervals (five named risk bands between 0.00 and 1.00)
are orientation labels only, not calibrated anchors, and there is no mandatory
spacing, no frozen anchor set, no
hard-coded country scores and no desired score or ranking.

Shared replacement S5 now states the user-mandated weighting **explicitly in both
variants**: documented curiosity and awkward friction (oddity, not threat) carry
**VERY LOW WEIGHT**, and documented social and state threat-framing carry **REAL
WEIGHT**, while official rhetoric must never be treated as proof of implemented policy
and documented threat-framing must not be dismissed merely because it has not yet
produced violence.

The candidates are produced by **literal exact-string replacement only** (no regex
prose transformation): 17 shared blocks (review sections S1–S10, with the S5 weight
restoration above) plus 7 variant sites (review A1–A4 / B1–B4). Every before-block must
match its source file exactly once and match exactly once at apply time, otherwise the
build stops and writes nothing. LLM-authored replacement paragraphs are used verbatim;
original source text is never edited.

## Materials — five matched synthetic pairs (`fixtures/`)

All inputs are synthetic, clearly labelled, and are **not factual claims** about any
real country, territory or person. No real identities, no ADM1 units, no existing
scores or rankings. Provider-visible content is rendered separately (see
*frozen user messages* below); fixture titles, design notes and `expected_reasoning`
are reviewer-only metadata and never reach the provider.

| Pair | Class | What varies |
|---|---|---|
| P1 | **bundled institutional-practice contrast** (relabelled) | mandatory gender-marker flag with recording, 24-month retention and release requirement on one side vs confidential ordinary registration on the other — flag, direct burdens, retention, recipients and discovery exposure all differ together |
| P2 | rule-vs-none, symmetric evidence | written operative custody rule covering visitors vs no written rule; no operational observations on either side; detention frequency unknown in both |
| P3 | **bundled hostility-and-treatment contrast** (relabelled) | curiosity/awkward friction vs threat framing **plus** ejections, one confrontation, one police call; identical specified 2018 incident and identical 2016 no-implementation statement in every copy |
| P4 | identity control | byte-identical evidence; presentation position created only by renderer order (no retained position strings) |
| P5 | scope-adherence control | identical trans-specific evidence plus an unrelated general travel hazard in one copy |

**Identification withdrawn for P1 and P3.** A convincing pure discovery-only contrast
could not be constructed — the mandatory flag is itself a counted direct burden — so
P1 is explicitly relabelled and its results must **not** be read as identifying an
independent discovery effect. P3 bundles framing with treatment and cannot isolate
framing weight alone. Each fixture pre-declares qualitative expected reasoning only,
never a target score.

## Frozen user messages (`frozen/user_messages.json`)

Before any call, the harness renders and freezes the actual provider-visible user
message for **every one of the 40 scheduled rows**, with a per-message sha256:

* evidence fields only, plus the synthetic disclaimer; **no** `title`, `design`,
  `expected_reasoning`, reviewer notes or fixture labels;
* **no cross-copy comparison or control cues** (summaries no longer announce what
  matches or what alone differs);
* order applied per schedule row, with `map_A` / `map_B` recording which original copy
  is presented as dossier A or B after any swap (P4 has no per-copy position string to
  conflict with a swap);
* an **identical diagnostic rationale request for both variants**: a `diagnostic`
  object in the same single JSON object with four short fields (`discovery`,
  `direct_harms`, `scope_triggers`, `uncertainty`).

The diagnostic fields support but **do not prove** reasoning: at these lengths, absence
of a factor from a response cannot establish that it was mishandled, and the 40-word
`why` field alone cannot establish semantic success or failure. Interpretation is
narrowed accordingly (see criteria).

## Pre-registration (before any call)

* **Ceiling: 40 calls** = 5 pairs × 2 variants × 2 models × 2 presentation orders,
  **one draw per cell**, fresh context per call, no retries selected for favourable
  output. Schedule `frozen/schedule.json` (seed 20261119) is randomized, balanced
  (20 A / 20 B, 20 per model, 20 per order, 8 per pair) and interleaved (≤2 consecutive
  calls of one variant; each half balanced within 8–12 per condition value).
* **One draw per cell and order:** reversing order changes both order and draw, and the
  two model families are not replicate draws. With one observation per cell, stochastic
  variation cannot be separated from any condition effect. **No causal claim, no
  statistical significance claim, no calibrated increments and no stable ranking claim
  may be made from this design**; outputs are individual descriptive records only.
* **Models (exact API ids only):** `deepseek/deepseek-v4.1-flash` and
  `google/gemini-3.8-flash`. No provider code is written now and none is running.
* **Declared caps (not enforced safeguards):** 2000 output tokens per call; 700 000
  input / 90 000 output tokens aggregate; **no monetary cap is declared** — token caps
  are not a budget and pricing is not established. A separately approved runner must
  enforce the ceiling, account all billed usage (including reasoning tokens), stop on
  unknown usage, and count failures rather than silently replacing them. (40 × 2000 =
  80 000 capped output tokens, so the 90 000 aggregate output figure is nonbinding.)
* Human reviewers classify coverage, triggers, provenance and expected reasoning
  **before** any call, without seeing scores or each other's notes.

## Hard-stop rules

1. **Create vs verify are separate.** `harness.py --create` re-checks repository scope
   (allowing the one known untracked sibling experiment directory
   `country-feasibility/`; any other outside path or any staged entry still fails
   closed) and index **before** writing, then writes; `harness.py --verify` is
   read-only and proves it wrote nothing via a whole-directory byte fingerprint.
2. Build fails closed: any before-block not matching exactly once in its source and
   exactly once at apply time aborts everything; nothing is written.
3. `STRIP_RULE_10B`, `REVERT_ENDPOINT` and `RESTORE_ARCHIVED_WORDING` are forbidden
   during the build; the AND endpoint conjunction must survive.
4. **Byte-level frozen verification:** `--verify` hashes the *actual on-disk* frozen
   prompt, schedule and user-message files against the manifest, re-checks current
   source/replacement/fixture bytes and proposal provenance, and runs an in-memory
   tamper self-test of **hash inequality only**: mutated prompt, schedule and fixture
   bytes must fail the same sha256 comparisons `--verify` uses. That self-test does not
   re-execute the full file-read/rebuild verification path, and hash checks cannot
   defend against a hostile co-modification of a file and the manifest. No output file
   is modified by the test.
5. Evidence failure (invented enforcement, dates, remedies or geographic reach) stops
   interpretation of that pair; semantic failure (A independently penalising discovery
   probability alone, B crediting personal stealth, or either assuming custody/ward/
   mismatch merely because status is known) and control failure (general danger driving
   trans-specific reasoning, or divergence between byte-identical dossiers) are recorded
   as failures, not averaged away.
6. A future runner must be approved separately; this directory deliberately contains no
   network client, credential or API-call code (checked by the harness).

## Predeclared test criteria

Offline checks: `python3 harness.py --create` runs **54 checks** (build + pre-write
scope/index precondition + generation + frozen-candidate weight assertions),
`python3 harness.py --verify` runs **58 checks** (read-only: the same checks plus
on-disk frozen-byte verification, proposal provenance and the hash-inequality tamper
self-test). Each run prints every check name and the total on its last line; re-quote
that line if the count ever changes:

* source literal uniqueness of all 24 replacement blocks; apply-once fail-closed;
* option comparability: A and B byte-identical except the 7 designated variant sites,
  identical output-format block and band legend;
* preserved rules: no-credit-for-passing language, `imprisonment **and** likely
  execution` endpoint, explicit VERY LOW WEIGHT / REAL WEIGHT language, rule 10b
  present, intermediates undefined, product formula gone, A-only and B-only discovery
  statements present;
* controls and relabelling: P4 byte-identical with position only from presentation, P5
  differs only by the general hazard, P1/P3 bundled class and withdrawn identification
  recorded, P2 symmetric evidence with unknown detention frequency;
* frozen user messages: one per row, disclaimer, evidence-only, no reviewer metadata or
  cross-copy cues, correct A/B mapping after order, identical diagnostic request;
* synthetic labelling, qualitative expectations with no target scores, no
  score/band/rating fields, no real country/ADM1/frozen-anchor names anywhere, no
  network or credential tokens, scope/index clean before and after writes;
* `--verify`: on-disk frozen bytes vs manifest vs rebuild, the hash-inequality tamper
  self-test, and a direct check that both actual frozen candidates still carry the
  explicit VERY LOW curiosity and REAL social/state threat-framing weight statements.

Online interpretation (predeclared for the future run, not executed now): compare
diagnostic fields and rationales, then direction, ties and order sensitivity **first**,
and only as descriptive records. Short structured fields support but never prove
reasoning; if the diagnostics cannot distinguish direct harms from a discovery
contribution, the result is **unidentified/inconclusive**. Numerical differences are
descriptive instrument outputs, not calibrated risk increments. No minimum gap, no
target score, no country ranking is required or accepted.

## Files

* `harness.py` — offline builder/verifier (`--create`, `--verify`).
* `proposal.md` — byte-for-byte in-repo copy of the reviewer-proposal artifact
  (sha256 unchanged: `39e9d0ac…59e2e`); provenance in `replacements.json` resolves
  this local file.
* `replacements.json` — literal shared/variant blocks + proposal sha256 (edit only via
  regeneration).
* `fixtures/P1…P5*.json` — five matched synthetic pairs (reviewer metadata included).
* `frozen/candidate_a.txt`, `frozen/candidate_b.txt` — frozen system prompts.
* `frozen/user_messages.json` — the 40 provider-visible user messages + hashes.
* `frozen/schedule.json` — the 40-call schedule; `frozen/manifest.json` — source,
  proposal, prompt, schedule and user-message hashes.

## Scope notes and limitations

* **Applied:** review sections 2 (S1–S10, with S5 weight restoration) and 3 (A1–A4,
  B1–B4). **Not applied:** review section 4 replacements (e.g. the rule-20 sentence);
  rule 12's parent-relative arithmetic, the ADM1 lane, rule 16's undercount treatment
  and rule 20's resident/visitor sentence remain unvalidated — exclude family/diaspora
  fixtures from any bounded run.
* The proposal's block for rule 9 normalized indentation; its warning says to use the
  literal source block, so the source bytes were used (3-space continuation indent
  where the review claimed four; wording verified identical after whitespace removal).
* P1 and P3 are **bundled** contrasts with identification withdrawn (above); the
  discovery-only question can only be probed indirectly by this five-pair design.
* The review proposed six contrast pairs plus two controls at a 64-call ceiling; this
  experiment implements the five pairs specified for this pre-registration at a
  40-call ceiling. Intrusion, scope, and date/remedy contrasts are not included, so
  success cannot demonstrate preservation of those behaviours.
* One draw per cell and order (above), no monetary cap, no running provider, and thin
  fictional evidence by design — results speak to prompt semantics, not to any
  jurisdiction's real risk.