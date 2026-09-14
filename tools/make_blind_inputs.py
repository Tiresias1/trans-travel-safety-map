#!/usr/bin/env python3
"""Extract identity-free payloads for the blind-anonymisation step.

Reads data/countries.json and writes one JSONL line per record containing ONLY the
fields that may be shown to the anonymising model:

    summary  outOfScopeNotes  localsOnly  tangentialFactors  sources[].summary

`sources[].url` is stripped. name / score / band / rank / anchorRefs / researchedAt /
comparisons are never included — see tools/blind_fields.md for why.

Each output line is {"iso": ..., "n": ..., "payload": {...}}. Pass **only** `payload`
to the model; `iso` and `n` are routing metadata for your harness.

Usage:
    python3 tools/make_blind_inputs.py
    python3 tools/make_blind_inputs.py --only WSM TON FJI
    python3 tools/make_blind_inputs.py --out /tmp/payloads.jsonl
    python3 tools/make_blind_inputs.py --emit-prompt
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# source field -> payload key
ALLOWED = {
    "summary": "summary",
    "outOfScopeNotes": "outOfScopeNotes",
    "localsOnly": "localsOnly",
    "tangentialFactors": "tangentialFactors",
}
FORBIDDEN = ("name", "score", "band", "rank", "anchorRefs", "researchedAt",
             "comparisons")


def build_payload(rec: dict) -> dict:
    payload = {}
    for src, key in ALLOWED.items():
        val = rec.get(src)
        if isinstance(val, str) and val.strip():
            payload[key] = val.strip()
    sums = [s.get("summary", "").strip() for s in rec.get("sources", [])
            if isinstance(s, dict)]
    sums = [s for s in sums if s]
    if sums:
        payload["sourceSummaries"] = sums
    # hard guarantee: no forbidden key can slip through
    for f in FORBIDDEN:
        payload.pop(f, None)
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--countries-file", default=str(ROOT / "data" / "countries.json"))
    ap.add_argument("--out", default=str(ROOT / "data" / "blind_inputs" / "payloads.jsonl"))
    ap.add_argument("--only", nargs="*", default=None,
                    help="restrict to these ISO3 codes")
    ap.add_argument("--emit-prompt", action="store_true",
                    help="print the instruction block for the anonymising model and exit")
    ap.add_argument("--stats", action="store_true", help="print size stats and exit")
    args = ap.parse_args()

    if args.emit_prompt:
        print((ROOT / "tools" / "blind_fields.md").read_text(encoding="utf-8")
              .split("## Prompt for the lightweight model")[1]
              .split("---")[0].strip())
        return 0

    countries = json.loads(Path(args.countries_file).read_text(encoding="utf-8"))
    isos = args.only or sorted(countries)
    missing = [i for i in isos if i not in countries]
    if missing:
        print(f"error: unknown ISO codes: {missing}", file=sys.stderr)
        return 2

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    total_chars = 0
    n_written = 0
    sizes = []
    with out.open("w", encoding="utf-8") as fh:
        for n, iso in enumerate(isos, 1):
            payload = build_payload(countries[iso])
            if not payload:
                print(f"warn: {iso} produced an empty payload", file=sys.stderr)
                continue
            fh.write(json.dumps({"iso": iso, "n": n, "payload": payload},
                                ensure_ascii=False) + "\n")
            c = len(json.dumps(payload, ensure_ascii=False))
            total_chars += c
            sizes.append(c)
            n_written += 1

    if args.stats:
        sizes.sort()
        print(f"records: {n_written}")
        print(f"payload chars: total {total_chars:,} · avg {total_chars//max(n_written,1):,} "
              f"· median {sizes[len(sizes)//2]:,} · max {sizes[-1]:,}")
        print(f"approx input tokens for all records: ~{total_chars//4:,}")
        return 0

    print(f"wrote {n_written} payloads -> {out}")
    print(f"total {total_chars:,} chars (~{total_chars//4:,} tokens)")
    print("Pass only the `payload` object to the model; `iso`/`n` are routing metadata.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
