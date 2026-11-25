# Adaptive Research — Phase 1 deliverable + US-states wave plan (Phase 2 handoff)

**Authoritative output path for this run:**
`/home/meme/.pi/agent/sessions/--home-meme-kóði-kort--/subagent-artifacts/outputs/79d7155c-9f40-418c-858a-a8096a308db6/research/adaptive-research-plan.md`

---

# Part A — What Phase 1 wrote (methodology)

| File | What it is |
|---|---|
| `research/ADAPTIVE_RESEARCH_METHOD.md` | **The user-facing research contract.** Search budgets (DDG workhorse, Exa ~150/day), adaptive rounds (cap 4) with explicit self-reflection, shared source registry + ≥3-region promotion threshold with coordinator review, per-source verification gate with quarantine, hash-gated cascade, zero-change fast path, per-region manifests, scope (ADM1-only; US federal parent stays frozen), risks, non-goals. |
| `research/ADM1_RESEARCH_PROMPT.md` | Updated to the adaptive structure: new header section "Adaptive round structure (per region — mandatory)" implementing rounds, self-reflection prompt, registry use, verification, manifests, stopping rules, "no new facts without a source". All prior factual disciplines retained untouched (single-incident rule, mandatory exceptions clause, traveler-facing scope, stop rule, ranked order). |
| `research/PIPELINE_INVARIANTS.md` | New §9 "Adaptive research (2026-11-25)" binding rules (a)–(h): search budget, rounds cap 4, registry + promotion + single-writer lock, verification gate + quarantine, hash-gated cascade, zero-change fast path, scope/parent-freeze, per-region manifests. Explicitly re-asserts rules 1–8 remain in force. |

**Key design decisions:**

1. **Registry is a new file** (`data/source_registry.json`), *beside* — not merged into —
   the existing `data/source_manifest.json` (URL → title/date/jurisdictions). The manifest
   knows what a source *is*; the registry knows what it *did* (fruitful-in, cited-in,
   verification, promotion decision).
2. **Verification is a separate pass from harvesting** (different agent invocation than
   the finder) — the researcher who found a source cannot clear it. Anti-fabrication
   reuses the existing verbatim n-gram pattern from `tools/run_research_wave.py`.
3. **Cascade stages map 1:1 onto existing scripts** (§8 of the method doc): fetch →
   manifest → blind rewrite → lead re-blind → `check_blind` → single-render dossier →
   consolidate → pairwise rerate. No new machinery is invented; only the *gating* is new.
4. **Rerate requires coordinator approval per batch** (manifest-visible) — evidence ships
   in the next approved rerate, never incrementally. Parent anchors (`PARENT_ANCHOR_FRACTION
   > 0`) + parent-current seeds per PIPELINE_INVARIANTS §8 are mandatory in any rerate.
5. **Rounds read the registry at round boundaries**, so a common-source promotion takes
   effect for all regions (including already-running ones) without restarts.

**Risks (see method doc §9 for full table):** Exa quota exhaustion (mitigation: DDG-first
+ per-round Exa cap of 2/region + quota ledger), DDG rate limits (throttle/backoff,
existing patterns), registry contention (single-writer lockfile + tmp-replace; only the
coordinator promotes), accidental full-cascade rerates (per-region hash gating, zero-change
default), verification bottleneck (per-source, not per-region — shared sources verify once).

**Paths:** method `research/ADAPTIVE_RESEARCH_METHOD.md`; researcher prompt
`research/ADM1_RESEARCH_PROMPT.md`; invariants §9 in `research/PIPELINE_INVARIANTS.md`;
registry `data/source_registry.json` (does not exist yet — Phase 2 creates it at wave
start); round manifests `research/adaptive/USA/<region>.manifest.json`.

---

# Part B — US-states wave plan (the Phase 2 worker's deliverable)

## B1. Scope: 56 units, all as ADM1 under USA

**50 states + DC + 5 territories = 56 ADM1 regions:**

