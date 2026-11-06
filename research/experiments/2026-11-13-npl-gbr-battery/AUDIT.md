# Matched national→division propagation + calibration audit (Sol's first fix)

## Propagation (does the national exposure reach every division?)
- UK: Scotland/England document the national tier-1 (biological-sex custody/search),
  Wales partially, **Northern Ireland not at all** (yet NI scores lowest 0.461 — its
  local hostility, not the national tier-1). Documentation is inconsistent.
- US states: all mention "federal", but with very varying depth (Maryland lists
  federal/passport/custody/detention/executive-order/marker/immigration; California
  only "federal").
- Nepal provinces: **no national-exposure terms** in the dossier text (they are
  `estimated`, not dedicated dossiers).

## Calibration consistency (the core problem)
gap = division-mean minus national-framework (positive => divisions score ABOVE national):

| country | n | div mean | natl fwk | gap | sd |
|---|---|---|---|---|---|
| USA  | 51 | 0.348 | 0.264 | **+0.084** | 0.112 |
| UK   |  4 | 0.476 | 0.444 | +0.033 | 0.009 |
| Canada | 13 | 0.811 | 0.764 | +0.046 | 0.036 |
| Australia | 9 | 0.807 | 0.787 | +0.020 | 0.029 |
| Germany | 16 | 0.684 | 0.681 | +0.003 | 0.039 |
| India | 27 | 0.503 | 0.546 | **-0.043** | 0.026 |
| Brazil | 27 | 0.630 | 0.690 | **-0.060** | 0.054 |
| Mexico | 30 | 0.489 | 0.475 | +0.014 | 0.034 |
| South Africa | 9 | 0.653 | 0.703 | **-0.050** | 0.033 |

The gap is INCONSISTENT IN SIGN AND MAGNITUDE (-0.06 to +0.08). If national exposure
were propagated consistently and both were on one anchor ladder, the gap would be
stable. It is not — confirming the maintainer's "divisions are not mutually consistent
relative to each other."

## Why the US reads low
Two compounding causes:
1. The national-framework value (0.264) is too harsh under the rubric (settled:
   multi-model consensus 0.30-0.35).  [now corrected: US published 0.330 provisional]
2. National exposure is not consistently carried/calibrated into the divisions (the
   +0.084 gap and the varying per-state "federal" depth), so neither instrument is
   trustworthy on its own.

## Fix direction
Calibrate divisions AND national to ONE fixed anchor ladder with matched comparisons;
propagate each national exposure into every affected division exactly once (no omission,
no double-count). Then a visitor-weighted destination aggregation becomes meaningful.
Do NOT floor divisions — a genuine destination risk should lower the nation; remove the
spurious penalty/duplication/comparator noise instead.
