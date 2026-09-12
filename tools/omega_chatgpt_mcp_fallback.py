#!/usr/bin/env python3
"""Multi-transport front-end for the OMEGA ChatGPT MCP gateway.

Fallback order is deliberately asymmetric and evidence preserving:

Gabriel on ai-core-node:
  read-only status: direct typed broker -> local Unix engine -> GitHub bridge
  read/effects:      local Unix engine -> GitHub bridge (only if local preflight
                     was unavailable before execution began)
Andreas:
  read-only status: direct typed broker -> GitHub bridge
  read/effects:      GitHub bridge

A transport is never retried through another effect path after an operation may
have started. PENDING/UNKNOWN outcomes remain pending/unknown and must be
resolved by receipt instead of risking duplicate execution.
"""
from __future__ import annotations

import copy
import hmac
import json
import os
import socket
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from typing import Any

import omega_chatgpt_mcp as base

_BASE_CALL_TOOL = base.call_tool

DIRECT_EXPECTED = {
    "gabriel": {"machine_id": "ai-core-node", "owner": "gabriel"},
    "andreas": {"machine_id": "andreas-maco", "owner": "andreas"},
}


class FallbackUnavailable(RuntimeError):
    pass


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _direct_cfg(person: str) -> tuple[str, str] | None:
    p = str(person or "").strip().lower()
    if p not in DIRECT_EXPECTED:
        base._target(p)  # raises canonical UNKNOWN_PERSON
    up = p.upper()
    url = (
        os.getenv(f"OMEGA_MCP_DIRECT_{up}_URL")
        or os.getenv(f"FRANK_VOICE_BROKER_{up}")
        or ""
    ).strip().rstrip("/")
    token = (
        os.getenv(f"OMEGA_MCP_DIRECT_{up}_TOKEN")
        or os.getenv(f"FRANK_VOICE_BROKER_{up}_TOKEN")
        or os.getenv("FRANK_VOICE_BROKER_TOKEN")
        or ""
    ).strip()
    return (url, token) if url and token else None


def _verify_direct(person: str, payload: dict[str, Any]) -> dict[str, Any]:
    expected = DIRECT_EXPECTED[person]
    machine = str(payload.get("machine_id") or "").strip().lower()
    owner = str(payload.get("owner") or "").strip().lower()
    if machine != expected["machine_id"] or owner != expected["owner"]:
        raise FallbackUnavailable(
            f"DIRECT_IDENTITY_MISMATCH: expected {expected['machine_id']}/{expected['owner']}, got {machine}/{owner}"
        )
    return payload


