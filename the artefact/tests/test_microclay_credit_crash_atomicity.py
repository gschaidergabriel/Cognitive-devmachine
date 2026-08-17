import json
import sqlite3

import pytest

from clayverse.identity import IdentityRouter
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


class _VerifiedEffectBridge:
    sha256 = "e" * 64

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
            "SELECT entry_key,capital,reward_ema,pulls FROM retrieval_entrypoint_policy ORDER BY entry_key"
        ).fetchall()
    ]


def test_feedback_insert_failure_rolls_back_policy_and_retry_applies_once(tmp_path):
    db = _db(tmp_path)
    try:
        db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                "atomic-memory",
                "fact",
                "procedure:orchid",
                "orchid verified procedure",
                None,
                "gabriel",
                100.0,
                json.dumps({"source": "crash-atomicity-test"}),
            ),
        )
        life = TurnLifecycle(
            db, "gabriel", "session:gabriel", entityos_bridge=_VerifiedEffectBridge()
        )
        turn = life.begin("orchid verified procedure")
        effect = life.request_effect("entityos.exec", "credit-crash-atomicity", ["verified"])
        assert effect["verified"] is True
        assert life.complete("done")["completed"] is True

        causal = db.db.execute(
            "SELECT c.credit,e.status FROM causal_episodes c "
            "JOIN effects e ON e.effect_id=c.effect_id "
            "WHERE c.causal_id=? AND c.reentered=1",
            (turn["causal_id"],),
        ).fetchone()
        assert causal is not None
        assert float(causal["credit"]) == 1.0
        signal = f"effect_outcome:{causal['status']}"
        organ = MicroClayRetrieval(db)
        memory_before = [tuple(row) for row in db.memories()]
        assert _policy_snapshot(db) == []
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0

        db.db.executescript(
            """
            CREATE TRIGGER fail_retrieval_feedback_insert
            BEFORE INSERT ON retrieval_feedback
            BEGIN
              SELECT RAISE(ABORT, 'injected_feedback_crash');
            END;
            """
        )
        with pytest.raises(sqlite3.IntegrityError, match="injected_feedback_crash"):
            organ.credit(
                causal_id=turn["causal_id"],
                generation=turn["generation"],
                credit=float(causal["credit"]),
                signal_class=signal,
            )

        assert db.db.in_transaction is False
        assert _policy_snapshot(db) == []
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        assert [tuple(row) for row in db.memories()] == memory_before

        db.db.execute("DROP TRIGGER fail_retrieval_feedback_insert")
        applied = organ.credit(
            causal_id=turn["causal_id"],
            generation=turn["generation"],
            credit=float(causal["credit"]),
            signal_class=signal,
        )
        assert applied["applied"] is True
        once = _policy_snapshot(db)
        assert once
        assert all(str(row[0]).startswith("v3:user:gabriel:") for row in once)
        assert all(int(row[3]) == 1 for row in once)
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 1

        replay = organ.credit(
            causal_id=turn["causal_id"],
            generation=turn["generation"],
            credit=float(causal["credit"]),
            signal_class=signal,
        )
        assert replay["applied"] is False
        assert replay["reason"] == "duplicate_receipt"
        assert _policy_snapshot(db) == once
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 1
        assert [tuple(row) for row in db.memories()] == memory_before
    finally:
        db.close()
