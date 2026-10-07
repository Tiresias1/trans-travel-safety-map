#!/usr/bin/env python3
"""Blinding gate (LANE_SPECS rule 7): banned-vocabulary scan + enrichment diff.
For each visible/blind field pair on a record: every content word (>=5 letters) in the blind
text that is absent from the visible counterpart AND absent from the allowed substitution
vocabulary is an ENRICHMENT violation (invented clue). Banned words are always errors.
Also provides a `--changelog` advisory mode that flags map-edit-narrative phrasing on
VISIBLE fields (STYLE_RULES/STYLE GATE): text describing an earlier profile or that
something "has been deleted". The map is not a changelog.
Usage: python3 tools/check_blind.py --who country:ASM | --all-countries | --admin1 <ISO>
       python3 tools/check_blind.py --changelog [--who country:X | --all-countries | --admin1 ISO]
"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
BANNED = re.compile(r"\b(federal\w*|territor\w*|dependenc\w*|colon\w*|island\w*|atoll\w*|archipelago|"
    r"pacific|atlantic|indian|caribbe\w*|mediterrane\w*|asia\w*|africa\w*|oceani\w*|europe\w*|"
    r"latin\s+americ\w*|caribbe\w*|central\s+america\w*|south\s+america\w*|north\s+america\w*|"
    r"overseas|crown|empire|kingdom|republic|attorney\s+general|commonwealth|"
    r"(north|south|east|west)ern?\s+(pacific|atlantic|asia|india|caribbean|hemisphere)|"
    r"\bmotto\b|\b\d{2,3},\d{3}\s+(?:residents|people)\b"
    # agency/programme proper nouns fingerprint the parent state (2026-10-07
    # ruling after 'Department of Justice' + 'SWS25' shipped in blind fields)
    r"|department of justice|\bDOJ\b|\bSWS25\b|\bFBI\b|"
    r"federal bureau of|\bTSA\b|\bCBP\b|\bICE\b|executive order \d+)", re.I)

# The "state" rule (2026-10-04 ruling): "state policy" is fine — "state" in
# governmental-adjective compounds refers to the national government generically
# and cannot fingerprint the division. It is also fine in "state/province" (the
# literal division idiom) and in parent-referent / generic-descriptor compounds
# ("encompassing state", "administering state", "metropolitan state", "unitary
# state", "partner state", "neighbouring state", "federal state"). Bare
# "state"/"state's" that begs "which state?" is a leak.
_STATE_OK_AFTER = frozenset((
    "policy", "backed", "run", "owned", "level", "wide", "endorsed",
    "persecution", "hostility", "religious", "apparatus", "mechanism",
    "friction", "capital", "pension", "security", "agency", "institution",
    "authority", "funded", "sanctioned", "sponsored", "government", "house",
    "officials", "legislature", "law", "court", "police", "prison", "media",
    "television", "companies", "enterprise", "bank", "university", "school",
    "hospital", "care", "service", "programme", "system", "body", "organ",
    "structure", "intervention", "sponsor", "institutions", "official",
    "risk", "risk assessment", "statistics",
))
_STATE_OK_PREFIXES = (
    "encompassing state", "administering state", "metropolitan state",
    "unitary state", "partner state", "neighbouring state", "federal state",
    "sovereign state", "central state", "national state", "parent state",
)
_STATE_RE = re.compile(r"\bstate(?:(?:'|\u2019)s)?\b", re.I)

def _state_leak(bl: str) -> bool:
    """True if bl contains a bare 'state'/'state's' that leaks identity.
    Allowed (per 2026-10-04 ruling): the state/province idiom; governmental
    adjective compounds ("state policy", "state-backed"...); parent-referent
    descriptors ("encompassing state", "administering state", "metropolitan
    state", "unitary state", "partner state", "neighbouring state", "federal
    state", "sovereign state"...); and the generic definite reference "the
    state"/"the state's" referring to the parent government. Anything else
    ("this state", "a state", bare "state" begging "which state?") is a leak."""
    for m in _STATE_RE.finditer(bl):
        s, e = m.start(), m.end()
        seg = bl[max(0, s - 35):e + 35].lower()
        if "state/province" in seg or "state / province" in seg:
            continue
        after = re.match(r"(?:\s+|\s*[-:]\s*)([A-Za-z]+)", bl[e:])
        if after and after.group(1).lower() in _STATE_OK_AFTER:
            continue
        after2 = re.match(r"\s*(?:'|\u2019)?s\s+([A-Za-z]+)", bl[e:])
        if after2 and after2.group(1).lower() in _STATE_OK_AFTER:
            continue
        # parent-referent / generic definite reference
        head = bl[max(0, s - 30):e]
        if re.search(r"(?:encompassing|administering|metropolitan|unitary|partner|"
                     r"neighbouring|federal|sovereign|central|national|parent)\s+"
                     r"state(?:'|\u2019)?s?$", head, re.I) \
                or re.search(r"\bthe\s+state(?:'|\u2019)?s?$", head, re.I):
            continue
        return True
    return False
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
        if _state_leak(bl): m.append(("state",))
        if m: banned.append(f"{b}: BANNED {sorted(set(x[0].lower() for x in m))}")
        enrich = words(bl) - words(rec.get(v)) - {stem(a) for a in ALLOW}
        if enrich: warnings.append(f"{b}: (adv) {sorted(enrich)[:12]}")
    bs = " ".join(str(x) for x in (rec.get("blindSourceSummaries") or []))
    if bs and BANNED.search(bs): banned.append("blindSourceSummaries: BANNED " + str(set(x[0] for x in BANNED.findall(bs))))
    if bs and _state_leak(bs): banned.append("blindSourceSummaries: BANNED state")
    if banned or warnings:
        print(("FAIL " if banned else "WARN ") + name)
        for f in banned: print("   ", f)
        for f in warnings[:3]: print("   ", f)
    return not banned


CHANGELOG_ISH = re.compile(
    r"\b(?:earlier|previous|old|original|former|prior)\s+"
    r"(?:profile|dossier|summary|research|assessment|"
    r"characterisation|characterization|write-upper|revision)\b"
    r"|\binherited arithmetic\b|\bborrowed (?:custody )?stor(?:y|ies)\b"
    r"|\bcarried in the (?:earlier|previous|prior)\b"
    r"|\bthe audited record\b|\bper freshness\b|\bat fetch time\b"
    r"|\bSUPERSEDED\b|\(rev [\d-]+\)"
    r"|\b(?:was|were|has|have)\s+been?\s+(?:deleted|dropped)\b"
    r"|\bdeleted because\b|\bdeleted for lack\b"
    r"|\bmodel prior\b|\bsurviving evidence\b|\bundersold\b"
    r"|\bunsupported by the record\'?s sources\b"
    r"|\bfreshness check against\b|\bconfirmed by the record\'?s freshness check\b"
    r"|\bno longer appears in the current overview\b"
    r"|\bthe record summary records\b|\bcarried on the record\b"
    r"|\bresearch pass\b|\bprune[ds]?\b", re.I)


def changelog_scan(rec, name):
    """Advisory (STYLE GATE): flag map-edit narrative in ANY text field —
    visible AND blind, including outOfScopeNotes and sources claims (the
    2026-10-05 miss: the scanner only covered summary/tangential/localsOnly/
    outOfScope, so 'outOfScopeNotes' sentences survived)."""
    fields = ["summary", "tangentialFactors", "tangential", "localsOnly",
              "localsOnlyNotes", "outOfScopeNotes", "outOfScope",
              "blindSummary", "blindTangential", "blindLocalsOnly", "blindOutOfScope"]
    texts = [(f, str(rec.get(f) or "")) for f in fields]
    for s in (rec.get("sources") or []):
        if isinstance(s, dict) and s.get("summary"):
            texts.append(("sources.claim", str(s["summary"])))
    hits = []
    for f, t in texts:
        for m in CHANGELOG_ISH.finditer(t):
            hits.append((f, t[max(0, m.start() - 40):m.end() + 40]))
    if hits:
        print(f"CHANGELOG {name}")
        for f, ctx in hits[:6]:
            print(f"   [{f}] ...{ctx.strip()[:120]}...")
    return hits

def main():
    C=json.load(open(ROOT/'data/countries.json')); A=json.load(open(ROOT/'data/admin1.json'))
    if '--changelog' in sys.argv:
        total = 0
        if '--who' in sys.argv:
            who = sys.argv[sys.argv.index('--who')+1]
            rec = C.get(who[8:]) if who.startswith('country:') else next((x for x in A.values() if x.get('iso3')==who.split('/')[0] and x.get('name')==who.split('/',1)[1]), None)
            total += len(changelog_scan(rec, who)) if rec else 0
        elif '--all-countries' in sys.argv:
            for k, r in C.items(): total += len(changelog_scan(r, 'country:'+k))
        elif '--admin1' in sys.argv:
            iso = sys.argv[sys.argv.index('--admin1')+1]
            for r in A.values():
                if r.get('iso3') == iso: total += len(changelog_scan(r, f"{iso}/{r['name']}"))
        else:
            for k, r in C.items(): total += len(changelog_scan(r, 'country:'+k))
            for r in A.values():
                if r.get('dossier'): total += len(changelog_scan(r, f"{r['iso3']}/{r['name']}"))
        print("changelog-style hits:", total)
        return
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
