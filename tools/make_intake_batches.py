#!/usr/bin/env python3
"""Turn the ILGA harvest + Wikipedia sweep into intake batches.

Two new corpus sources now exist that the pipeline did not have at W1-W4:
  data/ilga_news.json          (239 countries, 2,174 articles, monitor.ilga.org)
  research/wikipedia_sweep/    (per-country LGBTQ-rights + transgender topic pages)

This tool builds data/intake_batches/iNNN.json in the relevance-packet layout
({who, iso3, name, score, summary_text, sources:[{url,title,published,status,
cached,claim_summary}]}) so the existing intake/relevance lanes can consume them
unchanged. Only articles/pages that likely carry facts NOT already in the record
are emitted (URL not already cited + date >= the record's researchedAt when a
recency threshold is requested).

Usage:
  python3 tools/make_intake_batches.py [--out data/intake_batches] [--per 10]
                                       [--since 2025-01-01] [--max-per-country 8]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import fetch_ilga_news as fi


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "data" / "intake_batches"))
    ap.add_argument("--per", type=int, default=10)
    ap.add_argument("--since", default="2024-01-01",
                    help="only ILGA articles published at/after this date (YYYY-MM-DD)")
    ap.add_argument("--max-per-country", type=int, default=8)
    args = ap.parse_args()

    C = json.loads((ROOT / "data" / "countries.json").read_text())
    A = json.loads((ROOT / "data" / "admin1.json").read_text()) if (ROOT / "data" / "admin1.json").exists() else {}
    ilga = json.loads((ROOT / "data" / "ilga_news.json").read_text())
    iso3map = fi.iso3_to_iso2()

    outdir = Path(args.out); outdir.mkdir(parents=True, exist_ok=True)
    batches, cur = [], None
    n = 0

    def push(who, rec, url, title, claim):
        nonlocal n, cur
        iso3 = rec.get("iso3") or who.split(":")[-1]  # country records key by ISO3
        if cur is None:
            cur = []
        cur.append({"who": who, "iso3": iso3, "name": rec.get("name", ""),
                    "score": rec.get("score", 0),
                    "summary_text": str(rec.get("summary", ""))[:600],
                    "sources": [{"url": url, "title": title, "published": None,
                                 "status": "ok", "cached": None, "claim_summary": claim}]})
        n += 1
        if len(cur) >= args.per:
            batches.append(cur)
            cur = None  # reassign, never mutate the list stored in batches

    for iso3, r in C.items():
        iso2 = iso3map.get(iso3)
        if not iso2:
            continue
        cited = set()
        for s in (r.get("sources") or []):
            u = s.get("url") if isinstance(s, dict) else str(s)
            cited.add(u)
        # ILGA news
        per = 0
        for a in ilga.get(iso2, []) or []:
            u = a.get("url")
            if not u or u in cited:
                continue
            if str(a.get("published") or "")[:10] < args.since:
                continue
            claim = (a.get("snippet") or "")[:280]
            ttl = a.get("title") or u
            push(f"country:{iso3}", r, u, ttl, claim)
            per += 1
            if per >= args.max_per_country:
                break
        # Wikipedia sweep page (if it exists and is not already cited)
        wfile = ROOT / "research" / "wikipedia_sweep" / f"{iso3}.json"
        if wfile.exists():
            w = json.loads(wfile.read_text())
            if w.get("url") and w["url"] not in cited and w.get("extract"):
                push(f"country:{iso3}", r, w["url"], w.get("title") or w["url"],
                     (w.get("extract") or "")[:280])

    if cur:
        batches.append(cur)

    for i, b in enumerate(batches, 1):
        (outdir / f"i{i:03d}.json").write_text(
            json.dumps({"records": b}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(batches)} intake batches ({n} candidate sources) to {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())