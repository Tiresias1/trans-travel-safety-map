# ADM1 Research Hand-Off Prompt (lightweight model — autonomous batch)

**How this is used:** the operator pastes everything below the line into the research
model ONCE. The model works down the ranked country list autonomously — one output file
per country — until the stop rule fires. No per-country manual setup.

Requirements for the model: a shell (to run `python3 tools/adm1_list.py` from the repo
root `/home/meme/kóði/kort`), web search, and page fetching.

---

## Mission

You are researching **first-level administrative divisions** (states, provinces, regions,
republics) for a map that scores the risk to a **transgender visitor** — someone who is, or
is discovered to be, trans — in each jurisdiction. National-level scores already exist for
every country. Your job is to find **sub-national variation**: ways specific regions differ
from their country as a whole.

You do **research only**. Do not assign scores or numbers — a separate process scores from
your dossiers. Collect evidence, classify how much usable evidence exists, write it down,
move to the next country.

## Workflow (repeat per country, in the ranked order at the end)

1. Run `python3 tools/adm1_list.py <ISO3> --format md` — this prints the unit names and
   IDs to research, plus any EXCLUDED units (territories scored separately; never research
   those).
2. Research the country's sub-national variation: roughly **6–14 web searches**, rotated
   across angles (below). Fetch and read the promising sources.
3. Write `research/admin1/<ISO3>.md` in the exact template below.
4. Classify the country RICH / MEDIUM / POOR and apply the stop rule.
5. Continue to the next country.

### Search angles (adapt wording per country; don't repeat one phrasing)

- `<country> state OR provincial law transgender bathroom OR expression ban`
- `<country> regional differences LGBT police enforcement`
- `<country> trans violence OR murder monitoring by state OR region`
- `<major cities> transgender safety compared`
- `<country> pride banned OR attacked OR protected city`
- `<country> religious OR customary courts gender morality region` (for exception regions)
- `<country> transgender tourist OR visitor detained`
- Other governments' travel advisories for `<country>` — they often name specific regions.

Prefer sources giving **counts, dates, and region names**: NGO annual reports,
trans-murder monitoring (TGEU etc.), court records, foreign travel advisories, reputable
press. Go deep only on regions that show a signal.

## What counts as useful evidence

1. **Region-specific law or regulation** touching gender expression or trans presence in
   public life: bathroom/facility restrictions, drag/expression bans, local morality
   ordinances, a different legal system (religious/customary courts over morals),
   regional ID or policing practices. Also protective ones: regional non-discrimination
   ordinances covering gender identity, sanctuary/shield policies, official guidance
   protecting trans people in public facilities.
2. **Enforcement that varies by region**: documented police raids, arrest patterns,
   extortion of trans people by local police — or documented non-enforcement/protection.
3. **Documented patterns of violence or harassment** against trans people, with counts
   and dates and whether cases were prosecuted. Patterns only (see the rule below).
4. **Urban vs regional divide**: whether major cities have visible, organised communities
   and safer public life than a particular conservative region. Name them.
5. **Local official climate**: regional officials' statements, pride events
   permitted/banned/attacked, regional anti-trans campaigns, or official support.
6. **Traveler-specific incidents**: visitors detained/harassed/harmed; particular border
   posts or airports behaving differently; advisories naming regions.

## The single-incident rule (the main failure mode — obey it strictly)

Most crime never makes the news; one report is very weak evidence about how common
something is. **Never treat a lone incident as a finding about a region.** An incident
counts only if:

- it is part of a **pattern** (≥2 independent reports, or published counts/rates); or
- the **state is implicated** (police custody, officials as perpetrators, state-linked
  actors); or
- the **response was damning** (no investigation, victim prosecuted, documented impunity); or
- the region is **very small**, so one case carries real weight.

A **good** institutional response is positive evidence: convictions of attackers, public
outcry, official condemnation, reform after an incident. Record it as such.

Record patterns with counts, dates, and source URLs — not the most shocking single story.

## What to ignore

- Resident-only matters: domestic legal-gender-recognition procedures, transition
  healthcare availability, employment/adoption law, marriage equality. A visitor uses
  their home passport and never applies to local systems. Record these only if they
  reveal official or public hostility a visitor would encounter.
- General crime, terrorism, disease, natural hazards, instability — unless they
  specifically amplify trans-related risk.
- Anything you cannot source with a URL.

## Mandatory exceptions clause

