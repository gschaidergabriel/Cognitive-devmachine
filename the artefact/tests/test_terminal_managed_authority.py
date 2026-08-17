from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path

from clayverse.terminal_sessions import TerminalSessionManager


class _Completed:
    returncode = 0
    stderr = ""


def test_managed_policy_excludes_unmanaged_hooks_permissions_and_auto_memory():
    root = Path(__file__).parents[1]
    settings = json.loads((root / "policy" / "managed-settings.json").read_text())
    managed_mcp = json.loads((root / "policy" / "managed-mcp.json").read_text())

    assert settings["allowManagedHooksOnly"] is True
    assert settings["allowManagedPermissionRulesOnly"] is True
    assert settings["permissions"]["disableBypassPermissionsMode"] == "disable"
    assert settings["autoMemoryEnabled"] is False
    assert list(managed_mcp["mcpServers"]) == ["clayverse"]
    server = managed_mcp["mcpServers"]["clayverse"]
    assert server["command"] == "/usr/local/bin/python"
    assert server["args"] == ["-m", "clayverse.mcp_server"]


def test_enabled_entityos_authority_reaches_only_sanitized_terminal_environment(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "1")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", "/opt/entityos/EntityOS")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", "ab" * 32)
    monkeypatch.setenv("CLERK_JWT_KEY", "must-not-leak")
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        return _Completed()

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager.ensure("gabriel")

    argv = shlex.split(calls[-1][-1])
    assert argv[:2] == ["env", "-i"]
    assert "CLAYVERSE_ENABLE_ENTITYOS_EXEC=1" in argv
    assert "CLAYVERSE_ENTITYOS_PATH=/opt/entityos/EntityOS" in argv
    assert "CLAYVERSE_ENTITYOS_SHA256=" + "ab" * 32 in argv
    assert "CLAUDE_CODE_DISABLE_AUTO_MEMORY=1" in argv
    assert "CLAUDE_CODE_DISABLE_CLAUDE_MDS=1" in argv
    assert not any(item.startswith("CLERK_JWT_KEY=") for item in argv)
