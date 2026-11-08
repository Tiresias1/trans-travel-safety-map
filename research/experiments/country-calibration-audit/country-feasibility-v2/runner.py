#!/usr/bin/env python3
"""Disabled-by-default provider runner for country-feasibility-v2 stage one.

OFFLINE BY DEFAULT. This module does nothing unless it is invoked with an
explicit ``--execute`` flag AND a reviewed v2 preflight receipt
(``preflight_receipt_v2.json``) whose recorded hashes equal the current SHA-256
of every bound input. Without both gates it never reads a credential, never
resolves a hostname, never opens a socket and never writes a byte
(``main([])`` prints usage and exits 2). No receipt exists at preparation time
and the three independent review artifacts it must bind (methodology, code,
evidence) are absent until produced, so execution is refused fail-closed today.

v2 stage one is a NEW, explicitly ADAPTIVE feasibility diagnostic prepared after
the closed v1 failure (run ``country-feasibility-20261108-v1``: one attempted
cell, no final score, 39 cells never attempted). It does not resume, amend or
satisfy v1's no-retry contract, and v1's files must remain byte-identical.
The v1 failure record preserves provider partial reasoning text containing
provisional numerical musings that reviewers saw; no such provisional number is
reproduced here and none was used to choose countries, models, prompt wording,
schedule, sentinels or settings. The design states no desired scores.

Design (frozen in ``frozen/schedule.json`` before any v2 attempt exists):
exactly 20 attempts maximum = 16 core cells (4 countries USA/GBR/NPL/VAT x
2 exact model ids x 2 reviewed prompt variants A/B x 1 draw) + 4 anonymous
empty-dossier sentinels (model x variant), in one fixed randomized interleaved
order of 2 balanced blocks of 10. One draw per cell cannot estimate within-cell
repeat variance; with no neutral-label cells the design cannot test label
invariance; nothing here validates country rankings. Feasibility diagnostics
only.

Inputs: the exact v1 single-country prompt bytes (``frozen/single_a.txt`` /
``single_b.txt``) and the exact v1 evidence-message bytes (embedded in
``frozen/user_messages.json``, each hash-checked against the v1 originals).
No published scores and no sub-national (ADM1) values are inputs; the rubric is
unchanged because the prompt bytes are unchanged - including: 0.00 means a trans
visitor who is outed faces near-certain imprisonment AND likely execution; no
passing/stealth/concealment credit; ``unknown`` intermediates are never
resolved toward the midpoint.

Execution gates, in order, all fail-closed:

  1. explicit ``--execute`` flag (no credential may be passed on the CLI);
  2. valid path-safe ``--run-id`` (existence/overwrite checked under the lock);
  3. frozen-input self-check: v2 frozen files match ``frozen/manifest.json``
     and every manifest constant (settings, ceilings, plan, prior accounting,
     expected providers) equals this module's predeclared constants;
  4. schedule/message structural check (20 rows, cell composition, balance,
     message hashes and byte-identity to the v1 source rows);
  5. ONE SHARED EXCLUSIVE LOCK: ``../country-feasibility/.execution.lock`` -
     the same file and O_EXCL mechanism the closed v1 runner used - acquired
     BEFORE any ledger or prior state is read and held through dispatch and
     finalization. Contention, or a stale lock left by a crash, refuses before
     any call; a lock is never deleted by anyone but its own holder;
  6. reviewed v2 preflight receipt (absent until reviewed): exact binding of
     all v2 frozen inputs, this protocol (``protocol.md``), this code
     (``runner.py``, ``test_runner.py``), the source data
     (``data/countries.json``), the pinned v1 source records, and the three
     independent review artifacts (methodology / code / evidence);
  7. v1 prior-state reconstruction, read-only and pinned: every consumed v1
     file's SHA-256 is checked against a known constant; the exact prior cost
     is reconstructed with ``decimal.Decimal`` directly from the four
     ``probe-result.json`` files and v1 ``call-001`` ``billed_on_failure``
     (must total USD 0.001993276); provider response ids are deduplicated and
     pinned; any missing, unknown, duplicate or drifted record stops before
     dispatch. v1 data is never written;
  8. v2 prior-run state + the STRICT per-answer semantic checkpoint
     (pre-registered before outcomes): a run directory without a terminal
     ``result.json``, an unreadable tally, an unreconciled liability, a prior
     FAILED attempt, prior attempts that are not the contiguous schedule
     prefix 1..k (no skip, no reorder), or - for EVERY completed prior output
     - a MISSING / FAIL / UNCERTAIN / hash-tampered independent semantic
     review (``runs/<run-id>/semantic-reviews/call-NNN.json``, verdict PASS,
     bound to response_sha256, the score-blind sidecar hash, the frozen
     system-prompt and user-message hashes and RUBRIC_VERSION, with named
     reviewer identity/session) blocks ALL later calls BEFORE price fetch,
     credential read or any network access. Stale/incomplete state is never
     overwritten, repaired or retried, and this runner never writes a review;
     9. combined limits: all 5 previous dispatches + at most 20 new = 25
     maximum (each invocation dispatches AT MOST ONE next cell); all costs
     (prior exact decimals + new) against the same locally enforced USD 10.00
     guard - there is no provider-side hard spend guarantee;
     input reservation = UTF-8 bytes of prompt+message + a fixed 128-unit
     chat-framing allowance per call, an ASSUMED conservative administrative
     unit, explicitly not a guaranteed provider tokenizer bound;
 10. price metadata over the fixed HTTPS endpoint (after all gates); unknown /
     non-positive / non-finite prices refuse;
 11. credential from the environment only (never logged, never on the CLI).

One cell per invocation: each ``--execute`` run dispatches AT MOST the single
next not-yet-attempted scheduled cell under the shared lock, appends the
immutable raw/billing evidence plus a SCORE-BLIND structured sidecar
(status/why/evidence_ids/discovery/direct_harms/scope_triggers/uncertainty
copied verbatim WITHOUT the numeric score key, plus the exact frozen dossier
hashes), then terminates ``paused_pending_semantic_review`` until an
independent reviewer records a PASS verdict; the next invocation may dispatch
only call k+1. Overall the stage stays at <= 20 v2 attempts and <= 25
provider dispatches including v1's five, all against the same local USD 10.00
guard with v1's exact prior charges. Partial outputs and outcome-dependent
stopping are documented limitations; nothing here publishes scores or
rankings, and review verdicts are never forged or auto-authored by code.

The single predeclared GENERATION-settings change versus v1:
``max_output_tokens`` 2000 -> 11000 (temperature/top_p unchanged; no explicit
reasoning parameter, because v1 requested none). Basis: the prior separate
pilot2 instrument's 95/96 parseable logical calls at an 11000-token allowance
- operational precedent only, explicitly not a guarantee and not proof that
the cap caused the v1 failure. 11000 is the maximum billed output per call
INCLUDING any provider reasoning tokens.

One transport-only adjustment (NOT a generation setting): the chat-request
socket timeout is predeclared as 300 s (v1 used 30 s). The pinned call-001
took 28 s for only 2000 completion tokens and still ended ``length``, so an
11000-token non-streaming response plausibly needs minutes of server silence;
leaving 30 s would abort with no raw body and record a permanent unreconciled
liability. The price-fetch timeout stays 30 s. Timeout behavior remains
fail-closed: a socket timeout still raises a transport-error refusal, stops
the stage before any further dispatch, and an unknown charge stays an
unreconciled liability.

Dispatch protocol: fixed HTTPS OpenRouter endpoint, exact model ids, one
sequential fresh system+user context per cell built only from frozen bytes,
one attempt per predeclared cell, ZERO retries, no fallback model list, no
force-cache directives. Strict validation stops the whole stage immediately on
any failed/truncated/invalid output, API error (HTTP != 200 or error object),
model substitution or unexpected routing (provider outside the predeclared
per-model set observed in reviewed prior records), unknown or inconsistent
billing/usage (missing/non-finite cost, totals mismatch, BYOK, cache WRITE
tokens whose billing cannot be reconciled with the advertised prices,
missing or inconsistent reasoning-count semantics - the
reasoning_tokens <= completion_tokens bound is a PREDECLARED FAIL-CLOSED
ASSUMPTION, not an observation: the pinned v1 failure record itself reported
reasoning 2504 > completion 2000), an EMPTY-dossier sentinel returning
anything other than ``status: insufficient_evidence`` with ``score: null``
is a TERMINAL stop (context-aware semantic check; core cells may abstain or
score under the unchanged contract), any reservation/budget/integrity
failure, or a receipt/lock/source-hash failure. Provider-initiated cache READ
tokens are allowed only when the reported usage/cost arithmetic is valid
(cached_tokens <= prompt_tokens, finite consistent cost) and are logged in
full as an execution condition - with no reproducibility claim; the request
never carries cache directives and this runner never warms, forces or busts
cache. Every attempt and its response text - the provider body decoded as
UTF-8 with replacement before storage, so exact response TEXT but not
byte-exact transport bytes - is preserved once (exclusive create);
partial/tentative reasoning values are never interpreted, extracted or
summarized by this runner.

Output contract (unchanged v1 contract): a single bare JSON object with
``status`` in {ok, insufficient_evidence}; ``status`` ok requires a finite
numeric ``score`` in [0,1]; ``insufficient_evidence`` requires ``score`` null;
plus non-empty ``why``, ``evidence_ids``, ``discovery``, ``direct_harms``,
``scope_triggers``, ``uncertainty`` strings. Malformed content stops the run
with the raw output retained; there is no retry.

    python3 runner.py                          # disabled: usage + exit 2
    python3 runner.py --execute --run-id r1    # full gate chain; stops on any gate

This worker creates or signs no receipt and no review artifact, and performs
no provider call. If the required reviewed artifacts cannot be produced, this
runner must not run: stop honestly rather than weaken a gate.

OPEN BLOCKERS carried into any receipt: (a) the STRICT per-answer semantic
checkpoint is implemented here only as a fail-closed DISPATCH GATE - the
actual human/model review verdicts, the receipt's three review artifacts and
preflight_receipt_v2.json itself must still be produced independently; this
runner never forges or auto-authores a PASS and contains no code path that
writes a review file; (b) cache policy follows the separate consult: no
cache-control directives, provider-initiated cache reads allowed only with
valid reported accounting and logged in full, cache-write billing that cannot
be reconciled with advertised prices stops the stage, no warming, no
reproducibility claim. Dispatch stays impossible until those artifacts exist.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
# The closed v1 experiment directory: shared lock lives there (read-mostly;
# v1 data is never written; only the shared transient lock may be created).
V1_ROOT = HERE.parent / "country-feasibility"

# Fixed provider endpoint (HTTPS only, not configurable from the CLI).
API_BASE = "https://openrouter.ai/api/v1"
CHAT_URL = API_BASE + "/chat/completions"
MODELS_URL = API_BASE + "/models"
# Transport-only timeout adjustment (PREDECLARED and disclosed; NOT a
# generation setting - the sole generation-settings change remains
# max_output_tokens 2000 -> 11000). v1 used 30 s for both endpoints; the
# pinned call-001 took 28 s for just 2000 completion tokens and still ended
# `length`, so an 11000-token non-streaming response plausibly needs minutes
# of server-side silence - a 30 s read timeout would abort with no raw body
# -> unknown charge -> permanent unreconciled liability. Timeout stays
# fail-closed: a socket timeout still raises Refusal(EXIT_STOPPED,
# "transport error ...") and the unknown-charge/liability path is unchanged.
TRANSPORT_TIMEOUT_SECONDS = 300.0      # chat dispatch (predeclared)
PRICE_FETCH_TIMEOUT_SECONDS = 30.0     # price metadata fetch (unchanged)
V1_TRANSPORT_TIMEOUT_SECONDS = 30.0    # v1 baseline (disclosure only)
SECRET_ENV = "OPENROUTER_API_KEY"  # the ONLY credential source; never logged

# Pre-registered models (exact ids only; no fallback, no substitution).
MODELS = ("deepseek/deepseek-v4.1-flash", "google/gemini-3.8-flash")
# Predeclared routing: the providers observed for each model in the reviewed
# prior records (probes 1-4 raw bodies; v1 call-001 raw body). Any other or
# missing provider attribution is "unexpected routing" and stops the run.
EXPECTED_PROVIDERS = {"deepseek/deepseek-v4.1-flash": ("Relace",),
                      "google/gemini-3.8-flash": ("Google",)}

# v1 requested settings, preserved except the single predeclared CHANGE to
# generation settings.
V1_REQUESTED_SETTINGS = {"temperature": 1.0, "top_p": 1.0,
                         "max_output_tokens": 2000}
REQUESTED_SETTINGS = {"temperature": 1.0, "top_p": 1.0,
                      "max_output_tokens": 11000}
# Sole GENERATION-settings change: max output 2000 -> 11000; no reasoning
# parameter because v1 had none; basis is pilot2's 95/96 parseable logical
# calls at 11000 - precedent, not a guarantee, not proof of cause. The
# chat-request timeout 30 s -> 300 s is recorded separately as transport-only.
SETTINGS_CHANGE = {
    "preserved_from_v1": {"temperature": 1.0, "top_p": 1.0},
    "changed": {"max_output_tokens": {"from": 2000, "to": 11000}},
    "sole_generation_setting_change": True,
    "basis": "prior separate pilot2 instrument: 95/96 parseable logical calls "
             "at 11000 max output tokens; operational precedent only - not a "
             "guarantee, not proof that 2000 caused the v1 failure, not "
             "semantic validation",
    "reasoning_parameter": "none added: v1 requested no explicit reasoning "
                           "parameter, so v2 requests none; 11000 caps billed "
                           "output including reasoning",
    "transport_timeout": {
        "scope": "transport-only socket timeout for the chat request; NOT a "
                 "generation setting - the sole generation-settings change "
                 "remains max_output_tokens 2000 -> 11000",
        "from_seconds": 30, "to_seconds": 300,
        "price_fetch_timeout_seconds": 30,
        "basis": "pinned call-001 took 28 s for 2000 completion tokens and "
                 "still ended finish_reason length; an 11000-token "
                 "non-streaming response plausibly needs minutes of server "
                 "silence, so the unchanged 30 s timeout would abort with no "
                 "raw body and record a permanent unreconciled liability",
        "fail_closed": "a timeout still raises a transport-error refusal, "
                       "stops the stage before any further dispatch, and an "
                       "unknown charge remains an unreconciled liability "
                       "(never assumed to be zero)"}}
# Context-aware semantic rule for the EMPTY-dossier sentinels (must equal
# frozen/manifest.json -> design.sentinel_semantics).
EMPTY_SENTINEL_RULE = (
    "empty-dossier sentinels must return status 'insufficient_evidence' with "
    "score null; any other output stops the run fail-closed (context-aware "
    "semantic check); core cells keep the unchanged contract and may abstain "
    "or score; the broader independent semantic review is a separate, "
    "still-open process")

# Stage-one design constants (must equal frozen/manifest.json).
COUNTRIES = ("USA", "GBR", "NPL", "VAT")
VARIANTS = ("A", "B")
ATTEMPT_CEILING = 20          # 16 core + 4 empty sentinels, failures included
CORE_CELLS = 16
SENTINEL_CELLS = 4
BLOCKS = 2
ROWS_PER_BLOCK = 10
DRAWS = 1
PRIOR_DISPATCHES = 5          # 4 original/adaptive probes + v1 call-001
TOTAL_DISPATCH_CEILING = 25   # all previous dispatches + at most 20 new
MAX_USD = Decimal("10.00")    # same shared locally enforced guard as v1
RETRIES = 0

# Exact prior liability, reconstructed with Decimal from the preserved records
# (4 probe-result.json used_usd + v1 call-001 billed_on_failure.cost).
PRIOR_COST_USD = Decimal("0.001993276")
PRIOR_INPUT_TOKENS = 13652    # 276 probe + 13376 call-001, exact integers
PRIOR_OUTPUT_TOKENS = 2274    # 274 probe + 2000 call-001, exact integers

# Output budgets, retained SEPARATELY (never merged, never rounded):
# older (historical v1/probe budgets + exact usage) vs new (v2 reservation).
V2_MAX_OUTPUT_PER_CALL = 11000
V2_AGG_OUTPUT_RESERVATION = ATTEMPT_CEILING * V2_MAX_OUTPUT_PER_CALL  # 220000
HISTORICAL_OUTPUT_BUDGETS = {
    "v1_aggregate_max_output_tokens": 80000,
    "probe_output_allowance_tokens": 4128,
    "v1_output_used_tokens_exact": PRIOR_OUTPUT_TOKENS}

# Input reservation arithmetic (same honest method as v1): one unit = one
# UTF-8 byte of frozen prompt+message, plus a fixed 128-unit chat-framing
# allowance per call. Administrative reservation units under stated
# assumptions - NOT a guaranteed provider tokenizer bound, NOT a
# provider-enforced spend limit. Billed usage above its reservation stops.
BYTES_PER_TOKEN = 1
FIXED_OVERHEAD_TOKENS_PER_CALL = 128
RESERVATION_PER_CALL_UNITS = 70_000
RESERVATION_AGGREGATE_UNITS = 1_400_000
EXPECTED_PLAN = {"plan_max_per_call_units": 66609,
                 "plan_aggregate_units": 1112686}

RECEIPT_NAME = "preflight_receipt_v2.json"
RECEIPT_VERSION = 1
RECEIPT_KIND = "country-feasibility-v2-stage1-execution-receipt"
RECEIPT_PREFLIGHT_DOCUMENT = "protocol.md"

RUNS_DIR = "runs"
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

# ONE SHARED exclusive lock: the exact file and mechanism the v1 runner used,
# so at most one writer exists across both experiments. Transient (removed only
# by its own holder); a stale lock is refused, never deleted automatically.
LOCK_NAME = ".execution.lock"
DEFAULT_LOCK_PATH = V1_ROOT / LOCK_NAME

# Frozen single-score JSON output contract (unchanged from v1 prompts).
OUTPUT_CONTRACT_FIELDS = ("why", "evidence_ids", "discovery", "direct_harms",
                          "scope_triggers", "uncertainty")
OUTPUT_STATUSES = ("ok", "insufficient_evidence")

# Exactly these request fields are ever sent: no fallback list, no cache
# control, no reasoning or other extra parameter.
REQUEST_KEYS = ("model", "messages", "temperature", "top_p", "max_tokens",
                "stream", "usage", "provider")

# Pinned SHA-256 of every v1/repo source file this protocol consumes or that
# certifies the prior accounting. Any drift, missing or unknown file stops.
V1_SOURCE_PINS = {
    "frozen/manifest.json":
        "a55962ac1eba5458b3de517bdeb768f55db3a3ab6f20c10d887ab78e8692b756",
    "frozen/single_a.txt":
        "de747210956d1637b7a872f03a58dfe3d2aa483562c1de987ab34bcf66a5cc46",
    "frozen/single_b.txt":
        "7dfdeba76b963a6b4f53f6b8d37c76e865cfb1bdfe528f35657d886459850ee8",
    "frozen/schedule.json":
        "b40d6bd87301d731885b1d807d3bba76e878f0205b0ad371a2ac739a710f5f47",
    "frozen/user_messages.json":
        "eb37081737f89b59694f110cba1867d159247fa50e755f252ac32d1ffa942f14",
    "frozen/packets/USA.txt":
        "1ba052e91d93ea728d496cab21137ce27b08e952dea8758b15d4ada2be47c1cf",
    "frozen/packets/GBR.txt":
        "8290d08753ea7c710a3f243a5f08e4e94628cdeab1375f395f892d081c51b31c",
    "frozen/packets/NPL.txt":
        "2d8bcf42f158273ae00dddc272eda488b5a8607d553e260f61b849e0024e815b",
    "frozen/packets/VAT.txt":
        "1800643dd8eb943fef5cb57c2c503e390a6c1d0135b6d23435b9d9f0bca02fc1",
    "ledger.json":
        "3e3b20bc52f933f5e6928078ebf4dd067093ae1eaf0c8fedee5677811b778f43",
    "runner.py":
        "d1435d61533b85c0667626e0e52ef6f032a513d7ddfa1ce8f36565b38bdb8d42",
    "runs/country-feasibility-20261108-v1/run.json":
        "01d91bf82f5686e57e770f034616d39f99c97bf563aa04522513186b127e8f28",
    "runs/country-feasibility-20261108-v1/result.json":
        "f5b2ff64750c5471fc5bd95c7e375b842452ba416e952e0b88938ed29829c361",
    "runs/country-feasibility-20261108-v1/attempts/call-001.json":
        "0b091da4de2ffdf021beb17a3b8db6dd5d029f5b38baaaaee62e139dff5dc757",
    "probes/probe-1/dispatch.json":
        "7ac4dd6319b1533ae563fb94d01422801d08d597e6dcf2e595deec4677ab3da1",
    "probes/probe-1/probe-result.json":
        "5b3bb14a03d36f11a1b5990971f60bc9102de99a8daa53a087e392fecd907ef2",
    "probes/probe-1/review.json":
        "774fe27845017bdcab1a940e5d19c7bdfb220821b06eac83a3e8b42c7d1715a0",
    "probes/probe-2/dispatch.json":
        "7ef49398c1bfa53aa028e3109fb45f79587183cefde4d571f118a30ec4a3bdcf",
    "probes/probe-2/probe-result.json":
        "3a55716757b6aafc9122995196f1e0df8544eab52ff62a0e3e3d0b6930ee4b19",
    "probes/probe-2/review.json":
        "a022d6415d81395f34034da2cfa0247d83b70ce9ee005964ea6fbfed319de545",
    "probes/probe-3/dispatch.json":
        "a41b376e7c0ba6bca22b7ae5d992ceba30ec9ffe113df71c613f334e0170b7e3",
    "probes/probe-3/probe-result.json":
        "3557d8f8f5866032686944ab7381ff34009625f6ed66304110bb9ff21c33c0a8",
    "probes/probe-3/review.json":
        "ff783af9ef6531f0cbe639e53d38454000ca8991f05f42420f4e38de2ebe6e25",
    "probes/probe-4/dispatch.json":
        "9a62d935b6e3d2a998642d296aa7d3076628ea8354ee3860bc8f2c6cef406f54",
    "probes/probe-4/probe-result.json":
        "88e89f431dba67fee364048d5496d4b8905fa4168d65c9d05572cbf21e0db9f4",
    "probes/probe-4/review.json":
        "a4aa1b3a1e2974213037ec135e0468cd208b5a8b6d829a6bb67e7de079c98002",
}
DATA_COUNTRIES_PIN = \
    "c4a2c8339b0d389a42d8b90ec48bafab209d511185ab10e19789d29de4baebce"

# ---------------------------------------------------------------------------#
# STRICT per-answer semantic checkpoint (pre-registered before any v2 outcome;
# the per-answer path was chosen over batching per the independent method
# review's literal requirement and the semantic-process consult's stricter
# option). Must equal frozen/manifest.json design/cache_policy blocks.
# ---------------------------------------------------------------------------#
MAX_ATTEMPTS_PER_INVOCATION = 1
REVIEW_VERSION = 1
REVIEW_VERDICTS = ("PASS", "FAIL", "UNCERTAIN")
REVIEW_REL_DIR = "semantic-reviews"      # written ONLY by human/model
SIDECAR_REL_DIR = "semantic-inputs"      # reviewers, never by this runner
RUBRIC_VERSION = ("single-country-v1 prompts: single_a="
                  + V1_SOURCE_PINS["frozen/single_a.txt"]
                  + " single_b=" + V1_SOURCE_PINS["frozen/single_b.txt"])
SEMANTIC_CHECKPOINT = (
    "one scheduled cell per invocation under the shared lock; before the "
    "next dispatch every earlier completed output needs an independent PASS "
    "review (runs/<run-id>/semantic-reviews/call-NNN.json) bound to "
    "response_sha256, the score-blind sidecar sha256, the frozen "
    "system-prompt and user-message hashes and the rubric version - every "
    "record/sidecar/review message and prompt binding cross-checked against "
    "the re-read immutable frozen schedule/message/prompt bytes for that "
    "call (never only against the writable attempt record) and each attempt "
    "chained to this invocation's receipt hash - with named reviewer "
    "identity/session; missing/FAIL/UNCERTAIN/tampered review, a failed "
    "prior attempt, or an unreconciled liability blocks all later calls "
    "before price/credential/network access; reviewers judge source "
    "fidelity against the frozen dossier without numerical values or "
    "rankings; this runner never writes a review or authors a verdict")
CACHE_POLICY = {
    "request_cache_directives": "none ever sent (no cache key in the request "
        "whitelist); no cache warming, busting, forcing or retries to obtain "
        "a preferred cache condition",
    "provider_initiated_reads": "allowed only when reported usage/cost "
        "arithmetic is valid (ints, totals consistent, cached_tokens <= "
        "prompt_tokens, finite cost within the reservation); full cache "
        "usage is logged in every attempt as an execution condition - with "
        "no claim of reproducibility or of uncached performance",
    "cache_writes": "any nonzero cache_write_tokens stops the stage: "
        "cache-WRITE billing cannot be reconciled with the advertised prices "
        "this runner fetches, so it is never assumed to be free",
    "provenance": "token counts alone do not identify cache provenance; "
        "provider cache state is uncontrolled and precludes latency/cost "
        "reproduction claims"}

# The five prior dispatch records: identity + exact provider-reported values.
# (label, path under v1 root, expected status, provider response id, exact
#  cost decimal string, exact input tokens, exact output tokens)
PRIOR_RECORDS = (
    ("probe-1", "probes/probe-1/probe-result.json", "completed",
     "gen-1794106990-7PhsDMgoeYLY5Ey3xTWC", "0.00001551", 85, 30),
    ("probe-2", "probes/probe-2/probe-result.json", "stopped",
     "gen-1794106994-0siK3sXrXESUBEhvbyAa", "0.00026475", 53, 60),
    ("probe-3", "probes/probe-3/probe-result.json", "completed",
     "gen-1794110261-QsQTj3oz7EAh67YH2wwb", "0.00001551", 85, 30),
    ("probe-4", "probes/probe-4/probe-result.json", "completed",
     "gen-1794110270-0TMzHxo7IM8DnbBoLgJS", "0.00061725", 53, 154),
    ("call-001",
     "runs/country-feasibility-20261108-v1/attempts/call-001.json", None,
     "gen-1794111565-9wwedC2eXJIXQChRL86T", "0.001080256", 13376, 2000),
)
V1_RUN_ID = "country-feasibility-20261108-v1"
V1_PROBE_SLOTS = ("probe-1", "probe-2", "probe-3", "probe-4")
PROBE_FILE_SET = {"dispatch.json", "probe-result.json", "review.json"}
V1_RUN_FILE_SET = {"run.json", "result.json", "attempts"}

# Independent review artifacts the receipt must bind; absent until reviewed.
REVIEW_BINDINGS = (
    ("independent-methodology-review", "reviews/methodology-review.md"),
    ("independent-code-review", "reviews/code-review.md"),
    ("independent-evidence-review", "reviews/evidence-review.md"))

# Everything the receipt must bind (label -> resolved path is derived).
V2_INPUT_LABELS = ("frozen/manifest.json", "frozen/schedule.json",
                   "frozen/user_messages.json", "frozen/single_a.txt",
                   "frozen/single_b.txt")
CODE_LABELS = ("protocol.md", "runner.py", "test_runner.py")
SOURCE_DATA_LABELS = ("data/countries.json",)
V1_BINDING_LABELS = tuple(f"v1/{rel}" for rel in V1_SOURCE_PINS)

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


def dec_str(value) -> str:
    """Exact decimal text for money records (no rounding, no float repr)."""
    return format(value, "f") if isinstance(value, Decimal) else str(value)


# --------------------------------------------------------------------------- #
# CLI (no credential parameter exists; unknown flags are rejected)
# --------------------------------------------------------------------------- #

def usage() -> str:
    return ("usage: runner.py [--execute --run-id ID [--receipt PATH]]\n"
            "  disabled by default: without --execute this module performs no\n"
            "  network access, reads no credential and writes nothing;\n"
            "  ONE scheduled cell per invocation: every earlier completed\n"
            "  output first needs an independent PASS semantic review bound\n"
            "  to its response hash; missing/FAIL/UNCERTAIN review blocks\n"
            "  all later calls; no skip, no reorder, no retry;\n"
            "  stage one is exactly 20 attempts maximum (16 core cells + 4\n"
            "  empty-dossier sentinels), <= 25 dispatches with v1's five,\n"
            "  all against the same local USD 10.00 guard;\n"
            "  credentials are read only from the "
            f"{SECRET_ENV} environment variable (never from the CLI)")


def parse_args(argv) -> dict:
    opts = {"execute": False, "receipt": None, "run_id": None}
    i = 0
    while i < len(argv):
        a = argv[i]
        key, eq, val = a.partition("=")
        if key == "--execute" and not eq:
            opts["execute"] = True
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
                              f"credentials may never be passed on the command "
                              f"line ({key} rejected); the runner reads "
                              f"{SECRET_ENV} from the environment only under "
                              "--execute")
            raise Refusal(EXIT_USAGE, f"unknown argument: {key}")
        i += 1
    return opts


def validate_run_id_format(run_id: str) -> None:
    """Path-safety check only (no filesystem read); runs before the lock."""
    if not run_id:
        raise Refusal(EXIT_USAGE, "--run-id is required with --execute")
    if not RUN_ID_RE.match(run_id) or ".." in run_id:
        raise Refusal(EXIT_GATE,
                      f"invalid run id {run_id!r}: must match "
                      f"{RUN_ID_RE.pattern} and must not contain '..'")


def validate_run_id(run_id: str, root: Path) -> Path:
    """Existence/overwrite check; runs under the shared lock."""
    validate_run_id_format(run_id)
    runs = root / RUNS_DIR
    run_dir = runs / run_id
    if run_dir.resolve().parent != runs.resolve():
        raise Refusal(EXIT_GATE, f"run id escapes {RUNS_DIR}/: {run_id!r}")
    if run_dir.exists():
        raise Refusal(EXIT_GATE,
                      f"run {run_id!r} already exists - refusing to overwrite, "
                      "append to or retry an existing run")
    return run_dir


# --------------------------------------------------------------------------- #
# ONE shared exclusive execution lock (compatible with the closed v1 runner)
# --------------------------------------------------------------------------- #

def acquire_lock(path: Path, holder: str) -> Path:
    """Atomic O_EXCL create of the SHARED experiment lock.

    The default path is ``../country-feasibility/.execution.lock`` - the very
    file the v1 runner used - so at most one writer can exist across v1/v2.
    Must be held BEFORE any ledger or prior state is read and through dispatch
    and finalization. Contention or a stale/crash lock -> Refusal before any
    call; this runner never deletes a lock it did not acquire.
    """
    payload = json.dumps({"holder": holder, "pid": os.getpid(),
                          "runner": "country-feasibility-v2",
                          "acquired_at": utcnow()}, indent=1) + "\n"
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        try:
            existing = path.read_text(encoding="utf-8").strip()[:300]
        except OSError:
            existing = "<unreadable>"
        raise Refusal(EXIT_GATE,
                      f"shared experiment execution lock is held: {path} "
                      f"({existing}). Another run may be in progress, or a "
                      "crash left a stale lock; contention refuses BEFORE any "
                      "call. A human must inspect and remove it explicitly - "
                      "this runner never deletes a lock it did not acquire")
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
# Frozen inputs, manifest self-check, schedule/messages (all offline)
# --------------------------------------------------------------------------- #

def binding_paths(root: Path, v1_root: Path, data_path: Path) -> dict:
    """Resolve every receipt binding label to its absolute path."""
    out = {}
    for label in V2_INPUT_LABELS:
        out[label] = root / label
    for label in CODE_LABELS:
        out[label] = HERE / label          # the code/protocol under review
    out["data/countries.json"] = data_path
    for rel in V1_SOURCE_PINS:
        out[f"v1/{rel}"] = v1_root / rel
    for label, rel in REVIEW_BINDINGS:
        out[label] = root / rel
    return out


def current_bindings(root: Path, v1_root: Path, data_path: Path) -> dict:
    out = {}
    for label, path in binding_paths(root, v1_root, data_path).items():
        if not path.is_file():
            raise Refusal(EXIT_GATE,
                          f"missing input bound by the v2 preflight receipt: "
                          f"{label} ({path}) - the reviewed receipt cannot be "
                          "satisfied; execution refused")
        out[label] = sha(path.read_bytes())
    return out


def verify_manifest(manifest: dict, root: Path, data_path: Path,
                    v1_root: Path) -> None:
    """Frozen-input + constant self-check: disk bytes and every design
    constant must equal this module's predeclared values (fail closed)."""
    problems = []
    files = manifest.get("files") or {}
    for name in ("single_a.txt", "single_b.txt", "schedule.json",
                 "user_messages.json"):
        p = root / "frozen" / name
        rec = files.get(name) or {}
        if not p.is_file() or sha(p.read_bytes()) != rec.get("sha256"):
            problems.append(f"frozen/{name}")
    # Genuine prompt byte-identity BOTH ways: the manifest's recorded hash for
    # each v2 prompt copy must equal the pinned hash of the v1 ORIGINAL, not
    # merely agree with whatever bytes sit on disk (a prompt + manifest
    # co-tamper would otherwise pass this self-check).
    for name in ("single_a.txt", "single_b.txt"):
        rec = files.get(name) or {}
        if rec.get("sha256") != V1_SOURCE_PINS[f"frozen/{name}"]:
            problems.append(
                f"frozen/{name} manifest hash does not equal the pinned v1 "
                "prompt hash (prompt/manifest co-tamper)")
    for rel, want in (V1_SOURCE_PINS.items()):
        # v1 byte-identity for the inputs v2 derives from (prompts/messages)
        if rel in ("frozen/single_a.txt", "frozen/single_b.txt",
                   "frozen/user_messages.json", "frozen/schedule.json"):
            p = v1_root / rel
            if not p.is_file() or sha(p.read_bytes()) != want:
                problems.append(f"v1/{rel}")
    if manifest.get("requested_settings") != REQUESTED_SETTINGS:
        problems.append("requested_settings drifted")
    chg = manifest.get("requested_settings_change") or {}
    if chg.get("changed", {}).get("max_output_tokens") != {"from": 2000,
                                                           "to": 11000} \
            or chg.get("sole_generation_setting_change") is not True \
            or not isinstance(chg.get("basis"), str) or not chg.get("basis"):
        problems.append("requested_settings_change disclosure drifted")
    tc = chg.get("transport_timeout") or {}
    if tc.get("from_seconds") != int(V1_TRANSPORT_TIMEOUT_SECONDS) \
            or tc.get("to_seconds") != int(TRANSPORT_TIMEOUT_SECONDS) \
            or tc.get("price_fetch_timeout_seconds") \
            != int(PRICE_FETCH_TIMEOUT_SECONDS) \
            or "transport-only" not in str(tc.get("scope", "")) \
            or not isinstance(tc.get("basis"), str) or not tc.get("basis") \
            or not isinstance(tc.get("fail_closed"), str) \
            or not tc.get("fail_closed"):
        problems.append("transport-only timeout disclosure drifted")
    if int(TRANSPORT_TIMEOUT_SECONDS) != 300 \
            or int(PRICE_FETCH_TIMEOUT_SECONDS) != 30:
        problems.append("predeclared timeout constants drifted")
    if tuple(manifest.get("models") or ()) != MODELS:
        problems.append("pre-registered models drifted")
    if manifest.get("expected_providers") != \
            {m: list(p) for m, p in EXPECTED_PROVIDERS.items()}:
        problems.append("expected_providers drifted")
    design = manifest.get("design") or {}
    for key, want in (("attempts_max", ATTEMPT_CEILING),
                      ("core_cells", CORE_CELLS),
                      ("sentinel_cells", SENTINEL_CELLS),
                      ("draws", DRAWS), ("blocks", BLOCKS),
                      ("rows_per_block", ROWS_PER_BLOCK),
                      ("schedule_frozen_before_outcomes", True)):
        if design.get(key) != want:
            problems.append(f"design.{key} drifted")
    if tuple(design.get("countries") or ()) != COUNTRIES \
            or tuple(design.get("variants") or ()) != VARIANTS:
        problems.append("design countries/variants drifted")
    if design.get("sentinel_semantics") != EMPTY_SENTINEL_RULE:
        problems.append("design.sentinel_semantics drifted")
    if design.get("max_attempts_per_invocation") \
            != MAX_ATTEMPTS_PER_INVOCATION:
        problems.append("design.max_attempts_per_invocation drifted")
    if design.get("semantic_checkpoint") != SEMANTIC_CHECKPOINT:
        problems.append("semantic checkpoint disclosure drifted")
    if manifest.get("cache_policy") != CACHE_POLICY:
        problems.append("cache policy drifted")
    caps = manifest.get("caps") or {}
    for key, want in (("attempt_ceiling_including_failures", ATTEMPT_CEILING),
                      ("prior_dispatches", PRIOR_DISPATCHES),
                      ("total_dispatch_ceiling", TOTAL_DISPATCH_CEILING),
                      ("retries", RETRIES),
                      ("per_call_max_output_tokens",
                       V2_MAX_OUTPUT_PER_CALL),
                      ("v2_aggregate_output_reservation_tokens",
                       V2_AGG_OUTPUT_RESERVATION),
                      ("reservation_per_call_units",
                       RESERVATION_PER_CALL_UNITS),
                      ("reservation_aggregate_units",
                       RESERVATION_AGGREGATE_UNITS)):
        if caps.get(key) != want:
            problems.append(f"caps.{key} drifted")
    if str(caps.get("aggregate_max_usd_including_failures")) != "10.00":
        problems.append("USD ceiling drifted")
    hist = manifest.get("historical_output_budgets") or {}
    if {k: hist.get(k) for k in HISTORICAL_OUTPUT_BUDGETS} != \
            HISTORICAL_OUTPUT_BUDGETS:
        problems.append("historical output budgets drifted")
    plan = manifest.get("plan") or {}
    if {k: plan.get(k) for k in EXPECTED_PLAN} != EXPECTED_PLAN:
        problems.append("reservation plan constants drifted")
    if not isinstance(plan.get("input_reservation_method"), str) \
            or "NOT a guaranteed provider tokenizer bound" not in \
            plan["input_reservation_method"]:
        problems.append("input reservation method must disclose it is not a "
                        "guaranteed tokenizer bound")
    prior = manifest.get("prior_accounting") or {}
    if prior.get("total_usd") != dec_str(PRIOR_COST_USD) \
            or prior.get("input_tokens") != PRIOR_INPUT_TOKENS \
            or prior.get("output_tokens") != PRIOR_OUTPUT_TOKENS \
            or prior.get("dispatches") != PRIOR_DISPATCHES \
            or prior.get("record_ids") != [r[3] for r in PRIOR_RECORDS]:
        problems.append("prior accounting constants drifted")
    ev = manifest.get("evidence_snapshot") or {}
    if not data_path.is_file() \
            or sha(data_path.read_bytes()) != DATA_COUNTRIES_PIN \
            or ev.get("sha256") != DATA_COUNTRIES_PIN:
        problems.append("data/countries.json evidence snapshot drifted")
    src = manifest.get("source_v1_frozen_byte_identity") or {}
    for rel in ("frozen/single_a.txt", "frozen/single_b.txt"):
        if src.get(Path(rel).name) != V1_SOURCE_PINS[rel]:
            problems.append(f"source_v1_frozen_byte_identity {rel} drifted")
    if problems:
        raise Refusal(EXIT_GATE,
                      "v2 manifest/self-check failed (source or constant "
                      f"drift): {', '.join(problems)}")


