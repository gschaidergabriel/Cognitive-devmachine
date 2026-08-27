import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
LOCK_SHA256 = "32cd4587adbb45292c964b45f5efd4c38873ccd578792557fbf909f1953e1586"
LOCK_SIZE = 9181696


def test_entityos_lock_binds_verified_substrate_candidate():
    doc = json.loads((ROOT / "entityos.lock.json").read_text(encoding="utf-8"))
    assert doc["schema"] == "ClayVerseEntityOSArtifactLock/v1"
    assert doc["source_repository"] == "gschaidergabriel/Dr.-Unterweger"
    assert doc["source_head"] == "79dc06eb4cba7aa3e3f4d1944bf3c2609ca0d21c"
    assert doc["source_tree"] == "d55d9d41f5a294a4a692cdee6fa46750652a390d"
    assert doc["sha256"] == LOCK_SHA256
    assert doc["size_bytes"] == LOCK_SIZE
    assert doc["tests_passed"] == 207
    assert doc["full_pytest"] == "PASS_ZERO_SKIPS"
    assert doc["double_build"] == "BYTE_IDENTICAL"
    assert doc["runtime_gates"] == "PASS"
    assert doc["sandbox_stopped"] is True
    assert doc["whole_clayverse_acceptance"] is False


def test_docker_build_cannot_self_authorize_arbitrary_entityos_digest():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY --chown=root:root entityos.lock.json /opt/entityos/entityos.lock.json" in dockerfile
    assert 'test "${ENTITYOS_SHA256}" = "$LOCK_SHA256"' in dockerfile
    assert 'test "$(stat -c %s /opt/entityos/EntityOS)" = "$LOCK_SIZE"' in dockerfile
    assert "sha256sum -c -" in dockerfile


def test_default_deny_build_context_admits_every_declared_non_tree_copy_input():
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    assert dockerignore.splitlines()[3] == "*"
    for required in (
        "!runtime_CLAUDE.md",
        "!entityos.lock.json",
        "!EntityOS",
    ):
        assert required in dockerignore.splitlines()


def test_oci_workflow_derives_build_digest_from_tracked_lock():
    workflow = (REPO / ".github" / "workflows" / "clayverse-artifact-ci.yml").read_text(encoding="utf-8")
    assert 'doc["schema"] == "ClayVerseEntityOSArtifactLock/v1"' in workflow
    assert 'ACTUAL_SHA256="$(sha256sum "the artefact/EntityOS"' in workflow
    assert '--build-arg "ENTITYOS_SHA256=${CLAYVERSE_ENTITYOS_SHA256}"' in workflow
