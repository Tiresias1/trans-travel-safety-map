#!/usr/bin/env python3
"""Offline harness for the pre-registered rule-contrasts prompt experiment.

Builds candidates A/B from tools/blind_pairwise.py and research/outing-risk-taxonomy.md
by literal exact-string replacement only (review section 2 shared S1-S10, section 3
variant A1-A4/B1-B4; review section 4 deliberately not applied). Fail closed: every
before-block must match its source exactly once and apply exactly once, else nothing is
written. No regex prose transformation, no network code, no credentials, no model calls,
no diagnostic env hooks, no writes outside this directory.

    python3 harness.py --create    # all checks (scope/index precondition first), then
                                   # freeze prompts, schedule, user messages, manifest
    python3 harness.py --verify    # read-only: all checks + on-disk frozen-byte
                                   # verification + in-memory tamper self-test
    (--dry-run is accepted as an alias for --verify)
"""
from __future__ import annotations

import hashlib, json, os, random, re, subprocess, sys
from collections import Counter
from itertools import groupby
from pathlib import Path

sys.dont_write_bytecode = True  # never write tools/__pycache__
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EXP = "research/experiments/country-calibration-audit/rule-contrasts"
BP_SRC, TAX_SRC = "tools/blind_pairwise.py", "research/outing-risk-taxonomy.md"
FORBIDDEN_ENV = ("STRIP_RULE_10B", "REVERT_ENDPOINT", "RESTORE_ARCHIVED_WORDING")
MODELS = ("deepseek/deepseek-v4.1-flash", "google/gemini-3.8-flash")
PAIR_IDS = ("P1", "P2", "P3", "P4", "P5")
VARIANTS, ORDERS = ("A", "B"), ("left_first", "right_first")
CALL_CEILING, SEED = 40, 20261119  # 5 pairs x 2 variants x 2 models x 2 orders
CAPS = {"per_call_output_tokens": 2000, "total_input_tokens": 700000,
        "total_output_tokens": 90000, "stop_on_unknown_usage": True,
        "draws_per_condition": 1, "retries_selected_for_output": 0}
CODE_TOK = ("u" + "rlib", "re" + "quests", "sock" + "et", "call" + "_api", "api" + "_args")
BLOB_TOK = ("ht" + "tp", "api" + "_key", "API" + "_KEY", "Bear" + "er ")
KEY_TOK = r"\bsk-[A-Za-z0-9]{8,}"  # provider-style secret key pattern
RESULTS: list = []

def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f"  :: {detail}"))

def report():
    bad = [(n, d) for n, ok, d in RESULTS if not ok]
    print(f"\n{len(RESULTS)} checks: {len(RESULTS) - len(bad)} passed, {len(bad)} failed")
    for n, d in bad:
        print(f"  FAILED {n}  :: {d}")

def stop(name, detail):
    check(name, False, detail); report(); sys.exit(1)

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def load(p) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))

def once(text, before, after, where):
    n = text.count(before)
    if n != 1:
        stop(f"fail-closed apply-once [{where}]", f"expected exactly 1 literal match, found {n}")
    return text.replace(before, after, 1) if after else text

# --------------------------------------------------------------------------- #
# Source uniqueness and prompt construction
# --------------------------------------------------------------------------- #

def check_sources(repl):
    bad = [r["id"] for r in repl["shared"]
           if (ROOT / r["source"]).read_text(encoding="utf-8").count(r["before"]) != 1]
    bad += [s["id"] for s in repl["sites"]
            if (ROOT / s["source"]).read_text(encoding="utf-8").count(s["before"]) != 1]
    check("source literal uniqueness: 17 shared + 7 variant blocks match exactly once",
          not bad, f"non-unique/missing: {bad}")
    check("proposal provenance + sha256 recorded", bool(repl["provenance"].get("proposal_sha256")))
    check("review scope: shared/variant updates only, section 4 excluded",
          "section 4" in repl["provenance"].get("scope", ""))

