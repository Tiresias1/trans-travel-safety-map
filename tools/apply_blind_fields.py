#!/usr/bin/env python3
"""Validate and merge blind-anonymised fields into data/countries.json.

Accepts the anonymising model's output as either:
  * a JSONL file, one object per line: {"iso": "WSM", "blindSummary": ..., ...}
  * a directory of <ISO>.json files, each holding the blind fields (iso optional)

Every record is validated before it is written. A record that fails is skipped and
reported; the run continues.

Checks
------
hard fail (record skipped):
  * required field missing or empty
  * `blindSourceSummaries` is not a list, or its length != len(sources)
  * **identity leak**: the record's own name, its ISO3, any of its source-URL domains,
    or the name of ANY of the 233 jurisdictions appears in the blind text
  * **demonym leak**: a capitalised token that extends a jurisdiction name
    ("Samoan", "Fijian", "Chinese", "Israeli", ...)
  * **region leak**: continent / region / bloc terms ("European", "Pacific", "Caribbean",
    "Gulf", "Balkan", "African", ...) — these are the primary stereotype vector
  * blind text outside 40–200% of the source field's length (over-scrubbing or padding)

warning (does not block):
  * capitalised proper-noun tokens not on the generic allowlist — printed for human review
  * source URLs still present

Usage:
    python3 tools/apply_blind_fields.py --in data/blind_outputs.jsonl --dry-run
    python3 tools/apply_blind_fields.py --in data/blind_outputs.jsonl
    python3 tools/apply_blind_fields.py --in data/blind_outputs/ --report
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent

REQUIRED = ("blindSummary", "blindOutOfScope", "blindSourceSummaries")
OPTIONAL = ("blindLocalsOnly", "blindTangential")
# blind field -> source field it must correspond to
PAIRS = (("blindSummary", "summary"),
         ("blindOutOfScope", "outOfScopeNotes"),
         ("blindLocalsOnly", "localsOnly"),
         ("blindTangential", "tangentialFactors"))

REGION_TERMS = {
    "europe", "european", "europeans", "eu", "africa", "african", "africans",
    "sub-saharan", "asia", "asian", "asiatic", "americas", "american", "americans",
    "north america", "north american", "latin america", "latin american",
    "south america", "south american", "central america", "central american",
    "caribbean", "pacific", "oceania", "oceanian", "polynesia", "polynesian",
    "melanesia", "melanesian", "micronesia", "micronesian", "balkans", "balkan",
    "caucasus", "caucasian", "nordic", "scandinavia", "scandinavian",
    "middle east", "middle eastern", "mena", "gulf", "arab", "arabian",
    "western", "eastern", "northern", "southern", "global south", "global north",
    "iberian", "mediterranean", "andean", "amazonian", "sahel", "maghreb",
    "levant", "levantine", "british", "french", "dutch", "spanish", "portuguese",
    "german", "italian", "russian", "chinese", "indian", "japanese", "korean",
    "turkish", "iranian", "iraqi", "israeli", "saudi", "emirati", "qatari",
    "kuwaiti", "omani", "bahraini", "jordanian", "lebanese", "syrian", "yemeni",
    "egyptian", "libyan", "tunisian", "algerian", "moroccan", "nigerian",
    "kenyan", "ugandan", "tanzanian", "ethiopian", "somali", "sudanese",
    "congolese", "angolan", "mozambican", "zambian", "zimbabwean", "botswanan",
    "namibian", "south african", "ghanaian", "senegalese", "malian", "chadian",
    "gabonese", "cameroonian", "malawian", "burundian", "rwandan", "liberian",
    "sierra leonean", "togolese", "beninese", "guinean", "eritrean", "djiboutian",
    "comorian", "mauritian", "seychellois", "maldivian", "nepali", "bhutanese",
    "bangladeshi", "sri lankan", "burmese", "thai", "cambodian", "laotian",
    "vietnamese", "malaysian", "singaporean", "indonesian", "filipino",
    "australian", "new zealand", "kiwi", "chilean", "argentine", "brazilian",
    "peruvian", "ecuadorian", "colombian", "venezuelan", "bolivian", "paraguayan",
    "uruguayan", "guyanese", "surinamese", "cuban", "jamaican", "haitian",
    "dominican", "puerto rican", "belizean", "salvadoran", "guatemalan",
    "honduran", "nicaraguan", "costa rican", "panamanian", "mexican", "canadian",
    "icelandic", "irish", "scottish", "welsh", "english", "polish", "czech",
    "slovak", "hungarian", "romanian", "bulgarian", "serbian", "croatian",
    "bosnian", "slovenian", "macedonian", "albanian", "kosovar", "greek",
    "cypriot", "maltese", "ukrainian", "belarusian", "moldovan", "lithuanian",
    "latvian", "estonian", "finnish", "swedish", "norwegian", "danish", "swiss",
    "austrian", "belgian", "luxembourgish", "taiwanese", "mongolian",
    "kazakh", "kyrgyz", "tajik", "turkmen", "uzbek", "azerbaijani", "armenian",
    "georgian", "palestinian", "kurdish", "samoan", "tongan", "fijian", "niuean",
    "cook islands", "marshallese", "palauan", "nauruan", "tuvaluan", "kiribati",
    "solomon islands", "papua new guinean", "timorese",
}
REGION_TERMS = {t.strip() for t in REGION_TERMS}

# capitalised tokens that are fine and should not be flagged for review
GENERIC_ALLOWED = {
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "JSON", "UN", "UPR",
    "WHO", "ICD", "HIV", "AIDS", "NGO", "NGOs", "LGBT", "LGBTQ", "LGBTIQ",
    "LGBTQIA", "SOGI", "SOGIESC", "GI", "SO", "X", "The", "In", "However",
    "Although", "Since", "Under", "Following", "After", "Despite", "While",
    "Both", "This", "These", "There", "It", "Its", "No", "Not", "Only",
    "Court", "Courts", "Constitution", "Constitutional", "Supreme", "High",
    "Penal", "Code", "Act", "Law", "Laws", "Article", "Section", "Amendment",
    "Bill", "Decree", "Ordinance", "Statute", "Parliament", "Congress",
    "Senate", "Assembly", "Ministry", "Minister", "Government", "State",
    "Police", "Prison", "Prisons", "Detention", "Military", "Army", "Navy",
    "Air", "Force", "Forces", "Security", "Intelligence", "Judiciary",
    "Attorney", "General", "President", "Prime", "King", "Queen", "Sultan",
    "Emir", "Chief", "Chiefs", "Council", "Councils", "Commission",
    "Committee", "Committees", "Ombuds", "Ombudsperson", "Embassy",
    "Consulate", "Border", "Immigration", "Customs", "Registry", "Registry",
    "Health", "Hospital", "Hospitals", "Clinic", "School", "Schools",
    "University", "Church", "Churches", "Mosque", "Temple", "Religious",
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
}

URL_RE = re.compile(r"https?://\S+", re.I)
TAG_RE = re.compile(r"<[^>]+>")

# These expose the record's own stored rating, which would anchor the blind rater.
BAND_LABELS = ("low risk", "reduced risk", "elevated risk", "high risk",
               "do not travel", "do-not-travel")
RANK_RE = re.compile(r"\brank(?:ed|ing)?\s*#?\d", re.I)
SENT_START_RE = re.compile(r"(?:^|[.!?]\s+|</p>\s*|\A)\s*([A-Z][a-z]{2,})")


def strip_tags(s: str) -> str:
    return TAG_RE.sub(" ", s)


def domains_of(rec: dict) -> set[str]:
    out = set()
    for s in rec.get("sources", []):
        if isinstance(s, dict) and s.get("url"):
            try:
                host = urlparse(s["url"]).netloc.lower()
            except Exception:
                continue
            host = host.removeprefix("www.")
            out.add(host)
            # also the registrable-ish last two labels and the first path token
            parts = host.split(".")
            if len(parts) >= 2:
                out.add(".".join(parts[-2:]))
    return {d for d in out if d}


def blind_text(blind: dict) -> str:
    chunks = []
    for f in REQUIRED + OPTIONAL:
        v = blind.get(f)
        if isinstance(v, list):
            chunks.extend(str(x) for x in v)
        elif v:
            chunks.append(str(v))
    return "\n".join(chunks)


def check_leaks(text: str, iso: str, rec: dict, all_names: dict[str, str],
                allow_tokens: set[str]) -> tuple[list[str], list[str]]:
    """Return (hard_failures, warnings)."""
    fails, warns = [], []
    low = text.lower()
    plain = strip_tags(text)

    # URLs must be gone
    for u in URL_RE.findall(plain):
        warns.append(f"URL present: {u[:80]}")

    # own name / iso / domains
    own = rec.get("name", "")
    if own and re.search(rf"\b{re.escape(own)}\b", plain, re.I):
        fails.append(f"own name leaks: {own!r}")
    if re.search(rf"\b{re.escape(iso)}\b", plain, re.I):
        fails.append(f"own ISO3 leaks: {iso!r}")
    for dom in domains_of(rec):
        if dom and dom in low:
            fails.append(f"source domain leaks: {dom!r}")

    # the record's own rating must not appear — it would anchor the rater
    for bl in BAND_LABELS:
        if bl in low:
            fails.append(f"own band label leaks: {bl!r}")
    if RANK_RE.search(plain):
        fails.append("rank reference leaks (e.g. 'rank 48')")
    # only the record's OWN score is a leak; other decimals ("2.5 years") are fine
    own_score = rec.get("score")
    if isinstance(own_score, (int, float)):
        for form in (f"{own_score:.2f}", f"{own_score:.1f}", str(own_score)):
            if form and re.search(rf"(?<![\d.]){re.escape(form)}(?![\d])", plain):
                fails.append(f"own score leaks: {form!r}")
                break

    # any jurisdiction name (leak by association)
    for code, nm in all_names.items():
        if not nm or len(nm) < 4:
            continue
        if re.search(rf"\b{re.escape(nm)}\b", plain, re.I):
            fails.append(f"jurisdiction name leaks: {nm!r} ({code})")

    # region / demonym terms
    for term in REGION_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", plain, re.I):
            fails.append(f"region/demonym term leaks: {term!r}")

    # capitalised tokens that extend a jurisdiction name (Samoan, Chinese, ...)
    tokens = set(re.findall(r"\b[A-Z][a-z]{2,}\b", plain))
    for tok in tokens:
        tl = tok.lower()
        if tl in allow_tokens:
            continue
        for code, nm in all_names.items():
            nml = nm.lower()
            if len(nml) >= 4 and tl.startswith(nml) and tl != nml:
                fails.append(f"demonym leaks: {tok!r} (from {nm} / {code})")
                break

    # remaining capitalised tokens -> human review.
    # Sentence-initial capitals are ordinary English, not proper nouns, so only
    # tokens that are NOT at a sentence start are worth flagging.
    sent_initial = {m.group(1) for m in SENT_START_RE.finditer(plain)}
    for tok in sorted(tokens):
        if tok in GENERIC_ALLOWED or tok.lower() in allow_tokens:
            continue
        if tok in sent_initial:
            continue
        if any(tok.lower().startswith(nm.lower()) for nm in all_names.values()
               if len(nm) >= 4):
            continue  # already hard-failed above
        warns.append(f"capitalised token to review: {tok!r}")

    return fails, warns


def length_ok(blind_val, src_val) -> bool:
    if src_val is None:
        return True
    if isinstance(blind_val, list):
        b = sum(len(str(x)) for x in blind_val)
        s = sum(len(str(x.get("summary", ""))) if isinstance(x, dict) else len(str(x))
                for x in src_val)
    else:
        b = len(strip_tags(str(blind_val)))
        s = len(strip_tags(str(src_val)))
    if s == 0:
        return b == 0
    return 0.4 * s <= b <= 2.0 * s


def load_inputs(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if path.is_dir():
        for f in sorted(path.glob("*.json")):
            obj = json.loads(f.read_text(encoding="utf-8"))
            iso = obj.get("iso") or f.stem.upper()
            out[iso] = obj
    else:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            iso = (obj.get("iso") or "").upper()
            if not iso:
                raise SystemExit(f"line without iso: {line[:120]}")
            out[iso] = obj
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", required=True,
                    help="JSONL file or directory of <ISO>.json files")
    ap.add_argument("--countries-file", default=str(ROOT / "data" / "countries.json"))
    ap.add_argument("--dry-run", action="store_true", help="validate only; write nothing")
    ap.add_argument("--report", action="store_true",
                    help="report which records are ready for blind_pairwise and exit")
    ap.add_argument("--allow-token", action="append", default=[],
                    help="lowercase token to exempt from leak checks (repeatable)")
    ap.add_argument("--quiet-warnings", action="store_true")
    args = ap.parse_args()

    countries = json.loads(Path(args.countries_file).read_text(encoding="utf-8"))
    all_names = {k: v.get("name", "") for k, v in countries.items()}
    allow = {t.lower() for t in args.allow_token}

    if args.report:
        ready = [i for i, r in countries.items()
                 if all(str(r.get(f, "")).strip() or (f == "blindSourceSummaries"
                                                      and isinstance(r.get(f), list)
                                                      and r.get(f))
                        for f in REQUIRED)]
        print(f"records with all required blind fields: {len(ready)}/{len(countries)}")
        opt = [i for i, r in countries.items() if r.get("blindLocalsOnly")]
        print(f"records with blindLocalsOnly: {len(opt)}")
        opt2 = [i for i, r in countries.items() if r.get("blindTangential")]
        print(f"records with blindTangential: {len(opt2)}")
        if len(ready) < len(countries):
            miss = sorted(set(countries) - set(ready))
            print(f"not ready ({len(miss)}): {' '.join(miss[:40])}"
                  + (" ..." if len(miss) > 40 else ""))
        return 0

    inputs = load_inputs(Path(args.inp))
    print(f"loaded {len(inputs)} blind records from {args.inp}")

    ok = skipped = 0
    warn_total = 0
    for iso, blind in sorted(inputs.items()):
        rec = countries.get(iso)
        if rec is None:
            print(f"\n[SKIP] {iso}: not in countries.json")
            skipped += 1
            continue

        fails: list[str] = []
        warns: list[str] = []

        for f in REQUIRED:
            v = blind.get(f)
            if f == "blindSourceSummaries":
                if not isinstance(v, list) or not v:
                    fails.append(f"{f} missing or not a non-empty list")
                elif len(v) != len(rec.get("sources", [])):
                    fails.append(f"{f} length {len(v)} != sources length "
                                 f"{len(rec.get('sources', []))}")
                elif not all(isinstance(x, str) and x.strip() for x in v):
                    fails.append(f"{f} contains empty/non-string entries")
            else:
                if not isinstance(v, str) or not v.strip():
                    fails.append(f"{f} missing or empty")

        for f in OPTIONAL:
            src = dict(PAIRS).get(f)
            has_src = bool(str(rec.get(src, "")).strip()) if src else False
            v = blind.get(f)
            if v is not None and not isinstance(v, str):
                fails.append(f"{f} must be a string")
            if has_src and (v is None or not str(v).strip()):
                warns.append(f"source has {src} but {f} is absent")
            if not has_src and v:
                warns.append(f"{f} present but source record has no {src}")

        text = blind_text(blind)
        lf, lw = check_leaks(text, iso, rec, all_names, allow)
        fails += lf
        warns += lw

        for bf, sf in PAIRS:
            if bf in blind and blind[bf]:
                if not length_ok(blind[bf], rec.get(sf)):
                    b = len(strip_tags(str(blind[bf])))
                    s = len(strip_tags(str(rec.get(sf, ""))))
                    fails.append(f"{bf} length {b} outside 40–200% of {sf} ({s})")
        if isinstance(blind.get("blindSourceSummaries"), list) and rec.get("sources"):
            if not length_ok(blind["blindSourceSummaries"], rec["sources"]):
                b = sum(len(str(x)) for x in blind["blindSourceSummaries"])
                s = sum(len(str(x.get("summary", ""))) for x in rec["sources"]
                        if isinstance(x, dict))
                fails.append(f"blindSourceSummaries length {b} outside 40–200% of "
                             f"sources ({s})")

        if fails:
            print(f"\n[FAIL] {iso}")
            for f in dict.fromkeys(fails):
                print(f"   - {f}")
            skipped += 1
            continue

        if warns and not args.quiet_warnings:
            uniq = list(dict.fromkeys(warns))
            print(f"\n[WARN] {iso}: {len(uniq)} item(s) for review")
            for w in uniq[:12]:
                print(f"   · {w}")
            if len(uniq) > 12:
                print(f"   … +{len(uniq)-12} more")
        warn_total += len(warns)

        if not args.dry_run:
            for f in REQUIRED + OPTIONAL:
                if f in blind and blind[f]:
                    rec[f] = blind[f]
            for f in OPTIONAL:
                if f not in blind or not blind[f]:
                    rec.pop(f, None)
        ok += 1

    print(f"\nvalidated OK: {ok} · skipped: {skipped} · warnings: {warn_total}")
    if args.dry_run:
        print("dry run — nothing written")
        return 0 if skipped == 0 else 1

    if ok:
        tmp = Path(str(args.countries_file) + ".tmp")
        tmp.write_text(json.dumps(countries, indent=1, ensure_ascii=False),
                       encoding="utf-8")
        tmp.replace(args.countries_file)
        print(f"wrote {ok} records to {args.countries_file}")
        print("next: python3 tools/build_data.py")
    return 0 if skipped == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
