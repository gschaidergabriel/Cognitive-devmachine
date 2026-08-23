from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_entityos_runtime_identity_is_image_owned_only():
    service = (ROOT / "clayverse" / "service.py").read_text(encoding="utf-8")
    mcp_server = (ROOT / "clayverse" / "mcp_server.py").read_text(encoding="utf-8")
    terminal_sessions = (ROOT / "clayverse" / "terminal_sessions.py").read_text(encoding="utf-8")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    kata = (ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml").read_text(encoding="utf-8")

    assert '_ENTITYOS_PATH = "/opt/entityos/EntityOS"' in service
    assert '_ENTITYOS_LOCK_PATH = "/opt/entityos/entityos.lock.json"' in service
    assert 'from .service import _entityos_config' in mcp_server

    for source in (service, mcp_server, terminal_sessions):
        assert 'os.environ.get("CLAYVERSE_ENTITYOS_PATH"' not in source
        assert 'os.environ.get("CLAYVERSE_ENTITYOS_SHA256"' not in source

    assert "CLAYVERSE_ENTITYOS_PATH" not in terminal_sessions
    assert "CLAYVERSE_ENTITYOS_SHA256" not in terminal_sessions
    assert "CLAYVERSE_ENTITYOS_PATH=" not in dockerfile
    assert "CLAYVERSE_ENTITYOS_SHA256=" not in dockerfile
    assert "ARG ENTITYOS_SHA256" in dockerfile
    assert 'test "${ENTITYOS_SHA256}" = "$LOCK_SHA256"' in dockerfile
    assert "+os.environ.get('PORT','3000')+'/readyz'" in dockerfile

    assert "CLAYVERSE_ENTITYOS_PATH:" not in compose
    assert "CLAYVERSE_ENTITYOS_SHA256:" not in compose
    assert "- name: CLAYVERSE_ENTITYOS_PATH" not in kata
    assert "- name: CLAYVERSE_ENTITYOS_SHA256" not in kata


def test_runtime_can_only_toggle_embedded_entityos_execution():
    terminal_sessions = (ROOT / "clayverse" / "terminal_sessions.py").read_text(encoding="utf-8")
    mcp_server = (ROOT / "clayverse" / "mcp_server.py").read_text(encoding="utf-8")

    assert '"CLAYVERSE_ENABLE_ENTITYOS_EXEC": "1" if enable_entityos else "0"' in terminal_sessions
    assert "effect_env = [f\"CLAYVERSE_ENABLE_ENTITYOS_EXEC=" in terminal_sessions
    assert 'enable_exec = os.environ.get("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0") == "1"' in mcp_server
    assert "image-owned EntityOS admission" in mcp_server
