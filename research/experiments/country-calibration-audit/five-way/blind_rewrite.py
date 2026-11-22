#!/usr/bin/env python3
"""Model-based re-blinding wave for ADM1 dossier records (dossiers only).

Root cause addressed: the previous blind* fields were produced by lanes
whose output let identity survive (demonyms, institutions), and the
regex-only neutralize() in global_adm1_iterative could not catch them.
Primary blinding is therefore MODEL-BASED rewriting here: a judge model
(mimo via provider_models.call_v4) rewrites each source field into its
blind mirror with explicit "this division" / "this country" placeholders
and no demonyms/institutions. Regex demonym/institution matching
(harness.find_identity_leaks) is used ONLY as a post-hoc failsafe flag
(the leak gate), never as the primary transform and never to silently
fix a rewrite away.

Scope (frozen first, before any provider call): every ADM1 record in
data/admin1.json that is a dossier record WITH a summary AND an existing
blindSummary (the 598-record blind cohort; dossier:true). Records with a
summary but no blind fields (non-dossier records) are NOT in scope:
creating blind fields for them would change blind-eligibility and widen
scope beyond this dossiers-only, no-score-change wave. The frozen scope
list is written to runs/blind-rewrite-20261121/scope.json before the
first call and is never regenerated on resume.

Per record: one model call per field-group (one attempt per field, no
retries; a single multi-field reply truncates on long records):
  summary -> blindSummary, tangentialFactors -> blindTangential,
  localsOnly -> blindLocalsOnly, outOfScopeNotes -> blindOutOfScope.
A record's rewrite is applied only if every requested field succeeds.
The record's name/ISO3 are deliberately NOT shown to the writer model;
it genericises any proper names it finds. Original blind fields are
preserved in analysis/blind_rewrite_backup.json (sid, field, original)
BEFORE data/admin1.json is overwritten. Successful rewrites are appended
to runs/blind-rewrite-20261121/rewrites.jsonl and applied to
data/admin1.json atomically every --save-every successes and at the end;
on resume, completed rewrites are re-applied from rewrites.jsonl and
never re-called. Scores are never touched.

After the wave: the leak gate renders every in-scope dossier via
harness.render_admin1_dossier and regex-scans it with
harness.find_identity_leaks; residual offenders are LISTED in
analysis/blind_rewrite.json (not regex-fixed). Aggregate:
analysis/blind_rewrite.json. Single-writer guard: refuses to launch if
another blind_rewrite.py python process is running. Credential is read
only by provider_models; never echoed/logged.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import harness as H  # noqa: E402
import provider_models as PM  # noqa: E402

RUN_ID = "blind-rewrite-20261121"
RUN_DIR = HERE / "runs" / RUN_ID
AGGREGATE_PATH = HERE / "analysis" / "blind_rewrite.json"
BACKUP_PATH = HERE / "analysis" / "blind_rewrite_backup.json"
FIELD_PAIRS = (("summary", "blindSummary"),
               ("tangentialFactors", "blindTangential"),
               ("localsOnly", "blindLocalsOnly"),
               ("outOfScopeNotes", "blindOutOfScope"))

BLIND_WRITER_SYSTEM = """\
You are a blind-writer anonymising research records for a blind comparative rating exercise. Your only job is to strip every detail that could identify which division or country a record describes, while preserving every fact that bears on risk to a transgender visitor.

Rules:
- Preserve every risk-relevant fact verbatim in substance: laws, penalties, sentence lengths, counts, dates, enforcement patterns, court outcomes, years. Do not add, infer, soften, or intensify anything. Do not compress aggressively; aim for 80-110% of the source length.
- Replace every jurisdiction name, demonym/adjective (e.g. Scottish, Welsh, English), capital/city name, named institution/organisation/agency/court/parliament, named individual, statute name, and other-country name with explicit generic placeholders: "this division" for the division itself, "this country" for the parent country, "the legislature", "the highest civil court", "the police service", "the prison service", "the prosecution service", "the national health service", "a neighbouring jurisdiction", and similar generic descriptors. NO demonyms and NO institution names may survive.
- Never reproduce any rating, score number, band label (Low Risk / Reduced Risk / Elevated Risk / High Risk / Do Not Travel), or rank. Describe facts only.
- No meta-commentary about the record, the map, or previous versions. State current facts only.

