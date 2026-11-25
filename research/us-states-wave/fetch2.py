#!/usr/bin/env python3
"""Tranche 2-4 fetch sweep: direct fetches per remaining region.
Ballotpedia ballot-measures page + Wikipedia <State> page (+ ACLU case page only
where tranche-1 pattern suggests litigation — handled separately).
Saves to research/fetched/<sha16>.{txt,meta} via same layout as fetch.py.
Idempotent: existing cache files are not overwritten.
Writes research/us-states-wave/fetch2-results.json
"""
import hashlib, html, json, re, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FDIR = ROOT / "research" / "fetched"
WAVE = ROOT / "research" / "us-states-wave"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# (display name, ballotpedia slug, wikipedia slug candidates)
REMAINING = [
 ("Alaska","Alaska",["LGBTQ_rights_in_Alaska"]),
 ("Arizona","Arizona",["LGBTQ_rights_in_Arizona"]),
 ("California","California",["LGBTQ_rights_in_California"]),
 ("Colorado","Colorado",["LGBTQ_rights_in_Colorado"]),
 ("Connecticut","Connecticut",["LGBTQ_rights_in_Connecticut"]),
 ("Delaware","Delaware",["LGBTQ_rights_in_Delaware"]),
 ("District of Columbia","District_of_Columbia",["LGBTQ_rights_in_the_District_of_Columbia"]),
 ("Georgia","Georgia",["LGBTQ_rights_in_Georgia"]),
 ("Hawaii","Hawaii",["LGBTQ_rights_in_Hawaii"]),
 ("Illinois","Illinois",["LGBTQ_rights_in_Illinois"]),
 ("Indiana","Indiana",["LGBTQ_rights_in_Indiana"]),
 ("Iowa","Iowa",["LGBTQ_rights_in_Iowa"]),
 ("Kentucky","Kentucky",["LGBTQ_rights_in_Kentucky"]),
 ("Maine","Maine",["LGBTQ_rights_in_Maine"]),
 ("Maryland","Maryland",["LGBTQ_rights_in_Maryland"]),
 ("Massachusetts","Massachusetts",["LGBTQ_rights_in_Massachusetts"]),
 ("Michigan","Michigan",["LGBTQ_rights_in_Michigan"]),
 ("Minnesota","Minnesota",["LGBTQ_rights_in_Minnesota"]),
 ("Mississippi","Mississippi",["LGBTQ_rights_in_Mississippi"]),
 ("Missouri","Missouri",["LGBTQ_rights_in_Missouri"]),
 ("Nebraska","Nebraska",["LGBTQ_rights_in_Nebraska"]),
 ("Nevada","Nevada",["LGBTQ_rights_in_Nevada"]),
 ("New Hampshire","New_Hampshire",["LGBTQ_rights_in_New_Hampshire"]),
 ("New Jersey","New_Jersey",["LGBTQ_rights_in_New_Jersey"]),
 ("New Mexico","New_Mexico",["LGBTQ_rights_in_New_Mexico"]),
 ("New York","New_York",["LGBTQ_rights_in_New_York"]),
 ("North Carolina","North_Carolina",["LGBTQ_rights_in_North_Carolina"]),
 ("North Dakota","North_Dakota",["LGBTQ_rights_in_North_Dakota"]),
 ("Ohio","Ohio",["LGBTQ_rights_in_Ohio"]),
 ("Oklahoma","Oklahoma",["LGBTQ_rights_in_Oklahoma"]),
 ("Oregon","Oregon",["LGBTQ_rights_in_Oregon"]),
 ("Pennsylvania","Pennsylvania",["LGBTQ_rights_in_Pennsylvania"]),
 ("Rhode Island","Rhode_Island",["LGBTQ_rights_in_Rhode_Island"]),
 ("South Dakota","South_Dakota",["LGBTQ_rights_in_South_Dakota"]),
 ("Vermont","Vermont",["LGBTQ_rights_in_Vermont"]),
 ("Virginia","Virginia",["LGBTQ_rights_in_Virginia"]),
 ("Washington","Washington",["LGBTQ_rights_in_Washington"]),
 ("Wisconsin","Wisconsin",["LGBTQ_rights_in_Wisconsin"]),
 ("Wyoming","Wyoming",["LGBTQ_rights_in_Wyoming"]),
 ("Puerto Rico","Puerto_Rico",["LGBTQ_rights_in_Puerto_Rico"]),
 ("Guam","Guam",["LGBTQ_rights_in_Guam"]),
 ("U.S. Virgin Islands","US_Virgin_Islands",["LGBTQ_rights_in_the_United_States_Virgin_Islands"]),
 ("Northern Mariana Islands","Northern_Mariana_Islands",["LGBTQ_rights_in_the_Northern_Mariana_Islands"]),
 ("American Samoa","American_Samoa",["LGBTQ_rights_in_American_Samoa"]),
]
EXTRA = [
 "https://www.aclukansas.org/en/cases/doe-v-state-of-kansas",
 "https://www.acluidaho.org/en/cases/jackson-edney-v-labrador",
]

def key(url): return hashlib.sha256(url.encode()).hexdigest()[:16]
def visible_text(raw):
    raw = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()

def fetch(url):
    k = key(url); txtp, metap = FDIR / f"{k}.txt", FDIR / f"{k}.meta"
    if txtp.exists() and metap.exists():
        return {"url": url, "cached": True, "sha": k}
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9", "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status, raw = r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "sha": k}
    except Exception as e:
        return {"url": url, "error": str(e)[:120], "sha": k}
    tm = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
    title = visible_text(tm.group(1)) if tm else ""
    text = visible_text(raw)
    txtp.write_text(text, encoding="utf-8")
    metap.write_text(json.dumps({"url": url, "status": status, "bytes": len(raw.encode()), "title": title[:300],
                                 "fetchedAt": datetime.now(timezone.utc).isoformat(), "wave": "us-states-tranche-2"}, indent=1), encoding="utf-8")
    return {"url": url, "status": status, "sha": k, "title": title[:120], "chars": len(text)}

def main():
    only = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    results = {}
    urls = []
    for name, bp, wikis in REMAINING:
        if only and name not in only: continue
        urls.append(f"https://ballotpedia.org/{bp}_ballot_measures")
        for w in wikis:
            urls.append(f"https://en.wikipedia.org/wiki/{w}")
    urls += EXTRA
    for u in urls:
        r = fetch(u)
        results[u] = r
        print(r)
        time.sleep(0.8)
    out = WAVE / "fetch2-results.json"
    prev = json.loads(out.read_text()) if out.exists() else {}
    prev.update(results)
    out.write_text(json.dumps(prev, indent=1), encoding="utf-8")

if __name__ == "__main__":
    main()
