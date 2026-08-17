import json
import time

import pytest

from clayverse.method_memory import MethodMemoryValidationError, decode_method_json
from clayverse.store import UnifiedDB


def _candidate(**updates):
    record = {
        "name": "counterhypothesis discriminator",
        "problem_signature": {
            "goal": "distinguish competing mechanisms",
            "uncertainty": "multiple_plausible_causes",
            "evidence_state": ["incomplete", "conflicting"],
        },
        "preconditions": ["at least two plausible mechanisms remain"],
        "goal_shape": "find the cheapest observation that separates the leading mechanisms",
        "method_steps": [
            "state the leading mechanism",
            "state the strongest counterhypothesis",
            "derive divergent predictions",
            "run the cheapest discriminating test",
        ],
        "invariants": ["unknown facts remain unknown until evidence resolves them"],
        "expected_observations": ["the test changes relative support between hypotheses"],
        "falsifiers": ["both mechanisms predict the same observed outcome"],
        "failure_modes": ["choosing a broad test that cannot discriminate"],
        "scope_limits": ["not suitable when no competing mechanism can be articulated"],
        "source_episode_ids": ["episode:1"],
        "supporting_memory_ids": [],
        "counterexample_memory_ids": [],
        "abstraction_version": 1,
        "support_count": 1,
        "success_count": 1,
        "failure_count": 0,
        "calibration": 0.5,
        "last_validated_at": None,
        "status": "CANDIDATE",
    }
    record.update(updates)
    return record


def _promoted(**updates):
    record = _candidate(
        support_count=3,
        success_count=2,
        failure_count=1,
        calibration=0.67,
        last_validated_at=1234.5,
        status="PROMOTED",
    )
    record.update(updates)
    return record


def test_reserved_method_kind_cannot_bypass_admission(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        with pytest.raises(MethodMemoryValidationError, match="requires add_method_memory"):
            db.add_memory("framework", "method:test", "{}", None, "gabriel", {"source": "test"})
    finally:
        db.close()


def test_framework_candidate_roundtrips_as_canonical_json_without_schema_bump(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        record = _candidate()
        mid = db.add_method_memory(
            "framework_candidate",
            "method:discriminator",
            record,
            None,
            "gabriel",
            {"source": "test", "authority": "bounded_episode"},
        )
        row = db.db.execute("SELECT * FROM durable_memory WHERE memory_id=?", (mid,)).fetchone()
        assert row["kind"] == "framework_candidate"
        assert row["value"] == json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        assert db.method_memory(mid)["record"] == record
        assert db.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "6"
    finally:
        db.close()


def test_promoted_framework_requires_noncandidate_lifecycle_and_validation_time(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        with pytest.raises(MethodMemoryValidationError, match="last_validated_at"):
            db.add_method_memory(
                "framework", "method:x", _promoted(last_validated_at=None), None, "gabriel", {"source": "test"}
            )
        with pytest.raises(MethodMemoryValidationError, match="cannot carry CANDIDATE"):
            db.add_method_memory(
                "framework", "method:x", _candidate(), None, "gabriel", {"source": "test"}
            )
    finally:
        db.close()


def test_under_specified_framework_fails_closed(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        record = _promoted()
        del record["falsifiers"]
        with pytest.raises(MethodMemoryValidationError, match="falsifiers"):
            db.add_method_memory("framework", "method:x", record, None, "gabriel", {"source": "test"})
    finally:
        db.close()


def test_nonfinite_calibration_and_inconsistent_counts_fail_closed(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        with pytest.raises(MethodMemoryValidationError, match="calibration"):
            db.add_method_memory(
                "framework_candidate", "method:x", _candidate(calibration=float("nan")), None, "gabriel", {"source": "test"}
            )
        with pytest.raises(MethodMemoryValidationError, match="support_count"):
            db.add_method_memory(
                "framework_candidate",
                "method:x",
                _candidate(support_count=1, success_count=1, failure_count=1),
                None,
                "gabriel",
                {"source": "test"},
            )
    finally:
        db.close()


def test_raw_or_legacy_malformed_method_row_is_rejected_on_read(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            ("bad-method", "framework", "method:bad", "{}", None, "gabriel", time.time(), "{}"),
        )
        with pytest.raises(MethodMemoryValidationError):
            db.method_memory("bad-method")
        with pytest.raises(MethodMemoryValidationError):
            db.method_memories()
    finally:
        db.close()


def test_counterexample_requires_explicit_target_and_conditions(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        record = {
            "name": "lexical lookalike is structurally different",
            "problem_signature": {"surface_overlap": "high", "causal_structure": "different"},
            "conditions": ["same vocabulary but different dependency structure"],
            "contradiction": "the method's key precondition is absent",
            "target_method_ids": ["method:target"],
            "source_episode_ids": ["episode:counterexample"],
            "supporting_memory_ids": ["evidence:1"],
            "counterexample_memory_ids": [],
            "abstraction_version": 1,
            "status": "PROMOTED",
            "last_validated_at": 5.0,
        }
        mid = db.add_method_memory(
            "counterexample", "method:counterexample", record, None, "gabriel", {"source": "test"}
        )
        assert db.method_memory(mid)["record"]["target_method_ids"] == ["method:target"]
        broken = dict(record)
        broken["target_method_ids"] = []
        with pytest.raises(MethodMemoryValidationError, match="target_method_ids"):
            db.add_method_memory(
                "counterexample", "method:counterexample", broken, None, "gabriel", {"source": "test"}
            )
    finally:
        db.close()


def test_method_receipt_must_reference_existing_method_memory(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        candidate_id = db.add_method_memory(
            "framework_candidate", "method:x", _candidate(), None, "gabriel", {"source": "test"}
        )
        receipt = {
            "action": "EVALUATE",
            "method_memory_id": candidate_id,
            "causal_id": "causal:1",
            "episode_id": "episode:1",
            "generation": 1,
            "result": "retained_as_candidate",
            "details": {"held_out": False},
        }
        receipt_id = db.add_method_memory(
            "method_receipt", "method:receipt", receipt, None, "gabriel", {"source": "test"}
        )
        assert db.method_memory(receipt_id)["record"]["method_memory_id"] == candidate_id
        receipt["method_memory_id"] = "missing"
        with pytest.raises(MethodMemoryValidationError, match="existing non-receipt"):
            db.add_method_memory(
                "method_receipt", "method:receipt", receipt, None, "gabriel", {"source": "test"}
            )
    finally:
        db.close()


def test_normal_fact_memory_path_remains_unchanged(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        mid = db.add_memory("fact", "topic:test", "known value", None, "gabriel", {"source": "test"})
        row = db.db.execute("SELECT kind,value FROM durable_memory WHERE memory_id=?", (mid,)).fetchone()
        assert dict(row) == {"kind": "fact", "value": "known value"}
        with pytest.raises(MethodMemoryValidationError, match="not method memory"):
            db.method_memory(mid)
    finally:
        db.close()


def test_decoder_never_turns_method_into_fact_status():
    record = _candidate()
    value = json.dumps(record)
    decoded = decode_method_json("framework_candidate", value)
    assert decoded["status"] == "CANDIDATE"
    assert "fact_status" not in decoded
