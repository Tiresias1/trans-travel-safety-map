#!/usr/bin/env python3
"""Validate anonymised blinded ADM1 region records (v2, countries-schema).

Operates on files in data/blind_outputs/adm1/<id>.json with schema:
  {id, blindSummary, blindSourceSummaries:[...], blindOutOfScope?,
   blindLocalsOnly?, blindTangential?}

A region is eligible for blinding once apply_adm1_research.py has marked it
researched2. Merging writes the blind fields onto the admin1 record and marks
blindV2. --queue prints eligible-but-unblinded ids; --report prints progress.

Hard fails (over the concatenation of ALL blind fields): own/sibling unit names,
parent-country aliases incl. per-country demonym/capital table, ~90 neighbour
demonyms, US-shorthand, subnational unit-type words outside 'state/province',
band labels, own-score digits, rank tokens, bill/statute numbers, and the
DIRECTIVE list (phrases that tell the rater how to vote: national baselines,
deviation/tier language, "most protective", "most dangerous", etc).
blindSourceSummaries must be 1:1 with sources; trio fields mirror the record's
scope fields (present iff present)."""
from __future__ import annotations
import argparse, json, re, sys, unicodedata
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

BANDS = ("low risk", "reduced risk", "elevated risk", "high risk",
         "do not travel", "do-not-travel")
RANK_RE = re.compile(r"\brank(?:ed|ing)?\s*#?\d|\bin#\d|#[1-9]\d*\b", re.I)
BILL_RES = [
    re.compile(r"\b(?:h\.?b\.?|s\.?b\.?|a\.?b\.?|h\.?j\.?r\.?|s\.?j\.?r\.?|h\.?c\.?|s\.?c\.?|c\.?s\.?sb\.?)\s*\.?\s*[-/]?\s*\d{1,4}\b", re.I),
    re.compile(r"\b(?:prop(?:osition)?|question|measure|issue|initiative|amendment|act|law|law no\.?|no\.|p\.?l\.?)\s+(?:no\.?\s+)?\d{1,4}\b", re.I),
    re.compile(r"\bi[-\s]\d{1,3}\b"),
    re.compile(r"\bsection\s+\d{2,}\b", re.I),
]
PARENT_CI = [r"united states", r"u\.s\.a?", r"usa\b", r"american", r"\bus\b(?!\.)",
             r"\bu\.s\.\b", r"the states\b", r"washington,? d\.?c\.?", r"\bd\.c\."]
