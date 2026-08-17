import json

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _add(db, memory_id, value, *, subject, ts):
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (memory_id, "fact", subject, value, None, "gabriel", ts, json.dumps({"source": "test"})),
    )


def test_learned_alias_route_is_bound_to_rank1_memory_not_shared_subject(tmp_path):
    """One successful rank-1 memory must not teach the alias to a sibling subject row."""
    db = _db(tmp_path)
    try:
        _add(db, "target", "orchid procedure", subject="topic:shared", ts=100.0)
        _add(db, "distractor", "bicycle violet", subject="topic:shared", ts=999.0)
        life = TurnLifecycle(db, "gabriel", "session:gabriel")

        first = life.begin("orchid procedure codename")
        assert [m["memory_id"] for m in first["context"]["durable_memory"]] == ["target"]
        effect = life.request_effect("state.noop", "learn-rank1-memory-alias")
        assert effect["verified"] is True
        life.complete("done")

        second = life.begin("codename")
        receipt = second["context"]["retrieval_receipt"]
        assert receipt["outcome_learning_applied"] == 1
        # SHADOW still protects serving authority while the adaptive route is evaluated.
        assert second["context"]["durable_memory"] == []
        assert receipt["status"] == "UNKNOWN"

        row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids FROM retrieval_episodes WHERE causal_id=?",
            (second["causal_id"],),
        ).fetchone()
        assert json.loads(row["selected_memory_ids"]) == []
        # The alias was earned only by rank-1 `target`. A newer unrelated sibling that
        # merely shares `subject` must not become a learned non-lexical entry point.
        assert json.loads(row["shadow_memory_ids"]) == ["target"]
        life.abort("test-end")
    finally:
        db.close()
