#!/usr/bin/env python3
"""SandboxAPI remote sandbox adapter for FRANK/RAE.

Uses the user-authorized RAPIDAPI_KEY only at runtime and never prints it.
The default transport is SandboxAPI's hosted MCP endpoint because the provider
explicitly documents RapidAPI-issued keys for that endpoint. Executed programs
run in isolated gVisor-backed sandboxes; execution receipts are safe to persist
only after the caller applies normal RAE redaction/sanitization.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rae_secret_loader import get_secret, secret_source  # noqa: E402

MCP_URL = "https://mcp.sandboxapi.dev/mcp"
PROTOCOL_VERSION = "2025-03-26"
ALLOWED_LANGUAGES = {"python3", "javascript", "typescript", "bash", "java", "cpp", "c", "go"}


def _parse_http_body(raw: bytes, content_type: str) -> dict[str, Any]:
    text = raw.decode("utf-8", errors="replace")
    if "text/event-stream" not in content_type.lower():
        return json.loads(text)
    candidates: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            candidates.append(obj)
    if not candidates:
        raise RuntimeError("SandboxAPI MCP returned SSE without a JSON-RPC data event")
    return candidates[-1]


def _rpc(payload: dict[str, Any], *, timeout: int = 45) -> dict[str, Any]:
    key = get_secret("RAPIDAPI_KEY")
    req = urllib.request.Request(
        MCP_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "FRANK-RAE/8.8 sandbox research runtime",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = _parse_http_body(resp.read(), resp.headers.get("Content-Type", ""))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1200]
        raise RuntimeError(f"SandboxAPI MCP HTTP {exc.code}: {detail}") from exc
    if body.get("error"):
        err = body["error"]
        raise RuntimeError(f"SandboxAPI MCP JSON-RPC error: {err}")
    return body


def initialize() -> dict[str, Any]:
    return _rpc({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "frank-rae", "version": "8.8"},
        },
    })


def _tool_text(result: dict[str, Any]) -> str:
    payload = result.get("result") or {}
    content = payload.get("content") or []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            return str(item.get("text") or "")
    if payload.get("structuredContent") is not None:
        return json.dumps(payload["structuredContent"], ensure_ascii=False)
    raise RuntimeError(f"SandboxAPI MCP tool result contained no text content: {payload}")


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    # The hosted server is stateless, but initialize first so protocol/version
    # incompatibility is detected before a research execution is consumed.
    initialize()
    body = _rpc({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }, timeout=max(45, int(arguments.get("timeout", 10)) + 20))
    text = _tool_text(body)
    try:
        decoded = json.loads(text)
    except json.JSONDecodeError:
        return {"text": text}
    return decoded if isinstance(decoded, dict) else {"value": decoded}


def execute_code(code: str, *, language: str = "python3", timeout: int = 10, stdin: str = "") -> dict[str, Any]:
    if language not in ALLOWED_LANGUAGES:
        raise ValueError(f"unsupported language: {language}")
    if not code or len(code.encode("utf-8")) > 1_000_000:
        raise ValueError("code must be 1..1000000 UTF-8 bytes")
    timeout = max(1, min(int(timeout), 300))
    args: dict[str, Any] = {"language": language, "code": code, "timeout": timeout}
    if stdin:
        args["stdin"] = stdin
    out = call_tool("execute_code", args)
    return {
        "provider": "SandboxAPI via RapidAPI/MCP",
        "tool": "sandboxapi_sandbox",
        "evidence_class": "isolated_runtime_experiment",
        "language": language,
        "result": out,
    }


def smoke_test() -> dict[str, Any]:
    out = execute_code("print('RAE_SANDBOXAPI_OK:' + str(6*7))", language="python3", timeout=10)
    result = out.get("result") or {}
    stdout = str(result.get("stdout") or "")
    if int(result.get("exit_code", -1)) != 0 or "RAE_SANDBOXAPI_OK:42" not in stdout:
        raise RuntimeError(f"SandboxAPI smoke sentinel mismatch: {result}")
    return {
        "schema_version": "1.0",
        "provider": "SandboxAPI",
        "tool": "sandboxapi_sandbox",
        "status": "RUNTIME_VERIFIED",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "credential_source": secret_source("RAPIDAPI_KEY"),
        "credential_value_exposed": False,
        "verification_class": "remote_gvisor_code_execution",
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
    ap = argparse.ArgumentParser(description="Execute code through SandboxAPI's hosted MCP sandbox")
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
