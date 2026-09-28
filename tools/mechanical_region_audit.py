#!/usr/bin/env python3
"""Deterministic fallback audit for region packets that trip provider content
filters. Same output schema as the LLM lanes (consumed by
tools/audit_relevance_results.py unchanged), marked "mechanical": true.

Heuristics per source:
  cached missing / status!=ok        -> supports=unverifiable, keep=false
  tokens from claim_summary          -> grep counts in cached text
     >=60% hit: yes | >=30%: partial | else no
  on_topic                           -> region-name tokens present in cache;
     if ONLY a sibling region's tokens hit -> false
  keep=false when off-topic, or supports=no on a claimed source, or
  unverifiable (unreachable/nav-only pages follow the countries-tier rule).
Criminalisation verification is delegated to the freshness wave via
false_claims + needs_search (its tier-1 queue already covers legal claims).

Usage: python3 tools/mechanical_region_audit.py
"""
import json, os, re, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
P, R = ROOT / "data/relevance_packets", ROOT / "data/relevance_results"

STOP = set("the of and for in on at is was with law region says said after before over their its from that this".split())
NAME_NOISE = set("oblast krai republic state province prefecture department governorate region voivodeship emirate canton autonomous special capital federal district municipality metropolitan islands island".split())

def name_tokens(name):
    return {w for w in re.findall(r"[a-zà-ÿ]{4,}", name.lower()) if w not in STOP and w not in NAME_NOISE}

def claim_tokens(claim):
    if not claim:
        return []
    toks = []
    toks += [t.lower() for t in re.findall(r'"([^"]{3,40})"', claim)]
    toks += re.findall(r"\b(?:19|20)\d{2}\b", claim)
    toks += [t for t in re.findall(r"\b\d[\d,.]{2,}\b", claim)]
    caps = re.findall(r"\b([A-ZÀ-Þ][A-Za-zÀ-ÿ'’-]{2,}(?:\s+(?:of\s+)?[A-ZÀ-Þ][A-Za-zÀ-ÿ'’-]{2,}){0,3})\b", claim)
    toks += [c.lower() for c in caps][:6]
    out, seen = [], set()
    for t in toks:
        t = t.strip().lower()
        if 3 < len(t) < 45 and t not in seen and t not in STOP:
            seen.add(t); out.append(t)
    return out[:8]

def grep_hits(tokens, path):
    if not tokens or not os.path.exists(path):
        return 0, 0
    pat = "|".join(re.escape(t) for t in tokens)
    try:
        r = subprocess.run(["grep", "-oiE", pat, str(path)], capture_output=True, timeout=20)
        hits = {h.lower() for h in re.findall(r"\S+", r.stdout.decode("utf-8", "ignore"))}
    except Exception:
        return -1, len(tokens)
    hit_n = sum(1 for t in tokens if any(t in h or h in t for h in hits))
    return hit_n, len(tokens)

def main():
    done = {f[:-5] for f in os.listdir(R)}
    # sibling names per parent for off-topic detection
    sibs = {}
    for f in os.listdir(P):
        if f.startswith("country_"):
            continue
        pk = json.load(open(P / f))
        sibs.setdefault(pk["who"].split("/")[0], []).append((f[:-5], pk["name"]))
    CRIM_RE = re.compile(r"criminalis|criminaliz|sodomy|in force|banned? by|no law (?:against|criminalising)", re.I)
    n = 0
    for f in sorted(os.listdir(P)):
        if f.startswith("country_") or f[:-5] in done:
            continue
        pk = json.load(open(P / f))
        iso, rname = pk["who"].split("/", 1)
        rtoks = name_tokens(rname)
        verdicts, kept_tokens = [], set()
        for s in pk.get("sources") or []:
            url = s.get("url"); claim = s.get("summary") or ""
            cached = s.get("cached")
            import hashlib
            k = hashlib.sha256((url or "").encode()).hexdigest()[:16]
            mf = ROOT / "research/fetched" / f"{k}.meta"
            status = None
            if mf.exists():
                try: status = json.loads(mf.read_text()).get("status")
                except Exception: pass
            cpath = ROOT / cached if cached else None
            ct = claim_tokens(claim)
            if not cpath or not cpath.exists() or status == "error":
                verdicts.append({"url": url, "keep": False, "on_topic": None,
                                 "supports": "unverifiable",
                                 "note": "mechanical: unreachable/nav-only or uncached"})
                continue
            hn, tn = grep_hits(ct, cpath)
            sup = "unverifiable" if hn < 0 or tn == 0 else ("yes" if hn/tn >= .6 else "partial" if hn/tn >= .3 else "no")
            region_hit = bool(rtoks) and grep_hits(sorted(rtoks), cpath)[0] > 0
            on_topic, note = True, ""
            if not region_hit:
                sib_hit = next((nm for pid, nm in sibs.get(iso, [])
                                if pid != f[:-5] and grep_hits(sorted(name_tokens(nm)), cpath)[0] > 0), None)
                if sib_hit:
                    on_topic = False; note = f"mechanical: region absent from text; sibling '{sib_hit}' present"
                else:
                    on_topic = None; note = "mechanical: no region/sibling token; framework source"
            keep = on_topic is not False and sup != "no"
            if sup == "no" and ct:
                keep = False; note = (note + "; " if note else "") + "mechanical: claim tokens not found in source"
            if sup in ("yes", "partial") and keep:
                kept_tokens.update(ct)
            verdicts.append({"url": url, "keep": keep, "on_topic": on_topic,
                             "supports": sup, "note": note or "mechanical"})
        # false_claims: summary sentences whose tokens match nothing kept
        fcs, needs = [], []
        summary = re.sub(r"<[^>]+>", " ", pk.get("summary_text") or "")
        for sent in re.split(r"(?<=[.;])\s+", summary):
            st = claim_tokens(sent)
            if len(st) < 3:
                continue
            if not any(t in kept_tokens for t in st):
                clause = re.sub(r"\s+", " ", sent).strip()[:120]
                fcs.append(clause)
                if CRIM_RE.search(sent):
                    needs.append(clause)
        out = {"who": pk["who"], "mechanical": True, "verdicts": verdicts,
               "false_claims": fcs[:6], "search_updates": [],
               "needs_search": needs[:4]}
        (R / f"{f[:-5]}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
        n += 1
    print(f"mechanical verdicts written: {n}")

if __name__ == "__main__":
    main()
