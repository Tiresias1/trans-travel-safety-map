#!/usr/bin/env python3
"""Deterministic offline tests for the disabled-by-default provider runner.

Every test is mocked: no network, no credential, no provider call, no staging
and no writes outside a temporary fixture directory (except read-only
fingerprints of the repository's data/ and tools/).

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_runner
"""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import runner as R

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SECRET = "fixture-secret-value-DO-NOT-LOG"

PROMPT = ("You are a careful, evidence-bound reviewer of single-country "
          "dossiers.\n") * 3
CAPS = {"attempt_ceiling_including_failures": 40,
        "per_call_max_input_tokens": 20000,
        "per_call_max_output_tokens": 2000,
        "aggregate_max_input_tokens": 800000,
        "aggregate_max_output_tokens": 80000,
        "aggregate_max_usd_including_failures": 10.0,
        "stop_on_unknown_billing_usage": True,
        "retries_selected_for_output": 0,
        "enforced_by_this_code": False}
PRICES = {m: {"prompt": 1e-6, "completion": 2e-6} for m in R.MODELS}
# A response body that satisfies the frozen single-score JSON output contract.
VALID_OUTPUT = json.dumps({"status": "ok", "score": 0.42,
                           "why": "Grounded in the dossier evidence only.",
                           "evidence_ids": "ASSESSMENT; SOURCE EVIDENCE",
                           "discovery": "excluded, no state-engineered discovery",
                           "direct_harms": "facility and document restrictions",
                           "scope_triggers": "national scope, visitor trigger",
                           "uncertainty": "thin sources, no incidence data"})
VALID_EMPTY_OUTPUT = json.dumps({"status": "insufficient_evidence", "score": None,
                                 "why": "Dossier is empty.",
                                 "evidence_ids": "none",
                                 "discovery": "not assessable",
                                 "direct_harms": "not assessable",
                                 "scope_triggers": "not assessable",
                                 "uncertainty": "no evidence supplied"})


def sha(b: bytes) -> str:
    return R.sha(b)


def dump(obj) -> bytes:
    return (json.dumps(obj, indent=1, ensure_ascii=False) + "\n").encode()


class Bomber:
    """Callable that fails the test if the runner touches it (network/secret)."""

    def __init__(self, name):
        self.name = name
        self.calls = 0

    def __call__(self, *a, **k):
        self.calls += 1
        raise AssertionError(f"{self.name} must never be called here")


class CountingTransport:
    def __init__(self, body_fn):
        self.body_fn = body_fn
        self.calls = 0
        self.payloads = []

    def __call__(self, url, payload, headers, timeout):
        self.calls += 1
        self.payloads.append(payload)
        if url != R.CHAT_URL:
            raise AssertionError("runner may only call the fixed chat endpoint")
        if not url.startswith("https://"):
            raise AssertionError("endpoint must be HTTPS")
        if headers.get("Authorization") != "Bearer " + SECRET:
            raise AssertionError("credential must reach the transport, not the log")
        return self.body_fn(payload)


def ok_body(payload, *, usage=None, finish="stop", content=VALID_OUTPUT,
            model=None, provider="fixture-provider"):
    doc = {"id": "cmpl-fixture", "object": "chat.completion",
           "model": model if model is not None else payload["model"],
           "provider": provider,
           "choices": [{"index": 0, "finish_reason": finish,
                        "message": {"role": "assistant", "content": content}}],
           "usage": usage if usage is not None else
                    {"prompt_tokens": 100, "completion_tokens": 50,
                     "total_tokens": 150, "cost": 0.01}}
    return 200, json.dumps(doc)


def build_rows(dup_cell=False):
    rows = []
    combos = [(m, v, d) for m in R.MODELS for v in ("A", "B") for d in (1, 2)]
    for case in ("USA", "GBR", "NPL", "VAT"):
        for m, v, d in combos:
            rows.append({"case": case, "sentinel": "core", "model": m,
                         "variant": v, "draw": d, "label": "DOSSIER"})
    sentinels = [("empty", "", R.MODELS[0], "A", 1), ("empty", "", R.MODELS[1], "B", 1),
                 ("empty", "", R.MODELS[0], "B", 2), ("empty", "", R.MODELS[1], "A", 2),
                 ("neutral_label", "USA", R.MODELS[1], "A", 1),
                 ("neutral_label", "USA", R.MODELS[0], "B", 1),
                 ("neutral_label", "USA", R.MODELS[0], "A", 2),
                 ("neutral_label", "USA", R.MODELS[1], "B", 2)]
    for sentinel, case, m, v, d in sentinels:
        rows.append({"case": case, "sentinel": sentinel, "model": m,
                     "variant": v, "draw": d,
                     "label": "NEUTRAL-7" if sentinel == "neutral_label" else "DOSSIER"})
    for i, row in enumerate(rows):
        row.update({"call": i + 1, "block": 1 if i < 20 else 2, "fresh_context": True})
    if dup_cell:                       # row 6 repeats row 1's predeclared cell
        rows[5] = {**rows[0], "call": 6}
    return rows


def write_fixture(root: Path, *, msg_size=64, dup_cell=False, caps=None,
                  signed=True, probes="complete", probe_cost=0.001) -> dict:
    (root / "frozen" / "packets").mkdir(parents=True, exist_ok=True)
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "preflight.md").write_text(
        "fixture preflight procedure (exact bytes bound by the receipt)\n",
        encoding="utf-8")
    (root / "preflight-signoff.md").write_text(
        "fixture claim-level sign-off artifact (distinct from the procedure)\n",
        encoding="utf-8")
    for name in ("single_a.txt", "single_b.txt"):
        (root / "frozen" / name).write_text(PROMPT, encoding="utf-8")
    for iso in ("USA", "GBR", "NPL", "VAT"):
        (root / "frozen" / "packets" / f"{iso}.txt").write_text(
            f"fixture packet {iso}\n", encoding="utf-8")
    (root / "ledger.json").write_text('{"fixture": true}\n', encoding="utf-8")
    (root / "data" / "countries.json").write_text('{"USA": {}}\n', encoding="utf-8")

    rows = build_rows(dup_cell)
    msgs = [{"call": r["call"], "message": f"{r['label']}\n\n" + "x" * msg_size,
             "message_sha256": sha(f"{r['label']}\n\n".encode()
                                   + b"x" * msg_size)} for r in rows]
    (root / "frozen" / "schedule.json").write_bytes(dump(rows))
    (root / "frozen" / "user_messages.json").write_bytes(dump(msgs))
    prompt_bytes = len(PROMPT.encode("utf-8"))
    plan_units = [prompt_bytes + len(m["message"].encode("utf-8"))
                  + R.FIXED_OVERHEAD_TOKENS_PER_CALL for m in msgs]

    def fmeta(rel):
        b = (root / rel).read_bytes()
        return {"sha256": sha(b), "bytes": len(b)}

    manifest = {
        "experiment": "fixture", "version": "fixture",
        "git_commit": "fixture-commit-0000",
        "evidence_snapshot": {"path": "data/countries.json",
                              "sha256": sha((root / "data" / "countries.json")
                                            .read_bytes()),
                              "git_commit": "fixture-commit-0000"},
        "derived_prompts": {n: fmeta(f"frozen/{n}")
                            for n in ("single_a.txt", "single_b.txt")},
        "packets": {iso: fmeta(f"frozen/packets/{iso}.txt")
                    for iso in ("USA", "GBR", "NPL", "VAT")},
        "schedule_file_sha256": sha((root / "frozen" / "schedule.json").read_bytes()),
        "user_messages_file_sha256": sha((root / "frozen" / "user_messages.json")
                                         .read_bytes()),
        "ledger_sha256": sha((root / "ledger.json").read_bytes()),
        "models": list(R.MODELS),
        "requested_settings": dict(R.REQUESTED_SETTINGS),
        "proposed_caps": dict(caps or CAPS),
        "reservation_amendment": {
            "id": "pre-outcome-reservation-amendment-1",
            "unit": "fixture units",
            "per_call_input_reservation_units": R.RESERVATION_PER_CALL_UNITS,
            "aggregate_input_reservation_units": R.RESERVATION_AGGREGATE_UNITS,
            "plan_max_per_call_units": max(plan_units),
            "plan_aggregate_units": sum(plan_units),
            "preserved_original_proposal": dict(R.PRESERVED_PROPOSED_INPUT_CAPS),
        },
        "attempt_ceiling": 40,
    }
    (root / "frozen" / "manifest.json").write_bytes(dump(manifest))

    # Order matters: the ARCHIVAL original receipt is created first (immutable;
    # the original probe records chain to its hash), then the probe archive,
    # then the independent review of the adaptive follow-up amendment, then the
    # amended execution receipt that binds all of them.
    write_archival_receipt(root)
    (root / "reviews").mkdir(exist_ok=True)
    (root / R.PROBE_FOLLOWUP_REVIEW_REL).write_text(
        "fixture independent review of probe-followup-amendment.md: adaptation, "
        "gates, accounting, fixed requests and stopping rules inspected "
        "offline\n", encoding="utf-8")
    write_probe_fixture(root, probes, cost=probe_cost)
    if signed:
        write_receipt(root)
    return {"root": root, "receipt": root / R.RECEIPT_NAME,
            "data_path": root / "data" / "countries.json", "probes": probes}


def write_archival_receipt(root: Path) -> str:
    """Fixture stand-in for the ORIGINAL schema-v3 preflight receipt: archival,
    immutable evidence that the amended receipt must bind and that every
    original probe record chains to. Created once before the probe fixture and
    NEVER rewritten afterwards (tests fingerprint it to prove that)."""
    path = root / R.ARCHIVAL_RECEIPT_NAME
    if not path.is_file():
        doc = {"receipt_version": R.ARCHIVAL_RECEIPT_VERSION,
               "fixture_role": "archival original receipt (immutable)",
               "archived_at": "2026-01-01T00:00:00+00:00"}
        path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return sha(path.read_bytes())


def write_probe_fixture(root: Path, spec="complete", *, cost=0.001) -> None:
    """Fixture-only archive of probes and independent reviews that a separate
    authorized process and reviewers already produced. This worker never
    creates real probes, reviews or receipts outside tests.

    Specs:
      none            - no probes at all;
      one             - probe-1 only (completed, reviewed_ok);
      originals       - the archived original reality: probe-1 completed
                        + reviewed_ok, probe-2 STOPPED (failure) + reviewed_failure;
      complete        - originals + probe-3/probe-4 completed + reviewed_ok;
      unreviewed      - like complete but with NO review.json anywhere;
      followup-failed - originals + probe-3 completed + probe-4 STOPPED;
      followup3-failed - originals + probe-3 STOPPED + probe-4 completed
                        (fabricated post-failure state; scoring must refuse).
    """
    (root / "probes").mkdir(exist_ok=True)
    if spec == "none":
        return
    receipt_sha = write_archival_receipt(root)
    manifest_sha = sha((root / "frozen" / "manifest.json").read_bytes())
    amendment_sha = sha((HERE / "probe-amendment.md").read_bytes())
    followup_amendment_sha = sha((HERE / "probe-followup-amendment.md")
                                 .read_bytes())
    if spec == "one":
        wanted = ["probe-1"]
    elif spec == "originals":
        wanted = list(R.ORIGINAL_PROBE_SLOTS)
    else:                               # complete / unreviewed / followup-failed
        wanted = list(R.PROBE_SLOTS)
    for slot in wanted:
        is_original = slot in R.ORIGINAL_PROBE_SLOTS
        stopped = (slot == "probe-2"
                   or (spec == "followup-failed" and slot == "probe-4")
                   or (spec == "followup3-failed" and slot == "probe-3"))
        d = root / "probes" / slot
        d.mkdir(exist_ok=True)
        dispatch = {"slot": slot, "model": R.PROBE_SLOT_MODELS[slot],
                    "attempt_kind": "operational_probe",
                    "attempt_phase": ("original" if is_original
                                      else "adaptive_followup"),
                    "scoring_request": False,
                    "preflight_receipt_sha256": receipt_sha,
                    "manifest_sha256": manifest_sha,
                    "probe_amendment_sha256": amendment_sha,
                    "dispatched_at": "2026-01-01T00:00:00+00:00",
                    "retry": False}
        if not is_original:
            dispatch["probe_followup_amendment_sha256"] = followup_amendment_sha
            dispatch["adapted_after"] = {"original_failure_slot": "probe-2"}
        (d / "dispatch.json").write_text(json.dumps(dispatch), encoding="utf-8")
        result = {"slot": slot, "model": R.PROBE_SLOT_MODELS[slot],
                  "attempt_kind": "operational_probe",
                  "attempt_phase": ("original" if is_original
                                    else "adaptive_followup"),
                  "scoring_request": False,
                  "status": "stopped" if stopped else "completed",
                  "requested_settings": R.PROBE_SLOT_SETTINGS[slot],
                  "preflight_receipt_sha256": receipt_sha,
                  "finished_at": "2026-01-01T00:00:01+00:00",
                  "usage": {"prompt_tokens": 30, "completion_tokens": 5,
                            "total_tokens": 35, "cost": cost},
                  "used_input_tokens": 30, "used_output_tokens": 5,
                  "used_usd": cost,
                  "retry": False}
        if stopped:
            result["stop_reason"] = "fixture stopped probe"
            result["errors"] = ["fixture stopped probe"]
        (d / "probe-result.json").write_text(json.dumps(result), encoding="utf-8")
        if spec == "unreviewed":
            continue                    # gate must refuse: no independent review
        (d / "review.json").write_text(json.dumps({
            "status": (R.REVIEW_FAILURE_STATUS if stopped
                       else R.REVIEW_OK_STATUS),
            "probe_slot": slot,
            "reviewed_by": "fixture reviewer",
            "reviewed_at": "2026-01-01T00:00:02+00:00",
            "statement": ("archived failure confirmed against the recorded bytes"
                          if stopped else
                          "probe envelope, usage and cost reviewed")}),
            encoding="utf-8")


