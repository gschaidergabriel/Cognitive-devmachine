import time

import pytest

from clayverse.identity import IdentityRouter
from clayverse.method_memory import MethodMemory
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


def _record(signature):
    return {
        "problem_signature": signature,
        "preconditions": ["bounded evidence state"],
        "goal_shape": "diagnose",
        "method_steps": ["generate competing mechanisms", "run a discriminator"],
        "invariants": ["method context never changes fact status"],
        "expected_observations": ["one mechanism separates"],
        "falsifiers": ["the proposed discriminator cannot separate mechanisms"],
        "failure_modes": ["proxy overfit"],
        "scope_limits": ["requires an observable discriminator"],
        "source_episode_ids": ["episode-a", "episode-b"],
        "supporting_memory_ids": ["support-a", "support-b"],
        "counterexample_memory_ids": [],
        "provenance": {"source": "product-path-test"},
        "abstraction_version": 1,
        "support_count": 2,
        "success_count": 2,
        "failure_count": 0,
        "calibration": 0.8,
        "last_validated_at": time.time(),
        "status": "PROMOTED",
        "promotion_receipt_id": "promotion-test-1",
    }


def test_unknown_evidence_can_receive_method_context_without_becoming_fact(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    try:
        signature = MethodMemory.derive_problem_signature(
            query="diagnose the unfamiliar mechanism",
            evidence_status="UNKNOWN",
            resource_refs=[],
            collision_count=0,
        )
        method_id = MethodMemory(db).admit(
            kind="framework",
            name="mechanism discriminator",
            record=_record(signature),
            user_id="gabriel",
        )
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        turn = life.begin("diagnose the unfamiliar mechanism")
        context = turn["context"]

        assert context["retrieval_receipt"]["channel"] == "EVIDENCE_STAGE_A"
        assert context["retrieval_receipt"]["status"] == "UNKNOWN"
        assert context["durable_memory"] == []
        assert context["method_receipt"]["channel"] == "METHOD_STAGE_B"
        assert context["method_receipt"]["status"] == "PRESENT"
        assert context["method_receipt"]["fact_status_unchanged"] == "UNKNOWN"
        assert [item["memory_id"] for item in context["method_context"]] == [method_id]
        assert context["method_context"][0]["truth_authority"] is False
        assert context["method_context"][0]["effect_authority"] is False
        assert context["unknowns"] == [{
            "kind": "evidence_gap",
            "status": "UNKNOWN",
            "method_present": True,
            "truth_authority": False,
        }]
        life.abort("product-path-test-complete")
    finally:
        db.close()


def test_context_pressure_drops_method_before_direct_evidence():
    evidence = [{"memory_id": "fact-1", "kind": "fact", "value": "evidence", "subject": "x"}]
    world = {
        "own_recent": [],
        "cross_session_collision": [],
        "durable_memory": evidence,
        "retrieval_receipt": {
            "status": "PRESENT", "channel": "EVIDENCE_STAGE_A",
            "truth_authority": False, "effect_authority": False,
        },
        "problem_signature": {"goal_shape": "diagnose"},
        "method_context": [{"memory_id": "method-1", "method_steps": ["x" * 1200]}],
        "counterevidence": [],
        "unknowns": [],
        "method_receipt": {
            "triggered": True, "status": "PRESENT", "channel": "METHOD_STAGE_B",
            "truth_authority": False, "effect_authority": False,
        },
    }
    bounded = TurnLifecycle._bound_world(world, max_chars=900)
    assert bounded["durable_memory"] == evidence
    assert bounded["method_context"] == []


def test_method_receipt_cannot_smuggle_nested_unbounded_context():
    world = {
        "own_recent": [], "cross_session_collision": [], "durable_memory": [],
        "retrieval_receipt": {"status": "UNKNOWN"},
        "problem_signature": {}, "method_context": [], "counterevidence": [], "unknowns": [],
        "method_receipt": {"status": "PRESENT", "nested": {"not": "scalar"}},
    }
    with pytest.raises(TurnLifecycleError, match="method receipt values must be scalar"):
        TurnLifecycle._bound_world(world)
