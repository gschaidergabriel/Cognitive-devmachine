from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping

from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize

try:
    from .jspace_vector_control_v1 import (
        JSpaceVectorControlError,
        VectorControlPacket,
        validate_packet,
    )
except ImportError:
    from jspace_vector_control_v1 import (
        JSpaceVectorControlError,
        VectorControlPacket,
        validate_packet,
    )

try:
    from .outcome_receipt_content_key_v1 import (
        OutcomeReceiptContentKeyError,
        verify_outcome_receipt_content_key,
    )
except ImportError:
    from outcome_receipt_content_key_v1 import (
        OutcomeReceiptContentKeyError,
        verify_outcome_receipt_content_key,
    )

ADMISSION_SCHEMA = "ENTITYOS_HCU_JSPACE_DATASET_ADMISSION/v2"
PROTOTYPE_SCHEMA = "ENTITYOS_HCU_GLOBAL_JSPACE_GWT_TRACE/v3"
TRANSITION_SCHEMA = "JSPACE_GWT_TRANSITION_TRACE/v1"
TRAINING_SCHEMA = "ENTITYOS_HCU_JSPACE_TRAINING_TRACE/v1"
GRID_PLAN_SCHEMA = "ENTITYOS_HCU_GRID_PLAN/v2"
VECTOR_ABI = "JSPACE_VECTOR_CONTROL_ABI/v1"
CREDIT_LABELS = frozenset({"UNKNOWN", "POSITIVE", "NEGATIVE", "NEUTRAL"})


class JSpaceDatasetAdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class DatasetAdmission:
    schema: str
    training_trace_sha256: str
    transition_trace_sha256: str
    prototype_trace_sha256: str
    generation: int
    entry_event_sha256: str
    entry_admission_sha256: str
    route_decision_sha256: str
    grid_plan_sha256: str
    cell_id: str
    role: str
    jspace_basis_id: str
    jspace_basis_sha256: str
    vector_control_packet_sha256: str
    vector_control_condition: str
    credit_label: str
    outcome_receipt_sha256: str | None


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise JSpaceDatasetAdmissionError(f"{field}:MAPPING_REQUIRED")
    return value


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceDatasetAdmissionError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceDatasetAdmissionError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise JSpaceDatasetAdmissionError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _sha256_ref(value: Any, field: str) -> str:
    value = _text(value, field)
    prefix = "sha256:"
    if not value.startswith(prefix):
        raise JSpaceDatasetAdmissionError(f"{field}:SHA256_REF_REQUIRED")
    return _sha256(value[len(prefix):], field)


def _generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceDatasetAdmissionError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise JSpaceDatasetAdmissionError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _registry_exact(registry: Any, sha: str, observed: Mapping[str, Any], field: str) -> None:
    registry = _mapping(registry, field)
    admitted = registry.get(sha)
    if not isinstance(admitted, Mapping):
        raise JSpaceDatasetAdmissionError(f"{field}:TRACE_NOT_ADMITTED")
    if dict(admitted) != dict(observed):
        raise JSpaceDatasetAdmissionError(f"{field}:TRACE_REGISTRY_MISMATCH")


def _canonical_mapping_sha256(value: Any, field: str) -> str:
    """Return the RFC8785/JCS identity of an admitted mapping without inventing a second serializer."""
    value = _mapping(value, field)
    try:
        canonical = canonicalize(dict(value))
    except (CanonicalizationError, TypeError, ValueError) as exc:
        raise JSpaceDatasetAdmissionError(f"{field}:CANONICALIZATION_FAILED") from exc
    return hashlib.sha256(canonical).hexdigest()


def _verify_prototype_trace_identity(trace: Any, claimed_sha256: str) -> None:
    """Bind the prototype registry content key to the exact canonical prototype bytes.

    A registry lookup by a string named ``prototype_trace_sha256`` is not cryptographic
    provenance unless the key is re-derived from the admitted trace preimage. This check is
    deliberately local to the existing dataset-admission authority; it creates no second
    trace store or serializer authority.
    """
    observed = _canonical_mapping_sha256(trace, "admitted_prototype_trace")
    if observed != claimed_sha256:
        raise JSpaceDatasetAdmissionError("PROTOTYPE_TRACE_IDENTITY_MISMATCH")


