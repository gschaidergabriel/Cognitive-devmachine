from __future__ import annotations

from typing import Any

class CognitiveProcessABIValidationError(ValueError):
    pass

def _fail(code: str) -> None:
    raise CognitiveProcessABIValidationError(code)

def validate(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("schema") != "COGNITIVE_PROCESS_ABI/v1":
        _fail("SCHEMA_MISMATCH")

    authority = value.get("authority") or {}
    if authority.get("grid_size_law") != "VARIABLE_N_RUNTIME_PARAMETER_NOT_SEMANTIC_IDENTITY":
        _fail("GRID_SIZE_LAW_MISMATCH")
    if authority.get("database_law") != "SIMULATE_COGNITION_STORE_DURABLE_DATA":
        _fail("DATABASE_LAW_MISMATCH")
    if authority.get("claude_code_role") != "STRONG_MODEL_TOOL_CODE_EXECUTION_PARTNER":
        _fail("CLAUDE_CODE_ROLE_MISMATCH")
    if authority.get("free_only") is not True:
        _fail("FREE_ONLY_REQUIRED")
    if authority.get("canonical_census_schema") != "ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS/v1":
        _fail("CANONICAL_CENSUS_SCHEMA_MISMATCH")
    if authority.get("canonical_census_main_sha") != authority.get("reentered_canonical_main_sha"):
        _fail("CANONICAL_CENSUS_REENTRY_SHA_MISMATCH")

    process_ids = value.get("semantic_process_ids")
    expected = [f"ZECP{i:02d}" for i in range(1, 21)]
    if process_ids != expected:
        _fail("PROCESS_ID_SET_MISMATCH")

    sem = value.get("semantic_identity") or {}
    forbidden = set(sem.get("forbidden_identity_inputs") or [])
    required_forbidden = {"grid_n", "module_instance_id", "physical_host", "decode_lane", "retry_transport_id"}
    if not required_forbidden.issubset(forbidden):
        _fail("PHYSICAL_PLACEMENT_LEAKS_INTO_SEMANTIC_IDENTITY")
    if "grid_n" in set(sem.get("work_id_inputs") or []):
        _fail("GRID_N_MUST_NOT_DEFINE_WORK_ID")

    planes = value.get("state_planes") or {}
    if (planes.get("S0") or {}).get("authority") != "DETERMINISTIC_ONLY":
        _fail("S0_MUST_REMAIN_DETERMINISTIC")
    if (planes.get("S0") or {}).get("model_direct_write") is not False:
        _fail("MODEL_DIRECT_S0_WRITE_FORBIDDEN")
    if (planes.get("S1") or {}).get("authority") != "NONCANONICAL_CANDIDATE_PROJECTION":
        _fail("S1_AUTHORITY_MISMATCH")
    if (planes.get("S2") or {}).get("authority") != "NONCANONICAL_EXPERIMENTAL_PROJECTION":
        _fail("S2_AUTHORITY_MISMATCH")

    packet_types = value.get("packet_types") or {}
    required_packets = {
        "COGNITIVE_WORK/v1","COGNITIVE_RESULT/v1","DB_READ_REQUEST/v1","DB_WRITE_PROPOSAL/v1",
        "WORKSPACE_BROADCAST/v1","CLAUDE_BRIDGE_REQUEST/v1","CLAUDE_BRIDGE_RETURN/v1","EFFECT_PROPOSAL/v1",
    }
    if set(packet_types) != required_packets:
        _fail("PACKET_TYPE_SET_MISMATCH")
    for name, packet in packet_types.items():
        if "S0" in set(packet.get("may_write") or []):
            _fail(f"PACKET_DIRECT_S0_WRITE_FORBIDDEN:{name}")
    if packet_types["EFFECT_PROPOSAL/v1"].get("effect_authority") != "PROPOSE_ONLY":
        _fail("EFFECT_PROPOSAL_MUST_NOT_EXECUTE")

    effect = value.get("effect_boundary") or {}
    if effect.get("only_real_effect_path") != ["EFFECT_PROPOSAL/v1", "EffectGate", "EffectJournal"]:
        _fail("EFFECT_PATH_MISMATCH")
    if effect.get("model_or_module_direct_effect_forbidden") is not True:
        _fail("DIRECT_EFFECT_MUST_BE_FORBIDDEN")

    bridge = value.get("claude_code_bridge") or {}
    if bridge.get("activation_access_claim") != "FORBIDDEN_UNLESS_EXACT_MODEL_RUNTIME_INTERFACE_AND_CAUSAL_EVIDENCE_ARE_BOUND":
        _fail("CLAUDE_ACTIVATION_CLAIM_CEILING_MISSING")
    required_reentry = {
        "causal_event_id","workspace_episode_id","transfer_id","reentry_test_id",
        "pre_transfer_workspace_digest","transferred_state_digest","claude_interface_class",
        "claude_return_digest","post_return_workspace_digest","downstream_decision_or_work_ref",
        "matched_control_ref","measured_delta","off_target_regression","evidence_class",
    }
    if not required_reentry.issubset(set(bridge.get("reentry_receipt_required") or [])):
        _fail("REENTRY_RECEIPT_INCOMPLETE")
    if "MATCHED_CONTROL" not in bridge.get("causal_credit_rule",""):
        _fail("REENTRY_CAUSAL_CONTROL_REQUIRED")

    jspace = value.get("jspace") or {}
    if jspace.get("status") != "EMPIRICAL_CAUSAL_HYPOTHESIS":
        _fail("JSPACE_MUST_REMAIN_HYPOTHESIS")
    if jspace.get("majority_or_recurrence_mints_truth") is not False:
        _fail("MAJORITY_CANNOT_MINT_TRUTH")
    if jspace.get("frozen_v1_negative_evidence_preserved") is not True:
        _fail("FROZEN_V1_NEGATIVE_EVIDENCE_MUST_BE_PRESERVED")
    if "SEPARATELY_VERSIONED_PREREGISTERED_SUCCESSOR" not in jspace.get("successor_rule",""):
        _fail("JSPACE_SUCCESSOR_PREREGISTRATION_REQUIRED")

    coverage = value.get("owner_target_coverage") or {}
    if len(coverage) != 10:
        _fail("OWNER_ACCEPTANCE_COVERAGE_MUST_BE_10_OF_10")

    credit = value.get("credit_boundary") or {}
    for field in (
        "distributed_runtime_credit","claude_bridge_runtime_credit","jspace_model_runtime_credit",
        "whole_hcu_runtime_credit","whole_entityos_runtime_credit","training_credit",
    ):
        if credit.get(field) != 0:
            _fail(f"CREDIT_INFLATION:{field}")

    return {
        "ok": True,
        "process_count": len(process_ids),
        "packet_type_count": len(packet_types),
        "owner_acceptance_coverage": len(coverage),
        "sole_real_effect_path": "EFFECT_PROPOSAL/v1->EffectGate->EffectJournal",
        "next_exact_gate": value.get("next_exact_gate"),
    }
