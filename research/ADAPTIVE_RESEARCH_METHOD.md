# Adaptive Research Method — ADM1 researcher methodology (v1, 2026-11-25)

> **User-facing research contract.** This document defines how ADM1 research is done.
> The paste-ready researcher prompt (`research/ADM1_RESEARCH_PROMPT.md`) implements it;
> `research/PIPELINE_INVARIANTS.md` §9 binds every downstream stage to it.
> Scope: **ADM1 regions only** (first-level administrative divisions). Country-level
> records are not re-researched under this method (see §7).

**Style gate (leftover from the old prompt, still binding):** read `tools/STYLE_RULES.md`
before generating. All summary text is report-voice; never describe previous states of
the record or the map ("the earlier profile…", "has been deleted"). State the current fact.

---

## 1. Core principles

1. **Search first, always.** No region is written from memory. Every round begins with
   web search. A claim without a source URL does not exist.
2. **Adaptivity over templating.** Round 1 is a broad sweep; later rounds are *generated
   by what round 1 found*. A promising dataset, a recurring cited source, or an unread
   ballot-measure text schedules its own follow-up — the researcher does not wait for
   an operator to ask.
3. **Facts only, everywhere.** `sources[].summary` and `blindSourceSummaries[]` carry
   facts only (PIPELINE_INVARIANTS rule 4). No score/inclusion meta, no report-voice
   leakage of pipeline history. "No new facts without a source" is absolute.
4. **Local evidence only; parent stays frozen.** Under the US federal framework, ADM1
   research documents state-level deviation from the national score. The country record
   is the parent framework and is authoritative. If state research contradicts the
   parent framework, **flag it for the coordinator** — never silently rewrite the parent.
5. **One mechanism per layer** (PIPELINE_INVARIANTS rule 7/7b family): a fact renders
   exactly once per layer. Research writes sourced facts; blinding rewrites them;
   rating only reads. No stage invents evidence to paper over a gap left by another.
6. **Nothing reaches a dossier unverified** (§5). A source enters data only after its
   own verification pass.

---

## 2. Search engines and budgeting

Two engines are available:

| Engine | Role | Budget |
|---|---|---|
| **DuckDuckGo (DDG)** | default workhorse: broad sweeps, per-region query fans | no hard daily cap, but rate-limited — throttle, rotate phrasings, back off on 429/503 |
| **Exa** | agentic depth: extraction from long pages, full-text reads of measures/bills, targeted deep dives | **~150 queries/day shared across all regions and all agents** — this is a global budget, not per-region |

**Budget rule:** DDG first for breadth; Exa only when (a) a page needs agentic extraction
(long legal text, ballot-measure full text, paywalled/JS-heavy sources), or (b) DDG
returns thin results after ≥3 distinct phrasings. Never spend Exa on what a DDG sweep
plus a direct fetch answers.

**Query discipline (every round):**

- Multiple *distinct* queries per round (rotate phrasing; never repeat one query string).
  Per region per round minimum: **3 distinct DDG queries**, or 2 if the first returns
  rich results immediately (see "rich early exit" §3).
- Multiple result *pages* per query where the engine paginates (read past page 1 on
  contested topics; page 1 is SEO, not signal).
