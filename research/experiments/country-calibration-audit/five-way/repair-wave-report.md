# Symptomatic repair wave report (2026-11-27)

## Phase A — Wales dossier repairs (done by repair worker)
Four repairs from wales-thin-dossier-audit.md applied (de-inflated Action Plan,
consultation-stage guidance correctly marked, unenacted ban removed) plus added
missing restrictive operative facts. Re-blinded. Wales score untouched in this phase.
Backup: runs/repair-wave-20261127/pre-phaseA-admin1.json.

## Phase B — contamination gap reruns (done)
All 6 transport-gap groups judged OK (CHL MYS IDN MEX NGA USA); appended to
analysis/contamination_audit.json. CHL: confirmed Region Metropolitana Santiago
incident case + questionable Los Lagos case.

## Phase C — confirmed-contamination moves (done)
87 confirmed facts moved from parent country records to sibling division evidence
(manifest: research/contamination-repair-manifest.json), re-blinded
(runs/repair-wave-20261127/). Scores/bands untouched in this phase. Repaired
groups re-judged (runs/repair-wave-20261127/phaseC_rerun.json, phaseC_rerun2.py);
questionable items flagged separately (see analysis/contamination_audit.json appendices),
not moved.

## Phase D — UK re-rate post repair (done, report-only at the time)
36 calls, 34 OK, $0.216. Parent GBR 0.438 fixed reference (never updated).
Finals: England 0.433, NI 0.459, Scotland 0.490, Wales 0.507. Draw means:
Wales 0.510 / NI 0.490 / Scotland 0.481 / England 0.439. Scotland-England gap
+0.057; England returns to the parent level after its dossier reverted from the
round-3 concentrated form; Wales remains highest even after repair — now with
a de-inflated dossier, so the residual is at least partly genuine protective
delivery + residual thin-data premium (see Wales audit).

## Worker status
The phase A-D worker timed out after completing all phases; the aggregate analysis
(analysis/uk_rerate_post_repair.json) and this report were deduplicated by the
coordinator from the worker's raw artifacts. Under the standing user instruction
(deploy everything; no approval required) the coordinator synced the Phase-D
finals and deployed this report + data diffs.