ROW_KEYS = {"call", "block", "case", "sentinel", "model", "variant", "label",
            "draw", "fresh_context", "source_v1_call"}
MSG_KEYS = {"call", "source_v1_call", "case", "sentinel", "model", "variant",
            "message", "message_sha256"}


def verify_schedule(sched, msgs_doc, v1_root: Path) -> list:
    """Structural, balance and byte-identity checks over the frozen stage-one
    schedule and its messages. Returns aligned message rows."""
    problems = []
    rows = sched.get("rows") if isinstance(sched, dict) else sched
    messages = msgs_doc.get("messages") if isinstance(msgs_doc, dict) else None
    if not isinstance(rows, list) or len(rows) != ATTEMPT_CEILING:
        raise Refusal(EXIT_GATE,
                      f"schedule must hold exactly {ATTEMPT_CEILING} rows")
    if not isinstance(messages, list) or len(messages) != ATTEMPT_CEILING:
        raise Refusal(EXIT_GATE,
                      f"user messages must hold exactly {ATTEMPT_CEILING} rows")
    if [r.get("call") for r in rows] != list(range(1, ATTEMPT_CEILING + 1)) \
            or [m.get("call") for m in messages] != \
            list(range(1, ATTEMPT_CEILING + 1)):
        raise Refusal(EXIT_GATE, "schedule/message call numbering is not 1..20")
    core = [r for r in rows if r.get("sentinel") == "core"]
    empty = [r for r in rows if r.get("sentinel") == "empty"]
    if len(core) != CORE_CELLS or len(empty) != SENTINEL_CELLS:
        raise Refusal(EXIT_GATE,
                      f"cell composition must be {CORE_CELLS} core + "
                      f"{SENTINEL_CELLS} sentinels, got {len(core)}+{len(empty)}")
    combos = {(r.get("case"), r.get("model"), r.get("variant"))
              for r in core}
    want = {(c, m, v) for c in COUNTRIES for m in MODELS for v in VARIANTS}
    if combos != want or len(core) != len(combos):
        problems.append("core cells are not exactly country x model x variant")
    sent = {(r.get("model"), r.get("variant")) for r in empty}
    if sent != {(m, v) for m in MODELS for v in VARIANTS} \
            or any(r.get("case") != "" for r in empty):
        problems.append("sentinels are not exactly model x variant with empty case")
    if any(set(r) != ROW_KEYS for r in rows):
        problems.append("schedule row keys drifted")
    if any(r.get("label") != "DOSSIER" or r.get("draw") != 1
           or r.get("fresh_context") is not True for r in rows):
        problems.append("every row must be label DOSSIER, draw 1, fresh context")
    if sorted({r.get("block") for r in rows}) != [1, 2]:
        problems.append("exactly two blocks required")
    for blk in (1, 2):
        brows = [r for r in rows if r.get("block") == blk]
        if len(brows) != ROWS_PER_BLOCK:
            problems.append(f"block {blk} must hold {ROWS_PER_BLOCK} rows")
            continue
        bcore = [r for r in brows if r.get("sentinel") == "core"]
        bsent = [r for r in brows if r.get("sentinel") == "empty"]
        if len(bcore) != 8 or len(bsent) != 2:
            problems.append(f"block {blk} must be 8 core + 2 sentinels")
        for c in COUNTRIES:
            if sum(1 for r in bcore if r.get("case") == c) != 2:
                problems.append(f"block {blk} is not country-balanced ({c})")
        for m in MODELS:
            n = sum(1 for r in bcore if r.get("model") == m) \
                + sum(1 for r in bsent if r.get("model") == m)
            if n != ROWS_PER_BLOCK // 2:
                problems.append(f"block {blk} is not model-balanced ({m}: {n})")
        for v in VARIANTS:
            n = sum(1 for r in bcore if r.get("variant") == v) \
                + sum(1 for r in bsent if r.get("variant") == v)
            if n != ROWS_PER_BLOCK // 2:
                problems.append(f"block {blk} is not variant-balanced ({v}: {n})")
        idxs = [i for i, r in enumerate(brows) if r.get("sentinel") == "empty"]
        if any(i in (0, len(brows) - 1) for i in idxs) \
                or (len(idxs) == 2 and abs(idxs[0] - idxs[1]) == 1):
            problems.append(f"block {blk} sentinel interleave constraints "
                            "violated (edge or adjacent)")
        for c in COUNTRIES:
            ci = [i for i, r in enumerate(brows) if r.get("case") == c]
            if len(ci) == 2 and ci[1] - ci[0] == 1:
                problems.append(f"block {blk} rows for {c} are adjacent "
                                "(interleave violated)")
    # message alignment + byte-identity to the pinned v1 source rows
    try:
        v1_sched = load_json(v1_root / "frozen" / "schedule.json")
        v1_msgs = load_json(v1_root / "frozen" / "user_messages.json")
    except (OSError, ValueError) as exc:
        raise Refusal(EXIT_GATE, f"v1 frozen schedule/messages unreadable: {exc}")
    if not isinstance(v1_sched, list) or not isinstance(v1_msgs, list) \
            or len(v1_sched) != 40 or len(v1_msgs) != 40:
        raise Refusal(EXIT_GATE, "v1 frozen schedule/messages not the expected "
                                 "40-row originals")
    for row, msg in zip(rows, messages):
        if set(msg) != MSG_KEYS:
            problems.append(f"message row {row.get('call')} keys drifted")
            continue
        for key in ("source_v1_call", "case", "sentinel", "model", "variant"):
            if msg.get(key) != row.get(key):
                problems.append(f"message row {row.get('call')} disagrees with "
                                f"schedule on {key}")
        body = msg.get("message")
        if not isinstance(body, str) or \
                sha(body.encode("utf-8")) != msg.get("message_sha256"):
            problems.append(f"message {row.get('call')} hash does not match its "
                            "bytes")
        src = row.get("source_v1_call")
        if not isinstance(src, int) or not 1 <= src <= 40:
            problems.append(f"row {row.get('call')} source_v1_call out of range")
            continue
        v1row, v1msg = v1_sched[src - 1], v1_msgs[src - 1]
        if v1row.get("call") != src or v1msg.get("call") != src:
            problems.append("v1 source row misaligned")
        for key in ("case", "sentinel", "model", "variant"):
            if v1row.get(key) != row.get(key) or v1msg.get(key) != row.get(key):
                problems.append(f"row {row.get('call')} is not byte-identical "
                                f"to its v1 source row on {key}")
        if v1msg.get("message") != body \
                or v1msg.get("message_sha256") != msg.get("message_sha256"):
            problems.append(f"row {row.get('call')} message is not the exact "
                            "v1 evidence-message bytes")
    if problems:
        raise Refusal(EXIT_GATE, "schedule/messages rejected: "
                      + "; ".join(problems))
    return messages


