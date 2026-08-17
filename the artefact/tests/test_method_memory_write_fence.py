from __future__ import annotations

import json
import sqlite3

import pytest

from clayverse.store import UnifiedDB


def _candidate_value():
    return json.dumps(
        {
            "schema": "clayverse.method/v1",
            "problem_signature": ["bounded causal diagnosis"],
            "preconditions": ["uncertainty remains"],
            "goal_shape": "separate candidate mechanisms",
            "method_steps": ["derive a falsifier"],
            "invariants": ["method is not fact"],
            "expected_observations": ["mechanisms diverge"],
            "falsifiers": ["predictions remain identical"],
            "failure_modes": ["proxy mismatch"],
            "scope_limits": ["shadow only"],
            "source_episode_ids": ["episode:a"],
            "supporting_memory_ids": [],
            "counterexample_memory_ids": [],
            "abstraction_version": 1,
            "support_count": 1,
            "success_count": 1,
            "failure_count": 0,
            "calibration": 0.5,
            "last_validated_at": None,
            "status": "CANDIDATE",
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def test_public_memory_api_rejects_reserved_method_kind_and_preserves_fact_path(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        with pytest.raises(ValueError, match="canonical method admission"):
            db.add_memory(
                "framework_candidate",
                "candidate",
                _candidate_value(),
                None,
                "gabriel",
                {"source": "test"},
            )
        fact_id = db.add_memory("fact", "topic", "known", None, "gabriel", {"source": "test"})
        row = db.db.execute("SELECT kind,value FROM durable_memory WHERE memory_id=?", (fact_id,)).fetchone()
        assert dict(row) == {"kind": "fact", "value": "known"}
    finally:
        db.close()


def test_valid_looking_raw_sql_cannot_mint_reserved_method_memory(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        with pytest.raises(sqlite3.DatabaseError, match="canonical admission"):
            db.db.execute(
                "INSERT INTO durable_memory VALUES(?,?,?,?,?,?,?,?)",
                (
                    "raw-method",
                    "framework_candidate",
                    "candidate",
                    _candidate_value(),
                    None,
                    "gabriel",
                    1.0,
                    json.dumps({"source": "raw"}, sort_keys=True),
                ),
            )
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE memory_id='raw-method'").fetchone()[0] == 0
    finally:
        db.close()


def test_private_fixture_row_is_immutable_to_raw_sql(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        memory_id = db._insert_method_memory(
            "framework_candidate",
            "fixture",
            _candidate_value(),
            None,
            "gabriel",
            {"source": "reader-test-fixture", "fixture_only": True},
        )
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            db.db.execute("UPDATE durable_memory SET subject='mutated' WHERE memory_id=?", (memory_id,))
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            db.db.execute("UPDATE durable_memory SET kind='fact' WHERE memory_id=?", (memory_id,))
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            db.db.execute("DELETE FROM durable_memory WHERE memory_id=?", (memory_id,))
        row = db.db.execute("SELECT kind,subject FROM durable_memory WHERE memory_id=?", (memory_id,)).fetchone()
        assert dict(row) == {"kind": "framework_candidate", "subject": "fixture"}
    finally:
        db.close()


def test_reserved_write_guard_survives_reopen(tmp_path):
    path = tmp_path / "u.db"
    db = UnifiedDB(path)
    db.close()

    reopened = UnifiedDB(path)
    try:
        with pytest.raises(sqlite3.DatabaseError, match="canonical admission"):
            reopened.db.execute(
                "INSERT INTO durable_memory VALUES(?,?,?,?,?,?,?,?)",
                (
                    "raw-after-reopen",
                    "framework_candidate",
                    "candidate",
                    _candidate_value(),
                    None,
                    "gabriel",
                    1.0,
                    json.dumps({"source": "raw"}, sort_keys=True),
                ),
            )
    finally:
        reopened.close()