def load_base():
    for v in FORBIDDEN_ENV:
        if os.environ.get(v):
            stop(f"forbidden diagnostic env hook {v}", "build must run with all hooks unset")
    sys.path.insert(0, str(ROOT / "tools"))
    import blind_pairwise as BP  # constants only; no API call at import time
    base = BP.build_system_prompt((ROOT / TAX_SRC).read_text(encoding="utf-8"))
    check("base prompt built with hooks unset (original rule 10b intact)",
          "10b. **The score is what happens" in base and "imprisonment or execution" not in base)
    return BP, base

def build_candidates(base, repl):
    shared = base
    for r in repl["shared"]:
        shared = once(shared, r["before"], r["after"], r["id"])
    cands = {}
    for v in VARIANTS:
        t = shared
        for s in repl["sites"]:
            t = once(t, s["before"], s[v], f"{s['id']}/{v}")
        cands[v] = t
    return cands

# --------------------------------------------------------------------------- #
# Predeclared checks
# --------------------------------------------------------------------------- #

def check_comparability(cands, repl):
    marked = {}
    for v in VARIANTS:
        t = cands[v]
        for s in repl["sites"]:
            text = s[v] if s[v] else s["before"]  # A keeps the original task line
            if t.count(text) != 1:
                stop(f"variant site text [{s['id']}/{v}] not unique in candidate", f"count={t.count(text)}")
            t = t.replace(text, f"<<{s['id']}>>", 1)
        marked[v] = t
    check("option comparability: A and B differ only at the 7 designated sites",
          marked["A"] == marked["B"], "unexpected difference outside variant sites")
    fa, fb = cands["A"].split("## Output format"), cands["B"].split("## Output format")
    check("option comparability: identical output-format block",
          len(fa) == len(fb) == 2 and fa[1] == fb[1])
    band = lambda t: re.search(r"Bands \(for orientation only.*?Low Risk", t, re.S)
    ba, bb = band(cands["A"]), band(cands["B"])
    check("option comparability: identical band legend", bool(ba and bb and ba.group() == bb.group()))

def check_rules(cands):
    for v, t in cands.items():
        check(f"[{v}] no-credit-for-passing/stealth rule preserved",
              "Do not give credit for passing, stealth, silence or avoidance." in t
              and "passing, stealth, silence or avoidance" in t)
        check(f"[{v}] AND endpoint preserved, 'or execution' absent",
              "near-certain imprisonment and likely execution" in t and "imprisonment or execution" not in t)
        check(f"[{v}] rule 10b present / intermediates undefined / product formula gone",
              "10b. **" in t and "Intermediate points have no fixed definitions." in t
              and "The score integrates **probability of being outed**" not in t
              and "probability-of-outing" not in t)
        check(f"[{v}] weight: curiosity VERY LOW, social and state threat-framing REAL",
              "carry VERY LOW WEIGHT" in t and "Real weight." in t
              and "carries REAL WEIGHT" in t)
    check("[A] discovery probability is not an independent contribution",
          "is not an independent contribution to this score" in cands["A"]
          and "is not an independent contribution to this score" not in cands["B"])
    check("[B] state-engineered discovery may contribute independently",
          "engineering discovery" in cands["B"] and "engineering discovery" not in cands["A"])
    check("no anchor list or rubric version hard-coded into prompts",
          "ANCHOR" not in cands["A"] + cands["B"] and "RUBRIC_VERSION" not in cands["A"] + cands["B"])

def _strip(d, k):
    """Copy minus the varying field; the LEFT/RIGHT marker is position metadata,
    not dossier evidence, so it is normalised before comparison."""
    return {kk: (vv.replace("LEFT", "SIDE").replace("RIGHT", "SIDE") if kk == "label" else vv)
            for kk, vv in d.items() if kk != k}

def load_fixtures():
    return [load(p) for p in sorted((HERE / "fixtures").glob("*.json"))]

