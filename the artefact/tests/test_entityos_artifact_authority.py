import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
# Synced 2026-08-18 to the S2 relock commit (322f6b1a7): source repo head had
# advanced past the prior lock (79dc06e -> 36979a3). That relock is a real,
# separately-committed, self-documented rebuild (see entityos.lock.json's own
# "build_note") -- not something invented here. It honestly nulls fields it
# could not re-verify (tests_passed, full_pytest, archive/attestation digests)
# instead of carrying forward the old lock's unverified claims.
LOCK_SHA256 = "3ef1a9e082c195fc6908047333d9c01a51e71bbbe2bd24fde7378bd3187c60f7"
LOCK_SIZE = 8942304


def test_entityos_lock_binds_verified_substrate_candidate():
    doc = json.loads((ROOT / "entityos.lock.json").read_text(encoding="utf-8"))
    assert doc["schema"] == "ClayVerseEntityOSArtifactLock/v1"
    assert doc["source_repository"] == "gschaidergabriel/Dr.-Unterweger"
    assert doc["source_head"] == "36979a30c0f83c21bb59140bb4903be80f381bab"
    assert doc["source_tree"] == "25ae6c7363c789b712040802860a4449391134f5"
    assert doc["sha256"] == LOCK_SHA256
    assert doc["size_bytes"] == LOCK_SIZE
    # NOT carried forward from the pre-relock lock -- honestly null/unverified now.
    assert doc["tests_passed"] is None
    assert doc["full_pytest"] == "NOT_RUN_FOR_THIS_LOCK"
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
