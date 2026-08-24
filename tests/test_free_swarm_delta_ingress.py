import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from free_swarm_delta_ingress import parse_questions, parse_worker_delta  # noqa: E402


def proposal(**overrides):
    obj = {
        "delta_id": "worker-7-loader-proof",
        "hypothesis": "bind consumed bytes",
        "mechanism": "receipt edge",
        "target_files": ["tools/x.py"],
        "patch_unified_diff": "--- a/tools/x.py\n+++ b/tools/x.py\n@@ -1 +1 @@\n-a\n+b\n",
        "test_commands": ["python -m pytest -q tests/test_x.py"],
        "benchmark_command": "",
        "metric": "causal_binding",
        "expected_direction": "boolean",
        "baseline_needed": True,
        "falsifier": "mutated loader bytes still pass",
        "risk": "receipt-only overclaim",
        "ready_for_forge": True,
    }
    obj.update(overrides)
    return obj


def parse(obj):
    return parse_worker_delta("ARCHITECTURE_DELTA_JSON=" + json.dumps(obj))


def test_valid_ready_round_trip():
    obj = proposal()
    text = "x\nARCHITECTURE_DELTA_JSON=" + json.dumps(obj) + "\nOPEN_RESEARCH_QUESTIONS_JSON=[\"q1\",\"q2\"]"
    got = parse_worker_delta(text)
    assert got["status"] == "VALID_READY"
    assert got["valid"] is True
    assert got["proposal"] == obj
    assert len(got["proposal_sha256"]) == 64
    assert parse_questions(text) == ["q1", "q2"]


def test_missing_and_malformed_are_distinct():
    assert parse_worker_delta("plain text")["status"] == "MISSING"
    assert parse_worker_delta("ARCHITECTURE_DELTA_JSON={bad")["status"] == "MALFORMED"


def test_marker_does_not_skip_untyped_prose_to_later_json():
    got = parse_worker_delta("ARCHITECTURE_DELTA_JSON=not-the-payload " + json.dumps(proposal()))
    assert got["status"] == "MALFORMED"


def test_ready_requires_patch_targets_and_tests():
    got = parse(proposal(patch_unified_diff=""))
    assert got["status"] == "SCHEMA_INVALID"
    assert "READY_MISSING_PATCH" in got["reasons"]


def test_target_path_escape_rejected():
    got = parse(proposal(target_files=["../x.py"]))
    assert got["status"] == "SCHEMA_INVALID"
    assert "INVALID_TARGET_FILES" in got["reasons"]


def test_patch_header_path_escape_rejected():
    got = parse(proposal(patch_unified_diff="--- a/tools/x.py\n+++ b/../../escape.py\n@@ -1 +1 @@\n-a\n+b\n"))
    assert got["status"] == "SCHEMA_INVALID"
    assert "INVALID_PATCH" in got["reasons"]


def test_ready_patch_cannot_modify_undeclared_file():
    patch = (
        "--- a/tools/x.py\n+++ b/tools/x.py\n@@ -1 +1 @@\n-a\n+b\n"
        "--- a/tools/hidden.py\n+++ b/tools/hidden.py\n@@ -1 +1 @@\n-a\n+b\n"
    )
    got = parse(proposal(patch_unified_diff=patch, target_files=["tools/x.py"]))
    assert got["status"] == "SCHEMA_INVALID"
    assert "PATCH_TARGET_MISMATCH" in got["reasons"]


def test_ready_declared_target_must_be_present_in_patch():
    got = parse(proposal(target_files=["tools/x.py", "tools/phantom.py"]))
    assert got["status"] == "SCHEMA_INVALID"
    assert "PATCH_TARGET_MISMATCH" in got["reasons"]


def test_forge_forbidden_command_rejected_at_ingress():
    got = parse(proposal(test_commands=["sudo python -m pytest -q"]))
    assert got["status"] == "SCHEMA_INVALID"
    assert "INVALID_TEST_COMMANDS" in got["reasons"]


def test_non_ready_may_be_design_only_but_still_typed():
    got = parse(proposal(
        ready_for_forge=False,
        patch_unified_diff="",
        target_files=[],
        test_commands=[],
    ))
    assert got["status"] == "VALID_NOT_READY"
    assert got["valid"] is True
    assert got["ready_for_forge"] is False
