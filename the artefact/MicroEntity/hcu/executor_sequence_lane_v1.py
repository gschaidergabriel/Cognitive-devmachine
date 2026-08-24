#!/usr/bin/env python3
"""Derive executor-owned recurrent lane identity from deterministic admitted HCU context.

This is a source-level prerequisite for ``HCU_EXECUTOR_SEQUENCE_ADMISSION/v1``.  It does
not assign sequence positions or claim adjacency.  Instead it answers the narrower question
required by ``JSPACE_EXECUTOR_SEQUENCE_EVIDENCE_CONTRACT``: can two model invocations be
placed in the same recurrent executor lane without trusting caller step/timestamp labels?

The stable lane identity is derived only from fields already bound into Typed Entry event
identity plus executor/role context:

    entity generation + executor_id + source_kind + source_id + stream_id + model role

``stream_id`` is therefore not a fresh caller label at this boundary: the exact value must
already be inside the revalidated Entry event/admission identities that the scheduler-owned
GRID plan names.  If no admitted stream identity exists, derivation fails closed with
``EXECUTOR_SEQUENCE_LANE_IDENTITY_UNAVAILABLE``.

A per-invocation lane binding additionally cross-binds the exact Entry event/admission,
GRID plan and model cell.  The stable lane id can stay equal across adjacent Entry/GRID
steps while each binding retains exact step-specific provenance.

No new database, executor, truth/effect path, temporal ordering, model/J-Space runtime
credit or training credit is created here.
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
    from .xeno_entry_fabric_v1 import (
        ENTRY_ADMISSION_IDENTITY_SCHEMA,
        ENTRY_EVENT_IDENTITY_SCHEMA,
        ENTRY_SCHEMA,
        EntryPacket,
    )
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from grid10_scheduler_v1 import ExecutionClass, GridPlan, GridScheduleError, validate_grid_plan_identity
    from xeno_entry_fabric_v1 import (
        ENTRY_ADMISSION_IDENTITY_SCHEMA,
        ENTRY_EVENT_IDENTITY_SCHEMA,
        ENTRY_SCHEMA,
        EntryPacket,
    )

LANE_SCHEMA = "HCU_EXECUTOR_SEQUENCE_LANE_IDENTITY/v1"
BINDING_SCHEMA = "HCU_EXECUTOR_SEQUENCE_LANE_BINDING/v1"


class ExecutorSequenceLaneError(ValueError):
    pass


@dataclass(frozen=True)
class ExecutorSequenceLaneBinding:
    schema: str
    canonicalization_schema: str
    lane_schema: str
    generation: int
    executor_id: str
    source_kind: str
    source_id: str
    stream_id: str
    role: str
    sequence_lane_id: str
    ingress_id: str
    causal_id: str
    entry_parent_id: str | None
    entry_event_sha256: str
    entry_admission_sha256: str
    grid_plan_sha256: str
    cell_id: str
    binding_sha256: str


def _fail(message: str) -> None:
    raise ExecutorSequenceLaneError(message)


def _text(value: Any, field: str, max_len: int = 512) -> str:
    if not isinstance(value, str) or not value:
        _fail(f"{field}:NONEMPTY_STRING_REQUIRED")
    if value.strip() != value:
        _fail(f"{field}:NONCANONICAL_TEXT")
    if len(value) > max_len:
        _fail(f"{field}:TOO_LONG")
    return value


def _optional_text(value: Any, field: str, max_len: int = 512) -> str | None:
    if value is None:
        return None
    return _text(value, field, max_len)


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, 64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        _fail(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _generation(value: Any, field: str = "generation") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9_007_199_254_740_991:
        _fail(f"{field}:IJSON_SAFE_NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise ExecutorSequenceLaneError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _validated_capabilities(packet: EntryPacket) -> list[str]:
    capabilities = packet.capabilities
    if not isinstance(capabilities, tuple):
        _fail("ENTRY_CAPABILITIES_CANONICAL_TUPLE_REQUIRED")
    normalized = [_text(value, "entry.capability") for value in capabilities]
    if len(normalized) != len(set(normalized)) or normalized != sorted(normalized):
        _fail("ENTRY_CAPABILITIES_CANONICAL_ORDER_REQUIRED")
    return normalized


def _validated_budget(packet: EntryPacket) -> dict[str, int]:
    budget = packet.budget
    if not isinstance(budget, tuple):
        _fail("ENTRY_BUDGET_CANONICAL_TUPLE_REQUIRED")
    keys = [item[0] for item in budget if isinstance(item, tuple) and len(item) == 2]
    if len(keys) != len(budget) or len(keys) != len(set(keys)) or keys != sorted(keys):
        _fail("ENTRY_BUDGET_CANONICAL_ORDER_REQUIRED")
    result: dict[str, int] = {}
    for key, value in budget:
        key = _text(key, "entry.budget.key", 128)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            _fail(f"entry.budget.{key}:NONNEGATIVE_INTEGER_REQUIRED")
        result[key] = value
    return result


def _revalidate_entry_identity(packet: EntryPacket) -> None:
    if not isinstance(packet, EntryPacket):
        _fail("ENTRY_PACKET_REQUIRED")
    if packet.schema != ENTRY_SCHEMA:
        _fail("ENTRY_PACKET_SCHEMA_UNSUPPORTED")
    generation = _generation(packet.entity_generation, "entry.entity_generation")
    event_material = {
        "schema": ENTRY_EVENT_IDENTITY_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "causal_id": _text(packet.causal_id, "entry.causal_id"),
        "source_kind": _text(packet.source_kind, "entry.source_kind", 128),
        "source_id": _text(packet.source_id, "entry.source_id"),
        "modality": _text(packet.modality, "entry.modality", 128),
        "observed_time": _optional_text(packet.observed_time, "entry.observed_time"),
        "provenance_ref": _text(packet.provenance_ref, "entry.provenance_ref"),
        "provenance_sha256": _sha256(packet.provenance_sha256, "entry.provenance_sha256"),
        "parent_id": _optional_text(packet.parent_id, "entry.parent_id"),
        "stream_id": _optional_text(packet.stream_id, "entry.stream_id"),
        "payload_sha256": _sha256(packet.payload_sha256, "entry.payload_sha256"),
    }
    observed_event = _sha256(packet.event_sha256, "entry.event_sha256")
    if _canonical_sha256(event_material, "ENTRY_EVENT_IDENTITY") != observed_event:
        _fail("ENTRY_EVENT_IDENTITY_REVALIDATION_MISMATCH")

    admission_material = {
        "schema": ENTRY_ADMISSION_IDENTITY_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "event_sha256": observed_event,
        "entity_generation": generation,
        "ingress_id": _text(packet.ingress_id, "entry.ingress_id"),
        "received_time": _text(packet.received_time, "entry.received_time"),
        "capabilities": _validated_capabilities(packet),
        "capability_binding_sha256": _sha256(
            packet.capability_binding_sha256,
            "entry.capability_binding_sha256",
        ),
        "budget": _validated_budget(packet),
        "payload_ref": _text(packet.payload_ref, "entry.payload_ref"),
    }
    observed_admission = _sha256(packet.admission_sha256, "entry.admission_sha256")
    if _canonical_sha256(admission_material, "ENTRY_ADMISSION_IDENTITY") != observed_admission:
        _fail("ENTRY_ADMISSION_IDENTITY_REVALIDATION_MISMATCH")


def _revalidate_grid_plan(plan: GridPlan) -> None:
    if not isinstance(plan, GridPlan):
        _fail("GRID_PLAN_REQUIRED")
    try:
        observed = validate_grid_plan_identity(plan)
    except GridScheduleError as exc:
        raise ExecutorSequenceLaneError(f"GRID_PLAN_REJECTED:{exc}") from exc
    if observed != plan.plan_sha256:
        _fail("GRID_PLAN_IDENTITY_REVALIDATION_MISMATCH")


def _lane_material(binding: ExecutorSequenceLaneBinding) -> dict[str, Any]:
    return {
        "schema": LANE_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "generation": binding.generation,
        "executor_id": binding.executor_id,
        "source_kind": binding.source_kind,
        "source_id": binding.source_id,
        "stream_id": binding.stream_id,
        "role": binding.role,
    }


def _binding_material(binding: ExecutorSequenceLaneBinding) -> dict[str, Any]:
    data = asdict(binding)
    data.pop("binding_sha256", None)
    return data


def validate_executor_sequence_lane_binding(binding: ExecutorSequenceLaneBinding) -> None:
    if not isinstance(binding, ExecutorSequenceLaneBinding):
        _fail("EXECUTOR_SEQUENCE_LANE_BINDING_REQUIRED")
    if binding.schema != BINDING_SCHEMA or binding.lane_schema != LANE_SCHEMA:
        _fail("EXECUTOR_SEQUENCE_LANE_BINDING_SCHEMA_UNSUPPORTED")
    if binding.canonicalization_schema != CANONICALIZATION_SCHEMA:
        _fail("EXECUTOR_SEQUENCE_LANE_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    _generation(binding.generation)
    for field in ("executor_id", "source_kind", "source_id", "stream_id", "role", "ingress_id", "causal_id", "cell_id"):
        _text(getattr(binding, field), field)
    _optional_text(binding.entry_parent_id, "entry_parent_id")
    for field in ("sequence_lane_id", "entry_event_sha256", "entry_admission_sha256", "grid_plan_sha256", "binding_sha256"):
        _sha256(getattr(binding, field), field)
    expected_lane = _canonical_sha256(_lane_material(binding), "EXECUTOR_SEQUENCE_LANE_IDENTITY")
    if binding.sequence_lane_id != expected_lane:
        _fail("EXECUTOR_SEQUENCE_LANE_IDENTITY_MISMATCH")
    expected_binding = _canonical_sha256(_binding_material(binding), "EXECUTOR_SEQUENCE_LANE_BINDING")
    if binding.binding_sha256 != expected_binding:
        _fail("EXECUTOR_SEQUENCE_LANE_BINDING_DIGEST_MISMATCH")


def derive_executor_sequence_lane(
    entry: EntryPacket,
    grid_plan: GridPlan,
    *,
    executor_id: str,
    cell_id: str,
    role: str,
) -> ExecutorSequenceLaneBinding:
    """Derive one stable recurrent lane and exact step-specific source binding.

    No ordinal, timestamp, predecessor invocation id or caller-supplied lane label is accepted.
    The lane exists only when Typed Entry already carries an admitted ``stream_id``.
    """
    _revalidate_entry_identity(entry)
    _revalidate_grid_plan(grid_plan)

    executor_id = _text(executor_id, "executor_id", 256)
    cell_id = _text(cell_id, "cell_id", 256)
    role = _text(role, "role", 256)
    if entry.stream_id is None:
        _fail("EXECUTOR_SEQUENCE_LANE_IDENTITY_UNAVAILABLE")
    stream_id = _text(entry.stream_id, "entry.stream_id")

    cross_checks = {
        "generation": (entry.entity_generation, grid_plan.entity_generation),
        "ingress_id": (entry.ingress_id, grid_plan.ingress_id),
        "causal_id": (entry.causal_id, grid_plan.causal_id),
        "entry_event_sha256": (entry.event_sha256, grid_plan.entry_event_sha256),
        "entry_admission_sha256": (entry.admission_sha256, grid_plan.entry_admission_sha256),
    }
    for field, (left, right) in cross_checks.items():
        if left != right:
            _fail(f"EXECUTOR_SEQUENCE_LANE_ENTRY_GRID_MISMATCH:{field}")

    matching = [cell for cell in grid_plan.cells if cell.cell_id == cell_id]
    if len(matching) != 1:
        _fail("EXECUTOR_SEQUENCE_LANE_MODEL_CELL_NOT_UNIQUE")
    cell = matching[0]
    if cell.execution_class is not ExecutionClass.MODEL:
        _fail("EXECUTOR_SEQUENCE_LANE_CELL_NOT_MODEL")
    if cell.function != f"MODEL:{role}":
        _fail("EXECUTOR_SEQUENCE_LANE_CELL_ROLE_MISMATCH")

    lane_material = {
        "schema": LANE_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "generation": _generation(entry.entity_generation),
        "executor_id": executor_id,
        "source_kind": _text(entry.source_kind, "entry.source_kind", 128),
        "source_id": _text(entry.source_id, "entry.source_id"),
        "stream_id": stream_id,
        "role": role,
    }
    sequence_lane_id = _canonical_sha256(lane_material, "EXECUTOR_SEQUENCE_LANE_IDENTITY")
    material = {
        "schema": BINDING_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "lane_schema": LANE_SCHEMA,
        "generation": entry.entity_generation,
        "executor_id": executor_id,
        "source_kind": entry.source_kind,
        "source_id": entry.source_id,
        "stream_id": stream_id,
        "role": role,
        "sequence_lane_id": sequence_lane_id,
        "ingress_id": entry.ingress_id,
        "causal_id": entry.causal_id,
        "entry_parent_id": entry.parent_id,
        "entry_event_sha256": entry.event_sha256,
        "entry_admission_sha256": entry.admission_sha256,
        "grid_plan_sha256": grid_plan.plan_sha256,
        "cell_id": cell_id,
    }
    provisional = ExecutorSequenceLaneBinding(**material, binding_sha256="1" * 64)
    binding = ExecutorSequenceLaneBinding(
        **material,
        binding_sha256=_canonical_sha256(_binding_material(provisional), "EXECUTOR_SEQUENCE_LANE_BINDING"),
    )
    validate_executor_sequence_lane_binding(binding)
    return binding


__all__ = [
    "LANE_SCHEMA",
    "BINDING_SCHEMA",
    "ExecutorSequenceLaneError",
    "ExecutorSequenceLaneBinding",
    "derive_executor_sequence_lane",
    "validate_executor_sequence_lane_binding",
]
