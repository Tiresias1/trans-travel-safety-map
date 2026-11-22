#!/usr/bin/env python3
"""Dossier false-divergence audit (read-only over data/; writes only its own JSON).

For every ADM1 record whose dossier text matches export / non-application
patterns, one LLM judge call asks whether the record claims a parent-level
restriction does NOT apply to this division, and whether that claim is
(a) supported by a cited source in the record, (b) contradicted by the parent
framework (FALSE DIVERGENCE), or (c) unverifiable from the record. Also asks
whether the DELIBERATELY NOT COUNTED (blindOutOfScope) section lists something
the parent dossier DOES count.

Judge: provider_models.call_v4("mimo", ...) = MiMo V2.6 Flash, effort medium.
One call per record, no retries. Resume-safe: results are appended to
analysis/dossier_false_divergence.json as they complete; reruns skip done ids.
"""
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from provider_models import call_v4  # noqa: E402

ROOT = HERE.parents[3]  # kort/
ADMIN1 = ROOT / "data" / "admin1.json"
COUNTRIES = ROOT / "data" / "countries.json"
OUT = HERE / "analysis" / "dossier_false_divergence.json"

FIELDS = ["summary", "blindSummary", "blindOutOfScope", "outOfScopeNotes",
          "blindLocalsOnly", "localsOnly", "blindTangential", "tangentialFactors"]

# Textual patterns defining the audit scope (export / non-application language).
STRICT = re.compile(
    r"does not apply (?:here|in)|not appl(?:y|ies) (?:here|in this)"
    r"|another part of the (?:country|nation)|applies (?:only |in another)"
    r"|not applicable (?:here|to)|does not extend to (?:this|the)|not counted"
    r"|deliberately not counted|only (?:in|to) (?:the )?(?:other|northern|southern|another)"
    r"|applies in (?:the )?(?:north|south|other)"
    r"|for (?:England|Wales|Scotland|the rest of)"
    r"|in (?:England|Wales|Scotland) (?:only|alone)"
    r"|elsewhere in the (?:country|nation)"
    r"|other parts? of the (?:country|nation)", re.I)

SYSTEM = (
    "You are an audit judge checking research dossiers for 'false divergence' "
    "errors. You are given one sub-national division record (a state/province/"
    "region dossier), its parent country record excerpt, and the exact sentences "
    "that matched an export/non-application pattern search.\n"
    "Your job:\n"
    "1. Does the flagged text claim that a parent-level (national/country-wide) "
    "restriction, ban, duty or rule does NOT apply to THIS division (or applies "
    "only in another part of the country)? Answer yes/no and quote the claim.\n"
    "2. If yes, classify the claim using ONLY the record + parent excerpt given "
    "(do not use outside knowledge):\n"
    "   - SUPPORTED: a source cited in this record's source list supports the "
    "     non-application claim.\n"
    "   - FALSE_DIVERGENCE: the parent framework excerpt contradicts the claim "
    "     (the restriction is stated as national/country-wide, or counts the "
    "     same restriction at parent level as applying across the country).\n"
    "   - UNVERIFIABLE: neither the record's sources nor the parent excerpt "
    "     settles it.\n"
    "   If no non-application claim exists, verdict = NO_CLAIM.\n"
    "3. Does the record's out-of-scope / not-counted section list something the "
    "parent record DOES count (i.e. the same restriction/ban/duty is counted at "
    "country level but exported out of this division)? Answer yes/no and name it.\n"
    "Return ONLY a JSON object with keys: claims_non_application (bool), "
    "claim_quote (string, '' if none), verdict "
    "(SUPPORTED|FALSE_DIVERGENCE|UNVERIFIABLE|NO_CLAIM), evidence (string: the "
    "specific source/parent text relied on, or why unverifiable), "
    "parent_counts_exported (bool), parent_counts_what (string, '' if none). "
    "Keep each string under 300 characters."
)


def clean(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(t or ""))).strip()


def flagged_sentences(rec):
    out = []
    for f in FIELDS:
        t = clean(rec.get(f))
        if not t:
            continue
        for m in STRICT.finditer(t):
            s = max(0, m.start() - 200)
            e = min(len(t), m.end() + 240)
            out.append(f"[{f}] ...{t[s:e]}...")
    # dedupe, cap
    seen, res = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            res.append(x)
    return res[:8]


