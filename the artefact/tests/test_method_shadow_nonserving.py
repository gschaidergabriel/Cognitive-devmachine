from __future__ import annotations

import time
import uuid

import pytest

from clayverse.retrieval import WorldAssembler
from clayverse.store import UnifiedDB


class _UnknownEvidence:
    def retrieve(self, **_kwargs):
        return {
            "items": [],
            "receipt": {
                "mode": "SHADOW",
                "status": "UNKNOWN",
                "query_sha256": "0" * 64,
                "truth_authority": False,
                "effect_authority": False,
            },
        }


class _ShadowMethods:
    def retrieve(self, **_kwargs):
        return {
            "triggered": True,
            "fact_status": "UNKNOWN",
            "method_status": "PRESENT",
            "items": [{
                "memory_id": "method:shadow-only",
                "kind": "framework",
                "context_class": "method_context",
                "truth_authority": False,
                "effect_authority": False,
            }],
            "counterevidence": [{
                "memory_id": "counter:shadow-only",
                "kind": "counterevidence",
                "context_class": "counterevidence",
                "truth_authority": False,
                "effect_authority": False,
            }],
            "invalid_method_ids": [],
            "policy_mode": "SHADOW",
        }


class _ActiveMethods(_ShadowMethods):
    def retrieve(self, **kwargs):
        result = super().retrieve(**kwargs)
        result["policy_mode"] = "ACTIVE"
        return result


def _assembler(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    assembler = WorldAssembler(db)
    assembler.microclay = _UnknownEvidence()
    return db, session_id, assembler


def test_shadow_method_observations_never_enter_claude_world_context(tmp_path):
    db, session_id, assembler = _assembler(tmp_path)
    try:
        assembler.methods = _ShadowMethods()
        world = assembler.assemble(
            session_id,
            (),
            query="unknown mechanism; how should it be tested?",
            turn_id="turn:test",
            episode_id="episode:test",
            causal_id="causal:test",
            generation=db.entity_generation(),
        )

        assert world["method_context"] == []
        assert world["counterevidence"] == []
        ids = {item.get("memory_id") for item in world["durable_memory"]}
        assert "method:shadow-only" not in ids
        assert "counter:shadow-only" not in ids

        receipt = world["retrieval_receipt"]
        assert receipt["method_policy_mode"] == "SHADOW"
        assert receipt["method_served"] is False
        assert receipt["method_status"] == "NOT_SERVED"
        assert receipt["method_shadow_status"] == "PRESENT"
        assert receipt["method_count"] == 0
        assert receipt["method_shadow_count"] == 1
        assert receipt["counterevidence_count"] == 0
        assert receipt["counterevidence_shadow_count"] == 1
        assert receipt["fact_status"] == "UNKNOWN"
    finally:
        db.close()


def test_active_method_mode_fails_closed_until_causal_receipt_gate_exists(tmp_path):
    db, session_id, assembler = _assembler(tmp_path)
    try:
        assembler.methods = _ActiveMethods()
        with pytest.raises(RuntimeError, match="causal receipt gate"):
            assembler.assemble(
                session_id,
                (),
                query="unknown mechanism; how should it be tested?",
                turn_id="turn:test",
                episode_id="episode:test",
                causal_id="causal:test",
                generation=db.entity_generation(),
            )
    finally:
        db.close()


def test_active_identity_rejects_cross_session_episode_corruption(tmp_path):
    db, gabriel_session, assembler = _assembler(tmp_path)
    try:
        db.ensure_user("andreas", "Andreas")
        andreas_session = db.ensure_session("andreas", "clayverse-andreas")
        turn_id = db.append_turn(gabriel_session, "gabriel", "user", "identity corruption probe")
        episode_id = str(uuid.uuid4())
        db.db.execute(
            "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (episode_id, andreas_session, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
        )
        db.db.execute(
            "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                gabriel_session,
                "gabriel",
                turn_id,
                episode_id,
                "causal:corrupt",
                db.entity_generation(),
                "[]",
                None,
                None,
                0,
                time.time(),
            ),
        )

        with pytest.raises(RuntimeError, match="active causal identity mismatch"):
            assembler._active_identity(gabriel_session)
    finally:
        db.close()
