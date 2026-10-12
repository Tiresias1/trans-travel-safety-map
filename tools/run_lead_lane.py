#!/usr/bin/env python3
"""Lead-verification lane for research/wiki_cited/ leads (2026-10-08).

The wiki sweep harvested cited references as TITLE-ONLY leads (the plain-text
extract API strips links). This lane resolves each lead to a real URL:

  1. fetch the record's cited Wikipedia article RAW HTML (action=parse),
  2. extract the reference-section <a href> links mechanically (html.parser,
     NOT regex — href extraction from markup is parsing, not pattern-matching),
  3. match each lead title to a reference link by token overlap (difflib on
     slug tokens; no regex),
  4. fetch the resolved URL, LLM-summarise the trans-relevant substance
     (STYLE_RULES-gated, same failure handling as the audit lane),
  5. emit data/intake_out2/<batch>.json in the apply_intake lane format
     {who, adds:[{url,title,published,summary}]}.

Unresolved leads are reported, never fabricated.

Usage: python3 tools/run_lead_lane.py [--workers 2] [--batches N ...]
"""
from __future__ import annotations
import argparse, difflib, hashlib, json, re, sys, time
import urllib.request, urllib.error
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from consolidate_record import call_llm  # noqa

UA = "Mozilla/5.0 (X11; Linux x86_64) TransTravelLeadLane/1.0"


class _RefParser(HTMLParser):
    """Collect anchors + their anchor text from an HTML document."""
    def __init__(self):
        super().__init__()
        self.links = []  # (url, text)
        self._cur = None
        self._buf = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for k, v in attrs:
                if k == "href" and v and v.startswith("http") and "wikipedia.org" not in v:
                    self._cur = v
    def handle_data(self, data):
        if self._cur:
            self._buf.append(data)
    def handle_endtag(self, tag):
        if tag == "a" and self._cur:
            text = " ".join("".join(self._buf).split())
            if text:
                self.links.append((self._cur, text))
            self._cur = None
            self._buf = []


def article_refs(wiki_url: str) -> list:
    """All external links in the article's references, as (url, anchor-text)."""
    title = wiki_url.rsplit("/wiki/", 1)[-1]
    api = (f"https://en.wikipedia.org/w/api.php?action=parse&page={title}"
           f"&prop=text&format=json&formatversion=2&redirects=1")
    for attempt in range(3):
        try:
            req = urllib.request.Request(api, headers={"User-Agent": UA})
            d = json.loads(urllib.request.urlopen(req, timeout=90).read().decode())
            html = d.get("parse", {}).get("text", "")
            break
        except Exception:
            if attempt == 2:
                return []
            time.sleep(2 ** attempt)
    else:
        return []
    p = _RefParser()
    p.feed(html)
    # dedup by URL, keep first text
    seen = {}
    for u, t in p.links:
        seen.setdefault(u, t)
    return list(seen.items())


def slug_tokens(s: str) -> set:
    return set(re.sub(r"[^a-z0-9 ]", " ", str(s).lower()).split())


def resolve_leads(lead_titles: list, refs: list, who: str) -> list:
    """LLM resolves lead titles to reference URLs. Returns [{title,url}] —
    unresolved leads are omitted, never guessed."""
    if not refs:
        return []
    reflist = "\n".join(f"- {t[:110]} :: {u}" for u, t in refs[:60])
    titles = "\n".join(f"[{i}] {t}" for i, t in enumerate(lead_titles))
    out = call_llm(
        "You resolve research leads to their source links.",
        f"""Below are research LEADS (title descriptions of documents a dossier
wants) and the REFERENCE LINKS of the Wikipedia article they came from
(anchor text :: url). For each lead, pick the ONE reference link that is
that same document — match on document identity (court case name, law,
report title, incident description), not on wording similarity alone.
Dutch/other-language anchor texts may be translations of the lead title.
If no reference matches a lead, omit that lead. Never invent a URL.

LEADS for {who}:
{titles}

REFERENCES:
{reflist}

Return ONLY JSON: {{"resolved": [{{"index": 0, "url": "..."}}]}}""")
    resolved = []
    if isinstance(out, dict):
        valid = {u for u, _ in refs}
        for r in (out.get("resolved") or []):
            u = str(r.get("url") or "")
            if u in valid:
                i = int(r.get("index", -1))
                resolved.append({"title": lead_titles[i] if 0 <= i < len(lead_titles) else "",
                                 "url": u})
    return resolved


