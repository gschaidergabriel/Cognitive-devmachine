from __future__ import annotations

import hashlib
import json
import time
import uuid

import pytest

from clayverse.microclay_methods import (
    METHOD_SCHEMA,
    PROMOTION_RECEIPT_SCHEMA,
    MicroClayMethodRetrieval,
)
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.retrieval import WorldAssembler
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


SHADOW_SIGNATURE = ["timeout dependency sensor", "bounded diagnosis"]


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


def _activate_identity(db, sid, generation, turn_id, episode_id, causal_id):
    db.db.execute(
        "INSERT INTO active_turns("
        "session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,"
        "effect_id,outcome,workspace_selected,started_at"
        ") VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            sid, "gabriel", turn_id, episode_id, causal_id, generation, "[]",
            None, None, 0, time.time(),
        ),
    )


def _method_source_episodes(db: UnifiedDB, *, user_id="gabriel", count=2):
    db.ensure_user(user_id, user_id.title())
    sid = db.ensure_session(user_id, f"clayverse-{user_id}")
    result = []
    for _ in range(count):
        episode_id = str(uuid.uuid4())
        causal_id = str(uuid.uuid4())
        db.db.execute(
            "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (episode_id, sid, time.time(), None, 1.0, "[]", None, "COMPLETED"),
        )
        db.db.execute(
            "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (causal_id, episode_id, None, None, f"outcome:{episode_id}", 1.0, 1, time.time()),
        )
        result.append(episode_id)
    return result


def _framework_record(source_episode_ids):
    return {
        "schema": METHOD_SCHEMA,
        "problem_signature": ["timeout dependency sensor", "bounded diagnosis"],
        "preconditions": ["a dependency boundary exists"],
        "goal_shape": "diagnose the controlling dependency without manufacturing facts",
        "method_steps": ["isolate dependency", "run bounded falsifier"],
        "invariants": ["direct evidence outranks analogical method context"],
        "expected_observations": ["dependency removal changes the timeout if causal"],
        "falsifiers": ["timeout persists with dependency removed"],
        "failure_modes": ["surface similarity hides a different causal structure"],
        "scope_limits": ["not a factual claim about the current sensor"],
        "source_episode_ids": list(source_episode_ids),
        "supporting_memory_ids": [],
        "counterexample_memory_ids": [],
        "abstraction_version": 1,
        "support_count": len(source_episode_ids),
        "success_count": len(source_episode_ids),
        "failure_count": 0,
        "calibration": 0.8,
        "last_validated_at": time.time(),
        "status": "PROMOTED",
    }


def _add_promoted_framework(
    db: UnifiedDB,
    *,
    user_id="gabriel",
    kind="framework",
    source_episode_ids=None,
):
    source_episode_ids = source_episode_ids or _method_source_episodes(db, user_id=user_id)
    record = _framework_record(source_episode_ids)
    method_id = db.add_memory(
        kind,
        "dependency-timeout-diagnosis",
        json.dumps(record, sort_keys=True, separators=(",", ":")),
        None,
        user_id,
        {"method_schema": METHOD_SCHEMA, "promotion_receipt_id": "pending"},
    )
    receipt = {
        "schema": PROMOTION_RECEIPT_SCHEMA,
        "action": "PROMOTE",
        "method_memory_id": method_id,
        "source_episode_ids": list(source_episode_ids),
        "supporting_memory_ids": [],
        "counterexample_memory_ids": [],
        "ts": time.time(),
    }
    receipt_id = db.add_memory(
        "method_receipt",
        method_id,
        json.dumps(receipt, sort_keys=True, separators=(",", ":")),
        None,
        user_id,
        {"source": "test-only-promotion-fixture"},
    )
    db.db.execute(
        "UPDATE durable_memory SET provenance=? WHERE memory_id=?",
        (
            json.dumps({
                "method_schema": METHOD_SCHEMA,
                "promotion_receipt_id": receipt_id,
                "truth_authority": False,
                "effect_authority": False,
            }, sort_keys=True, separators=(",", ":")),
            method_id,
        ),
    )
    return method_id