Return ONLY a JSON object with the keys listed in the user message, each value the rewritten text for that field. No prose, no markdown fences."""


def check_single_writer() -> list[int]:
    pids = []
    proc = Path("/proc")
    if proc.is_dir():
        for entry in proc.iterdir():
            if not entry.name.isdigit():
                continue
            pid = int(entry.name)
            if pid == os.getpid():
                continue
            try:
                raw = (entry / "cmdline").read_bytes()
            except OSError:
                continue
            if not raw:
                continue
            parts = [p.decode("utf-8", "replace") for p in raw.split(b"\x00") if p]
            argv0 = Path(parts[0]).name if parts else ""
            if not argv0.startswith("python"):
                continue
            if any(p == "blind_rewrite.py" or p.endswith("/blind_rewrite.py")
                   for p in parts):
                pids.append(pid)
    return sorted(pids)


def frozen_scope(admin1: dict) -> list[str]:
    """Dossier records with a summary and an existing blindSummary, sorted."""
    return sorted(sid for sid, rec in admin1.items()
                  if isinstance(rec, dict)
                  and H.clean(rec.get("summary"))
                  and H.clean(rec.get("blindSummary")))


def _atomic_json(path: Path, doc) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    tmp.replace(path)


def ensure_scope_and_backup(admin1: dict) -> list[str]:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    scope_path = RUN_DIR / "scope.json"
    if scope_path.exists():
        scope = json.loads(scope_path.read_text(encoding="utf-8"))["sids"]
        missing = [s for s in scope if s not in admin1]
        if missing:
            raise SystemExit(f"frozen scope sids missing from admin1.json: {missing[:5]}")
        return scope
    scope = frozen_scope(admin1)
    _atomic_json(scope_path, {
        "run_id": RUN_ID,
        "rule": "dossier records (existing blindSummary) with a non-empty summary",
        "n": len(scope),
        "sids": scope,
        "excluded": "records with a summary but no blind fields (non-dossier): "
                    "creating blind fields would change blind-eligibility; "
                    "out of scope for this dossiers-only wave",
    })
    # Preserve originals BEFORE any overwrite of data/admin1.json.
    if not BACKUP_PATH.exists():
        backup = []
        for sid in scope:
            rec = admin1[sid]
            for _src, blind in FIELD_PAIRS:
                if str(rec.get(blind) or "").strip():
                    backup.append({"sid": sid, "field": blind,
                                   "original": rec.get(blind)})
        _atomic_json(BACKUP_PATH, {"run_id": RUN_ID, "entries": backup})
    return scope


def load_rewrites() -> dict:
    path = RUN_DIR / "rewrites.jsonl"
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entry = json.loads(line)
                out[entry["sid"]] = entry
    return out


def apply_rewrites(admin1: dict, rewrites: dict) -> None:
    for sid, entry in rewrites.items():
        if entry.get("status") != "ok":
            continue
        rec = admin1.get(sid)
        if not isinstance(rec, dict):
            continue
        for blind, text in (entry.get("rewritten") or {}).items():
            if isinstance(text, str) and text.strip():
                rec[blind] = text


def rewrite_one(sid: str, rec: dict) -> dict:
    """One attempt, no retries. Returns a rewrites.jsonl entry."""
    payload, keys = {}, []
    for src, blind in FIELD_PAIRS:
        text = str(rec.get(src) or "")
        if H.clean(text) and blind in ("blindSummary",) or H.clean(text) and str(rec.get(blind) or "").strip():
            payload[src] = text
            keys.append(blind)
    # blindSummary is always rewritten for in-scope records (they all have
    # a summary); the other mirrors only where a blind mirror already
    # exists, so we never invent a field the record did not have.
    entry = {"sid": sid, "attempts": len(keys), "keys": keys}
    rewritten, usages = {}, []
    for src, blind in FIELD_PAIRS:
        if blind not in keys:
            continue
        user = (f"Rewrite this one field into its blind mirror. Return a "
                f"JSON object with exactly this key: {blind}.\n\n"
                + json.dumps({src: payload[src]}, ensure_ascii=False))
        try:
            res = PM.call_v4("mimo", BLIND_WRITER_SYSTEM, user)
        except Exception as e:  # one attempt; preserve failure, no retry
            entry.update(status="transport_failure",
                         reason=f"{src}: {type(e).__name__}: {e}",
                         usage={"cost_usd": _sum_cost(usages)})
            return entry
        usage = res.get("usage") or {}
        usages.append(usage)
        if "cost_usd" not in usage:
            entry.update(status="stopped", reason=f"{src}: unknown charge",
                         usage={"cost_usd": _sum_cost(usages)})
            return entry
        try:
            raw = json.loads(res["raw_response"])
            content = ((raw.get("choices") or [{}])[0].get("message") or {}
                       ).get("content") or ""
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("reply is not a JSON object")
        except Exception as e:
            entry.update(status="rejected",
                         reason=f"{src}: parse: {type(e).__name__}: {e}",
                         usage={"cost_usd": _sum_cost(usages)})
            return entry
        # Accept either the source-field key or the blind-mirror key:
        # writer models naturally answer with the blind field names.
        value = parsed.get(src) or parsed.get(blind)
        if not isinstance(value, str) or not value.strip():
            entry.update(status="rejected",
                         reason=f"missing/empty rewrite for {src}",
                         usage={"cost_usd": _sum_cost(usages)})
            return entry
        src_len = len(H.clean(rec.get(src)))
        new_len = len(H.clean(value))
        if src_len and not (0.4 * src_len <= new_len <= 2.0 * src_len):
            entry.update(status="rejected",
                         reason=f"length sanity failed for {src}: "
                         f"{new_len} vs source {src_len}",
                         usage={"cost_usd": _sum_cost(usages)})
            return entry
        rewritten[blind] = value
    entry.update(status="ok", rewritten=rewritten,
                 usage={"cost_usd": _sum_cost(usages)})
    return entry


def _sum_cost(usages) -> str:
    total = Decimal("0")
    for u in usages:
        if u.get("cost_usd"):
            total += Decimal(u["cost_usd"])
    return str(total)


def leak_gate(admin1: dict, countries: dict, scope: list[str]) -> dict:
    """Render every in-scope dossier; regex-scan for identity terms.

    Failsafe flag only: offenders are listed, never regex-fixed.
    """
    offenders = []
    for sid in scope:
        rec = admin1.get(sid)
        if not isinstance(rec, dict):
            continue
        iso = rec.get("iso3")
        try:
            dossier = H.render_admin1_dossier(sid, iso, admin1, countries)
        except H.HarnessError as e:
            offenders.append({"sid": sid, "name": rec.get("name"),
                              "iso3": iso, "error": str(e)})
            continue
        siblings = [str(r.get("name") or "") for r in admin1.values()
                    if isinstance(r, dict) and r.get("iso3") == iso
                    and str(r.get("name") or "")]
        leaks = H.find_identity_leaks(dossier, str(rec.get("name") or ""),
                                      str((countries.get(iso) or {}).get("name") or ""),
                                      str(iso or ""), siblings)
        if leaks:
            offenders.append({"sid": sid, "name": rec.get("name"),
                              "iso3": iso, "leaks": leaks})
    return {"n_scanned": len(scope), "n_residual_leaks": len(offenders),
            "offenders": offenders}


def run(dry_run: bool = False, only: list[str] | None = None,
        limit: int | None = None, workers: int = 1,
        save_every: int = 10) -> int:
    others = check_single_writer()
    if others:
        print(f"single-writer guard: blind_rewrite.py already running, "
              f"PID(s)={others}; refusing to launch", flush=True)
        return 2
    admin1 = H.load_admin1()
    countries = H.load_countries()
    scope = ensure_scope_and_backup(admin1)
    if only:
        scope = [s for s in scope if s in set(only)]
    if limit is not None:
        scope = scope[:limit]
    rewrites = load_rewrites()
    apply_rewrites(admin1, rewrites)  # resume: re-apply completed rewrites
    done = {s for s, e in rewrites.items()}
    todo = [s for s in scope if s not in done]
    print(f"scope={len(scope)} already_done={len(done)} todo={len(todo)} "
          f"workers={workers}", flush=True)
    if dry_run:
        print(f"dry run: first todo={todo[:3]}; no provider calls made",
              flush=True)
        gate = leak_gate(admin1, countries, scope)
        print(f"leak gate (pre-wave): scanned={gate['n_scanned']} "
              f"residual={gate['n_residual_leaks']}", flush=True)
        return 0

    lock = threading.Lock()
    total = Decimal("0")
    for e in rewrites.values():
        if e.get("usage", {}).get("cost_usd"):
            total += Decimal(e["usage"]["cost_usd"])
    since_save = 0
    rewrites_path = RUN_DIR / "rewrites.jsonl"

    def _do(sid):
        nonlocal since_save, total
        entry = rewrite_one(sid, admin1[sid])
        with lock:
            with rewrites_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
            rewrites[sid] = entry
            if entry.get("usage", {}).get("cost_usd"):
                total += Decimal(entry["usage"]["cost_usd"])
            since_save += 1
            if since_save >= save_every:
                apply_rewrites(admin1, rewrites)
                _atomic_json(Path(H.ADMIN1_PATH), admin1)
                since_save = 0
        print(f"  {sid} {admin1[sid].get('name')} status={entry['status']}",
              flush=True)

    if workers and workers > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(_do, todo))
    else:
        for sid in todo:
            _do(sid)

    apply_rewrites(admin1, rewrites)
    _atomic_json(Path(H.ADMIN1_PATH), admin1)

    gate = leak_gate(admin1, countries, scope)
    n_ok = sum(1 for e in rewrites.values() if e.get("status") == "ok")
    aggregate = {
        "run_id": RUN_ID,
        "model": "mimo (provider_models.call_v4, medium effort)",
        "attempts_per_record": 1,
        "scope_rule": "dossier records with summary + existing blindSummary",
        "n_scope": len(scope),
        "n_rewritten_ok": n_ok,
        "n_failed": len(rewrites) - n_ok,
        "total_usd": str(total),
        "backup": str(BACKUP_PATH.relative_to(HERE)),
        "rewrites": str((RUN_DIR / "rewrites.jsonl").relative_to(HERE)),
        "leak_gate": gate,
        "scores_changed": False,
    }
    _atomic_json(AGGREGATE_PATH, aggregate)
    (RUN_DIR / "ledger.json").write_text(
        json.dumps(aggregate, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"done: ok={n_ok} failed={len(rewrites) - n_ok} "
          f"residual_leaks={gate['n_residual_leaks']} exact cost {total} USD",
          flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", nargs="*", default=None,
                    help="restrict to these sids (pilot)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--save-every", type=int, default=10)
    a = ap.parse_args()
    return run(a.dry_run, a.only, a.limit, a.workers, a.save_every)


if __name__ == "__main__":
    sys.exit(main())
