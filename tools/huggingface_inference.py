#!/usr/bin/env python3
"""Hugging Face Inference Providers adapter for FRANK/RAE.

Uses the current OpenAI-compatible Hugging Face router. The canonical credential is
HF_TOKEN. The adapter supports model discovery and chat-completion calls while keeping
credential values out of output/logs.

Model/provider results are external model-runtime evidence, not scientific verification
by themselves.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rae_secret_loader import get_secret, secret_source  # noqa: E402

BASE = "https://router.huggingface.co/v1"
DEFAULT_TIMEOUT = 60
MAX_RETRIES = 4


def _headers() -> dict[str, str]:
    token = get_secret("HF_TOKEN")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "FRANK-RAE/8.8 Hugging Face Inference Providers adapter",
    }


def _request(path: str, *, method: str = "GET", body: dict | None = None, timeout: int = DEFAULT_TIMEOUT):
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(BASE + path, data=payload, headers=_headers(), method=method)
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == MAX_RETRIES - 1:
                detail = exc.read().decode("utf-8", errors="replace")[:600]
                raise RuntimeError(f"Hugging Face HTTP {exc.code}: {detail}") from exc
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else min(2 ** attempt, 8)
            time.sleep(delay)
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f"Hugging Face request failed: {last_error}")


def list_models(limit: int = 20) -> dict:
    data = _request("/models")
    items = data.get("data") if isinstance(data, dict) else []
    compact = []
    for item in (items or [])[:max(1, min(limit, 100))]:
        compact.append({
            "id": item.get("id"),
            "object": item.get("object"),
            "created": item.get("created"),
            "owned_by": item.get("owned_by"),
        })
    return {
        "provider": "Hugging Face Inference Providers",
        "tool": "huggingface_inference",
        "evidence_class": "external_model_runtime",
        "models": compact,
    }


def chat(model: str, prompt: str, *, max_tokens: int = 128, temperature: float = 0.0) -> dict:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    data = _request("/chat/completions", method="POST", body=body, timeout=120)
    choice = ((data.get("choices") or [{}])[0] or {}) if isinstance(data, dict) else {}
    message = choice.get("message") or {}
    return {
        "provider": "Hugging Face Inference Providers",
        "tool": "huggingface_inference",
        "evidence_class": "external_model_runtime",
        "model_requested": model,
        "model_returned": data.get("model") if isinstance(data, dict) else None,
        "content": message.get("content"),
        "finish_reason": choice.get("finish_reason"),
        "usage": data.get("usage") if isinstance(data, dict) else None,
        "id": data.get("id") if isinstance(data, dict) else None,
    }


def smoke_test() -> dict:
    # Model listing verifies router reachability and token authorization without spending
    # an inference request/credit.
    data = list_models(limit=1)
    if not data.get("models"):
        raise RuntimeError("Hugging Face smoke test returned no available models")
    return {
        "schema_version": "1.0",
        "provider": "Hugging Face Inference Providers",
        "tool": "huggingface_inference",
        "status": "RUNTIME_VERIFIED",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "credential_source": secret_source("HF_TOKEN"),
        "credential_value_persisted_here": False,
        "verification_endpoint_class": "v1/models",
        "inference_credit_spent": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Hugging Face Inference Providers adapter")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--list-models", action="store_true")
    group.add_argument("--chat", help="prompt for a chat completion")
    group.add_argument("--smoke-test", action="store_true")
    ap.add_argument("--model", default="openai/gpt-oss-120b:cheapest")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--max-tokens", type=int, default=128)
    ap.add_argument("--temperature", type=float, default=0.0)
    args = ap.parse_args()

    if args.smoke_test:
        out = smoke_test()
    elif args.list_models:
        out = list_models(args.limit)
    else:
        out = chat(args.model, args.chat, max_tokens=args.max_tokens, temperature=args.temperature)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
