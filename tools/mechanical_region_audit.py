#!/usr/bin/env python3
"""Deterministic (LLM-free) source audit for ADM1 region packets.

The provider content filter kills LLM lanes that read region packets (graphic
incident text), and the blinder fleet's research pass already fetched+verified
these sources once. This pass adds the two mechanical checks that matter:
  - on_topic: region/sibling-name token presence in the cached article;
  - supports: distinctive claim tokens grep-found in the cached article.
Outputs the SAME schema as LLM lanes (consumed by audit_relevance_results.py),
plus 'needs_search' clauses (criminalisation claims) for the freshness wave.

Usage: python3 tools/mechanical_region_audit.py [--force]
"""
import json, os, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
P, R, F = ROOT/'data/relevance_packets', ROOT/'data/relevance_results', ROOT/'research/fetched'

STOP = {"the", "of", "and", "autonomous", "region", "oblast", "krai", "republic",
        "state", "province", "special", "capital", "district", "metropolitan",
        "department", "governorate", "prefecture", "canton", "emirate", "voivodeship",
        "this", "that", "with", "from", "have", "has", "was", "were", "its", "for",
        "after", "under", "into", "been", "are", "not", "more", "most", "other"}
CRIM = re.compile(r"criminali[sz]|sodomy|decriminali[sz]|banned?|prohibition|illegal|arrest", re.I)

def key(u):
    import hashlib; return hashlib.sha256((u or "").encode()).hexdigest()[:16]

def name_words(s):
    return {w for w in re.findall(r"[a-zA-ZÀ-ɏ]{4,}", (s or "").lower()) if w not in STOP}

def claim_tokens(t):
    out = set()
    for m in re.findall(r"[\"'“‘]([^\"'’”]{4,60})[\"'’”]", t or ""): out.add(m.lower())
    for m in re.findall(r"\b(?:19|20)\d{2}\b", t or ""): out.add(m)
    for m in re.findall(r"\b[A-ZÀ-ɏ][\wÀ-ɏ'-]{3,}(?:\s+[A-ZÀ-ɏ][\wÀ-ɏ'-]{2,}){0,3}\b", t or ""):
        out.add(m.lower())
    for m in re.findall(r"\b\d[\d,.]{1,9}\b", t or ""): out.add(m)
    return {x for x in out if len(x) > 3}

def main():
    force = "--force" in sys.argv
    done = {f[:-5] for f in os.listdir(R)}
    # sibling names per parent for off-topic detection
    sibs = {}
    for fn in os.listdir(P):
        if fn.startswith("country_"): continue
        w = json.load(open(P/fn))["who"]
        sibs.setdefault(w.split("/")[0], []).append(w.split("/", 1)[1])
    n = 0
    for fn in sorted(os.listdir(P)):
        if fn.startswith("country_"): continue
        stem = fn[:-5]
        if stem in done and not force: continue
        pk = json.load(open(P/fn))
        who, rname = pk["who"], pk["name"]
        iso = who.split("/")[0]
        rw = name_words(rname)
        sib_words = set()
        for s in sibs.get(iso, []):
            if s != rname: sib_words |= name_words(s)
        verdicts, kept_tokens = [], set()
        for src in pk.get("sources") or []:
            u = src.get("url"); cached = src.get("cached")
            path = ROOT/cached if cached else (F/f"{key(u)}.txt")
            meta = json.loads(Path(str(path)+".meta" if cached else F/f"{key(u)}.meta").read_text()) \
                   if Path(str(path)+".meta" if cached else F/f"{key(u)}.meta").exists() else {}
            if meta.get("status") != "ok" or not Path(path).exists():
                verdicts.append({"url": u, "keep": False, "on_topic": False,
                                 "supports": "no", "note": "mechanical: uncached/unreachable at audit time"})
                continue
            text = Path(path).read_text(errors="ignore").lower()
            toks = claim_tokens(src.get("summary") or "")
            hits = sum(1 for t in toks if t in text)
            sup = ("yes" if toks and hits/len(toks) >= 0.6 else
                   "partial" if toks and hits >= 1 else "no" if toks else "partial")
            region_in = any(w in text for w in rw) if rw else True
            sib_only = (not region_in) and any(w in text for w in sib_words)
            on_topic = bool(region_in) or (not sib_only)
            keep = on_topic and sup in ("yes", "partial")
            if sup in ("yes", "partial") and keep:
                kept_tokens |= {t for t in toks if t in text}
            note = "mechanical"
            if sib_only: note = f"mechanical: sibling-region names present, region name absent"
            elif sup == "no": note = "mechanical: claim tokens absent from article"
            verdicts.append({"url": u, "keep": keep, "on_topic": on_topic,
                             "supports": sup, "note": note})
        # unsupported-clause scan of the summary
        summary = re.sub(r"<[^>]+>", " ", pk.get("summary_text") or "")
        fcs, needs = [], []
        for clause in re.split(r"(?<=[.;])\s+", summary):
            ct = claim_tokens(clause)
            if len(ct) < 2: continue
            if sum(1 for t in ct if t in kept_tokens) >= 2: continue
            q = clause.strip()[:110]
            if len(q) > 25:
                fcs.append(q)
                if CRIM.search(clause): needs.append(q)
        out = {"who": who, "mechanical": True, "verdicts": verdicts,
               "false_claims": fcs[:6], "search_updates": [], "needs_search": needs[:4]}
        (R/f"{stem}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
        n += 1
    print(f"mechanical region verdicts written: {n}")

if __name__ == "__main__":
    main()
