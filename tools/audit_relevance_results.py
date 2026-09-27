#!/usr/bin/env python3
"""Apply relevance-lane verdicts: prune off-topic sources, collect false-claim
findings and freshness evidence for the summary-rework waves.

Reads data/relevance_results/<who>.json written by audit lanes:
  { "who", "verdicts": [{"url","keep":bool,"on_topic":bool,"supports":bool,
     "note"}], "false_claims": ["..."], "search_updates": [{"claim","found",
     "url","date"}] }

Modes:
  --plan      print what would change (default)
  --apply     prune keep=false / on_topic=false sources from countries.json and
              admin1.json (only when ALL of a jurisdiction's sources were
              reviewed — never partial-prune); write
              data/relevance_findings.json {who: {pruned:[urls],
              false_claims:[...], search_updates:[...]}}
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "data/relevance_results"

def load_results():
    out = {}
    for p in sorted(RES.glob("*.json")):
        try:
            d = json.loads(p.read_text())
        except Exception as e:
            print(f"[warn] unreadable result {p.name}: {e}")
            continue
        if isinstance(d, dict) and d.get("who"):
            out[d["who"]] = d
    return out

def url_of(s):
    return s.get("url") if isinstance(s, dict) else s

FLOOR = 2  # never leave a record under this many sources; survivors are queued for research

def rank_verdict(v):
    """Best-of-the-worst ordering for floor-keeps: on-topic & unverifiable > contradicted."""
    return (0 if v.get("on_topic") else 1,
            {"partial": 0, "unverifiable": 1, "yes": 0, "no": 2}.get(v.get("supports"), 3))

def prunable(sources, verdicts):
    """Return (drop_set, floor_kept, needs_research)."""
    drop = {u for u, v in verdicts.items()
            if v.get("keep") is False or v.get("on_topic") is False}
    kept = sum(1 for s in sources if url_of(s) not in drop)
    floor_kept = []
    if kept < FLOOR:
        candidates = sorted((url_of(s) for s in sources if url_of(s) in drop),
                            key=lambda u: rank_verdict(verdicts[u]))
        need = FLOOR - kept
        floor_kept = candidates[:need]
        drop -= set(floor_kept)
    return drop, floor_kept, bool(floor_kept) or kept == 0

def main() -> int:
    apply = "--apply" in sys.argv
    res = load_results()
    c = json.load(open(ROOT / "data/countries.json"))
    a = json.load(open(ROOT / "data/admin1.json"))
    findings = {}
    research_needed = {}
    pruned_urls = 0
    for who, d in sorted(res.items()):
        verdicts = {v.get("url"): v for v in d.get("verdicts", []) if v.get("url")}
        # resolve target record(s) sources first, so floor logic can see them
        if who.startswith("country:"):
            tgt = [(c.get(who.split(":", 1)[1]) or {}).get("sources")]
        else:
            iso, name = who.split("/", 1)
            tgt = [next((a[sid]["sources"] for sid in a
                         if a[sid].get("iso3") == iso and a[sid].get("name") == name), None)]
        srcs = tgt[0] or []
        all_drop = {u for u, v in verdicts.items()
                    if v.get("keep") is False or v.get("on_topic") is False}
        full_cover = bool(srcs) and len(verdicts) >= len(srcs)
        if full_cover:
            drop, floor_kept, needs = prunable(srcs, verdicts)
        else:
            drop, floor_kept, needs = set(), [], False
        f = {"reviewed": len(verdicts), "pruned": sorted(all_drop),
             "floor_kept": floor_kept, "needs_research": needs,
             "false_claims": d.get("false_claims") or [],
             "search_updates": d.get("search_updates") or [],
             "notes": {u: v.get("note") for u, v in verdicts.items()
                       if v.get("note") and v.get("supports") is not True}}
        findings[who] = f
        if needs:
            research_needed[who] = {"reason": "floor-kept low-quality sources",
                                    "false_claims": f["false_claims"]}
        if f["pruned"] or f["false_claims"]:
            print(f"{who}: drop {len(all_drop)}"
                  + (f" (floor keeps {len(floor_kept)})" if floor_kept else "")
                  + f", false_claims {len(f['false_claims'])}, reviewed {f['reviewed']}")
        if not apply or not drop:
            continue
        if who.startswith("country:"):
            iso = who.split(":", 1)[1]
            r = c.get(iso)
            if not r or not r.get("sources"):
                continue
            if not full_cover:
                print(f"[skip partial] {who}: {len(verdicts)} verdicts for {len(r['sources'])} sources")
                continue
            drop2, fkeep, needs = prunable(r["sources"], verdicts)
            before = len(r["sources"])
            r["sources"] = [s for s in r["sources"] if url_of(s) not in drop2]
            pruned_urls += before - len(r["sources"])
            if needs:
                research_needed[who] = {"why": f"{len(r['sources'])} usable sources remain ({len(fkeep)} weakest kept as floor)", "false_claims": f["false_claims"]}
        else:
            iso, name = who.split("/", 1)
            sids = [sid for sid, r in a.items() if r.get("iso3") == iso and r.get("name") == name]
            for sid in sids[:1]:
                r = a[sid]
                if not r.get("sources"):
                    continue
                if not full_cover:
                    print(f"[skip partial] {who}: verdicts cover {len(verdicts)}/{len(r['sources'])}")
                    continue
                drop2, fkeep, needs = prunable(r["sources"], verdicts)
                before = len(r["sources"])
                r["sources"] = [s for s in r["sources"] if url_of(s) not in drop2]
                pruned_urls += before - len(r["sources"])
                if needs:
                    research_needed[who] = {"why": f"{len(r['sources'])} usable sources remain ({len(fkeep)} weakest kept as floor)", "false_claims": f["false_claims"]}
    if apply:
        json.dump(findings, open(ROOT / "data/relevance_findings.json", "w"),
                  ensure_ascii=False, indent=1)
        json.dump(research_needed, open(ROOT / "data/research_needed.json", "w"),
                  ensure_ascii=False, indent=1)
        print(f"research-needed queue: {len(research_needed)} jurisdictions")
        json.dump(research_needed, open(ROOT / "data/research_needed.json", "w"),
                  ensure_ascii=False, indent=1)
        tmp = ROOT / "data/countries.json.tmp"
        tmp.write_text(json.dumps(c, ensure_ascii=False, indent=1))
        tmp.replace(ROOT / "data/countries.json")
        tmp = ROOT / "data/admin1.json.tmp"
        tmp.write_text(json.dumps(a, ensure_ascii=False, indent=1))
        tmp.replace(ROOT / "data/admin1.json")
        print(f"applied: {pruned_urls} source links pruned; findings -> data/relevance_findings.json")
    else:
        print(f"plan only: {len(res)} jurisdiction results, "
              f"{sum(len(f['pruned']) for f in findings.values())} urls would drop")
    return 0

if __name__ == "__main__":
    sys.exit(main())
