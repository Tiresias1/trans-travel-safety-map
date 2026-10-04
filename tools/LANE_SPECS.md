# Lane spec corrections (2026-09-29) — apply to ALL audit/rework/freshness launches
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
     caveats. Each field: 1-3 <p> (outOfScopeNotes may be plain sentences), absolute terms, sourced.
7. BLIND MIRRORS ARE DERIVATIONS, NOT REWRITES. Rules:
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
