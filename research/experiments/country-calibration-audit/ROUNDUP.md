# Roundup — state at end of this session (2026-11-07)

All evidence and reports live in this folder. Nothing was committed; nothing user-visible
was deployed; no published score changed at any point.

## Completed
1. **Evidence repair (applied to data/countries.json, USA block only, 9 lines):** the two
   overstated claims (visa fraud-bar, cash-reward directive) rewritten to primary-verified
   scope per `us-primary-ocr.md`; `us-repair-final.md` holds the final before/after and the
   backend-only provenance note. Applied after Terra fidelity review
   (`terra-fidelity-review.md`, blocked-as-written → 5 prescribed fixes, all applied) and
   one follow-up de-quoting the pre-existing "anti-American" leak in `blindSummary`.
   Gated: exact-once replacement, full JSON before/after diff (0 scores changed,
   232 other countries byte-identical), check_blind 233/233, changelog 0.
   Flagged scope-expansion items C9/C10 updated the outdated "not corroborated" caveat.
   Residual: cable = OCR of one image-only copy; bounded-search absence ≠ proof;
   pre-existing blindSummary strategy clause paraphrased per reviewer wording.
2. **Country pilot (`pilot2-report.md`, 96 calls, production rater):** USA order effect
   first>second 4/4 pairs (2/4 exceed within-cell noise); pilot-1's 0.22 contrast shrinks to
   0.068 with 4 draws (order/draw confounding confirmed); isolated USA 0.320±0.014 (tight),
   isolated > pair for all three targets; partner-context shifts up to ±0.06; identical-copy
   block-order shift (USA −0.12), zero within-call A/B bias; relative ordering NPL>GBR>USA
   stable everywhere far beyond noise. Absolute US level is instrument-unstable.
3. **ADM1 shadow (`adm1-shadow-report.md`, frozen national level + documented local
   delta):** controls perfect (no-evidence 0.00, duplication-not-counted 0.00), 0/33
   national re-rating violations, 0 boundary hits; deltas CA +0.045, TX −0.120, ENG −0.015,
   BAG +0.025; shadow-vs-published mean gap −0.002 (mixed signs, no uniform bias).
   Known weak point: "is this local fact already national" is case-by-case and draw-unstable
   (England/Texas); paraphrased duplication not auto-detected; label effect +0.04;
   thin-evidence drift (Bagmati +0.025).
4. **Manifest reporting fix (`tools/build_manifest.py`, uncommitted):** reproducibilityAudit
   now reports live verifier output fail-closed (AUDIT: FAIL, USA 0.33 vs archived 0.264359
   named explicitly); stale 3474/3474 claim and unsupported residualClass removed;
   logArchive.note corrected; SELFTEST: PASS.
5. Retracted the over-claimed causal conclusions in `../2026-11-13-npl-gbr-battery/AUDIT.md`
   and `FINDING.md` (kept as corrected history).

## Open decisions (user)
- Commit + deploy the text/provenance work (site still shows old text; commit would update
  it after Pages build)? The manifest fix makes `build_manifest --check` honest but red
  while the US override is unreconciled — decide whether that stays red or an approved
  reconciliation path is chosen (never by re-labelling the override as reproduced).
- Scale the country instrument: re-run the same design with more draws / always-balanced
  orders as a candidate production measurement method? Pilot evidence says pairwise
  absolute levels are unstable (USA especially) while isolated assessments are tight.
- ADM1: pilot the national-baseline+delta interface at larger scale (more countries,
  more divisions), with the double-counting weakness addressed first (e.g. explicit
  per-fact inheritance checklist)? Nothing publishes without approval.
- The US override (0.330 vs archived 0.264359) remains an open reconciliation item; the
  evidence gathered (pilot isolated 0.32±0.014; prior 4-model calls 0.32/0.32/0.39/0.18;
  order/partner sensitivity) informs but does not settle it.

## Working rules encoded this session
- User-visible text: clean verified prose. Attribution/citation-gap material is
  backend-only. No development/audit language in UI.
- No regex prose surgery; LLM rewrites only. No Grok/Muse. Cheap MiMo subagents for
  routine work; Terra (thinking medium, non-leading questions) for reviews.
- Country scores never derived from ADM1 scores; ADM1 diagnostics never recentre.
- Provider content_filter failures: retry same-protocol with reduced sensitive-content
  throughput, not silent lane switches.
