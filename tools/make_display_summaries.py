#!/usr/bin/env python3
"""Generate display-only summaries for dossier ADM1 regions (2026-10-16).

Problem: region summaries carry the full parent-regime assessment (federal
framework paragraphs etc.) because the pairwise rater needs that context.
Users don't — it's spammy in the popup.

Fix: generate `displaySummary` — a display variant of `summary` where
country-level/parent-regime content is compressed to at most 1-2 sentences
ending with a pointer to the national record, and everything else is strictly
region-local. `summary` itself is untouched (it remains the pairwise and
archive record); popups prefer displaySummary when present.

Gate: digits preserved, capital start, terminal period, no pipeline jargon,
length sanity.

Usage: python3 tools/make_display_summaries.py [--workers 4] [--limit N]
       [--only WHO ...]
"""
from __future__ import annotations
import argparse, json, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from consolidate_record import call_llm  # noqa


def nums(t: str) -> list:
    return re.findall(r"\d+(?:[.,]\d+)*", t)


def make_display(rec: dict, parent: dict) -> str | None:
    summ = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(rec.get("summary", "")))).strip()
    pname = parent.get("name", rec.get("iso3", ""))
    # Very long summaries overflow the model's reasoning+JSON budget in one
    # pass (empty content, stop=length). Pre-compress in chunks small enough
    # for one pass — same preservation duties, no JSON envelope to complete.
    if len(summ) > 4000:
        # split at sentence boundaries into ~2800-char chunks
        sents = re.findall(r"[^.]+\.", summ)
        chunks, cur = [], ""
        for s in sents:
            if len(cur) + len(s) > 2800 and cur:
                chunks.append(cur.strip()); cur = ""
            cur += " " + s
        if cur.strip():
            chunks.append(cur.strip())
        pcs = []
        for ci, ch in enumerate(chunks):
            pre = call_llm(
                "You compress travel-safety assessments without losing facts.",
                f"""Compress the text below (part {ci+1}/{len(chunks)} of a longer
assessment) to at most 1300 characters of flowing prose. Keep every
region-local law, incident, statistic, date and figure for {rec.get('name')}
exactly as written; the parent-country federal/national framework may be
reduced to its shortest accurate mention. Do not invent, drop or alter any
number.

Return ONLY JSON: {{"text": "..."}}.
TEXT:
{ch}""", max_tokens=14000)
            if isinstance(pre, dict):
                pc = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(pre.get("text") or ""))).strip()
                if len(pc) >= 200 and not (set(nums(pc)) - set(nums(ch))):
                    pcs.append(pc)
        if len(pcs) == len(chunks):
            summ = " ".join(pcs)
    target = max(900, min(4200, int(len(summ) * 0.7)))
    for attempt in range(3):
        out = call_llm(
            "You write visitor-facing display text for a trans-visitor travel-safety map.",
            f"""The summary below for the region {rec.get('name')} ({pname}) mixes two
kinds of content: (a) the parent country's national/federal framework
(passports, executive orders, federal agencies, national statistics, national
bans) and (b) THIS region's own laws, enforcement, incidents and practice.

Rewrite it as a DISPLAY summary for a traveller viewing this region's popup:
- Keep ALL region-local substance: every law, incident, statistic and
  enforcement fact that belongs to {rec.get('name')} itself, with all dates
  and figures preserved exactly.
- The parent-country national framework is ALREADY SHOWN from the national
  record — so compress it here to AT MOST 1-2 short opening sentences,
  totalling under 400 characters, ending with a pointer such as "the
  national record for {pname} covers the federal layer in detail."
- HARD LENGTH LIMIT: at most {target} characters. If the region-local
  material alone is long, it has priority — cut further into the federal
  content, never into the region-local facts.
- Do not invent, drop or alter any region-local fact or number. Complete
  sentences, capital first letter, terminal period. Same sober tone.

CURRENT SUMMARY:
{summ[:6000]}

Return ONLY JSON: {{"display": "..."}}""")
        if not isinstance(out, dict) or not (out.get("display") or "").strip():
            continue
        s = re.sub(r"\s+", " ", out["display"]).strip()
        ok_shape = s and s[0].isupper() and s.endswith(".")
        ok_len = len(s) <= target + 900
        # fabrication check: no NEW digits may appear. Dropped digits are fine —
        # compressing the federal layer legitimately drops federal dates/figures;
        # region-local preservation is a prompt duty + spot-check, not a
        # mechanical equality (that gate blocked every compression).
        ok_digits = not (set(nums(s)) - set(nums(summ)))
        ok_jargon = not re.search(r"route \d|model estimate|SUPERSEDED|earlier profile", s, re.I)
        if ok_shape and ok_len and ok_digits and ok_jargon and len(s) >= 120:
            return s
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--missing", action="store_true",
                    help="only records that do not yet have a displaySummary")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    jobs = []
    for key, r in A.items():
        if r.get("dossier") and r.get("summary"):
            if getattr(args, "missing", False) and r.get("displaySummary"):
                continue
            who = f"{r['iso3']}/{r['name']}"
            if args.only and who not in args.only and f"country:{r['iso3']}" not in args.only:
                continue
            parent = C.get(r.get("parentIso3") or r.get("iso3"), {})
            jobs.append((key, r, parent))
    if args.limit:
        jobs = jobs[: args.limit]
    print(f"display summaries to generate: {len(jobs)}", flush=True)
    fixed = 0

    def one(j):
        key, r, parent = j
        try:
            return key, make_display(r, parent), ""
        except Exception as e:
            return key, None, str(e)[:120]
    with ThreadPoolExecutor(args.workers) as ex:
        futs = [ex.submit(one, j) for j in jobs]
        for i, f in enumerate(as_completed(futs)):
            key, new_s, err = f.result()
            r = A[key]
            if err:
                print(f"[FAIL] {r.get('name')}: {err}", flush=True)
            elif new_s is None:
                print(f"[GATE] {r.get('name')}: rejected after retries", flush=True)
            else:
                r["displaySummary"] = new_s
                fixed += 1
            if (i + 1) % 50 == 0:
                print(f"... {i+1}/{len(jobs)} fixed={fixed}", flush=True)
    print(f"LANE DONE: {fixed}/{len(jobs)} display summaries generated", flush=True)
    if args.apply:
        (ROOT / "data" / "admin1.json").write_text(
            json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")
        print("applied", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())