import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.microclay_feedback import apply_explicit_retrieval_miss
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def test_explicit_miss_feedback_joins_outer_transaction_and_rolls_back(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    try:
        db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                "target",
                "fact",
                "topic:target",
                "vault-entry-742",
                None,
                "gabriel",
                1.0,
                json.dumps({"source": "test"}),
            ),
        )
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        first = life.begin("orchid alias")
        retrieval_id = first["context"]["retrieval_receipt"]["retrieval_id"]
        life.abort("feedback-boundary")
        feedback_turn = db.append_turn(
            "session:gabriel",
            "gabriel",
            "user",
            "that old target should have been retrieved",
        )
        organ = MicroClayRetrieval(db)

        with pytest.raises(RuntimeError, match="force outer rollback"):
            with db.tx() as outer:
                learned = apply_explicit_retrieval_miss(
                    organ,
                    retrieval_id=retrieval_id,
                    source_turn_id=feedback_turn,
                    memory_id="target",
                    user_id="gabriel",
                    session_id="session:gabriel",
                    generation=first["generation"],
                )
                assert learned["applied"] is True
                assert outer.execute(
                    "SELECT COUNT(*) FROM retrieval_feedback WHERE receipt_id=?",
                    (learned["receipt_id"],),
                ).fetchone()[0] == 1
                assert outer.execute(
                    "SELECT COUNT(*) FROM retrieval_entrypoint_policy WHERE entry_key LIKE 'route:%'"
                ).fetchone()[0] == 2
                raise RuntimeError("force outer rollback")

        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        assert db.db.execute(
            "SELECT COUNT(*) FROM retrieval_entrypoint_policy WHERE entry_key LIKE 'route:%'"
        ).fetchone()[0] == 0
    finally:
        db.close()
