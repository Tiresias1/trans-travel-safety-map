# Global ADM1 iterative pairwise anchored calibration — report (global-adm1-iterative-20261117)

## Logistics

- Script: `global_adm1_iterative.py`; run artifacts: `runs/global-adm1-iterative-20261117/`; aggregate: `analysis/global_adm1_iterative.json`.
- Scope: 3241 ADM1 records in `data/admin1.json` with a current numeric score, minus 4 US-territory dependency records (ASM, GUM, MNP, VIR) = 3237 included across 227 ISO3; 2048 have a local differentiator, 1189 are no-differentiator (neutralized local evidence <20 words or >90% parent-frame overlap; excluded from pairing, recorded in aggregate `scope.no_differentiator_regions`, no score update); 36 differentiator records are singleton within ISO3 and never focal/partner (stay at initial score); focal-eligible: 2012. US states included. Iterations 1-9 used parent-only dossiers (kept); neutralized-summary rule applies from iteration 10.
- Dossiers: parent framework + blind division fields via `harness.render_admin1_dossier`, plus neutralized local evidence (`summary` plus `blindSummary` where present) for every record through `neutralize()` (record/country names and ISO3 -> this division/this country; score-like numbers removed).
- Planned pairings: 4800; completed: 4800.
- Seed: 20261117; focal ADM1 random; candidate partners: nearest max(10% of that country's ADM1 regions, 3) by current running score within ISO3 (capped at n_iso3-1), tie-break region id; no immediate repeat of the same unordered pair when an alternative exists.
- Effort: medium via `provider_models.call_v4`; exactly one model per pairing, chosen by per-ADM1 least-used model (participations in either slot) with seeded tie-break; attempts per pairing: 1; retries: none; failed draws recorded with no score update. Models (7): mimo, deepseek, qwen, glm, haiku, luna, muse.
- Update schedule (both participants, per-ADM1 update number): updates 1-20 `0.80*old + 0.20*new`; 21-25 `0.92*old + 0.08*new`; 26+ `0.95*old + 0.05*new`.
- Base v4 system sha256: `c5814409d66a4f21e4674fe9377ca4e21d875ff82c3643fbc03870db7d77e3a5`; directive-augmented system sha256: `3f6af3f8f757a108afe5d87362d576cf6cbe7308a9e4d4f97a8f6a29facc5e56`. Directive: severe LGB signal is operative when trans-specific data is absent; legal ambiguity does not create safety; de facto authorities count; discovered/outs visitors are not assumed invulnerable for denying same-sex conduct; absence of a documented exact pathway is not mitigating evidence.
- Initial scores: `iterativeScore` if present, else `score`, per record from `data/admin1.json` (site data not overwritten).
- Single-writer guard: `global_adm1_iterative.py` refuses to launch if another such process is running (reports PID).

## Cost and outcomes

- OK: 4128; rejected/failed: 672.
- Total cost (exact): 23.79903788473 USD.

| Model | OK | Rejected/failed | Cost USD |
|---|---|---|---|
| mimo | 432 | 259 | 3.0306286806 |
| deepseek | 576 | 86 | 3.34212867323 |
| qwen | 560 | 139 | 5.879245590 |
| glm | 500 | 166 | 2.5634070989 |
| haiku | 693 | 6 | 4.6325644 |
| luna | 680 | 3 | 2.214368750 |
| muse | 687 | 13 | 2.136694692 |

## Drift summary (final minus initial)

- Included records: 3237; updated: 1985.
- Mean drift (all included): 0.013872
- Mean absolute drift (all included): 0.020500
- Max absolute drift (all included): 0.138193
- Min drift (all included): -0.089389
- Max drift (all included): 0.138193
- Mean drift (updated only): 0.022621
- Mean absolute drift (updated only): 0.033431
- Max absolute drift (updated only): 0.138193
- Min drift (updated only): -0.089389
- Max drift (updated only): 0.138193

## Model-usage balance

- Records with participations: 2005.
- Mean largest-model share per record: 0.3730
- Max largest-model share per record: 1.0000
- Mean model-count range per record: 1.441
- Max model-count range per record: 4

