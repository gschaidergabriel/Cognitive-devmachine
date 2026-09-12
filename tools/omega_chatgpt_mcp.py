#!/usr/bin/env python3
"""Authenticated MCP surface for OMEGA -> verified local FranKenstein bridges.

This is an adapter, not a second authority system.  It exposes the existing
GitHub Local Bridge as real MCP tools so ChatGPT can *actually* inspect and act
on Gabriel/Andreas hosts instead of merely knowing that the bridge exists.

Hard invariants:
- person -> machine_id/owner/control/results mapping is exact and closed;
- every returned receipt is verified against that mapping, command_id, op and
  the exact immutable command bytes queued to the Local Bridge;
- DELETE/removal, storage/filesystem FORMAT and protected alignment mutation are
  denied by the same pre-dispatch guard used by ``omega_grid_relay``;
- write/exec/screenshot effects are fail-closed unless OMEGA_MCP_EFFECTS_ENABLED=1;
- a model statement is never treated as execution evidence: only a verified
  Local Bridge receipt may be returned as PASS.

Transport is MCP Streamable HTTP compatible for the subset ChatGPT needs:
``initialize``, ``ping``, ``tools/list`` and ``tools/call``.  The server is
stateless and may be put behind any HTTPS reverse proxy.  Authentication uses
``Authorization: Bearer $OMEGA_MCP_TOKEN``.
"""
from __future__ import annotations

import hmac
import json
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import omega_grid_relay as relay  # noqa: E402

PROTOCOL_VERSION = "2025-03-26"
SERVER_NAME = "omega-frankenstein-bridge"
SERVER_VERSION = "1.1.0"
BIND = (os.getenv("OMEGA_MCP_BIND") or "127.0.0.1").strip()
PORT = int(os.getenv("OMEGA_MCP_PORT") or "8789")
MAX_BODY = max(4096, min(int(os.getenv("OMEGA_MCP_MAX_BODY") or str(256 * 1024)), 2 * 1024 * 1024))
DEFAULT_WAIT_S = max(0.0, min(float(os.getenv("OMEGA_MCP_WAIT_SECONDS") or "12"), 25.0))

PERSON_TO_ORGAN = {
    "gabriel": "host:ai-core-node",
    "andreas": "host:andreas-maco",
}

_ID_SAFE = re.compile(r"[^A-Za-z0-9_.-]+")


class McpBridgeError(RuntimeError):
    def __init__(self, code: str, message: str | None = None):
        super().__init__(message or code)
        self.code = code
        self.message = message or code


def _effects_enabled() -> bool:
    return (os.getenv("OMEGA_MCP_EFFECTS_ENABLED") or "").strip().lower() in {"1", "true", "yes", "on"}


def _token() -> str:
    return (os.getenv("OMEGA_MCP_TOKEN") or "").strip()


def _authorized(header: str | None) -> bool:
    expected = _token()
    if not expected:
        return False
    provided = str(header or "")
    prefix = "Bearer "
    if not provided.startswith(prefix):
        return False
    return hmac.compare_digest(provided[len(prefix):], expected)


def _target(person: str) -> tuple[str, dict[str, str]]:
    label = str(person or "").strip().lower()
    organ_id = PERSON_TO_ORGAN.get(label)
    if organ_id is None:
        raise McpBridgeError("UNKNOWN_PERSON", "person must be exactly 'gabriel' or 'andreas'")
    target = relay.ORGAN.get(organ_id)
    if not isinstance(target, dict):
        raise McpBridgeError("ORGAN_MAPPING_MISSING")
    return organ_id, target


def _request_key(rpc_id: Any, person: str, op: str, args: dict[str, Any]) -> str:
    # Stable for an HTTP retry with the same JSON-RPC id + exact arguments.
    # The argument digest makes accidental id reuse unable to alias another op.
    raw_id = _ID_SAFE.sub("-", str(rpc_id if rpc_id is not None else "notification"))[:48] or "call"
    d = relay.digest({"person": person, "op": op, "args": args})[:16]
    return f"{raw_id}-{d}"


def _receipt_path(command_id: str) -> str:
    return f"local_bridge/results/receipts/{command_id}.json"


def _command_path(command_id: str) -> str:
    return f"local_bridge/commands/{command_id}.json"


