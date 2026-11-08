#!/usr/bin/env python3
"""Disabled-by-default provider runner for the country-feasibility pilot.

OFFLINE BY DEFAULT. This module does nothing unless it is invoked with an
explicit ``--execute`` flag AND a reviewed amended receipt whose recorded
hashes equal the current SHA-256 of every bound input. Without both gates it
never reads a credential, never resolves a hostname, never opens a socket and
never writes a byte (``main([])`` prints usage and exits 2).

Execution gates, in order, all fail-closed:

  1. explicit ``--execute`` flag (no credential may be passed on the CLI);
  2. valid ``--run-id`` (path-safe; scoring ids must not exist, probe ids are the
     FOUR registered slots ``probe-1``/``probe-2`` (originals, already executed:
     probe-1 completed, probe-2 FAILED at 64 output tokens with a known charge)
     and ``probe-3``/``probe-4`` (adaptive follow-ups,
     ``probe-followup-amendment.md``));
  3. frozen-input self-check: every frozen file still matches the hashes in
     ``frozen/manifest.json`` (source/hash drift -> stop);
  4. amended execution receipt ``probe_followup_receipt.json`` schema v4: exact
     binding of the frozen inputs, the amended ``runner.py``,
     ``budget-amendment.md``, ``probe-amendment.md``,
     ``probe-followup-amendment.md``, the feasibility-only exploratory amendment
     (``evidence-preflight-amendment.md``), the exact preflight procedure
     (``preflight.md``), a DISTINCT claim-level sign-off artifact
     (``preflight-signoff.md``, content-bound, not a path string), the ARCHIVAL
     original ``preflight_receipt.json`` bytes (schema v3, immutable, never the
     execution receipt again), ``data/countries.json`` and the independent
     reviews including the adaptive amendment's review
     (``reviews/probe-followup-review.md``). Binding these bytes is not a
     receipt, a sign-off or execution approval and weakens no other gate.
     Provider usage/pricing semantics must be DOCUMENTED (with sources) with
     live behavior ``unobserved`` or ``observed_in_bounded_probe`` and the
     residual assumptions listed - there is deliberately NO ``verified`` flag.
     An observed record hash-binds ALL FOUR probe results and reviews (eight
     entries: the exact old + new evidence) plus the structured
     ``original_failure`` disclosure of the failed original slot;
  5. EXPERIMENT-WIDE EXCLUSIVE LOCK (``.execution.lock``): acquired BEFORE any
     prior state is read or any budget decision is taken and held through all
     dispatch and finalization. Contention refuses before any call; a lock left by
     a crash is NEVER deleted automatically - a human must inspect and remove it;
  6. prior-run + probe ledger: an unreconciled liability (run OR probe), an
     unknown prior state (e.g. a crash-incomplete run/probe with no terminal
     record), or any predeclared cell already attempted blocks a new run (no
     silent budget or schedule reset); reconciliation is a human record we never
     write and evidence is never deleted;
  7. probe gates: no probe may dispatch while any original or prior record is
     missing, unknown or unreconciled; adaptive follow-ups additionally require
     the intact original evidence chain (pinned archived statuses: probe-1
     ``completed``, probe-2 ``stopped`` - the failed slot is never re-labelled),
     the frozen slot order and a COMPLETED earlier follow-up: **any follow-up
     failure ends the phase** - no remaining follow-up may dispatch (refused
     before price fetch, credential read and transport) and scoring stays
     blocked. Scoring requires all four slots dispatched,
     original evidence preserved with the original failure truthfully disclosed,
     BOTH follow-up slots successful and independently reviewed, plus the
     structured slot reviews (probe-2's must CONFIRM the failure - never a
     success attestation); probes count in the same ledger (44 total dispatches
     = 40 scoring + 4 probes; same USD 10 ceiling);
  8. budget plan: input reservation = UTF-8 byte count of the frozen prompt +
     message + a fixed 128-unit chat-framing allowance per call, checked against
     the PRE-OUTCOME administrative reservation ceilings (70,000/call,
     2,400,000 aggregate - budget-amendment.md). Administrative reservation units
     under stated tokenizer/framing assumptions, NOT proven provider-native token
     bounds. The original 20,000/800,000 proposal stays recorded and still stops
     the run if BILLING exceeds it. If the plan does not fit, this runner STOPS
     AND REPORTS - it never raises a ceiling;
  9. price metadata fetched over fixed HTTPS with an explicit timeout, only for
     the exact pre-registered models; unknown / negative / non-finite prices
     refuse; prior used (runs + probes) + worst-case monetary reservation must fit
     the locally enforced USD 10.00 ceiling (not a provider-enforced spend limit);
 10. credential read from the environment (never logged, never on the CLI).

Each call is a fresh single system+user context built only from the frozen
prompt/message bytes: no dynamic input, no other country's data, no map scores
or sub-national values, no fallback model list, no cache directives, no retries
and one attempt per predeclared cell (40 attempted requests maximum including
failures, sequential). FOUR fixed non-country operational probes total - the two
originals (``--probe``, pre-registered in ``probe-amendment.md``, executed:
probe-1 completed, probe-2 failed with a known charge and is never retried or
called successful) and exactly one adaptive follow-up per model
(``probe-3``/``probe-4``, ``probe-followup-amendment.md``: identical fixed
messages/settings except max output = the scoring setting 2000, one dispatch
per slot, no automatic retries, no further slots) - may precede scoring; probes
and scoring share one ledger, one lock and the same USD 10.00 ceiling (covering
all original and future probe charges and all failures), for 44 total
dispatches maximum. Probes test transport/schema/usage ONLY and make no claim
about future provider behavior, token bounds or scoring validity. Every attempt
is written once (exclusive create) under ``runs/<run-id>/`` (probes under
``probes/<slot>/``) and never appended to; the only writes outside a run
directory are the ``runs/``/``probes/`` containers, the experiment-wide
``.execution.lock`` and nothing else. Raw response bytes, finish reason,
requested and returned model/provider, timestamp, full usage, errors,
prompt/message hashes and the receipt binding are preserved verbatim. Outputs
must satisfy the frozen single-score JSON contract; malformed content stops the
run and the raw output is retained. On a failed dispatch any parseable billed
usage/cost is recorded separately from the validated fields, and an unknown
charge is recorded as an unreconciled liability that blocks any new run until a
human-reviewed reconciliation record exists.

    python3 runner.py                         # disabled: usage + exit 2
    python3 runner.py --execute --run-id r1   # full gate chain; stops on any gate
    python3 runner.py --execute --probe --run-id probe-3   # one registered probe

The original two probes WERE dispatched from this directory under the original
protocol (probe-1 completed; probe-2 FAILED with a known charge; archived
under ``probes/probe-{1,2}/`` as immutable evidence); no scoring attempt has
ever been dispatched. Scoring and follow-up dispatch gates refuse until an
independent reviewer signs ``probe_followup_receipt.json`` documenting the
provider semantics AND - for scoring - recording the bounded-probe observation
over all four probes with recomputed hashes and the original-failure
disclosure. This worker creates or signs no receipt, no sign-off artifact and no
probe review, and runs no provider call or probe.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]

# Fixed provider endpoint (HTTPS only, not configurable from the CLI).
API_BASE = "https://openrouter.ai/api/v1"
CHAT_URL = API_BASE + "/chat/completions"
MODELS_URL = API_BASE + "/models"
TIMEOUT_SECONDS = 30.0            # explicit timeout for every request incl. price fetch
SECRET_ENV = "OPENROUTER_API_KEY"  # the ONLY credential source; never logged

# Pre-registered models (exact ids only; no fallback, no substitution).
MODELS = ("deepseek/deepseek-v4.1-flash", "google/gemini-3.8-flash")
# Requested settings (frozen; must match the manifest or execution refuses).
REQUESTED_SETTINGS = {"temperature": 1.0, "top_p": 1.0, "max_output_tokens": 2000}

# Declared ceilings this runner enforces (never raises them).
ATTEMPT_CEILING = 40
MAX_USD = 10.00
# Input reservation arithmetic (budget-amendment.md). One reservation unit = one
# UTF-8 byte of the frozen prompt+message, plus a fixed 128-unit chat-framing
# allowance per call. HONEST LABEL: these are administrative reservation units
# that are conservative ONLY under the stated assumptions (the provider bills
# the serialized message bytes plus <= 128 units of framing; byte-level
# tokenizers never emit more tokens than bytes of text). They are NOT proven
# provider-native token bounds and NOT a provider-enforced spend limit; billed
# usage above its reservation stops the run fail-closed. chars/3.5-style
# estimates are deliberately NOT used.
BYTES_PER_TOKEN = 1
FIXED_OVERHEAD_TOKENS_PER_CALL = 128
# Pre-outcome reservation amendment: must equal frozen/manifest.json ->
# reservation_amendment and the renderer constants, else execution refuses.
RESERVATION_PER_CALL_UNITS = 70_000
RESERVATION_AGGREGATE_UNITS = 2_400_000
# The original proposal stays recorded AND stays an in-run stop rule on billed
# native tokens (dispatch reservation uses the amendment ceilings above).
PRESERVED_PROPOSED_INPUT_CAPS = {"per_call_max_input_tokens": 20_000,
                                 "aggregate_max_input_tokens": 800_000}
RECEIPT_VERSION = 4           # amended execution receipt (probe_followup_receipt.json)
ARCHIVAL_RECEIPT_VERSION = 3  # original preflight_receipt.json: archival, immutable
RECEIPT_NAME = "probe_followup_receipt.json"       # separately named amended receipt
ARCHIVAL_RECEIPT_NAME = "preflight_receipt.json"   # original receipt, never the
                                                   # execution receipt again
# Probe slots: the TWO original pre-registered probes (probe-amendment.md,
# already executed: probe-1 completed, probe-2 FAILED at 64 output tokens with a
# known charge) plus the TWO adaptive follow-up slots (probe-followup-amendment.md:
# exactly one fixed non-country probe per original model, identical messages and
# settings except max output raised to the actual scoring setting 2000). One
# dispatch per slot ever, no retry, no further slots; all four share the SAME
# local USD 10 ledger as scoring; total dispatch ceiling = 40 scoring attempts
# + 4 probes = 44. Probes test transport/schema/usage ONLY and never become
# scores.
ORIGINAL_PROBE_SLOTS = ("probe-1", "probe-2")
FOLLOWUP_PROBE_SLOTS = ("probe-3", "probe-4")
PROBE_SLOTS = ORIGINAL_PROBE_SLOTS + FOLLOWUP_PROBE_SLOTS
PROBE_SLOT_MODELS = {"probe-1": MODELS[0], "probe-2": MODELS[1],
                     "probe-3": MODELS[0], "probe-4": MODELS[1]}
PROBE_CEILING = 4
TOTAL_DISPATCH_CEILING = ATTEMPT_CEILING + PROBE_CEILING      # 44
# The archived, independently reviewed outcomes of the ORIGINAL probes. These
# are pinned facts of the executed original phase: the failed slot is never
# re-labelled a success (and never treated as one) and the completed slot is
# never re-labelled; scoring never requires a success status for probe-2.
ORIGINAL_PROBE_STATUSES = {"probe-1": "completed", "probe-2": "stopped"}
ORIGINAL_FAILURE_SLOT = "probe-2"
PROBE_SYSTEM = ('Reply with only this JSON object and no other text: '
                '{"probe": "ok"}')
PROBE_USER = ("Operational transport, schema and usage probe. This is not an "
              "assessment request: it contains no jurisdiction, evidence or "
              "rating content, and no output of it is used as a result.")
# Original probe settings (archived in probes/probe-{1,2}/dispatch.json) vs the
# adaptive follow-up settings: IDENTICAL except max output = the actual scoring
# setting (2000), per probe-followup-amendment.md.
PROBE_SETTINGS = {"temperature": 0.0, "top_p": 1.0, "max_output_tokens": 64}
# 2000 = the actual scoring setting (REQUESTED_SETTINGS["max_output_tokens"] /
# RESERVED_OUTPUT_TOKENS_PER_CALL, defined below; asserted equal in tests).
FOLLOWUP_PROBE_SETTINGS = {"temperature": 0.0, "top_p": 1.0,
                           "max_output_tokens": 2000}
PROBE_MAX_OUTPUT_TOKENS = 64
FOLLOWUP_PROBE_MAX_OUTPUT_TOKENS = 2000
PROBE_SLOT_SETTINGS = {slot: (PROBE_SETTINGS if slot in ORIGINAL_PROBE_SLOTS
                              else FOLLOWUP_PROBE_SETTINGS)
                       for slot in PROBE_SLOTS}
PROBE_SLOT_MAX_OUTPUT = {slot: (PROBE_MAX_OUTPUT_TOKENS
                                if slot in ORIGINAL_PROBE_SLOTS
                                else FOLLOWUP_PROBE_MAX_OUTPUT_TOKENS)
                         for slot in PROBE_SLOTS}
# Structured review statuses (probe-review-policy.md for successful probes;
# probe-followup-amendment.md adds the failure confirmation status for the
# original failed slot). reviews are human/reviewer artifacts the runner only
# verifies - it never writes one.
REVIEW_OK_STATUS = "reviewed_ok"
REVIEW_FAILURE_STATUS = "reviewed_failure"   # independent review confirming an
                                              # archived FAILED probe; never a
                                              # success attestation
REVIEW_FIELDS = ("probe_slot", "reviewed_by", "reviewed_at", "statement")
# Declared probe token allowance (probe-amendment.md as amended by
# probe-followup-amendment.md): probes share the USD 10 ledger and the
# 44-dispatch ceiling; their token usage is recorded in the same ledger but
# counted against THIS declared probe allowance rather than the 40-call scoring
# reservation ceilings (which are sized exactly for the frozen schedule).
# Input: all four probes carry byte-identical messages. Output: originals
# reserved 64+64, follow-ups reserved 2000+2000 = 4128 total.
PROBE_INPUT_ALLOWANCE_UNITS = PROBE_CEILING * (
    len(PROBE_SYSTEM.encode("utf-8")) + len(PROBE_USER.encode("utf-8"))
    + FIXED_OVERHEAD_TOKENS_PER_CALL)
PROBE_OUTPUT_ALLOWANCE_TOKENS = (2 * PROBE_MAX_OUTPUT_TOKENS
                                 + 2 * FOLLOWUP_PROBE_MAX_OUTPUT_TOKENS)  # 4128
# Experiment-wide exclusive lock: file-based so contention is detected across
# processes; never deleted automatically (a crash leaves it for a human).
LOCK_NAME = ".execution.lock"
PROBES_DIR = "probes"
# Frozen single-score JSON output contract (derived prompts, "## Output format").
OUTPUT_CONTRACT_FIELDS = ("why", "evidence_ids", "discovery", "direct_harms",
                          "scope_triggers", "uncertainty")
OUTPUT_STATUSES = ("ok", "insufficient_evidence")
# Worst-case billed output + reasoning reserved per call (frozen setting).
RESERVED_OUTPUT_TOKENS_PER_CALL = 2000

RUNS_DIR = "runs"
# RECEIPT_NAME (amended execution receipt) and ARCHIVAL_RECEIPT_NAME (original,
# archival preflight_receipt.json) are declared with the receipt constants above.
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

# Files whose hashes the receipt must bind (label -> path is derived per root).
BINDING_LABELS = (
    "frozen/manifest.json",
    "frozen/single_a.txt",
    "frozen/single_b.txt",
    "frozen/schedule.json",
    "frozen/user_messages.json",
    "frozen/packets/USA.txt",
    "frozen/packets/GBR.txt",
    "frozen/packets/NPL.txt",
    "frozen/packets/VAT.txt",
    "ledger.json",
    "runner.py",
    "budget-amendment.md",
    "probe-amendment.md",
    "probe-review-policy.md",
    "probe-followup-amendment.md",
    ARCHIVAL_RECEIPT_NAME,
    "preflight.md",
    "preflight-signoff.md",
    "evidence-preflight-amendment.md",
    "data/countries.json",
)
# Durable copies of the independent reviews; the receipt binds their content.
# The follow-up review is the durable local copy of the reviewer's written-preflight
# compliance follow-up that motivates the feasibility-only amendment; binding its
# bytes is not a sign-off and creates no receipt.
EVIDENCE_REVIEW_PATH = HERE / "reviews" / "evidence-review.md"
BUDGET_REVIEW_PATH = HERE / "reviews" / "budget-review.md"
EVIDENCE_PREFLIGHT_FOLLOWUP_PATH = HERE / "reviews" / "evidence-preflight-followup.md"
PREFLIGHT_AMENDMENT_REVIEW_PATH = HERE / "reviews" / "preflight-amendment-review.md"
PREFLIGHT_ADOPTION_REVIEW_PATH = HERE / "reviews" / "preflight-adoption-review.md"
PROBE_POLICY_REVIEW_PATH = HERE / "reviews" / "probe-policy-review.md"
PROBE_POLICY_FINAL_REVIEW_PATH = HERE / "reviews" / "probe-policy-final-review.md"
RUNNER_GATE_REVIEW_PATH = HERE / "reviews" / "runner-gate-review.md"
ORIGINAL_PROBE_REVIEW_PATH = HERE / "reviews" / "probe-initial-review.md"
FOLLOWUP_ORIGINAL_BLOCK_PATH = HERE / "reviews" / "probe-followup-original-block.md"
FOLLOWUP_LIVE_BLOCK_PATH = HERE / "reviews" / "probe-followup-live-block.md"
PROBE_PROTOCOL_REVIEW_PATH = HERE / "reviews" / "probe-protocol-review.md"
PROBE_HASH_AUDIT_PATH = HERE / "reviews" / "probe-hash-audit.md"
PROBE_SLOT_ATTESTATIONS_PATH = HERE / "reviews" / "probe-slot-attestations.json"
PROBE_SLOT_RUNTIME_STATUS_PATH = HERE / "reviews" / "probe-slot-runtime-status.json"
PILOT_FINAL_PROTOCOL_BLOCK_PATH = HERE / "reviews" / "pilot-final-protocol-block.md"
PILOT_FINAL_ATTRIBUTION_REVIEW_PATH = HERE / "reviews" / "pilot-final-attribution-review.md"
PILOT_FINAL_HASH_GATE_PATH = HERE / "reviews" / "pilot-final-hash-gate.md"
BLOCKED_OBSERVATION_RECEIPT_PATH = HERE / "reviews" / "scoring-observation-receipt-blocked.json"
# Independent review of the ADAPTIVE follow-up amendment (must exist before any
# follow-up dispatch; relative paths resolve under the experiment root so the
# runner verifies the durable copy in the active experiment directory). The
# worker never creates it - without these bytes every receipt build and every
# execution refuses fail-closed.
PROBE_FOLLOWUP_REVIEW_LABEL = "independent-probe-followup-review"
PROBE_FOLLOWUP_REVIEW_REL = "reviews/probe-followup-review.md"
REVIEW_BINDINGS = (("independent-evidence-review", EVIDENCE_REVIEW_PATH),
                   ("independent-budget-review", BUDGET_REVIEW_PATH),
                   ("independent-evidence-preflight-followup",
                    EVIDENCE_PREFLIGHT_FOLLOWUP_PATH),
                   ("independent-preflight-amendment-review",
                    PREFLIGHT_AMENDMENT_REVIEW_PATH),
                   ("independent-preflight-adoption-review",
                    PREFLIGHT_ADOPTION_REVIEW_PATH),
                   ("independent-probe-policy-review", PROBE_POLICY_REVIEW_PATH),
                   ("independent-probe-policy-final-review", PROBE_POLICY_FINAL_REVIEW_PATH),
                   ("independent-runner-gate-review", RUNNER_GATE_REVIEW_PATH),
                   ("independent-original-probe-review", ORIGINAL_PROBE_REVIEW_PATH),
                   ("independent-followup-original-block", FOLLOWUP_ORIGINAL_BLOCK_PATH),
                   ("independent-followup-live-block", FOLLOWUP_LIVE_BLOCK_PATH),
                   ("independent-probe-protocol-review", PROBE_PROTOCOL_REVIEW_PATH),
                   ("independent-probe-hash-audit", PROBE_HASH_AUDIT_PATH),
                   ("independent-probe-slot-attestations", PROBE_SLOT_ATTESTATIONS_PATH),
                   ("probe-slot-runtime-status", PROBE_SLOT_RUNTIME_STATUS_PATH),
                   ("independent-pilot-final-protocol-block", PILOT_FINAL_PROTOCOL_BLOCK_PATH),
                   ("independent-pilot-final-attribution-review", PILOT_FINAL_ATTRIBUTION_REVIEW_PATH),
                   ("independent-pilot-final-hash-gate", PILOT_FINAL_HASH_GATE_PATH),
                   ("blocked-observation-receipt", BLOCKED_OBSERVATION_RECEIPT_PATH),
                   (PROBE_FOLLOWUP_REVIEW_LABEL, PROBE_FOLLOWUP_REVIEW_REL))
# Exactly these request fields are ever sent: no fallback list, no cache control.
REQUEST_KEYS = ("model", "messages", "temperature", "top_p", "max_tokens",
                "stream", "usage", "provider")

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_GATE = 3      # refused before any request
EXIT_STOPPED = 4   # refused during the run; recorded under runs/<id>


class Refusal(Exception):
    def __init__(self, code: int, reason: str):
        super().__init__(reason)
        self.code = code
        self.reason = reason


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_exclusive(path: Path, text: str) -> None:
    """Create-once write: never overwrites, never appends."""
    with path.open("x", encoding="utf-8") as fh:
        fh.write(text)


# --------------------------------------------------------------------------- #
# CLI (no credential parameter exists, unknown flags are rejected)
# --------------------------------------------------------------------------- #

def usage() -> str:
    return ("usage: runner.py [--execute [--probe] --run-id ID "
            "[--receipt PATH]]\n"
            "  disabled by default: without --execute this module performs no\n"
            "  network access, reads no credential and writes nothing;\n"
            "  --probe dispatches ONE registered non-country probe "
            "(probe-1/probe-2 originals, probe-3/probe-4 adaptive "
            "follow-ups);\n"
            "  credentials are read only from the "
            f"{SECRET_ENV} environment variable (never from the CLI)")


def parse_args(argv) -> dict:
    opts = {"execute": False, "receipt": None, "run_id": None, "probe": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        key, eq, val = a.partition("=")
        if key == "--execute" and not eq:
            opts["execute"] = True
        elif key == "--probe" and not eq:
            opts["probe"] = True
        elif key in ("--receipt", "--run-id"):
            if not eq:
                i += 1
                if i >= len(argv):
                    raise Refusal(EXIT_USAGE, f"{key} requires a value")
                val = argv[i]
            if not val:
                raise Refusal(EXIT_USAGE, f"{key} requires a value")
            opts["receipt" if key == "--receipt" else "run_id"] = val
        else:
            low = key.lower()
            if any(t in low for t in ("key", "token", "secret", "credential",
                                      "password")):
                raise Refusal(EXIT_USAGE,
                              "credentials may never be passed on the command "
                              f"line ({key} rejected); the runner reads "
                              f"{SECRET_ENV} from the environment only under "
                              "--execute")
            raise Refusal(EXIT_USAGE, f"unknown argument: {key}")
        i += 1
    return opts


def validate_run_id(run_id: str, root: Path) -> Path:
    if not run_id:
        raise Refusal(EXIT_USAGE, "--run-id is required with --execute")
    if not RUN_ID_RE.match(run_id) or ".." in run_id:
        raise Refusal(EXIT_GATE,
                      f"invalid run id {run_id!r}: must match "
                      f"{RUN_ID_RE.pattern} and must not contain '..'")
    runs = root / RUNS_DIR
    run_dir = runs / run_id
    if run_dir.resolve().parent != runs.resolve():
        raise Refusal(EXIT_GATE, f"run id escapes {RUNS_DIR}/: {run_id!r}")
    if run_dir.exists():
        raise Refusal(EXIT_GATE,
                      f"run {run_id!r} already exists - refusing to overwrite "
                      "or append to an existing run")
    return run_dir


def validate_probe_slot(slot, root: Path) -> str:
    """Probe run ids are the FOUR registered slots only (fixed paths): the two
    executed originals and the two adaptive follow-ups; each exists at most once."""
    if slot not in PROBE_SLOTS:
        raise Refusal(EXIT_USAGE,
                      f"--probe requires --run-id in {list(PROBE_SLOTS)}, got "
                      f"{slot!r}")
    probe_dir = root / PROBES_DIR / slot
    if probe_dir.resolve().parent != (root / PROBES_DIR).resolve():
        raise Refusal(EXIT_GATE, f"probe slot escapes {PROBES_DIR}/: {slot!r}")
    if probe_dir.exists():
        raise Refusal(EXIT_GATE,
                      f"probe slot {slot!r} already exists - refusing to overwrite "
                      "or re-dispatch a probe slot")
    return slot


# --------------------------------------------------------------------------- #
# Experiment-wide exclusive execution lock (contention refuses before any call)
# --------------------------------------------------------------------------- #

def acquire_lock(root: Path, holder: str) -> Path:
    """Atomic O_EXCL create of ``.execution.lock`` under the experiment root.

    Must be held BEFORE any prior state is read or budget decided, and through
    dispatch and finalization. Contention -> Refusal (no call is ever made). A
    lock left behind by a crash is reported for HUMAN inspection and is never
    deleted automatically.
    """
    path = root / LOCK_NAME
    payload = json.dumps({"holder": holder, "pid": os.getpid(),
                          "acquired_at": utcnow()}, indent=1) + "\n"
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        try:
            existing = path.read_text(encoding="utf-8").strip()[:300]
        except OSError:
            existing = "<unreadable>"
        raise Refusal(EXIT_GATE,
                      f"experiment execution lock is held: {path} ({existing}). "
                      "Another run/probe may be in progress, or a crash left the "
                      "lock; contention refuses BEFORE any call. A human must "
                      f"inspect and remove {LOCK_NAME} explicitly - this runner "
                      "never deletes a lock it did not acquire")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(payload)
    return path


def release_lock(path: Path, holder: str) -> None:
    """Remove ONLY a lock whose payload matches this holder (ours)."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return                      # unreadable/not ours: never delete blindly
    if doc.get("holder") == holder and doc.get("pid") == os.getpid():
        try:
            path.unlink()
        except OSError:
            pass