| Group | Units | Notes |
|---|---|---|
| 50 states | Alabama … Wyoming (see `tools/adm1_list.py USA --format md` for exact names + shapeIDs) | `data/admin1.json` already carries 51 USA records (50 states + DC), all dossier-bearing, researched 2026-10-01 – 2026-10-04. This wave refreshes them; it does not create them. |
| DC | District of Columbia | shapeID `66186276B94082813086253`. Federally-administered caveat already in dossier. |
| PR | Puerto Rico | **Currently a country record** (`data/countries.json: PRI`, score 0.451357) and listed as EXCLUDED by `adm1_list.py`. Research as ADM1 under USA; do not create/refresh a country record. |
| GU | Guam | Currently country record `GUM` (0.407106). Same treatment. |
| VI | U.S. Virgin Islands | Currently country record `VIR` (0.370414). Same treatment. |
| MP | Northern Mariana Islands | Currently country record `MNP` (0.407332). Same treatment. (ADM1 list shows MP as a USA unit; `adm1_list.py` output confirms PR exclusion; GU/VI/MP/AS need shapeID confirmation from `boundaries/admin1.geojson` at wave start.) |
| AS | American Samoa | Currently country record `ASM` (0.416686). Same treatment. |

**Territory handling rule (binding):** territories are researched **as ADM1 under USA,
never as countries** — the parent's full operative layer (federal Executive Order /
passport / custody block) must render in each territory dossier with rule-2 parity
(parent-layer keyword counts comparable to a sibling state) before any pairwise run.
The pre-existing country records (PRI/GUM/VIR/ASM/MNP) are **flagged for the
coordinator, not silently deleted** — reconciling the map's territory representation is
a coordinator decision outside this wave. If a territory's ADM1 shapeID cannot be
confirmed in boundary data, the manifest records `stopReason: coordinator` and the
region is skipped, not improvised.

**Parent framework (frozen):** `data/countries.json: USA` (score 0.379039, 22 sources)
is authoritative and is **not re-researched**. State research that contradicts it is
flagged in the region manifest (`knownGaps`/`selfReflection`), per method §7.

## B2. Primary target: midterm trans ballot measures / referenda + related state legislation

The wave's primary target is the **2026 midterm cycle**: trans-related ballot measures /
referenda (state initiatives, referenda, bond/social-issue measures with trans provisions)
and related state legislation since the last research pass (2026-10-01 – 2026-10-04 for
the 51; territories per their records). Secondary material changes anywhere in the
dossier (new facility bans, enforcement actions, shield-law changes, violence patterns)
are captured by the ordinary adaptive rounds.

**Per-region search seed (round 1, then adapt):**

- `<State> ballot measure 2026 transgender initiative referendum`
- `<State> legislature transgender bill 2025 2026 bathroom facility`
- `<State> ballotpedia transgender measure`
- `<State> transgender violence rate state comparison dataset`

Ballot-measure full text is exactly the Exa-worthy case (long legal text, DDG-resistant);
statute/bill tracking is DDG-first.

## B3. Region queue order

Priority = expected signal volume × risk of change, so Exa/DDG budget is spent where
change is likeliest first, and the round cap binds the quiet tail:

1. **Tier 1 — active litigation/amendment states (Oct 2026 dossier shows live fights):**
   Idaho, Kansas, Florida, Texas, Tennessee, Louisiana, Arkansas, West Virginia, Montana,
   Utah, South Carolina, Alabama. (Idaho HB 752 court status; Kansas SB 244 suit;
   Florida enforcement record — all dated mid-2026, highest churn.)
2. **Tier 2 — 2026 ballot-measure states:** any state with a certified 2026 trans-related
   measure (discovered in the first Tier-1 round's registry; the coordinator promotes
   ballot databases — Ballotpedia state pages — to `common` once fruitful in ≥3).
3. **Tier 3 — remaining states:** alphabetical, with per-round signal-stop rules.
4. **Tier 4 — territories (PR, GU, VI, MP, AS) + DC:** run after the states so their
   dossiers can reuse the parent-layer template and the promoted common sources; each
   gets the rule-2 parity check before it is marked ready for pairwise.

Concurrency: **small batches only** (laptop RAM; AGENTS.md guidance — a few region
agents at a time, not 56). Suggested: 2–4 concurrent region agents, Tier 1 first.

## B4. Exa budget math

