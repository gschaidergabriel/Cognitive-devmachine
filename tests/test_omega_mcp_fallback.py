from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import omega_chatgpt_mcp_fallback as fb  # noqa: E402


def _ok(payload):
    return fb.base._text_result(payload, is_error=False)


def test_tools_include_transport_diagnostic():
    names = {t["name"] for t in fb.TOOLS}
    assert "omega_transport_status" in names
    status = next(t for t in fb.TOOLS if t["name"] == "omega_status")
    assert status["inputSchema"]["properties"]["transport"]["enum"] == ["auto", "direct", "local", "github"]


def test_status_prefers_direct_broker(monkeypatch):
    monkeypatch.setattr(fb, "_direct_status", lambda person: {"ok": True, "state": "PASS", "person": person, "machine_id": "ai-core-node", "owner": "gabriel", "transport_used": "direct_host_broker"})
    monkeypatch.setattr(fb, "_local_eligible", lambda person: True)
    monkeypatch.setattr(fb, "_local_call", lambda *a, **k: (_ for _ in ()).throw(AssertionError("local should not run")))
    result = fb.call_tool("omega_status", {"person": "gabriel"}, rpc_id="s1")
    assert result["isError"] is False
    p = result["structuredContent"]
    assert p["transport_used"] == "direct_host_broker"
    assert p["fallback_used"] is False


def test_status_falls_direct_to_local(monkeypatch):
    monkeypatch.setattr(fb, "_direct_status", lambda person: (_ for _ in ()).throw(fb.FallbackUnavailable("down")))
    monkeypatch.setattr(fb, "_local_eligible", lambda person: True)
    monkeypatch.setattr(fb, "_local_call", lambda *a, **k: {"ok": True, "state": "PASS", "person": "gabriel", "machine_id": "ai-core-node", "owner": "gabriel", "transport_used": "local_unix_engine"})
    result = fb.call_tool("omega_status", {"person": "gabriel"}, rpc_id="s2")
    p = result["structuredContent"]
    assert p["transport_used"] == "local_unix_engine"
    assert p["fallback_used"] is True
    assert [x["transport"] for x in p["transport_attempts"]] == ["direct_host_broker", "local_unix_engine"]


def test_status_falls_to_github_when_direct_and_local_unavailable(monkeypatch):
    monkeypatch.setattr(fb, "_direct_status", lambda person: (_ for _ in ()).throw(fb.FallbackUnavailable("direct down")))
    monkeypatch.setattr(fb, "_local_eligible", lambda person: True)
    monkeypatch.setattr(fb, "_local_call", lambda *a, **k: (_ for _ in ()).throw(fb.FallbackUnavailable("local down")))
    monkeypatch.setattr(fb, "_BASE_CALL_TOOL", lambda name, args, rpc_id=None: _ok({"ok": True, "state": "PASS", "person": "gabriel", "machine_id": "ai-core-node", "owner": "gabriel"}))
    result = fb.call_tool("omega_status", {"person": "gabriel"}, rpc_id="s3")
    p = result["structuredContent"]
    assert p["transport_used"] == "github_local_bridge"
    assert p["fallback_used"] is True
    assert len(p["transport_attempts"]) == 3


def test_gabriel_effect_prefers_local_and_never_calls_github_after_accept(monkeypatch):
    monkeypatch.setattr(fb, "_local_eligible", lambda person: True)
    monkeypatch.setattr(fb, "_local_call", lambda *a, **k: {"ok": True, "state": "PASS", "person": "gabriel", "machine_id": "ai-core-node", "owner": "gabriel", "command_id": "local-1", "transport_used": "local_unix_engine"})
    monkeypatch.setattr(fb, "_BASE_CALL_TOOL", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not duplicate through github")))
    result = fb.call_tool("omega_execute", {"person": "gabriel", "command": "printf ok"}, rpc_id="e1")
    p = result["structuredContent"]
    assert p["state"] == "PASS"
    assert p["transport_used"] == "local_unix_engine"


def test_local_unknown_outcome_never_double_dispatches(monkeypatch):
    monkeypatch.setattr(fb, "_local_eligible", lambda person: True)
    monkeypatch.setattr(fb, "_local_call", lambda *a, **k: {"ok": False, "state": "UNKNOWN_LOCAL_OUTCOME", "person": "gabriel", "machine_id": "ai-core-node", "owner": "gabriel", "command_id": "local-unknown", "transport_used": "local_unix_engine"})
    monkeypatch.setattr(fb, "_BASE_CALL_TOOL", lambda *a, **k: (_ for _ in ()).throw(AssertionError("unknown outcome must not be replayed")))
    result = fb.call_tool("omega_execute", {"person": "gabriel", "command": "printf maybe"}, rpc_id="e2")
    assert result["structuredContent"]["state"] == "UNKNOWN_LOCAL_OUTCOME"


def test_effect_falls_to_github_only_on_pre_dispatch_local_unavailable(monkeypatch):
    monkeypatch.setattr(fb, "_local_eligible", lambda person: True)
    monkeypatch.setattr(fb, "_local_call", lambda *a, **k: (_ for _ in ()).throw(fb.FallbackUnavailable("socket missing")))
    monkeypatch.setattr(fb, "_BASE_CALL_TOOL", lambda name, args, rpc_id=None: _ok({"ok": True, "state": "PASS", "person": "gabriel", "machine_id": "ai-core-node", "owner": "gabriel", "command_id": "github-1"}))
    result = fb.call_tool("omega_execute", {"person": "gabriel", "command": "printf ok"}, rpc_id="e3")
    p = result["structuredContent"]
    assert p["transport_used"] == "github_local_bridge"
    assert p["fallback_used"] is True


def test_andreas_effect_stays_on_verified_github_plane(monkeypatch):
    monkeypatch.setattr(fb, "_local_eligible", lambda person: False)
    monkeypatch.setattr(fb, "_BASE_CALL_TOOL", lambda name, args, rpc_id=None: _ok({"ok": True, "state": "PASS", "person": "andreas", "machine_id": "andreas-maco", "owner": "andreas"}))
    result = fb.call_tool("omega_execute", {"person": "andreas", "command": "printf ok"}, rpc_id="a1")
    p = result["structuredContent"]
    assert p["transport_used"] == "github_local_bridge"


def test_direct_transport_refuses_effects():
    result = fb.call_tool("omega_execute", {"person": "gabriel", "command": "printf x", "transport": "direct"}, rpc_id="e4")
    assert result["isError"] is True
    assert result["structuredContent"]["error"] == "DIRECT_EFFECT_UNSUPPORTED"


def test_transport_status_never_needs_effect_dispatch(monkeypatch):
    monkeypatch.setattr(fb, "_direct_cfg", lambda p: None)
    monkeypatch.setattr(fb, "_local_eligible", lambda p: False)
    result = fb.call_tool("omega_transport_status", {"person": "gabriel"}, rpc_id="d1")
    assert result["isError"] is False
    p = result["structuredContent"]
    assert "github_control_plane_configured" in p
    assert p["people"]["gabriel"]["local_adapter_eligible"] is False
