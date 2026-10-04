#!/usr/bin/env python3
"""Blind-gate remediation pass (LANE_SPECS rule 7b/7e/7f fixed vocabulary).

Applies the prescribed substitutions to blind fields of records that FAIL the
blind gate, so blind mirrors stop leaking identity. Targets ONLY the blind
fields (blindSummary/blindTangential/blindLocalsOnly/blindOutOfScope/
blindSourceSummaries); visible fields and scores are untouched.

Design: phrase-level mappings first (so "Southeast Asian federation" collapses
to "nation" instead of leaving "Southeast nation"), then token mappings, then
a state-token walk that converts leaking bare "state" to the literal
"state/province" using the SAME per-token context rules as check_blind.py's
_state_leak(), preserving possessives.

Usage:
  python3 tools/fix_blind_gate.py --dry      (report only)
  python3 tools/fix_blind_gate.py            (write data/countries.json + admin1.json)
"""
import json, re, sys
from pathlib import Path
import importlib.util
ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('cb', ROOT/'tools/check_blind.py')
cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)

# Phrase-level first. Order matters: longest/specific first.
PHRASES = [
    (r"(?:large\s+)?federal\s+republic", "nation"),
    (r"(?:large\s+)?Federal\s+Republic", "nation"),
    (r"(?:federal\s+service\s+state)", "state/province"),
    (r"Southeast\s+Asian\s+(?:federation|republic|nation)", "nation"),
    (r"Southeast\s+Asian", ""),
    (r"North\s+Atlantic\s+(?:island\s+)?settlement", "settlement"),
    (r"North\s+Atlantic\s+(?:island\s+)?(?:territory|dependenc\w*)\b", "state/province"),
    (r"South\s+Atlantic\s+(?:island\s+)?settlement", "settlement"),
    (r"South\s+Pacific\s+overseas\s+collectivity\b", "external collectivity"),
    (r"South\s+Pacific\s+dependencies\b", "external state/province"),
    (r"world's\s+largest\s+island\b", "world's largest state/province"),
    (r"A\s+North\s+state/province\b", "A state/province"),
    (r"\bSouth\s+external\s+collectivity\b", "external collectivity"),
    (r"three-?island\s+South\s+Atlantic\s+state/province", "state/province"),
    (r"(?:small\s+)?self-governing\s+island\s+state/province", "self-governing state/province"),
    (r"in\s+an\s+off\s+a\s+northwestern\s+coast", "off a northwestern coast"),
    (r"in\s+an\s+off\s+a\s+(?:distant\s+)?coast", "off a distant coast"),
    (r"in an off a", "off a"),
    (r"state/province\s+penal\s+code", "state/province's penal code"),
    (r"state/province\s+religious\s+enactments", "state/province's religious enactments"),
    (r"the\s+most\s+populous\s+of\s+a\s+nation", "the most populous region of a nation"),
    (r"an?\s+(?:osmekio|island)\s+archipelago", ""),
    (r"East\s+Asian\s+(?:federation|republic|nation)", "nation"),
    (r"West\s+African\s+(?:federation|republic|nation)", "nation"),
    (r"South\s+American\s+(?:state|territory|nation)", "nation"),
    (r"Western\s+European\s+state(?:'s)?", "nation"),
    (r"Indian\s+Ocean\s+(?:overseas\s+)?(?:department|collectivity|territory)", "state/province"),
    (r"Indian\s+Ocean", ""),
    (r"\bin\s+the\s*(?=[,:;.]|$)", ""),
    (r"\bof\s+a\s+state/province\s+in\s+the\b", "of a state/province"),
    (r"\bOverseas\s+(?:department|collectivity|territory)\b", "state/province"),
    (r"\b(federal|Federal)\s+(capital|Courts|courts)\b", r"national \2"),
    (r"\b(republic|Republic|kingdom|Kingdom|commonwealth|Commonwealth|empire|Empire)\b", "nation"),
    (r"\b(federal|Federal|federation|Federation)\b", "national"),
    (r"\b(federally|Federally)\b", "nationally"),
    (r"\b(territories|Territories|territory|Territory)\b", "state/province"),
    (r"\b(dependencies|Dependencies|dependency|Dependency)\b", "state/province"),
    (r"\bterritorial\b", "jurisdictional"),
    (r"\b(overseas|Overseas)\b", "external"),
    (r"\b(colonial|Colonial)\b", "historic"),
    (r"\b(colonisation|colonization|Colonisation|Colonization)\b", "historic period"),
    (r"\battorney\s+general\b", "top government lawyer"),
    (r"\bAttorney\s+General\b", "top government lawyer"),
]
DROP = [
    "Atlantic", "Pacific", "Caribbean", "South American", "European", "Asian",
    "African", "Oceanian", "Western", "islander", "Islander", "islands",
    "Islands", "island", "Island", "archipelago", "Archipelago", "atolls",
    "Atolls", "isles", "Isles",
]

