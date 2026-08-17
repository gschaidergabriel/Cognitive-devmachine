from __future__ import annotations

import json
import time
import uuid

import pytest

from clayverse.method_signature import MethodSignatureAuthority
from clayverse.method_stage_b import StageBMethodRetrieval
from clayverse.store import StaleGeneration, UnifiedDB


SIGNATURE = {"goal": ["recover"], "mechanism": ["provenance", "stateful"]}


def _active_turn(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    turn_id = db.append_turn(session_id, "gabriel", "user", "recover state provenance")
    episode_id = "active:" + uuid.uuid4().hex
    causal_id = "causal:" + uuid.uuid4().hex
    generation = db.entity_generation()
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
    )
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (session_id, "gabriel", turn_id, episode_id, causal_id, generation, "[]", None, None, 0, time.time()),
    )
    return db, session_id, turn_id, episode_id, causal_id, generation


def _signature(db, session_id, turn_id, episode_id, causal_id, generation, signature=SIGNATURE):
    return MethodSignatureAuthority(db).admit(
        problem_signature=signature,
        producer="clayverse:problem-signature:v1",
        user_id="gabriel",
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
    )


def _base(session_id, turn_id, episode_id, causal_id, generation, signature_receipt_id=None):
    return dict(
        query="recover state provenance",
        user_id="gabriel",
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        evidence_status="UNKNOWN",
        resource_refs=["repo:clay", "db:world"],
        signature_receipt_id=signature_receipt_id,
        limit=4,
        budget_chars=2048,
    )


def test_raw_structured_signature_is_non_serving_and_does_not_poison_causal_use_receipt(tmp_path):
    db, session_id, turn_id, episode_id, causal_id, generation = _active_turn(tmp_path)
    stage_b = StageBMethodRetrieval(db)
    result = stage_b.retrieve(
        **_base(session_id, turn_id, episode_id, causal_id, generation),
        problem_signature=SIGNATURE,
    )
    assert result["methods"] == []
    assert result["counterevidence"] == []
    assert result["problem_signature"] is None
    assert result["receipt"]["status"] == "SIGNATURE_REQUIRED"
    assert result["receipt"]["factual_status_unchanged"] == "UNKNOWN"
    assert result["receipt"]["truth_authority"] is False
    assert result["receipt"]["effect_authority"] is False
    assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE subject LIKE 'stage_b_method_use:%'").fetchone()[0] == 0

    signature_id = _signature(db, session_id, turn_id, episode_id, causal_id, generation)
    admitted = stage_b.retrieve(**_base(session_id, turn_id, episode_id, causal_id, generation, signature_id))
    assert admitted["receipt"]["status"] == "METHOD_UNKNOWN"
    assert admitted["receipt"]["signature_receipt_id"] == signature_id
    assert admitted["receipt"]["replayed"] is False
    assert db.db.execute("SELECT COUNT(*) FROM durable_memory WHERE subject LIKE 'stage_b_method_use:%'").fetchone()[0] == 1


def test_signature_admission_is_exact_active_identity_and_idempotent(tmp_path):
    db, session_id, turn_id, episode_id, causal_id, generation = _active_turn(tmp_path)
    signature_id = _signature(db, session_id, turn_id, episode_id, causal_id, generation)
    again = _signature(db, session_id, turn_id, episode_id, causal_id, generation)
    assert again == signature_id

    with pytest.raises(StaleGeneration, match="method_signature_identity"):
        _signature(
            db, session_id, turn_id, episode_id, causal_id, generation,
            {"goal": ["verify"], "mechanism": ["provenance"]},
        )

    row = db.db.execute("SELECT * FROM durable_memory WHERE memory_id=?", (signature_id,)).fetchone()
    payload = json.loads(row["value"])
    provenance = json.loads(row["provenance"])
    assert row["kind"] == "method_receipt"
    assert payload["truth_authority"] is False and payload["effect_authority"] is False
    assert provenance["truth_authority"] is False and provenance["effect_authority"] is False


