#!/usr/bin/env python3
"""Deterministic lane-context derivation for future executor-owned J-Space sequencing.

This module deliberately does *not* create temporal/adjacency evidence.  It only derives a
stable lane key and an event-specific context digest from already-admitted Typed Entry,
scheduler-owned GRID10 and VerifiedModelExecution evidence.  A future executor sequence
admission store may use this context at the actual executor I/O boundary, but caller-labelled
`t/t+1`, timestamps, ordinals or trace names never become sequence authority here.

Cross-event recurrence is admitted for lane-key derivation only when Typed Entry already carries
an admitted ``stream_id``.  Without that stream identity the strongest permitted scope is one
GRID plan.  Source construction alone grants zero runtime, J-Space-model or training credit.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
    from .grid10_scheduler_v1 import (
        ExecutionClass,
        GridPlan,
        GridScheduleError,
        validate_grid_plan_identity,
    )
    from .model_execution_receipt_v1 import (
        VerifiedModelExecution,
        ModelExecutionReceiptError,
        validate_verified_model_execution,
    )
    from .xeno_entry_fabric_v1 import EntryPacket
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
    from grid10_scheduler_v1 import ExecutionClass, GridPlan, GridScheduleError, validate_grid_plan_identity
    from model_execution_receipt_v1 import (
        VerifiedModelExecution,
        ModelExecutionReceiptError,
        validate_verified_model_execution,
    )
    from xeno_entry_fabric_v1 import EntryPacket


SCHEMA = "HCU_EXECUTOR_SEQUENCE_LANE_CONTEXT/v1"
LANE_KEY_SCHEMA = "HCU_EXECUTOR_SEQUENCE_LANE_KEY/v1"
CROSS_EVENT_STREAM = "CROSS_EVENT_STREAM"
INTRA_REQUEST_GRID = "INTRA_REQUEST_GRID"
LANE_SCOPES = {CROSS_EVENT_STREAM, INTRA_REQUEST_GRID}


class ExecutorSequenceLaneContextError(ValueError):
    pass


@dataclass(frozen=True)
class ExecutorSequenceLaneContext:
    schema: str
    canonicalization_schema: str
    lane_scope: str
    entity_generation: int
    executor_id: str
    role: str
    source_kind: str
    source_id: str
    stream_id: str | None
    entry_event_sha256: str
    entry_admission_sha256: str
    grid_plan_sha256: str
    output_producing_cell_id: str
    verified_model_execution_sha256: str
    lane_key_sha256: str
    context_sha256: str


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ExecutorSequenceLaneContextError(message)


def _text(value: Any, field: str) -> str:
    _need(isinstance(value, str) and bool(value.strip()), f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    _need(len(value) <= 1024, f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field)
    _need(
        len(value) == 64
        and value.lower() == value
        and all(ch in "0123456789abcdef" for ch in value)
        and value not in {"0" * 64, "f" * 64},
        f"{field}:LOWERCASE_NONPLACEHOLDER_SHA256_REQUIRED",
    )
    return value


def _digest(material: dict[str, Any]) -> str:
    return hashlib.sha256(canonicalize(material)).hexdigest()


def _cross_bind_sources(
    packet: EntryPacket,
    grid_plan: GridPlan,
    verified_execution: VerifiedModelExecution,
) -> None:
    _need(isinstance(packet, EntryPacket), "ADMITTED_ENTRY_PACKET_REQUIRED")
    _need(isinstance(grid_plan, GridPlan), "GRID_PLAN_REQUIRED")
    _need(isinstance(verified_execution, VerifiedModelExecution), "VERIFIED_MODEL_EXECUTION_REQUIRED")
    try:
        validate_grid_plan_identity(grid_plan)
    except GridScheduleError as exc:
        raise ExecutorSequenceLaneContextError(f"GRID_PLAN_REJECTED:{exc}") from exc
    try:
        validate_verified_model_execution(verified_execution)
    except ModelExecutionReceiptError as exc:
        raise ExecutorSequenceLaneContextError(f"VERIFIED_MODEL_EXECUTION_REJECTED:{exc}") from exc

    _need(
        packet.entity_generation == grid_plan.entity_generation == verified_execution.entity_generation,
        "SEQUENCE_LANE_GENERATION_MISMATCH",
    )
    _need(packet.ingress_id == grid_plan.ingress_id, "SEQUENCE_LANE_INGRESS_ID_MISMATCH")
    _need(packet.causal_id == grid_plan.causal_id, "SEQUENCE_LANE_CAUSAL_ID_MISMATCH")
    _need(packet.event_sha256 == grid_plan.entry_event_sha256, "SEQUENCE_LANE_ENTRY_EVENT_MISMATCH")
    _need(
        packet.admission_sha256 == grid_plan.entry_admission_sha256,
        "SEQUENCE_LANE_ENTRY_ADMISSION_MISMATCH",
    )
    _need(
        verified_execution.grid_plan_sha256 == grid_plan.plan_sha256,
        "SEQUENCE_LANE_MODEL_EXECUTION_GRID_MISMATCH",
    )

    cells = [
        cell for cell in grid_plan.cells
        if cell.cell_id == verified_execution.output_producing_cell_id
    ]
    _need(len(cells) == 1, "SEQUENCE_LANE_MODEL_CELL_NOT_UNIQUE")
    cell = cells[0]
    _need(cell.execution_class is ExecutionClass.MODEL, "SEQUENCE_LANE_OUTPUT_CELL_NOT_MODEL")
    _need(cell.function == f"MODEL:{verified_execution.role}", "SEQUENCE_LANE_ROLE_MISMATCH")


def _lane_key_material(
    *,
    lane_scope: str,
    packet: EntryPacket,
    grid_plan: GridPlan,
    verified_execution: VerifiedModelExecution,
) -> dict[str, Any]:
    common = {
        "schema": LANE_KEY_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "lane_scope": lane_scope,
        "entity_generation": packet.entity_generation,
        "executor_id": _text(verified_execution.executor_id, "verified_execution.executor_id"),
        "role": _text(verified_execution.role, "verified_execution.role"),
    }
    if lane_scope == CROSS_EVENT_STREAM:
        stream_id = packet.stream_id
        _need(
            isinstance(stream_id, str) and bool(stream_id.strip()),
            "EXECUTOR_SEQUENCE_LANE_IDENTITY_UNAVAILABLE:ADMITTED_STREAM_ID_REQUIRED",
        )
        return {
            **common,
            "source_kind": _text(packet.source_kind, "packet.source_kind"),
            "source_id": _text(packet.source_id, "packet.source_id"),
            "stream_id": stream_id.strip(),
        }
    if lane_scope == INTRA_REQUEST_GRID:
        return {
            **common,
            "grid_plan_sha256": _sha256(grid_plan.plan_sha256, "grid_plan.plan_sha256"),
            "output_producing_cell_id": _text(
                verified_execution.output_producing_cell_id,
                "verified_execution.output_producing_cell_id",
            ),
        }
    raise ExecutorSequenceLaneContextError("SEQUENCE_LANE_SCOPE_UNSUPPORTED")


def derive_executor_sequence_lane_context(
    packet: EntryPacket,
    grid_plan: GridPlan,
    verified_execution: VerifiedModelExecution,
    *,
    lane_scope: str,
) -> ExecutorSequenceLaneContext:
    """Derive a non-temporal lane context from exact admitted causal parents.

    ``lane_key_sha256`` is stable across events only for ``CROSS_EVENT_STREAM`` and only when
    Typed Entry already admitted the same source/stream identity.  ``context_sha256`` remains
    event/plan/execution specific.  Neither digest establishes predecessor/successor ordering.
    """
    _need(lane_scope in LANE_SCOPES, "SEQUENCE_LANE_SCOPE_UNSUPPORTED")
    _cross_bind_sources(packet, grid_plan, verified_execution)

    lane_key_material = _lane_key_material(
        lane_scope=lane_scope,
        packet=packet,
        grid_plan=grid_plan,
        verified_execution=verified_execution,
    )
    lane_key_sha256 = _digest(lane_key_material)

    stream_id = packet.stream_id.strip() if isinstance(packet.stream_id, str) else None
    material = {
        "schema": SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "lane_scope": lane_scope,
        "entity_generation": packet.entity_generation,
        "executor_id": _text(verified_execution.executor_id, "verified_execution.executor_id"),
        "role": _text(verified_execution.role, "verified_execution.role"),
        "source_kind": _text(packet.source_kind, "packet.source_kind"),
        "source_id": _text(packet.source_id, "packet.source_id"),
        "stream_id": stream_id,
        "entry_event_sha256": _sha256(packet.event_sha256, "packet.event_sha256"),
        "entry_admission_sha256": _sha256(packet.admission_sha256, "packet.admission_sha256"),
        "grid_plan_sha256": _sha256(grid_plan.plan_sha256, "grid_plan.plan_sha256"),
        "output_producing_cell_id": _text(
            verified_execution.output_producing_cell_id,
            "verified_execution.output_producing_cell_id",
        ),
        "verified_model_execution_sha256": _sha256(
            verified_execution.receipt_sha256,
            "verified_execution.receipt_sha256",
        ),
        "lane_key_sha256": lane_key_sha256,
    }
    context_sha256 = _digest(material)
    return ExecutorSequenceLaneContext(**material, context_sha256=context_sha256)


def validate_executor_sequence_lane_context(
    value: ExecutorSequenceLaneContext,
    packet: EntryPacket,
    grid_plan: GridPlan,
    verified_execution: VerifiedModelExecution,
) -> str:
    """Re-derive from exact source objects; a self-consistent outer hash is insufficient."""
    _need(isinstance(value, ExecutorSequenceLaneContext), "EXECUTOR_SEQUENCE_LANE_CONTEXT_REQUIRED")
    expected = derive_executor_sequence_lane_context(
        packet,
        grid_plan,
        verified_execution,
        lane_scope=value.lane_scope,
    )
    _need(value == expected, "EXECUTOR_SEQUENCE_LANE_CONTEXT_SOURCE_REVALIDATION_MISMATCH")
    return expected.context_sha256
