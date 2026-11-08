#!/usr/bin/env python3
"""Offline, mock-only tests for the country-feasibility-v2 stage-one runner.

No network, no credentials, no provider calls, no live dispatch. All fixture
writes stay inside this country-feasibility-v2 directory; the single permitted
write outside it is the shared transient ``.execution.lock`` in the closed v1
directory, which these tests create only as their own holder and always remove
(or leave untouched if a foreign lock is already present). Nothing here
creates a real preflight receipt, review artifact, commit or staged file.
"""
from __future__ import annotations

import contextlib
import hashlib
import inspect
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from decimal import Decimal
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE))
import runner  # noqa: E402

V1_ROOT = runner.V1_ROOT
TMPROOT = HERE / ".testtmp"
TMPROOT.mkdir(exist_ok=True)

# Pinned digests of the trees that must remain byte-identical (computed over
# sorted "relpath<TAB>sha256" lines of every file, joined with "\n" + trailing
# newline). v1 is CLOSED; rule-contrasts and data/ are out of scope for edits.
V1_TREE_FILES = 64
V1_TREE_DIGEST = "d33b3c23e1d822ab6ecb967d3af578a8c341332cb84f28870545c4c0e8fe06d1"
RC_TREE_FILES = 15
RC_TREE_DIGEST = "35932a71e4e1791abe29324b0baf291cdb17c4ceeb3e5452870a7992396c0949"
DATA_COUNTRIES_PIN = \
    "c4a2c8339b0d389a42d8b90ec48bafab209d511185ab10e19789d29de4baebce"

CONTRACT_OK = json.dumps({
    "status": "ok", "score": 0.5, "why": "grounds",
    "evidence_ids": ["E1"], "discovery": "d", "direct_harms": "h",
    "scope_triggers": "t", "uncertainty": "u"})
CONTRACT_ABSTAIN = json.dumps({
    "status": "insufficient_evidence", "score": None, "why": "empty dossier",
    "evidence_ids": "none", "discovery": "d", "direct_harms": "h",
    "scope_triggers": "t", "uncertainty": "u"})

DEFAULT_PRICES = {
    "deepseek/deepseek-v4.1-flash": {"prompt": Decimal("0.000000051"),
                                     "completion": Decimal("0.000000567")},
    "google/gemini-3.8-flash": {"prompt": Decimal("0.000000825"),
                                "completion": Decimal("0.000004125")}}

FORBIDDEN_EVIDENCE_KEYS = {"score", "band", "rank", "provenance", "anchor",
                           "subnational", "adm1"}


class NotCalled(AssertionError):
    """Raised if a loader/transport that must stay untouched is invoked."""


def not_called(name: str, log: list):
    def _f(*a, **k):
        log.append(name)
        raise NotCalled(f"{name} must not be called in this scenario")
    return _f


def tree_digest(root: Path):
    lines = []
    for dp, dns, fns in os.walk(root):
        dns.sort()
        for fn in sorted(fns):
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, root)
            h = hashlib.sha256(Path(p).read_bytes()).hexdigest()
            lines.append(f"{rel}\t{h}")
    lines.sort()
    blob = ("\n".join(lines) + "\n").encode()
    return hashlib.sha256(blob).hexdigest(), len(lines)


def repo_snapshot() -> dict:
    """(size, mtime_ns) of every repo file outside this v2 directory."""
    v2_rel = os.path.relpath(HERE, REPO)
    out = {}
    for dp, dns, fns in os.walk(REPO):
        rel_dp = os.path.relpath(dp, REPO)
        if rel_dp == ".git" or rel_dp.startswith(".git" + os.sep):
            dns[:] = []
            continue
        if rel_dp == v2_rel or rel_dp.startswith(v2_rel + os.sep):
            dns[:] = []
            continue
        dns[:] = [d for d in dns if d != ".git"]
        for fn in fns:
            p = os.path.join(dp, fn)
            st = os.stat(p)
            out[os.path.relpath(p, REPO)] = (st.st_size, st.st_mtime_ns)
    return out


def default_usage(**over):
    usage = {
        "prompt_tokens": 40000, "completion_tokens": 100,
        "total_tokens": 40100, "cost": 0.0005, "is_byok": False,
        "prompt_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
        "completion_tokens_details": {"reasoning_tokens": 80},
    }
    usage.update(over)
    return usage


def provider_body(model: str, content=CONTRACT_OK, provider=None,
                  finish="stop", usage=None, id_="gen-fixture-0001"):
    if provider is None:
        provider = runner.EXPECTED_PROVIDERS[model][0]
    doc = {"id": id_, "model": model, "provider": provider,
           "choices": [{"index": 0, "finish_reason": finish,
                        "message": {"role": "assistant",
                                    "content": content}}],
           "usage": default_usage() if usage is None else usage}
    return json.dumps(doc)


# The exact empty-dossier message: a default "good" response must abstain
# when (and only when) the request carries this empty-evidence message, so
# generic happy-path scripts satisfy the context-aware sentinel rule.
EMPTY_MESSAGE = next(
    m["message"] for m in json.loads(
        (HERE / "frozen" / "user_messages.json")
        .read_text(encoding="utf-8"))["messages"]
    if m["sentinel"] == "empty")


def default_content_for(payload) -> str:
    user = payload["messages"][1]["content"]
    return CONTRACT_ABSTAIN if user == EMPTY_MESSAGE else CONTRACT_OK


class Transport:
    """Scripted transport: each entry is None (a good response derived from
    the actual request payload - abstaining for empty-dossier requests,
    scored otherwise), a (status, body) tuple, a callable
    payload -> body, or an Exception instance to raise (e.g. a socket-timeout
    transport error). Raises if invoked more often than scripted, which also
    proves there is no retry. Records every observed timeout argument."""

    def __init__(self, modes=None):
        self.modes = list(modes) if modes else []
        self.calls = []
        self.urls = []
        self.headers = []
        self.timeouts = []

    def __call__(self, url, payload, headers, timeout):
        self.urls.append(url)
        self.headers.append(headers)
        self.calls.append(payload)
        self.timeouts.append(timeout)
        if not self.modes:
            raise NotCalled("transport invoked more often than scripted - "
                            "the runner must never retry")
        mode = self.modes.pop(0)
        if isinstance(mode, Exception):
            raise mode
        if mode is None:
            return 200, provider_body(payload["model"],
                                      content=default_content_for(payload))
        if isinstance(mode, tuple):
            return mode
        return 200, mode(payload)

    @property
    def left(self):
        return len(self.modes)


def attempt_record_shape(row) -> dict:
    """The identity block _dispatch_stage actually writes into attempt files
    (never a raw schedule row: attempt records carry ``requested_model``, not
    ``model``)."""
    return {"call": row["call"], "block": row["block"],
            "draw": row["draw"], "case": row["case"],
            "sentinel": row["sentinel"], "variant": row["variant"],
            "label": row["label"], "requested_model": row["model"],
            "requested_settings": runner.REQUESTED_SETTINGS,
            "reserved_input_units": 43437,
            "retry": False}


def invoke(tmp: Path, run_id: str, modes, prices=None, secret_loader=None):
    """One offline invocation: fresh scripted transport, quiet run()."""
    transport = Transport(modes)
    cfg = fixture_cfg(tmp, transport, run_id=run_id, prices=prices,
                      secret_loader=secret_loader)
    rc, out = quiet(runner.run, cfg)
    return rc, out, transport


def write_fixture_review(run_dir: Path, call: int, verdict="PASS",
                         mutate=None, omit=()):
    """TEST-ONLY synthetic review standing in for the independent human/model
    reviewer (clearly marked FIXTURE; the runner never writes this path)."""
    att = json.loads((run_dir / "attempts" / f"call-{call:03d}.json")
                     .read_text(encoding="utf-8"))
    side = runner.sidecar_path(run_dir, call)
    doc = {
        "review_version": 1,
        "verdict": verdict,
        "response_sha256": hashlib.sha256(
            att["raw_response"].encode("utf-8")).hexdigest(),
        "sidecar_sha256": hashlib.sha256(side.read_bytes()).hexdigest(),
        "user_message_sha256": att["user_message_sha256"],
        "system_prompt_sha256": att["system_prompt_sha256"],
        "rubric_version": runner.RUBRIC_VERSION,
        "reviewer": {"name": "fixture-reviewer",
                     "session": "fixture-session-2b030de8"},
        "reviewed_at": "2026-11-13T00:00:00+00:00",
        "statement": "FIXTURE review for offline tests only - source "
                     "fidelity checked against the frozen dossier; no "
                     "numerical value or ranking considered.",
    }
    if mutate:
        mutate(doc)
    for key in omit:
        doc.pop(key, None)
    d = run_dir / runner.REVIEW_REL_DIR
    d.mkdir(parents=True, exist_ok=True)
    target = d / f"call-{call:03d}.json"
    target.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    return target


# Two-process lock children (offline: they only import runner and touch one
# lock path - no networking, no credential, no receipt).
CONTEND_CHILD = (
    "import sys\n"
    "sys.path.insert(0, " + repr(str(HERE)) + ")\n"
    "import runner\n"
    "from pathlib import Path\n"
    "path = Path(sys.argv[1])\n"
    "try:\n"
    "    runner.acquire_lock(path, 'contending-child')\n"
    "except runner.Refusal:\n"
    "    print('REFUSED')\n"
    "    sys.exit(3)\n"
    "print('WON')\n"
    "runner.release_lock(path, 'contending-child')\n"
    "sys.exit(0)\n")

RACE_CHILD = (
    "import sys, time\n"
    "sys.path.insert(0, " + repr(str(HERE)) + ")\n"
    "import runner\n"
    "from pathlib import Path\n"
    "path, holder = Path(sys.argv[1]), sys.argv[2]\n"
    "ready = Path(sys.argv[3]); start = Path(sys.argv[4])\n"
    "res = Path(sys.argv[5]); release = Path(sys.argv[6])\n"
    "ready.touch()\n"
    "while not start.exists():\n"
    "    time.sleep(0.001)\n"
    "outcome, code = 'REFUSED', 3\n"
    "try:\n"
    "    runner.acquire_lock(path, holder)\n"
    "    outcome, code = 'WON', 0\n"
    "except runner.Refusal:\n"
    "    pass\n"
    "res.write_text(outcome)\n"
    "if outcome == 'WON':\n"
    "    while not release.exists():\n"
    "        time.sleep(0.001)\n"
    "    runner.release_lock(path, holder)\n"
    "sys.exit(code)\n")


def run_child(script: str, args):
    """Spawn one offline child process running ``script`` (a -c snippet)."""
    return subprocess.run(
        [sys.executable, "-B", "-c", script] + [str(a) for a in args],
        capture_output=True, text=True, timeout=60, cwd=str(HERE))


def wait_for(paths, timeout=25.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if all(Path(p).exists() for p in paths):
            return True
        time.sleep(0.01)
    return False


def build_fixture(tmp: Path) -> None:
    """A complete fake experiment root: byte-copies of the real v2 frozen
    inputs and of every pinned v1 source record, plus fixture review files."""
    (tmp / "frozen").mkdir(parents=True)
    for name in ("manifest.json", "schedule.json", "user_messages.json",
                 "single_a.txt", "single_b.txt"):
        shutil.copy(HERE / "frozen" / name, tmp / "frozen" / name)
    for rel in runner.V1_SOURCE_PINS:
        src, dst = V1_ROOT / rel, tmp / "v1" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
    (tmp / "reviews").mkdir()
    for _, rel in runner.REVIEW_BINDINGS:
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp / rel).write_text("# FIXTURE review copy for offline tests\n",
                               encoding="utf-8")


