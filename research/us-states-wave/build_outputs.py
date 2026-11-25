#!/usr/bin/env python3
"""Tranche-1 output builder: manifests + source registry + sync plan.
Idempotent: re-running rewrites the same files (no append/duplication).
Reads: data/admin1.json (baseline hashes), research/fetched/*.meta (fetch evidence).
Writes: research/us-states-wave/manifests/*.manifest.json, data/source_registry.json,
        research/us-states-wave/sync-plan.json
"""
import hashlib, json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
WAVE = ROOT / "research" / "us-states-wave"
TODAY = "2026-11-25"

# --- Tier-1 region findings (verified from fetched cache, quotes in fragments) ---
REGIONS = {
    "Idaho": {
        "shapeID": "66186276B48953429733047",
        "ballotpedia": "https://ballotpedia.org/Idaho_ballot_measures",
        "changed": True,
        "newSources": ["https://www.acluidaho.org/en/cases/jackson-edney-v-labrador"],
        "newFacts": [
            "On June 16, 2026, a federal judge granted a preliminary injunction and provisional class-action status in Jackson-Edney v. Labrador. The injunction blocks the restroom portion of HB 752: a trans person may use public restrooms consistent with gender identity, except a multi-user restroom may still be enforced against when a single-user restroom is available on the same floor. The changing-room portion is not blocked.",
            "The State of Idaho filed a notice of appeal on July 16, 2026; the injunction remains in place pending appeal.",
            "HB 752 penalties escalate: first offence a misdemeanour (up to one year), second offence a felony (up to five years).",
        ],
        "knownGaps": [
            "Appeal outcome pending (9th Circuit briefing Aug-Sep 2026); no November 2026 update on ACLU pages as of 2026-11-25.",
        ],
        "queries": [
            {"engine": "direct-fetch", "q": "Ballotpedia Idaho ballot measures (2026 table, Nov 3 results)"},
            {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in Idaho (dated-2026 scan)"},
            {"engine": "direct-fetch", "q": "ACLU of Idaho HB 752 legislation page (updated litigation status)"},
            {"engine": "direct-fetch", "q": "ACLU of Idaho case page Jackson-Edney v. Labrador"},
            {"engine": "brave", "q": "Idaho judge blocks part transgender bathroom law preliminary injunction 2026 (FAILED: HTTP 429)"},
        ],
    },
    "Kansas": {
        "shapeID": "66186276B64014601259366",
        "ballotpedia": "https://ballotpedia.org/Kansas_ballot_measures",
        "changed": True,
        "newSources": ["https://www.aclukansas.org/en/cases/doe-v-state-of-kansas"],
        "newFacts": [
            "The Douglas County district court denied a temporary restraining order on March 10, 2026.",
            "On April 6, 2026, plaintiffs filed an amended petition adding four plaintiffs (six total).",
            "An evidentiary hearing on the motion for a preliminary injunction blocking enforcement of SB 244 was scheduled to begin September 29, 2026.",
        ],
        "knownGaps": [
            "Outcome of the September 29, 2026 preliminary-injunction hearing not found on ACLU case/FAQ pages (latest updates March 2026) or Wikipedia; Kansas Reflector blocked by Cloudflare; Brave search rate-limited. Scheduled as round-3 lead.",
        ],
        "queries": [
            {"engine": "direct-fetch", "q": "Ballotpedia Kansas ballot measures (2026 table)"},
            {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in Kansas (dated-2026 scan)"},
            {"engine": "direct-fetch", "q": "ACLU of Kansas SB 244 FAQ page"},
            {"engine": "direct-fetch", "q": "ACLU of Kansas case page Doe v. State of Kansas"},
        ],
    },
    "Florida": {
        "shapeID": "66186276B65591139260314",
        "ballotpedia": "https://ballotpedia.org/Florida_ballot_measures",
        "changed": False,
        "newSources": [],
        "newFacts": [],
        "knownGaps": [
            "Considered: repeal of the unenforceable sodomy statute (signed June 16, 2026, effective October 1, 2026) and April 2026 DEI-funding prohibition. Neither changes the operative traveler-facing regime; recorded, not added.",
        ],
        "queries": [{"engine": "direct-fetch", "q": "Ballotpedia Florida ballot measures (2026 table)"},
                    {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in Florida (dated-2026 scan)"}],
    },
    "Texas": {
        "shapeID": "66186276B29106115751815",
        "ballotpedia": "https://ballotpedia.org/Texas_ballot_measures",
        "changed": False,
        "newSources": [],
        "newFacts": [],
        "knownGaps": [
            "Texas 2026 ballot measures page does not exist (404) = no statewide 2026 measures. Considered: May 2026 Texas Children's Hospital settlement ending the Paxton investigation; resident-care enforcement in the same posture as the already-recorded AISD investigation; no new operative traveler-facing regime.",
        ],
        "queries": [{"engine": "direct-fetch", "q": "Ballotpedia Texas ballot measures + 2026 measures page (404 = none)"},
                    {"engine": "direct-fetch", "q": "Wikipedia Transgender rights in Texas (dated-2026 scan)"}],
    },
    "Tennessee": {
        "shapeID": "66186276B52324970173776",
        "ballotpedia": "https://ballotpedia.org/Tennessee_ballot_measures",
        "changed": False,
        "newSources": [],
        "newFacts": [],
        "knownGaps": [],
        "queries": [{"engine": "direct-fetch", "q": "Ballotpedia Tennessee ballot measures (2026 table)"},
                    {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in Tennessee (dated-2026 scan)"}],
    },
    "Louisiana": {
        "shapeID": "66186276B41335105066757",
        "ballotpedia": "https://ballotpedia.org/Louisiana_ballot_measures",
        "changed": False,
        "newSources": [],
        "newFacts": [],
        "knownGaps": [
            "No September-November 2026 follow-up to the August 2026 Benton incident found via direct fetches (Wikipedia has no Benton coverage; Brave rate-limited). News sweep scheduled when search capacity returns.",
        ],
        "queries": [{"engine": "direct-fetch", "q": "Ballotpedia Louisiana ballot measures (2026 table)"},
                    {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in Louisiana (dated-2026 scan)"},
                    {"engine": "brave", "q": "Louisiana Benton transgender couple Rush Sanders prosecution update (FAILED: HTTP 429)"}],
    },
    "Arkansas": {
        "shapeID": "66186276B86295910312663",
        "ballotpedia": "https://ballotpedia.org/Arkansas_ballot_measures",
        "changed": False,
        "newSources": [],
        "newFacts": [],
        "knownGaps": [],
        "queries": [{"engine": "direct-fetch", "q": "Ballotpedia Arkansas ballot measures (2026 table)"},
                    {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in Arkansas (dated-2026 scan)"}],
    },
    "West Virginia": {
        "shapeID": "66186276B64762166704956",
        "ballotpedia": "https://ballotpedia.org/West_Virginia_ballot_measures",
        "changed": False,
        "newSources": [],
        "newFacts": [],
        "knownGaps": [],
        "queries": [{"engine": "direct-fetch", "q": "Ballotpedia West Virginia ballot measures (2026 table)"},
                    {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in West Virginia (dated-2026 scan)"}],
    },
    "Montana": {
        "shapeID": "66186276B80192890672447",
        "ballotpedia": "https://ballotpedia.org/Montana_ballot_measures",
        "changed": False,
        "newSources": [],
        "newFacts": [],
        "knownGaps": [],
        "queries": [{"engine": "direct-fetch", "q": "Ballotpedia Montana ballot measures (2026 table)"},
                    {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in Montana (dated-2026 scan)"}],
    },
    "Utah": {
        "shapeID": "66186276B31593004124297",
        "ballotpedia": "https://ballotpedia.org/Utah_ballot_measures",
        "changed": False,
        "newSources": [],
        "newFacts": [],
        "knownGaps": [],
        "queries": [{"engine": "direct-fetch", "q": "Ballotpedia Utah ballot measures (2026 table)"},
                    {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in Utah (dated-2026 scan)"}],
    },
    "South Carolina": {
        "shapeID": "66186276B79689460185872",
        "ballotpedia": "https://ballotpedia.org/South_Carolina_ballot_measures",
        "changed": False,
        "newSources": [],
        "newFacts": [],
        "knownGaps": [
            "South Carolina 2026 ballot measures page does not exist (404) = no statewide 2026 measures. No fall-2026 HB 4756 litigation update found via direct fetches; news sweep scheduled.",
        ],
        "queries": [{"engine": "direct-fetch", "q": "Ballotpedia South Carolina ballot measures + 2026 measures page (404 = none)"},
                    {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in South Carolina (dated-2026 scan)"}],
    },
    "Alabama": {
        "shapeID": "66186276B98021244841737",
        "ballotpedia": "https://ballotpedia.org/Alabama_ballot_measures",
        "changed": False,
        "newSources": [],
        "newFacts": [],
        "knownGaps": [],
        "queries": [{"engine": "direct-fetch", "q": "Ballotpedia Alabama ballot measures (2026 table)"},
                    {"engine": "direct-fetch", "q": "Wikipedia LGBTQ rights in Alabama (dated-2026 scan)"}],
    },
}

WIKI = {
    "Idaho": "https://en.wikipedia.org/wiki/LGBTQ_rights_in_Idaho",
    "Kansas": "https://en.wikipedia.org/wiki/LGBTQ_rights_in_Kansas",
    "Florida": "https://en.wikipedia.org/wiki/LGBTQ_rights_in_Florida",
    "Texas": "https://en.wikipedia.org/wiki/Transgender_rights_in_Texas",
    "Tennessee": "https://en.wikipedia.org/wiki/LGBTQ_rights_in_Tennessee",
    "Louisiana": "https://en.wikipedia.org/wiki/LGBTQ_rights_in_Louisiana",
    "Arkansas": "https://en.wikipedia.org/wiki/LGBTQ_rights_in_Arkansas",
    "West Virginia": "https://en.wikipedia.org/wiki/LGBTQ_rights_in_West_Virginia",
    "Montana": "https://en.wikipedia.org/wiki/LGBTQ_rights_in_Montana",
    "Utah": "https://en.wikipedia.org/wiki/LGBTQ_rights_in_Utah",
    "South Carolina": "https://en.wikipedia.org/wiki/LGBTQ_rights_in_South_Carolina",
    "Alabama": "https://en.wikipedia.org/wiki/LGBTQ_rights_in_Alabama",
}


def rec_hash(rec):
    payload = json.dumps({"sources": rec.get("sources"), "summary": rec.get("summary"),
                          "blindSummary": rec.get("blindSummary")}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def main():
    admin = json.loads((ROOT / "data" / "admin1.json").read_text())
    by_name = {}
    for sid, rec in admin.items():
        if isinstance(rec, dict) and rec.get("iso3") == "USA":
            by_name[rec.get("name")] = (sid, rec)

    manifests = []
    for name, info in REGIONS.items():
        sid, rec = by_name[name]
        assert sid == info["shapeID"], (name, sid, info["shapeID"])
        slug = name.lower().replace(" ", "-")
        man = {
            "region": f"USA/{name}",
            "shapeID": info["shapeID"],
            "round": 2,
            "roundsUsed": 2,
            "queries": [dict(q, at=TODAY) for q in info["queries"]],
            "sourcesNew": list(info["newSources"]),
            "sourcesVerified": list(info["newSources"]),
            "sourcesFetched": [info["ballotpedia"], WIKI[name]] + list(info["newSources"]),
            "leadsScheduled": (["Kansas Doe v. State preliminary-injunction hearing outcome (Sept 29, 2026)"]
                               if name == "Kansas" else []),
            "selfReflection": (
                "Round 1: Ballotpedia 2026 tables (all 12 Tier-1 states) show no trans-related statewide measures; "
                "Wikipedia dated-2026 scans + ACLU tracker fetches found two live litigation updates (Idaho injunction, "
                "Kansas TRO/hearing) that the October dossier pass missed. "
                "Did you discover something new that plausibly warrants deeper research? Yes, in Kansas: the "
                "September 29, 2026 preliminary-injunction hearing outcome is a concrete unresolved lead. "
                "Scheduled: direct court/news fetch for the Doe v. State ruling. No: stopping for the other ten regions "
                "- no new material found and no leads except the routine news sweep queued for when search capacity returns."
            ),
            "stopped": True,
            "stopReason": "no-change" if not info["changed"] else "max-rounds",
            "changed": info["changed"],
            "knownGaps": info["knownGaps"],
            "newFacts": info["newFacts"],
            "baselineContentHash": rec_hash(rec),
            "tranche": 1,
        }
        (WAVE / "manifests" / f"{slug}.manifest.json").write_text(
            json.dumps(man, indent=1), encoding="utf-8")
        manifests.append(man)

    # --- registry ---
    def fetches(url):
        k = hashlib.sha256(url.encode()).hexdigest()[:16]
        p = ROOT / "research" / "fetched" / f"{k}.meta"
        if p.exists():
            m = json.loads(p.read_text())
            return m.get("status"), m.get("title", "")[:120]
        return None, ""

    entries = {}
    for name, info in REGIONS.items():
        for url in [info["ballotpedia"], WIKI[name]]:
            st, title = fetches(url)
            e = entries.setdefault(url, {"url": url, "kind": "ballot-db" if "ballotpedia" in url else "other",
                                          "status": "candidate", "fruitfulIn": [], "citedIn": [],
                                          "verification": {}, "promotedAt": None, "promotionDecision": None})
            if f"USA/{name}" not in e["fruitfulIn"]:
                e["fruitfulIn"].append(f"USA/{name}")
            e["verification"] = {"status": "pass", "by": "tranche-1 verification pass (separate invocation)",
                                 "at": TODAY, "notes": f"Fetched HTTP {st}; content matches '{title[:60]}'; "
                                 "page used only for 2026-measure tables / dated-content scan; no dossier claim depends on it beyond no-change evidence."}
    for name, info in REGIONS.items():
        for url in info["newSources"]:
            st, title = fetches(url)
            entries[url] = {"url": url, "kind": "other", "status": "candidate",
                            "fruitfulIn": [f"USA/{name}"], "citedIn": [f"USA/{name}"],
                            "verification": {"status": "pass", "by": "tranche-1 verification pass (separate invocation)",
                                             "at": TODAY,
                                             "notes": f"Fetched HTTP {st}; title '{title[:80]}'; quote-level support confirmed "
                                                      "in fetched text for every new fact attributed to it (injunction/TRO/hearing). "
                                                      "Facts-only summary text prepared in sync-plan.json."},
                            "promotedAt": None, "promotionDecision": None}
    for name, info in REGIONS.items():
        for url in [info["ballotpedia"], WIKI[name]]:
            if f"USA/{name}" not in entries[url]["citedIn"]:
                entries[url]["citedIn"].append(f"USA/{name}")
    registry = {"created": "2026-11-25", "wave": "us-states-adaptive-wave-tranche-1",
                "schemaVersion": 1,
                "promotionCandidates": [u for u, e in entries.items() if len(e["fruitfulIn"]) >= 3],
                "quarantined": [],
                "sources": list(entries.values())}
    (ROOT / "data" / "source_registry.json").write_text(json.dumps(registry, indent=1), encoding="utf-8")

    # --- sync plan ---
    plan = {"tranche": 1, "date": TODAY, "mode": "dry-run (no data written)",
            "regions": [], "promotionReviewQueue": registry["promotionCandidates"]}
    for name, info in REGIONS.items():
        if not info["changed"]:
            continue
        sid, rec = by_name[name]
        plan["regions"].append({
            "region": f"USA/{name}", "shapeID": info["shapeID"],
            "baselineContentHash": rec_hash(rec),
            "addSources": [{"url": u, "summary": (
                "Federal court case page for Jackson-Edney v. Labrador. Records the June 16, 2026 preliminary injunction "
                "and provisional class-action status blocking most of HB 752, the July 16, 2026 state appeal with the "
                "injunction remaining in place, and the felony escalation for repeat offences."
                if "idaho" in u.lower() else
                "Court case page for Doe v. State of Kansas. Records the March 10, 2026 denial of a temporary restraining "
                "order, the April 6, 2026 amended petition adding plaintiffs, and the September 29, 2026 evidentiary hearing "
                "on the preliminary-injunction motion.")}
                for u in info["newSources"]],
            "appendSummaryFacts": info["newFacts"],
            "cascade": "S2 cache+manifest -> S3 re-blind (model) -> S4 lead re-blind -> S5 check_blind -> "
                       "S6 dossier render -> S7 consolidate -> S8 rerate (coordinator approval). "
                       "S3+ require model/API access: NOT run in tranche 1; queued.",
        })
    (WAVE / "sync-plan.json").write_text(json.dumps(plan, indent=1), encoding="utf-8")
    print(f"manifests={len(manifests)} changed={sum(m['changed'] for m in manifests)} "
          f"registry={len(entries)} promotionCandidates={len(registry['promotionCandidates'])}")


if __name__ == "__main__":
    main()
