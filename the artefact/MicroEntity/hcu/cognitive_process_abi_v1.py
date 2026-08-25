"""EntityOS/HCU cognitive-process ABI v1.

Source-level contract for the owner-directed variable-size cognitive grid.
This module does not create canonical state, a canonicalizer, effect authority,
or model/J-Space runtime credit. Process semantic identity is intentionally
independent of grid size and physical/logical cell assignment.

Authority epoch: owner 2026-08-25 + supervisor 8.78.
Canonical census: research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

ABI_VERSION = "ENTITYOS_HCU_COGNITIVE_PROCESS_ABI/v1"
REQUEST_VERSION = "ENTITYOS_HCU_COGNITIVE_PROCESS_REQUEST/v1"
RESULT_VERSION = "ENTITYOS_HCU_COGNITIVE_PROCESS_RESULT/v1"
ASSIGNMENT_VERSION = "ENTITYOS_HCU_COGNITIVE_ASSIGNMENT/v1"
CENSUS_SCHEMA = "ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS/v1"
CENSUS_PATH = "research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json"
KNOWN_PROCESS_IDS = frozenset({f"ZECP{i:02d}" for i in range(1, 21)})

FORBIDDEN_DIRECT_AUTHORITY_FIELDS = frozenset({
    "canonical_fact_write", "canonical_state_update", "canonical_truth",
    "effect_execute", "effect_committed", "journal_commit", "authority_grant",
    "provider_authority_grant",
})

DURABLE_EXACT_KINDS = frozenset({
    "canonical_fact", "durable_memory", "task_state", "project_state",
    "historical_event", "historical_result", "evidence_ref", "provenance_ref",
    "long_lived_goal", "configuration", "index", "retrieval_structure",
    "checkpoint", "snapshot", "counter", "identifier", "epoch", "digest",
})
SIMULATED_EPHEMERAL_KINDS = frozenset({
    "attention_state", "hypothesis", "plan_candidate", "working_interpretation",
    "uncertainty_estimate", "critique", "workspace_competition_state",
    "bounded_simulation", "hyperposition_candidate",
})
MIXED_PROPOSAL_KINDS = frozenset({
    "memory_update", "goal_update", "tool_action", "effect_request",
    "workspace_db_compression",
})


class CognitiveABIError(ValueError):
    """Fail-closed ABI validation error."""


@dataclass(frozen=True)
class SemanticProcessIdentityMaterial:
    causal_event_id: str
    admission_id: str
    generation: int
    process_id: str
    step_index: int
    parent_process_instance_id: str | None = None

    def as_mapping(self) -> dict[str, Any]:
        """Return material for the existing canonical identity authority.

        Deliberately excludes grid size, cell id, model replica, provider,
        and physical execution details. Those belong to assignment/runtime
        receipts and cannot alter the semantic process instance identity.
        """
        return {
            "schema_version": ABI_VERSION,
            "census_schema": CENSUS_SCHEMA,
            "causal_event_id": self.causal_event_id,
            "admission_id": self.admission_id,
            "generation": self.generation,
            "process_id": self.process_id,
            "step_index": self.step_index,
            "parent_process_instance_id": self.parent_process_instance_id,
        }


def _require_text(packet: Mapping[str, Any], key: str) -> str:
    value = packet.get(key)
    if not isinstance(value, str) or not value:
        raise CognitiveABIError(f"{key}:REQUIRED_NONEMPTY_TEXT")
    return value


def _reject_direct_authority(packet: Mapping[str, Any]) -> None:
    present = sorted(FORBIDDEN_DIRECT_AUTHORITY_FIELDS.intersection(packet))
    if present:
        raise CognitiveABIError("DIRECT_AUTHORITY_FIELD_FORBIDDEN:" + ",".join(present))


def validate_process_request(packet: Mapping[str, Any]) -> dict[str, Any]:
    if packet.get("schema_version") != REQUEST_VERSION:
        raise CognitiveABIError("REQUEST_SCHEMA_VERSION")
    _reject_direct_authority(packet)

    process_id = _require_text(packet, "process_id")
    if process_id not in KNOWN_PROCESS_IDS:
        raise CognitiveABIError("UNKNOWN_PROCESS_ID")
    _require_text(packet, "causal_event_id")
    _require_text(packet, "admission_id")
    _require_text(packet, "process_instance_id")
    _require_text(packet, "capability_scope_ref")
    _require_text(packet, "resource_budget_ref")

    generation = packet.get("generation")
    step_index = packet.get("step_index")
    if not isinstance(generation, int) or generation < 0:
        raise CognitiveABIError("GENERATION_INVALID")
    if not isinstance(step_index, int) or step_index < 0:
        raise CognitiveABIError("STEP_INDEX_INVALID")

    for topology_key in ("grid_size", "cell_id", "replica_index", "physical_worker_id"):
        if topology_key in packet:
            raise CognitiveABIError(f"TOPOLOGY_FIELD_IN_SEMANTIC_REQUEST:{topology_key}")

    input_refs = packet.get("input_refs", [])
    evidence_refs = packet.get("evidence_refs", [])
    if not isinstance(input_refs, list) or not all(isinstance(x, str) and x for x in input_refs):
        raise CognitiveABIError("INPUT_REFS_INVALID")
    if not isinstance(evidence_refs, list) or not all(isinstance(x, str) and x for x in evidence_refs):
        raise CognitiveABIError("EVIDENCE_REFS_INVALID")
    return dict(packet)


def validate_process_result(packet: Mapping[str, Any]) -> dict[str, Any]:
    if packet.get("schema_version") != RESULT_VERSION:
        raise CognitiveABIError("RESULT_SCHEMA_VERSION")
    _reject_direct_authority(packet)

    process_id = _require_text(packet, "process_id")
    if process_id not in KNOWN_PROCESS_IDS:
        raise CognitiveABIError("UNKNOWN_PROCESS_ID")
    _require_text(packet, "process_instance_id")

    for key in ("candidates", "evidence_refs", "db_write_proposals", "effect_proposals"):
        if not isinstance(packet.get(key, []), list):
            raise CognitiveABIError(f"{key.upper()}_INVALID")

    uncertainty = packet.get("uncertainty")
    if uncertainty is not None:
        if not isinstance(uncertainty, (int, float)) or isinstance(uncertainty, bool):
            raise CognitiveABIError("UNCERTAINTY_INVALID")
        if not 0.0 <= float(uncertainty) <= 1.0:
            raise CognitiveABIError("UNCERTAINTY_OUT_OF_RANGE")

    for proposal in packet.get("db_write_proposals", []):
        if not isinstance(proposal, Mapping):
            raise CognitiveABIError("DB_WRITE_PROPOSAL_INVALID")
        _reject_direct_authority(proposal)
    for proposal in packet.get("effect_proposals", []):
        if not isinstance(proposal, Mapping):
            raise CognitiveABIError("EFFECT_PROPOSAL_INVALID")
        _reject_direct_authority(proposal)
    return dict(packet)


def validate_assignment(packet: Mapping[str, Any]) -> dict[str, Any]:
    if packet.get("schema_version") != ASSIGNMENT_VERSION:
        raise CognitiveABIError("ASSIGNMENT_SCHEMA_VERSION")
    _require_text(packet, "assignment_id")
    _require_text(packet, "process_instance_id")
    _require_text(packet, "cell_id")
    grid_size = packet.get("grid_size")
    replica_index = packet.get("replica_index")
    if not isinstance(grid_size, int) or grid_size < 1:
        raise CognitiveABIError("GRID_SIZE_INVALID")
    if not isinstance(replica_index, int) or replica_index < 0:
        raise CognitiveABIError("REPLICA_INDEX_INVALID")
    return dict(packet)


def classify_data_disposition(kind: str) -> str:
    if kind in DURABLE_EXACT_KINDS:
        return "STORE_DURABLY"
    if kind in SIMULATED_EPHEMERAL_KINDS:
        return "SIMULATE_EPHEMERALLY"
    if kind in MIXED_PROPOSAL_KINDS:
        return "PROPOSE_THEN_ADMIT_EXTERNALLY"
    return "UNKNOWN_FAIL_CLOSED"


def semantic_identity_material_from_request(packet: Mapping[str, Any]) -> SemanticProcessIdentityMaterial:
    validate_process_request(packet)
    parent = packet.get("parent_process_instance_id")
    if parent is not None and (not isinstance(parent, str) or not parent):
        raise CognitiveABIError("PARENT_PROCESS_INSTANCE_ID_INVALID")
    return SemanticProcessIdentityMaterial(
        causal_event_id=packet["causal_event_id"],
        admission_id=packet["admission_id"],
        generation=packet["generation"],
        process_id=packet["process_id"],
        step_index=packet["step_index"],
        parent_process_instance_id=parent,
    )
