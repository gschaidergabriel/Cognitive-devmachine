from clayverse.terminal_sessions import TerminalSessionManager


def test_disabled_entityos_execution_omits_artifact_reference_from_mcp_config(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", "/opt/entityos/EntityOS")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", "a" * 64)
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")

    env = manager._mcp_env(manager.binding("gabriel"))

    assert env["CLAYVERSE_ENABLE_ENTITYOS_EXEC"] == "0"
    assert "CLAYVERSE_ENTITYOS_PATH" not in env
    assert "CLAYVERSE_ENTITYOS_SHA256" not in env


def test_enabled_entityos_execution_forwards_digest_binding(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "1")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", "/opt/entityos/EntityOS")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", "b" * 64)
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")

    env = manager._mcp_env(manager.binding("andreas"))

    assert env["CLAYVERSE_ENABLE_ENTITYOS_EXEC"] == "1"
    assert env["CLAYVERSE_ENTITYOS_PATH"] == "/opt/entityos/EntityOS"
    assert env["CLAYVERSE_ENTITYOS_SHA256"] == "b" * 64