def check_fixtures(fx):
    check("five synthetic fixture pairs P1..P5 present",
          [f.get("pair_id") for f in fx] == list(PAIR_IDS), str([f.get("pair_id") for f in fx]))
    for f in fx:
        pid, vf = f.get("pair_id"), f.get("varying_field")
        if not pid or not vf:
            stop("fixture structure", f"missing pair_id/varying_field in {f.get('title')}")
        L, R = f.get("copy_left", {}), f.get("copy_right", {})
        exp = json.dumps(f.get("expected_reasoning", []))
        blob = json.dumps(f)
        check(f"{pid} matched copies differ only in '{vf}'", _strip(L, vf) == _strip(R, vf))
        check(f"{pid} labelled synthetic, no score/band/ranking fields, qualitative expectations",
              f.get("synthetic") is True and "SYNTHETIC" in f.get("disclaimer", "")
              and bool(f.get("expected_reasoning")) and "score" not in exp.lower()
              and not re.search(r"\b[01]\.\d{2}\b", exp)
              and not re.search(r'"\s*(score|band|rating)\s*":', blob))
    by = {f["pair_id"]: f for f in fx}
    p1, p2, p3, p4, p5 = (by.get(k, {}) for k in ("P1", "P2", "P3", "P4", "P5"))
    check("control P4: byte-identical evidence, position created only by presentation",
          p4.get("varying_field") == "presentation_position"
          and p4.get("copy_left") == p4.get("copy_right")
          and "position" not in p4.get("copy_left", {}))
    check("P1 relabelled bundled institutional-practice, discovery identification withdrawn",
          p1.get("contrast_class") == "bundled-institutional-practice"
          and "withdrawn" in p1.get("identification", "")
          and "not a pure discovery-only" in p1.get("design", "").lower())
    check("P3 relabelled bundled hostility-and-treatment contrast",
          p3.get("contrast_class") == "bundled-hostility-treatment"
          and "cannot isolate" in p3.get("design", "").lower())
    check("control P5: irrelevant general hazard added to one copy only",
          p5.get("varying_field") == "general_hazard" and "general_hazard" not in p5.get("copy_left", {})
          and "general_hazard" in p5.get("copy_right", {}))
    check("P2 states detention frequency unknown in both copies",
          bool(p2) and all("unknown" in (p2[c]["custody_placement_rule"] + " "
                                         + " ".join(p2[c]["uncertainties"])).lower()
                           for c in ("copy_left", "copy_right")))

def _real_names(text, countries, adm1):
    hits = [n for n in countries if re.search(r"\b%s\b" % re.escape(n), text, re.I)]
    return hits + [n for n in adm1 if n in text and re.search(r"\b%s\b" % re.escape(n), text)]

def check_no_real_geo(cands, base, fx, sched, BP):
    countries = sorted({r["name"] for r in load(ROOT / "data/countries.json").values()})
    adm1 = sorted({r["name"].strip() for r in load(ROOT / "data/admin1.json").values()
                   if len(r["name"].strip()) >= 6})
    anchors = list(getattr(BP, "ANCHOR_ISOS", ()))
    blob = json.dumps(fx) + json.dumps(sched)
    hits = _real_names(blob, countries, adm1) + [i for i in anchors if re.search(r"\b%s\b" % i, blob)]
    check("fixtures/schedule: no real country, ADM1 or frozen-anchor reference", not hits, str(hits[:8]))
    pat = lambda n: r"\b%s\b" % re.escape(n)
    for v, t in cands.items():
        added = [n for n in set(_real_names(t, countries, adm1) + anchors)
                 if len(re.findall(pat(n), t, re.I)) > len(re.findall(pat(n), base, re.I))]
        check(f"[{v}] prompt adds no country/ADM1/anchor reference beyond source", not added, str(added[:8]))

def _sched_ok(rows):
    half = len(rows) // 2
    for key in ("variant", "model", "order"):
        if len(set(Counter(r[key] for r in rows).values())) != 1:
            return False
        if any(not (8 <= n <= 12) for n in Counter(r[key] for r in rows[:half]).values()):
            return False
    return max(len(list(g)) for _, g in groupby(r["variant"] for r in rows)) <= 2

