import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_keeps_baseline_entityos_optional_but_digest_binds_embedding():
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert 'ARG ENTITYOS_SHA256=""' in dockerfile
    assert "COPY --chown=root:root build-assets/entityos/ /opt/entityos-stage/" in dockerfile
    assert "staged EntityOS requires ENTITYOS_SHA256" in dockerfile
    assert 'test "${ENTITYOS_SHA256}" = "$LOCK_SHA256"' in dockerfile
    assert 'test "$(stat -c %s /opt/entityos-stage/EntityOS)" = "$LOCK_SIZE"' in dockerfile
    assert "sha256sum -c -" in dockerfile
    assert "COPY --chown=root:root EntityOS /opt/entityos/EntityOS" not in dockerfile


def test_stager_targets_ignored_bounded_build_asset_path():
    stager = (ROOT / "stage-entityos.sh").read_text()
    ignore = (ROOT / ".gitignore").read_text().splitlines()
    assert "stage_dir=./build-assets/entityos" in stager
    assert "/build-assets/entityos/EntityOS" in ignore
    assert "/build-assets/entityos/.EntityOS.stage.*" in ignore


def test_optional_build_asset_directory_is_tracked_without_binary():
    assert (ROOT / "build-assets/entityos/.keep").is_file()
    assert not (ROOT / "build-assets/entityos/EntityOS").exists()


def test_manifest_matches_optional_entityos_baseline():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    assert "optional" in manifest["build_context"].lower()
    assert "optional" in manifest["entityos_role"].lower()
    assert "optional" in manifest["entityos_transport"].lower()
    admission = manifest["entityos_admission"]
    assert "baseline may omit" in admission.lower()
    assert "CLAYVERSE_ENABLE_ENTITYOS_EXEC=0" in admission
    assert "digest" in admission.lower()
    assert "size" in admission.lower()
    gates = manifest["requires_for_final_pass"]
    assert any("where EntityOS is deliberately admitted" in gate for gate in gates)
    assert "accepted EntityOS embedded image runtime and effect contract" not in gates
