# Non-dossier merge report v3 (hardened parent-diff + relaxed validation)

Run: `nondossier-merge-v3-20261124` (MiMo medium, one call/region; mean rating in code).
Worker timed out at ~1,089/1,219; script finished detached; this report written by coordinator.

## Coverage
- 1,219 regions: **1,161 ok / 58 rejected**, exact cost **$0.6121699460**.
- Knowledge class: region-specific 900, parent-only 261 (of ok).
- Length: median 202 words; parent-only median 114 / max 162; region-specific median 210 / max 292; overall max 292.

## Hormozgan (worked example; sid 17685810B64963005891064, rating 0.093857)
- v1 (live before this sync): 2,597 chars, dossier-length, national sources shown as region references.
- v2: 185 words but still re-narrated parent regime beyond one sentence.
- v3 (186 words, class region-specific): one parent sentence ("subject to Iran's national law in full, with no local exception."),
  then local color (Persian Gulf coast, Bandar Abbas cosmopolitan port, Kish/Qeshm tourists, anonymity limits,
  conservative Baloch Sunni society, checkpoints, scarce support networks). Residual borderline: "gender-nonconforming
  presentation is at least as socially fraught as elsewhere in Iran" — framed as local social climate (knowledge claim),
  not parent provisions. No criminal-provision enumeration, no victimology list.

## Parent-restatement audit (coordinator spot-checks)
- Length caps now hold (parent-only max 162 words); the one-sentence parent rule holds in spot checks.
- Rejected breakdown (58): contract violations preserved as gaps (summaries in raw responses, not applied).

## Changes vs v2
- Locality test verbatim in prompt ("could I have written this from the parent text alone? then it goes");
  paragraph tolerance back to 3; same seven source waves; same mean-rating computation.
