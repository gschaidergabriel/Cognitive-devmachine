from pathlib import Path


ARTEFACT = Path(__file__).resolve().parents[1]
WORKFLOW = ARTEFACT.parent / ".github" / "workflows" / "clayverse-artefact-ci.yml"


def test_oci_workflow_requires_explicit_same_repo_entityos_identity():
    text = WORKFLOW.read_text()

    assert "entityos_release_tag:" in text
    assert "entityos_sha256:" in text
    assert 'GH_TOKEN: ${{ github.token }}' in text
    assert 'gh release download "$ENTITYOS_RELEASE_TAG"' in text
    assert '--repo "$GITHUB_REPOSITORY"' in text
    assert "--pattern 'EntityOS'" in text
    assert 'sh ./stage-entityos.sh /tmp/clayverse-entityos-release/EntityOS "$entityos_sha256"' in text


def test_oci_build_and_packaged_bytes_share_the_same_digest_authority():
    text = WORKFLOW.read_text()

    assert 'echo "ENTITYOS_SHA256=$entityos_sha256" >> "$GITHUB_ENV"' in text
    assert 'docker build --pull=false --build-arg "ENTITYOS_SHA256=${ENTITYOS_SHA256}"' in text
    assert "open('/opt/entityos/EntityOS','rb').read()" in text
    assert 'test "$embedded_sha" = "$ENTITYOS_SHA256"' in text
    assert 'entityos_sha256=%s' in text
