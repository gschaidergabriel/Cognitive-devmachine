from __future__ import annotations

import time
import uuid

from clayverse.retrieval import WorldAssembler
from clayverse.store import UnifiedDB


class _UnknownEvidence:
    def retrieve(self, **kwargs):
        return {
            "items": [],
            "receipt": {
                "route": "evidence",
                "status": "UNKNOWN",
                "query_sha256": "test-query",
                "turn_id": kwargs["turn_id"],
                "episode_id": kwargs["episode_id"],
                "causal_id": kwargs["causal_id"],
                "generation": kwargs["generation"],
                "truth_authority": False,
                "effect_authority": False,
            },
        }


class _MethodBomb:
    def retrieve(self, **kwargs):
        raise AssertionError("canonical product path must not call raw-query Stage B")


class _ShadowMethod:
    def retrieve(self, **kwargs):
        assert kwargs["problem_signature"] == ["novel unresolved causal structure"]
        return {
            "items": [{
                "memory_id": "method-shadow-1",
                "kind": "framework",
                "subject": "shadow-only",
                "method_record": {"scope_limits": ["shadow only"]},
                "truth_authority": False,
                "effect_authority": False,
            }],
            "receipt": {
                "route": "method",
                "matcher": "explicit_signature_token_v1_shadow",
                "signature_source": "EXPLICIT_SHADOW_INPUT",
                "status": "METHOD_PRESENT",
                "causal_id": kwargs["causal_id"],
                "generation": kwargs["generation"],
                "truth_authority": False,
                "effect_authority": False,
                "promotion_verified": True,
            },
        }


def _active_unknown_turn(db: UnifiedDB):
    db.ensure_user("gabriel", "Gabriel")
    session_id = db.ensure_session("gabriel", "clayverse-gabriel")
    generation = db.entity_generation()
    turn_id = db.append_turn(session_id, "gabriel", "user", "novel unresolved problem")
    episode_id = str(uuid.uuid4())
    causal_id = str(uuid.uuid4())
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (episode_id, session_id, time.time(), turn_id, 1.0, "[]", None, "OPEN"),
    )
    db.db.execute(
        "INSERT INTO active_turns("
        "session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,"
        "effect_id,outcome,workspace_selected,started_at"
        ") VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            session_id, "gabriel", turn_id, episode_id, causal_id, generation, "[]",
            None, None, 0, time.time(),
        ),
    )
    return session_id, generation, turn_id, episode_id, causal_id


def test_canonical_active_turn_does_not_invoke_raw_query_stage_b(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        session_id, generation, _, _, causal_id = _active_unknown_turn(db)
        world = WorldAssembler(db)
        world.microclay = _UnknownEvidence()
        world.methods = _MethodBomb()

        result = world.assemble(session_id, ())

        assert result["retrieval_receipt"]["status"] == "UNKNOWN"
        assert result["method_context"] == []
        assert result["counterevidence"] == []
        assert result["method_receipt"] == {
            "route": "method",
            "mode": "SHADOW_METHOD_V1",
            "status": "METHOD_NOT_SERVED_SIGNATURE_ADMISSION_REQUIRED",
            "causal_id": causal_id,
            "generation": generation,
            "truth_authority": False,
            "effect_authority": False,
            "served": False,
        }
        assert result["unknowns"] == [{
            "status": "FACT_UNKNOWN",
            "query_sha256": "test-query",
            "method_present": False,
        }]
    finally:
        db.close()


def test_explicit_internal_method_evaluation_requires_signature_and_is_not_served(tmp_path):
    db = UnifiedDB(tmp_path / "u.db")
    try:
        session_id, generation, _, _, causal_id = _active_unknown_turn(db)
        world = WorldAssembler(db)
        world.microclay = _UnknownEvidence()
        world.methods = _ShadowMethod()

        result = world.assemble(
            session_id,
            (),
            query="novel unresolved problem",
            problem_signature=["novel unresolved causal structure"],
            generation=generation,
        )

        assert [item["memory_id"] for item in result["method_context"]] == ["method-shadow-1"]
        assert result["method_receipt"]["mode"] == "SHADOW_METHOD_V1"
        assert result["method_receipt"]["served"] is False
        assert result["method_receipt"]["status"] == "METHOD_PRESENT"
        assert result["method_receipt"]["causal_id"] == causal_id
        assert result["method_receipt"]["truth_authority"] is False
        assert result["unknowns"][0]["status"] == "FACT_UNKNOWN"
    finally:
        db.close()
