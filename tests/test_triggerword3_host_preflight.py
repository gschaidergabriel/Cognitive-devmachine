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
    (root / "research_entity" / "claycode" / "autonomous").mkdir(parents=True)
    (root / "the artefact").mkdir()
    (root / "AI_START_HERE_DO_NOT_SCAN_REPO").mkdir()
    (root / "CLAY_EXECUTION_AUTHORITY.md").write_text("authority", encoding="utf-8")
    (root / "research_entity" / "continuity" / "BOOTSTRAP_MINIMAL.json").write_text("{}", encoding="utf-8")
    return root


def _write_authority(root: Path, *, provider_routes=False, emergency_stop=True):
    steering_rel = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_TEST.json"
    (root / steering_rel).write_text("{}", encoding="utf-8")
    inbox = {
        "steering": steering_rel,
        "free_only": {
            "enabled": True,
            "no_paid_fallback": True,
            "together_forbidden": True,
            "provider_routes_admitted": provider_routes,
            "free_swarm_owner_emergency_stop": emergency_stop,
        },
    }
    (root / preflight.INBOX_RELATIVE_PATH).write_text(json.dumps(inbox), encoding="utf-8")
    return inbox


def test_read_only_classification_never_mints_native_or_adapted(tmp_path):
    root = _make_repo_root(tmp_path)
    present = {path: True for path in preflight.AUTHORITY_FILES}
    assert preflight.classify(root, present, False, True) == "DEGRADED"
    assert preflight.classify(root, present, True, False) == "BLOCKED"
    assert preflight.classify(root, present, True, True) == "DEGRADED"
    assert preflight.classify(None, present, True, True) == "BLOCKED"


def test_repository_preflight_requires_all_authority_files(tmp_path):
    root = _make_repo_root(tmp_path)
    present = {path: True for path in preflight.AUTHORITY_FILES}
    status, _ = preflight.repository_preflight_class(root, present, True, True)
    assert status == "DEGRADED"
    present[preflight.AUTHORITY_FILES[0]] = False
    status, reason = preflight.repository_preflight_class(root, present, True, True)
    assert (status, reason) == ("BLOCKED", "REQUIRED_AUTHORITY_FILE_MISSING")


def test_dynamic_steering_must_exist_inside_repository(tmp_path):
    root = _make_repo_root(tmp_path)
    _write_authority(root)
    state = preflight.resolve_inbox_and_steering(root)
    assert state["verified"] is True
    assert Path(state["steering_path"]).is_file()
    Path(state["steering_path"]).unlink()
    state = preflight.resolve_inbox_and_steering(root)
    assert state["verified"] is False
    assert state["reason"] == "STEERING_TARGET_MISSING"


def test_dynamic_steering_rejects_traversal_and_absolute_paths(tmp_path):
    root = _make_repo_root(tmp_path)
    inbox = root / preflight.INBOX_RELATIVE_PATH
    inbox.write_text(json.dumps({"steering": "../../outside.json"}), encoding="utf-8")
    state = preflight.resolve_inbox_and_steering(root)
    assert state["verified"] is False
    assert state["reason"] == "STEERING_POINTER_ESCAPES_REPOSITORY"
    inbox.write_text(json.dumps({"steering": str((tmp_path / "absolute.json").resolve())}), encoding="utf-8")
    state = preflight.resolve_inbox_and_steering(root)
    assert state["verified"] is False
    assert state["reason"] == "STEERING_POINTER_ABSOLUTE_REJECTED"


def test_dynamic_steering_fails_closed_on_malformed_inbox(tmp_path):
    root = _make_repo_root(tmp_path)
    (root / preflight.INBOX_RELATIVE_PATH).write_text("not-json", encoding="utf-8")
    state = preflight.resolve_inbox_and_steering(root)
    assert state["verified"] is False
    assert state["reason"].startswith("INBOX_UNREADABLE:")


def test_current_hardoff_shape_blocks_provider_orchestration(tmp_path):
    root = _make_repo_root(tmp_path)
    inbox = _write_authority(root, provider_routes=False, emergency_stop=True)
    status, reason = preflight.provider_action_class(inbox)
    assert status == "BLOCKED"
    assert reason == "FREE_SWARM_OWNER_EMERGENCY_STOP"


def test_future_source_open_shape_still_cannot_mint_execution_pass(tmp_path):
    root = _make_repo_root(tmp_path)
    inbox = _write_authority(root, provider_routes=True, emergency_stop=False)
    status, reason = preflight.provider_action_class(inbox)
    assert status == "DEGRADED"
    assert "EXECUTION_NOT_PROBED" in reason


def test_preflight_source_contains_no_provider_or_network_clients():
    source = PREFLIGHT_PATH.read_text(encoding="utf-8")
    forbidden = ("requests", "urllib", "http.client", "socket", "openai", "groq", "mistral", "together")
    lowered = source.lower()
    for token in forbidden:
        assert f"import {token}" not in lowered
        assert f"from {token}" not in lowered
