# OK — offline provider-usage check

- The saved attempt and lookup agree on generation ID, provider, native prompt/completion counts (11,547/1,119) and reported charge ($0.000628782). The saved response uses the requested undated model; the lookup returns a dated model ID. Their relationship is not established. Both saved and lookup finish fields are `stop`. Normalized counts differ, and native reasoning count 1,148 exceeds native completion 1,119; token semantics remain unresolved.
- Independently summed the four probe charges and v1/v2 attempt charges: $0.002622058, matching `RESULT.md` and `CURRENT_STATUS.md`. These are reported charges, not independent billing verification. The saved response reports upstream inference cost $0.000628782 while the lookup reports 0; the cause is unknown.
- The terminal result records `stopped`, one attempted call, and the same costs. The documents explicitly prohibit resumption and do not claim a validated score. `run.json` still says `in_progress`; the terminal `result.json` is the relevant final record.
- The metadata contains only scalar timestamp, HTTP status, generation IDs, model/provider routing, token and cost fields, finish fields, a hash and documentation URL. No secret, user ID, header, response content or reasoning text was found in the allowlisted metadata. The report discloses raw lookup bytes were not retained and the SHA cannot be independently recomputed; hash syntax alone was checked.

## Evidence
- `country-feasibility-v2/analysis/provider-generation-metadata.json` lines 1–26; `provider-generation-lookup-report.md` lines 3–16.
- `country-feasibility-v2/analysis/RESULT.md` lines 7–35; `CURRENT_STATUS.md` lines 40–62 (paths relative to `research/experiments/country-calibration-audit/`).
- Programmatic field-only extraction from `country-feasibility-v2/runs/v2-stage1-call-001/attempts/call-001.json` and `result.json`, plus the v1 attempt and four probe results. No network requests, repository edits, or staging performed. Existing lookup provenance and lack of retained raw lookup bytes cannot be independently verified offline.