def _direct_request(person: str, path: str, body: dict[str, Any] | None = None, timeout: float = 0.8) -> dict[str, Any]:
    cfg = _direct_cfg(person)
    if cfg is None:
        raise FallbackUnavailable("DIRECT_BROKER_NOT_CONFIGURED")
    url, token = cfg
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode()
    req = urllib.request.Request(
        url + path,
        data=data,
        method="GET" if body is None else "POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=max(0.1, min(timeout, 2.0))) as response:
            raw = response.read(256 * 1024)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise FallbackUnavailable(f"DIRECT_BROKER_UNAVAILABLE:{type(exc).__name__}:{exc}") from exc
    try:
        payload = json.loads(raw.decode())
    except Exception as exc:
        raise FallbackUnavailable(f"DIRECT_BROKER_INVALID_JSON:{exc}") from exc
    if not isinstance(payload, dict):
        raise FallbackUnavailable("DIRECT_BROKER_INVALID_TYPE")
    return _verify_direct(person, payload)


def _direct_status(person: str) -> dict[str, Any]:
    health = _direct_request(person, "/health", timeout=0.55)
    state = None
    try:
        state = _direct_request(person, "/v1/state-snapshot", {"person": person}, timeout=0.8)
    except FallbackUnavailable:
        pass
    expected = DIRECT_EXPECTED[person]
    return {
        "ok": True,
        "state": "PASS",
        "person": person,
        "machine_id": expected["machine_id"],
        "owner": expected["owner"],
        "transport_used": "direct_host_broker",
        "health": health,
        "host_state": state,
    }


def _local_enabled() -> bool:
    return _env_bool("OMEGA_MCP_LOCAL_FALLBACK_ENABLED", True)


def _local_socket() -> str:
    configured = (os.getenv("OMEGA_LOCAL_EFFECT_SOCKET") or "").strip()
    if configured:
        return os.path.expanduser(configured)
    runtime = os.getenv("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    return os.path.join(runtime, "omega-local-effect.sock")


def _local_token() -> str:
    return (os.getenv("OMEGA_LOCAL_EFFECT_TOKEN") or "").strip()


def _local_eligible(person: str) -> bool:
    return str(person or "").strip().lower() == "gabriel" and _local_enabled() and bool(_local_token())


def _local_request(payload: dict[str, Any], timeout: float = 2.0) -> dict[str, Any]:
    if not _local_token():
        raise FallbackUnavailable("LOCAL_ADAPTER_TOKEN_MISSING")
    req = {"schema": "OMEGA_LOCAL_EFFECT/v1", "token": _local_token(), **payload}
    raw = json.dumps(req, ensure_ascii=False, separators=(",", ":")).encode() + b"\n"
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(max(0.2, min(timeout, 30.0)))
    try:
        sock.connect(_local_socket())
        sock.sendall(raw)
        chunks = []
        size = 0
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk); size += len(chunk)
            if b"\n" in chunk or size > 512 * 1024:
                break
    except (OSError, TimeoutError) as exc:
        raise FallbackUnavailable(f"LOCAL_ADAPTER_UNAVAILABLE:{type(exc).__name__}:{exc}") from exc
    finally:
        sock.close()
    try:
        response = json.loads(b"".join(chunks).split(b"\n", 1)[0].decode())
    except Exception as exc:
        raise FallbackUnavailable(f"LOCAL_ADAPTER_INVALID_JSON:{exc}") from exc
    if not isinstance(response, dict):
        raise FallbackUnavailable("LOCAL_ADAPTER_INVALID_TYPE")
    return response


def _local_call(person: str, op: str, args: dict[str, Any], rpc_id: Any, timeout: float = 30.0) -> dict[str, Any]:
    if not _local_eligible(person):
        raise FallbackUnavailable("LOCAL_ADAPTER_NOT_ELIGIBLE")
    response = _local_request({"kind": "execute", "person": person, "op": op, "args": args, "rpc_id": rpc_id}, timeout=timeout)
    if response.get("error"):
        error = str(response.get("error"))
        # Configuration/socket/identity failures happen before an effect begins
        # and may safely degrade to GitHub. Policy and execution failures may not.
        if error.startswith(("LOCAL_ENGINE_", "GATEWAY_IDENTITY_", "LOCAL_TRANSPORT_")):
            raise FallbackUnavailable(error)
    return response


def _local_receipt(command_id: str) -> dict[str, Any]:
    return _local_request({"kind": "receipt", "command_id": command_id}, timeout=1.5)


def _strip_transport(arguments: dict[str, Any]) -> dict[str, Any]:
    clean = dict(arguments)
    clean.pop("transport", None)
    return clean


def _decorate_result(result: dict[str, Any], attempts: list[dict[str, str]], selected: str | None = None) -> dict[str, Any]:
    if not isinstance(result, dict):
        return result
    payload = result.get("structuredContent")
    if isinstance(payload, dict):
        payload = dict(payload)
        payload.setdefault("transport_attempts", attempts)
        if selected:
            payload.setdefault("transport_used", selected)
        payload["fallback_used"] = len(attempts) > 1
        return base._text_result(payload, is_error=bool(result.get("isError")))
    return result


def _github_call(name: str, arguments: dict[str, Any], rpc_id: Any) -> dict[str, Any]:
    return _BASE_CALL_TOOL(name, _strip_transport(arguments), rpc_id=rpc_id)


def _transport_status(person: str | None = None) -> dict[str, Any]:
    people = [person] if person else ["gabriel", "andreas"]
    out: dict[str, Any] = {
        "ok": True,
        "effects_enabled": base._effects_enabled(),
        "github_control_plane_configured": bool(getattr(base.relay, "TOKEN", "")),
        "local_adapter_enabled": _local_enabled(),
        "local_adapter_socket": _local_socket(),
        "people": {},
    }
    for p in people:
        base._target(p)
        entry: dict[str, Any] = {
            "direct_broker_configured": _direct_cfg(p) is not None,
            "local_adapter_eligible": _local_eligible(p),
            "github_control_plane": True,
        }
        if _local_eligible(p):
            try:
                health = _local_request({"kind": "health"}, timeout=0.5)
                entry["local_adapter_live"] = bool(health.get("ok"))
            except Exception as exc:
                entry["local_adapter_live"] = False
                entry["local_adapter_error"] = str(exc)[:240]
        out["people"][p] = entry
    return out


TOOLS = copy.deepcopy(base.TOOLS)
for tool in TOOLS:
    schema = tool.get("inputSchema") or {}
    props = schema.setdefault("properties", {})
    props["transport"] = {
        "type": "string",
        "enum": ["auto", "direct", "local", "github"],
        "description": "Transport preference. auto uses the verified fallback stack; use explicit values only for diagnostics.",
    }
TOOL_TRANSPORT_STATUS = {
    "name": "omega_transport_status",
    "description": "Inspect which verified OMEGA transport paths are configured/live without guessing. This is diagnostic and does not execute host effects.",
    "inputSchema": {
        "type": "object",
        "properties": {"person": {"type": "string", "enum": ["gabriel", "andreas"]}},
        "additionalProperties": False,
    },
    "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
}
TOOLS.append(TOOL_TRANSPORT_STATUS)


def call_tool(name: str, arguments: dict[str, Any], *, rpc_id: Any = None) -> dict[str, Any]:
    if not isinstance(arguments, dict):
        return base._text_result({"ok": False, "error": "INVALID_ARGUMENTS"}, is_error=True)
    if name == "omega_transport_status":
        try:
            person = str(arguments.get("person") or "").strip().lower() or None
            return base._text_result(_transport_status(person))
        except Exception as exc:
            return base._text_result({"ok": False, "error": type(exc).__name__, "message": str(exc)[:500]}, is_error=True)

    person = str(arguments.get("person") or "").strip().lower()
    try:
        base._target(person)
    except Exception as exc:
        return base._text_result({"ok": False, "error": getattr(exc, "code", type(exc).__name__), "message": str(exc)}, is_error=True)
    transport = str(arguments.get("transport") or "auto").strip().lower()
    if transport not in {"auto", "direct", "local", "github"}:
        return base._text_result({"ok": False, "error": "INVALID_TRANSPORT"}, is_error=True)
    attempts: list[dict[str, str]] = []

    def note(which: str, state: str, detail: str = "") -> None:
        item = {"transport": which, "state": state}
        if detail:
            item["detail"] = detail[:300]
        attempts.append(item)

    # Receipt resolution is special: query local idempotency first, then GitHub.
    if name == "omega_receipt":
        cid = str(arguments.get("command_id") or "")
        if transport in {"auto", "local"} and _local_eligible(person):
            try:
                payload = _local_receipt(cid)
                note("local_unix_engine", str(payload.get("state") or "UNKNOWN"))
                if payload.get("state") != "NOT_FOUND" or transport == "local":
                    return base._text_result({**payload, "transport_attempts": attempts, "fallback_used": False}, is_error=False)
            except FallbackUnavailable as exc:
                note("local_unix_engine", "UNAVAILABLE", str(exc))
                if transport == "local":
                    return base._text_result({"ok": False, "error": "LOCAL_UNAVAILABLE", "message": str(exc), "transport_attempts": attempts}, is_error=True)
        if transport == "direct":
            return base._text_result({"ok": False, "error": "DIRECT_RECEIPT_UNSUPPORTED"}, is_error=True)
        result = _github_call(name, arguments, rpc_id)
        note("github_local_bridge", "CALLED")
        return _decorate_result(result, attempts, "github_local_bridge")

    # Status has the richest read-only fallback stack.
    if name == "omega_status":
        if transport in {"auto", "direct"}:
            try:
                payload = _direct_status(person)
                note("direct_host_broker", "PASS")
                payload.update({"transport_attempts": attempts, "fallback_used": False})
                return base._text_result(payload)
            except FallbackUnavailable as exc:
                note("direct_host_broker", "UNAVAILABLE", str(exc))
                if transport == "direct":
                    return base._text_result({"ok": False, "error": "DIRECT_UNAVAILABLE", "message": str(exc), "transport_attempts": attempts}, is_error=True)
        if transport in {"auto", "local"} and _local_eligible(person):
            try:
                payload = _local_call(person, "status", {}, rpc_id, timeout=2.0)
                note("local_unix_engine", str(payload.get("state") or "UNKNOWN"))
                payload.update({"transport_attempts": attempts, "fallback_used": len(attempts) > 1})
                return base._text_result(payload, is_error=False)
            except FallbackUnavailable as exc:
                note("local_unix_engine", "UNAVAILABLE", str(exc))
                if transport == "local":
                    return base._text_result({"ok": False, "error": "LOCAL_UNAVAILABLE", "message": str(exc), "transport_attempts": attempts}, is_error=True)
        if transport == "local":
            return base._text_result({"ok": False, "error": "LOCAL_NOT_ELIGIBLE", "transport_attempts": attempts}, is_error=True)
        result = _github_call(name, arguments, rpc_id)
        note("github_local_bridge", "CALLED")
        return _decorate_result(result, attempts, "github_local_bridge")

    op_map = {"omega_read": "read_file", "omega_execute": "exec", "omega_write_text": "write_text", "omega_screenshot": "screenshot"}
    op = op_map.get(name)
    if op is None:
        return _github_call(name, arguments, rpc_id)
    clean = _strip_transport(arguments)
    clean.pop("person", None)
    clean.pop("wait_seconds", None)
    if op == "exec":
        args = {"command": str(clean.get("command") or ""), "timeout_seconds": int(clean.get("timeout_seconds", 120))}
        if clean.get("cwd"):
            args["cwd"] = str(clean["cwd"])
    elif op == "read_file":
        args = {"path": str(clean.get("path") or "")}
    elif op == "write_text":
        args = {"path": str(clean.get("path") or ""), "content": str(clean.get("content") or "")}
    else:
        args = {"name": str(clean.get("name") or "omega-chatgpt")[:120]}

    if transport == "direct":
        return base._text_result({"ok": False, "error": "DIRECT_EFFECT_UNSUPPORTED"}, is_error=True)

    if transport in {"auto", "local"} and _local_eligible(person):
        try:
            payload = _local_call(person, op, args, rpc_id, timeout=max(2.0, min(float(arguments.get("wait_seconds", 12)) + 2.0, 30.0)))
            note("local_unix_engine", str(payload.get("state") or payload.get("error") or "UNKNOWN"))
            # Once the local adapter accepted the request, never double-dispatch
            # an effect through GitHub, even when the result is ERROR/UNKNOWN.
            payload.update({"transport_attempts": attempts, "fallback_used": False})
            return base._text_result(payload, is_error=bool(payload.get("error")))
        except FallbackUnavailable as exc:
            note("local_unix_engine", "UNAVAILABLE_PRE_DISPATCH", str(exc))
            if transport == "local":
                return base._text_result({"ok": False, "error": "LOCAL_UNAVAILABLE", "message": str(exc), "transport_attempts": attempts}, is_error=True)
    elif transport == "local":
        return base._text_result({"ok": False, "error": "LOCAL_NOT_ELIGIBLE"}, is_error=True)

    # Universal recovery/remote path. If this returns PENDING, do not attempt a
    # second effect transport because the command may already be in flight.
    result = _github_call(name, arguments, rpc_id)
    note("github_local_bridge", "CALLED")
    return _decorate_result(result, attempts, "github_local_bridge")


# Patch only the MCP adapter module's extension points; the canonical relay and
# underlying Local Bridge remain untouched.
base.TOOLS = TOOLS
base.call_tool = call_tool


class Handler(base.Handler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/health":
            payload = {
                "ok": True,
                "service": base.SERVER_NAME,
                "version": "1.1.0-fallback",
                "auth_required": True,
                "effects_enabled": base._effects_enabled(),
                "github_control_plane_configured": bool(getattr(base.relay, "TOKEN", "")),
                "local_fallback_enabled": _local_enabled(),
                "local_socket": _local_socket(),
            }
            self._send_json(200, payload)
            return
        super().do_GET()


def main() -> int:
    if not base._token():
        raise SystemExit("OMEGA_MCP_TOKEN is required; refusing to start unauthenticated")
    # Unlike the original single-transport server, do not require GitHub at
    # process start. Direct/local read paths stay useful during a GitHub outage.
    server = ThreadingHTTPServer((base.BIND, base.PORT), Handler)
    print(json.dumps({"service": base.SERVER_NAME, "version": "1.1.0-fallback", "bind": base.BIND, "port": base.PORT, "effects_enabled": base._effects_enabled()}, separators=(",", ":")), flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
