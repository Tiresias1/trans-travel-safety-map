#!/usr/bin/env python3
"""Fetch every unique ADM1 source URL into a content cache.

Reads /tmp/adm1_url_inventory.txt (one URL per line) or --urls FILE. For each URL:
  cache key = sha1(url)[:16]
  research/fetched/<key>.txt   extracted text (HTML stripped, or pdftotext for PDFs)
  research/fetched/<key>.meta  JSON {url, status, http, bytes, error?}

Idempotent: a URL with an existing .meta and .txt > 200 bytes is skipped
unless --force. Failures are recorded (status=fail) so summarisation can emit
"NOTE: not retrievable" summaries, exactly like the country dossiers do.

Usage:
  python3 tools/fetch_adm1_articles.py                 # all, 12-way parallel
  python3 tools/fetch_adm1_articles.py --only 30       # first 30 (pilot)
  python3 tools/fetch_adm1_articles.py --jobs 8 --timeout 45
"""
from __future__ import annotations
import argparse, hashlib, html, json, os, re, subprocess, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "research" / "fetched"
UA = ("Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0")
TAG_RE = re.compile(r"<(script|style|noscript|svg|head)[^>]*>.*?</\1>", re.I | re.S)
ALLTAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"[ \t]{2,}")


def key_of(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:16]


def extract_html(raw: bytes) -> str:
    t = raw.decode("utf-8", "replace")
    t = TAG_RE.sub(" ", t)
    t = ALLTAG_RE.sub(" ", t)
    t = html.unescape(t)
    t = re.sub(r"\s*\n\s*", "\n", t)
    t = WS_RE.sub(" ", t)
    return t.strip()


def fetch_one(url: str, timeout: int, force: bool) -> dict:
    k = key_of(url)
    txt_p = CACHE / f"{k}.txt"
    meta_p = CACHE / f"{k}.meta"
    if not force and txt_p.exists() and meta_p.exists() and txt_p.stat().st_size > 200:
        try:
            return json.loads(meta_p.read_text())
        except Exception:
            pass
    meta = {"url": url, "status": "fail", "http": None, "bytes": 0, "error": None}
    try:
        r = subprocess.run(
            ["curl", "-sL", "--compressed", "--max-time", str(timeout),
             "--user-agent", UA, "-w", "%{http_code}",
             url, "-o", str(CACHE / f"{k}.raw")],
            capture_output=True, text=True, timeout=timeout + 15)
        code = r.stdout.strip()[-3:]
        meta["http"] = int(code) if code.isdigit() else None
        raw = CACHE / f"{k}.raw"
        if not raw.exists() or raw.stat().st_size < 100:
            meta["error"] = "empty/403 body"
            return meta
        head = raw.read_bytes()[:5]
        if head[:4] == b"%PDF" or url.lower().split("?")[0].endswith(".pdf"):
            try:
                t = subprocess.run(["pdftotext", "-q", "-l", "40", str(raw), "-"],
                                   capture_output=True, timeout=90)
                text = t.stdout.decode("utf-8", "replace").strip()
            except Exception as e:
                text = ""
            if len(text) < 200:
                meta["error"] = "pdf extraction thin"
            else:
                meta["status"] = "ok"
        else:
            text = extract_html(raw.read_bytes())
            meta["status"] = "ok" if len(text) >= 200 else "too-short"
            if meta["status"] != "ok":
                meta["error"] = f"text {len(text)} chars"
        txt_p.write_text(text or "")
        meta["bytes"] = len(text or "")
    except Exception as e:
        meta["error"] = str(e)[:140]
    finally:
        meta_p.write_text(json.dumps(meta))
        rp = CACHE / f"{k}.raw"
        if rp.exists():
            rp.unlink(missing_ok=True)
    return meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls", default="/tmp/adm1_url_inventory.txt")
    ap.add_argument("--jobs", type=int, default=12)
    ap.add_argument("--timeout", type=int, default=40)
    ap.add_argument("--only", type=int, default=None, help="limit count (pilot)")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    urls = [l.strip() for l in open(args.urls) if l.strip()]
    if args.only:
        urls = urls[:args.only]
    ok = fail = skip = 0
    lock = threading.Lock()
    counters = {"ok": 0, "bad": 0, "done": 0}

    def work(u):
        existing_ok = False
        m = CACHE / f"{key_of(u)}.meta"
        t = CACHE / f"{key_of(u)}.txt"
        if not args.force and m.exists() and t.exists() and t.stat().st_size > 200:
            existing_ok = True
        meta = fetch_one(u, args.timeout, args.force)
        with lock:
            counters["done"] += 1
            if existing_ok:
                counters["skip"] = counters.get("skip", 0) + 1
            if meta.get("status") == "ok":
                counters["ok"] += 1
            else:
                counters["bad"] += 1
            if counters["done"] % 25 == 0:
                print(f"{counters['done']}/{len(urls)} ok={counters['ok']} bad={counters['bad']}", flush=True)
        return meta

    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        list(ex.map(work, urls))
    print(f"DONE total={len(urls)} ok={counters['ok']} bad={counters['bad']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