- Budget: **~150 Exa queries/day, global** (all agents, all regions).
- Cap: **≤2 Exa queries per region per round** unless the coordinator raises it.
- Expected spend: Tier 1 (12 regions × up to 4 rounds × 2) ≈ 96 queries worst-case,
  spread over ≥2 days; Tier 2–4 run mostly on DDG + promoted common sources.
- The wave-ledger records remaining quota at every round start; when the ledger shows
  <20 queries remaining, Exa is reserved for ballot-measure full text only.
- DDG carries the load: 56 regions × ~3 queries × ~2 rounds ≈ 340 DDG queries total,
  throttled with backoff (existing `run_research_wave.py` pattern).

## B5. Expected duration

**Days, in background** — this is a long wave, not a session:

- Tier 1 at 2–4 concurrent agents, 2–4 rounds each: **1–2 days**.
- Tiers 2–3 (remaining ~39 states, mostly 1–2 rounds or signal-stop): **1–3 days**.
- Tier 4 territories + parity checks: **0.5–1 day**.
- Cascade (hash-gated; zero-change regions skip everything): **0.5–1 day**, plus
  coordinator rerate approval time.
- **Total: ~3–7 days** elapsed, depending on Exa quota refill and coordinator
  touchpoint latency. No launches, no launches — the Phase 2 worker dispatches Tier 1
  only after the coordinator approves this plan's queue order.

## B6. Per-region manifests (the cascade contract)

Path: `research/adaptive/USA/<region-slug>.manifest.json` (schema: method doc §6).
Required fields per region: `region`, `shapeID`, `round`, `roundsUsed`, `queries[]`
(engine per query), `sourcesNew[]`, `sourcesVerified[]`, `leadsScheduled[]`,
`selfReflection`, `stopped`, `stopReason`, `knownGaps[]`. The cascade reads
`stopped` + `sourcesNew` to decide zero-change fast path vs. full cascade; the
coordinator reads `knownGaps` + registry proposals. **No manifest, no cascade.**

## B7. Coordinator touchpoints (all manifest/registry-visible)

1. **Source-promotion review** — when a source hits ≥3 fruitful regions, the
   coordinator promotes it to `common` in `data/source_registry.json` (decision +
   date recorded). Regions pick it up next round.
2. **Quarantine review** — failed sources are quarantined automatically by the
   verifier; the coordinator reviews the quarantine list each round boundary.
3. **Territory contradiction review** — any state-vs-parent contradiction flagged in
   manifests is a coordinator decision; agents never edit `data/countries.json: USA`.
4. **Rerate approval** — after S7, the coordinator approves (per batch, in the wave
   log + manifest) which changed regions enter the pairwise rerate. Unapproved regions
   keep current scores.

## B8. Stop conditions

- **Per region:** rich early exit · no-change · signal stop (2 rounds national-only) ·
  hard stop at **4 rounds** (remaining leads → `knownGaps`).
- **Per wave:** Exa ledger <20 → Exa restricted to ballot full text; DDG sustained
  429s → pause 1h and resume at lower concurrency; registry lock contention → serialize
  writers (never bypass the lock).
- **Wave complete when:** all 56 regions have a manifest with `stopped: true`, all new
  sources are either verified-and-cited or quarantined, the cascade has run to S5
  (check_blind passed) for every changed region, and the coordinator has approved the
  rerate batch. Scores only move via the approved pairwise rerate — never manually.

---

# Part C — Readiness for Phase 2

- **Ready:** methodology contract, researcher prompt, invariants §9, and this wave plan
  are written and internally consistent. No code changes were needed or made — the
  method reuses existing scripts; gating is procedural + manifest/hash based.
- **Phase 2 preconditions (coordinator):** (1) confirm GU/VI/MP/AS shapeIDs in
  `boundaries/admin1.geojson`; (2) decide disposition of the pre-existing territory
  country records (document, don't delete, in this wave); (3) create
  `data/source_registry.json` at wave start (empty + schema from method §4);
  (4) approve Tier-1 queue order (§B3).
- **Not done (deliberately):** no provider waves launched, no Exa/DDG queries spent, no
  data/ writes, no smoke test that writes `data/` — per Phase 1 scope.
