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
    (root / "CLAY_EXECUTION_AUTHORITY.md").write_text("authority")
    (root / "research_entity" / "continuity" / "BOOTSTRAP_MINIMAL.json").write_text("{}")
    (root / "research_entity" / "rooms" / "PROGRAM_STATE.json").write_text("{}")
    return root


def _present() -> dict[str, bool]:
    return {path: True for path in preflight.AUTHORITY_FILES}


def test_read_only_preflight_never_mints_adapted_or_native(tmp_path):
    root = _make_repo_root(tmp_path)
    present = _present()
    assert preflight.classify(root, present, False, True) == "DEGRADED"
    assert preflight.classify(root, present, True, True) == "DEGRADED"
    assert preflight.classify(root, present, True, True) not in {"ADAPTED", "NATIVE"}


def test_missing_root_or_current_authority_blocks(tmp_path):
    root = _make_repo_root(tmp_path)
    present = _present()
    assert preflight.classify(None, present, True, True) == "BLOCKED"
    missing = dict(present)
    missing[preflight.AUTHORITY_FILES[0]] = False
    assert preflight.classify(root, missing, True, True) == "BLOCKED"
    assert preflight.classify(root, present, True, False) == "BLOCKED"


def test_dynamic_steering_must_exist_inside_repository(tmp_path):
    root = _make_repo_root(tmp_path)
    inbox = root / preflight.INBOX_RELATIVE_PATH
    steering_rel = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_TEST.json"
    steering = root / steering_rel
    steering.write_text("{}")
    inbox.write_text(json.dumps({"steering": steering_rel}))
    state = preflight.resolve_dynamic_steering(root)
    assert state["verified"] is True
    assert state["pointer"] == steering_rel
    assert Path(state["resolved_path"]) == steering.resolve()
    steering.unlink()
    state = preflight.resolve_dynamic_steering(root)
    assert state["verified"] is False
    assert state["reason"] == "STEERING_TARGET_MISSING"


def test_dynamic_steering_rejects_traversal_and_absolute_paths(tmp_path):
    root = _make_repo_root(tmp_path)
    inbox = root / preflight.INBOX_RELATIVE_PATH
    inbox.write_text(json.dumps({"steering": "../../outside.json"}))
    state = preflight.resolve_dynamic_steering(root)
    assert state["verified"] is False
    assert state["reason"] == "STEERING_POINTER_ESCAPES_REPOSITORY"
    inbox.write_text(json.dumps({"steering": str((tmp_path / "absolute.json").resolve())}))
    state = preflight.resolve_dynamic_steering(root)
    assert state["verified"] is False
    assert state["reason"] == "STEERING_POINTER_ABSOLUTE_REJECTED"


def test_dynamic_steering_fails_closed_on_unreadable_inbox(tmp_path):
    root = _make_repo_root(tmp_path)
    inbox = root / preflight.INBOX_RELATIVE_PATH
    inbox.write_text("not-json")
    state = preflight.resolve_dynamic_steering(root)
    assert state["verified"] is False
    assert state["reason"].startswith("INBOX_UNREADABLE:")


def test_contract_declares_unprobed_lifecycle_boundaries():
    assert set(preflight.LIFECYCLE_BOUNDARIES) == {
        "real_lifecycle_hook_firing",
        "cross_session_durable_state_when_claimed",
        "effect_or_result_receipt_when_claimed",
    }
    source = PREFLIGHT_PATH.read_text()
    assert '"FRANKENSTEIN_HOST_PREFLIGHT/v3"' in source
    assert '"adapted_or_native_possible_from_this_preflight": False' in source
