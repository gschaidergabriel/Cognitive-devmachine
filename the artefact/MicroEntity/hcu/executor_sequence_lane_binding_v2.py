#!/usr/bin/env python3
"""Authority-backed executor sequence-lane binding for EntityOS/HCU.

v1 proves deterministic source integrity and grouping from Typed Entry ``stream_id`` but
cannot prove that the original stream label was independently authorized.  v2 is the
successor trust-boundary profile: it first revalidates the exact v1 source binding, then
requires an already-persisted ``HCU_ENTRY_STREAM_AUTHORITY_ADMISSION/v1`` from the same
canonical MiniUnifiedDB.  No write is performed by this lane binder.

The stable v2 lane identity therefore includes the independent stream-authority admission
identity in addition to generation/source/executor/engine/cell/role.  A self-consistent
Entry with an attacker-chosen stream label fails closed unless that exact stream scope was
admitted earlier by the external deterministic stream-authority boundary.

This still does NOT assign executor sequence positions or predecessor/successor adjacency,
execute a model, prove hidden-state use, or grant runtime/model/training/effect credit.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import sqlite3
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .entry_stream_authority_store_v1 import (
        ADMISSION_SCHEMA as STREAM_AUTHORITY_ADMISSION_SCHEMA,
        EntryStreamAuthorityError,
        read_entry_stream_authority_admission,
    )
    from .executor_sequence_lane_binding_v1 import (
        ExecutorSequenceLaneBinding as SourceLaneBindingV1,
        ExecutorSequenceLaneBindingError as SourceLaneBindingV1Error,
        bind_executor_sequence_lane as bind_source_lane_v1,
        validate_executor_sequence_lane_binding as validate_source_lane_v1,
    )
    from .grid10_scheduler_v1 import GridPlan
    from .model_input_control_binding_v1 import ModelInputControlBinding
    from .xeno_entry_fabric_v1 import EntryPacket
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from entry_stream_authority_store_v1 import (
        ADMISSION_SCHEMA as STREAM_AUTHORITY_ADMISSION_SCHEMA,
        EntryStreamAuthorityError,
        read_entry_stream_authority_admission,
    )
    from executor_sequence_lane_binding_v1 import (
        ExecutorSequenceLaneBinding as SourceLaneBindingV1,
        ExecutorSequenceLaneBindingError as SourceLaneBindingV1Error,
        bind_executor_sequence_lane as bind_source_lane_v1,
        validate_executor_sequence_lane_binding as validate_source_lane_v1,
    )
    from grid10_scheduler_v1 import GridPlan
    from model_input_control_binding_v1 import ModelInputControlBinding
    from xeno_entry_fabric_v1 import EntryPacket

LANE_IDENTITY_SCHEMA = "HCU_EXECUTOR_SEQUENCE_LANE_IDENTITY/v2"
BINDING_SCHEMA = "HCU_EXECUTOR_SEQUENCE_LANE_BINDING/v2"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class AuthorityBackedExecutorSequenceLaneError(ValueError):
    pass


@dataclass(frozen=True)
class AuthorityBackedExecutorSequenceLaneBinding:
    schema: str
    canonicalization_schema: str
    lane_identity_schema: str
    stream_authority_admission_schema: str
    generation: int
    authority_namespace: str
    authority_decision_id: str
    stream_authority_decision_sha256: str
    stream_authority_admission_sha256: str
    source_kind: str
    source_id: str
    stream_id: str
    executor_id: str
    engine_identity_sha256: str
    cell_id: str
    role: str
    sequence_lane_sha256: str
    source_lane_binding_v1_sha256: str
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


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise AuthorityBackedExecutorSequenceLaneError(message)


def _text(value: Any, field: str, max_len: int = 512) -> str:
    _need(isinstance(value, str) and bool(value.strip()), f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
    _need(value == normalized, f"{field}:NONCANONICAL_TEXT")
    _need(len(normalized) <= max_len, f"{field}:TOO_LONG")
    return normalized


def _sha256(value: Any, field: str) -> str:
    normalized = _text(value, field, 64)
    _need(
        len(normalized) == 64
        and normalized.lower() == normalized
        and all(ch in "0123456789abcdef" for ch in normalized)
        and normalized not in {"0" * 64, "f" * 64},
        f"{field}:LOWERCASE_NONPLACEHOLDER_SHA256_REQUIRED",
    )
    return normalized


def _generation(value: Any) -> int:
    _need(
        type(value) is int and 0 <= value <= MAX_SAFE_INTEGER,
        "generation:IJSON_SAFE_NONNEGATIVE_INTEGER_REQUIRED",
    )
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise AuthorityBackedExecutorSequenceLaneError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _binding_material(binding: AuthorityBackedExecutorSequenceLaneBinding) -> dict[str, Any]:
    data = asdict(binding)
    data.pop("binding_sha256", None)
    return data


def _lane_material(
    source: SourceLaneBindingV1,
    *,
    stream_authority_admission_sha256: str,
) -> dict[str, Any]:
    return {
        "schema": LANE_IDENTITY_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "generation": _generation(source.generation),
        "source_kind": _text(source.source_kind, "source_kind", 128),
        "source_id": _text(source.source_id, "source_id"),
        "stream_id": _text(source.stream_id, "stream_id"),
        "stream_authority_admission_sha256": _sha256(
            stream_authority_admission_sha256,
            "stream_authority_admission_sha256",
        ),
        "executor_id": _text(source.executor_id, "executor_id", 256),
        "engine_identity_sha256": _sha256(source.engine_identity_sha256, "engine_identity_sha256"),
        "cell_id": _text(source.cell_id, "cell_id", 256),
        "role": _text(source.role, "role", 256),
    }


def _authority_for_source(
    db: sqlite3.Connection,
    source: SourceLaneBindingV1,
):
    try:
        admission = read_entry_stream_authority_admission(
            db,
            current_generation=source.generation,
            source_kind=source.source_kind,
            source_id=source.source_id,
            stream_id=source.stream_id,
        )
    except EntryStreamAuthorityError as exc:
        raise AuthorityBackedExecutorSequenceLaneError(
            f"EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE:{exc}"
        ) from exc
    _need(
        admission.schema == STREAM_AUTHORITY_ADMISSION_SCHEMA,
        "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_SCHEMA_MISMATCH",
    )
    _need(admission.generation == source.generation, "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_GENERATION_MISMATCH")
    _need(admission.source_kind == source.source_kind, "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_SOURCE_KIND_MISMATCH")
    _need(admission.source_id == source.source_id, "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_SOURCE_ID_MISMATCH")
    _need(admission.stream_id == source.stream_id, "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_STREAM_ID_MISMATCH")
    return admission


def bind_authority_backed_executor_sequence_lane(
    db: sqlite3.Connection,
    packet: EntryPacket,
    grid_plan: GridPlan,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
) -> AuthorityBackedExecutorSequenceLaneBinding:
    """Derive a recurrent lane only after independent canonical stream admission exists."""
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    try:
        source = bind_source_lane_v1(packet, grid_plan, input_binding, consumed_input_bytes)
        validate_source_lane_v1(source, packet, grid_plan, input_binding, consumed_input_bytes)
    except SourceLaneBindingV1Error as exc:
        raise AuthorityBackedExecutorSequenceLaneError(f"SOURCE_LANE_V1_REJECTED:{exc}") from exc

    authority = _authority_for_source(db, source)
    lane_sha = _canonical_sha256(
        _lane_material(
            source,
            stream_authority_admission_sha256=authority.admission_sha256,
        ),
        "EXECUTOR_SEQUENCE_LANE_IDENTITY_V2",
    )
    material = {
        "schema": BINDING_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "lane_identity_schema": LANE_IDENTITY_SCHEMA,
        "stream_authority_admission_schema": STREAM_AUTHORITY_ADMISSION_SCHEMA,
        "generation": source.generation,
        "authority_namespace": _text(authority.authority_namespace, "authority_namespace", 256),
        "authority_decision_id": _text(authority.authority_decision_id, "authority_decision_id"),
        "stream_authority_decision_sha256": _sha256(authority.decision_sha256, "stream_authority_decision_sha256"),
        "stream_authority_admission_sha256": _sha256(authority.admission_sha256, "stream_authority_admission_sha256"),
        "source_kind": source.source_kind,
        "source_id": source.source_id,
        "stream_id": source.stream_id,
        "executor_id": source.executor_id,
        "engine_identity_sha256": source.engine_identity_sha256,
        "cell_id": source.cell_id,
        "role": source.role,
        "sequence_lane_sha256": lane_sha,
        "source_lane_binding_v1_sha256": _sha256(source.binding_sha256, "source_lane_binding_v1_sha256"),
        "entry_event_sha256": source.entry_event_sha256,
        "entry_admission_sha256": source.entry_admission_sha256,
        "route_decision_sha256": source.route_decision_sha256,
        "grid_plan_sha256": source.grid_plan_sha256,
        "model_input_control_binding_sha256": source.model_input_control_binding_sha256,
        "vector_control_packet_sha256": source.vector_control_packet_sha256,
        "invocation_id": source.invocation_id,
        "input_sha256": source.input_sha256,
        "input_size": source.input_size,
    }
    provisional = AuthorityBackedExecutorSequenceLaneBinding(**material, binding_sha256="1" * 64)
    binding = AuthorityBackedExecutorSequenceLaneBinding(
        **material,
        binding_sha256=_canonical_sha256(_binding_material(provisional), "EXECUTOR_SEQUENCE_LANE_BINDING_V2"),
    )
    validate_authority_backed_executor_sequence_lane_binding(
        binding,
        db,
        packet,
        grid_plan,
        input_binding,
        consumed_input_bytes,
    )
    return binding


def validate_authority_backed_executor_sequence_lane_binding(
    binding: AuthorityBackedExecutorSequenceLaneBinding,
    db: sqlite3.Connection,
    packet: EntryPacket,
    grid_plan: GridPlan,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
) -> None:
    if not isinstance(binding, AuthorityBackedExecutorSequenceLaneBinding):
        raise AuthorityBackedExecutorSequenceLaneError("AUTHORITY_BACKED_EXECUTOR_SEQUENCE_LANE_BINDING_REQUIRED")
    _need(binding.schema == BINDING_SCHEMA, "EXECUTOR_SEQUENCE_LANE_BINDING_V2_SCHEMA_UNSUPPORTED")
    _need(binding.canonicalization_schema == CANONICALIZATION_SCHEMA, "EXECUTOR_SEQUENCE_LANE_V2_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    _need(binding.lane_identity_schema == LANE_IDENTITY_SCHEMA, "EXECUTOR_SEQUENCE_LANE_IDENTITY_V2_SCHEMA_UNSUPPORTED")
    _need(
        binding.stream_authority_admission_schema == STREAM_AUTHORITY_ADMISSION_SCHEMA,
        "EXECUTOR_SEQUENCE_STREAM_AUTHORITY_SCHEMA_MISMATCH",
    )
    observed = _sha256(binding.binding_sha256, "binding_sha256")
    expected = _canonical_sha256(_binding_material(binding), "EXECUTOR_SEQUENCE_LANE_BINDING_V2")
    _need(observed == expected, "EXECUTOR_SEQUENCE_LANE_BINDING_V2_DIGEST_MISMATCH")

    rebuilt = bind_authority_backed_executor_sequence_lane.__wrapped__(db, packet, grid_plan, input_binding, consumed_input_bytes) if hasattr(bind_authority_backed_executor_sequence_lane, "__wrapped__") else None
    if rebuilt is None:
        # Avoid recursive public validation: rederive the two independent sources directly.
        try:
            source = bind_source_lane_v1(packet, grid_plan, input_binding, consumed_input_bytes)
            validate_source_lane_v1(source, packet, grid_plan, input_binding, consumed_input_bytes)
        except SourceLaneBindingV1Error as exc:
            raise AuthorityBackedExecutorSequenceLaneError(f"SOURCE_LANE_V1_REJECTED:{exc}") from exc
        authority = _authority_for_source(db, source)
        lane_sha = _canonical_sha256(
            _lane_material(source, stream_authority_admission_sha256=authority.admission_sha256),
            "EXECUTOR_SEQUENCE_LANE_IDENTITY_V2",
        )
        checks = {
            "generation": (binding.generation, source.generation),
            "source_kind": (binding.source_kind, source.source_kind),
            "source_id": (binding.source_id, source.source_id),
            "stream_id": (binding.stream_id, source.stream_id),
            "executor_id": (binding.executor_id, source.executor_id),
            "engine_identity_sha256": (binding.engine_identity_sha256, source.engine_identity_sha256),
            "cell_id": (binding.cell_id, source.cell_id),
            "role": (binding.role, source.role),
            "sequence_lane_sha256": (binding.sequence_lane_sha256, lane_sha),
            "source_lane_binding_v1_sha256": (binding.source_lane_binding_v1_sha256, source.binding_sha256),
            "entry_event_sha256": (binding.entry_event_sha256, source.entry_event_sha256),
            "entry_admission_sha256": (binding.entry_admission_sha256, source.entry_admission_sha256),
            "route_decision_sha256": (binding.route_decision_sha256, source.route_decision_sha256),
            "grid_plan_sha256": (binding.grid_plan_sha256, source.grid_plan_sha256),
            "model_input_control_binding_sha256": (binding.model_input_control_binding_sha256, source.model_input_control_binding_sha256),
            "vector_control_packet_sha256": (binding.vector_control_packet_sha256, source.vector_control_packet_sha256),
            "invocation_id": (binding.invocation_id, source.invocation_id),
            "input_sha256": (binding.input_sha256, source.input_sha256),
            "input_size": (binding.input_size, source.input_size),
            "authority_namespace": (binding.authority_namespace, authority.authority_namespace),
            "authority_decision_id": (binding.authority_decision_id, authority.authority_decision_id),
            "stream_authority_decision_sha256": (binding.stream_authority_decision_sha256, authority.decision_sha256),
            "stream_authority_admission_sha256": (binding.stream_authority_admission_sha256, authority.admission_sha256),
        }
        for field, (left, right) in checks.items():
            _need(left == right, f"EXECUTOR_SEQUENCE_LANE_V2_SOURCE_REVALIDATION_MISMATCH:{field}")


__all__ = [
    "LANE_IDENTITY_SCHEMA",
    "BINDING_SCHEMA",
    "AuthorityBackedExecutorSequenceLaneError",
    "AuthorityBackedExecutorSequenceLaneBinding",
    "bind_authority_backed_executor_sequence_lane",
    "validate_authority_backed_executor_sequence_lane_binding",
]