# --------------------------------------------------------------------------- #
# v2 preflight receipt (absent until independently reviewed)
# --------------------------------------------------------------------------- #

def verify_receipt(receipt: dict, bindings: dict) -> None:
    """Schema 1 of the v2 execution receipt: exact binding of every input,
    this protocol, this code, the source data, the pinned v1 source records
    and the three independent review artifacts, plus the reviewer's signed-off
    preflight over protocol.md and the exact prior-accounting reconstruction.
    Binding bytes is not execution approval and weakens no other gate."""
    problems = []
    if receipt.get("receipt_version") != RECEIPT_VERSION:
        problems.append(f"receipt_version must be {RECEIPT_VERSION}")
    if receipt.get("receipt_kind") != RECEIPT_KIND:
        problems.append(f"receipt_kind must be {RECEIPT_KIND!r}")
    pf = receipt.get("preflight") or {}
    if pf.get("status") != "signed_off":
        problems.append("preflight.status must be 'signed_off'")
    if pf.get("document") != RECEIPT_PREFLIGHT_DOCUMENT:
        problems.append(f"preflight.document must be exactly "
                        f"{RECEIPT_PREFLIGHT_DOCUMENT!r}")
    for k in ("reviewed_by", "reviewed_at", "statement"):
        if not isinstance(pf.get(k), str) or not pf.get(k).strip():
            problems.append(f"preflight.{k} must be a non-empty string")
    pa = receipt.get("prior_accounting") or {}
    want_ids = [r[3] for r in PRIOR_RECORDS]
    if pa.get("total_usd") != dec_str(PRIOR_COST_USD):
        problems.append("prior_accounting.total_usd must equal the exact "
                        "reconstructed 0.001993276")
    if pa.get("dispatches") != PRIOR_DISPATCHES \
            or pa.get("input_tokens") != PRIOR_INPUT_TOKENS \
            or pa.get("output_tokens") != PRIOR_OUTPUT_TOKENS \
            or pa.get("record_ids") != want_ids:
        problems.append("prior_accounting dispatch/token/id record mismatch")
    rec = receipt.get("bindings")
    if not isinstance(rec, dict):
        problems.append("bindings must be an object of label -> sha256")
    elif set(rec) != set(bindings):
        missing = sorted(set(bindings) - set(rec))
        extra = sorted(set(rec) - set(bindings))
        problems.append(f"bindings key set differs (missing={missing}, "
                        f"extra={extra})")
    else:
        bad = [k for k in bindings if rec[k] != bindings[k]]
        if bad:
            problems.append(f"binding hash mismatch for {sorted(bad)}")
    if problems:
        raise Refusal(EXIT_GATE, "v2 preflight receipt rejected: "
                      + "; ".join(problems))


