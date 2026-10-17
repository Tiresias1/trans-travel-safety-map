#!/usr/bin/env python3
"""Repair the front-truncated model-estimate summaries (2026-10-16).

Root cause: fix_nondossier_text.py's mechanical strip `Model estimate[^:]*:`
was greedy to the next colon and ate the region's name and opening clause,
leaving 1,423 estimate summaries starting mid-sentence ("capital orbit.
Assessed relative to...").

The eaten text is unrecoverable, so this lane REWRITES: fragment + national
context + region name -> complete 2-4 sentence estimate summary. Same facts,
same hedging discipline, complete sentences. Gate: terminal punctuation,
capital start, digit preservation.

Usage: python3 tools/fix_estimate_fragments.py [--workers 4] [--limit N]
"""
from __future__ import annotations
import argparse, json, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from consolidate_record import call_llm  # noqa

TEMPLATE = "No sub-national signal was identified; the national assessment applies here."


def is_fragment(s: str) -> bool:
    s = re.sub(r"<[^>]+>", " ", s).strip()
    if s == TEMPLATE or not s:
        return False
    return s[0].islower() or not s.endswith(".") or (s.count(",") >= 2 and len(s) < 200)


def fix_record(rec: dict, national: str) -> str | None:
    frag = re.sub(r"<[^>]+>", " ", str(rec.get("summary", ""))).strip()
    for attempt in range(3):
        out = call_llm(
            "You complete truncated model-estimate summaries for a trans-visitor map.",
            f"""The summary below for {rec.get('name')} ({rec.get('iso3')}) was truncated at
its front by a data-processing bug: it now begins mid-sentence. Rewrite it as a
complete 2-4 sentence model-estimate summary: what this division is (its role,
city, region character) and what that means for a trans visitor relative to the
national picture. STRICT: use ONLY the facts present in the fragment plus the
bare fact that this division belongs to {rec.get('iso3')} — do NOT add any
dates, statistics, names, or events not in the fragment. Keep the "Assessed
relative to the national picture" framing. Complete sentences, capital first
letter, terminal period.

FRAGMENT: {frag}

Return ONLY JSON: {{"summary": "..."}}""")
        if isinstance(out, dict) and (out.get("summary") or "").strip():
            s = out["summary"].strip()
            def nums(t):
                return re.findall(r"\d+(?:[.,]\d+)*", t)
            if s and s[0].isupper() and nums(frag) == nums(s) and s.endswith("."):
                return s
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    jobs = []
    for key, r in A.items():
        if r.get("estimated") and is_fragment(str(r.get("summary", ""))):
            jobs.append((key, r))
    if args.limit:
        jobs = jobs[: args.limit]
    print(f"fragments to repair: {len(jobs)}", flush=True)
    fixed = 0

    def one(j):
        key, r = j
        try:
            nat = re.sub(r"<[^>]+>", " ", str(C.get(r.get("iso3"), {}).get("summary", "")))
            new_s = fix_record(r, nat)
            if new_s is None:
                print(f"[GATE] {r.get('name')}: rewrite rejected (invention/lowercase/digits)", flush=True)
            return key, new_s, ""
        except Exception as e:
            return key, None, str(e)[:120]
    with ThreadPoolExecutor(args.workers) as ex:
        futs = [ex.submit(one, j) for j in jobs]
        for i, f in enumerate(as_completed(futs)):
            key, new_s, err = f.result()
            if err:
                print(f"[FAIL] {key}: {err}", flush=True)
            elif new_s:
                pass
                A[key]["summary"] = new_s
                fixed += 1
            if (i + 1) % 50 == 0:
                print(f"... {i+1}/{len(jobs)} fixed={fixed}", flush=True)
    print(f"LANE DONE: {fixed}/{len(jobs)} rewritten", flush=True)
    if args.apply:
        (ROOT / "data" / "admin1.json").write_text(
            json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")
        print("applied", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
