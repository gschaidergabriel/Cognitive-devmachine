import hashlib
import inspect
import json
import time
import uuid

import pytest

from clayverse.microclay_feedback import MicroClayExplicitFeedback
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    db.ensure_session("andreas", "clayverse-andreas")
    return db, session_id


def _seed_retrieval(db, session_id, *, query="codename"):
    turn_id = db.append_turn(session_id, "gabriel", "user", query)
    episode_id = str(uuid.uuid4())
    causal_id = str(uuid.uuid4())
    retrieval_id = str(uuid.uuid4())
    retrieval_ts = time.time()
    db.db.execute(
        "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, retrieval_ts, turn_id, 0.5, "[]", None, "OPEN"),
    )
    token_hashes = [
        MicroClayRetrieval._token_key(token)[4:]
        for token in sorted(MicroClayRetrieval._tokens(query))
    ]
    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
    db.db.execute(
        "INSERT INTO retrieval_episodes("
        "retrieval_id,turn_id,episode_id,causal_id,session_id,user_id,generation,"
        "policy_version,mode,query_hash,query_token_hashes,selected_memory_ids,"
        "shadow_memory_ids,entry_keys,budget_chars,limit_items,chars_selected,status,ts"
        ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            retrieval_id,
            turn_id,
            episode_id,
            causal_id,
            session_id,
            "gabriel",
            db.entity_generation(),
            MicroClayRetrieval.POLICY_VERSION,
            "SHADOW",
            query_hash,
            json.dumps(token_hashes),
            "[]",
            "[]",
            "[]",
            12000,
            24,
            0,
            "UNKNOWN",
            retrieval_ts,
        ),
    )
    return {
        "retrieval_id": retrieval_id,
        "user_id": "gabriel",
        "session_id": session_id,
        "turn_id": turn_id,
        "episode_id": episode_id,
        "causal_id": causal_id,
        "generation": db.entity_generation(),
        "query_sha256": query_hash,
        "budget_chars": 12000,
        "limit_items": 24,
        "retrieval_ts": retrieval_ts,
    }


def test_complete_miss_cannot_learn_from_memory_created_after_retrieval(tmp_path):
    """A later-created fact cannot be relabelled as evidence that was missed earlier."""
    db, session_id = _db(tmp_path)
    try:
        request = _seed_retrieval(db, session_id)
        db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                "future-memory",
                "fact",
                "procedure:orchid",
                "orchid procedure learned later",
                None,
                "gabriel",
                request["retrieval_ts"] + 1.0,
                "{}",
            ),
        )
        request.pop("retrieval_ts")

        with pytest.raises((PermissionError, ValueError), match="retrieval|exist|histor"):
            MicroClayExplicitFeedback(db).apply(
                **request,
                feedback_class="USER_MISS_TARGET",
                target_memory_id="future-memory",
                source="USER_EXPLICIT",
            )

        assert db.db.execute(
            "SELECT COUNT(*) FROM retrieval_entrypoint_policy"
        ).fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
    finally:
        db.close()


def test_user_explicit_provenance_cannot_be_silently_minted_by_default_argument():
    """Omitting provenance must not automatically become USER_EXPLICIT authority."""
    source = inspect.signature(MicroClayExplicitFeedback.apply).parameters["source"]
    assert source.default is inspect.Parameter.empty
