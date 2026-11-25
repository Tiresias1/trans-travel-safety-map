#!/usr/bin/env python3
"""Cascade S4/S5(+S8 in method numbering): dossier render + pairwise rerate
for changed regions only (tranche 2). Per changed region, 2 pairings:
A=focal, B1=USA parent anchor, B2=nearest-score state. One model call per
pairing (7-model cycle, PM.call_v4). Focal score update: established
running-average schedule alpha=0.20 per update (us_iterative_pairwise),
starting at update 1 for this recalibration; recorded explicitly.
Artifacts: research/us-states-wave/renders/<Region>.txt (S6 render + leak
scan), research/us-states-wave/rerate-ledger.json. Scores written to
data/admin1.json. Resume-safe via rerate-results.jsonl.
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
import single_rate_v4 as V4  # noqa: E402
import nh_ri_comparison as NHRI  # noqa: E402

CHANGED = ["Arizona", "California", "Colorado", "Idaho", "Kansas", "Missouri",
           "Nebraska", "Vermont", "Virginia", "Washington"]
RESULTS = WAVE / "rerate-results.jsonl"
LEDGER = WAVE / "rerate-ledger.json"

def alpha(update_number):
    if update_number <= 20: return 0.20
    if update_number <= 25: return 0.08
    return 0.05

def main():
    admin1 = H.load_admin1(); countries = H.load_countries()
    by_name = {v.get("name"): k for k, v in admin1.items() if isinstance(v, dict)}
    scores = {k: v.get("score") for k, v in admin1.items()
              if isinstance(v, dict) and v.get("iso3") == "USA" and isinstance(v.get("score"), (int, float))}
    # S6 render + leak scan
    leak_report = {}
    for name in CHANGED:
        sid = by_name[name]
        text = H.render_admin1_dossier(sid, "USA", admin1, countries)
        (WAVE / "renders").mkdir(exist_ok=True)
        (WAVE / "renders" / f"{name}.txt").write_text(text, encoding="utf-8")
        leaks = H.find_identity_leaks(text, name, str(countries["USA"].get("name") or ""), "USA")
        leak_report[name] = leaks
        print(f"render {name}: chars={len(text)} leaks={leaks}")
    # build pairwise inputs from fresh cells
    cells = V4.build("admin1")
    cell_by_name = {}
    for c in cells:
        cell_by_name[c["region"].split(":", 1)[-1]] = c
    country_cells = V4.build("countries")
    usa_cell = next(c for c in country_cells if c["region"] == "USA")
    system = cells[0]["_system"]
    dossiers = {n: NHRI._dossier_from_cell(cell_by_name[n]) for n in CHANGED}
    dossiers["__USA__"] = NHRI._dossier_from_cell(usa_cell)
    # all state dossiers for nearest-partner B side
    for c in cells:
        n = c["region"].split(":", 1)[-1]
        if n not in dossiers:
            dossiers[n] = NHRI._dossier_from_cell(c)
    models = list(PM.SINGLE_MODELS.keys())
    done = {}
    if RESULTS.exists():
        for line in RESULTS.read_text().splitlines():
            if line.strip():
                e = json.loads(line)
                done[(e["focal"], e["partner_kind"])] = e
    pairs = []
    for name in CHANGED:
        sid = by_name[name]
        # nearest-score partner (current scores, before rerate edits)
        others = sorted((abs(scores[k] - scores[sid]), admin1[k].get("name")) for k in scores if k != sid)
        nearest = others[0][1]
        pairs.append((name, "__USA__", "parent"))
        pairs.append((name, nearest, "nearest"))
    total = Decimal("0")
    focal_new = {n: scores[by_name[n]] for n in CHANGED}
    focal_updates = {n: 0 for n in CHANGED}
    results = []
    for i, (focal, partner, kind) in enumerate(pairs):
        key = (focal, kind)
        if key in done:
            e = done[key]
            results.append(e)
            if e.get("status") == "ok":
                focal_updates[focal] += 1
                a = alpha(focal_updates[focal])
                focal_new[focal] = (1 - a) * focal_new[focal] + a * e["A_rating"]
            continue
        model_key = models[i % len(models)]
        user = (NHRI.COMBINED_INSTRUCTION + dossiers[focal] + NHRI.MID_INSTRUCTION
                + dossiers[partner] + NHRI.QUESTION_TAIL + NHRI.SUFFIX)
        entry = {"focal": focal, "partner": partner, "partner_kind": kind,
                 "model": model_key, "combined_user_sha256": V4.sha(user)}
        try:
            res = PM.call_v4(model_key, system, user)
            usage = res.get("usage") or {}
            entry["usage"] = usage
            if "cost_usd" not in usage:
                entry.update(status="stopped", reason="unknown charge")
            else:
                total += Decimal(usage["cost_usd"])
                entry["cost_usd"] = usage["cost_usd"]
                raw = json.loads(res["raw_response"])
                content = ((raw.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
                try:
                    parsed = NHRI.parse_combined(content)
                    entry.update(status="ok", A_rating=parsed["A"]["rating"],
                                 B_rating=parsed["B"]["rating"],
                                 difference_B_minus_A=parsed["difference_ri_minus_nh"])
                except Exception as e:
                    entry.update(status="rejected", reason=f"{type(e).__name__}: {e}")
        except Exception as e:
            entry.update(status="transport_failure", reason=f"{type(e).__name__}: {e}")
        with RESULTS.open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        results.append(entry)
        if entry.get("status") == "ok":
            focal_updates[focal] += 1
            a = alpha(focal_updates[focal])
            focal_new[focal] = (1 - a) * focal_new[focal] + a * entry["A_rating"]
        print(f"{focal} vs {partner} ({kind}, {model_key}): {entry.get('status')} "
              f"A={entry.get('A_rating')} B={entry.get('B_rating')} cost={entry.get('cost_usd')}")
    # write scores
    admin = json.loads((ROOT / "data" / "admin1.json").read_text())
    score_changes = []
    for name in CHANGED:
        sid = by_name[name]
        old = admin[sid].get("score")
        new = focal_new[name]
        if focal_updates[name] and new != old:
            admin[sid]["score"] = new
            score_changes.append({"region": f"USA/{name}", "old": old, "new": new,
                                  "updates": focal_updates[name]})
    (ROOT / "data" / "admin1.json").write_text(json.dumps(admin, indent=1, ensure_ascii=False), encoding="utf-8")
    ledger = {"wave": "us-states-tranche-2", "pairsPlanned": len(pairs),
              "pairsOk": sum(1 for r in results if r.get("status") == "ok"),
              "pairsFailed": sum(1 for r in results if r.get("status") != "ok"),
              "totalCostUsdThisProcess": str(total),
              "scoreUpdateRule": "running-average schedule alpha=0.20 per update (us_iterative_pairwise), recalibration draws numbered from 1; focal (A-side) rating only",
              "scoreChanges": score_changes, "leakScan": leak_report,
              "results": results}
    LEDGER.write_text(json.dumps(ledger, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"pairs ok {ledger['pairsOk']}/{len(pairs)}; score changes: {len(score_changes)}; cost this process ${total}")

if __name__ == "__main__":
    main()
