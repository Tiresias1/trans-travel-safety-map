#!/usr/bin/env python3
"""Non-dossier merge pass v3: seven per-region bases -> one public summary.

For each of the 1,219 manifest regions (keyed by sid, never by name),
collect the ok bases from whichever of the seven model waves succeeded
(muse, mimo, deepseek, glm, haiku, luna, qwen), and merge them with ONE
call via provider_models.call_v4("mimo", ...) at medium effort. The
merged rating is the MEAN of the contributing per-model ratings,
computed here in code -- the model is never asked for a number.

v3 hardens the v2 parent-regime anti-restatement discipline (v2's
Hormozgan output still re-narrated the parent regime beyond one
sentence) with verbatim locality discipline, and relaxes validation
back to v1's proven tolerance: instructed 1-2 paragraphs, validated
<=3; parent-only 20-170 words, region-specific 30-380 words. The
parent country's unblinded dossier text (data/countries.json, keyed by
iso3 -- the same text the raters saw) is passed into the prompt
labelled PARENT REGIME TEXT, and the merger must not restate any claim
already in it beyond one parent sentence. Each contributing model's
KNOWLEDGE FLAG (region-specific vs parent-only, from
analysis/nondossier_{model}.json) and the parent name are also passed,
plus a DERIVED CLASS (parent-only if >= half of contributors flagged
parent-only, else region-specific); the flags are a secondary signal
for the class cap, the parent-text diffing is the attribution
mechanism.

One attempt per region, no retries; failed/rejected source models are
gaps, never re-called. Resume-safe: per-region results persist
incrementally to runs/nondossier-merge-v3-20261124/ and completed
regions are skipped on relaunch. Single-writer guard per run-id via
/proc scan. Exact Decimal cost accounting, MAX_USD local guard ($30);
provider-error payloads (no usage/cost) count as transport_failure
gaps and the run CONTINUES; only a billed response with unparseable
cost halts (mirrors nondossier_panel.py). Credentials stay inside
provider_models. Site data is never written.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import nondossier_muse as NM   # noqa: E402  (validation regexes)
import provider_models as PM   # noqa: E402

RUN_ID_DEFAULT = "nondossier-merge-v3-20261124"
MANIFEST_PATH = NM.MANIFEST_PATH
COUNTRIES_PATH = HERE.parents[3] / "data" / "countries.json"  # read-only
AGGREGATE_PATH = HERE / "analysis" / "nondossier_merge_v3.json"
MODEL_KEY = "mimo"
MAX_USD = Decimal("30.00")
MODELS = ("muse", "mimo", "deepseek", "glm", "haiku", "luna", "qwen")
# Bounds by derived knowledge class (v3 spec); instructed 1-2
# paragraphs, validated <=3 (v1's proven tolerance).
CLASS_BOUNDS = {
    "parent-only": (20, 170),
    "region-specific": (30, 380),
}
MERGED_MAX_PARAS = 3
MODEL_NAME_RE = re.compile(r"\b(muse|mimo|deepseek|glm|haiku|luna|qwen)\b", re.I)

SYSTEM = """\
You are merging several independent assessments of one region into ONE public summary for a travel-safety website.

Each assessment below is already a factual justification grounded in a 0-1 rating, but you are NOT given any numbers and must not invent any. Each assessment is labelled with the assessor's KNOWLEDGE FLAG: "region-specific" means the assessor had local knowledge beyond the national picture; "parent-only" means it had none. You are also told the region's DERIVED CLASS, computed from those flags.

