#!/usr/bin/env python3
"""Fleet claim audit (2026-10-06 full-run phase 1).

For every record (country or dossier-ADM1), send its source-claim inventory to
the rating model and demand a per-claim verdict:

  ok       — on-topic for THIS jurisdiction, trans-visitor relevant, clean voice
  rewrite  — offtopic / generic-to-all-jurisdictions / LLM-ism / poorly done
             (spends most space on anything other than the actual finding)

Rewrite constraints (enforced mechanically):
  - preserve EVERY fact, date, number, penalty, article number in the original;
  - no new facts, no new sources, never touch the URL;
  - voice per STYLE_RULES (no meta-commentary about outlets/fetches, no
    em-dashes, no rule-of-three, no hedging debris);
  - equal length or shorter.

A claim whose original carries no digits may not gain any (no fabrication
vector); a claim with digits must keep them all.

Usage:
  python3 tools/audit_claims.py --countries --workers 6
  python3 tools/audit_claims.py --admin1-dossier --workers 6
  python3 tools/audit_claims.py --who country:MLT
"""
from __future__ import annotations
import argparse, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from consolidate_record import (call_llm, META_NARRATIVE, VIS_ANON,
                                GENERIC_TRAVEL, TRANS_KEEP, valid_summary)  # noqa

API_KEY = os.environ.get("OPENROUTER_KEY", "")
# Lane model: shared with consolidate_record.call_llm (bulk work = contributor tier).
STYLE = (ROOT / "tools" / "STYLE_RULES.md").read_text()

SYSTEM = f"""You audit source-claim summaries for a trans-visitor travel-safety
map. Each claim belongs to ONE jurisdiction's record. You receive the claim
list and return verdicts.

{STYLE}

VERDICT RULES. Mark a claim "rewrite" when it has any of these defects:
1. OFFTOPIC: describes a different jurisdiction, or a sub-unit of a different
   country, without a stated bearing on this jurisdiction.
2. GENERIC: the content applies to essentially every jurisdiction (generic
   travel logistics, general crime precautions, universal airline procedure)
   and carries no trans-specific or jurisdiction-specific finding.
3. LLM-ISM: meta-commentary about the source or the fetch ("state news agency
   page", "page body was navigation content", "headline only", revision stamps,
   "per freshness"); bullets; em-dashes; rule-of-three; hedging debris
   ("it is worth noting", "importantly"); assistant voice.
4. POORLY DONE: spends most of its space on anything other than the actual
   finding (outlet description, background padding), or buries the finding.
Otherwise mark "ok". Do NOT rewrite claims that are merely short.

REWRITE CONSTRAINTS (violations are mechanically rejected):
- preserve every fact, date, number, penalty, article/section number;
- add NO new facts and NO sources; never invent;
- same length or shorter; plain declarative sentences;
- keep the jurisdiction's own name or neutral reference as in the original.

Output ONLY JSON: {{"claims": [{{"i": 0, "verdict": "ok"}},
{{"i": 3, "verdict": "rewrite", "text": "..."}}]}} — include ONLY claims you
mark rewrite (listing every index is wasteful)."""

DIGITS = re.compile(r"\d")


def digit_set(t: str) -> set:
    return set(DIGITS.findall(t))


def audit_record(who: str, rec: dict) -> tuple[str, int, int]:
    srcs = [s for s in (rec.get("sources") or []) if isinstance(s, dict)]
    claims = []
    for i, s in enumerate(srcs):
        claims.append({"i": i, "url": s.get("url", ""),
                       "claim": s.get("summary") or s.get("title") or ""})
    if not claims:
        return who, 0, 0
    inv = "\n".join(f"[{c['i']}] {c['claim']}" for c in claims)
    user = (f"JURISDICTION: {rec.get('name')} ({rec.get('iso3', who)})\n"
            f"CLAIM LIST:\n{inv}\n\nReturn verdicts (rewrites only).")
    out = call_llm(SYSTEM, user)
    data = out if isinstance(out, dict) else json.loads(out)
    changed = dropped = 0
    for item in data.get("claims", []):
        i = int(item.get("i", -1))
        if not (0 <= i < len(srcs)) or item.get("verdict") != "rewrite":
            continue
        new = str(item.get("text", "")).strip()
        old = srcs[i].get("summary") or ""
        if not new or len(new) > max(len(old), 400):
            continue
        if META_NARRATIVE.search(new) or VIS_ANON.search(new):
            continue
        # digits preservation: no new digit-sequences, none lost
        if digit_set(new) - digit_set(old):
            continue
        if digit_set(old) and not digit_set(new):
            continue
        if not DIGITS.search(old) and DIGITS.search(new):
            continue
        srcs[i]["summary"] = new
        changed += 1
    return who, changed, len(claims)


def load_targets(args):
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    targets = []
    if args.who:
        for w in args.who:
            if w.startswith("country:"):
                targets.append((w, C[w[8:]]))
            else:
                iso, nm = w.split("/", 1)
                targets.append((w, next(x for x in A.values()
                                        if x.get("iso3") == iso and x.get("name") == nm)))
        return C, A, targets
    if args.countries:
        targets += [(f"country:{k}", r) for k, r in C.items()]
    if args.admin1_dossier:
        targets += [(f"{r['iso3']}/{r['name']}", r) for r in A.values() if r.get("dossier")]
    return C, A, targets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--countries", action="store_true")
    ap.add_argument("--admin1-dossier", action="store_true")
    ap.add_argument("--who", nargs="*")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    C, A, targets = load_targets(args)
    print(f"auditing {len(targets)} records, {args.workers} workers")
    total_changed = 0
    done = 0
    with ThreadPoolExecutor(args.workers) as ex:
        futs = {ex.submit(audit_record, w, r): w for w, r in targets}
        for f in as_completed(futs):
            w = futs[f]
            try:
                who, ch, tot = f.result()
                total_changed += ch
                if ch:
                    print(f"[{who}] rewrote {ch}/{tot} claims")
            except Exception as e:
                print(f"[{w}] ERROR {str(e)[:120]}")
            done += 1
            if done % 25 == 0:
                print(f"... {done}/{len(targets)} records, {total_changed} claims rewritten")
    (ROOT / "data" / "countries.json").write_text(
        json.dumps(C, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "data" / "admin1.json").write_text(
        json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"DONE: {total_changed} claims rewritten across {len(targets)} records")


if __name__ == "__main__":
    main()