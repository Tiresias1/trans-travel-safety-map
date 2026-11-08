# OpenRouter generation metadata lookup

One read-only GET for `gen-1794119089-sSyXsbMryWONFjne0nMv` returned HTTP 200. There were no retries or other network requests. The allowlisted metadata and SHA-256 of the exact response bytes are saved at `research/experiments/country-calibration-audit/country-feasibility-v2/analysis/provider-generation-metadata.json`; no raw response was saved. Endpoint documentation: https://openrouter.ai/docs/api-reference/get-a-generation.

## Accounting comparison

- The native prompt/completion counts, **11,547 / 1,119**, match the preserved failed v2 attempt. The attempt recorded 12,666 total tokens; the generation record did not supply a total-token field. Its normalized prompt/completion counts are **14,454 / 1,440**, different from the attempt's counts.
- Native reasoning is **1,148**, still greater than native completion **1,119**. The relationship between native and normalized token counts, and whether those reasoning counts are nested in either completion figure, remains unclear. The provider record therefore does **not** fully reconcile token semantics.
- The provider's `total_cost` and `usage` are both **$0.000628782**, matching the preserved attempt's reported cost. Its reported `upstream_inference_cost` is **0**; the reason for that distinction is not established. This is not independent billing verification.
- The requested model was `deepseek/deepseek-v4.1-flash`; the lookup returned `deepseek/deepseek-v4.1-flash-20260910` and provider `Relace`. The preserved response reported the undated model and the same provider; the relationship between the model IDs is not assumed. Both lookup finish reasons were `stop`.

The failed v2 stage remains terminally stopped. This lookup does not validate a score or authorize resumption. The comparison used only accounting and routing fields, without displaying the model score.

## Validation and scope

A local, offline check verified the metadata allowlist, matching generation ID, SHA-256 format, requested-model binding to the frozen schedule, accounting comparisons, and the preserved terminal state. The repository status shows only the new metadata JSON as untracked, with no tracked changes and no staged paths. No experiment inputs, run artifacts, receipts, code, configuration, or git index were changed. The endpoint documentation URL was not fetched, consistent with the one-network-request limit; the response hash cannot be independently recomputed from the repository because raw response bytes were intentionally not retained.