ISO3_ALIASES = {
 "ITA": ["italian", "italy", "rome", "roma", "milan", "naples", "turin"],
 "CAN": ["canadian", "ottawa", "toronto", "vancouver", "calgary", "edmonton", "notwithstanding"],
 "MEX": ["mexican", "mexico", "mexico city", "cdmx", "guadalajara", "monterrey"],
 "IND": ["indian", "new delhi", "delhi", "mumbai"],
 "BRA": ["brazilian", "brasilia", "são paulo", "rio de janeiro"],
 "DEU": ["german", "germany", "berlin", "munich", "frankfurt"],
 "ESP": ["spanish", "spain", "madrid", "barcelona"],
 "ARG": ["argentine", "argentina", "buenos aires"],
 "POL": ["polish", "poland", "warsaw", "krakow"],
 "NGA": ["nigerian", "nigeria", "abuja", "lagos"],
 "IDN": ["indonesian", "indonesia", "jakarta"],
 "ZAF": ["south african", "south africa", "pretoria", "johannesburg", "cape town"],
 "FRA": ["french", "france", "paris"],
 "RUS": ["russian", "russia", "moscow", "kremlin", "siberia"],
 "PHL": ["filipino", "philippines", "manila"],
 "KOR": ["korean", "korea", "seoul"],
 "CHL": ["chilean", "chile", "santiago"],
 "AUS": ["australian", "australia", "canberra", "sydney", "melbourne"],
 "MYS": ["malaysian", "malaysia", "kuala lumpur"],
 "PER": ["peruvian", "peru", "lima"],
 "COL": ["colombian", "colombia", "bogota", "bogotá"],
 "TUR": ["turkish", "turkey", "ankara", "istanbul"],
 "USA": ["united states", "u.s.", "usa", "american", "washington"],
 "GBR": ["united kingdom", "britain", "british", "england", "scotland", "wales", "london"],
}
NEIGHBOR_WORDS = ["bangladeshi","bengali","assamese","myanmar","burmese","pakistani",
 "chinese","venezuelan","haitian","guatemalan","salvadoran","nicaraguan","honduran",
 "moroccan","algerian","egyptian","libyan","tunisian","mauritanian","senegalese",
 "malian","nigerien","chadian","sudanese","eritrean","ethiopian","somali","kenyan",
 "ugandan","rwandan","burundian","congolese","gabonese","cameroonian","central african",
 "south african","angolan","zambian","mozambican","botswanan","swazi","lesothan",
 "syrian","iraqi","iranian","georgian","armenian","azerbaijani","ukrainian","belarusian",
 "moldovan","german","austrian","swiss","dutch","belgian","italian","french","spanish",
 "portuguese","polish","czech","slovak","hungarian","romanian","bulgarian","croatian",
 "serbian","bosnian","slovenian","albanian","macedonian","montenegrin","greek","turkish",
 "kurdish","indonesian","malaysian","thai","papua new guinean","east timorese","timorese",
 "american","canadian","mexican","korean","japanese","filipino","chilean","peruvian",
 "bolivian","brazilian","argentine","argentinian","colombian","ecuadorian","uruguayan",
 "paraguayan","guyanese","surinamese","panamanian","costa rican","cuban","jamaican",
 "dominican","haitian","nigerian","ghanaian","ivorian","guinean","sierra leonean","liberian"]
SHORTHAND = [r"red[- ]states?", r"blue[- ]states?", r"purple[- ]states?",
             r"bible belt", r"deep south", r"new england", r"\bheartland\b",
             r"\bmaga\b", r"tea party", r"title ix",
             r"pacific northwest|mountain west|mason[- ]dixon|\bdixie\b"]
UNIT_TYPE = [r"oblast", r"krai", r"guberniya", r"voivodeship", r"prefectur",
             r"governorat", r"regency", r"departament", r"federal subject",
             r"\bprovinces?\b", r"\brepublics?\b"]
# Phrases that tell the comparator how to vote instead of letting it decide:
DIRECTIVE = [r"national (score|baseline|average|level)", r"country[- ]wide (average|level)",
             r"\bdeviation[s]?\b", r"\btier\b", r"(most|least) protective",
             r"worst[- ]law", r"\bharshest\b", r"\bsafest\b", r"material enough",
             r"score(?:d)? separately", r"well (below|above)", r"(above|below) the countr",
             r"than the (national|country)", r"red zone", r"on this map",
             r"reference point", r"most dangerous", r"relative to the national",
             r"compared with (a |the )?neighbouring state"]
ACRONYM_OK = {"UN", "WHO", "AIDS", "HIV", "LGBT", "LGBTQ", "LGBTQIA", "SOGI",
              "SOGIESC", "NGO", "NGOS", "UNDP", "ILO", "OSCE", "UPR", "ID",
              "II", "III", "IV", "V", "X", "CEDAW", "UPRs", "NOTE", "DPI", "ICU"}
SENT_RE = re.compile(r"(?:^|[.!?]\s+|</p>\s*|\A)\s*([A-Z][a-z]{2,})")
MONTH_OK = {"jan","feb","mar","apr","may","jun","jul","aug","sept","sep","oct","nov","dec",
            "january","february","march","april","june","july","august","september",
            "october","november","december","pride","page","for","safe","caution",
            "being","loading","very","unnatural","immodest","same","day","women","human",
            "rights","international","council","joint","statement","recognition"}

def strip_tags(s): return re.sub(r"<[^>]+>", " ", s)

