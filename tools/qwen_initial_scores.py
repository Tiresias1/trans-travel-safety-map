#!/usr/bin/env python3
"""Run the lightweight model (qwen3.8-flash) through research/ADM1_SCORING_PROMPT.md
for initial ADM1 scoring of dossier countries — the automated form of the hand-off.

For each ISO3:
  1. builds the unit list exactly like tools/adm1_list.py (same exclusion rules),
  2. sends the scoring prompt + the country's dossier + unit list to the model,
  3. parses JSONL records (tolerating fences/thinking text), canonicalises names
     and shapeIDs against the boundary data,
  4. writes data/admin1_scores/<ISO3>.jsonl and merges via apply_admin1_scores.py
     (dry-run then real), reporting FAILs.

The model only creates records for units deviating >=0.02 from the national score;
an empty output file is a valid result (inheritance).

Usage:
    python3 tools/qwen_initial_scores.py MEX CAN GBR
    python3 tools/qwen_initial_scores.py --all
    python3 tools/qwen_initial_scores.py --all --workers 3
Key: pass --api-key or set QWEN_API_KEY (file path accepted: @/tmp/.qwen_key).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ALL_ISOS = ["MEX", "CAN", "GBR", "AUS", "BRA", "IND", "DEU", "ESP", "COL", "ARG",
            "ITA", "POL", "NGA", "IDN", "MYS", "TUR", "RUS", "ZAF", "FRA", "PHL",
            "PER", "CHL", "KOR"]

BASEURL = "https://token-plan.ap-southeast-1.maas.aliyuncs.com/apps/anthropic"
MODEL = "qwen3.8-flash"


def call_api(key: str, system_text: str, user_text: str,
             reasoning_tokens: int = 10000, max_output: int = 24000,
             timeout: float = 600.0, retries: int = 4, backoff: float = 2.0,
             attempt: int = 0) -> dict:
    body = {
        "model": MODEL,
        "max_tokens": reasoning_tokens + max_output,
        "system": [{"type": "text", "text": system_text}],
        "messages": [{"role": "user", "content": [{"type": "text", "text": user_text}]}],
        "thinking": {"type": "enabled", "budget_tokens": reasoning_tokens},
    }
    headers = {"content-type": "application/json", "anthropic-version": "2023-06-01",
               "x-api-key": key, "Authorization": f"Bearer {key}"}
    req = urllib.request.Request(BASEURL + "/v1/messages",
                                 data=json.dumps(body).encode("utf-8"),
                                 headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        if e.code in (429, 500, 502, 503, 504) and attempt < retries:
            time.sleep(backoff * (2 ** attempt) + random.random())
            return call_api(key, system_text, user_text, reasoning_tokens, max_output,
                            timeout, retries, backoff, attempt + 1)
        raise RuntimeError(f"HTTP {e.code}: {detail}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        if attempt < retries:
            time.sleep(backoff * (2 ** attempt) + random.random())
            return call_api(key, system_text, user_text, reasoning_tokens, max_output,
                            timeout, retries, backoff, attempt + 1)
        raise RuntimeError(f"request failed: {e}") from None


def unit_list(iso: str) -> tuple[list[tuple[str, str]], float, str, str]:
    """Return [(shapeID, name)], national score, country name, adm1_list md output."""
    out = subprocess.run([sys.executable, str(ROOT / "tools" / "adm1_list.py"), iso,
                          "--format", "md"], capture_output=True, text=True, check=True)
    countries = json.loads((ROOT / "data" / "countries.json").read_text())
    c = countries[iso]
    units = []
    for line in out.stdout.splitlines():
        m = re.match(r"- (.+?) \(`([^`]+)`\)", line.strip())
        if m:
            units.append((m.group(2), m.group(1)))
    return units, float(c["score"]), c["name"], out.stdout


def build_prompt(iso: str, units, nat: float, cname: str, unit_md: str,
                 scored_already: list[str]) -> tuple[str, str]:
    scoring = (ROOT / "research" / "ADM1_SCORING_PROMPT.md").read_text(encoding="utf-8")
    # trim the meta sections meant for the human operator
    scoring = scoring.split("## Country order")[0]
    dossier = (ROOT / "research" / "admin1" / f"{iso}.md").read_text(encoding="utf-8")
    system = ("You are the initial-scoring model for a travel-safety map scoring risk to "
              "a transgender visitor if discovered/outed. Follow the mission, scale and "
              "rules below exactly. Output ONLY JSONL record lines (one JSON object per "
              "line) — no prose, no markdown fences, no preamble.\n\n" + scoring)
    already = ("\nUnits that ALREADY have records (do NOT emit them): "
               + ", ".join(scored_already) + "\n") if scored_already else ""
    user = (f"Score country {iso} ({cname}), national score {nat:.2f}.\n\n"
            f"## Unit list (shapeID in backticks — copy exactly)\n{unit_md}\n"
            f"{already}\n"
            f"## Dossier (research/admin1/{iso}.md)\n{dossier}\n\n"
            f"Emit one JSONL line per unit whose evidence puts it >=0.02 from the "
            f"national score, per the rules. Today's date for researchedAt: "
            f"{date.today().isoformat()}.")
    return system, user


def parse_records(text: str, units, nat: float) -> tuple[list[dict], list[str]]:
    canon = {sid: name for sid, name in units}
    valid_ids = set(canon)
    recs, warns = {}, []
    # robust extraction: objects may span multiple lines (literal newlines inside
    # summary strings), so walk the text with a streaming decoder instead of
    # parsing line-by-line
    dec = json.JSONDecoder()
    idx = 0
    while True:
        start = text.find("{", idx)
        if start < 0:
            break
        try:
            r, end = dec.raw_decode(text, start)
            idx = end
        except json.JSONDecodeError:
            warns.append(f"unparsable fragment at char {start}: {text[start:start+60]!r}")
            nxt = text.find("{", start + 1)
            idx = nxt if nxt > 0 else len(text)
            continue
        if not isinstance(r, dict) or "shapeID" not in r:
            continue
        sid = r.get("shapeID")
        if sid not in valid_ids:
            # try to rescue by exact name match
            by_name = {n: s for s, n in canon.items()}
            sid = by_name.get(r.get("name", ""), None)
            if sid is None:
                warns.append(f"unknown shapeID dropped: {r.get('shapeID')!r} {r.get('name')!r}")
                continue
        r["shapeID"] = sid
        r["name"] = canon[sid]  # canonical name always
        try:
            sc = float(r.get("score"))
        except (TypeError, ValueError):
            warns.append(f"bad score dropped: {canon[sid]}")
            continue
        if not 0 <= sc <= 1:
            warns.append(f"out-of-range score dropped: {canon[sid]} {sc}")
            continue
        r["score"] = round(sc, 4)
        summ = r.get("summary", "")
        if not (1 <= summ.count("<p") <= 4) and summ:
            summ = f"<p>{summ}</p>" if "<p" not in summ else summ
        r["summary"] = summ[:2500]
        srcs = r.get("sources") or []
        srcs = [u for u in srcs if isinstance(u, str) and u.startswith("http")]
        if not srcs:
            srcs = ["https://outrightinternational.org/"]
            warns.append(f"{canon[sid]}: no usable sources; default inserted")
        r["sources"] = srcs[:6]
        r["researchedAt"] = date.today().isoformat()
        r.pop("estimated", None)  # these are dossier-grounded, not route-3
        recs[sid] = r
    return list(recs.values()), warns


def score_country(iso: str, key: str, apply_merge: bool = True) -> dict:
    units, nat, cname, unit_md = unit_list(iso)
    admin1 = json.loads((ROOT / "data" / "admin1.json").read_text())
    scored = [n for sid, n in units if sid in admin1]
    system, user = build_prompt(iso, units, nat, cname, unit_md, scored)
    t0 = time.time()
    resp = call_api(key, system, user)
    dt = time.time() - t0
    text = "".join(b.get("text", "") for b in resp.get("content", [])
                   if isinstance(b, dict) and b.get("type") == "text")
    stop = resp.get("stop_reason")
    recs, warns = parse_records(text, units, nat)
    if stop == "max_tokens":
        warns.append("OUTPUT TRUNCATED (stop_reason=max_tokens) — records after the "
                     "cut are missing; consider a continuation run")
    outdir = ROOT / "data" / "admin1_scores"
    outdir.mkdir(exist_ok=True)
    outpath = outdir / f"{iso}.jsonl"
    outpath.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs)
                       + ("\n" if recs else ""), encoding="utf-8")
    result = {"iso": iso, "units": len(units), "records": len(recs),
              "seconds": round(dt), "stop": stop, "warns": warns,
              "file": str(outpath)}
    if apply_merge and recs:
        for dry in (True, False):
            cmd = [sys.executable, str(ROOT / "tools" / "apply_admin1_scores.py"),
                   "--in", str(outpath)] + (["--dry-run"] if dry else [])
            p = subprocess.run(cmd, capture_output=True, text=True)
            fails = p.stdout.count("[FAIL]")
            if fails and dry:
                result["apply_fails_dryrun"] = fails
                result["apply_stdout"] = p.stdout[-1500:]
                break  # do not merge with failures; report instead
            if not dry:
                result["merged"] = True
                result["apply_tail"] = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("isos", nargs="*", help="ISO3 codes (default: none)")
    ap.add_argument("--all", action="store_true", help="all 23 pending dossier countries")
    ap.add_argument("--api-key", default=os.environ.get("QWEN_API_KEY", ""))
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--no-merge", action="store_true",
                    help="write JSONL only; do not run apply_admin1_scores")
    args = ap.parse_args()

    key = args.api_key
    if key.startswith("@"):
        key = Path(key[1:]).read_text().strip()
    if not key:
        print("error: no API key (--api-key or QWEN_API_KEY)", file=sys.stderr)
        return 2
    isos = [i.upper() for i in args.isos] or (ALL_ISOS if args.all else [])
    if not isos:
        print("error: give ISO3s or --all", file=sys.stderr)
        return 2

    def run(iso):
        try:
            r = score_country(iso, key, apply_merge=not args.no_merge)
            print(json.dumps(r, ensure_ascii=False), flush=True)
            return r
        except Exception as e:  # keep the batch alive
            print(json.dumps({"iso": iso, "error": str(e)[:400]}), flush=True)
            return {"iso": iso, "error": str(e)[:400]}

    if args.workers > 1 and len(isos) > 1:
        with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
            results = list(ex.map(run, isos))
    else:
        results = [run(i) for i in isos]

    errs = [r for r in results if "error" in r]
    truncs = [r for r in results if any("TRUNCATED" in w for w in r.get("warns", []))]
    fails = [r for r in results if r.get("apply_fails_dryrun")]
    print(f"\ndone: {len(results)} countries · {sum(r.get('records',0) for r in results)} "
          f"records · errors {len(errs)} · truncated {len(truncs)} · dry-run-fails {len(fails)}")
    for r in errs + truncs + fails:
        print("  check:", r.get("iso"), r.get("error", "") or r.get("warns", "")
              or r.get("apply_stdout", ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
