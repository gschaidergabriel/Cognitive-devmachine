from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import omega_chatgpt_mcp as mcp  # noqa: E402


def _receipt(command: dict, *, status: str = "PASS", machine_id: str | None = None, owner: str | None = None):
    person = "gabriel" if command["owner"] == "gabriel" else "andreas"
    target = mcp.relay.ORGAN[mcp.PERSON_TO_ORGAN[person]]
    return {
        "schema": "CLAY_LOCAL_RECEIPT/v1",
        "command_id": command["command_id"],
        "machine_id": machine_id or target["machine_id"],
        "owner": owner or target["owner"],
        "op": command["op"],
        "command_sha256": mcp.relay.command_sha256(mcp.relay.serialized_local_command(command)),
        "status": status,
        "exit_code": 0 if status == "PASS" else 1,
        "errors": [],
        "execution_boundary": "REAL_LOCAL_HOST_TEST",
        "stdout_tail": "ok",
    }


def _bridge_harness(monkeypatch):
    queued: list[tuple[str, str, dict]] = []

    def put_new(branch: str, path: str, content: bytes, message: str):
        command = json.loads(content.decode())
        queued.append((branch, path, command))
        return True

    def wait_file(branch: str, path: str, timeout_s: float = 0.0):
        assert queued
        return json.dumps(_receipt(queued[-1][2])).encode()

    monkeypatch.setattr(mcp.relay, "put_new", put_new)
    monkeypatch.setattr(mcp.relay, "wait_file", wait_file)
    return queued


def test_initialize_and_tool_list_expose_real_bridge_surface():
    init = mcp.handle_rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": mcp.PROTOCOL_VERSION}})
    assert init["result"]["serverInfo"]["name"] == "omega-frankenstein-bridge"
    listed = mcp.handle_rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    names = {tool["name"] for tool in listed["result"]["tools"]}
    assert names == {"omega_status", "omega_read", "omega_execute", "omega_write_text", "omega_screenshot", "omega_receipt"}
    exec_tool = next(t for t in listed["result"]["tools"] if t["name"] == "omega_execute")
    assert exec_tool["annotations"]["destructiveHint"] is True
    assert exec_tool["annotations"]["readOnlyHint"] is False


def test_status_routes_gabriel_to_exact_machine_owner(monkeypatch):
    queued = _bridge_harness(monkeypatch)
    result = mcp.call_tool("omega_status", {"person": "gabriel", "wait_seconds": 1}, rpc_id="abc")
    assert result["isError"] is False
    payload = result["structuredContent"]
    assert payload["ok"] is True
    assert payload["machine_id"] == "ai-core-node"
    assert payload["owner"] == "gabriel"
    branch, path, command = queued[0]
    assert branch == "chatgpt-local-ai-core-node-control"
    assert path.startswith("local_bridge/commands/")
    assert command["op"] == "status"
    assert command["machine_id"] == "ai-core-node"
    assert command["owner"] == "gabriel"


def test_status_routes_andreas_to_exact_machine_owner(monkeypatch):
    queued = _bridge_harness(monkeypatch)
    result = mcp.call_tool("omega_status", {"person": "andreas", "wait_seconds": 1}, rpc_id="xyz")
    assert result["isError"] is False
    payload = result["structuredContent"]
    assert payload["machine_id"] == "andreas-maco"
    assert payload["owner"] == "andreas"
    assert queued[0][0] == "chatgpt-local-andreas-maco-control"


def test_effects_fail_closed_until_gateway_explicitly_enables_them(monkeypatch):
    monkeypatch.delenv("OMEGA_MCP_EFFECTS_ENABLED", raising=False)
    result = mcp.call_tool("omega_execute", {"person": "gabriel", "command": "printf hi"}, rpc_id=3)
    assert result["isError"] is True
    assert result["structuredContent"]["error"] == "EFFECTS_DISABLED"


def test_execute_reuses_alignment_guard_and_denies_delete(monkeypatch):
    monkeypatch.setenv("OMEGA_MCP_EFFECTS_ENABLED", "1")
    result = mcp.call_tool("omega_execute", {"person": "gabriel", "command": "rm -rf /tmp/omega-nope"}, rpc_id=4)
    assert result["isError"] is True
    assert result["structuredContent"]["error"] == "DELETE_REMOVAL_DENIED"


