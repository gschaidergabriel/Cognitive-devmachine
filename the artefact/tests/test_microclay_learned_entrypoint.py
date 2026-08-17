import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import StaleGeneration, UnifiedDB
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


def test_new_alias_route_credit_is_bound_to_rank1_served_evidence(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "top", "orchid procedure", subject="procedure:top", ts=200.0)
        _add(db, "other", "orchid procedure", subject="procedure:other", ts=100.0)
        life = TurnLifecycle(db, "gabriel", "session:gabriel")

        first = life.begin("orchid procedure codename")
        assert [m["memory_id"] for m in first["context"]["durable_memory"]][:2] == ["top", "other"]
        effect = life.request_effect("state.noop", "rank1-alias-entry")
        assert effect["verified"] is True
        life.complete("done")

        second = life.begin("codename")
        assert second["context"]["durable_memory"] == []
        row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids FROM retrieval_episodes WHERE causal_id=?",
            (second["causal_id"],),
        ).fetchone()
        assert json.loads(row["selected_memory_ids"]) == []
        assert json.loads(row["shadow_memory_ids"]) == ["top"]

        top_key = MicroClayRetrieval._route_key("codename", "procedure:top")
        other_key = MicroClayRetrieval._route_key("codename", "procedure:other")
        assert db.db.execute(
            "SELECT 1 FROM retrieval_entrypoint_policy WHERE entry_key=?", (top_key,)
        ).fetchone() is not None
        assert db.db.execute(
            "SELECT 1 FROM retrieval_entrypoint_policy WHERE entry_key=?", (other_key,)
        ).fetchone() is None
        life.abort("test-end")
    finally:
        db.close()


def test_control_kind_in_persisted_shadow_route_fails_closed_before_learning(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "m1", "orchid procedure", subject="procedure:orchid")
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        result = life.begin("orchid")
        db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            ("control", "source_archive", "control:test", "opaque", None, "gabriel", 1.0, "{}"),
        )
        db.db.execute(
            "UPDATE retrieval_episodes SET shadow_memory_ids=? WHERE causal_id=?",
            (json.dumps(["control"]), result["causal_id"]),
        )
        organ = MicroClayRetrieval(db)
        with pytest.raises(StaleGeneration):
            organ.retrieve(
                query="orchid",
                user_id="gabriel",
                session_id="session:gabriel",
                turn_id=result["turn_id"],
                episode_id=result["episode_id"],
                causal_id=result["causal_id"],
                generation=result["generation"],
            )
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        life.abort("test-end")
    finally:
        db.close()
