# Fleet plan — source-integrity pipeline (status 2026-09-28)

Context: launched from the "American Samoa sources" review. Country+region source bases
were audited/trimmed for relevance; summary text is now known to contain unsourced
claims (1200+ flagged) and pipeline boilerplate. Nothing may be hand-fixed — all
repairs flow through these waves. Countries.json scores are trusted inputs; REGION
scores are provisional until sources/summaries are reworked.

## Waves (queue)
1. ✅ Wave1 countries full audit (35) + Wave2 remaining countries (167) — applied, 270 pruned.
2. 🔄 Wave2b: 66 throttle-lost countries (lanes 087ae3.. running) → on completion:
   `python3 tools/audit_relevance_results.py --plan` → `--apply` → build_data → commit+push.
3. Region tier (633 packets): mechanical pass first (deterministic, filter-proof):
   `python3 tools/mechanical_region_audit.py` → apply → build → commit. LLM tranche ONLY
   for flagged subsets later (scrubbed packets: url+title only).
4. Freshness wave (T1 stale legal claims; batches data/fresh_batches/fNN.json,
   oldest-first, name+url+title inputs only — raw claims are NOT sent to lanes since
   provider data_inspection_failed kills lanes on graphic text). Outputs
   data/freshness/fNN.json {results:[{who,url,status,fact,newer:[{url,title,date}]}]}.
5. REWORK wave (after 1-4): per jurisdiction: inputs = current record + retained sources
   (relevance_results verdicts) + false_claims + search_updates + freshness facts.
   Qwen (qwen3.8-flash, tools/call_qwen.py) regenerates visible summary + blind* fields,
   countries.json-style: claim-per-source, no boilerplate, no deviation-space language.
   Territory summaries: drop "re-anchored" provenance entirely; facts + framework only.
6. Re-pairing: territories (--only-countries) + regions (--regions-vs-countries) with
   comparator prompt updated to show per-source DATES (data/source_manifest.json) and a
   recency rule. Then build_data, deploy (push + bump index.html ?v= stamps).

## Invariants
- One git writer at a time; never rebase while fleet waves are in flight (429 lesson:
  66 lost lanes came from launching 24 at once; <=12 lanes per fanout, staggered).
- Every wave: --plan first, apply, build_data (CI gate), commit+push, log to
  data/fleet_log.md (one timestamped line per step).
- research-needed floor=2 sources; jurisdictions below get priority in rework (must
  gain NEW dated sources in freshness wave or be honestly flagged in summary).
- Scores only move via blind_pairwise.py; audits never touch score fields.

## State @ handoff point
- Freshness: sf01-08 done, g-tranche landing; 147 judged/24 superseded. Merge point: data/freshness/*.json consumed by make_rework_batches.py.
- Rework: data/rework_batches/r0NN.json (34 batches/300 flagged records: derived-ancestors + research-floor + audit-flagged regions). Lane rules must be filter-safe: lanes get the batch file (claims are short quoted clauses — if 400s recur, strip flags[] to token lists).
- After rework applies: territory pairwise via blind_pairwise --only-countries <37+parents>, then region re-calibration --regions-vs-countries, dated-evidence prompt tweak, deploy.

## RESUME HERE (session handoff, 150 merged + final 11-batch tranche in flight)
1. When tranche 4 wakes: `python3 tools/apply_rework.py` (expect ~108 more), compact remaining (script pattern in git history, e.g. commit "rework tranche 3 merged"), dispatch any leftovers until remaining=0, build+commit+push.
2. Re-pair territories (37 derived + parents): `python3 tools/blind_pairwise.py --only-countries <list from fix_derived_anchors TERR keys + GBR USA FRA NLD DNK NZL CHN MAR> --num-pairs 500 --workers 4` (re-anchored scores + fresh reworked blind fields). Re-run any region whose batch lane reported flags dropped materially, or simply re-run --regions-vs-countries for flagged countries (workers<=8, tranche if throttled).
3. Comparator dated-evidence: inject data/source_manifest.json publication dates into dossier() evidence bullets + one recency rule in RATING_RULES; deploy = build_data, bump index.html ?v=, push, curl-verify Pages; final sanity: ASM ~0.6+ if its 1980 decrim fact made it into summary via freshness/rework (do not force if sources still disagree).