Write ONE public-facing summary (1-2 paragraphs max), under these rules:
- The parent regime gets AT MOST ONE SENTENCE (for example: "The region is subject to [parent] national law in full, with no local exception."). Never enumerate criminal provisions, recognition requirements, or enforcement practices that belong to the parent dossier -- the visitor already sees the parent regime at country level.
- Locality, not importance, decides what stays. If a candidate sentence's only warrant is the parent text, DELETE it even if it feels important — the parent dossier is one link away on the same page, and repeating it is the failure mode being fixed. Ask of every sentence: could I have written this from the parent text alone? If yes, it goes (beyond the one allowed parent sentence). How local conditions COMBINE with the parent regime may be stated only in terms of the local conditions (e.g. 'port anonymity does not extend to official encounters'), never by re-enumerating parent provisions, enforcement practices, or victimology.
- You are given the PARENT REGIME TEXT, already shown to visitors at country level. Any factual claim already present in that text must NOT be restated in the merged summary, beyond the one allowed parent sentence. The summary must contain only claims that add local information beyond the parent text; use the parent text to identify and exclude parent restatement inside the assessments.
- Focus on what is actually local: geographic and social color from knowledge (terrain, demographics, port or tourism character, conservatism, security presence) and how local conditions modulate, not replace, the parent regime for a trans visitor. Geographic color from knowledge is fine and welcome; do not strip it.
- If the derived class is parent-only: keep the whole summary to about 170 words at most; include one explicit sentence that no region-specific evidence was found distinguishing this region from the national picture (phrased naturally, not as process meta); include no region-specific color beyond one short sentence; imply no local research.
- If the derived class is region-specific: cap the summary at about 380 words; include only local claims, each traceable to at least one assessment.
- Anti-absence discipline: absence of local evidence is not safety; legal ambiguity is not safety.
- Preserve every materially distinct LOCAL claim from the assessments; merge overlapping claims into single statements. If assessments disagree factually, state what is known without inventing detail. Do not add new factual claims.
- Use NO score numbers, NO rating band names or categorical risk labels, NO model or assessor names, NO meta or rating-process language, and NO placeholders -- the region name may appear.
- Write for the site's public UI, as factual prose about the place for a trans visitor.

