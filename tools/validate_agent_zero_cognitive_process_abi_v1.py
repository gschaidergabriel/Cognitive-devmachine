#!/usr/bin/env python3
"""Fail-closed validator for AGENT_ZERO_COGNITIVE_PROCESS_ABI/v1.

PASS proves only the source contract and deterministic packet rejection logic.
It grants no EntityOS/HCU/J-Space/model/training/provider runtime credit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "AGENT_ZERO_COGNITIVE_PROCESS_ABI/v1"
CURRENT_OWNER_PATH = "research_entity/global/OWNER_CORRECTION_ZERO_ENTITYOS_COGNITIVE_GRID_DB_CLAUDECODE_GLOBAL_JSPACE_2026-08-25.md"
EXPECTED_PROCESSES = {f"AZP{i:02d}" for i in range(1, 21)}
REQUIRED_KINDS = {
    "COGNITIVE_WORK", "COGNITIVE_RESULT", "DB_READ_REQUEST", "DB_WRITE_PROPOSAL",
    "WORKSPACE_BROADCAST", "WORKSPACE_REENTRY", "CLAUDE_CODE_HANDOFF",
    "CLAUDE_CODE_RETURN", "JSPACE_MEASUREMENT", "EFFECT_PROPOSAL", "RECOVERY_REJOIN",
}


class AbiValidationError(ValueError):
    pass


def need(ok: bool, message: str) -> None:
    if not ok:
        raise AbiValidationError(message)


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AbiValidationError(f"ABI_READ_OR_JSON_FAILED:{exc}") from exc
    need(isinstance(value, dict), "ABI_OBJECT_REQUIRED")
    return value


def validate_contract(value: dict[str, Any]) -> dict[str, Any]:
    need(value.get("schema") == SCHEMA, "SCHEMA_MISMATCH")
    need(value.get("status") == "CANDIDATE_SOURCE_CONTRACT_NOT_RUNTIME_CREDIT", "STATUS_MUST_DENY_RUNTIME_CREDIT")

    authority = value.get("authority")
    need(isinstance(authority, dict), "AUTHORITY_OBJECT_REQUIRED")
    need(authority.get("owner_target_path") == CURRENT_OWNER_PATH, "CURRENT_OWNER_TARGET_PATH_REQUIRED")
    need(authority.get("grid_size_law") == "N_IS_RUNTIME_PARAMETER_NOT_ARCHITECTURE_IDENTITY", "VARIABLE_N_GRID_LAW_REQUIRED")
    need(authority.get("database_law") == "SIMULATE_COGNITION_STORE_DURABLE_DATA", "DB_VS_SIMULATION_LAW_REQUIRED")
    need("NOT_REPLACED" in authority.get("claude_code_role", ""), "CLAUDE_CODE_STRONG_PARTNER_ROLE_REQUIRED")
    blob = authority.get("census_source_blob_sha")
    need(isinstance(blob, str) and len(blob) == 40 and all(c in "0123456789abcdef" for c in blob), "CENSUS_BLOB_SHA_REQUIRED")

    processes = value.get("process_ids")
    need(isinstance(processes, list) and set(processes) == EXPECTED_PROCESSES and len(processes) == 20, "PROCESS_IDS_AZP01_TO_AZP20_REQUIRED")

    envelope = value.get("common_envelope")
    need(isinstance(envelope, dict), "COMMON_ENVELOPE_REQUIRED")
    required = envelope.get("required")
    need(isinstance(required, list), "COMMON_REQUIRED_LIST_REQUIRED")
    for field in ("causal_event_id", "admission_id", "generation", "process_id", "state_basis", "authority_refs", "provenance_refs", "payload"):
        need(field in required, f"COMMON_REQUIRED_FIELD_MISSING:{field}")
    need(envelope.get("abi_value") == SCHEMA, "ENVELOPE_ABI_VALUE_MISMATCH")
    need("NEVER_SELF_GRANT" in envelope.get("capability_law", ""), "CAPABILITY_SELF_GRANT_FENCE_REQUIRED")
    need("FIXED_GRID_SIZE" in envelope.get("grid_law", ""), "FIXED_GRID_SEMANTIC_FENCE_REQUIRED")

    kinds = value.get("packet_kinds")
    need(isinstance(kinds, dict), "PACKET_KINDS_OBJECT_REQUIRED")
    need(set(kinds) == REQUIRED_KINDS, f"PACKET_KIND_SET_MISMATCH:{sorted(set(kinds) ^ REQUIRED_KINDS)}")
    for name, spec in kinds.items():
        need(isinstance(spec, dict), f"{name}:SPEC_OBJECT_REQUIRED")
        need(isinstance(spec.get("required_payload"), list) and spec["required_payload"], f"{name}:REQUIRED_PAYLOAD_REQUIRED")
        need(isinstance(spec.get("authority"), str) and spec["authority"], f"{name}:AUTHORITY_CLASS_REQUIRED")
    need(kinds["DB_WRITE_PROPOSAL"].get("direct_commit_forbidden") is True, "DB_DIRECT_COMMIT_MUST_BE_FORBIDDEN")
    need(kinds["EFFECT_PROPOSAL"].get("direct_execution_forbidden") is True, "EFFECT_DIRECT_EXECUTION_MUST_BE_FORBIDDEN")

    bridge = value.get("claude_code_bridge")
    need(isinstance(bridge, dict), "CLAUDE_CODE_BRIDGE_REQUIRED")
    need(bridge.get("activation_access_default") == "UNKNOWN_NOT_CLAIMED", "CLAUDE_ACTIVATION_ACCESS_MUST_DEFAULT_UNKNOWN")
    need("MEASURABLY_CHANGE" in bridge.get("causal_reentry_requirement", ""), "CLAUDE_CAUSAL_REENTRY_REQUIREMENT_REQUIRED")

    research = value.get("jspace_research_boundary")
    need(isinstance(research, dict), "JSPACE_RESEARCH_BOUNDARY_REQUIRED")
    need(research.get("same_holdout_retune") == "FORBIDDEN", "FROZEN_V1_HOLDOUT_RETUNE_MUST_BE_FORBIDDEN")
    need("FALSIFIED_FOR_ABSTRACT_BEHAVIORAL_CONTROL" in research.get("frozen_qwen3_06b_structural_native_v1", ""), "FROZEN_V1_NEGATIVE_EVIDENCE_MUST_BE_PRESERVED")
    need("SEPARATELY_VERSIONED_PREREGISTERED" in research.get("successor_requirement", ""), "JSPACE_SUCCESSOR_PREREGISTRATION_REQUIRED")

    credit = value.get("credit_boundary")
    need(isinstance(credit, dict), "CREDIT_BOUNDARY_REQUIRED")
    for key in ("whole_entityos_hcu_runtime_credit", "hcu_full_runtime_credit", "jspace_model_runtime_credit", "training_credit", "provider_runtime_credit"):
        need(credit.get(key) == 0, f"CREDIT_MUST_REMAIN_ZERO:{key}")

    need(value.get("next_owner_gate") == "DB_VS_SIMULATION_BOUNDARY", "NEXT_OWNER_GATE_MISMATCH")
    return {
        "ok": True,
        "schema": SCHEMA,
        "process_count": 20,
        "packet_kind_count": len(kinds),
        "owner_target_path": CURRENT_OWNER_PATH,
        "next_owner_gate": "DB_VS_SIMULATION_BOUNDARY",
        "credit_scope": "ABI_SOURCE_CONTRACT_AND_DETERMINISTIC_VALIDATOR_ONLY",
    }


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_packet(packet: dict[str, Any], abi: dict[str, Any]) -> dict[str, Any]:
    validate_contract(abi)
    need(isinstance(packet, dict), "PACKET_OBJECT_REQUIRED")

    required = abi["common_envelope"]["required"]
    missing = [field for field in required if field not in packet]
    need(not missing, f"PACKET_COMMON_FIELDS_MISSING:{missing}")
    need(packet.get("abi") == SCHEMA, "PACKET_ABI_MISMATCH")

    kind = packet.get("packet_kind")
    need(kind in abi["packet_kinds"], "UNKNOWN_PACKET_KIND")
    need(packet.get("process_id") in EXPECTED_PROCESSES, "UNKNOWN_PROCESS_ID")
    for field in ("packet_id", "causal_event_id", "admission_id", "source_runtime_id"):
        need(_nonempty_string(packet.get(field)), f"PACKET_IDENTITY_REQUIRED:{field}")
    generation = packet.get("generation")
    need(isinstance(generation, int) and not isinstance(generation, bool) and generation >= 0, "GENERATION_NONNEGATIVE_INTEGER_REQUIRED")
    need(isinstance(packet.get("workspace_epoch"), int) and packet["workspace_epoch"] >= 0, "WORKSPACE_EPOCH_NONNEGATIVE_INTEGER_REQUIRED")
    need(isinstance(packet.get("target_selector"), dict), "TARGET_SELECTOR_OBJECT_REQUIRED")
    need(isinstance(packet.get("state_basis"), dict), "STATE_BASIS_OBJECT_REQUIRED")
    for field in abi["state_basis"]["required"]:
        need(field in packet["state_basis"], f"STATE_BASIS_FIELD_MISSING:{field}")
    need(isinstance(packet.get("authority_refs"), list), "AUTHORITY_REFS_LIST_REQUIRED")
    need(isinstance(packet.get("provenance_refs"), list), "PROVENANCE_REFS_LIST_REQUIRED")
    need(packet.get("self_granted_capability") is not True, "PACKET_SELF_GRANTED_CAPABILITY_FORBIDDEN")
    need(packet.get("fixed_grid_size_required") in (None, False), "FIXED_GRID_SIZE_PACKET_SEMANTIC_FORBIDDEN")

    payload = packet.get("payload")
    need(isinstance(payload, dict), "PAYLOAD_OBJECT_REQUIRED")
    for field in abi["packet_kinds"][kind]["required_payload"]:
        need(field in payload, f"{kind}:PAYLOAD_FIELD_MISSING:{field}")

    if kind == "DB_WRITE_PROPOSAL":
        need(payload.get("commit") is not True and payload.get("canonical") is not True, "DB_WRITE_PROPOSAL_CANNOT_COMMIT_CANONICAL_STATE")
    elif kind == "EFFECT_PROPOSAL":
        need(payload.get("execute") is not True, "EFFECT_PROPOSAL_CANNOT_EXECUTE")
        need(payload.get("effect_authority") in (None, "PROPOSE_ONLY"), "EFFECT_PROPOSAL_CANNOT_SELF_GRANT_EFFECT_AUTHORITY")
    elif kind == "COGNITIVE_RESULT":
        need(payload.get("truth_status") not in {"CANONICAL", "FACT", "VERIFIED_FACT"}, "COGNITIVE_RESULT_CANNOT_MINT_CANONICAL_FACT")
    elif kind == "CLAUDE_CODE_RETURN" and payload.get("activation_level_claim") is True:
        need(_nonempty_string(payload.get("exposed_interface_evidence_ref")), "CLAUDE_ACTIVATION_CLAIM_REQUIRES_EXPOSED_INTERFACE_EVIDENCE")
        need(_nonempty_string(payload.get("causal_reentry_receipt_ref")), "CLAUDE_ACTIVATION_CLAIM_REQUIRES_CAUSAL_REENTRY_EVIDENCE")
    elif kind == "JSPACE_MEASUREMENT" and payload.get("causal_claim") is True:
        for field in ("exact_model_artifact_ref", "intervention_receipt_ref", "fresh_holdout_id", "model_family_provenance_ref"):
            need(_nonempty_string(payload.get(field)), f"JSPACE_CAUSAL_CLAIM_REQUIRES:{field}")
        need(payload.get("controller_version") != "frozen_structural_native_v1", "FROZEN_V1_CANNOT_BE_PROMOTED_OR_RETUNED")
    elif kind == "RECOVERY_REJOIN":
        need(payload.get("replay_unknown_effect") is not True, "UNKNOWN_EXTERNAL_EFFECT_MUST_NOT_BE_BLINDLY_REPLAYED")

    return {
        "ok": True,
        "packet_kind": kind,
        "process_id": packet["process_id"],
        "causal_event_id": packet["causal_event_id"],
        "credit_scope": "PACKET_STATIC_VALIDATION_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="research_entity/global/AGENT_ZERO_COGNITIVE_PROCESS_ABI_v1.json")
    args = parser.parse_args()
    try:
        result = validate_contract(load(Path(args.path)))
    except AbiValidationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