# --------------------------------------------------------------------------- #
# v1 prior-state reconstruction (read-only; pinned; Decimal accounting)
# --------------------------------------------------------------------------- #

def verify_v1_source_files(v1_root: Path) -> None:
    """Independently re-hash the known raw v1 records and require the exact
    directory shape. Missing, unknown (unexpected) or duplicated files stop."""
    problems = []
    probes = v1_root / "probes"
    runs = v1_root / "runs"
    probe_dirs = sorted(p.name for p in probes.iterdir()) if probes.is_dir() \
        else []
    if probe_dirs != sorted(V1_PROBE_SLOTS):
        problems.append(f"probes/ must contain exactly {list(V1_PROBE_SLOTS)}, "
                        f"found {probe_dirs}")
    for slot in V1_PROBE_SLOTS:
        d = probes / slot
        if d.is_dir():
            names = sorted(p.name for p in d.iterdir())
            if names != sorted(PROBE_FILE_SET):
                problems.append(f"probes/{slot} unexpected files: {names}")
    run_dirs = sorted(p.name for p in runs.iterdir()) if runs.is_dir() else []
    if run_dirs != [V1_RUN_ID]:
        problems.append(f"runs/ must contain exactly {[V1_RUN_ID]}, found "
                        f"{run_dirs}")
    rd = runs / V1_RUN_ID
    if rd.is_dir():
        names = sorted(
            "attempts" if p.name == "attempts" and p.is_dir() else p.name
            for p in rd.iterdir())
        if names != sorted(V1_RUN_FILE_SET):
            problems.append(f"runs/{V1_RUN_ID} unexpected entries: {names}")
        att = rd / "attempts"
        if att.is_dir():
            att_names = sorted(p.name for p in att.iterdir())
            if att_names != ["call-001.json"]:
                problems.append(f"runs/{V1_RUN_ID}/attempts unexpected files: "
                                f"{att_names}")
    for rel, want in V1_SOURCE_PINS.items():
        p = v1_root / rel
        if not p.is_file():
            problems.append(f"missing known raw record: v1/{rel}")
        else:
            got = sha(p.read_bytes())
            if got != want:
                problems.append(f"known raw hash mismatch: v1/{rel} "
                                f"{got[:16]}... != pinned {want[:16]}...")
    if problems:
        raise Refusal(EXIT_GATE,
                      "v1 prior records missing/unknown/duplicated/drifted - "
                      "cannot reconstruct prior accounting: "
                      + "; ".join(problems))


def _raw_body_id_and_cost(doc: dict, path: str) -> tuple:
    """Provider response id + usage.cost from a record's raw_response."""
    raw = doc.get("raw_response")
    if not isinstance(raw, str) or not raw:
        raise Refusal(EXIT_GATE, f"{path}: missing raw response body")
    try:
        body = json.loads(raw, parse_constant=_reject_constant)
    except ValueError as exc:
        raise Refusal(EXIT_GATE, f"{path}: raw body is not strict JSON: {exc}")
    rid = body.get("id") if isinstance(body, dict) else None
    usage = body.get("usage") if isinstance(body, dict) else None
    cost = usage.get("cost") if isinstance(usage, dict) else None
    if not isinstance(rid, str) or not rid.strip():
        raise Refusal(EXIT_GATE, f"{path}: missing provider response id")
    if isinstance(cost, bool) or not isinstance(cost, (int, float)) \
            or not math.isfinite(float(cost)) or float(cost) < 0:
        raise Refusal(EXIT_GATE, f"{path}: raw usage.cost missing or invalid")
    return rid, cost


def parse_prior_records(v1_root: Path) -> list:
    """Parse the five pinned prior records into comparable entries; every
    internal inconsistency stops (unknown liability is never treated as zero)."""
    out = []
    for label, rel, want_status, want_id, want_cost, want_in, want_out \
            in PRIOR_RECORDS:
        p = v1_root / rel
        try:
            doc = load_json(p)
        except (OSError, ValueError) as exc:
            raise Refusal(EXIT_GATE, f"prior record {label} unreadable: {exc}")
        if want_status is not None and doc.get("status") != want_status:
            raise Refusal(EXIT_GATE,
                          f"prior record {label} status {doc.get('status')!r} "
                          f"!= pinned {want_status!r} - archived outcomes are "
                          "immutable")
        if label == "call-001":
            billed = doc.get("billed_on_failure") or {}
            cost = billed.get("cost")
            usage = billed.get("usage") or {}
            inp = usage.get("prompt_tokens")
            outp = usage.get("completion_tokens")
            if billed.get("parsed") is not True:
                raise Refusal(EXIT_GATE, "call-001 billed_on_failure not parsed")
        else:
            cost = doc.get("used_usd")
            inp = doc.get("used_input_tokens")
            outp = doc.get("used_output_tokens")
        try:
            cost_d = Decimal(str(cost))
        except (InvalidOperation, ValueError):
            raise Refusal(EXIT_GATE,
                          f"prior record {label} cost is not a decimal: "
                          f"{cost!r}")
        rid, raw_cost = _raw_body_id_and_cost(doc, label)
        if rid != want_id:
            raise Refusal(EXIT_GATE,
                          f"prior record {label} provider id {rid!r} != pinned "
                          f"{want_id!r}")
        if Decimal(str(raw_cost)) != cost_d:
            raise Refusal(EXIT_GATE,
                          f"prior record {label} raw usage.cost disagrees with "
                          "the recorded charge (unknown billing)")
        if cost_d != Decimal(want_cost) or inp != want_in or outp != want_out:
            raise Refusal(EXIT_GATE,
                          f"prior record {label} charge/usage "
                          f"({cost_d} / {inp} / {outp}) != pinned "
                          f"({want_cost} / {want_in} / {want_out})")
        if (isinstance(inp, bool) or not isinstance(inp, int) or inp < 0
                or isinstance(outp, bool) or not isinstance(outp, int)
                or outp < 0):
            raise Refusal(EXIT_GATE, f"prior record {label} token counts invalid")
        out.append({"label": label, "id": rid, "cost": cost_d,
                    "input": inp, "output": outp})
    return out


def reconcile_prior_records(records: list) -> dict:
    """Deduplicate ids and total the exact Decimal costs; anything unknown,
    duplicated or off the pinned totals refuses (no silent budget reset)."""
    ids = [r["id"] for r in records]
    if len(ids) != len(set(ids)):
        raise Refusal(EXIT_GATE,
                      "duplicate provider response id in prior records "
                      f"({len(ids)} records, {len(set(ids))} unique ids) - a "
                      "record may be double-counted; refusing")
    total = sum((r["cost"] for r in records), Decimal(0))
    inputs = sum(r["input"] for r in records)
    outputs = sum(r["output"] for r in records)
    if len(records) != PRIOR_DISPATCHES:
        raise Refusal(EXIT_GATE,
                      f"expected {PRIOR_DISPATCHES} prior dispatch records, "
                      f"found {len(records)} - missing or unknown dispatch")
    if total != PRIOR_COST_USD or inputs != PRIOR_INPUT_TOKENS \
            or outputs != PRIOR_OUTPUT_TOKENS:
        raise Refusal(EXIT_GATE,
                      "prior accounting does not equal the pinned exact "
                      f"totals: ${total} / {inputs} in / {outputs} out != "
                      f"${PRIOR_COST_USD} / {PRIOR_INPUT_TOKENS} / "
                      f"{PRIOR_OUTPUT_TOKENS} - human reconciliation required "
                      "before any dispatch")
    return {"dispatches": len(records), "cost": total, "input": inputs,
            "output": outputs, "ids": ids}


def read_v1_prior(v1_root: Path) -> dict:
    verify_v1_source_files(v1_root)
    return reconcile_prior_records(parse_prior_records(v1_root))


# --------------------------------------------------------------------------- #
# v2 prior-run state (stale/incomplete state fails closed; never overwritten)
# --------------------------------------------------------------------------- #

def _collect_keys(obj, wanted=("score",), path="$") -> list:
    """Recursive key scan (v1 pattern): used to keep review artifacts
    score-blind by structure - a review may not carry a score/rank/band key."""
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


def sidecar_path(run_dir: Path, call: int) -> Path:
    return run_dir / SIDECAR_REL_DIR / f"call-{call:03d}.json"


def review_path(run_dir: Path, call: int) -> Path:
    # Written only by human/model reviewers; this runner only ever reads it.
    return run_dir / REVIEW_REL_DIR / f"call-{call:03d}.json"


