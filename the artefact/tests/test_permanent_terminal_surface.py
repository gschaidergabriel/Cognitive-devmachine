import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

import clayverse.terminal_sessions as terminal_sessions
from clayverse.store import UnifiedDB
from clayverse.terminal_gateway import create_terminal_app
from clayverse.terminal_sessions import CANONICAL_TERMINALS, TerminalSessionManager


ROOT = Path(__file__).resolve().parents[1]


def test_exactly_two_canonical_terminal_perspectives():
    assert CANONICAL_TERMINALS == {
        "gabriel": "clayverse-gabriel",
        "andreas": "clayverse-andreas",
    }


def test_diagnostic_mcp_mirror_binds_one_session_and_no_other_user(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0")
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    g = manager.binding("gabriel")
    a = manager.binding("andreas")
    manager._write_mcp_config(g)
    manager._write_mcp_config(a)
    gp = json.loads(g.mcp_config.read_text())
    ap = json.loads(a.mcp_config.read_text())
    ge = gp["mcpServers"]["clayverse"]["env"]
    ae = ap["mcpServers"]["clayverse"]["env"]
    assert ge["CLAYVERSE_USER_ID"] == "gabriel"
    assert ge["CLAYVERSE_SESSION_ID"] == "session:gabriel"
    assert ae["CLAYVERSE_USER_ID"] == "andreas"
    assert ae["CLAYVERSE_SESSION_ID"] == "session:andreas"
    assert ge["PYTHONPATH"] == "/opt/clayverse"
    assert gp["mcpServers"]["clayverse"]["command"] == "/usr/local/bin/python"
    assert a.home != g.home
    assert a.mcp_config != g.mcp_config


def test_product_claude_process_is_interactive_and_uses_only_managed_mcp(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: None)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    manager.ensure("gabriel")
    # The claude launch is embedded as a flat argv list inside the tmux
    # new-session call, not a single joined shell string -- match the list
    # membership pattern used by the sibling test in
    # test_terminal_managed_authority.py::test_enabled_entityos_authority_*.
    creation = next(argv for argv in calls if "new-session" in argv)
    assert "claude" in creation
    assert "-p" not in creation
    assert "--no-session-persistence" not in creation
    assert "--mcp-config" not in creation
    assert "--strict-mcp-config" not in creation
    assert not any("clayverse-mcp.json" in item for item in creation)
    assert "--tools" in creation and creation[creation.index("--tools") + 1] == ""
    assert "mcp__clayverse__session_state" in creation
    assert "mcp__clayverse__request_effect" in creation
    assert "mcp__clayverse__*" not in creation
    assert "--append-system-prompt-file" in creation
    assert any("/etc/claude-code/managed-settings.json" in item for item in creation)


def test_managed_mcp_is_exclusive_and_command_bound():
    mcp = json.loads((ROOT / "policy" / "managed-mcp.json").read_text())
    settings = json.loads((ROOT / "policy" / "managed-settings.json").read_text())
    assert set(mcp["mcpServers"]) == {"clayverse"}
    server = mcp["mcpServers"]["clayverse"]
    expected_command = [server["command"], *server.get("args", [])]
    assert settings["allowManagedMcpServersOnly"] is True
    assert settings["allowedMcpServers"] == [{"serverCommand": expected_command}]


def test_service_source_uses_terminal_gateway_not_custom_chat_engine():
    source = (ROOT / "clayverse" / "service.py").read_text()
    assert "create_terminal_app" in source
    assert "TerminalSessionManager" in source
    assert "ClaudeCodeInference" not in source
    assert "ClayVerseAPI" not in source
    assert "ClayVerseEngine" not in source
    assert "from .clerk_auth import" in source


def test_browser_surface_is_terminal_not_textarea_chat():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text()
    assert "WebSocket" in source
    assert "Terminal(" in source
    assert "/ws/terminal" in source
    assert "/api/chat" not in source
    assert "textarea" not in source.lower()
    assert "from .clerk_auth import" in source


def test_browser_terminal_io_waits_for_authenticated_ready_frame():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text()
    assert "let terminalReady=false; let authRefreshTimer=null;" in source
    assert "if(m.type==='ready'){{scheduleAuthRefresh(m.auth_expires_at);}}" in source
    assert "if(m.type==='ready'){{terminalReady=true;term.focus();return;}}" in source
    assert "if(m.type==='reauthenticated'){{scheduleAuthRefresh(m.auth_expires_at);return;}}" in source
    assert "Clerk.session.getToken({{skipCache:true}})" in source
    assert "type:'reauth'" in source
    assert "if(!terminalReady||ws.readyState!==1)return;" in source
    assert "offset+=maxInputFrameBytes" in source
    assert "encoded.slice(offset,offset+maxInputFrameBytes)" in source
    assert "if(terminalReady&&ws.readyState===1) ws.send(JSON.stringify({{type:'resize'" in source
    assert "ws.addEventListener('close',()=>{{if(authRefreshTimer)clearTimeout(authRefreshTimer);}});" in source
    assert source.index("type:'auth'") < source.index("term.onData")


class _RejectVerifier:
    def verify(self, token):
        raise RuntimeError("expected-auth-reject")


def test_terminal_websocket_is_injected_before_auth_processing(tmp_path):
    db = UnifiedDB(tmp_path / "state" / "unified.db")
    try:
        app = create_terminal_app(
            db=db,
            clerk_map={},
            verifier=_RejectVerifier(),
            state_root=tmp_path / "state",
            publishable_key="pk_test_browser_gate",
            frontend_api_url="https://clerk.invalid",
        )
        with TestClient(app) as client:
            with client.websocket_connect("/ws/terminal") as websocket:
                websocket.send_text(json.dumps({
                    "type": "auth",
                    "token": "rejected-token",
                    "rows": 24,
                    "cols": 80,
                }))
                message = websocket.receive_json()
        assert message == {"type": "error", "message": "expected-auth-reject"}
    finally:
        db.close()
