import json
import time
import uuid

import pytest

from clayverse.identity import IdentityRouter
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB


def _seed_reentered_outcome(db: UnifiedDB, status: str, credit: float = 0.0):
    user_id, session_id = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    generation = db.session_generation(session_id)
    turn_id = db.append_turn(session_id, user_id, "user", "retrieve the relevant memory")
    episode_id = str(uuid.uuid4())
    causal_id = str(uuid.uuid4())
    retrieval_id = str(uuid.uuid4())
    now = time.time()

    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, now, turn_id, 0.5, "[]", None, "SELECTED"),
    )
    db.db.execute(
        "INSERT INTO retrieval_episodes("
        "retrieval_id,turn_id,episode_id,causal_id,session_id,user_id,generation,policy_version,mode,"
        "query_hash,query_token_hashes,selected_memory_ids,shadow_memory_ids,entry_keys,budget_chars,chars_selected,status,ts"
        ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            retrieval_id,
            turn_id,
            episode_id,
            causal_id,
            session_id,
            user_id,
            generation,
            1,
            "SHADOW",
            "q" * 64,
            "[]",
            "[]",
            "[]",
            json.dumps(["kind:fact"]),
            1024,
            0,
            "UNKNOWN",
            now,
        ),
    )
    effect_id = db.record_effect(
        episode_id,
        user_id,
        "entityos.exec",
        "test-target",
        generation,
        status,
        argv=["noop"],
        outcome={"certainty": "unknown"} if "UNKNOWN" in status else {"ok": False},
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,1,?)",
        (causal_id, episode_id, effect_id, turn_id, "h" * 64, float(credit), now),
    )
    return session_id, generation


@pytest.mark.parametrize(
    "status",
    ["UNKNOWN_OUTCOME", "UNKNOWN_AFTER_RESTART", "STALE_OUTCOME", "PENDING"],
)
def test_uncertain_or_nonterminal_effect_outcome_creates_no_learning(status, tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        session_id, generation = _seed_reentered_outcome(db, status)
        result = MicroClayRetrieval(db).learn_from_verified_outcomes(
            session_id=session_id,
            generation=generation,
        )

        assert result == {"eligible": 0, "applied": 0}
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0] == 0
    finally:
        db.close()


def test_known_failed_outcome_remains_an_eligible_learning_signal(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        session_id, generation = _seed_reentered_outcome(db, "FAILED", credit=0.0)
        result = MicroClayRetrieval(db).learn_from_verified_outcomes(
            session_id=session_id,
            generation=generation,
        )

        assert result == {"eligible": 1, "applied": 1}
        feedback = db.db.execute(
            "SELECT credit,signal_class FROM retrieval_feedback"
        ).fetchone()
        assert float(feedback["credit"]) == 0.0
        assert feedback["signal_class"] == "effect_outcome:FAILED"
        policy = db.db.execute(
            "SELECT pulls,capital FROM retrieval_entrypoint_policy WHERE entry_key='kind:fact'"
        ).fetchone()
        assert int(policy["pulls"]) == 1
        assert float(policy["capital"]) < 0.0
    finally:
        db.close()