def write_fixture_receipt(root: Path, mutate=None) -> None:
    """A structurally valid FIXTURE receipt for offline tests only. It lives
    only inside the temp fixture root - the real receipt path is never written
    by this test suite, and this fixture is never a review artifact."""
    bindings = runner.current_bindings(root, root / "v1",
                                       REPO / "data" / "countries.json")
    if mutate:
        mutate(bindings)
    receipt = {
        "receipt_version": 1,
        "receipt_kind": runner.RECEIPT_KIND,
        "preflight": {"status": "signed_off", "document": "protocol.md",
                      "reviewed_by": "offline test fixture",
                      "reviewed_at": "2026-11-13T00:00:00Z",
                      "statement": "FIXTURE receipt generated by the offline "
                                   "test suite to exercise gate logic; not a "
                                   "review artifact and never written to the "
                                   "real repository path."},
        "prior_accounting": {
            "total_usd": "0.001993276", "dispatches": 5,
            "input_tokens": 13652, "output_tokens": 2274,
            "record_ids": [r[3] for r in runner.PRIOR_RECORDS]},
        "bindings": bindings,
    }
    (root / runner.RECEIPT_NAME).write_text(
        json.dumps(receipt, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8")


def quiet(fn, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = fn(*args)
    return result, buf.getvalue()


def fixture_cfg(tmp: Path, transport, prices=None, secret_loader=None,
                run_id="stage1-fixture") -> dict:
    return {
        "execute": True, "run_id": run_id, "receipt": None,
        "root": tmp, "v1_root": tmp / "v1",
        "data_path": REPO / "data" / "countries.json",
        "lock_path": tmp / "shared.lock",
        "transport": transport,
        "price_fetch": (lambda: prices) if prices is not None
        else (lambda: DEFAULT_PRICES),
        "secret_loader": secret_loader or (lambda: "fixture-secret-value"),
    }


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fx-", dir=str(TMPROOT)))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        build_fixture(self.tmp)

    def prepared(self, **kw) -> Path:
        write_fixture_receipt(self.tmp)
        return self.tmp


class DisabledByDefaultTests(unittest.TestCase):
    """No network, no credential, no writes when the --execute gate is absent."""

    def test_main_disabled_no_network_no_key(self):
        saved = (runner.https_post, runner.fetch_prices, runner.load_secret)
        log = []
        runner.https_post = not_called("https_post", log)
        runner.fetch_prices = not_called("fetch_prices", log)
        runner.load_secret = not_called("load_secret", log)
        try:
            rc, out = quiet(runner.main, [])
        finally:
            (runner.https_post, runner.fetch_prices,
             runner.load_secret) = saved
        self.assertEqual(rc, runner.EXIT_USAGE)
        self.assertEqual(log, [])
        self.assertIn("disabled", out)

    def test_cli_rejects_credential_flags(self):
        for argv in (["--execute", "--api-key", "abc"],
                     ["--token=x"],
                     ["--password", "x"],
                     ["--execute", "--credential=x"]):
            with self.assertRaises(runner.Refusal) as ctx:
                runner.parse_args(argv)
            self.assertEqual(ctx.exception.code, runner.EXIT_USAGE)
        with self.assertRaises(runner.Refusal) as ctx:
            runner.parse_args(["--frobnicate"])
        self.assertEqual(ctx.exception.code, runner.EXIT_USAGE)

    def test_disabled_preparation_preserves_receipt_and_reviews(self):
        # Independent reviews and a receipt may legitimately exist. Disabled
        # preparation must neither create nor modify them.
        paths = [HERE / runner.RECEIPT_NAME] + [HERE / rel for _, rel in runner.REVIEW_BINDINGS]
        before = {p: p.read_bytes() if p.is_file() else None for p in paths}
        rc, _ = quiet(runner.main, [])
        after = {p: p.read_bytes() if p.is_file() else None for p in paths}
        self.assertEqual(rc, runner.EXIT_USAGE)
        self.assertEqual(before, after)


class SharedLockTests(unittest.TestCase):
    def test_default_lock_path_is_the_v1_shared_lock(self):
        self.assertEqual(str(runner.DEFAULT_LOCK_PATH),
                         str(V1_ROOT / ".execution.lock"))

    def test_one_writer_release_and_foreign_lock_untouched(self):
        path = runner.DEFAULT_LOCK_PATH     # the shared transient lock
        if path.exists():                   # foreign/stale: never touch it
            before = path.read_bytes()
            with self.assertRaises(runner.Refusal):
                runner.acquire_lock(path, "stage1-fixture")
            self.assertEqual(path.read_bytes(), before)
            return
        runner.acquire_lock(path, "stage1-fixture")
        try:
            with self.assertRaises(runner.Refusal):
                runner.acquire_lock(path, "other-holder")
            doc = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(doc["holder"], "stage1-fixture")
            runner.release_lock(path, "other-holder")   # not ours: no removal
            self.assertTrue(path.exists())
        finally:
            runner.release_lock(path, "stage1-fixture")
        self.assertFalse(path.exists(), "our own lock must be released")

    def test_stale_crash_lock_is_refused_never_deleted(self):
        tmp = Path(tempfile.mkdtemp(prefix="lock-", dir=str(TMPROOT)))
        self.addCleanup(shutil.rmtree, tmp, True)
        path = tmp / ".execution.lock"
        path.write_text(json.dumps({"holder": "crashed", "pid": 12345}),
                        encoding="utf-8")
        before = path.read_bytes()
        with self.assertRaises(runner.Refusal) as ctx:
            runner.acquire_lock(path, "stage1-fixture")
        self.assertIn("stale", ctx.exception.reason)
        self.assertEqual(path.read_bytes(), before)
        # even a matching holder string must not remove a foreign pid's lock
        runner.release_lock(path, "crashed")
        self.assertTrue(path.exists())


class PriorAccountingTests(FixtureCase):
    """Exact Decimal reconstruction from the five preserved records."""

    def test_exact_reconstruction(self):
        prior = runner.read_v1_prior(self.tmp / "v1")
        self.assertEqual(prior["cost"], Decimal("0.001993276"))
        self.assertEqual(prior["input"], 13652)
        self.assertEqual(prior["output"], 2274)
        self.assertEqual(prior["dispatches"], 5)
        self.assertEqual(len(set(prior["ids"])), 5)
        self.assertEqual(prior["ids"], [r[3] for r in runner.PRIOR_RECORDS])

    def test_missing_record_refuses(self):
        (self.tmp / "v1" / "probes" / "probe-3" /
         "probe-result.json").unlink()
        with self.assertRaises(runner.Refusal) as ctx:
            runner.read_v1_prior(self.tmp / "v1")
        self.assertIn("missing", ctx.exception.reason)

    def test_hash_drift_refuses(self):
        p = self.tmp / "v1" / "probes" / "probe-2" / "probe-result.json"
        p.write_bytes(p.read_bytes() + b" ")
        with self.assertRaises(runner.Refusal) as ctx:
            runner.read_v1_prior(self.tmp / "v1")
        self.assertIn("hash mismatch", ctx.exception.reason)

    def test_unknown_extra_file_refuses(self):
        (self.tmp / "v1" / "probes" / "probe-1" /
         "notes.txt").write_text("rogue", encoding="utf-8")
        with self.assertRaises(runner.Refusal) as ctx:
            runner.read_v1_prior(self.tmp / "v1")
        self.assertIn("unexpected files", ctx.exception.reason)

    def test_extra_attempt_file_refuses(self):
        att = self.tmp / "v1" / "runs" / runner.V1_RUN_ID / "attempts"
        (att / "call-002.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(runner.Refusal) as ctx:
            runner.read_v1_prior(self.tmp / "v1")
        self.assertIn("unexpected files", ctx.exception.reason)

    def test_duplicate_provider_id_refuses(self):
        records = runner.parse_prior_records(self.tmp / "v1")
        records[4]["id"] = records[0]["id"]
        with self.assertRaises(runner.Refusal) as ctx:
            runner.reconcile_prior_records(records)
        self.assertIn("duplicate", ctx.exception.reason)

    def test_off_total_refuses(self):
        records = runner.parse_prior_records(self.tmp / "v1")
        records[4] = dict(records[4])
        records[4]["cost"] = Decimal("0.001080255")   # one ulp off
        with self.assertRaises(runner.Refusal) as ctx:
            runner.reconcile_prior_records(records)
        self.assertIn("pinned exact", ctx.exception.reason)

    def test_status_relabel_refuses(self):
        p = self.tmp / "v1" / "probes" / "probe-2" / "probe-result.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
        doc["status"] = "completed"          # relabel the failed probe
        p.write_text(json.dumps(doc), encoding="utf-8")
        with self.assertRaises(runner.Refusal) as ctx:
            runner.parse_prior_records(self.tmp / "v1")
        self.assertIn("status", ctx.exception.reason)


class InputHashTests(FixtureCase):
    def test_real_manifest_and_frozen_self_check(self):
        manifest = json.loads((HERE / "frozen" / "manifest.json")
                              .read_text(encoding="utf-8"))
        runner.verify_manifest(manifest, HERE, REPO / "data" /
                               "countries.json", V1_ROOT)

    def test_prompt_copies_byte_identical_to_v1(self):
        for name in ("single_a.txt", "single_b.txt"):
            self.assertEqual((HERE / "frozen" / name).read_bytes(),
                             (V1_ROOT / "frozen" / name).read_bytes())

    def test_tampered_v2_prompt_copy_refuses(self):
        p = self.tmp / "frozen" / "single_a.txt"
        p.write_bytes(p.read_bytes() + b"\n")
        manifest = json.loads((self.tmp / "frozen" / "manifest.json")
                              .read_text(encoding="utf-8"))
        with self.assertRaises(runner.Refusal):
            runner.verify_manifest(manifest, self.tmp,
                                   REPO / "data" / "countries.json",
                                   self.tmp / "v1")

    def test_tampered_v1_source_pin_refuses(self):
        p = self.tmp / "v1" / "frozen" / "single_a.txt"
        p.write_bytes(p.read_bytes() + b"\n")
        manifest = json.loads((self.tmp / "frozen" / "manifest.json")
                              .read_text(encoding="utf-8"))
        with self.assertRaises(runner.Refusal) as ctx:
            runner.verify_manifest(manifest, self.tmp,
                                   REPO / "data" / "countries.json",
                                   self.tmp / "v1")
        self.assertIn("v1/frozen/single_a.txt", ctx.exception.reason)

    def test_prompt_and_manifest_cotamper_refuses(self):
        # Regression for the byte-identity hole: tamper the v2 prompt copy AND
        # rewrite the manifest entry to match the tampered bytes. The v1
        # original is untouched, so only the new cross-check against the
        # pinned v1 prompt hash can catch this.
        p = self.tmp / "frozen" / "single_a.txt"
        p.write_bytes(p.read_bytes() + b"\n")
        mf = self.tmp / "frozen" / "manifest.json"
        doc = json.loads(mf.read_text(encoding="utf-8"))
        doc["files"]["single_a.txt"]["sha256"] = hashlib.sha256(
            p.read_bytes()).hexdigest()
        doc["files"]["single_a.txt"]["bytes"] = len(p.read_bytes())
        mf.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                      encoding="utf-8")
        # disk-vs-manifest and v1-original checks all pass now...
        with self.assertRaises(runner.Refusal) as ctx:
            runner.verify_manifest(doc, self.tmp,
                                   REPO / "data" / "countries.json",
                                   self.tmp / "v1")
        self.assertIn("co-tamper", ctx.exception.reason)

    def test_manifest_sentinel_semantics_drift_refuses(self):
        manifest = json.loads((HERE / "frozen" / "manifest.json")
                              .read_text(encoding="utf-8"))
        manifest["design"]["sentinel_semantics"] = "score is fine actually"
        with self.assertRaises(runner.Refusal) as ctx:
            runner.verify_manifest(manifest, HERE,
                                   REPO / "data" / "countries.json", V1_ROOT)
        self.assertIn("sentinel_semantics", ctx.exception.reason)

    def test_manifest_checkpoint_and_cache_policy_drift_refuse(self):
        def fresh():
            return json.loads((HERE / "frozen" / "manifest.json")
                              .read_text(encoding="utf-8"))
        m = fresh()
        m["design"]["semantic_checkpoint"] = "reviews are optional"
        with self.assertRaises(runner.Refusal) as ctx:
            runner.verify_manifest(m, HERE, REPO / "data" /
                                   "countries.json", V1_ROOT)
        self.assertIn("semantic checkpoint", ctx.exception.reason)
        m = fresh()
        m["design"]["max_attempts_per_invocation"] = 5
        with self.assertRaises(runner.Refusal) as ctx:
            runner.verify_manifest(m, HERE, REPO / "data" /
                                   "countries.json", V1_ROOT)
        self.assertIn("max_attempts_per_invocation", ctx.exception.reason)
        m = fresh()
        m["cache_policy"]["cache_writes"] = "assume it is free"
        with self.assertRaises(runner.Refusal) as ctx:
            runner.verify_manifest(m, HERE, REPO / "data" /
                                   "countries.json", V1_ROOT)
        self.assertIn("cache policy", ctx.exception.reason)

    def test_plan_constants(self):
        manifest = json.loads((HERE / "frozen" / "manifest.json")
                              .read_text(encoding="utf-8"))
        sched = json.loads((HERE / "frozen" / "schedule.json")
                           .read_text(encoding="utf-8"))["rows"]
        msgs = json.loads((HERE / "frozen" / "user_messages.json")
                          .read_text(encoding="utf-8"))["messages"]
        plan = runner.build_plan(HERE, sched, msgs, manifest)
        self.assertEqual(plan["max_per_call_input"], 66609)
        self.assertEqual(plan["aggregate_input"], 1112686)
        self.assertEqual(plan["aggregate_output"], 220000)
        self.assertLessEqual(plan["max_per_call_input"],
                             runner.RESERVATION_PER_CALL_UNITS)
        self.assertIn("NOT a guaranteed provider tokenizer bound",
                      plan["input_method"])

    def test_messages_byte_identical_to_v1_source_rows(self):
        v1_msgs = json.loads((V1_ROOT / "frozen" / "user_messages.json")
                             .read_text(encoding="utf-8"))
        msgs = json.loads((HERE / "frozen" / "user_messages.json")
                          .read_text(encoding="utf-8"))["messages"]
        self.assertEqual(len(msgs), 20)
        for m in msgs:
            src = v1_msgs[m["source_v1_call"] - 1]
            self.assertEqual(m["message"], src["message"])
            self.assertEqual(m["message_sha256"], src["message_sha256"])


class TimeoutDisclosureTests(FixtureCase):
    """P1: the 11000-token budget requires a predeclared, disclosed,
    transport-only timeout adjustment (30 s -> 300 s for the chat request),
    with the sole GENERATION-settings change still max_tokens 2000 -> 11000."""

    def test_timeout_constants_and_disclosure(self):
        self.assertEqual(runner.TRANSPORT_TIMEOUT_SECONDS, 300.0)
        self.assertEqual(runner.PRICE_FETCH_TIMEOUT_SECONDS, 30.0)
        self.assertEqual(runner.V1_TRANSPORT_TIMEOUT_SECONDS, 30.0)
        # generation settings: only max_output differs from v1
        diff = {k for k in runner.V1_REQUESTED_SETTINGS
                if runner.V1_REQUESTED_SETTINGS[k]
                != runner.REQUESTED_SETTINGS.get(k)}
        self.assertEqual(diff, {"max_output_tokens"})
        tc = runner.SETTINGS_CHANGE["transport_timeout"]
        self.assertEqual((tc["from_seconds"], tc["to_seconds"]), (30, 300))
        self.assertEqual(tc["price_fetch_timeout_seconds"], 30)
        self.assertIn("transport-only", tc["scope"])
        self.assertIn("NOT a generation setting", tc["scope"])
        self.assertIn("max_output_tokens 2000 -> 11000", tc["scope"])
        self.assertIn("28 s", tc["basis"])
        self.assertIn("unreconciled liability", tc["fail_closed"])
        self.assertTrue(
            runner.SETTINGS_CHANGE["sole_generation_setting_change"])
        # the real manifest discloses the identical block and still verifies
        manifest = json.loads((HERE / "frozen" / "manifest.json")
                              .read_text(encoding="utf-8"))
        self.assertEqual(
            manifest["requested_settings_change"]["transport_timeout"], tc)
        runner.verify_manifest(manifest, HERE,
                               REPO / "data" / "countries.json", V1_ROOT)

    def test_manifest_timeout_disclosure_drift_refuses(self):
        manifest = json.loads((HERE / "frozen" / "manifest.json")
                              .read_text(encoding="utf-8"))
        manifest["requested_settings_change"]["transport_timeout"][
            "to_seconds"] = 30
        with self.assertRaises(runner.Refusal) as ctx:
            runner.verify_manifest(manifest, HERE,
                                   REPO / "data" / "countries.json", V1_ROOT)
        self.assertIn("timeout", ctx.exception.reason)

    def test_transport_error_timeout_records_liability_and_stops(self):
        # Socket-timeout path stays fail-closed: transport raises, no raw
        # body -> unknown charge -> unreconciled liability -> stage stops and
        # any later run refuses before any call.
        write_fixture_receipt(self.tmp)
        transport = Transport([
            runner.Refusal(runner.EXIT_STOPPED,
                           "transport error (TimeoutError)")])
        cfg = fixture_cfg(self.tmp, transport)
        rc, out = quiet(runner.run, cfg)
        self.assertEqual(rc, runner.EXIT_STOPPED, out)
        self.assertEqual(len(transport.calls), 1)
        attempt = json.loads(
            (self.tmp / "runs" / "stage1-fixture" / "attempts" /
             "call-001.json").read_text(encoding="utf-8"))
        self.assertIn("transport error", attempt["stop_reason"])
        self.assertIsNone(attempt["raw_response"])
        self.assertIsNone(attempt["billed_on_failure"]["cost"])
        self.assertIsInstance(attempt["unreconciled_liability"], dict)
        result = json.loads((self.tmp / "runs" / "stage1-fixture" /
                             "result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "stopped")
        self.assertIsInstance(result["unreconciled_liability"], dict)
        # a follow-up run refuses on the liability before any dispatch
        transport2 = Transport()
        cfg2 = fixture_cfg(self.tmp, transport2, run_id="stage1-again")
        cfg2["price_fetch"] = not_called("price_fetch", [])
        rc2, out2 = quiet(runner.run, cfg2)
        self.assertEqual(rc2, runner.EXIT_GATE, out2)
        self.assertIn("liability", out2)
        self.assertEqual(transport2.calls, [])


class CrossProcessLockTests(unittest.TestCase):
    """P1: genuine two-process contention over the O_EXCL lock - offline only
    (children import runner and touch one lock path; no networking)."""

    def test_child_refuses_lock_held_by_parent_process(self):
        path = runner.DEFAULT_LOCK_PATH     # the real shared v1/v2 lock
        if path.exists():
            before = path.read_bytes()
            proc = run_child(CONTEND_CHILD, [path])
            self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
            self.assertIn("REFUSED", proc.stdout)
            self.assertEqual(path.read_bytes(), before)
            return
        runner.acquire_lock(path, "parent-holder")
        try:
            proc = run_child(CONTEND_CHILD, [path])
            self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
            self.assertIn("REFUSED", proc.stdout)
            doc = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(doc["holder"], "parent-holder")   # child must
            self.assertEqual(doc["pid"], os.getpid())           # not delete
        finally:
            runner.release_lock(path, "parent-holder")
        self.assertFalse(path.exists(), "parent releases its own lock")

    def test_two_processes_race_exactly_one_winner(self):
        ws = Path(tempfile.mkdtemp(prefix="race-", dir=str(TMPROOT)))
        self.addCleanup(shutil.rmtree, ws, True)
        lock = ws / ".execution.lock"
        start, release = ws / "start", ws / "release"
        slots = []
        for i in (1, 2):
            slots.append({"holder": f"racer-{i}",
                          "ready": ws / f"ready{i}",
                          "res": ws / f"res{i}"})
        procs = []
        for s in slots:
            procs.append(subprocess.Popen(
                [sys.executable, "-B", "-c", RACE_CHILD, str(lock),
                 s["holder"], str(s["ready"]), str(start), str(s["res"]),
                 str(release)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                cwd=str(HERE)))
        try:
            self.assertTrue(wait_for([s["ready"] for s in slots]),
                            "children never became ready")
            start.touch()                     # simultaneous attempt signal
            self.assertTrue(wait_for([s["res"] for s in slots]),
                            "children never reported an attempt outcome")
            outcomes = {s["holder"]: s["res"].read_text()
                        for s in slots}
            self.assertEqual(sorted(outcomes.values()),
                             ["REFUSED", "WON"],
                             f"exactly one winner required: {outcomes}")
            winner = next(h for h, o in outcomes.items() if o == "WON")
            # loser exited without touching the lock; winner still holds it
            doc = json.loads(lock.read_text(encoding="utf-8"))
            self.assertEqual(doc["holder"], winner)
            release.touch()                    # let the winner release
            for p in procs:
                out, err = p.communicate(timeout=30)
                self.assertIn(p.returncode, (0, 3), err)
            self.assertFalse(lock.exists(),
                             "winner releases; loser never deletes foreign lock")
        finally:
            for p in procs:
                if p.poll() is None:
                    p.kill()
                    p.wait()


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.sched_doc = json.loads((HERE / "frozen" / "schedule.json")
                                    .read_text(encoding="utf-8"))
        self.msgs_doc = json.loads((HERE / "frozen" / "user_messages.json")
                                   .read_text(encoding="utf-8"))
        self.rows = self.sched_doc["rows"]

    def test_exact_20_cells_cases_and_sentinels(self):
        msgs = runner.verify_schedule(self.rows, self.msgs_doc, V1_ROOT)
        self.assertEqual(len(msgs), 20)
        core = [r for r in self.rows if r["sentinel"] == "core"]
        empty = [r for r in self.rows if r["sentinel"] == "empty"]
        self.assertEqual(len(core), 16)
        self.assertEqual(len(empty), 4)
        self.assertEqual({(r["model"], r["variant"]) for r in empty},
                         {(m, v) for m in runner.MODELS for v in ("A", "B")})
        self.assertEqual({(r["case"], r["model"], r["variant"]) for r in core},
                         {(c, m, v) for c in runner.COUNTRIES
                          for m in runner.MODELS for v in ("A", "B")})
        # one draw, fresh contexts, DOSSIER label everywhere
        self.assertEqual({r["draw"] for r in self.rows}, {1})
        self.assertTrue(all(r["fresh_context"] for r in self.rows))
        self.assertEqual({r["label"] for r in self.rows}, {"DOSSIER"})

    def test_two_balanced_blocks_and_interleave(self):
        for blk in (1, 2):
            brows = [r for r in self.rows if r["block"] == blk]
            self.assertEqual(len(brows), 10)
            core = [r for r in brows if r["sentinel"] == "core"]
            sent = [r for r in brows if r["sentinel"] == "empty"]
            self.assertEqual((len(core), len(sent)), (8, 2))
            for c in runner.COUNTRIES:
                self.assertEqual(
                    sum(1 for r in core if r["case"] == c), 2, f"block {blk}")
            for m in runner.MODELS:
                self.assertEqual(
                    sum(1 for r in brows if r["model"] == m), 5)
            for v in ("A", "B"):
                self.assertEqual(
                    sum(1 for r in brows if r["variant"] == v), 5)
            idxs = [i for i, r in enumerate(brows)
                    if r["sentinel"] == "empty"]
            self.assertTrue(all(i not in (0, 9) for i in idxs))
            self.assertNotEqual(abs(idxs[0] - idxs[1]), 1)
            for c in runner.COUNTRIES:
                ci = [i for i, r in enumerate(brows) if r["case"] == c]
                self.assertNotEqual(ci[1] - ci[0], 1,
                                    f"country rows adjacent in block {blk}")

    def test_design_metadata_declares_freeze_and_limits(self):
        design = self.sched_doc["design"]
        self.assertEqual(design["attempts_max"], 20)
        self.assertEqual(design["generation"]["seed"],
                         "country-feasibility-v2-stage1")
        self.assertTrue(design["frozen_before_outcomes"])
        limits = design["limitations"]
        self.assertIn("within-cell repeat variance", limits)
        self.assertIn("label invariance", limits)
        self.assertIn("country rankings", limits)
        self.assertIn("neutral-label", design["excluded_v1_sentinel_family"])

    def test_tampered_schedule_row_refuses(self):
        rows = json.loads(json.dumps(self.rows))
        rows[0]["variant"] = "B" if rows[0]["variant"] == "A" else "A"
        with self.assertRaises(runner.Refusal):
            runner.verify_schedule(rows, self.msgs_doc, V1_ROOT)

    def test_tampered_message_bytes_refuse_even_with_updated_hash(self):
        doc = json.loads(json.dumps(self.msgs_doc))
        doc["messages"][0]["message"] += " tampered"
        doc["messages"][0]["message_sha256"] = hashlib.sha256(
            doc["messages"][0]["message"].encode()).hexdigest()
        with self.assertRaises(runner.Refusal) as ctx:
            runner.verify_schedule(self.rows, doc, V1_ROOT)
        self.assertIn("v1", ctx.exception.reason)


class ScoreLeakAndEndpointTests(unittest.TestCase):
    def test_fixed_https_endpoint_only(self):
        self.assertTrue(runner.API_BASE.startswith("https://"))
        self.assertEqual(runner.API_BASE,
                         "https://openrouter.ai/api/v1")
        self.assertEqual(runner.CHAT_URL,
                         runner.API_BASE + "/chat/completions")

    def test_request_whitelist_no_cache_no_fallback_no_reasoning(self):
        payload = runner.build_request(
            runner.MODELS[0], "sys", "msg", runner.REQUESTED_SETTINGS)
        self.assertEqual(set(payload), set(runner.REQUEST_KEYS))
        blob = json.dumps(payload)
        self.assertNotIn("cache", blob.lower())
        self.assertNotIn("reasoning", blob.lower())
        self.assertEqual(payload["provider"], {"allow_fallbacks": False})
        self.assertEqual(payload["max_tokens"], 11000)
        self.assertEqual(payload["temperature"], 1.0)
        self.assertEqual(payload["top_p"], 1.0)
        self.assertEqual(payload["model"], runner.MODELS[0])

    def test_single_settings_change_and_no_reasoning_parameter(self):
        self.assertEqual(runner.REQUESTED_SETTINGS,
                         {"temperature": 1.0, "top_p": 1.0,
                          "max_output_tokens": 11000})
        changed = {k for k in runner.V1_REQUESTED_SETTINGS
                   if runner.V1_REQUESTED_SETTINGS[k]
                   != runner.REQUESTED_SETTINGS.get(k)}
        self.assertEqual(changed, {"max_output_tokens"})
        self.assertTrue(
            runner.SETTINGS_CHANGE["sole_generation_setting_change"])
        self.assertNotIn("reasoning", runner.REQUEST_KEYS)

    def test_frozen_evidence_is_data_only(self):
        for fname in ("schedule.json", "user_messages.json"):
            doc = json.loads((HERE / "frozen" / fname)
                             .read_text(encoding="utf-8"))
            blob = json.dumps(doc).lower()
            for key in FORBIDDEN_EVIDENCE_KEYS:
                self.assertNotIn(f'"{key}"', blob,
                                 f"{fname} must not carry evidence key {key}")
        # source evidence snapshot is the pinned, whitelist-derived file
        manifest = json.loads((HERE / "frozen" / "manifest.json")
                              .read_text(encoding="utf-8"))
        self.assertEqual(manifest["evidence_snapshot"]["sha256"],
                         DATA_COUNTRIES_PIN)
        self.assertEqual(
            hashlib.sha256((REPO / "data" / "countries.json")
                           .read_bytes()).hexdigest(),
            DATA_COUNTRIES_PIN)

    def test_review_gate_never_reads_a_model_score(self):
        # Acceptance is structural/hash-based only: the gate must never
        # dereference a score value from any output.
        gate_src = inspect.getsource(runner.verify_prior_semantic_reviews)
        self.assertNotIn('["score"]', gate_src)
        side_src = inspect.getsource(runner.score_blind_sidecar)
        self.assertIn('k != "score"', side_src)   # score key is DROPPED
        self.assertNotIn('["score"]', side_src)

    def test_runner_source_references_no_adm1_data(self):
        # No sub-national or raw-evidence datasets may ever be inputs.
        src = (HERE / "runner.py").read_text(encoding="utf-8").lower()
        self.assertNotIn("raw_adm1", src)
        self.assertNotIn("raw_adm0", src)
        self.assertNotIn("raw_extra", src)


class OutputContractTests(unittest.TestCase):
    def test_valid_ok_and_abstention(self):
        obj = runner.validate_output_contract(CONTRACT_OK)
        self.assertEqual(obj["status"], "ok")
        obj = runner.validate_output_contract(CONTRACT_ABSTAIN)
        self.assertIsNone(obj["score"])

    def test_rejections(self):
        base = {"status": "ok", "why": "w", "evidence_ids": ["e"],
                "discovery": "d", "direct_harms": "h",
                "scope_triggers": "t", "uncertainty": "u"}
        bad_cases = []
        for score in (1.5, -0.1, "0.5", True, None, float("nan")):
            bad_cases.append(("score " + repr(score),
                              dict(base, score=score)))
        bad_cases.append(("missing score", dict(base)))
        bad_cases.append(("bad status", dict(base, status="pass",
                                              score=0.5)))
        bad_cases.append(("abstain with score",
                          dict(base, status="insufficient_evidence",
                               score=0.3)))
        bad_cases.append(("abstain missing score field",
                          dict(base, status="insufficient_evidence")))
        bad_cases.append(("missing why",
                          {k: v for k, v in base.items() if k != "why"}
                          | {"score": 0.5}))
        for name, case in bad_cases:
            with self.assertRaises(runner.Refusal, msg=name):
                runner.validate_output_contract(json.dumps(case))
        # prose around the object
        with self.assertRaises(runner.Refusal):
            runner.validate_output_contract("Sure: " + CONTRACT_OK)
        with self.assertRaises(runner.Refusal):
            runner.validate_output_contract(json.dumps([1, 2]))


def _validate(raw, status=200, model=runner.MODELS[0],
               reserved_in=43437, worst=Decimal("0.5")):
    return runner.validate_response(status, raw, model, reserved_in, worst)


class SentinelSemanticsTests(unittest.TestCase):
    """Context-aware check: an EMPTY-dossier sentinel must abstain
    (status insufficient_evidence + score null); core cells are free under
    the unchanged contract. The broader semantic review stays a separate,
    open process."""

    def test_empty_sentinel_rules(self):
        abstain = json.loads(CONTRACT_ABSTAIN)
        ok = json.loads(CONTRACT_OK)
        runner.validate_sentinel_semantics("empty", abstain)   # required
        runner.validate_sentinel_semantics("core", ok)         # allowed
        runner.validate_sentinel_semantics("core", abstain)    # allowed
        bad_cases = [
            ok,                                             # scored empty
            {"status": "ok", "score": None},               # wrong status
            {"status": "insufficient_evidence", "score": 0.5},   # score!
            {"status": "insufficient_evidence"},            # score missing
            "not-an-object",
        ]
        for bad in bad_cases:
            with self.assertRaises(runner.Refusal, msg=repr(bad)) as ctx:
                runner.validate_sentinel_semantics("empty", bad)
            self.assertEqual(ctx.exception.code, runner.EXIT_STOPPED)
            self.assertIn("empty-dossier sentinel", ctx.exception.reason)


class ResponseValidationTests(unittest.TestCase):
    """Every individual stop condition raises before any retry logic exists."""

    def test_reasoning_bound_documented_as_predeclared_assumption(self):
        doc = runner._validate_usage.__doc__ or ""
        self.assertIn("PREDECLARED FAIL-CLOSED ASSUMPTION", doc)
        self.assertIn("NOT an observation", doc)
        self.assertIn("2504", doc)          # the contradicting v1 record
        proto = (HERE / "protocol.md").read_text(encoding="utf-8")
        flat = " ".join(proto.split())
        self.assertIn("predeclared fail-closed assumption, not an observation",
                      flat)
        self.assertIn("2504", flat)
        # the behavioral rule itself is unchanged: still stops
        with self.assertRaises(runner.Refusal):
            _validate(provider_body(
                runner.MODELS[0],
                usage=default_usage(completion_tokens=50,
                                    total_tokens=40050,
                                    completion_tokens_details={
                                        "reasoning_tokens": 51})))

    def test_valid_response(self):
        ev = _validate(provider_body(runner.MODELS[0]))
        self.assertEqual(ev["http_status"], 200)
        self.assertEqual(ev["finish_reason"], "stop")
        self.assertEqual(ev["cost"], Decimal("0.0005"))
        self.assertEqual(ev["returned_provider"], "Relace")
        self.assertEqual(ev["parsed_output"]["score"], 0.5)

    def test_transport_and_shape_failures(self):
        m0, m1 = runner.MODELS
        no_provider = json.loads(provider_body(m0))
        no_provider["provider"] = None
        cases = [
            ("http error", 500, "{}"),
            ("malformed json", 200, "{not json"),
            ("error object", 200, json.dumps({"error": {"code": 402}})),
            ("nan literal", 200,
             '{"usage": {"cost": NaN}, "choices": [], "model": "x"}'),
            ("no choices", 200, json.dumps({"model": m0,
                                            "provider": "Relace",
                                            "choices": []})),
            ("empty content", 200, provider_body(m0, content="   ")),
            ("null content", 200, json.dumps({
                "model": m0, "provider": "Relace",
                "choices": [{"finish_reason": "stop",
                             "message": {"content": None}}]})),
            ("missing finish_reason", 200, json.dumps({
                "model": m0, "provider": "Relace",
                "choices": [{"message": {"content": "text"}}]})),
            ("truncated finish", 200, provider_body(m0, finish="length")),
            ("model substitution", 200, provider_body(m1)),
            ("missing provider", 200, json.dumps(no_provider)),
            ("unexpected routing", 200,
             provider_body(m0, provider="MysteryRoute")),
            ("bad contract", 200,
             provider_body(m0,
                           content='{"status": "ok", "score": 1.5}')),
        ]
        for name, status, raw in cases:
            with self.assertRaises(runner.Refusal, msg=name):
                _validate(raw, status=status)

    def test_billing_and_usage_failures(self):
        model = runner.MODELS[0]
        usage_cases = [
            ("totals mismatch", default_usage(total_tokens=40101)),
            ("missing cost", {k: v for k, v in default_usage().items()
                              if k != "cost"}),
            ("zero cost", default_usage(cost=0)),
            ("negative cost", default_usage(cost=-1)),
            ("byok", default_usage(is_byok=True)),
            ("cache write unreconcilable", default_usage(
                prompt_tokens_details={"cached_tokens": 0,
                                       "cache_write_tokens": 3})),
            ("cached exceeds billed prompt", default_usage(
                prompt_tokens_details={"cached_tokens": 44000,
                                       "cache_write_tokens": 0})),
            ("missing prompt details", {
                k: v for k, v in default_usage().items()
                if k != "prompt_tokens_details"}),
            ("missing reasoning details", {
                k: v for k, v in default_usage().items()
                if k != "completion_tokens_details"}),
            ("reasoning exceeds completion",
             default_usage(completion_tokens=50,
                           total_tokens=40050,
                           completion_tokens_details={"reasoning_tokens": 51})),
            ("negative reasoning",
             default_usage(
                 completion_tokens_details={"reasoning_tokens": -1})),
            ("billed input over reservation",
             default_usage(prompt_tokens=44000, total_tokens=44100)),
            ("billed output over 11000",
             default_usage(completion_tokens=11001,
                           total_tokens=51001,
                           completion_tokens_details={"reasoning_tokens": 5000})),
        ]
        for name, usage in usage_cases:
            with self.assertRaises(runner.Refusal, msg=name):
                _validate(provider_body(model, usage=usage))
        # cost above the call's worst-case reservation
        with self.assertRaises(runner.Refusal) as ctx:
            _validate(provider_body(model, usage=default_usage(cost=0.9)),
                       worst=Decimal("0.5"))
        self.assertIn("reservation", ctx.exception.reason)
        # provider-initiated cache READ with valid arithmetic is ACCEPTED
        # (no cache directive is ever sent; it is logged, never claimed
        # reproducible)
        ev = _validate(provider_body(
            model,
            usage=default_usage(
                prompt_tokens_details={"cached_tokens": 50,
                                       "cache_write_tokens": 0})))
        self.assertEqual(ev["cache_usage"]["cached_read_tokens"], 50)
        self.assertEqual(ev["cache_usage"]["cache_write_tokens"], 0)
        self.assertIn("no reproducibility claim", ev["cache_usage"]["note"])

    def test_unknown_provider_prices_refuse(self):
        with self.assertRaises(runner.Refusal):
            runner._price(0, runner.MODELS[0], "prompt")
        with self.assertRaises(runner.Refusal):
            runner._price(-1, runner.MODELS[0], "completion")
        with self.assertRaises(runner.Refusal):
            runner._price("free", runner.MODELS[0], "prompt")


class CeilingTests(unittest.TestCase):
    """Single-call pre-dispatch ceilings and the cross-invocation USD guard."""

    def _plan(self, n=20):
        return {"per_call_input": [66609] * n}

    def _prior(self, **over):
        p = {"used_usd": Decimal(0), "used_input": 0, "used_output": 0,
             "reserved_in": 0}
        p.update(over)
        return p

    def test_attempt_ceiling_max_20(self):
        plan = self._plan()
        self.assertIsNone(runner.pre_dispatch_ceiling_violation(
            19, plan, self._prior(), Decimal("0.001993276")))
        v = runner.pre_dispatch_ceiling_violation(
            20, plan, self._prior(), Decimal(0))
        self.assertIn("attempt ceiling", v)

    def test_schedule_exhausted_defense(self):
        v = runner.pre_dispatch_ceiling_violation(
            5, self._plan(n=5), self._prior(), Decimal(0))
        self.assertIn("schedule exhausted", v)

    def test_combined_dispatch_ceiling_25(self):
        self.assertIsNone(runner.total_dispatch_violation(0, 1))
        self.assertIn("25", runner.total_dispatch_violation(1, 20))
        self.assertIn("25", runner.total_dispatch_violation(0, 21))
        saved = runner.PRIOR_DISPATCHES       # defense-in-depth if constants
        runner.PRIOR_DISPATCHES = 6           # ever diverge
        try:
            v = runner.pre_dispatch_ceiling_violation(
                19, self._plan(), self._prior(), Decimal(0))
        finally:
            runner.PRIOR_DISPATCHES = saved
        self.assertIn("combined dispatch ceiling", v)

    def test_output_reservation_accumulates_across_invocations(self):
        plan = self._plan()
        self.assertIsNone(runner.pre_dispatch_ceiling_violation(
            18, plan, self._prior(used_output=209000), Decimal(0)))
        v = runner.pre_dispatch_ceiling_violation(
            18, plan, self._prior(used_output=209001), Decimal(0))
        self.assertIn("output", v)

    def test_input_reservation_accumulates_across_invocations(self):
        plan = self._plan()
        self.assertIn("input reservation",
                      runner.pre_dispatch_ceiling_violation(
                          0, plan, self._prior(reserved_in=1400000),
                          Decimal(0)))
        self.assertIn("input reservation",
                      runner.pre_dispatch_ceiling_violation(
                          0, plan, self._prior(used_input=1400000),
                          Decimal(0)))

    def test_corrupted_accounting_refuses(self):
        plan = self._plan()
        self.assertIn("accounting corrupted",
                      runner.pre_dispatch_ceiling_violation(
                          0, plan, self._prior(), 0.5))   # float, not Decimal
        self.assertIn("accounting corrupted",
                      runner.pre_dispatch_ceiling_violation(
                          0, plan,
                          self._prior(used_usd=Decimal("NaN")), Decimal(0)))
        self.assertIn("accounting corrupted",
                      runner.pre_dispatch_ceiling_violation(
                          0, plan, self._prior(used_input=-1), Decimal(0)))

    def test_usd_guard_counts_exact_combined_prior(self):
        plan = {"caps": {"usd_ceiling": Decimal("10.00")}}
        # combined exact prior (v1 + prior v2) + THIS call's worst case
        v = runner.prior_budget_violation(Decimal("9.99"), plan,
                                          Decimal("0.09"))
        self.assertIn("budget already consumed", v)
        # message must say ONE call's reservation, not the whole stage
        self.assertIn("this call's worst-case reservation", v)
        self.assertNotIn("this stage's worst-case", v)
        self.assertIsNone(runner.prior_budget_violation(
            Decimal("0.001993276"), plan, Decimal("0.09")))


class ExecuteGateTests(FixtureCase):
    """Gate refusals happen before any network, credential or dispatch."""

    def _expect_gate(self, cfg, transport, needle=None):
        rc, out = quiet(runner.run, cfg)
        self.assertEqual(rc, runner.EXIT_GATE, out)
        self.assertEqual(transport.calls, [])
        if needle:
            self.assertIn(needle, out)
        return out

    def test_missing_receipt_no_side_effects(self):
        transport = Transport()
        cfg = fixture_cfg(self.tmp, transport)
        cfg["price_fetch"] = not_called("price_fetch", [])
        cfg["secret_loader"] = not_called("secret_loader", [])
        out = self._expect_gate(cfg, transport,
                                "no reviewed v2 preflight receipt")
        self.assertFalse((self.tmp / "shared.lock").exists())
        self.assertFalse((self.tmp / "runs").exists())

    def test_receipt_hash_mismatch_refuses(self):
        write_fixture_receipt(
            self.tmp,
            mutate=lambda b: b.__setitem__("protocol.md", "0" * 64))
        transport = Transport()
        cfg = fixture_cfg(self.tmp, transport)
        cfg["price_fetch"] = not_called("price_fetch", [])
        self._expect_gate(cfg, transport, "binding hash mismatch")

    def test_missing_review_artifact_refuses(self):
        write_fixture_receipt(self.tmp)
        (self.tmp / "reviews" / "code-review.md").unlink()
        transport = Transport()
        cfg = fixture_cfg(self.tmp, transport)
        cfg["price_fetch"] = not_called("price_fetch", [])
        self._expect_gate(cfg, transport, "independent-code-review")

    def test_tampered_v1_bytes_refuse_before_dispatch(self):
        write_fixture_receipt(self.tmp)
        p = self.tmp / "v1" / "ledger.json"
        p.write_bytes(p.read_bytes() + b"\n")
        transport = Transport()
        cfg = fixture_cfg(self.tmp, transport)
        cfg["price_fetch"] = not_called("price_fetch", [])
        self._expect_gate(cfg, transport, "binding hash mismatch")

    def test_stale_incomplete_v2_run_refuses(self):
        write_fixture_receipt(self.tmp)
        stale = self.tmp / "runs" / "crashed"
        stale.mkdir(parents=True)
        (stale / "run.json").write_text('{"status": "in_progress"}',
                                        encoding="utf-8")
        transport = Transport()
        cfg = fixture_cfg(self.tmp, transport)
        cfg["price_fetch"] = not_called("price_fetch", [])
        out = self._expect_gate(cfg, transport, "no terminal result.json")
        self.assertFalse((self.tmp / "shared.lock").exists(),
                         "the shared lock must be released on refusal")

    def test_existing_run_id_refuses_overwrite(self):
        write_fixture_receipt(self.tmp)
        (self.tmp / "runs" / "stage1-fixture").mkdir(parents=True)
        transport = Transport()
        cfg = fixture_cfg(self.tmp, transport)
        cfg["price_fetch"] = not_called("price_fetch", [])
        self._expect_gate(cfg, transport, "already exists")

    def _run_successful_first_call(self):
        """Real invocation 1 (schedule call 1) -> paused pending review."""
        write_fixture_receipt(self.tmp)
        rc, out, transport = invoke(self.tmp, "first", [None])
        self.assertEqual(rc, runner.EXIT_OK, out)
        self.assertEqual(len(transport.calls), 1)
        run_dir = self.tmp / "runs" / "first"
        rec = json.loads((run_dir / "attempts" / "call-001.json")
                         .read_text(encoding="utf-8"))
        self.assertEqual(rec["requested_model"],
                         json.loads((HERE / "frozen" / "schedule.json")
                                    .read_text(encoding="utf-8"))
                         ["rows"][0]["model"])
        self.assertNotIn("model", rec)          # requested_model, never model
        return run_dir

    def test_missing_review_blocks_before_price_secret_network(self):
        self._run_successful_first_call()       # NO review recorded
        transport2 = Transport()
        cfg = fixture_cfg(self.tmp, transport2, run_id="second")
        plog, slog = [], []
        cfg["price_fetch"] = not_called("price_fetch", plog)
        cfg["secret_loader"] = not_called("secret_loader", slog)
        self._expect_gate(cfg, transport2,
                          "missing independent semantic review")
        self.assertEqual(plog, [])              # blocked BEFORE price fetch
        self.assertEqual(slog, [])              # and BEFORE the credential
        self.assertEqual(transport2.calls, [])  # and BEFORE any network
        self.assertFalse((self.tmp / "shared.lock").exists())

    def test_fail_uncertain_or_tampered_reviews_block(self):
        run1 = self._run_successful_first_call()
        cases = {
            "FAIL verdict": {"verdict": "FAIL"},
            "UNCERTAIN verdict": {"verdict": "UNCERTAIN"},
            "invalid verdict": {"verdict": "MAYBE"},
            "tampered response hash": {"response_sha256": "0" * 64},
            "tampered sidecar hash": {"sidecar_sha256": "0" * 64},
            "wrong frozen message": {"user_message_sha256": "0" * 64},
            "wrong frozen prompt": {"system_prompt_sha256": "0" * 64},
            "wrong rubric version": {"rubric_version": "something-else"},
            "score key leaked into review": {"score": 0.9},
            "rank key leaked into review": {"ranking": ["x"]},
            "reviewer identity missing":
                {"reviewer": {"name": " ", "session": ""}},
            "statement missing": {"statement": ""},
            "reviewed_at missing": {"reviewed_at": ""},
            "wrong review version": {"review_version": 99},
        }
        for name, patch in cases.items():
            with self.subTest(case=name):
                write_fixture_review(
                    run1, 1,
                    mutate=lambda d, p=patch: d.update(p))
                transport = Transport()
                cfg = fixture_cfg(self.tmp, transport, run_id="second")
                plog, slog = [], []
                cfg["price_fetch"] = not_called("price_fetch", plog)
                cfg["secret_loader"] = not_called("secret_loader", slog)
                out = self._expect_gate(cfg, transport,
                                        "blocks all later calls")
                self.assertNotIn("dispatched", out)
                self.assertEqual(plog, [])
                self.assertEqual(slog, [])

    def test_parsed_output_cotamper_with_unchanged_raw_refuses(self):
        # P1 follow-up regression: parsed_output + sidecar + review ALL
        # mutated consistently while raw_response stays byte-identical - the
        # gate must re-parse the raw text, re-validate it under the frozen
        # contract, demand exact equality, and refuse BEFORE price/secret/
        # transport.
        run1 = self._run_successful_first_call()
        write_fixture_review(run1, 1)
        att_path = run1 / "attempts" / "call-001.json"
        att = json.loads(att_path.read_text(encoding="utf-8"))
        raw_before = att["raw_response"]
        att["parsed_output"]["why"] = "co-tampered rationale"
        att["parsed_output"]["discovery"] = "co-tampered discovery"
        att_path.write_text(json.dumps(att, indent=1) + "\n",
                            encoding="utf-8")
        side = runner.sidecar_path(run1, 1)
        sd = json.loads(side.read_text(encoding="utf-8"))
        sd["output"]["why"] = "co-tampered rationale"
        sd["output"]["discovery"] = "co-tampered discovery"
        side.write_text(json.dumps(sd, indent=1) + "\n", encoding="utf-8")
        rv_path = runner.review_path(run1, 1)
        rv = json.loads(rv_path.read_text(encoding="utf-8"))
        rv["sidecar_sha256"] = hashlib.sha256(
            side.read_bytes()).hexdigest()      # consistent with tamper
        rv_path.write_text(json.dumps(rv, indent=1) + "\n", encoding="utf-8")
        att_after = json.loads(att_path.read_text(encoding="utf-8"))
        self.assertEqual(att_after["raw_response"], raw_before)  # raw intact
        transport = Transport()
        cfg = fixture_cfg(self.tmp, transport, run_id="second")
        plog, slog = [], []
        cfg["price_fetch"] = not_called("price_fetch", plog)
        cfg["secret_loader"] = not_called("secret_loader", slog)
        self._expect_gate(
            cfg, transport,
            "frozen-contract parse of the preserved raw response")
        self.assertEqual(plog, [])              # refused BEFORE price fetch
        self.assertEqual(slog, [])              # BEFORE the credential
        self.assertEqual(transport.calls, [])   # BEFORE any network

    def test_malformed_or_missing_raw_output_blocks_before_dispatch(self):
        run1 = self._run_successful_first_call()
        write_fixture_review(run1, 1)
        att_path = run1 / "attempts" / "call-001.json"
        original = att_path.read_text(encoding="utf-8")
        cases = [
            ("{not json", "is not strict JSON"),
            (json.dumps({"id": "x", "choices": []}),
             "no usable assistant content"),
            (json.dumps({"id": "x",
                         "choices": [{"message": {"content": None}}]}),
             "no usable assistant content"),
            (json.dumps({"id": "x",
                         "choices": [{"message": {
                             "content": '{"status": "ok", '
                                        '"score": 1.5}'}}]}),
             "fails the frozen output contract"),
        ]
        for raw, needle in cases:
            with self.subTest(case=needle):
                att = json.loads(original)
                att["raw_response"] = raw
                # keep the record self-consistent so ONLY the content checks
                # (not the stored hash) can decide the refusal
                att["raw_response_sha256"] = hashlib.sha256(
                    raw.encode("utf-8")).hexdigest()
                att_path.write_text(json.dumps(att, indent=1) + "\n",
                                    encoding="utf-8")
                transport = Transport()
                cfg = fixture_cfg(self.tmp, transport, run_id="second")
                plog, slog = [], []
                cfg["price_fetch"] = not_called("price_fetch", plog)
                cfg["secret_loader"] = not_called("secret_loader", slog)
                self._expect_gate(cfg, transport, needle)
                self.assertEqual(plog, [])
                self.assertEqual(slog, [])
                self.assertEqual(transport.calls, [])

    def test_honest_raw_rederivation_equals_and_gate_passes(self):
        # Honest control: the raw re-derivation equals the recorded
        # parsed_output, and with an honest PASS review the gate accepts and
        # the next invocation still dispatches exactly one next cell.
        run1 = self._run_successful_first_call()
        att = json.loads((run1 / "attempts" / "call-001.json")
                         .read_text(encoding="utf-8"))
        body = json.loads(att["raw_response"])   # strict parse of preserved raw
        content = body["choices"][0]["message"]["content"]
        derived = runner.validate_output_contract(content)
        self.assertEqual(derived, att["parsed_output"])
        write_fixture_review(run1, 1)
        rc, out, transport2 = invoke(self.tmp, "second", [None])
        self.assertEqual(rc, runner.EXIT_OK, out)
        self.assertEqual(len(transport2.calls), 1)
        att2 = json.loads((self.tmp / "runs" / "second" /
                           "attempts" / "call-002.json")
                          .read_text(encoding="utf-8"))
        self.assertEqual(att2["call"], 2)      # next cell only

    def test_attempt_sidecar_review_cotamper_frozen_anchor_refuses(self):
        # P1 regression: attempt record + sidecar + review ALL mutated to
        # agree on a WRONG prompt/message must still be refused, because the
        # gate anchors to the re-read immutable frozen bytes - not to the
        # writable run directory - and before price/secret/transport.
        run1 = self._run_successful_first_call()
        write_fixture_review(run1, 1)
        fake_msg = hashlib.sha256(b"wrong-message").hexdigest()
        fake_prompt = hashlib.sha256(b"wrong-prompt").hexdigest()
        att_path = run1 / "attempts" / "call-001.json"
        att = json.loads(att_path.read_text(encoding="utf-8"))
        att["user_message_sha256"] = fake_msg
        att["system_prompt_sha256"] = fake_prompt
        att_path.write_text(json.dumps(att, indent=1) + "\n",
                            encoding="utf-8")
        side = runner.sidecar_path(run1, 1)
        sd = json.loads(side.read_text(encoding="utf-8"))
        sd["frozen_dossier"]["user_message_sha256"] = fake_msg
        sd["frozen_dossier"]["system_prompt_sha256"] = fake_prompt
        side.write_text(json.dumps(sd, indent=1) + "\n", encoding="utf-8")
        rv_path = runner.review_path(run1, 1)
        rv = json.loads(rv_path.read_text(encoding="utf-8"))
        rv["user_message_sha256"] = fake_msg
        rv["system_prompt_sha256"] = fake_prompt
        rv["sidecar_sha256"] = hashlib.sha256(
            side.read_bytes()).hexdigest()      # consistent with tamper
        rv_path.write_text(json.dumps(rv, indent=1) + "\n", encoding="utf-8")
        transport = Transport()
        cfg = fixture_cfg(self.tmp, transport, run_id="second")
        plog, slog = [], []
        cfg["price_fetch"] = not_called("price_fetch", plog)
        cfg["secret_loader"] = not_called("secret_loader", slog)
        self._expect_gate(
            cfg, transport,
            "verified frozen schedule/message/prompt bytes for that call")
        self.assertEqual(plog, [])              # refused BEFORE price fetch
        self.assertEqual(slog, [])              # BEFORE the credential
        self.assertEqual(transport.calls, [])   # BEFORE any network

    def test_attempt_receipt_binding_drift_blocks(self):
        # The attempt must chain to the current invocation's receipt hash.
        run1 = self._run_successful_first_call()
        write_fixture_review(run1, 1)
        att_path = run1 / "attempts" / "call-001.json"
        att = json.loads(att_path.read_text(encoding="utf-8"))
        att["preflight_receipt_sha256"] = "0" * 64
        att_path.write_text(json.dumps(att, indent=1) + "\n",
                            encoding="utf-8")
        transport = Transport()
        cfg = fixture_cfg(self.tmp, transport, run_id="second")
        plog, slog = [], []
        cfg["price_fetch"] = not_called("price_fetch", plog)
        cfg["secret_loader"] = not_called("secret_loader", slog)
        out = self._expect_gate(cfg, transport, "preflight_receipt_sha256")
        self.assertEqual(plog, [])
        self.assertEqual(slog, [])
        self.assertEqual(transport.calls, [])

    def test_honest_records_pass_frozen_anchor_cross_check(self):
        # Normal pass: honest records/sidecars/reviews satisfy the new
        # frozen-byte anchoring and the next cell dispatches normally.
        write_fixture_receipt(self.tmp)
        rc1, out1, t1 = invoke(self.tmp, "first", [None])
        self.assertEqual(rc1, runner.EXIT_OK, out1)
        write_fixture_review(self.tmp / "runs" / "first", 1)
        rc2, out2, t2 = invoke(self.tmp, "second", [None])
        self.assertEqual(rc2, runner.EXIT_OK, out2)
        self.assertEqual(len(t2.calls), 1)
        att2 = json.loads((self.tmp / "runs" / "second" /
                           "attempts" / "call-002.json")
                          .read_text(encoding="utf-8"))
        self.assertEqual(att2["call"], 2)      # still the next cell only

    def test_tampered_sidecar_file_blocks(self):
        run1 = self._run_successful_first_call()
        write_fixture_review(run1, 1)
        side = runner.sidecar_path(run1, 1)
        doc = json.loads(side.read_text(encoding="utf-8"))
        doc["output"]["why"] = "tampered prose"
        side.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
        transport = Transport()
        cfg = fixture_cfg(self.tmp, transport, run_id="second")
        cfg["price_fetch"] = not_called("price_fetch", [])
        self._expect_gate(cfg, transport, "sidecar")

    def test_failed_prior_attempt_terminally_blocks_later_invocations(self):
        write_fixture_receipt(self.tmp)
        rc, out, t1 = invoke(
            self.tmp, "first",
            [(200, provider_body(runner.MODELS[0], finish="length"))])
        self.assertEqual(rc, runner.EXIT_STOPPED, out)
        transport2 = Transport()
        cfg = fixture_cfg(self.tmp, transport2, run_id="second")
        plog, slog = [], []
        cfg["price_fetch"] = not_called("price_fetch", plog)
        cfg["secret_loader"] = not_called("secret_loader", slog)
        self._expect_gate(cfg, transport2, "FAILED/partial output")
        self.assertEqual(plog, [])
        self.assertEqual(slog, [])
        self.assertEqual(transport2.calls, [])

    def test_prior_attempts_must_be_contiguous_prefix_no_skip(self):
        # Two real-shaped prior attempts identical except requested_model must
        # yield two DISTINCT cell keys (regression: the old model=None reading
        # collided them), and a non-prefix set {1,17} must be refused.
        write_fixture_receipt(self.tmp)
        rows = json.loads((HERE / "frozen" / "schedule.json")
                          .read_text(encoding="utf-8"))["rows"]
        row_a = rows[0]                        # core/NPL/deepseek/A
        row_b = next(r for r in rows
                     if r["case"] == "NPL" and r["variant"] == "A"
                     and r["sentinel"] == "core"
                     and r["model"] != row_a["model"])
        self.assertNotEqual(runner.cell_key(attempt_record_shape(row_a)),
                            runner.cell_key(attempt_record_shape(row_b)))
        prior = self.tmp / "runs" / "earlier"
        (prior / "attempts").mkdir(parents=True)
        for row in (row_a, row_b):
            (prior / "attempts" / f"call-{row['call']:03d}.json").write_text(
                json.dumps(attempt_record_shape(row)), encoding="utf-8")
        (prior / "result.json").write_text(json.dumps(
            {"used_usd": "0.0002", "used_input_tokens": 80000,
             "used_output_tokens": 200,
             "attempted_calls": sorted([row_a["call"], row_b["call"]]),
             "unreconciled_liability": None}), encoding="utf-8")
        state = runner.prior_v2_state(self.tmp, rows)
        self.assertEqual(sorted(state["attempt_records"]),
                         [row_a["call"], row_b["call"]])
        models = {rec["requested_model"]
                  for _, rec in state["attempt_records"].values()}
        self.assertEqual(models, {row_a["model"], row_b["model"]})
        transport = Transport()
        cfg = fixture_cfg(self.tmp, transport)
        cfg["price_fetch"] = not_called("price_fetch", [])
        self._expect_gate(cfg, transport,
                          "not the contiguous schedule prefix")

    def test_cell_key_matches_schedule_and_attempt_shapes(self):
        rows = json.loads((HERE / "frozen" / "schedule.json")
                          .read_text(encoding="utf-8"))["rows"]
        keys = set()
        for row in rows:
            self.assertEqual(runner.cell_key(attempt_record_shape(row)),
                             runner.cell_key(row))
            keys.add(runner.cell_key(row))
        self.assertEqual(len(keys), 20)         # 20 distinct cells

    def test_stage_complete_blocks_21st_invocation(self):
        # Fixture: all 20 scheduled attempts already dispatched (success
        # shaped; the completion gate fires before the review gate, so no
        # reviews are needed for this fixture).
        write_fixture_receipt(self.tmp)
        rows = json.loads((HERE / "frozen" / "schedule.json")
                          .read_text(encoding="utf-8"))["rows"]
        for row in rows:
            d = self.tmp / "runs" / f"inv-{row['call']:02d}"
            (d / "attempts").mkdir(parents=True)
            att = attempt_record_shape(row)
            content = (CONTRACT_ABSTAIN if row["sentinel"] == "empty"
                       else CONTRACT_OK)
            att["parsed_output"] = json.loads(content)
            att["raw_response"] = provider_body(row["model"],
                                                 content=content)
            att["raw_response_sha256"] = hashlib.sha256(
                att["raw_response"].encode("utf-8")).hexdigest()
            (d / "attempts" / f"call-{row['call']:03d}.json").write_text(
                json.dumps(att), encoding="utf-8")
            (d / "result.json").write_text(json.dumps(
                {"used_usd": "0.0005", "used_input_tokens": 40000,
                 "used_output_tokens": 100,
                 "attempted_calls": [row["call"]],
                 "unreconciled_liability": None}), encoding="utf-8")
        transport = Transport()
        cfg = fixture_cfg(self.tmp, transport, run_id="inv-21")
        plog, slog = [], []
        cfg["price_fetch"] = not_called("price_fetch", plog)
        cfg["secret_loader"] = not_called("secret_loader", slog)
        self._expect_gate(cfg, transport, "stage one complete")
        self.assertEqual(plog, [])
        self.assertEqual(slog, [])
        self.assertEqual(transport.calls, [])

    def test_shared_usd_guard_enforced_across_invocations(self):
        # Real invocation 1 + PASS review, then the prior tally sits just
        # under the ceiling: the next invocation must refuse at the budget
        # gate (v1's exact prior cost is always part of the shared total)
        # before any credential or call.
        run1 = self._run_successful_first_call()
        write_fixture_review(run1, 1)
        run1_doc = json.loads((run1 / "run.json").read_text(
            encoding="utf-8"))
        self.assertEqual(run1_doc["prior_accounting"]["total_usd"],
                         "0.001993276")         # exact v1 prior, always
        result_path = run1 / "result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["used_usd"] = "9.99"              # fixture: near the ceiling
        result_path.write_text(json.dumps(result) + "\n", encoding="utf-8")
        transport2 = Transport()
        cfg = fixture_cfg(self.tmp, transport2, run_id="second")
        slog = []
        cfg["secret_loader"] = not_called("secret_loader", slog)
        self._expect_gate(cfg, transport2, "budget already consumed")
        self.assertEqual(slog, [])
        self.assertEqual(transport2.calls, [])

    def test_unreconciled_liability_blocks_new_run(self):
        write_fixture_receipt(self.tmp)
        prior = self.tmp / "runs" / "liability"
        (prior / "attempts").mkdir(parents=True)
        (prior / "result.json").write_text(json.dumps(
            {"used_usd": "0.01", "attempted_calls": [],
             "unreconciled_liability": {"reason": "cost unknown",
                                        "call": 1}}), encoding="utf-8")
        transport = Transport()
        cfg = fixture_cfg(self.tmp, transport)
        cfg["price_fetch"] = not_called("price_fetch", [])
        self._expect_gate(cfg, transport, "unreconciled liability")

    def test_budget_refuses_before_credential_or_transport(self):
        write_fixture_receipt(self.tmp)
        transport = Transport()
        cfg = fixture_cfg(self.tmp, transport,
                          prices={"deepseek/deepseek-v4.1-flash":
                                  {"prompt": Decimal("1"),
                                   "completion": Decimal("1")},
                                  "google/gemini-3.8-flash":
                                  {"prompt": Decimal("1"),
                                   "completion": Decimal("1")}})
        cfg["secret_loader"] = not_called("secret_loader", [])
        self._expect_gate(cfg, transport, "budget")

    def test_empty_secret_refuses_before_transport(self):
        write_fixture_receipt(self.tmp)
        transport = Transport()
        cfg = fixture_cfg(self.tmp, transport,
                          secret_loader=lambda: "")
        self._expect_gate(cfg, transport, "OPENROUTER_API_KEY")


class DispatchTests(FixtureCase):
    def _prepared_cfg(self, modes, **kw):
        write_fixture_receipt(self.tmp)
        transport = Transport(modes)
        cfg = fixture_cfg(self.tmp, transport, **kw)
        return cfg, transport

    def test_single_invocation_dispatches_exactly_one_call(self):
        # TWO responses scripted; a compliant invocation must consume exactly
        # ONE (next scheduled cell) and terminate paused for review.
        cfg, transport = self._prepared_cfg([None, None])
        rc, out = quiet(runner.run, cfg)
        self.assertEqual(rc, runner.EXIT_OK, out)
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(transport.left, 1)      # second cell NOT dispatched
        self.assertEqual(set(transport.timeouts), {300.0})
        payload = transport.calls[0]
        self.assertEqual(payload["max_tokens"], 11000)
        self.assertEqual(set(payload), set(runner.REQUEST_KEYS))
        self.assertNotIn("cache", json.dumps(payload).lower())
        rows = json.loads((HERE / "frozen" / "schedule.json")
                          .read_text(encoding="utf-8"))["rows"]
        run_dir = self.tmp / "runs" / "stage1-fixture"
        # every scoring output preserved: raw + billing + parsed + sidecar
        att = json.loads((run_dir / "attempts" / "call-001.json")
                         .read_text(encoding="utf-8"))
        self.assertEqual(att["call"], rows[0]["call"])
        self.assertEqual(att["requested_model"], rows[0]["model"])
        self.assertEqual(att["retry"], False)
        self.assertEqual(att["reserved_output_tokens"], 11000)
        self.assertTrue(att["raw_response"])
        self.assertEqual(att["raw_response_sha256"], hashlib.sha256(
            att["raw_response"].encode("utf-8")).hexdigest())
        self.assertEqual(att["parsed_output"]["score"], 0.5)
        self.assertIn("usage", att)
        self.assertEqual(att["returned_provider"],
                         runner.EXPECTED_PROVIDERS[rows[0]["model"]][0])
        # score-blind sidecar: score key omitted, every prose field verbatim
        side = json.loads(runner.sidecar_path(run_dir, 1).read_text(
            encoding="utf-8"))
        self.assertNotIn("score", side["output"])
        for f in ("status", "why", "evidence_ids", "discovery",
                  "direct_harms", "scope_triggers", "uncertainty"):
            self.assertEqual(side["output"][f], att["parsed_output"][f])
        self.assertEqual(
            side["frozen_dossier"]["user_message_sha256"],
            att["user_message_sha256"])
        # the runner never writes a review directory (never authors a PASS)
        self.assertFalse((run_dir / runner.REVIEW_REL_DIR).exists())
        # invocation result: completed ONE call, paused for review
        result = json.loads((run_dir / "result.json").read_text(
            encoding="utf-8"))
        self.assertEqual(result["status"], "completed")
        self.assertIsNone(result["stop_reason"])
        self.assertEqual(result["stage_state"],
                         "paused_pending_semantic_review")
        self.assertIn("PASS", result["next_dispatch_requires"])
        # persisted stop list includes the empty-sentinel terminal rule
        self.assertTrue(any("empty-dossier sentinel" in s for s in
                            result["stop_conditions"]),
                        result["stop_conditions"])
        self.assertEqual(result["attempted_calls"], [1])
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(result["stage_total_attempts"], 1)
        self.assertEqual(Decimal(result["used_usd"]), Decimal("0.0005"))
        self.assertEqual(
            Decimal(result["shared_usd_total"]),
            Decimal("0.001993276") + Decimal("0.0005"))
        self.assertIsInstance(result["used_usd"], str)
        self.assertIsNone(result["unreconciled_liability"])
        run_doc = json.loads((run_dir / "run.json").read_text(
            encoding="utf-8"))
        ckpt = run_doc["dispatch_checkpoint"]
        self.assertEqual(ckpt["max_attempts_per_invocation"], 1)
        self.assertEqual(ckpt["prior_stage_attempts"], 0)
        self.assertEqual(ckpt["dispatched_call"], 1)
        self.assertEqual(ckpt["prior_semantic_reviews"], [])
        self.assertEqual(run_doc["cache_policy"], runner.CACHE_POLICY)
        self.assertEqual(run_doc["stage_prior"]["attempts"], 0)
        self.assertFalse((self.tmp / "shared.lock").exists(),
                         "shared lock must be released after the invocation")

    def test_full_stage_20_invocations_sequential_next_cell(self):
        # The STRICT per-answer flow end to end: 20 invocations, exactly one
        # NEXT cell each, a PASS review between them, every output preserved,
        # the runner never writing a review, and exact shared accounting.
        write_fixture_receipt(self.tmp)
        rows = json.loads((HERE / "frozen" / "schedule.json")
                          .read_text(encoding="utf-8"))["rows"]
        written_by_runner = []
        orig_write = runner.write_exclusive

        def recorder(path, text):
            written_by_runner.append(str(path))
            return orig_write(path, text)

        runner.write_exclusive = recorder
        stage_total = Decimal(0)
        try:
            for row in rows:
                rc, out, transport = invoke(self.tmp,
                                            f"inv-{row['call']:02d}", [None])
                self.assertEqual(rc, runner.EXIT_OK,
                                 f"call {row['call']}: {out}")
                self.assertEqual(len(transport.calls), 1,
                                 "exactly one call per invocation")
                self.assertEqual(transport.left, 0)
                run_dir = self.tmp / "runs" / f"inv-{row['call']:02d}"
                att = json.loads((run_dir / "attempts" /
                                  f"call-{row['call']:03d}.json")
                                 .read_text(encoding="utf-8"))
                # sequential: the NEXT cell only, never a skip or repeat
                self.assertEqual(att["call"], row["call"])
                self.assertEqual(att["requested_model"], row["model"])
                self.assertTrue(att["raw_response"])
                self.assertIn("usage", att)
                self.assertIn("parsed_output", att)
                self.assertTrue(runner.sidecar_path(
                    run_dir, row["call"]).is_file())
                res = json.loads((run_dir / "result.json").read_text(
                    encoding="utf-8"))
                self.assertEqual(res["stage_state"],
                                 ("stage_attempts_complete"
                                  if row["call"] == 20
                                  else "paused_pending_semantic_review"))
                stage_total += Decimal(res["used_usd"])
                # an independent PASS review lands between invocations
                # (written by the TEST, never by the runner)
                write_fixture_review(run_dir, row["call"])
        finally:
            runner.write_exclusive = orig_write
        # never a review path written by runner code (no forged/auto PASS)
        self.assertTrue(all("semantic-reviews" not in p
                            for p in written_by_runner),
                        written_by_runner)
        # 20 attempts total, calls 1..20 exactly once each
        seen_calls = []
        for d in sorted((self.tmp / "runs").iterdir()):
            seen_calls += [int(f.stem.split("-")[1]) for f in
                           sorted((d / "attempts").glob("*.json"))]
        self.assertEqual(sorted(seen_calls), list(range(1, 21)))
        # exact shared USD across invocations (no rounding)
        self.assertEqual(stage_total, Decimal("0.01"))
        self.assertEqual(Decimal("0.001993276") + stage_total,
                         Decimal("0.011993276"))
        # the next invocation recorded the actual reviewer identity/session
        # and the review file hash of the verified PASS (audited, not forged)
        run2 = json.loads((self.tmp / "runs" / "inv-02" / "run.json")
                          .read_text(encoding="utf-8"))
        attests = run2["dispatch_checkpoint"]["prior_semantic_reviews"]
        self.assertEqual(len(attests), 1)
        self.assertEqual(attests[0]["call"], 1)
        self.assertEqual(attests[0]["verdict"], "PASS")
        self.assertEqual(attests[0]["reviewer"]["name"],
                         "fixture-reviewer")
        self.assertEqual(attests[0]["reviewer"]["session"],
                         "fixture-session-2b030de8")
        self.assertRegex(attests[0]["review_sha256"], r"^[0-9a-f]{64}$")
        # a 21st invocation refuses: stage complete, before price/secret
        t21 = Transport()
        cfg = fixture_cfg(self.tmp, t21, run_id="inv-21")
        plog = []
        cfg["price_fetch"] = not_called("price_fetch", plog)
        rc, out = quiet(runner.run, cfg)
        self.assertEqual(rc, runner.EXIT_GATE, out)
        self.assertIn("stage one complete", out)
        self.assertEqual(t21.calls, [])
        self.assertEqual(plog, [])

    def test_first_failure_stops_immediately_no_retry(self):
        modes = {
            "malformed json": [(200, "{oops")],
            "empty content": [(200, provider_body(
                runner.MODELS[0], content=""))],
            "truncated finish": [(200, provider_body(
                runner.MODELS[0], finish="length"))],
            "api error http": [(502, "upstream error")],
            "error object": [(200, json.dumps(
                {"error": {"message": "quota"}}))],
            "model substitution": [(200, provider_body(runner.MODELS[1]))],
            "unexpected routing": [(200, provider_body(
                runner.MODELS[0], provider="SomeoneElse"))],
            "cache write unreconcilable": [(200, provider_body(
                runner.MODELS[0],
                usage=default_usage(
                    prompt_tokens_details={"cached_tokens": 0,
                                           "cache_write_tokens": 3})))],
            "reasoning over completion": [(200, provider_body(
                runner.MODELS[0],
                usage=default_usage(
                    completion_tokens_details={"reasoning_tokens": 9999})))],
            "byok billing": [(200, provider_body(
                runner.MODELS[0], usage=default_usage(is_byok=True)))],
            "missing cost": [(200, provider_body(
                runner.MODELS[0],
                usage={k: v for k, v in default_usage().items()
                       if k != "cost"}))],
            "zero cost": [(200, provider_body(
                runner.MODELS[0], usage=default_usage(cost=0)))],
            "cost over reservation": [(200, provider_body(
                runner.MODELS[0], usage=default_usage(cost=99)))],
            "totals mismatch": [(200, provider_body(
                runner.MODELS[0],
                usage=default_usage(total_tokens=999999)))],
            "billed output over cap": [(200, provider_body(
                runner.MODELS[0],
                usage=default_usage(completion_tokens=11001,
                                    total_tokens=51001,
                                    completion_tokens_details={
                                        "reasoning_tokens": 6000})))],
            "invalid contract": [(200, provider_body(
                runner.MODELS[0],
                content='{"status": "ok", "score": 2.0}'))],
            "prose around json": [(200, provider_body(
                runner.MODELS[0],
                content="My answer is 0.5. " + CONTRACT_OK))],
        }
        for name, script in modes.items():
            with self.subTest(mode=name):
                tmp = Path(tempfile.mkdtemp(prefix="fail-", dir=str(TMPROOT)))
                try:
                    build_fixture(tmp)
                    write_fixture_receipt(tmp)
                    transport = Transport(script)
                    cfg = fixture_cfg(tmp, transport,
                                      run_id="stage1-fixture")
                    rc, out = quiet(runner.run, cfg)
                    self.assertEqual(rc, runner.EXIT_STOPPED, f"{name}: {out}")
                    self.assertEqual(len(transport.calls), 1, name)
                    att = sorted((tmp / "runs" / "stage1-fixture" /
                                  "attempts").glob("*.json"))
                    self.assertEqual(len(att), 1,
                                     f"{name}: must not attempt a second cell")
                    self.assertEqual(att[0].name, "call-001.json")
                    result = json.loads(
                        (tmp / "runs" / "stage1-fixture" / "result.json")
                        .read_text(encoding="utf-8"))
                    self.assertEqual(result["status"], "stopped")
                    self.assertEqual(result["stage_state"],
                                     "terminal_failure")
                    self.assertEqual(result["attempts"], 1)
                    self.assertTrue(result["stop_reason"])
                    self.assertFalse((tmp / "shared.lock").exists())
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)

    def test_cache_read_accepted_logged_no_request_directive(self):
        # Automatic provider cache READ with valid usage/cost arithmetic is
        # accepted and logged; the request itself carries no cache directive.
        cfg, transport = self._prepared_cfg([
            (200, provider_body(
                runner.MODELS[0],
                usage=default_usage(
                    prompt_tokens_details={"cached_tokens": 50,
                                           "cache_write_tokens": 0})))])
        rc, out = quiet(runner.run, cfg)
        self.assertEqual(rc, runner.EXIT_OK, out)
        self.assertEqual(len(transport.calls), 1)
        blob = json.dumps(transport.calls[0]).lower()
        self.assertNotIn("cache", blob)      # no request cache directive
        att = json.loads((self.tmp / "runs" / "stage1-fixture" /
                          "attempts" / "call-001.json").read_text(
            encoding="utf-8"))
        self.assertEqual(att["cache_usage"]["cached_read_tokens"], 50)
        self.assertEqual(att["cache_usage"]["cache_write_tokens"], 0)
        self.assertIn("no reproducibility claim", att["cache_usage"]["note"])
        self.assertEqual(
            att["usage"]["prompt_tokens_details"]["cached_tokens"], 50)
        result = json.loads((self.tmp / "runs" / "stage1-fixture" /
                             "result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["stage_state"],
                         "paused_pending_semantic_review")

    def test_unknown_charge_records_liability_and_blocks_next_run(self):
        cfg, transport = self._prepared_cfg([(200, provider_body(
            runner.MODELS[0],
            usage={k: v for k, v in default_usage().items()
                   if k != "cost"}))])
        rc, out = quiet(runner.run, cfg)
        self.assertEqual(rc, runner.EXIT_STOPPED)
        result = json.loads((self.tmp / "runs" / "stage1-fixture" /
                             "result.json").read_text(encoding="utf-8"))
        self.assertIsInstance(result["unreconciled_liability"], dict)
        attempt = json.loads(
            (self.tmp / "runs" / "stage1-fixture" / "attempts" /
             "call-001.json").read_text(encoding="utf-8"))
        self.assertIsNone(attempt["billed_on_failure"]["cost"])
        # a later invocation (new run id) must refuse on the liability,
        # before any call
        transport2 = Transport()
        cfg2 = fixture_cfg(self.tmp, transport2, run_id="stage1-again")
        cfg2["price_fetch"] = not_called("price_fetch", [])
        rc2, out2 = quiet(runner.run, cfg2)
        self.assertEqual(rc2, runner.EXIT_GATE, out2)
        self.assertIn("liability", out2)
        self.assertEqual(transport2.calls, [])

    def test_abstention_allowed_for_core_and_score_blind(self):
        # A core cell may abstain under the unchanged contract; no score is
        # ever forced, and the sidecar stays score-blind either way.
        cfg, transport = self._prepared_cfg(
            [lambda p: provider_body(p["model"],
                                     content=CONTRACT_ABSTAIN), None])
        rc, out = quiet(runner.run, cfg)
        self.assertEqual(rc, runner.EXIT_OK, out)
        self.assertEqual(len(transport.calls), 1)   # still one call only
        run_dir = self.tmp / "runs" / "stage1-fixture"
        attempt = json.loads((run_dir / "attempts" / "call-001.json")
                             .read_text(encoding="utf-8"))
        self.assertIsNone(attempt["parsed_output"]["score"])
        self.assertEqual(attempt["parsed_output"]["status"],
                         "insufficient_evidence")
        side = json.loads(runner.sidecar_path(run_dir, 1).read_text(
            encoding="utf-8"))
        self.assertNotIn("score", side["output"])
        self.assertEqual(side["output"]["status"],
                         "insufficient_evidence")
        result = json.loads((run_dir / "result.json").read_text(
            encoding="utf-8"))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["stage_state"],
                         "paused_pending_semantic_review")

    def test_empty_sentinel_returning_score_is_terminal_stop(self):
        # Invocation 1: core call 1 scores -> paused; independent PASS review
        # recorded. Invocation 2: schedule call 2 is the first EMPTY sentinel;
        # a scored answer instead of abstention is a TERMINAL stop.
        write_fixture_receipt(self.tmp)
        rc1, out1, t1 = invoke(self.tmp, "first", [None])
        self.assertEqual(rc1, runner.EXIT_OK, out1)
        write_fixture_review(self.tmp / "runs" / "first", 1)
        rc2, out2, t2 = invoke(
            self.tmp, "second",
            [lambda p: provider_body(p["model"], content=CONTRACT_OK)])
        self.assertEqual(rc2, runner.EXIT_STOPPED, out2)
        self.assertEqual(len(t2.calls), 1)
        attempt2 = json.loads(
            (self.tmp / "runs" / "second" / "attempts" /
             "call-002.json").read_text(encoding="utf-8"))
        self.assertEqual(attempt2["sentinel"], "empty")
        self.assertIn("empty-dossier sentinel", attempt2["stop_reason"])
        # raw bytes preserved verbatim; the score is never parsed out of them
        raw = json.loads(attempt2["raw_response"])
        content = raw["choices"][0]["message"]["content"]
        self.assertEqual(json.loads(content)["score"], 0.5)
        self.assertNotIn("parsed_output", attempt2)   # failure-path schema
        result2 = json.loads(
            (self.tmp / "runs" / "second" / "result.json")
            .read_text(encoding="utf-8"))
        self.assertEqual(result2["status"], "stopped")
        self.assertEqual(result2["stage_state"], "terminal_failure")
        self.assertEqual(result2["attempted_calls"], [2])
        self.assertIsNone(result2["unreconciled_liability"])
        # terminal: a third invocation must not dispatch schedule call 3
        t3 = Transport()
        cfg3 = fixture_cfg(self.tmp, t3, run_id="third")
        plog = []
        cfg3["price_fetch"] = not_called("price_fetch", plog)
        rc3, out3 = quiet(runner.run, cfg3)
        self.assertEqual(rc3, runner.EXIT_GATE, out3)
        self.assertIn("FAILED/partial output", out3)
        self.assertEqual(t3.calls, [])
        self.assertEqual(plog, [])


class WriteScopeTests(FixtureCase):
    def test_no_writes_outside_v2_during_a_full_mock_run(self):
        write_fixture_receipt(self.tmp)
        transport = Transport([None])          # one call per invocation
        cfg = fixture_cfg(self.tmp, transport)
        before = repo_snapshot()
        rc, out = quiet(runner.run, cfg)
        after = repo_snapshot()
        self.assertEqual(rc, runner.EXIT_OK, out)
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(before, after,
                         "a mock invocation must not touch any repo file "
                         "outside country-feasibility-v2")


class V1PreservedTests(unittest.TestCase):
    def test_v1_tree_byte_identical(self):
        self.assertEqual(tree_digest(V1_ROOT),
                         (V1_TREE_DIGEST, V1_TREE_FILES))

    def test_rule_contrasts_tree_byte_identical(self):
        self.assertEqual(tree_digest(V1_ROOT.parent / "rule-contrasts"),
                         (RC_TREE_DIGEST, RC_TREE_FILES))

    def test_data_countries_pinned(self):
        self.assertEqual(
            hashlib.sha256((REPO / "data" / "countries.json")
                           .read_bytes()).hexdigest(),
            DATA_COUNTRIES_PIN)

    def test_live_v1_source_records_verify(self):
        runner.verify_v1_source_files(V1_ROOT)     # raises on any drift

    def test_default_lock_lives_in_v1_directory(self):
        self.assertEqual(runner.DEFAULT_LOCK_PATH.parent, V1_ROOT)
        self.assertEqual(runner.DEFAULT_LOCK_PATH.name, ".execution.lock")


def tearDownModule():
    shutil.rmtree(TMPROOT, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)