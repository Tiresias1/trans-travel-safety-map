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

2. RELEVANCE GATE — the test is: would this fact change what a trans visitor
   expects to face (law, enforcement, documents, entry, screening, care access,
   facilities, violence risk, partner recognition, protection machinery)?
   IN: criminalisation and its penalties; document/marker rules; entry and visa
   rules; screening that risks outing; bathroom/facilities law; care bans;
   hate-crime protection and its enforcement; marriage/partner recognition;
   trans-specific violence with dates and outcomes; official hostility or
   protection.
   OUT: generic travel logistics that apply in every country (carry-on liquid
   limits, prohibited items, airline procedure, general crime/city safety);
   general LGB history with no trans bearing unless it evidences the legal
   regime; a publication's own editorial framing.
   If a source's only usable content is OUT-material, drop it silently.

3. REPRESENTATIVENESS — for a national dossier, any single sub-national unit
   (state, province, city) is ONE data point illustrating a wider pattern,
   never the headline. Summarise the pattern first (how many states, which
   direction, what enforcement), then cite at most one or two named units as
   examples. A national summary must never read like the profile of one state.

4. Four-field split for the visible record: summary (visitor risk assessment),
   tangentialFactors (adjacent/turbulence, comparisons), localsOnly (resident-
   facing facts), outOfScopeNotes (unresolved/verifiable caveats, honestly
   worded as 'unresolved'/'not sourced' — never as pipeline outcomes). Number
   of <p> per field is unbounded but each paragraph must a real finding.

5. VISIBLE fields use REAL NAMES — the actual country, territory, ministry,
   court. The anonymisation vocabulary (state/province, parent nation,
   administering state, national instead of federal) belongs ONLY to the blind
   mirrors. Never write 'the administering state' or 'state/province' in a
   visible field.

6. Absolute terms, sourced-backed. Do not fabricate beyond the inventory. For
   a dependency, state plainly which parent laws extend and which do not —
   that is a research fact, not an unknown: if the sources say the parent's
   statute does not extend here, say that.

7. Blind mirrors: same claims, same structure, fixed vocabulary only
   (territory->state/province, federal->national, no geographic names/oceans/
   cardinal directions/region names), substitution-only derivation.

8. For a region or dependency: state the parent-framework layer explicitly
   ("stands under the national framework: ...", naming in visible text the
   actual parent country) unless the region text already does.

