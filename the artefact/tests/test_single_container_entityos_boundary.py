from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_baseline_container_has_no_mandatory_entityos_runtime_sidecar():
    dockerfile = (ROOT / "Dockerfile").read_text()
    compose = (ROOT / "compose.yaml").read_text()

    assert "CLAYVERSE_REQUIRE_ENTITYOS=0" in dockerfile
    assert 'CLAYVERSE_REQUIRE_ENTITYOS: "0"' in compose
    assert "CLAYVERSE_ENTITYOS_HOST_PATH" not in compose
    assert "/opt/entityos/EntityOS:ro" not in compose


def test_future_entityos_staging_input_is_not_a_source_history_artifact():
    ignore = (ROOT / ".gitignore").read_text().splitlines()
    assert "/EntityOS" in ignore
    assert "/.EntityOS.stage.*" in ignore