def write_receipt(root: Path, *, bindings_update=None, status="signed_off",
                   live_status=None, residual=None,
                   sources=None, legacy=False, extra=None,
                   drop=None, record_sha_overrides=None) -> Path:
    """Schema-v4 AMENDED execution receipt (probe_followup_receipt.json), bound
    to the amended runner/protocol/reviews and the archival original receipt
    bytes. Default live status: observed only when all FOUR probe archives with
    reviews exist (the eight hash-bound entries); otherwise unobserved. Missing
    probe files hash to the empty string so structural checks still run. The
    original preflight_receipt.json stays archival and is never rewritten."""
    write_archival_receipt(root)
    manifest = json.loads((root / "frozen" / "manifest.json").read_text())
    bindings = R.current_bindings(root, root / "data" / "countries.json")
    if bindings_update:
        bindings.update(bindings_update)
    if live_status is None:
        live_status = ("observed_in_bounded_probe"
                       if all((root / "probes" / slot / name).is_file()
                              for slot in R.PROBE_SLOTS
                              for name in ("probe-result.json", "review.json"))
                       else "unobserved")
    live = {"status": live_status}
    if live_status == "observed_in_bounded_probe":
        entries = []
        for slot in R.PROBE_SLOTS:
            for name in ("probe-result.json", "review.json"):
                p = root / "probes" / slot / name
                entries.append({"path": f"probes/{slot}/{name}",
                                "sha256": sha(p.read_bytes()) if p.is_file()
                                          else sha(b"")})
        if record_sha_overrides:
            for e in entries:
                if e["path"] in record_sha_overrides:
                    e["sha256"] = record_sha_overrides[e["path"]]
        try:
            of_status = json.loads((root / "probes" / "probe-2"
                                    / "probe-result.json")
                                   .read_text(encoding="utf-8")).get("status")
        except (OSError, ValueError):
            of_status = "stopped"
        live.update({"observed_at": "2026-01-01T00:00:00+00:00",
                     "scope": "four fixed non-country schema/usage probes: two "
                              "originals + two adaptive follow-ups (fixture)",
                     "record": {"probe_evidence": entries,
                                "original_failure": {"slot": "probe-2",
                                                     "status": of_status}}})
    receipt = {
        "receipt_version": R.RECEIPT_VERSION,
        "preflight": {"status": status, "document": "preflight.md",
                      "signoff_artifact": "preflight-signoff.md",
                      "reviewed_by": "fixture reviewer",
                      "reviewed_at": "2026-01-01T00:00:00+00:00",
                      "statement": "claim-level preflight performed against the "
                                   "exact frozen packets"},
        "provider_semantics": {
            "documentation": {
                "status": "documented",
                "sources": ["OpenRouter API docs (fixture)"] if sources is None
                           else sources,
                "reviewed_by": "fixture reviewer",
                "reviewed_at": "2026-01-01T00:00:00+00:00"},
            "live_behavior": live,
            "residual_assumptions": [
                "fixture residual assumption: live usage shape untested"]
                if residual is None else residual,
        },
        "source_commit": manifest["git_commit"],
        "bindings": bindings,
    }
    if legacy:
        receipt["provider_api_semantics"] = {"verified": True,
                                             "notes": "false claim"}
    if extra:
        receipt.update(extra)
    if drop:
        for key in drop:
            receipt.pop(key, None)
    path = root / R.RECEIPT_NAME
    path.write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    return path


def make_cfg(fx, run_id="fixture-run", *, transport=None, prices=None,
             secret=SECRET, receipt=None, probe=False):
    return {"execute": True, "run_id": run_id, "probe": probe,
            "receipt": Path(receipt) if receipt else fx["receipt"],
            "root": fx["root"], "data_path": fx["data_path"],
            "transport": transport or CountingTransport(ok_body),
            "price_fetch": (lambda: prices) if prices is not None
                           else (lambda: dict(PRICES)),
            "secret_loader": (lambda: secret)}


def stat_fingerprint(paths) -> dict:
    out = {}
    for base in paths:
        for p in sorted(base.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                st = p.stat()
                out[str(p)] = (st.st_size, st.st_mtime_ns)
    return out


def tree_fingerprint(root: Path, skip=()) -> dict:
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(s in p.relative_to(root).parts for s in skip):
            out[str(p.relative_to(root))] = sha(p.read_bytes())
    return out


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cf-runner-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "exp"

    def fx(self, **kw):
        return write_fixture(self.root, **kw)


class DisabledByDefault(unittest.TestCase):
    def test_no_network_no_secret_no_writes_when_disabled(self):
        net, prices, secret = Bomber("transport"), Bomber("price fetch"), \
            Bomber("secret loader")
        root = Path(tempfile.mkdtemp(prefix="cf-disabled-"))
        self.addCleanup(shutil.rmtree, root, True)
        code = R.run({"execute": False, "run_id": None, "receipt": None,
                      "root": root, "data_path": root / "data" / "countries.json",
                      "transport": net, "price_fetch": prices,
                      "secret_loader": secret})
        self.assertEqual(code, R.EXIT_USAGE)
        self.assertEqual((net.calls, prices.calls, secret.calls), (0, 0, 0))
        self.assertFalse((root / "runs").exists())      # nothing written

    def test_credential_flags_rejected_on_cli(self):
        for flag in ("--key", "--api-key", "--token", "--secret"):
            with self.assertRaises(R.Refusal) as ctx:
                R.parse_args(["--execute", "--run-id", "r", flag, "value"])
            self.assertEqual(ctx.exception.code, R.EXIT_USAGE)
            self.assertIn("never be passed on the command line", ctx.exception.reason)
        with self.assertRaises(R.Refusal):
            R.parse_args(["--execute", "--run-id", "r", "--unknown"])

    def test_execute_without_receipt_stops_before_network_and_secret(self):
        net, prices, secret = Bomber("transport"), Bomber("price fetch"), \
            Bomber("secret loader")
        real_post, real_get, real_secret = (R.https_post, R.fetch_prices,
                                            R.load_secret)
        R.https_post, R.fetch_prices, R.load_secret = net, prices, secret
        try:
            code = R.main(["--execute", "--run-id", "no-receipt-run"])
        finally:
            R.https_post, R.fetch_prices, R.load_secret = (real_post, real_get,
                                                           real_secret)
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual((net.calls, prices.calls, secret.calls), (0, 0, 0))
        self.assertFalse((HERE / "runs" / "no-receipt-run").exists())


class ReceiptAndDrift(FixtureCase):
    def test_receipt_hash_mismatch_refused_before_any_request(self):
        fx = self.fx()
        transport = CountingTransport(ok_body)
        cfg = make_cfg(fx, transport=transport)
        cfg["receipt"] = write_receipt(self.root, bindings_update={
            "frozen/packets/USA.txt": "0" * 64})
        code = R.run(cfg)
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(transport.calls, 0)
        self.assertFalse((self.root / "runs").exists())

    def test_source_drift_after_receipt_refused(self):
        fx = self.fx()
        transport = CountingTransport(ok_body)
        (self.root / "frozen" / "packets" / "USA.txt").write_text(
            "tampered packet\n", encoding="utf-8")
        code = R.run(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(transport.calls, 0)
        self.assertFalse((self.root / "runs").exists())

    def test_unsynced_or_unsigned_receipt_refused(self):
        fx = self.fx()
        for kwargs in ({"status": "draft"}, {"live_status": "unobserved"},
                       {"residual": []}, {"sources": []}, {"legacy": True}):
            transport = CountingTransport(ok_body)
            cfg = make_cfg(fx, transport=transport)
            cfg["receipt"] = write_receipt(self.root, **kwargs)
            self.assertEqual(R.run(cfg), R.EXIT_GATE, kwargs)
            self.assertEqual(transport.calls, 0, kwargs)

    def test_receipt_source_commit_must_match_manifest(self):
        fx = self.fx()
        cfg = make_cfg(fx, transport=CountingTransport(ok_body))
        rec = json.loads(fx["receipt"].read_text())
        rec["source_commit"] = "0000000000000000000000000000000000000000"
        fx["receipt"].write_text(json.dumps(rec), encoding="utf-8")
        self.assertEqual(R.run(cfg), R.EXIT_GATE)

    def test_missing_frozen_file_refused(self):
        fx = self.fx()
        (self.root / "frozen" / "single_b.txt").unlink()
        code = R.run(make_cfg(fx, transport=CountingTransport(ok_body)))
        self.assertEqual(code, R.EXIT_GATE)


class BudgetReservations(FixtureCase):
    def test_real_frozen_inputs_fit_the_amended_reservation_ceilings(self):
        manifest = json.loads((HERE / "frozen" / "manifest.json").read_text())
        sched = json.loads((HERE / "frozen" / "schedule.json").read_text())
        msgs = json.loads((HERE / "frozen" / "user_messages.json").read_text())
        caps = R.declared_limits(manifest)
        plan = R.build_plan(manifest, sched, msgs, caps)
        self.assertEqual(plan["problems"], [], "exact plan must fit the amendment")
        # exact plan numbers pre-registered by the amendment
        self.assertEqual(plan["max_per_call_input"], 66611)
        self.assertEqual(plan["aggregate_input"], 2316208)
        self.assertLessEqual(plan["max_per_call_input"],
                             caps["reservation_per_call_units"])
        self.assertLessEqual(plan["aggregate_input"],
                             caps["reservation_aggregate_units"])
        # the original 20 000 / 800 000 proposal is preserved, not reinterpreted
        self.assertGreater(plan["max_per_call_input"],
                           caps["per_call_max_input_tokens"])
        self.assertGreater(plan["aggregate_input"],
                           caps["aggregate_max_input_tokens"])
        self.assertEqual(plan["preserved_original_proposal"],
                         R.PRESERVED_PROPOSED_INPUT_CAPS)
        self.assertNotIn("strict token upper bound", plan["input_method"])
        again = R.build_plan(manifest, sched, msgs, caps)   # deterministic
        self.assertEqual(again["per_call_input"], plan["per_call_input"])
        self.assertEqual(again["problems"], plan["problems"])

    def test_reservation_amendment_drift_refused(self):
        for key, value in (("per_call_input_reservation_units", 66611),
                           ("aggregate_input_reservation_units", 2_316_208),
                           ("preserved_original_proposal",
                            {"per_call_max_input_tokens": 1,
                             "aggregate_max_input_tokens": 1})):
            fx = self.fx(signed=False)
            mpath = self.root / "frozen" / "manifest.json"
            manifest = json.loads(mpath.read_text())
            manifest["reservation_amendment"][key] = value
            mpath.write_text(json.dumps(manifest), encoding="utf-8")
            write_receipt(self.root)
            transport = CountingTransport(ok_body)
            code = R.run(make_cfg(fx, transport=transport))
            self.assertEqual(code, R.EXIT_GATE, key)
            self.assertEqual(transport.calls, 0, key)

    def test_original_proposal_altered_in_caps_refused(self):
        fx = self.fx(signed=False)
        mpath = self.root / "frozen" / "manifest.json"
        manifest = json.loads(mpath.read_text())
        manifest["proposed_caps"]["per_call_max_input_tokens"] = 70000
        mpath.write_text(json.dumps(manifest), encoding="utf-8")
        write_receipt(self.root)
        transport = CountingTransport(ok_body)
        self.assertEqual(R.run(make_cfg(fx, transport=transport)), R.EXIT_GATE)
        self.assertEqual(transport.calls, 0)

    def test_refusal_never_raises_declared_caps(self):
        manifest = json.loads((HERE / "frozen" / "manifest.json").read_text())
        caps = R.declared_limits(manifest)
        self.assertEqual(caps["per_call_max_input_tokens"], 20000)
        self.assertEqual(caps["aggregate_max_input_tokens"], 800000)
        self.assertEqual(caps["reservation_per_call_units"], 70000)
        self.assertEqual(caps["reservation_aggregate_units"], 2400000)
        self.assertEqual(caps["aggregate_max_usd_including_failures"], 10.0)
        self.assertEqual(caps["attempt_ceiling_including_failures"], 40)
        am = manifest["reservation_amendment"]
        self.assertEqual(am["preserved_original_proposal"],
                         {"per_call_max_input_tokens": 20000,
                          "aggregate_max_input_tokens": 800000})
        self.assertIn("not a proven provider-native token bound",
                      am["not_claims"])

    def test_nonfinite_or_invalid_configured_caps_refused_before_accounting(self):
        bad_cases = (
            ("usd_nan", "aggregate_max_usd_including_failures", float("nan")),
            ("usd_inf", "aggregate_max_usd_including_failures", float("inf")),
            ("usd_negative", "aggregate_max_usd_including_failures", -1.0),
            ("usd_bool", "aggregate_max_usd_including_failures", True),
            ("usd_string", "aggregate_max_usd_including_failures", "10.0"),
            ("input_bool", "per_call_max_input_tokens", True),
            ("agg_nan", "aggregate_max_input_tokens", float("nan")),
            ("output_string", "aggregate_max_output_tokens", "80000"),
        )
        for name, key, value in bad_cases:
            with self.subTest(name):
                fx = self.fx(signed=False)
                mpath = self.root / "frozen" / "manifest.json"
                manifest = json.loads(mpath.read_text())
                manifest["proposed_caps"][key] = value
                mpath.write_text(json.dumps(manifest), encoding="utf-8")
                write_receipt(self.root)
                transport = CountingTransport(ok_body)
                code = R.run(make_cfg(fx, transport=transport))
                self.assertEqual(code, R.EXIT_GATE, name)
                self.assertEqual(transport.calls, 0, name)
                self.assertFalse((self.root / "runs").exists(), name)

    def test_ceiling_accounting_units(self):
        fx = self.fx()
        manifest = json.loads((self.root / "frozen" / "manifest.json").read_text())
        sched = json.loads((self.root / "frozen" / "schedule.json").read_text())
        msgs = json.loads((self.root / "frozen" / "user_messages.json").read_text())
        caps = R.declared_limits(manifest)
        plan = R.build_plan(manifest, sched, msgs, caps)
        plan["_sched"] = sched
        plan["worst_usd"] = [0.01] * len(sched)
        used = {"input": 0, "output": 0, "usd": 0.0, "reserved_in": 0}
        self.assertIsNone(R.ceiling_violation(0, 0, plan, used))
        self.assertIn("attempt ceiling",
                      R.ceiling_violation(0, 40, plan, used))
        self.assertIn("aggregate input reservation ceiling",
                      R.ceiling_violation(0, 0, plan,
                                          {"input": 0, "output": 0, "usd": 0.0,
                                           "reserved_in": 2_400_001}))
        self.assertIn("preserved aggregate input proposal",
                      R.ceiling_violation(0, 0, plan,
                                          {"input": 800001, "output": 0, "usd": 0.0,
                                           "reserved_in": 0}))
        self.assertIn("aggregate output ceiling",
                      R.ceiling_violation(0, 0, plan,
                                          {"input": 0, "output": 80001, "usd": 0.0,
                                           "reserved_in": 0}))
        self.assertIn("USD ceiling",
                      R.ceiling_violation(0, 0, plan,
                                          {"input": 0, "output": 0, "usd": 10.0,
                                           "reserved_in": 0}))
        # P1 regression: a NaN/inf/bool used cost can never silence the ceiling
        for bad in (float("nan"), float("inf"), -1.0, True, "1.0"):
            self.assertIn("accounting corrupted",
                          R.ceiling_violation(0, 0, plan,
                                              {"input": 0, "output": 0, "usd": bad,
                                               "reserved_in": 0}), repr(bad))

    def test_nonfinite_billed_cost_helpers(self):
        for bad in (float("nan"), float("inf"), float("-inf"), True, False,
                    "0.5", None):
            self.assertIsNone(R._cost_or_none(bad), repr(bad))
        self.assertEqual(R._cost_or_none(0), 0.0)
        self.assertEqual(R._cost_or_none(1.25), 1.25)
        with self.assertRaises(ValueError):     # NaN/Infinity JSON literals
            R.json_loads_strict('{"cost": NaN}')
        with self.assertRaises(ValueError):
            R.json_loads_strict('{"cost": Infinity}')
        # 1e999 parses to inf without a literal -> still rejected as a cost
        self.assertIsNone(R._cost_or_none(json.loads('{"cost": 1e999}')["cost"]))

    def test_worst_case_cost_reservation_blocks_dispatch(self):
        fx = self.fx()
        expensive = {m: {"prompt": 1.0, "completion": 1.0} for m in R.MODELS}
        transport = CountingTransport(ok_body)
        code = R.run(make_cfg(fx, transport=transport, prices=expensive))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(transport.calls, 0)          # refused before dispatch
        self.assertFalse((self.root / "runs").exists())

    def test_unknown_negative_or_nonfinite_price_refused(self):
        for bad in ("n/a", None, "", float("nan"), float("inf"), -1e-6):
            with self.assertRaises(R.Refusal) as ctx:
                R._price(bad, R.MODELS[0], "prompt")
            self.assertEqual(ctx.exception.code, R.EXIT_GATE)
        self.assertEqual(R._price("1.5e-6", R.MODELS[0], "completion"), 1.5e-6)

    def test_price_fetch_refuses_unexpected_shape(self):
        real = R.https_get
        for status, body in ((503, "unavailable"),
                             (200, "not json"),
                             (200, json.dumps({"unexpected": []})),
                             (200, json.dumps({"data": [{"id": R.MODELS[0],
                                                        "pricing": {}}]})),
                             (200, json.dumps({"data": []}))):
            R.https_get = lambda *a, s=status, b=body, **k: (s, b)
            try:
                with self.assertRaises(R.Refusal) as ctx:
                    R.fetch_prices()
                self.assertEqual(ctx.exception.code, R.EXIT_GATE)
            finally:
                R.https_get = real

    def test_price_fetch_requires_all_pre_registered_models(self):
        real = R.https_get
        body = json.dumps({"data": [
            {"id": R.MODELS[0],
             "pricing": {"prompt": "1e-6", "completion": "2e-6"}}]})
        R.https_get = lambda *a, **k: (200, body)
        try:
            with self.assertRaises(R.Refusal):
                R.fetch_prices()
        finally:
            R.https_get = real


class RequestShape(unittest.TestCase):
    def test_fixed_whitelist_no_fallback_no_cache(self):
        payload = R.build_request(R.MODELS[0], "system", "user",
                                  R.REQUESTED_SETTINGS)
        self.assertEqual(set(payload), set(R.REQUEST_KEYS))
        self.assertEqual(payload["model"], R.MODELS[0])
        self.assertEqual(payload["max_tokens"], 2000)
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["provider"], {"allow_fallbacks": False})
        self.assertNotIn("models", payload)
        blob = json.dumps(payload).lower()
        for banned in ("cache", "fallback", "seed", "tools"):
            self.assertNotIn(banned, blob.replace("allow_fallbacks", ""))
        self.assertEqual([m["role"] for m in payload["messages"]],
                         ["system", "user"])
        self.assertEqual(payload["messages"][1]["content"], "user")

    def test_default_invocation_is_disabled(self):
        self.assertEqual(R.main([]), R.EXIT_USAGE)


class DispatchGuards(FixtureCase):
    def test_missing_usage_stops_after_one_request(self):
        fx = self.fx()

        def body(payload):
            doc = {"model": payload["model"], "finish_reason": "stop",
                   "choices": [{"message": {"content": "x"},
                                "finish_reason": "stop"}]}
            return 200, json.dumps(doc)          # no usage at all

        transport = CountingTransport(body)
        code = R.run(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_STOPPED)
        self.assertEqual(transport.calls, 1)
        self.assert_stopped("missing billed usage")

    def test_invalid_usage_and_missing_cost_stop(self):
        for usage in ({"prompt_tokens": -1, "completion_tokens": 5,
                       "total_tokens": 4, "cost": 0.1},
                      {"prompt_tokens": 10, "completion_tokens": 5,
                       "total_tokens": 15},
                      {"prompt_tokens": 10, "completion_tokens": 5,
                       "total_tokens": 99, "cost": 0.1}):
            root = Path(tempfile.mkdtemp(prefix="cf-usage-"))
            self.addCleanup(shutil.rmtree, root, True)
            fx = write_fixture(root)
            transport = CountingTransport(
                lambda p, u=usage: ok_body(p, usage=u))
            self.assertEqual(R.run(make_cfg(fx, transport=transport)),
                             R.EXIT_STOPPED)
            self.assertEqual(transport.calls, 1)

    def test_returned_model_mismatch_stops(self):
        fx = self.fx()
        other = R.MODELS[1]
        transport = CountingTransport(
            lambda p: ok_body(p, model=other))
        code = R.run(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_STOPPED)
        self.assertEqual(transport.calls, 1)
        self.assert_stopped("model substitution")

    def test_incomplete_or_truncated_output_stops(self):
        cases = ({"content": ""}, {"content": "   "},
                 {"finish": "length"}, {"finish": None})
        for kwargs in cases:
            root = Path(tempfile.mkdtemp(prefix="cf-out-"))
            self.addCleanup(shutil.rmtree, root, True)
            fx = write_fixture(root)
            transport = CountingTransport(lambda p, k=kwargs: ok_body(p, **k))
            self.assertEqual(R.run(make_cfg(fx, transport=transport)),
                             R.EXIT_STOPPED)
            self.assertEqual(transport.calls, 1)

    def test_http_error_and_context_overflow_stop(self):
        fx = self.fx()

        def server_error(payload):
            return 503, "upstream unavailable"

        transport = CountingTransport(server_error)
        self.assertEqual(R.run(make_cfg(fx, transport=transport)),
                         R.EXIT_STOPPED)
        self.assertEqual(transport.calls, 1)

        root = Path(tempfile.mkdtemp(prefix="cf-ctx-"))
        self.addCleanup(shutil.rmtree, root, True)
        fx2 = write_fixture(root)
        transport2 = CountingTransport(
            lambda p: (400, '{"error":{"message":"maximum context length exceeded"}}'))
        self.assertEqual(R.run(make_cfg(fx2, transport=transport2)),
                         R.EXIT_STOPPED)
        self.assertEqual(transport2.calls, 1)
        result = json.loads((root / "runs" / "fixture-run" / "result.json")
                            .read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "stopped")
        self.assertIn("context overflow", result["stop_reason"])

    def test_billed_usage_over_reservation_stops(self):
        fx = self.fx()
        transport = CountingTransport(
            lambda p: ok_body(p, usage={"prompt_tokens": 5000,   # > reserved 413, <= 20000
                                        "completion_tokens": 50,
                                        "total_tokens": 5050, "cost": 0.01}))
        self.assertEqual(R.run(make_cfg(fx, transport=transport)),
                         R.EXIT_STOPPED)
        self.assertEqual(transport.calls, 1)
        self.assert_stopped("reservation/accounting failure")

    def test_billed_input_over_preserved_per_call_proposal_stops(self):
        fx = self.fx()
        transport = CountingTransport(
            lambda p: ok_body(p, usage={"prompt_tokens": 30000,  # > preserved 20000
                                        "completion_tokens": 50,
                                        "total_tokens": 30050, "cost": 0.01}))
        self.assertEqual(R.run(make_cfg(fx, transport=transport)),
                         R.EXIT_STOPPED)
        self.assertEqual(transport.calls, 1)
        self.assert_stopped("preserved per-call input proposal")

    def test_cost_ceiling_stops_before_next_request(self):
        fx = self.fx()
        transport = CountingTransport(
            lambda p: ok_body(p, usage={"prompt_tokens": 100,
                                        "completion_tokens": 50,
                                        "total_tokens": 150, "cost": 1.00}))
        code = R.run(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_STOPPED)
        self.assertEqual(transport.calls, 10)        # 10 x $1.00 = $10.00 ceiling
        self.assert_stopped("USD ceiling")

    def test_duplicate_cell_stops_before_dispatch(self):
        fx = self.fx(dup_cell=True)
        transport = CountingTransport(ok_body)
        code = R.run(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_STOPPED)
        self.assertEqual(transport.calls, 5)         # row 6 repeats row 1's cell
        self.assert_stopped("one attempt per cell")

    def assert_stopped(self, needle: str):
        run_dir = self.root / "runs" / "fixture-run"
        result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "stopped")
        self.assertIn(needle, result["stop_reason"])


