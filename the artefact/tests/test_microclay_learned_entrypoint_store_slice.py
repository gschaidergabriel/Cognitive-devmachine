import hashlib
import json
import time

from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clay-gabriel")
    assert session_id == "session:gabriel"
    return db


def _turn_and_workspace(db, label, query):
    now = time.time()
    turn_id = f"turn:{label}"
    episode_id = f"episode:{label}"
    causal_id = f"causal:{label}"
    ordinal = int(db.db.execute(
        "SELECT COALESCE(MAX(ordinal),0)+1 FROM turns WHERE session_id='session:gabriel'"
    ).fetchone()[0])
    db.db.execute(
        "INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) "
        "VALUES(?,?,?,?,?,?,?,?,?,?)",
        (turn_id, "session:gabriel", "gabriel", ordinal, now, "user", query, "[]", "[]", "{}"),
    )
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, "session:gabriel", now, turn_id, 0.5, "[]", None, "OPEN"),
    )
    return turn_id, episode_id, causal_id


def _bind_positive_causal_outcome(db, turn_id, episode_id, causal_id, generation):
    now = time.time()
    effect_id = f"effect:{causal_id}"
    outcome = json.dumps({"ok": True, "boundary": "focused-store-slice"}, sort_keys=True)
    db.db.execute(
        "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            effect_id,
            episode_id,
            "gabriel",
            "entityos.exec",
            json.dumps({"sha256": "focused-store-slice"}, sort_keys=True),
            None,
            int(generation),
            "VERIFIED",
            outcome,
            now,
            now,
        ),
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            causal_id,
            episode_id,
            effect_id,
            turn_id,
            hashlib.sha256(outcome.encode()).hexdigest(),
            1.0,
            1,
            now,
        ),
    )


def test_store_bound_verified_outcome_learns_new_shadow_entrypoint(tmp_path):
    db = _db(tmp_path)
    try:
        db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                "m1",
                "fact",
                "procedure:orchid",
                "orchid procedure",
                None,
                "gabriel",
                time.time(),
                json.dumps({"source": "focused-store-slice"}),
            ),
        )
        generation = db.entity_generation()
        organ = MicroClayRetrieval(db)

        first_turn, first_episode, first_causal = _turn_and_workspace(
            db, "first", "orchid procedure codename"
        )
        first = organ.retrieve(
            query="orchid procedure codename",
            user_id="gabriel",
            session_id="session:gabriel",
            turn_id=first_turn,
            episode_id=first_episode,
            causal_id=first_causal,
            generation=generation,
            limit=8,
            budget_chars=4096,
        )
        assert [item["memory_id"] for item in first["items"]] == ["m1"]
        assert first["receipt"]["policy_version"] == 2
        assert first["receipt"]["mode"] == "SHADOW"

        first_row = db.db.execute(
            "SELECT entry_keys FROM retrieval_episodes WHERE causal_id=?", (first_causal,)
        ).fetchone()
        route_key = MicroClayRetrieval._route_key("codename", "procedure:orchid")
        assert route_key in json.loads(first_row["entry_keys"])
        _bind_positive_causal_outcome(
            db, first_turn, first_episode, first_causal, generation
        )

        second_turn, second_episode, second_causal = _turn_and_workspace(
            db, "second", "codename"
        )
        second = organ.retrieve(
            query="codename",
            user_id="gabriel",
            session_id="session:gabriel",
            turn_id=second_turn,
            episode_id=second_episode,
            causal_id=second_causal,
            generation=generation,
            limit=8,
            budget_chars=4096,
        )
        assert second["receipt"]["outcome_learning_applied"] == 1
        assert second["items"] == []
        assert second["receipt"]["status"] == "UNKNOWN"

        second_row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids FROM retrieval_episodes WHERE causal_id=?",
            (second_causal,),
        ).fetchone()
        assert json.loads(second_row["selected_memory_ids"]) == []
        assert json.loads(second_row["shadow_memory_ids"]) == ["m1"]

        learned = db.db.execute(
            "SELECT capital,pulls FROM retrieval_entrypoint_policy WHERE entry_key=?",
            (route_key,),
        ).fetchone()
        assert learned is not None
        assert float(learned["capital"]) > 0.0
        assert int(learned["pulls"]) == 1
    finally:
        db.close()


def test_v1_active_and_generic_subject_capital_cannot_open_v2_miss(tmp_path):
    db = _db(tmp_path)
    try:
        db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES('m1','fact','procedure:orchid','orchid procedure',NULL,'gabriel',?,?)",
            (time.time(), json.dumps({"source": "focused-store-slice"})),
        )
        db.db.execute(
            "UPDATE retrieval_policy_state SET mode='ACTIVE',policy_version=1 WHERE singleton=1"
        )
        db.db.execute(
            "INSERT INTO retrieval_entrypoint_policy(entry_key,capital,reward_ema,pulls,updated_at) "
            "VALUES('v2:subject:procedure:orchid',4.0,1.0,10,?)",
            (time.time(),),
        )
        organ = MicroClayRetrieval(db)
        assert organ.mode() == "SHADOW"
        turn_id, episode_id, causal_id = _turn_and_workspace(db, "miss", "codename")
        result = organ.retrieve(
            query="codename",
            user_id="gabriel",
            session_id="session:gabriel",
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=db.entity_generation(),
            limit=8,
            budget_chars=4096,
        )
        assert result["items"] == []
        row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids,policy_version,mode "
            "FROM retrieval_episodes WHERE causal_id=?",
            (causal_id,),
        ).fetchone()
        assert json.loads(row["selected_memory_ids"]) == []
        assert json.loads(row["shadow_memory_ids"]) == []
        assert int(row["policy_version"]) == 2
        assert row["mode"] == "SHADOW"
    finally:
        db.close()
