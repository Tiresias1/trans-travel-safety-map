#!/usr/bin/env python3
"""Full-consolidation lane: regenerate a record's summary from ALL its sources.

The old 1-3 <p> / 2800-char caps forced summarizers to *select* rather than
*consolidate* (the USA dossier had 17 sources, each with distinct substantive
claims, but the summary carried only ~4). With the caps raised (8000/12),
this lane feeds the FULL claim inventory per source and instructs the model
to include every sourced substantive claim, in report voice (STYLE_RULES),
with the four-field split + blind mirror.

Usage: python3 tools/consolidate_record.py --who country:USA [--who ISO/Region]
       env OPENROUTER_KEY or /tmp/.openrouter_key.
Writes data/consolidate_out/<sanitized>.json for review; apply with
tools/apply_rework.py-style merge (see --apply).
"""
from __future__ import annotations
import argparse, json, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEY = (__import__("os").environ.get("OPENROUTER_KEY")
       or Path("/tmp/.openrouter_key").read_text().strip())
API = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "xiaomi/mimo-v2.6-flash"

STYLE = (ROOT / "tools" / "STYLE_RULES.md").read_text()

SYSTEM = f"""You are the dossier writer for a trans-visitor travel-safety map. You
rewrite one jurisdiction's dossier from its LIVE source inventory.

{STYLE}

RULES FOR THIS PASS (consolidation, not compression):
1. Include EVERY substantively distinct claim from the source inventory below.
   One <p> per claim or tightly-linked claim cluster. There is NO paragraph
   cap and NO length target beyond completeness: if the inventory has 10
   distinct visitor-relevant findings, the summary carries 10.
2. Four-field split for the visible record: summary (visitor risk assessment),
   tangentialFactors (adjacent/turbulence, comparisons), localsOnly (resident-
   facing facts), outOfScopeNotes (unresolved/verifiable caveats). Number of
   <p> per field is unbounded but each paragraph must be a real finding.
3. Absolute terms, sourced-backed. Do not fabricate beyond the inventory.
4. Blind mirrors: same claims, same structure, fixed vocabulary only
   (territory->state/province, federal->national, no geographic names/oceans/
   cardinal directions/region names), substitution-only derivation.
5. For a region: state the parent-framework layer explicitly unless the region
   text already does ("stands under the national framework: ...").

Output ONLY a JSON object:
{{\"summary\": \"...\", \"tangentialFactors\": \"...\", \"localsOnly\": \"...\",
  \"outOfScopeNotes\": \"...\", \"blindSummary\": \"...\",
  \"blindTangential\": \"...\", \"blindLocalsOnly\": \"...\",
  \"blindOutOfScope\": \"...\"}}"""


def build_user(rec, parent_summ=""):
    lines = [f"JURISDICTION: {rec.get('name')} ({rec.get('iso3')})"]
    if parent_summ:
        lines.append(f"PARENT FRAMEWORK (restate if a region): {parent_summ}")
    lines.append(f"CURRENT SUMMARY (for continuity): {rec.get('summary','')[:900]}")
    lines.append("SOURCE CLAIM INVENTORY (include every substantive claim):")
    for i, s in enumerate(rec.get("sources") or [], 1):
        if isinstance(s, dict):
            claim = s.get("summary") or s.get("title") or ""
            lines.append(f"  [{i}] ({s.get('url','')}) {claim}")
        elif isinstance(s, str):
            lines.append(f"  [{i}] {s}")
    return "\n".join(lines)


def run(who, rec, parent_summ=""):
    body = {
        "model": MODEL,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": build_user(rec, parent_summ)}],
        "temperature": 0.3,
        "max_tokens": 4000,
    }
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(),
        headers={"authorization": f"Bearer {KEY}",
                 "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read().decode())
    text = d["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"no JSON in model output: {text[:200]}")
    out = json.loads(m.group(0))
    return out


def valid_summary(s):
    if not s or len(s) > 8000:
        return False
    n = len(re.findall(r"<p[\s>]", s))
    return 1 <= n <= 12


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--who", required=True, help="country:ISO or ISO/Region")
    ap.add_argument("--apply", action="store_true", help="write into data files")
    args = ap.parse_args()
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    outdir = ROOT / "data" / "consolidate_out"; outdir.mkdir(exist_ok=True)
    who = args.who
    rec = parent = None
    if who.startswith("country:"):
        iso = who[8:]
        rec = C.get(iso)
    elif "/" in who:
        iso, nm = who.split("/", 1)
        rec = next((x for x in A.values()
                    if x.get("iso3") == iso and x.get("name") == nm), None)
        parent = C.get(iso)
    if not rec:
        sys.exit(f"not found: {who}")
    for attempt in range(3):
        try:
            out = run(who, rec, parent.get("summary", "") if parent else "")
            break
        except Exception as e:
            print(f"[retry {attempt+1}] {e}")
            time.sleep(5)
    else:
        sys.exit("failed after retries")
    # validate + gate-relevant sanity
    problems = []
    for k in ("summary", "tangentialFactors", "localsOnly", "outOfScopeNotes"):
        if k in out and not valid_summary(out[k]):
            problems.append(f"{k} invalid")
    if problems:
        print("validation problems:", problems)
        sys.exit(1)
    fn = who.replace(":", "_").replace("/", "_")
    out["who"] = who
    path = outdir / f"{fn}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {path} | summary {len(out.get('summary',''))} chars "
          f"({out.get('summary','').count('<p')} <p>)")
    if args.apply:
        for k in ("summary", "tangentialFactors", "localsOnly", "outOfScopeNotes",
                  "blindSummary", "blindTangential", "blindLocalsOnly", "blindOutOfScope"):
            if out.get(k) is not None:
                rec[k] = out[k]
        if who.startswith("country:"):
            C[iso] = rec
            (ROOT / "data" / "countries.json").write_text(
                json.dumps(C, ensure_ascii=False, indent=1), encoding="utf-8")
        else:
            (ROOT / "data" / "admin1.json").write_text(
                json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")
        print("applied to", who)
    return 0


if __name__ == "__main__":
    sys.exit(main())