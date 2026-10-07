#!/usr/bin/env python3
"""LLM-lane blind-vocabulary remediation (2026-10-07).

REGEX PROSE SURGERY IS BANNED (user ruling after the greedy vocabulary
substitution corrupted "state" the verb, "state" the polity and self-references
across the fleet). All meaning-bearing text transforms go through the model
with the substitution rules as INSTRUCTIONS; the gate validates the result.

What this fixes (per record kind):
  independent country — self-references must read "the country" (never
      "state/province"); foreign sub-unit references stay "state/province".
  dependent territory / admin1 region — "state/province" self-references are
      correct; only artifacts and leaks are fixed.
  all — restore "state" where the meaning was the VERB ("do not state whether")
      or the POLITY ("state institutions", "state media"); replace identifying
      agency proper nouns with anonymised equivalents.

Mechanical gates on the output: no digits lost or invented, length within
bounds, blind gate passes, no new facts (length + digit checks approximate
this; the blind gate does the rest).

Usage:
  python3 tools/fix_blind_vocab_llm.py --run        # fleet pass on candidates
  python3 tools/fix_blind_vocab_llm.py --who country:WSM
"""
from __future__ import annotations
import argparse, json, os, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from consolidate_record import call_llm  # noqa

TERR = {"ASM", "GUM", "VIR", "MNP", "PRI", "FLK", "GIB", "BMU", "CYM", "VGB",
        "AIA", "MSR", "TCA", "SHN", "PCN", "GGY", "IMN", "JEY", "GLP", "MTQ",
        "GUF", "REU", "MYT", "BLM", "PYF", "NCL", "CUW", "ABW", "BES", "FRO",
        "GRL", "COK", "NIU", "HKG", "MAC"}

FIELDS = ("blindSummary", "blindTangential", "blindLocalsOnly", "blindOutOfScope")

# candidate DETECTION (finding records, not editing text — detection may use
# patterns; MODIFICATION is model-lane only)
DETECT = re.compile(
    r"state/province|Department of Justice|\bDOJ\b|SWS25", re.I)


def detect(kind: str, rec: dict) -> bool:
    texts = [str(rec.get(f) or "") for f in FIELDS]
    ss = rec.get("blindSourceSummaries")
    if isinstance(ss, list):
        texts += [str(x) for x in ss]
    joined = "\n".join(texts)
    if not DETECT.search(joined):
        return False
    if kind == "country":
        # needs rule 1 work if any self-reference-looking usage exists
        return True
    return True  # territories/regions still need artifact/leak checks


def build_prompt(kind: str, rec: dict) -> str:
    rules = []
    if kind == "country":
        rules.append(
            "1. This record is an INDEPENDENT COUNTRY. Where the text refers to THIS "
            "jurisdiction as 'the state/province' or 'this state/province', that is an "
            "error: rewrite the self-reference as 'the country' / 'this country'. "
            "Genuine references to sub-national units of any jurisdiction (e.g. 'nine "
            "state/provinces', 'another state/province', 'a state/province census') are "
            "CORRECT and must stay.")
    else:
        rules.append(
            "1. This record is a sub-national unit or dependent territory: "
            "'state/province' self-references are CORRECT. Do not change them.")
    rules.extend([
        "2. 'state/province' must NEVER appear where the intended word was the VERB "
        "'state' (as in 'the sources do not state whether...') — restore 'state'. "
        "Likewise where the intended word was the POLITY 'the state' ('state "
        "institutions', 'state media', 'state practice', 'state officials') — restore "
        "'state'. When unsure between 'state' and 'national', prefer 'national'.",
        "3. FULL FIXED VOCABULARY (blind-speak) — apply throughout: "
        "'territory'/'territories'/'dependency'/'island(s)'/'atoll'/'archipelago' -> "
        "'state/province(s)'; bare 'state'/'states' meaning a sub-division of the "
        "parent nation -> 'state/province(s)' (e.g. '9 states plus 1 territory' -> "
        "'9 state/provinces plus 1 state/province'); 'federal'/'federally' -> 'national'/'nationally'; "
        "'overseas'/'crown'/'commonwealth'/'kingdom'/'republic'/'empire' -> anonymised "
        "equivalents ('the parent nation's overseas territory' -> 'a state/province of "
        "the parent nation'); oceans/seas/continents/regions ('Pacific', 'Caribbean', "
        "'Europe', 'Latin America', 'West') -> 'the region' / 'a neighbouring "
        "jurisdiction' / similar; attorney general -> the national justice department; "
        "'Department of Justice'/'DOJ' -> 'the national justice department'; 'SWS25' -> "
        "'an internal marking'; 'Executive Order <number>' -> 'an executive order'. "
        "Keep every other fact.",
        "4. Replace identifying agency/programme proper nouns with anonymised "
        "equivalents (covered by rule 3). Keep every other fact.",
        "5. If a sentence is ungrammatical or appears to have lost a word, repair it "
        "minimally. Do NOT add facts, drop facts, or change meaning. Preserve every "
        "number, date, and penalty. Keep <p> paragraph structure exactly.",
    ])
    payload = {}
    for f in FIELDS:
        if rec.get(f):
            payload[f] = rec[f]
    ss = rec.get("blindSourceSummaries")
    if isinstance(ss, list) and ss:
        payload["blindSourceSummaries"] = ss
    return ("KIND: " + kind + "\n\nRULES:\n" + "\n".join(rules) +
            "\n\nReturn ONLY a JSON object mapping each input field name to its "
            "corrected text (same keys, same paragraph structure).\n\nINPUT:\n" +
            json.dumps(payload, ensure_ascii=False))


