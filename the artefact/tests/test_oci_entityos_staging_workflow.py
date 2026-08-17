from pathlib import Path


ARTEFACT = Path(__file__).resolve().parents[1]
WORKFLOW = ARTEFACT.parent / ".github" / "workflows" / "clayverse-artifact-ci.yml"


def test_canonical_oci_workflow_uses_release_only_as_transport_locator():
    text = WORKFLOW.read_text()

    assert "entityos_release_tag:" in text
    assert 'GH_TOKEN: ${{ github.token }}' in text
    assert 'gh release download "$ENTITYOS_RELEASE_TAG"' in text
    assert '--repo "$GITHUB_REPOSITORY"' in text
    assert "--pattern 'EntityOS'" in text
    assert 'doc["schema"] == "ClayVerseEntityOSArtifactLock/v1"' in text
    assert 'sha = doc["sha256"]' in text
    assert 'size = doc["size_bytes"]' in text
    assert 'sh ./stage-entityos.sh /tmp/clayverse-entityos-release/EntityOS "$LOCK_SHA256"' in text
    assert "ENTITYOS_SHA256_INPUT" not in text


def test_canonical_oci_workflow_binds_one_digest_through_stage_build_and_image():
    text = WORKFLOW.read_text()

    assert 'echo "CLAYVERSE_ENTITYOS_SHA256=$LOCK_SHA256" >> "$GITHUB_ENV"' in text
    assert '--build-arg "ENTITYOS_SHA256=${CLAYVERSE_ENTITYOS_SHA256}"' in text
    assert "open('/opt/entityos/EntityOS','rb').read()" in text
    assert 'test "$EMBEDDED_SHA256" = "$CLAYVERSE_ENTITYOS_SHA256"' in text
    assert 'test "$ACTUAL_SIZE" = "$ENTITYOS_LOCK_SIZE"' in text


def test_only_one_clayverse_oci_artifact_workflow_is_canonical():
    workflows = ARTEFACT.parent / ".github" / "workflows"
    assert (workflows / "clayverse-artifact-ci.yml").is_file()
    assert not (workflows / "clayverse-artefact-ci.yml").exists()
