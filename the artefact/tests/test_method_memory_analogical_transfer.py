import time

import pytest

from clayverse.identity import IdentityRouter
from clayverse.method_memory import MethodMemoryError
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _record(*, kind="framework", status="PROMOTED", name="Epoch-fenced state diagnosis", target_method_ids=None):
    return {
        "kind": kind,
        "name": name,
        "problem_signature": {
            "goal_shape": "diagnose",
            "facets": ["concurrency", "state-continuity"],
            "resource_types": [],
        },
        "preconditions": ["shared mutable state exists"],
        "goal_shape": "diagnose",
        "method_steps": ["freeze causal identity", "compare generations", "falsify stale writer"],
        "invariants": ["method context never promotes factual truth"],
        "expected_observations": ["a stale generation diverges when the hypothesis is correct"],
        "falsifiers": ["no shared mutable state exists"],
        "failure_modes": ["single-thread-only failure with no generation boundary"],
        "scope_limits": ["state-continuity and concurrency failures"],
        "source_episode_ids": ["episode-source-1"],
        "supporting_memory_ids": ["memory-source-1"],
        "counterexample_memory_ids": [],
        "target_method_ids": list(target_method_ids or []),
        "provenance": {"source": "isolated-transfer-test", "authority": "method-only"},
        "abstraction_version": 1,
        "support_count": 3,
        "success_count": 2,
        "failure_count": 1,
        "calibration": 0.75,
        "last_validated_at": time.time(),
        "status": status,
    }


def _begin(life, prompt):
    result = life.begin(prompt)
    assert result["context"]["retrieval_receipt"]["truth_authority"] is False
    assert result["context"]["method_receipt"]["truth_authority"] is False
    return result


def test_unknown_fact_can_receive_structural_method_without_becoming_fact(tmp_path):
    db = _db(tmp_path)
    try:
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        method_id = life.world.methods.admit(_record(), method_id="epoch-method")

        result = _begin(life, "why did concurrent state restart fail because generation race")
        context = result["context"]

        assert context["retrieval_receipt"]["status"] == "UNKNOWN"
        assert context["unknowns"] == [{"kind": "evidence_status", "status": "UNKNOWN"}]
        assert [item["method_id"] for item in context["method_context"]] == [method_id]
        assert context["method_receipt"]["status"] == "PRESENT"
        assert context["method_receipt"]["fact_status_unchanged"] == "UNKNOWN"
        assert context["evidence_context"] == context["durable_memory"] == []
        life.abort("test-complete")
    finally:
        db.close()


def test_known_fact_does_not_need_method_fallback_without_method_intent(tmp_path):
    db = _db(tmp_path)
    try:
        db.add_memory("fact", "alpha", "alpha launch code", None, "gabriel", {"source": "test"})
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        life.world.methods.admit(_record(), method_id="unrelated-method")

        result = _begin(life, "where is the alpha launch code")
        context = result["context"]
        assert context["retrieval_receipt"]["status"] == "PRESENT"
        assert context["method_context"] == []
        assert context["method_receipt"]["status"] == "NOT_TRIGGERED"
        assert context["unknowns"] == []
        life.abort("test-complete")
    finally:
        db.close()


def test_candidate_and_lexical_similarity_cannot_bypass_structural_gate(tmp_path):
    db = _db(tmp_path)
    try:
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        candidate = _record(kind="framework_candidate", status="CANDIDATE", name="candidate only")
        life.world.methods.admit(candidate, method_id="candidate")
        life.world.methods.admit(_record(name="promoted state method"), method_id="state-method")

        candidate_query = _begin(life, "why did concurrent state restart fail because generation race")
        assert "candidate" not in [x["method_id"] for x in candidate_query["context"]["method_context"]]
        life.abort("test-candidate")

        mismatch = _begin(life, "compare retrieval token budget performance")
        assert mismatch["context"]["retrieval_receipt"]["status"] == "UNKNOWN"
        assert mismatch["context"]["method_context"] == []
        assert mismatch["context"]["method_receipt"]["status"] == "UNKNOWN"
        life.abort("test-mismatch")
    finally:
        db.close()


def test_counterexample_blocks_target_method_and_replay_drift_fails_closed(tmp_path):
    db = _db(tmp_path)
    try:
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        life.world.methods.admit(_record(), method_id="epoch-method")
        life.world.methods.admit(
            _record(kind="counterexample", name="counterexample", target_method_ids=["epoch-method"]),
            method_id="counterexample-1",
        )

        result = _begin(life, "why did concurrent state restart fail because generation race")
        context = result["context"]
        assert context["method_context"] == []
        assert "epoch-method" in context["method_receipt"]["blocked_method_ids"]
        request = {
            "query": "why did concurrent state restart fail because generation race",
            "resource_refs": [],
            "evidence_status": "UNKNOWN",
            "user_id": "gabriel",
            "session_id": "session:gabriel",
            "turn_id": result["turn_id"],
            "episode_id": result["episode_id"],
            "causal_id": result["causal_id"],
            "generation": result["generation"],
        }
        replay = life.world.methods.retrieve(**request)
        assert replay["receipt"]["replayed"] is True
        with pytest.raises(MethodMemoryError, match="method_retrieval_identity"):
            life.world.methods.retrieve(**{**request, "evidence_status": "PRESENT"})
        life.abort("test-complete")
    finally:
        db.close()


def test_user_scoped_method_does_not_cross_perspectives(tmp_path):
    db = _db(tmp_path)
    try:
        gabriel = TurnLifecycle(db, "gabriel", "session:gabriel")
        gabriel.world.methods.admit(_record(), user_id="gabriel", method_id="gabriel-private-method")

        andreas = TurnLifecycle(db, "andreas", "session:andreas")
        result = _begin(andreas, "why did concurrent state restart fail because generation race")
        assert "gabriel-private-method" not in [x["method_id"] for x in result["context"]["method_context"]]
        andreas.abort("test-complete")
    finally:
        db.close()


def test_malformed_or_oversized_method_context_fails_closed_at_turn_boundary(tmp_path):
    db = _db(tmp_path)
    try:
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        base = {
            "own_recent": [],
            "cross_session_collision": [],
            "durable_memory": [],
            "evidence_context": [],
            "unknowns": [],
            "counterevidence": [],
            "retrieval_receipt": {"status": "UNKNOWN", "truth_authority": False, "effect_authority": False},
            "method_receipt": {"status": "UNKNOWN", "truth_authority": False, "effect_authority": False},
        }
        with pytest.raises(Exception, match="method context must be a list of objects"):
            life._bound_world({**base, "method_context": ["not-an-object"]})
        with pytest.raises(Exception, match="method context exceeds compact context bound"):
            life._bound_world({**base, "method_context": [{"x": "z" * 40_000}]})
    finally:
        db.close()
