# MASTER TODO (user, 2026-09-29) — applies to BOTH countries.json and admin1.json
1. All links checked, off-topic deleted, updated info fetched where needed, summarized.
   STATUS: audits ran under OLD specs; ASM test proved the fixed pipeline. Fleet redo = W1.
   Known holes: freshness landed for only ~15 jurisdictions (g-lanes mostly lost, never
   reconciled); 161 regions flagged needsIntake; link claims mostly violate LANE_SPECS r2.
2. summary/offScope/tangential/localsOnly generated: countries mostly have 4 fields;
   only 167/633 regions do. Region split pass = W2.
3. All fields blinded under LANE_SPECS r7/7e w/ check_blind gate: only ASM has v2 blind.
   Fleet-wide blind regen = W3 (gate every record; self-gating lanes only).
4. Blind pairwise: COUNTRIES FIRST (233×16 ≈ 3,700 pairs), THEN admin1
   (--regions-vs-countries, 633×16 ≈ 10,100 pairs ≈ 20-24h workers=4; run in country-chunk
   tranches, commit per chunk). Only AFTER 1-3. 16 comparisons/entity average.
LESSONS-LECS BAKED IN: r1 Hertz on-topic; r2 task-useful claims; r3 exact URLs
(prefix-match fallback); r4 floor=2+needsIntake; r5 framework tie-break; r6 four-field;
r7/7e derivation-only blind; apply-time ordering = newest-mtime + per-(who,class) ownership
(apply_rework pattern); NEVER trust aggregate counts or lane attestations — verify landed
(verify_prunes / check_blind / per-record diffs); content filter kills lanes reading graphic
text — tolerate deaths, self-heal via rebatching, mask or grep-only for hot locales; no git
push while other writers active; deploy after changes (build, push, curl-verify Pages).
WAVES: W1 links (link_batches/link_out/apply_links) -> W2 region 4-field rework
(reuse make_rework_batches+apply_rework, regions scope) -> W3 blind regen
(make_blind_batches/apply_blind, gate) -> W4a countries pairwise -> W4b admin1 pairwise ->
deploy+verify. After each wave: apply -> build_data -> per-record verify -> commit+push.
INFRA NOTE (2026-09-30 22:30 UTC): all subagent lanes failed at bootstrap after a pi-subagents
npm auto-update (package root mtime 20:30). Host (session started earlier) loads src-runtime as
`.ts`; new package ships `.js` only -> "Extension path does not exist". Repair: created shim
`~/.pi/agent/npm/node_modules/pi-subagents/src/runs/shared/subagent-prompt-runtime.ts` re-exporting
the compiled `subagent-prompt-runtime.js` (named + default). Verified by infra-check lane. Safe to
delete after Pi host restart (which will load package layout natively). Repo untouched.