def _canonical_transition_sha256(trace: Any) -> str:
    """Recreate the transition producer's exact RFC8785/JCS trace material identity.

    ``JSpaceGWTTransitionTrace.trace_sha256`` is defined over ``trace_material(trace)``:
    the trace digest itself is excluded and the selected HCU canonicalization schema is
    inserted. DatasetAdmission receives plain mappings rather than the producer dataclass,
    so it must reproduce that same material rule before treating a registry key as causal
    provenance.
    """
    material = dict(_mapping(trace, "admitted_transition_trace"))
    material.pop("trace_sha256", None)
    declared_schema = material.get("canonicalization_schema")
    if declared_schema is not None and declared_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceDatasetAdmissionError("TRANSITION_TRACE_CANONICALIZATION_SCHEMA_MISMATCH")
    material["canonicalization_schema"] = CANONICALIZATION_SCHEMA
    return _canonical_mapping_sha256(material, "admitted_transition_trace.material")


def _verify_transition_trace_identity(trace: Any, claimed_sha256: str) -> None:
    if _canonical_transition_sha256(trace) != claimed_sha256:
        raise JSpaceDatasetAdmissionError("TRANSITION_TRACE_IDENTITY_MISMATCH")


def _verify_outcome_receipt_identity(
    receipt: Any,
    claimed_sha256: str,
    *,
    expected_training_trace_sha256: str,
) -> None:
    """Verify the acyclic outcome content key plus its late training-trace back-reference.

    The training trace stores a content key that excludes exactly the late
    ``training_trace_sha256`` field. The final admitted receipt must still bind the exact
    training digest here. This removes the impossible full-receipt/training hash cycle without
    weakening the existing causal checks or creating a second dataset authority.
    """
    receipt = _mapping(receipt, "admitted_outcome_receipt")
    try:
        verify_outcome_receipt_content_key(
            receipt,
            claimed_sha256,
            expected_training_trace_sha256=expected_training_trace_sha256,
        )
    except OutcomeReceiptContentKeyError as exc:
        code = str(exc)
        if code == "OUTCOME_TRAINING_TRACE_MISMATCH":
            raise JSpaceDatasetAdmissionError(code) from exc
        raise JSpaceDatasetAdmissionError("OUTCOME_RECEIPT_IDENTITY_MISMATCH") from exc


def _same(values: Mapping[str, Any], field: str) -> Any:
    unique = []
    for label, value in values.items():
        if not unique:
            unique.append(value)
        elif value != unique[0]:
            raise JSpaceDatasetAdmissionError(f"{field}:MISMATCH:{label}")
    return unique[0] if unique else None


def _verify_grid_plan_binding(
    admitted_grid_plans: Any,
    *,
    grid_plan_sha256: str,
    generation: int,
    causal: Mapping[str, str],
) -> None:
    """Require GRID10 identity to come from external admitted plan evidence."""
    registry = _mapping(admitted_grid_plans, "admitted_grid_plans")
    plan = registry.get(grid_plan_sha256)
    if not isinstance(plan, Mapping):
        raise JSpaceDatasetAdmissionError("GRID_PLAN_NOT_ADMITTED")
    required = {
        "schema",
        "plan_sha256",
        "entity_generation",
        "entry_event_sha256",
        "entry_admission_sha256",
        "route_decision_sha256",
    }
    if set(plan) != required:
        raise JSpaceDatasetAdmissionError("GRID_PLAN_RECEIPT_SCHEMA_MISMATCH")
    if plan.get("schema") != GRID_PLAN_SCHEMA:
        raise JSpaceDatasetAdmissionError("GRID_PLAN_SCHEMA_UNSUPPORTED")
    if _sha256(plan.get("plan_sha256"), "admitted_grid_plan.plan_sha256") != grid_plan_sha256:
        raise JSpaceDatasetAdmissionError("GRID_PLAN_IDENTITY_MISMATCH")
    if _generation(plan.get("entity_generation"), "admitted_grid_plan.entity_generation") != generation:
        raise JSpaceDatasetAdmissionError("GRID_PLAN_GENERATION_MISMATCH")
    for field in ("entry_event_sha256", "entry_admission_sha256", "route_decision_sha256"):
        if _sha256(plan.get(field), f"admitted_grid_plan.{field}") != causal[field]:
            raise JSpaceDatasetAdmissionError(f"GRID_PLAN_CAUSAL_BINDING_MISMATCH:{field}")