def build_schedule():
    rows = [{"pair_id": p, "variant": v, "model": m, "order": o}
            for p in PAIR_IDS for v in VARIANTS for m in MODELS for o in ORDERS]
    if len(rows) != CALL_CEILING:
        stop("schedule construction", f"{len(rows)} cells != ceiling {CALL_CEILING}")
    for attempt in range(200):  # derived seeds; first balanced interleaving wins
        pool, out, run_v, run_n = rows[:], [], None, 0
        rng = random.Random(SEED + attempt)
        while pool:  # random pick among cells that keep runs of one variant <= 2
            elig = [r for r in pool if not (r["variant"] == run_v and run_n >= 2)] or pool
            pick = rng.choice(elig); pool.remove(pick)
            run_n = run_n + 1 if pick["variant"] == run_v else 1
            run_v = pick["variant"]; out.append(pick)
        if _sched_ok(out):
            for i, r in enumerate(out, 1):
                r.update(call=i, draw=1, fresh_context=True, caps=CAPS)
            return out
    stop("schedule balance", "no balanced interleaving found for the fixed seed")

def check_schedule(sched):
    cells = [(r["pair_id"], r["variant"], r["model"], r["order"]) for r in sched]
    want = {(p, v, m, o) for p in PAIR_IDS for v in VARIANTS for m in MODELS for o in ORDERS}
    check("schedule: 40 calls, every condition cell exactly once",
          len(sched) == CALL_CEILING and set(cells) == want and len(set(cells)) == CALL_CEILING)
    check("schedule: randomized, balanced halves, interleaved (<=2 same variant)", _sched_ok(sched))
    check("schedule: one draw per cell, fresh context, no outcome selection",
          all(r["draw"] == 1 and r["fresh_context"] for r in sched)
          and CAPS["retries_selected_for_output"] == 0 and CAPS["draws_per_condition"] == 1)
    check("schedule: exact API model ids, hard caps, stop on unknown usage",
          {r["model"] for r in sched} == set(MODELS) and all(r["caps"] == CAPS for r in sched)
          and CAPS["stop_on_unknown_usage"])

def check_static(fx, sched):
    src = Path(__file__).read_text(encoding="utf-8")
    blob = src + json.dumps(fx) + json.dumps(sched)
    # code-identifier tokens only against harness source; fixture prose is exempt
    bad = [t for t in CODE_TOK if t in src] + [t for t in BLOB_TOK if t in blob]
    bad += [KEY_TOK] if re.search(KEY_TOK, blob) else []
    check("no network client, credential or API-call code in harness/schedule", not bad, str(bad))

def check_readme():
    p = HERE / "README.md"
    if not p.exists():
        check("README present with rationale and predeclared criteria", False, "missing")
        return
    t = p.read_text(encoding="utf-8")
    dec = set(re.findall(r"\b[01]\.\d{2}\b", t))
    check("README holds no model scores (0.00/1.00 endpoints only)", dec <= {"0.00", "1.00"}, str(sorted(dec)))
    need = ("Pilot rationale", "Hard-stop rules", "Predeclared test criteria", "40 calls",
            "one draw per cell", "no model scores")
    check("README covers rationale, hard stops, criteria, ceiling, one draw",
          all(k in t for k in need), str([k for k in need if k not in t]))

DIAG_ADDENDUM = (
    "\n\nIn the SAME single JSON object, add a \"diagnostic\" object with four short string "
    "fields: \"discovery\" (was state-engineered discovery counted as an independent "
    "contribution? answer yes/no plus basis), \"direct_harms\" (direct burdens counted), "
    "\"scope_triggers\" (scope and trigger conditions identified), \"uncertainty\" (key "
    "unknowns). Each field at most 15 words. This diagnostic request is identical for both "
    "prompt variants, is diagnostic-only, and does not change the scale. Short structured "
    "fields support but do not prove the reasoning behind a score.")

CUE_BAN = ("both copies", "counterpart", "carry identical", "identical evidence",
           "differs only", "held constant", "expected_reasoning")

def _render_copy(c):
    out = []
    for k, v in c.items():
        if k == "label":
            continue
        if isinstance(v, list):
            out.append(f"{k}:")
            out += [f"  - {x}" for x in v]
        else:
            out.append(f"{k}: {v}")
    return "\n".join(out)

