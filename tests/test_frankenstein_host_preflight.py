from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "AI_START_HERE_DO_NOT_SCAN_REPO" / "frankenstein_host_preflight.py"

spec = spec_from_file_location("frankenstein_host_preflight", PREFLIGHT)
assert spec is not None and spec.loader is not None
preflight = module_from_spec(spec)
spec.loader.exec_module(preflight)


def test_read_only_preflight_never_mints_native(tmp_path):
    authority = {"a": True, "b": True, "c": True}
    assert preflight.classify(tmp_path, authority, True, True) == "ADAPTED"


def test_missing_repo_root_is_blocked():
    authority = {"a": True, "b": True, "c": True}
    assert preflight.classify(None, authority, True, True) == "BLOCKED"


def test_incomplete_authority_or_git_is_degraded(tmp_path):
    complete = {"a": True, "b": True, "c": True}
    incomplete = {"a": True, "b": False, "c": True}

    assert preflight.classify(tmp_path, incomplete, True, True) == "DEGRADED"
    assert preflight.classify(tmp_path, complete, False, True) == "DEGRADED"
    assert preflight.classify(tmp_path, complete, True, False) == "DEGRADED"


def test_native_boundaries_are_explicit_and_not_probed_here():
    assert set(preflight.NATIVE_BOUNDARIES) == {
        "real_lifecycle_hook_firing",
        "cross_session_durable_state_when_claimed",
        "effect_or_result_receipt_when_claimed",
    }
