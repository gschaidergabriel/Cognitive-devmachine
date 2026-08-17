import json
import sqlite3
import time

import pytest

from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB


def _seed_retrieval(db: UnifiedDB):
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clay-gabriel")
    generation = db.entity_generation()
    turn_id = "turn:atomic-credit"
    episode_id = "episode:atomic-credit"
    causal_id = "causal:atomic-credit"
    now = time.time()
    db.db.execute(
        "INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) "
        "VALUES(?,?,?,?,?,?,?,?,?,?)",
        (turn_id, session_id, "gabriel", 1, now, "user", "orchid codename", "[]", "[]", "{}"),
    )
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, now, turn_id, 0.5, "[]", None, "OPEN"),
    )
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            "memory:atomic-credit",
            "fact",
            "procedure:orchid",
            "orchid procedure",
            None,
            "gabriel",
            now,
            json.dumps({"source": "atomic-credit-test"}),
        ),
    )
    organ = MicroClayRetrieval(db)
    result = organ.retrieve(
        query="orchid codename",
        user_id="gabriel",
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        limit=8,
        budget_chars=4096,
    )
    assert result["items"]
    return organ, causal_id, generation


def _policy_snapshot(db: UnifiedDB):
    return [
        tuple(row)
        for row in db.db.execute(
            "SELECT entry_key,capital,reward_ema,pulls FROM retrieval_entrypoint_policy ORDER BY entry_key"
        ).fetchall()
    ]


def test_credit_rolls_back_capital_if_feedback_receipt_insert_crashes(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        organ, causal_id, generation = _seed_retrieval(db)
        memory_before = [tuple(row) for row in db.memories()]
        policy_before = _policy_snapshot(db)
        assert policy_before == []

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
                causal_id=causal_id,
                generation=generation,
                credit=1.0,
                signal_class="effect_outcome:VERIFIED",
                receipt_id="receipt:atomic-credit",
            )

        assert db.db.in_transaction is False
        assert _policy_snapshot(db) == policy_before
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        assert [tuple(row) for row in db.memories()] == memory_before

        db.db.execute("DROP TRIGGER fail_retrieval_feedback_insert")
        applied = organ.credit(
            causal_id=causal_id,
            generation=generation,
            credit=1.0,
            signal_class="effect_outcome:VERIFIED",
            receipt_id="receipt:atomic-credit",
        )
        assert applied["applied"] is True
        once = _policy_snapshot(db)
        assert once
        assert all(int(row[3]) == 1 for row in once)
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 1

        duplicate = organ.credit(
            causal_id=causal_id,
            generation=generation,
            credit=1.0,
            signal_class="effect_outcome:VERIFIED",
            receipt_id="receipt:atomic-credit",
        )
        assert duplicate == {
            "applied": False,
            "reason": "duplicate_receipt",
            "receipt_id": "receipt:atomic-credit",
        }
        assert _policy_snapshot(db) == once
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 1
        assert [tuple(row) for row in db.memories()] == memory_before
    finally:
        db.close()