# --------------------------------------------------------------------------- #
# Frozen inputs, receipt, plan (all offline)
# --------------------------------------------------------------------------- #

def binding_paths(root: Path, data_path: Path) -> dict:
    # runner.py and the amendments are bound where they live in this module's
    # directory (they are the executable and amendments under review, even when a
    # test fixture uses a different experiment root); the independent reviews are
    # bound to their durable local copies.
    module_owned = {"runner.py": HERE / "runner.py",
                    "budget-amendment.md": HERE / "budget-amendment.md",
                    "probe-amendment.md": HERE / "probe-amendment.md",
                    "probe-review-policy.md": HERE / "probe-review-policy.md",
                    "probe-followup-amendment.md":
                        HERE / "probe-followup-amendment.md",
                    "evidence-preflight-amendment.md":
                        HERE / "evidence-preflight-amendment.md"}
    out = {}
    for label in BINDING_LABELS:
        if label in module_owned:
            out[label] = module_owned[label]
        elif label.startswith("data/"):
            out[label] = data_path
        else:
            out[label] = root / label
    for label, path in REVIEW_BINDINGS:
        out[label] = path if isinstance(path, Path) and path.is_absolute() \
            else root / path          # relative entries resolve in the experiment
    return out


def current_bindings(root: Path, data_path: Path) -> dict:
    out = {}
    for label, path in binding_paths(root, data_path).items():
        if not path.is_file():
            raise Refusal(EXIT_GATE, f"missing input bound by preflight: {label}")
        out[label] = sha(path.read_bytes())
    return out


