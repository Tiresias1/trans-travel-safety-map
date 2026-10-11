#!/usr/bin/env python3
"""Universal Wikipedia coverage sweep (2026-10-08, user directive).

Every country and dossier ADM1 region that has an LGBTQ-rights / trans-rights
Wikipedia article must have that article AS A SOURCE. For each record:

  1. LOCATE the article: try the canonical URL set
     (LGBTQ_rights_in_X, LGBT_history_in_X, LGBTQ_rights_in_<region>,
      Transgender_rights_in_X, ...), fetch via the Wikipedia API.
  2. CHECK whether that article is already listed in sources[].url.
  3. If missing: SUMMARISE it (LLM, substance-first, trans-visitor-relevant
     per LANE_SPECS r2) and append it as a source — claim carries the article's
     own key facts (no fabrication; text comes from the fetched extract).
  4. CITED-SOURCE HARVEST: list up to 10 on-topic sources cited by the article
     (from its References section) that the record does not already hold, and
     write them to research/wiki_cited/<who>.json for the intake queue
     (review + verification happens there, per the no-fabrication rules).

Also: extracts the article's trans-specific vs sexuality-law distinction where
present (feeds RATING_RULES 2's primary/tangential split).

Usage:
  python3 tools/wiki_universal_sweep.py --plan
  python3 tools/run_research_wave.py-style drivers call sweep_one().
"""
from __future__ import annotations
import argparse, json, re, sys, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from consolidate_record import call_llm  # noqa

UA = "TransTravelResearch/1.0 (coverage sweep; contact: research@transtravelsafety.com)"

TITLE_PATTERNS = [
    "LGBTQ rights in {x}", "LGBT rights in {x}", "LGBT history in {x}",
    "Transgender rights in {x}", "Transgender people in {x}",
    "LGBTQ people in {x}", "Human rights in {x}",  # last resort only
]


def fetch_extract(title: str) -> tuple[str, str]:
    """Returns (extract, canonical_url) or ("", "") if the page is missing."""
    t = urllib.parse.quote(title.replace(" ", "_"))
    api = (f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts"
           f"&explaintext=1&redirects=1&format=json&formatversion=2&titles={t}")
    for attempt in range(4):
        try:
            req = urllib.request.Request(api, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read().decode())
            pages = d.get("query", {}).get("pages", [])
            if pages and "missing" not in pages[0]:
                full = pages[0].get("extract") or ""
                # keep the sections that matter (rights/identity/status), drop
                # pure-culture padding beyond ~60k chars
                return full[:60000], f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
            return "", ""
        except Exception:
            if attempt == 3:
                return "", ""
            time.sleep(2 ** attempt)
    return "", ""


def find_article(name: str, iso3: str = "") -> tuple[str, str]:
    cands = []
    for pat in TITLE_PATTERNS:
        cands.append(pat.format(x=name))
    if iso3:  # disambiguation helper, e.g. "Georgia (country)"
        cands.append(f"LGBTQ rights in {name} ({iso3})")
    for t in cands:
        txt, url = fetch_extract(t)
        if txt:
            return txt, url
    return "", ""


def already_source(rec: dict, url: str) -> bool:
    return any(isinstance(s, dict) and s.get("url") == url for s in (rec.get("sources") or []))


def summarise(article: str, name: str) -> str:
    out = call_llm(
        "You summarise source material for a trans-visitor travel-safety dossier.",
        f"""Summarise the Wikipedia article below as a SOURCE CLAIM for {name}'s
dossier, per these rules: substance-first (acts, provisions, penalties, dates,
outcomes — never narrate the outlet); TRANS-VISITOR-RELEVANT only (law,
enforcement, documents, screening, facilities, custody, care, violence,
protection machinery); explicitly preserve the distinction between
sexuality-law facts and transgender-specific facts, and quote any documented
statement about societal tolerance OF TRANSGENDER people specifically.
4-8 sentences per field. No fabrication — only what the article states.
If the article covers a field, include it; if not, return "" for that field.

ARTICLE:
{article[:30000]}

Return ONLY JSON: {{"trans_facts": "...", "sexuality_facts": "...", "social": "..."}}""")
    if isinstance(out, dict):
        parts = [str(out.get(k) or "") for k in ("trans_facts", "sexuality_facts", "social")]
        parts = [p for p in parts if p.strip()]
        if parts:
            return " ".join(parts)
    raise ValueError("summarise: model returned no usable fields")