def build_user_messages(fx, sched):
    """Provider-visible user messages: evidence fields only, synthetic disclaimer,
    order applied; reviewer metadata (title/design/expected_reasoning/labels) excluded;
    presented A/B -> original copy identity recorded separately."""
    by = {f["pair_id"]: f for f in fx}
    rows = []
    for r in sched:
        f = by[r["pair_id"]]
        left_first = r["order"] == "left_first"
        first = f["copy_left"] if left_first else f["copy_right"]
        second = f["copy_right"] if left_first else f["copy_left"]
        msg = (f["disclaimer"] + "\n\nDOSSIER A\n" + _render_copy(first)
               + "\n\nDOSSIER B\n" + _render_copy(second) + DIAG_ADDENDUM)
        rows.append({**{k: r[k] for k in ("call", "pair_id", "variant", "model", "order")},
                     "map_A": "copy_left" if left_first else "copy_right",
                     "map_B": "copy_right" if left_first else "copy_left",
                     "message": msg, "message_sha256": sha(msg.encode())})
    return rows

def check_user_messages(msgs, fx, sched):
    check("user messages: one frozen message per scheduled row",
          len(msgs) == len(sched) == CALL_CEILING
          and [m["call"] for m in msgs] == [r["call"] for r in sched])
    by = {f["pair_id"]: f for f in fx}
    meta = []
    for f in fx:
        meta += [f["design"], f["title"]] + list(f["expected_reasoning"])
        meta += [f["copy_left"]["label"], f["copy_right"]["label"]]
    bad = [m["call"] for m in msgs
           if "SYNTHETIC FICTIONAL EVIDENCE" not in m["message"]
           or "DOSSIER A" not in m["message"] or "DOSSIER B" not in m["message"]
           or not m["message"].endswith(DIAG_ADDENDUM)
           or any(s in m["message"] for s in CUE_BAN)
           or any(s in m["message"] for s in meta)]
    check("user messages: disclaimer, evidence-only content, no reviewer metadata or cross-copy cues",
          not bad, f"failing calls: {bad[:8]}")
    wrong = [m["call"] for m in msgs
             if (m["map_A"] == "copy_left") != (m["order"] == "left_first")
             or m["map_B"] == m["map_A"]
             or m["map_A"] not in by[m["pair_id"]]]
    check("user messages: A/B mapping follows presentation order for every row",
          not wrong, f"failing calls: {wrong[:8]}")
    tails = {m["message"][m["message"].index("In the SAME"):] for m in msgs}
    check("user messages: identical diagnostic rationale request for both variants",
          len(tails) == 1)

def verify_frozen(cands, sched, msgs, repl):
    """Compare ACTUAL on-disk frozen bytes to the manifest and to a fresh rebuild."""
    m = HERE / "frozen" / "manifest.json"
    if not m.exists():
        check("frozen manifest present", False, "missing - run --create first")
        return None
    man = load(m)
    for v in VARIANTS:
        name = f"candidate_{v.lower()}.txt"
        p = HERE / "frozen" / name
        disk = p.read_bytes() if p.exists() else b""
        check(f"frozen prompt {name}: on-disk bytes match manifest hash and rebuild",
              bool(disk) and sha(disk) == man["prompts"][name]["sha256"]
              and disk == cands[v].encode())
    sb = (HERE / "frozen" / "schedule.json").read_bytes()
    check("frozen schedule: on-disk bytes match manifest hash and rebuild",
          bool(sb) and sha(sb) == man.get("schedule_file_sha256") and json.loads(sb) == sched)
    ub = (HERE / "frozen" / "user_messages.json").read_bytes()
    check("frozen user messages: on-disk bytes match manifest hash and rebuild",
          bool(ub) and sha(ub) == man.get("user_messages_file_sha256") and json.loads(ub) == msgs)
    bad = [f for f, h in man["sources"].items()
           if not (ROOT / f).exists() or sha((ROOT / f).read_bytes()) != h]
    check("current source, replacements and fixture bytes match manifest", not bad, str(bad))
    # provenance resolves the in-repo copy of the proposal (proposal.md, byte-for-byte
    # copy of the original artifact); absolute paths are still accepted if present
    prop = Path(repl["provenance"]["proposal"])
    if not prop.is_absolute():
        prop = ROOT / prop
    check("proposal file bytes match manifest provenance hash",
          prop.exists() and sha(prop.read_bytes()) == man["proposal_sha256"])
    check("proposal provenance resolves the in-repo copy under this experiment dir",
          prop.exists() and prop.is_relative_to(HERE))
    return man

