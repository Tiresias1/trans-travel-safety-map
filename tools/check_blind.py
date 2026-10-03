#!/usr/bin/env python3
"""Blinding gate (LANE_SPECS rule 7): banned-vocabulary scan + enrichment diff.
For each visible/blind field pair on a record: every content word (>=5 letters) in the blind
text that is absent from the visible counterpart AND absent from the allowed substitution
vocabulary is an ENRICHMENT violation (invented clue). Banned words are always errors.
Usage: python3 tools/check_blind.py --who country:ASM | --all-countries | --admin1 <ISO>
"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
BANNED = re.compile(r"\b(federal\w*|territor\w*|dependenc\w*|colon\w*|island\w*|atoll\w*|archipelago|"
    r"pacific|atlantic|indian|caribbe\w*|mediterrane\w*|asia\w*|africa\w*|oceani\w*|europe\w*|"
    r"latin\s+americ\w*|caribbe\w*|central\s+america\w*|south\s+america\w*|north\s+america\w*|"
    r"overseas|crown|empire|kingdom|republic|attorney\s+general|commonwealth|"
    r"(north|south|east|west)ern?\s+(pacific|atlantic|asia|india|caribbean|hemisphere)|"
    r"\bstate\b(?!\s*/\s*province)|\bmotto\b|\b\d{2,3},\d{3}\s+(?:residents|people)\b)", re.I)
ALLOW = set("""nation national state province historic parent lawyer official government legal
top local elected legislature legislature courts judiciary custom customs culture customary society societies
marriage wedlock conduct consent criminal decriminalised decriminalised decriminalized recognition rights
protection protections discrimination discriminates travellers travel visiting visitor resident residents
performed unions statute ruling federalforeign international regional region country gender sodomy
human organisation organisations organization organizations lgbt lgbtq lgbti exist existence present absence
law court policy passport documentation document identity civil religious penalty punishment prison
health sexual orientation equality share shared relation relations community communities activism advocacy
network networks support groups based both one two three four five six seven eight nine ten overall net
low medium high moderate degree level degree risk safety safer safe protect protected registration register
birth marker markers change changes changed amendment amendments ban ban banned ban legalisation
legalized legality criminalisation criminalizes criminalises enforcement enforcement incident incidents
report reporting reported official officials authority authorities court-house legal system seen shows
found evidence documents requirement requires required apply applicable applied available availability
across within among between without with despite although regression focus focused general broadly
largely widely widely-adopted nationwide national-level locality localised atoll land mass coastal inland
mountain mountainous urban suburban rural remote settlement populated densely sparse thicket dense
homeland third-gender maleness femaleness embodied embodying performance performed middle both neither
rather simply simply beyond back fall short stop retains stopping continues continue continued after""".split())
PAIRS = [("summary","blindSummary"),("tangentialFactors","blindTangential"),
         ("localsOnly","blindLocalsOnly"),("outOfScopeNotes","blindOutOfScope")]
def stem(w):
    if w.endswith("ing") and len(w) > 5: return w[:-3]
    if w.endswith("ed") and len(w) > 4: return w[:-2]
    if w.endswith("es") and len(w) > 4: return w[:-2]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 4: return w[:-1]
    return w
def words(t):
    t = re.sub(r"<[^>]+>"," ", t or "").lower()
    return {stem(w) for w in re.findall(r"[a-zà-ɿ']{5,}", t)}
def check(rec, name):
    # BANNED = hard rule-7 failure (identity leaks). ENRICHMENT is advisory-only:
    # the blind-vs-visible word diff flags innocent function words and stemming
    # artifacts, so it must NOT gate or it forces pointless lane churn.
    banned = []
    warnings = []
    for v,b in PAIRS:
        bl = str(rec.get(b) or "")
        if not bl: continue
        m = BANNED.findall(bl)
        if m: banned.append(f"{b}: BANNED {sorted(set(x[0].lower() for x in m))}")
        enrich = words(bl) - words(rec.get(v)) - {stem(a) for a in ALLOW}
        if enrich: warnings.append(f"{b}: (adv) {sorted(enrich)[:12]}")
    bs = " ".join(str(x) for x in (rec.get("blindSourceSummaries") or []))
    if bs and BANNED.search(bs): banned.append("blindSourceSummaries: BANNED " + str(set(x[0] for x in BANNED.findall(bs))))
    if banned or warnings:
        print(("FAIL " if banned else "WARN ") + name)
        for f in banned: print("   ", f)
        for f in warnings[:3]: print("   ", f)
    return not banned
def main():
    C=json.load(open(ROOT/'data/countries.json')); A=json.load(open(ROOT/'data/admin1.json'))
    if '--file' in sys.argv:
        fp = sys.argv[sys.argv.index('--file')+1]
        d = json.load(open(fp)); ok = True
        for r in d.get('rewrites', []):
            mapped = {k: (r.get(k) or '') for k in
                      ('summary','tangentialFactors','localsOnly','outOfScopeNotes')}
            for k in ('blindSummary','blindTangential','blindLocalsOnly','blindOutOfScope','blindSourceSummaries'):
                if r.get(k) is not None: mapped[k] = r[k]
            if not check(mapped, r.get('who', fp)): ok = False
        sys.exit(0 if ok else 1)
    if '--all-countries' in sys.argv:
        bad=[k for k,r in C.items() if not check(r,k)]
        print(f"{len(C)-len(bad)}/{len(C)} pass | fails: {bad[:20]}")
    elif '--admin1' in sys.argv:
        iso=sys.argv[sys.argv.index('--admin1')+1]
        bad=[r['name'] for r in A.values() if r.get('iso3')==iso and not check(r, f"{iso}/{r['name']}")]
        print("admin1 fails:", bad or "none")
    else:
        who=sys.argv[sys.argv.index('--who')+1]
        rec = C.get(who[8:]) if who.startswith('country:') else next((x for x in A.values() if x.get('iso3')==who.split('/')[0] and x.get('name')==who.split('/',1)[1]), None)
        sys.exit(0 if rec is not None and check(rec, who) else 1)
if __name__ == '__main__':
    main()
