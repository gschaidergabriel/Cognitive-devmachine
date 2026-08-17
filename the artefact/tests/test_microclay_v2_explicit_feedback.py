import hashlib
import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.microclay_feedback import MicroClayExplicitFeedback
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _memory(
    db,
    memory_id,
    value,
    *,
    subject="topic:shared",
    kind="fact",
    user_id="gabriel",
    source_turn_id=None,
):
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,strftime('%s','now') + (julianday('now') - julianday(date('now'))) * 0,?)",
        (
            memory_id,
            kind,
            subject,
            value,
            source_turn_id,
            user_id,
            json.dumps({"source": "test"}),
        ),
    )


def _request(db, first):
    row = db.db.execute(
        "SELECT * FROM retrieval_episodes WHERE causal_id=?",
        (first["causal_id"],),
    ).fetchone()
    assert row is not None
    return row, {
        "retrieval_id": row["retrieval_id"],
        "user_id": row["user_id"],
        "session_id": row["session_id"],
        "turn_id": row["turn_id"],
        "episode_id": row["episode_id"],
        "causal_id": row["causal_id"],
        "generation": int(row["generation"]),
        "query_sha256": row["query_hash"],
        "budget_chars": int(row["budget_chars"]),
    }


def _feedback_turn(db, request, feedback_class, target_memory_id):
    provenance = {
        "schema": "ClayVerseRetrievalFeedback/v1",
        "source": "clayverse:retrieval-feedback",
        "retrieval_id": request["retrieval_id"],
        "feedback_class": feedback_class,
        "target_memory_id": target_memory_id,
    }
    return db.append_turn(
        "session:gabriel",
        "gabriel",
        "user",
        "explicit retrieval feedback",
        provenance=provenance,
    )


def test_explicit_miss_opens_only_exact_memory_in_shadow(tmp_path):
    db = _db(tmp_path)
    try:
        _memory(db, "target", "vault-entry-742")
        _memory(db, "sibling", "vault-entry-999")
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        first = life.begin("orchid alias")
        row, request = _request(db, first)
        assert json.loads(row["selected_memory_ids"]) == []
        assert json.loads(row["shadow_memory_ids"]) == []
        assert int(row["policy_version"]) == 2
        life.abort("collect explicit feedback")

        feedback_turn_id = _feedback_turn(
            db, request, "USER_MISS_TARGET", "target"
        )
        learned = MicroClayExplicitFeedback(db).apply(
            **request,
            feedback_turn_id=feedback_turn_id,
            feedback_class="USER_MISS_TARGET",
            target_memory_id="target",
        )
        duplicate = MicroClayExplicitFeedback(db).apply(
            **request,
            feedback_turn_id=feedback_turn_id,
            feedback_class="USER_MISS_TARGET",
            target_memory_id="target",
        )

        assert learned["applied"] is True
        assert learned["mode"] == "SHADOW"
        assert learned["truth_authority"] is False
        assert learned["effect_authority"] is False
        assert learned["updated_entrypoints"] == 2
        assert duplicate == {
            "applied": False,
            "reason": "duplicate_receipt",
            "receipt_id": learned["receipt_id"],
        }
        route_rows = db.db.execute(
            "SELECT entry_key,capital FROM retrieval_entrypoint_policy "
            "WHERE entry_key LIKE 'route:v2:%' ORDER BY entry_key"
        ).fetchall()
        assert len(route_rows) == 2
        assert all(float(item["capital"]) > 0.0 for item in route_rows)

        second = life.begin("orchid alias")
        second_row, _ = _request(db, second)
        assert json.loads(second_row["selected_memory_ids"]) == []
        shadow = json.loads(second_row["shadow_memory_ids"])
        assert "target" in shadow
        assert "sibling" not in shadow
        assert second_row["mode"] == "SHADOW"
        life.abort("test end")
    finally:
        db.close()


def test_feedback_rejects_hindsight_memory_created_after_retrieval(tmp_path):
    db = _db(tmp_path)
    try:
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        first = life.begin("orchid alias")
        row, request = _request(db, first)
        life.abort("feedback boundary")
        db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                "future",
                "fact",
                "topic:shared",
                "learned later",
                None,
                "gabriel",
                float(row["ts"]) + 1.0,
                "{}",
            ),
        )
        feedback_turn_id = _feedback_turn(
            db, request, "USER_MISS_TARGET", "future"
        )
        with pytest.raises(PermissionError, match="did not exist at retrieval time"):
            MicroClayExplicitFeedback(db).apply(
                **request,
                feedback_turn_id=feedback_turn_id,
                feedback_class="USER_MISS_TARGET",
                target_memory_id="future",
            )
        assert db.db.execute(
            "SELECT COUNT(*) FROM retrieval_entrypoint_policy WHERE entry_key LIKE 'route:v2:%'"
        ).fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
    finally:
        db.close()


def test_feedback_requires_typed_later_canonical_user_turn(tmp_path):
    db = _db(tmp_path)
    try:
        _memory(db, "target", "vault-entry-742")
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        first = life.begin("orchid alias")
        _, request = _request(db, first)
        life.abort("feedback boundary")
        ordinary_turn = db.append_turn(
            "session:gabriel",
            "gabriel",
            "user",
            "ordinary prompt text is not retrieval feedback",
            provenance={"source": "claude-hook:UserPromptSubmit"},
        )
        with pytest.raises(PermissionError, match="feedback provenance mismatch"):
            MicroClayExplicitFeedback(db).apply(
                **request,
                feedback_turn_id=ordinary_turn,
                feedback_class="USER_MISS_TARGET",
                target_memory_id="target",
            )

        wrong_target_turn = _feedback_turn(
            db, request, "USER_MISS_TARGET", "different-memory"
        )
        with pytest.raises(PermissionError, match="target_memory_id"):
            MicroClayExplicitFeedback(db).apply(
                **request,
                feedback_turn_id=wrong_target_turn,
                feedback_class="USER_MISS_TARGET",
                target_memory_id="target",
            )
    finally:
        db.close()


def test_feedback_is_atomic_with_outer_canonical_transaction(tmp_path):
    db = _db(tmp_path)
    try:
        _memory(db, "target", "vault-entry-742")
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        first = life.begin("orchid alias")
        _, request = _request(db, first)
        life.abort("feedback boundary")
        feedback_turn_id = _feedback_turn(
            db, request, "USER_MISS_TARGET", "target"
        )

        with pytest.raises(RuntimeError, match="force rollback"):
            with db.tx() as outer:
                learned = MicroClayExplicitFeedback(db).apply(
                    **request,
                    feedback_turn_id=feedback_turn_id,
                    feedback_class="USER_MISS_TARGET",
                    target_memory_id="target",
                )
                assert learned["applied"] is True
                assert outer.execute(
                    "SELECT COUNT(*) FROM retrieval_feedback WHERE receipt_id=?",
                    (learned["receipt_id"],),
                ).fetchone()[0] == 1
                raise RuntimeError("force rollback")

        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        assert db.db.execute(
            "SELECT COUNT(*) FROM retrieval_entrypoint_policy WHERE entry_key LIKE 'route:v2:%'"
        ).fetchone()[0] == 0
    finally:
        db.close()


def test_legacy_active_policy_cannot_silently_activate_v2(tmp_path):
    db = _db(tmp_path)
    try:
        db.db.execute(
            "UPDATE retrieval_policy_state SET mode='ACTIVE',policy_version=1"
        )
        with pytest.raises(StaleGeneration, match="retrieval_policy_version"):
            MicroClayRetrieval(db).mode()
    finally:
        db.close()