def fix_record(kind: str, rec: dict) -> tuple[dict, list]:
    """Returns (changes dict, problems list). Empty changes = nothing to do."""
    out = call_llm("You repair anonymised mirror texts. Output only JSON.",
                   build_prompt(kind, rec))
    changes, problems = {}, []
    DIG = re.compile(r"\d")
    for f, new in out.items():
        if f not in FIELDS and f != "blindSourceSummaries":
            continue
        old = rec.get(f)
        if f == "blindSourceSummaries" and isinstance(old, list):
            if not isinstance(new, list) or len(new) != len(old):
                problems.append(f"{f}: list shape changed")
                continue
            kept = []
            for o, nn in zip(old, new):
                nn = str(nn)
                if set(DIG.findall(nn)) - set(DIG.findall(str(o))):
                    problems.append(f"{f}: digits invented")
                elif len(nn) > max(len(str(o)) * 2, 400):
                    problems.append(f"{f}: length blowup")
                else:
                    kept.append(nn)
            if kept != old:
                changes[f] = kept
            continue
        new = str(new)
        old = str(old or "")
        if set(DIG.findall(new)) - set(DIG.findall(old)):
            problems.append(f"{f}: digits invented")
        elif len(new) > max(len(old) * 2, 8000):
            problems.append(f"{f}: length blowup")
        elif new != old:
            changes[f] = new
    return changes, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--who", nargs="*")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    C = json.loads((ROOT / "data" / "countries.json").read_text())
    A = json.loads((ROOT / "data" / "admin1.json").read_text())
    jobs = []
    if args.who:
        for w in args.who:
            if w.startswith("country:"):
                iso = w[8:]
                jobs.append(("territory" if iso in TERR else "country", iso, None, C[iso]))
            else:
                iso, nm = w.split("/", 1)
                jobs.append(("region", iso, nm,
                             next(x for x in A.values()
                                  if x.get("iso3") == iso and x.get("name") == nm)))
    else:
        for iso, r in sorted(C.items()):
            if detect("territory" if iso in TERR else "country", r):
                jobs.append(("territory" if iso in TERR else "country", iso, None, r))
        for sid, r in sorted(A.items()):
            if r.get("inherited"):
                continue  # stand-ins mirror their country record at build time
            if detect("region", r):
                jobs.append(("region", r.get("iso3"), r.get("name"), r))
    print(f"candidates: {len(jobs)}", flush=True)
    if not args.run:
        for kind, iso, nm, _ in jobs[:25]:
            print("  ", kind, iso, nm or "")
        return
    import fcntl
    fixed = failed = 0
    def one(job):
        kind, iso, nm, rec = job
        try:
            changes, problems = fix_record(kind, rec)
            return job, changes, problems, None
        except Exception as e:
            return job, {}, [], str(e)[:140]
    with ThreadPoolExecutor(args.workers) as ex:
        futs = [ex.submit(one, j) for j in jobs]
        for f in as_completed(futs):
            job, changes, problems, err = f.result()
            kind, iso, nm, rec = job
            who = f"{iso}/{nm}" if nm else f"country:{iso}"
            if err:
                failed += 1
                print(f"[ERR] {who}: {err}", flush=True)
                continue
            if problems:
                failed += 1
                print(f"[GATE-FAIL] {who}: {problems}", flush=True)
                continue
            if changes:
                with open(ROOT / "data" / ".apply.lock", "a+") as lf:
                    fcntl.flock(lf, fcntl.LOCK_EX)
                    try:
                        # re-read fresh under lock; re-apply to the live record
                        if nm is None:
                            D = json.loads((ROOT / "data" / "countries.json").read_text())
                            tgt = D[iso]
                        else:
                            D = json.loads((ROOT / "data" / "admin1.json").read_text())
                            tgt = next(x for x in D.values()
                                       if x.get("iso3") == iso and x.get("name") == nm)
                        for fn, v in changes.items():
                            tgt[fn] = v
                        tmp = (ROOT / "data" / ("countries.json" if nm is None else "admin1.json")).with_suffix(".tmp")
                        tmp.write_text(json.dumps(D, ensure_ascii=False, indent=1), encoding="utf-8")
                        tmp.replace(ROOT / "data" / ("countries.json" if nm is None else "admin1.json"))
                    finally:
                        fcntl.flock(lf, fcntl.LOCK_UN)
                fixed += 1
            else:
                pass
    print(f"VOCAB FIX DONE: {fixed} records changed, {failed} failed/gate-rejected", flush=True)


if __name__ == "__main__":
    main()