#!/usr/bin/env python3
"""Authority-bearing executor sequence-lane projection over the canonical stream store.

``executor_sequence_lane_binding_v1`` proves an exact Entry/GRID10/model-input grouping path,
but the Entry's hash-bound ``stream_id`` is not authority by itself. Positive stream authority
comes only from ``entry_stream_authority_store_v1``: an external deterministic decision must
already have been admitted and atomically persisted into the caller's canonical MiniUnifiedDB.

This module is a read-only consumer of that single authority. It creates no stream store and no
temporal-order authority. A positive result means the exact lane and exact canonical stream
authority admission agree. It still does NOT assign sequence positions, prove t->t+1 adjacency,
execute a model, prove hidden-state causal use, mint truth/effects, or grant runtime/training
credit. Actual adjacency remains a later atomic executor-boundary admission in canonical state.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import sqlite3
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .entry_stream_authority_store_v1 import (
        ADMISSION_SCHEMA as STREAM_AUTHORITY_ADMISSION_SCHEMA,
        EntryStreamAuthorityAdmission,
        EntryStreamAuthorityError,
        read_entry_stream_authority_admission,
        validate_entry_stream_authority_admission,
    )
    from .executor_sequence_lane_binding_v1 import (
        BINDING_SCHEMA as LANE_BINDING_SCHEMA,
        ExecutorSequenceLaneBinding,
        ExecutorSequenceLaneBindingError,
        bind_executor_sequence_lane,
    )
    from .grid10_scheduler_v1 import GridPlan
    from .model_input_control_binding_v1 import ModelInputControlBinding
    from .xeno_entry_fabric_v1 import EntryPacket
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from entry_stream_authority_store_v1 import (
        ADMISSION_SCHEMA as STREAM_AUTHORITY_ADMISSION_SCHEMA,
        EntryStreamAuthorityAdmission,
        EntryStreamAuthorityError,
        read_entry_stream_authority_admission,
        validate_entry_stream_authority_admission,
    )
    from executor_sequence_lane_binding_v1 import (
        BINDING_SCHEMA as LANE_BINDING_SCHEMA,
        ExecutorSequenceLaneBinding,
        ExecutorSequenceLaneBindingError,
        bind_executor_sequence_lane,
    )
    from grid10_scheduler_v1 import GridPlan
    from model_input_control_binding_v1 import ModelInputControlBinding
    from xeno_entry_fabric_v1 import EntryPacket


SCHEMA = "HCU_AUTHORIZED_EXECUTOR_SEQUENCE_LANE/v2"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class AuthorizedExecutorSequenceLaneError(ValueError):
    pass


@dataclass(frozen=True)
class AuthorizedExecutorSequenceLane:
    schema: str
    canonicalization_schema: str
    lane_binding_schema: str
    stream_authority_admission_schema: str
    entity_generation: int
    executor_id: str
    invocation_id: str
    sequence_lane_sha256: str
    lane_binding_sha256: str
    stream_authority_admission_sha256: str
    stream_authority_decision_sha256: str
    stream_authority_namespace: str
    stream_authority_decision_id: str
    entry_event_sha256: str
    entry_admission_sha256: str
    grid_plan_sha256: str
    authorization_sha256: str


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise AuthorizedExecutorSequenceLaneError(message)


def _sha256(value: Any, field: str) -> str:
    _need(isinstance(value, str), f"{field}:STRING_REQUIRED")
    _need(
        len(value) == 64
        and value.lower() == value
        and all(ch in "0123456789abcdef" for ch in value)
        and value not in {"0" * 64, "f" * 64},
        f"{field}:LOWERCASE_NONPLACEHOLDER_SHA256_REQUIRED",
    )
    return value


def _text(value: Any, field: str, max_len: int = 512) -> str:
    _need(isinstance(value, str) and bool(value.strip()), f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
    _need(value == normalized, f"{field}:NONCANONICAL_TEXT")
    _need(len(normalized) <= max_len, f"{field}:TOO_LONG")
    return normalized


def _generation(value: Any) -> int:
    _need(
        type(value) is int and 0 <= value <= MAX_SAFE_INTEGER,
        "entity_generation:IJSON_SAFE_NONNEGATIVE_INTEGER_REQUIRED",
    )
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise AuthorizedExecutorSequenceLaneError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _read_authority(
    db: sqlite3.Connection,
    packet: EntryPacket,
    *,
    current_generation: int,
) -> EntryStreamAuthorityAdmission:
    _need(isinstance(db, sqlite3.Connection), "CANONICAL_SQLITE_CONNECTION_REQUIRED")
    _need(isinstance(packet, EntryPacket), "ENTRY_PACKET_REQUIRED")
    generation = _generation(current_generation)
    _need(packet.entity_generation == generation, "ENTRY_STREAM_AUTHORITY_GENERATION_MISMATCH")
    _need(packet.stream_id is not None, "EXECUTOR_SEQUENCE_STREAM_ID_REQUIRED")
    try:
        admission = read_entry_stream_authority_admission(
            db,
            current_generation=generation,
            source_kind=packet.source_kind,
            source_id=packet.source_id,
            stream_id=packet.stream_id,
        )
        validate_entry_stream_authority_admission(admission)
    except EntryStreamAuthorityError as exc:
        raise AuthorizedExecutorSequenceLaneError(
            f"EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE:{exc}"
        ) from exc
    for left, right, code in (
        (admission.generation, packet.entity_generation, "ENTRY_STREAM_AUTHORITY_GENERATION_MISMATCH"),
        (admission.source_kind, packet.source_kind, "ENTRY_STREAM_AUTHORITY_SOURCE_KIND_MISMATCH"),
        (admission.source_id, packet.source_id, "ENTRY_STREAM_AUTHORITY_SOURCE_ID_MISMATCH"),
        (admission.stream_id, packet.stream_id, "ENTRY_STREAM_AUTHORITY_STREAM_ID_MISMATCH"),
    ):
        _need(left == right, code)
    return admission


def _material(
    lane: ExecutorSequenceLaneBinding,
    admission: EntryStreamAuthorityAdmission,
) -> dict[str, Any]:
    _need(lane.generation == admission.generation, "LANE_STREAM_AUTHORITY_GENERATION_MISMATCH")
    _need(lane.source_kind == admission.source_kind, "LANE_STREAM_AUTHORITY_SOURCE_KIND_MISMATCH")
    _need(lane.source_id == admission.source_id, "LANE_STREAM_AUTHORITY_SOURCE_ID_MISMATCH")
    _need(lane.stream_id == admission.stream_id, "LANE_STREAM_AUTHORITY_STREAM_ID_MISMATCH")
    return {
        "schema": SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "lane_binding_schema": LANE_BINDING_SCHEMA,
        "stream_authority_admission_schema": STREAM_AUTHORITY_ADMISSION_SCHEMA,
        "entity_generation": _generation(lane.generation),
        "executor_id": _text(lane.executor_id, "lane.executor_id", 256),
        "invocation_id": _text(lane.invocation_id, "lane.invocation_id", 256),
        "sequence_lane_sha256": _sha256(lane.sequence_lane_sha256, "lane.sequence_lane_sha256"),
        "lane_binding_sha256": _sha256(lane.binding_sha256, "lane.binding_sha256"),
        "stream_authority_admission_sha256": _sha256(
            admission.admission_sha256,
            "stream_authority_admission_sha256",
        ),
        "stream_authority_decision_sha256": _sha256(
            admission.decision_sha256,
            "stream_authority_decision_sha256",
        ),
        "stream_authority_namespace": _text(
            admission.authority_namespace,
            "stream_authority_namespace",
            256,
        ),
        "stream_authority_decision_id": _text(
            admission.authority_decision_id,
            "stream_authority_decision_id",
            512,
        ),
        "entry_event_sha256": _sha256(lane.entry_event_sha256, "lane.entry_event_sha256"),
        "entry_admission_sha256": _sha256(
            lane.entry_admission_sha256,
            "lane.entry_admission_sha256",
        ),
        "grid_plan_sha256": _sha256(lane.grid_plan_sha256, "lane.grid_plan_sha256"),
    }


def authorize_executor_sequence_lane(
    db: sqlite3.Connection,
    packet: EntryPacket,
    grid_plan: GridPlan,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    *,
    current_generation: int,
) -> AuthorizedExecutorSequenceLane:
    """Read canonical stream authority, then bind it to the exact executor lane parents."""
    try:
        lane = bind_executor_sequence_lane(packet, grid_plan, input_binding, consumed_input_bytes)
    except ExecutorSequenceLaneBindingError as exc:
        raise AuthorizedExecutorSequenceLaneError(f"SEQUENCE_LANE_BINDING_REJECTED:{exc}") from exc
    admission = _read_authority(db, packet, current_generation=current_generation)
    material = _material(lane, admission)
    return AuthorizedExecutorSequenceLane(
        **material,
        authorization_sha256=_canonical_sha256(material, "AUTHORIZED_EXECUTOR_SEQUENCE_LANE"),
    )


def validate_authorized_executor_sequence_lane(
    authorized: AuthorizedExecutorSequenceLane,
    db: sqlite3.Connection,
    packet: EntryPacket,
    grid_plan: GridPlan,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    *,
    current_generation: int,
) -> str:
    """Re-read canonical stream authority and re-derive exact lane parents."""
    _need(isinstance(authorized, AuthorizedExecutorSequenceLane), "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_REQUIRED")
    expected = authorize_executor_sequence_lane(
        db,
        packet,
        grid_plan,
        input_binding,
        consumed_input_bytes,
        current_generation=current_generation,
    )
    _need(
        authorized == expected,
        "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_SOURCE_REVALIDATION_MISMATCH",
    )
    return expected.authorization_sha256


__all__ = [
    "SCHEMA",
    "AuthorizedExecutorSequenceLaneError",
    "AuthorizedExecutorSequenceLane",
    "authorize_executor_sequence_lane",
    "validate_authorized_executor_sequence_lane",
]
