import json
from pathlib import Path
from types import SimpleNamespace

import clayverse.terminal_sessions as terminal_sessions
from clayverse.terminal_sessions import CANONICAL_TERMINALS, TerminalSessionManager


ROOT = Path(__file__).resolve().parents[1]


def test_exactly_two_canonical_terminal_perspectives():
    assert CANONICAL_TERMINALS == {
        "gabriel": "clayverse-gabriel",
        "andreas": "clayverse-andreas",
    }


def test_per_user_mcp_config_binds_one_session_and_no_other_user(tmp_path, monkeypatch):
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
    assert a.home != g.home
    assert a.mcp_config != g.mcp_config


def test_product_claude_process_is_interactive_not_headless(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(terminal_sessions.subprocess, "run", fake_run)
    manager.ensure("gabriel")
    command = calls[-1][-1]
    assert "claude" in command
    assert " -p " not in f" {command} "
    assert "--no-session-persistence" not in command
    assert "--strict-mcp-config" in command
    assert "--tools ''" in command or '--tools ""' in command
    assert "mcp__clayverse__*" in command
    assert "--append-system-prompt-file" in command


def test_service_source_uses_terminal_gateway_not_custom_chat_engine():
    source = (ROOT / "clayverse" / "service.py").read_text()
    assert "create_terminal_app" in source
    assert "TerminalSessionManager" in source
    assert "ClaudeCodeInference" not in source
    assert "ClayVerseAPI" not in source
    assert "ClayVerseEngine" not in source


def test_browser_surface_is_terminal_not_textarea_chat():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text()
    assert "WebSocket" in source
    assert "Terminal(" in source
    assert "/ws/terminal" in source
    assert "/api/chat" not in source
    assert "textarea" not in source.lower()
