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
    (root / "research_entity" / "continuity" / "BOOTSTRAP_MINIMAL.json").write_text("{}")
    (root / "research_entity" / "rooms" / "PROGRAM_STATE.json").write_text("{}")
    return root


def test_read_only_classification_never_promotes_without_lifecycle_witness(tmp_path):
    root = _make_repo_root(tmp_path)
    present = {path: True for path in preflight.AUTHORITY_FILES}

    assert preflight.classify(root, present, False, True) == "DEGRADED"
    assert preflight.classify(root, present, True, False) == "BLOCKED"
    assert preflight.classify(root, present, True, True) == "DEGRADED"
    assert preflight.classify(None, present, True, True) == "BLOCKED"

    observed = {
        preflight.classify(root, present, git_ok, steering_ok)
        for git_ok in (False, True)
        for steering_ok in (False, True)
    }
    assert "NATIVE" not in observed
    assert "ADAPTED" not in observed


def test_missing_required_authority_file_blocks(tmp_path):
    root = _make_repo_root(tmp_path)
    present = {path: True for path in preflight.AUTHORITY_FILES}
    missing = dict(present)
    missing[preflight.AUTHORITY_FILES[0]] = False
    assert preflight.classify(root, missing, True, True) == "BLOCKED"


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