def build_user(rec, parent_rec, sid):
    lines = [
        f"RECORD: {rec.get('name')} (id {sid}, parent iso {rec.get('iso3')}, "
        f"dossier={bool(rec.get('dossier'))})",
        f"FLAGGED SENTENCES ({len(flagged_sentences(rec))}):",
    ]
    lines += flagged_sentences(rec)
    boo = clean(rec.get("blindOutOfScope") or rec.get("outOfScopeNotes"))
    if boo:
        lines.append("RECORD OUT-OF-SCOPE TEXT (rendered to raters as "
                     "'DELIBERATELY NOT COUNTED'):\n" + boo[:3000])
    srcs = rec.get("sources") or []
    if srcs:
        lines.append("RECORD SOURCES (url + claim):")
        for s in srcs[:10]:
            if isinstance(s, dict):
                lines.append(f"- {s.get('url','')} :: {str(s.get('summary',''))[:280]}")
            else:
                lines.append(f"- {str(s)[:280]}")
    if parent_rec:
        ps = clean(parent_rec.get("summary"))
        lines.append(f"PARENT COUNTRY ({parent_rec.get('name')}) SUMMARY EXCERPT:\n"
                     + ps[:2800])
        pb = clean(parent_rec.get("blindOutOfScope") or parent_rec.get("outOfScopeNotes"))
        if pb:
            lines.append("PARENT OUT-OF-SCOPE TEXT:\n" + pb[:1200])
    return "\n".join(lines)


def parse(raw):
    try:
        inner = json.loads(raw)
        content = inner["choices"][0]["message"]["content"]
    except Exception:
        content = raw
    m = re.search(r"\{.*\}", content, re.S)
    if not m:
        raise ValueError("no JSON in judge reply")
    return json.loads(m.group(0))


def main():
    A = json.loads(ADMIN1.read_text(encoding="utf-8"))
    C = json.loads(COUNTRIES.read_text(encoding="utf-8"))
    targets = {}
    for sid, rec in A.items():
        if any(STRICT.search(clean(rec.get(f))) for f in FIELDS):
            targets[sid] = rec
    print(f"flagged records (textual patterns): {len(targets)}", flush=True)

    done = {}
    if OUT.exists():
        prev = json.loads(OUT.read_text(encoding="utf-8"))
        done = {r["sid"]: r for r in prev.get("results", [])}
        print(f"resuming: {len(done)} already judged", flush=True)
    todo = [sid for sid in targets if sid not in done]
    print(f"to judge this run: {len(todo)}", flush=True)

    results = list(done.values())

    def one(sid):
        rec = targets[sid]
        parent = C.get(rec.get("parentIso3") or rec.get("iso3")) or {}
        user = build_user(rec, parent, sid)
        t0 = time.time()
        try:
            resp = call_v4("mimo", SYSTEM, user)
            j = parse(resp.get("raw_response", ""))
            return {"sid": sid, "iso3": rec.get("iso3"), "name": rec.get("name"),
                    "dossier": bool(rec.get("dossier")),
                    "judge": j,
                    "usage": resp.get("usage", {}),
                    "seconds": round(time.time() - t0, 1)}
        except Exception as e:  # one attempt, no retries
            return {"sid": sid, "iso3": rec.get("iso3"), "name": rec.get("name"),
                    "dossier": bool(rec.get("dossier")), "error": str(e)[:300]}

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(one, sid): sid for sid in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            r = fut.result()
            results.append(r)
            if i % 10 == 0 or i == len(todo):
                OUT.write_text(json.dumps(
                    {"audit": "dossier_false_divergence", "n_flagged": len(targets),
                     "n_done": len(results), "results": results},
                    indent=1, ensure_ascii=False), encoding="utf-8")
                print(f"... {i}/{len(todo)} judged", flush=True)
    OUT.write_text(json.dumps(
        {"audit": "dossier_false_divergence", "n_flagged": len(targets),
         "n_done": len(results), "results": results},
        indent=1, ensure_ascii=False), encoding="utf-8")
    print("DONE", len(results))


if __name__ == "__main__":
    main()
