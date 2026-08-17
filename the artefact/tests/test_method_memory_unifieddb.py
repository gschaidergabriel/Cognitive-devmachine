import json
import sqlite3
import time

import pytest

from clayverse.method_memory import METHOD_SCHEMA_VERSION, MethodMemoryValidationError
from clayverse.store import UnifiedDB


def candidate_record(**overrides):
    value = {
        "problem_signature": {
            "goal": ["identify causal fault"],
            "constraint_shape": ["partial observability"],
            "evidence_shape": ["competing explanations"],
        },
        "preconditions": ["at least two plausible mechanisms remain"],
        "goal_shape": "separate competing causal mechanisms",
        "method_steps": ["generate alternatives", "derive discriminating predictions", "run cheapest falsifier"],
        "invariants": ["method memory is never factual authority"],
        "expected_observations": ["one intervention separates predictions"],
        "falsifiers": ["candidate predictions remain indistinguishable"],
        "failure_modes": ["proxy metric is not causally diagnostic"],
        "scope_limits": ["not for settled factual lookup"],
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
    value.update(overrides)
    return value


def promoted_record():
    return candidate_record(
        source_episode_ids=["episode:a", "episode:b"],
        support_count=2,
        success_count=2,
        calibration=0.7,
        last_validated_at=1234.5,
        status="PROMOTED",
    )


def test_unifieddb_method_candidate_roundtrips_through_strict_boundary(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        mid = db.add_method_memory(
            "framework_candidate",
            "causal discrimination",
            candidate_record(),
            None,
            "gabriel",
            {"source": "episode_abstraction"},
        )
        decoded = db.method_memory(mid)
        assert decoded["kind"] == "framework_candidate"
        assert decoded["value"]["status"] == "CANDIDATE"
        assert decoded["provenance"]["method_schema_version"] == METHOD_SCHEMA_VERSION
        assert db.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "6"
    finally:
        db.close()


def test_generic_fact_api_cannot_write_reserved_method_kind(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        with pytest.raises(MethodMemoryValidationError, match="reserved method-memory kind"):
            db.add_memory(
                "framework_candidate", "bypass", json.dumps(candidate_record()), None, "gabriel", {"source": "bypass"}
            )
    finally:
        db.close()


def test_raw_sql_valid_method_insert_still_requires_manager_capability(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        provenance = json.dumps({"source": "raw", "method_schema_version": 1}, sort_keys=True)
        value = json.dumps(candidate_record(), sort_keys=True, separators=(",", ":"))
        with pytest.raises(sqlite3.DatabaseError, match="canonical admission"):
            db.db.execute(
                "INSERT INTO durable_memory VALUES(?,?,?,?,?,?,?,?)",
                ("raw-valid", "framework_candidate", "raw", value, None, "gabriel", 1.0, provenance),
            )
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE memory_id='raw-valid'").fetchone()[0] == 0
    finally:
        db.close()


def test_raw_sql_malformed_method_insert_fails_closed(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        with pytest.raises(sqlite3.DatabaseError):
            db.db.execute(
                "INSERT INTO durable_memory VALUES(?,?,?,?,?,?,?,?)",
                ("bad", "framework_candidate", "bad", "not-json", None, "gabriel", 1.0, "{}"),
            )
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE memory_id='bad'").fetchone()[0] == 0
    finally:
        db.close()


def test_method_row_is_immutable_and_cannot_be_relabelled_as_fact(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        mid = db.add_method_memory(
            "framework_candidate", "method:x", candidate_record(), None, "gabriel", {"source": "test"}
        )
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            db.db.execute("UPDATE durable_memory SET kind='fact' WHERE memory_id=?", (mid,))
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            db.db.execute("UPDATE durable_memory SET subject='mutated' WHERE memory_id=?", (mid,))
        assert db.db.execute("SELECT kind FROM durable_memory WHERE memory_id=?", (mid,)).fetchone()[0] == "framework_candidate"
    finally:
        db.close()


def test_fact_row_cannot_be_relabelled_as_method(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        mid = db.add_memory("fact", "topic", "plain evidence", None, "gabriel", {"source": "test"})
        with pytest.raises(sqlite3.DatabaseError, match="cannot be relabeled"):
            db.db.execute("UPDATE durable_memory SET kind='framework_candidate' WHERE memory_id=?", (mid,))
        assert db.db.execute("SELECT kind FROM durable_memory WHERE memory_id=?", (mid,)).fetchone()[0] == "fact"
    finally:
        db.close()


def test_generic_method_admission_cannot_mint_promoted_framework(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        with pytest.raises(MethodMemoryValidationError, match="dedicated promotion lifecycle"):
            db.add_method_memory(
                "framework",
                "promoted",
                promoted_record(),
                None,
                "gabriel",
                {"source": "promotion", "promotion_receipt_id": "receipt:1"},
            )
    finally:
        db.close()


def test_dedicated_promotion_transaction_can_write_exact_promoted_row(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        db.ensure_user("gabriel", "Gabriel")
        session_id = db.ensure_session("gabriel", "clay-gabriel")
        supporting = [
            db.add_memory("fact", "evidence:a", "observed A", None, "gabriel", {"source": "test"}),
            db.add_memory("fact", "evidence:b", "observed B", None, "gabriel", {"source": "test"}),
        ]
        for episode_id in ("episode:a", "episode:b"):
            db.db.execute(
                "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) VALUES(?,?,?,?,?,?,?,?)",
                (episode_id, session_id, time.time(), None, 0.5, "[]", None, "CLOSED"),
            )
        candidate_id = db.add_method_memory(
            "framework_candidate",
            "transferable discriminator",
            candidate_record(
                source_episode_ids=["episode:a", "episode:b"],
                supporting_memory_ids=supporting,
                support_count=2,
                success_count=2,
                calibration=0.7,
            ),
            None,
            "gabriel",
            {"source": "episode_abstraction"},
        )
        result = db.promote_method_memory(
            candidate_id,
            evaluation="held-out structural transfer succeeded",
            provenance={"source": "held_out_evaluation"},
        )
        promoted = db.method_memory(result["promoted_memory_id"])
        receipt = db.method_memory(result["receipt_memory_id"])
        assert promoted["kind"] == "framework"
        assert promoted["value"]["status"] == "PROMOTED"
        assert promoted["provenance"]["promotion_receipt_id"] == result["receipt_memory_id"]
        assert receipt["value"]["action"] == "PROMOTE"
        assert receipt["value"]["method_memory_id"] == candidate_id
    finally:
        db.close()


def test_raw_sql_cannot_mint_promoted_framework(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        provenance = json.dumps(
            {"source": "promotion", "promotion_receipt_id": "receipt:forged", "method_schema_version": 1},
            sort_keys=True,
        )
        value = json.dumps(promoted_record(), sort_keys=True, separators=(",", ":"))
        with pytest.raises(sqlite3.DatabaseError, match="canonical admission"):
            db.db.execute(
                "INSERT INTO durable_memory VALUES(?,?,?,?,?,?,?,?)",
                ("forged", "framework", "forged", value, None, "gabriel", 1.0, provenance),
            )
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE memory_id='forged'").fetchone()[0] == 0
    finally:
        db.close()


def test_restart_rejects_legacy_invalid_reserved_row(tmp_path):
    path = tmp_path / "unified.db"
    db = UnifiedDB(path)
    try:
        db.db.execute("DROP TRIGGER durable_method_memory_admission_guard")
        db.db.execute("DROP TRIGGER durable_method_memory_validate_insert")
        db.db.execute(
            "INSERT INTO durable_memory VALUES(?,?,?,?,?,?,?,?)",
            ("legacy-bad", "framework_candidate", "legacy", "{}", None, "gabriel", 1.0, "{}"),
        )
    finally:
        db.close()

    with pytest.raises(MethodMemoryValidationError, match="invalid persisted method memory legacy-bad"):
        UnifiedDB(path)


def test_method_memory_cannot_be_deleted_raw(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        mid = db.add_method_memory(
            "framework_candidate", "method:x", candidate_record(), None, "gabriel", {"source": "test"}
        )
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            db.db.execute("DELETE FROM durable_memory WHERE memory_id=?", (mid,))
        assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE memory_id=?", (mid,)).fetchone()[0] == 1
    finally:
        db.close()


def test_normal_fact_memory_path_remains_unchanged(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        mid = db.add_memory("fact", "topic", "known value", None, "gabriel", {"source": "test"})
        row = db.db.execute("SELECT kind,value FROM durable_memory WHERE memory_id=?", (mid,)).fetchone()
        assert dict(row) == {"kind": "fact", "value": "known value"}
    finally:
        db.close()
