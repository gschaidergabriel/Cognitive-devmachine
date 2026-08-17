from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_entityos_is_embedded_at_build_not_runtime_bind_mounted():
    dockerfile = (ROOT / "Dockerfile").read_text()
    compose = (ROOT / "compose.yaml").read_text()

    assert "ARG ENTITYOS_SHA256" in dockerfile
    assert "COPY --chown=root:root EntityOS /opt/entityos/EntityOS" in dockerfile
    assert "sha256sum -c -" in dockerfile
    assert "chmod 0555 /opt/entityos/EntityOS" in dockerfile

    assert 'ENTITYOS_SHA256: "${CLAYVERSE_ENTITYOS_SHA256:?required}"' in compose
    assert "CLAYVERSE_ENTITYOS_HOST_PATH" not in compose
    assert "/opt/entityos/EntityOS:ro" not in compose


def test_staged_entityos_input_is_not_a_source_history_artifact():
    ignore = (ROOT / ".gitignore").read_text().splitlines()
    assert "/EntityOS" in ignore
    assert "/.EntityOS.stage.*" in ignore
