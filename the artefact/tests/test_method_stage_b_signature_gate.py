from __future__ import annotations

import time
import uuid

import pytest

from clayverse.method_stage_b import StageBMethodRetrieval
from clayverse.store import StaleGeneration, UnifiedDB


def _active_turn(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    turn_id = db.append_turn(session_id, "gabriel", "user", "recover state provenance")
    episode_id = "active:" + uuid.uuid4().hex
    causal_id = "causal:" + uuid.uuid4().hex
    generation = db.entity_generation()
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
    )
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (session_id, "gabriel", turn_id, episode_id, causal_id, generation, "[]", None, None, 0, time.time()),
    )
    return db, session_id, turn_id, episode_id, causal_id, generation


def test_stage_b_without_explicit_structural_signature_fails_closed(tmp_path):
    db, session_id, turn_id, episode_id, causal_id, generation = _active_turn(tmp_path)

    result = StageBMethodRetrieval(db).retrieve(
        query="recover state provenance",
        user_id="gabriel",
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        evidence_status="UNKNOWN",
        problem_signature=None,
    )

    assert result["methods"] == []
    assert result["counterevidence"] == []
    assert result["problem_signature"] is None
    assert result["receipt"]["status"] == "SIGNATURE_REQUIRED"
    assert result["receipt"]["triggered"] is False
    assert result["receipt"]["problem_signature_sha256"] is None
    assert result["receipt"]["signature_source"] == "NONE"
    assert result["receipt"]["factual_status_unchanged"] == "UNKNOWN"
    assert result["receipt"]["truth_authority"] is False
    assert result["receipt"]["effect_authority"] is False
    assert result["receipt"]["replayed"] is False
    assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE kind='method_receipt'").fetchone()[0] == 1


def test_stage_b_signature_required_receipt_blocks_later_same_causal_signature_drift(tmp_path):
    db, session_id, turn_id, episode_id, causal_id, generation = _active_turn(tmp_path)
    stage_b = StageBMethodRetrieval(db)
    base = dict(
        query="recover state provenance",
        user_id="gabriel",
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        evidence_status="UNKNOWN",
        problem_signature=None,
        resource_refs=["repo:clay"],
        limit=4,
        budget_chars=2048,
    )

    first = stage_b.retrieve(**base)
    assert first["receipt"]["status"] == "SIGNATURE_REQUIRED"
    assert first["receipt"]["replayed"] is False

    replay = stage_b.retrieve(**base)
    assert replay["receipt"]["status"] == "SIGNATURE_REQUIRED"
    assert replay["receipt"]["replayed"] is True

    with pytest.raises(StaleGeneration, match="method_retrieval_identity"):
        stage_b.retrieve(
            **{**base, "problem_signature": {"goal": ["recover"], "mechanism": ["provenance"]}}
        )


def test_stage_b_durable_receipt_binds_full_request_identity(tmp_path):
    db, session_id, turn_id, episode_id, causal_id, generation = _active_turn(tmp_path)
    stage_b = StageBMethodRetrieval(db)
    signature = {"goal": ["recover"], "mechanism": ["provenance"]}
    base = dict(
        query="recover state provenance",
        user_id="gabriel",
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        evidence_status="UNKNOWN",
        resource_refs=["repo:clay", "db:world"],
        problem_signature=signature,
        limit=4,
        budget_chars=2048,
    )

    first = stage_b.retrieve(**base)
    assert first["receipt"]["replayed"] is False
    assert first["receipt"]["budget_chars"] == 2048
    assert first["receipt"]["limit"] == 4
    assert first["receipt"]["resource_ref_count"] == 2
    assert first["receipt"]["problem_signature_sha256"]

    same_set_different_order = stage_b.retrieve(
        **{**base, "resource_refs": ["db:world", "repo:clay", "repo:clay"]}
    )
    assert same_set_different_order["receipt"]["replayed"] is True

    drifts = [
        {"evidence_status": "UNDERCOVERED"},
        {"resource_refs": ["repo:clay", "db:other"]},
        {"limit": 5},
        {"budget_chars": 2049},
        {"problem_signature": {"goal": ["verify"], "mechanism": ["provenance"]}},
        {"query": "verify state provenance"},
    ]
    for delta in drifts:
        with pytest.raises(StaleGeneration, match="method_retrieval_identity"):
            stage_b.retrieve(**{**base, **delta})

    assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE kind='method_receipt'").fetchone()[0] == 1


def test_stage_b_context_budget_keeps_whole_counterevidence_first():
    counter = [{"memory_id": "counter:1", "payload": "c" * 80}]
    method = [{"memory_id": "method:1", "payload": "m" * 80}]
    counter_chars = len(StageBMethodRetrieval._canonical_json(counter[0]))

    methods, counterevidence, chars = StageBMethodRetrieval._bound_context(
        method,
        counter,
        budget_chars=counter_chars,
    )

    assert counterevidence == counter
    assert methods == []
    assert chars == counter_chars


def test_stage_b_rejects_cross_session_turn_episode_corruption(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    gabriel_session = db.ensure_session("gabriel", "clayverse-gabriel")
    andreas_session = db.ensure_session("andreas", "clayverse-andreas")

    foreign_turn = db.append_turn(andreas_session, "andreas", "user", "foreign turn")
    foreign_episode = "foreign:" + uuid.uuid4().hex
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (foreign_episode, andreas_session, time.time(), foreign_turn, 0.5, "[]", None, "OPEN"),
    )

    causal_id = "causal:" + uuid.uuid4().hex
    generation = db.entity_generation()
    # The schema's independent foreign keys allow individually valid IDs from another
    # session to be wired into Gabriel's active row. Stage-B must detect the relational
    # mismatch instead of treating referential validity as canonical identity.
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (gabriel_session, "gabriel", foreign_turn, foreign_episode, causal_id, generation, "[]", None, None, 0, time.time()),
    )

    with pytest.raises(RuntimeError, match="Stage-B retrieval identity mismatch"):
        StageBMethodRetrieval(db).retrieve(
            query="recover state provenance",
            user_id="gabriel",
            session_id=gabriel_session,
            turn_id=foreign_turn,
            episode_id=foreign_episode,
            causal_id=causal_id,
            generation=generation,
            evidence_status="UNKNOWN",
            problem_signature=None,
        )
