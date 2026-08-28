#!/usr/bin/env python3
"""Small, secret-safe GLM inference adapter for GRID10 research tests.

Design goals:
- no Claude Code dependency;
- default to the low-cost/free GLM-4.7-Flash model for smoke/regulator tests;
- API key only from runtime environment, never source/receipts;
- bounded output by default;
- thinking disabled by default for cheap/low-latency mechanical tests;
- sanitized receipts suitable for persistence.

Official endpoint family: https://open.bigmodel.cn/api/paas/v4
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Mapping, Sequence

API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-4.7-flash"
KEY_ENV_CANDIDATES = ("ZAI_API_KEY", "GLM_API_KEY", "BIGMODEL_API_KEY")


class GLMProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class GLMInferenceConfig:
    model: str = DEFAULT_MODEL
    max_tokens: int = 128
    temperature: float = 0.2
    thinking: bool = False
    timeout_seconds: float = 45.0

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("model required")
        if not 1 <= self.max_tokens <= 4096:
            raise ValueError("test max_tokens must be in [1,4096]")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be in [0,2]")
        if not 1.0 <= self.timeout_seconds <= 300.0:
            raise ValueError("timeout_seconds must be in [1,300]")


@dataclass(frozen=True)
class GLMInferenceReceipt:
    provider: str
    model_requested: str
    model_reported: str | None
    request_digest: str
    response_digest: str
    latency_ms: float
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    thinking_enabled: bool
    max_tokens: int
    finish_reason: str | None
    response_id: str | None
    secret_recorded: bool = False


@dataclass(frozen=True)
class GLMInferenceResult:
    content: str
    reasoning_content: str | None
    receipt: GLMInferenceReceipt


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def load_api_key(env: Mapping[str, str] | None = None) -> str:
    source = os.environ if env is None else env
    for name in KEY_ENV_CANDIDATES:
        value = source.get(name)
        if value and value.strip():
            return value.strip()
    raise GLMProviderError("GLM_API_KEY_MISSING_FROM_RUNTIME_ENVIRONMENT")


def build_payload(messages: Sequence[Mapping[str, Any]], config: GLMInferenceConfig) -> dict[str, Any]:
    if not messages:
        raise ValueError("at least one message required")
    payload: dict[str, Any] = {
        "model": config.model,
        "messages": [dict(x) for x in messages],
        "thinking": {"type": "enabled" if config.thinking else "disabled"},
        "stream": False,
        "max_tokens": config.max_tokens,
        "temperature": config.temperature,
    }
    return payload


def infer(
    messages: Sequence[Mapping[str, Any]],
    *,
    config: GLMInferenceConfig = GLMInferenceConfig(),
    api_key: str | None = None,
    opener=urllib.request.urlopen,
) -> GLMInferenceResult:
    key = api_key or load_api_key()
    payload = build_payload(messages, config)
    request_digest = _digest(payload)
    request = urllib.request.Request(
        API_URL,
        data=_canonical(payload),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        },
        method="POST",
    )
    started = time.perf_counter()
    try:
        with opener(request, timeout=config.timeout_seconds) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1000]
        raise GLMProviderError(f"GLM_HTTP_{exc.code}:{body}") from exc
    except Exception as exc:
        raise GLMProviderError(f"GLM_TRANSPORT_ERROR:{type(exc).__name__}:{exc}") from exc
    latency_ms = (time.perf_counter() - started) * 1000.0

    try:
        data = json.loads(raw.decode("utf-8"))
        choice = (data.get("choices") or [])[0]
        message = choice.get("message") or {}
        content = str(message.get("content") or "")
        reasoning = message.get("reasoning_content")
        if reasoning is not None:
            reasoning = str(reasoning)
        usage = data.get("usage") or {}
    except Exception as exc:
        raise GLMProviderError(f"GLM_RESPONSE_PARSE_ERROR:{type(exc).__name__}:{exc}") from exc

    receipt = GLMInferenceReceipt(
        provider="ZHIPU_BIGMODEL",
        model_requested=config.model,
        model_reported=data.get("model"),
        request_digest=request_digest,
        response_digest=hashlib.sha256(raw).hexdigest(),
        latency_ms=latency_ms,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        total_tokens=usage.get("total_tokens"),
        thinking_enabled=config.thinking,
        max_tokens=config.max_tokens,
        finish_reason=choice.get("finish_reason"),
        response_id=data.get("id"),
        secret_recorded=False,
    )
    return GLMInferenceResult(content=content, reasoning_content=reasoning, receipt=receipt)


def smoke_probe(*, expected: str = "GRID10_GLM_OK", max_tokens: int = 32) -> dict[str, Any]:
    result = infer(
        [{"role": "user", "content": f"Reply with exactly: {expected}"}],
        config=GLMInferenceConfig(max_tokens=max_tokens, temperature=0.1, thinking=False),
    )
    return {
        "schema": "GRID10_GLM_SMOKE_RECEIPT/v1",
        "pass": result.content.strip() == expected,
        "expected": expected,
        "content_digest": hashlib.sha256(result.content.encode("utf-8")).hexdigest(),
        "receipt": asdict(result.receipt),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--expected", default="GRID10_GLM_OK")
    parser.add_argument("--max-tokens", type=int, default=32)
    args = parser.parse_args()
    if not args.probe:
        parser.error("only --probe is supported by this bounded test CLI")
    out = smoke_probe(expected=args.expected, max_tokens=args.max_tokens)
    print(json.dumps(out, sort_keys=True))
    return 0 if out["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
