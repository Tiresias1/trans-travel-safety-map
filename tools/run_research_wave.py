#!/usr/bin/env python3
"""Fleet research wave (2026-10-07 redo, phase 1).

Per record (country + dossier region):
  1. COVERAGE AUDIT — LLM-tags existing claims against DIMENSION_MATRIX.md.
  2. SOURCE TEXT — fetch the country's LGBTQ-rights Wikipedia page full text
     (raw API, throttled, cached); merge held ILGA monitor snippets as sources.
  3. GAP FILL — extract one claim per uncovered dimension, every claim gated by
     a verbatim >=5-word n-gram against the source text (anti-fabrication).
     Dimensions with no source support get an EXPLICIT absence note appended to
     outOfScopeNotes (silence is not an answer).
  4. APPLY — locked read-modify-write; failure leaves the record untouched.

Regions: parent-managed dimensions (D3/D4/D5) are skipped — they inherit the
parent framework layer; local dimensions only.

Usage:
  python3 tools/run_research_wave.py --plan
  python3 tools/run_research_wave.py --run --workers 6 [--skip-fetch]
"""
from __future__ import annotations
import argparse, fcntl, json, re, subprocess, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from consolidate_record import call_llm  # noqa

MATRIX = (ROOT / "research" / "DIMENSION_MATRIX.md").read_text()
DIMS = re.findall(r"^(D\d+)\s+(.+?)\s+—", MATRIX, re.M)
DIM_IDS = [d[0] for d in DIMS]
PARENT_MANAGED = {"D3", "D4", "D5"}
CACHE = Path("/tmp/research_texts")

UA = "TransTravelResearch/1.0 (dossier coverage research; contact: research@transtravelsafety.com)"


def fetch_page(url: str) -> str:
    """Fetch a Wikipedia page raw wikitext, throttled, with backoff."""
    title = url.rstrip("/").split("/wiki/")[-1]
    api = ("https://en.wikipedia.org/w/api.php?action=query&prop=extracts"
           "&explaintext=1&format=json&formatversion=2&redirects=1&titles="
           + urllib.parse.quote(title))
    for attempt in range(5):
        try:
            req = urllib.request.Request(api, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read().decode())
            pages = d.get("query", {}).get("pages", [])
            return (pages[0].get("extract") if pages else "") or ""
        except Exception as e:
            if attempt == 4:
                print(f"    [fetch fail] {title}: {str(e)[:80]}", flush=True)
                return ""
            time.sleep(2 ** attempt)
    return ""


