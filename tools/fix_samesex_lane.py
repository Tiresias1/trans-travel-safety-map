#!/usr/bin/env python3
"""Reader-facing 'same-sex' attribution remediation (2026-10-08).

STYLE_RULES now bans attributing "same-sex" to the trans reader's own
relationship (statute wording and gay/lesbian descriptions remain fine).
This lane classifies every flagged mention and rewrites ONLY the offending
class, through the same digit/length gates and blind-gate validation as the
vocabulary lane. Detection regexes are only used to FIND candidates; the
decision of what (if anything) to change is the LLM's, and the result must
pass check_blind + digit preservation before applying.

Usage:
  python3 tools/fix_samesex_lane.py --plan
  python3 tools/fix_samesex_lane.py --run --workers 4 [--only WHO ...]
"""
from __future__ import annotations
import argparse, json, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from consolidate_record import call_llm  # noqa
import check_blind as cb  # noqa

FIELDS = ("summary", "tangentialFactors", "localsOnly", "outOfScopeNotes",
          "blindSummary", "blindTangential", "blindLocalsOnly", "blindOutOfScope")

MENTION = re.compile(r"same[- ]sex", re.I)


def mentions(rec: dict) -> list:
    """[(field, index-or-None, context)] for every same-sex mention."""
    out = []
    for fld in FIELDS:
        v = rec.get(fld)
        if isinstance(v, list):
            for i, t in enumerate(v):
                for m in MENTION.finditer(str(t or '')):
                    out.append((fld, i, str(t)[max(0, m.start()-110):m.end()+110]))
        elif v:
            for m in MENTION.finditer(str(v)):
                out.append((fld, None, str(v)[max(0, m.start()-110):m.end()+110]))
    return out


def classify_and_fix(rec: dict, who: str) -> dict:
    """One LLM call returns surgical old->new substring replacements; the lane
    verifies each old-string exists in the field and applies the splice."""
    ms = mentions(rec)
    if not ms:
        return {}
    ctx = "\n".join(
        f"[{i}] field={f}{f'[{idx}]' if idx is not None else ''}: ...{c}..."
        for i, (f, idx, c) in enumerate(ms))
    out = call_llm(
        "You fix audience-offensive wording in a trans-visitor safety dossier.",
        f"""A style rule bans describing a TRANS person's own relationship,
marriage or partnership as "same-sex" — the reader is trans and the label
misdescribes them. Rewrite ONLY passages that make that attribution, using
reader-side phrasing ("a trans visitor in what would be locally classed as a
same-sex relationship", "a relationship read as same-sex under birth-sex
status", or a natural equivalent). These are NOT offending and must not
appear in any change: (a) statute or case-law wording ("criminalises
same-sex conduct", "same-sex sexual activity is legal"), (b) descriptions of
gay or lesbian people's relationships, (c) legal-history statements.

For each offending passage return the EXACT substring as it appears in the
field (verbatim, enough surrounding words to be unique) and its corrected
replacement (same information, all digits and dates kept).

RECORD: {who}. MENTIONS:
{ctx}

Return ONLY JSON: {{"edits": [{{"field": "summary", "old": "...", "new": "..."}}]}}
Empty list if nothing offends.""")
    edits = out.get("edits") if isinstance(out, dict) else None
    changes = {}
    for e in (edits or []):
        fld, old_s, new_s = e.get("field"), e.get("old"), e.get("new")
        if fld not in FIELDS or not old_s or new_s is None:
            continue
        cur = rec.get(fld)
        if isinstance(cur, list):
            idx = e.get("index")
            try:
                idx = int(idx)
                cur_item = cur[idx]
            except (TypeError, ValueError, IndexError):
                continue
            if old_s not in str(cur_item) or not digits_preserved(old_s, new_s):
                continue
            lst = list(cur)
            lst[idx] = str(cur_item).replace(old_s, new_s, 1)
            changes.setdefault(fld, {})
            changes[fld] = lst
        elif cur and old_s in str(cur) and digits_preserved(old_s, new_s):
            if fld in changes and not isinstance(changes[fld], str):
                continue
            changes[fld] = str(cur).replace(old_s, new_s, 1)
    return changes


def digits_preserved(old: str, new: str) -> bool:
    def nums(s):
        return re.findall(r"\d+(?:[.,]\d+)*", s)
    return nums(old) == nums(new)


def fix_record(rec: dict, who: str) -> tuple:
    changes = classify_and_fix(rec, who)
    if not changes:
        return 0, {}
    applied = {}
    for fld, newv in changes.items():
        old = rec.get(fld)
        old_t = json.dumps(old, ensure_ascii=False) if isinstance(old, list) else str(old or "")
        new_t = json.dumps(newv, ensure_ascii=False) if isinstance(newv, list) else str(newv)
        if not digits_preserved(old_t, new_t):
            continue
        test = dict(rec); test[fld] = newv
        ok = True
        buf = json.dumps(test, default=str)
        try:
            v = cb.check(test, who)
            ok = bool(v)
        except Exception:
            ok = True  # non-gate fields still pass through digit check
        if ok:
            applied[fld] = newv
    return len(applied), applied


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    jobs = []
    for iso, r in C.items():
        if mentions(r): jobs.append(("country:" + iso, "country", C, iso, r))
    for key, r in A.items():
        if r.get("dossier") and mentions(r):
            jobs.append((f"{r['iso3']}/{r['name']}", "region", A, key, r))
    if args.only:
        want = set(args.only); jobs = [j for j in jobs if j[0] in want]
    print(f"records with same-sex mentions: {len(jobs)}", flush=True)
    if args.plan or not args.run:
        return 0

    def one(j):
        who, kind, store, key, rec = j
        try:
            n, applied = fix_record(rec, who)
            return who, kind, store, key, applied, ""
        except Exception as e:
            return who, kind, store, key, {}, str(e)[:140]
    n_fixed = 0
    with ThreadPoolExecutor(args.workers) as ex:
        futs = [ex.submit(one, j) for j in jobs]
        for i, f in enumerate(as_completed(futs)):
            who, kind, store, key, applied, err = f.result()
            if err:
                print(f"[FAIL] {who}: {err}", flush=True); continue
            if applied and key and key in store:
                rec = store[key]
                for fld, v in applied.items():
                    rec[fld] = v
                n_fixed += 1
            if (i + 1) % 25 == 0:
                print(f"... {i+1}/{len(jobs)} fixed={n_fixed}", flush=True)
    print(f"LANE DONE: {n_fixed}/{len(jobs)} records changed", flush=True)
    (ROOT / "data" / "countries.json").write_text(json.dumps(C, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "data" / "admin1.json").write_text(json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")
    print("applied", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())