def _verify_vector_control_packet_binding(
    admitted_vector_control_packets: Any,
    *,
    packet_sha256: str,
    generation: int,
    basis_id: str,
    basis_sha256: str,
    role: str,
    control_condition: str,
) -> None:
    """Require an independently admitted canonical Vector-Control packet preimage.

    Cross-trace digest equality proves only that several layers repeat the same digest. It
    cannot prove that the digest identifies a real, canonical, semantically valid
    ``JSPACE_VECTOR_CONTROL_ABI/v1`` packet. The caller-owned registry supplies that missing
    preimage without creating a second vector or dataset authority.
    """
    registry = _mapping(admitted_vector_control_packets, "admitted_vector_control_packets")
    packet = registry.get(packet_sha256)
    if packet is None:
        raise JSpaceDatasetAdmissionError("VECTOR_CONTROL_PACKET_NOT_ADMITTED")
    if not isinstance(packet, VectorControlPacket):
        raise JSpaceDatasetAdmissionError("VECTOR_CONTROL_PACKET_PREIMAGE_TYPE_INVALID")
    observed_packet_sha = _sha256(packet.packet_sha256, "admitted_vector_control_packet.packet_sha256")
    if observed_packet_sha != packet_sha256:
        raise JSpaceDatasetAdmissionError("VECTOR_CONTROL_PACKET_IDENTITY_MISMATCH")
    try:
        validate_packet(packet)
    except JSpaceVectorControlError as exc:
        raise JSpaceDatasetAdmissionError(f"VECTOR_CONTROL_PACKET_REJECTED:{exc}") from exc
    if packet.generation != generation:
        raise JSpaceDatasetAdmissionError("VECTOR_CONTROL_PACKET_GENERATION_MISMATCH")
    if packet.basis_id != basis_id:
        raise JSpaceDatasetAdmissionError("VECTOR_CONTROL_PACKET_BASIS_ID_MISMATCH")
    if packet.basis_sha256 != basis_sha256:
        raise JSpaceDatasetAdmissionError("VECTOR_CONTROL_PACKET_BASIS_SHA256_MISMATCH")
    if packet.role != role:
        raise JSpaceDatasetAdmissionError("VECTOR_CONTROL_PACKET_ROLE_MISMATCH")
    if packet.control_condition != control_condition:
        raise JSpaceDatasetAdmissionError("VECTOR_CONTROL_PACKET_CONDITION_MISMATCH")


def _verify_outcome_binding(
    receipt: Any,
    *,
    training_sha: str,
    transition_sha: str,
    generation: int,
    causal: Mapping[str, str],
    cell_id: str,
    role: str,
    credit: str,
) -> None:
    """Require any admitted outcome reference to bind the exact causal training family.

    UNKNOWN keeps credit epistemically unknown; it does not permit an unrelated admitted
    receipt to become false provenance for this training row.
    """
    receipt = _mapping(receipt, "admitted_outcome_receipt")
    if _text(receipt.get("status"), "admitted_outcome_receipt.status").upper() != "VERIFIED":
        raise JSpaceDatasetAdmissionError("OUTCOME_RECEIPT_NOT_VERIFIED")
    if _text(receipt.get("credit_label"), "admitted_outcome_receipt.credit_label").upper() != credit:
        raise JSpaceDatasetAdmissionError("OUTCOME_CREDIT_LABEL_MISMATCH")
    if _sha256(receipt.get("training_trace_sha256"), "admitted_outcome_receipt.training_trace_sha256") != training_sha:
        raise JSpaceDatasetAdmissionError("OUTCOME_TRAINING_TRACE_MISMATCH")
    if _sha256(receipt.get("transition_trace_sha256"), "admitted_outcome_receipt.transition_trace_sha256") != transition_sha:
        raise JSpaceDatasetAdmissionError("OUTCOME_TRANSITION_TRACE_MISMATCH")
    if _generation(receipt.get("generation"), "admitted_outcome_receipt.generation") != generation:
        raise JSpaceDatasetAdmissionError("OUTCOME_GENERATION_MISMATCH")
    for field in (
        "entry_event_sha256",
        "entry_admission_sha256",
        "route_decision_sha256",
        "grid_plan_sha256",
    ):
        if _sha256(receipt.get(field), f"admitted_outcome_receipt.{field}") != causal[field]:
            raise JSpaceDatasetAdmissionError(f"OUTCOME_CAUSAL_BINDING_MISMATCH:{field}")
    if _text(receipt.get("cell_id"), "admitted_outcome_receipt.cell_id") != cell_id:
        raise JSpaceDatasetAdmissionError("OUTCOME_CELL_MISMATCH")
    if _text(receipt.get("role"), "admitted_outcome_receipt.role") != role:
        raise JSpaceDatasetAdmissionError("OUTCOME_ROLE_MISMATCH")


