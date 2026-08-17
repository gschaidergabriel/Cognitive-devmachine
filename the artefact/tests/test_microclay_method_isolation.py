from __future__ import annotations

import json
import time
import uuid

import pytest

from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.retrieval import WorldAssembler
from clayverse.store import StaleGeneration, UnifiedDB


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


def _add_framework(db: UnifiedDB, *, kind="framework", provenance=None, value="diagnostic framework"):
    return db.add_memory(
        kind,
        "dependency-timeout-diagnosis",
        value,
        None,
        "gabriel",
        provenance if provenance is not None else {"method_record": _framework_record()},
    )


def test_method_presence_never_satisfies_evidence_present(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        _add_framework(db)
        micro = MicroClayRetrieval(db)

        evidence = micro.retrieve(
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

        method = micro.retrieve_methods(
            query="sensor timeout dependency",
            user_id="gabriel",
            turn_id=turn_id,
        )
        assert method["receipt"]["status"] == "METHOD_PRESENT"
        assert [x["kind"] for x in method["items"]] == ["framework"]
        assert all(x["truth_authority"] is False for x in method["items"])

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
        assert world["unknowns"][0]["status"] == "FACT_UNKNOWN"
        assert world["unknowns"][0]["method_present"] is True
        assert world["retrieval_receipt"]["status"] == "UNKNOWN"
        assert world["retrieval_receipt"]["method"]["status"] == "METHOD_PRESENT"
    finally:
        db.close()


def test_direct_evidence_outranks_method_and_stage_b_does_not_replace_it(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        fact_id = db.add_memory(
            "fact",
            "sensor",
            "sensor timeout dependency is confirmed by current measurement",
            None,
            "gabriel",
            {"source": "test-measurement"},
        )
        _add_framework(db)

        world = WorldAssembler(db).assemble(
            sid,
            (),
            query="sensor timeout dependency",
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
        )
        assert world["retrieval_receipt"]["status"] == "PRESENT"
        assert [x["memory_id"] for x in world["durable_memory"]] == [fact_id]
        assert world["method_context"] == []
        assert world["unknowns"] == []
    finally:
        db.close()


def test_malformed_promoted_method_fails_closed_on_stage_b(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        _add_framework(
            db,
            provenance={
                "method_record": {
                    "problem_signature": ["sensor timeout dependency"],
                    "lifecycle_status": "PROMOTED",
                }
            },
        )
        with pytest.raises(ValueError, match="scope_limits|preconditions|method_steps|falsifiers"):
            WorldAssembler(db).assemble(
                sid,
                (),
                query="sensor timeout dependency",
                turn_id=turn_id,
                episode_id=episode_id,
                causal_id=causal_id,
                generation=generation,
            )
    finally:
        db.close()


def test_method_candidates_are_neither_evidence_nor_active_method_context(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        _add_framework(db, kind="framework_candidate")
        micro = MicroClayRetrieval(db)
        evidence = micro.retrieve(
            query="sensor timeout dependency",
            user_id="gabriel",
            session_id=sid,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
        )
        method = micro.retrieve_methods(
            query="sensor timeout dependency",
            user_id="gabriel",
            turn_id=turn_id,
        )
        assert evidence["receipt"]["status"] == "UNKNOWN"
        assert evidence["items"] == []
        assert method["receipt"]["status"] == "METHOD_UNKNOWN"
        assert method["items"] == []
    finally:
        db.close()


def test_legacy_replay_that_contains_method_memory_fails_closed(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        method_id = _add_framework(db)
        query = "sensor timeout dependency"
        import hashlib
        db.db.execute(
            "INSERT INTO retrieval_episodes("
            "retrieval_id,turn_id,episode_id,causal_id,session_id,user_id,generation,"
            "policy_version,mode,query_hash,query_token_hashes,selected_memory_ids,"
            "shadow_memory_ids,entry_keys,budget_chars,chars_selected,status,ts"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                str(uuid.uuid4()), turn_id, episode_id, causal_id, sid, "gabriel", generation,
                1, "SHADOW", hashlib.sha256(query.encode()).hexdigest(), "[]",
                json.dumps([method_id]), json.dumps([method_id]), "[]", 12000, 20,
                "PRESENT", time.time(),
            ),
        )
        with pytest.raises(StaleGeneration, match="retrieval_route_contract"):
            MicroClayRetrieval(db).retrieve(
                query=query,
                user_id="gabriel",
                session_id=sid,
                turn_id=turn_id,
                episode_id=episode_id,
                causal_id=causal_id,
                generation=generation,
            )
    finally:
        db.close()


def test_packing_never_admits_oversized_first_evidence_item(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db, "oversized needle")
        db.add_memory(
            "fact",
            "oversized",
            "needle " + ("x" * 300),
            None,
            "gabriel",
            {"source": "packing-regression"},
        )
        result = MicroClayRetrieval(db).retrieve(
            query="oversized needle",
            user_id="gabriel",
            session_id=sid,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
            budget_chars=256,
        )
        assert result["items"] == []
        assert result["receipt"]["chars_selected"] == 0
        assert result["receipt"]["status"] == "UNKNOWN"
    finally:
        db.close()
