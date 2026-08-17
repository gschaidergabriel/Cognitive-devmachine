import json
import time

import pytest

from clayverse.identity import IdentityRouter
from clayverse.microclay_feedback import apply_explicit_retrieval_miss
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _add(
    db,
    memory_id,
    value,
    *,
    subject="topic:target",
    kind="fact",
    user_id="gabriel",
    ts=1.0,
):
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (memory_id, kind, subject, value, None, user_id, ts, json.dumps({"source": "test"})),
    )


def _feedback_turn(db, content="that prior memory should have been retrieved"):
    return db.append_turn(
        "session:gabriel",
        "gabriel",
        "user",
        content,
        provenance={"source": "explicit-retrieval-feedback-test"},
    )


def test_explicit_miss_teaches_shadow_entry_route_without_rewriting_memory(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "target", "vault-entry-742")
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        first = life.begin("orchid alias")
        assert first["context"]["durable_memory"] == []
        assert first["context"]["retrieval_receipt"]["status"] == "UNKNOWN"
        retrieval_id = first["context"]["retrieval_receipt"]["retrieval_id"]
        before = [tuple(r) for r in db.db.execute("SELECT * FROM durable_memory ORDER BY memory_id")]
        life.abort("collect-explicit-feedback")

        source_turn_id = _feedback_turn(db)
        organ = MicroClayRetrieval(db)
        learned = apply_explicit_retrieval_miss(
            organ,
            retrieval_id=retrieval_id,
            source_turn_id=source_turn_id,
            memory_id="target",
            user_id="gabriel",
            session_id="session:gabriel",
            generation=first["generation"],
        )
        duplicate = apply_explicit_retrieval_miss(
            organ,
            retrieval_id=retrieval_id,
            source_turn_id=source_turn_id,
            memory_id="target",
            user_id="gabriel",
            session_id="session:gabriel",
            generation=first["generation"],
        )
        after = [tuple(r) for r in db.db.execute("SELECT * FROM durable_memory ORDER BY memory_id")]

        assert learned["applied"] is True
        assert learned["truth_authority"] is False
        assert learned["effect_authority"] is False
        assert learned["updated_entrypoints"] == 2
        assert duplicate == {
            "applied": False,
            "reason": "duplicate_receipt",
            "receipt_id": learned["receipt_id"],
        }
        assert before == after
        assert db.db.execute(
            "SELECT COUNT(*) FROM retrieval_feedback WHERE signal_class LIKE 'user_feedback:miss:%'"
        ).fetchone()[0] == 1
        capitals = db.db.execute(
            "SELECT entry_key,capital FROM retrieval_entrypoint_policy WHERE entry_key LIKE 'route:%'"
        ).fetchall()
        assert len(capitals) == 2
        assert all(float(row["capital"]) > 0.0 for row in capitals)

        second = life.begin("orchid alias")
        # SHADOW stays safe: the deterministic baseline still serves nothing.
        assert second["context"]["durable_memory"] == []
        row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids,mode FROM retrieval_episodes WHERE causal_id=?",
            (second["causal_id"],),
        ).fetchone()
        assert row["mode"] == "SHADOW"
        assert json.loads(row["selected_memory_ids"]) == []
        assert "target" in json.loads(row["shadow_memory_ids"])
        assert second["context"]["retrieval_receipt"]["shadow_differs"] is True
        life.abort("test-end")
    finally:
        db.close()


def test_explicit_miss_requires_later_same_user_turn(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "target", "vault-entry-742")
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        first = life.begin("orchid alias")
        retrieval_id = first["context"]["retrieval_receipt"]["retrieval_id"]
        original_turn_id = first["turn_id"]
        life.abort("feedback-boundary")
        organ = MicroClayRetrieval(db)

        with pytest.raises(ValueError, match="later canonical user turn"):
            apply_explicit_retrieval_miss(
                organ,
                retrieval_id=retrieval_id,
                source_turn_id=original_turn_id,
                memory_id="target",
                user_id="gabriel",
                session_id="session:gabriel",
                generation=first["generation"],
            )

        assistant_turn = db.append_turn(
            "session:gabriel", "gabriel", "assistant", "model says it missed something"
        )
        with pytest.raises(PermissionError, match="same canonical user session"):
            apply_explicit_retrieval_miss(
                organ,
                retrieval_id=retrieval_id,
                source_turn_id=assistant_turn,
                memory_id="target",
                user_id="gabriel",
                session_id="session:gabriel",
                generation=first["generation"],
            )
    finally:
        db.close()


def test_explicit_miss_rejects_selected_future_private_and_non_evidence_targets(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "selected", "orchid alias")
        _add(db, "private", "vault-entry-742", user_id="andreas")
        _add(db, "method", "vault-entry-743", kind="framework_candidate")
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        first = life.begin("orchid alias")
        retrieval_id = first["context"]["retrieval_receipt"]["retrieval_id"]
        assert "selected" in [x["memory_id"] for x in first["context"]["durable_memory"]]
        life.abort("feedback-boundary")
        source_turn_id = _feedback_turn(db)
        _add(db, "future", "vault-entry-744", ts=time.time() + 10.0)
        organ = MicroClayRetrieval(db)

        with pytest.raises(ValueError, match="already selected"):
            apply_explicit_retrieval_miss(
                organ,
                retrieval_id=retrieval_id,
                source_turn_id=source_turn_id,
                memory_id="selected",
                user_id="gabriel",
                session_id="session:gabriel",
                generation=first["generation"],
            )
        with pytest.raises(PermissionError, match="user memory boundary"):
            apply_explicit_retrieval_miss(
                organ,
                retrieval_id=retrieval_id,
                source_turn_id=source_turn_id,
                memory_id="private",
                user_id="gabriel",
                session_id="session:gabriel",
                generation=first["generation"],
            )
        with pytest.raises(PermissionError, match="not Stage-A evidence"):
            apply_explicit_retrieval_miss(
                organ,
                retrieval_id=retrieval_id,
                source_turn_id=source_turn_id,
                memory_id="method",
                user_id="gabriel",
                session_id="session:gabriel",
                generation=first["generation"],
            )
        with pytest.raises(ValueError, match="did not exist at retrieval time"):
            apply_explicit_retrieval_miss(
                organ,
                retrieval_id=retrieval_id,
                source_turn_id=source_turn_id,
                memory_id="future",
                user_id="gabriel",
                session_id="session:gabriel",
                generation=first["generation"],
            )
    finally:
        db.close()


def test_explicit_miss_is_generation_fenced(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "target", "vault-entry-742")
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        first = life.begin("orchid alias")
        retrieval_id = first["context"]["retrieval_receipt"]["retrieval_id"]
        life.abort("feedback-boundary")
        source_turn_id = _feedback_turn(db)
        db.advance_entity_generation()
        with pytest.raises(StaleGeneration):
            apply_explicit_retrieval_miss(
                MicroClayRetrieval(db),
                retrieval_id=retrieval_id,
                source_turn_id=source_turn_id,
                memory_id="target",
                user_id="gabriel",
                session_id="session:gabriel",
                generation=first["generation"],
            )
    finally:
        db.close()