def _verify_receipt(
    target: dict[str, str],
    command_id: str,
    receipt: dict[str, Any],
    *,
    command: dict[str, Any],
    command_bytes: bytes,
) -> dict[str, Any]:
    if str(command.get("command_id") or "") != command_id:
        raise McpBridgeError("COMMAND_EVIDENCE_MISMATCH", "command file id does not match requested command_id")
    machine = str(command.get("machine_id") or "").strip().lower()
    owner = str(command.get("owner") or "").strip().lower()
    if machine != target["machine_id"] or owner != target["owner"]:
        raise McpBridgeError(
            "COMMAND_IDENTITY_MISMATCH",
            f"expected command target {target['machine_id']}/{target['owner']}, got {machine}/{owner}",
        )
    try:
        return relay.verify_local_receipt(target, command, command_bytes, receipt, require_pass=False)
    except relay.ReceiptVerificationError as exc:
        raise McpBridgeError(exc.code, exc.message) from exc


def _load_receipt(
    person: str,
    command_id: str,
    *,
    wait_seconds: float = 0.0,
    command: dict[str, Any] | None = None,
    command_bytes: bytes | None = None,
) -> dict[str, Any]:
    _organ_id, target = _target(person)
    cid = str(command_id or "").strip()
    if not cid or len(cid) > 180 or _ID_SAFE.search(cid):
        raise McpBridgeError("INVALID_COMMAND_ID")
    raw = relay.wait_file(target["results"], _receipt_path(cid), max(0.0, min(wait_seconds, 25.0))) if wait_seconds > 0 else relay.get_file(target["results"], _receipt_path(cid))
    if raw is None:
        return {
            "ok": False,
            "state": "PENDING",
            "person": person,
            "machine_id": target["machine_id"],
            "owner": target["owner"],
            "command_id": cid,
        }
    try:
        receipt = json.loads(raw)
    except Exception as exc:
        raise McpBridgeError("INVALID_RECEIPT_JSON", str(exc)) from exc
    if not isinstance(receipt, dict):
        raise McpBridgeError("INVALID_RECEIPT_TYPE")

    if command is None or command_bytes is None:
        command_bytes = relay.get_file(target["control"], _command_path(cid))
        if command_bytes is None:
            raise McpBridgeError("COMMAND_EVIDENCE_MISSING")
        try:
            command = json.loads(command_bytes)
        except Exception as exc:
            raise McpBridgeError("INVALID_COMMAND_EVIDENCE_JSON", str(exc)) from exc
        if not isinstance(command, dict):
            raise McpBridgeError("INVALID_COMMAND_EVIDENCE_TYPE")

    _verify_receipt(target, cid, receipt, command=command, command_bytes=command_bytes)
    status = str(receipt.get("status") or "UNKNOWN").upper()
    return {
        "ok": status == "PASS",
        "state": status,
        "person": person,
        "machine_id": target["machine_id"],
        "owner": target["owner"],
        "command_id": cid,
        "receipt": receipt,
    }


def _dispatch(person: str, op: str, args: dict[str, Any], *, rpc_id: Any, wait_seconds: float = DEFAULT_WAIT_S) -> dict[str, Any]:
    label = str(person or "").strip().lower()
    organ_id, target = _target(label)

    if op in {"exec", "write_text", "screenshot"} and not _effects_enabled():
        raise McpBridgeError(
            "EFFECTS_DISABLED",
            "effect tools are fail-closed; set OMEGA_MCP_EFFECTS_ENABLED=1 only on the authenticated production gateway",
        )

    task = {"bridge_op": op, "bridge_args": dict(args)}
    effect_id = "chatgpt-mcp-" + _request_key(rpc_id, label, op, args)
    # Reuse the canonical relay command builder so DELETE/FORMAT/protected-path
    # fences are mechanically identical to GRID -> Local Bridge delivery.
    effect = {"effect_id": effect_id, "organ_id": organ_id, "task": task}
    try:
        command_id, command, _ = relay.build_local_command(effect)
    except PermissionError as exc:
        raise McpBridgeError(str(exc), str(exc)) from exc

    path = _command_path(command_id)
    command_bytes = relay.serialized_local_command(command)
    relay.put_new(
        target["control"],
        path,
        command_bytes,
        f"omega mcp: {op} {command_id}",
    )
    return _load_receipt(
        label,
        command_id,
        wait_seconds=wait_seconds,
        command=command,
        command_bytes=command_bytes,
    )


def _text_result(payload: dict[str, Any], *, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, separators=(",", ":"))}],
        "structuredContent": payload,
        "isError": bool(is_error),
    }