def verify_frozen(manifest: dict, root: Path, data_path: Path) -> None:
    """Frozen-input self-check: on-disk bytes must match the manifest."""
    problems = []
    for v in ("A", "B"):
        name = f"single_{v.lower()}.txt"
        rec = (manifest.get("derived_prompts") or {}).get(name) or {}
        p = root / "frozen" / name
        if not p.is_file() or sha(p.read_bytes()) != rec.get("sha256"):
            problems.append(name)
    for iso, rec in (manifest.get("packets") or {}).items():
        p = root / "frozen" / "packets" / f"{iso}.txt"
        if not p.is_file() or sha(p.read_bytes()) != rec.get("sha256"):
            problems.append(f"packets/{iso}.txt")
    for rel, key in (("frozen/schedule.json", "schedule_file_sha256"),
                     ("frozen/user_messages.json", "user_messages_file_sha256"),
                     ("ledger.json", "ledger_sha256")):
        p = root / rel
        if not p.is_file() or sha(p.read_bytes()) != manifest.get(key):
            problems.append(rel)
    ev = (manifest.get("evidence_snapshot") or {})
    if not data_path.is_file() or sha(data_path.read_bytes()) != ev.get("sha256"):
        problems.append("data/countries.json")
    if problems:
        raise Refusal(EXIT_GATE,
                      "source/hash drift - frozen inputs no longer match "
                      f"manifest.json: {', '.join(problems)}")


def _all_nonempty_strings(items) -> bool:
    return (isinstance(items, list) and bool(items)
            and all(isinstance(x, str) and x.strip() for x in items))


