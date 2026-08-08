#!/usr/bin/env python3
"""Groq model adapter for FRANK/RAE small-model experiments.

The current default is Groq's Llama 3.1 8B Instant. It is used as an
`8b_proxy_for_4b` when an experiment calls for a bare/small ~4B reader but no verified
4B provider is operational. Never relabel its results as actual 4B evidence.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from rae_secret_loader import get_secret

BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.1-8b-instant"
EVIDENCE_ROLE = "8b_proxy_for_4b"


def _request(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    key = get_secret("GROQ_API_KEY")
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="GET" if payload is None else "POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"Groq HTTP {exc.code}: {body}") from exc


def list_models() -> list[dict[str, Any]]:
    data = _request("/models")
    return data.get("data", []) if isinstance(data, dict) else []


def model_available(model: str = DEFAULT_MODEL) -> bool:
    return any(x.get("id") == model for x in list_models())


def chat(prompt: str, *, model: str = DEFAULT_MODEL, max_tokens: int = 256, temperature: float = 0.0, system: str | None = None) -> dict[str, Any]:
    if not prompt.strip():
        raise ValueError("prompt required")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max(1, min(int(max_tokens), 4096)),
        "temperature": max(0.0, min(float(temperature), 2.0)),
    }
    raw = _request("/chat/completions", payload)
    choice = (raw.get("choices") or [{}])[0]
    usage = raw.get("usage") or {}
    return {
        "provider": "Groq",
        "model": model,
        "evidence_role": EVIDENCE_ROLE if model == DEFAULT_MODEL else "external_model_runtime",
        "content": ((choice.get("message") or {}).get("content") or ""),
        "finish_reason": choice.get("finish_reason"),
        "usage": usage,
    }


def smoke_test() -> dict[str, Any]:
    models = list_models()
    ids = [x.get("id") for x in models if x.get("id")]
    if DEFAULT_MODEL not in ids:
        raise RuntimeError(f"Groq account does not currently expose required proxy model {DEFAULT_MODEL}")
    out = chat("Reply with exactly: GROQ_8B_OK", max_tokens=12, temperature=0.0)
    if "GROQ_8B_OK" not in out.get("content", ""):
        raise RuntimeError("Groq 8B sentinel mismatch")
    return {
        "status": "RUNTIME_VERIFIED",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "provider": "Groq",
        "model": DEFAULT_MODEL,
        "parameter_class": "8B",
        "test_role": EVIDENCE_ROLE,
        "credential_value_exposed": False,
        "inference_call_succeeded": True,
    }


if __name__ == "__main__":
    print(json.dumps(smoke_test(), ensure_ascii=False, indent=2))
