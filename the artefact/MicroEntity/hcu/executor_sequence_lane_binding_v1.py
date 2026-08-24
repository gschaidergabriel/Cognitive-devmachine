#!/usr/bin/env python3
"""Deterministic executor-sequence lane binding for EntityOS/HCU.

This primitive closes one narrow provenance gap needed before recurrent J-Space control can
claim executor-owned t->t+1 adjacency. Typed Entry already admits ``stream_id`` as part of
the immutable event identity, while GRID10 and model-input control bind the exact event,
admission, route, plan, cell and executor invocation. This module composes those existing
facts into one stable lane identity without changing GRID10/v2 and without inventing a
caller-supplied time/step ordinal.

It deliberately does NOT assign sequence positions, prove predecessor/successor ordering,
execute a model, mint truth/effects, or grant runtime/model/training credit. A later
pre-invocation canonical store may use ``sequence_lane_sha256`` as a lane key and must
atomically assign/admit adjacency at the actual executor boundary. If an admitted Entry has
no deterministic ``stream_id``, this module fails closed instead of deriving a lane from a
timestamp, trace label or invocation spelling.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .grid10_scheduler_v1 import (
        ExecutionClass,
        GridPlan,
        GridScheduleError,
        validate_grid_plan_identity,
    )
    from .model_input_control_binding_v1 import (
        ModelInputControlBinding,
        ModelInputControlBindingError,
        validate_model_input_control_binding,
    )
    from .xeno_entry_fabric_v1 import EntryFabricError, EntryPacket, admit_entry
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from grid10_scheduler_v1 import ExecutionClass, GridPlan, GridScheduleError, validate_grid_plan_identity
    from model_input_control_binding_v1 import (
        ModelInputControlBinding,
        ModelInputControlBindingError,
        validate_model_input_control_binding,
    )
    from xeno_entry_fabric_v1 import EntryFabricError, EntryPacket, admit_entry

LANE_IDENTITY_SCHEMA = "HCU_EXECUTOR_SEQUENCE_LANE_IDENTITY/v1"
BINDING_SCHEMA = "HCU_EXECUTOR_SEQUENCE_LANE_BINDING/v1"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class ExecutorSequenceLaneBindingError(ValueError):
    pass


@dataclass(frozen=True)
class ExecutorSequenceLaneBinding:
    schema: str
    canonicalization_schema: str
    lane_identity_schema: str
    generation: int
    source_kind: str
    source_id: str
    stream_id: str
    executor_id: str
    engine_identity_sha256: str
    cell_id: str
    role: str
    sequence_lane_sha256: str
    entry_event_sha256: str
    entry_admission_sha256: str
    route_decision_sha256: str
    grid_plan_sha256: str
    model_input_control_binding_sha256: str
    vector_control_packet_sha256: str
    invocation_id: str
    input_sha256: str
    input_size: int
    binding_sha256: str


def _text(value: Any, field: str, max_len: int = 8192) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExecutorSequenceLaneBindingError(f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
    if value != normalized:
        raise ExecutorSequenceLaneBindingError(f"{field}:NONCANONICAL_TEXT")
    if len(normalized) > max_len:
        raise ExecutorSequenceLaneBindingError(f"{field}:TOO_LONG")
    return normalized


def _sha256(value: Any, field: str) -> str:
    normalized = _text(value, field, 64)
    if (
        len(normalized) != 64
        or normalized.lower() != normalized
        or any(ch not in "0123456789abcdef" for ch in normalized)
    ):
        raise ExecutorSequenceLaneBindingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if normalized in {"0" * 64, "f" * 64}:
        raise ExecutorSequenceLaneBindingError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return normalized


def _generation(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ExecutorSequenceLaneBindingError("generation:NONNEGATIVE_INTEGER_REQUIRED")
    if value > MAX_SAFE_INTEGER:
        raise ExecutorSequenceLaneBindingError("generation:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _input_size(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ExecutorSequenceLaneBindingError("input_size:POSITIVE_INTEGER_REQUIRED")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise ExecutorSequenceLaneBindingError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _material(binding: ExecutorSequenceLaneBinding) -> dict[str, Any]:
    data = asdict(binding)
    data.pop("binding_sha256", None)
    return data


def _revalidate_entry(packet: EntryPacket) -> None:
    """Rebuild exact typed-entry identities without treating packet claims as new authority."""
    if not isinstance(packet, EntryPacket):
        raise ExecutorSequenceLaneBindingError("ENTRY_PACKET_REQUIRED")
    try:
        rebuilt = admit_entry(
            {
                "schema": packet.schema,
                "ingress_id": packet.ingress_id,
                "causal_id": packet.causal_id,
                "entity_generation": packet.entity_generation,
                "source_kind": packet.source_kind,
                "source_id": packet.source_id,
                "modality": packet.modality,
                "observed_time": packet.observed_time,
                "received_time": packet.received_time,
                "provenance_ref": packet.provenance_ref,
                "provenance_sha256": packet.provenance_sha256,
                "capabilities": list(packet.capabilities),
                "capability_binding_sha256": packet.capability_binding_sha256,
                "parent_id": packet.parent_id,
                "stream_id": packet.stream_id,
                "budget": dict(packet.budget),
                "payload_ref": packet.payload_ref,
                "payload_sha256": packet.payload_sha256,
            },
            current_generation=packet.entity_generation,
            expected_capability_binding_sha256=packet.capability_binding_sha256,
            admitted_capabilities=packet.capabilities,
            admitted_budget=dict(packet.budget),
        )
    except (EntryFabricError, TypeError, ValueError) as exc:
        raise ExecutorSequenceLaneBindingError(f"ENTRY_PACKET_REVALIDATION_FAILED:{exc}") from exc
    if rebuilt != packet:
        raise ExecutorSequenceLaneBindingError("ENTRY_PACKET_IDENTITY_MISMATCH")


def _validate_sources(
    packet: EntryPacket,
    grid_plan: GridPlan,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
) -> str:
    _revalidate_entry(packet)
    if packet.stream_id is None:
        raise ExecutorSequenceLaneBindingError("EXECUTOR_SEQUENCE_STREAM_ID_REQUIRED")
    stream_id = _text(packet.stream_id, "stream_id", 512)

    try:
        validate_grid_plan_identity(grid_plan)
    except GridScheduleError as exc:
        raise ExecutorSequenceLaneBindingError(f"GRID_PLAN_REJECTED:{exc}") from exc
    try:
        validate_model_input_control_binding(input_binding, consumed_input_bytes)
    except ModelInputControlBindingError as exc:
        raise ExecutorSequenceLaneBindingError(f"MODEL_INPUT_CONTROL_BINDING_REJECTED:{exc}") from exc

    generation = _generation(packet.entity_generation)
    if grid_plan.entity_generation != generation or input_binding.generation != generation:
        raise ExecutorSequenceLaneBindingError("EXECUTOR_SEQUENCE_GENERATION_MISMATCH")

    for left, right, code in (
        (packet.ingress_id, grid_plan.ingress_id, "ENTRY_GRID_INGRESS_MISMATCH"),
        (packet.causal_id, grid_plan.causal_id, "ENTRY_GRID_CAUSAL_ID_MISMATCH"),
        (packet.event_sha256, grid_plan.entry_event_sha256, "ENTRY_GRID_EVENT_IDENTITY_MISMATCH"),
        (packet.admission_sha256, grid_plan.entry_admission_sha256, "ENTRY_GRID_ADMISSION_IDENTITY_MISMATCH"),
        (input_binding.entry_event_sha256, grid_plan.entry_event_sha256, "INPUT_GRID_EVENT_IDENTITY_MISMATCH"),
        (input_binding.entry_admission_sha256, grid_plan.entry_admission_sha256, "INPUT_GRID_ADMISSION_IDENTITY_MISMATCH"),
        (input_binding.route_decision_sha256, grid_plan.route_decision_sha256, "INPUT_GRID_ROUTE_IDENTITY_MISMATCH"),
        (input_binding.grid_plan_sha256, grid_plan.plan_sha256, "INPUT_GRID_PLAN_IDENTITY_MISMATCH"),
    ):
        if left != right:
            raise ExecutorSequenceLaneBindingError(code)

    matching = [cell for cell in grid_plan.cells if cell.cell_id == input_binding.cell_id]
    if len(matching) != 1:
        raise ExecutorSequenceLaneBindingError("EXECUTOR_SEQUENCE_GRID_CELL_NOT_UNIQUE")
    cell = matching[0]
    if cell.execution_class is not ExecutionClass.MODEL:
        raise ExecutorSequenceLaneBindingError("EXECUTOR_SEQUENCE_GRID_CELL_NOT_MODEL")
    if cell.function != f"MODEL:{input_binding.role}":
        raise ExecutorSequenceLaneBindingError("EXECUTOR_SEQUENCE_GRID_CELL_ROLE_MISMATCH")

    return stream_id


def _lane_material(
    *,
    generation: int,
    source_kind: str,
    source_id: str,
    stream_id: str,
    executor_id: str,
    engine_identity_sha256: str,
    cell_id: str,
    role: str,
) -> dict[str, Any]:
    return {
        "schema": LANE_IDENTITY_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "generation": _generation(generation),
        "source_kind": _text(source_kind, "source_kind", 128),
        "source_id": _text(source_id, "source_id", 512),
        "stream_id": _text(stream_id, "stream_id", 512),
        "executor_id": _text(executor_id, "executor_id", 256),
        "engine_identity_sha256": _sha256(engine_identity_sha256, "engine_identity_sha256"),
        "cell_id": _text(cell_id, "cell_id", 256),
        "role": _text(role, "role", 256),
    }


def bind_executor_sequence_lane(
    packet: EntryPacket,
    grid_plan: GridPlan,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
) -> ExecutorSequenceLaneBinding:
    """Bind one exact pre-invocation control/input observation to a deterministic stream lane."""
    stream_id = _validate_sources(packet, grid_plan, input_binding, consumed_input_bytes)

    lane_material = _lane_material(
        generation=packet.entity_generation,
        source_kind=packet.source_kind,
        source_id=packet.source_id,
        stream_id=stream_id,
        executor_id=input_binding.executor_id,
        engine_identity_sha256=grid_plan.engine_identity_sha256,
        cell_id=input_binding.cell_id,
        role=input_binding.role,
    )
    lane_sha256 = _canonical_sha256(lane_material, "EXECUTOR_SEQUENCE_LANE_IDENTITY")

    material = {
        "schema": BINDING_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "lane_identity_schema": LANE_IDENTITY_SCHEMA,
        "generation": _generation(packet.entity_generation),
        "source_kind": _text(packet.source_kind, "source_kind", 128),
        "source_id": _text(packet.source_id, "source_id", 512),
        "stream_id": stream_id,
        "executor_id": _text(input_binding.executor_id, "executor_id", 256),
        "engine_identity_sha256": _sha256(grid_plan.engine_identity_sha256, "engine_identity_sha256"),
        "cell_id": _text(input_binding.cell_id, "cell_id", 256),
        "role": _text(input_binding.role, "role", 256),
        "sequence_lane_sha256": lane_sha256,
        "entry_event_sha256": _sha256(packet.event_sha256, "entry_event_sha256"),
        "entry_admission_sha256": _sha256(packet.admission_sha256, "entry_admission_sha256"),
        "route_decision_sha256": _sha256(grid_plan.route_decision_sha256, "route_decision_sha256"),
        "grid_plan_sha256": _sha256(grid_plan.plan_sha256, "grid_plan_sha256"),
        "model_input_control_binding_sha256": _sha256(
            input_binding.binding_sha256,
            "model_input_control_binding_sha256",
        ),
        "vector_control_packet_sha256": _sha256(
            input_binding.vector_control_packet_sha256,
            "vector_control_packet_sha256",
        ),
        "invocation_id": _text(input_binding.invocation_id, "invocation_id", 256),
        "input_sha256": _sha256(input_binding.input_sha256, "input_sha256"),
        "input_size": _input_size(input_binding.input_size),
    }
    provisional = ExecutorSequenceLaneBinding(**material, binding_sha256="1" * 64)
    return ExecutorSequenceLaneBinding(
        **material,
        binding_sha256=_canonical_sha256(_material(provisional), "EXECUTOR_SEQUENCE_LANE_BINDING"),
    )


def validate_executor_sequence_lane_binding(
    binding: ExecutorSequenceLaneBinding,
    packet: EntryPacket,
    grid_plan: GridPlan,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
) -> None:
    """Revalidate a stored lane binding against all exact source objects and input bytes."""
    if not isinstance(binding, ExecutorSequenceLaneBinding):
        raise ExecutorSequenceLaneBindingError("EXECUTOR_SEQUENCE_LANE_BINDING_REQUIRED")
    if binding.schema != BINDING_SCHEMA:
        raise ExecutorSequenceLaneBindingError("EXECUTOR_SEQUENCE_LANE_BINDING_SCHEMA_UNSUPPORTED")
    if binding.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise ExecutorSequenceLaneBindingError("EXECUTOR_SEQUENCE_LANE_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    if binding.lane_identity_schema != LANE_IDENTITY_SCHEMA:
        raise ExecutorSequenceLaneBindingError("EXECUTOR_SEQUENCE_LANE_IDENTITY_SCHEMA_UNSUPPORTED")

    observed = _sha256(binding.binding_sha256, "binding_sha256")
    expected = _canonical_sha256(_material(binding), "EXECUTOR_SEQUENCE_LANE_BINDING")
    if observed != expected:
        raise ExecutorSequenceLaneBindingError("EXECUTOR_SEQUENCE_LANE_BINDING_DIGEST_MISMATCH")

    expected_binding = bind_executor_sequence_lane(
        packet,
        grid_plan,
        input_binding,
        consumed_input_bytes,
    )
    if binding != expected_binding:
        raise ExecutorSequenceLaneBindingError("EXECUTOR_SEQUENCE_LANE_SOURCE_REVALIDATION_MISMATCH")


def binding_dict(
    binding: ExecutorSequenceLaneBinding,
    packet: EntryPacket,
    grid_plan: GridPlan,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
) -> dict[str, Any]:
    validate_executor_sequence_lane_binding(
        binding,
        packet,
        grid_plan,
        input_binding,
        consumed_input_bytes,
    )
    data = _material(binding)
    data["binding_sha256"] = binding.binding_sha256
    return data
