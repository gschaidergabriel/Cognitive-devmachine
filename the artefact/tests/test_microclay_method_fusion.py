from __future__ import annotations

import hashlib
import json
import time
import uuid

import pytest

from clayverse.microclay_methods import MicroClayMethodRetrieval
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.retrieval import WorldAssembler
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


def _identity(db: UnifiedDB, query: str = "sensor timeout dependency"):
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    generation = db.entity_generation()
    turn_id = db.append_turn(session_id, "gabriel", "user", query)
    episode_id = str(uuid.uuid4())
    causal_id = str(uuid.uuid4())
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 1.0, "[]", None, "OPEN"),
    )
    return session_id, generation, turn_id, episode_id, causal_id


def _framework_record():
    return {
        "problem_signature": ["timeout dependency sensor", "bounded diagnosis"],
        "preconditions": ["a dependency boundary exists"],
        "method_steps": ["isolate dependency", "run bounded falsifier"],
        "falsifiers": ["timeout persists with dependency removed"],
        "scope_limits": ["not a factual claim about the current sensor"],
        "lifecycle_status": "PROMOTED",
    }


def _add_framework(db: UnifiedDB, *, kind="framework", provenance=None):
    return db.add_memory(
        kind,
        "dependency-timeout-diagnosis",
        "diagnostic framework",
        None,
        "gabriel",
        provenance if provenance is not None else {"method_record": _framework_record()},
    )


def test_fact_unknown_survives_method_present_and_receipts_stay_separate(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        _add_framework(db)
        evidence = MicroClayRetrieval(db).retrieve(
            query="sensor timeout dependency",
            user_id="gabriel",
            session_id=sid,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
        )
        assert evidence["items"] == []
        assert evidence["receipt"]["status"] == "UNKNOWN"
        assert evidence["receipt"]["route"] == "evidence"

        world = WorldAssembler(db).assemble(
            sid,
            (),
            query="sensor timeout dependency",
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
        )
        assert world["durable_memory"] == []
        assert [x["kind"] for x in world["method_context"]] == ["framework"]
        assert world["unknowns"] == [{
            "status": "FACT_UNKNOWN",
            "query_sha256": world["retrieval_receipt"]["query_sha256"],
            "method_present": True,
        }]
        assert world["retrieval_receipt"]["status"] == "UNKNOWN"
        assert "method" not in world["retrieval_receipt"]
        assert world["method_receipt"]["status"] == "METHOD_PRESENT"
        assert world["method_receipt"]["causal_id"] == causal_id
        assert world["method_receipt"]["generation"] == generation
        assert world["method_receipt"]["truth_authority"] is False
    finally:
        db.close()


def test_direct_evidence_suppresses_unknown_triggered_method_lane(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        fact_id = db.add_memory(
            "fact", "sensor",
            "sensor timeout dependency is confirmed by current measurement",
            None, "gabriel", {"source": "test-measurement"},
        )
        _add_framework(db)
        world = WorldAssembler(db).assemble(
            sid, (), query="sensor timeout dependency", turn_id=turn_id,
            episode_id=episode_id, causal_id=causal_id, generation=generation,
        )
        assert world["retrieval_receipt"]["status"] == "PRESENT"
        assert [x["memory_id"] for x in world["durable_memory"]] == [fact_id]
        assert world["method_context"] == []
        assert world["unknowns"] == []
        assert world["method_receipt"]["status"] == "METHOD_NOT_REQUESTED"
    finally:
        db.close()


def test_candidate_and_malformed_method_fail_closed(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        _add_framework(db, kind="framework_candidate")
        method = MicroClayMethodRetrieval(db).retrieve(
            query="sensor timeout dependency", user_id="gabriel", session_id=sid,
            turn_id=turn_id, episode_id=episode_id, causal_id=causal_id,
            generation=generation,
        )
        assert method["items"] == []
        assert method["receipt"]["status"] == "METHOD_UNKNOWN"

        _add_framework(
            db,
            provenance={"method_record": {
                "problem_signature": ["sensor timeout dependency"],
                "lifecycle_status": "PROMOTED",
            }},
        )
        with pytest.raises(ValueError, match="scope_limits|preconditions|method_steps|falsifiers"):
            MicroClayMethodRetrieval(db).retrieve(
                query="sensor timeout dependency", user_id="gabriel", session_id=sid,
                turn_id=turn_id, episode_id=episode_id, causal_id=causal_id,
                generation=generation,
            )
    finally:
        db.close()


def test_legacy_evidence_replay_containing_method_fails_before_learning(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        method_id = _add_framework(db)
        query = "sensor timeout dependency"
        db.db.execute(
            "INSERT INTO retrieval_episodes("
            "retrieval_id,turn_id,episode_id,causal_id,session_id,user_id,generation,"
            "policy_version,mode,query_hash,query_token_hashes,selected_memory_ids,"
            "shadow_memory_ids,entry_keys,budget_chars,limit_items,chars_selected,status,ts"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                str(uuid.uuid4()), turn_id, episode_id, causal_id, sid, "gabriel", generation,
                1, "SHADOW", hashlib.sha256(query.encode()).hexdigest(), "[]",
                json.dumps([method_id]), json.dumps([method_id]), "[]", 12000, 24, 20,
                "PRESENT", time.time(),
            ),
        )
        with pytest.raises(StaleGeneration, match="retrieval_route_contract"):
            MicroClayRetrieval(db).retrieve(
                query=query, user_id="gabriel", session_id=sid, turn_id=turn_id,
                episode_id=episode_id, causal_id=causal_id, generation=generation,
            )
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
    finally:
        db.close()


def test_bound_world_preserves_distinct_method_channel_or_fails_closed():
    world = {
        "own_recent": [],
        "cross_session_collision": [],
        "durable_memory": [],
        "method_context": [{"kind": "framework", "method_record": {"x": "y"}}],
        "unknowns": [{"status": "FACT_UNKNOWN"}],
        "counterevidence": [],
        "retrieval_receipt": {"route": "evidence", "status": "UNKNOWN"},
        "method_receipt": {"route": "method", "status": "METHOD_PRESENT"},
    }
    packed = TurnLifecycle._bound_world(world, max_chars=2_000)
    assert packed["retrieval_receipt"]["status"] == "UNKNOWN"
    assert packed["method_receipt"]["status"] == "METHOD_PRESENT"
    assert packed["method_context"]
    assert packed["unknowns"] == [{"status": "FACT_UNKNOWN"}]

    bad = dict(world)
    bad["retrieval_receipt"] = {"status": "UNKNOWN", "method": {"status": "METHOD_PRESENT"}}
    with pytest.raises(TurnLifecycleError, match="retrieval receipt values must be scalar"):
        TurnLifecycle._bound_world(bad)