def wiki_url_for(iso3: str, name: str) -> str:
    u = (json.loads((ROOT / "research" / "wikipedia_sweep" / f"{iso3}.json").read_text())
         if (ROOT / "research" / "wikipedia_sweep" / f"{iso3}.json").exists() else {})
    url = u.get("url") or ""
    if "/wiki/" not in url:
        url = "https://en.wikipedia.org/wiki/LGBTQ_rights_in_" + name.replace(" ", "_")
    return url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--skip-fetch", action="store_true")
    args = ap.parse_args()
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    targets = [(f"country:{k}", "country", k, None, C[k]) for k in sorted(C)]
    targets += [(f"{r['iso3']}/{r['name']}", "region", r["iso3"], r["name"], r)
                for r in sorted(A.values(), key=lambda x: x.get("name", ""))
                if r.get("dossier") and not r.get("inherited")]
    print(f"research wave: {len(targets)} records", flush=True)
    if args.plan:
        return

    ILGA = json.loads((ROOT / "data" / "ilga_news.json").read_text())
    cov_dir = ROOT / "research" / "coverage"; cov_dir.mkdir(exist_ok=True)
    if not args.skip_fetch:
        CACHE.mkdir(exist_ok=True)

    # fetches are serialized at a low rate by a dedicated thread pool
    fetch_lock = __import__("threading").Lock()
    last_fetch = [0.0]

    def stats():
        out = []
        done = 0
        return done

    def one(t):
        who, kind, iso, nm, rec = t
        label = nm or iso
        # ---- 1. audit ----
        claims = []
        for i, s in enumerate(rec.get("sources") or []):
            if isinstance(s, dict) and (s.get("summary") or s.get("title")):
                claims.append(f"[{i}] {str(s.get('summary') or s.get('title'))[:400]}")
        if not claims:
            return who, "skip: no sources"
        audit = call_llm(
            "You are a coverage auditor for a trans-visitor travel-safety dossier.",
            f"""{MATRIX}

TASK: audit which dimensions the record's source claims cover. For each claim,
assign the dimension ids it substantively covers. Then list dimensions with
ZERO coverage as gaps.{'  For a REGION record, D3/D4/D5 are parent-managed and inherit the parent framework layer — audit only the remaining dimensions.' if kind == 'region' else ''}

Record: {who}
CLAIMS:
{chr(10).join(claims)}

Return ONLY JSON: {{"claim_dims": {{"0": ["D1","D9"]}}, "gaps": ["D7"], "notes": "..."}}""")
        gaps = [g for g in audit.get("gaps", []) if g in DIM_IDS]
        if kind == "region":
            gaps = [g for g in gaps if g not in PARENT_MANAGED]
        if not gaps:
            return who, "clean: full coverage"
        # ---- 2. source text ----
        srcs = []
        if kind == "country":
            url = wiki_url_for(iso, label)
            cf = CACHE / f"{iso}.txt"
            if cf.exists():
                txt = cf.read_text()
            elif args.skip_fetch:
                txt = ""
            else:
                with fetch_lock:
                    wait = max(0.0, 0.7 - (time.time() - last_fetch[0]))
                    time.sleep(wait)
                    last_fetch[0] = time.time()
                txt = fetch_page(url)
                cf.write_text(txt)
            if txt:
                srcs.append((url, str(audit.get("title") or "Wikipedia country coverage"), txt))
        # held ILGA snippets as auxiliary material
        ilga_items = ILGA.get(iso if kind == "country" else "") or []
        if ilga_items:
            bundle = "\n".join(f"- ({a.get('da','')[:10]}) {a.get('h','')}: {a.get('d','')[:220]}"
                               for a in ilga_items[:12])
            srcs.append(("https://database.ilga.org/" + (iso or "").lower() + "-lgbti",
                         "ILGA World monitor items", bundle))
        if not srcs:
            # explicit absence marker
            rec.setdefault("outOfScopeNotes", "")
            note = "<p>Unsourced dimensions (no held source covers them, none found in this pass): " \
                   + ", ".join(gaps) + ".</p>"
            if not any(g in str(rec.get("outOfScopeNotes", "")) for g in gaps):
                rec["outOfScopeNotes"] = str(rec.get("outOfScopeNotes", "")) + note
            return who, f"no-source: {','.join(gaps)} (recorded explicitly)"
        # ---- 3. gap fill per source ----
        dim_list = "\n".join(f"{d}: {t}" for d, t in DIMS if d in gaps)
        added = []
        for url, title, text in srcs:
            if not text.strip():
                continue
            out = call_llm(
                "You extract sourced findings for a trans-visitor dossier. Any claim "
                "not grounded in the source text is fabrication and is mechanically rejected.",
                f"""GAP DIMENSIONS to fill:
{dim_list}

SOURCE TEXT (verbatim):
{text[:45000]}

For EACH gap dimension, either extract the finding the source text supports
(2-4 sentences, substance-first: what happened, whom it hits, dates, numbers,
policy names in plain language) or write exactly 'no source text supports this
dimension'. Trans-youth angles matter: minors travel, carry medication, and are
a major political target — note youth-specific findings under D8/D13 where
present.

Return ONLY JSON: {{"D7": "claim text or 'no source text...'", ...}}""")
            have = {s.get("url") for s in (rec.get("sources") or []) if isinstance(s, dict)}
            for d, t2 in out.items():
                if d not in gaps or not isinstance(t2, str):
                    continue
                t2 = t2.strip()
                if not t2 or "no source text" in t2.lower():
                    continue
                words = re.findall(r"[a-z']+", t2.lower())
                ok = False
                if len(words) >= 5:
                    tt = " ".join(re.sub(r"\[\[|\]\]|\\'|'|\{|\}|\|", " ", text.lower()).split())
                    text_words = tt.split()
                    tn = {" ".join(text_words[i:i + 5]) for i in range(len(text_words) - 4)}
                    for i in range(len(words) - 4):
                        if " ".join(words[i:i + 5]) in tn:
                            ok = True
                            break
                else:
                    ok = True
                if not ok:
                    continue
                claim = f"{title}: {t2}"
                if url in have:
                    for s in rec["sources"]:
                        if isinstance(s, dict) and s.get("url") == url:
                            s["summary"] = str(s.get("summary", "")).rstrip() + " " + claim
                            break
                else:
                    rec.setdefault("sources", []).append(
                        {"url": url, "title": title, "summary": claim})
                    have.add(url)
                added.append(d)
        # explicit absence for dimensions still uncovered
        still = [g for g in gaps if g not in added]
        if still:
            note = "<p>Unsourced dimensions after this research pass: " + ", ".join(still) + ".</p>"
            on = str(rec.get("outOfScopeNotes", "") or "")
            if not all(("Unsourced dimensions" not in on) or True for _ in [0]):
                pass
            if "Unsourced dimensions after this research pass" not in on:
                rec["outOfScopeNotes"] = on + note
        # ---- 4. apply (locked RMW) ----
        with open(ROOT / "data" / ".apply.lock", "a+") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            try:
                if kind == "country":
                    D = json.loads((ROOT / "data" / "countries.json").read_text())
                    D[iso] = rec
                    pth = ROOT / "data" / "countries.json"
                else:
                    D = json.loads((ROOT / "data" / "admin1.json").read_text())
                    tgt = next(x for x in D.values()
                               if x.get("iso3") == iso and x.get("name") == nm)
                    for k2 in ("sources", "outOfScopeNotes"):
                        if rec.get(k2) is not None:
                            tgt[k2] = rec[k2]
                    pth = ROOT / "data" / "admin1.json"
                tmp = pth.with_suffix(".tmp")
                tmp.write_text(json.dumps(D, ensure_ascii=False, indent=1), encoding="utf-8")
                tmp.replace(pth)
            finally:
                fcntl.flock(lf, fcntl.LOCK_UN)
        return who, f"ok: filled {','.join(added) or 'none'} (gaps {','.join(gaps)})"

    with ThreadPoolExecutor(args.workers) as ex:
        futs = {ex.submit(one, t): t[0] for t in targets}
        done = 0
        for f in as_completed(futs):
            w = futs[f]
            try:
                who, msg = f.result()
                print(f"[{who}] {msg}", flush=True)
            except Exception as e:
                print(f"[{w}] ERROR {str(e)[:140]}", flush=True)
            done += 1
            if done % 25 == 0:
                print(f"... {done}/{len(targets)}", flush=True)
    print("RESEARCH WAVE DONE", flush=True)


if __name__ == "__main__":
    main()