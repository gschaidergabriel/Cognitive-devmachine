from __future__ import annotations

from typing import Any


class ABIValidationError(ValueError):
    pass


def _require(cond: bool, code: str) -> None:
    if not cond:
        raise ABIValidationError(code)


def validate(value: dict[str, Any]) -> dict[str, Any]:
    _require(value.get("schema") == "ZERO_ENTITYOS_COGNITIVE_PROCESS_ABI/v1", "SCHEMA_MISMATCH")
    authority = value.get("authority", {})
    _require(authority.get("product") == "EntityOS", "PRODUCT_AUTHORITY_MISMATCH")
    _require(authority.get("architecture") == "HCU", "ARCHITECTURE_AUTHORITY_MISMATCH")
    _require(authority.get("grid_size_law") == "N_IS_RUNTIME_PARAMETER", "GRID_SIZE_LAW_MISMATCH")
    _require(authority.get("durable_state_authority") == "PERSISTENT_DATABASE_DETERMINISTIC", "DB_AUTHORITY_MISMATCH")
    _require(authority.get("real_effect_authority") == "EFFECTGATE_EFFECTJOURNAL_ONLY", "EFFECT_AUTHORITY_MISMATCH")
    _require(authority.get("strong_model_partner") == "CLAUDE_CODE", "STRONG_MODEL_PARTNER_MISMATCH")
    _require(authority.get("model_outputs_are") == "CANDIDATE_PROJECTION_MEASUREMENT_ONLY", "MODEL_AUTHORITY_MISMATCH")
    _require(authority.get("supervisor_epoch") == "8.78", "SUPERVISOR_EPOCH_MISMATCH")
    _require(authority.get("execution_mode") == "FREE_ONLY", "EXECUTION_MODE_MISMATCH")

    wire = value.get("wire_types", {})
    required_types = {
        "COGNITIVE_WORK/v1",
        "COGNITIVE_RESULT/v1",
        "DB_WRITE_PROPOSAL/v1",
        "EFFECT_PROPOSAL/v1",
        "CLAUDE_BRIDGE_REQUEST/v1",
        "CLAUDE_BRIDGE_RESULT/v1",
        "WORKSPACE_REENTRY/v1",
        "EPHEMERAL_GRID_LEASE/v1",
        "JSPACE_SUCCESSOR_CANDIDATE/v1",
    }
    _require(set(wire) == required_types, "WIRE_TYPE_SET_MISMATCH")

    result = wire["COGNITIVE_RESULT/v1"]
    _require(result.get("authority") == "NONCANONICAL_OUTPUT_ONLY", "RESULT_AUTHORITY_ESCALATION")
    _require("CANONICAL" not in result.get("allowed_result_kinds", []), "CANONICAL_RESULT_KIND_FORBIDDEN")

    dbp = wire["DB_WRITE_PROPOSAL/v1"]
    _require(dbp.get("authority") == "PROPOSAL_ONLY", "DB_PROPOSAL_AUTHORITY_ESCALATION")
    _require(dbp.get("commit_rule") == "DETERMINISTIC_DB_GATE_AND_CAS_REQUIRED", "DB_COMMIT_RULE_MISMATCH")

    ep = wire["EFFECT_PROPOSAL/v1"]
    _require(ep.get("authority") == "PROPOSAL_ONLY", "EFFECT_PROPOSAL_AUTHORITY_ESCALATION")
    _require(ep.get("execution_rule") == "EFFECTGATE_EFFECTJOURNAL_REQUIRED", "EFFECT_EXECUTION_RULE_MISMATCH")

    lease = wire["EPHEMERAL_GRID_LEASE/v1"]
    _require(lease.get("authority") == "SCHEDULING_ONLY", "LEASE_AUTHORITY_ESCALATION")
    forbidden = set(lease.get("forbidden", []))
    _require({"CANONICAL_TRUTH_AUTHORITY", "REAL_EFFECT_AUTHORITY", "CAPABILITY_BROADENING"} <= forbidden, "LEASE_FORBIDDEN_SET_INCOMPLETE")

    js = wire["JSPACE_SUCCESSOR_CANDIDATE/v1"]
    _require(js.get("authority") == "EXPERIMENTAL_MEASUREMENT_ONLY", "JSPACE_AUTHORITY_ESCALATION")
    _require("FALSIFIED" in js.get("frozen_v1_status", ""), "FROZEN_V1_NEGATIVE_EVIDENCE_ERASED")
    _require("DO_NOT_RETUNE_OR_RERUN" in js.get("frozen_v1_status", ""), "FROZEN_V1_HOLDOUT_REUSE_FORBIDDEN")
    _require(js.get("promotion_rule") == "SEPARATELY_VERSIONED_PREREGISTERED_FRESH_HOLDOUT_EXECUTABLE_REVIEW_REQUIRED", "JSPACE_SUCCESSOR_PROMOTION_RULE_MISMATCH")

    invariants = set(value.get("invariants", []))
    must = {
        "SIMULATE_COGNITION_STORE_DURABLE_DATA",
        "NO_PACKET_SELF_GRANTS_CAPABILITY_OR_EFFECT_AUTHORITY",
        "FROZEN_JSPACE_V1_NEGATIVE_EVIDENCE_MUST_BE_PRESERVED",
        "SUCCESSOR_JSPACE_REQUIRES_SEPARATE_PREREGISTRATION_AND_FRESH_HOLDOUT",
    }
    _require(must <= invariants, "MANDATORY_INVARIANT_MISSING")

    credit = value.get("credit", {})
    for key in ("distributed_runtime", "whole_entityos", "whole_hcu", "jspace_model", "training"):
        _require(credit.get(key) == 0, f"CREDIT_INFLATION_{key.upper()}")

    return {
        "ok": True,
        "schema": value["schema"],
        "wire_type_count": len(wire),
        "grid_size_law": authority["grid_size_law"],
        "supervisor_epoch": authority["supervisor_epoch"],
        "runtime_credit": credit["distributed_runtime"],
    }
