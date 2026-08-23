#!/usr/bin/env python3
"""Observable training-trace envelope for the EntityOS/HCU J-Space/GWT prototype.

This module creates no private chain-of-thought and claims no model-hidden-state access.
It binds an observable Global-J-Space/GWT prototype step plus the versioned token/byte
Vector Control ABI to the causal EntityOS/HCU Entry -> route -> GRID10 path and records an
explicit downstream-outcome reference plus lesion/credit claim.

Important authority boundary: ``outcome_receipt_sha256`` is only a typed reference inside
this self-authenticating trace envelope. This module does NOT validate that referenced
outcome, does NOT admit reward, and does NOT make a row serious-training eligible. Exact
verified outcome ancestry is admitted later by ``jspace_dataset_admission_gate_v1`` while
real inference/load evidence remains separately bound by ``jspace_inference_binding_v1`` /
``compile_admitted_jspace_training_dataset_v1``. Keeping those phases separate avoids a
circular trace-hash dependency and prevents model inference receipts from becoming reward.

A trace is never durable truth, reward by model self-approval, or EffectGate authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any, Mapping, Sequence

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .global_jspace_gwt_v1 import JSpaceStep, TRACE_CANONICALIZATION_SCHEMA
    from .jspace_vector_control_v1 import ABI_SCHEMA, VectorControlPacket, packet_bytes, validate_packet
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from global_jspace_gwt_v1 import JSpaceStep, TRACE_CANONICALIZATION_SCHEMA
    from jspace_vector_control_v1 import ABI_SCHEMA, VectorControlPacket, packet_bytes, validate_packet

TRACE_SCHEMA = "ENTITYOS_HCU_JSPACE_TRAINING_TRACE/v1"
CREDIT_LABELS = frozenset({"UNKNOWN", "POSITIVE", "NEGATIVE", "NEUTRAL"})
PROVENANCE_CLASSES = frozenset({
    "EXACT_PROTOTYPE_TRACE",
    "EXACT_PROTOTYPE_TRACE_WITH_VERIFIED_OUTCOME",
    "DETERMINISTIC_COUNTERFACTUAL_CONTROL",
})


class JSpaceTrainingTraceError(ValueError):
    pass


@dataclass(frozen=True)
class TrainingTrace:
    schema_version: str
    canonicalization_schema: str
    trace_id: str
    trace_family_id: str
    generation: int
    entry_event_sha256: str
    entry_admission_sha256: str
    route_decision_sha256: str
    grid_plan_sha256: str
    cell_id: str
    role: str
    jspace_basis_id: str
    jspace_basis_sha256: str
    jspace_input_vector_ref: str
    jspace_input_codec_version: str
    vector_control_packet_sha256: str
    vector_control_packet_jcs_utf8: str
    vector_control_condition: str
    local_workspace_state_ref: str
    gwt_competition_set: tuple[tuple[str, str, int], ...]
    gwt_broadcast_gate: int
    global_jspace_slice_ref: str
    hyperposition_branch_ids: tuple[str, ...]
    provenance_evidence_class: str
    resource_budget: tuple[tuple[str, int], ...]
    requested_action_class: str
    expected_structured_model_output: str
    observed_downstream_outcome: str
    outcome_receipt_sha256: str | None
    falsifier_lesion_condition: str
    credit_label: str
    prototype_trace_sha256: str
    trace_sha256: str


def _text(value: Any, field: str, max_len: int = 8192) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceTrainingTraceError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise JSpaceTrainingTraceError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, 64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceTrainingTraceError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise JSpaceTrainingTraceError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _generation(value: Any, field: str = "generation") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceTrainingTraceError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise JSpaceTrainingTraceError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _budget(value: Mapping[str, Any]) -> tuple[tuple[str, int], ...]:
    if not isinstance(value, Mapping) or not value:
        raise JSpaceTrainingTraceError("resource_budget:MAPPING_REQUIRED")
    out: list[tuple[str, int]] = []
    for key, amount in value.items():
        key = _text(key, "resource_budget.key", 128)
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            raise JSpaceTrainingTraceError(f"resource_budget.{key}:NONNEGATIVE_INTEGER_REQUIRED")
        out.append((key, amount))
    return tuple(sorted(out))


def _branches(values: Sequence[Any]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray)) or not isinstance(values, Sequence):
        raise JSpaceTrainingTraceError("hyperposition_branch_ids:SEQUENCE_REQUIRED")
    return tuple(sorted({_text(value, "hyperposition_branch_id", 256) for value in values}))


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        raw = canonicalize(value)
    except CanonicalizationError as exc:
        raise JSpaceTrainingTraceError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(raw).hexdigest()


def _competition(step: JSpaceStep) -> tuple[tuple[str, str, int], ...]:
    contributions = step.trace.get("contributions") if isinstance(step.trace, dict) else None
    if not isinstance(contributions, list) or not contributions:
        raise JSpaceTrainingTraceError("PROTOTYPE_COMPETITION_TRACE_REQUIRED")
    out: list[tuple[str, str, int]] = []
    seen: set[str] = set()
    for item in contributions:
        if not isinstance(item, Mapping):
            raise JSpaceTrainingTraceError("PROTOTYPE_COMPETITION_ITEM_INVALID")
        cell_id = _text(item.get("cell_id"), "competition.cell_id", 256)
        role = _text(item.get("role"), "competition.role", 256)
        gate = item.get("gate_q")
        if isinstance(gate, bool) or not isinstance(gate, int) or not 0 <= gate <= 10000:
            raise JSpaceTrainingTraceError("competition.gate_q:OUT_OF_RANGE")
        if cell_id in seen:
            raise JSpaceTrainingTraceError("PROTOTYPE_COMPETITION_DUPLICATE_CELL")
        seen.add(cell_id)
        out.append((cell_id, role, gate))
    return tuple(sorted(out))


def _material(trace: TrainingTrace) -> dict[str, Any]:
    data = asdict(trace)
    data.pop("trace_sha256", None)
    data["gwt_competition_set"] = [
        {"cell_id": cell_id, "role": role, "gate_q": gate_q}
        for cell_id, role, gate_q in trace.gwt_competition_set
    ]
    data["hyperposition_branch_ids"] = list(trace.hyperposition_branch_ids)
    data["resource_budget"] = {key: value for key, value in trace.resource_budget}
    return data


def build_training_trace(
    prototype_step: JSpaceStep,
    vector_control_packet: VectorControlPacket,
    *,
    trace_id: str,
    trace_family_id: str,
    entry_event_sha256: str,
    entry_admission_sha256: str,
    route_decision_sha256: str,
    grid_plan_sha256: str,
    jspace_input_vector_ref: str,
    local_workspace_state_ref: str,
    global_jspace_slice_ref: str,
    hyperposition_branch_ids: Sequence[str],
    provenance_evidence_class: str,
    resource_budget: Mapping[str, int],
    requested_action_class: str,
    expected_structured_model_output: str,
    observed_downstream_outcome: str,
    falsifier_lesion_condition: str,
    credit_label: str = "UNKNOWN",
    outcome_receipt_sha256: str | None = None,
) -> TrainingTrace:
    """Bind one observable prototype transition to a self-authenticating trace envelope.

    A non-UNKNOWN credit label must carry an outcome receipt *reference* and the explicit
    verified-outcome provenance class. Those checks only make the claim structurally
    explicit; they do not verify the receipt or admit reward. Verification is deliberately
    deferred to the canonical dataset-admission gate, which can bind the completed trace's
    own SHA plus transition/prototype/outcome ancestry without circular hashing.

    The supplied Vector Control packet must be the exact packet produced by the supplied
    prototype step. Counterfactual controls therefore use a separately constructed prototype
    step rather than transplanting an unrelated packet into another trace family.
    """
    if not isinstance(prototype_step, JSpaceStep):
        raise JSpaceTrainingTraceError("JSPACE_STEP_REQUIRED")
    if TRACE_CANONICALIZATION_SCHEMA != CANONICALIZATION_SCHEMA:
        raise JSpaceTrainingTraceError("PROTOTYPE_CANONICALIZATION_AUTHORITY_MISMATCH")
    if prototype_step.trace.get("canonicalization_schema") != CANONICALIZATION_SCHEMA:
        raise JSpaceTrainingTraceError("PROTOTYPE_TRACE_CANONICALIZATION_MISMATCH")
    observed_prototype_sha = _sha256(prototype_step.trace_sha256, "prototype_trace_sha256")
    if _canonical_sha256(prototype_step.trace, "PROTOTYPE_TRACE") != observed_prototype_sha:
        raise JSpaceTrainingTraceError("PROTOTYPE_TRACE_DIGEST_MISMATCH")

    try:
        validate_packet(vector_control_packet)
        packet_wire = packet_bytes(vector_control_packet).decode("utf-8", "strict")
    except Exception as exc:
        raise JSpaceTrainingTraceError(f"VECTOR_CONTROL_PACKET_REJECTED:{exc}") from exc
    if vector_control_packet.abi_schema != ABI_SCHEMA:
        raise JSpaceTrainingTraceError("VECTOR_CONTROL_ABI_MISMATCH")
    if vector_control_packet.generation != prototype_step.generation:
        raise JSpaceTrainingTraceError("VECTOR_CONTROL_GENERATION_MISMATCH")
    if vector_control_packet.basis_id != prototype_step.basis_id:
        raise JSpaceTrainingTraceError("VECTOR_CONTROL_BASIS_MISMATCH")
    if vector_control_packet.basis_sha256 != prototype_step.basis_sha256:
        raise JSpaceTrainingTraceError("VECTOR_CONTROL_BASIS_SHA256_MISMATCH")
    if vector_control_packet.role != prototype_step.winner_role:
        raise JSpaceTrainingTraceError("VECTOR_CONTROL_ROLE_MISMATCH")
    if vector_control_packet.control_condition != prototype_step.control_condition:
        raise JSpaceTrainingTraceError("VECTOR_CONTROL_CONDITION_MISMATCH")
    if vector_control_packet.packet_sha256 != prototype_step.control_packet.packet_sha256:
        raise JSpaceTrainingTraceError("VECTOR_CONTROL_PACKET_TRANSPLANT")
    if packet_wire != prototype_step.control_packet_text:
        raise JSpaceTrainingTraceError("VECTOR_CONTROL_PACKET_WIRE_MISMATCH")

    credit = _text(credit_label, "credit_label", 32).upper()
    if credit not in CREDIT_LABELS:
        raise JSpaceTrainingTraceError("credit_label:UNSUPPORTED")
    outcome_receipt = outcome_receipt_sha256
    if credit != "UNKNOWN":
        if outcome_receipt is None:
            raise JSpaceTrainingTraceError("NONUNKNOWN_CREDIT_REQUIRES_OUTCOME_RECEIPT_REFERENCE")
        outcome_receipt = _sha256(outcome_receipt, "outcome_receipt_sha256")
    elif outcome_receipt is not None:
        outcome_receipt = _sha256(outcome_receipt, "outcome_receipt_sha256")

    provenance = _text(provenance_evidence_class, "provenance_evidence_class", 128).upper()
    if provenance not in PROVENANCE_CLASSES:
        raise JSpaceTrainingTraceError("provenance_evidence_class:UNSUPPORTED")
    if credit != "UNKNOWN" and provenance != "EXACT_PROTOTYPE_TRACE_WITH_VERIFIED_OUTCOME":
        raise JSpaceTrainingTraceError("NONUNKNOWN_CREDIT_REQUIRES_VERIFIED_OUTCOME_PROVENANCE")

    material = {
        "schema_version": TRACE_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "trace_id": _text(trace_id, "trace_id", 256),
        "trace_family_id": _text(trace_family_id, "trace_family_id", 256),
        "generation": _generation(prototype_step.generation),
        "entry_event_sha256": _sha256(entry_event_sha256, "entry_event_sha256"),
        "entry_admission_sha256": _sha256(entry_admission_sha256, "entry_admission_sha256"),
        "route_decision_sha256": _sha256(route_decision_sha256, "route_decision_sha256"),
        "grid_plan_sha256": _sha256(grid_plan_sha256, "grid_plan_sha256"),
        "cell_id": _text(prototype_step.winner_cell_id, "cell_id", 256),
        "role": _text(prototype_step.winner_role, "role", 256),
        "jspace_basis_id": _text(prototype_step.basis_id, "jspace_basis_id", 256),
        "jspace_basis_sha256": _sha256(prototype_step.basis_sha256, "jspace_basis_sha256"),
        "jspace_input_vector_ref": _text(jspace_input_vector_ref, "jspace_input_vector_ref"),
        "jspace_input_codec_version": ABI_SCHEMA,
        "vector_control_packet_sha256": _sha256(vector_control_packet.packet_sha256, "vector_control_packet_sha256"),
        "vector_control_packet_jcs_utf8": packet_wire,
        "vector_control_condition": _text(vector_control_packet.control_condition, "vector_control_condition", 64),
        "local_workspace_state_ref": _text(local_workspace_state_ref, "local_workspace_state_ref"),
        "gwt_competition_set": _competition(prototype_step),
        "gwt_broadcast_gate": prototype_step.winner_gate_q,
        "global_jspace_slice_ref": _text(global_jspace_slice_ref, "global_jspace_slice_ref"),
        "hyperposition_branch_ids": _branches(hyperposition_branch_ids),
        "provenance_evidence_class": provenance,
        "resource_budget": _budget(resource_budget),
        "requested_action_class": _text(requested_action_class, "requested_action_class", 128),
        "expected_structured_model_output": _text(
            expected_structured_model_output,
            "expected_structured_model_output",
        ),
        "observed_downstream_outcome": _text(
            observed_downstream_outcome,
            "observed_downstream_outcome",
        ),
        "outcome_receipt_sha256": outcome_receipt,
        "falsifier_lesion_condition": _text(
            falsifier_lesion_condition,
            "falsifier_lesion_condition",
        ),
        "credit_label": credit,
        "prototype_trace_sha256": observed_prototype_sha,
    }
    trace_without_sha = TrainingTrace(**material, trace_sha256="1" * 64)
    trace_sha256 = _canonical_sha256(_material(trace_without_sha), "JSPACE_TRAINING_TRACE")
    return TrainingTrace(**material, trace_sha256=trace_sha256)


def validate_training_trace(trace: TrainingTrace) -> None:
    """Validate only the trace envelope's own schema/digest/reference invariants.

    This function deliberately does not validate or admit downstream outcome truth.
    """
    if not isinstance(trace, TrainingTrace):
        raise JSpaceTrainingTraceError("TRAINING_TRACE_REQUIRED")
    if trace.schema_version != TRACE_SCHEMA or trace.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceTrainingTraceError("TRAINING_TRACE_SCHEMA_UNSUPPORTED")
    observed = _sha256(trace.trace_sha256, "trace_sha256")
    expected = _canonical_sha256(_material(trace), "JSPACE_TRAINING_TRACE")
    if observed != expected:
        raise JSpaceTrainingTraceError("TRAINING_TRACE_DIGEST_MISMATCH")
    if trace.credit_label != "UNKNOWN" and trace.outcome_receipt_sha256 is None:
        raise JSpaceTrainingTraceError("NONUNKNOWN_CREDIT_REQUIRES_OUTCOME_RECEIPT_REFERENCE")


def trace_dict(trace: TrainingTrace) -> dict[str, Any]:
    validate_training_trace(trace)
    data = _material(trace)
    data["trace_sha256"] = trace.trace_sha256
    return data