def admit_for_training_dataset(
    training_trace: Mapping[str, Any],
    transition_trace: Mapping[str, Any],
    *,
    admitted_training_traces: Mapping[str, Mapping[str, Any]],
    admitted_transition_traces: Mapping[str, Mapping[str, Any]],
    admitted_prototype_traces: Mapping[str, Mapping[str, Any]],
    admitted_grid_plans: Mapping[str, Mapping[str, Any]],
    admitted_vector_control_packets: Mapping[str, VectorControlPacket],
    admitted_outcome_receipts: Mapping[str, Any] | None = None,
) -> DatasetAdmission:
    """Fail-closed admission for one-shot-training dataset material.

    This gate does not mint truth. It proves that admitted training, live-transition,
    prototype and GRID10 evidence refer to the same generation/cell/role/basis, exact Vector
    Control packet/control condition, and Entry->Route->GRID10 identities. The transition
    and prototype ancestry keys must additionally resolve to the exact RFC8785/JCS content
    identities they claim. The shared Vector Control digest must resolve through a caller-owned
    registry to an exact canonical packet preimage that passes the sole
    ``JSPACE_VECTOR_CONTROL_ABI/v1`` validator. Outcome identity uses the selected acyclic
    content key and separately revalidates the final training-trace back-reference. A raw
    standalone prototype, self-consistent row, digest-only vector label, shared but unadmitted
    GRID hash, content-false registry alias, or unbound outcome receipt is insufficient.
    """
    training_trace = _mapping(training_trace, "training_trace")
    transition_trace = _mapping(transition_trace, "transition_trace")

    if training_trace.get("schema_version") != TRAINING_SCHEMA:
        raise JSpaceDatasetAdmissionError("TRAINING_TRACE_SCHEMA_UNSUPPORTED")
    if transition_trace.get("schema_version") != TRANSITION_SCHEMA:
        raise JSpaceDatasetAdmissionError("TRANSITION_TRACE_SCHEMA_UNSUPPORTED")

    training_sha = _sha256(training_trace.get("trace_sha256"), "training_trace.trace_sha256")
    transition_sha = _sha256(transition_trace.get("trace_sha256"), "transition_trace.trace_sha256")
    prototype_sha = _sha256(training_trace.get("prototype_trace_sha256"), "training_trace.prototype_trace_sha256")

    _registry_exact(admitted_training_traces, training_sha, training_trace, "admitted_training_traces")
    _registry_exact(admitted_transition_traces, transition_sha, transition_trace, "admitted_transition_traces")
    _verify_transition_trace_identity(transition_trace, transition_sha)
    prototype_trace = _mapping(admitted_prototype_traces, "admitted_prototype_traces").get(prototype_sha)
    if not isinstance(prototype_trace, Mapping):
        raise JSpaceDatasetAdmissionError("admitted_prototype_traces:TRACE_NOT_ADMITTED")
    if prototype_trace.get("schema") != PROTOTYPE_SCHEMA:
        raise JSpaceDatasetAdmissionError("PROTOTYPE_TRACE_SCHEMA_UNSUPPORTED")
    _verify_prototype_trace_identity(prototype_trace, prototype_sha)

    generation = _same(
        {
            "transition": _generation(transition_trace.get("generation"), "transition_trace.generation"),
            "prototype": _generation(prototype_trace.get("generation"), "prototype_trace.generation"),
            "training": _generation(training_trace.get("generation"), "training_trace.generation"),
        },
        "GENERATION_BINDING",
    )
    cell_id = _same(
        {
            "transition": _text(transition_trace.get("cell_id"), "transition_trace.cell_id"),
            "prototype": _text(prototype_trace.get("winner_cell_id"), "prototype_trace.winner_cell_id"),
            "training": _text(training_trace.get("cell_id"), "training_trace.cell_id"),
        },
        "CELL_BINDING",
    )
    role = _same(
        {
            "transition": _text(transition_trace.get("role"), "transition_trace.role"),
            "prototype": _text(prototype_trace.get("winner_role"), "prototype_trace.winner_role"),
            "training": _text(training_trace.get("role"), "training_trace.role"),
        },
        "ROLE_BINDING",
    )
    basis_id = _same(
        {
            "transition": _text(transition_trace.get("jspace_basis_id"), "transition_trace.jspace_basis_id"),
            "prototype": _text(prototype_trace.get("basis_id"), "prototype_trace.basis_id"),
            "training": _text(training_trace.get("jspace_basis_id"), "training_trace.jspace_basis_id"),
        },
        "BASIS_ID_BINDING",
    )
    basis_sha = _same(
        {
            "transition": _sha256(transition_trace.get("jspace_basis_sha256"), "transition_trace.jspace_basis_sha256"),
            "prototype": _sha256(prototype_trace.get("basis_sha256"), "prototype_trace.basis_sha256"),
            "training": _sha256(training_trace.get("jspace_basis_sha256"), "training_trace.jspace_basis_sha256"),
        },
        "BASIS_SHA256_BINDING",
    )
    vector_control_packet_sha = _same(
        {
            "transition": _sha256_ref(transition_trace.get("jspace_input_vector_ref"), "transition_trace.jspace_input_vector_ref"),
            "prototype": _sha256(prototype_trace.get("control_packet_identity_sha256"), "prototype_trace.control_packet_identity_sha256"),
            "training": _sha256(training_trace.get("vector_control_packet_sha256"), "training_trace.vector_control_packet_sha256"),
        },
        "VECTOR_CONTROL_PACKET_BINDING",
    )
    vector_control_condition = _same(
        {
            "transition": _text(transition_trace.get("falsifier_lesion_condition"), "transition_trace.falsifier_lesion_condition"),
            "prototype": _text(prototype_trace.get("control_condition"), "prototype_trace.control_condition"),
            "training": _text(training_trace.get("vector_control_condition"), "training_trace.vector_control_condition"),
        },
        "VECTOR_CONTROL_CONDITION_BINDING",
    )

    causal: dict[str, str] = {}
    for field in (
        "entry_event_sha256",
        "entry_admission_sha256",
        "route_decision_sha256",
        "grid_plan_sha256",
    ):
        causal[field] = _same(
            {
                "transition": _sha256(transition_trace.get(field), f"transition_trace.{field}"),
                "training": _sha256(training_trace.get(field), f"training_trace.{field}"),
            },
            f"CAUSAL_BINDING:{field}",
        )

    _verify_grid_plan_binding(
        admitted_grid_plans,
        grid_plan_sha256=causal["grid_plan_sha256"],
        generation=generation,
        causal=causal,
    )

    if _text(training_trace.get("jspace_input_codec_version"), "training_trace.jspace_input_codec_version") != VECTOR_ABI:
        raise JSpaceDatasetAdmissionError("TRAINING_VECTOR_ABI_UNSUPPORTED")
    if _text(transition_trace.get("jspace_vector_control_abi"), "transition_trace.jspace_vector_control_abi") != VECTOR_ABI:
        raise JSpaceDatasetAdmissionError("TRANSITION_VECTOR_ABI_UNSUPPORTED")

    _verify_vector_control_packet_binding(
        admitted_vector_control_packets,
        packet_sha256=vector_control_packet_sha,
        generation=generation,
        basis_id=basis_id,
        basis_sha256=basis_sha,
        role=role,
        control_condition=vector_control_condition,
    )

    credit = _same(
        {
            "transition": _text(transition_trace.get("credit_label"), "transition_trace.credit_label").upper(),
            "training": _text(training_trace.get("credit_label"), "training_trace.credit_label").upper(),
        },
        "CREDIT_LABEL_BINDING",
    )
    if credit not in CREDIT_LABELS:
        raise JSpaceDatasetAdmissionError("CREDIT_LABEL_UNSUPPORTED")
    outcome = training_trace.get("outcome_receipt_sha256")
    if outcome is not None:
        outcome = _sha256(outcome, "training_trace.outcome_receipt_sha256")
        outcome_registry = _mapping(admitted_outcome_receipts, "admitted_outcome_receipts")
        receipt = outcome_registry.get(outcome)
        if receipt is None:
            raise JSpaceDatasetAdmissionError("OUTCOME_RECEIPT_NOT_ADMITTED")
        _verify_outcome_receipt_identity(
            receipt,
            outcome,
            expected_training_trace_sha256=training_sha,
        )
        _verify_outcome_binding(
            receipt,
            training_sha=training_sha,
            transition_sha=transition_sha,
            generation=generation,
            causal=causal,
            cell_id=cell_id,
            role=role,
            credit=credit,
        )
    elif credit != "UNKNOWN":
        raise JSpaceDatasetAdmissionError("NONUNKNOWN_CREDIT_REQUIRES_ADMITTED_OUTCOME_RECEIPT")

    return DatasetAdmission(
        schema=ADMISSION_SCHEMA,
        training_trace_sha256=training_sha,
        transition_trace_sha256=transition_sha,
        prototype_trace_sha256=prototype_sha,
        generation=generation,
        entry_event_sha256=causal["entry_event_sha256"],
        entry_admission_sha256=causal["entry_admission_sha256"],
        route_decision_sha256=causal["route_decision_sha256"],
        grid_plan_sha256=causal["grid_plan_sha256"],
        cell_id=cell_id,
        role=role,
        jspace_basis_id=basis_id,
        jspace_basis_sha256=basis_sha,
        vector_control_packet_sha256=vector_control_packet_sha,
        vector_control_condition=vector_control_condition,
        credit_label=credit,
        outcome_receipt_sha256=outcome,
    )