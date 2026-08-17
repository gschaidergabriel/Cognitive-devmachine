import json
import sqlite3
import time

import pytest

from clayverse.method_memory import METHOD_SCHEMA_VERSION, MethodMemoryValidationError
from clayverse.store import UnifiedDB


def candidate_record():
    return {
        "problem_signature": {
            "goal": ["identify causal fault"],
            "constraint_shape": ["partial observability"],
        },
        "preconditions": ["two mechanisms remain"],
        "goal_shape": "separate competing mechanisms",
        "method_steps": ["derive discriminator"],
        "invariants": ["unknown remains unknown"],
        "expected_observations": ["predictions separate"],
        "falsifiers": ["predictions do not separate"],
        "failure_modes": ["proxy overfit"],
        "scope_limits": ["requires observable discriminator"],
        "source_episode_ids": ["episode:a"],
        "supporting_memory_ids": [],
        "counterexample_memory_ids": [],
        "abstraction_version": "1",
        "support_count": 1,
        "success_count": 1,
        "failure_count": 0,
        "calibration": 0.5,
        "last_validated_at": None,
        "status": "CANDIDATE",
    }


def test_generic_memory_api_cannot_write_reserved_method_kind(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        with pytest.raises(MethodMemoryValidationError, match="reserved method-memory kind"):
            db.add_memory(
                "framework_candidate",
                "bypass",
                json.dumps(candidate_record()),
                None,
                "gabriel",
                {"source": "bypass"},
            )
    finally:
        db.close()


def test_raw_sql_valid_method_insert_requires_canonical_capability(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        value = json.dumps(candidate_record(), sort_keys=True, separators=(",", ":"))
        provenance = json.dumps(
            {"source": "raw", "method_schema_version": METHOD_SCHEMA_VERSION},
            sort_keys=True,
        )
        with pytest.raises(sqlite3.DatabaseError, match="canonical admission"):
            db.db.execute(
                "INSERT INTO durable_memory VALUES(?,?,?,?,?,?,?,?)",
                ("raw-method", "framework_candidate", "raw", value, None, "gabriel", time.time(), provenance),
            )
        assert db.db.execute(
            "SELECT COUNT(*) FROM durable_memory WHERE memory_id='raw-method'"
        ).fetchone()[0] == 0
    finally:
        db.close()


def test_method_rows_are_immutable_and_fact_rows_cannot_be_relabelled(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        mid = db.add_method_memory(
            "framework_candidate",
            "candidate",
            candidate_record(),
            None,
            "gabriel",
            {"source": "test"},
        )
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            db.db.execute("UPDATE durable_memory SET subject='mutated' WHERE memory_id=?", (mid,))
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            db.db.execute("DELETE FROM durable_memory WHERE memory_id=?", (mid,))

        fact_id = db.add_memory("fact", "topic", "known", None, "gabriel", {"source": "test"})
        with pytest.raises(sqlite3.DatabaseError, match="cannot be relabeled"):
            db.db.execute(
                "UPDATE durable_memory SET kind='framework_candidate' WHERE memory_id=?",
                (fact_id,),
            )
    finally:
        db.close()


def test_generic_method_admission_cannot_mint_promoted_framework(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        promoted = candidate_record()
        promoted.update(
            {
                "source_episode_ids": ["episode:a", "episode:b"],
                "support_count": 2,
                "success_count": 2,
                "calibration": 0.7,
                "last_validated_at": time.time(),
                "status": "PROMOTED",
            }
        )
        with pytest.raises(MethodMemoryValidationError, match="dedicated promotion lifecycle"):
            db.add_method_memory(
                "framework",
                "forged promotion",
                promoted,
                None,
                "gabriel",
                {"source": "forged", "promotion_receipt_id": "forged"},
            )
    finally:
        db.close()


def test_restart_rejects_invalid_persisted_method_row(tmp_path):
    path = tmp_path / "unified.db"
    db = UnifiedDB(path)
    try:
        db.db.execute("DROP TRIGGER durable_method_memory_admission_guard")
        db.db.execute("DROP TRIGGER durable_method_memory_validate_insert")
        db.db.execute(
            "INSERT INTO durable_memory VALUES(?,?,?,?,?,?,?,?)",
            ("legacy-bad", "framework_candidate", "bad", "{}", None, "gabriel", time.time(), "{}"),
        )
    finally:
        db.close()

    with pytest.raises(MethodMemoryValidationError, match="invalid persisted method memory legacy-bad"):
        UnifiedDB(path)


def test_normal_fact_path_and_schema7_remain_intact(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        mid = db.add_memory("fact", "topic", "known", None, "gabriel", {"source": "test"})
        row = db.db.execute("SELECT kind,value FROM durable_memory WHERE memory_id=?", (mid,)).fetchone()
        assert dict(row) == {"kind": "fact", "value": "known"}
        assert db.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "7"
    finally:
        db.close()