TOOLS: list[dict[str, Any]] = [
    {
        "name": "omega_status",
        "description": "Get live status from Gabriel's ai-core-node or Andreas' andreas-maco through the verified OMEGA Local Bridge. Use this instead of guessing whether a host is reachable.",
        "inputSchema": {
            "type": "object",
            "properties": {"person": {"type": "string", "enum": ["gabriel", "andreas"]}, "wait_seconds": {"type": "number", "minimum": 0, "maximum": 25}},
            "required": ["person"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
    },
    {
        "name": "omega_read",
        "description": "Read one file from the selected verified Frankenstein host. Use when the user asks about a local file or current machine state stored in a file.",
        "inputSchema": {
            "type": "object",
            "properties": {"person": {"type": "string", "enum": ["gabriel", "andreas"]}, "path": {"type": "string", "minLength": 1, "maxLength": 4096}, "wait_seconds": {"type": "number", "minimum": 0, "maximum": 25}},
            "required": ["person", "path"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
    },
    {
        "name": "omega_execute",
        "description": "Execute an authorized shell command on the selected verified Frankenstein host through OMEGA. Real execution is proven only by the returned Local Bridge receipt. DELETE/removal, storage/filesystem FORMAT and protected alignment mutation are denied at pre-dispatch.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "person": {"type": "string", "enum": ["gabriel", "andreas"]},
                "command": {"type": "string", "minLength": 1, "maxLength": 32000},
                "cwd": {"type": "string", "maxLength": 4096},
                "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 3600},
                "wait_seconds": {"type": "number", "minimum": 0, "maximum": 25}
            },
            "required": ["person", "command"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True},
    },
    {
        "name": "omega_write_text",
        "description": "Write exact text to one path on the selected verified Frankenstein host. Protected alignment/security files are denied. Use only when the user asked for a file change.",
        "inputSchema": {
            "type": "object",
            "properties": {"person": {"type": "string", "enum": ["gabriel", "andreas"]}, "path": {"type": "string", "minLength": 1, "maxLength": 4096}, "content": {"type": "string", "maxLength": 200000}, "wait_seconds": {"type": "number", "minimum": 0, "maximum": 25}},
            "required": ["person", "path", "content"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": True},
    },
    {
        "name": "omega_screenshot",
        "description": "Request a screenshot from the selected verified Frankenstein host. Availability depends on that host's desktop/session permissions.",
        "inputSchema": {
            "type": "object",
            "properties": {"person": {"type": "string", "enum": ["gabriel", "andreas"]}, "name": {"type": "string", "maxLength": 120}, "wait_seconds": {"type": "number", "minimum": 0, "maximum": 25}},
            "required": ["person"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True},
    },
    {
        "name": "omega_receipt",
        "description": "Fetch a Local Bridge receipt for a previously queued OMEGA command. Use when another tool returned PENDING; never claim execution success until this returns an exactly correlated PASS.",
        "inputSchema": {
            "type": "object",
            "properties": {"person": {"type": "string", "enum": ["gabriel", "andreas"]}, "command_id": {"type": "string", "minLength": 1, "maxLength": 180}, "wait_seconds": {"type": "number", "minimum": 0, "maximum": 25}},
            "required": ["person", "command_id"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
    },
]


def call_tool(name: str, arguments: dict[str, Any], *, rpc_id: Any = None) -> dict[str, Any]:
    try:
        if not isinstance(arguments, dict):
            raise McpBridgeError("INVALID_ARGUMENTS")
        person = str(arguments.get("person") or "").strip().lower()
        wait_s = max(0.0, min(float(arguments.get("wait_seconds", DEFAULT_WAIT_S)), 25.0))

        if name == "omega_status":
            payload = _dispatch(person, "status", {}, rpc_id=rpc_id, wait_seconds=wait_s)
        elif name == "omega_read":
            path = str(arguments.get("path") or "")
            if not path or "\x00" in path:
                raise McpBridgeError("INVALID_PATH")
            payload = _dispatch(person, "read_file", {"path": path}, rpc_id=rpc_id, wait_seconds=wait_s)
        elif name == "omega_execute":
            command = str(arguments.get("command") or "")
            if not command.strip() or "\x00" in command:
                raise McpBridgeError("INVALID_COMMAND")
            args: dict[str, Any] = {"command": command, "timeout_seconds": max(1, min(int(arguments.get("timeout_seconds", 120)), 3600))}
            cwd = str(arguments.get("cwd") or "").strip()
            if cwd:
                if "\x00" in cwd:
                    raise McpBridgeError("INVALID_CWD")
                args["cwd"] = cwd
            payload = _dispatch(person, "exec", args, rpc_id=rpc_id, wait_seconds=wait_s)
        elif name == "omega_write_text":
            path = str(arguments.get("path") or "")
            content = str(arguments.get("content") or "")
            if not path or "\x00" in path:
                raise McpBridgeError("INVALID_PATH")
            payload = _dispatch(person, "write_text", {"path": path, "content": content}, rpc_id=rpc_id, wait_seconds=wait_s)
        elif name == "omega_screenshot":
            shot = str(arguments.get("name") or "omega-chatgpt")[:120]
            payload = _dispatch(person, "screenshot", {"name": shot}, rpc_id=rpc_id, wait_seconds=wait_s)
        elif name == "omega_receipt":
            payload = _load_receipt(person, str(arguments.get("command_id") or ""), wait_seconds=wait_s)
        else:
            raise McpBridgeError("UNKNOWN_TOOL", name)
        return _text_result(payload, is_error=False)
    except McpBridgeError as exc:
        return _text_result({"ok": False, "error": exc.code, "message": exc.message}, is_error=True)
    except Exception as exc:  # do not leak tracebacks/secrets through MCP
        return _text_result({"ok": False, "error": type(exc).__name__, "message": str(exc)[:500]}, is_error=True)


def handle_rpc(req: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(req, dict):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}
    rpc_id = req.get("id")
    method = str(req.get("method") or "")
    params = req.get("params") if isinstance(req.get("params"), dict) else {}

    if method.startswith("notifications/"):
        return None
    if method == "initialize":
        requested = str(params.get("protocolVersion") or PROTOCOL_VERSION)
        result = {
            "protocolVersion": requested,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "instructions": "Use omega_* tools for live Gabriel/Andreas host facts and actions. Tool availability is real capability; never claim host execution without an exactly correlated PASS receipt.",
        }
        return {"jsonrpc": "2.0", "id": rpc_id, "result": result}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": rpc_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = str(params.get("name") or "")
        arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        return {"jsonrpc": "2.0", "id": rpc_id, "result": call_tool(name, arguments, rpc_id=rpc_id)}
    return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": "Method not found"}}


class Handler(BaseHTTPRequestHandler):
    server_version = "OmegaMCP/1"

    def log_message(self, fmt: str, *args: Any) -> None:
        if (os.getenv("OMEGA_MCP_ACCESS_LOG") or "").strip().lower() in {"1", "true", "yes"}:
            super().log_message(fmt, *args)

    def _send_json(self, code: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("MCP-Protocol-Version", PROTOCOL_VERSION)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/health":
            self._send_json(200, {"ok": True, "service": SERVER_NAME, "version": SERVER_VERSION, "auth_required": True, "effects_enabled": _effects_enabled()})
            return
        self._send_json(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") not in {"", "/mcp"}:
            self._send_json(404, {"ok": False, "error": "not_found"})
            return
        if not _authorized(self.headers.get("Authorization")):
            self._send_json(401, {"ok": False, "error": "unauthorized"})
            return
        try:
            n = int(self.headers.get("Content-Length") or "0")
        except Exception:
            n = 0
        if n <= 0 or n > MAX_BODY:
            self._send_json(413 if n > MAX_BODY else 400, {"ok": False, "error": "invalid_body_size"})
            return
        try:
            raw = self.rfile.read(n)
            obj = json.loads(raw.decode("utf-8"))
        except Exception:
            self._send_json(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
            return

        if isinstance(obj, list):
            responses = [r for r in (handle_rpc(x) for x in obj) if r is not None]
            if responses:
                self._send_json(200, responses)
            else:
                self.send_response(202); self.end_headers()
            return
        response = handle_rpc(obj)
        if response is None:
            self.send_response(202); self.send_header("MCP-Protocol-Version", PROTOCOL_VERSION); self.end_headers()
            return
        self._send_json(200, response)


def main() -> int:
    if not _token():
        raise SystemExit("OMEGA_MCP_TOKEN is required; refusing to start unauthenticated")
    if not relay.TOKEN:
        raise SystemExit("GITHUB_TOKEN is required for Local Bridge delivery")
    server = ThreadingHTTPServer((BIND, PORT), Handler)
    print(json.dumps({"service": SERVER_NAME, "bind": BIND, "port": PORT, "effects_enabled": _effects_enabled()}), flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())