from __future__ import annotations

import json
import sqlite3

import pytest

from clayverse.identity import IdentityRouter
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _verified_retrieval(tmp_path):
    db = _db(tmp_path)
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            "atomic-credit-memory",
            "fact",
            "procedure:atomic-orchid",
            "atomic orchid verified procedure",
            None,
            "gabriel",
            100.0,
            json.dumps({"source": "test"}),
        ),
    )
    life = TurnLifecycle(db, "gabriel", "session:gabriel")
    turn = life.begin("atomic orchid verified procedure")
    effect = life.request_effect("state.noop", "atomic-credit-test")
    assert effect["verified"] is True
    life.complete("done")
    causal = db.db.execute(
        "SELECT c.credit,e.status FROM causal_episodes c JOIN effects e ON e.effect_id=c.effect_id "
        "WHERE c.causal_id=? AND c.reentered=1",
        (turn["causal_id"],),
    ).fetchone()
    assert causal is not None
    return db, turn, float(causal["credit"]), f"effect_outcome:{causal['status']}"


def _policy_snapshot(db):
    return [
        tuple(row)
        for row in db.db.execute(
            "SELECT entry_key,capital,reward_ema,pulls,updated_at "
            "FROM retrieval_entrypoint_policy ORDER BY entry_key"
        ).fetchall()
    ]


def _memory_snapshot(db):
    return [
        tuple(row)
        for row in db.db.execute(
            "SELECT memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance "
            "FROM durable_memory ORDER BY memory_id"
        ).fetchall()
    ]


def test_credit_fault_before_feedback_rolls_back_policy_then_retry_commits_once(tmp_path):
    db, turn, credit, signal = _verified_retrieval(tmp_path)
    organ = MicroClayRetrieval(db)
    try:
        before_policy = _policy_snapshot(db)
        before_feedback = db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0]
        before_memory = _memory_snapshot(db)

        db.db.execute(
            "CREATE TRIGGER fail_microclay_feedback BEFORE INSERT ON retrieval_feedback "
            "BEGIN SELECT RAISE(ABORT, 'injected feedback fault'); END"
        )
        with pytest.raises(sqlite3.DatabaseError, match="injected feedback fault"):
            organ.credit(
                causal_id=turn["causal_id"],
                generation=turn["generation"],
                credit=credit,
                signal_class=signal,
            )
        db.db.execute("DROP TRIGGER fail_microclay_feedback")

        assert _policy_snapshot(db) == before_policy
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == before_feedback
        assert _memory_snapshot(db) == before_memory

        accepted = organ.credit(
            causal_id=turn["causal_id"],
            generation=turn["generation"],
            credit=credit,
            signal_class=signal,
        )
        after_once = _policy_snapshot(db)
        assert accepted["applied"] is True
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == before_feedback + 1
        assert after_once != before_policy
        assert all(int(row[3]) == 1 for row in after_once)

        replay = organ.credit(
            causal_id=turn["causal_id"],
            generation=turn["generation"],
            credit=credit,
            signal_class=signal,
        )
        assert replay["applied"] is False
        assert replay["reason"] == "duplicate_receipt"
        assert _policy_snapshot(db) == after_once
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == before_feedback + 1
        assert _memory_snapshot(db) == before_memory
    finally:
        db.close()


def test_credit_joined_to_turn_admission_rolls_back_with_outer_transaction_then_retries_once(tmp_path):
    db, first, credit, signal = _verified_retrieval(tmp_path)
    life = TurnLifecycle(db, "gabriel", "session:gabriel")
    organ = MicroClayRetrieval(db)
    try:
        before_policy = _policy_snapshot(db)
        before_feedback = db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0]
        before_memory = _memory_snapshot(db)

        with pytest.raises(RuntimeError, match="injected admission rollback"):
            with life.begin_admission("atomic orchid verified procedure followup") as admitted:
                assert admitted["context"]["retrieval_receipt"]["outcome_learning_applied"] == 1
                assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == before_feedback + 1
                assert _policy_snapshot(db) != before_policy
                raise RuntimeError("injected admission rollback")

        assert life.active() is None
        assert _policy_snapshot(db) == before_policy
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == before_feedback
        assert _memory_snapshot(db) == before_memory

        retry = life.begin("atomic orchid verified procedure followup")
        assert retry["context"]["retrieval_receipt"]["outcome_learning_applied"] == 1
        after_once = _policy_snapshot(db)
        assert after_once != before_policy
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == before_feedback + 1

        replay = organ.credit(
            causal_id=first["causal_id"],
            generation=first["generation"],
            credit=credit,
            signal_class=signal,
        )
        assert replay["applied"] is False
        assert replay["reason"] == "duplicate_receipt"
        assert _policy_snapshot(db) == after_once
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == before_feedback + 1
        assert _memory_snapshot(db) == before_memory
        life.abort("test-end")
    finally:
        db.close()