def test_fact_unknown_survives_method_present_and_receipts_stay_separate(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        _add_promoted_framework(db)
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
            problem_signature=SHADOW_SIGNATURE,
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
        assert world["method_receipt"]["promotion_verified"] is True
        assert world["method_receipt"]["served"] is False
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
        _add_promoted_framework(db)
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


def test_candidate_malformed_and_unreceipted_method_fail_closed(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        db.add_memory(
            "framework_candidate", "candidate", "{}", None, "gabriel", {"source": "test"}
        )
        method = MicroClayMethodRetrieval(db).retrieve(
            query="sensor timeout dependency", problem_signature=SHADOW_SIGNATURE,
            user_id="gabriel", session_id=sid,
            turn_id=turn_id, episode_id=episode_id, causal_id=causal_id,
            generation=generation,
        )
        assert method["items"] == []
        assert method["receipt"]["status"] == "METHOD_UNKNOWN"

        malformed_id = db.add_memory(
            "framework", "malformed", "{}", None, "gabriel",
            {"method_schema": METHOD_SCHEMA, "promotion_receipt_id": "missing"},
        )
        with pytest.raises(ValueError, match="fields mismatch"):
            MicroClayMethodRetrieval(db).retrieve(
                query="sensor timeout dependency", problem_signature=SHADOW_SIGNATURE,
                user_id="gabriel", session_id=sid,
                turn_id=turn_id, episode_id=episode_id, causal_id=causal_id,
                generation=generation,
            )
        db.db.execute("DELETE FROM durable_memory WHERE memory_id=?", (malformed_id,))

        source_episode_ids = _method_source_episodes(db)
        record = _framework_record(source_episode_ids)
        db.add_memory(
            "framework",
            "unreceipted",
            json.dumps(record, sort_keys=True, separators=(",", ":")),
            None,
            "gabriel",
            {"method_schema": METHOD_SCHEMA, "promotion_receipt_id": "missing"},
        )
        with pytest.raises(ValueError, match="promotion receipt is missing"):
            MicroClayMethodRetrieval(db).retrieve(
                query="sensor timeout dependency", problem_signature=SHADOW_SIGNATURE,
                user_id="gabriel", session_id=sid,
                turn_id=turn_id, episode_id=episode_id, causal_id=causal_id,
                generation=generation,
            )
    finally:
        db.close()


def test_unscoped_global_method_is_not_admitted_to_user_method_context(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        db.add_memory(
            "framework",
            "global-unadmitted",
            "{}",
            None,
            None,
            {"method_schema": METHOD_SCHEMA, "promotion_receipt_id": "forged"},
        )
        result = MicroClayMethodRetrieval(db).retrieve(
            query="sensor timeout dependency", problem_signature=SHADOW_SIGNATURE,
            user_id="gabriel", session_id=sid,
            turn_id=turn_id, episode_id=episode_id, causal_id=causal_id,
            generation=generation,
        )
        assert result["items"] == []
        assert result["receipt"]["status"] == "METHOD_UNKNOWN"
    finally:
        db.close()


def test_nonterminal_or_cross_user_source_episode_fails_closed(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        good_episode = _method_source_episodes(db, count=1)[0]
        db.ensure_user("andreas", "Andreas")
        andreas_sid = db.ensure_session("andreas", "clayverse-andreas")
        foreign_episode = str(uuid.uuid4())
        db.db.execute(
            "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (foreign_episode, andreas_sid, time.time(), None, 1.0, "[]", None, "COMPLETED"),
        )
        db.db.execute(
            "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), foreign_episode, None, None, "foreign", 1.0, 1, time.time()),
        )
        record = _framework_record([good_episode, foreign_episode])
        method_id = db.add_memory(
            "framework", "cross-user-source",
            json.dumps(record, sort_keys=True, separators=(",", ":")),
            None, "gabriel",
            {"method_schema": METHOD_SCHEMA, "promotion_receipt_id": "pending"},
        )
        receipt_id = db.add_memory(
            "method_receipt", method_id,
            json.dumps({
                "schema": PROMOTION_RECEIPT_SCHEMA,
                "action": "PROMOTE",
                "method_memory_id": method_id,
                "source_episode_ids": [good_episode, foreign_episode],
                "supporting_memory_ids": [],
                "counterexample_memory_ids": [],
                "ts": time.time(),
            }, sort_keys=True, separators=(",", ":")),
            None, "gabriel", {"source": "test"},
        )
        db.db.execute(
            "UPDATE durable_memory SET provenance=? WHERE memory_id=?",
            (json.dumps({"method_schema": METHOD_SCHEMA, "promotion_receipt_id": receipt_id}), method_id),
        )
        with pytest.raises(ValueError, match="crosses user boundary"):
            MicroClayMethodRetrieval(db).retrieve(
                query="sensor timeout dependency", problem_signature=SHADOW_SIGNATURE,
                user_id="gabriel", session_id=sid,
                turn_id=turn_id, episode_id=episode_id, causal_id=causal_id,
                generation=generation,
            )
    finally:
        db.close()


def test_legacy_evidence_replay_containing_method_fails_before_learning(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        method_id = _add_promoted_framework(db)
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


def test_partial_turn_identity_matches_active_and_is_completed(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        _activate_identity(db, sid, generation, turn_id, episode_id, causal_id)
        _add_promoted_framework(db)

        world = WorldAssembler(db).assemble(
            sid,
            (),
            query="sensor timeout dependency",
            problem_signature=SHADOW_SIGNATURE,
            generation=generation,
        )

        assert world["retrieval_receipt"]["turn_id"] == turn_id
        assert world["retrieval_receipt"]["episode_id"] == episode_id
        assert world["retrieval_receipt"]["causal_id"] == causal_id
        assert world["retrieval_receipt"]["generation"] == generation
        assert world["retrieval_receipt"]["status"] == "UNKNOWN"
        assert world["method_receipt"]["status"] == "METHOD_PRESENT"
        assert world["method_receipt"]["promotion_verified"] is True
        assert world["method_receipt"]["served"] is False
    finally:
        db.close()


def test_partial_turn_identity_conflict_fails_before_retrieval_mutation(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, generation, turn_id, episode_id, causal_id = _identity(db)
        _activate_identity(db, sid, generation, turn_id, episode_id, causal_id)

        with pytest.raises(StaleGeneration, match="active_turn_identity:turn_id"):
            WorldAssembler(db).assemble(
                sid,
                (),
                query="sensor timeout dependency",
                turn_id="foreign-turn",
            )

        assert db.db.execute("SELECT COUNT(*) FROM retrieval_episodes").fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
    finally:
        db.close()


def test_partial_turn_identity_without_active_turn_fails_closed(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        sid, _, _, _, _ = _identity(db)
        with pytest.raises(StaleGeneration, match="partial_turn_identity_without_active_turn"):
            WorldAssembler(db).assemble(
                sid,
                (),
                query="sensor timeout dependency",
            )
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_episodes").fetchone()[0] == 0
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