def _fix_text(t):
    if not t:
        return t
    for pat, repl in PHRASES:
        t = re.sub(pat, repl, t)
    for w in DROP:
        t = re.sub(r'(?<![A-Za-z])' + re.escape(w) + r'(?![A-Za-z])', '', t)
    # second PHRASES pass: drops create artifacts like "in an off a"
    for pat, repl in PHRASES:
        t = re.sub(pat, repl, t)
    # Possessive preservation: "state's" / "territory's" -> "state/province's"
    t = re.sub(r"\bstate/province(?:\u2019|')s\b", "state/province", t)
    t = re.sub(r"\bstates/provinces\b", "state/province", t)
    t = _fix_state_tokens(t)
    # cleanup
    t = re.sub(r'\s{2,}', ' ', t)
    t = re.sub(r'\s+([,.;:])', r'\1', t)
    t = re.sub(r'\ba\s+a\b', 'a', t)
    t = re.sub(r'\bthe\s+the\b', 'the', t)
    t = re.sub(r'\bof\s+of\b', 'of', t)
    t = re.sub(r'\ban?\s+state/province\s+of\s+a\s+state/province\b',
               'a state/province of a nation', t, flags=re.I)
    # an/a agreement for stranded words after drops (vowel-initial nouns only)
    t = re.sub(r'\b(an?)\s+(?!state/province|union|European|ensuring|hour|one\b|honest|honour|heir|useful|university|uniform|unique|ultra)([A-Za-z]+)\b',
               lambda m: ("an " if m.group(2)[0].lower() in 'aeiou' else "a ") + m.group(2),
               t, flags=re.I)
    t = re.sub(r'\(\s*\)', '', t)
    return t.strip()

def _fix_state_tokens(t):
    """Convert leaking bare 'state'/'state's' to 'state/province' (possessive kept).
    Same context rules as cb._state_leak so governmental-idiom and parent-
    referent uses stay untouched."""
    out = []
    last = 0
    for m in cb._STATE_RE.finditer(t):
        s, e = m.start(), m.end()
        seg = t[max(0, s - 35):e + 35].lower()
        ok = ('state/province' in seg or 'state / province' in seg)
        if not ok:
            after = re.match(r'(?:\s+|\s*[-:]\s*)([A-Za-z]+)', t[e:])
            if after and after.group(1).lower() in cb._STATE_OK_AFTER:
                ok = True
        if not ok:
            after2 = re.match(r"\s*(?:'|\u2019)?s\s+([A-Za-z]+)", t[e:])
            if after2 and after2.group(1).lower() in cb._STATE_OK_AFTER:
                ok = True
        if not ok:
            head = t[max(0, s - 30):e]
            if re.search(r"(?:encompassing|administering|metropolitan|unitary|partner|"
                         r"neighbouring|federal|sovereign|central|national|parent)\s+"
                         r"state(?:'|\u2019)?s?$", head, re.I) or \
               re.search(r"\bthe\s+state(?:'|\u2019)?s?$", head, re.I):
                ok = True
        if ok:
            continue
        out.append(t[last:s])
        p = t[s:e]
        if p.endswith(("'s", "\u2019s")):
            out.append("state/province's")
        else:
            out.append("state/province")
        last = e
    out.append(t[last:])
    return ''.join(out)

def _field_map(rec, who):
    ch = {}
    for bf in ('blindSummary', 'blindTangential', 'blindLocalsOnly', 'blindOutOfScope'):
        if str(rec.get(bf) or ''):
            ch[bf] = _fix_text(str(rec[bf]))
    bss = rec.get('blindSourceSummaries') or []
    ch['blindSourceSummaries'] = [_fix_text(str(x)) for x in bss]
    return ch

def main():
    dry = '--dry' in sys.argv
    C = json.load(open(ROOT/'data/countries.json'))
    A = json.load(open(ROOT/'data/admin1.json'))
    touched = 0
    for k, r in C.items():
        if cb.check(r, k):
            continue
        ch = _field_map(r, 'country:' + k)
        if dry:
            print('country:' + k)
        else:
            for f, v in ch.items():
                r[f] = v
        touched += 1
    for r in A.values():
        who = f"{r['iso3']}/{r['name']}"
        if not r.get('dossier') or cb.check(r, who):
            continue
        ch = _field_map(r, who)
        if dry:
            print(who)
        else:
            for f, v in ch.items():
                r[f] = v
        touched += 1
    if not dry:
        json.dump(C, open(ROOT/'data/countries.json', 'w'), ensure_ascii=False, indent=1)
        json.dump(A, open(ROOT/'data/admin1.json', 'w'), ensure_ascii=False, indent=1)
    print(f"touched {touched} records" + (" (dry)" if dry else ""))

if __name__ == '__main__':
    main()