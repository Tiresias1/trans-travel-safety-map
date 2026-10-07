#!/usr/bin/env python3
"""Dimension-driven research pilot (2026-10-07, user-approved).

Phase 1  coverage audit: LLM-tags a record's existing source claims against
         DIMENSION_MATRIX.md -> coverage matrix with gaps.
Phase 2  gap-fill: for each uncovered dimension, extract claims from SPECIFIED
         source texts with an ANTI-FABRICATION GATE — every extracted claim
         must share a verbatim >=5-word n-gram with the source text, else it
         is rejected. New sources are appended to the record.
Phase 3  (caller runs tools/consolidate_record.py --who ... --apply) so the
         dossier regenerates through the gated pipeline with the new claims.

Usage:
  python3 tools/pilot_research.py --who country:USA --audit
  python3 tools/pilot_research.py --who country:USA --fill --source-text-file /tmp/persecution.txt \
      --source-url https://en.wikipedia.org/wiki/Persecution_of_transgender_people_under_the_second_Trump_administration \
      --source-title "Persecution of transgender people under the second Trump administration (Wikipedia)"
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from consolidate_record import call_llm  # noqa

MATRIX = (ROOT / "research" / "DIMENSION_MATRIX.md").read_text()
DIMS = re.findall(r"^(D\d+)\s+(.+?)\s+—", MATRIX, re.M)
DIM_IDS = [d[0] for d in DIMS]


def load_target(who: str):
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    if who.startswith("country:"):
        return C, who[8:], C[who[8:]]
    iso, nm = who.split("/", 1)
    return A, iso, next(x for x in A.values()
                        if x.get("iso3") == iso and x.get("name") == nm)


def audit(rec: dict, who: str) -> dict:
    claims = []
    for i, s in enumerate(rec.get("sources") or []):
        if isinstance(s, dict) and (s.get("summary") or s.get("title")):
            claims.append(f"[{i}] {s.get('summary') or s.get('title')}")
    inv = "\n".join(claims)
    out = call_llm(
        "You are a coverage auditor for a trans-visitor travel-safety dossier.",
        f"""{MATRIX}

TASK: audit which dimensions the record's source claims cover. For each claim,
assign the dimension ids it substantively covers. Then list dimensions with
ZERO coverage as gaps.

Record: {who}
CLAIMS:
{inv}

Return ONLY JSON:
{{"claim_dims": {{"0": ["D1","D9"], ...}},
  "gaps": ["D7", ...],
  "notes": "one-line assessment"}}""")
    return out


def ngram_shared(claim: str, text: str, n: int = 5) -> bool:
    words = re.findall(r"[a-z']+", claim.lower())
    if len(words) < n:
        return True  # short claims can't be n-gram checked
    text_ngrams = {" ".join(text.lower().split()[i:i + n])
                   for i in range(len(text.lower().split()) - n + 1)}
    for i in range(len(words) - n + 1):
        if " ".join(words[i:i + n]) in text_ngrams:
            return True
    return False


def fill(rec: dict, who: str, gaps: list, src_text: str,
         src_url: str, src_title: str) -> list:
    """Extract one claim per gap dimension from the source text, gated."""
    dim_list = "\n".join(f"{d}: {t}" for d, t in DIMS if d in gaps)
    out = call_llm(
        "You extract sourced findings for a trans-visitor dossier. You must "
        "quote the source faithfully — any claim that cannot be grounded in the "
        "source text is fabrication and will be mechanically rejected.",
        f"""GAP DIMENSIONS to fill:
{dim_list}

SOURCE TEXT (verbatim):
{src_text[:60000]}

For EACH gap dimension, either extract the finding the source text supports
(2-4 sentences, substance-first: what happened, whom it hits, dates, numbers,
policy names in plain language) or write exactly 'no source text supports this
dimension'. Trans-youth angles matter: minors travel and are a major political
target — note youth-specific findings under D8/D13 where present.

Return ONLY JSON: {{"D7": "claim text or 'no source text...'", ...}}""")
    added = []
    have = {s.get("url") for s in (rec.get("sources") or []) if isinstance(s, dict)}
    for d, txt in out.items():
        if d not in gaps or not isinstance(txt, str):
            continue
        txt = txt.strip()
        if not txt or "no source text" in txt.lower():
            continue
        if not ngram_shared(txt, src_text):
            print(f"  [ANTI-FABRICATION REJECT] {d}: claim not grounded in source")
            continue
        claim = f"{src_title}: {txt}"
        if src_url not in have:
            rec.setdefault("sources", []).append(
                {"url": src_url, "title": src_title, "summary": claim})
            have.add(src_url)
        else:
            # source already present: merge the dimension finding into its claim
            for s in rec["sources"]:
                if isinstance(s, dict) and s.get("url") == src_url:
                    s["summary"] = str(s.get("summary", "")).rstrip() + " " + claim
                    break
        added.append(d)
    return added


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--who", required=True)
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--fill", action="store_true")
    ap.add_argument("--source-text-file")
    ap.add_argument("--source-url", default="")
    ap.add_argument("--source-title", default="")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    store, key, rec = load_target(args.who)
    if args.audit:
        res = audit(rec, args.who)
        print(json.dumps(res, ensure_ascii=False, indent=1)[:3000])
        Path(ROOT / "research" / "coverage").mkdir(exist_ok=True)
        (ROOT / "research" / "coverage" /
         (args.who.replace(":", "_").replace("/", "_") + ".json")
         ).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        return
    if args.fill:
        gaps = json.loads((ROOT / "research" / "coverage" /
                           (args.who.replace(":", "_").replace("/", "_") + ".json")
                           ).read_text()).get("gaps", [])
        src_text = Path(args.source_text_file).read_text()
        added = fill(rec, args.who, gaps, src_text,
                     args.source_url, args.source_title)
        print(f"dimensions filled from source: {added} (gaps were: {gaps})")
        if args.apply:
            store[key] = rec
            (ROOT / "data" / ("countries.json" if args.who.startswith("country:")
                              else "admin1.json")).write_text(
                json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
            print("applied")


if __name__ == "__main__":
    main()