def test_execute_reuses_alignment_guard_and_denies_storage_format(monkeypatch):
    monkeypatch.setenv("OMEGA_MCP_EFFECTS_ENABLED", "1")
    result = mcp.call_tool("omega_execute", {"person": "andreas", "command": "mkfs.ext4 /dev/sdb"}, rpc_id=5)
    assert result["isError"] is True
    assert result["structuredContent"]["error"] == "STORAGE_FORMAT_DENIED"


def test_enabled_execute_returns_only_verified_real_receipt(monkeypatch):
    monkeypatch.setenv("OMEGA_MCP_EFFECTS_ENABLED", "1")
    queued = _bridge_harness(monkeypatch)
    result = mcp.call_tool(
        "omega_execute",
        {"person": "gabriel", "command": "printf hello", "cwd": "/tmp", "timeout_seconds": 30, "wait_seconds": 1},
        rpc_id="exec-1",
    )
    assert result["isError"] is False
    payload = result["structuredContent"]
    assert payload["ok"] is True
    assert payload["state"] == "PASS"
    command = queued[0][2]
    assert command["op"] == "exec"
    assert command["command"] == "printf hello"
    assert command["cwd"] == "/tmp"


def test_receipt_identity_mismatch_is_hard_error(monkeypatch):
    queued = []

    def put_new(branch: str, path: str, content: bytes, message: str):
        queued.append(json.loads(content.decode()))
        return True

    def wait_file(branch: str, path: str, timeout_s: float = 0.0):
        return json.dumps(_receipt(queued[-1], machine_id="andreas-maco", owner="andreas")).encode()

    monkeypatch.setattr(mcp.relay, "put_new", put_new)
    monkeypatch.setattr(mcp.relay, "wait_file", wait_file)
    result = mcp.call_tool("omega_status", {"person": "gabriel", "wait_seconds": 1}, rpc_id=6)
    assert result["isError"] is True
    assert result["structuredContent"]["error"] == "RECEIPT_IDENTITY_MISMATCH"


def test_receipt_digest_mismatch_is_hard_error(monkeypatch):
    queued = []

    def put_new(branch: str, path: str, content: bytes, message: str):
        queued.append(json.loads(content.decode()))
        return True

    def wait_file(branch: str, path: str, timeout_s: float = 0.0):
        receipt = _receipt(queued[-1])
        receipt["command_sha256"] = "0" * 64
        return json.dumps(receipt).encode()

    monkeypatch.setattr(mcp.relay, "put_new", put_new)
    monkeypatch.setattr(mcp.relay, "wait_file", wait_file)
    result = mcp.call_tool("omega_status", {"person": "gabriel", "wait_seconds": 1}, rpc_id=8)
    assert result["isError"] is True
    assert result["structuredContent"]["error"] == "RECEIPT_COMMAND_DIGEST_MISMATCH"


def test_receipt_op_mismatch_is_hard_error(monkeypatch):
    queued = []

    def put_new(branch: str, path: str, content: bytes, message: str):
        queued.append(json.loads(content.decode()))
        return True

    def wait_file(branch: str, path: str, timeout_s: float = 0.0):
        receipt = _receipt(queued[-1])
        receipt["op"] = "exec" if queued[-1]["op"] != "exec" else "status"
        return json.dumps(receipt).encode()

    monkeypatch.setattr(mcp.relay, "put_new", put_new)
    monkeypatch.setattr(mcp.relay, "wait_file", wait_file)
    result = mcp.call_tool("omega_status", {"person": "andreas", "wait_seconds": 1}, rpc_id=9)
    assert result["isError"] is True
    assert result["structuredContent"]["error"] == "RECEIPT_OP_MISMATCH"


def test_unknown_person_never_falls_back_to_other_host():
    result = mcp.call_tool("omega_status", {"person": "someone"}, rpc_id=7)
    assert result["isError"] is True
    assert result["structuredContent"]["error"] == "UNKNOWN_PERSON"


def test_mcp_auth_requires_configured_bearer(monkeypatch):
    monkeypatch.setenv("OMEGA_MCP_TOKEN", "secret-123")
    assert mcp._authorized("Bearer secret-123") is True
    assert mcp._authorized("Bearer wrong") is False
    assert mcp._authorized(None) is False
