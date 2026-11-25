#!/usr/bin/env python3
"""US-states wave search helper. Engines tried in order this session:
DDG (bot-challenge 202) -> Bing HTML (junk/geo) -> Brave (works).
Usage: python3 research/us-states-wave/search.py '<state>' '<query>' [...]
Saves research/us-states-wave/raw/<slug>-<n>-<hash>.{html,json} with parsed results.
Sequential, 1.5s throttle. No credentials.
"""
import json, re, sys, time, urllib.request, urllib.parse, urllib.error, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RAW = ROOT / "research" / "us-states-wave" / "raw"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

_opener = urllib.request.build_opener(NoRedirect)

def resolve_go(token):
    url = "https://search.brave.com/go/v1/" + token
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with _opener.open(req, timeout=15) as r:
            return r.geturl()
    except urllib.error.HTTPError as e:
        loc = e.headers.get("Location")
        return loc or ""
    except Exception:
        return ""

def clean(s):
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&nbsp;", " ").replace("&#39;", "'").replace("&amp;", "&")
    return re.sub(r"\s+", " ", s).strip()

def parse_brave(html):
    out = []
    blocks = re.split(r'<div class="snippet svelte-', html)
    for b in blocks[1:]:
        mtype = re.search(r'data-type="([^"]+)"', b)
        if mtype and mtype.group(1) != "web":
            continue
        href = re.search(r'href="(/go/v1/[^"]+)"', b)
        title = re.search(r'class="title search-snippet-title[^"]*" title="([^"]+)"', b)
        snip = re.search(r'class="generic-snippet[^"]*"><div class="content[^"]*">(.*?)<!--', b, re.S)
        cite = re.search(r'<cite class="snippet-url[^"]*">(.*?)</cite>', b, re.S)
        if not href:
            continue
        token = href.group(1).split("/go/v1/")[1]
        real = resolve_go(token)
        if not real or "brave.com" in real:
            continue
        out.append({"url": real,
                    "title": clean(title.group(1)) if title else "",
                    "snippet": clean(snip.group(1))[:700] if snip else "",
                    "cite": clean(cite.group(1))[:150] if cite else ""})
        time.sleep(0.3)
    return out

def fetch_search(q):
    url = "https://search.brave.com/search?" + urllib.parse.urlencode({"q": q})
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status, r.read().decode("utf-8", "ignore")

def main():
    state, queries = sys.argv[1], sys.argv[2:]
    slug = re.sub(r"[^a-z0-9]+", "-", state.lower()).strip("-")
    for i, q in enumerate(queries):
        try:
            status, html = fetch_search(q)
        except Exception as e:
            print(f"[{state}] q{i} FAIL {e}")
            continue
        h = hashlib.sha256(q.encode()).hexdigest()[:8]
        (RAW / f"{slug}-{i:02d}-{h}.html").write_text(html, encoding="utf-8")
        results = parse_brave(html)
        (RAW / f"{slug}-{i:02d}-{h}.json").write_text(
            json.dumps({"state": state, "engine": "brave", "query": q, "status": status,
                        "n": len(results), "results": results}, indent=1), encoding="utf-8")
        print(f"[{state}] q{i} status={status} web-results={len(results)} :: {q}")
        for r in results[:5]:
            print(f"    - {r['title'][:85]} | {r['url'][:105]}")
        time.sleep(1.5)

if __name__ == "__main__":
    main()
