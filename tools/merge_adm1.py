#!/usr/bin/env python3
"""One-shot ADM1 cycle merge: prune invalid drafts, merge research, merge blind.

A research draft (data/adm1_research/<id>.json) is pruned if it is unreadable,
orphaned, or fails the apply tool's schema (summary/sources/scope). A blind file
(data/blind_outputs/adm1/<id>.json) is pruned if it fails check_adm1_blind's
v2 validation. Pruned ids simply stay in (or return to) their queues and get
re-run by the next wave - nothing is ever half-merged.
"""
import glob, json, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from check_adm1_blind import region_checks_v2  # noqa: E402


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def valid_research(o, admin1):
    try:
        rec = admin1.get(o.get("id"))
        if not rec:
            return False
        if not str(o.get("summary", "")).strip():
            return False
        src, old = o.get("sources"), rec.get("sources", [])
        if not isinstance(src, list) or len(src) != len(old):
            return False
        for i, s in enumerate(src):
            if not isinstance(s, dict) or not str(s.get("url", "")).strip() \
                    or not str(s.get("summary", "")).strip():
                return False
            u = old[i] if isinstance(old[i], str) else old[i].get("url")
            if s["url"] != u:
                return False
        for k in ("outOfScopeNotes", "tangentialFactors", "localsOnly"):
            if k in o and not str(o[k]).strip():
                return False
        return True
    except Exception:
        return False


def main():
    admin1 = load(ROOT / "data" / "admin1.json")
    countries = load(ROOT / "data" / "countries.json")
    dossier = {k: v for k, v in admin1.items() if v.get("dossier")}

    pr = 0
    for f in glob.glob(str(ROOT / "data/adm1_research/*.json")):
        try:
            ok = valid_research(json.load(open(f)), admin1)
        except Exception:
            ok = False
        if not ok:
            os.remove(f)
            pr += 1
    pb = 0
    for f in glob.glob(str(ROOT / "data/blind_outputs/adm1/*.json")):
        keep = False
        try:
            o = json.load(open(f))
            rec = dossier.get(o.get("id"))
            if rec and rec.get("researched2"):
                iso3 = rec.get("iso3")
                sibs = [v.get("name", "") for _, v in admin1.items() if v.get("iso3") == iso3]
                par = countries.get(iso3) or {}
                pn = [par["name"]] if par.get("name") else []
                fails, _ = region_checks_v2(rec, o, sibs, pn)
                keep = not fails
        except Exception:
            keep = False
        if not keep:
            os.remove(f)
            pb += 1

    for tool in ("apply_adm1_research.py", "check_adm1_blind.py"):
        r = subprocess.run([sys.executable, str(ROOT / "tools" / tool)],
                           capture_output=True, text=True, cwd=ROOT)
        tail = [l for l in r.stdout.splitlines() if l.strip()][-1:]
        print(tool, "->", tail[0] if tail else r.stdout.strip()[-80:])
    for rep in ("apply_adm1_research.py --report", "check_adm1_blind.py --report"):
        r = subprocess.run(sys.executable + f" tools/{rep}", shell=True,
                           capture_output=True, text=True, cwd=ROOT)
        print(r.stdout.strip())
    print(f"pruned research={pr} blind={pb}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
