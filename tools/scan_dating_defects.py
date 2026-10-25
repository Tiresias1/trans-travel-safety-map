#!/usr/bin/env python3
"""Detect dating/recency defects in dossiers (2026-10-25, mechanism not patch).

Classes detected (per record, per claim/summary):
  SNAPSHOT   — a legal statement pinned to a past year ("as of <year>", "at that
               time", "by <year>") while another claim carries a LATER date: the
               dossier contains the present rule, but a stale snapshot is stated
               as if current.
  STALE-ONLY — the only dated violence/incidents are old (>= 10 years) with no
               later documented instance.
  UNDATED-PREVALENCE — prevalence wording with no figure/period.

Emits a queue (who, class, evidence) for regeneration. It NEVER edits text:
the summarizer rules fix the output; this only finds the records.

Usage: python3 tools/scan_dating_defects.py [--json OUT]
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAP = re.compile(r"as of (?:[A-Z][a-z]+ )?(\d{4})|at that time|by (\d{4})|in (\d{4}) the law", re.I)
VIO = re.compile(r"assault|attack|murder|kill|beat|kidnap|rap(?:e|ed)|violence|harass", re.I)
PREV = re.compile(r"\b(?:common|widespread|frequent|pervasive|rampant|routine|"
                  r"often|regularly|routinely|frequently|in many cases|typically)\b", re.I)
NUM = re.compile(r"\d+\s*%|\d+\s*(?:per|in)\s*\d|survey|study|census|monitor", re.I)


def years(t: str) -> list[int]:
    return [int(y) for y in re.findall(r"\b(1\d{3}|20[0-2]\d)\b", t)]


def scan_record(rec: dict) -> list[tuple]:
    out = []
    claims = [str(s.get("summary", "")) for s in (rec.get("sources") or [])
              if isinstance(s, dict)]
    summ = str(rec.get("summary") or "")
    all_years = years(" ".join(claims + [summ]))
    latest = max(all_years) if all_years else None
    # SNAPSHOT: past-pinned legal statement while a later date exists elsewhere
    for cl in claims:
        for m in SNAP.finditer(cl):
            yr = next((int(g) for g in m.groups() if g), None)
            if yr and latest and latest - yr >= 4:
                out.append(("SNAPSHOT", f"pinned to {yr}, dossier later dated {latest}",
                            cl[:110]))
                break
    # STALE-ONLY: violence present, all dates old
    vt = " ".join([summ] + claims)
    if VIO.search(vt) and all_years:
        vy = [y for y in all_years if y >= 2016]
        vint = [y for y in all_years if y < 2016]
        if vint and not vy:
            out.append(("STALE-ONLY", f"violence dates {sorted(set(vint))[-3:]}",
                        vt[max(0, vt.lower().find("attack") - 60):][:110]))
    # UNDATED-PREVALENCE
    for cl in [summ] + claims:
        if PREV.search(cl) and not NUM.search(cl):
            out.append(("UNDATED-PREVALENCE", "prevalence word without figure/period",
                        cl[:110]))
            break
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="/tmp/dating_defects.json")
    args = ap.parse_args()
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    findings = []
    for iso, rec in C.items():
        for cls, ev, snip in scan_record(rec):
            findings.append({"who": f"country:{iso}", "name": rec.get("name"),
                             "class": cls, "evidence": ev, "snippet": snip})
    for rec in A.values():
        if not rec.get("dossier"):
            continue
        for cls, ev, snip in scan_record(rec):
            findings.append({"who": f"{rec['iso3']}/{rec['name']}", "name": rec.get("name"),
                             "class": cls, "evidence": ev, "snippet": snip})
    Path(args.json).write_text(json.dumps(findings, ensure_ascii=False, indent=1))
    from collections import Counter
    print(f"findings: {len(findings)} | by class: {dict(Counter(f['class'] for f in findings))}")
    records = sorted({f["who"] for f in findings})
    print(f"records to regenerate: {len(records)}")
    for f in findings[:8]:
        print(f"  {f['class']:20} {f['who'][:28]:28} {f['evidence'][:52]}")
    Path("/tmp/dating_targets.txt").write_text("\n".join(records) + ("\n" if records else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