def tamper_selftest(man):
    """In-memory mutations only: prove the byte verifiers reject tampered frozen
    prompt, schedule and fixture content without writing anything to disk."""
    if man is None:
        check("tamper self-test (prompt/schedule/fixture rejected)", False, "no manifest")
        return
    bad = bytearray((HERE / "frozen" / "candidate_a.txt").read_bytes())
    bad[100] ^= 0x01
    prompt_tamper_accepted = sha(bytes(bad)) == man["prompts"]["candidate_a.txt"]["sha256"]
    sch = json.loads((HERE / "frozen" / "schedule.json").read_text())
    sch[0]["variant"] = "A" if sch[0]["variant"] == "B" else "B"
    sched_bytes = (json.dumps(sch, indent=1, ensure_ascii=False) + "\n").encode()
    sched_tamper_accepted = sha(sched_bytes) == man.get("schedule_file_sha256")
    fp = sorted((HERE / "fixtures").glob("*.json"))[0]
    fix_tamper_accepted = (sha(fp.read_bytes() + b" ")
                           == man["sources"].get(f"{EXP}/fixtures/{fp.name}"))
    check("tamper self-test: modified frozen prompt, schedule and fixture all rejected in memory",
          not (prompt_tamper_accepted or sched_tamper_accepted or fix_tamper_accepted),
          f"accepted prompt={prompt_tamper_accepted} schedule={sched_tamper_accepted} "
          f"fixture={fix_tamper_accepted}")

KNOWN_SIBLING = EXP.rsplit("/", 1)[0] + "/country-feasibility/"


def scope_violations(lines):
    """Classify `git status --porcelain` lines -> (outside_paths, staged_lines).

    Any staged entry is a violation regardless of path. Any path outside this
    experiment is a violation, EXCEPT the one known untracked sibling experiment
    directory (country-feasibility/), which is allowed only while it appears as
    untracked ('??'); a staged or tracked-modified sibling entry, or any other
    outside path, still fails closed."""
    staged, outside = [], []
    for l in lines:
        if not l.strip():
            continue
        path = l[3:]
        if l[0] not in " ?":
            staged.append(l)
        if path.startswith(EXP):
            continue
        if path.startswith(KNOWN_SIBLING) and l.startswith("??"):
            continue
        outside.append(path)
    return outside, staged


def git_scope():
    out = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        check("git status runs", False, out.stderr.strip()[:80])
        return
    lines = [l for l in out.stdout.splitlines() if l.strip()]
    outside, staged = scope_violations(lines)
    check("no writes outside the experiment directory "
          "(known untracked sibling allowed)", not outside, str(outside[:6]))
    check("no staged files", not staged, str(staged[:6]))


