#!/usr/bin/env python3
"""US-states wave: fetch + cache a URL into research/fetched/<sha16>.{txt,meta}
(same layout as tools/fetch_all_sources.py — the single cache).
Usage: python3 research/us-states-wave/fetch.py <url> [<url> ...]
Prints: sha, http status, byte size, visible-text char count, title.
"""
import hashlib, html, json, re, sys, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FDIR = ROOT / "research" / "fetched"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

def key(url):
    return hashlib.sha256(url.encode()).hexdigest()[:16]

def visible_text(raw):
    raw = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()

def main():
    for url in sys.argv[1:]:
        k = key(url)
        txtp, metap = FDIR / f"{k}.txt", FDIR / f"{k}.meta"
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9",
                                                   "Accept": "text/html,application/xhtml+xml"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                status, raw = r.status, r.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            print(f"{url} :: HTTP {e.code}")
            continue
        except Exception as e:
            print(f"{url} :: FAIL {e}")
            continue
        title_m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
        title = visible_text(title_m.group(1)) if title_m else ""
        text = visible_text(raw)
        if not txtp.exists():
            txtp.write_text(text, encoding="utf-8")
        meta = {"url": url, "status": status, "bytes": len(raw.encode()),
                "title": title[:300], "fetchedAt": datetime.now(timezone.utc).isoformat(),
                "wave": "us-states-tranche-1"}
        metap.write_text(json.dumps(meta, indent=1), encoding="utf-8")
        print(f"{k} status={status} bytes={len(raw.encode())} textchars={len(text)} :: {title[:90]}")
        print(f"    {url}")

if __name__ == "__main__":
    main()
