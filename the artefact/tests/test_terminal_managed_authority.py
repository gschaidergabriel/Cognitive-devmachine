from __future__ import annotations

import json
import subprocess
from pathlib import Path

from clayverse.terminal_sessions import TerminalSessionManager


class _Completed:
    returncode = 0
    stderr = ""
    stdout = ""


def test_managed_policy_excludes_unmanaged_hooks_permissions_and_auto_memory():
    root = Path(__file__).parents[1]
    settings = json.loads((root / "policy" / "managed-settings.json").read_text())
    managed_mcp = json.loads((root / "policy" / "managed-mcp.json").read_text())
    source_lock = json.loads((root / "SOURCE_LOCK.json").read_text())
    assert settings["allowManagedHooksOnly"] is True
    assert settings["allowManagedPermissionRulesOnly"] is True
    assert settings["allowManagedMcpServersOnly"] is True
    assert settings["allowedChannelPlugins"] == []
    assert settings["allowedMcpServers"] == [{"serverCommand": ["/usr/local/bin/python", "-m", "clayverse.mcp_server"]}]
    assert settings["permissions"]["disableBypassPermissionsMode"] == "disable"
    assert settings["permissions"]["deny"] == ["Bash", "Artifact"]
    assert settings["autoMemoryEnabled"] is False
    assert settings["channelsEnabled"] is False
    assert settings["crossSessionInbound"] == "refuse"
    assert settings["disableAgentView"] is True
    assert settings["disableArtifact"] is True
    assert settings["disableAutoMode"] == "disable"
    assert settings["disableBundledSkills"] is True
    assert settings["disableClaudeAiConnectors"] is True
    assert settings["disableDeepLinkRegistration"] == "disable"
    assert settings["disableRemoteControl"] is True
    assert settings["disableSideloadFlags"] is True
    assert settings["disableSkillShellExecution"] is True
    assert settings["disableWorkflows"] is True
    assert settings["isolatePeerMachines"] is True
    assert settings["strictKnownMarketplaces"] == []
    assert settings["env"]["CLAUDE_CODE_DISABLE_ATTACHMENTS"] == "1"
    assert settings["env"]["CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"] == "1"
    assert settings["env"]["CLAUDE_CODE_DISABLE_CRON"] == "1"
    assert settings["env"]["CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS"] == "1"
    assert settings["env"]["CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL"] == "1"
    assert settings["env"]["CLAUDE_CODE_SHELL_PREFIX"] == "/opt/clayverse/runtime/deny-shell"
    assert tuple(int(part) for part in source_lock["claude_code"]["version"].split(".")) >= (2, 1, 224)
    assert list(managed_mcp["mcpServers"]) == ["clayverse"]
    server = managed_mcp["mcpServers"]["clayverse"]
    assert server["command"] == "/usr/local/bin/python"
    assert server["args"] == ["-m", "clayverse.mcp_server"]


def test_enabled_entityos_authority_reaches_only_sanitized_terminal_environment(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    monkeypatch.setattr(manager, "_require_programs", lambda: None)
    monkeypatch.setattr(manager, "_has_session", lambda binding: False)
    monkeypatch.setattr(manager, "_enforce_tmux_policy", lambda binding: None)
    monkeypatch.setattr(manager, "_assert_tmux_server_policy", lambda binding: None)
    monkeypatch.setattr(manager, "_attest_existing_session", lambda binding: True)
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "1")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", "/opt/entityos/EntityOS")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", "ab" * 32)
    monkeypatch.setenv("CLERK_JWT_KEY", "must-not-leak")
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        return _Completed()

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager.ensure("gabriel")

    creation = next(argv for argv in calls if "new-session" in argv)
    env_index = creation.index("env")
    argv = creation[env_index:]
    assert argv[:2] == ["env", "-i"]
    assert all(not item.startswith("env -i ") for item in creation)
    assert "CLAYVERSE_ENABLE_ENTITYOS_EXEC=1" in argv
    assert "CLAYVERSE_ENTITYOS_PATH=/opt/entityos/EntityOS" in argv
    assert "CLAYVERSE_ENTITYOS_SHA256=" + "ab" * 32 in argv
    assert "DISABLE_UPDATES=1" in argv
    assert "CLAUDE_CODE_DISABLE_AUTO_MEMORY=1" in argv
    assert "CLAUDE_CODE_DISABLE_CLAUDE_MDS=1" in argv
    assert "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1" in argv
    assert "CLAUDE_CODE_SHELL_PREFIX=/opt/clayverse/runtime/deny-shell" in argv
    assert "--setting-sources" in argv and argv[argv.index("--setting-sources") + 1] == ""
    assert "--tools" in argv and argv[argv.index("--tools") + 1] == ""
    assert "mcp__clayverse__session_state" in argv
    assert "mcp__clayverse__request_effect" in argv
    assert "mcp__clayverse__*" not in argv
    assert "--remote-control" not in argv
    assert "--bg" not in argv
    assert not any(item.startswith("CLERK_JWT_KEY=") for item in argv)


def test_direct_shell_guard_fails_closed_without_executing_payload(tmp_path):
    root = Path(__file__).parents[1]
    guard = root / "policy" / "deny-shell"
    marker = tmp_path / "must-not-exist"
    cp = subprocess.run(["/bin/sh", str(guard), f"touch {marker}"], capture_output=True, text=True, check=False)
    assert cp.returncode == 126
    assert cp.stdout == ""
    assert "direct shell execution is disabled" in cp.stderr
    assert not marker.exists()


def test_container_embeds_root_owned_executable_shell_guard():
    root = Path(__file__).parents[1]
    dockerfile = (root / "Dockerfile").read_text()
    assert "COPY --chown=root:root policy/deny-shell /opt/clayverse/runtime/deny-shell" in dockerfile
    assert "chown -R root:root /opt/clayverse" in dockerfile
    assert "chmod -R a-w /opt/clayverse" in dockerfile
    assert "chmod 0555 /opt/clayverse/runtime/deny-shell" in dockerfile
