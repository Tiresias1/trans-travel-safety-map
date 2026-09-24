#!/usr/bin/env python3
"""Validate anonymised blindSummary fields for ADM1 regions (data/admin1.json).

Region dossiers in tools/blind_pairwise.py consist of the parent country's blind
bundle (validated separately) + the region's single blindSummary. This checker
enforces, per region:

hard fail:
  * blindSummary missing / empty / outside 40-200% of the source summary
  * the region's own name (e.g. "Idaho") - it is withheld in the prompt header
  * ANY other admin1 unit name in the same parent country (state-to-state
    references must read "a neighbouring state/province")
  * parent-country aliases: United States / US / U.S. / USA / American(s) /
    "the States" / D.C. / Washington D.C. (case-insensitive where unambiguous)
  * band labels, the region's or parent's score digits, "#N" rank tokens
  * bill/initiative/statute numbers (HB 706, SB 426, Prop 1, I-732, Issue 1,
    P.L. 117, No. 123, Section 1234) - the user's rule: no reason for them
  * region terms from the country rulebook's list (e.g. midwest-style blocs
    caught by shared REGION_TERMS where applicable) + extra US shorthand:
    red/blue/purple state(s), bible belt, deep south, new england, the
    heartland, maga, tds, "the States"
  * all-caps agency/NGO acronyms not on a tiny allowlist (ICE, CBP, BOP,
    EEOC, Title IX -> must be rewritten as mechanisms). Title IX and the
    T-word pattern are hard-failed directly.
warning:
  * capitalised tokens not in an allowlist (month names etc.) - city, county,
    university, team, org, person names end up here; worker must resolve them
"""
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
    re.compile(r"\bi[-\s]\d{1,3}\b"),          # I-732 style ballot measures
    re.compile(r"\bsection\s+\d{2,}\b", re.I), # bare statute sections
]
# case-insensitive parent aliases (unambiguous strings only)
PARENT_CI = [r"united states", r"u\.s\.a?", r"usa\b", r"american", r"\bus\b(?!\.)",
             r"\bu\.s\.\b", r"the states\b", r"washington,? d\.?c\.?", r"\bd\.c\."]
# explicit shorthand that singles out the US political landscape
SHORTHAND = [r"red[- ]states?", r"blue[- ]states?", r"purple[- ]states?",
             r"bible belt", r"deep south", r"new england", r"\bheartland\b",
             r"\bmaga\b", r"teaparty|tea party", r"title ix", r"\bcdrr?\b",
             r"pacific northwest|mountain west|mason[- ]dixon|\bdixie\b"]
ACRONYM_OK = {"UN", "WHO", "AIDS", "HIV", "LGBT", "LGBTQ", "LGBTQIA", "SOGI",
              "SOGIESC", "NGO", "NGOS", "UNDP", "ILO", "OSCE", "UPR", "ID",
              "II", "III", "IV", "V", "X"}
SENT_RE = re.compile(r"(?:^|[.!?]\s+|</p>\s*|\A)\s*([A-Z][a-z]{2,})")

def strip_tags(s): return re.sub(r"<[^>]+>", " ", s)

