#!/usr/bin/env python3
"""Cascade S3/S4: model-based re-blind for changed regions only (tranche 2).
Per region: rewrite blindSummary (from summary) + existing mirrors
blindTangential / blindLocalsOnly / blindOutOfScope, plus append one blinded
entry to blindSourceSummaries for the newly added source. Uses the five-way
provider adapter (PM.call_v4('mimo')) with the blind_rewrite writer prompt.
Originals backed up to research/us-states-wave/cascade-backup.json before any
write. One attempt per field, no retries. Scores never touched.
Resume-safe: completed rewrites are cached in cascade-rewrites.jsonl and
re-applied without re-calling.
"""
import json, sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
WAVE = ROOT / "research" / "us-states-wave"
FW = ROOT / "research" / "experiments" / "country-calibration-audit" / "five-way"
sys.path.insert(0, str(FW))
import provider_models as PM  # noqa: E402
import harness as H  # noqa: E402
from blind_rewrite import BLIND_WRITER_SYSTEM, FIELD_PAIRS  # noqa: E402

CHANGED = ["Arizona", "California", "Colorado", "Idaho", "Kansas", "Missouri",
           "Nebraska", "Vermont", "Virginia", "Washington"]
NEW_SOURCE = {
 "Arizona": "https://ballotpedia.org/Arizona_ballot_measures",
 "California": "https://en.wikipedia.org/wiki/LGBTQ_rights_in_California",
 "Colorado": "https://ballotpedia.org/Colorado_ballot_measures",
 "Idaho": "https://www.acluidaho.org/en/cases/jackson-edney-v-labrador",
 "Kansas": "https://www.aclukansas.org/en/cases/doe-v-state-of-kansas",
 "Missouri": "https://ballotpedia.org/Missouri_ballot_measures",
 "Nebraska": "https://ballotpedia.org/Nebraska_ballot_measures",
 "Vermont": "https://ballotpedia.org/Vermont_ballot_measures",
 "Virginia": "https://ballotpedia.org/Virginia_ballot_measures",
 "Washington": "https://ballotpedia.org/Washington_ballot_measures",
}
LOG = WAVE / "cascade-rewrites.jsonl"
BACKUP = WAVE / "cascade-backup.json"

def content_of(res):
    raw = json.loads(res["raw_response"])
    return ((raw.get("choices") or [{}])[0].get("message") or {}).get("content") or ""

def rewrite_field(src_text, blind_key, src_key="text"):
    user = (f"Rewrite this one field into its blind mirror. Return a "
            f"JSON object with exactly this key: {blind_key}.\n\n"
            + json.dumps({src_key: src_text}, ensure_ascii=False))
    res = PM.call_v4("mimo", BLIND_WRITER_SYSTEM, user)
    usage = res.get("usage") or {}
    if "cost_usd" not in usage:
        raise RuntimeError("unknown charge")
    parsed = json.loads(content_of(res))
    value = parsed.get(blind_key) or parsed.get(src_key) or parsed.get("text")
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"empty rewrite for {blind_key}")
    return value, usage

def main():
    admin = json.loads((ROOT / "data" / "admin1.json").read_text())
    by_name = {v.get("name"): k for k, v in admin.items() if isinstance(v, dict)}
    done = {}
    if LOG.exists():
        for line in LOG.read_text().splitlines():
            if line.strip():
                e = json.loads(line)
                done[e["region"]] = e
    backup = json.loads(BACKUP.read_text()) if BACKUP.exists() else []
    total = Decimal("0")
    for name in CHANGED:
        if name in done and done[name].get("status") == "ok":
            print(f"{name}: already done, skip")
            continue
        sid = by_name[name]
        rec = admin[sid]
        for _src, blind in FIELD_PAIRS:
            if str(rec.get(blind) or "").strip():
                backup.append({"region": name, "sid": sid, "field": blind, "original": rec.get(blind)})
        rewritten, usages, status = {}, [], "ok"
        try:
            for src, blind in FIELD_PAIRS:
                text = str(rec.get(src) or "")
                if not (H.clean(text) and str(rec.get(blind) or "").strip()):
                    continue
                value, usage = rewrite_field(text, blind, src)
                rewritten[blind] = value
                usages.append(usage)
            # blindSourceSummaries: append blinded entry for the new source
            src_url = NEW_SOURCE[name]
            src_rec = next((s for s in rec.get("sources", []) if s.get("url") == src_url), None)
            if src_rec:
                value, usage = rewrite_field(str(src_rec.get("summary") or ""), "blindSourceSummary", "summary")
                usages.append(usage)
                rewritten["__new_blind_source__"] = value
        except Exception as e:
            status = f"failed: {type(e).__name__}: {e}"
            print(f"{name}: {status}")
        cost = sum(Decimal(u.get("cost_usd", "0")) for u in usages)
        total += cost
        entry = {"region": name, "sid": sid, "status": status,
                 "rewritten": rewritten, "usage": usages, "cost_usd": str(cost)}
        with LOG.open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        done[name] = entry
        print(f"{name}: {status} fields={len(rewritten)} cost=${cost}")
    # apply
    for name in CHANGED:
        e = done.get(name)
        if not e or e.get("status") != "ok":
            continue
        rec = admin[e["sid"]]
        for blind, text in e["rewritten"].items():
            if blind == "__new_blind_source__":
                rec.setdefault("blindSourceSummaries", []).append(text)
            elif isinstance(text, str) and text.strip():
                rec[blind] = text
    BACKUP.write_text(json.dumps(backup, indent=1, ensure_ascii=False), encoding="utf-8")
    (ROOT / "data" / "admin1.json").write_text(json.dumps(admin, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"APPLIED re-blind for {len(CHANGED)} regions. total cost this run list below.")
    print(json.dumps({"totalCostUpper": str(total)}, indent=1))

if __name__ == "__main__":
    main()
