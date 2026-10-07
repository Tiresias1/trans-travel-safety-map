# Lane spec corrections (2026-09-29) — apply to ALL audit/rework/freshness launches

> **STYLE GATE — read `tools/STYLE_RULES.md` before generating any text field.**
> Every prose field (summary, tangential, localsOnly, outOfScope, source summaries, blind
> mirrors) must be written in the STYLE_RULES voice: professional/report-like, no LLM-isms,
> and — above all — **never a changelog**. Text that describes "an earlier profile", "has
> been deleted", or any previous state of the map is a hard failure, the same way a banned
> word in a blind field is. When in doubt, state the current fact, not the editing history.

1. on_topic: "the article concerns THIS jurisdiction" means the jurisdiction is a SUBJECT of the
   article, not that the article is merely compatible with it. Example rule: an article about
   Hertz car rental is NOT on-topic for a region just because people there drive cars.
   National-framework documents ARE in scope for region records when the framework is what the
   visitor stands under (the encompassing state's law applies to its regions) — for dependent
   territories likewise. Never mark a framework source off-topic merely because the region's
   name doesn't appear in it; mark supports by whether the CLAIM's facts appear.
2. Source link summaries are NOT "summarize the article". They are: "state the information
   USEFUL TO THIS RECORD that the article contains" — substance, with numbers/dates/outcomes,
   2-5 sentences. If the page has no usable finding for this record, say exactly
   'thin: no usable finding' (that verdict then feeds intake, never a silent pass).
   TRANS-VISITOR RELEVANCE TEST before writing a claim: would this fact change what a
   trans visitor faces (law, enforcement, documents, entry, screening, care, facilities,
   violence, partner recognition, protection)? If not, it is OUT and must not appear,
   even as background. Generic travel logistics that apply in every country (carry-on
   limits, prohibited items, airline procedure, general crime/city safety) are ALWAYS
   OUT unless they are trans-specific (scanner/pat-down outing risk IS in; liquid limits
   are NOT). Substance over creator (see below).
   SUBSTANCE OVER CREATOR: a claim names the ACT (what happened, whom it hits, the quoted
   provision, the penalty, the date); it does not spend sentences describing the outlet
   ("state news agency", "official state-press"), the article's existence, or the fetch
   experience. The outlet/creator is identified once, lightly, only where it changes the
   evidentiary weight (e.g. "government announcement as reported by X"). Never narrate the
   fetch ("page body was largely navigation content", "headline finding only") — that is
   meta-commentary; if the page could not be read, write the usable finding you did extract
   or 'thin: no usable finding'. BAD: "Agence Nigérienne de Presse (state news agency,
   French): headline 'Le Niger criminalise' — official state-press announcement of the
   criminalisation. Page body was largely navigation content at fetch time." GOOD: "Niger's
   new penal code (Feb 2026) criminalises 'indecent, unnatural and LGBTQIA+ acts' (art. 390;
   5-10 years) — reported by the state press agency after adoption."
3. Verdicts must echo the record's source URL EXACTLY (copy, never truncate — lanes truncated
   URLs at 56 chars and prunes silently missed; verify_prunes now prefix-matches, but lanes
   must still copy verbatim).
4. No lane may remove a record's last sources: floor=2 usable links; below that, needsIntake
   and the intake step supplies replacements.
5. Tie-break for territory/region records vs rule 1: a generic parent-framework document stays
   on a child record ONLY if the child's own text makes a claim that document supports AND no
   child-specific source covers it; otherwise drop it (the fact belongs sourced on the parent).