def region_checks_v2(rec, blind_obj, siblings, parent_names):
    fails, warns = [], []
    parts = {}
    bs = str(blind_obj.get("blindSummary", "")).strip()
    if not bs:
        return ["blindSummary missing/empty"], []
    parts["blindSummary"] = bs
    srcs = rec.get("sources", [])
    bss = blind_obj.get("blindSourceSummaries")
    if not isinstance(bss, list) or len(bss) != len(srcs):
        fails.append(f"blindSourceSummaries must be array of len {len(srcs)}")
        bss = []
    for i, x in enumerate(bss):
        parts[f"src{i}"] = str(x)
    trio = [("outOfScopeNotes", "blindOutOfScope"),
            ("tangentialFactors", "blindTangential"),
            ("localsOnly", "blindLocalsOnly")]
    for src_f, bl_f in trio:
        has_src = bool(str(rec.get(src_f, "")).strip())
        has_bl = bool(str(blind_obj.get(bl_f, "")).strip())
        if has_src and not has_bl:
            fails.append(f"{bl_f} missing (source has {src_f})")
        if has_bl and not has_src:
            fails.append(f"{bl_f} present but source lacks {src_f}")
        if has_bl:
            parts[bl_f] = str(blind_obj[bl_f])
    # lengths
    src_len = len(strip_tags(str(rec.get("summary", ""))))
    if src_len and not (0.4 * src_len <= len(strip_tags(bs)) <= 2.2 * src_len):
        fails.append(f"blindSummary length {len(strip_tags(bs))} vs source {src_len}")
    for i, x in enumerate(bss):
        sl = len(str(srcs[i].get("summary", ""))) if isinstance(srcs[i], dict) else 0
        if sl and not (0.3 * sl <= len(str(x)) <= 2.5 * sl):
            fails.append(f"blindSourceSummaries[{i}] length {len(str(x))} vs source {sl}")
    blob = " ".join(parts.values())
    plain = strip_tags(blob)
    low = plain.lower()
    own = str(rec.get("name", ""))
    if own and re.search(rf"\b{re.escape(own)}\b", plain, re.I):
        fails.append(f"own unit name leaks: {own!r}")
    for nm in siblings:
        if nm == own or len(nm) < 4: continue
        if re.search(rf"\b{re.escape(nm)}\b", plain, re.I):
            fails.append(f"sibling unit name leaks: {nm!r}")
    for p in parent_names:
        if p and re.search(rf"\b{re.escape(p)}\b", plain, re.I):
            fails.append(f"parent-country name leaks: {p!r}")
    for pat in PARENT_CI:
        if re.search(pat, low):
            fails.append(f"parent alias leaks: {pat}")
    iso3 = str(rec.get("iso3", ""))
    for alias in ISO3_ALIASES.get(iso3, []):
        if re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", low):
            fails.append(f"parent demonym/capital leaks: {alias!r}")
    stripped = re.sub(r"(?:states?['\u2019]?s*|state['\u2019]?s)/(?:provinces?['\u2019]?s*|province['\u2019]?s*)", "", low)
    for ut in UNIT_TYPE:
        m = re.search(ut, stripped)
        if m:
            fails.append(f"subnational unit-type word leaks: {m.group(0)!r}")
    for nw in NEIGHBOR_WORDS:
        if re.search(r"(?<!\w)" + re.escape(nw) + r"(?!\w)", low):
            fails.append(f"neighbour-country word leaks: {nw!r}")
    for r in SHORTHAND:
        m = re.search(r, low)
        if m: fails.append(f"shorthand leaks: {m.group(0)!r}")
    for r in DIRECTIVE:
        m = re.search(r, low)
        if m: fails.append(f"directive-language leaks (let the rater decide): {m.group(0)!r}")
    for b in BANDS:
        if b in low: fails.append(f"band label leaks: {b!r}")
    if RANK_RE.search(plain): fails.append("rank-style token leaks")
    if re.search(r"[±]\s*0?\.\d", plain) or re.search(r"\([+\-]\s*0?\.\d+\)", plain):
        fails.append("deviation-space number leaks")
    for rr in BILL_RES:
        m = rr.search(plain)
        if m: fails.append(f"bill/statute number leaks: {m.group(0)!r}")
    s = rec.get("score")
    if isinstance(s, (int, float)):
        for form in (f"{s:.2f}", f"{s:.1f}", str(s)):
            if form and re.search(rf"(?<![\d.]){re.escape(form)}(?![\d])", plain):
                fails.append(f"own score leaks: {form!r}"); break
    sent_initial = {m.group(1) for m in SENT_RE.finditer(plain)}
    for tok in set(re.findall(r"\b[A-Z][a-z]{2,}\b", plain)):
        if tok.upper() == "NOTE": continue
        if tok.lower() in MONTH_OK or tok in sent_initial: continue
        warns.append(f"capitalised token to review: {tok!r}")
    for tok in set(re.findall(r"\b[A-Z]{2,}\b", plain)):
        if tok in ACRONYM_OK or tok == "NOTE":
            continue
        warns.append(f"all-caps acronym to review: {tok!r}")
    return fails, warns

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=str(ROOT / "data/blind_outputs/adm1"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--queue", action="store_true")
    ap.add_argument("--queue-limit", type=int, default=None)
    args = ap.parse_args()
    admin1 = json.loads((ROOT / "data" / "admin1.json").read_text(encoding="utf-8"))
    countries = json.loads((ROOT / "data" / "countries.json").read_text(encoding="utf-8"))
    dossier = {k: v for k, v in admin1.items() if v.get("dossier")}

    if args.report:
        res = sum(1 for v in dossier.values() if v.get("researched2"))
        bl = sum(1 for v in dossier.values() if v.get("blindV2"))
        print(f"dossier: {len(dossier)} | researched2: {res} | blindV2: {bl}")
        return 0
    if args.queue:
        need = [k for k, v in dossier.items() if v.get("researched2") and not v.get("blindV2")]
        for k in (need[:args.queue_limit] if args.queue_limit else need):
            print(k)
        return 0

    inp = Path(args.inp)
    files = sorted(inp.glob("*.json"))
    ok = fails_total = 0
    for f in files:
        obj = json.loads(f.read_text(encoding="utf-8"))
        rid = obj.get("id") or f.stem
        rec = dossier.get(rid)
        if rec is None:
            print(f"[SKIP] {f.name}: not a dossier id"); continue
        if not rec.get("researched2"):
            print(f"[SKIP] {rec.get('name')}: not researched yet"); continue
        iso3 = rec.get("iso3")
        siblings = [v.get("name", "") for _, v in admin1.items() if v.get("iso3") == iso3]
        parent = countries.get(iso3) or {}
        parent_names = [parent.get("name", "")] if parent.get("name") else []
        fails, warns = region_checks_v2(rec, obj, siblings, parent_names)
        if fails:
            print(f"\n[FAIL] {rec.get('name')} ({rid})")
            for x in dict.fromkeys(fails): print("   -", x)
            fails_total += 1
            continue
        if warns:
            uniq = list(dict.fromkeys(warns))
            print(f"\n[WARN] {rec.get('name')} ({rid}): {len(uniq)}")
            for w in uniq[:12]: print("   ·", w)
        if not args.dry_run:
            rec["blindSummary"] = obj["blindSummary"]
            rec["blindSourceSummaries"] = obj["blindSourceSummaries"]
            for src_f, bl_f in [("outOfScopeNotes","blindOutOfScope"),
                                ("tangentialFactors","blindTangential"),
                                ("localsOnly","blindLocalsOnly")]:
                if obj.get(bl_f): rec[bl_f] = obj[bl_f]
                else: rec.pop(bl_f, None)
            rec["blindV2"] = True
        ok += 1
    if not args.dry_run and ok:
        tmp = Path(str(ROOT / "data" / "admin1.json") + ".tmp")
        tmp.write_text(json.dumps(admin1, indent=1, ensure_ascii=False), encoding="utf-8")
        tmp.replace(ROOT / "data" / "admin1.json")
    print(f"\nvalidated OK: {ok} · failed: {fails_total}"
          + (" · dry run, nothing written" if args.dry_run else f" · wrote {ok} blinded records (v2)"))
    return 0 if fails_total == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
