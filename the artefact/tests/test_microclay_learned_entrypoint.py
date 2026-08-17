import json

from clayverse.identity import IdentityRouter
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _add(db, memory_id, value, *, subject, user_id="gabriel", ts=100.0):
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (memory_id, "fact", subject, value, None, user_id, ts, json.dumps({"source": "test"})),
    )


def test_verified_query_alias_opens_shadow_entry_without_changing_served_fact_status(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "m1", "orchid procedure", subject="procedure:orchid")
        life = TurnLifecycle(db, "gabriel", "session:gabriel")

        first = life.begin("orchid procedure codename")
        assert [m["memory_id"] for m in first["context"]["durable_memory"]] == ["m1"]
        effect = life.request_effect("state.noop", "learn-alias-entry")
        assert effect["verified"] is True
        life.complete("done")

        second = life.begin("codename")
        receipt = second["context"]["retrieval_receipt"]
        assert receipt["outcome_learning_applied"] == 1
        # SHADOW never changes factual serving authority: lexical Stage A is still UNKNOWN.
        assert second["context"]["durable_memory"] == []
        assert receipt["status"] == "UNKNOWN"

        row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids FROM retrieval_episodes WHERE causal_id=?",
            (second["causal_id"],),
        ).fetchone()
        assert json.loads(row["selected_memory_ids"]) == []
        assert json.loads(row["shadow_memory_ids"]) == ["m1"]

        route_key = MicroClayRetrieval._route_key("codename", "procedure:orchid")
        learned = db.db.execute(
            "SELECT capital,pulls FROM retrieval_entrypoint_policy WHERE entry_key=?",
            (route_key,),
        ).fetchone()
        assert learned is not None
        assert float(learned["capital"]) > 0.0
        assert int(learned["pulls"]) == 1
        life.abort("test-end")
    finally:
        db.close()


def test_generic_subject_capital_cannot_open_unrelated_shadow_entry(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "m1", "orchid procedure", subject="procedure:orchid")
        db.db.execute(
            "INSERT INTO retrieval_entrypoint_policy(entry_key,capital,reward_ema,pulls,updated_at) "
            "VALUES(?,?,?,?,?)",
            ("subject:procedure:orchid", 4.0, 1.0, 10, 1.0),
        )
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        result = life.begin("completely-unrelated-cue")
        assert result["context"]["durable_memory"] == []
        assert result["context"]["retrieval_receipt"]["status"] == "UNKNOWN"
        row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids FROM retrieval_episodes WHERE causal_id=?",
            (result["causal_id"],),
        ).fetchone()
        assert json.loads(row["selected_memory_ids"]) == []
        assert json.loads(row["shadow_memory_ids"]) == []
        life.abort("test-end")
    finally:
        db.close()
