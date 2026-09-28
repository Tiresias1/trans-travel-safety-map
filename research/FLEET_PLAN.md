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