Even where data is thin, you **must** check for and report every region operating under a
**different legal system** than the national one — religious or customary courts with
jurisdiction over morality/personal status, autonomous regions with own criminal law,
specially administered territories. Known examples to verify and document: **Chechnya
(RUS), Aceh (IDN), northern sharia states (NGA — e.g. Kano, Kaduna, Sokoto, Zamfara,
Jigawa, Katsina, Bauchi, Borno, Yobe, Kebbi, Niger, Adamawa, Gombe, Taraba, Katsina,
Jigawa), sharia-court states (MYS — e.g. Kelantan, Terengganu, Kedah, Pahang, Perak),
Zanzibar (TZA), Iraqi Kurdistan (IRQ), Xinjiang and Tibet (CHN)**. These are the
highest-stakes regional distinctions on the map. If you find nothing beyond the
legal-framework fact itself, say exactly that — the framework fact alone is the finding.

## Output template — `research/admin1/<ISO3>.md`

```markdown
# <ISO3> — <country name> · ADM1 research
Researched: <YYYY-MM-DD> · Units in boundary data: <N usable, M excluded>

## Richness classification
<RICH | MEDIUM | POOR> — <1–2 sentences: how many regions had real sub-national
evidence, and of what kind>

## Different-legal-system regions
<each with its legal basis and source URL; or "none found">

## Regions with findings

### <Region name> (`<shapeID>`)
Direction: <worse | better | mixed> than national — <one-line reason>
- <evidence: fact + date/count where available> — <source URL>
- <...>

## Regions with no sub-national signal
<comma-separated names; no shapeIDs needed>

## Urban / rural and general notes
<how much variation is city-vs-countryside rather than region-vs-region; anything
an assessor should know that isn't region-specific>

## Sources consulted
- <URL> — <what it was useful for>
```

Use exact region names and shapeIDs from `adm1_list.py`. Include a region under
"Regions with findings" only with at least one sourced bullet. "No sub-national signal
found" is a complete and useful result — do not manufacture findings.

**Large unit counts** (examples: RUS 83, TUR 81, NGA 37, IND 36, IDN 34, MEX/COL 32–33):
do not attempt every unit, as no data will exist for most. Where real
variation is nation-level or a handful of regions (RUS: Chechnya plus a few cities for
example; TUR: Istanbul vs the southeast; GBR: its 4 constituent
nations), report at that level and list everything else under "no sub-national signal".
Five regions with real evidence beats eighty thin guesses.

## Stop rule

After each country, classify honestly. If **three consecutive countries** come back
**POOR** with no different-legal-system regions worth reporting, stop: write
`research/admin1/_STOP.md` naming where you stopped and which ranked countries remain.
Continuing past the point of data exhaustion invents regional distinctions from noise —
worse than leaving regions at their national score. Just do not forget the Mandatory
Exceptions Clause.

## Ranked country order (work top-down; unit counts are post-exclusion)

1. **USA** (51) — extensive state-level legislation and enforcement data
2. **MEX** (32) — state-level variation documented
3. **CAN** (13) — provincial jurisdiction over facilities/education
4. **GBR** (4) — Scotland/England/Wales/NI divergence
5. **AUS** (9) — state-level legal differences
6. **BRA** (27) — state-level violence and public-security data
7. **IND** (36) — state enforcement and community variation
8. **DEU** (16) — Länder implementation differences
9. **ESP** (19) — autonomous-community variation
10. **COL** (33) — department-level violence data
11. **ARG** (23) — provincial variation
12. **ITA** (5) — regional political-climate variation
13. **POL** (16) — documented "LGBT-free zone" declarations
14. **NGA** (37) — **northern sharia states: mandatory exception**
15. **IDN** (34) — **Aceh: mandatory exception**; city-level raid records
16. **MYS** (16) — **state sharia courts: mandatory exception**
17. **TUR** (81) — Istanbul vs southeast
18. **RUS** (83) — **Chechnya: mandatory exception**; otherwise federally homogenous
19. **ZAF** (9) — province-level enforcement variation
20. **FRA** (13) — limited regional variation
21. **PHL** (17) — city-level ordinances (some protective)
22. **PER** (26) — regional variation
23. **CHL** (16) — regional variation
24. **KOR** (17) — limited

Beyond these: assume POOR unless evidence says otherwise; let the stop rule decide.
Countries not on this list are handled by a different route (model-assisted estimation)
and are not your concern.
