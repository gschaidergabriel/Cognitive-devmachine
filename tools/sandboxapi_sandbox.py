#!/usr/bin/env python3
"""SandboxAPI remote execution adapter for FRANK/RAE.

Uses RAPIDAPI_KEY only at runtime and never prints it. The primary transport is
the RapidAPI REST gateway documented by SandboxAPI. The adapter discovers the
RapidAPI host from the listing page when possible and probes a small bounded set
of provider-name candidates as fallback. Executed code runs at the remote
SandboxAPI service, not on the GitHub runner.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rae_secret_loader import get_secret, secret_source  # noqa: E402

RAPIDAPI_LISTING = "https://rapidapi.com/sandboxapidev/api/sandboxapi"
HOST_CANDIDATES = [
    "sandboxapi.p.rapidapi.com",
    "sandbox-api.p.rapidapi.com",
    "sandboxapi1.p.rapidapi.com",
]
ALLOWED_LANGUAGES = {"python3", "javascript", "typescript", "bash", "java", "cpp", "c", "go"}


def _http(req: urllib.request.Request, *, timeout: int = 45) -> tuple[int, str, dict[str, str]]:
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace"), dict(resp.headers.items())
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace"), dict(exc.headers.items()) if exc.headers else {}


def _listing_hosts() -> list[str]:
    req = urllib.request.Request(
        RAPIDAPI_LISTING,
        headers={"Accept": "text/html,application/xhtml+xml", "User-Agent": "FRANK-RAE/8.8 sandbox capability discovery"},
    )
    status, text, _ = _http(req, timeout=20)
    if status >= 400:
        return []
    normalized = text.replace("\\u002e", ".").replace("\\u002E", ".").replace("\\/", "/")
    found = re.findall(r"([A-Za-z0-9][A-Za-z0-9.-]*\.p\.rapidapi\.com)", normalized)
    out: list[str] = []
    for host in found:
        if host not in out:
            out.append(host)
    return out


def _headers(host: str) -> dict[str, str]:
    return {
        "x-rapidapi-key": get_secret("RAPIDAPI_KEY"),
        "x-rapidapi-host": host,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "FRANK-RAE/8.8 sandbox research runtime",
    }


def discover_host() -> tuple[str, list[dict[str, Any]]]:
    candidates = _listing_hosts() + [h for h in HOST_CANDIDATES if h not in _listing_hosts()]
    attempts: list[dict[str, Any]] = []
    for host in candidates[:8]:
        req = urllib.request.Request(f"https://{host}/v1/languages", headers=_headers(host), method="GET")
        status, text, _ = _http(req, timeout=20)
        attempts.append({"host": host, "status": status, "body_prefix": text[:240]})
        if status == 200:
            return host, attempts
        lower = text.lower()
        if status in {401, 403} and ("not subscribed" in lower or "invalid api key" in lower or "forbidden" in lower):
            # This is enough to establish that the RapidAPI gateway host resolved;
            # preserve the precise account/subscription failure instead of hiding it.
            raise RuntimeError(f"RapidAPI gateway reached at {host} but authorization/subscription failed: HTTP {status}: {text[:500]}")
    raise RuntimeError(f"Could not resolve a working SandboxAPI RapidAPI host; attempts={attempts}")


def execute_code(code: str, *, language: str = "python3", timeout: int = 10, stdin: str = "") -> dict[str, Any]:
    if language not in ALLOWED_LANGUAGES:
        raise ValueError(f"unsupported language: {language}")
    if not code or len(code.encode("utf-8")) > 1_000_000:
        raise ValueError("code must be 1..1000000 UTF-8 bytes")
    timeout = max(1, min(int(timeout), 300))
    host, discovery = discover_host()
    payload: dict[str, Any] = {"language": language, "code": code, "timeout": timeout}
    if stdin:
        payload["stdin"] = stdin
    req = urllib.request.Request(
        f"https://{host}/v1/execute",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=_headers(host),
        method="POST",
    )
    status, text, headers = _http(req, timeout=max(30, timeout + 15))
    if status != 200:
        raise RuntimeError(f"SandboxAPI RapidAPI execute HTTP {status}: {text[:1000]}")
    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"SandboxAPI returned non-JSON success body: {text[:800]}") from exc
    return {
        "provider": "SandboxAPI via RapidAPI",
        "tool": "sandboxapi_sandbox",
        "evidence_class": "isolated_runtime_experiment",
        "language": language,
        "rapidapi_host": host,
        "host_discovery_attempts": discovery,
        "rate_limit_remaining": headers.get("X-RateLimit-requests-Remaining") or headers.get("x-ratelimit-requests-remaining"),
        "result": result,
    }


def smoke_test() -> dict[str, Any]:
    out = execute_code("print('RAE_SANDBOXAPI_OK:' + str(6*7))", language="python3", timeout=10)
    result = out.get("result") or {}
    stdout = str(result.get("stdout") or "")
    if int(result.get("exit_code", -1)) != 0 or "RAE_SANDBOXAPI_OK:42" not in stdout:
        raise RuntimeError(f"SandboxAPI smoke sentinel mismatch: {result}")
    return {
        "schema_version": "1.0",
        "provider": "SandboxAPI via RapidAPI",
        "tool": "sandboxapi_sandbox",
        "status": "RUNTIME_VERIFIED",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "credential_source": secret_source("RAPIDAPI_KEY"),
        "credential_value_exposed": False,
        "verification_class": "remote_gvisor_code_execution",
        "rapidapi_host": out.get("rapidapi_host"),
        "sentinel": "RAE_SANDBOXAPI_OK:42",
        "execution": {
            "language": result.get("language"),
            "status": result.get("status"),
            "exit_code": result.get("exit_code"),
            "execution_time_ms": result.get("execution_time_ms"),
            "memory_used_kb": result.get("memory_used_kb"),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Execute code through SandboxAPI via RapidAPI")
    ap.add_argument("--smoke-test", action="store_true")
    ap.add_argument("--language", default="python3", choices=sorted(ALLOWED_LANGUAGES))
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--stdin", default="")
    ap.add_argument("code", nargs="?")
    args = ap.parse_args()
    if args.smoke_test:
        out = smoke_test()
    else:
        if args.code is None:
            ap.error("code required unless --smoke-test is used")
        out = execute_code(args.code, language=args.language, timeout=args.timeout, stdin=args.stdin)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
