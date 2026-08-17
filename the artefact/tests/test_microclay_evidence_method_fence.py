import hashlib
import json
import time
import uuid

import pytest

from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import StaleGeneration, UnifiedDB


def _episode(db, session_id):
    turn_id = db.append_turn(session_id, "gabriel", "user", "alpha")
    episode_id = str(uuid.uuid4())
    db.db.execute(
        "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
    )
    return turn_id, episode_id


def _retrieve(db, retrieval, *, session_id, turn_id, episode_id, causal_id):
    return retrieval.retrieve(
        query="alpha",
        user_id="gabriel",
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=db.entity_generation(),
        limit=2,
        budget_chars=256,
    )


def test_method_memory_never_satisfies_stage_a_fact_evidence(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        db.ensure_user("gabriel", "Gabriel")
        session_id = db.ensure_session("gabriel", "terminal:gabriel")
        retrieval = MicroClayRetrieval(db)
        method_id = db.add_memory(
            "framework", "alpha method", "alpha alpha alpha", None, "gabriel", {"source": "test"}
        )
        turn_id, episode_id = _episode(db, session_id)
        result = _retrieve(
            db, retrieval, session_id=session_id, turn_id=turn_id,
            episode_id=episode_id, causal_id=str(uuid.uuid4()),
        )
        assert result["receipt"]["status"] == "UNKNOWN"
        assert result["items"] == []
        assert method_id not in [item["memory_id"] for item in result["items"]]

        fact_id = db.add_memory(
            "fact", "alpha fact", "alpha fact value", None, "gabriel", {"source": "test"}
        )
        turn_id, episode_id = _episode(db, session_id)
        result = _retrieve(
            db, retrieval, session_id=session_id, turn_id=turn_id,
            episode_id=episode_id, causal_id=str(uuid.uuid4()),
        )
        assert result["receipt"]["status"] == "PRESENT"
        assert [item["memory_id"] for item in result["items"]] == [fact_id]
    finally:
        db.close()


def test_pre_fence_method_contaminated_replay_is_rejected(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        db.ensure_user("gabriel", "Gabriel")
        session_id = db.ensure_session("gabriel", "terminal:gabriel")
        method_id = db.add_memory(
            "framework", "alpha method", "alpha method", None, "gabriel", {"source": "legacy"}
        )
        turn_id, episode_id = _episode(db, session_id)
        causal_id = str(uuid.uuid4())
        db.db.execute(
            "INSERT INTO retrieval_episodes("
            "retrieval_id,turn_id,episode_id,causal_id,session_id,user_id,generation,"
            "policy_version,mode,query_hash,query_token_hashes,selected_memory_ids,"
            "shadow_memory_ids,entry_keys,budget_chars,limit_items,chars_selected,status,ts"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                str(uuid.uuid4()), turn_id, episode_id, causal_id, session_id, "gabriel",
                db.entity_generation(), 1, "SHADOW", hashlib.sha256(b"alpha").hexdigest(),
                "[]", json.dumps([method_id]), json.dumps([method_id]), "[]", 256, 2, 12,
                "PRESENT", time.time(),
            ),
        )
        with pytest.raises(StaleGeneration, match="retrieval_semantic_class"):
            _retrieve(
                db, MicroClayRetrieval(db), session_id=session_id, turn_id=turn_id,
                episode_id=episode_id, causal_id=causal_id,
            )
    finally:
        db.close()