- Search angles (adapted per region; the old prompt's list remains valid):
  `<state> + transgender bathroom / expression / facility ban`,
  `<state> + state legislature transgender bill <session>`,
  `<state> + ballot measure / initiative transgender`,
  `<state> + transgender violence / assault rate by state`,
  `<state> + sanctuary / shield law / non-discrimination ordinance gender identity`,
  `<state> + travel advisory transgender`,
  `<state> + police enforcement / arrest facility ban`.

---

## 3. Adaptive round structure

Each region runs **rounds, capped at 4** (`MAX_ROUNDS = 4`). A round is one unit of
search → cache → reflect → schedule. No fifth round without coordinator approval.

### Round template

1. **Search.** Per §2. Record every query and engine used (see manifest, §6).
2. **Extract + cache.** Fetch every promising URL; save text under the existing cache
   layout: `research/fetched/<sha16>.txt` (+ `.meta`) via `tools/fetch_all_sources.py`,
   which is the single writer path for that cache. `tools/build_source_manifest.py`
   rolls the result into `data/source_manifest.json`. Do not invent a second cache.
3. **Verify (per new source).** Every newly added source gets its own verification pass
   (§5) *before* it can be cited. Quarantined sources are never entered.
4. **Self-reflection step** — the researcher must write this section into the region's
   round log, verbatim prompt:

   > "Did you discover something new that plausibly warrants deeper research
   > (a promising dataset, a recurring cited source, a ballot measure whose full
   > text you haven't read)? If yes, schedule it for the next round."

   The answer is either **"no — stopping"** (with one line of justification) or a
   concrete next-round schedule: named sources/datasets/measures + the targeted
   queries that will read them. A round that finds a lead but schedules nothing is an
   incomplete round.
5. **Schedule.** New leads spawn targeted searches next round: the scheduled items
   become that round's query list (the DDG/Exa choice per §2 applies to them).

### Stopping rules

- **Rich early exit:** if round 1 returns rich results immediately (a state statute
  full text + enforcement record + a per-state dataset, all verified), the researcher
  may stop after 1 round — but must still write the self-reflection explicitly.
- **No-change stop (§8):** if a round surfaces nothing new, stop; downstream stages do
  not run for that region.
- **Hard stop:** round 4 ends research for the region regardless of remaining leads.
  Unsatisfied leads are recorded in the round log as *known gaps* for the next wave,
  not pursued ad hoc.
- **Signal-based stop:** if rounds 1–2 return only national-level material with no
  state-specific signal, stop early. "No sub-national signal found" is a complete,
  useful result — do not manufacture findings to justify more rounds.

---

## 4. Cross-region source adoption (shared source registry)

### Registry

**Path:** `data/source_registry.json` (beside the existing `data/source_manifest.json`,
which tracks URL → title/date/jurisdictions; the registry tracks *adoption* state).
One registry entry per source URL. Suggested schema:

```json
{
  "url": "https://…",
  "title": "…",
  "kind": "state-tracker | ballot-db | dataset | statute | news | advisory | law-text | other",
  "status": "candidate | common | quarantined | rejected",
  "fruitfulIn": ["USA/Idaho", "USA/Kansas"],
  "citedIn": ["USA/Idaho"],
  "verification": {"status": "pass | fail", "by": "agent", "at": "YYYY-MM-DD",
                   "notes": "quote-level support confirmed"},
  "promotedAt": "YYYY-MM-DD | null",
  "promotionDecision": {"by": "coordinator", "at": "YYYY-MM-DD", "note": "…"} | null
}
```

`status` values:

- `candidate` — verified (or awaiting verification) and cited in ≥1 region.
- `common` — promoted: fruitful in **≥3 regions** AND coordinator-reviewed (§4).
- `quarantined` — verification failed; never enters dossiers (§5).
- `rejected` — coordinator declined promotion; may still be cited region-locally.

### Promotion rule

A source becomes a **candidate common source** when it is retrieved + cited (and
verified) in **≥3 regions** in the current wave. Promotion to `common` additionally
requires **manual/coordinator review** — an agent proposing a promotion records the
proposal in the registry; the coordinator approves or rejects; the decision (and who
made it, and when) is written into `promotionDecision`. No agent promotes unilaterally.

### What promotion does

Once a source is `common`, all regions (including regions already finished whose
round count allows) are **instructed to query it in the next round** — e.g. a state
ballot-initiative database, a legislature bill tracker, Ballotpedia, a state-by-state
tracker. Implementation: the coordinator writes the promotion into the registry and
into the wave's shared prompt addendum; region agents re-read the registry at the
start of every round (§3 step 1), so a promotion takes effect at the next round
boundary without restarting finished regions.

Examples of sources that typically qualify (illustrative, not pre-approved): ACLU
state-law trackers / Equality Map, Movement Advancement Project (MAP) state policy
trackers, Ballotpedia state pages, legiscan / state legislature bill trackers,
TGEU / FBI HTHR hate-crime state tables, state statute official text.

### Concurrency

Multiple region agents may propose entries concurrently. **Single-writer rule:**
registry writes go through a file lock (same pattern as existing locked RMW in
`tools/run_research_wave.py`: `fcntl` on a lockfile, tmp-then-replace). Agents never
append blindly; promotion proposals are *staged* entries (`status: candidate`,
`promotionDecision: null`) until the coordinator acts. See also §9.

---

## 5. Source verification gate

Every newly added source gets its **own verification agent pass** before any dossier
may cite it. The verifier is a separate pass from the researcher who found the source
(not the same agent invocation that harvested it). The pass checks:

1. **Real:** the URL resolves; the fetched content matches what the citation claims
   (title, jurisdiction, date range). An unreachable or content-mismatched URL fails.
2. **Properly cited:** quote-level support — for each claim attributed to the source,
   the fetched text contains support for it (the claim is not extrapolated beyond the
   text). Borrowed from the existing anti-fabrication pattern in
   `tools/run_research_wave.py` (verbatim n-gram grounding): claims without textual
   support are rejected, not softened.
3. **Properly summarized:** the `sources[].summary` text is facts-only per
   PIPELINE_INVARIANTS rule 4 — no map-score mention, no "why this source was
   included", no obsolete values; report-voice (STYLE_RULES); no changelog narrative.

**Output:** appended to the registry entry's `verification` block (status, agent, date,
notes). **FAIL → `quarantined`:** the source is never entered into dossiers, never
cited, and its URL is excluded from any batch packet that would feed it downstream.
Quarantine is sticky: re-admission requires a new verification pass, not a researcher
override.

---

## 6. Per-region manifests

Each region (state/territory) maintains a **round manifest** (path convention:
`research/adaptive/<ISO3>/<region-slug>.manifest.json`), written by the region agent
and read by the cascade (§8). Minimum contents:

```json
{
  "region": "USA/Idaho",
  "shapeID": "66186276B48953429733047",
  "round": 2,
  "roundsUsed": 2,
  "queries": [{"engine": "ddg|exa", "q": "…", "at": "…"}],
  "sourcesNew": ["https://…"],
  "sourcesVerified": ["https://…"],
  "leadsScheduled": ["…"],
  "selfReflection": "…",
  "stopped": false,
  "stopReason": "rich-early-exit | no-change | max-rounds | no-signal | coordinator",
  "knownGaps": ["…"]
}
```

The manifest is the region's contract with the cascade: it declares what changed, so
downstream stages can decide whether to run at all. **Coordinator touchpoints** are
manifest-visible: source-promotion proposals (§4), quarantine list (§5), and the
rerate-approval gate (§8) are all read from manifests + registry, never from chat.

---

## 7. Scope

- **ADM1 regions only** for this method. The US federal country record
  (`data/countries.json: USA`) is the parent framework (PIPELINE_INVARIANTS rules 2–3)
  and stays authoritative; this wave does not re-research it.
- **Contradiction rule:** if state research contradicts the parent framework (e.g. a
  state dossier implies the federal position is other than what the country record
  states), the researcher **flags it for the coordinator** in the manifest's
  `knownGaps`/`selfReflection` and continues on the state evidence. No agent edits the
  parent record under this method.
- **Territories as ADM1 under USA, never as countries.** DC, PR, GU, VI, MP, AS are
  researched as ADM1 regions under USA with the parent's full operative layer rendered
  (PIPELINE_INVARIANTS rule 2). They do not get country-level records from this wave.
  Note: PRI/GUM/VIR/ASM/MNP currently exist as country records in `data/countries.json`
  (see US-states wave plan) — that is pre-existing state this method does not create
  and does not silently delete; territory dossiers must carry the parent-layer parity
  check of rule 2 before any pairwise run.
- **Existing factual disciplines (unchanged, still binding on every round):**
  anti-absence (legal ambiguity ≠ safety; absence of evidence is not safety), the LGB
  signal IS operative when trans data is absent, de facto authorities count as the
  operative regime, no passing/stealth credit, facts-only sources (rule 4), the
  single-incident rule, traveler-facing only, enforcement > statute.

---

## 8. The cascade (systematic, gated)

A source change propagates through exactly these stages, in order. **Each stage is a
script with input/output manifests; a stage runs only if its input manifest changed
since its last run (content-hash gating).** No stage runs "because a wave ran".

```
S1 research (this method)
  → S2 source cache + manifest          (tools/fetch_all_sources.py → research/fetched/,
                                          tools/build_source_manifest.py → data/source_manifest.json)
  → S3 blindSourceSummaries re-derived  (five-way/blind_rewrite.py via tools/make_blind_batches.py)
  → S4 blind lead fields re-blinded     (blindSummary, blindTangential, blindLocalsOnly,
                                          blindOutOfScope — apply_blind_fields.py / apply_rework.py path)
  → S5 check_blind gate                 (tools/check_blind.py — must pass before anything downstream)
  → S6 lead fields / dossiers re-rendered (harness.render_admin1_dossier — the *one* rendering;
       single-render rule, rule 7b)
  → S7 summaries follow from consolidated evidence (tools/consolidate_record.py path;
       summary is derived from the re-blinded evidence, never hand-edited)
  → S8 RERATE affected regions only, via pairwise machinery (tools/blind_pairwise.py
       and/or the five-way harness), with parent-anchor pairings (rule 8a:
       PARENT_ANCHOR_FRACTION > 0, e.g. 0.20) and parent-current seeds (rule 8b).
       Never manual score edits (rule 6).
```

**Stage inheritance rules:**

- S2 runs if any region's manifest lists new/changed sources.
- S3 runs for a region iff its `sources[]` (or source summaries) changed in S2.
- S4 runs for a region iff S3 output (`blindSourceSummaries`) changed textually
  (hash comparison, not "a rewrite ran").
- S5 runs iff S4 wrote anything; a failing gate blocks S6–S8 for that region only.
- S6–S7 run iff S5 passed and blind text changed. A region whose blind text is
  byte-identical after re-derivation stops here.
- S8 runs for a region iff S7 changed its summary or dossier inputs, **and** the
  coordinator has approved the rerate batch (manifest-visible approval). Unapproved
  regions keep their current scores; their new evidence ships in the next approved
  rerate, not incrementally.

**Zero-change fast path:** if research finds nothing new for a region (manifest
`stopped` with `stopReason: no-change` and no new sources), **no stage downstream of
research runs for that region** — no reblinding, no dossier re-render, no rerating.
This is the default outcome for a quiet region, not an optimization to request.

Content-hash gating is per-region per-stage: a stage keeps a small `.stagehash` sidecar
(or a row in the stage's input manifest) recording the hash of its inputs at last run;
it compares before running and exits with `no-change` without touching outputs when
the hash matches.

---

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Exa quota (~150/day) exhausted early by a few regions | Global budget: DDG-first rule (§2); per-round Exa cap per region (≤2 queries/round unless coordinator raises it); quota ledger in the wave log, checked at round start |
| DDG rate limits / 429s | Throttle + exponential backoff (pattern in `tools/run_research_wave.py`: serialized fetches, 5 attempts); rotate query phrasings; fall back to direct fetch of known trackers |
| Registry contention between concurrent region agents | Single-writer lockfile + tmp-then-replace RMW (existing `data/.apply.lock` pattern); promotion is a staged proposal, coordinator is the only promoter; agents re-read the registry at round boundaries, never hold it across a round |
| Cascade accidentally rerating everything | Hash gating per region per stage (§8); zero-change fast path is the default; rerate requires coordinator approval per batch |
| Verification bottleneck (one pass per source) | Verification is per *source*, not per region — shared sources verify once via the registry; region-local sources verify in parallel by their own agents |
| Contradictory sources between regions (same tracker, different readings) | Registry `citedIn` + `verification.notes` expose the divergence; coordinator resolves; quotes, not paraphrase chains, are the evidence |
| Round explosion (56 regions × 4 rounds × agents) | Max 4 rounds, signal-based early stop, rich early exit; queue order in the wave plan (US-states wave plan, `research/adaptive-research-plan.md`) prioritizes high-signal regions so the cap binds the quiet tail, not the rich head |

---

## 10. Non-goals

- No country-level re-research under this method (§7).
- No score invention: researchers do not assign scores; scoring stays with
  `research/ADM1_SCORING_PROMPT.md` + the pairwise machinery.
- No second source cache, no second registry: `research/fetched/` + `data/source_manifest.json`
  + `data/source_registry.json` are the only stores.
- No manual rerating, no hand-edited scores (rule 6).

---

## 11. References (current code this method builds on)

- `tools/run_research_wave.py` — coverage audit + verbatim n-gram anti-fabrication gate;
  locked RMW apply pattern.
- `tools/fetch_all_sources.py` → `research/fetched/<sha16>.{txt,meta}`;
  `tools/build_source_manifest.py` → `data/source_manifest.json`.
- `tools/check_blind.py` (blinding gate, rule 7/7b), `tools/apply_blind_fields.py`
  (blind-field validation/merge), `tools/make_blind_batches.py` (blind regen batches),
  `research/experiments/country-calibration-audit/five-way/blind_rewrite.py` (model-based
  primary blinding), `five-way/harness.py` (`render_admin1_dossier`, leak gate).
- `tools/blind_pairwise.py` (pairwise rating inputs; parent-anchor rules in
  `research/PIPELINE_INVARIANTS.md` §8), `tools/apply_admin1_scores.py` (score merge),
  `tools/consolidate_record.py` (summary-from-evidence).
- `tools/adm1_list.py USA --format md` — authoritative unit names + shapeIDs.