def _collect_keys(obj, wanted=("verified", "verification"), path="$") -> list:
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in wanted:
                hits.append(f"{path}.{k}")
            hits += _collect_keys(v, wanted, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += _collect_keys(v, wanted, f"{path}[{i}]")
    return hits


def verify_receipt(receipt: dict, bindings: dict, manifest: dict) -> None:
    """Schema v4 (the amended execution receipt, probe_followup_receipt.json):
    separates DOCUMENTED provider usage/pricing semantics from UNOBSERVED live
    behavior, requires the residual assumptions to be recorded, content-binds the
    exact preflight procedure AND a distinct claim-level sign-off artifact (not a
    mere path string) plus the adaptive follow-up amendment, the archival
    original receipt bytes and its independent review - and, when an observation
    is claimed, requires a structured probe-evidence record over ALL FOUR probe
    slots (old + new results and reviews) plus the structured disclosure of the
    original FAILED probe instead of free text. The original schema-v3
    preflight_receipt.json is archival immutable evidence and is never accepted
    here as the execution receipt. There is deliberately no ``verified`` flag to
    assert - claiming one is rejected as a false verification claim."""
    problems = []
    if receipt.get("receipt_version") != RECEIPT_VERSION:
        problems.append(f"receipt_version must be {RECEIPT_VERSION}")
    if "provider_api_semantics" in receipt:
        problems.append("legacy provider_api_semantics block rejected: schema v3 "
                        "reports documented sources + unobserved/observed live "
                        "behavior + residual assumptions (provider_semantics)")
    pf = receipt.get("preflight") or {}
    if pf.get("status") != "signed_off":
        problems.append("preflight.status must be 'signed_off'")
    if pf.get("document") != "preflight.md":
        problems.append("preflight.document must be exactly 'preflight.md' (the "
                        "bound procedure)")
    if pf.get("signoff_artifact") != "preflight-signoff.md":
        problems.append("preflight.signoff_artifact must be exactly "
                        "'preflight-signoff.md' (the distinct content-bound "
                        "claim-level decision artifact)")
    for k in ("reviewed_by", "reviewed_at", "statement"):
        if not isinstance(pf.get(k), str) or not pf.get(k).strip():
            problems.append(f"preflight.{k} must be a non-empty string")
    sem = receipt.get("provider_semantics")
    if not isinstance(sem, dict):
        problems.append("provider_semantics must be an object separating "
                        "documentation, live_behavior and residual_assumptions")
    else:
        doc = sem.get("documentation") or {}
        if doc.get("status") != "documented":
            problems.append("provider_semantics.documentation.status must be "
                            "'documented' (what documentation was reviewed)")
        if not _all_nonempty_strings(doc.get("sources")):
            problems.append("provider_semantics.documentation.sources must be a "
                            "non-empty list of non-empty strings")
        for k in ("reviewed_by", "reviewed_at"):
            if not isinstance(doc.get(k), str) or not doc.get(k).strip():
                problems.append(f"provider_semantics.documentation.{k} must be a "
                                "non-empty string")
        live = sem.get("live_behavior") or {}
        status = live.get("status")
        if status not in ("unobserved", "observed_in_bounded_probe"):
            problems.append("provider_semantics.live_behavior.status must be "
                            "'unobserved' or 'observed_in_bounded_probe'")
        if status == "observed_in_bounded_probe":
            for k in ("observed_at", "scope"):
                if not isinstance(live.get(k), str) or not live.get(k).strip():
                    problems.append(
                        f"provider_semantics.live_behavior.{k} must be a non-empty "
                        "string when a bounded probe is claimed")
            rec = live.get("record")
            entries = (rec.get("probe_evidence")
                       if isinstance(rec, dict)
                       and isinstance(rec.get("probe_evidence"), list) else None)
            if not isinstance(rec, dict) or entries is None:
                problems.append("provider_semantics.live_behavior.record must be "
                                "an object with a probe_evidence list of "
                                "{path, sha256} entries (structured evidence, not "
                                "a free-text claim)")
            elif not entries or not all(isinstance(e, dict) for e in entries):
                problems.append("provider_semantics.live_behavior.record."
                                "probe_evidence must be a non-empty list of "
                                "{path, sha256} objects")
            else:
                want = {f"{PROBES_DIR}/{s}/probe-result.json"
                        for s in PROBE_SLOTS} \
                    | {f"{PROBES_DIR}/{s}/review.json" for s in PROBE_SLOTS}
                paths = [e.get("path") for e in entries]
                if (len(paths) != len(set(paths)) or set(paths) != want):
                    problems.append("live_behavior.record.probe_evidence must cover "
                                    f"exactly {sorted(want)} (got {sorted(map(str, paths))})")
                for e in entries:
                    h, p = e.get("sha256"), str(e.get("path", ""))
                    if not isinstance(h, str) or not re.fullmatch(
                            r"[0-9a-f]{64}", h):
                        problems.append(f"probe_evidence sha256 invalid for {p!r}")
                    if p.startswith("/") or ".." in p.split("/"):
                        problems.append(f"probe_evidence path not relative: {p!r}")
            # the original failure must be disclosed structurally, never replaced
            of = rec.get("original_failure") if isinstance(rec, dict) else None
            if not isinstance(of, dict) \
                    or of.get("slot") != ORIGINAL_FAILURE_SLOT \
                    or not isinstance(of.get("status"), str) \
                    or not of.get("status").strip():
                problems.append(
                    "provider_semantics.live_behavior.record.original_failure "
                    "must be a structured {slot, status} disclosure of the "
                    f"original failed probe ({ORIGINAL_FAILURE_SLOT!r}) - the "
                    "original failure is never omitted or re-labelled")
        if not _all_nonempty_strings(sem.get("residual_assumptions")):
            problems.append("provider_semantics.residual_assumptions must be a "
                            "non-empty list of non-empty strings (the assumptions "
                            "that remain unverified)")
        claims = _collect_keys(sem)
        if claims:
            problems.append("false verification claim rejected - schema v2 has no "
                            f"'verified' flag: {claims}")
    if receipt.get("source_commit") != manifest.get("git_commit"):
        problems.append(f"source_commit {receipt.get('source_commit')!r} != "
                        f"manifest git_commit {manifest.get('git_commit')!r}")
    rec = receipt.get("bindings")
    if not isinstance(rec, dict):
        problems.append("bindings must be an object of path -> sha256")
    elif set(rec) != set(bindings):
        missing = sorted(set(bindings) - set(rec))
        extra = sorted(set(rec) - set(bindings))
        problems.append(f"bindings key set differs (missing={missing}, extra={extra})")
    else:
        bad = [k for k in bindings if rec[k] != bindings[k]]
        if bad:
            problems.append(f"binding hash mismatch for {bad}")
    if problems:
        raise Refusal(EXIT_GATE, "preflight receipt rejected: " + "; ".join(problems))


def verify_probe_observation(receipt: dict, root: Path) -> None:
    """Hash-verify the receipt's structured probe-evidence record against the
    bytes actually archived under probes/ (results AND independent reviews)."""
    live = (receipt.get("provider_semantics") or {}).get("live_behavior") or {}
    if live.get("status") != "observed_in_bounded_probe":
        return                      # nothing claimed, nothing to verify
    rec = live.get("record") or {}
    entries = rec.get("probe_evidence")
    if not isinstance(entries, list):
        raise Refusal(EXIT_GATE,
                      "observation record missing probe_evidence - structured "
                      "hashed evidence required (no free-text claim)")
    bad = []
    for e in entries:
        if not isinstance(e, dict):
            bad.append(str(e))
            continue
        path, want = str(e.get("path", "")), e.get("sha256")
        fp = root / path
        if not path.startswith(PROBES_DIR + "/") or not fp.is_file():
            bad.append(f"{path}: missing")
            continue
        got = sha(fp.read_bytes())
        if got != want:
            bad.append(f"{path}: sha256 {got[:16]}... != receipt {str(want)[:16]}...")
    if bad:
        raise Refusal(EXIT_GATE,
                      "probe evidence failed hash verification (tampered or "
                      f"outdated archive): {bad}")
    # The disclosed original failure must equal the archived bytes: the failed
    # original slot can never be quietly re-labelled (or attested) as a success.
    of = rec.get("original_failure")
    archived_path = root / PROBES_DIR / ORIGINAL_FAILURE_SLOT / "probe-result.json"
    try:
        archived_status = load_json(archived_path).get("status")
    except (OSError, ValueError):
        archived_status = None
    if not isinstance(of, dict) \
            or of.get("slot") != ORIGINAL_FAILURE_SLOT \
            or of.get("status") != archived_status \
            or archived_status in (None, "completed"):
        raise Refusal(
            EXIT_GATE,
            "observation record original_failure does not match the archived "
            f"original failure: disclosed {of!r} vs archived "
            f"{ORIGINAL_FAILURE_SLOT} status {archived_status!r} - the original "
            "failed probe is never re-labelled or omitted")


def declared_limits(manifest: dict) -> dict:
    """The pre-registered ceilings; the runner enforces them and never raises them."""
    caps = dict(manifest.get("proposed_caps") or {})
    ceiling = caps.get("attempt_ceiling_including_failures")
    if ceiling != ATTEMPT_CEILING or manifest.get("attempt_ceiling") != ATTEMPT_CEILING:
        raise Refusal(EXIT_GATE,
                      f"declared attempt ceiling {ceiling!r} != {ATTEMPT_CEILING}")
    if caps.get("retries_selected_for_output") != 0:
        raise Refusal(EXIT_GATE, "declared retries_selected_for_output must be 0")
    # USD cap: must be a finite, positive number no larger than the approved
    # local maximum (NaN / +/-inf / bool / string / negative all refuse).
    raw_usd = caps.get("aggregate_max_usd_including_failures")
    if isinstance(raw_usd, bool) or not isinstance(raw_usd, (int, float)):
        raise Refusal(EXIT_GATE,
                      f"declared USD cap missing or non-numeric: {raw_usd!r}")
    usd = float(raw_usd)
    if not math.isfinite(usd) or usd <= 0:
        raise Refusal(EXIT_GATE,
                      f"declared USD cap is not finite and positive: {raw_usd!r}")
    if usd > MAX_USD:
        raise Refusal(EXIT_GATE,
                      f"declared USD cap exceeds the approved ${MAX_USD:.2f} maximum")
    caps["aggregate_max_usd_including_failures"] = usd
    for k in ("per_call_max_input_tokens", "per_call_max_output_tokens",
              "aggregate_max_input_tokens", "aggregate_max_output_tokens"):
        v = caps.get(k)
        if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
            raise Refusal(EXIT_GATE,
                          f"declared cap {k} missing, non-integer or non-positive: "
                          f"{v!r}")
    if caps["per_call_max_output_tokens"] < RESERVED_OUTPUT_TOKENS_PER_CALL:
        raise Refusal(EXIT_GATE,
                      "declared per-call output cap below the reserved "
                      "2000 output/reasoning tokens")
    # The original 20 000 / 800 000 proposal must still be recorded verbatim:
    # the amendment supersedes it for dispatch reservation only, and it remains
    # an in-run stop rule on billed native tokens.
    for k, v in PRESERVED_PROPOSED_INPUT_CAPS.items():
        if caps.get(k) != v:
            raise Refusal(EXIT_GATE,
                          f"original proposed cap {k} altered: {caps.get(k)!r} "
                          f"!= {v!r} (budget-amendment.md preserves it verbatim)")
    am = manifest.get("reservation_amendment")
    if not isinstance(am, dict):
        raise Refusal(EXIT_GATE,
                      "reservation amendment missing from manifest "
                      "(pre-outcome amendment not pre-registered)")
    if am.get("per_call_input_reservation_units") != RESERVATION_PER_CALL_UNITS:
        raise Refusal(EXIT_GATE,
                      "reservation amendment per-call ceiling drifted: "
                      f"{am.get('per_call_input_reservation_units')!r} != "
                      f"{RESERVATION_PER_CALL_UNITS}")
    if am.get("aggregate_input_reservation_units") != RESERVATION_AGGREGATE_UNITS:
        raise Refusal(EXIT_GATE,
                      "reservation amendment aggregate ceiling drifted: "
                      f"{am.get('aggregate_input_reservation_units')!r} != "
                      f"{RESERVATION_AGGREGATE_UNITS}")
    if am.get("preserved_original_proposal") != PRESERVED_PROPOSED_INPUT_CAPS:
        raise Refusal(EXIT_GATE,
                      "reservation amendment does not preserve the original "
                      "proposal verbatim")
    caps["reservation_per_call_units"] = RESERVATION_PER_CALL_UNITS
    caps["reservation_aggregate_units"] = RESERVATION_AGGREGATE_UNITS
    if manifest.get("requested_settings") != REQUESTED_SETTINGS:
        raise Refusal(EXIT_GATE,
                      f"requested settings drifted: {manifest.get('requested_settings')!r}")
    models = tuple(manifest.get("models") or ())
    if models != MODELS:
        raise Refusal(EXIT_GATE, f"pre-registered models drifted: {models!r}")
    return caps


def build_plan(manifest: dict, sched: list, msgs: list, caps: dict) -> dict:
    """Worst-case reservation from frozen bytes; returns the plan or refuses."""
    if len(sched) != ATTEMPT_CEILING or len(msgs) != ATTEMPT_CEILING:
        raise Refusal(EXIT_GATE,
                      f"schedule/messages must hold {ATTEMPT_CEILING} rows, got "
                      f"{len(sched)}/{len(msgs)}")
    if [m.get("call") for m in msgs] != [r.get("call") for r in sched]:
        raise Refusal(EXIT_GATE, "user messages are not aligned with the schedule")
    prompt_bytes = {}
    for v in ("A", "B"):
        name = f"single_{v.lower()}.txt"
        prompt_bytes[v] = int((manifest["derived_prompts"][name])["bytes"])
    per_call_in, worst_usd = [], []
    for row, msg in zip(sched, msgs):
        if row.get("model") not in MODELS or row.get("variant") not in ("A", "B"):
            raise Refusal(EXIT_GATE, f"schedule row {row.get('call')} carries an "
                                     "unregistered model or variant")
        if not row.get("fresh_context"):
            raise Refusal(EXIT_GATE, f"schedule row {row.get('call')} is not a "
                                     "fresh context")
        body = msg["message"]
        if msg.get("message_sha256") != sha(body.encode("utf-8")):
            raise Refusal(EXIT_GATE, f"message {row['call']} hash does not match "
                                     "its bytes")
        reserved = math.ceil((prompt_bytes[row["variant"]]
                              + len(body.encode("utf-8"))) / BYTES_PER_TOKEN) \
            + FIXED_OVERHEAD_TOKENS_PER_CALL
        per_call_in.append(reserved)
    max_per_call = max(per_call_in)
    agg_in = sum(per_call_in)
    agg_out = ATTEMPT_CEILING * RESERVED_OUTPUT_TOKENS_PER_CALL
    problems = []
    if max_per_call > caps["reservation_per_call_units"]:
        problems.append(
            f"worst-case input reservation {max_per_call} units/call > administrative "
            f"reservation ceiling {caps['reservation_per_call_units']} "
            "(budget-amendment.md)")
    if agg_in > caps["reservation_aggregate_units"]:
        problems.append(
            f"worst-case aggregate input reservation {agg_in} units > administrative "
            f"reservation ceiling {caps['reservation_aggregate_units']} "
            "(budget-amendment.md)")
    if agg_out > caps["aggregate_max_output_tokens"]:
        problems.append(f"worst-case aggregate output reservation {agg_out} tokens "
                        f"> declared aggregate cap "
                        f"{caps['aggregate_max_output_tokens']}")
    am = manifest.get("reservation_amendment") or {}
    if (am.get("plan_max_per_call_units") != max_per_call
            or am.get("plan_aggregate_units") != agg_in):
        problems.append("recorded plan in reservation_amendment does not match the "
                        "recomputed exact plan (manifest drift)")
    return {"caps": caps, "per_call_input": per_call_in, "worst_usd": worst_usd,
            "max_per_call_input": max_per_call, "aggregate_input": agg_in,
            "aggregate_output": agg_out, "problems": problems,
            "preserved_original_proposal": dict(PRESERVED_PROPOSED_INPUT_CAPS),
            "input_method": "UTF-8 byte count of the frozen prompt + message + "
                            f"{FIXED_OVERHEAD_TOKENS_PER_CALL} fixed chat-framing "
                            "units per call (administrative reservation units: "
                            "conservative under the documented tokenizer/framing "
                            "assumptions, NOT a proven provider-native token bound)"}


def cost_reservation(plan: dict, prices: dict) -> list:
    """Worst-case USD per attempt from reserved tokens x provider prices."""
    worst = []
    for row, reserved in zip(plan["_sched"], plan["per_call_input"]):
        p = prices[row["model"]]
        worst.append(reserved * p["prompt"]
                     + RESERVED_OUTPUT_TOKENS_PER_CALL * p["completion"])
    plan["worst_usd"] = worst
    return worst


# --------------------------------------------------------------------------- #
# Ceilings (pure accounting; checked before every dispatch)
# --------------------------------------------------------------------------- #

def ceiling_violation(idx, n_attempts_done, plan, used,
                      prior_usd=0.0) -> str | None:
    """Pre-dispatch stop check. ``prior_usd`` is the shared experiment spend
    (prior probes and earlier runs) that must be counted in EVERY USD comparison
    alongside this run's local counter; result.json totals stay run-local."""
    caps = plan["caps"]
    if n_attempts_done >= caps["attempt_ceiling_including_failures"]:
        return (f"attempt ceiling reached: {n_attempts_done} attempted requests "
                "(failures included)")
    if idx + 1 > len(plan["per_call_input"]):
        return "schedule exhausted"
    usd = used.get("usd", 0.0)
    if not isinstance(usd, (int, float)) or isinstance(usd, bool) \
            or not math.isfinite(usd) or usd < 0:
        return ("accounting corrupted: used cost is not a finite non-negative "
                "number")
    if not isinstance(prior_usd, (int, float)) or isinstance(prior_usd, bool) \
            or not math.isfinite(prior_usd) or prior_usd < 0:
        return ("accounting corrupted: prior shared cost is not a finite "
                "non-negative number")
    shared_usd = usd + prior_usd
    remaining_in = sum(plan["per_call_input"][idx:])
    if used.get("reserved_in", 0) + remaining_in > caps["reservation_aggregate_units"]:
        return (f"aggregate input reservation ceiling "
                f"{caps['reservation_aggregate_units']} units: "
                f"{used.get('reserved_in', 0)} dispatched + {remaining_in} "
                "remaining reservation")
    if used.get("input", 0) > caps["aggregate_max_input_tokens"]:
        return (f"preserved aggregate input proposal exceeded by billed native "
                f"tokens: {used['input']} > {caps['aggregate_max_input_tokens']}")
    remaining_out = (len(plan["per_call_input"]) - idx) \
        * RESERVED_OUTPUT_TOKENS_PER_CALL
    if used.get("output", 0) + remaining_out > caps["aggregate_max_output_tokens"]:
        return (f"aggregate output ceiling: used {used.get('output', 0)} + remaining "
                f"reservation {remaining_out} > "
                f"{caps['aggregate_max_output_tokens']}")
    remaining_usd = sum(plan["worst_usd"][idx:])
    if shared_usd + remaining_usd > caps["aggregate_max_usd_including_failures"]:
        return (f"USD ceiling ${caps['aggregate_max_usd_including_failures']:.2f}: "
                f"shared ${shared_usd:.6f} (run-local ${usd:.6f} + prior "
                f"${prior_usd:.6f}) + remaining worst-case reservation "
                f"${remaining_usd:.6f}")
    return None


def cell_key(row) -> tuple:
    return (row.get("sentinel"), row.get("case"), row.get("model"),
            row.get("variant"), row.get("draw"))


# --------------------------------------------------------------------------- #
# Prior-run ledger: no silent budget/schedule reset between runs
# --------------------------------------------------------------------------- #

def reconciliation_valid(path: Path, call) -> bool:
    """A human-reviewed reconciliation is an EXTERNAL record the runner only
    reads; it never writes or repairs one itself."""
    if not path.is_file():
        return False
    try:
        doc = load_json(path)
    except (OSError, ValueError):
        return False
    if not isinstance(doc, dict) or doc.get("liability_call") != call:
        return False
    return all(isinstance(doc.get(k), str) and doc[k].strip()
               for k in ("reviewed_by", "reviewed_at", "statement"))


def prior_run_state(root: Path, sched: list) -> dict:
    """Aggregate every existing run directory before a new run may start.

    Unknown prior state (no terminal result, non-finite tallies) and unresolved
    unreconciled liabilities block the new run; attempted cells block it because
    one attempt per predeclared cell is an experiment-level ceiling.
    """
    state = {"runs": [], "attempted": {}, "unreconciled": [], "unknown": [],
             "used_usd": 0.0, "used_input": 0, "used_output": 0,
             "scoring_used_input": 0, "scoring_used_output": 0,
             "probe_used_input": 0, "probe_used_output": 0,
             "probe_slots": [], "probe_dispatched": 0}
    runs = root / RUNS_DIR
    run_dirs = (sorted(p for p in runs.iterdir() if p.is_dir())
                if runs.is_dir() else [])
    by_call = {r.get("call"): r for r in sched}
    for d in run_dirs:
        rid = d.name
        state["runs"].append(rid)
        result_path = d / "result.json"
        if not result_path.is_file():
            state["unknown"].append(f"{rid}: no terminal result.json")
            continue
        try:
            result = load_json(result_path)
        except (OSError, ValueError) as exc:
            state["unknown"].append(f"{rid}: unreadable result ({exc})")
            continue
        used_usd = _cost_or_none(result.get("used_usd"))
        if used_usd is None:
            state["unknown"].append(f"{rid}: used_usd not a finite non-negative "
                                    "number")
            continue
        state["used_usd"] += used_usd
        state["used_input"] += int(result.get("used_input_tokens") or 0)
        state["used_output"] += int(result.get("used_output_tokens") or 0)
        state["scoring_used_input"] += int(result.get("used_input_tokens") or 0)
        state["scoring_used_output"] += int(result.get("used_output_tokens") or 0)
        attempts = d / "attempts"
        files = sorted(attempts.glob("*.json")) if attempts.is_dir() else []
        for f in files:
            try:
                rec = load_json(f)
            except (OSError, ValueError):
                state["unknown"].append(f"{rid}: unreadable attempt {f.name}")
                continue
            call = rec.get("call")
            if call in by_call:
                state["attempted"][call] = rid
            liab = rec.get("unreconciled_liability")
            if isinstance(liab, dict) and not reconciliation_valid(
                    d / "reconciliation.json", call):
                state["unreconciled"].append(
                    {"run": rid, "call": call,
                     "reason": liab.get("reason", "billed cost unknown")})
    # ---- probes: separate evidence tree, SAME experiment-wide ledger ----
    probes = root / PROBES_DIR
    if probes.is_dir():
        for d in sorted(p for p in probes.iterdir() if p.is_dir()):
            slot = d.name
            state["probe_slots"].append(slot)
            if slot not in PROBE_SLOTS:
                state["unknown"].append(
                    f"{slot}: unregistered probe directory under {PROBES_DIR}/")
                continue
            dispatch, result_path = d / "dispatch.json", d / "probe-result.json"
            if not dispatch.is_file():
                state["unknown"].append(
                    f"{slot}: probe directory without dispatch.json")
                continue
            state["probe_dispatched"] += 1
            if not result_path.is_file():
                state["unknown"].append(
                    f"{slot}: dispatched probe has no terminal probe-result.json "
                    "(crash-incomplete; a human must reconcile, evidence is never "
                    "deleted)")
                continue
            try:
                result = load_json(result_path)
            except (OSError, ValueError) as exc:
                state["unknown"].append(f"{slot}: unreadable probe result ({exc})")
                continue
            used_usd = _cost_or_none(result.get("used_usd"))
            if used_usd is None:
                state["unknown"].append(
                    f"{slot}: probe used_usd not a finite non-negative number")
                continue
            state["used_usd"] += used_usd
            state["used_input"] += int(result.get("used_input_tokens") or 0)
            state["used_output"] += int(result.get("used_output_tokens") or 0)
            state["probe_used_input"] += int(result.get("used_input_tokens") or 0)
            state["probe_used_output"] += int(result.get("used_output_tokens") or 0)
            liab = result.get("unreconciled_liability")
            if isinstance(liab, dict) and not reconciliation_valid(
                    d / "reconciliation.json", slot):
                state["unreconciled"].append(
                    {"run": slot, "call": slot,
                     "reason": liab.get("reason", "probe charge unknown")})
    return state


def prior_gate(prior: dict, sched: list) -> str | None:
    """Return a refusal reason if a new run may not start."""
    if prior["unknown"]:
        return ("prior run state unknown - manual reconciliation required before "
                f"any new run: {prior['unknown']}")
    if prior["unreconciled"]:
        first = prior["unreconciled"][0]
        return ("unreconciled liability blocks any new run (unknown charges are "
                "not zero spend and the budget must not be silently reset): "
                f"run {first['run']} call {first['call']}: {first['reason']} - "
                "a human-reviewed runs/<run>/reconciliation.json is required")
    overlap = sorted(c for c in prior["attempted"]
                     if c in {r.get("call") for r in sched})
    if overlap:
        return ("predeclared attempt(s) already dispatched in prior run(s) "
                f"{sorted({prior['attempted'][c] for c in overlap})} - calls "
                f"{overlap}: one attempt per cell across the experiment, so a new "
                "run cannot silently reset the schedule or the budget")
    return None


def total_dispatch_violation(prior: dict, planned: int) -> str | None:
    """Combined ceiling: scoring attempts + probes <= 44 (40 frozen scoring +
    the 2 executed original probes + the 2 adaptive follow-up probes;
    probe-followup-amendment.md §3, superseding the original 42 for this phase)."""
    scoring = len(prior.get("attempted", {}))
    probes = prior.get("probe_dispatched", 0)
    total = scoring + probes + planned
    if total > TOTAL_DISPATCH_CEILING:
        return (f"total dispatch ceiling {TOTAL_DISPATCH_CEILING} "
                f"({ATTEMPT_CEILING} scoring + {PROBE_CEILING} probes) exceeded: "
                f"{scoring} prior scoring + {probes} prior probes + {planned} planned")
    return None


def original_probe_evidence_gate(root: Path, bindings: dict | None) -> str | None:
    """The TWO original probe slots must be present and truthful before any
    adaptive follow-up dispatch and before any scoring dispatch.

    Checks, against the archived bytes only:
      * both original dispatch.json + probe-result.json exist (a missing or
        unreadable original record blocks - never silently ignored);
      * each archived status still equals the independently reviewed outcome
        (probe-1 completed, probe-2 stopped/FAILED): the failed slot is never
        re-labelled a success and the completed slot is never re-labelled;
      * the failed original discloses its failure (stop_reason/errors);
      * the receipt chain is intact: each original record's
        ``preflight_receipt_sha256`` equals the SHA-256 of the untouched
        archival ``preflight_receipt.json``, and each original dispatch still
        carries the matching manifest + probe-amendment hashes;
      * each original record still says ``retry: false`` (the executed
        no-retry protocol).

    It never writes anything and never inspects a review: reviews are checked by
    scoring_probe_gate (independent, honestly attributed review artifacts).
    """
    if not bindings:
        return ("receipt bindings unavailable - cannot verify the original probe "
                "evidence chain")
    archival_sha = bindings.get(ARCHIVAL_RECEIPT_NAME)
    for slot in ORIGINAL_PROBE_SLOTS:
        d = root / PROBES_DIR / slot
        problems = []
        dispatch, result = d / "dispatch.json", d / "probe-result.json"
        for p in (dispatch, result):
            if not p.is_file():
                return (f"original probe evidence missing: {p.relative_to(root)} - "
                        "original records must exist and stay preserved")
        try:
            disp_doc = load_json(dispatch)
            res_doc = load_json(result)
        except (OSError, ValueError) as exc:
            return f"original probe evidence unreadable for {slot}: {exc}"
        want_status = ORIGINAL_PROBE_STATUSES[slot]
        got_status = res_doc.get("status")
        if got_status != want_status:
            return (f"original probe {slot} must keep its archived, independently "
                    f"reviewed status {want_status!r} (found {got_status!r}) - "
                    "original evidence is immutable and the failed slot is never "
                    "re-labelled a success")
        if want_status != "completed":
            disclosure = str(res_doc.get("stop_reason") or "").strip() \
                or "; ".join(str(e) for e in (res_doc.get("errors") or []))
            if not disclosure.strip():
                return (f"original failed probe {slot} does not disclose its failure "
                        "(no stop_reason/errors) - the original failure must stay "
                        "truthfully recorded")
        expected_dispatch = {
            "preflight_receipt_sha256": archival_sha,
            "manifest_sha256": bindings.get("frozen/manifest.json"),
            "probe_amendment_sha256": bindings.get("probe-amendment.md")}
        for key, want_hash in expected_dispatch.items():
            if disp_doc.get(key) != want_hash:
                problems.append(
                    f"dispatch.json {key}={str(disp_doc.get(key))[:16]}... != "
                    f"current {str(want_hash)[:16]}... (receipt/manifest/amendment "
                    "chain broken)")
        if res_doc.get("preflight_receipt_sha256") != archival_sha:
            problems.append(
                "probe-result.json preflight_receipt_sha256="
                f"{str(res_doc.get('preflight_receipt_sha256'))[:16]}... != current "
                f"archival receipt {str(archival_sha)[:16]}...")
        if disp_doc.get("retry") is not False or res_doc.get("retry") is not False:
            problems.append("original record no longer says retry: false")
        if problems:
            return (f"original probe {slot} evidence hash binding failed: "
                    + "; ".join(problems))
    return None


def scoring_probe_gate(prior: dict, root: Path,
                       bindings: dict | None = None) -> str | None:
    """Scoring requires ALL FOUR probe slots dispatched: the two originals with
    their evidence preserved and the original failure truthfully disclosed, and
    BOTH adaptive follow-up slots successful and independently reviewed.

    Deliberately does NOT require a success status for the original failed
    probe (probe-2): its archived ``stopped`` status plus an independent
    ``reviewed_failure`` confirmation is what must exist - a success attestation
    for it is rejected. Probe charges unknown/unreconciled are blocked earlier by
    prior_gate (same ledger)."""
    dispatched = prior.get("probe_dispatched", 0)
    if dispatched > PROBE_CEILING:
        return (f"probe dispatch ceiling {PROBE_CEILING} exceeded: "
                f"{dispatched} probes already dispatched")
    slots = sorted(prior.get("probe_slots", []))
    if slots != sorted(PROBE_SLOTS):
        return ("scoring refused before any dispatch: all four probe slots must be "
                "dispatched first - originals " + "/".join(ORIGINAL_PROBE_SLOTS) +
                " plus adaptive follow-ups " + "/".join(FOLLOWUP_PROBE_SLOTS) +
                f" (found {slots})")
    evidence_reason = original_probe_evidence_gate(root, bindings)
    if evidence_reason:
        return f"scoring refused before any dispatch: {evidence_reason}"
    results = {}
    for slot in ORIGINAL_PROBE_SLOTS:            # pinned statuses, loaded above
        try:
            results[slot] = load_json(root / PROBES_DIR / slot / "probe-result.json")
        except (OSError, ValueError):
            return (f"scoring refused before any dispatch: original probe {slot} "
                    "has no readable probe-result.json")
    for slot in FOLLOWUP_PROBE_SLOTS:
        try:
            results[slot] = load_json(root / PROBES_DIR / slot / "probe-result.json")
        except (OSError, ValueError):
            return (f"scoring refused before any dispatch: adaptive follow-up "
                    f"{slot} has no readable probe-result.json")
        if results[slot].get("status") != "completed":
            return (f"scoring refused before any dispatch: adaptive follow-up "
                    f"{slot} is not a successful probe "
                    f"(status={results[slot].get('status')!r}) - both follow-ups "
                    "must complete and be independently reviewed; any failure ends "
                    "the phase")
    for slot in PROBE_SLOTS:
        try:
            review = load_json(root / PROBES_DIR / slot / "review.json")
        except (OSError, ValueError):
            return (f"scoring refused before any dispatch: probe {slot} lacks an "
                    "independent review (review.json)")
        expected = (REVIEW_FAILURE_STATUS if slot == ORIGINAL_FAILURE_SLOT
                    else REVIEW_OK_STATUS)
        ok = (isinstance(review, dict)
              and review.get("status") == expected
              and review.get("probe_slot") == slot
              and all(isinstance(review.get(k), str) and review[k].strip()
                      for k in REVIEW_FIELDS))
        if not ok:
            if (isinstance(review, dict)
                    and slot == ORIGINAL_FAILURE_SLOT
                    and review.get("status") == REVIEW_OK_STATUS):
                return (f"scoring refused before any dispatch: probe {slot}'s "
                        "independent review must confirm the archived failure "
                        f"(status {REVIEW_FAILURE_STATUS!r}); a {REVIEW_OK_STATUS!r} "
                        "success attestation for the original failed probe is "
                        "rejected")
            return (f"scoring refused before any dispatch: probe {slot} lacks a "
                    f"valid independent-review status (structured {expected} "
                    "review.json with " + "/".join(REVIEW_FIELDS) +
                    ", not a free-text claim)")
    return None


def probe_dispatch_gate(prior: dict, slot, root: Path,
                        bindings: dict | None = None) -> str | None:
    """Probe-mode gates (unknown/unreconciled states are blocked by prior_gate).
    One dispatch per registered slot, ever; adaptive follow-up slots additionally
    require the original evidence chain (original_probe_evidence_gate), the
    frozen slot order, and a COMPLETED earlier follow-up: any follow-up failure
    ends the phase, so no later follow-up may dispatch - checked here, before
    any price fetch, credential read or transport call. No skipping, no retries,
    no extra slots; the 44-dispatch ceiling is a maximum, never a requirement
    to consume every slot."""
    if prior.get("attempted"):
        return ("probes must precede any scoring dispatch - a scoring attempt "
                "already exists (probe-amendment.md)")
    if (root / PROBES_DIR / slot).exists():
        return f"probe slot {slot!r} already exists - no overwrite, no re-dispatch"
    dispatched = prior.get("probe_dispatched", 0)
    if dispatched >= PROBE_CEILING:
        return (f"probe ceiling reached: {dispatched}/{PROBE_CEILING} probes "
                "already dispatched (no fifth slot, no retries)")
    if slot in FOLLOWUP_PROBE_SLOTS:
        evidence_reason = original_probe_evidence_gate(root, bindings)
        if evidence_reason:
            return (f"adaptive follow-up {slot} refused before dispatch: "
                    f"{evidence_reason}")
        idx = PROBE_SLOTS.index(slot)
        for earlier in PROBE_SLOTS[:idx]:
            earlier_result = root / PROBES_DIR / earlier / "probe-result.json"
            if not earlier_result.is_file():
                return (f"adaptive follow-up slot {slot!r} requires the terminal "
                        f"probe-result.json of {earlier!r} first (frozen order "
                        f"{list(PROBE_SLOTS)}); no skipping, no retries")
            if earlier in FOLLOWUP_PROBE_SLOTS:
                # Stopping rule (probe-followup-amendment.md §2/§5): any
                # follow-up failure ends the phase. A later follow-up may not
                # dispatch after an earlier follow-up failed - refused here,
                # before price fetch, credential read and transport.
                try:
                    earlier_status = load_json(earlier_result).get("status")
                except (OSError, ValueError):
                    return (f"adaptive follow-up {slot} refused before dispatch: "
                            f"{earlier} terminal record is unreadable - the phase "
                            "cannot continue")
                if earlier_status != "completed":
                    return (f"adaptive follow-up {slot} refused before dispatch: "
                            f"earlier follow-up {earlier} is not completed "
                            f"(status={earlier_status!r}) - any follow-up failure "
                            "ends the phase: no remaining follow-up may dispatch "
                            "and scoring stays blocked (probe-followup-amendment.md "
                            "§2)")
    reason = total_dispatch_violation(prior, 1)
    if reason:
        return reason
    return None


def prior_budget_violation(prior: dict, plan: dict, total_usd: float) -> str | None:
    """Prior accounted spend plus this run's worst case must still fit the
    declared ceilings.

    USD: ALL prior charges (scoring AND probes) share the same local ceiling.
    Probe tokens: counted in the same ledger, bounded by the pre-registered
    probe allowance. Scoring tokens: charged against the scoring reservation
    ceilings (sized exactly for the 40 frozen calls).
    """
    caps = plan["caps"]
    usd = prior.get("used_usd", 0.0)
    if not math.isfinite(usd) or usd < 0:
        return "prior used cost is not a finite non-negative number"
    if usd + total_usd > caps["aggregate_max_usd_including_failures"]:
        return (f"budget already consumed: prior ${usd:.6f} + this run's "
                f"worst-case ${total_usd:.6f} > "
                f"${caps['aggregate_max_usd_including_failures']:.2f}")
    probe_in = int(prior.get("probe_used_input", 0))
    probe_out = int(prior.get("probe_used_output", 0))
    scoring_in = int(prior.get("scoring_used_input",
                               prior.get("used_input", 0)))
    scoring_out = int(prior.get("scoring_used_output",
                                prior.get("used_output", 0)))
    if plan.get("is_probe"):
        if probe_in + plan["aggregate_input"] > PROBE_INPUT_ALLOWANCE_UNITS:
            return ("probe input allowance would be exceeded: "
                    f"{probe_in} prior + {plan['aggregate_input']} planned > "
                    f"{PROBE_INPUT_ALLOWANCE_UNITS} declared in probe-amendment.md")
        if probe_out + plan["aggregate_output"] > PROBE_OUTPUT_ALLOWANCE_TOKENS:
            return ("probe output allowance would be exceeded: "
                    f"{probe_out} prior + {plan['aggregate_output']} planned > "
                    f"{PROBE_OUTPUT_ALLOWANCE_TOKENS} declared in probe-amendment.md")
        return None
    if probe_in > PROBE_INPUT_ALLOWANCE_UNITS:
        return ("probe token usage exceeds the pre-registered probe input "
                f"allowance: {probe_in} > {PROBE_INPUT_ALLOWANCE_UNITS}")
    if probe_out > PROBE_OUTPUT_ALLOWANCE_TOKENS:
        return ("probe token usage exceeds the pre-registered probe output "
                f"allowance: {probe_out} > {PROBE_OUTPUT_ALLOWANCE_TOKENS}")
    if scoring_in + plan["aggregate_input"] \
            > caps["reservation_aggregate_units"]:
        return ("aggregate input reservation ceiling would be exceeded by prior "
                "billed usage plus this run's reservation")
    if scoring_out + plan["aggregate_output"] \
            > caps["aggregate_max_output_tokens"]:
        return ("aggregate output ceiling would be exceeded by prior billed usage "
                "plus this run's reservation")
    return None


# --------------------------------------------------------------------------- #
# Request construction (frozen bytes only; no dynamic input, no fallback/cache)
# --------------------------------------------------------------------------- #

def build_request(model: str, prompt: str, message: str, settings: dict) -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": prompt},
                     {"role": "user", "content": message}],
        "temperature": settings["temperature"],
        "top_p": settings["top_p"],
        "max_tokens": settings["max_output_tokens"],
        "stream": False,
        "usage": {"include": True},
        # no model fallback list and no cache directives are ever sent
        "provider": {"allow_fallbacks": False},
    }
    if set(payload) != set(REQUEST_KEYS):
        raise Refusal(EXIT_GATE, "request shape drifted from the fixed whitelist")
    return payload


