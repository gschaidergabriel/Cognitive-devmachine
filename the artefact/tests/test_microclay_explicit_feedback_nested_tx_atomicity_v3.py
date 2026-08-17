import sqlite3

import pytest

from clayverse.identity import IdentityRouter
from clayverse.microclay_feedback import MicroClayExplicitFeedback
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def test_caught_inner_feedback_failure_rolls_back_savepoint_without_poisoning_outer_tx(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        IdentityRouter(db, {})
        target_memory_id = db.add_memory(
            "fact",
            "topic:orchid",
            "orchid procedure",
            None,
            "gabriel",
            {"source": "nested-explicit-feedback-atomicity-test"},
        )
        lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
        begun = lifecycle.begin("codename")
        row = db.db.execute(
            "SELECT * FROM retrieval_episodes WHERE causal_id=?",
            (begun["causal_id"],),
        ).fetchone()
        assert row is not None

        request = {
            "retrieval_id": row["retrieval_id"],
            "user_id": row["user_id"],
            "session_id": row["session_id"],
            "turn_id": row["turn_id"],
            "episode_id": row["episode_id"],
            "causal_id": row["causal_id"],
            "generation": int(row["generation"]),
            "query_sha256": row["query_hash"],
            "budget_chars": int(row["budget_chars"]),
            "limit_items": int(row["limit_items"]),
            "feedback_class": "USER_MISS_TARGET",
            "source": "USER_EXPLICIT",
            "target_memory_id": target_memory_id,
        }
        organ = MicroClayExplicitFeedback(db)

        db.db.executescript(
            """
            CREATE TRIGGER fail_explicit_feedback_receipt
            BEFORE INSERT ON retrieval_feedback
            WHEN NEW.signal_class LIKE 'user_explicit:v3:%'
            BEGIN
              SELECT RAISE(ABORT, 'injected_explicit_feedback_crash');
            END;
            """
        )

        with db.tx() as outer:
            with pytest.raises(sqlite3.IntegrityError, match="injected_explicit_feedback_crash"):
                organ.apply(**request)

            assert db.db.in_transaction is True
            assert outer.execute(
                "SELECT COUNT(*) FROM retrieval_feedback WHERE signal_class LIKE 'user_explicit:v3:%'"
            ).fetchone()[0] == 0
            assert outer.execute(
                "SELECT COUNT(*) FROM retrieval_entrypoint_policy"
            ).fetchone()[0] == 0
            outer.execute(
                "UPDATE sessions SET last_seen=last_seen WHERE session_id=?",
                (row["session_id"],),
            )

        assert db.db.in_transaction is False
        assert db.db.execute(
            "SELECT COUNT(*) FROM retrieval_feedback WHERE signal_class LIKE 'user_explicit:v3:%'"
        ).fetchone()[0] == 0
        assert db.db.execute(
            "SELECT COUNT(*) FROM retrieval_entrypoint_policy"
        ).fetchone()[0] == 0

        db.db.execute("DROP TRIGGER fail_explicit_feedback_receipt")
        applied = organ.apply(**request)
        assert applied["applied"] is True
        assert applied["updated_entrypoints"] == 1
        assert db.db.execute(
            "SELECT COUNT(*) FROM retrieval_feedback WHERE signal_class LIKE 'user_explicit:v3:%'"
        ).fetchone()[0] == 1
        assert db.db.execute(
            "SELECT COUNT(*) FROM retrieval_entrypoint_policy"
        ).fetchone()[0] == 1
        lifecycle.abort("test-end")
    finally:
        db.close()
