#!/usr/bin/env python3
"""Authority-bearing wrapper for deterministic executor sequence-lane bindings.

``executor_sequence_lane_binding_v1`` remains useful as an integrity/grouping primitive, but a
hash-bound Entry stream label is not by itself control-plane stream authority.  This module is
the promotion boundary: it requires an independently derived ``StreamAuthorityView`` before a
cross-event lane may be represented as authorized.

Even an authorized lane does NOT assign t/t+1 positions, prove temporal adjacency, execute a
model, establish hidden-state causality, or grant runtime/training credit.  Actual adjacency
must later be atomically assigned/admitted at the real executor boundary in canonical state.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any

try:
    from .control_plane_stream_authority_v1 import (
        SCHEMA as STREAM_AUTHORITY_SCHEMA,
        StreamAuthorityError,
        StreamAuthorityView,
        validate_entry_stream_authority,
    )
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .executor_sequence_lane_binding_v1 import (
        BINDING_SCHEMA as LANE_BINDING_SCHEMA,
        ExecutorSequenceLaneBinding,
        ExecutorSequenceLaneBindingError,
        bind_executor_sequence_lane,
        validate_executor_sequence_lane_binding,
    )
    from .grid10_scheduler_v1 import GridPlan
    from .model_input_control_binding_v1 import ModelInputControlBinding
    from .xeno_entry_fabric_v1 import EntryPacket
except ImportError:
    from control_plane_stream_authority_v1 import (
        SCHEMA as STREAM_AUTHORITY_SCHEMA,
        StreamAuthorityError,
        StreamAuthorityView,
        validate_entry_stream_authority,
    )
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from executor_sequence_lane_binding_v1 import (
        BINDING_SCHEMA as LANE_BINDING_SCHEMA,
        ExecutorSequenceLaneBinding,
        ExecutorSequenceLaneBindingError,
        bind_executor_sequence_lane,
        validate_executor_sequence_lane_binding,
    )
    from grid10_scheduler_v1 import GridPlan
    from model_input_control_binding_v1 import ModelInputControlBinding
    from xeno_entry_fabric_v1 import EntryPacket


SCHEMA = "HCU_AUTHORIZED_EXECUTOR_SEQUENCE_LANE/v1"


class AuthorizedExecutorSequenceLaneError(ValueError):
    pass


@dataclass(frozen=True)
class AuthorizedExecutorSequenceLane:
    schema: str
    canonicalization_schema: str
    lane_binding_schema: str
    stream_authority_schema: str
    entity_generation: int
    executor_id: str
    invocation_id: str
    sequence_lane_sha256: str
    lane_binding_sha256: str
    stream_authority_binding_sha256: str
    entry_event_sha256: str
    entry_admission_sha256: str
    grid_plan_sha256: str
    authorization_sha256: str


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise AuthorizedExecutorSequenceLaneError(f"{field}:STRING_REQUIRED")
    if (
        len(value) != 64
        or value.lower() != value
        or any(ch not in "0123456789abcdef" for ch in value)
        or value in {"0" * 64, "f" * 64}
    ):
        raise AuthorizedExecutorSequenceLaneError(f"{field}:LOWERCASE_NONPLACEHOLDER_SHA256_REQUIRED")
    return value


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise AuthorizedExecutorSequenceLaneError(f"{field}:CANONICAL_NONEMPTY_STRING_REQUIRED")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise AuthorizedExecutorSequenceLaneError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _material(
    lane: ExecutorSequenceLaneBinding,
    authority_binding_sha256: str,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "lane_binding_schema": LANE_BINDING_SCHEMA,
        "stream_authority_schema": STREAM_AUTHORITY_SCHEMA,
        "entity_generation": lane.generation,
        "executor_id": _text(lane.executor_id, "lane.executor_id"),
        "invocation_id": _text(lane.invocation_id, "lane.invocation_id"),
        "sequence_lane_sha256": _sha256(lane.sequence_lane_sha256, "lane.sequence_lane_sha256"),
        "lane_binding_sha256": _sha256(lane.binding_sha256, "lane.binding_sha256"),
        "stream_authority_binding_sha256": _sha256(
            authority_binding_sha256,
            "stream_authority_binding_sha256",
        ),
        "entry_event_sha256": _sha256(lane.entry_event_sha256, "lane.entry_event_sha256"),
        "entry_admission_sha256": _sha256(
            lane.entry_admission_sha256,
            "lane.entry_admission_sha256",
        ),
        "grid_plan_sha256": _sha256(lane.grid_plan_sha256, "lane.grid_plan_sha256"),
    }


def authorize_executor_sequence_lane(
    packet: EntryPacket,
    grid_plan: GridPlan,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    stream_authority: StreamAuthorityView,
) -> AuthorizedExecutorSequenceLane:
    """Promote an integrity-bound lane only after independent stream authority validation."""
    try:
        authority_binding_sha256 = validate_entry_stream_authority(packet, stream_authority)
    except StreamAuthorityError as exc:
        raise AuthorizedExecutorSequenceLaneError(f"STREAM_AUTHORITY_REJECTED:{exc}") from exc
    try:
        lane = bind_executor_sequence_lane(packet, grid_plan, input_binding, consumed_input_bytes)
    except ExecutorSequenceLaneBindingError as exc:
        raise AuthorizedExecutorSequenceLaneError(f"SEQUENCE_LANE_BINDING_REJECTED:{exc}") from exc

    material = _material(lane, authority_binding_sha256)
    return AuthorizedExecutorSequenceLane(
        **material,
        authorization_sha256=_canonical_sha256(material, "AUTHORIZED_EXECUTOR_SEQUENCE_LANE"),
    )


def validate_authorized_executor_sequence_lane(
    authorized: AuthorizedExecutorSequenceLane,
    packet: EntryPacket,
    grid_plan: GridPlan,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    stream_authority: StreamAuthorityView,
) -> str:
    """Revalidate both the independent authority view and exact lane source parents."""
    if not isinstance(authorized, AuthorizedExecutorSequenceLane):
        raise AuthorizedExecutorSequenceLaneError("AUTHORIZED_EXECUTOR_SEQUENCE_LANE_REQUIRED")
    expected = authorize_executor_sequence_lane(
        packet,
        grid_plan,
        input_binding,
        consumed_input_bytes,
        stream_authority,
    )
    if authorized != expected:
        raise AuthorizedExecutorSequenceLaneError(
            "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_SOURCE_REVALIDATION_MISMATCH"
        )
    return expected.authorization_sha256
