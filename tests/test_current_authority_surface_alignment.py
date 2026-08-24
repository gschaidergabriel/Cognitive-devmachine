from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _json(rel_path: str) -> dict:
    return json.loads((REPO_ROOT / rel_path).read_text(encoding="utf-8"))


def test_current_authority_surfaces_follow_bootstrap_successor() -> None:
    """Fail if current-facing surfaces form a self-consistent stale authority island."""

    bootstrap = _json("research_entity/continuity/BOOTSTRAP_MINIMAL.json")
    steering_rel = bootstrap["authority_correction"]
    steering = _json(steering_rel)
    expected_epoch = steering["schema_version"]

    assert bootstrap["schema_version"] == expected_epoch

    inbox = _json("research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")
    assert inbox["schema_version"] == expected_epoch
    assert inbox["steering"] == steering_rel

    program = _json("research_entity/rooms/PROGRAM_STATE.json")
    assert program["schema_version"] == expected_epoch
    assert program["authority_correction"] == steering_rel
    assert program["all_worker_protocol"] == bootstrap["all_worker_protocol"]
    assert program["execution_policy"]["external_provider_admission_file"] == bootstrap["free_provider_admission"]

    manifest = _json("the artefact/manifest.json")
    assert manifest["authority_correction"] == steering_rel
    assert manifest["execution_policy"]["active_supervisor_epoch"] == expected_epoch
    assert manifest["execution_policy"]["external_provider_admission_file"] == bootstrap["free_provider_admission"]

    provider_admission = _json(bootstrap["free_provider_admission"])
    assert provider_admission["authority_epoch"] == expected_epoch
    assert set(provider_admission["providers"]) == set(bootstrap["free_provider_allowlist_current"])

    directive_rel = bootstrap["all_worker_protocol"]
    directive = (REPO_ROOT / directive_rel).read_text(encoding="utf-8")
    assert f"Authority epoch: {expected_epoch}" in directive
    assert steering_rel in directive

    readme = (REPO_ROOT / "the artefact/README.md").read_text(encoding="utf-8")
    assert steering_rel in readme
    assert directive_rel in readme