Reply with only one JSON object, no prose before or after it, with exactly this shape:
{"summary": "<the merged public summary>"}
"""


def aggregate_path() -> Path:
    return AGGREGATE_PATH


def runner_run_id(parts: list[str]) -> str | None:
    script = None
    for p in parts:
        base = p.rsplit("/", 1)[-1]
        if base == "nondossier_merge_v3.py":
            script = base
    if script is None:
        return None
    for i, p in enumerate(parts):
        if p == "--run-id" and i + 1 < len(parts):
            return parts[i + 1]
        if p.startswith("--run-id="):
            return p.split("=", 1)[1]
    return RUN_ID_DEFAULT


def check_single_writer(run_id: str) -> list[int]:
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
            if runner_run_id(parts) == run_id and any(
                    p == "nondossier_merge_v3.py" or p.endswith("/nondossier_merge_v3.py")
                    for p in parts):
                pids.append(pid)
    return sorted(pids)


def load_parent_texts() -> dict:
    """iso3 -> HTML-stripped parent dossier summary (read-only)."""
    doc = json.loads(COUNTRIES_PATH.read_text(encoding="utf-8"))
    out = {}
    for iso3, rec in doc.items():
        text = re.sub(r"<[^>]+>", " ", rec.get("summary") or "")
        out[iso3] = re.sub(r"\s+", " ", text).strip()
    return out


def derive_knowledge_class(bases: list) -> str:
    """parent-only if >= half of contributors flagged parent-only."""
    if not bases:
        return "parent-only"  # no contributors: no local evidence
    n_po = sum(1 for b in bases if b[3] == "parent-only")
    return "parent-only" if n_po * 2 >= len(bases) else "region-specific"


def load_bases() -> dict:
    """sid -> list of (model, rating, basis, knowledge) for ok entries."""
    by_sid: dict[str, list[tuple[str, float, str, str]]] = {}
    identity: dict[str, dict] = {}
    for model in MODELS:
        doc = json.loads((HERE / "analysis" / f"nondossier_{model}.json")
                         .read_text(encoding="utf-8"))
        for r in doc["regions"]:
            if r.get("rating") is None or not r.get("basis"):
                continue
            by_sid.setdefault(r["sid"], []).append(
                (model, float(r["rating"]), r["basis"],
                 r.get("knowledge") or "region-specific"))
            identity[r["sid"]] = {k: r[k] for k in
                                  ("sid", "name", "iso3", "parent_name",
                                   "parent_score")}
    return by_sid, identity


def build_user(entry: dict, bases: list, knowledge_class: str,
               parent_text: str = "") -> str:
    parts = [
        f"Region: {entry['name']}",
        f"Parent country: {entry['parent_name']} ({entry['iso3']})",
        f"Parent name: {entry['parent_name']}",
        f"Derived knowledge class: {knowledge_class}",
        "",
        "PARENT REGIME TEXT (already shown to visitors at country level; "
        "do not restate its claims beyond the one allowed parent sentence):",
        parent_text or "(no parent text available)",
        "",
        "Independent assessments of this region "
        "(each already a factual justification, with its knowledge flag):",
    ]
    for i, (_model, _rating, basis, knowledge) in enumerate(bases, 1):
        parts.append(f"\nAssessment {i} [knowledge flag: {knowledge}]:\n{basis}")
    return "\n".join(parts) + "\n"


def _string_literals(text: str) -> list[str]:
    """All JSON string literals in text, in order (escape-aware scan)."""
    out, i, n = [], 0, len(text)
    while i < n:
        if text[i] != '"':
            i += 1
            continue
        j, esc = i + 1, False
        while j < n:
            c = text[j]
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                break
            j += 1
        if j >= n:
            break
        try:
            out.append(json.loads(text[i:j + 1]))
        except Exception:
            pass
        i = j + 1
    return out


def parse_merged(content: str, knowledge_class: str = "region-specific") -> dict:
    import single_rate_v4 as V4  # noqa: E402  (shared JSON extraction)
    if not isinstance(content, str):
        raise ValueError("content is not text")
    text = V4._extract_json_text(content)
    # Strict, then lenient (literal newlines inside JSON strings are a
    # recurring merger formatting flaw, not a content flaw).
    parsed = None
    for strict in (True, False):
        try:
            parsed = json.loads(text, strict=strict)
            break
        except Exception:
            parsed = None
    if isinstance(parsed, dict) and isinstance(parsed.get("summary"), str):
        if set(parsed) == {"summary"}:
            return _validate_summary(parsed["summary"], knowledge_class)
        # Extra string keys (e.g. region_specifics): join all string
        # values in order so no factual claim is dropped.
        vals = [v for v in parsed.values() if isinstance(v, str) and v.strip()]
        if vals:
            return _validate_summary("\n\n".join(vals), knowledge_class)
    # Salvage (same single attempt, no new call): the merger sometimes
    # emits paragraphs as comma-separated JSON strings ({"summary": "p1", "p2"})
    # instead of one string with \n\n. Join the string literals after the
    # "summary" key as paragraphs and validate the result identically.
    literals = _string_literals(content)
    if literals and literals[0] == "summary" and len(literals) >= 2:
        return _validate_summary("\n\n".join(literals[1:]), knowledge_class)
    # Unterminated salvage: output truncated before the closing quote/brace.
    m = re.search(r'"summary"\s*:\s*"', text)
    if m:
        rest = text[m.end():].rstrip()
        for suffix in ('"}', '",', '"', '}'):
            if rest.endswith(suffix):
                rest = rest[:-len(suffix)].rstrip()
                break
        if rest:
            return _validate_summary(rest, knowledge_class)
    raise ValueError("output keys do not match {summary}")


def _validate_summary(summary: str, knowledge_class: str = "region-specific") -> dict:
    summary = summary.strip()
    min_words, max_words = CLASS_BOUNDS.get(knowledge_class,
                                            CLASS_BOUNDS["region-specific"])
    words = len(summary.split())
    if words < min_words or words > max_words:
        raise ValueError(f"merged word count {words} outside "
                         f"[{min_words},{max_words}] for {knowledge_class}")
    paras = [p for p in re.split(r"\n\s*\n", summary) if p.strip()]
    if len(paras) > MERGED_MAX_PARAS:
        raise ValueError(f"merged paragraph count {len(paras)} > {MERGED_MAX_PARAS}")
    m = NM.BASIS_SCORE_NUM_RE.search(summary)
    if m:
        raise ValueError(f"merged carries score-shaped number {m.group(0)!r}")
    m = NM.BASIS_META_RE.search(summary)
    if m:
        raise ValueError(f"merged carries rating-process meta {m.group(0)!r}")
    m = MODEL_NAME_RE.search(summary)
    if m:
        raise ValueError(f"merged carries model name {m.group(0)!r}")
    return {"summary": summary}


def _do_one(run_dir: Path, idx: int, entry: dict, bases: list,
              parent_text: str = "") -> dict:
    suffix = f"{idx:04d}"
    labels = {"sid": entry["sid"], "iso3": entry["iso3"], "name": entry["name"]}
    knowledge_class = derive_knowledge_class(bases)
    if not bases:
        doc = dict(labels, cell=idx, status="no_contributors", attempts=0,
                   merged_rating=None, contributing_models=[],
                   n_contributors=0, rating_spread=None,
                   knowledge_class=knowledge_class, merged_summary=None)
        (run_dir / f"result-{suffix}.json").write_text(
            json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
        return doc
    ratings = [b[1] for b in bases]
    merged_rating = sum(ratings) / len(ratings)
    user = build_user(entry, bases, knowledge_class, parent_text)
    try:
        res = PM.call_v4(MODEL_KEY, SYSTEM, user)
    except Exception as e:  # one attempt; preserve failure, no retry
        doc = dict(labels, cell=idx, status="transport_failure", attempts=1,
                   reason=f"{type(e).__name__}: {e}", merged_rating=merged_rating,
                   contributing_models=[b[0] for b in bases],
                   n_contributors=len(bases),
                   rating_spread=max(ratings) - min(ratings),
                   knowledge_class=knowledge_class, merged_summary=None)
        (run_dir / f"result-{suffix}.json").write_text(
            json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
        return doc
    usage = res.get("usage") or {}
    (run_dir / f"attempt-{suffix}.json").write_text(json.dumps(dict(
        labels, cell=idx, model=MODEL_KEY, model_id=PM.SINGLE_MODELS[MODEL_KEY],
        effort="medium", attempts=1, usage=usage,
        raw_response=res["raw_response"]), indent=1, ensure_ascii=False),
        encoding="utf-8")
    try:
        _raw = json.loads(res["raw_response"])
    except Exception:
        _raw = {}
    if isinstance(_raw, dict) and (_raw.get("error") or not _raw.get("choices")):
        # Provider error (e.g. 504 timeout): no usage, no charge, no output.
        # Record as a gap and CONTINUE; do not halt the run.
        doc = dict(labels, cell=idx, status="transport_failure", attempts=1,
                   usage=usage, merged_rating=merged_rating,
                   contributing_models=[b[0] for b in bases],
                   n_contributors=len(bases),
                   rating_spread=max(ratings) - min(ratings),
                   knowledge_class=knowledge_class,
                   reason=f"ProviderError: {(_raw.get('error') or {}).get('message', 'no choices')}",
                   merged_summary=None)
        (run_dir / f"result-{suffix}.json").write_text(
            json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
        return doc
    if "cost_usd" not in usage:
        doc = dict(labels, cell=idx, status="stopped_unknown_charge", attempts=1,
                   usage=usage, merged_rating=merged_rating,
                   contributing_models=[b[0] for b in bases],
                   n_contributors=len(bases),
                   rating_spread=max(ratings) - min(ratings),
                   knowledge_class=knowledge_class, merged_summary=None)
        (run_dir / f"result-{suffix}.json").write_text(
            json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
        return doc
    try:
        raw = json.loads(res["raw_response"])
        content = ((raw.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    except Exception as e:
        doc = dict(labels, cell=idx, status="rejected", attempts=1,
                   cost_usd=usage["cost_usd"], usage=usage,
                   merged_rating=merged_rating,
                   contributing_models=[b[0] for b in bases],
                   n_contributors=len(bases),
                   rating_spread=max(ratings) - min(ratings),
                   knowledge_class=knowledge_class,
                   parse_error=f"raw-response parse: {type(e).__name__}: {e}",
                   merged_summary=None)
        (run_dir / f"result-{suffix}.json").write_text(
            json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
        return doc
    (run_dir / f"content-{suffix}.txt").write_text(content, encoding="utf-8")
    parsed, perr = None, None
    try:
        parsed = parse_merged(content, knowledge_class)
    except Exception as e:  # preserve the failed draw; never retry
        perr = f"{type(e).__name__}: {e}"
    doc = dict(labels, cell=idx, model=MODEL_KEY,
               model_id=PM.SINGLE_MODELS[MODEL_KEY],
               status="ok" if parsed else "rejected", attempts=1,
               cost_usd=usage["cost_usd"], usage=usage,
               merged_rating=merged_rating,
               contributing_models=[b[0] for b in bases],
               n_contributors=len(bases),
               rating_spread=max(ratings) - min(ratings),
               knowledge_class=knowledge_class,
               merged_summary=parsed["summary"] if parsed else None,
               parse_error=perr)
    (run_dir / f"result-{suffix}.json").write_text(
        json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    return doc


def _aggregate(run_id: str, run_dir: Path, entries: list) -> dict:
    out, total = [], Decimal("0")
    statuses = Counter()
    for idx, entry in enumerate(entries, 1):
        path = run_dir / f"result-{idx:04d}.json"
        if not path.is_file():
            statuses["missing"] += 1
            out.append(dict(sid=entry["sid"], name=entry["name"],
                            iso3=entry["iso3"], merged_summary=None,
                            merged_rating=None, contributing_models=[],
                            n_contributors=0, rating_spread=None,
                            knowledge_class=None, status="missing"))
            continue
        res = json.loads(path.read_text(encoding="utf-8"))
        statuses[res["status"]] += 1
        if "cost_usd" in res:
            total += Decimal(res["cost_usd"])
        out.append(dict(sid=res["sid"], name=res["name"], iso3=res["iso3"],
                        merged_summary=res.get("merged_summary"),
                        merged_rating=res.get("merged_rating"),
                        contributing_models=res.get("contributing_models", []),
                        n_contributors=res.get("n_contributors", 0),
                        rating_spread=res.get("rating_spread"),
                        knowledge_class=res.get("knowledge_class"),
                        status=res["status"]))
    ok = [e for e in out if e["status"] == "ok"]
    spreads = [e["rating_spread"] for e in out if e["rating_spread"] is not None]
    return {
        "run_id": run_id,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "instrument": "nondossier-merge-v3-mimo-v4 (mean of ok bases, unblinded; knowledge-flag derived class, parent-regime capped at one sentence, hardened locality discipline)",
        "model": MODEL_KEY, "model_id": PM.SINGLE_MODELS[MODEL_KEY],
        "effort": "medium", "attempts_per_region": 1,
        "frozen_manifest": "frozen/nondossier_muse_manifest.json",
        "n_regions": len(entries),
        "status_counts": dict(statuses),
        "total_usd": str(total),
        "mean_spread": (sum(spreads) / len(spreads)) if spreads else None,
        "regions": out,
    }


def run(run_id: str, limit: int | None = None) -> int:
    others = check_single_writer(run_id)
    if others:
        print(f"single-writer guard: run-id {run_id} already has a runner, "
              f"PID(s)={others}; refusing to launch", flush=True)
        return 2
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entries = [{k: r[k] for k in ("sid", "name", "iso3", "parent_name",
                                  "parent_score")}
               for r in manifest["regions"]]
    by_sid, _identity = load_bases()
    parent_texts = load_parent_texts()
    # Key alignment is by sid against the manifest scope.
    missing_sids = [e["sid"] for e in entries if e["sid"] not in by_sid]
    print(f"scope={len(entries)} regions, {len(missing_sids)} with no ok bases",
          flush=True)
    run_dir = HERE / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    total = Decimal("0")
    skipped = 0
    for idx in range(1, len(entries) + 1):
        path = run_dir / f"result-{idx:04d}.json"
        if path.is_file():
            skipped += 1
            res = json.loads(path.read_text(encoding="utf-8"))
            if "cost_usd" in res:
                total += Decimal(res["cost_usd"])
    print(f"{skipped} already completed; model={MODEL_KEY} "
          f"({PM.SINGLE_MODELS[MODEL_KEY]}), effort=medium, "
          f"one attempt per region", flush=True)
    stopped = None
    done = 0
    for idx, entry in enumerate(entries, 1):
        if (run_dir / f"result-{idx:04d}.json").is_file():
            continue
        if limit is not None and done >= limit:
            stopped = f"limit {limit} reached"
            break
        if total >= MAX_USD:
            stopped = f"local budget guard {MAX_USD} USD reached at cell {idx}"
            print(f"STOP {stopped}", flush=True)
            break
        res = _do_one(run_dir, idx, entry, by_sid.get(entry["sid"], []),
                      parent_texts.get(entry["iso3"], ""))
        done += 1
        if "cost_usd" in res:
            total += Decimal(res["cost_usd"])
        if res["status"] == "stopped_unknown_charge":
            stopped = f"unknown charge at cell {idx}"
            print(f"STOP {stopped}", flush=True)
            break
        if idx % 25 == 0 or res["status"] != "ok":
            print(f"  {idx}/{len(entries)} {entry['sid']}:{entry['name']}: "
                  f"{res['status']} (running cost {total} USD)", flush=True)
    aggregate = _aggregate(run_id, run_dir, entries)
    agg_path = aggregate_path()
    agg_path.write_text(json.dumps(aggregate, indent=1, ensure_ascii=False)
                        + "\n", encoding="utf-8")
    (run_dir / "ledger.json").write_text(json.dumps({
        "run_id": run_id, "model": MODEL_KEY,
        "model_id": PM.SINGLE_MODELS[MODEL_KEY], "effort": "medium",
        "n_regions": len(entries), "status_counts": aggregate["status_counts"],
        "total_usd": str(total), "stopped": stopped,
        "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, indent=1) + "\n", encoding="utf-8")
    print(f"done: {aggregate['status_counts']}; exact cost {total} USD; "
          f"aggregate {agg_path}", flush=True)
    return 0 if stopped is None else 5


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default=RUN_ID_DEFAULT)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    return run(a.run_id, a.limit)


if __name__ == "__main__":
    sys.exit(main())