def region_checks(rec: dict, all_unit_names: list[str], parent_names: list[str]):
    fails, warns = [], []
    blind = str(rec.get("blindSummary", ""))
    plain = strip_tags(blind)
    if not plain.strip():
        fails.append("blindSummary missing/empty"); return fails, warns
    src = strip_tags(str(rec.get("summary", "")))
    if len(src) and not (0.4 * len(src) <= len(plain) <= 2.0 * len(src)):
        fails.append(f"length {len(plain)} vs source {len(src)} outside 40-200%")
    low = plain.lower()
    own = str(rec.get("name", ""))
    if own and re.search(rf"\b{re.escape(own)}\b", plain, re.I):
        fails.append(f"own unit name leaks: {own!r}")
    for nm in all_unit_names:
        if nm == own or len(nm) < 4: continue
        if re.search(rf"\b{re.escape(nm)}\b", plain, re.I):
            fails.append(f"sibling unit name leaks: {nm!r}")
    for p in parent_names:
        if re.search(rf"\b{re.escape(p)}\b", plain, re.I):
            fails.append(f"parent-country name leaks: {p!r}")
    for pat in PARENT_CI:
        if re.search(pat, low):
            fails.append(f"parent alias leaks: {pat}")
    for b in BANDS:
        if b in low: fails.append(f"band label leaks: {b!r}")
    if RANK_RE.search(plain): fails.append("rank-style token leaks")
    for r in BILL_RES:
        m = r.search(plain)
        if m: fails.append(f"bill/statute number leaks: {m.group(0)!r}")
    for r in SHORTHAND:
        m = re.search(r, low)
        if m: fails.append(f"US-shorthand leaks: {m.group(0)!r}")
    # own score digits
    s = rec.get("score")
    if isinstance(s, (int, float)):
        for form in (f"{s:.2f}", f"{s:.1f}", str(s)):
            if form and re.search(rf"(?<![\d.]){re.escape(form)}(?![\d])", plain):
                fails.append(f"own score leaks: {form!r}"); break
    sent_initial = {m.group(1) for m in SENT_RE.finditer(plain)}
    for tok in set(re.findall(r"\b[A-Z][a-z]{2,}\b", plain)):
        if tok in ("NOTE",): continue
        tl = tok.lower()
        if tl in {"jan","feb","mar","apr","may","jun","jul","aug","sept","sep",
                  "oct","nov","dec","january","february","march","april","june",
                  "july","august","september","october","november","december",
                  "pride","page","for","safe","caution","being","loading"}:
            continue
        if tok in sent_initial: continue
        if unicodedata.normalize("NFKD", tok).encode("ascii", "ignore").decode() in ():
            pass
        warns.append(f"capitalised token to review: {tok!r}")
    for tok in set(re.findall(r"\b[A-Z]{2,}\b", plain)):
        if tok not in ACRONYM_OK:
            warns.append(f"all-caps acronym to review: {tok!r}")
    return fails, warns

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=str(ROOT / "data/blind_outputs/adm1"),
                    help="dir of <id>.json files ({id, blindSummary}) to validate+apply")
    ap.add_argument("--admin1-file", default=str(ROOT / "data/admin1.json"))
    ap.add_argument("--countries-file", default=str(ROOT / "data/countries.json"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    admin1 = json.loads(Path(args.admin1_file).read_text(encoding="utf-8"))
    countries = json.loads(Path(args.countries_file).read_text(encoding="utf-8"))

    if args.report:
        need = [k for k, v in admin1.items() if v.get("estimated") is False]
        have = [k for k in need if str(admin1[k].get("blindSummary", "")).strip()]
        print(f"estimated:false regions: {len(need)} | with blindSummary: {len(have)}")
        miss = [k for k in need if k not in have]
        if miss:
            names = " ".join(admin1[k]["name"] for k in miss[:40])
            print(f"missing ({len(miss)}): {names}")
        return 0

    inp = Path(args.inp)
    files = sorted(inp.glob("*.json"))
    ok = fails_total = 0
    for f in files:
        obj = json.loads(f.read_text(encoding="utf-8"))
        rid = obj.get("id") or f.stem
        rec = admin1.get(rid)
        if rec is None:
            print(f"[SKIP] {f.name}: id not in admin1.json"); continue
        iso3 = rec.get("iso3")
        siblings = [v.get("name", "") for k, v in admin1.items()
                    if v.get("iso3") == iso3]
        parent = countries.get(iso3) or {}
        parent_names = [parent.get("name", "")] if parent.get("name") else []
        fails, warns = region_checks({**rec, "blindSummary": obj.get("blindSummary", "")},
                                     siblings, parent_names)
        if fails:
            print(f"\n[FAIL] {rec['name']} ({rid})")
            for x in dict.fromkeys(fails): print("   -", x)
            fails_total += 1
            continue
        if warns:
            uniq = list(dict.fromkeys(warns))
            print(f"\n[WARN] {rec['name']} ({rid}): {len(uniq)} item(s)")
            for w in uniq[:14]: print("   ·", w)
        if not args.dry_run:
            rec["blindSummary"] = obj["blindSummary"]
        ok += 1
    if not args.dry_run and ok:
        tmp = Path(args.admin1_file + ".tmp")
        tmp.write_text(json.dumps(admin1, indent=1, ensure_ascii=False), encoding="utf-8")
        tmp.replace(args.admin1_file)
    print(f"\nvalidated OK: {ok} · failed: {fails_total}"
          + (" · dry run, nothing written" if args.dry_run else f" · wrote {ok} blindSummary fields"))
    return 0 if fails_total == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
