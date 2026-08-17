import json
import sqlite3

import pytest

from clayverse.method_memory import MethodMemoryValidationError
from clayverse.store import UnifiedDB


def _record(*, status="CANDIDATE", support_count=1, success_count=1, source_ids=None):
    return {
        "name": "bounded diagnostic transfer",
        "problem_signature": {
            "goal": "diagnose mechanism",
            "constraints": ["bounded tools"],
            "observables": ["receipt", "state delta"],
            "permissions": "read-only-first",
            "uncertainty": "fact_unknown_method_present",
        },
        "preconditions": ["canonical state readable"],
        "goal_shape": "identify a mechanism without inventing facts",
        "method_steps": ["retrieve evidence", "retrieve method if undercovered", "falsify"],
        "invariants": ["method context is not fact context"],
        "expected_observations": ["unknown remains explicit until evidence exists"],
        "falsifiers": ["direct evidence contradicts the proposed mechanism"],
        "failure_modes": [],
        "scope_limits": ["no truth authority"],
        "source_episode_ids": source_ids or ["episode:1"],
        "supporting_memory_ids": ["memory:evidence:1"],
        "counterexample_memory_ids": [],
        "abstraction_version": 1,
        "support_count": support_count,
        "success_count": success_count,
        "failure_count": 0,
        "calibration": 0.5,
        "last_validated_at": None if status == "CANDIDATE" else 1234.5,
        "status": status,
    }


def _db(tmp_path):
    return UnifiedDB(tmp_path / "unified.db")


def test_evidence_memory_path_is_unchanged(tmp_path):
    db = _db(tmp_path)
    try:
        mid = db.add_memory("fact", "topic", "plain text", None, "gabriel", {"source": "test"})
        row = db.db.execute("SELECT kind,value FROM durable_memory WHERE memory_id=?", (mid,)).fetchone()
        assert (row["kind"], row["value"]) == ("fact", "plain text")
    finally:
        db.close()


def test_candidate_roundtrips_canonically(tmp_path):
    db = _db(tmp_path)
    try:
        record = _record()
        mid = db.add_method_memory(
            "framework_candidate", "diagnostic-loop", record, None, "gabriel",
            {"source": "causal_episode", "contract": "meta-learning-v1"},
        )
        row = db.db.execute("SELECT value,provenance FROM durable_memory WHERE memory_id=?", (mid,)).fetchone()
        assert json.loads(row["value"]) == record
        assert row["value"] == json.dumps(record, sort_keys=True, separators=(",", ":"))
        assert json.loads(row["provenance"])["contract"] == "meta-learning-v1"
    finally:
        db.close()


def test_raw_sql_cannot_bypass_method_admission(tmp_path):
    db = _db(tmp_path)
    try:
        with pytest.raises(sqlite3.OperationalError):
            db.db.execute(
                "INSERT INTO durable_memory VALUES(?,?,?,?,?,?,?,?)",
                ("bad", "framework_candidate", "bad", "not-json", None, "gabriel", 1.0, "{}"),
            )
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0] == 0
    finally:
        db.close()


def test_raw_sql_cannot_relabel_fact_as_malformed_method(tmp_path):
    db = _db(tmp_path)
    try:
        mid = db.add_memory("fact", "topic", "plain text", None, "gabriel", {"source": "test"})
        with pytest.raises(sqlite3.OperationalError):
            db.db.execute("UPDATE durable_memory SET kind='framework_candidate' WHERE memory_id=?", (mid,))
        assert db.db.execute("SELECT kind FROM durable_memory WHERE memory_id=?", (mid,)).fetchone()[0] == "fact"
    finally:
        db.close()


def test_raw_sql_cannot_relabel_method_as_fact(tmp_path):
    db = _db(tmp_path)
    try:
        mid = db.add_method_memory(
            "framework_candidate", "method:x", _record(), None, "gabriel", {"source": "test"}
        )
        with pytest.raises(sqlite3.IntegrityError, match="cannot become evidence memory"):
            db.db.execute("UPDATE durable_memory SET kind='fact' WHERE memory_id=?", (mid,))
        assert db.db.execute("SELECT kind FROM durable_memory WHERE memory_id=?", (mid,)).fetchone()[0] == "framework_candidate"
    finally:
        db.close()


def test_single_success_cannot_be_promoted(tmp_path):
    db = _db(tmp_path)
    try:
        with pytest.raises(MethodMemoryValidationError, match="two supporting successful"):
            db.add_method_memory(
                "framework", "too-early", _record(status="PROMOTED"), None, "gabriel", {"source": "test"}
            )
    finally:
        db.close()


def test_two_distinct_successes_can_enter_promoted_shape(tmp_path):
    db = _db(tmp_path)
    try:
        record = _record(
            status="PROMOTED", support_count=2, success_count=2, source_ids=["episode:1", "episode:2"]
        )
        mid = db.add_method_memory("framework", "bounded", record, None, "gabriel", {"source": "test"})
        assert db.method_memory(mid)["record"]["status"] == "PROMOTED"
    finally:
        db.close()


def test_duplicate_source_episode_ids_do_not_fake_support(tmp_path):
    db = _db(tmp_path)
    try:
        record = _record(
            status="PROMOTED", support_count=2, success_count=2, source_ids=["episode:1", "episode:1"]
        )
        with pytest.raises(MethodMemoryValidationError, match="duplicates"):
            db.add_method_memory("framework", "duplicate", record, None, "gabriel", {"source": "test"})
    finally:
        db.close()


def test_nonfinite_calibration_fails_closed(tmp_path):
    db = _db(tmp_path)
    try:
        record = _record()
        record["calibration"] = float("nan")
        with pytest.raises(MethodMemoryValidationError):
            db.add_method_memory("framework_candidate", "nan", record, None, "gabriel", {"source": "test"})
    finally:
        db.close()


def test_restart_rejects_legacy_invalid_method_row(tmp_path):
    path = tmp_path / "unified.db"
    db = UnifiedDB(path)
    try:
        db.db.execute("DROP TRIGGER durable_method_memory_validate_insert")
        db.db.execute(
            "INSERT INTO durable_memory VALUES(?,?,?,?,?,?,?,?)",
            ("legacy-bad", "framework", "legacy", "{}", None, "gabriel", 1.0, "{}"),
        )
    finally:
        db.close()

    with pytest.raises(MethodMemoryValidationError, match="invalid persisted method memory legacy-bad"):
        UnifiedDB(path)


def test_candidate_status_smuggling_is_rejected(tmp_path):
    db = _db(tmp_path)
    try:
        record = _record(
            status="PROMOTED", support_count=2, success_count=2, source_ids=["episode:1", "episode:2"]
        )
        with pytest.raises(MethodMemoryValidationError, match="must remain CANDIDATE"):
            db.add_method_memory(
                "framework_candidate", "smuggled", record, None, "gabriel", {"source": "test"}
            )
    finally:
        db.close()