Output ONLY a JSON object:
{{\"summary\": \"...\", \"tangentialFactors\": \"...\", \"localsOnly\": \"...\",
  \"outOfScopeNotes\": \"...\", \"blindSummary\": \"...\",
  \"blindTangential\": \"...\", \"blindLocalsOnly\": \"...\",
  \"blindOutOfScope\": \"...\"}}"""


# Mechanical pre-filter: claims that are pure generic travel logistics never
# reach the model (belt-and-braces behind rule 2; the carry-on text was the
# failure that motivated this).
GENERIC_TRAVEL = re.compile(
    r"carry-on|carry on|prohibited items|liquid limits|checked bag|security queue|"
    r"boarding|check-in|layover|jet lag|currency exchange|tipping|"
    r"traffic safety|road safety|pickpocket|scams targeting tourists", re.I)
TRANS_KEEP = re.compile(r"outing|scann|pat-down|secondary screen|marker|gender|x marker", re.I)


def relevant_claims(rec):
    out, dropped = [], []
    for s in (rec.get("sources") or []):
        if isinstance(s, dict):
            claim = s.get("summary") or s.get("title") or ""
            if GENERIC_TRAVEL.search(claim) and not TRANS_KEEP.search(claim):
                dropped.append((s.get("url", ""), claim[:60]))
                continue
            out.append(s)
        else:
            out.append(s)
    return out, dropped


def build_user(rec, parent_summ=""):
    lines = [f"JURISDICTION: {rec.get('name')} ({rec.get('iso3')})"]
    if parent_summ:
        lines.append(f"PARENT FRAMEWORK (restate if a region): {parent_summ}")
    lines.append(f"CURRENT SUMMARY (for continuity): {rec.get('summary','')[:900]}")
    lines.append("SOURCE CLAIM INVENTORY (include every substantive claim that passes the relevance gate):")
    kept, dropped = relevant_claims(rec)
    for i, s in enumerate(kept, 1):
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
        "max_tokens": 6000,
    }
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(),
        headers={"authorization": f"Bearer {KEY}",
                 "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read().decode())
    content = d["choices"][0]["message"].get("content")
    if content is None:
        raise ValueError("empty model content (None)")
    text = content
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


# Mechanical post-validation: no lane output ships unless it passes these.
# (The 2026-10-05 hand-edits fixed records; these rules fix the SYSTEM that
# writes them: the same defects can never pass validation again.)
META_NARRATIVE = re.compile(
    r"earlier profile|previous profile|inherited arithmetic|borrowed custody|"
    r"SUPERSEDED|per freshness|\(rev [\d-]+\)|at fetch time|the audited record|"
    r"were deleted|was deleted|deleted because|deleted for lack|model prior", re.I)
VIS_ANON = re.compile(
    r"administering state|parent nation|parent state|parent government|"
    r"\bstate/province\b|\bstate/provinces\b", re.I)
GENERIC_TRAVEL_OUT = re.compile(
    r"carry-on|prohibited items and carry|liquid limits", re.I)


def validate_output(out, problems):
    for k in ("summary", "tangentialFactors", "localsOnly", "outOfScopeNotes"):
        t = str(out.get(k) or "")
        if META_NARRATIVE.search(t):
            problems.append(f"{k}: edit-narrative/pipeline jargon (rejected)")
        if VIS_ANON.search(t):
            problems.append(f"{k}: blind vocabulary in visible text (rejected)")
    for k in ("summary", "tangentialFactors"):
        t = str(out.get(k) or "")
        if GENERIC_TRAVEL_OUT.search(t):
            problems.append(f"{k}: generic travel logistics (rejected)")
    for k, v in out.items():
        if isinstance(v, str) and META_NARRATIVE.search(v):
            if not any(f"{kk}: edit" in p for kk, vv in out.items() if kk != k):
                problems.append(f"{k}: edit-narrative (blind field)")
    return not problems


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
    gate_passed = False
    for attempt in range(5):
        try:
            out = run(who, rec, parent.get("summary", "") if parent else "")
        except Exception as e:
            print(f"[retry {attempt+1}] {e}")
            time.sleep(5)
            continue
        # REAL BLIND GATE on every generation attempt (systematic 2026-10-06):
        # reject edit-narrative/jargon/vis-anon/generic-travel, then the blind
        # gate with auto-remediation; a failed attempt saves the output for
        # inspection and RETRIES the generation (nondeterministic output).
        problems = []
        for k in ("summary", "tangentialFactors", "localsOnly", "outOfScopeNotes"):
            if k in out and not valid_summary(out[k]):
                problems.append(f"{k} invalid")
        validate_output(out, problems)
        if problems:
            print(f"[attempt {attempt+1}] content gate: {problems}; retrying")
            continue
        import importlib.util as _ilu
        _s1 = _ilu.spec_from_file_location("cb", ROOT / "tools" / "check_blind.py")
        _cb = _ilu.module_from_spec(_s1); _s1.loader.exec_module(_cb)
        _s2 = _ilu.spec_from_file_location("fbg", ROOT / "tools" / "fix_blind_gate.py")
        _fbg = _ilu.module_from_spec(_s2); _s2.loader.exec_module(_fbg)
        _rec = {k: out.get(k) for k in ("summary", "tangentialFactors", "localsOnly",
                 "outOfScopeNotes", "blindSummary", "blindTangential",
                 "blindLocalsOnly", "blindOutOfScope")}
        if _cb.check(_rec, who):
            gate_passed = True
            break
        print(f"[attempt {attempt+1}] blind gate failed; running fixed-vocabulary remediation")
        for k in ("blindSummary", "blindTangential", "blindLocalsOnly", "blindOutOfScope"):
            if out.get(k):
                out[k] = _fbg._fix_text(out[k])
        _rec = {k: out.get(k) for k in ("summary", "tangentialFactors", "localsOnly",
                 "outOfScopeNotes", "blindSummary", "blindTangential",
                 "blindLocalsOnly", "blindOutOfScope")}
        if _cb.check(_rec, who):
            print("[gate] remediation passed")
            gate_passed = True
            break
        rej = ROOT / "data" / "consolidate_out" / (who.replace(":", "_").replace("/", "_") + ".rejected.json")
        rej.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[attempt {attempt+1}] blind gate FAILS even after remediation; saved {rej.name}; retrying generation")
    if not gate_passed:
        print("validation problems: no generation passed the gates after retries")
        sys.exit(1)
    # validate + gate-relevant sanity
    problems = []
    for k in ("summary", "tangentialFactors", "localsOnly", "outOfScopeNotes"):
        if k in out and not valid_summary(out[k]):
            problems.append(f"{k} invalid")
    if not validate_output(out, problems):
        pass  # problems already collected
    if problems:
        print("validation problems:", problems)
        sys.exit(1)
    # REAL BLIND GATE: the consolidation's blind mirrors must pass
    # check_blind (banned vocabulary + state-leak). If they fail, run the
    # deterministic fixed-vocabulary remediation and re-check; only if it
    # STILL fails does the run reject. (Systematic fix 2026-10-06: the
    # automated ASM output leaked banned words and would have shipped.)
    import importlib.util as _ilu
    _s1 = _ilu.spec_from_file_location("cb", ROOT / "tools" / "check_blind.py")
    _cb = _ilu.module_from_spec(_s1); _s1.loader.exec_module(_cb)
    _s2 = _ilu.spec_from_file_location("fbg", ROOT / "tools" / "fix_blind_gate.py")
    _fbg = _ilu.module_from_spec(_s2); _s2.loader.exec_module(_fbg)
    _rec = {k: out.get(k) for k in ("summary", "tangentialFactors", "localsOnly",
             "outOfScopeNotes", "blindSummary", "blindTangential",
             "blindLocalsOnly", "blindOutOfScope")}
    _ok = _cb.check(_rec, who)
    if not _ok:
        print("[gate] blind mirrors failed blind gate; running fixed-vocabulary remediation")
        for k in ("blindSummary", "blindTangential", "blindLocalsOnly", "blindOutOfScope"):
            if out.get(k):
                out[k] = _fbg._fix_text(out[k])
        _rec = {k: out.get(k) for k in ("summary", "tangentialFactors", "localsOnly",
                 "outOfScopeNotes", "blindSummary", "blindTangential",
                 "blindLocalsOnly", "blindOutOfScope")}
        if not _cb.check(_rec, who):
            print("validation problems: blind gate FAILS even after remediation — output rejected")
            sys.exit(1)
        print("[gate] remediation passed")
    # report what the relevance gate dropped (transparency, not ship-blocking)
    kept, dropped = relevant_claims(rec)
    if dropped:
        print(f"relevance gate dropped {len(dropped)} generic-travel claims:")
        for u, c in dropped:
            print(f"   - {u[:70]} | {c}")
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