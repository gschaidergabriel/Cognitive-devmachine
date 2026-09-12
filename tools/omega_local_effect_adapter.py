#!/usr/bin/env python3
"""Host-local, non-network fallback transport for OMEGA MCP effects.

This adapter exists so a Gabriel-hosted OMEGA MCP gateway does not depend on
GitHub being reachable for every local action. It is a transport adapter, not a
second authority system:

* only the exact ai-core-node/gabriel installation is admitted;
* the canonical ``omega_grid_relay.build_local_command`` guard is applied
  before any operation, preserving DELETE/FORMAT/protected-path denials;
* the already-running FranKenstein local-bridge engine supplies operation
  semantics (status/read/exec/write/screenshot);
* a 0600 Unix socket plus an independent bearer secret is required;
* command ids are deterministic and persisted before execution so a crash can
  never cause a blind replay of an effect with an unknown outcome.

The socket is intentionally local only. Remote Andreas effects remain on the
verified GitHub Local Bridge unless a separately authenticated private transport
is explicitly deployed there.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import importlib.util
import json
import os
import pathlib
import re
import socketserver
import sqlite3
import subprocess
import sys
import threading
import traceback
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import omega_grid_relay as relay  # noqa: E402

SCHEMA = "OMEGA_LOCAL_EFFECT/v1"
EXPECTED_PERSON = "gabriel"
EXPECTED_MACHINE = "ai-core-node"
EXPECTED_OWNER = "gabriel"
MAX_REQUEST = 512 * 1024
_ID_SAFE = re.compile(r"[^A-Za-z0-9_.-]+")
_DB_LOCK = threading.RLock()
_ENGINE = None


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _effects_enabled() -> bool:
    return (os.getenv("OMEGA_MCP_EFFECTS_ENABLED") or "").strip().lower() in {"1", "true", "yes", "on"}


def _token() -> str:
    return (os.getenv("OMEGA_LOCAL_EFFECT_TOKEN") or "").strip()


def _socket_path() -> pathlib.Path:
    configured = (os.getenv("OMEGA_LOCAL_EFFECT_SOCKET") or "").strip()
    if configured:
        return pathlib.Path(configured).expanduser()
    runtime = os.getenv("XDG_RUNTIME_DIR")
    if runtime:
        return pathlib.Path(runtime) / "omega-local-effect.sock"
    return pathlib.Path.home() / ".local/state/omega-chatgpt-mcp/local-effect.sock"


def _db_path() -> pathlib.Path:
    configured = (os.getenv("OMEGA_LOCAL_EFFECT_DB") or "").strip()
    if configured:
        return pathlib.Path(configured).expanduser()
    return pathlib.Path.home() / ".local/state/omega-chatgpt-mcp/local-effect.sqlite3"


def _engine_path() -> pathlib.Path:
    configured = (os.getenv("OMEGA_LOCAL_BRIDGE_ENGINE") or "").strip()
    if configured:
        return pathlib.Path(configured).expanduser()
    return pathlib.Path.home() / ".claude/star/local_bridge_daemon.py"


def _configured_identity() -> tuple[str, str]:
    machine = (os.getenv("OMEGA_MCP_GATEWAY_MACHINE_ID") or "").strip().lower()
    owner = (os.getenv("OMEGA_MCP_GATEWAY_OWNER") or "").strip().lower()
    return machine, owner


def _identity_preflight() -> None:
    machine, owner = _configured_identity()
    if machine != EXPECTED_MACHINE or owner != EXPECTED_OWNER:
        raise RuntimeError(f"GATEWAY_IDENTITY_MISMATCH:{machine}/{owner}")


def _db() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=2)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS operation("
        "command_id TEXT PRIMARY KEY,state TEXT NOT NULL,receipt_json TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL)"
    )
    conn.commit()
    return conn


def _load_engine():
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    path = _engine_path()
    if not path.is_file():
        raise RuntimeError(f"LOCAL_ENGINE_MISSING:{path}")
    spec = importlib.util.spec_from_file_location("omega_existing_local_bridge_engine", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("LOCAL_ENGINE_IMPORT_SPEC_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    machine = str(getattr(module, "MACHINE_ID", "")).strip().lower()
    owner = str(getattr(module, "OWNER", "")).strip().lower()
    if machine != EXPECTED_MACHINE or owner != EXPECTED_OWNER:
        raise RuntimeError(f"LOCAL_ENGINE_IDENTITY_MISMATCH:{machine}/{owner}")
    if not callable(getattr(module, "operate", None)):
        raise RuntimeError("LOCAL_ENGINE_OPERATE_MISSING")
    _ENGINE = module
    return module


def _request_key(rpc_id: Any, op: str, args: dict[str, Any]) -> str:
    raw = _ID_SAFE.sub("-", str(rpc_id if rpc_id is not None else "call"))[:48] or "call"
    return f"{raw}-{relay.digest({'person': EXPECTED_PERSON, 'op': op, 'args': args})[:16]}"


def _build_command(op: str, args: dict[str, Any], rpc_id: Any) -> tuple[str, dict[str, Any]]:
    effect_id = "chatgpt-mcp-local-" + _request_key(rpc_id, op, args)
    effect = {
        "effect_id": effect_id,
        "organ_id": "host:ai-core-node",
        "task": {"bridge_op": op, "bridge_args": dict(args)},
    }
    try:
        command_id, command, _ = relay.build_local_command(effect)
    except PermissionError as exc:
        raise ValueError(str(exc)) from exc
    return command_id, command


def _row(command_id: str) -> tuple[str, str | None] | None:
    with _DB_LOCK, _db() as conn:
        r = conn.execute("SELECT state,receipt_json FROM operation WHERE command_id=?", (command_id,)).fetchone()
    return None if r is None else (str(r[0]), r[1])


def _begin_once(command_id: str) -> bool:
    now = _now()
    with _DB_LOCK, _db() as conn:
        try:
            conn.execute(
                "INSERT INTO operation(command_id,state,receipt_json,created_at,updated_at) VALUES(?,?,?,?,?)",
                (command_id, "STARTED", None, now, now),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def _finish(command_id: str, receipt: dict[str, Any]) -> None:
    with _DB_LOCK, _db() as conn:
        conn.execute(
            "UPDATE operation SET state=?,receipt_json=?,updated_at=? WHERE command_id=?",
            (str(receipt.get("status") or "UNKNOWN"), json.dumps(receipt, ensure_ascii=False), _now(), command_id),
        )
        conn.commit()


def _receipt_lookup(command_id: str) -> dict[str, Any]:
    row = _row(command_id)
    if row is None:
        return {"ok": False, "state": "NOT_FOUND", "command_id": command_id}
    state, raw = row
    if raw:
        receipt = json.loads(raw)
        return {"ok": str(receipt.get("status")).upper() == "PASS", "state": str(receipt.get("status") or state), "command_id": command_id, "receipt": receipt}
    return {
        "ok": False,
        "state": "UNKNOWN_LOCAL_OUTCOME",
        "command_id": command_id,
        "message": "operation was durably marked STARTED but no receipt was committed; refusing blind replay",
    }


def _execute(person: str, op: str, args: dict[str, Any], rpc_id: Any) -> dict[str, Any]:
    if str(person or "").strip().lower() != EXPECTED_PERSON:
        raise PermissionError("LOCAL_TRANSPORT_PERSON_MISMATCH")
    _identity_preflight()
    if op in {"exec", "write_text", "screenshot"} and not _effects_enabled():
        raise PermissionError("EFFECTS_DISABLED")
    engine = _load_engine()  # preflight before the durable STARTED marker
    command_id, command = _build_command(op, args, rpc_id)

    existing = _receipt_lookup(command_id)
    if existing.get("state") != "NOT_FOUND":
        existing.update({"transport_used": "local_unix_engine", "machine_id": EXPECTED_MACHINE, "owner": EXPECTED_OWNER, "person": EXPECTED_PERSON})
        return existing

    if not _begin_once(command_id):
        return _receipt_lookup(command_id)

    raw_command = json.dumps(command, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    started = _now()
    stdout = stderr = b""
    meta: dict[str, Any] = {}
    try:
        proc, meta = engine.operate(command)
        code = int(proc.returncode)
        stdout = proc.stdout or b""
        stderr = proc.stderr or b""
        status = "PASS" if code == 0 else "FAIL"
    except subprocess.TimeoutExpired as exc:
        code, status = 124, "TIMEOUT"
        stdout = exc.stdout or b""
        stderr = (exc.stderr or b"") + repr(exc).encode()
    except Exception as exc:
        code, status = 125, "ERROR"
        stderr = (repr(exc) + "\n" + traceback.format_exc()).encode()

    receipt = {
        "schema": "CLAY_LOCAL_RECEIPT/v1",
        "command_id": command_id,
        "command_sha256": _sha(raw_command),
        "host": EXPECTED_MACHINE,
        "owner": EXPECTED_OWNER,
        "machine_id": EXPECTED_MACHINE,
        "started_at": started,
        "finished_at": _now(),
        "status": status,
        "exit_code": code,
        "op": op,
        "stdout_sha256": _sha(stdout),
        "stderr_sha256": _sha(stderr),
        "stdout_tail": stdout.decode("utf-8", errors="replace")[-24000:],
        "stderr_tail": stderr.decode("utf-8", errors="replace")[-24000:],
        "meta": meta,
        "execution_boundary": "REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED",
        "transport": "local_unix_engine",
    }
    _finish(command_id, receipt)
    return {
        "ok": status == "PASS",
        "state": status,
        "person": EXPECTED_PERSON,
        "machine_id": EXPECTED_MACHINE,
        "owner": EXPECTED_OWNER,
        "command_id": command_id,
        "transport_used": "local_unix_engine",
        "receipt": receipt,
    }


def handle_request(req: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(req, dict) or req.get("schema") != SCHEMA:
        return {"ok": False, "error": "INVALID_SCHEMA"}
    supplied = str(req.get("token") or "")
    expected = _token()
    if not expected or not hmac.compare_digest(supplied, expected):
        return {"ok": False, "error": "UNAUTHORIZED"}
    kind = str(req.get("kind") or "execute")
    try:
        if kind == "receipt":
            _identity_preflight()
            cid = str(req.get("command_id") or "")
            if not cid or len(cid) > 180 or _ID_SAFE.search(cid):
                raise ValueError("INVALID_COMMAND_ID")
            result = _receipt_lookup(cid)
            result.update({"person": EXPECTED_PERSON, "machine_id": EXPECTED_MACHINE, "owner": EXPECTED_OWNER, "transport_used": "local_unix_engine"})
            return result
        if kind == "health":
            _identity_preflight(); _load_engine()
            return {"ok": True, "person": EXPECTED_PERSON, "machine_id": EXPECTED_MACHINE, "owner": EXPECTED_OWNER, "effects_enabled": _effects_enabled(), "transport_used": "local_unix_engine"}
        op = str(req.get("op") or "")
        if op not in {"status", "read_file", "exec", "write_text", "screenshot"}:
            raise ValueError("UNSUPPORTED_OP")
        args = req.get("args") if isinstance(req.get("args"), dict) else {}
        return _execute(str(req.get("person") or ""), op, args, req.get("rpc_id"))
    except (PermissionError, ValueError, RuntimeError) as exc:
        return {"ok": False, "error": str(exc), "message": str(exc)[:500]}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__, "message": str(exc)[:500]}


class ThreadedUnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


class Handler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        raw = self.rfile.readline(MAX_REQUEST + 1)
        if len(raw) > MAX_REQUEST:
            response = {"ok": False, "error": "REQUEST_TOO_LARGE"}
        else:
            try:
                req = json.loads(raw.decode("utf-8"))
                response = handle_request(req)
            except Exception:
                response = {"ok": False, "error": "INVALID_JSON"}
        self.wfile.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode() + b"\n")


def main() -> int:
    if not _token():
        raise SystemExit("OMEGA_LOCAL_EFFECT_TOKEN is required")
    _identity_preflight()
    _load_engine()
    sock = _socket_path()
    sock.parent.mkdir(parents=True, exist_ok=True)
    try:
        sock.unlink()
    except FileNotFoundError:
        pass
    server = ThreadedUnixServer(str(sock), Handler)
    os.chmod(sock, 0o600)
    print(json.dumps({"service": "omega-local-effect-adapter", "socket": str(sock), "machine_id": EXPECTED_MACHINE, "owner": EXPECTED_OWNER}), flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        try:
            sock.unlink()
        except FileNotFoundError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