def score_blind_sidecar(parsed_output: dict, system_sha: str,
                        message_sha: str, source_v1_call) -> dict:
    """Score-blind structured sidecar: the numeric ``score`` key is omitted
    and every other contract field is copied VERBATIM (no prose rewriting,
    no rounding, no selection), plus the exact frozen dossier reference
    (hashes) so reviewers can check source fidelity without ever seeing a
    numerical value or ranking."""
    out = {k: v for k, v in parsed_output.items() if k != "score"}
    expected_keys = set(OUTPUT_CONTRACT_FIELDS) | {"status"}
    if set(out) != expected_keys or "score" in out:
        raise Refusal(EXIT_STOPPED,
                      f"sidecar projection refused: fields {sorted(out)} != "
                      f"score-blind contract fields {sorted(expected_keys)}")
    return {
        "sidecar_version": 1,
        "score_blind": "the numeric score key is omitted; every other field "
                       "is copied verbatim from the model output - no prose "
                       "is rewritten, no value is rounded or selected",
        "output": out,
        "frozen_dossier": {
            "system_prompt_sha256": system_sha,
            "user_message_sha256": message_sha,
            "source_v1_call": source_v1_call,
            "reference": "check source fidelity against exactly these "
                         "frozen bytes (frozen/single_{a,b}.txt and "
                         "frozen/user_messages.json row source_v1_call); no "
                         "preferred numerical value or ranking is a review "
                         "criterion"}}


def prior_v2_state(root: Path, sched: list) -> dict:
    """Aggregate every prior v2 invocation's terminal state (read-only,
    under the lock). Each invocation owns one run directory; continuation
    depends on this scan. Unknown/stale/incomplete state, liabilities,
    duplicate or misnumbered attempt records, or a record whose cell identity
    disagrees with its frozen schedule row all fail closed. Attempt records
    keep their run directory so the per-answer review gate can verify the
    sidecar and review in place."""
    state = {"runs": [], "attempts": 0, "used_usd": Decimal(0),
             "used_input": 0, "used_output": 0, "reserved_in": 0,
             "attempt_records": {}, "prior_reviews": []}
    runs = root / RUNS_DIR
    run_dirs = sorted(p for p in runs.iterdir() if p.is_dir()) \
        if runs.is_dir() else []
    for d in run_dirs:
        rid = d.name
        state["runs"].append(rid)
        result_path = d / "result.json"
        if not result_path.is_file():
            raise Refusal(EXIT_GATE,
                          f"prior v2 run {rid!r} has no terminal result.json "
                          "(stale/incomplete state) - fail closed: a human must "
                          "reconcile; evidence is never deleted and runs are "
                          "never overwritten or retried")
        try:
            result = load_json(result_path)
        except (OSError, ValueError) as exc:
            raise Refusal(EXIT_GATE,
                          f"prior v2 run {rid!r} terminal record unreadable "
                          f"({exc}) - fail closed")
        liab = result.get("unreconciled_liability")
        if liab is not None:
            raise Refusal(EXIT_GATE,
                          f"prior v2 run {rid!r} carries an unreconciled "
                          "liability - unknown charge is not zero; v2 stage "
                          "dispatch stays blocked and requires a new reviewed "
                          "version after human reconciliation")
        used = result.get("used_usd")
        try:
            used_d = Decimal(str(used))
        except (InvalidOperation, ValueError):
            raise Refusal(EXIT_GATE,
                          f"prior v2 run {rid!r} used_usd not decimal: {used!r}")
        if used_d < 0 or not used_d.is_finite():
            raise Refusal(EXIT_GATE,
                          f"prior v2 run {rid!r} used_usd invalid: {used!r}")
        used_in = result.get("used_input_tokens")
        used_out = result.get("used_output_tokens")
        for fname, val in (("used_input_tokens", used_in),
                           ("used_output_tokens", used_out)):
            if isinstance(val, bool) or not isinstance(val, int) or val < 0:
                raise Refusal(EXIT_GATE,
                              f"prior v2 run {rid!r} {fname} invalid: "
                              f"{val!r}")
        state["used_input"] += used_in
        state["used_output"] += used_out
        attempts_dir = d / "attempts"
        files = sorted(attempts_dir.glob("*.json")) if attempts_dir.is_dir() \
            else []
        attempted_list = result.get("attempted_calls")
        if not isinstance(attempted_list, list) or \
                sorted(attempted_list) != [int(f.stem.split("-")[1])
                                           for f in files]:
            raise Refusal(EXIT_GATE,
                          f"prior v2 run {rid!r} attempt records do not match "
                          "its terminal attempted_calls - stale/incomplete "
                          "state; fail closed")
        state["used_usd"] += used_d
        state["attempts"] += len(files)
        for f in files:
            try:
                fn_call = int(f.stem.split("-")[1])
            except (IndexError, ValueError):
                raise Refusal(EXIT_GATE,
                              f"prior v2 run {rid!r} unexpected attempt "
                              f"filename {f.name!r} - unknown state")
            try:
                rec = load_json(f)
            except (OSError, ValueError):
                raise Refusal(EXIT_GATE,
                              f"prior v2 run {rid!r} attempt {f.name} "
                              "unreadable - fail closed")
            call = rec.get("call")
            if call != fn_call or not isinstance(call, int) \
                    or not 1 <= call <= ATTEMPT_CEILING:
                raise Refusal(EXIT_GATE,
                              f"prior v2 run {rid!r} attempt {f.name} call "
                              f"{call!r} does not match its filename/schedule "
                              "range - unknown state")
            if call in state["attempt_records"]:
                other = state["attempt_records"][call][0].name
                raise Refusal(EXIT_GATE,
                              f"duplicate prior attempt for call {call} in "
                              f"runs {other!r} and {rid!r} - one attempt per "
                              "scheduled cell maximum")
            if cell_key(rec) != cell_key(sched[call - 1]):
                raise Refusal(EXIT_GATE,
                              f"prior attempt call-{call:03d} ({rid!r}) does "
                              "not match its frozen schedule row - "
                              "tampered/unknown state; fail closed")
            reserved = rec.get("reserved_input_units")
            if isinstance(reserved, bool) or not isinstance(reserved, int) \
                    or reserved < 0:
                raise Refusal(EXIT_GATE,
                              f"prior attempt call-{call:03d} ({rid!r}) "
                              f"reserved_input_units invalid: {reserved!r}")
            state["reserved_in"] += reserved
            state["attempt_records"][call] = (d, rec)
    return state


def stage_sequence_gate(state: dict, sched: list) -> int:
    """Contiguous-prefix and completion gate for STRICT per-answer progress.
    Returns k = number of prior stage attempts, i.e. the 0-based schedule
    index of THE single next cell this invocation may dispatch (call k+1).
    Prior attempts must be exactly {1..k} - no skip, no reorder, no rerun -
    and a finished stage may make no further call under this version."""
    calls = sorted(state["attempt_records"])
    k = len(calls)
    if calls != list(range(1, k + 1)):
        raise Refusal(EXIT_GATE,
                      f"prior attempts {calls} are not the contiguous "
                      f"schedule prefix 1..{k} - no skip, no reorder; fail "
                      "closed")
    if k >= ATTEMPT_CEILING:
        raise Refusal(EXIT_GATE,
                      f"stage one complete: all {ATTEMPT_CEILING} scheduled "
                      "attempts are dispatched - this version may make no "
                      "further provider call (any later work needs a new, "
                      "separately reviewed version)")
    return k


def verify_prior_semantic_reviews(state: dict, sched: list, msgs: list,
                                  prompt_digests: dict,
                                  receipt_sha: str) -> None:
    """The STRICT per-answer semantic checkpoint, checked BEFORE price fetch,
    credential read or any network access.

    For EVERY earlier completed output, in schedule row order, an independent
    review must exist at ``runs/<run-id>/semantic-reviews/call-NNN.json`` with
    verdict PASS, bound to: the preserved response hash, the score-blind
    sidecar hash (whose content is re-derived and compared), the frozen
    system-prompt and user-message hashes, and RUBRIC_VERSION - plus named
    reviewer identity/session and a statement.

    P1 anchoring: every message/prompt binding in the attempt record, the
    sidecar's ``frozen_dossier`` block and the review itself is compared to
    the frozen schedule/messages/prompt bytes RE-READ for that call in this
    invocation (``msgs``/``prompt_digests`` passed in from the verified
    frozen inputs, whose receipt bindings anchor them), never merely to the
    other writable files under ``runs/``, and each attempt must carry this
    invocation's receipt hash. A mutually consistent edit of record +
    sidecar + review inside the writable run directory therefore cannot
    pass. Verdicts FAIL/UNCERTAIN, any missing or tampered artifact, a
    score/rank key inside the review, or a prior FAILED attempt blocks ALL
    later calls. This runner never writes a review file and never authors a
    verdict; acceptance never depends on any model score.

    Raw-output integrity: before the score-blind sidecar is derived, the
    preserved ``raw_response`` text is strictly re-parsed, its assistant
    content is validated under the EXISTING frozen output contract, and that
    parse must EXACTLY equal the record's ``parsed_output`` - so record,
    sidecar and review cannot diverge from the preserved provider output
    while ``raw_response`` stays unchanged. Malformed, missing or mismatched
    raw output blocks ALL later calls before price fetch, credential read or
    any network access. Guarantee: detection of any INCONSISTENT edit among
    the writable artifacts relative to the stored raw text and the
    receipt-bound frozen inputs. Non-cryptographic limit: all digests here
    are equality cross-checks, not signatures or MACs - an actor able to
    rewrite ``runs/`` could rewrite ``raw_response`` and its recorded hash
    consistently, and reviews/receipt remain self-asserted. This is
    integrity checking only, not a semantic classifier or rating rule."""
    for call in sorted(state["attempt_records"]):
        run_dir, rec = state["attempt_records"][call]
        if not isinstance(rec.get("parsed_output"), dict) \
                or not isinstance(rec.get("raw_response"), str):
            raise Refusal(
                EXIT_GATE,
                f"prior attempt call-{call:03d} (run {run_dir.name!r}) "
                "recorded a FAILED/partial output with no completed answer - "
                "a failed attempt terminally stops stage one: no "
                "regeneration, no replacement cell, no retry; any later "
                "version requires its own disclosed review")
        # ---- frozen anchors for THIS call (independently re-derived) ------
        row = sched[call - 1] if 1 <= call <= len(sched) else None
        msg_row = msgs[call - 1] if 1 <= call <= len(msgs) else None
        if row is None or msg_row is None \
                or row.get("call") != call or msg_row.get("call") != call:
            raise Refusal(EXIT_GATE,
                          f"frozen schedule/message rows for call-{call:03d} "
                          "missing or misaligned - fail closed")
        expected_msg_sha = sha(msg_row["message"].encode("utf-8"))
        if msg_row.get("message_sha256") != expected_msg_sha:
            raise Refusal(EXIT_GATE,
                          f"frozen message bytes for call-{call:03d} do not "
                          "re-hash to their recorded digest - fail closed")
        expected_prompt_sha = prompt_digests[row["variant"]]
        expected_source_v1 = row["source_v1_call"]
        drifted = []
        if rec.get("user_message_sha256") != expected_msg_sha:
            drifted.append("user_message_sha256")
        if rec.get("system_prompt_sha256") != expected_prompt_sha:
            drifted.append("system_prompt_sha256")
        if rec.get("source_v1_call") != expected_source_v1:
            drifted.append("source_v1_call")
        if rec.get("preflight_receipt_sha256") != receipt_sha:
            drifted.append("preflight_receipt_sha256")
        if drifted:
            raise Refusal(
                EXIT_GATE,
                f"prior attempt call-{call:03d} does not match the verified "
                "frozen schedule/message/prompt bytes for that call or its "
                f"invocation receipt ({', '.join(drifted)}) - writable-record "
                "tampering; blocks all later calls")
        # ---- raw-output integrity: re-derive parsed_output from the stored
        # raw provider text BEFORE the sidecar is derived. The record, sidecar
        # and review are all writable; the preserved raw text is what they
        # must agree with. Existing frozen contract only - no new rule.
        try:
            body = json_loads_strict(rec["raw_response"])
        except ValueError as exc:
            raise Refusal(EXIT_GATE,
                          f"prior attempt call-{call:03d} preserved raw "
                          f"response is not strict JSON ({exc}) - blocks all "
                          "later calls")
        choices = body.get("choices") if isinstance(body, dict) else None
        choice0 = choices[0] if isinstance(choices, list) and choices \
            and isinstance(choices[0], dict) else None
        message = choice0.get("message") if choice0 else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise Refusal(EXIT_GATE,
                          f"prior attempt call-{call:03d} preserved raw "
                          "response has no usable assistant content - blocks "
                          "all later calls")
        try:
            derived_output = validate_output_contract(content)
        except Refusal as exc:
            raise Refusal(EXIT_GATE,
                          f"prior attempt call-{call:03d} assistant content "
                          f"fails the frozen output contract ({exc.reason}) "
                          "- blocks all later calls")
        if derived_output != rec["parsed_output"]:
            raise Refusal(EXIT_GATE,
                          f"prior attempt call-{call:03d}: parsed_output does "
                          "not equal the frozen-contract parse of the "
                          "preserved raw response (writable-record tampering; "
                          "raw_response left unchanged) - blocks all later "
                          "calls")
        expected_sidecar = score_blind_sidecar(
            rec["parsed_output"], expected_prompt_sha, expected_msg_sha,
            expected_source_v1)
        side_file = sidecar_path(run_dir, call)
        if not side_file.is_file():
            raise Refusal(EXIT_GATE,
                          f"score-blind sidecar missing for call-{call:03d} "
                          f"({side_file}) - blocks all later calls")
        try:
            actual_sidecar = load_json(side_file)
        except (OSError, ValueError) as exc:
            raise Refusal(EXIT_GATE,
                          f"sidecar for call-{call:03d} unreadable ({exc}) - "
                          "blocks all later calls")
        if actual_sidecar != expected_sidecar:
            raise Refusal(EXIT_GATE,
                          f"sidecar for call-{call:03d} does not equal the "
                          "score-blind projection of the preserved output "
                          "against the verified frozen message/prompt "
                          "digests for that call (tampered or rewritten) - "
                          "blocks all later calls")
        sidecar_digest = sha(side_file.read_bytes())
        resp_digest = sha(rec["raw_response"].encode("utf-8"))
        if rec.get("raw_response_sha256") != resp_digest:
            raise Refusal(EXIT_GATE,
                          f"attempt call-{call:03d} raw_response_sha256 "
                          "drift - integrity failure; fail closed")
        rv_file = review_path(run_dir, call)
        if not rv_file.is_file():
            raise Refusal(
                EXIT_GATE,
                f"missing independent semantic review for call-{call:03d} "
                f"({rv_file}) - a fresh PASS review bound to "
                "response_sha256, the sidecar sha256, the frozen "
                "system-prompt/user-message hashes and RUBRIC_VERSION is "
                "required before any later dispatch")
        try:
            rv = load_json(rv_file)
        except (OSError, ValueError) as exc:
            raise Refusal(EXIT_GATE,
                          f"semantic review for call-{call:03d} unreadable "
                          f"({exc}) - blocks all later calls")
        if not isinstance(rv, dict):
            raise Refusal(EXIT_GATE,
                          f"semantic review for call-{call:03d} is not a "
                          "JSON object - blocks all later calls")
        verdict = rv.get("verdict")
        if verdict not in REVIEW_VERDICTS:
            raise Refusal(EXIT_GATE,
                          f"semantic review for call-{call:03d} carries an "
                          f"invalid verdict {verdict!r} (must be one of "
                          f"{list(REVIEW_VERDICTS)}) - blocks all later calls")
        if verdict != "PASS":
            raise Refusal(
                EXIT_GATE,
                f"semantic review verdict {verdict!r} for call-{call:03d} "
                "blocks all later calls (never retried, overridden or "
                "re-scored by this runner; recovery needs a new reviewed "
                "version)")
        problems = []
        if rv.get("review_version") != REVIEW_VERSION:
            problems.append(f"review_version must be {REVIEW_VERSION}")
        leaked = _collect_keys(rv, ("score", "rank", "ranking", "band"))
        if leaked:
            problems.append("review must be score-blind - unexpected keys "
                            f"{leaked}")
        if rv.get("response_sha256") != resp_digest:
            problems.append("response_sha256 does not match the preserved "
                            "response text")
        if rv.get("sidecar_sha256") != sidecar_digest:
            problems.append("sidecar_sha256 does not match the sidecar file")
        if rv.get("user_message_sha256") != expected_msg_sha:
            problems.append("user_message_sha256 does not match the verified "
                            "frozen dossier message bytes")
        if rv.get("system_prompt_sha256") != expected_prompt_sha:
            problems.append("system_prompt_sha256 does not match the "
                            "verified frozen prompt bytes")
        if rv.get("rubric_version") != RUBRIC_VERSION:
            problems.append("rubric_version mismatch")
        rev = rv.get("reviewer") if isinstance(rv.get("reviewer"), dict) \
            else {}
        for field in ("name", "session"):
            if not isinstance(rev.get(field), str) \
                    or not rev.get(field).strip():
                problems.append(
                    f"reviewer.{field} must be a non-empty string (the "
                    "actual reviewer identity/session is recorded, never "
                    "invented or auto-authored)")
        for field in ("reviewed_at", "statement"):
            if not isinstance(rv.get(field), str) \
                    or not rv.get(field).strip():
                problems.append(f"{field} must be a non-empty string")
        if problems:
            raise Refusal(
                EXIT_GATE,
                f"independent semantic review for call-{call:03d} rejected - "
                "blocks all later calls: " + "; ".join(problems))
        state["prior_reviews"].append({
            "call": call, "run_id": run_dir.name,
            "review_sha256": sha(rv_file.read_bytes()),
            "verdict": verdict, "reviewer": rev,
            "reviewed_at": rv["reviewed_at"]})


