import json
import sqlite3
import time
import uuid

import pytest

from clayverse.identity import IdentityRouter
from clayverse.method_memory import MethodMemoryManager, MethodMemoryValidationError
from clayverse.store import UnifiedDB


def _candidate_record(episodes):
    return {
        "problem_signature": {"task_shape": ["diagnose"], "evidence_state": ["unknown"]},
        "preconditions": ["bounded_input"],
        "goal_shape": "identify_mechanism",
        "method_steps": ["generate_competing_mechanisms", "run_discriminator"],
        "invariants": ["facts_remain_evidence_bound"],
        "expected_observations": ["mechanisms_separate_under_test"],
        "falsifiers": ["discriminator_does_not_separate"],
        "failure_modes": ["proxy_match"],
        "scope_limits": ["method_guidance_only"],
        "source_episode_ids": list(episodes),
        "supporting_memory_ids": [],
        "counterexample_memory_ids": [],
        "abstraction_version": "v1",
        "support_count": 2,
        "success_count": 2,
        "failure_count": 0,
        "calibration": 0.75,
        "last_validated_at": None,
        "status": "CANDIDATE",
    }


def _terminal_episode(db, label):
    turn_id = db.append_turn("session:gabriel", "gabriel", "user", label)
    episode_id = str(uuid.uuid4())
    db.db.execute(
        "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, "session:gabriel", time.time(), turn_id, 0.5, "[]", None, "COMPLETED"),
    )
    db.db.execute(
        "INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), episode_id, None, turn_id, "test-outcome", 1.0, 1, time.time()),
    )
    return episode_id


def test_generic_and_raw_sql_method_writes_fail_closed_but_manager_admission_succeeds(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    try:
        record = _candidate_record(["episode:a", "episode:b"])
        with pytest.raises(MethodMemoryValidationError, match="reserved method-memory kind"):
            db.add_memory(
                "framework_candidate", "candidate", json.dumps(record), None, "gabriel", {"source": "bypass"}
            )

        with pytest.raises(sqlite3.IntegrityError, match="canonical admission"):
            db.db.execute(
                "INSERT INTO durable_memory VALUES(?,?,?,?,?,?,?,?)",
                (
                    str(uuid.uuid4()), "framework_candidate", "candidate", json.dumps(record),
                    None, "gabriel", time.time(), json.dumps({"source": "raw-sql"}),
                ),
            )

        candidate_id = MethodMemoryManager(db).admit(
            "framework_candidate", "candidate", record, None, "gabriel", {"source": "manager"}
        )
        assert db.method_memory(candidate_id)["kind"] == "framework_candidate"

        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            db.db.execute("UPDATE durable_memory SET user_id='andreas' WHERE memory_id=?", (candidate_id,))
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            db.db.execute("DELETE FROM durable_memory WHERE memory_id=?", (candidate_id,))
    finally:
        db.close()


def test_startup_rejects_promoted_method_after_receipt_lineage_is_removed(tmp_path):
    path = tmp_path / "unified.db"
    db = UnifiedDB(path)
    IdentityRouter(db, {})
    e1 = _terminal_episode(db, "source one")
    e2 = _terminal_episode(db, "source two")
    manager = MethodMemoryManager(db)
    candidate_id = manager.admit(
        "framework_candidate", "candidate", _candidate_record([e1, e2]), None, "gabriel", {"source": "test"}
    )
    promoted = manager.promote(
        candidate_id,
        evaluation="two terminal re-entered episodes",
        provenance={"source": "test-promotion"},
    )
    receipt_id = promoted["receipt_memory_id"]
    db.close()

    raw = sqlite3.connect(path)
    try:
        raw.execute("DROP TRIGGER durable_method_memory_no_delete")
        raw.execute("DELETE FROM durable_memory WHERE memory_id=?", (receipt_id,))
        raw.commit()
    finally:
        raw.close()

    with pytest.raises(MethodMemoryValidationError, match="promotion lineage"):
        UnifiedDB(path)
