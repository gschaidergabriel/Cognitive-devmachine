from __future__ import annotations

import json
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


def _request(stage_b, *, session_id, turn_id, episode_id, causal_id, generation):
    return stage_b.retrieve(
        query="recover state provenance",
        user_id="gabriel",
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
        evidence_status="UNKNOWN",
        resource_refs=["repo:clay"],
        problem_signature=None,
        limit=4,
        budget_chars=2048,
    )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("selected_method_ids", ["forged:method"]),
        ("counterevidence_ids", ["forged:counterexample"]),
        ("chars_selected", 1),
        ("factual_status_unchanged", "PRESENT"),
        ("truth_authority", True),
        ("effect_authority", True),
    ],
)
def test_stage_b_replay_rejects_persisted_receipt_output_drift(
    tmp_path, field, replacement
):
    db, session_id, turn_id, episode_id, causal_id, generation = _active_turn(tmp_path)
    stage_b = StageBMethodRetrieval(db)
    first = _request(
        stage_b,
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id,
        causal_id=causal_id,
        generation=generation,
    )
    assert first["receipt"]["status"] == "SIGNATURE_REQUIRED"

    memory_id = stage_b._receipt_memory_id(causal_id)
    row = db.db.execute(
        "SELECT value FROM durable_memory WHERE memory_id=?", (memory_id,)
    ).fetchone()
    payload = json.loads(str(row["value"]))
    payload["receipt"][field] = replacement
    db.db.execute(
        "UPDATE durable_memory SET value=? WHERE memory_id=?",
        (stage_b._canonical_json(payload), memory_id),
    )

    with pytest.raises(StaleGeneration, match="method_retrieval_receipt"):
        _request(
            stage_b,
            session_id=session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=generation,
        )
