#!/usr/bin/env python3
"""Non-dossier ADM1 text hygiene (2026-10-06 full-run phase 3).

1. Mechanical strip of pipeline jargon from visitor-facing summaries
   ("Model estimate (route 3...)", "scored at the national level", "scored
   relative to the national score (N)") — map mechanics never appear on the
   map (same doctrine as the changelog ban).
2. Style scan of every non-dossier summary against STYLE_RULES patterns;
   records that still fail are listed for LLM repair (only the ~46 with real
   text can fail; the formulaic ones pass after the strip).

Usage: python3 tools/fix_nondossier_text.py [--apply]
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (pattern, replacement) applied to summary + outOfScopeNotes + tangential
STRIPS = [
    (re.compile(r"No sub-national signal was identified; scored at the national level\. "
                r"Model estimate \(route 3\): deviation from the national score is zero "
                r"where no reliable sub-national knowledge exists\.",
                re.I),
     "No sub-national signal was identified; the national assessment applies here."),
    (re.compile(r"Model estimate \(route 3, best-knowledge delta\):\s*", re.I), ""),
    (re.compile(r"Model estimate \(route 3\):\s*", re.I), ""),
    (re.compile(r"Model estimate \(no dedicated dossier\)\.\s*", re.I), ""),
    (re.compile(r"Model estimate[^:.]*[:.]\s*", re.I), ""),
    (re.compile(r"Model estimate[^:]*:\s*", re.I), ""),
    (re.compile(r"Scored relative to the national score \(\d+(?:\.\d+)?\) for "
                r"([^.<]+?)\s*(?:\.|$)", re.I),
     r"Assessed relative to the national picture in \1."),
    (re.compile(r"This unit is a distinct jurisdiction scored at country level",
                re.I),
     "This unit is a distinct jurisdiction assessed at the country level"),
    (re.compile(r"\bscored at the national level\b", re.I),
     "assessed at the national level"),
    (re.compile(r"\broute \d\b", re.I), ""),
]

# residual style red flags (LLM-isms / jargon that must not survive)
RESIDUAL = re.compile(
    r"route \d|model estimate|SUPERSEDED|per freshness|rev 20\d\d|at fetch time|"
    r"earlier profile|inherited arithmetic|borrowed custody|were deleted|was deleted|"
    r"it is worth noting|importantly,|note that\b|delve|tapestry|testament to|"
    r" navigating the|landscape of|vibrant|bustling", re.I)


def clean(t: str) -> str:
    if not t:
        return t
    for pat, rep in STRIPS:
        t = pat.sub(rep, t)
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"\s+([.;])", r"\1", t)
    return t.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    changed = flagged = 0
    leftovers = []
    for sid, r in A.items():
        if r.get("dossier") or r.get("inherited"):
            continue
        touched = False
        for f in ("summary", "outOfScopeNotes", "tangentialFactors", "localsOnly"):
            t = r.get(f)
            if isinstance(t, str) and t:
                new = clean(t)
                if new != t:
                    r[f] = new
                    touched = True
        if touched:
            changed += 1
        joined = " ".join(str(r.get(f) or "") for f in
                          ("summary", "outOfScopeNotes", "tangentialFactors", "localsOnly"))
        m = RESIDUAL.search(joined)
        if m:
            flagged += 1
            leftovers.append((sid, r.get("iso3"), r.get("name"),
                               joined[max(0, m.start() - 40):m.end() + 40][:100]))
    # same strip for country records + dossier regions (safety net)
    for D in (C, A):
        for r in D.values():
            for f in ("summary", "outOfScopeNotes", "tangentialFactors", "localsOnly",
                      "blindSummary", "blindTangential", "blindLocalsOnly", "blindOutOfScope"):
                t = r.get(f)
                if isinstance(t, str) and t and RESIDUAL.search(t):
                    new = clean(t)
                    if new != t:
                        r[f] = new
                        changed += 1
    print(f"records cleaned: {changed}; residual flags: {flagged}")
    for sid, iso, nm, ctx in leftovers[:15]:
        print(f"  FLAG {iso}/{nm}: ...{ctx}...")
    if args.apply:
        (ROOT / "data" / "admin1.json").write_text(
            json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")
        (ROOT / "data" / "countries.json").write_text(
            json.dumps(C, ensure_ascii=False, indent=1), encoding="utf-8")
        print("applied")


if __name__ == "__main__":
    main()