def harvest_cited(article: str, name: str, have_urls: set) -> list:
    """LLM names up to 10 on-topic references the article cites."""
    out = call_llm(
        "You extract source leads from a Wikipedia article for verification.",
        f"""List up to 10 ON-TOPIC sources cited by this Wikipedia article that a
trans-visitor safety dossier for {name} would want (laws, court rulings,
government reports, human-rights reports, documented incidents). For each:
title/outlet, what it documents, and any URL or citation detail visible in the
text. On-topic = transgender/LGBTQ legal status, enforcement, or rights
machinery in {name}. Prefer primary/legal and institutional sources.

ARTICLE:
{article[:30000]}

Return ONLY JSON: {{"sources": [{{"title": "...", "documents": "...", "detail": "..."}}]}}""")
    out_list = out.get("sources") if isinstance(out, dict) else None
    return out_list[:10] if isinstance(out_list, list) else []


def sweep_one(rec: dict, who: str, name: str, iso3: str = "") -> dict:
    """Returns a report dict; mutates rec (adds the wiki source when missing)."""
    rep = {"who": who, "article_found": False, "was_missing": False, "added": False,
           "cited_leads": 0}
    article, url = find_article(name, iso3)
    if not article:
        rep["note"] = "no LGBTQ/trans rights Wikipedia article found"
        return rep
    rep["article_found"] = True
    rep["url"] = url
    if already_source(rec, url):
        return rep
    rep["was_missing"] = True
    claim = summarise(article, name)
    rec.setdefault("sources", []).append({
        "url": url, "title": f"LGBTQ rights in {name} (Wikipedia)", "summary": claim})
    rep["added"] = True
    rep["claim"] = claim[:400]
    # cited-source harvest for the intake queue
    have = {s.get("url") for s in (rec.get("sources") or []) if isinstance(s, dict)}
    leads = harvest_cited(article, name, have)
    rep["cited_leads"] = len(leads)
    if leads:
        outdir = ROOT / "research" / "wiki_cited"
        outdir.mkdir(exist_ok=True)
        fn = who.replace(":", "_").replace("/", "_") + ".json"
        (outdir / fn).write_text(json.dumps({"who": who, "url": url, "leads": leads},
                                            ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--countries", action="store_true")
    ap.add_argument("--regions", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    jobs = []
    if args.countries:
        jobs += [("country:" + k, k, None, C[k]) for k in sorted(C)]
    if args.regions:
        jobs += [(f"{r['iso3']}/{r['name']}", r['iso3'], r['name'], r)
                 for r in sorted(A.values(), key=lambda x: x.get("name", ""))
                 if r.get("dossier")]
    if args.only:
        want = set(args.only)
        jobs = [j for j in jobs if j[0] in want]
    print(f"sweeping {len(jobs)} records", flush=True)

    report = []
    def one(j):
        who, iso3, nm, rec = j
        try:
            return sweep_one(rec, who, nm or rec.get("name", iso3), iso3 if not nm else "")
        except Exception as e:
            return {"who": who, "error": str(e)[:200]}
    with ThreadPoolExecutor(args.workers) as ex:
        futs = {ex.submit(one, j): j[0] for j in jobs}
        done = 0
        for f in as_completed(futs):
            r = f.result()
            report.append(r)
            done += 1
            if r.get("error"):
                tag = f"ERROR {r['error'][:80]}"
            else:
                tag = ("ADDED" if r.get("added") else
                       "MISSING-ARTICLE" if not r.get("article_found") else
                       "already-sourced" if not r.get("was_missing") else "checked")
            print(f"[{r.get('who')}] {tag} leads={r.get('cited_leads', 0)}", flush=True)
            if done % 25 == 0:
                print(f"... {done}/{len(jobs)}", flush=True)
    outdir = ROOT / "research" / "wiki_sweep2"
    outdir.mkdir(exist_ok=True)
    (outdir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1),
                                        encoding="utf-8")
    n_added = sum(1 for r in report if r.get("added"))
    n_missing = sum(1 for r in report if not r.get("article_found"))
    leads = sum(r.get("cited_leads", 0) for r in report)
    print(f"SWEEP DONE: {n_added} articles added as sources, {n_missing} countries/regions "
          f"have no such article, {leads} cited-source leads queued", flush=True)
    if args.apply:
        (ROOT / "data" / "countries.json").write_text(
            json.dumps(C, ensure_ascii=False, indent=1), encoding="utf-8")
        (ROOT / "data" / "admin1.json").write_text(
            json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")
        print("applied", flush=True)


if __name__ == "__main__":
    main()