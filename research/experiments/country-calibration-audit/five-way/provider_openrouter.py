#!/usr/bin/env python3
"""OpenRouter adapter for the five-way harness (execute path only).

Contract: call_model(system_text, user_text) -> {"raw_response": str,
"usage": {"cost_usd": str, "input_tokens": int, "output_tokens": int}}.

One HTTP attempt per call (the harness never retries). The credential is read
from /tmp/.openrouter_key into process memory only — never logged, never placed
in argv, never written anywhere. No cache directives, no fallback routing.
"""
from __future__ import annotations

import json
import urllib.request
from decimal import Decimal
from pathlib import Path

URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-v4.1-flash"   # production rater model
MAX_TOKENS = 11000                        # v2's reviewed output allowance
TIMEOUT_S = 300
KEY_FILE = Path("/tmp/.openrouter_key")


def _exact(value) -> str:
    return format(Decimal(str(value)), "f")


def call_model(system_text: str, user_text: str) -> dict:
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    if not key:
        raise RuntimeError("empty provider credential")
    body = json.dumps({
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ],
    }).encode("utf-8")
    req = urllib.request.Request(URL, data=body, method="POST", headers={
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
    })
    del key
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        raw_bytes = resp.read()
    raw = raw_bytes.decode("utf-8", "replace")
    doc = json.loads(raw)
    usage = doc.get("usage") or {}
    out = {
        "raw_response": raw,
        "usage": {
            # cost_usd deliberately omitted when the provider reports no cost:
            # classify_usage then raises UnknownCharge and the run stops.
        },
    }
    if isinstance(usage.get("cost"), (int, float)):
        out["usage"]["cost_usd"] = _exact(usage["cost"])
    for src, dst in (("prompt_tokens", "input_tokens"),
                     ("completion_tokens", "output_tokens")):
        v = usage.get(src)
        if isinstance(v, int):
            out["usage"][dst] = v
    return out
