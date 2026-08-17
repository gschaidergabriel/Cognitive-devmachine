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


def test_caught_inner_credit_failure_rolls_back_its_savepoint_only(tmp_path):
    db = _db(tmp_path)
    try:
        db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                "nested-credit-memory",
                "fact",
                "procedure:violet",
                "violet verified procedure",
                None,
                "gabriel",
                100.0,
                json.dumps({"source": "nested-credit-atomicity-test"}),
            ),
        )
        life = TurnLifecycle(
            db, "gabriel", "session:gabriel", entityos_bridge=_VerifiedEffectBridge()
        )
        turn = life.begin("violet verified procedure")
        effect = life.request_effect("entityos.exec", "nested-credit-atomicity", ["verified"])
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
        assert _policy_snapshot(db) == []
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0

        db.db.executescript(
            """
            CREATE TRIGGER fail_nested_retrieval_feedback_insert
            BEFORE INSERT ON retrieval_feedback
            BEGIN
              SELECT RAISE(ABORT, 'injected_nested_credit_failure');
            END;
            """
        )

        with db.tx() as outer:
            outer.execute(
                "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (
                    "outer-write-survives",
                    "fact",
                    "outer:transaction",
                    "unrelated outer write",
                    None,
                    "gabriel",
                    101.0,
                    json.dumps({"source": "outer-transaction-control"}),
                ),
            )
            with pytest.raises(sqlite3.IntegrityError, match="injected_nested_credit_failure"):
                organ.credit(
                    causal_id=turn["causal_id"],
                    generation=turn["generation"],
                    credit=float(causal["credit"]),
                    signal_class=signal,
                )
            assert db.db.in_transaction is True
            assert _policy_snapshot(db) == []
            assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0

        assert db.db.in_transaction is False
        assert db.db.execute(
            "SELECT value FROM durable_memory WHERE memory_id='outer-write-survives'"
        ).fetchone()["value"] == "unrelated outer write"
        assert _policy_snapshot(db) == []
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0

        db.db.execute("DROP TRIGGER fail_nested_retrieval_feedback_insert")
        applied = organ.credit(
            causal_id=turn["causal_id"],
            generation=turn["generation"],
            credit=float(causal["credit"]),
            signal_class=signal,
        )
        assert applied["applied"] is True
        once = _policy_snapshot(db)
        assert once
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
    finally:
        db.close()
