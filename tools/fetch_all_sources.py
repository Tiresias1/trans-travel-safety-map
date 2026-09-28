#!/usr/bin/env python3
"""Fetch/cache every source URL on the map and extract title + publication date.

Adds to research/fetched/<sha16>.meta a richer dict (existing txt is never
overwritten if present; missing URLs fetched):
  {url, status, http, bytes, error, title, published, published_src, fetchedAt}
Then run tools/build_source_manifest.py to roll dates into data/source_manifest.json.

Usage: python3 tools/fetch_all_sources.py [--only ISO3[,ISO3]] [--workers 10]
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, hashlib, html, json, os, re, sys, time
import urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FDIR = ROOT / "research" / "fetched"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
DATE_RES = [
    (re.compile(r'(?:article:published_time|publication_date)[^>]*content="([^"]+)"', re.I), "meta"),
    (re.compile(r'"datePublished"\s*:\s*"([^"]+)"'), "jsonld"),
    (re.compile(r'itemprop="datePublished"[^>]*content="([^"]+)"', re.I), "microdata"),
    (re.compile(r'<time[^>]*datetime="([^"T]+)T', re.I), "time-tag"),
    (re.compile(r'citation_date"[^>]*content="([^"]+)"', re.I), "citation"),
    (re.compile(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}(?:\s*[0-2]?\d:\d{2})?'), "prose"),
]
MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"])}

def norm(raw):
    raw = html.unescape(raw or "").strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", raw)
    if m:
        return m.group(0)
    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})", raw)
    if m:
        return f"{m.group(3)}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}"
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", raw)
    if m:
        return f"{m.group(3)}-{m.group(1)}-{m.group(2)}"
    return (raw or "")[:24] or None

def strip(raw):
    raw = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()

def key(url):
    return hashlib.sha256(url.encode()).hexdigest()[:16]

def all_urls(only):
    c = json.load(open(ROOT / "data/countries.json"))
    a = json.load(open(ROOT / "data/admin1.json"))
    out = {}
    def add(u, iso):
        if isinstance(u, dict):
            u = u.get("url")
        if isinstance(u, str) and u.startswith("http"):
            out.setdefault(u, set()).add(iso)
    for iso, r in c.items():
        if only and iso not in only:
            continue
        for s in r.get("sources") or []:
            add(s, iso)
    for sid, r in a.items():
        if only and r.get("iso3") not in only:
            continue
        for s in r.get("sources") or []:
            add(s, r["iso3"])
    return out

def process(url, iso_set):
    k = key(url)
    txt_p, meta_p = FDIR / f"{k}.txt", FDIR / f"{k}.meta"
    meta = {}
    if meta_p.exists():
        try:
            meta = json.loads(meta_p.read_text())
        except Exception:
            meta = {}
    have_txt = txt_p.exists() and txt_p.stat().st_size > 400
    if meta.get("published") and have_txt:
        return "cached"
    raw = None
    try:
        req = urllib.request.Request(url, headers={"user-agent": UA, "accept": "*/*"})
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read(900_000).decode("utf-8", "replace")
        status, http = "ok", 200
    except Exception as e:
        status, http = "error", getattr(e, "code", None)
    if raw:
        title = None
        m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
        if m:
            title = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()[:180]
        pub, src = None, None
        for rx, tag in DATE_RES:
            m = rx.search(raw[:220_000])
            if m:
                g = m.group(1) if m.groups else m.group(0)
                pub = norm(g)
                src = tag
                if pub:
                    break
        if not have_txt:
            txt_p.write_text(strip(raw)[:400_000], encoding="utf-8")
    else:
        title, pub, src = meta.get("title"), meta.get("published"), meta.get("published_src")
    meta.update({"url": url, "status": status, "http": http,
                 "title": title or meta.get("title"), "published": pub,
                 "published_src": src, "iso3s": sorted(iso_set),
                 "fetchedAt": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                 "error": None if raw else meta.get("error") or "unreachable"})
    tmp = meta_p.with_suffix(".tmp"); tmp.write_text(json.dumps(meta, ensure_ascii=False))
    tmp.replace(meta_p)
    return status

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="comma-separated ISO3s")
    ap.add_argument("--workers", type=int, default=10)
    args = ap.parse_args()
    only = {o.upper() for o in (args.only or "").split(",") if o} or None
    FDIR.mkdir(parents=True, exist_ok=True)
    urls = all_urls(only)
    print(f"{len(urls)} unique URLs", flush=True)
    counts = {"ok": 0, "error": 0, "cached": 0}
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(process, u, s): u for u, s in urls.items()}
        for i, f in enumerate(cf.as_completed(futs), 1):
            try:
                counts[f.result()] = counts.get(f.result(), 0) + 1
            except Exception:
                counts["error"] += 1
            if i % 100 == 0:
                print(f"[{i}/{len(urls)}] {counts}", flush=True)
    print("done:", counts)
    return 0

if __name__ == "__main__":
    sys.exit(main())