class NoOverwriteAndPathEscape(FixtureCase):
    def test_existing_run_never_overwritten(self):
        fx = self.fx()
        existing = self.root / "runs" / "fixture-run"
        existing.mkdir(parents=True)
        (existing / "marker.txt").write_text("prior run\n", encoding="utf-8")
        before = tree_fingerprint(existing)
        transport = CountingTransport(ok_body)
        code = R.run(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(transport.calls, 0)
        self.assertEqual(tree_fingerprint(existing), before)

    def test_run_id_path_escape_refused(self):
        fx = self.fx()
        for bad in ("../escape", "a/b", "..", "", ".hidden", "x" * 70, "a..b"):
            transport = CountingTransport(ok_body)
            code = R.run(make_cfg(fx, run_id=bad, transport=transport))
            self.assertNotEqual(code, R.EXIT_OK, bad)
            self.assertEqual(transport.calls, 0, bad)
        self.assertFalse((self.root.parent / "runs").exists())
        self.assertFalse((self.tmp / "escape").exists())

    def test_attempt_files_are_exclusive_creates(self):
        fx = self.fx()
        self.assertEqual(R.run(make_cfg(fx, transport=CountingTransport(ok_body))),
                         R.EXIT_OK)
        attempts = sorted((self.root / "runs" / "fixture-run"
                           / "attempts").glob("*.json"))
        self.assertEqual(len(attempts), 40)


class SuccessfulMockRun(FixtureCase):
    def test_evidence_written_and_no_production_path_touched(self):
        fx = self.fx()
        prod_before = stat_fingerprint([REPO / "data", REPO / "tools"])
        outside_before = tree_fingerprint(self.root, skip=())
        transport = CountingTransport(ok_body)
        code = R.run(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_OK)
        self.assertEqual(transport.calls, 40)         # exactly one per cell

        run_dir = self.root / "runs" / "fixture-run"
        result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["attempts"], 40)
        self.assertAlmostEqual(result["used_usd"], 0.4, places=6)
        self.assertEqual(result["attempt_ceiling"], 40)

        attempts = sorted((run_dir / "attempts").glob("*.json"))
        self.assertEqual(len(attempts), 40)
        first = json.loads(attempts[0].read_text(encoding="utf-8"))
        for key in ("raw_response", "finish_reason", "requested_model",
                    "returned_model", "returned_provider", "requested_at",
                    "finished_at", "usage", "system_prompt_sha256",
                    "user_message_sha256", "preflight_receipt_sha256",
                    "manifest_sha256", "source_bindings", "reserved_input_tokens",
                    "requested_vs_actual"):
            self.assertIn(key, first, key)
        self.assertIn("parsed_output", first)
        self.assertEqual(first["parsed_output"]["score"], 0.42)
        self.assertNotIn("unreconciled_liability", first)
        for key in ("reservation_amendment", "provider_semantics",
                    "prior_run_state", "budget_note"):
            self.assertIn(key, result, key)
        self.assertIsNone(result["unreconciled_liability"])
        self.assertEqual(result["used_reserved_input_units"],
                         result["plan"]["aggregate_input"])
        for label in ("runner.py", "budget-amendment.md",
                      "evidence-preflight-amendment.md",
                      "independent-evidence-review", "independent-budget-review",
                      "independent-evidence-preflight-followup"):
            self.assertIn(label, result["receipt_bindings"], label)
        self.assertEqual(first["requested_model"], first["returned_model"])
        self.assertEqual(first["finish_reason"], "stop")
        self.assertEqual(first["usage"]["prompt_tokens"], 100)
        self.assertEqual(json.loads(first["raw_response"])["id"], "cmpl-fixture")

        # nothing outside the new run directory was written
        outside_after = tree_fingerprint(self.root, skip=())
        for path, digest in outside_before.items():
            self.assertEqual(outside_after.get(path), digest, path)
        created = set(outside_after) - set(outside_before)
        self.assertTrue(all(p.startswith("runs/") for p in created), created)
        # no production data, tools, renderer or config output changed
        self.assertEqual(prod_before, stat_fingerprint([REPO / "data",
                                                        REPO / "tools"]))
        # credentials never reach any written byte
        for p in run_dir.rglob("*.json"):
            text = p.read_text(encoding="utf-8")
            self.assertNotIn(SECRET, text, p)
            self.assertNotIn("Bearer", text, p)
        # request shape stayed the frozen one for every dispatched call
        for payload in transport.payloads:
            self.assertEqual(set(payload), set(R.REQUEST_KEYS))
            self.assertEqual(payload["messages"][0]["content"], PROMPT)
            self.assertEqual(payload["max_tokens"], 2000)


