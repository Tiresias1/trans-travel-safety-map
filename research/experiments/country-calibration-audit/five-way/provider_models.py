#!/usr/bin/env python3
"""Six-model provider adapters for the five-way harness (execute only).

Each function has the harness caller contract:
call_X(system_text, user_text) -> {"raw_response": str,
"usage": {"cost_usd": str, "input_tokens": int, "output_tokens": int}}.

Generation settings are uniform across the panel: max_tokens 8000, reasoning
effort "low". One HTTP attempt per call (the harness never retries). The
credential is read from /tmp/.openrouter_key into process memory only.
"""
from __future__ import annotations

import json
import urllib.request
from decimal import Decimal
from pathlib import Path

URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_TOKENS = 8000
TIMEOUT_S = 300
KEY_FILE = Path("/tmp/.openrouter_key")


def _call(model: str, system_text: str, user_text: str,
          max_tokens: int = MAX_TOKENS) -> dict:
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    if not key:
        raise RuntimeError("empty provider credential")
    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "reasoning": {"effort": "low"},
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
        raw = resp.read().decode("utf-8", "replace")
    doc = json.loads(raw)
    usage = doc.get("usage") or {}
    out = {"raw_response": raw, "usage": {}}
    if isinstance(usage.get("cost"), (int, float)):
        out["usage"]["cost_usd"] = format(Decimal(str(usage["cost"])), "f")
    for src, dst in (("prompt_tokens", "input_tokens"),
                     ("completion_tokens", "output_tokens")):
        v = usage.get(src)
        if isinstance(v, int):
            out["usage"][dst] = v
    return out


def call_mimo(system_text: str, user_text: str) -> dict:
    return _call("xiaomi/mimo-v2.6-flash", system_text, user_text)


def call_deepseek(system_text: str, user_text: str) -> dict:
    return _call("deepseek/deepseek-v4.1-flash-1017", system_text, user_text)


def call_qwen(system_text: str, user_text: str) -> dict:
    # 16000: qwen's reasoning exhausts 8000 on these prompts with empty
    # content (documented amendment 2026-11-09); other models stay at 8000.
    return _call("qwen/qwen3.8-flash", system_text, user_text, max_tokens=16000)


def call_glm(system_text: str, user_text: str) -> dict:
    return _call("z-ai/glm-5.3-flash", system_text, user_text)


def call_haiku(system_text: str, user_text: str) -> dict:
    return _call("anthropic/claude-haiku-5.5", system_text, user_text)


def call_luna(system_text: str, user_text: str) -> dict:
    return _call("openai/gpt-6-luna", system_text, user_text)


def call_mimo_medium(system_text: str, user_text: str) -> dict:
    """MiMo V2.6 Flash at thinking effort medium (phase-2 anchored raters)."""
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    body = json.dumps({
        "model": "xiaomi/mimo-v2.6-flash",
        "max_tokens": MAX_TOKENS,
        "reasoning": {"effort": "medium"},
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
        raw = resp.read().decode("utf-8", "replace")
    doc = json.loads(raw)
    usage = doc.get("usage") or {}
    out = {"raw_response": raw, "usage": {}}
    if isinstance(usage.get("cost"), (int, float)):
        out["usage"]["cost_usd"] = format(Decimal(str(usage["cost"])), "f")
    for src, dst in (("prompt_tokens", "input_tokens"),
                     ("completion_tokens", "output_tokens")):
        v = usage.get(src)
        if isinstance(v, int):
            out["usage"][dst] = v
    return out
