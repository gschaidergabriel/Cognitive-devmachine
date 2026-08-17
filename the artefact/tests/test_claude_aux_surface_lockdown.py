import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _settings() -> dict:
    return json.loads((ROOT / "policy" / "managed-settings.json").read_text(encoding="utf-8"))


def test_claude_auxiliary_control_surfaces_fail_closed():
    settings = _settings()
    assert settings["channelsEnabled"] is False
    assert settings["allowedChannelPlugins"] == []
    assert settings["crossSessionInbound"] == "refuse"
    assert settings["disableAgentView"] is True
    assert settings["disableArtifact"] is True
    assert settings["disableAutoMode"] == "disable"
    assert settings["disableBundledSkills"] is True
    assert settings["disableClaudeAiConnectors"] is True
    assert settings["disableDeepLinkRegistration"] == "disable"
    assert settings["disableRemoteControl"] is True
    assert settings["disableSideloadFlags"] is True
    assert settings["disableWorkflows"] is True
    assert settings["isolatePeerMachines"] is True


def test_noncanonical_scheduler_and_context_side_inputs_are_disabled():
    env = _settings()["env"]
    assert env["CLAUDE_CODE_DISABLE_ATTACHMENTS"] == "1"
    assert env["CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"] == "1"
    assert env["CLAUDE_CODE_DISABLE_CRON"] == "1"
    assert env["CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS"] == "1"
    assert env["CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL"] == "1"


def test_pinned_claude_version_supports_cross_session_lockdown_contract():
    lock = json.loads((ROOT / "SOURCE_LOCK.json").read_text(encoding="utf-8"))
    version = lock["claude_code"]["version"]
    parts = tuple(int(part) for part in version.split("."))
    # crossSessionInbound/isolatePeerMachines require Claude Code >= 2.1.224;
    # all other managed controls asserted above have equal or older version gates.
    assert parts >= (2, 1, 224)


def test_product_launch_keeps_filesystem_setting_sources_and_builtin_tools_off():
    source = (ROOT / "clayverse" / "terminal_sessions.py").read_text(encoding="utf-8")
    assert '"--setting-sources", ""' in source
    assert '"--tools", ""' in source
    assert '"--allowedTools", "mcp__clayverse__*"' in source
    assert '"--permission-mode", "dontAsk"' in source
    assert "--remote-control" not in source
    assert '"--bg"' not in source
