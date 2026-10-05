#!/usr/bin/env python3
"""Wikipedia topical sweep for every country: harvest the canonical LGBTQ-rights
and transgender-topic pages (which the pipeline under-uses — 27/233 countries
cite one) and emit claim-ready packets for the intake queue.

For each country (from data/countries.json) it queries the Wikipedia API for
candidate titles, fetches the best matches' intro + recent-history sections via
the REST plain-text extract, and writes research/wikipedia_sweep/<ISO>.json
with {url, title, extract}. One sweep run is a data pull; the intake step
decides relevance/claims.

Usage: python3 tools/sweep_wikipedia.py [--only NER,USA] [--out research/wikipedia_sweep]
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, json, re, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://en.wikipedia.org/w/api.php"
HEAD = {"user-agent": "trans-travel-map/1.0 (research; contact: map maintainer)"}

def wp(params: dict) -> dict:
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{API}?{qs}", headers=HEAD)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

def candidates(iso: str, name: str) -> list[str]:
    """Title candidates for a country's topic pages."""
    base = name
    bases = [base]
    # common inflections: "in the United States", "in the United Kingdom"
    alt = {"USA": ["the United States", "United States"],
           "GBR": ["the United Kingdom", "United Kingdom", "Britain"],
           "RUS": ["Russia", "the Russian Federation"],
           "KOR": ["South Korea", "Korea"],
           "PRK": ["North Korea"],
           "PSE": ["Palestine", "the State of Palestine"],
           "IRN": ["Iran"],
           "COD": ["the Democratic Republic of the Congo", "Democratic Republic of the Congo"],
           "TWN": ["Taiwan"],
           "CIV": ["Ivory Coast"],
           "NLD": ["the Netherlands", "Netherlands"],
           "PHL": ["the Philippines", "Philippines"],
           "MDA": ["Moldova", "Moldova"],
           "BHS": ["the Bahamas", "Bahamas"],
           "GMB": ["the Gambia", "Gambia"],
           "ARE": ["the United Arab Emirates", "United Arab Emirates"],
           "CZE": ["the Czech Republic", "Czech Republic"],
           "DMA": ["Dominica"]}
    if iso in alt:
        bases = alt[iso] + [base]
    out = []
    for b in bases:
        for tmpl in ("LGBTQ rights in {}", "LGBT rights in {}", "Transgender people in {}",
                     "LGBT in {}", "LGBTQ in {}", "Homosexuality in {}"):
            out.append(tmpl.format(b))
    return list(dict.fromkeys(out))

def fetch_extract(title: str) -> str | None:
    """Resolve redirects + fetch lead extract in ONE API call (avoids the
    429 wall). Retries on transient errors."""
    import time
    for attempt in range(4):
        try:
            d = wp({"action": "query", "titles": title, "prop": "extracts",
                    "explaintext": "1", "exintro": "1", "format": "json",
                    "redirects": "1"})
            pages = d.get("query", {}).get("pages", {})
            # follow normalized/redirect title if present
            for p in pages.values():
                if p.get("missing"):
                    return None
                ex = p.get("extract")
                if ex and len(ex) > 40:
                    return ex
            return None
        except Exception:
            if attempt == 3:
                return None
            time.sleep(2.0 * (2 ** attempt))
    return None

def has_page(title: str) -> bool:
    try:
        d = wp({"action": "query", "titles": title, "format": "json", "redirects": "1"})
    except Exception:
        return False
    pages = d.get("query", {}).get("pages", {})
    return any(p.get("pageid") for p in pages.values())

def work(iso: str, name: str) -> dict:
    cands = candidates(iso, name)
    chosen, extract = None, None
    for c in cands:
        extract = fetch_extract(c)   # resolves redirects; one API call
        if extract:
            chosen = c
            # normalize to the actual article title via a cheap callback is
            # optional; the candidate URL redirects fine for citation
            break
    return {"iso3": iso, "name": name,
            "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(chosen.replace(' ', '_'))}" if chosen else None,
            "title": chosen, "extract": extract}


REGION_TMPLS = ("LGBTQ rights in {}", "LGBT rights in {}", "Transgender rights in {}",
                "Transgender people in {}", "LGBT culture in {}", "LGBT history in {}")


def work_region(iso: str, name: str) -> dict:
    """Find a region-level Wikipedia page: 'LGBT rights in Texas' etc. The region
    name often includes a suffix ('Province', 'Region', 'Voivodeship', 'State').
    Tries several inflections; returns the first that resolves with an extract.
    """
    cands = []
    base = name.replace(" (Malvinas)", "").strip()
    # try the full region name and increasingly trimmed forms (drop parentheticals)
    forms = [base]
    for suf in (" Region", " Oblast", " Kraj", " Voivodeship", " State", " Province",
                " Department", " Governorate", " Prefecture", " Municipality"):
        if base.endswith(suf):
            forms.append(base[: -len(suf)])
            break
    for f in dict.fromkeys(forms):
        for tmpl in REGION_TMPLS:
            cands.append(tmpl.format(f))
    chosen, extract = None, None
    for c in cands:
        extract = fetch_extract(c)
        if extract:
            chosen = c
            break
    return {"iso3": iso, "name": name,
            "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(chosen.replace(' ', '_'))}" if chosen else None,
            "title": chosen, "extract": extract}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default=str(ROOT / "research" / "wikipedia_sweep"))
    ap.add_argument("--regions", action="store_true",
                    help="sweep is over dossier ADM1 regions instead of countries")
    ap.add_argument("--parents", default="",
                    help="with --regions: limit to these parent countries (comma ISO3)")
    args = ap.parse_args()
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    only = [x.strip().upper() for x in args.only.split(",") if x.strip()]
    if args.regions:
        A = json.loads((ROOT / "data" / "admin1.json").read_text())
        parents = {p.strip().upper() for p in args.parents.split(",") if p.strip()}
        items = [(r.get("iso3"), r.get("name", "")) for r in A.values()
                 if r.get("dossier") and (not parents or r.get("iso3") in parents)]
        if only:
            items = [(iso, nm) for iso, nm in items if nm.strip().upper() in only]
        # still sweep the region-specific candidates plus "state of X"
        outdir = Path(args.out) / "regions"; outdir.mkdir(parents=True, exist_ok=True)
        picks = items
    else:
        picks = only or list(C)
        outdir = Path(args.out); outdir.mkdir(parents=True, exist_ok=True)
    got = miss = 0
    country_name = {}
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        futs = []
        if args.regions:
            # region candidates: <name>, <name>, <parent>, plus US-state / province forms
            for iso, nm in picks:
                country_name[f"{iso}/{nm}"] = nm
                time.sleep(0.05)
                futs.append(ex.submit(work_region, iso, nm))
        else:
            for iso in picks:
                time.sleep(0.05)
                futs.append(ex.submit(work, iso, C[iso].get("name", iso)))
        for fu in futs:
            rec = fu.result()
            fn = f"{rec['iso3']}__{re.sub(r'[^a-zA-Z0-9_-]', '_', rec['name'])[:60]}.json"
            p = outdir / fn
            p.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
            if rec["extract"]:
                got += 1
            else:
                miss += 1
            print(f"{rec['iso3']}/{rec['name'][:30]}: {rec['title'] or 'NO TOPIC PAGE'} "
                  f"({len(rec['extract'] or '')} chars)", flush=True)
    print(f"\nwrote {len(picks)} files to {outdir}: {got} with extract, {miss} no topic page")

if __name__ == "__main__":
    main()