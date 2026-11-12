# Anchored single-rating v3 — combined-regime structured instrument

## Why this instrument exists

The previous single-rating outputs treated the federal/national regime as a
starting point and then added or subtracted a subnational adjustment. The
saved reasoning showed the consequences: models explicitly estimated a
parent score even when none was supplied, treated protective local law as a
premium, and often reduced the national layer to a generic “border problem.”

The v3 instrument replaces that parent-plus-local arithmetic with
**combined-operating-regime synthesis**. The visitor encounters national,
regional, and local authorities as one system whose rules can interact. A
state-level protection is not allowed to cancel a federal exposure unless the
dossier documents operative pre-emption, immunity, or another mechanism by
which the relevant actor cannot impose that exposure.

## Prompt changes

- The system prompt retains the scale, rating rules, taxonomy, and 50 synthetic
  anchors.
- A v3 override supersedes parent-baseline wording. It prohibits estimating a
  parent score, parent-plus-local arithmetic, and sovereign-neutralisation
  assumptions.
- Adult visitors and travelling families/minors are both in scope. Age-
  dependent rules must be described for a minor and for a parent or guardian.
- Identity comments are prohibited: inferred real-world identity and outside
  knowledge are not evidence. This is not a claim that detailed facts cannot
  identify the jurisdiction; recognition limits are recorded below.
- Local law cannot cancel a federal exposure unless operative jurisdiction or
  pre-emption is documented.
- Interactions across stages are mandatory: entry/document findings can lead
  to investigation, detention, custody, or family consequences.

## Mandatory output

Every answer is one JSON object containing:

1. `rating`
2. `explanation` — combined-regime synthesis, at most 150 words in the prompt
3. `factor_matrix` — the eight required factors below
4. `anchor_checks` — at least three different synthetic-anchor IDs with
   operative comparisons
5. `synthesis` — how the components interact in practice

Required factors:

- `entry_documents`
- `investigation_detention_custody`
- `federal_state_facilities`
- `care_services`
- `threat_framing_law_enforcement`
- `minors_guardians`
- `street_violence_police_response`
- `remedies_unknowns`

Each factor contains `exposure`, `protection`, `interaction`, and `status`.
The status must be `documented`, `not_documented`, or `uncertain`. A factor
that the dossier does not document must not be omitted and must not be treated
as safety.

## Anchor discipline

The model must compare the case with at least three synthetic anchors and
explain the operative differences. Merely naming a score band is not enough:
the comparison must identify the features that make this case more severe,
less severe, or materially similar.

Schema validation rejects missing factors, unknown anchor IDs, repeated
anchor IDs, non-object output, ratings outside [0,1], and explanation/synthesis
budgets that substantially exceed the requested limits.

## Provider and accounting settings

- Seven models: MiMo, DeepSeek, Qwen, GLM, Haiku, Luna, and Muse.
- Thinking effort: medium for every model.
- Output allowance: 16,000 tokens. The larger allowance is specifically to
  prevent the previous Qwen failure mode in which a long reasoning trace hit
  the output ceiling before the final answer.
- One attempt per model/region; failed draws are preserved and never retried.
- Unknown charges stop a run. Exact Decimal costs are persisted.

## Anonymisation limits and deceptive details

The dossier contains no jurisdiction name, ISO code, score, rank, or other
stored score. Nevertheless, highly distinctive operative facts can identify a
jurisdiction — especially the United States — to a knowledgeable model.

Deliberately false irrelevant details were considered as an additional
blinding mechanism: wrong geography, hemisphere, age, land area, population,
or approximate number of subregions. They were **not adopted** in this
instrument because:

1. they may distract from real operational evidence rather than protect the
   rating task;
2. they would be incorrect in any later non-blind production use; and
3. they are very unlikely to defeat identification when the legal facts are
   sufficiently distinctive.

The v3 prompt therefore treats identity inference as non-evidence but does not
pretend that factual de-anonymisation is impossible.

## Deployment status

The map values currently live are the earlier non-v3 ensembles. This method
document, code, tests, and frozen manifest are the approved v3 design. Map
values should only change after v3 runs are executed and their structured
outputs and fresh ensembles are reviewed.
