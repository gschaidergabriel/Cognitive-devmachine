#!/usr/bin/env python3
"""FREE_ONLY pooled Mistral worker adapter for Clay/FRANK research/build work.

Architecture:
- ChatGPT is the sole FRANK cascade orchestrator/adjudicator.
- Mistral is a subordinate builder/research worker.
- configured MISTRAL_API_KEY* secrets form a credential pool;
- secret values are loaded only at the provider boundary and never returned/persisted;
- HTTP 402 is a hard FREE_ONLY stop; no auto-purchase/top-up;
- HTTP 429 marks that credential attempt limited and allows another configured key attempt,
  without claiming keys have independent workspace quota;
- only final worker output/usage metadata are persisted, never hidden reasoning traces.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rae_secret_loader import get_secret, secret_source

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "research_entity/runtime/tool_results"
POOL_STATE = ROOT / "research_entity/runtime/MISTRAL_KEY_POOL_STATE.json"
BASE = os.environ.get("MISTRAL_API_BASE", "https://api.mistral.ai/v1").rstrip("/")
DEFAULT_MODEL = os.environ.get("MISTRAL_BUILD_MODEL", "mistral-small-latest")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")


class FreeOnlyViolation(RuntimeError):
    pass


class RateLimited(RuntimeError):
    pass


class KeyPoolUnavailable(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fp(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()[:12]


def _load_pool() -> dict[str, Any]:
    try:
        obj = json.loads(POOL_STATE.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {"schema_version": "1.0", "keys": {}}
    except (FileNotFoundError, json.JSONDecodeError):
        return {"schema_version": "1.0", "keys": {}}


def _save_pool(obj: dict[str, Any]) -> None:
    obj["schema_version"] = "1.0"
    obj["updated_at"] = _now()
    POOL_STATE.parent.mkdir(parents=True, exist_ok=True)
    POOL_STATE.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _secret_names() -> list[str]:
    names: list[str] = []
    for raw in os.environ.get("MISTRAL_KEY_POOL", "").split(","):
        name = raw.strip()
        if name and name not in names:
            names.append(name)
    for name in ["MISTRAL_API_KEY"] + [f"MISTRAL_API_KEY_{i}" for i in range(1, 33)]:
        if name not in names:
            names.append(name)
    return names


def _configured() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for name in _secret_names():
        try:
            value = get_secret(name, required=False)
        except Exception:
            value = None
        if value:
            rows.append((name, value, _fp(value)))
    return rows


def key_pool_status() -> dict[str, Any]:
    state = _load_pool().get("keys") or {}
    rows = []
    for name, _value, fp in _configured():
        meta = state.get(fp, {})
        rows.append({
            "key_fingerprint": fp,
            "credential_source": secret_source(name),
            "lease_state": meta.get("lease_state", "FREE"),
            "provider_state": meta.get("provider_state", "UNKNOWN"),
            "last_used_at": meta.get("last_used_at"),
            "last_http_status": meta.get("last_http_status"),
        })
    return {
        "configured_count": len(rows),
        "keys": rows,
        "credential_values_exposed": False,
        "independent_quota_assumed": False,
        "free_only": True,
    }


def _record(fp: str, **fields: Any) -> None:
    obj = _load_pool()
    meta = obj.setdefault("keys", {}).setdefault(fp, {})
    meta.update(fields)
    _save_pool(obj)


def _ordered_keys() -> list[tuple[str, str, str]]:
    rows = _configured()
    if not rows:
        raise KeyPoolUnavailable("No configured MISTRAL_API_KEY* credential found")
    state = _load_pool().get("keys") or {}

    def rank(row: tuple[str, str, str]):
        _name, _value, fp = row
        meta = state.get(fp, {})
        hard = str(meta.get("provider_state")) in {"AUTH_FAILED", "FREE_ONLY_402"}
        leased = str(meta.get("lease_state", "FREE")) == "IN_USE"
        last = str(meta.get("last_used_at") or "")
        return (1 if hard else 0, 1 if leased else 0, last)

    return sorted(rows, key=rank)


def _http(path: str, key: str, body: dict[str, Any] | None = None, timeout: int = 120) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Clay/0.1 FREE_ONLY Mistral worker",
        },
        method="GET" if body is None else "POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return int(resp.status), json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")[:2000]
        if exc.code == 402:
            raise FreeOnlyViolation(f"Mistral FREE_ONLY rejected paid usage: HTTP 402: {text}") from exc
        if exc.code == 429:
            raise RateLimited(f"Mistral rate limited: HTTP 429: {text}") from exc
        if exc.code in {401, 403}:
            raise PermissionError(f"Mistral auth rejected: HTTP {exc.code}: {text}") from exc
        raise RuntimeError(f"Mistral HTTP {exc.code}: {text}") from exc


def _request(path: str, body: dict[str, Any] | None = None, timeout: int = 120) -> tuple[Any, str]:
    failures: list[str] = []
    for name, key, fp in _ordered_keys():
        prior = (_load_pool().get("keys") or {}).get(fp, {})
        if str(prior.get("provider_state")) in {"AUTH_FAILED", "FREE_ONLY_402"}:
            continue
        if str(prior.get("lease_state", "FREE")) == "IN_USE":
            continue
        _record(fp, secret_name=name, lease_state="IN_USE", last_used_at=_now())
        try:
            status, payload = _http(path, key, body, timeout)
            _record(fp, lease_state="FREE", provider_state="AVAILABLE", last_http_status=status, last_success_at=_now())
            return payload, fp
        except FreeOnlyViolation as exc:
            _record(fp, lease_state="FREE", provider_state="FREE_ONLY_402", last_http_status=402, last_failure_at=_now())
            failures.append(f"{fp}:FREE_ONLY_402")
        except RateLimited as exc:
            _record(fp, lease_state="FREE", provider_state="RATE_LIMITED_429", last_http_status=429, last_failure_at=_now())
            failures.append(f"{fp}:RATE_LIMITED_429")
        except PermissionError:
            _record(fp, lease_state="FREE", provider_state="AUTH_FAILED", last_failure_at=_now())
            failures.append(f"{fp}:AUTH_FAILED")
        except Exception as exc:
            _record(fp, lease_state="FREE", provider_state="ERROR", last_failure_at=_now(), last_error_type=type(exc).__name__)
            failures.append(f"{fp}:{type(exc).__name__}")
    raise KeyPoolUnavailable("No usable configured Mistral key; attempts=" + ",".join(failures))


def list_models() -> list[dict[str, Any]]:
    raw, _fp_used = _request("/models")
    return list(raw.get("data", raw if isinstance(raw, list) else []))


def _answer_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    out = []
    if isinstance(content, list):
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                out.append(str(c.get("text") or ""))
    return "".join(out)


def chat(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    system: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.1,
    reasoning_effort: str = "high",
    n: int = 1,
    json_mode: bool = False,
    prompt_cache_key: str | None = "frank-build-current-v1",
    timeout: int = 180,
) -> dict[str, Any]:
    if not prompt.strip():
        raise ValueError("prompt required")
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    body: dict[str, Any] = {
        "model": model,
        "messages": msgs,
        "max_tokens": max(1, min(int(max_tokens), 8192)),
        "temperature": max(0.0, min(float(temperature), 1.0)),
        "reasoning_effort": reasoning_effort,
        "n": max(1, min(int(n), 4)),
    }
    if prompt_cache_key:
        body["prompt_cache_key"] = prompt_cache_key
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    started = time.time()
    raw, fp_used = _request("/chat/completions", body, timeout=timeout)
    choices = raw.get("choices") or []
    return {
        "provider": "Mistral",
        "model": raw.get("model") or model,
        "worker_role": "SUBORDINATE_BUILD_RESEARCH_WORKER",
        "evidence_label": "WORKER_PROPOSAL",
        "key_fingerprint": fp_used,
        "answers": [
            {
                "content": _answer_text((c.get("message") or {}).get("content")),
                "finish_reason": c.get("finish_reason"),
            }
            for c in choices
        ],
        "usage": raw.get("usage") or {},
        "latency_ms": round((time.time() - started) * 1000, 1),
        "reasoning_trace_persisted": False,
        "free_only": True,
    }


def fim(prefix: str, *, suffix: str = "", model: str = "codestral-latest", max_tokens: int = 2048, prompt_cache_key: str | None = "frank-build-fim-v1") -> dict[str, Any]:
    if not prefix:
        raise ValueError("prefix required")
    body: dict[str, Any] = {"model": model, "prompt": prefix, "suffix": suffix, "max_tokens": max(1, min(int(max_tokens), 8192))}
    if prompt_cache_key:
        body["prompt_cache_key"] = prompt_cache_key
    raw, fp_used = _request("/fim/completions", body)
    choice = (raw.get("choices") or [{}])[0]
    return {
        "provider": "Mistral",
        "model": model,
        "worker_role": "SUBORDINATE_BUILD_RESEARCH_WORKER",
        "evidence_label": "WORKER_PROPOSAL",
        "key_fingerprint": fp_used,
        "capability": "fim",
        "content": choice.get("text") or ((choice.get("message") or {}).get("content") or ""),
        "finish_reason": choice.get("finish_reason"),
        "usage": raw.get("usage") or {},
        "free_only": True,
    }


def embeddings(inputs: list[str] | str, *, model: str = "mistral-embed") -> dict[str, Any]:
    vals = [inputs] if isinstance(inputs, str) else list(inputs)
    raw, fp_used = _request("/embeddings", {"model": model, "input": vals, "encoding_format": "float"})
    return {
        "provider": "Mistral",
        "model": model,
        "key_fingerprint": fp_used,
        "capability": "embeddings",
        "data": raw.get("data") or [],
        "usage": raw.get("usage") or {},
        "free_only": True,
    }


def capabilities() -> dict[str, Any]:
    models = list_models()
    return {
        "provider": "Mistral",
        "free_only": True,
        "key_pool": key_pool_status(),
        "models": [
            {
                "id": m.get("id"),
                "capabilities": m.get("capabilities") or {},
                "max_context_length": m.get("max_context_length"),
            }
            for m in models
        ],
        "implemented_adapter_modes": ["models", "chat_reasoning", "structured_json", "multi_completion", "prompt_cache", "fim", "embeddings", "pooled_keys"],
        "orchestration_authority": "CHATGPT_ONLY",
    }


def process_request(path: Path) -> dict[str, Any]:
    req = json.loads(path.read_text(encoding="utf-8"))
    rid = str(req.get("request_id") or path.stem)
    if not ID_RE.fullmatch(rid):
        raise ValueError("invalid request_id")
    mode = str(req.get("mode") or "models")
    env: dict[str, Any] = {
        "schema_version": "1.1",
        "request_id": rid,
        "tool": "mistral_inference",
        "request_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "processed_at": _now(),
        "free_only": True,
        "orchestrator": "chatgpt-secondary",
    }
    try:
        if mode == "models":
            env["result"] = capabilities()
        elif mode == "status":
            env["result"] = key_pool_status()
        elif mode == "chat":
            env["result"] = chat(
                str(req.get("prompt") or ""),
                model=str(req.get("model") or DEFAULT_MODEL),
                system=str(req.get("system")) if req.get("system") else None,
                max_tokens=int(req.get("max_tokens") or 4096),
                temperature=float(req.get("temperature") or 0.05),
                reasoning_effort=str(req.get("reasoning_effort") or "high"),
                n=int(req.get("n") or 1),
                json_mode=bool(req.get("json_mode", False)),
                prompt_cache_key=str(req.get("prompt_cache_key") or "frank-build-current-v1"),
                timeout=int(req.get("timeout") or 180),
            )
        elif mode == "fim":
            env["result"] = fim(
                str(req.get("prefix") or ""),
                suffix=str(req.get("suffix") or ""),
                model=str(req.get("model") or "codestral-latest"),
                max_tokens=int(req.get("max_tokens") or 2048),
            )
        elif mode == "embeddings":
            env["result"] = embeddings(req.get("input") or [], model=str(req.get("model") or "mistral-embed"))
        else:
            raise ValueError(f"unsupported mode: {mode}")
        env["status"] = "SUCCESS"
    except Exception as exc:
        env["status"] = "FAILED"
        env["error_type"] = type(exc).__name__
        env["error"] = str(exc)[:2000]
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{rid}.json"
    out.write_text(json.dumps(env, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"request_id": rid, "status": env["status"], "result_path": str(out.relative_to(ROOT))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request")
    ap.add_argument("--capabilities", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    if args.request:
        print(json.dumps(process_request(Path(args.request)), ensure_ascii=False, indent=2))
    elif args.status:
        print(json.dumps(key_pool_status(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(capabilities(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