def dir_fingerprint():
    """sha256 of every file under this experiment dir (bytecode caches ignored);
    used by --verify to prove the whole run modified nothing."""
    return {str(p.relative_to(HERE)): sha(p.read_bytes())
            for p in sorted(HERE.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}

def freeze(cands, sched, msgs, repl):
    frozen = HERE / "frozen"
    frozen.mkdir(exist_ok=True)
    prompts = {}
    for v in VARIANTS:
        data, name = cands[v].encode(), f"candidate_{v.lower()}.txt"
        (frozen / name).write_text(cands[v], encoding="utf-8")
        prompts[name] = {"sha256": sha(data), "bytes": len(data), "path": f"{EXP}/frozen/{name}"}
    sched_bytes = (json.dumps(sched, indent=1, ensure_ascii=False) + "\n").encode()
    (frozen / "schedule.json").write_bytes(sched_bytes)
    msg_bytes = (json.dumps(msgs, indent=1, ensure_ascii=False) + "\n").encode()
    (frozen / "user_messages.json").write_bytes(msg_bytes)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                            text=True).stdout.strip()
    sources = {f: sha((ROOT / f).read_bytes()) for f in (BP_SRC, TAX_SRC, f"{EXP}/replacements.json")}
    sources.update({f"{EXP}/fixtures/{p.name}": sha(p.read_bytes())
                    for p in sorted((HERE / "fixtures").glob("*.json"))})
    manifest = {"experiment": EXP, "git_commit": commit, "sources": sources,
                "proposal_sha256": repl["provenance"]["proposal_sha256"], "prompts": prompts,
                "shared_replacements": len(repl["shared"]), "variant_sites": [s["id"] for s in repl["sites"]],
                "excluded_from_scope": "review section 4 (rules 12/15-20 boundaries, ADM1 lane) not applied",
                "models": list(MODELS), "call_ceiling": CALL_CEILING, "presentation_orders": list(ORDERS),
                "caps": CAPS, "seed": SEED, "schedule_sha256": sha(json.dumps(sched, sort_keys=True).encode()),
                "schedule_file_sha256": sha(sched_bytes),
                "user_messages_file_sha256": sha(msg_bytes), "user_message_count": len(msgs),
                "forbidden_env_hooks": list(FORBIDDEN_ENV),
                "live_code": "none - no network, credential or provider code in this experiment"}
    (frozen / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n",
                                          encoding="utf-8")
    check("frozen prompts, schedule, user messages and manifest written under experiment dir", True)

def check_frozen_weight():
    """The actual frozen candidate files (not the in-memory build) must carry the
    user-mandated weight statements."""
    bad = []
    for v in VARIANTS:
        p = HERE / "frozen" / f"candidate_{v.lower()}.txt"
        if not p.exists():
            bad.append(f"{p.name}: missing")
            continue
        t = p.read_text(encoding="utf-8")
        if not ("carry VERY LOW WEIGHT" in t and "Real weight." in t
                and "carries REAL WEIGHT" in t):
            bad.append(f"{p.name}: a required weight statement is missing")
    check("actual frozen candidates preserve very-low curiosity and real social/state threat weight",
          not bad, str(bad))

def main():
    args = set(sys.argv[1:])
    if "--create" in args:
        mode = "create"
    elif args & {"--verify", "--dry-run"}:
        mode = "verify"
    else:
        print("usage: harness.py --create (build + write frozen artifacts) | "
              "--verify (read-only checks + frozen-byte verification + tamper self-test)")
        sys.exit(2)
    fp_before = dir_fingerprint() if mode == "verify" else None
    if mode == "create":  # scope/index precondition BEFORE any write
        git_scope()
        if any(not ok for _, ok, _ in RESULTS):
            stop("create blocked", "scope/index precondition failed; nothing written")
    repl = load(HERE / "replacements.json")
    check_sources(repl)
    BP, base = load_base()
    cands = build_candidates(base, repl)
    check_comparability(cands, repl)
    check_rules(cands)
    fx = load_fixtures()
    check_fixtures(fx)
    sched = build_schedule()
    check_schedule(sched)
    msgs = build_user_messages(fx, sched)
    check_user_messages(msgs, fx, sched)
    check_static(fx, sched)
    check_readme()
    check_no_real_geo(cands, base, fx, sched, BP)
    if mode == "create":
        if all(ok for _, ok, _ in RESULTS):
            freeze(cands, sched, msgs, repl)
        else:
            stop("freeze skipped", "at least one check failed; nothing written")
        git_scope()
    else:  # verify: read-only; never writes
        man = verify_frozen(cands, sched, msgs, repl)
        tamper_selftest(man)
        check("verify mode wrote nothing (whole experiment-dir fingerprint unchanged)",
              fp_before == dir_fingerprint())
    check_frozen_weight()
    report()
    sys.exit(0 if all(ok for _, ok, _ in RESULTS) else 1)

if __name__ == "__main__":
    main()