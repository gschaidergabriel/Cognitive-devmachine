#!/usr/bin/env python3
"""OpenRouter model adapter for FRANK/RAE target small-model experiments.

Preferred target is Qwen3-4B when exposed by the credential-specific catalog. If it is
not exposed, other explicit 4B routes may be used for parameter-class experiments but
must never be relabeled as Qwen evidence. Credential values are never printed/stored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rae_secret_loader import get_secret, secret_source

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research_entity" / "runtime" / "tool_results"
BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "qwen/qwen3-4b"
QWEN_FREE_MODEL = "qwen/qwen3-4b:free"
GEMMA_4B_MODEL = "google/gemma-3-4b-it"
USER_AGENT = "FRANK-RAE/8.8 research-runtime (+https://github.com/gschaidergabriel/clay-global-research-entity)"
MAX_RATE_RETRIES = 8
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")

MODEL_META = {
    DEFAULT_MODEL: {"class": "4B", "role": "direct_qwen3_4b_external_runtime", "identity": "Qwen3-4B"},
    QWEN_FREE_MODEL: {"class": "4B", "role": "direct_qwen3_4b_external_runtime", "identity": "Qwen3-4B"},
    GEMMA_4B_MODEL: {"class": "4B", "role": "direct_4b_external_runtime", "identity": "Gemma-3-4B-IT"},
}


def _retry_seconds(exc: urllib.error.HTTPError, body: str, attempt: int) -> float:
    header = exc.headers.get("Retry-After") if exc.headers else None
    if header:
        try:
            return max(0.5, min(float(header) + 0.25, 45.0))
        except ValueError:
            pass
    m = re.search(r"(?:try again in|retry after)\s+([0-9.]+)\s*(ms|s)", body, flags=re.I)
    if m:
        value = float(m.group(1)) / (1000.0 if m.group(2).lower() == "ms" else 1.0)
        return max(0.5, min(value + 0.25, 45.0))
    return min(1.5 + attempt * 1.5, 20.0)


def _request(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    key = get_secret("OPENROUTER_API_KEY")
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    for attempt in range(MAX_RATE_RETRIES + 1):
        req = urllib.request.Request(
            BASE_URL + path,
            data=data,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
                "HTTP-Referer": "https://github.com/gschaidergabriel/clay-global-research-entity",
                "X-Title": "FRANK RAE research runtime",
            },
            method="GET" if payload is None else "POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:3000]
            if exc.code == 429 and attempt < MAX_RATE_RETRIES:
                time.sleep(_retry_seconds(exc, body, attempt))
                continue
            raise RuntimeError(f"OpenRouter HTTP {exc.code}: {body[:1200]}") from exc
    raise RuntimeError("OpenRouter request retry loop exhausted")


def list_models() -> list[dict[str, Any]]:
    data = _request("/models")
    return data.get("data", []) if isinstance(data, dict) else []


def model_available(model: str = DEFAULT_MODEL) -> bool:
    return any(x.get("id") == model for x in list_models())


def chat(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 512,
    temperature: float = 0.0,
    system: str | None = None,
    requested_target_class: str | None = None,
) -> dict[str, Any]:
    if not prompt.strip():
        raise ValueError("prompt required")
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max(1, min(int(max_tokens), 8192)),
        "temperature": max(0.0, min(float(temperature), 2.0)),
    }
    raw = _request("/chat/completions", payload)
    choice = (raw.get("choices") or [{}])[0]
    usage = raw.get("usage") or {}
    message = choice.get("message") or {}
    meta = MODEL_META.get(model, {"class": "external_model", "role": "external_model_runtime", "identity": model})
    return {
        "provider": "OpenRouter",
        "model": model,
        "model_identity": meta["identity"],
        "requested_target_class": requested_target_class or meta["identity"],
        "executed_model_class": meta["class"],
        "evidence_role": meta["role"],
        "content": message.get("content") or "",
        "reasoning": message.get("reasoning"),
        "finish_reason": choice.get("finish_reason"),
        "usage": usage,
        "provider_route": raw.get("provider"),
    }


def smoke_test(model: str = DEFAULT_MODEL) -> dict[str, Any]:
    if not model_available(model):
        raise RuntimeError(f"OpenRouter account/catalog does not expose required model {model}")
    meta = MODEL_META.get(model, {"class": "external_model", "role": "external_model_runtime", "identity": model})
    sentinel = "OPENROUTER_MODEL_OK"
    out = chat(f"Reply with exactly: {sentinel}", model=model, max_tokens=32, temperature=0.0)
    if sentinel not in out.get("content", ""):
        raise RuntimeError(f"OpenRouter sentinel mismatch for {model}")
    return {
        "status": "RUNTIME_VERIFIED",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "provider": "OpenRouter",
        "model": model,
        "model_identity": meta["identity"],
        "parameter_class": meta["class"],
        "evidence_role": meta["role"],
        "credential_source": secret_source("OPENROUTER_API_KEY"),
        "credential_value_exposed": False,
        "inference_call_succeeded": True,
    }


def process_request(path: Path) -> dict[str, Any]:
    req = json.loads(path.read_text(encoding="utf-8"))
    rid = str(req.get("request_id") or path.stem)
    if not ID_RE.fullmatch(rid):
        raise ValueError("invalid request_id")
    mode = str(req.get("mode") or "chat")
    model = str(req.get("model") or DEFAULT_MODEL)
    envelope: dict[str, Any] = {
        "schema_version": "1.0",
        "request_id": rid,
        "tool": "openrouter_inference",
        "request_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        if mode == "smoke_test":
            envelope["result"] = smoke_test(model)
        elif mode == "list_models":
            envelope["result"] = {"provider": "OpenRouter", "models": [x.get("id") for x in list_models() if x.get("id")]}
        elif mode == "chat":
            envelope["result"] = chat(
                str(req.get("prompt") or ""),
                model=model,
                max_tokens=int(req.get("max_tokens") or 512),
                temperature=float(req.get("temperature") or 0.0),
                system=str(req.get("system")) if req.get("system") else None,
                requested_target_class=str(req.get("requested_target_class")) if req.get("requested_target_class") else None,
            )
        else:
            raise ValueError(f"unsupported mode: {mode}")
        envelope["status"] = "SUCCESS"
    except Exception as exc:
        envelope["status"] = "FAILED"
        envelope["error_type"] = type(exc).__name__
        envelope["error"] = str(exc)[:2000]
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{rid}.json"
    out.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"request_id": rid, "status": envelope["status"], "result_path": str(out.relative_to(ROOT))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke-test", action="store_true")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--request")
    args = ap.parse_args()
    if args.request:
        print(json.dumps(process_request(Path(args.request)), ensure_ascii=False, indent=2))
    elif args.smoke_test:
        print(json.dumps(smoke_test(args.model), ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"models": [x.get("id") for x in list_models() if x.get("id")]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
