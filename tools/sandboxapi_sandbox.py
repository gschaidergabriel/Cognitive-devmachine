#!/usr/bin/env python3
"""SandboxAPI remote execution adapter for FRANK/RAE.

Uses RAPIDAPI_KEY only at runtime and never prints it. Current SandboxAPI documentation
uses the direct api.sandboxapi.dev REST endpoint with X-RapidAPI-Key; older deployments
and the RapidAPI listing expose a gateway host. The adapter probes the current direct
endpoint first and then falls back to a bounded RapidAPI-host discovery path.
Executed code runs at the remote SandboxAPI service, not on the GitHub runner.
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

DIRECT_BASE = "https://api.sandboxapi.dev"
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


def _direct_headers() -> dict[str, str]:
    return {
        "X-RapidAPI-Key": get_secret("RAPIDAPI_KEY"),
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "FRANK-RAE/8.8 sandbox research runtime",
    }


def _gateway_headers(host: str) -> dict[str, str]:
    return {
        "x-rapidapi-key": get_secret("RAPIDAPI_KEY"),
        "x-rapidapi-host": host,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "FRANK-RAE/8.8 sandbox research runtime",
    }


def discover_endpoint() -> tuple[str, str | None, list[dict[str, Any]]]:
    """Return (base_url, rapidapi_gateway_host_or_none, attempts)."""
    attempts: list[dict[str, Any]] = []

    # Current official docs use api.sandboxapi.dev directly with X-RapidAPI-Key.
    direct_req = urllib.request.Request(f"{DIRECT_BASE}/v1/languages", headers=_direct_headers(), method="GET")
    status, text, _ = _http(direct_req, timeout=20)
    attempts.append({"transport": "DIRECT", "base": DIRECT_BASE, "status": status, "body_prefix": text[:240]})
    if status == 200:
        return DIRECT_BASE, None, attempts

    listing_hosts = _listing_hosts()
    candidates = listing_hosts + [h for h in HOST_CANDIDATES if h not in listing_hosts]
    for host in candidates[:8]:
        req = urllib.request.Request(f"https://{host}/v1/languages", headers=_gateway_headers(host), method="GET")
        g_status, g_text, _ = _http(req, timeout=20)
        attempts.append({"transport": "RAPIDAPI_GATEWAY", "host": host, "status": g_status, "body_prefix": g_text[:240]})
        if g_status == 200:
            return f"https://{host}", host, attempts

    # Prefer the direct failure when it reached the official service and clearly classified auth.
    lower = text.lower()
    if status in {401, 403}:
        raise RuntimeError(f"SandboxAPI direct endpoint reached but authorization/subscription failed: HTTP {status}: {text[:500]}; attempts={attempts}")
    for attempt in attempts[1:]:
        body = str(attempt.get("body_prefix") or "").lower()
        g_status = int(attempt.get("status") or 0)
        if g_status in {401, 403} and ("not subscribed" in body or "invalid api key" in body or "forbidden" in body):
            raise RuntimeError(f"SandboxAPI RapidAPI gateway reached but authorization/subscription failed: attempts={attempts}")
    raise RuntimeError(f"Could not resolve a working SandboxAPI endpoint; attempts={attempts}")


def execute_code(code: str, *, language: str = "python3", timeout: int = 10, stdin: str = "") -> dict[str, Any]:
    if language not in ALLOWED_LANGUAGES:
        raise ValueError(f"unsupported language: {language}")
    if not code or len(code.encode("utf-8")) > 1_000_000:
        raise ValueError("code must be 1..1000000 UTF-8 bytes")
    timeout = max(1, min(int(timeout), 300))
    base_url, gateway_host, discovery = discover_endpoint()
    payload: dict[str, Any] = {"language": language, "code": code, "timeout": timeout}
    if stdin:
        payload["stdin"] = stdin
    headers = _direct_headers() if gateway_host is None else _gateway_headers(gateway_host)
    req = urllib.request.Request(
        f"{base_url}/v1/execute",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    status, text, response_headers = _http(req, timeout=max(30, timeout + 15))
    if status != 200:
        raise RuntimeError(f"SandboxAPI execute HTTP {status}: {text[:1000]}")
    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"SandboxAPI returned non-JSON success body: {text[:800]}") from exc
    return {
        "provider": "SandboxAPI",
        "tool": "sandboxapi_sandbox",
        "evidence_class": "isolated_runtime_experiment",
        "language": language,
        "transport": "DIRECT" if gateway_host is None else "RAPIDAPI_GATEWAY",
        "base_url": base_url,
        "rapidapi_host": gateway_host,
        "endpoint_discovery_attempts": discovery,
        "rate_limit_remaining": response_headers.get("X-RateLimit-requests-Remaining") or response_headers.get("x-ratelimit-requests-remaining"),
        "result": result,
    }


def smoke_test() -> dict[str, Any]:
    out = execute_code("print('RAE_SANDBOXAPI_OK:' + str(6*7))", language="python3", timeout=10)
    result = out.get("result") or {}
    stdout = str(result.get("stdout") or "")
    if int(result.get("exit_code", -1)) != 0 or "RAE_SANDBOXAPI_OK:42" not in stdout:
        raise RuntimeError(f"SandboxAPI smoke sentinel mismatch: {result}")
    return {
        "schema_version": "1.1",
        "provider": "SandboxAPI",
        "tool": "sandboxapi_sandbox",
        "status": "RUNTIME_VERIFIED",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "credential_source": secret_source("RAPIDAPI_KEY"),
        "credential_value_exposed": False,
        "verification_class": "remote_gvisor_code_execution",
        "transport": out.get("transport"),
        "base_url": out.get("base_url"),
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
    ap = argparse.ArgumentParser(description="Execute code through SandboxAPI")
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