def total_dispatch_violation(prior_v2_attempts: int, planned: int) -> str | None:
    total = PRIOR_DISPATCHES + prior_v2_attempts + planned
    if total > TOTAL_DISPATCH_CEILING:
        return (f"combined dispatch ceiling {TOTAL_DISPATCH_CEILING} "
                f"({PRIOR_DISPATCHES} previous dispatches + new) exceeded: "
                f"{PRIOR_DISPATCHES} prior + {prior_v2_attempts} prior v2 + "
                f"{planned} planned = {total}")
    return None


# --------------------------------------------------------------------------- #
# Ceilings (exact Decimal accounting; checked before every dispatch)
# --------------------------------------------------------------------------- #

def pre_dispatch_ceiling_violation(k, plan, v2_prior,
                                   combined_prior) -> str | None:
    """Pre-price/dispatch ceilings for THE single call this invocation may
    dispatch (next = call k+1, plan index k). The USD comparison needs fetched
    prices and is enforced by ``prior_budget_violation`` against THIS call's
    worst case plus the exact combined prior spend (v1 exact + prior v2), and
    re-checked against billed usage after the call."""
    if k + 1 > ATTEMPT_CEILING:
        return (f"attempt ceiling reached: {k} prior stage attempts + "
                f"{MAX_ATTEMPTS_PER_INVOCATION} > {ATTEMPT_CEILING}")
    if k >= len(plan["per_call_input"]):
        return "schedule exhausted"
    total = PRIOR_DISPATCHES + k + MAX_ATTEMPTS_PER_INVOCATION
    if total > TOTAL_DISPATCH_CEILING:
        return (f"combined dispatch ceiling {TOTAL_DISPATCH_CEILING} "
                f"exceeded: {PRIOR_DISPATCHES} prior + {k} stage + "
                f"{MAX_ATTEMPTS_PER_INVOCATION} planned = {total}")
    if not isinstance(combined_prior, Decimal) \
            or not combined_prior.is_finite() or combined_prior < 0:
        return ("accounting corrupted: prior shared cost is not a finite "
                "non-negative decimal")
    if not isinstance(v2_prior["used_usd"], Decimal) \
            or not v2_prior["used_usd"].is_finite() \
            or v2_prior["used_usd"] < 0:
        return ("accounting corrupted: prior v2 cost is not a finite "
                "non-negative decimal")
    for name in ("used_input", "used_output", "reserved_in"):
        value = v2_prior[name]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return (f"accounting corrupted: prior {name} is not a "
                    "non-negative integer")
    if v2_prior["reserved_in"] + plan["per_call_input"][k] \
            > RESERVATION_AGGREGATE_UNITS:
        return (f"aggregate input reservation ceiling "
                f"{RESERVATION_AGGREGATE_UNITS} units: "
                f"{v2_prior['reserved_in']} reserved by prior invocations + "
                f"{plan['per_call_input'][k]} for this call")
    if v2_prior["used_input"] + plan["per_call_input"][k] \
            > RESERVATION_AGGREGATE_UNITS:
        return (f"aggregate input reservation ceiling "
                f"{RESERVATION_AGGREGATE_UNITS} units: "
                f"{v2_prior['used_input']} billed by prior invocations + "
                f"{plan['per_call_input'][k]} reserved for this call")
    if v2_prior["used_output"] + V2_MAX_OUTPUT_PER_CALL \
            > V2_AGG_OUTPUT_RESERVATION:
        return (f"v2 aggregate output reservation: "
                f"{v2_prior['used_output']} billed by prior invocations + "
                f"{V2_MAX_OUTPUT_PER_CALL} for this call > "
                f"{V2_AGG_OUTPUT_RESERVATION} tokens")
    return None


def cell_key(row) -> tuple:
    """Cell identity shared by frozen schedule rows and WRITTEN attempt
    records. Schedule rows carry ``model``; attempt records carry
    ``requested_model`` (the runner never writes ``model``) - read whichever
    exists so the prior-attempt overlap gate matches real records instead of
    collapsing every row to model=None."""
    model = row.get("model") or row.get("requested_model")
    return (row.get("sentinel"), row.get("case"), model,
            row.get("variant"), row.get("draw"))


def validate_sentinel_semantics(sentinel: str, parsed_output: dict) -> None:
    """Context-aware semantic output check for the EMPTY-dossier sentinels.

    An empty-dossier sentinel must abstain: ``status: "insufficient_evidence"``
    with ``score: null``. Any other output is a semantic failure of the
    empty-evidence condition and stops the stage (raw output preserved, no
    retry, no interpretation). Core cells are NOT constrained here: under the
    unchanged contract they may abstain or return a finite score. This is a
    narrow mechanical check only - the broader independent semantic review of
    outputs is a separate process, still open under independent consultation.
    """
    if sentinel != "empty":
        return
    if not isinstance(parsed_output, dict):
        raise Refusal(EXIT_STOPPED,
                      "empty-dossier sentinel semantic failure: no parsed "
                      "output object to check abstention against - stopped "
                      "without retry")
    status = parsed_output.get("status")
    score = parsed_output.get("score", "<missing>")
    if status != "insufficient_evidence" or score is not None:
        raise Refusal(
            EXIT_STOPPED,
            "empty-dossier sentinel semantic failure: expected status "
            "'insufficient_evidence' with score null, got "
            f"status={status!r} score={score!r} - the empty-evidence "
            "sentinel must abstain; stopped without retry (raw output "
            "preserved verbatim, never interpreted)")


# --------------------------------------------------------------------------- #
# Plan and prices (reservation arithmetic; fail closed on drift)
# --------------------------------------------------------------------------- #

def build_plan(root: Path, sched: list, msgs: list, manifest: dict) -> dict:
    """Worst-case reservation from frozen bytes; refuses on drift."""
    prompt_bytes = {}
    for v in VARIANTS:
        p = root / "frozen" / f"single_{v.lower()}.txt"
        prompt_bytes[v] = len(p.read_bytes())
    per_call_in = []
    for row, msg in zip(sched, msgs):
        if row.get("model") not in MODELS or row.get("variant") not in VARIANTS:
            raise Refusal(EXIT_GATE, f"schedule row {row.get('call')} carries "
                                     "an unregistered model or variant")
        body = msg["message"]
        reserved = (prompt_bytes[row["variant"]]
                    + len(body.encode("utf-8"))) // BYTES_PER_TOKEN \
            + FIXED_OVERHEAD_TOKENS_PER_CALL
        per_call_in.append(reserved)
    max_per_call = max(per_call_in)
    agg_in = sum(per_call_in)
    plan_rec = (manifest.get("plan") or {})
    problems = []
    if max_per_call > RESERVATION_PER_CALL_UNITS:
        problems.append(f"worst-case input reservation {max_per_call} "
                        f"units/call > ceiling {RESERVATION_PER_CALL_UNITS}")
    if agg_in > RESERVATION_AGGREGATE_UNITS:
        problems.append(f"worst-case aggregate input reservation {agg_in} > "
                        f"ceiling {RESERVATION_AGGREGATE_UNITS}")
    if max_per_call != EXPECTED_PLAN["plan_max_per_call_units"] \
            or agg_in != EXPECTED_PLAN["plan_aggregate_units"] \
            or plan_rec.get("plan_max_per_call_units") != max_per_call \
            or plan_rec.get("plan_aggregate_units") != agg_in:
        problems.append("recomputed reservation plan does not equal the "
                        "predeclared plan (66609 max / 1112686 aggregate)")
    agg_out = ATTEMPT_CEILING * V2_MAX_OUTPUT_PER_CALL
    if agg_out != V2_AGG_OUTPUT_RESERVATION:
        problems.append("v2 output reservation arithmetic drifted")
    if problems:
        raise Refusal(EXIT_GATE,
                      "reservation plan rejected (ceilings are never raised): "
                      + "; ".join(problems))
    return {"per_call_input": per_call_in,
            "max_per_call_input": max_per_call,
            "aggregate_input": agg_in, "aggregate_output": agg_out,
            "worst_usd": [Decimal(0)] * len(per_call_in),
            "input_method": "UTF-8 byte count of the frozen prompt + message + "
                            f"{FIXED_OVERHEAD_TOKENS_PER_CALL} fixed "
                            "chat-framing units per call (administrative "
                            "reservation units: conservative under the stated "
                            "assumptions, NOT a guaranteed provider tokenizer "
                            "bound)"}


def cost_reservation(plan: dict, sched: list, prices: dict) -> None:
    """Worst-case Decimal USD per attempt: reserved input x prompt price +
    11000 output (including reasoning) x completion price."""
    worst = []
    for row, reserved in zip(sched, plan["per_call_input"]):
        p = prices[row["model"]]
        worst.append(Decimal(reserved) * p["prompt"]
                     + Decimal(V2_MAX_OUTPUT_PER_CALL) * p["completion"])
    plan["worst_usd"] = worst


def prior_budget_violation(prior_cost: Decimal, plan: dict,
                           total_worst: Decimal) -> str | None:
    caps = plan["caps"]
    if total_worst < 0 or not total_worst.is_finite():
        return "worst-case cost reservation is not a finite non-negative decimal"
    if prior_cost + total_worst > caps["usd_ceiling"]:
        return (f"budget already consumed: prior exact ${dec_str(prior_cost)} "
                f"+ this call's worst-case reservation "
                f"${dec_str(total_worst)} > ${caps['usd_ceiling']} "
                "(checked per call between dispatches; locally enforced "
                "guard, no provider-side hard limit exists)")
    return None


# --------------------------------------------------------------------------- #
# Provider transport (real implementations; used only after every gate)
# --------------------------------------------------------------------------- #

def _https(method: str, url: str, payload=None, headers=None,
           timeout: float = TRANSPORT_TIMEOUT_SECONDS) -> tuple:
    import urllib.error
    import urllib.request
    if not url.startswith("https://") or not url.startswith(API_BASE):
        raise Refusal(EXIT_GATE, f"refusing non-fixed endpoint: {url}")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {},
                                 method=method)
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


def _price(value, model, kind) -> Decimal:
    try:
        p = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise Refusal(EXIT_GATE,
                      f"unknown {kind} price for {model}: {value!r}")
    if not p.is_finite() or p <= 0:
        raise Refusal(EXIT_GATE,
                      f"invalid/non-positive {kind} price for {model}: "
                      f"{value!r} - refusing unknown prices")
    return p


def fetch_prices() -> dict:
    """Provider model-price metadata over the fixed HTTPS endpoint, explicit
    timeout, fail closed. Unknown or missing prices for a pre-registered
    model refuse before any dispatch."""
    status, body = https_get(MODELS_URL, {"Accept": "application/json"},
                             PRICE_FETCH_TIMEOUT_SECONDS)
    if status != 200:
        raise Refusal(EXIT_GATE, f"price metadata fetch failed: HTTP {status}")
    try:
        doc = json.loads(body, parse_constant=_reject_constant)
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
            prices[entry["id"]] = {
                "prompt": _price(pricing.get("prompt"), entry["id"], "prompt"),
                "completion": _price(pricing.get("completion"), entry["id"],
                                     "completion")}
    missing = [m for m in MODELS if m not in prices]
    if missing:
        raise Refusal(EXIT_GATE, f"no price metadata for pre-registered "
                                 f"model(s) {missing} - refusing unknown prices")
    return prices


def load_secret() -> str:
    """Reads the credential from the environment; never logged, never echoed."""
    return os.environ.get(SECRET_ENV, "").strip()


# --------------------------------------------------------------------------- #
# Request construction (frozen bytes only; no fallback, no cache, no retry)
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
        # no model fallback list, no cache directives, no reasoning parameter
        "provider": {"allow_fallbacks": False},
    }
    if set(payload) != set(REQUEST_KEYS):
        raise Refusal(EXIT_GATE, "request shape drifted from the fixed whitelist")
    return payload


# --------------------------------------------------------------------------- #
# Validation (strict output contract + strict billing/usage/routing checks)
# --------------------------------------------------------------------------- #

