#!/usr/bin/env python3
"""Turn research/wiki_cited/ leads into intake batches (2026-10-08).

The universal Wikipedia sweep harvested up to 10 cited references per
LGBTQ-rights article into research/wiki_cited/<who>.json as
{"who", "url", "leads": [{title, documents, detail}]}.

These are RAW leads (title + description only — no verified URL, no fetched
text), so they must go through the intake verification lane: this tool emits
data/intake_batches2/iNNN.json in the relevance-packet layout with
status:"lead-verification" so the existing consumers can fetch/verify/summarise
them unchanged. Leads that duplicate an already-cited URL (by slug match) are
dropped; nothing is added to the records here — the intake lane decides.

Usage:
  python3 tools/make_lead_batches.py [--out data/intake_batches2] [--per 8]
                                     [--only-who country:WSM ...]
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", " ", str(s).lower())
    return re.sub(r"\s+", " ", s).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "research" / "wiki_cited"))
    ap.add_argument("--out", default=str(ROOT / "data" / "intake_batches2"))
    ap.add_argument("--per", type=int, default=8)
    ap.add_argument("--only-who", nargs="*")
    args = ap.parse_args()
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    A = json.loads((ROOT / "data" / "admin1.json").read_text())

    def rec_for(who: str):
        if who.startswith("country:"):
            return who.split(":", 1)[1], C.get(who.split(":", 1)[1])
        iso3, nm = who.split("/", 1)
        for r in A.values():
            if r.get("iso3") == iso3 and r.get("name") == nm:
                return iso3, r
        return None, None

    files = sorted(Path(args.dir).glob("*.json"))
    if args.only_who:
        want = set(args.only_who)
        files = [f for f in files if json.loads(f.read_text()).get("who") in want]
    outdir = Path(args.out)
    outdir.mkdir(exist_ok=True)
    n_batches = n_leads = n_dropped = 0
    batch = []
    def flush():
        nonlocal n_batches, batch
        if not batch: return
        (outdir / f"i{n_batches+1:03d}.json").write_text(
            json.dumps(batch, ensure_ascii=False, indent=1), encoding="utf-8")
        n_batches += 1; batch = []
    for f in files:
        d = json.loads(f.read_text())
        who = d.get("who"); iso3, rec = rec_for(who)
        if rec is None:
            print(f"[skip] {who}: record not found"); continue
        have = {slug(s.get("url","")) for s in (rec.get("sources") or []) if isinstance(s, dict)}
        have |= {slug(s.get("title","")) for s in (rec.get("sources") or []) if isinstance(s, dict)}
        have.discard("")
        for lead in (d.get("leads") or [])[:10]:
            key = slug(lead.get("title",""))
            if not key or key in have:
                n_dropped += 1; continue
            batch.append({
                "who": who, "iso3": iso3, "name": rec.get("name", iso3),
                "score": rec.get("score"),
                "summary_text": re.sub(r"<[^>]+>", " ", str(rec.get("summary",""))),
                "sources": [{"title": lead.get("title",""),
                             "documents": lead.get("documents",""),
                             "detail": lead.get("detail",""),
                             "status": "lead-verification"}]})
            n_leads += 1
            if len(batch) >= args.per: flush()
    flush()
    print(f"intake_batches2: {n_batches} batches, {n_leads} leads, {n_dropped} dropped as already-cited")
    return 0


if __name__ == "__main__":
    sys.exit(main())