from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_baseline_container_has_no_mandatory_entityos_runtime_sidecar():
    dockerfile = (ROOT / "Dockerfile").read_text()
    compose = (ROOT / "compose.yaml").read_text()

    # EntityOS is digest-bound into the one ClayVerse image, but execution is
    # explicitly disabled in the admitted baseline. The retired REQUIRE switch
    # must not be treated as the current optionality contract.
    assert "CLAYVERSE_ENABLE_ENTITYOS_EXEC=0" in dockerfile
    assert 'CLAYVERSE_ENABLE_ENTITYOS_EXEC: "0"' in compose
    assert "CLAYVERSE_REQUIRE_ENTITYOS" not in dockerfile
    assert "CLAYVERSE_REQUIRE_ENTITYOS" not in compose
    assert "CLAYVERSE_ENTITYOS_HOST_PATH" not in compose
    assert "/opt/entityos/EntityOS:ro" not in compose


def test_future_entityos_staging_input_is_not_a_source_history_artifact():
    ignore = (ROOT / ".gitignore").read_text().splitlines()
    assert "/EntityOS" in ignore
    assert "/.EntityOS.stage.*" in ignore
