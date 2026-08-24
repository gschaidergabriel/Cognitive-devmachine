#!/usr/bin/env python3
"""Canonical-DB-authorized executor sequence lanes for EntityOS/HCU.

This v2 successor removes the remaining caller-trust boundary in
``authorized_executor_sequence_lane_binding_v1``.  The caller no longer supplies an
``expected_stream_authority_binding_sha256``.  Instead the exact stream authority is read
from the existing canonical MiniUnifiedDB via ``entry_stream_authority_store_v1`` and then
cross-bound to the external authority-side binding before the lower sequence lane is built.

Positive v2 source closure therefore requires all of:

* an externally admitted stream-authority decision already persisted in canonical state;
* canonical DB readback of that exact admission/decision;
* an authority-side binding whose ``authority_binding_sha256`` equals the canonical decision
  digest and whose registry reference equals the canonical decision id;
* exact Entry/GRID/model-input/consumed-byte lane closure.

This still proves no temporal adjacency, model execution, hidden-state influence, reward,
training benefit, canonical truth or EffectGate authority.  It is a prerequisite evidence
object for the single temporal-causality gate only.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import sqlite3
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .entry_stream_authority_binding_v1 import (
        EntryStreamAuthorityBinding,
        EntryStreamAuthorityBindingError,
        validate_entry_stream_authority_binding,
    )
    from .entry_stream_authority_store_v1 import (
        EntryStreamAuthorityError,
        read_entry_stream_authority_admission,
        validate_entry_stream_authority_admission,
    )
    from .executor_sequence_lane_binding_v1 import (
        ExecutorSequenceLaneBindingError,
        bind_executor_sequence_lane,
        validate_executor_sequence_lane_binding,
    )
    from .grid10_scheduler_v1 import GridPlan
    from .model_input_control_binding_v1 import ModelInputControlBinding
    from .xeno_entry_fabric_v1 import EntryPacket
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from entry_stream_authority_binding_v1 import (
        EntryStreamAuthorityBinding,
        EntryStreamAuthorityBindingError,
        validate_entry_stream_authority_binding,
    )
    from entry_stream_authority_store_v1 import (
        EntryStreamAuthorityError,
        read_entry_stream_authority_admission,
        validate_entry_stream_authority_admission,
    )
    from executor_sequence_lane_binding_v1 import (
        ExecutorSequenceLaneBindingError,
        bind_executor_sequence_lane,
        validate_executor_sequence_lane_binding,
    )
    from grid10_scheduler_v1 import GridPlan
    from model_input_control_binding_v1 import ModelInputControlBinding
    from xeno_entry_fabric_v1 import EntryPacket

AUTHORIZED_LANE_SCHEMA = "HCU_AUTHORIZED_EXECUTOR_SEQUENCE_LANE_BINDING/v2"
REQUIRED_AUTHORITY_KIND = "CANONICAL_STREAM_REGISTRY"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class AuthorizedExecutorSequenceLaneBindingV2Error(ValueError):
    pass


@dataclass(frozen=True)
class AuthorizedExecutorSequenceLaneBindingV2:
    schema: str
    canonicalization_schema: str
    generation: int
    sequence_lane_sha256: str
    lane_binding_sha256: str
    stream_authority_binding_sha256: str
    stream_authority_admission_sha256: str
    stream_authority_decision_sha256: str
    stream_authority_namespace: str
    stream_authority_decision_id: str
    entry_event_sha256: str
    entry_admission_sha256: str
    executor_id: str
    invocation_id: str
    binding_sha256: str


def _need(condition: bool, code: str) -> None:
    if not condition:
        raise AuthorizedExecutorSequenceLaneBindingV2Error(code)


def _text(value: Any, field: str, max_len: int = 512) -> str:
    _need(isinstance(value, str) and bool(value.strip()), f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
    _need(value == normalized, f"{field}:NONCANONICAL_TEXT")
    _need(len(normalized) <= max_len, f"{field}:TOO_LONG")
    return normalized


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, 64)
    _need(
        len(value) == 64
        and value.lower() == value
        and all(ch in "0123456789abcdef" for ch in value)
        and value not in {"0" * 64, "f" * 64},
        f"{field}:LOWERCASE_NONPLACEHOLDER_SHA256_REQUIRED",
    )
    return value


def _generation(value: Any, field: str = "generation") -> int:
    _need(
        type(value) is int and 0 <= value <= MAX_SAFE_INTEGER,
        f"{field}:IJSON_SAFE_NONNEGATIVE_INTEGER_REQUIRED",
    )
    return value


def _material(binding: AuthorizedExecutorSequenceLaneBindingV2) -> dict[str, Any]:
    value = asdict(binding)
    value.pop("binding_sha256", None)
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except (CanonicalizationError, TypeError, ValueError) as exc:
        raise AuthorizedExecutorSequenceLaneBindingV2Error(f"{field}:CANONICALIZATION_FAILED") from exc


def _canonical_stream_authority(
    db: sqlite3.Connection,
    packet: EntryPacket,
    stream_authority: EntryStreamAuthorityBinding,
    *,
    current_generation: int,
):
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    _need(isinstance(packet, EntryPacket), "ENTRY_PACKET_REQUIRED")
    current_generation = _generation(current_generation, "current_generation")
    _need(packet.entity_generation == current_generation, "ENTRY_STREAM_AUTHORITY_GENERATION_MISMATCH")
    _need(packet.stream_id is not None, "ENTRY_STREAM_ID_REQUIRED")

    try:
        admission = read_entry_stream_authority_admission(
            db,
            current_generation=current_generation,
            source_kind=packet.source_kind,
            source_id=packet.source_id,
            stream_id=packet.stream_id,
        )
        validate_entry_stream_authority_admission(admission)
    except EntryStreamAuthorityError as exc:
        raise AuthorizedExecutorSequenceLaneBindingV2Error(
            f"CANONICAL_STREAM_AUTHORITY_UNAVAILABLE:{exc}"
        ) from exc

    _need(
        stream_authority.authority_kind == REQUIRED_AUTHORITY_KIND,
        "STREAM_AUTHORITY_NOT_CANONICAL_REGISTRY_KIND",
    )
    _need(
        stream_authority.authority_ref == admission.authority_decision_id,
        "STREAM_AUTHORITY_REFERENCE_NOT_CANONICAL_DECISION",
    )
    _need(
        stream_authority.authority_binding_sha256 == admission.decision_sha256,
        "STREAM_AUTHORITY_BINDING_NOT_CANONICAL_DECISION",
    )
    try:
        validate_entry_stream_authority_binding(
            stream_authority,
            packet,
            expected_authority_binding_sha256=admission.decision_sha256,
        )
    except EntryStreamAuthorityBindingError as exc:
        raise AuthorizedExecutorSequenceLaneBindingV2Error(
            f"STREAM_AUTHORITY_REJECTED:{exc}"
        ) from exc
    return admission


def bind_authorized_executor_sequence_lane_v2(
    db: sqlite3.Connection,
    packet: EntryPacket,
    grid_plan: GridPlan,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    stream_authority: EntryStreamAuthorityBinding,
    *,
    current_generation: int,
) -> AuthorizedExecutorSequenceLaneBindingV2:
    """Build an authorized lane with authority identity sourced only from canonical DB readback."""
    admission = _canonical_stream_authority(
        db,
        packet,
        stream_authority,
        current_generation=current_generation,
    )
    try:
        lane = bind_executor_sequence_lane(packet, grid_plan, input_binding, consumed_input_bytes)
        validate_executor_sequence_lane_binding(lane, packet, grid_plan, input_binding, consumed_input_bytes)
    except ExecutorSequenceLaneBindingError as exc:
        raise AuthorizedExecutorSequenceLaneBindingV2Error(f"SEQUENCE_LANE_REJECTED:{exc}") from exc

    _need(lane.generation == admission.generation, "LANE_STREAM_AUTHORITY_GENERATION_MISMATCH")
    material = {
        "schema": AUTHORIZED_LANE_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "generation": lane.generation,
        "sequence_lane_sha256": _sha256(lane.sequence_lane_sha256, "sequence_lane_sha256"),
        "lane_binding_sha256": _sha256(lane.binding_sha256, "lane_binding_sha256"),
        "stream_authority_binding_sha256": _sha256(
            stream_authority.binding_sha256,
            "stream_authority_binding_sha256",
        ),
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
        "entry_event_sha256": _sha256(lane.entry_event_sha256, "entry_event_sha256"),
        "entry_admission_sha256": _sha256(lane.entry_admission_sha256, "entry_admission_sha256"),
        "executor_id": _text(lane.executor_id, "executor_id", 256),
        "invocation_id": _text(lane.invocation_id, "invocation_id", 256),
    }
    provisional = AuthorizedExecutorSequenceLaneBindingV2(**material, binding_sha256="1" * 64)
    return AuthorizedExecutorSequenceLaneBindingV2(
        **material,
        binding_sha256=_canonical_sha256(_material(provisional), "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_V2"),
    )


def validate_authorized_executor_sequence_lane_v2(
    db: sqlite3.Connection,
    binding: AuthorizedExecutorSequenceLaneBindingV2,
    packet: EntryPacket,
    grid_plan: GridPlan,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    stream_authority: EntryStreamAuthorityBinding,
    *,
    current_generation: int,
) -> None:
    _need(
        isinstance(binding, AuthorizedExecutorSequenceLaneBindingV2),
        "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_V2_BINDING_REQUIRED",
    )
    _need(binding.schema == AUTHORIZED_LANE_SCHEMA, "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_V2_SCHEMA_UNSUPPORTED")
    _need(
        binding.canonicalization_schema == CANONICALIZATION_SCHEMA,
        "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_V2_CANONICALIZATION_SCHEMA_UNSUPPORTED",
    )
    observed = _sha256(binding.binding_sha256, "binding_sha256")
    expected_digest = _canonical_sha256(_material(binding), "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_V2")
    _need(observed == expected_digest, "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_V2_DIGEST_MISMATCH")

    expected = bind_authorized_executor_sequence_lane_v2(
        db,
        packet,
        grid_plan,
        input_binding,
        consumed_input_bytes,
        stream_authority,
        current_generation=current_generation,
    )
    _need(binding == expected, "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_V2_SOURCE_REVALIDATION_MISMATCH")


__all__ = [
    "AUTHORIZED_LANE_SCHEMA",
    "REQUIRED_AUTHORITY_KIND",
    "AuthorizedExecutorSequenceLaneBindingV2Error",
    "AuthorizedExecutorSequenceLaneBindingV2",
    "bind_authorized_executor_sequence_lane_v2",
    "validate_authorized_executor_sequence_lane_v2",
]