class OutputContract(FixtureCase):
    """The frozen single-score JSON output contract is actually validated."""

    def test_valid_contract_accepted(self):
        for text in (VALID_OUTPUT, VALID_EMPTY_OUTPUT,
                     json.dumps({**json.loads(VALID_OUTPUT), "score": 0}),
                     json.dumps({**json.loads(VALID_OUTPUT), "score": 1.0}),
                     json.dumps({**json.loads(VALID_OUTPUT),
                                 "evidence_ids": ["a", "b"]})):
            obj = R.validate_output_contract(text)
            self.assertIsInstance(obj, dict)

    def test_malformed_contract_rejected(self):
        bad = {
            "not json": "this is prose, not json",
            "fenced": "```json\n" + VALID_OUTPUT + "\n```",
            "prose before": "Here you go: " + VALID_OUTPUT,
            "top-level list": "[1, 2, 3]",
            "missing status": json.dumps({"score": 0.5}),
            "unknown status": json.dumps({"status": "maybe", "score": 0.5}),
            "ok missing score": json.dumps({"status": "ok"}),
            "score string": json.dumps({**json.loads(VALID_OUTPUT),
                                        "score": "0.5"}),
            "score bool": json.dumps({**json.loads(VALID_OUTPUT), "score": True}),
            "score above one": json.dumps({**json.loads(VALID_OUTPUT), "score": 1.5}),
            "score negative": json.dumps({**json.loads(VALID_OUTPUT), "score": -0.1}),
            "score missing from ok": json.dumps({
                **{k: v for k, v in json.loads(VALID_OUTPUT).items()
                   if k != "score"}, "status": "ok"}),
            "empty with score": json.dumps({**json.loads(VALID_EMPTY_OUTPUT),
                                            "score": 0.5}),
            "empty missing score key": json.dumps({
                k: v for k, v in json.loads(VALID_EMPTY_OUTPUT).items()
                if k != "score"}),
            "missing why": json.dumps({k: v for k, v in
                                       json.loads(VALID_OUTPUT).items()
                                       if k != "why"}),
            "why blank": json.dumps({**json.loads(VALID_OUTPUT), "why": "  "}),
            "diagnostic wrong type": json.dumps({**json.loads(VALID_OUTPUT),
                                                 "discovery": 7}),
            "evidence_ids empty list": json.dumps({**json.loads(VALID_OUTPUT),
                                                   "evidence_ids": []}),
            "evidence_ids bad list": json.dumps({**json.loads(VALID_OUTPUT),
                                                 "evidence_ids": [1, 2]}),
            "nan literal": VALID_OUTPUT.replace("0.42", "NaN"),
        }
        for name, text in bad.items():
            with self.assertRaises(R.Refusal, msg=name) as ctx:
                R.validate_output_contract(text)
            self.assertEqual(ctx.exception.code, R.EXIT_STOPPED, name)

    def test_invalid_output_stops_run_and_retains_raw_without_retry(self):
        root = Path(tempfile.mkdtemp(prefix="cf-contract-"))
        self.addCleanup(shutil.rmtree, root, True)
        fx = write_fixture(root)
        bad = "I scored this dossier 0.7 out of 10."

        def body(payload):
            return 200, json.dumps({
                "model": payload["model"], "provider": "fixture-provider",
                "choices": [{"finish_reason": "stop",
                             "message": {"role": "assistant", "content": bad}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50,
                          "total_tokens": 150, "cost": 0.01}})

        transport = CountingTransport(body)
        self.assertEqual(R.run(make_cfg(fx, transport=transport)), R.EXIT_STOPPED)
        self.assertEqual(transport.calls, 1)              # no auto retry
        attempt_path = root / "runs" / "fixture-run" / "attempts" / "call-001.json"
        attempt = json.loads(attempt_path.read_text(encoding="utf-8"))
        self.assertIn("output contract", attempt["stop_reason"])
        self.assertIn(bad, attempt["raw_response"])       # raw output retained
        # billing was valid and is recorded separately even though output failed
        self.assertTrue(attempt["billed_on_failure"]["parsed"])
        self.assertEqual(attempt["billed_on_failure"]["cost"], 0.01)
        self.assertNotIn("unreconciled_liability", attempt)


class FailedDispatchBilling(FixtureCase):
    def _first_run(self, body_fn):
        fx = self.fx()
        transport = CountingTransport(body_fn)
        code = R.run(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_STOPPED)
        self.assertEqual(transport.calls, 1)              # one attempt, no retry
        run_dir = self.root / "runs" / "fixture-run"
        attempt = json.loads((run_dir / "attempts" / "call-001.json")
                             .read_text(encoding="utf-8"))
        result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
        return fx, attempt, result

    def test_unknown_billed_cost_marks_liability_and_blocks_new_run(self):
        def body(payload):                                # no usage at all
            return 200, json.dumps({
                "model": payload["model"],
                "choices": [{"finish_reason": "stop",
                             "message": {"role": "assistant",
                                         "content": VALID_OUTPUT}}]})

        fx, attempt, result = self._first_run(body)
        self.assertFalse(attempt["billed_on_failure"]["parsed"])
        self.assertIn("unreconciled_liability", attempt)
        self.assertIn("reconciliation", attempt["unreconciled_liability"]["requires"])
        self.assertIsNotNone(result["unreconciled_liability"])
        # a new run may not silently reset the budget
        second = CountingTransport(ok_body)
        code = R.run(make_cfg(fx, run_id="second-run", transport=second))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(second.calls, 0)
        stop = json.loads((self.root / "runs" / "fixture-run" / "result.json")
                          .read_text(encoding="utf-8"))
        self.assertIsNotNone(stop["unreconciled_liability"])

    def test_human_reconciliation_lifts_liability_but_cells_still_block(self):
        def body(payload):
            return 200, json.dumps({
                "model": payload["model"],
                "choices": [{"finish_reason": "stop",
                             "message": {"role": "assistant",
                                         "content": VALID_OUTPUT}}]})

        fx, attempt, _ = self._first_run(body)
        recon = self.root / "runs" / "fixture-run" / "reconciliation.json"
        recon.write_text(json.dumps({"reviewed_by": "human reviewer",
                                     "reviewed_at": "2026-01-02T00:00:00+00:00",
                                     "statement": "charge reconciled against the "
                                                  "provider invoice",
                                     "liability_call": 1}), encoding="utf-8")
        second = CountingTransport(ok_body)
        code = R.run(make_cfg(fx, run_id="second-run", transport=second))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(second.calls, 0)
        # the liability is gone; what blocks now is the cell already attempted
        prior = R.prior_run_state(self.root,
                                  json.loads((self.root / "frozen" / "schedule.json")
                                             .read_text()))
        self.assertEqual(prior["unreconciled"], [])

    def test_completed_prior_run_blocks_new_run(self):
        fx = self.fx()
        first = CountingTransport(ok_body)
        self.assertEqual(R.run(make_cfg(fx, transport=first)), R.EXIT_OK)
        self.assertEqual(first.calls, 40)
        second = CountingTransport(ok_body)
        code = R.run(make_cfg(fx, run_id="second-run", transport=second))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(second.calls, 0)

    def test_unknown_prior_run_state_blocks_new_run(self):
        fx = self.fx()
        orphan = self.root / "runs" / "orphan"
        orphan.mkdir(parents=True)
        second = CountingTransport(ok_body)
        code = R.run(make_cfg(fx, run_id="second-run", transport=second))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(second.calls, 0)
        (orphan / "result.json").write_text(
            json.dumps({"used_usd": float("nan")}), encoding="utf-8")
        third = CountingTransport(ok_body)
        self.assertEqual(R.run(make_cfg(fx, run_id="third-run", transport=third)),
                         R.EXIT_GATE)
        self.assertEqual(third.calls, 0)

    def test_prior_budget_arithmetic_blocks(self):
        fx = self.fx()
        manifest = json.loads((self.root / "frozen" / "manifest.json").read_text())
        sched = json.loads((self.root / "frozen" / "schedule.json").read_text())
        msgs = json.loads((self.root / "frozen" / "user_messages.json").read_text())
        caps = R.declared_limits(manifest)
        plan = R.build_plan(manifest, sched, msgs, caps)
        plan["_sched"] = sched
        R.cost_reservation(plan, PRICES)
        total = sum(plan["worst_usd"])
        clean = {"used_usd": 0.0, "used_input": 0, "used_output": 0}
        self.assertIsNone(R.prior_budget_violation(clean, plan, total))
        self.assertIn("budget already consumed",
                      R.prior_budget_violation(
                          {**clean, "used_usd": 9.99}, plan, total) or "")
        self.assertIn("not a finite",
                      R.prior_budget_violation(
                          {**clean, "used_usd": float("nan")}, plan, total) or "")
        self.assertIn("aggregate input reservation ceiling",
                      R.prior_budget_violation(
                          {**clean, "used_input": 2_400_000}, plan, total) or "")
        self.assertIn("aggregate output ceiling",
                      R.prior_budget_violation(
                          {**clean, "used_output": 80_000}, plan, total) or "")


class ReceiptSemantics(FixtureCase):
    def test_unobserved_live_behavior_valid_but_blocks_execution(self):
        fx = self.fx(signed=False)
        path = write_receipt(self.root, live_status="unobserved")
        receipt = json.loads(path.read_text())
        bindings = R.current_bindings(self.root, self.root / "data" /
                                      "countries.json")
        manifest = json.loads((self.root / "frozen" / "manifest.json").read_text())
        R.verify_receipt(receipt, bindings, manifest)   # structurally honest
        transport = CountingTransport(ok_body)
        cfg = make_cfg(fx, transport=transport, receipt=path)
        code = R.run(cfg)
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(transport.calls, 0)

    def test_false_verification_claim_rejected(self):
        fx = self.fx(signed=False)
        path = write_receipt(
            self.root,
            extra={"provider_semantics": {"documentation": {
                "status": "documented", "sources": ["doc"],
                "reviewed_by": "r", "reviewed_at": "t",
                "verified": True},
                "live_behavior": {"status": "unobserved"},
                "residual_assumptions": ["a"]}})
        transport = CountingTransport(ok_body)
        self.assertEqual(R.run(make_cfg(fx, transport=transport, receipt=path)),
                         R.EXIT_GATE)
        self.assertEqual(transport.calls, 0)
        # legacy v1 shape is rejected outright
        legacy = write_receipt(self.root, legacy=True)
        legacy_transport = CountingTransport(ok_body)
        self.assertEqual(R.run(make_cfg(fx, run_id="r2",
                                        transport=legacy_transport,
                                        receipt=legacy)), R.EXIT_GATE)
        self.assertEqual(legacy_transport.calls, 0)

    def test_receipt_must_bind_runner_amendment_and_reviews(self):
        fx = self.fx()
        receipt = json.loads(fx["receipt"].read_text())
        expected = set(R.BINDING_LABELS) | {lbl for lbl, _ in R.REVIEW_BINDINGS}
        self.assertEqual(set(receipt["bindings"]), expected)
        self.assertEqual(receipt["bindings"]["runner.py"],
                         sha((HERE / "runner.py").read_bytes()))
        self.assertEqual(receipt["bindings"]["budget-amendment.md"],
                         sha((HERE / "budget-amendment.md").read_bytes()))
        self.assertEqual(receipt["bindings"]["probe-amendment.md"],
                         sha((HERE / "probe-amendment.md").read_bytes()))
        # the feasibility-only amendment and the durable follow-up review are
        # bound byte-for-byte to the copies that live beside this runner
        self.assertIn("evidence-preflight-amendment.md", expected)
        self.assertEqual(receipt["bindings"]["evidence-preflight-amendment.md"],
                         sha((HERE / "evidence-preflight-amendment.md").read_bytes()))
        self.assertIn("independent-evidence-preflight-followup", expected)
        followup = HERE / "reviews" / "evidence-preflight-followup.md"
        self.assertTrue(followup.is_file())
        self.assertEqual(receipt["bindings"]
                         ["independent-evidence-preflight-followup"],
                         sha(followup.read_bytes()))
        # the ADAPTIVE follow-up amendment, the archival original receipt and
        # the amendment's independent review are all content-bound too
        self.assertIn("probe-followup-amendment.md", expected)
        self.assertEqual(receipt["bindings"]["probe-followup-amendment.md"],
                         sha((HERE / "probe-followup-amendment.md").read_bytes()))
        self.assertIn(R.ARCHIVAL_RECEIPT_NAME, expected)
        self.assertEqual(receipt["bindings"][R.ARCHIVAL_RECEIPT_NAME],
                         sha((self.root / R.ARCHIVAL_RECEIPT_NAME).read_bytes()))
        self.assertIn(R.PROBE_FOLLOWUP_REVIEW_LABEL, expected)
        self.assertEqual(receipt["bindings"][R.PROBE_FOLLOWUP_REVIEW_LABEL],
                         sha((self.root / R.PROBE_FOLLOWUP_REVIEW_REL)
                             .read_bytes()))
        for label in ("preflight.md", "preflight-signoff.md"):
            self.assertEqual(receipt["bindings"][label],
                             sha((self.root / label).read_bytes()), label)
        for label, path in R.REVIEW_BINDINGS:
            resolved = path if (isinstance(path, Path) and path.is_absolute()) \
                else (self.root / path)   # relative entries live in the experiment
            self.assertTrue(resolved.is_file(), label)
            self.assertEqual(receipt["bindings"][label], sha(resolved.read_bytes()))

    def test_missing_new_binding_label_rejected(self):
        fx = self.fx(signed=False)
        path = write_receipt(self.root, bindings_update={
            "runner.py": "0" * 64})          # hash mismatch
        transport = CountingTransport(ok_body)
        self.assertEqual(R.run(make_cfg(fx, transport=transport, receipt=path)),
                         R.EXIT_GATE)
        self.assertEqual(transport.calls, 0)
        # dropping a required label changes the key set -> refused
        receipt = json.loads(path.read_text())
        del receipt["bindings"]["independent-budget-review"]
        path.write_text(json.dumps(receipt), encoding="utf-8")
        self.assertEqual(R.run(make_cfg(fx, run_id="r2",
                                        transport=CountingTransport(ok_body),
                                        receipt=path)), R.EXIT_GATE)

    def test_missing_feasibility_amendment_and_followup_bindings_rejected(self):
        fx = self.fx(signed=False)
        for i, label in enumerate(("evidence-preflight-amendment.md",
                                   "independent-evidence-preflight-followup")):
            path = write_receipt(self.root)
            receipt = json.loads(path.read_text())
            del receipt["bindings"][label]          # key set now differs
            path.write_text(json.dumps(receipt), encoding="utf-8")
            transport = CountingTransport(ok_body)
            code = R.run(make_cfg(fx, run_id=f"missing-{i}",
                                  transport=transport, receipt=path))
            self.assertEqual(code, R.EXIT_GATE, label)
            self.assertEqual(transport.calls, 0, label)

    def test_tampered_feasibility_amendment_and_followup_bindings_rejected(self):
        fx = self.fx(signed=False)
        path = write_receipt(self.root, bindings_update={
            "evidence-preflight-amendment.md": "0" * 64,
            "independent-evidence-preflight-followup": "1" * 64})
        transport = CountingTransport(ok_body)
        self.assertEqual(R.run(make_cfg(fx, run_id="tampered-bindings",
                                        transport=transport, receipt=path)),
                         R.EXIT_GATE)
        self.assertEqual(transport.calls, 0)
        # a byte change in the bound files themselves must also refuse:
        # re-read the receipt and compare against freshly computed bindings after
        # a single-byte drift of the amendment copy
        receipt = json.loads(path.read_text())
        drifted = bytearray((HERE / "evidence-preflight-amendment.md").read_bytes())
        drifted[0] ^= 0x01
        bindings = R.current_bindings(self.root, self.root / "data" /
                                      "countries.json")
        bindings["evidence-preflight-amendment.md"] = sha(bytes(drifted))
        manifest = json.loads((self.root / "frozen" / "manifest.json").read_text())
        with self.assertRaises(R.Refusal):
            R.verify_receipt(receipt, bindings, manifest)   # hash mismatch


def run_capturing(cfg):
    """Run() with captured stdout so refusal reasons can be asserted."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = R.run(cfg)
    return code, buf.getvalue()


def probe_ok_body(payload, *, usage=None, content='{"probe": "ok"}',
                  model=None):
    doc = {"model": model or payload["model"], "provider": "fixture-provider",
           "choices": [{"finish_reason": "stop",
                        "message": {"role": "assistant", "content": content}}],
           "usage": usage if usage is not None else
                    {"prompt_tokens": 20, "completion_tokens": 5,
                     "total_tokens": 25, "cost": 0.002}}
    return 200, json.dumps(doc)


def _sub(code: str, args, timeout: int = 120):
    """Real child process (offline, mocked transport, no credentials)."""
    return subprocess.run([sys.executable, "-c", code, *map(str, args)],
                          capture_output=True, text=True, timeout=timeout,
                          cwd=str(HERE), env=_child_env())


def _popen(code: str, args):
    return subprocess.Popen([sys.executable, "-c", code, *map(str, args)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, cwd=str(HERE), env=_child_env())


def _child_env():
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


# Child driver: full gated scoring run with a mocked transport that records any
# dispatch in marker file argv[3]; prices JSON in argv[4]; per-call delay argv[5].
RUN_DRIVER = '''
import json, sys, time
from pathlib import Path
import runner as R
root = Path(sys.argv[1]); run_id = sys.argv[2]; marker = Path(sys.argv[3])
prices = json.loads(sys.argv[4]); delay = float(sys.argv[5])
content = json.dumps({"status": "ok", "score": 0.5, "why": "fixture",
                      "evidence_ids": "none", "discovery": "excluded",
                      "direct_harms": "none", "scope_triggers": "none",
                      "uncertainty": "none"})
def transport(url, payload, headers, timeout):
    time.sleep(delay)
    marker.write_text("dispatched")
    return 200, json.dumps({"model": payload["model"],
        "provider": "fixture-provider",
        "choices": [{"finish_reason": "stop",
                     "message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5,
                  "total_tokens": 15, "cost": 0.001}})
cfg = {"execute": True, "run_id": run_id, "probe": False,
       "receipt": root / R.RECEIPT_NAME,
       "root": root, "data_path": root / "data" / "countries.json",
       "transport": transport, "price_fetch": lambda: prices,
       "secret_loader": lambda: "fixture-secret-DO-NOT-LOG"}
sys.exit(R.run(cfg))
'''

# Child driver: takes the experiment lock, waits for the release file, releases
# it (normal holder behaviour).
HOLDER_DRIVER = '''
import sys, time
from pathlib import Path
import runner as R
root = Path(sys.argv[1]); release = Path(sys.argv[2]); who = sys.argv[3]
lock = R.acquire_lock(root, "holder-" + who)
print("LOCKED", flush=True)
deadline = time.time() + 60
while not release.exists() and time.time() < deadline:
    time.sleep(0.02)
R.release_lock(lock, "holder-" + who)
print("RELEASED", flush=True)
'''

# Child driver: simulates a CRASH - takes the lock, leaves a run directory with
# no terminal record, and exits without releasing anything (os._exit).
CRASH_DRIVER = '''
import os, sys
from pathlib import Path
import runner as R
root = Path(sys.argv[1])
R.acquire_lock(root, "crashing-holder")
d = root / "runs" / "crashed-run"
d.mkdir(parents=True, exist_ok=True)
(d / "attempts").mkdir(exist_ok=True)
os._exit(9)
'''


class ExecutionLock(FixtureCase):
    """Experiment-wide exclusive lock: acquired before prior state/budget,
    held through finalization, contention refuses before any call."""

    def test_lock_contention_refuses_before_any_call(self):
        fx = self.fx()
        lock = R.acquire_lock(self.root, "holder")
        try:
            transport = CountingTransport(ok_body)
            code, out = run_capturing(make_cfg(fx, transport=transport))
            self.assertEqual(code, R.EXIT_GATE)
            self.assertEqual(transport.calls, 0)
            self.assertIn("lock is held", out)
            self.assertIn("never deletes", out)
        finally:
            R.release_lock(lock, "holder")
        transport2 = CountingTransport(ok_body)
        self.assertEqual(R.run(make_cfg(fx, transport=transport2)), R.EXIT_OK)

    def test_lock_released_after_run_and_absent_by_default(self):
        fx = self.fx()
        self.assertFalse((self.root / R.LOCK_NAME).exists())
        self.assertEqual(R.run(make_cfg(fx, transport=CountingTransport(ok_body))),
                         R.EXIT_OK)
        self.assertFalse((self.root / R.LOCK_NAME).exists())   # released after
        # disabled default: no lock, no writes
        code = R.run({"execute": False, "run_id": None, "probe": False,
                      "receipt": None, "root": self.root,
                      "data_path": fx["data_path"], "transport": Bomber("net"),
                      "price_fetch": Bomber("prices"),
                      "secret_loader": Bomber("secret")})
        self.assertEqual(code, R.EXIT_USAGE)
        self.assertFalse((self.root / R.LOCK_NAME).exists())

    def test_two_process_lock_race_exactly_one_winner(self):
        fx = self.fx()
        prices = json.dumps(PRICES)
        m1, m2 = self.tmp / "m1.txt", self.tmp / "m2.txt"
        p1 = _popen(RUN_DRIVER, [self.root, "race-a", m1, prices, 0.15])
        p2 = _popen(RUN_DRIVER, [self.root, "race-b", m2, prices, 0.15])
        out1, _ = p1.communicate(timeout=120)
        out2, _ = p2.communicate(timeout=120)
        codes = [p1.returncode, p2.returncode]
        self.assertEqual(sorted(codes), [0, R.EXIT_GATE],
                         f"stdout1={out1[-400:]} stdout2={out2[-400:]}")
        loser_out = out1 if p1.returncode != 0 else out2
        self.assertIn("lock is held", loser_out)
        winners = [m for m in (m1, m2) if m.exists()]
        self.assertEqual(len(winners), 1)      # exactly one process dispatched
        run_dirs = sorted(p.name for p in (self.root / "runs").iterdir()
                          if p.is_dir())
        self.assertEqual(len(run_dirs), 1)
        self.assertFalse((self.root / R.LOCK_NAME).exists())  # winner released

    def test_second_process_exits_early_while_lock_held(self):
        fx = self.fx()
        release = self.tmp / "release"
        holder = _popen(HOLDER_DRIVER, [self.root, release, "early"])
        try:
            lock_path = self.root / R.LOCK_NAME
            for _ in range(300):               # wait for the holder's lock
                if lock_path.exists():
                    break
                time.sleep(0.02)
            self.assertTrue(lock_path.exists(), "holder never acquired the lock")
            marker = self.tmp / "early-marker.txt"
            out = _sub(RUN_DRIVER,
                       [self.root, "contender", marker, json.dumps(PRICES), 0])
            self.assertEqual(out.returncode, R.EXIT_GATE, out.stdout + out.stderr)
            self.assertIn("lock is held", out.stdout)
            self.assertFalse(marker.exists())          # exited before any call
            self.assertFalse((self.root / "runs" / "contender").exists())
            self.assertIsNone(holder.poll(),          # holder still holding
                              "contender must exit while the lock is held")
        finally:
            release.write_text("go\n", encoding="utf-8")
            holder_out, _ = holder.communicate(timeout=60)
            if holder.poll() not in (0, None):
                holder.kill()
        self.assertIn("RELEASED", holder_out)
        self.assertFalse((self.root / R.LOCK_NAME).exists())  # owner released it

    def test_crash_lock_and_incomplete_run_require_human_reconciliation(self):
        fx = self.fx()
        crashed = _sub(CRASH_DRIVER, [self.root])
        self.assertEqual(crashed.returncode, 9, crashed.stdout + crashed.stderr)
        lock_path = self.root / R.LOCK_NAME
        self.assertTrue(lock_path.exists(), "crash must leave the lock in place")
        crashed_dir = self.root / "runs" / "crashed-run"
        self.assertTrue(crashed_dir.is_dir())
        self.assertFalse((crashed_dir / "result.json").exists())

        marker = self.tmp / "crash-marker.txt"
        out1 = _sub(RUN_DRIVER,
                    [self.root, "survivor", marker, json.dumps(PRICES), 0])
        self.assertEqual(out1.returncode, R.EXIT_GATE, out1.stdout + out1.stderr)
        self.assertIn("lock is held", out1.stdout)
        self.assertIn("human must inspect", out1.stdout)
        self.assertTrue(lock_path.exists(),           # never silently deleted
                        "stale lock must survive a refused run")
        self.assertFalse(marker.exists())

        # explicit human reconciliation step 1: inspect and remove the lock
        lock_path.unlink()
        out2 = _sub(RUN_DRIVER,
                    [self.root, "survivor", marker, json.dumps(PRICES), 0])
        self.assertEqual(out2.returncode, R.EXIT_GATE, out2.stdout + out2.stderr)
        self.assertIn("prior run state unknown", out2.stdout)
        self.assertFalse(marker.exists())             # still refused: no calls
        # evidence of the crashed run is intact (never deleted)
        self.assertTrue(crashed_dir.is_dir())
        self.assertFalse((crashed_dir / "result.json").exists())


class ProbeDispatch(FixtureCase):
    """Pre-registered non-country probes: one dispatch per slot, no retry,
    shared ledger, evidence written only under probes/<slot>/."""

    def test_probe_dispatch_success_and_fixed_non_country_request(self):
        fx = self.fx(probes="none")            # receipt: live unobserved
        transport = CountingTransport(probe_ok_body)
        code, out = run_capturing(
            make_cfg(fx, run_id="probe-1", probe=True, transport=transport))
        self.assertEqual(code, R.EXIT_OK, out)
        self.assertEqual(transport.calls, 1)    # one dispatch, no retry
        payload = transport.payloads[0]
        self.assertEqual(set(payload), set(R.REQUEST_KEYS))
        self.assertEqual(payload["model"], R.MODELS[0])
        self.assertEqual(payload["messages"][0]["content"], R.PROBE_SYSTEM)
        self.assertEqual(payload["messages"][1]["content"], R.PROBE_USER)
        self.assertEqual(payload["max_tokens"], 64)
        self.assertEqual(payload["temperature"], 0.0)
        blob = json.dumps(payload)
        country_names = ("United States", "USA", "United Kingdom", "Nepal",
                         "Vatican")
        for banned in (*country_names, "DOSSIER", "NEUTRAL-7", "score",
                       "dossier"):
            self.assertNotIn(banned, blob, banned)
        d = self.root / "probes" / "probe-1"
        self.assertTrue((d / "dispatch.json").is_file())
        result = json.loads((d / "probe-result.json").read_text())
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["attempt_kind"], "operational_probe")
        self.assertFalse(result["scoring_request"])
        self.assertEqual(result["used_usd"], 0.002)
        # probes write nothing into runs/ and leave no lock behind
        self.assertFalse((self.root / "runs").exists())
        self.assertFalse((self.root / R.LOCK_NAME).exists())
        # receipts untouched: the runner never manufactures, edits or replaces
        # either the amended execution receipt or the archival original
        self.assertEqual(json.loads(fx["receipt"].read_text())["receipt_version"],
                         R.RECEIPT_VERSION)
        self.assertEqual(json.loads((self.root / R.ARCHIVAL_RECEIPT_NAME)
                                    .read_text())["receipt_version"],
                         R.ARCHIVAL_RECEIPT_VERSION)
        self.assertEqual(result["attempt_phase"], "original")

    def test_probe_slots_single_dispatch_frozen_order_and_ceiling(self):
        fx = self.fx(probes="none")

        def body(payload):
            # original model-2 at 64 tokens fails (mirrors the real archived
            # probe-2 outcome); everything else succeeds
            if payload["model"] == R.MODELS[1] and payload["max_tokens"] == 64:
                return 200, json.dumps({
                    "model": payload["model"], "provider": "fixture-provider",
                    "choices": [{"finish_reason": "length",
                                 "message": {"role": "assistant",
                                             "content": None}}],
                    "usage": {"prompt_tokens": 53, "completion_tokens": 60,
                              "total_tokens": 113, "cost": 0.001}})
            return probe_ok_body(payload)

        transport = CountingTransport(body)
        # original slot probe-1 dispatches first
        self.assertEqual(R.run(make_cfg(fx, run_id="probe-1", probe=True,
                                        transport=transport)), R.EXIT_OK)
        self.assertEqual(transport.calls, 1)
        # same slot again: refused, no second dispatch (no slot reuse)
        code, out = run_capturing(make_cfg(fx, run_id="probe-1", probe=True,
                                           transport=transport))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertIn("already exists", out)
        self.assertEqual(transport.calls, 1)
        # follow-up refused while an ORIGINAL record is missing
        code, out = run_capturing(make_cfg(fx, run_id="probe-3", probe=True,
                                           transport=transport))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertIn("original probe evidence missing", out)
        self.assertEqual(transport.calls, 1)
        # probe-2 dispatches and FAILS - one dispatch, terminal record, no retry
        code, out = run_capturing(make_cfg(fx, run_id="probe-2", probe=True,
                                           transport=transport))
        self.assertEqual(code, R.EXIT_STOPPED, out)
        self.assertEqual(transport.calls, 2)
        code, out = run_capturing(make_cfg(fx, run_id="probe-2", probe=True,
                                           transport=transport))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(transport.calls, 2)          # failed slot never retried
        p2 = json.loads((self.root / "probes" / "probe-2" / "probe-result.json")
                        .read_text())
        self.assertEqual(p2["status"], "stopped")    # failure preserved
        self.assertIn("http_status", p2)             # captured because received
        # probe-4 may not skip probe-3 (frozen order)
        code, out = run_capturing(make_cfg(fx, run_id="probe-4", probe=True,
                                           transport=transport))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertIn("requires the terminal", out)
        self.assertEqual(transport.calls, 2)
        # probe-3 now allowed: originals present, statuses pinned, chain intact
        self.assertEqual(R.run(make_cfg(fx, run_id="probe-3", probe=True,
                                        transport=transport)), R.EXIT_OK)
        self.assertEqual(transport.calls, 3)
        self.assertEqual(R.run(make_cfg(fx, run_id="probe-4", probe=True,
                                        transport=transport)), R.EXIT_OK)
        self.assertEqual(transport.calls, 4)
        # every slot exists: any further probe refused before any call
        code, out = run_capturing(make_cfg(fx, run_id="probe-1", probe=True,
                                           transport=transport))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(transport.calls, 4)
        # unregistered slot ids are refused outright
        code, out = run_capturing(make_cfg(fx, run_id="probe-5", probe=True,
                                           transport=transport))
        self.assertEqual(code, R.EXIT_USAGE)
        self.assertEqual(transport.calls, 4)
        # ledger counts all four slots and every cost
        sched = json.loads((self.root / "frozen" / "schedule.json").read_text())
        prior = R.prior_run_state(self.root, sched)
        self.assertEqual(prior["probe_dispatched"], 4)
        self.assertEqual(sorted(prior["probe_slots"]), sorted(R.PROBE_SLOTS))
        # probe-2 failed with a $0.001 body; the three successful bodies bill
        # $0.002 each - every cost, success or failure, is counted
        self.assertAlmostEqual(prior["used_usd"], 3 * 0.002 + 0.001, places=9)
        self.assertEqual(prior["unknown"], [])
        self.assertEqual(prior["unreconciled"], [])

    def test_probe_unknown_cost_is_liability_and_blocks_scoring(self):
        fx = self.fx(probes="none")

        def no_usage(payload):
            return 200, json.dumps({
                "model": payload["model"], "provider": "fixture-provider",
                "choices": [{"finish_reason": "stop",
                             "message": {"role": "assistant",
                                         "content": '{"probe": "ok"}'}}]})

        transport = CountingTransport(no_usage)
        code, out = run_capturing(
            make_cfg(fx, run_id="probe-1", probe=True, transport=transport))
        self.assertEqual(code, R.EXIT_STOPPED, out)
        self.assertEqual(transport.calls, 1)
        result = json.loads((self.root / "probes" / "probe-1"
                             / "probe-result.json").read_text())
        self.assertEqual(result["status"], "stopped")
        self.assertIn("unreconciled_liability", result)
        self.assertFalse(result["billed_on_failure"]["parsed"])
        # both probes are counted in the same ledger, liability included
        sched = json.loads((self.root / "frozen" / "schedule.json").read_text())
        prior = R.prior_run_state(self.root, sched)
        self.assertEqual(prior["probe_dispatched"], 1)
        self.assertEqual([u["run"] for u in prior["unreconciled"]], ["probe-1"])
        # scoring refused before any call (receipt now claims the observation,
        # so the ledger - not the live gate - is what must refuse)
        write_receipt(self.root, live_status="observed_in_bounded_probe")
        s1 = CountingTransport(ok_body)
        code, out = run_capturing(make_cfg(fx, transport=s1))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(s1.calls, 0)
        self.assertIn("unreconciled liability", out)
        # a further probe is refused too
        s2 = CountingTransport(probe_ok_body)
        code, _ = run_capturing(make_cfg(fx, run_id="probe-2", probe=True,
                                         transport=s2))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(s2.calls, 0)

    def test_probe_budget_is_the_shared_usd_ledger(self):
        fx = self.fx(probes="none")
        expensive = {"prompt_tokens": 20, "completion_tokens": 5,
                     "total_tokens": 25, "cost": 10.0}
        transport = CountingTransport(
            lambda p: probe_ok_body(p, usage=expensive))
        self.assertEqual(R.run(make_cfg(fx, run_id="probe-1", probe=True,
                                        transport=transport)), R.EXIT_OK)
        self.assertEqual(transport.calls, 1)
        # second probe: prior $10 + worst case > $10 -> refused, no call
        code, out = run_capturing(make_cfg(fx, run_id="probe-2", probe=True,
                                           transport=transport))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertIn("budget already consumed", out)
        self.assertEqual(transport.calls, 1)

    def test_probe_must_precede_scoring_dispatch(self):
        fx = self.fx(probes="complete")
        self.assertEqual(R.run(make_cfg(fx, transport=CountingTransport(ok_body))),
                         R.EXIT_OK)               # scoring attempted first
        prior = R.prior_run_state(
            self.root, json.loads((self.root / "frozen" / "schedule.json")
                                  .read_text()))
        reason = R.probe_dispatch_gate(prior, "probe-1", self.root)
        self.assertIn("must precede", reason)     # defensive gate unit-checked
        # integration: any probe attempt after scoring is refused before a call
        transport = CountingTransport(probe_ok_body)
        code, out = run_capturing(make_cfg(fx, run_id="probe-1", probe=True,
                                           transport=transport))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(transport.calls, 0)


class ScoringProbeGates(FixtureCase):
    def test_no_score_dispatch_before_all_four_probes_and_reviews(self):
        cases = {
            "none": ("none", "all four probe slots"),
            "one": ("one", "all four probe slots"),
            "originals": ("originals", "all four probe slots"),
            "unreviewed": ("unreviewed", "independent review"),
            "followup-failed": ("followup-failed", "not a successful probe"),
        }
        for name, (spec, needle) in cases.items():
            with self.subTest(name):
                root = Path(tempfile.mkdtemp(prefix="cf-probegate-"))
                self.addCleanup(shutil.rmtree, root, True)
                fx = write_fixture(root, probes=spec)
                write_receipt(root, live_status="observed_in_bounded_probe")
                transport = CountingTransport(ok_body)
                code, out = run_capturing(make_cfg(fx, transport=transport))
                self.assertEqual(code, R.EXIT_GATE, out)
                self.assertEqual(transport.calls, 0, name)
                self.assertIn(needle, out, name)
                self.assertFalse((root / "runs").exists(), name)

    def test_original_failed_slot_never_grants_success(self):
        # only the two ORIGINALS exist, complete, reviewed and disclosed:
        # scoring must still refuse - the failed original slot (probe-2,
        # stopped) never substitutes for the required follow-up successes and
        # its recorded failure is never treated as a success.
        fx = self.fx(probes="originals")
        write_receipt(self.root, live_status="observed_in_bounded_probe")
        transport = CountingTransport(ok_body)
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertEqual(transport.calls, 0)
        self.assertIn("all four probe slots", out)
        # and the truthful failure record itself passes the original gate:
        sched = json.loads((self.root / "frozen" / "schedule.json").read_text())
        prior = R.prior_run_state(self.root, sched)
        bindings = R.current_bindings(self.root, self.root / "data"
                                      / "countries.json")
        self.assertIsNone(R.original_probe_evidence_gate(self.root, bindings))
        self.assertEqual(prior["probe_dispatched"], 2)

    def test_falsified_original_status_refused_everywhere(self):
        # flipping the archived probe-2 failure to "completed" must refuse
        # BOTH any follow-up dispatch and scoring (truthful disclosure)
        # part A: originals only, unsigned observation -> dispatch refused
        fx = self.fx(probes="originals")
        target = self.root / "probes" / "probe-2" / "probe-result.json"
        doc = json.loads(target.read_text())
        doc["status"] = "completed"
        target.write_text(json.dumps(doc), encoding="utf-8")
        # unobserved receipt: only the ORIGINAL-GATE truth check can fire
        write_receipt(self.root, live_status="unobserved")
        t1 = CountingTransport(probe_ok_body)
        code, out = run_capturing(make_cfg(fx, run_id="probe-3", probe=True,
                                           transport=t1))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertEqual(t1.calls, 0)
        self.assertIn("never re-labelled", out)
        # part B: all four slots present -> scoring refuses on the same truth
        # check before any receipt observation is even consulted
        root = Path(tempfile.mkdtemp(prefix="cf-falsify-"))
        self.addCleanup(shutil.rmtree, root, True)
        fx2 = write_fixture(root, probes="complete")
        target = root / "probes" / "probe-2" / "probe-result.json"
        doc = json.loads(target.read_text())
        doc["status"] = "completed"
        target.write_text(json.dumps(doc), encoding="utf-8")
        write_receipt(root, live_status="observed_in_bounded_probe")
        t2 = CountingTransport(ok_body)
        code, out = run_capturing(make_cfg(fx2, transport=t2))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertEqual(t2.calls, 0)
        self.assertIn("never re-labelled", out)

    def test_original_failure_review_must_confirm_not_attest_success(self):
        # a reviewed_ok success attestation on the FAILED original slot is
        # rejected; reviewed_failure is the only accepted status there
        fx = self.fx(probes="complete")
        target = self.root / "probes" / "probe-2" / "review.json"
        doc = json.loads(target.read_text())
        doc["status"] = R.REVIEW_OK_STATUS
        target.write_text(json.dumps(doc), encoding="utf-8")
        write_receipt(self.root, live_status="observed_in_bounded_probe")
        transport = CountingTransport(ok_body)
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertEqual(transport.calls, 0)
        self.assertIn("success attestation", out)

    def test_only_both_reviewed_followups_enable_scoring(self):
        # staged progression: originals -> +follow-ups -> +reviews -> enabled
        fx = self.fx(probes="originals")
        write_receipt(self.root, live_status="observed_in_bounded_probe")
        transport = CountingTransport(ok_body)
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertIn("all four probe slots", out)
        self.assertEqual(transport.calls, 0)
        # follow-ups exist but nobody reviewed them yet
        write_probe_fixture(self.root, "unreviewed")
        write_receipt(self.root, live_status="observed_in_bounded_probe")
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertIn("independent review", out)
        self.assertEqual(transport.calls, 0)
        # one follow-up fails -> phase ends, still no scoring
        (self.root / "probes" / "probe-4" / "probe-result.json").write_text(
            json.dumps({**json.loads((self.root / "probes" / "probe-4"
                                      / "probe-result.json").read_text()),
                        "status": "stopped", "stop_reason": "fixture failure"}),
            encoding="utf-8")
        write_receipt(self.root, live_status="observed_in_bounded_probe")
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertIn("not a successful probe", out)
        self.assertEqual(transport.calls, 0)
        # fully restored state (both follow-ups completed + all reviews)
        write_probe_fixture(self.root, "complete")
        write_receipt(self.root, live_status="observed_in_bounded_probe")
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_OK, out)
        self.assertEqual(transport.calls, 40)

    def test_probe_evidence_tampering_invalidates_receipt(self):
        fx = self.fx(probes="complete")
        target = self.root / "probes" / "probe-1" / "probe-result.json"
        target.write_text(target.read_text() + " ", encoding="utf-8")
        transport = CountingTransport(ok_body)
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(transport.calls, 0)
        self.assertIn("hash verification", out)

    def test_free_text_observation_record_rejected(self):
        fx = self.fx(probes="complete")
        rec = json.loads(fx["receipt"].read_text())
        rec["provider_semantics"]["live_behavior"]["record"] = \
            "probes look fine (free text)"
        fx["receipt"].write_text(json.dumps(rec), encoding="utf-8")
        transport = CountingTransport(ok_body)
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(transport.calls, 0)
        self.assertIn("free-text", out)

    def test_incomplete_probe_dispatch_blocks_everything(self):
        fx = self.fx(probes="none")
        d = self.root / "probes" / "probe-1"
        d.mkdir(parents=True)
        (d / "dispatch.json").write_text('{"slot": "probe-1"}',
                                          encoding="utf-8")   # crash-incomplete
        # further probe refused on the unknown state (receipt: live unobserved)
        code, out = run_capturing(
            make_cfg(fx, run_id="probe-2", probe=True,
                     transport=CountingTransport(probe_ok_body)))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertIn("prior run state unknown", out)
        # scoring (receipt now claims the observation) still refuses on it
        write_receipt(self.root, live_status="observed_in_bounded_probe")
        transport = CountingTransport(ok_body)
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(transport.calls, 0)
        self.assertIn("prior run state unknown", out)
        self.assertTrue(d.is_dir())               # evidence never deleted


class PreflightBinding(FixtureCase):
    def test_preflight_procedure_and_signoff_content_bound(self):
        fx = self.fx()
        for name in ("preflight.md", "preflight-signoff.md"):
            with self.subTest(name):
                target = self.root / name
                original = target.read_text(encoding="utf-8")
                target.write_text(original + "tampered\n", encoding="utf-8")
                transport = CountingTransport(ok_body)
                code, out = run_capturing(make_cfg(fx, transport=transport))
                self.assertEqual(code, R.EXIT_GATE, name)
                self.assertEqual(transport.calls, 0, name)
                self.assertIn("binding hash mismatch", out)
                target.write_text(original, encoding="utf-8")   # restore

    def test_signoff_artifact_must_exist(self):
        fx = self.fx()
        (self.root / "preflight-signoff.md").unlink()
        transport = CountingTransport(ok_body)
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(transport.calls, 0)
        self.assertIn("missing input bound by preflight", out)

    def test_receipt_must_name_the_bound_procedure_and_signoff(self):
        for field, bad_value in (("document", "README.md"),
                                 ("signoff_artifact", "preflight.md"),
                                 ("document", " "),
                                 ("signoff_artifact", None)):
            with self.subTest(f"{field}={bad_value!r}"):
                root = Path(tempfile.mkdtemp(prefix="cf-signoff-"))
                self.addCleanup(shutil.rmtree, root, True)
                fx = write_fixture(root)
                rec = json.loads(fx["receipt"].read_text())
                rec["preflight"][field] = bad_value
                fx["receipt"].write_text(json.dumps(rec), encoding="utf-8")
                transport = CountingTransport(ok_body)
                code, out = run_capturing(make_cfg(fx, transport=transport))
                self.assertEqual(code, R.EXIT_GATE, repr(bad_value))
                self.assertEqual(transport.calls, 0)


class CombinedCeilings(FixtureCase):
    def test_total_dispatch_cap_is_exactly_44(self):
        # 2 original probes + 2 adaptive follow-ups + 40 scoring = 44, strict
        self.assertEqual(R.TOTAL_DISPATCH_CEILING, 44)
        self.assertEqual(R.PROBE_CEILING, 4)
        self.assertEqual(len(R.ORIGINAL_PROBE_SLOTS), 2)
        self.assertEqual(len(R.FOLLOWUP_PROBE_SLOTS), 2)
        prior40 = {"attempted": {i: "r" for i in range(1, 41)},
                   "probe_dispatched": 4}
        prior_clean = {"attempted": {}, "probe_dispatched": 4}
        self.assertIsNone(R.total_dispatch_violation(prior_clean, 40))  # 44 ok
        self.assertIn("44", R.total_dispatch_violation(prior_clean, 41) or "")
        self.assertIn("44", R.total_dispatch_violation(prior40, 1) or "")
        self.assertIsNone(R.total_dispatch_violation({"attempted": {},
                                                      "probe_dispatched": 0}, 40))
        # a real fixture with all four probes + the frozen 40-cell plan = 44
        fx = self.fx(probes="complete")
        sched = json.loads((self.root / "frozen" / "schedule.json").read_text())
        prior = R.prior_run_state(self.root, sched)
        self.assertEqual(prior["probe_dispatched"], 4)
        self.assertIsNone(R.total_dispatch_violation(prior, R.ATTEMPT_CEILING))
        self.assertEqual(len(prior["attempted"]) + prior["probe_dispatched"]
                         + 40, 44)

    def test_shared_usd_ledger_blocks_scoring_on_probe_charges(self):
        fx = self.fx(probes="complete", probe_cost=9.5)
        transport = CountingTransport(ok_body)
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_GATE)
        self.assertEqual(transport.calls, 0)
        self.assertIn("budget already consumed", out)

    def test_probe_token_allowance_enforced(self):
        # declared output allowance = originals 64+64 + follow-ups 2000+2000
        self.assertEqual(R.PROBE_OUTPUT_ALLOWANCE_TOKENS, 64 * 2 + 2000 * 2)
        self.assertEqual(R.PROBE_OUTPUT_ALLOWANCE_TOKENS, 4128)
        prior = {"used_usd": 0.0, "used_input": 0, "used_output": 0,
                 "scoring_used_input": 0, "scoring_used_output": 0,
                 "probe_used_input": 0,
                 "probe_used_output": R.PROBE_OUTPUT_ALLOWANCE_TOKENS + 1}
        fx = self.fx(probes="complete")
        manifest = json.loads((self.root / "frozen" / "manifest.json").read_text())
        caps = R.declared_limits(manifest)
        plan = {"caps": caps, "aggregate_input": 100, "aggregate_output": 0}
        reason = R.prior_budget_violation(prior, plan, 0.0)
        self.assertIn("probe output allowance", reason)
        # a follow-up dispatch itself reserves 2000 against the same allowance
        probe_plan = {"caps": caps, "aggregate_input": 1,
                      "aggregate_output": R.FOLLOWUP_PROBE_MAX_OUTPUT_TOKENS,
                      "is_probe": True}
        headroom = (R.PROBE_OUTPUT_ALLOWANCE_TOKENS
                    - R.FOLLOWUP_PROBE_MAX_OUTPUT_TOKENS)
        self.assertIsNone(R.prior_budget_violation(
            {**prior, "probe_used_output": headroom}, probe_plan, 0.0))
        self.assertIn("probe output allowance", R.prior_budget_violation(
            {**prior, "probe_used_output": headroom + 1},
            probe_plan, 0.0) or "")

    def test_probe_flag_without_execute_stays_disabled(self):
        # the real archived probes/ tree exists (original evidence): the
        # disabled default must leave it byte-for-byte untouched and create
        # no lock, no runs/ and no new probe slot
        archived = (tree_fingerprint(HERE / "probes")
                    if (HERE / "probes").exists() else None)
        slots_before = (sorted(p.name for p in (HERE / "probes").iterdir())
                        if (HERE / "probes").exists() else [])
        self.assertEqual(R.main(["--probe"]), R.EXIT_USAGE)
        self.assertFalse((HERE / R.LOCK_NAME).exists())
        self.assertFalse((HERE / "runs").exists())
        if archived is not None:
            self.assertEqual(tree_fingerprint(HERE / "probes"), archived)
            self.assertEqual(sorted(p.name for p in (HERE / "probes").iterdir()),
                             slots_before)   # no probe-3/probe-4 materialized


class SharedBudgetMidRun(FixtureCase):
    """P1 regression: prior probe/experiment spend must be counted in EVERY
    in-run USD comparison (pre-dispatch reservation AND postpaid), while each
    result.json used_usd stays run-local so later ledger scans sum exactly once."""

    def _scoring_transport(self, cost):
        return CountingTransport(
            lambda p: ok_body(p, usage={"prompt_tokens": 100,
                                        "completion_tokens": 50,
                                        "total_tokens": 150, "cost": cost}))

    def _ledger(self):
        sched = json.loads((self.root / "frozen" / "schedule.json").read_text())
        return R.prior_run_state(self.root, sched)

    def test_unexpectedly_costly_first_call_shares_ledger_and_stops(self):
        # four reviewed probes cost $2.00 combined (4 x $0.50); first scoring
        # response bills $8.10
        fx = self.fx(probes="complete", probe_cost=0.5)
        transport = self._scoring_transport(8.10)
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_STOPPED, out)
        self.assertEqual(transport.calls, 1)      # exactly one scoring request
        self.assertIn("USD ceiling", out)        # shared postpaid stop
        self.assertIn("shared $10.100000", out)
        self.assertIn("run-local $8.100000", out)
        self.assertIn("prior $2.000000", out)
        result = json.loads((self.root / "runs" / "fixture-run"
                             / "result.json").read_text())
        self.assertEqual(result["status"], "stopped")
        # result totals stay RUN-LOCAL (no double counting on later scans)
        self.assertAlmostEqual(result["used_usd"], 8.10, places=6)
        self.assertAlmostEqual(result["prior_run_state"]["used_usd"], 2.0, places=6)
        # shared experiment totals are correct in the same ledger
        ledger = self._ledger()
        self.assertEqual(len(ledger["attempted"]), 1)
        self.assertEqual(ledger["probe_dispatched"], 4)
        self.assertAlmostEqual(ledger["used_usd"], 10.10, places=6)  # 2.00 + 8.10

    def test_pre_dispatch_reservation_includes_prior_spend(self):
        # $7.90 response alone is under the ceiling; shared $9.90 + remaining
        # reservation must refuse BEFORE dispatching a second scoring call
        fx = self.fx(probes="complete", probe_cost=0.5)
        transport = self._scoring_transport(7.90)
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_STOPPED, out)
        self.assertEqual(transport.calls, 1)      # stopped before the next call
        self.assertIn("shared $9.900000", out)
        self.assertIn("prior $2.000000", out)
        self.assertIn("remaining worst-case reservation", out)
        result = json.loads((self.root / "runs" / "fixture-run"
                             / "result.json").read_text())
        self.assertAlmostEqual(result["used_usd"], 7.90, places=6)   # run-local
        self.assertAlmostEqual(self._ledger()["used_usd"], 9.90, places=6)

    def test_control_non_exceeded_shared_spend_completes(self):
        # $2.00 prior (4 probes x $0.50) + $0.05 x 40 = $4.00 shared -> completes
        fx = self.fx(probes="complete", probe_cost=0.5)
        transport = self._scoring_transport(0.05)
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_OK, out)
        self.assertEqual(transport.calls, 40)
        result = json.loads((self.root / "runs" / "fixture-run"
                             / "result.json").read_text())
        self.assertEqual(result["status"], "completed")
        self.assertAlmostEqual(result["used_usd"], 2.0, places=6)    # run-local
        self.assertAlmostEqual(result["prior_run_state"]["used_usd"], 2.0,
                               places=6)
        ledger = self._ledger()
        self.assertAlmostEqual(ledger["used_usd"], 4.0, places=6)    # 2.0 + 2.0
        self.assertEqual(len(ledger["attempted"]), 40)


class AdaptiveFollowupAmendment(FixtureCase):
    """probe-followup-amendment.md: adaptive-after-failure follow-up controls -
    matched settings, evidence-chain binding, shared-cost stop, receipt guards
    and HTTP-status honesty."""

    def test_followup_dispatch_binds_amendment_and_scoring_output_setting(self):
        fx = self.fx(probes="originals")
        transport = CountingTransport(probe_ok_body)
        code, out = run_capturing(make_cfg(fx, run_id="probe-3", probe=True,
                                           transport=transport))
        self.assertEqual(code, R.EXIT_OK, out)
        self.assertEqual(transport.calls, 1)          # one dispatch, no retry
        payload = transport.payloads[0]
        # identical non-country messages; ONLY max output raised to the
        # actual scoring setting (2000)
        self.assertEqual(set(payload), set(R.REQUEST_KEYS))
        self.assertEqual(payload["messages"][0]["content"], R.PROBE_SYSTEM)
        self.assertEqual(payload["messages"][1]["content"], R.PROBE_USER)
        self.assertEqual(payload["max_tokens"],
                         R.FOLLOWUP_PROBE_MAX_OUTPUT_TOKENS)
        self.assertEqual(payload["max_tokens"],
                         R.REQUESTED_SETTINGS["max_output_tokens"])
        self.assertEqual(payload["temperature"], 0.0)
        self.assertEqual(payload["top_p"], 1.0)
        blob = json.dumps(payload)
        for banned in ("United States", "USA", "United Kingdom", "Nepal",
                       "Vatican", "DOSSIER", "NEUTRAL-7", "score", "dossier"):
            self.assertNotIn(banned, blob, banned)
        d = self.root / "probes" / "probe-3"
        dispatch = json.loads((d / "dispatch.json").read_text())
        self.assertEqual(dispatch["attempt_phase"], "adaptive_followup")
        self.assertEqual(dispatch["probe_followup_amendment_sha256"],
                         sha((HERE / "probe-followup-amendment.md").read_bytes()))
        self.assertEqual(dispatch["probe_amendment_sha256"],
                         sha((HERE / "probe-amendment.md").read_bytes()))
        self.assertEqual(dispatch["adapted_after"]["original_failure_slot"],
                         "probe-2")                   # provenance of the adaptation
        self.assertEqual(dispatch["reserved_output_tokens"], 2000)
        self.assertIs(dispatch["retry"], False)
        result = json.loads((d / "probe-result.json").read_text())
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["requested_settings"], R.FOLLOWUP_PROBE_SETTINGS)
        self.assertFalse((self.root / "runs").exists())
        self.assertFalse((self.root / R.LOCK_NAME).exists())

    def test_followup_differs_from_original_only_in_max_output(self):
        self.assertEqual(set(R.PROBE_SETTINGS), set(R.FOLLOWUP_PROBE_SETTINGS))
        for key in ("temperature", "top_p"):
            self.assertEqual(R.PROBE_SETTINGS[key],
                             R.FOLLOWUP_PROBE_SETTINGS[key], key)
        self.assertEqual(R.PROBE_SETTINGS["max_output_tokens"], 64)
        self.assertEqual(R.FOLLOWUP_PROBE_SETTINGS["max_output_tokens"], 2000)
        self.assertEqual(R.FOLLOWUP_PROBE_MAX_OUTPUT_TOKENS,
                         R.REQUESTED_SETTINGS["max_output_tokens"])
        self.assertEqual(R.FOLLOWUP_PROBE_MAX_OUTPUT_TOKENS,
                         R.RESERVED_OUTPUT_TOKENS_PER_CALL)
        self.assertEqual(sum(R.PROBE_SLOT_MAX_OUTPUT[s] for s in R.PROBE_SLOTS),
                         R.PROBE_OUTPUT_ALLOWANCE_TOKENS)
        self.assertEqual(R.PROBE_INPUT_ALLOWANCE_UNITS,
                         4 * (len(R.PROBE_SYSTEM.encode("utf-8"))
                              + len(R.PROBE_USER.encode("utf-8"))
                              + R.FIXED_OVERHEAD_TOKENS_PER_CALL))
        for slot in R.ORIGINAL_PROBE_SLOTS:
            self.assertEqual(R.PROBE_SLOT_SETTINGS[slot], R.PROBE_SETTINGS)
        for slot in R.FOLLOWUP_PROBE_SLOTS:
            self.assertEqual(R.PROBE_SLOT_SETTINGS[slot],
                             R.FOLLOWUP_PROBE_SETTINGS)

    def test_followup_blocked_by_missing_unknown_or_unreconciled_records(self):
        # missing original record: probe-2 was never dispatched
        fx = self.fx(probes="one")
        t = CountingTransport(probe_ok_body)
        code, out = run_capturing(make_cfg(fx, run_id="probe-3", probe=True,
                                           transport=t))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertIn("original probe evidence missing", out)
        self.assertEqual(t.calls, 0)
        # unknown prior state: a crash-incomplete original (directory, no record)
        (self.root / "probes" / "probe-2").mkdir(exist_ok=True)
        code, out = run_capturing(make_cfg(fx, run_id="probe-3", probe=True,
                                           transport=t))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertIn("prior run state unknown", out)
        self.assertEqual(t.calls, 0)
        (self.root / "probes" / "probe-2").rmdir()
        # unreconciled liability: an original probe with an unknown charge
        root = Path(tempfile.mkdtemp(prefix="cf-followup-liab-"))
        self.addCleanup(shutil.rmtree, root, True)
        fx2 = write_fixture(root, probes="none")

        def no_usage(payload):
            return 200, json.dumps({
                "model": payload["model"], "provider": "fixture-provider",
                "choices": [{"finish_reason": "stop",
                             "message": {"role": "assistant",
                                         "content": '{"probe": "ok"}'}}]})

        t1 = CountingTransport(no_usage)
        self.assertEqual(R.run(make_cfg(fx2, run_id="probe-1", probe=True,
                                        transport=t1)), R.EXIT_STOPPED)
        t2 = CountingTransport(probe_ok_body)
        code, out = run_capturing(make_cfg(fx2, run_id="probe-3", probe=True,
                                           transport=t2))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertIn("unreconciled liability", out)
        self.assertEqual(t2.calls, 0)

    def test_shared_cost_stops_followup_after_originals_spent(self):
        # the two originals already consumed the whole $10 local ceiling:
        # the shared ledger must stop the follow-up before any dispatch
        fx = self.fx(probes="originals", probe_cost=5.0)   # 2 x $5.00 = $10.00
        sched = json.loads((self.root / "frozen" / "schedule.json").read_text())
        prior = R.prior_run_state(self.root, sched)
        self.assertAlmostEqual(prior["used_usd"], 10.0, places=6)
        t = CountingTransport(probe_ok_body)
        code, out = run_capturing(make_cfg(fx, run_id="probe-3", probe=True,
                                           transport=t))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertIn("budget already consumed", out)
        self.assertEqual(t.calls, 0)

    def test_failed_probe3_ends_phase_before_price_credential_transport(self):
        # reviewer P1 regression: a known-charge probe-3 failure ends the phase;
        # the probe-4 invocation must refuse BEFORE price fetch, credential read
        # and transport, and scoring must stay blocked too.
        fx = self.fx(probes="originals")

        def known_charge_failure(payload):
            return 200, json.dumps({
                "model": payload["model"], "provider": "fixture-provider",
                "choices": [{"finish_reason": "length",
                             "message": {"role": "assistant", "content": None}}],
                "usage": {"prompt_tokens": 53, "completion_tokens": 60,
                          "total_tokens": 113, "cost": 0.003}})

        transport = CountingTransport(known_charge_failure)
        cfg3 = make_cfg(fx, run_id="probe-3", probe=True, transport=transport)
        prices3, secrets3 = [], []
        cfg3["price_fetch"] = lambda: (prices3.append(1), dict(PRICES))[1]
        cfg3["secret_loader"] = lambda: (secrets3.append(1), SECRET)[1]
        self.assertEqual(R.run(cfg3), R.EXIT_STOPPED)
        self.assertEqual(transport.calls, 1)
        self.assertEqual(prices3, [1])           # probe-3 itself fetched prices
        result3 = json.loads((self.root / "probes" / "probe-3"
                              / "probe-result.json").read_text())
        self.assertEqual(result3["status"], "stopped")
        self.assertEqual(result3["used_usd"], 0.003)   # known charge, not unknown
        self.assertNotIn("unreconciled_liability", result3)
        # probe-4: refused before price fetch, credential read and transport
        cfg4 = make_cfg(fx, run_id="probe-4", probe=True, transport=transport)
        prices4, secrets4 = [], []
        cfg4["price_fetch"] = lambda: (prices4.append(1), dict(PRICES))[1]
        cfg4["secret_loader"] = lambda: (secrets4.append(1), SECRET)[1]
        code, out = run_capturing(cfg4)
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertIn("ends the phase", out)
        self.assertEqual(prices4, [])            # zero price-fetch calls
        self.assertEqual(secrets4, [])           # zero credential reads
        self.assertEqual(transport.calls, 1)     # zero probe-4 transport calls
        self.assertFalse((self.root / "probes" / "probe-4").exists())
        # the known failure cost is still counted in the shared ledger
        sched = json.loads((self.root / "frozen" / "schedule.json").read_text())
        prior = R.prior_run_state(self.root, sched)
        self.assertEqual(prior["probe_dispatched"], 3)
        self.assertAlmostEqual(prior["used_usd"], 2 * 0.001 + 0.003, places=9)
        # no scoring after the failure either - also refused before price fetch
        write_receipt(self.root, live_status="observed_in_bounded_probe")
        t5 = CountingTransport(ok_body)
        cfg5 = make_cfg(fx, transport=t5)
        prices5, secrets5 = [], []
        cfg5["price_fetch"] = lambda: (prices5.append(1), dict(PRICES))[1]
        cfg5["secret_loader"] = lambda: (secrets5.append(1), SECRET)[1]
        code, out = run_capturing(cfg5)
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertIn("all four probe slots", out)
        self.assertEqual(t5.calls, 0)
        self.assertEqual(prices5, [])
        self.assertEqual(secrets5, [])

    def test_completed_probe3_allows_probe4_control(self):
        # control: a COMPLETED probe-3 permits exactly one probe-4 dispatch
        fx = self.fx(probes="originals")
        transport = CountingTransport(probe_ok_body)
        cfg3 = make_cfg(fx, run_id="probe-3", probe=True, transport=transport)
        prices3, secrets3 = [], []
        cfg3["price_fetch"] = lambda: (prices3.append(1), dict(PRICES))[1]
        cfg3["secret_loader"] = lambda: (secrets3.append(1), SECRET)[1]
        self.assertEqual(R.run(cfg3), R.EXIT_OK)
        self.assertEqual(prices3, [1])
        self.assertEqual(secrets3, [1])
        self.assertEqual(transport.calls, 1)
        cfg4 = make_cfg(fx, run_id="probe-4", probe=True, transport=transport)
        prices4, secrets4 = [], []
        cfg4["price_fetch"] = lambda: (prices4.append(1), dict(PRICES))[1]
        cfg4["secret_loader"] = lambda: (secrets4.append(1), SECRET)[1]
        code, out = run_capturing(cfg4)
        self.assertEqual(code, R.EXIT_OK, out)
        self.assertEqual(prices4, [1])           # allowed: probe-3 completed
        self.assertEqual(secrets4, [1])
        self.assertEqual(transport.calls, 2)
        result4 = json.loads((self.root / "probes" / "probe-4"
                              / "probe-result.json").read_text())
        self.assertEqual(result4["status"], "completed")

    def test_no_scoring_after_either_followup_failure(self):
        # either follow-up failing blocks scoring, with zero transport calls
        for spec, needle in (
                ("followup3-failed",
                 "adaptive follow-up probe-3 is not a successful probe"),
                ("followup-failed",
                 "adaptive follow-up probe-4 is not a successful probe")):
            with self.subTest(spec):
                root = Path(tempfile.mkdtemp(prefix="cf-stopphase-"))
                self.addCleanup(shutil.rmtree, root, True)
                fx = write_fixture(root, probes=spec)
                write_receipt(root, live_status="observed_in_bounded_probe")
                transport = CountingTransport(ok_body)
                code, out = run_capturing(make_cfg(fx, transport=transport))
                self.assertEqual(code, R.EXIT_GATE, out)
                self.assertEqual(transport.calls, 0, spec)
                self.assertIn(needle, out, spec)
                self.assertIn("any failure ends the phase", out, spec)
                self.assertFalse((root / "runs").exists(), spec)

    def test_original_receipt_chain_and_amendment_review_binding_required(self):
        fx = self.fx(probes="originals")
        # (a) the independent review of the amendment must exist and be bound
        review_path = self.root / R.PROBE_FOLLOWUP_REVIEW_REL
        review_bytes = review_path.read_bytes()
        review_path.unlink()
        t = CountingTransport(probe_ok_body)
        code, out = run_capturing(make_cfg(fx, run_id="probe-3", probe=True,
                                           transport=t))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertIn("missing input bound by preflight", out)
        self.assertEqual(t.calls, 0)
        review_path.write_bytes(review_bytes)
        # (b) tampering the ARCHIVAL receipt (even after re-signing the amended
        # receipt over the tampered bytes) breaks the original record chain
        archival = self.root / R.ARCHIVAL_RECEIPT_NAME
        arch_doc = json.loads(archival.read_text())   # still valid schema-v3 JSON
        arch_doc["archived_at"] = "2026-01-02T00:00:00+00:00"  # bytes changed
        archival.write_text(json.dumps(arch_doc, indent=1) + "\n",
                            encoding="utf-8")
        write_receipt(self.root)                     # re-sign -> only gate left
        t2 = CountingTransport(probe_ok_body)
        code, out = run_capturing(make_cfg(fx, run_id="probe-3", probe=True,
                                           transport=t2))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertIn("chain broken", out)
        self.assertEqual(t2.calls, 0)
        # (c) the archival receipt must exist at all
        archival.unlink()
        t3 = CountingTransport(probe_ok_body)
        code, out = run_capturing(make_cfg(fx, run_id="probe-3", probe=True,
                                           transport=t3))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertIn("archival original receipt", out)
        self.assertEqual(t3.calls, 0)

    def test_receipt_guards_name_version_and_failure_disclosure(self):
        fx = self.fx(probes="complete")
        # the archival receipt can never be passed as the execution receipt
        transport = CountingTransport(ok_body)
        code, out = run_capturing(make_cfg(
            fx, receipt=str(self.root / R.ARCHIVAL_RECEIPT_NAME),
            transport=transport))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertIn("archival immutable evidence", out)
        self.assertEqual(transport.calls, 0)
        # a schema-v3 receipt is refused as the amended execution receipt
        path = self.root / R.RECEIPT_NAME
        doc = json.loads(path.read_text())
        doc["receipt_version"] = 3
        path.write_text(json.dumps(doc), encoding="utf-8")
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertIn("receipt_version must be 4", out)
        self.assertEqual(transport.calls, 0)
        # observed record MUST disclose the original failure structure
        write_receipt(self.root, live_status="observed_in_bounded_probe")
        doc = json.loads(path.read_text())
        del doc["provider_semantics"]["live_behavior"]["record"][
            "original_failure"]
        path.write_text(json.dumps(doc), encoding="utf-8")
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertIn("original_failure", out)
        self.assertEqual(transport.calls, 0)
        # a disclosure that contradicts the archived bytes is refused too
        write_receipt(self.root, live_status="observed_in_bounded_probe")
        doc = json.loads(path.read_text())
        doc["provider_semantics"]["live_behavior"]["record"][
            "original_failure"]["status"] = "completed"
        path.write_text(json.dumps(doc), encoding="utf-8")
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertIn("original_failure does not match", out)
        self.assertEqual(transport.calls, 0)

    def test_original_evidence_hash_binding_for_scoring(self):
        fx = self.fx(probes="complete")
        target = self.root / "probes" / "probe-1" / "dispatch.json"
        doc = json.loads(target.read_text())
        doc["preflight_receipt_sha256"] = "0" * 64
        target.write_text(json.dumps(doc), encoding="utf-8")
        transport = CountingTransport(ok_body)
        code, out = run_capturing(make_cfg(fx, transport=transport))
        self.assertEqual(code, R.EXIT_GATE, out)
        self.assertEqual(transport.calls, 0)
        self.assertIn("evidence hash binding failed", out)
        # the receipt's hash-bound probe-result is untouched; the chain check
        # fired first, before any observation could be accepted
        real = json.loads((self.root / "probes" / "probe-1"
                           / "probe-result.json").read_text())
        self.assertEqual(real["status"], "completed")

    def test_failed_probe_http_status_captured_only_if_received(self):
        # (i) a response arrives -> its HTTP status is recorded on the failure
        fx = self.fx(probes="none")

        def empty_content(payload):
            return 200, json.dumps({
                "model": payload["model"], "provider": "fixture-provider",
                "choices": [{"finish_reason": "length",
                             "message": {"role": "assistant", "content": None}}],
                "usage": {"prompt_tokens": 53, "completion_tokens": 60,
                          "total_tokens": 113, "cost": 0.001}})

        t = CountingTransport(empty_content)
        self.assertEqual(R.run(make_cfg(fx, run_id="probe-1", probe=True,
                                        transport=t)), R.EXIT_STOPPED)
        result = json.loads((self.root / "probes" / "probe-1"
                             / "probe-result.json").read_text())
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(result.get("http_status"), 200)
        # (ii) a transport-level failure has no status to record -> none is
        # invented
        root = Path(tempfile.mkdtemp(prefix="cf-http-"))
        self.addCleanup(shutil.rmtree, root, True)
        fx2 = write_fixture(root, probes="none")

        def dead(*a, **k):
            raise R.Refusal(R.EXIT_STOPPED,
                            "transport error (ConnectionResetError)")

        t2 = CountingTransport(dead)
        self.assertEqual(R.run(make_cfg(fx2, run_id="probe-1", probe=True,
                                        transport=t2)), R.EXIT_STOPPED)
        result2 = json.loads((root / "probes" / "probe-1"
                              / "probe-result.json").read_text())
        self.assertEqual(result2["status"], "stopped")
        self.assertNotIn("http_status", result2)      # never invented
        # (iii) the REAL archived originals: probe-2 never gains a status field
        # retrospectively, and their bytes chain to the archival receipt
        real2 = json.loads((HERE / "probes" / "probe-2"
                            / "probe-result.json").read_text())
        self.assertNotIn("http_status", real2)
        self.assertEqual(real2["status"], "stopped")  # failure stays reported
        self.assertEqual(real2["retry"], False)
        archival_sha = sha((HERE / R.ARCHIVAL_RECEIPT_NAME).read_bytes())
        for slot in ("probe-1", "probe-2"):
            disp = json.loads((HERE / "probes" / slot / "dispatch.json")
                              .read_text())
            res = json.loads((HERE / "probes" / slot / "probe-result.json")
                             .read_text())
            self.assertEqual(disp["preflight_receipt_sha256"], archival_sha, slot)
            self.assertEqual(res["preflight_receipt_sha256"], archival_sha, slot)
            self.assertEqual(res["retry"], False, slot)
        real1 = json.loads((HERE / "probes" / "probe-1"
                            / "probe-result.json").read_text())
        self.assertEqual(real1["status"], "completed")
        # known original charges: $0.00001551 + $0.00026475 = $0.00028026
        self.assertAlmostEqual(real1["used_usd"] + real2["used_usd"], 0.00028026,
                               places=11)


if __name__ == "__main__":
    unittest.main()