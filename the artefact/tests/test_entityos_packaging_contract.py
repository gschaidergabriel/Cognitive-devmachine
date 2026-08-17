from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_keeps_baseline_entityos_optional_but_digest_binds_embedding():
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert 'ARG ENTITYOS_SHA256=""' in dockerfile
    assert "COPY --chown=root:root build-assets/entityos/ /opt/entityos-stage/" in dockerfile
    assert "staged EntityOS requires ENTITYOS_SHA256" in dockerfile
    assert "sha256sum -c -" in dockerfile
    assert "COPY --chown=root:root EntityOS /opt/entityos/EntityOS" not in dockerfile


def test_stager_targets_ignored_bounded_build_asset_path():
    stager = (ROOT / "stage-entityos.sh").read_text()
    ignore = (ROOT / ".gitignore").read_text().splitlines()
    assert 'stage_dir="$root/build-assets/entityos"' in stager
    assert "/build-assets/entityos/EntityOS" in ignore
    assert "/build-assets/entityos/.EntityOS.stage.*" in ignore
    assert "/EntityOS" not in ignore


def test_optional_build_asset_directory_is_tracked_without_binary():
    assert (ROOT / "build-assets/entityos/.keep").is_file()
    assert not (ROOT / "build-assets/entityos/EntityOS").exists()
