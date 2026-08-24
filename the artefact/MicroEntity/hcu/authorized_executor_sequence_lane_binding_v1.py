#!/usr/bin/env python3
"""NONCURRENT compatibility-only authority-bound executor sequence lane wrapper.

Historical/research purpose only. The lower-level ``executor_sequence_lane_binding_v1`` proves
deterministic composition of Entry/GRID/input facts, and this wrapper records an externally
supplied stream-authority binding. It is retained for reproducibility and donor comparison.

CURRENT PROMOTION LAW: this module is NOT a promotable stream/lane authority because
``expected_stream_authority_binding_sha256`` is caller-supplied at this API boundary. Current
promotion must use ``executor_sequence_lane_authority_v1`` / ``HCU_AUTHORIZED_EXECUTOR_SEQUENCE_LANE/v2``,
which reads the already externally admitted stream-authority decision from the caller's existing
canonical MiniUnifiedDB and re-derives the exact lane parents. This compatibility module creates
no canonical truth/state/effect/temporal authority and grants no recurrent t->t+1, intervention,
hidden-state, model-runtime, or training credit.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .entry_stream_authority_binding_v1 import (
        EntryStreamAuthorityBinding,
        EntryStreamAuthorityBindingError,
        validate_entry_stream_authority_binding,
    )
    from .executor_sequence_lane_binding_v1 import (
        ExecutorSequenceLaneBinding,
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
    from executor_sequence_lane_binding_v1 import (
        ExecutorSequenceLaneBinding,
        ExecutorSequenceLaneBindingError,
        bind_executor_sequence_lane,
        validate_executor_sequence_lane_binding,
    )
    from grid10_scheduler_v1 import GridPlan
    from model_input_control_binding_v1 import ModelInputControlBinding
    from xeno_entry_fabric_v1 import EntryPacket

AUTHORIZED_LANE_SCHEMA = "HCU_AUTHORIZED_EXECUTOR_SEQUENCE_LANE_BINDING/v1"
PROMOTION_STATUS = "NONCURRENT_COMPATIBILITY_RESEARCH_ONLY"
CURRENT_PROMOTION_SCHEMA = "HCU_AUTHORIZED_EXECUTOR_SEQUENCE_LANE/v2"
CURRENT_PROMOTION_MODULE = "executor_sequence_lane_authority_v1.py"


class AuthorizedExecutorSequenceLaneBindingError(ValueError):
    pass


@dataclass(frozen=True)
class AuthorizedExecutorSequenceLaneBinding:
    schema: str
    canonicalization_schema: str
    generation: int
    sequence_lane_sha256: str
    lane_binding_sha256: str
    stream_authority_binding_sha256: str
    external_authority_binding_sha256: str
    entry_event_sha256: str
    entry_admission_sha256: str
    executor_id: str
    invocation_id: str
    binding_sha256: str


def _need(condition: bool, code: str) -> None:
    if not condition:
        raise AuthorizedExecutorSequenceLaneBindingError(code)


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


def _material(binding: AuthorizedExecutorSequenceLaneBinding) -> dict[str, Any]:
    value = asdict(binding)
    value.pop("binding_sha256", None)
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except (CanonicalizationError, TypeError, ValueError) as exc:
        raise AuthorizedExecutorSequenceLaneBindingError(f"{field}:CANONICALIZATION_FAILED") from exc


def bind_authorized_executor_sequence_lane(
    packet: EntryPacket,
    grid_plan: GridPlan,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    stream_authority: EntryStreamAuthorityBinding,
    *,
    expected_stream_authority_binding_sha256: str,
) -> AuthorizedExecutorSequenceLaneBinding:
    """Reproduce the historical v1 compatibility binding; never use it for promotion."""
    try:
        validate_entry_stream_authority_binding(
            stream_authority,
            packet,
            expected_authority_binding_sha256=expected_stream_authority_binding_sha256,
        )
    except EntryStreamAuthorityBindingError as exc:
        raise AuthorizedExecutorSequenceLaneBindingError(
            f"STREAM_AUTHORITY_REJECTED:{exc}"
        ) from exc
    try:
        lane = bind_executor_sequence_lane(packet, grid_plan, input_binding, consumed_input_bytes)
    except ExecutorSequenceLaneBindingError as exc:
        raise AuthorizedExecutorSequenceLaneBindingError(f"SEQUENCE_LANE_REJECTED:{exc}") from exc

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
        "external_authority_binding_sha256": _sha256(
            expected_stream_authority_binding_sha256,
            "expected_stream_authority_binding_sha256",
        ),
        "entry_event_sha256": _sha256(lane.entry_event_sha256, "entry_event_sha256"),
        "entry_admission_sha256": _sha256(lane.entry_admission_sha256, "entry_admission_sha256"),
        "executor_id": _text(lane.executor_id, "executor_id", 256),
        "invocation_id": _text(lane.invocation_id, "invocation_id", 256),
    }
    provisional = AuthorizedExecutorSequenceLaneBinding(**material, binding_sha256="1" * 64)
    return AuthorizedExecutorSequenceLaneBinding(
        **material,
        binding_sha256=_canonical_sha256(_material(provisional), "AUTHORIZED_EXECUTOR_SEQUENCE_LANE"),
    )


def validate_authorized_executor_sequence_lane(
    binding: AuthorizedExecutorSequenceLaneBinding,
    packet: EntryPacket,
    grid_plan: GridPlan,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    stream_authority: EntryStreamAuthorityBinding,
    *,
    expected_stream_authority_binding_sha256: str,
) -> None:
    """Revalidate the historical v1 compatibility binding; no promotion credit follows."""
    _need(
        isinstance(binding, AuthorizedExecutorSequenceLaneBinding),
        "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_BINDING_REQUIRED",
    )
    _need(binding.schema == AUTHORIZED_LANE_SCHEMA, "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_SCHEMA_UNSUPPORTED")
    _need(
        binding.canonicalization_schema == CANONICALIZATION_SCHEMA,
        "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_CANONICALIZATION_SCHEMA_UNSUPPORTED",
    )
    observed = _sha256(binding.binding_sha256, "binding_sha256")
    expected = _canonical_sha256(_material(binding), "AUTHORIZED_EXECUTOR_SEQUENCE_LANE")
    _need(observed == expected, "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_DIGEST_MISMATCH")

    try:
        validate_entry_stream_authority_binding(
            stream_authority,
            packet,
            expected_authority_binding_sha256=expected_stream_authority_binding_sha256,
        )
        lane = bind_executor_sequence_lane(packet, grid_plan, input_binding, consumed_input_bytes)
        validate_executor_sequence_lane_binding(lane, packet, grid_plan, input_binding, consumed_input_bytes)
    except (EntryStreamAuthorityBindingError, ExecutorSequenceLaneBindingError) as exc:
        raise AuthorizedExecutorSequenceLaneBindingError(f"AUTHORIZED_LANE_SOURCE_REVALIDATION_FAILED:{exc}") from exc

    expected_binding = bind_authorized_executor_sequence_lane(
        packet,
        grid_plan,
        input_binding,
        consumed_input_bytes,
        stream_authority,
        expected_stream_authority_binding_sha256=expected_stream_authority_binding_sha256,
    )
    _need(binding == expected_binding, "AUTHORIZED_EXECUTOR_SEQUENCE_LANE_SOURCE_MISMATCH")


__all__ = [
    "AUTHORIZED_LANE_SCHEMA",
    "PROMOTION_STATUS",
    "CURRENT_PROMOTION_SCHEMA",
    "CURRENT_PROMOTION_MODULE",
    "AuthorizedExecutorSequenceLaneBindingError",
    "AuthorizedExecutorSequenceLaneBinding",
    "bind_authorized_executor_sequence_lane",
    "validate_authorized_executor_sequence_lane",
]