# --------------------------------------------------------------------------- #
# Provider transport (real implementations; used only after every gate)
# --------------------------------------------------------------------------- #

def _https(method: str, url: str, payload=None, headers=None,
           timeout: float = TIMEOUT_SECONDS) -> tuple:
    import urllib.error
    import urllib.request
    if not url.startswith("https://") or not url.startswith(API_BASE):
        raise Refusal(EXIT_GATE, f"refusing non-fixed endpoint: {url}")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        return exc.code, body
    except Exception as exc:                       # noqa: BLE001 - fail closed
        raise Refusal(EXIT_STOPPED, f"transport error ({type(exc).__name__})")


def https_post(url, payload, headers, timeout):
    return _https("POST", url, payload, headers, timeout)


def https_get(url, headers, timeout):
    return _https("GET", url, None, headers, timeout)


def fetch_prices() -> dict:
    """Provider model-price metadata (USD per token), explicit timeout, fail closed.

    The response shape ({data:[{id, pricing:{prompt, completion}}]}) has never
    been verified against a live call: if it is not exactly as expected, this
    refuses rather than guessing.
    """
    status, body = https_get(MODELS_URL, {"Accept": "application/json"},
                              TIMEOUT_SECONDS)
    if status != 200:
        raise Refusal(EXIT_GATE, f"price metadata fetch failed: HTTP {status}")
    try:
        doc = json.loads(body)
    except ValueError:
        raise Refusal(EXIT_GATE, "price metadata is not JSON")
    entries = doc.get("data") if isinstance(doc, dict) else None
    if not isinstance(entries, list):
        raise Refusal(EXIT_GATE, "unexpected price metadata shape (no data list)")
    prices = {}
    for entry in entries:
        if isinstance(entry, dict) and entry.get("id") in MODELS:
            pricing = entry.get("pricing")
            if not isinstance(pricing, dict):
                raise Refusal(EXIT_GATE,
                              f"missing pricing for pre-registered model "
                              f"{entry.get('id')!r}")
            prices[entry["id"]] = {"prompt": _price(pricing.get("prompt"),
                                                    entry["id"], "prompt"),
                                   "completion": _price(pricing.get("completion"),
                                                        entry["id"], "completion")}
    missing = [m for m in MODELS if m not in prices]
    if missing:
        raise Refusal(EXIT_GATE, f"no price metadata for pre-registered model(s) "
                                 f"{missing} - refusing unknown prices")
    return prices


