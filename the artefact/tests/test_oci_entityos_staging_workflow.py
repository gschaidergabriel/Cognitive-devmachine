from pathlib import Path


ARTEFACT = Path(__file__).resolve().parents[1]
WORKFLOW = ARTEFACT.parent / ".github" / "workflows" / "clayverse-artefact-ci.yml"


def test_oci_workflow_admits_tokenless_baseline_and_pairs_optional_entityos_inputs():
    text = WORKFLOW.read_text()

    assert "EntityOS omitted: validating tokenless ClayVerse baseline." in text
    assert "EntityOS release tag and SHA-256 must be supplied together" in text
    assert "required: false" in text
    assert "Stage optional exact EntityOS release asset" in text
    assert "inputs.entityos_release_tag != '' && inputs.entityos_sha256 != ''" in text
    assert "GITHUB_READ_TOKEN" not in text


def test_optional_entityos_staging_stays_same_repo_and_digest_bound():
    text = WORKFLOW.read_text()

    assert 'GH_TOKEN: ${{ github.token }}' in text
    assert 'gh release download "$ENTITYOS_RELEASE_TAG"' in text
    assert '--repo "$GITHUB_REPOSITORY"' in text
    assert "--pattern 'EntityOS'" in text
    assert 'sh ./stage-entityos.sh /tmp/clayverse-entityos-release/EntityOS "$ENTITYOS_SHA256"' in text


def test_oci_build_and_packaged_bytes_share_optional_digest_authority():
    text = WORKFLOW.read_text()

    assert 'docker build --pull=false --build-arg "ENTITYOS_SHA256=${ENTITYOS_SHA256:-}"' in text
    assert "open('/opt/entityos/EntityOS','rb').read()" in text
    assert 'test "$embedded_sha" = "$ENTITYOS_SHA256"' in text
    assert "test ! -e /opt/entityos/EntityOS" in text
    assert 'entityos_sha256=%s' in text