def test_stage_b_use_receipt_binds_full_request_and_admitted_signature_identity(tmp_path):
    db, session_id, turn_id, episode_id, causal_id, generation = _active_turn(tmp_path)
    signature_id = _signature(db, session_id, turn_id, episode_id, causal_id, generation)
    stage_b = StageBMethodRetrieval(db)
    base = _base(session_id, turn_id, episode_id, causal_id, generation, signature_id)

    first = stage_b.retrieve(**base)
    assert first["receipt"]["replayed"] is False
    assert first["receipt"]["signature_receipt_id"] == signature_id
    assert first["receipt"]["signature_sha256"]
    assert first["receipt"]["request_identity_sha256"]
    assert first["receipt"]["selection_sha256"]

    same_set = stage_b.retrieve(**{**base, "resource_refs": ["db:world", "repo:clay", "repo:clay"]})
    assert same_set["receipt"]["replayed"] is True

    for delta in (
        {"evidence_status": "UNDERCOVERED"},
        {"resource_refs": ["repo:clay", "db:other"]},
        {"limit": 5},
        {"budget_chars": 2049},
        {"query": "verify state provenance"},
    ):
        with pytest.raises(StaleGeneration, match="method_retrieval_identity"):
            stage_b.retrieve(**{**base, **delta})


def test_stage_b_replay_detects_selection_payload_tamper(tmp_path):
    db, session_id, turn_id, episode_id, causal_id, generation = _active_turn(tmp_path)
    signature_id = _signature(db, session_id, turn_id, episode_id, causal_id, generation)
    stage_b = StageBMethodRetrieval(db)
    base = _base(session_id, turn_id, episode_id, causal_id, generation, signature_id)
    first = stage_b.retrieve(**base)
    receipt_id = first["receipt"]["receipt_id"]
    row = db.db.execute("SELECT value FROM durable_memory WHERE memory_id=?", (receipt_id,)).fetchone()
    payload = json.loads(row["value"])
    payload["methods"] = [{"memory_id": "forged", "kind": "framework"}]
    db.db.execute("UPDATE durable_memory SET value=? WHERE memory_id=?", (json.dumps(payload, sort_keys=True), receipt_id))
    with pytest.raises(StaleGeneration, match="method_retrieval_selection_identity"):
        stage_b.retrieve(**base)


def test_stage_b_context_budget_keeps_whole_counterevidence_first():
    counter = [{"memory_id": "counter:1", "payload": "c" * 80}]
    method = [{"memory_id": "method:1", "payload": "m" * 80}]
    counter_chars = len(StageBMethodRetrieval._canonical_json(counter[0]))
    methods, counterevidence, chars = StageBMethodRetrieval._bound_context(method, counter, budget_chars=counter_chars)
    assert counterevidence == counter
    assert methods == []
    assert chars == counter_chars


def test_signature_admission_rejects_cross_session_relational_corruption(tmp_path):
    db = UnifiedDB(tmp_path / "world.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    gabriel_session = db.ensure_session("gabriel", "clayverse-gabriel")
    andreas_session = db.ensure_session("andreas", "clayverse-andreas")
    foreign_turn = db.append_turn(andreas_session, "andreas", "user", "foreign turn")
    foreign_episode = "foreign:" + uuid.uuid4().hex
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) VALUES(?,?,?,?,?,?,?,?)",
        (foreign_episode, andreas_session, time.time(), foreign_turn, 0.5, "[]", None, "OPEN"),
    )
    causal_id = "causal:" + uuid.uuid4().hex
    generation = db.entity_generation()
    db.db.execute(
        "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (gabriel_session, "gabriel", foreign_turn, foreign_episode, causal_id, generation, "[]", None, None, 0, time.time()),
    )
    with pytest.raises(StaleGeneration, match="method_signature_identity"):
        MethodSignatureAuthority(db).admit(
            problem_signature=SIGNATURE,
            producer="clayverse:problem-signature:v1",
            user_id="gabriel", session_id=gabriel_session, turn_id=foreign_turn,
            episode_id=foreign_episode, causal_id=causal_id, generation=generation,
        )
