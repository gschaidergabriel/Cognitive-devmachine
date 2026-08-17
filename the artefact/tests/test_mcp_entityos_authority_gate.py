import os

import pytest

from clayverse.mcp_server import BridgeStateError, ClayVerseEffectBridge
from clayverse.terminal_sessions import TerminalSessionManager


def _base_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(tmp_path / "state"))
    monkeypatch.setenv("CLAYVERSE_USER_ID", "gabriel")
    monkeypatch.setenv("CLAYVERSE_SESSION_ID", "session:gabriel")


def test_terminal_mcp_env_does_not_disclose_entityos_reference_when_exec_disabled(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", "/opt/entityos/EntityOS")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", "a" * 64)
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")

    env = manager._mcp_env(manager.binding("gabriel"))

    assert env["CLAYVERSE_ENABLE_ENTITYOS_EXEC"] == "0"
    assert "CLAYVERSE_ENTITYOS_PATH" not in env
    assert "CLAYVERSE_ENTITYOS_SHA256" not in env


def test_mcp_does_not_infer_entityos_authority_from_path_and_digest(monkeypatch, tmp_path):
    _base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", "/opt/entityos/EntityOS")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", "b" * 64)

    import clayverse.entityos_bridge as entityos_bridge

    class MustNotConstruct:
        def __init__(self, *args, **kwargs):
            raise AssertionError("disabled EntityOS bridge was constructed")

    monkeypatch.setattr(entityos_bridge, "EntityOSBridge", MustNotConstruct)
    bridge = ClayVerseEffectBridge.from_env()
    try:
        assert bridge.session_state()["capabilities"] == ("state.noop",)
    finally:
        bridge.db.close()


def test_mcp_exec_gate_requires_complete_entityos_configuration(monkeypatch, tmp_path):
    _base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "1")
    monkeypatch.delenv("CLAYVERSE_ENTITYOS_PATH", raising=False)
    monkeypatch.delenv("CLAYVERSE_ENTITYOS_SHA256", raising=False)

    with pytest.raises(BridgeStateError, match="execution enabled but configuration is incomplete"):
        ClayVerseEffectBridge.from_env()


def test_mcp_exec_gate_constructs_verified_bridge_only_when_enabled(monkeypatch, tmp_path):
    _base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "1")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", "/opt/entityos/EntityOS")
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", "c" * 64)

    import clayverse.entityos_bridge as entityos_bridge

    seen = {}

    class FakeBridge:
        def __init__(self, path, sha256):
            seen["path"] = path
            seen["sha256"] = sha256

        def verify(self):
            seen["verified"] = True
            return {"ok": True}

    monkeypatch.setattr(entityos_bridge, "EntityOSBridge", FakeBridge)
    bridge = ClayVerseEffectBridge.from_env()
    try:
        assert seen == {
            "path": "/opt/entityos/EntityOS",
            "sha256": "c" * 64,
            "verified": True,
        }
        assert "entityos.exec" in bridge.session_state()["capabilities"]
    finally:
        bridge.db.close()
