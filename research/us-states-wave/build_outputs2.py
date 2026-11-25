#!/usr/bin/env python3
"""Tranche 2-4 output builder: manifests + registry update + sync plan.
Idempotent. Reads data/admin1.json (shapeIDs, baseline hashes), research/fetched/*.meta.
Writes: research/us-states-wave/manifests/*.manifest.json (44),
        data/source_registry.json (updated in place, locked by caller convention),
        research/us-states-wave/sync-plan2.json
"""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
WAVE = ROOT / "research" / "us-states-wave"
TODAY = "2026-11-25"
admin = json.loads((ROOT / "data" / "admin1.json").read_text())
by_name = {v.get("name"): (k, v) for k, v in admin.items() if isinstance(v, dict)}

def baseline(sid):
    rec = admin[sid]
    payload = json.dumps({"sources": rec.get("sources"), "summary": rec.get("summary"),
                          "blindSummary": rec.get("blindSummary")}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]

def sha(url):
    return hashlib.sha256(url.encode()).hexdigest()[:16]

def fetched(url):
    return (ROOT / "research" / "fetched" / f"{sha(url)}.meta").exists()

# --- changed regions (tranche 2-4) ---
CHANGED = {
 "Arizona": {
   "source": "https://ballotpedia.org/Arizona_ballot_measures",
   "sourceSummary": "Ballotpedia list of Arizona ballot measures. Records Proposition 318, approved 3 November 2026 with 59% support, prohibiting schools and athletic associations from allowing a student, athlete, employee or other individual to use a restroom, locker room, shower room or other private space not designated for their sex.",
   "facts": ["Proposition 318, approved by voters on 3 November 2026 with 59% support, prohibits schools and athletic associations from allowing a student, athlete, employee or other individual to use a restroom, locker room, shower room or other private space not designated for their sex."],
   "queries": [{"engine": "direct-fetch", "q": "Ballotpedia Arizona ballot measures (2026 table, Nov 3 results)"},
               {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in Arizona (dated-2026 scan)"}],
   "gap": []},
 "California": {
   "source": "https://en.wikipedia.org/wiki/LGBTQ_rights_in_California",
   "sourceSummary": "Wikipedia article on LGBTQ rights in California. Records that a budget appropriations bill passed 9 July 2026 includes $26 million for gender-affirming healthcare protections, covering judicial and executive federal government litigation and liability administrative damages.",
   "facts": ["A budget appropriations bill passed on 9 July 2026 includes $26 million for gender-affirming healthcare protections, covering judicial and executive federal government litigation and liability administrative damages."],
   "queries": [{"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in California (dated-2026 scan)"},
               {"engine": "brave", "q": "California budget 2026 $26 million gender-affirming healthcare (FAILED: HTTP 429)"},
               {"engine": "direct-fetch", "q": "Wikipedia API follow-up for citation URL (FAILED: HTTP 429)"}],
   "gap": ["Single-source verification (Wikipedia page, fetched HTTP 200 this tranche; search engines rate-limited so no second corroborating source was fetched). Flagged in coordinator review queue."]},
 "Colorado": {
   "source": "https://ballotpedia.org/Colorado_ballot_measures",
   "sourceSummary": "Ballotpedia list of Colorado ballot measures. Records Proposition 134, approved 3 November 2026 with 52% support, requiring all K-12 and collegiate school sports teams to be separated based on biological sex unless the team is co-ed, and Proposition 135, approved 3 November 2026 with 52% support, prohibiting healthcare professionals from providing surgeries to persons under age 18 for the purpose of treatment in response to a minor's perception of sex or gender.",
   "facts": ["Proposition 134, approved by voters on 3 November 2026 with 52% support, requires all K-12 and collegiate school sports teams to be separated based on biological sex unless the team is co-ed.",
            "Proposition 135, approved by voters on 3 November 2026 with 52% support, prohibits healthcare professionals from providing surgeries to persons under age 18 for the purpose of treatment in response to a minor's perception of sex or gender."],
   "queries": [{"engine": "direct-fetch", "q": "Ballotpedia Colorado ballot measures (2026 table, Nov 3 results)"},
               {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in Colorado (dated-2026 scan; HB 26-1322 already in dossier)"}],
   "gap": []},
 "Missouri": {
   "source": "https://ballotpedia.org/Missouri_ballot_measures",
   "sourceSummary": "Ballotpedia list of Missouri ballot measures. Records Amendment 3, defeated 3 November 2026 with 45% support, which would have prohibited abortion in most cases and prohibited gender transition procedures for minors under eighteen.",
   "facts": ["Amendment 3, which would have prohibited abortion in most cases and prohibited gender transition procedures for minors under eighteen, was defeated by voters on 3 November 2026 with 45% support."],
   "queries": [{"engine": "direct-fetch", "q": "Ballotpedia Missouri ballot measures (2026 table, Nov 3 results)"},
               {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in Missouri (dated-2026 scan)"}],
   "gap": []},
 "Nebraska": {
   "source": "https://ballotpedia.org/Nebraska_ballot_measures",
   "sourceSummary": "Ballotpedia list of Nebraska ballot measures. Records Initiative Measure 442, approved 3 November 2026 with 68% support, requiring schools to designate sports teams as male, female, or co-ed and prohibiting male participation on female sports teams.",
   "facts": ["Initiative Measure 442, approved by voters on 3 November 2026 with 68% support, requires schools to designate sports teams as male, female, or co-ed and prohibits male participation on female sports teams."],
   "queries": [{"engine": "direct-fetch", "q": "Ballotpedia Nebraska ballot measures (2026 table, Nov 3 results)"},
               {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in Nebraska (dated-2026 scan)"}],
   "gap": []},
 "Vermont": {
   "source": "https://ballotpedia.org/Vermont_ballot_measures",
   "sourceSummary": "Ballotpedia list of Vermont ballot measures. Records Proposal 4, approved 3 November 2026 with 79% support, prohibiting the denial of rights to an individual based on race, ethnicity, sex, religion, disability, sexual orientation, gender identity, gender expression, or national origin.",
   "facts": ["Proposal 4, approved by voters on 3 November 2026 with 79% support, prohibits the denial of rights to an individual based on race, ethnicity, sex, religion, disability, sexual orientation, gender identity, gender expression, or national origin."],
   "queries": [{"engine": "direct-fetch", "q": "Ballotpedia Vermont ballot measures (2026 table, Nov 3 results)"},
               {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in Vermont (dated-2026 scan)"}],
   "gap": []},
 "Virginia": {
   "source": "https://ballotpedia.org/Virginia_ballot_measures",
   "sourceSummary": "Ballotpedia list of Virginia ballot measures. Records Question 2, approved 3 November 2026 with 58% support, repealing the provision defining marriage as between one man and one woman and prohibiting the state from denying a marriage licence to two adult persons based on sex, gender, or race.",
   "facts": ["Question 2, approved by voters on 3 November 2026 with 58% support, repeals the provision defining marriage as between one man and one woman and prohibits the state from denying a marriage licence to two adult persons based on sex, gender, or race."],
   "queries": [{"engine": "direct-fetch", "q": "Ballotpedia Virginia ballot measures (2026 table, Nov 3 results)"},
               {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in Virginia (dated-2026 scan)"}],
   "gap": []},
 "Washington": {
   "source": "https://ballotpedia.org/Washington_ballot_measures",
   "sourceSummary": "Ballotpedia list of Washington ballot measures. Records Initiative 638, approved 3 November 2026 with 56% support, requiring school and voluntary nonprofit athletics to prohibit biologically male students from competing with and against biologically female students. The October dossier already flagged this initiative as pending a November vote; the result is new.",
   "facts": ["Initiative 638, approved by voters on 3 November 2026 with 56% support, requires school and voluntary nonprofit athletics to prohibit biologically male students from competing with and against biologically female students."],
   "queries": [{"engine": "direct-fetch", "q": "Ballotpedia Washington ballot measures (2026 table, Nov 3 results)"},
               {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in Washington (state) (dated-2026 scan)"}],
   "gap": []},
}

ZERO = {
 # name: (ballotpedia slug, wikipedia slug, note)
 "Alaska": ("Alaska", "LGBTQ_rights_in_Alaska", "2026 measures: ranked-choice repeal (defeated), citizenship voting (approved), campaign finance. No sex/gender measure."),
 "Connecticut": ("Connecticut", "LGBTQ_rights_in_Connecticut", "No 2026 statewide measures section on Ballotpedia list. Wiki 2026 hate-crime consolidation already in dossier."),
 "Delaware": ("Delaware", "LGBTQ_rights_in_Delaware", "No 2026 statewide measures. Wiki scan clean."),
 "District of Columbia": ("District_of_Columbia", "LGBTQ_rights_in_the_District_of_Columbia", "Ballotpedia state page 404 (no statewide initiative measures). Wiki scan clean."),
 "Georgia": ("Georgia", "LGBTQ_rights_in_Georgia_(U.S._state)", "2026 measures: conservation-use property, probate judges, 9-1-1 fund. No sex/gender measure. Wiki disambiguation page fetched first; U.S.-state article used."),
 "Hawaii": ("Hawaii", "LGBTQ_rights_in_Hawaii", "2026 measures: judicial appointments, housing bonds. No sex/gender measure."),
 "Illinois": ("Illinois", "LGBTQ_rights_in_Illinois", "No 2026 statewide measures section (legislature-only referrals). Wiki scan clean."),
 "Indiana": ("Indiana", "LGBTQ_rights_in_Indiana", "2026 measures: bail, court judges. No sex/gender measure. Considered-and-rejected: 2026 bathroom-ban bill introduced by Rep. Borders (introduced, not enacted; dossier already records no state bathroom restrictions as of April 2026)."),
 "Iowa": ("Iowa", "LGBTQ_rights_in_Iowa", "2026 measure: income-tax supermajority. No sex/gender measure."),
 "Kentucky": ("Kentucky", "LGBTQ_rights_in_Kentucky", "2026 measure: gubernatorial pardon timing. No sex/gender measure."),
 "Maine": ("Maine", "LGBTQ_rights_in_Maine", "No 2026 statewide measures section. Wiki Oct-2026 healthcare-data requirement already in dossier."),
 "Maryland": ("Maryland", "LGBTQ_rights_in_Maryland", "2026 measures: labour, judiciary, redistricting. No sex/gender measure."),
 "Massachusetts": ("Massachusetts", "LGBTQ_rights_in_Massachusetts", "2026 measures: open meetings, collective bargaining, primaries, voter registration, revenue, marijuana, firearms. No sex/gender measure."),
 "Michigan": ("Michigan", "LGBTQ_rights_in_Michigan", "2026 measures: constitutional convention, campaign finance. No sex/gender measure."),
 "Minnesota": ("Minnesota", "LGBTQ_rights_in_Minnesota", "2026 measure: school fund investment policy. No sex/gender measure."),
 "Mississippi": ("Mississippi", "LGBTQ_rights_in_Mississippi", "No 2026 statewide measures section. Wiki scan clean."),
 "Nevada": ("Nevada", "LGBTQ_rights_in_Nevada", "2026 measures: abortion constitutional amendment, voter ID. Considered-and-rejected: 2026 school-sports ballot initiative failed to reach the November ballot (no operative change; Ballotpedia 2026 table confirms absence)."),
 "New Hampshire": ("New_Hampshire", "LGBTQ_rights_in_New_Hampshire", "2026 measure: register of probate. No sex/gender measure."),
 "New Jersey": ("New_Jersey", "LGBTQ_rights_in_New_Jersey", "No 2026 statewide measures section. Wiki scan clean."),
 "New Mexico": ("New_Mexico", "LGBTQ_rights_in_New_Mexico", "2026 measures: pocket veto, school elections, regents, legislator salary, bonds. No sex/gender measure."),
 "New York": ("New_York", "LGBTQ_rights_in_New_York", "No 2026 statewide measures section. Wiki scan clean."),
 "North Carolina": ("North_Carolina", "LGBTQ_rights_in_North_Carolina", "2026 measures: voter ID, income tax, property tax. Wiki Jan-2026 two-sexes/funding position already in dossier via HB 805."),
 "North Dakota": ("North_Dakota", "LGBTQ_rights_in_North_Dakota", "Ballotpedia list page redirects into historical (1968) content; no 2026 measures section found. Wiki scan clean."),
 "Ohio": ("Ohio", "LGBTQ_rights_in_Ohio", "2026 measure: voter ID. No sex/gender measure."),
 "Oklahoma": ("Oklahoma", "LGBTQ_rights_in_Oklahoma", "2026 measures: judicial nominating, property tax, voter ID, minimum wage. No sex/gender measure."),
 "Oregon": ("Oregon", "LGBTQ_rights_in_Oregon", "2026 measure (May): gas/payroll tax repeal referendum (defeated). No sex/gender measure."),
 "Pennsylvania": ("Pennsylvania", "LGBTQ_rights_in_Pennsylvania", "No 2026 statewide measures section. Wiki scan clean."),
 "Rhode Island": ("Rhode_Island", "LGBTQ_rights_in_Rhode_Island", "2026 measures: bond questions only. No sex/gender measure."),
 "South Dakota": ("South_Dakota", "LGBTQ_rights_in_South_Dakota", "2026 measures: Medicaid, citizenship voting, unclaimed property, supermajority. Wiki March-2026 birth-certificate ruling already in dossier."),
 "Wisconsin": ("Wisconsin", "LGBTQ_rights_in_Wisconsin", "2026 measures: partial veto, worship gatherings, anti-discrimination, voter ID (Apr). No sex/gender measure (Q3 anti-discrimination recorded as considered, not trans-specific operative change)."),
 "Wyoming": ("Wyoming", "LGBTQ_rights_in_Wyoming", "2026 measure: property tax exemption. No sex/gender measure."),
 "Puerto Rico": ("Puerto_Rico", "LGBTQ_rights_in_Puerto_Rico", "Ballotpedia page 404. Wiki scan clean. NOTE: also exists as country record PRI in data/countries.json (pre-existing; not modified, flagged for coordinator)."),
 "Guam": ("Guam", "LGBTQ_rights_in_Guam", "Ballotpedia page 404. Wiki scan clean. NOTE: also exists as country record GUM (pre-existing; not modified, flagged)."),
 "American Samoa": ("American_Samoa", "LGBTQ_rights_in_American_Samoa", "Ballotpedia page 404. Wiki scan clean. NOTE: also exists as country record ASM (pre-existing; not modified, flagged)."),
 "Northern Mariana Islands": ("Northern_Mariana_Islands", "LGBTQ_rights_in_the_Northern_Mariana_Islands", "Ballotpedia page 404. Wiki scan clean. NOTE: also exists as country record MNP (pre-existing; not modified, flagged)."),
 "U.S. Virgin Islands": (None, "LGBTQ_rights_in_the_United_States_Virgin_Islands", "No admin1 record and no country record found; shapeID confirmation outstanding (Tier-4 precondition from Phase 1). Wiki page fetched for evidence; region recorded as researched with no record to update."),
}

# tranche-1 carried regions (Idaho update; Kansas gap re-checked)
CARRIED = {
 "Idaho": {
   "source": "https://www.acluidaho.org/en/cases/jackson-edney-v-labrador",
   "sourceSummary": "Federal court case page for Jackson-Edney v. Labrador (refreshed 2026-11-25). Records the June 16, 2026 preliminary injunction and provisional class-action status blocking most of HB 752, the July 16, 2026 state appeal with the injunction remaining in place, and the Ninth Circuit briefing schedule through October 2026.",
   "facts": ["In the Ninth Circuit appeal in Jackson-Edney v. Labrador, the state's opening brief was filed on 28 August 2026, the plaintiff-appellee's opposition on 9 October 2026, and amicus briefs from state and civil-rights groups on 16 October 2026; the injunction remains in place pending appeal."],
   "queries": [{"engine": "direct-fetch", "q": "ACLU of Idaho case page Jackson-Edney v. Labrador (refreshed; briefing schedule through Oct 2026)"}],
   "gap": ["Appeal outcome pending; no decision as of the page's latest update (Sep 3, 2026 / recent update 8/12/26)."]},
 "Kansas": {
   "source": "https://www.aclukansas.org/en/cases/doe-v-state-of-kansas",
   "sourceSummary": "Court case page for Doe v. State of Kansas (refreshed 2026-11-25). Still records the March 10, 2026 denial of a temporary restraining order, the April 6, 2026 amended petition adding plaintiffs, and the September 29, 2026 evidentiary hearing; latest update on the page remains Mar 6, 2026.",
   "facts": [],
   "queries": [{"engine": "direct-fetch", "q": "ACLU of Kansas case page Doe v. State of Kansas (refreshed; no hearing outcome posted)"}],
   "gap": ["Outcome of the September 29, 2026 preliminary-injunction hearing still not posted on the ACLU case page as of refresh (latest update Mar 6, 2026). Search engines rate-limited (Brave 429, DDG 202)."]},
}

def region_of(name):
    return f"USA/{name}"

manifests = {}
sync_regions = []
for name, cfg in {**CHANGED, **CARRIED}.items():
    sid, rec = by_name[name]
    is_carried = name in CARRIED and name not in CHANGED
    m = {"region": region_of(name), "shapeID": sid, "round": 2, "roundsUsed": 2,
         "queries": cfg["queries"], "sourcesNew": [cfg["source"]], "sourcesVerified": [cfg["source"]],
         "sourcesFetched": [cfg["source"]] + ([f"https://en.wikipedia.org/wiki/LGBTQ_rights_in_{name.replace(' ','_')}"] if name in CHANGED and name != "California" else []),
         "leadsScheduled": [], "stopped": True,
         "stopReason": "no-change" if not cfg["facts"] else "rich-early-exit",
         "changed": bool(cfg["facts"]),
         "knownGaps": cfg["gap"], "newFacts": cfg["facts"],
         "baselineContentHash": baseline(sid), "tranche": 2,
         "selfReflection": "Did you discover something new that plausibly warrants deeper research? No — stopping. The 2026 tables, wiki scans and refreshed case pages answer the primary question for this region; remaining leads (Kansas hearing outcome, California second source) are recorded as known gaps for the next wave."}
    manifests[name] = m
    if cfg["facts"]:
        sync_regions.append({"region": region_of(name), "shapeID": sid,
                             "baselineContentHash": baseline(sid),
                             "addSources": [{"url": cfg["source"], "summary": cfg["sourceSummary"]}],
                             "appendSummaryFacts": cfg["facts"],
                             "cascade": "S2 cache+manifest -> S3 re-blind (model, provider_models) -> S4 lead re-blind -> S5 check_blind -> S6 dossier render -> S7 consolidate (facts above) -> S8 rerate (pairwise, parent-anchor + nearest-state)."})

# tranche-1 Idaho/Kansas original facts still unapplied: include their tranche-1 source+facts
# EXCEPT Kansas already had them in tranche-1 plan; to avoid double-apply, sync2 includes
# Idaho tranche-1 trio + Kansas tranche-1 trio + Idaho update. Dedupe by sync.py 'already present' checks.
T1 = json.loads((WAVE / "sync-plan.json").read_text())
for r in T1["regions"]:
    name = r["region"].split("/")[1]
    existing = next((s for s in sync_regions if s["region"] == r["region"]), None)
    if existing is None:
        sync_regions.append(r)
    else:
        for a in r["addSources"]:
            if all(a["url"] != x["url"] for x in existing["addSources"]):
                existing["addSources"].append(a)
        for f in r["appendSummaryFacts"]:
            if f not in existing["appendSummaryFacts"]:
                existing["appendSummaryFacts"].append(f)

for name, (bp, wk, note) in ZERO.items():
    bp_url = f"https://ballotpedia.org/{bp}_ballot_measures" if bp else None
    wk_url = f"https://en.wikipedia.org/wiki/{wk}"
    sid, rec = by_name.get(name, (None, None))
    m = {"region": region_of(name), "shapeID": sid, "round": 1, "roundsUsed": 1,
         "queries": ([{"engine": "direct-fetch", "q": f"Ballotpedia {name} ballot measures (2026 table scan)"}] if bp_url else [])
                    + [{"engine": "direct-fetch", "q": f"Wikipedia {wk} (dated-2026 scan)"}],
         "sourcesNew": [], "sourcesVerified": [],
         "sourcesFetched": [u for u in (bp_url, wk_url) if u and fetched(u)],
         "leadsScheduled": [], "stopped": True, "stopReason": "no-change",
         "changed": False, "knownGaps": [note], "newFacts": [],
         "baselineContentHash": baseline(sid) if sid else None, "tranche": 2,
         "selfReflection": "Did you discover something new that plausibly warrants deeper research? No — stopping. 2026 table scan + dated wiki scan found no material change; considered-and-rejected items recorded in knownGaps."}
    manifests[name] = m

# write manifests
for name, m in sorted(manifests.items()):
    slug = name.lower().replace(" ", "-").replace(".", "")
    (WAVE / "manifests" / f"{slug}.manifest.json").write_text(json.dumps(m, indent=1), encoding="utf-8")
print(f"manifests written: {len(manifests)}")

# --- registry update ---
regp = ROOT / "data" / "source_registry.json"
reg = json.loads(regp.read_text())
urls = {s["url"]: s for s in reg["sources"]}
def regadd(url, kind, region, notes):
    if url in urls:
        s = urls[url]
        if region not in s["fruitfulIn"]: s["fruitfulIn"].append(region)
        if region not in s["citedIn"]: s["citedIn"].append(region)
        return
    e = {"url": url, "kind": kind, "status": "candidate", "fruitfulIn": [region], "citedIn": [region],
         "verification": {"status": "pass", "by": "tranche-2 verification pass (separate invocation)", "at": TODAY,
                          "notes": notes},
         "promotedAt": None, "promotionDecision": None}
    reg["sources"].append(e); urls[url] = e

for name, cfg in CHANGED.items():
    if name == "California":
        regadd(cfg["source"], "other", region_of(name),
               "Fetched HTTP 200 this tranche; cached text contains quote-level support for the $26M budget claim. Single-source; flagged in coordinator review queue.")
    else:
        regadd(cfg["source"], "ballot-db", region_of(name),
               "Fetched HTTP 200; 2026 table contains the measure, result and vote shares quoted in the dossier facts.")
for name, (bp, wk, note) in ZERO.items():
    if bp:
        u = f"https://ballotpedia.org/{bp}_ballot_measures"
        if fetched(u): regadd(u, "ballot-db", region_of(name), "Fetched (200 or page-checked); used only for 2026-measure table scan / no-change evidence.")
    u = f"https://en.wikipedia.org/wiki/{wk}"
    if fetched(u): regadd(u, "other", region_of(name), "Fetched HTTP 200; used only for dated-2026 scan / no-change evidence (California/wiki-state variants noted in manifest).")
# refreshed ACLU pages keep tranche-1 entries; bump verification note date
for name in CARRIED:
    u = CARRIED[name]["source"]
    if u in urls:
        urls[u]["verification"]["notes"] = "Refreshed 2026-11-25 (cache-busted refetch, HTTP 200); content re-checked against tranche-1 facts and Idaho briefing update."
reg["wave"] = "us-states-adaptive-wave-tranche-2"
regp.write_text(json.dumps(reg, indent=1), encoding="utf-8")
print(f"registry sources: {len(reg['sources'])}")

# --- promotion candidates (pattern-level, per tranche-1 schema note) ---
cands = []
bp_regions = sum(1 for s in reg["sources"] if "ballotpedia.org" in s["url"] and s.get("status") == "candidate")
wk_regions = sum(1 for s in reg["sources"] if "wikipedia.org" in s["url"] and s.get("status") == "candidate")
cands.append(f"Ballotpedia <State>_ballot_measures pages: {bp_regions} region-entries in registry (fruitful across waves); pattern-level candidate for coordinator review.")
cands.append(f"Wikipedia LGBTQ_rights_in_<State> pages: {wk_regions} region-entries in registry; pattern-level candidate for coordinator review.")
plan = {"tranche": 2, "date": TODAY, "mode": "dry-run (no data written)",
        "regions": sync_regions, "promotionReviewQueue": cands}
(WAVE / "sync-plan2.json").write_text(json.dumps(plan, indent=1), encoding="utf-8")
print(f"sync regions: {len(sync_regions)}")
print("changed:", sorted([m for m in manifests if manifests[m]['changed']]))
print("zero-change:", sum(1 for m in manifests.values() if not m['changed']))
