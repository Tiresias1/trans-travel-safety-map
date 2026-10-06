#!/usr/bin/env python3
"""Build per-record REWORK inputs: current summary + surviving source claims +
audit findings + freshness facts, assembled server-side from files the lanes
already produced (results files are clean of narrative). Each batch file lists
<=10 records as {who, name, current_summary, sources:[{url,title,claim}],
flags:[false_claim|needs_search strings], freshness:{status,fact,evidence}}.
Usage: python3 tools/make_rework_batches.py [--per 10] [--out N] [--only ...]
"""
import json, sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
q = ROOT/'data/staleness_queue.json'
C = json.load(open(ROOT/'data/countries.json'))
A = json.load(open(ROOT/'data/admin1.json'))
RES = ROOT/'data/relevance_results'; FR = ROOT/'data/freshness'
def url_meta(u):
    try:
        m = json.load(open(ROOT/'data/source_manifest.json'))
        return m.get(u or '', {})
    except Exception: return {}
def build(who):
    if who.startswith('country:'):
        iso = who[8:]; r = C.get(iso)
        if not r: return None
        name, summ, srcs = r['name'], r.get('summary',''), r.get('sources') or []
    elif '/' in who:
        iso, nm = who.split('/',1)
        r = next((x for x in A.values() if x.get('iso3')==iso and x.get('name')==nm), None)
        if not r: return None
        name, summ, srcs = nm, r.get('summary',''), r.get('sources') or []
    else: return None
    res_f = RES / (who.replace('/','_').replace(':','_')+'.json')
    d = json.load(open(res_f)) if res_f.exists() else {}
    fresh = {"status":"unaudited"}
    if FR.exists():
        for f in FR.glob('*.json'):
            try:
                for x in json.load(open(f)).get('results', []):
                    if x.get('who') == who: fresh = x
            except Exception: pass
    # LANE_SPECS rule 9: freshness facts reaching rework lanes must be free of
    # pipeline jargon — status/rev metadata never appears in prose (the fault
    # that shipped "SUPERSEDED by freshness (rev ...)" into claims).
    fact = str(fresh.get('fact') or '')
    fact = re.sub(r"SUPERSEDED by freshness\s*\(rev\s*[\d-]+\)\s*:?\s*", "", fact, flags=re.I)
    fact = re.sub(r"per freshness\b", "", fact, flags=re.I)
    fact = re.sub(r"\(rev\s*[\d-]+\)", "", fact)
    fact = re.sub(r"\s{2,}", " ", fact).strip()
    fresh['fact'] = fact
    # same for the claim text going into the batch (rule 9 + rule 2 history)
    def clean_claim(s):
        if not isinstance(s, str): return s
        s = re.sub(r"SUPERSEDED by freshness\s*\(rev\s*[\d-]+\)\s*:?\s*", "", s, flags=re.I)
        s = re.sub(r"SUPERSEDED per resolved review\s*:?\s*", "", s, flags=re.I)
        s = re.sub(r"\(rev\s*[\d-]+\)", "", s)
        s = re.sub(r"\s{2,}", " ", s)
        return s.strip() or None
    return {"who": who, "name": name, "current_summary": re.sub(r"<[^>]+>"," ",summ).strip(),
            "sources": [{"url": (s.get('url') if isinstance(s,dict) else s),
                         "claim": clean_claim(s.get('summary')) if isinstance(s,dict) or isinstance(s,str) else None}
                        for s in srcs],
            "flags": (d.get('false_claims') or [])[:8] + (d.get('needs_search') or [])[:4],
            "freshness": {k: fresh.get(k) for k in ('status','fact','evidence')}}
def main():
    per = int(sys.argv[sys.argv.index('--per')+1]) if '--per' in sys.argv else 10
    only = set(a.upper() for a in sys.argv[sys.argv.index('--only')+1:]) if '--only' in sys.argv else None
    who = []
    for iso, r in C.items():
        if any(u in r.get('summary','') for u in ('re-anchored','derived from')) or f'country:{iso}' in json.load(open(ROOT/'data/research_needed.json')):
            who.append(f'country:{iso}')
    for sid, r in A.items():
        if not r.get('dossier'): continue
        rf = RES / (f"{r['iso3']}_{r['name']}.json")
        if rf.exists():
            d = json.load(open(rf))
            if d.get('false_claims') or d.get('needs_search') or d.get('mechanical') or \
               any(v.get('keep') is False for v in d.get('verdicts', [])):
                who.append(f"{r['iso3']}/{r['name']}")
    B = ROOT/'data/rework_batches'; B.mkdir(exist_ok=True)
    n = 0
    for i in range(0, len(who), per):
        recs = [x for x in (build(w) for w in who[i:i+per]) if x]
        if only and not any(r['who'].split('/')[0].split(':')[-1] in only for r in recs): 
            pass
        n += 1
        (B/f'r{n:03d}.json').write_text(json.dumps({"records": recs}, ensure_ascii=False, indent=1))
    print(f"rework batches: {n} covering {len(who)} flagged records")
if __name__ == '__main__': main()
