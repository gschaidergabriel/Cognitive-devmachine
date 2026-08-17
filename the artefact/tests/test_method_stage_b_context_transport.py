from __future__ import annotations

import pytest

from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


def _world(status="UNKNOWN"):
    return {
        "own_recent": [],
        "cross_session_collision": [],
        "durable_memory": [],
        "evidence_context": [],
        "method_context": [],
        "unknowns": [] if status == "PRESENT" else [{"status": status, "fact_resolved": False}],
        "counterevidence": [],
        "retrieval_receipt": {
            "status": status,
            "truth_authority": False,
            "effect_authority": False,
        },
        "method_retrieval_receipt": {
            "policy_version": 2,
            "evidence_status": status,
            "selected_method_ids": [],
            "counterevidence_ids": [],
            "truth_authority": False,
            "effect_authority": False,
        },
    }


def test_bound_world_preserves_separated_method_unknown_and_counterevidence_channels():
    world = _world("UNKNOWN")
    world["durable_memory"] = [{"memory_id": "fact:1", "kind": "fact", "value": "observed"}]
    world["evidence_context"] = list(world["durable_memory"])
    world["method_context"] = [{"memory_id": "method:1", "kind": "framework", "value": "how to test"}]
    world["counterevidence"] = [{"memory_id": "counter:1", "kind": "counterexample", "value": "scope limit"}]
    world["method_retrieval_receipt"].update({
        "selected_method_ids": ["method:1"],
        "counterevidence_ids": ["counter:1"],
        "factual_status_unchanged": "UNKNOWN",
    })

    packed = TurnLifecycle._bound_world(world)

    assert packed["durable_memory"] == packed["evidence_context"]
    assert [item["memory_id"] for item in packed["method_context"]] == ["method:1"]
    assert [item["memory_id"] for item in packed["counterevidence"]] == ["counter:1"]
    assert packed["unknowns"][0]["fact_resolved"] is False
    assert packed["retrieval_receipt"]["status"] == "UNKNOWN"
    assert packed["method_retrieval_receipt"]["factual_status_unchanged"] == "UNKNOWN"


def test_bound_world_rejects_method_receipt_context_id_drift():
    world = _world("UNKNOWN")
    world["method_context"] = [{"memory_id": "method:1"}]
    world["method_retrieval_receipt"]["selected_method_ids"] = ["method:other"]
    with pytest.raises(TurnLifecycleError, match="selected IDs diverge"):
        TurnLifecycle._bound_world(world)


def test_bound_world_rejects_method_fact_status_drift():
    world = _world("UNKNOWN")
    world["method_retrieval_receipt"]["factual_status_unchanged"] = "PRESENT"
    with pytest.raises(TurnLifecycleError, match="factual status diverges"):
        TurnLifecycle._bound_world(world)


def test_bound_world_rejects_evidence_alias_divergence():
    world = _world("PRESENT")
    world["durable_memory"] = [{"memory_id": "fact:1", "value": "canonical"}]
    world["evidence_context"] = [{"memory_id": "fact:2", "value": "competing"}]
    with pytest.raises(TurnLifecycleError, match="evidence_context diverges"):
        TurnLifecycle._bound_world(world)


def test_bound_world_rejects_nested_evidence_receipt_and_authority_escalation():
    nested = _world("UNKNOWN")
    nested["retrieval_receipt"]["nested"] = {"not": "compact"}
    with pytest.raises(TurnLifecycleError, match="values must be scalar"):
        TurnLifecycle._bound_world(nested)

    escalation = _world("UNKNOWN")
    escalation["method_retrieval_receipt"]["truth_authority"] = True
    with pytest.raises(TurnLifecycleError, match="authority flags must be false"):
        TurnLifecycle._bound_world(escalation)


def test_bound_world_never_silently_drops_nonoptional_method_channels_to_fit_total_budget():
    world = _world("UNKNOWN")
    world["method_context"] = [{"memory_id": "method:1", "value": "x" * 1024}]
    world["method_retrieval_receipt"].update({
        "selected_method_ids": ["method:1"],
        "factual_status_unchanged": "UNKNOWN",
    })
    with pytest.raises(TurnLifecycleError, match="world context exceeds bound"):
        TurnLifecycle._bound_world(world, max_chars=128)
