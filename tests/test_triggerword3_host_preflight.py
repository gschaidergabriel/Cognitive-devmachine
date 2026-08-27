import importlib.util
import json
from pathlib import Path

PREFLIGHT_PATH = Path(__file__).resolve().parents[1] / "AI_START_HERE_DO_NOT_SCAN_REPO" / "frankenstein_host_preflight.py"
spec = importlib.util.spec_from_file_location("triggerword3_host_preflight", PREFLIGHT_PATH)
preflight = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(preflight)


def _make_repo_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "research_entity" / "continuity").mkdir(parents=True)
    (root / "research_entity" / "rooms").mkdir(parents=True)
    (root / "research_entity" / "claycode" / "autonomous").mkdir(parents=True)
    (root / "the artefact").mkdir()
    (root / "AI_START_HERE_DO_NOT_SCAN_REPO").mkdir()
    (root / "CLAY_EXECUTION_AUTHORITY.md").write_text("authority", encoding="utf-8")
    (root / "research_entity" / "continuity" / "BOOTSTRAP_MINIMAL.json").write_text("{}", encoding="utf-8")
    (root / "research_entity" / "rooms" / "PROGRAM_STATE.json").write_text("{}", encoding="utf-8")
    return root


def _write_current_inbox(root: Path, **free_only_overrides) -> str:
    steering_rel = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_TEST.json"
    (root / steering_rel).write_text("{}", encoding="utf-8")
    free_only = {
        "provider_routes_admitted": False,
        "together_forbidden": True,
        "free_swarm_owner_emergency_stop": True,
        "remaining_together_paid_runs_authorized": 0,
    }
    free_only.update(free_only_overrides)
    (root / preflight.INBOX_RELATIVE_PATH).write_text(
        json.dumps({
            "schema_version": "9.13",
            "supervisor_delta": "9.13Q_NON_AUTHORITY",
            "steering": steering_rel,
            "free_only": free_only,
        }),
        encoding="utf-8",
    )
    return steering_rel


def test_read_only_preflight_never_mints_native_or_adapted(tmp_path):
    root = _make_repo_root(tmp_path)
    _write_current_inbox(root)
    present = {path: True for path in preflight.AUTHORITY_FILES}
    assert preflight.classify(root, present, False, True) == "DEGRADED"
    assert preflight.classify(root, present, True, True) == "DEGRADED"
    assert preflight.classify(None, present, True, True) == "BLOCKED"
    missing = dict(present)
    missing[preflight.AUTHORITY_FILES[0]] = False
    assert preflight.classify(root, missing, True, True) == "BLOCKED"


def test_dynamic_steering_must_exist_inside_repository(tmp_path):
    root = _make_repo_root(tmp_path)
    steering_rel = _write_current_inbox(root)
    state = preflight.resolve_dynamic_steering(root)
    assert state["verified"] is True
    assert state["pointer"] == steering_rel
    assert Path(state["resolved_path"]) == (root / steering_rel).resolve()
    (root / steering_rel).unlink()
    state = preflight.resolve_dynamic_steering(root)
    assert state["verified"] is False
    assert state["reason"] == "STEERING_TARGET_MISSING"


def test_dynamic_steering_rejects_traversal_and_absolute_paths(tmp_path):
    root = _make_repo_root(tmp_path)
    inbox = root / preflight.INBOX_RELATIVE_PATH
    inbox.write_text(json.dumps({"steering": "../../outside.json"}), encoding="utf-8")
    state = preflight.resolve_dynamic_steering(root)
    assert state["verified"] is False
    assert state["reason"] == "STEERING_POINTER_ESCAPES_REPOSITORY"
    inbox.write_text(json.dumps({"steering": str((tmp_path / "absolute.json").resolve())}), encoding="utf-8")
    state = preflight.resolve_dynamic_steering(root)
    assert state["verified"] is False
    assert state["reason"] == "STEERING_POINTER_ABSOLUTE_REJECTED"


def test_dynamic_steering_fails_closed_on_unreadable_inbox(tmp_path):
    root = _make_repo_root(tmp_path)
    inbox = root / preflight.INBOX_RELATIVE_PATH
    inbox.write_text("not-json", encoding="utf-8")
    state = preflight.resolve_dynamic_steering(root)
    assert state["verified"] is False
    assert state["reason"].startswith("INBOX_UNREADABLE:")


def test_current_hard_off_blocks_provider_orchestration(tmp_path):
    root = _make_repo_root(tmp_path)
    _write_current_inbox(root)
    state = preflight.resolve_dynamic_steering(root)
    classification, reason = preflight.provider_action_class(state["inbox"])
    assert classification == "BLOCKED"
    assert reason == "FREE_SWARM_OWNER_EMERGENCY_STOP"


def test_source_open_provider_shape_is_still_degraded_not_executable(tmp_path):
    root = _make_repo_root(tmp_path)
    _write_current_inbox(
        root,
        provider_routes_admitted=True,
        free_swarm_owner_emergency_stop=False,
    )
    state = preflight.resolve_dynamic_steering(root)
    classification, reason = preflight.provider_action_class(state["inbox"])
    assert classification == "DEGRADED"
    assert "EXECUTION_NOT_PROBED" in reason


def test_preflight_has_no_network_or_provider_client_imports():
    source = PREFLIGHT_PATH.read_text(encoding="utf-8")
    banned = ("requests", "urllib", "http.client", "socket", "openai", "together", "groq", "mistral")
    for token in banned:
        assert f"import {token}" not in source
        assert f"from {token}" not in source