def fetch_url(url: str, limit: int = 40000) -> str:
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                raw = r.read(limit * 4)
            text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ",
                          raw.decode("utf-8", "ignore"))
            text = re.sub(r"<[^>]+>", " ", text)
            return re.sub(r"\s+", " ", text)[:limit]
        except Exception:
            if attempt == 2:
                return ""
            time.sleep(2 ** attempt)
    return ""


def summarise_claim(text: str, title: str, name: str) -> str:
    out = call_llm(
        "You write source-claim summaries for a trans-visitor travel-safety dossier.",
        f"""Summarise the source below as ONE claim sentence-chain for {name}'s
dossier: what this document/incident establishes, with dates, provisions,
outcomes — substance only, no outlet narration, no meta-commentary about the
record. Trans-visitor-relevant facts only. If the source does not contain
trans-relevant substance, return {{"on_topic": false}}.

SOURCE ({title}):
{text[:16000]}

Return ONLY JSON: {{"on_topic": true/false, "summary": "...", "published": "YYYY-MM-DD or \"\""}}""")
    if isinstance(out, dict) and out.get("on_topic") and (out.get("summary") or "").strip():
        return json.dumps({"summary": out["summary"], "published": out.get("published", "")},
                          ensure_ascii=False)
    return ""


def process_batch(path: Path, outdir: Path, cache: dict) -> dict:
    d = json.loads(path.read_text())
    out = {"records": []}
    for rec in (d if isinstance(d, list) else (d.get("records") or [])):
        who = rec.get("who")
        # the wiki article URL for this record: stored in research/wiki_cited
        cited = ROOT / "research" / "wiki_cited" / (who.replace(":", "_").replace("/", "_") + ".json")
        if not cited.exists():
            continue
        cd = json.loads(cited.read_text())
        wiki_url = cd.get("url")
        ckey = hashlib.sha1(wiki_url.encode()).hexdigest()[:10]
        if ckey not in cache:
            cache[ckey] = article_refs(wiki_url)
        refs = cache[ckey]
        titles = [s.get("title", "") for s in (rec.get("sources") or [])]
        resolved = resolve_leads(titles, refs, who)
        adds = []
        for res in resolved:
            title, url = res["title"], res["url"]
            text = fetch_url(url)
            if not text:
                continue
            r = summarise_claim(text, title, rec.get("name", who))
            if not r:
                continue
            rj = json.loads(r)
            adds.append({"url": url, "title": title,
                         "published": rj.get("published", ""),
                         "summary": rj["summary"]})
        if adds:
            out["records"].append({"who": who, "adds": adds})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batches", nargs="*", type=int)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--limit", type=int, default=0, help="process at most N batches")
    args = ap.parse_args()
    indir = ROOT / "data" / "intake_batches2"
    outdir = ROOT / "data" / "intake_out2"
    outdir.mkdir(exist_ok=True)
    files = sorted(indir.glob("i*.json"))
    if args.batches:
        files = [f for f in files if int(f.stem[1:]) in set(args.batches)]
    if args.limit:
        files = files[:args.limit]
    print(f"lead lane: {len(files)} batches", flush=True)
    cache = {}
    import concurrent.futures as cf
    def one(f):
        outp = outdir / f.name
        if outp.exists():
            return f.name, "done-already"
        try:
            out = process_batch(f, outdir, cache)
            outp.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
            n = sum(len(r.get("adds", [])) for r in out["records"])
            return f.name, f"ok adds={n}"
        except Exception as e:
            return f.name, f"ERROR {str(e)[:120]}"
    done = 0
    with cf.ThreadPoolExecutor(args.workers) as ex:
        for name, status in ex.map(one, files):
            done += 1
            print(f"[{done}/{len(files)}] {name}: {status}", flush=True)
    print("LEAD LANE DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())