def _price(value, model, kind) -> float:
    try:
        p = float(value)
    except (TypeError, ValueError):
        raise Refusal(EXIT_GATE,
                      f"unknown {kind} price for {model}: {value!r}")
    if not math.isfinite(p) or p < 0:
        raise Refusal(EXIT_GATE, f"invalid {kind} price for {model}: {value!r}")
    return p


def load_secret() -> str:
    """Reads the credential from the environment; never logged, never echoed."""
    return os.environ.get(SECRET_ENV, "").strip()


# --------------------------------------------------------------------------- #
# Dispatch (one attempt per cell, sequential, no retries, evidence preserved)
# --------------------------------------------------------------------------- #

def _reject_constant(name):
    # Python's json decoder accepts NaN/Infinity literals by default; billing
    # and output numbers must never come from them.
    raise ValueError(f"non-finite JSON number {name}")


def json_loads_strict(text):
    return json.loads(text, parse_constant=_reject_constant)


def _cost_or_none(value):
    """A billed cost is valid only as a finite, non-negative number (bool and
    NaN/+/-inf rejected). Returns None for anything else."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    f = float(value)
    if not math.isfinite(f) or f < 0:
        return None
    return f


def _usage_ints(usage):
    """Validated prompt/completion/total token counts, or None if invalid."""
    if not isinstance(usage, dict):
        return None
    out = {}
    for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
        v = usage.get(k)
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            return None
        out[k] = v
    if out["total_tokens"] != out["prompt_tokens"] + out["completion_tokens"]:
        return None
    return out


def parse_billed(raw) -> dict:
    """Best-effort, never-raising billed usage/cost parse of a raw body.

    Used on failed dispatch so any parseable billing is still recorded even
    when the output is invalid; ``cost is None`` means the charge is unknown,
    i.e. an unreconciled liability (never assumed to be zero).
    """
    out = {"parsed": False, "usage": None, "cost": None, "reason": None}
    if not raw:
        out["reason"] = "no response body"
        return out
    try:
        doc = json_loads_strict(raw)
    except ValueError as exc:
        out["reason"] = f"body is not strict JSON ({exc})"
        return out
    if not isinstance(doc, dict):
        out["reason"] = "body is not a JSON object"
        return out
    usage = doc.get("usage")
    ints = _usage_ints(usage)
    cost = _cost_or_none(usage.get("cost")) if isinstance(usage, dict) else None
    if ints is None and cost is None:
        out["reason"] = "no valid billed usage or cost in the response"
        return out
    out["parsed"] = True
    out["usage"] = ints
    out["cost"] = cost
    if ints is None:
        out["reason"] = "billed cost recorded; usage token counts missing/invalid"
    if cost is None:
        out["reason"] = "billed usage recorded; cost missing/invalid - charge unknown"
    return out


def validate_output_contract(content: str) -> dict:
    """Validate the frozen single-score JSON output contract.

    JSON object only (no prose/fences); status ok -> finite numeric score in
    [0,1]; insufficient_evidence -> score must be null; the required fields
    (why + the five diagnostics) must carry their declared types. Malformed
    content raises Refusal (run stops, raw output retained).
    """
    try:
        obj = json_loads_strict(content)
    except ValueError:
        raise Refusal(EXIT_STOPPED,
                      "output contract: content is not a single bare JSON object")
    if not isinstance(obj, dict):
        raise Refusal(EXIT_STOPPED, "output contract: top level is not an object")
    status = obj.get("status")
    if status == "ok":
        if "score" not in obj:
            raise Refusal(EXIT_STOPPED, "output contract: status ok requires a score")
        score = obj["score"]
        if isinstance(score, bool) or not isinstance(score, (int, float)) \
                or not math.isfinite(float(score)):
            raise Refusal(EXIT_STOPPED,
                          f"output contract: status ok requires a finite numeric "
                          f"score, got {score!r}")
        if not 0.0 <= float(score) <= 1.0:
            raise Refusal(EXIT_STOPPED,
                          f"output contract: score {float(score)} outside [0,1]")
    elif status == "insufficient_evidence":
        if "score" not in obj or obj["score"] is not None:
            raise Refusal(EXIT_STOPPED,
                          "output contract: status insufficient_evidence requires "
                          f"\"score\": null, got {obj.get('score')!r}")
    else:
        raise Refusal(EXIT_STOPPED,
                      "output contract: status must be one of "
                      f"{OUTPUT_STATUSES}, got {status!r}")
    why = obj.get("why")
    if not isinstance(why, str) or not why.strip():
        raise Refusal(EXIT_STOPPED, "output contract: 'why' must be a non-empty string")
    for field in (f for f in OUTPUT_CONTRACT_FIELDS if f != "evidence_ids"):
        v = obj.get(field)
        if not isinstance(v, str) or not v.strip():
            raise Refusal(EXIT_STOPPED,
                          f"output contract: '{field}' must be a non-empty string, "
                          f"got {v!r}")
    ev = obj.get("evidence_ids")
    ev_ok = ((isinstance(ev, str) and ev.strip())
             or (isinstance(ev, list) and bool(ev)
                 and all(isinstance(x, str) and x.strip() for x in ev)))
    if not ev_ok:
        raise Refusal(EXIT_STOPPED,
                      "output contract: 'evidence_ids' must be a non-empty string "
                      f"or a list of non-empty strings, got {ev!r}")
    return obj


def validate_response(status: int, raw: str, requested_model: str,
                      reserved_in: int, caps: dict) -> dict:
    """Returns evidence fields; raises Refusal on any stop condition."""
    if status != 200:
        low = raw.lower()
        if "context" in low and ("length" in low or "window" in low
                                 or "maximum" in low):
            raise Refusal(EXIT_STOPPED, f"provider returned HTTP {status}: "
                                        "context overflow")
        raise Refusal(EXIT_STOPPED, f"provider returned HTTP {status}")
    try:
        doc = json_loads_strict(raw)
    except ValueError:
        raise Refusal(EXIT_STOPPED, "unexpected provider shape: body is not strict JSON")
    if not isinstance(doc, dict) or "error" in doc:
        raise Refusal(EXIT_STOPPED,
                      f"unexpected provider shape: {json.dumps(doc)[:200]}")
    choices = doc.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise Refusal(EXIT_STOPPED, "incomplete output: no choices")
    choice = choices[0]
    message = choice.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise Refusal(EXIT_STOPPED, "incomplete output: empty assistant content")
    finish = choice.get("finish_reason")
    if not isinstance(finish, str) or not finish:
        raise Refusal(EXIT_STOPPED, "incomplete output: missing finish_reason")
    if finish != "stop":
        raise Refusal(EXIT_STOPPED, f"truncated/non-final output: "
                                    f"finish_reason={finish!r}")
    model = doc.get("model")
    if model != requested_model:
        raise Refusal(EXIT_STOPPED,
                      f"model substitution: requested {requested_model!r}, "
                      f"returned {model!r}")
    usage = doc.get("usage")
    if not isinstance(usage, dict):
        raise Refusal(EXIT_STOPPED, "missing billed usage")
    ints = _usage_ints(usage)
    if ints is None:
        raise Refusal(EXIT_STOPPED,
                      f"missing/invalid billed usage: {json.dumps(usage)[:120]}")
    cost = _cost_or_none(usage.get("cost"))
    if cost is None:
        raise Refusal(EXIT_STOPPED,
                      f"missing/invalid billed cost: {usage.get('cost')!r} "
                      "(must be a finite non-negative number)")
    if ints["prompt_tokens"] > caps["per_call_max_input_tokens"]:
        raise Refusal(EXIT_STOPPED,
                      f"billed input {ints['prompt_tokens']} exceeds the preserved "
                      f"per-call input proposal "
                      f"{caps['per_call_max_input_tokens']}")
    if ints["prompt_tokens"] > reserved_in:
        raise Refusal(EXIT_STOPPED,
                      f"reservation/accounting failure: billed input "
                      f"{ints['prompt_tokens']} > reserved {reserved_in}")
    if ints["completion_tokens"] > RESERVED_OUTPUT_TOKENS_PER_CALL:
        raise Refusal(EXIT_STOPPED,
                      f"reservation/accounting failure: billed output "
                      f"{ints['completion_tokens']} > reserved "
                      f"{RESERVED_OUTPUT_TOKENS_PER_CALL}")
    parsed_output = validate_output_contract(content)
    return {"http_status": status, "finish_reason": finish,
            "returned_model": doc.get("model"),
            "returned_provider": doc.get("provider"),
            "usage": usage, "cost": cost,
            "billed_input_tokens": ints["prompt_tokens"],
            "billed_output_tokens": ints["completion_tokens"],
            "parsed_output": parsed_output}


def probe_reservation_units() -> int:
    """Administrative reservation units for one probe (same unit arithmetic as
    scoring reservations: UTF-8 bytes + fixed framing allowance). All four probe
    slots carry byte-identical fixed messages, so one figure covers every slot."""
    return (len(PROBE_SYSTEM.encode("utf-8")) + len(PROBE_USER.encode("utf-8"))
            + FIXED_OVERHEAD_TOKENS_PER_CALL)


def build_probe_request(model: str, settings: dict | None = None) -> dict:
    """Fixed, tiny, non-country probe payload: no dossier, no case, no rating
    field, no cache/fallback directives (same request whitelist as scoring).
    ``settings`` is PROBE_SETTINGS for the originals or FOLLOWUP_PROBE_SETTINGS
    (identical except max output = the scoring setting) for the adaptive
    follow-ups."""
    if model not in MODELS:
        raise Refusal(EXIT_GATE, f"probe model not pre-registered: {model!r}")
    return build_request(model, PROBE_SYSTEM, PROBE_USER,
                         settings or PROBE_SETTINGS)


def validate_probe_response(status: int, raw: str, model: str,
                            reserved_units: int, caps: dict,
                            max_output: int = PROBE_MAX_OUTPUT_TOKENS) -> dict:
    """Probe validation covers transport + response schema + usage ONLY.

    It deliberately does NOT evaluate any output contract: a probe is not a
    result, proves nothing about future provider behavior, token bounds or
    scoring validity.
    """
    if status != 200:
        low = raw.lower()
        if "context" in low and ("length" in low or "window" in low
                                 or "maximum" in low):
            raise Refusal(EXIT_STOPPED,
                          f"probe provider returned HTTP {status}: context overflow")
        raise Refusal(EXIT_STOPPED, f"probe provider returned HTTP {status}")
    try:
        doc = json_loads_strict(raw)
    except ValueError:
        raise Refusal(EXIT_STOPPED,
                      "probe: unexpected provider shape - body is not strict JSON")
    if not isinstance(doc, dict) or "error" in doc:
        raise Refusal(EXIT_STOPPED,
                      f"probe: unexpected provider shape: {json.dumps(doc)[:200]}")
    choices = doc.get("choices")
    if not isinstance(choices, list) or not choices \
            or not isinstance(choices[0], dict):
        raise Refusal(EXIT_STOPPED, "probe: incomplete output - no choices")
    choice = choices[0]
    message = choice.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise Refusal(EXIT_STOPPED, "probe: incomplete output - empty content")
    finish = choice.get("finish_reason")
    if finish != "stop":
        raise Refusal(EXIT_STOPPED, f"probe: non-final output: {finish!r}")
    if doc.get("model") != model:
        raise Refusal(EXIT_STOPPED,
                      f"probe model substitution: requested {model!r}, "
                      f"returned {doc.get('model')!r}")
    usage = doc.get("usage")
    if not isinstance(usage, dict):
        raise Refusal(EXIT_STOPPED, "probe: missing billed usage")
    ints = _usage_ints(usage)
    if ints is None:
        raise Refusal(EXIT_STOPPED,
                      f"probe: missing/invalid billed usage: "
                      f"{json.dumps(usage)[:120]}")
    cost = _cost_or_none(usage.get("cost"))
    if cost is None:
        raise Refusal(EXIT_STOPPED,
                      f"probe: missing/invalid billed cost: {usage.get('cost')!r}")
    if ints["prompt_tokens"] > caps["per_call_max_input_tokens"]:
        raise Refusal(EXIT_STOPPED,
                      f"probe billed input {ints['prompt_tokens']} exceeds the "
                      f"preserved per-call cap {caps['per_call_max_input_tokens']}")
    if ints["prompt_tokens"] > reserved_units:
        raise Refusal(EXIT_STOPPED,
                      f"probe reservation failure: billed input "
                      f"{ints['prompt_tokens']} > reserved {reserved_units}")
    if ints["completion_tokens"] > max_output:
        raise Refusal(EXIT_STOPPED,
                      f"probe reservation failure: billed output "
                      f"{ints['completion_tokens']} > reserved {max_output}")
    return {"http_status": status, "finish_reason": finish,
            "returned_model": doc.get("model"),
            "returned_provider": doc.get("provider"),
            "usage": usage, "cost": cost,
            "billed_input_tokens": ints["prompt_tokens"],
            "billed_output_tokens": ints["completion_tokens"]}


def execute(cfg) -> int:
    root = cfg["root"]
    if not cfg["execute"]:
        print("runner disabled: no --execute flag. " + usage())
        return EXIT_USAGE

    manifest = load_json(root / "frozen" / "manifest.json")
    verify_frozen(manifest, root, cfg["data_path"])
    caps = declared_limits(manifest)
    sched = load_json(root / "frozen" / "schedule.json")
    msgs = load_json(root / "frozen" / "user_messages.json")

    receipt_path = cfg["receipt"] or (root / RECEIPT_NAME)
    archival_path = root / ARCHIVAL_RECEIPT_NAME
    if receipt_path.is_file() \
            and receipt_path.resolve() == archival_path.resolve():
        raise Refusal(EXIT_GATE,
                      f"{ARCHIVAL_RECEIPT_NAME} is archival immutable evidence of "
                      f"the original phase - execution requires the separately "
                      f"named amended receipt {RECEIPT_NAME}")
    if not receipt_path.is_file():
        raise Refusal(EXIT_GATE,
                      f"no reviewed amended preflight receipt at {receipt_path} - "
                      f"the separately named {RECEIPT_NAME} (schema "
                      f"{RECEIPT_VERSION}, binding the amended runner, protocol, "
                      "independent reviews and the archival original receipt "
                      "bytes) is required; execution refused")
    if not archival_path.is_file():
        raise Refusal(EXIT_GATE,
                      f"archival original receipt {ARCHIVAL_RECEIPT_NAME} missing - "
                      "original evidence must stay preserved; execution refused")
    archival = load_json(archival_path)
    if archival.get("receipt_version") != ARCHIVAL_RECEIPT_VERSION:
        raise Refusal(EXIT_GATE,
                      f"archival {ARCHIVAL_RECEIPT_NAME} must remain the original "
                      f"schema-{ARCHIVAL_RECEIPT_VERSION} receipt (found "
                      f"{archival.get('receipt_version')!r}) - it is immutable "
                      "archival evidence, never the execution receipt")
    bindings = current_bindings(root, cfg["data_path"])
    receipt = load_json(receipt_path)
    verify_receipt(receipt, bindings, manifest)
    receipt_sha = sha(receipt_path.read_bytes())
    live = (receipt.get("provider_semantics") or {}).get("live_behavior") or {}

    probe_mode = bool(cfg.get("probe"))
    run_dir = None
    slot = None
    if probe_mode:
        slot = validate_probe_slot(cfg["run_id"], root)
    else:
        run_dir = validate_run_id(cfg["run_id"], root)
        if live.get("status") != "observed_in_bounded_probe":
            raise Refusal(EXIT_GATE,
                          "live provider behavior is unobserved (documentation only) "
                          "- scoring refused until the amended receipt records a "
                          "bounded-probe observation hash-binding all four probe "
                          "results and reviews plus the structured original-failure "
                          "disclosure; this worker creates no receipt, no review and "
                          "no probe")

    # ---- experiment-wide exclusive lock: acquired BEFORE reading prior state
    # ---- or deciding any budget, held through dispatch and finalization.
    lock_path = acquire_lock(root, cfg["run_id"])
    try:
        if probe_mode:
            return _execute_probe(cfg, root, manifest, caps, sched, receipt,
                                  receipt_sha, bindings, slot, live)
        return _execute_scoring(cfg, root, manifest, caps, sched, msgs, receipt,
                                receipt_sha, bindings, run_dir)
    finally:
        release_lock(lock_path, cfg["run_id"])


def _execute_scoring(cfg, root, manifest, caps, sched, msgs, receipt,
                     receipt_sha, bindings, run_dir) -> int:
    prior = prior_run_state(root, sched)
    prior_gate_reason = prior_gate(prior, sched)
    if prior_gate_reason:
        raise Refusal(EXIT_GATE, prior_gate_reason)
    probe_gate_reason = scoring_probe_gate(prior, root, bindings)
    if probe_gate_reason:
        raise Refusal(EXIT_GATE, probe_gate_reason)
    verify_probe_observation(receipt, root)
    dispatch_reason = total_dispatch_violation(prior, ATTEMPT_CEILING)
    if dispatch_reason:
        raise Refusal(EXIT_GATE, dispatch_reason)

    plan = build_plan(manifest, sched, msgs, caps)
    if plan["problems"]:
        raise Refusal(EXIT_GATE,
                      "worst-case reservation does not fit the DECLARED ceilings "
                      "(ceilings are never raised): " + "; ".join(plan["problems"])
                      + f" [method: {plan['input_method']}]")
    plan["_sched"] = sched

    prices = cfg["price_fetch"]()                     # network: only after all gates
    cost_reservation(plan, prices)
    total_usd = sum(plan["worst_usd"])
    if not math.isfinite(total_usd) or total_usd < 0:
        raise Refusal(EXIT_GATE, "worst-case cost reservation is not a finite "
                                 "non-negative number")
    budget_reason = prior_budget_violation(prior, plan, total_usd)
    if budget_reason:
        raise Refusal(EXIT_GATE,
                      budget_reason + " (prior runs stay accounted - the budget "
                      "is never silently reset)")
    if total_usd > caps["aggregate_max_usd_including_failures"]:
        raise Refusal(EXIT_GATE,
                      f"worst-case cost ${total_usd:.4f} exceeds the "
                      f"${caps['aggregate_max_usd_including_failures']:.2f} maximum; "
                      "refusing to dispatch")

    secret = cfg["secret_loader"]()
    if not secret:
        raise Refusal(EXIT_GATE, f"{SECRET_ENV} is empty or unset - refusing")

    # read/decode the frozen prompts BEFORE creating any directory, so a decode
    # failure can never leave an orphan run directory
    prompt_by_variant = {v: (root / "frozen" / f"single_{v.lower()}.txt")
                         .read_text(encoding="utf-8") for v in ("A", "B")}

    (root / RUNS_DIR).mkdir(exist_ok=True)
    try:
        run_dir.mkdir()
    except FileExistsError:
        raise Refusal(EXIT_GATE, f"run {cfg['run_id']!r} already exists")
    (run_dir / "attempts").mkdir()
    cfg["_run_dir"] = run_dir

    run_record = {
        "run_id": cfg["run_id"], "status": "in_progress", "started_at": utcnow(),
        "api_base": API_BASE, "models": list(MODELS),
        "requested_settings": REQUESTED_SETTINGS,
        "manifest_sha256": bindings["frozen/manifest.json"],
        "receipt_sha256": receipt_sha, "receipt_bindings": bindings,
        "preflight_signoff": receipt["preflight"],
        "provider_semantics": receipt["provider_semantics"],
        "reservation_amendment": manifest.get("reservation_amendment"),
        "prior_run_state": {"prior_runs": prior["runs"],
                            "used_usd": round(prior["used_usd"], 6),
                            "used_input_tokens": prior["used_input"],
                            "used_output_tokens": prior["used_output"],
                            "probe_slots": prior["probe_slots"],
                            "probe_dispatched": prior["probe_dispatched"]},
        "plan": {k: v for k, v in plan.items() if k != "_sched"},
        "prices_usd_per_token": prices,
        "attempt_ceiling": caps["attempt_ceiling_including_failures"],
        "total_dispatch_ceiling": TOTAL_DISPATCH_CEILING,
        "usd_ceiling": caps["aggregate_max_usd_including_failures"],
        "budget_note": "USD ceiling enforced locally by this runner; not a "
                       "provider-enforced spend limit; in-run USD comparisons "
                       "include prior shared spend (probes + earlier runs) while "
                       "used_usd stays run-local",
    }
    write_exclusive(run_dir / "run.json", json.dumps(run_record, indent=1,
                                                     ensure_ascii=False) + "\n")

    used = {"input": 0, "output": 0, "usd": 0.0, "reserved_in": 0}
    # shared experiment spend (prior probes + earlier runs, already validated
    # finite by prior_budget_violation above): included in EVERY in-run USD
    # comparison below, while result.json's used_usd stays run-local so future
    # ledger scans sum prior + run exactly once.
    prior_usd = prior["used_usd"]
    attempted, seen = [], set()
    stop_reason = None
    liability = None
    raw = None
    for idx, row in enumerate(sched):
        raw = None                      # never carry a previous attempt's body forward
        violation = ceiling_violation(idx, len(attempted), plan, used, prior_usd)
        if violation:
            stop_reason = violation
            break
        if cell_key(row) in seen:
            stop_reason = (f"predeclared cell already attempted: "
                           f"{cell_key(row)!r} - one attempt per cell maximum")
            break
        seen.add(cell_key(row))
        prompt = prompt_by_variant[row["variant"]]
        message = msgs[idx]["message"]
        try:
            payload = build_request(row["model"], prompt, message,
                                    manifest["requested_settings"])
        except Refusal as gate_stop:
            stop_reason = f"stop before dispatch: {gate_stop.reason}"
            break
        headers = {"Content-Type": "application/json",
                   "Authorization": "[REDACTED]"}
        real_headers = {"Content-Type": "application/json",
                        "Authorization": "Bearer " + secret}
        record = {
            "call": row["call"], "block": row["block"], "draw": row["draw"],
            "case": row["case"], "sentinel": row["sentinel"],
            "variant": row["variant"], "label": row["label"],
            "requested_model": row["model"],
            "requested_settings": REQUESTED_SETTINGS,
            "system_prompt_sha256": sha(prompt.encode("utf-8")),
            "user_message_sha256": sha(message.encode("utf-8")),
            "preflight_receipt_sha256": receipt_sha,
            "manifest_sha256": bindings["frozen/manifest.json"],
            "source_bindings": bindings,
            "reserved_input_tokens": plan["per_call_input"][idx],
            "reserved_output_tokens": RESERVED_OUTPUT_TOKENS_PER_CALL,
            "reserved_usd": plan["worst_usd"][idx],
            "request_headers_logged": headers,
            "requested_at": utcnow(),
            "errors": [],
        }
        try:
            status, raw = cfg["transport"](CHAT_URL, payload, real_headers,
                                           TIMEOUT_SECONDS)
            evidence = validate_response(status, raw, row["model"],
                                         plan["per_call_input"][idx], caps)
        except Refusal as stop:
            # Preserve the raw body and record any parseable billed usage/cost
            # SEPARATELY from the validated fields, even if the output itself is
            # what failed validation; an unknown charge is an unreconciled
            # liability, never assumed to be zero spend.
            billed = parse_billed(raw)
            record["billed_on_failure"] = billed
            record["raw_response"] = raw
            record["errors"].append(stop.reason)
            record["stop_reason"] = stop.reason
            record["finished_at"] = utcnow()
            if billed["cost"] is None:
                liability = {
                    "reason": billed["reason"] or "billed cost unknown",
                    "call": row["call"],
                    "requires": "human-reviewed reconciliation "
                                f"(runs/{cfg['run_id']}/reconciliation.json) "
                                "before any new run may start"}
                record["unreconciled_liability"] = liability
            write_exclusive(run_dir / "attempts"
                            / f"call-{row['call']:03d}.json",
                            json.dumps(record, indent=1, ensure_ascii=False) + "\n")
            attempted.append(row["call"])
            # the reservation for this dispatched attempt is consumed and any
            # parseable billing is added to the run tallies
            used["reserved_in"] += plan["per_call_input"][idx]
            if billed.get("usage"):
                used["input"] += billed["usage"]["prompt_tokens"]
                used["output"] += billed["usage"]["completion_tokens"]
            if billed["cost"] is not None:
                used["usd"] += billed["cost"]
            stop_reason = stop.reason
            break
        record.update(evidence)
        record["raw_response"] = raw              # exact provider response bytes
        record["finished_at"] = utcnow()
        record["requested_vs_actual"] = {
            "reserved_input_tokens": plan["per_call_input"][idx],
            "billed_input_tokens": evidence["billed_input_tokens"],
            "reserved_output_tokens": RESERVED_OUTPUT_TOKENS_PER_CALL,
            "billed_output_tokens": evidence["billed_output_tokens"],
            "reserved_usd": plan["worst_usd"][idx],
            "billed_usd": evidence["cost"],
        }
        write_exclusive(run_dir / "attempts" / f"call-{row['call']:03d}.json",
                        json.dumps(record, indent=1, ensure_ascii=False) + "\n")
        attempted.append(row["call"])
        used["reserved_in"] += plan["per_call_input"][idx]
        used["input"] += evidence["billed_input_tokens"]
        used["output"] += evidence["billed_output_tokens"]
        used["usd"] += evidence["cost"]
        if used["usd"] + prior_usd > caps["aggregate_max_usd_including_failures"]:
            stop_reason = (f"USD ceiling exceeded by billed usage: shared "
                           f"${used['usd'] + prior_usd:.6f} = run-local "
                           f"${used['usd']:.6f} + prior ${prior_usd:.6f} > "
                           f"${caps['aggregate_max_usd_including_failures']:.2f}")
            break
        if used["input"] > caps["aggregate_max_input_tokens"]:
            stop_reason = ("preserved aggregate input proposal exceeded by billed "
                           f"native tokens: {used['input']} > "
                           f"{caps['aggregate_max_input_tokens']}")
            break
        if used["output"] > caps["aggregate_max_output_tokens"]:
            stop_reason = "aggregate output ceiling exceeded by billed usage"
            break

    run_record.update({
        "status": "completed" if stop_reason is None else "stopped",
        "stop_reason": stop_reason,
        "finished_at": utcnow(),
        "attempts": len(attempted),
        "attempted_calls": attempted,
        "unreconciled_liability": liability,
        "used_input_tokens": used["input"],
        "used_output_tokens": used["output"],
        "used_reserved_input_units": used["reserved_in"],
        "used_usd": round(used["usd"], 6),
    })
    write_exclusive(run_dir / "result.json",
                    json.dumps(run_record, indent=1, ensure_ascii=False) + "\n")
    if stop_reason is not None:
        print(f"STOP  {stop_reason}")
        return EXIT_STOPPED
    print(f"run {cfg['run_id']}: completed {len(attempted)} attempts "
          f"({used['input']} in / {used['output']} out tokens, "
          f"${used['usd']:.6f})")
    return EXIT_OK


def _execute_probe(cfg, root, manifest, caps, sched, receipt, receipt_sha,
                   bindings, slot, live) -> int:
    """Dispatch ONE registered probe slot (original or adaptive follow-up),
    exactly once, with no retry under the experiment-wide lock, writing only
    probes/<slot>/. Probe charges and attempts join the same ledger as scoring
    (probe-amendment.md as amended by probe-followup-amendment.md). Follow-up
    slots additionally require intact original evidence and the frozen slot
    order before any dispatch."""
    model = PROBE_SLOT_MODELS[slot]
    settings = PROBE_SLOT_SETTINGS[slot]
    max_output = PROBE_SLOT_MAX_OUTPUT[slot]
    is_followup = slot in FOLLOWUP_PROBE_SLOTS

    prior = prior_run_state(root, sched)
    gate = prior_gate(prior, [])     # unknown/unreconciled block probes as well
    if gate:
        raise Refusal(EXIT_GATE, gate)
    if live.get("status") == "observed_in_bounded_probe":
        verify_probe_observation(receipt, root)   # claimed evidence must verify
    reason = probe_dispatch_gate(prior, slot, root, bindings)
    if reason:
        raise Refusal(EXIT_GATE, reason)

    prices = cfg["price_fetch"]()                    # network: only after all gates
    reserved_units = probe_reservation_units()
    worst = (reserved_units * prices[model]["prompt"]
             + max_output * prices[model]["completion"])
    if not math.isfinite(worst) or worst < 0:
        raise Refusal(EXIT_GATE, "probe worst-case cost is not a finite "
                                 "non-negative number")
    probe_plan = {"caps": caps, "aggregate_input": reserved_units,
                  "aggregate_output": max_output,
                  "is_probe": True}
    budget = prior_budget_violation(prior, probe_plan, worst)
    if budget:
        raise Refusal(EXIT_GATE,
                      budget + " (probe charges share the same local USD ledger; "
                      "never reset)")

    secret = cfg["secret_loader"]()
    if not secret:
        raise Refusal(EXIT_GATE, f"{SECRET_ENV} is empty or unset - refusing")

    payload = build_probe_request(model, settings)
    headers = {"Content-Type": "application/json", "Authorization": "[REDACTED]"}
    real_headers = {"Content-Type": "application/json",
                    "Authorization": "Bearer " + secret}
    # Record binding: ORIGINAL slots chain to the archival original receipt
    # (the protocol they were executed under - as the real archived originals
    # do); adaptive follow-up slots chain to the amended receipt in force.
    slot_receipt_sha = receipt_sha if is_followup \
        else bindings[ARCHIVAL_RECEIPT_NAME]

    (root / PROBES_DIR).mkdir(exist_ok=True)
    probe_dir = root / PROBES_DIR / slot
    try:
        probe_dir.mkdir()
    except FileExistsError:
        raise Refusal(EXIT_GATE, f"probe slot {slot!r} already exists - no overwrite")
    dispatch_doc = {
        "slot": slot, "model": model,
        "attempt_kind": "operational_probe",
        "attempt_phase": "adaptive_followup" if is_followup else "original",
        "scoring_request": False,
        "scope": "transport/schema/usage only; makes no "
                 "claim about future provider behavior, "
                 "token bounds or scoring validity",
        "request": payload,
        "request_sha256":
            sha(json.dumps(payload, sort_keys=True).encode("utf-8")),
        "reserved_input_units": reserved_units,
        "reserved_output_tokens": max_output,
        "reserved_usd": worst,
        "preflight_receipt_sha256": slot_receipt_sha,
        "manifest_sha256": bindings["frozen/manifest.json"],
        "probe_amendment_sha256": bindings["probe-amendment.md"],
        "request_headers_logged": headers,
        "dispatched_at": utcnow(), "retry": False}
    if is_followup:
        dispatch_doc["probe_followup_amendment_sha256"] = \
            bindings["probe-followup-amendment.md"]
        dispatch_doc["adapted_after"] = {
            "original_failure_slot": ORIGINAL_FAILURE_SLOT,
            "note": "adaptive-after-failure: the original 64-token output probe "
                    f"{ORIGINAL_FAILURE_SLOT} recorded a failure; recorded in "
                    "probe-followup-amendment.md before this dispatch"}
    write_exclusive(probe_dir / "dispatch.json",
                    json.dumps(dispatch_doc, indent=1, ensure_ascii=False) + "\n")

    record = {"slot": slot, "model": model,
              "attempt_kind": "operational_probe",
              "attempt_phase": "adaptive_followup" if is_followup else "original",
              "scoring_request": False,
              "requested_settings": settings,
              "reserved_input_units": reserved_units,
              "reserved_output_tokens": max_output,
              "preflight_receipt_sha256": slot_receipt_sha,
              "request_headers_logged": headers,
              "errors": [], "retry": False,
              "started_at": utcnow()}
    raw = None
    status = None
    try:
        status, raw = cfg["transport"](CHAT_URL, payload, real_headers,
                                       TIMEOUT_SECONDS)
        evidence = validate_probe_response(status, raw, model, reserved_units,
                                           caps, max_output)
    except Refusal as stop:
        billed = parse_billed(raw)
        record.update({"status": "stopped", "raw_response": raw,
                       "stop_reason": stop.reason, "errors": [stop.reason],
                       "billed_on_failure": billed, "finished_at": utcnow(),
                       "used_input_tokens": (billed["usage"] or {}).get(
                           "prompt_tokens", 0) if billed.get("usage") else 0,
                       "used_output_tokens": (billed["usage"] or {}).get(
                           "completion_tokens", 0) if billed.get("usage") else 0,
                       "used_usd": billed["cost"] or 0.0})
        if status is not None:
            # captured only because an HTTP status was actually received; a
            # transport failure records none and historical records are never
            # backfilled.
            record["http_status"] = status
        if billed["cost"] is None:
            record["unreconciled_liability"] = {
                "reason": billed["reason"] or "probe charge unknown",
                "call": slot,
                "requires": "human-reviewed reconciliation "
                            f"({PROBES_DIR}/{slot}/reconciliation.json) before any "
                            "scoring or further probe may start"}
        write_exclusive(probe_dir / "probe-result.json",
                        json.dumps(record, indent=1, ensure_ascii=False) + "\n")
        print(f"STOP  probe {slot}: {stop.reason}")
        return EXIT_STOPPED
    record.update(evidence)
    record.update({"status": "completed", "raw_response": raw,
                   "finished_at": utcnow(),
                   "used_input_tokens": evidence["billed_input_tokens"],
                   "used_output_tokens": evidence["billed_output_tokens"],
                   "used_usd": evidence["cost"]})
    write_exclusive(probe_dir / "probe-result.json",
                    json.dumps(record, indent=1, ensure_ascii=False) + "\n")
    phase = ("adaptive follow-up" if is_followup else "original")
    print(f"probe {slot} ({phase}): completed 1 dispatch ({model}, "
          f"{evidence['billed_input_tokens']} in / "
          f"{evidence['billed_output_tokens']} out tokens, "
          f"${evidence['cost']:.6f}); independent review of {PROBES_DIR}/{slot}/"
          "probe-result.json is required before scoring")
    return EXIT_OK


def _finalize_orphan(cfg: dict, kind: str, exc) -> None:
    """A failure after the run directory exists must still leave a terminal
    record, so no run directory is ever orphaned as 'in_progress'."""
    run_dir = cfg.get("_run_dir")
    if not run_dir:
        return
    run_dir = Path(run_dir)
    if not run_dir.is_dir() or (run_dir / "result.json").exists():
        return
    try:
        write_exclusive(run_dir / "result.json",
                        json.dumps({"run_id": cfg.get("run_id"),
                                    "status": "failed_closed",
                                    "finished_at": utcnow(),
                                    "stop_reason": f"unexpected {kind}: "
                                                   f"{type(exc).__name__}: {exc}"},
                                   indent=1) + "\n")
    except OSError:
        pass


def run(cfg: dict) -> int:
    try:
        return execute(cfg)
    except Refusal as refusal:
        _finalize_orphan(cfg, "refusal", refusal)
        print("STOP  " + refusal.reason)
        return refusal.code
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        _finalize_orphan(cfg, "error", exc)
        print(f"STOP  fail-closed on {type(exc).__name__}: {exc}")
        return EXIT_GATE


def make_cfg(opts: dict) -> dict:
    return {"execute": opts["execute"], "run_id": opts["run_id"],
            "probe": bool(opts.get("probe")),
            "receipt": Path(opts["receipt"]) if opts["receipt"] else None,
            "root": HERE, "data_path": ROOT / "data" / "countries.json",
            "transport": None, "price_fetch": None, "secret_loader": None}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        opts = parse_args(argv)
        cfg = make_cfg(opts)
        if cfg["transport"] is None:
            cfg["transport"] = https_post
        if cfg["price_fetch"] is None:
            cfg["price_fetch"] = fetch_prices
        if cfg["secret_loader"] is None:
            cfg["secret_loader"] = load_secret
        return run(cfg)
    except Refusal as refusal:
        print("STOP  " + refusal.reason)
        if refusal.code == EXIT_USAGE:
            print(usage())
        return refusal.code


if __name__ == "__main__":
    sys.exit(main())