from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_baseline_container_has_no_mandatory_entityos_runtime_sidecar():
    dockerfile = (ROOT / "Dockerfile").read_text()
    compose = (ROOT / "compose.yaml").read_text()

    # EntityOS is optional in the baseline image and execution is explicitly
    # disabled. If bytes are deliberately embedded, Dockerfile digest/size
    # binding remains the separate fail-closed admission contract.
    assert "CLAYVERSE_ENABLE_ENTITYOS_EXEC=0" in dockerfile
    assert 'CLAYVERSE_ENABLE_ENTITYOS_EXEC: "0"' in compose
    assert "CLAYVERSE_REQUIRE_ENTITYOS" not in dockerfile
    assert "CLAYVERSE_REQUIRE_ENTITYOS" not in compose
    assert "CLAYVERSE_ENTITYOS_HOST_PATH" not in compose
    assert "/opt/entityos/EntityOS:ro" not in compose


def test_baseline_compose_does_not_require_entityos_digest():
    compose = (ROOT / "compose.yaml").read_text()

    assert compose.count('${CLAYVERSE_ENTITYOS_SHA256:-}') == 2
    assert "CLAYVERSE_ENTITYOS_SHA256:?required" not in compose
    # Authentication configuration remains fail-closed; only the optional
    # internal EntityOS substrate loses the accidental baseline requirement.
    assert '${CLAYVERSE_CLERK_MAP_JSON:?required}' in compose
    assert '${CLERK_ISSUER:?required}' in compose
    assert '${CLERK_AUTHORIZED_PARTIES:?required}' in compose


def test_future_entityos_staging_input_is_not_a_source_history_artifact():
    ignore = (ROOT / ".gitignore").read_text().splitlines()
    assert "/EntityOS" in ignore
    assert "/.EntityOS.stage.*" in ignore
