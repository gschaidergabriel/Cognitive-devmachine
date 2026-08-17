import hashlib
import json
import time

from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    assert db.ensure_session("gabriel", "clay-gabriel") == "session:gabriel"
    assert db.ensure_session("andreas", "clay-andreas") == "session:andreas"
    return db


def _memory(db, memory_id, value, *, subject, user_id, ts):
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (memory_id, "fact", subject, value, None, user_id, ts, json.dumps({"source": "cross-user-red-gate"})),
    )


def _identity(db, *, user_id, session_id, label, query):
    now = time.time()
    turn_id = f"turn:{label}"
    episode_id = f"episode:{label}"
    causal_id = f"causal:{label}"
    ordinal = int(db.db.execute(
        "SELECT COALESCE(MAX(ordinal),0)+1 FROM turns WHERE session_id=?", (session_id,)
    ).fetchone()[0])
    db.db.execute(
        "INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) "
        "VALUES(?,?,?,?,?,?,?,?,?,?)",
        (turn_id, session_id, user_id, ordinal, now, "user", query, "[]", "[]", "{}"),
    )
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, now, turn_id, 0.5, "[]", None, "OPEN"),
    )
    return turn_id, episode_id, causal_id


def _retrieve(db, organ, *, user_id, session_id, label, query):
    turn_id, episode_id, causal_id = _identity(
        db, user_id=user_id, session_id=session_id, label=label, query=query
    )
    result = organ.retrieve(
        query=query,
        user_id=user_id,
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=db.entity_generation(),
        limit=8,
        budget_chars=4096,
    )
    return result, turn_id, episode_id, causal_id


def _positive_outcome(db, *, user_id, turn_id, episode_id, causal_id):
    now = time.time()
    outcome = json.dumps({"ok": True, "boundary": "cross-user-red-gate"}, sort_keys=True)
    effect_id = f"effect:{causal_id}"
    db.db.execute(
        "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            effect_id,
            episode_id,
            user_id,
            "entityos.exec",
            json.dumps({"sha256": "cross-user-red-gate"}, sort_keys=True),
            None,
            db.entity_generation(),
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


def test_v3_learned_route_capital_does_not_cross_user_perspectives(tmp_path):
    """One user's learned exact-memory route must not open the other user's memory."""
    db = _db(tmp_path)
    try:
        subject = "procedure:shared-label"
        _memory(db, "gabriel-memory", "orchid procedure", subject=subject, user_id="gabriel", ts=200.0)
        _memory(db, "andreas-memory", "violet bicycle", subject=subject, user_id="andreas", ts=100.0)
        organ = MicroClayRetrieval(db)

        first, turn_id, episode_id, causal_id = _retrieve(
            db,
            organ,
            user_id="gabriel",
            session_id="session:gabriel",
            label="gabriel-source",
            query="orchid procedure codename",
        )
        assert [item["memory_id"] for item in first["items"]] == ["gabriel-memory"]
        _positive_outcome(
            db,
            user_id="gabriel",
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
        )

        learning, _, _, _ = _retrieve(
            db,
            organ,
            user_id="gabriel",
            session_id="session:gabriel",
            label="gabriel-consume",
            query="orchid",
        )
        assert learning["receipt"]["outcome_learning_applied"] == 1
        route_key = MicroClayRetrieval._route_key("codename", "gabriel-memory")
        assert route_key.startswith("v3:route:")
        assert db.db.execute(
            "SELECT capital FROM retrieval_entrypoint_policy WHERE entry_key=?",
            (route_key,),
        ).fetchone() is not None

        andreas, _, _, andreas_causal = _retrieve(
            db,
            organ,
            user_id="andreas",
            session_id="session:andreas",
            label="andreas-miss",
            query="codename",
        )
        assert andreas["items"] == []
        assert andreas["receipt"]["status"] == "UNKNOWN"
        row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids FROM retrieval_episodes WHERE causal_id=?",
            (andreas_causal,),
        ).fetchone()
        assert json.loads(row["selected_memory_ids"]) == []
        assert json.loads(row["shadow_memory_ids"]) == []
    finally:
        db.close()