6. Four-field split for ALL rework outputs (visible AND blind mirrors of each):
   - summary: THE VISITOR RISK ASSESSMENT — what a trans traveler faces on the ground: legal
     protections/enforcement, practical safety, documents/screening at borders, marriage/travel-with-
     partner relevance. Context may inform the assessment but must not dominate it.
   - tangentialFactors: adjacent circumstances coloring a visit but not core local risk (federal
     policy turbulence of the parent state, litigation flux, comparisons with neighbours).
   - localsOnly: facts governing residents, not visitors (cultural-gender roles like fa'afafine
     social embedding, birth-register practice, resident discrimination data, local surveys).
   - outOfScopeNotes: unresolved or unverifiable status ('passport marker regime unknown'), scope
     caveats. Each field: as many <p> as the sourced substance requires — NO paragraph cap.
     If the source set carries 8 distinct substantive visitor-relevant claims, the summary
     should carry all 8 (each claim one <p>, or grouped where tightly linked), NOT the top
     2-3. The summary is the dossier's digest of the evidence, not a press-release opener;
     covering every sourced claim is what makes the map's popup authoritative. Quality rules:
     absolute terms, sourced, report-voice (see STYLE_RULES) — verbosity is not a bug when
     each paragraph is a distinct sourced finding. Caps: keep outOfScopeNotes to plain
     sentences; do not pad with rephrasing — one paragraph = one claim or one tightly-linked
     claim cluster.
