import pytest

from cognitive_process_abi_v1 import (
    CognitiveABIError,
    REQUEST_VERSION,
    RESULT_VERSION,
    classify_data_disposition,
    semantic_identity_material_from_request,
    validate_process_request,
)
from variable_grid_scheduler_v1 import assign_process, aggregate_candidate_results
from claude_code_workspace_bridge_v1 import (
    RETURN_VERSION,
    build_reentry_probe,
    ingest_return,
)


def request():
    return {
        "schema_version": REQUEST_VERSION,
        "causal_event_id": "evt-1",
        "admission_id": "adm-1",
        "generation": 7,
        "process_instance_id": "proc-identity-bound-upstream",
        "process_id": "PLAN",
        "step_index": 3,
        "parent_process_instance_id": "parent-2",
        "input_refs": ["db:task/1"],
        "evidence_refs": ["ev:1"],
        "capability_scope_ref": "cap:readonly",
        "resource_budget_ref": "budget:bounded",
    }


def result(candidates):
    return {
        "schema_version": RESULT_VERSION,
        "process_instance_id": "proc-identity-bound-upstream",
        "process_id": "PLAN",
        "candidates": candidates,
        "evidence_refs": ["ev:1"],
        "uncertainty": 0.25,
        "db_write_proposals": [],
        "effect_proposals": [],
    }


def test_semantic_identity_excludes_topology():
    material = semantic_identity_material_from_request(request()).as_mapping()
    assert "grid_size" not in material
    assert "cell_id" not in material
    assert "replica_index" not in material
    assert material["process_id"] == "PLAN"


def test_semantic_request_rejects_topology_fields():
    req = request()
    req["grid_size"] = 10
    with pytest.raises(CognitiveABIError, match="TOPOLOGY_FIELD_IN_SEMANTIC_REQUEST"):
        validate_process_request(req)


def test_variable_n_assignment_preserves_process_identity():
    req = request()
    a10 = assign_process(req, grid_size=10, replicas=2)
    a20 = assign_process(req, grid_size=20, replicas=2)
    assert {a.process_instance_id for a in a10 + a20} == {req["process_instance_id"]}
    assert {a.grid_size for a in a10} == {10}
    assert {a.grid_size for a in a20} == {20}


def test_majority_never_promotes_truth():
    agg = aggregate_candidate_results([
        result([{"plan": "A"}]),
        result([{"plan": "A"}]),
        result([{"plan": "B"}]),
    ])
    assert agg["agreement_state"] == "UNRESOLVED_DISAGREEMENT"
    assert agg["truth_promotion"] == "FORBIDDEN_BY_AGGREGATION"
    assert len(agg["alternatives"]) == 3


def test_direct_canonical_write_is_rejected():
    req = request()
    req["canonical_state_update"] = {"x": 1}
    with pytest.raises(CognitiveABIError, match="DIRECT_AUTHORITY_FIELD_FORBIDDEN"):
        validate_process_request(req)


def test_db_vs_simulation_boundary():
    assert classify_data_disposition("durable_memory") == "STORE_DURABLY"
    assert classify_data_disposition("hypothesis") == "SIMULATE_EPHEMERALLY"
    assert classify_data_disposition("memory_update") == "PROPOSE_THEN_ADMIT_EXTERNALLY"
    assert classify_data_disposition("mystery") == "UNKNOWN_FAIL_CLOSED"


def test_claude_return_rejects_activation_claim():
    packet = {
        "schema_version": RETURN_VERSION,
        "process_instance_id": "proc-1",
        "handoff_id": "handoff-1",
        "return_id": "return-1",
        "interface_mode": "TEXT_TOOL_SESSION",
        "activation_access_claim": True,
        "evidence_refs": ["tool:result"],
    }
    with pytest.raises(CognitiveABIError, match="UNPROVEN_ACTIVATION_ACCESS_CLAIM"):
        ingest_return(packet)


def test_reentry_is_measurement_not_truth():
    packet = {
        "schema_version": RETURN_VERSION,
        "process_instance_id": "proc-1",
        "handoff_id": "handoff-1",
        "return_id": "return-1",
        "interface_mode": "TEXT_TOOL_SESSION",
        "activation_access_claim": False,
        "evidence_refs": ["tool:result"],
    }
    probe = build_reentry_probe(
        claude_return=packet,
        pre_reentry_state_ref="state:before",
        post_reentry_observation_ref="state:after",
        downstream_action_ref="candidate:next",
        discriminator_ref="test:counterfactual-v1",
    )
    assert probe["causal_claim_status"] == "UNRESOLVED_UNTIL_CONTROLLED_DISCRIMINATOR"
    assert probe["global_jspace_claim"] == "OBSERVABLE_WORKSPACE_BRIDGE_ONLY"
    assert probe["canonical_truth_authority"] is False