def _reject_constant(name):
    raise ValueError(f"non-finite JSON number {name}")


def json_loads_strict(text):
    return json.loads(text, parse_constant=_reject_constant)


def _cost_or_none(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    f = float(value)
    if not math.isfinite(f) or f < 0:
        return None
    return f


def _usage_ints(usage):
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
    ``cost is None`` means the charge is unknown, i.e. an unreconciled
    liability - never assumed to be zero."""
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
        out["reason"] = "billed usage recorded; cost missing/invalid - charge " \
                        "unknown"
    return out


def validate_output_contract(content: str) -> dict:
    """The unchanged v1 single-score JSON output contract.

    A single bare JSON object (no prose/fences); status ok -> finite numeric
    score in [0,1]; insufficient_evidence -> score must be null; the required
    fields must carry their declared types. Malformed content raises Refusal
    (the stage stops; the raw output is retained; there is no retry)."""
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
                          "output contract: status insufficient_evidence "
                          f"requires \"score\": null, got {obj.get('score')!r}")
    else:
        raise Refusal(EXIT_STOPPED, "output contract: status must be one of "
                      f"{OUTPUT_STATUSES}, got {status!r}")
    why = obj.get("why")
    if not isinstance(why, str) or not why.strip():
        raise Refusal(EXIT_STOPPED,
                      "output contract: 'why' must be a non-empty string")
    for field in OUTPUT_CONTRACT_FIELDS:
        if field == "evidence_ids":
            continue
        v = obj.get(field)
        if not isinstance(v, str) or not v.strip():
            raise Refusal(EXIT_STOPPED,
                          f"output contract: '{field}' must be a non-empty "
                          f"string, got {v!r}")
    ev = obj.get("evidence_ids")
    ev_ok = ((isinstance(ev, str) and ev.strip())
             or (isinstance(ev, list) and bool(ev)
                 and all(isinstance(x, str) and x.strip() for x in ev)))
    if not ev_ok:
        raise Refusal(EXIT_STOPPED,
                      "output contract: 'evidence_ids' must be a non-empty "
                      f"string or a list of non-empty strings, got {ev!r}")
    return obj


def _validate_usage(usage, reserved_in: int, worst_usd: Decimal) -> dict:
    """Strict billing/usage semantics: unknown or inconsistent fields refuse.

    REQUIRED FIELDS, observed as present in all five reviewed prior records:
    consistent prompt/completion/total integer token counts; finite
    non-negative ``cost`` > 0 when tokens were billed; ``is_byok`` present and
    false; ``prompt_tokens_details`` with cached/cache-write counters;
    ``completion_tokens_details`` with a ``reasoning_tokens`` counter.

    CACHE (per the separate consult): requests never carry cache directives,
    so provider-initiated cache READS are an allowed execution condition when
    the reported arithmetic is valid (counts present, non-negative integers,
    cached_tokens <= prompt_tokens, cost finite and within the reservation) -
    they are logged in full with no reproducibility claim. Cache WRITES stop
    the stage: their billing cannot be reconciled with the advertised prices
    this runner fetches, so it is never assumed to be free.

    PREDECLARED FAIL-CLOSED ASSUMPTION (NOT an observation): the reasoning
    count is assumed to be a subset of billed completion, i.e.
    ``reasoning_tokens <= completion_tokens``. The pinned v1 failure record
    itself reported ``reasoning_tokens 2504 > completion_tokens 2000`` -
    exactly why an inconsistent count stops the run instead of being
    reconciled silently. The completion total is the billed output INCLUDING
    reasoning and is never double-counted."""
    if not isinstance(usage, dict):
        raise Refusal(EXIT_STOPPED, "missing billed usage")
    ints = _usage_ints(usage)
    if ints is None:
        raise Refusal(EXIT_STOPPED,
                      f"inconsistent billed usage (totals must match): "
                      f"{json.dumps(usage)[:160]}")
    cost = _cost_or_none(usage.get("cost"))
    if cost is None:
        raise Refusal(EXIT_STOPPED,
                      f"missing/invalid billed cost: {usage.get('cost')!r} "
                      "(unknown billing stops the stage)")
    if usage.get("is_byok") is not False:
        raise Refusal(EXIT_STOPPED,
                      f"unexpected billing mode: is_byok="
                      f"{usage.get('is_byok')!r} (must be present and false)")
    pdet = usage.get("prompt_tokens_details")
    if not isinstance(pdet, dict):
        raise Refusal(EXIT_STOPPED,
                      "unknown usage semantics: prompt_tokens_details missing")
    cache_counts = {}
    for k in ("cached_tokens", "cache_write_tokens"):
        v = pdet.get(k)
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise Refusal(EXIT_STOPPED,
                          f"unknown usage semantics: {k} missing/invalid "
                          f"({v!r})")
        cache_counts[k] = v
    if cache_counts["cached_tokens"] > ints["prompt_tokens"] \
            or cache_counts["cache_write_tokens"] > ints["prompt_tokens"]:
        raise Refusal(
            EXIT_STOPPED,
            f"inconsistent cache accounting: cached/write token counts "
            f"{cache_counts} exceed billed prompt_tokens "
            f"{ints['prompt_tokens']}")
    if cache_counts["cache_write_tokens"] > 0:
        raise Refusal(
            EXIT_STOPPED,
            "cache WRITE tokens reported "
            f"(cache_write_tokens={cache_counts['cache_write_tokens']}) - "
            "cache-write billing cannot be reconciled with the advertised "
            "prices this runner fetches, so the stage stops rather than "
            "assume it is free (provider-initiated cache READS remain "
            "allowed with valid reported accounting)")
    cdet = usage.get("completion_tokens_details")
    if not isinstance(cdet, dict):
        raise Refusal(EXIT_STOPPED,
                      "unknown reasoning count semantics: "
                      "completion_tokens_details missing")
    rt = cdet.get("reasoning_tokens")
    if isinstance(rt, bool) or not isinstance(rt, int) or rt < 0:
        raise Refusal(EXIT_STOPPED,
                      f"unknown reasoning count semantics: reasoning_tokens "
                      f"missing/invalid ({rt!r})")
    if rt > ints["completion_tokens"]:
        raise Refusal(EXIT_STOPPED,
                      f"inconsistent reasoning count semantics: "
                      f"reasoning_tokens {rt} > billed completion "
                      f"{ints['completion_tokens']} (provider usage fields "
                      "inconsistent - stop; never reconciled silently)")
    if ints["prompt_tokens"] > reserved_in:
        raise Refusal(EXIT_STOPPED,
                      f"reservation/accounting failure: billed input "
                      f"{ints['prompt_tokens']} > reserved {reserved_in} "
                      "units (byte+framing assumption held not to cover it)")
    if ints["completion_tokens"] > V2_MAX_OUTPUT_PER_CALL:
        raise Refusal(EXIT_STOPPED,
                      f"reservation/accounting failure: billed output "
                      f"{ints['completion_tokens']} > {V2_MAX_OUTPUT_PER_CALL} "
                      "max output (including reasoning)")
    cost_d = Decimal(str(cost))
    if ints["prompt_tokens"] + ints["completion_tokens"] > 0 and cost_d == 0:
        raise Refusal(EXIT_STOPPED,
                      "inconsistent billing: zero cost for billed tokens "
                      "(unknown price - stop)")
    if cost_d > worst_usd:
        raise Refusal(EXIT_STOPPED,
                      f"reservation integrity failure: billed ${dec_str(cost_d)} "
                      f"> worst-case reservation ${dec_str(worst_usd)} for "
                      "this call (price metadata inconsistent with billing)")
    return {"cost": cost_d, **ints, **cache_counts}


def validate_response(status: int, raw: str, requested_model: str,
                      reserved_in: int, worst_usd: Decimal) -> dict:
    """Returns evidence fields; raises Refusal on ANY stop condition."""
    if status != 200:
        raise Refusal(EXIT_STOPPED, f"provider returned HTTP {status} (API error)")
    try:
        doc = json_loads_strict(raw)
    except ValueError:
        raise Refusal(EXIT_STOPPED,
                      "unexpected provider shape: body is not strict JSON")
    if not isinstance(doc, dict) or "error" in doc:
        raise Refusal(EXIT_STOPPED,
                      f"API error or unexpected provider shape: "
                      f"{json.dumps(doc)[:200]}")
    choices = doc.get("choices")
    if not isinstance(choices, list) or not choices \
            or not isinstance(choices[0], dict):
        raise Refusal(EXIT_STOPPED, "failed output: no choices")
    choice = choices[0]
    message = choice.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise Refusal(EXIT_STOPPED, "failed/empty output: no assistant content")
    finish = choice.get("finish_reason")
    if not isinstance(finish, str) or not finish:
        raise Refusal(EXIT_STOPPED, "failed output: missing finish_reason")
    if finish != "stop":
        raise Refusal(EXIT_STOPPED,
                      f"truncated/non-final output: finish_reason={finish!r} "
                      "(length/content-filter/etc.)")
    model = doc.get("model")
    if model != requested_model:
        raise Refusal(EXIT_STOPPED,
                      f"provider mismatch: requested {requested_model!r}, "
                      f"returned {model!r} (model substitution)")
    provider = doc.get("provider")
    allowed = EXPECTED_PROVIDERS.get(requested_model, ())
    if not isinstance(provider, str) or not provider.strip():
        raise Refusal(EXIT_STOPPED,
                      "unexpected routing: provider attribution missing")
    if provider not in allowed:
        raise Refusal(EXIT_STOPPED,
                      f"unexpected routing: provider {provider!r} for "
                      f"{requested_model!r} is outside the predeclared set "
                      f"{list(allowed)}")
    usage_ev = _validate_usage(doc.get("usage"), reserved_in, worst_usd)
    parsed_output = validate_output_contract(content)
    return {"http_status": status, "finish_reason": finish,
            "returned_model": model, "returned_provider": provider,
            "usage": doc.get("usage"), "cost": usage_ev["cost"],
            "billed_input_tokens": usage_ev["prompt_tokens"],
            "billed_output_tokens": usage_ev["completion_tokens"],
            "cache_usage": {
                "cached_read_tokens": usage_ev["cached_tokens"],
                "cache_write_tokens": usage_ev["cache_write_tokens"],
                "note": "provider-initiated; the request carried no cache "
                       "directive and none was warmed/forced/busted; full "
                       "usage preserved verbatim in 'usage'; execution "
                       "condition only - no reproducibility claim"},
            "parsed_output": parsed_output}


# --------------------------------------------------------------------------- #
# Execution
# --------------------------------------------------------------------------- #

def execute(cfg) -> int:
    root = cfg["root"]
    if not cfg["execute"]:
        print("runner disabled: no --execute flag. " + usage())
        return EXIT_USAGE

    # ---- static gates first (no writes, no network, no credential) --------
    manifest = load_json(root / "frozen" / "manifest.json")
    verify_manifest(manifest, root, cfg["data_path"], cfg["v1_root"])
    sched_doc = load_json(root / "frozen" / "schedule.json")
    msgs_doc = load_json(root / "frozen" / "user_messages.json")
    validate_run_id_format(cfg["run_id"])
    sched = sched_doc["rows"]
    msgs = verify_schedule(sched, msgs_doc, cfg["v1_root"])

    # ---- ONE shared lock BEFORE any ledger/prior-state read ---------------
    lock_path = acquire_lock(Path(cfg["lock_path"]), cfg["run_id"])
    try:
        # ---- reviewed v2 preflight receipt (absent until reviewed) --------
        receipt_path = Path(cfg["receipt"]) if cfg["receipt"] \
            else root / RECEIPT_NAME
        if not receipt_path.is_file():
            raise Refusal(EXIT_GATE,
                          f"no reviewed v2 preflight receipt at {receipt_path} "
                          f"- {RECEIPT_NAME} must bind every exact input, "
                          "protocol.md, runner.py/test_runner.py, the source "
                          "data, the pinned v1 records and the independent "
                          "methodology/code/evidence reviews (absent until "
                          "reviewed); execution refused")
        bindings = current_bindings(root, cfg["v1_root"], cfg["data_path"])
        receipt = load_json(receipt_path)
        verify_receipt(receipt, bindings)
        receipt_sha = sha(receipt_path.read_bytes())

        # ---- prior state (read only under the lock) ----------------------
        v1_prior = read_v1_prior(cfg["v1_root"])
        run_dir = validate_run_id(cfg["run_id"], root)   # post-lock existence
        v2_prior = prior_v2_state(root, sched)
        # STRICT per-answer checkpoint: contiguous prefix {1..k}, stage
        # completion, failed-attempt and PASS-review gates - ALL before price
        # fetch, credential read or any network access.
        k = stage_sequence_gate(v2_prior, sched)   # next call = k+1 (idx k)
        # Frozen anchors for the per-answer gate: re-read the immutable
        # prompt bytes here and require them to equal the pinned v1 digests
        # (verify_manifest already checked this once; re-derive for the gate).
        prompt_digests = {}
        for v in VARIANTS:
            digest = sha((root / "frozen" /
                          f"single_{v.lower()}.txt").read_bytes())
            if digest != V1_SOURCE_PINS[f"frozen/single_{v.lower()}.txt"]:
                raise Refusal(EXIT_GATE,
                              f"frozen prompt single_{v.lower()}.txt no "
                              "longer matches the pinned v1 hash - fail "
                              "closed before any review gate decision")
            prompt_digests[v] = digest
        verify_prior_semantic_reviews(v2_prior, sched, msgs, prompt_digests,
                                      receipt_sha)
        dispatch_reason = total_dispatch_violation(
            k, MAX_ATTEMPTS_PER_INVOCATION)
        if dispatch_reason:
            raise Refusal(EXIT_GATE, dispatch_reason)
        # exact shared prior spend: v1's pinned reconstruction + prior v2 runs
        combined_prior = v1_prior["cost"] + v2_prior["used_usd"]

        # ---- budget plan (exact Decimal arithmetic) ----------------------
        plan = build_plan(root, sched, msgs, manifest)
        plan["caps"] = {
            "attempt_ceiling_including_failures": ATTEMPT_CEILING,
            "usd_ceiling": MAX_USD,
            "reservation_aggregate_units": RESERVATION_AGGREGATE_UNITS,
            "reservation_per_call_units": RESERVATION_PER_CALL_UNITS,
            "v2_aggregate_output_tokens": V2_AGG_OUTPUT_RESERVATION}
        plan["_sched"] = sched
        ceiling_reason = pre_dispatch_ceiling_violation(k, plan, v2_prior,
                                                        combined_prior)
        if ceiling_reason:
            raise Refusal(EXIT_GATE, ceiling_reason)
        prices = cfg["price_fetch"]()               # network: only after gates
        cost_reservation(plan, sched, prices)
        # USD guard for THIS call only: combined exact prior + this call's
        # worst case must fit the same local USD 10.00 ceiling.
        budget_reason = prior_budget_violation(combined_prior, plan,
                                               plan["worst_usd"][k])
        if budget_reason:
            raise Refusal(EXIT_GATE, budget_reason)

        secret = cfg["secret_loader"]()
        if not secret:
            raise Refusal(EXIT_GATE, f"{SECRET_ENV} is empty or unset - refusing")

        # read/decode the frozen prompts BEFORE creating any directory, so a
        # decode failure can never leave an orphan run directory
        prompt_by_variant = {
            v: (root / "frozen" / f"single_{v.lower()}.txt")
            .read_text(encoding="utf-8") for v in VARIANTS}

        (root / RUNS_DIR).mkdir(exist_ok=True)
        try:
            run_dir.mkdir()
        except FileExistsError:
            raise Refusal(EXIT_GATE,
                          f"run {cfg['run_id']!r} already exists - never "
                          "overwrite or retry")
        (run_dir / "attempts").mkdir()
        # review INPUTS container (the runner never creates REVIEW_REL_DIR -
        # semantic-reviews/ is written only by human/model reviewers)
        (run_dir / SIDECAR_REL_DIR).mkdir()
        cfg["_run_dir"] = run_dir
        return _dispatch_stage(cfg, root, manifest, receipt, receipt_sha,
                               bindings, sched, msgs, plan, prices,
                               combined_prior, v1_prior, v2_prior, k, secret,
                               prompt_by_variant, run_dir)
    finally:
        release_lock(lock_path, cfg["run_id"])


def _dispatch_stage(cfg, root, manifest, receipt, receipt_sha, bindings,
                    sched, msgs, plan, prices, combined_prior, v1_prior,
                    v2_prior, k, secret, prompt_by_variant,
                    run_dir) -> int:
    """Dispatch AT MOST ONE scheduled cell (call k+1, plan index k), append
    its immutable raw/billing evidence plus the score-blind sidecar, then
    terminate - paused until an independent PASS semantic review is recorded.
    No loop, no skip, no reorder, no retry exists in this path."""
    row = sched[k]
    run_record = {
        "run_id": cfg["run_id"], "stage": "country-feasibility-v2 stage one",
        "status": "in_progress", "started_at": utcnow(),
        "dispatch_checkpoint": {
            "max_attempts_per_invocation": MAX_ATTEMPTS_PER_INVOCATION,
            "prior_stage_attempts": k, "dispatched_call": row["call"],
            "semantic_checkpoint": SEMANTIC_CHECKPOINT,
            "prior_semantic_reviews": v2_prior["prior_reviews"]},
        "cache_policy": CACHE_POLICY,
        "stage_prior": {
            "attempts": v2_prior["attempts"],
            "used_usd": dec_str(v2_prior["used_usd"]),
            "used_input_tokens": v2_prior["used_input"],
            "used_output_tokens": v2_prior["used_output"]},
        "adaptive_disclosure": manifest.get("adaptive_disclosure"),
        "api_base": API_BASE, "models": list(MODELS),
        "requested_settings": REQUESTED_SETTINGS,
        "requested_settings_change": SETTINGS_CHANGE,
        "expected_providers": {m: list(p)
                               for m, p in EXPECTED_PROVIDERS.items()},
        "manifest_sha256": bindings["frozen/manifest.json"],
        "receipt_sha256": receipt_sha, "receipt_bindings": bindings,
        "preflight": receipt["preflight"],
        "prior_accounting": {
            "source": "exact Decimal reconstruction from the 4 original "
                      "probe-result.json files + v1 call-001 "
                      "billed_on_failure (deduplicated provider ids, pinned "
                      "raw hashes)",
            "total_usd": dec_str(v1_prior["cost"]),
            "input_tokens": v1_prior["input"],
            "output_tokens": v1_prior["output"],
            "dispatches": v1_prior["dispatches"],
            "record_ids": v1_prior["ids"],
            "note": "rounded v1 summary fields are never used for budgeting"},
        "output_budgets": {
            "historical": HISTORICAL_OUTPUT_BUDGETS,
            "v2_max_output_per_call": V2_MAX_OUTPUT_PER_CALL,
            "v2_aggregate_output_reservation_tokens":
                V2_AGG_OUTPUT_RESERVATION,
            "note": "older and new output budgets retained separately as exact "
                    "integers; never merged or rounded"},
        "plan": {k: v for k, v in plan.items()
                 if k not in ("_sched", "caps", "worst_usd")},
        "plan_worst_usd": [dec_str(w) for w in plan["worst_usd"]],
        "prices_usd_per_token": {m: {k: dec_str(v)
                                     for k, v in p.items()}
                                 for m, p in prices.items()},
        "caps": {"attempt_ceiling_including_failures": ATTEMPT_CEILING,
                 "prior_dispatches": PRIOR_DISPATCHES,
                 "total_dispatch_ceiling": TOTAL_DISPATCH_CEILING,
                 "retries": RETRIES,
                 "usd_ceiling": dec_str(MAX_USD),
                 "reservation_per_call_units": RESERVATION_PER_CALL_UNITS,
                 "reservation_aggregate_units":
                     RESERVATION_AGGREGATE_UNITS},
        "budget_note": "USD guard enforced locally between calls only; not a "
                       "provider-enforced spend limit; a single in-flight call "
                       "is postpaid and can overshoot the local guard before "
                       "the next check; prior shared spend is included in "
                       "every in-run USD comparison while used_usd stays "
                       "stage-local and exact (decimal strings, no rounding)",
        "stop_conditions": [
            "failed/empty/truncated/invalid output - TERMINAL, no retry",
            "API error (HTTP != 200 or error object) - TERMINAL",
            "provider mismatch (model substitution) or unexpected routing "
            "- TERMINAL",
            "unknown or inconsistent billing/usage incl. reasoning-count "
            "semantics, unreconcilable cache-WRITE billing, BYOK - TERMINAL",
            "empty-dossier sentinel not abstaining - TERMINAL",
            "missing/FAIL/UNCERTAIN/tampered prior semantic review - all "
            "later calls blocked before price/credential/network access",
            "budget/reservation/dispatch/attempt ceiling breach",
            "receipt, lock, hash or other integrity failure"],
    }
    write_exclusive(run_dir / "run.json",
                    json.dumps(run_record, indent=1, ensure_ascii=False) + "\n")

    used = {"input": 0, "output": 0, "cost": Decimal(0), "reserved_in": 0}
    attempted = []
    stop_reason = None
    liability = None
    idx = k                       # exactly ONE scheduled cell this invocation
    prompt = prompt_by_variant[row["variant"]]
    message = msgs[idx]["message"]
    payload = build_request(row["model"], prompt, message,
                            REQUESTED_SETTINGS)
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
        "source_v1_call": row["source_v1_call"],
        "preflight_receipt_sha256": receipt_sha,
        "manifest_sha256": bindings["frozen/manifest.json"],
        "source_bindings": bindings,
        "reserved_input_units": plan["per_call_input"][idx],
        "reserved_output_tokens": V2_MAX_OUTPUT_PER_CALL,
        "reserved_usd": dec_str(plan["worst_usd"][idx]),
        "request_headers_logged": headers,
        "requested_at": utcnow(),
        "retry": False,
        "errors": [],
    }
    raw = None
    try:
        status, raw = cfg["transport"](CHAT_URL, payload, real_headers,
                                       TRANSPORT_TIMEOUT_SECONDS)
        evidence = validate_response(status, raw, row["model"],
                                     plan["per_call_input"][idx],
                                     plan["worst_usd"][idx])
        validate_sentinel_semantics(row["sentinel"],
                                    evidence["parsed_output"])
    except Refusal as stop:
        # Preserve the raw body and any parseable billed usage/cost
        # SEPARATELY from the validated fields; partial/tentative values
        # (including any reasoning text) are kept verbatim and NEVER
        # interpreted, extracted or summarized here. An unknown charge is
        # an unreconciled liability, never assumed to be zero.
        billed = parse_billed(raw)
        record["billed_on_failure"] = billed
        record["raw_response"] = raw
        record["raw_response_sha256"] = sha(raw.encode("utf-8")) \
            if isinstance(raw, str) else None
        record["errors"].append(stop.reason)
        record["stop_reason"] = stop.reason
        record["finished_at"] = utcnow()
        if billed["cost"] is None:
            liability = {
                "reason": billed["reason"] or "billed cost unknown",
                "call": row["call"],
                "requires": "human reconciliation and a new reviewed "
                            "version before any further v2 dispatch"}
            record["unreconciled_liability"] = liability
        write_exclusive(run_dir / "attempts"
                        / f"call-{row['call']:03d}.json",
                        json.dumps(record, indent=1, ensure_ascii=False) +
                        "\n")
        attempted.append(row["call"])
        used["reserved_in"] += plan["per_call_input"][idx]
        if billed.get("usage"):
            used["input"] += billed["usage"]["prompt_tokens"]
            used["output"] += billed["usage"]["completion_tokens"]
        if billed["cost"] is not None:
            used["cost"] += Decimal(str(billed["cost"]))
        stop_reason = stop.reason
    if stop_reason is None:
        # success path: immutable raw/billing evidence + score-blind sidecar
        record.update(evidence)
        record["cost"] = dec_str(evidence["cost"])
        # stored response text: decoded utf-8 with replacement (not
        # byte-exact transport bytes); its sha binds the stored text
        record["raw_response"] = raw
        record["raw_response_sha256"] = sha(raw.encode("utf-8"))
        record["finished_at"] = utcnow()
        record["requested_vs_actual"] = {
            "reserved_input_units": plan["per_call_input"][idx],
            "billed_input_tokens": evidence["billed_input_tokens"],
            "reserved_output_tokens": V2_MAX_OUTPUT_PER_CALL,
            "billed_output_tokens": evidence["billed_output_tokens"],
            "reserved_usd": dec_str(plan["worst_usd"][idx]),
            "billed_usd": dec_str(evidence["cost"]),
        }
        write_exclusive(run_dir / "attempts"
                        / f"call-{row['call']:03d}.json",
                        json.dumps(record, indent=1, ensure_ascii=False) +
                        "\n")
        attempted.append(row["call"])
        used["reserved_in"] += plan["per_call_input"][idx]
        used["input"] += evidence["billed_input_tokens"]
        used["output"] += evidence["billed_output_tokens"]
        used["cost"] += evidence["cost"]
        # Score-blind sidecar written alongside the attempt: this runner
        # writes review INPUTS only - never a review file, verdict or PASS.
        sidecar = score_blind_sidecar(
            evidence["parsed_output"], record["system_prompt_sha256"],
            record["user_message_sha256"], record["source_v1_call"])
        write_exclusive(sidecar_path(run_dir, row["call"]),
                        json.dumps(sidecar, indent=1, ensure_ascii=False) +
                        "\n")
        if combined_prior + used["cost"] > MAX_USD:
            stop_reason = ("USD ceiling exceeded by billed usage: shared "
                           f"${dec_str(combined_prior + used['cost'])} = "
                           f"prior ${dec_str(combined_prior)} + "
                           f"stage-local ${dec_str(used['cost'])} > "
                           f"${MAX_USD}")
        if v2_prior["used_output"] + used["output"] \
                > V2_AGG_OUTPUT_RESERVATION:
            stop_reason = ("v2 aggregate output reservation exceeded by "
                           "billed usage across invocations: "
                           f"{v2_prior['used_output']} + "
                           f"{used['output']} > "
                           f"{V2_AGG_OUTPUT_RESERVATION}")

    if stop_reason is None and attempted:
        stage_state = ("stage_attempts_complete" if row["call"]
                       >= ATTEMPT_CEILING
                       else "paused_pending_semantic_review")
        next_requires = (
            "independent semantic review of call "
            f"{row['call']} (this attempt) must record PASS bound to "
            "response_sha256, the score-blind sidecar sha256, the frozen "
            "system-prompt/user-message hashes and RUBRIC_VERSION before "
            "any later dispatch"
            if row["call"] < ATTEMPT_CEILING else
            "the stage's semantic disposition is determined by the "
            "independent review of call " + str(row["call"]) + "; no further "
            "batch or call follows under this version")
    elif stop_reason is not None:
        stage_state = "terminal_failure"
        next_requires = ("none: a failed or ceiling-stopped attempt "
                         "terminally ends this stage - no regeneration, no "
                         "replacement cell, no retry; recovery requires a "
                         "new, separately reviewed version")
    else:                              # zero-attempt stop before dispatch
        stage_state = "terminal_failure"
        next_requires = "none"

    run_record.update({
        "status": "completed" if stop_reason is None else "stopped",
        "stage_state": stage_state,
        "next_dispatch_requires": next_requires,
        "stop_reason": stop_reason,
        "finished_at": utcnow(),
        "attempts": len(attempted),
        "attempted_calls": attempted,
        "unreconciled_liability": liability,
        "used_input_tokens": used["input"],
        "used_output_tokens": used["output"],
        "used_reserved_input_units": used["reserved_in"],
        "used_usd": dec_str(used["cost"]),
        "shared_usd_total": dec_str(combined_prior + used["cost"]),
        "stage_total_attempts": k + len(attempted),
    })
    write_exclusive(run_dir / "result.json",
                    json.dumps(run_record, indent=1, ensure_ascii=False) + "\n")
    if stop_reason is not None:
        print(f"STOP  {stop_reason}")
        return EXIT_STOPPED
    print(f"run {cfg['run_id']}: dispatched one cell (call {row['call']}) "
          f"({used['input']} in / {used['output']} out tokens, "
          f"${dec_str(used['cost'])} this call; "
          f"${dec_str(combined_prior + used['cost'])} shared total); stage "
          f"{stage_state}")
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
                                                   f"{type(exc).__name__}: "
                                                   f"{exc}"},
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
    except (OSError, ValueError, KeyError, TypeError,
            json.JSONDecodeError) as exc:
        _finalize_orphan(cfg, "error", exc)
        print(f"STOP  fail-closed on {type(exc).__name__}: {exc}")
        return EXIT_GATE


def make_cfg(opts: dict) -> dict:
    return {"execute": opts["execute"], "run_id": opts["run_id"],
            "receipt": Path(opts["receipt"]) if opts["receipt"] else None,
            "root": HERE, "v1_root": V1_ROOT,
            "data_path": ROOT / "data" / "countries.json",
            "lock_path": DEFAULT_LOCK_PATH,
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