7. BLIND MIRRORS ARE DERIVATIONS, NOT REWRITES. Rules:
   0. VISIBLE FIELDS USE REAL NAMES — the actual country, territory, ministry, court,
      statute. The fixed vocabulary below is BLIND-FIELD ONLY. Writing "the administering
      state", "the parent nation" or "state/province" in a VISIBLE field is the same class
      of error as a blind leak, and ships rejected. (Fault fixed 2026-10-05: territory
      outOfScope text carried blind vocabulary into the visitor-facing map.)
   a. Substitution-only: every substantive claim in a blind field must exist in its visible
      counterpart. NO new descriptors (geography, direction, ocean, climate, governance flavor)
      may appear in blind text that the visible text lacks. Adding "South Pacific chiefly
      customary" to blind a US territory is an unblinding attack, not caution.
   b. Fixed vocabulary (countries-tier convention):
      territory/dependency -> "state/province"; colony/colonial/colonisation -> "historic"/
      "historic administration"; federal/federation/federal republic -> "national"/"the parent
      nation"; island(s)/archipelago/atolls -> omit entirely; oceans/continents/cardinal
      directions + region names ("the Pacific", "Asia") -> banned entirely; attorney general ->
      "top government lawyer"; republic/kingdom/empire for the parent -> "nation"; demonyms ->
      banned; named institutions -> generic function ("the national court system", "the elected
      local legislature") without flourish.
   c. blindSummary, blindTangential, blindLocalsOnly, blindOutOfScope ALL derive from their
      visible field by (a)+(b). blindSourceSummaries: same mapping, no name leakage.
   d. Mechanical gate: python3 tools/check_blind.py --who <who> must pass before any blind field
      is merged. Banned words + enrichment-diff are errors, not warnings.
7e. EXTENDED BLIND VOCABULARY (ruling 2026-09-29):
   - bare "state" as unit placeholder is BANNED -> always the literal "state/province"
   - blind mirrors (including blindSourceSummaries) must carry no SEARCHABLE FINGERPRINTS even
     where visible text does: exact populations ("~57,000 residents"), mottos, founding stories of
     named-by-function organisations ("formed 2010 by merging two associations"), personal
     testimonies at hearings, unique slogans. Generalise: "tens of thousands of residents",
     "a long-standing local third-gender society", "local witnesses opposed the bill on cultural
     grounds". Dates of LAWS/rulings stay (they are the facts raters must weigh); identity-
     granular colour goes.
7f. STATE-WORD RULING (2026-10-04): the literal "state/province" is the division idiom and is
    always allowed. "State" in governmental-adjective compounds — "state policy", "state-backed",
    "state-run", "state security", "state religious (authorities)", "the state keeps no
    statistics" — describes the national government generically, cannot fingerprint the division,
    and is ALLOWED in blind text. Parent-referent descriptors ("encompassing state", "administering
    state", "metropolitan state", "unitary state", "partner state", "neighbouring state", "federal
    state", "sovereign state") refer to the deliberately-unblinded parent or a generic descriptor
    and are ALLOWED. Bare "state"/"state's" that begs "which state?" — "this state", "a
    state", "that state" as unit placeholder — is still BANNED and must use "state/province".
    check_blind.py implements this via a token-level _state_leak() on each field including
    blindSourceSummaries.

8. PROPORTION AND THIN-DATA (2026-10-03 — mandatory in ALL summaries and four-field text):
   a. Frequency × severity: universal-exposure measures (bathroom/facility bills,
      document-marker mismatches at checkpoints, mandatory disclosure, registration of
      visibly trans people) reach EVERY trans visitor and must be stated as the
      continuous exposure they are — never diluted by "few arrests". Murder/torture are
      the severest outcomes but their weight tracks frequency: figures at or near the
      region's general murder rate (single/low-double-digit per 100k/yr) are an
      "elevated version of a normal non-trans-specific risk", not a campaign — say so.
      Organised targeting (moral/religious police, militia or gang sweeps, state
      campaigns making visibly trans people primary targets) is a different tier and
      dominates. Always calibrate against the region's general-violence baseline.
   b. Thin data: never write summaries that imply unknown = safe or unknown = midpoint.
      State what is unknown AND extrapolate from the structural signals that exist
      (criminalisation, LGR absence, governance character, analogues). A thin dossier in
      a criminalising, no-LGR, no-recourse state must read as dangerous unless evidence
      says otherwise.

9. FRESHNESS-LANE OUTPUT IS METADATA, NOT PROSE (2026-10-05 ruling; the fault
   that shipped "SUPERSEDED by freshness (rev 2026-09-27)" into visitor-facing
   claims). The `fact` field of a freshness result is a SUBSTANTIVE LEGAL
   FINDING (what changed, when, with what penalty/status) — never a statement
   about the audit itself. Status values (confirmed/superseded/changed) go in
   the `status` field only; run dates and revision stamps NEVER appear in
   prose. Nothing about the pipeline (freshness, revision numbers, fetch
   conditions, pruning, the audit) may be written into any field that reaches
   the map. If the rework input carries such strings, rewrite the finding and
   drop the jargon.

10. NATIONAL REPRESENTATIVENESS (countries-tier summaries). A single
    sub-national unit (state, province, city) in a country summary is ONE
    data point illustrating a pattern — never the headline. Lead with the
    pattern (how many states, which direction, what enforcement), then at most
    one or two named examples. A country summary that reads like the profile
    of one state is a structural failure even if every sentence is sourced.
    (Fault fixed 2026-10-05: the US summary opened its state-law paragraph
    with Kansas, which was merely 2 of 17 sources.)

11. PROSE TRANSFORMS ARE LLM-LANE WORK (2026-10-07 ruling, after a greedy
    regex substitution corrupted "state" the verb, "state" the polity and
    country self-references across 160+ records). Deterministic string ops on
    natural-language dossier text are FORBIDDEN except:
    a. DETECTION — finding candidate records or violations (patterns may flag,
       never edit); and
    b. ENFORCED REDACTION — dropping banned content (population figures,
       mottos, agency names) with a FIXED replacement token, never rephrasing.
    Every meaning-bearing rewrite (vocabulary substitution, de-anonymisation,
    grammar repair, de-jargoning) goes through the model with the rules as
    instructions, and passes the mechanical gates (digits preserved, length
    bounded, blind gate) before it can apply.

12. BLIND VOCABULARY BY RECORD KIND. An independent country's blind text
    self-refers as "the country"; "state/province" is ONLY for sub-national
    units and dependent territories. (The 2026-10-07 bug had 160 countries
    self-describe as sub-units, which made the rater read two dossiers as
    sharing a parent and smear parent regimes across pairs.)
