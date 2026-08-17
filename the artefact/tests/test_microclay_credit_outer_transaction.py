from __future__ import annotations

import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


class _VerifiedEffectBridge:
    sha256 = "a" * 64

    def run(self, argv):
        return {"ok": True, "exit": 0, "stdout": "", "stderr": ""}


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _policy_snapshot(db):
    return [
        tuple(row)
        for row in db.db.execute(
            "SELECT entry_key,capital,reward_ema,pulls,updated_at "
            "FROM retrieval_entrypoint_policy ORDER BY entry_key"
        ).fetchall()
    ]


def _prepare_verified_uncredited_outcome(db):
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            "outer-tx-memory",
            "fact",
            "procedure:outer-orchid",
            "outer orchid verified procedure",
            None,
            "gabriel",
            100.0,
            json.dumps({"source": "test"}),
        ),
    )
    life = TurnLifecycle(
        db,
        "gabriel",
        "session:gabriel",
        entityos_bridge=_VerifiedEffectBridge(),
    )
    first = life.begin("outer orchid verified procedure")
    effect = life.request_effect("entityos.exec", "outer-tx-credit", ["verified-outcome"])
    assert effect["verified"] is True
    assert life.complete("done")["completed"] is True
    assert db.db.execute(
        "SELECT COUNT(*) FROM retrieval_feedback WHERE causal_id=?", (first["causal_id"],)
    ).fetchone()[0] == 0
    return life, first


def test_outcome_credit_joins_outer_turn_transaction_and_rolls_back_with_it(tmp_path):
    db = _db(tmp_path)
    try:
        life, first = _prepare_verified_uncredited_outcome(db)
        before_policy = _policy_snapshot(db)
        before_feedback = db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0]
        before_turns = db.db.execute("SELECT COUNT(*) FROM turns").fetchone()[0]

        with pytest.raises(RuntimeError, match="rollback outer admission"):
            with life.begin_admission("second outer orchid request") as admitted:
                # World assembly has already consumed the verified prior outcome here.
                # Credit must have joined begin_admission's existing transaction rather
                # than attempting a nested BEGIN IMMEDIATE.
                assert admitted["context"]["retrieval_receipt"]["outcome_learning_applied"] == 1
                assert db.db.execute(
                    "SELECT COUNT(*) FROM retrieval_feedback WHERE causal_id=?",
                    (first["causal_id"],),
                ).fetchone()[0] == 1
                assert _policy_snapshot(db) != before_policy
                raise RuntimeError("rollback outer admission")

        # The enclosing turn transaction owns the learning mutation. Its rollback must
        # therefore remove both the policy delta and feedback receipt together.
        assert db.db.in_transaction is False
        assert _policy_snapshot(db) == before_policy
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == before_feedback
        assert db.db.execute("SELECT COUNT(*) FROM turns").fetchone()[0] == before_turns

        retry = life.begin("second outer orchid request")
        assert retry["context"]["retrieval_receipt"]["outcome_learning_applied"] == 1
        after_once = _policy_snapshot(db)
        assert after_once != before_policy
        assert db.db.execute(
            "SELECT COUNT(*) FROM retrieval_feedback WHERE causal_id=?", (first["causal_id"],)
        ).fetchone()[0] == 1

        # Re-checking the same verified prior outcome cannot apply it twice.
        assert life.world.microclay.learn_from_verified_outcomes(
            session_id="session:gabriel", generation=retry["generation"]
        ) == {"eligible": 0, "applied": 0}
        assert _policy_snapshot(db) == after_once
        life.abort("test-end")
    finally:
        db.close()
