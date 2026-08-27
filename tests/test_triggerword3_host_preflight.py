import importlib.util
import json
from pathlib import Path


PREFLIGHT_PATH = (
    Path(__file__).resolve().parents[1]
    / "AI_START_HERE_DO_NOT_SCAN_REPO"
    / "frankenstein_host_preflight.py"
)
spec = importlib.util.spec_from_file_location("triggerword3_host_preflight", PREFLIGHT_PATH)
assert spec is not None and spec.loader is not None
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


def _make_repo_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "research_entity" / "continuity").mkdir(parents=True)
    (root / "research_entity" / "claycode" / "autonomous").mkdir(parents=True)
    (root / "the artefact").mkdir()
    (root / "AI_START_HERE_DO_NOT_SCAN_REPO").mkdir()
    (root / "CLAY_EXECUTION_AUTHORITY.md").write_text("authority\n", encoding="utf-8")
    (root / "research_entity" / "continuity" / "BOOTSTRAP_MINIMAL.json").write_text(
        "{}\n", encoding="utf-8"
    )
    return root


def _write_inbox(root: Path, pointer: str, **free_only_overrides) -> Path:
    steering = root / pointer
    steering.parent.mkdir(parents=True, exist_ok=True)
    steering.write_text("{}\n", encoding="utf-8")
    free_only = {
        "provider_routes_admitted": False,
        "together_forbidden": True,
        "free_swarm_owner_emergency_stop": True,
        "remaining_together_paid_runs_authorized": 0,
    }
    free_only.update(free_only_overrides)
    inbox = root / preflight.INBOX_RELATIVE_PATH
    inbox.write_text(
        json.dumps(
            {
                "schema_version": "TEST",
                "supervisor_delta": "TEST",
                "steering": pointer,
                "free_only": free_only,
            }
        ),
        encoding="utf-8",
    )
    return steering


def test_read_only_preflight_never_self_promotes_native_or_adapted(tmp_path):
    root = _make_repo_root(tmp_path)
    present = {path: True for path in preflight.AUTHORITY_FILES}

    assert preflight.repository_preflight_class(root, present, True, True) == (
        "DEGRADED",
        "READ_ONLY_PREFLIGHT_CANNOT_PROVE_LIFECYCLE_STATE_OR_EFFECTS",
    )
    assert preflight.repository_preflight_class(root, present, True, False) == (
        "DEGRADED",
        "AUTHORITY_READABLE_BUT_GIT_IDENTITY_UNVERIFIED",
    )


def test_missing_root_or_required_authority_blocks(tmp_path):
    root = _make_repo_root(tmp_path)
    present = {path: True for path in preflight.AUTHORITY_FILES}
    assert preflight.repository_preflight_class(None, present, True, True)[0] == "BLOCKED"

    missing = dict(present)
    missing["CLAY_EXECUTION_AUTHORITY.md"] = False
    assert preflight.repository_preflight_class(root, missing, True, True) == (
        "BLOCKED",
        "REQUIRED_AUTHORITY_FILE_MISSING",
    )
    assert preflight.repository_preflight_class(root, present, False, True) == (
        "BLOCKED",
        "CURRENT_STEERING_AUTHORITY_UNRESOLVED",
    )


def test_dynamic_steering_must_resolve_inside_repository(tmp_path):
    root = _make_repo_root(tmp_path)
    pointer = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_TEST.json"
    steering = _write_inbox(root, pointer)

    state = preflight.resolve_inbox_and_steering(root)
    assert state["verified"] is True
    assert state["steering_pointer"] == pointer
    assert Path(state["steering_path"]) == steering.resolve()

    steering.unlink()
    state = preflight.resolve_inbox_and_steering(root)
    assert state["verified"] is False
    assert state["reason"] == "STEERING_TARGET_MISSING"


def test_dynamic_steering_rejects_path_escape_absolute_and_bad_json(tmp_path):
    root = _make_repo_root(tmp_path)
    inbox = root / preflight.INBOX_RELATIVE_PATH

    inbox.write_text(json.dumps({"steering": "../../../../outside.json"}), encoding="utf-8")
    state = preflight.resolve_inbox_and_steering(root)
    assert state["verified"] is False
    assert state["reason"] == "STEERING_POINTER_ESCAPES_REPOSITORY"

    inbox.write_text(
        json.dumps({"steering": str((tmp_path / "absolute.json").resolve())}),
        encoding="utf-8",
    )
    state = preflight.resolve_inbox_and_steering(root)
    assert state["verified"] is False
    assert state["reason"] == "STEERING_POINTER_ABSOLUTE_REJECTED"

    inbox.write_text("not-json", encoding="utf-8")
    state = preflight.resolve_inbox_and_steering(root)
    assert state["verified"] is False
    assert state["reason"].startswith("INBOX_UNREADABLE:")


def test_provider_orchestration_blocks_current_hardoff_shape(tmp_path):
    root = _make_repo_root(tmp_path)
    pointer = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_TEST.json"
    _write_inbox(root, pointer)
    state = preflight.resolve_inbox_and_steering(root)
    classification, reason = preflight.provider_action_class(state["inbox"])
    assert classification == "BLOCKED"
    assert reason == "FREE_SWARM_OWNER_EMERGENCY_STOP"


def test_provider_open_shape_is_still_only_degraded_not_execution_pass(tmp_path):
    root = _make_repo_root(tmp_path)
    pointer = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_TEST.json"
    _write_inbox(
        root,
        pointer,
        provider_routes_admitted=True,
        together_forbidden=False,
        free_swarm_owner_emergency_stop=False,
    )
    state = preflight.resolve_inbox_and_steering(root)
    classification, reason = preflight.provider_action_class(state["inbox"])
    assert classification == "DEGRADED"
    assert reason == "SOURCE_AUTHORITY_APPEARS_OPEN_BUT_EXECUTION_NOT_PROBED"


def test_preflight_source_has_no_provider_or_network_client_imports():
    source = PREFLIGHT_PATH.read_text(encoding="utf-8")
    forbidden = (
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "import urllib.request",
        "from urllib.request",
        "import socket",
        "from socket",
        "import llm",
    )
    for token in forbidden:
        assert token not in source
