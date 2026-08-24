#!/usr/bin/env python3
"""Close an executor sequence-lane binding against independent stream authority.

``executor_sequence_lane_v1`` gives a deterministic lane/grouping identity derived from an
Entry's hash-bound ``stream_id``.  ``entry_stream_authority_store_v1`` separately admits an
external transport/control-plane stream decision into the existing canonical MiniUnifiedDB.
This module composes the two without creating another lane, store or temporal-order authority.

A positive closure means only:

* the lane binding is self-authenticating at its declared source scope;
* the same generation/source-kind/source-id/stream-id has a canonical DB stream-authority
  admission that was previously gated by an external admitted-decision registry; and
* the lane binding names that exact stream authority admission/decision.

It does NOT establish predecessor/successor adjacency, packet ancestry, model execution,
hidden-state causal use, reward, training benefit, canonical truth or EffectGate authority.
Those remain separate gates.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import sqlite3
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .entry_stream_authority_store_v1 import (
        EntryStreamAuthorityError,
        read_entry_stream_authority_admission,
        validate_entry_stream_authority_admission,
    )
    from .executor_sequence_lane_v1 import (
        BINDING_SCHEMA as LANE_BINDING_SCHEMA,
        LANE_SCHEMA,
        ExecutorSequenceLaneBinding,
        ExecutorSequenceLaneError,
        validate_executor_sequence_lane_binding,
    )
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from entry_stream_authority_store_v1 import (
        EntryStreamAuthorityError,
        read_entry_stream_authority_admission,
        validate_entry_stream_authority_admission,
    )
    from executor_sequence_lane_v1 import (
        BINDING_SCHEMA as LANE_BINDING_SCHEMA,
        LANE_SCHEMA,
        ExecutorSequenceLaneBinding,
        ExecutorSequenceLaneError,
        validate_executor_sequence_lane_binding,
    )

SCHEMA = "HCU_EXECUTOR_SEQUENCE_LANE_AUTHORITY_CLOSURE/v1"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class ExecutorSequenceLaneAuthorityClosureError(ValueError):
    pass


@dataclass(frozen=True)
class ExecutorSequenceLaneAuthorityClosure:
    schema: str
    canonicalization_schema: str
    lane_schema: str
    lane_binding_schema: str
    generation: int
    executor_id: str
    source_kind: str
    source_id: str
    stream_id: str
    role: str
    sequence_lane_id: str
    lane_binding_sha256: str
    stream_authority_admission_sha256: str
    stream_authority_decision_sha256: str
    stream_authority_namespace: str
    stream_authority_decision_id: str
    closure_sha256: str


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ExecutorSequenceLaneAuthorityClosureError(message)


def _text(value: Any, field: str, max_len: int = 512) -> str:
    _need(isinstance(value, str), f"{field}:STRING_REQUIRED")
    normalized = value.strip()
    _need(bool(normalized), f"{field}:NONEMPTY_STRING_REQUIRED")
    _need(normalized == value, f"{field}:NONCANONICAL_TEXT")
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
        raise ExecutorSequenceLaneAuthorityClosureError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _material(closure: ExecutorSequenceLaneAuthorityClosure) -> dict[str, Any]:
    data = asdict(closure)
    data.pop("closure_sha256", None)
    return data


def validate_executor_sequence_lane_authority_closure(
    closure: ExecutorSequenceLaneAuthorityClosure,
) -> None:
    if not isinstance(closure, ExecutorSequenceLaneAuthorityClosure):
        raise ExecutorSequenceLaneAuthorityClosureError("EXECUTOR_SEQUENCE_LANE_AUTHORITY_CLOSURE_REQUIRED")
    _need(closure.schema == SCHEMA, "EXECUTOR_SEQUENCE_LANE_AUTHORITY_CLOSURE_SCHEMA_UNSUPPORTED")
    _need(
        closure.canonicalization_schema == CANONICALIZATION_SCHEMA,
        "EXECUTOR_SEQUENCE_LANE_AUTHORITY_CLOSURE_CANONICALIZATION_SCHEMA_UNSUPPORTED",
    )
    _need(closure.lane_schema == LANE_SCHEMA, "EXECUTOR_SEQUENCE_LANE_SCHEMA_MISMATCH")
    _need(closure.lane_binding_schema == LANE_BINDING_SCHEMA, "EXECUTOR_SEQUENCE_LANE_BINDING_SCHEMA_MISMATCH")
    _generation(closure.generation)
    for field, max_len in (
        ("executor_id", 256),
        ("source_kind", 128),
        ("source_id", 512),
        ("stream_id", 512),
        ("role", 256),
        ("stream_authority_namespace", 256),
        ("stream_authority_decision_id", 512),
    ):
        _text(getattr(closure, field), field, max_len)
    for field in (
        "sequence_lane_id",
        "lane_binding_sha256",
        "stream_authority_admission_sha256",
        "stream_authority_decision_sha256",
        "closure_sha256",
    ):
        _sha256(getattr(closure, field), field)
    expected = _canonical_sha256(_material(closure), "EXECUTOR_SEQUENCE_LANE_AUTHORITY_CLOSURE")
    _need(closure.closure_sha256 == expected, "EXECUTOR_SEQUENCE_LANE_AUTHORITY_CLOSURE_DIGEST_MISMATCH")


def close_executor_sequence_lane_authority(
    db: sqlite3.Connection,
    lane_binding: ExecutorSequenceLaneBinding,
    *,
    current_generation: int,
) -> ExecutorSequenceLaneAuthorityClosure:
    """Bind one existing lane binding to stream authority read from canonical MiniUnifiedDB."""
    _need(isinstance(db, sqlite3.Connection), "SQLITE_CONNECTION_REQUIRED")
    current_generation = _generation(current_generation)
    try:
        validate_executor_sequence_lane_binding(lane_binding)
    except ExecutorSequenceLaneError as exc:
        raise ExecutorSequenceLaneAuthorityClosureError(f"EXECUTOR_SEQUENCE_LANE_REJECTED:{exc}") from exc
    _need(lane_binding.generation == current_generation, "EXECUTOR_SEQUENCE_LANE_GENERATION_MISMATCH")

    try:
        admission = read_entry_stream_authority_admission(
            db,
            current_generation=current_generation,
            source_kind=lane_binding.source_kind,
            source_id=lane_binding.source_id,
            stream_id=lane_binding.stream_id,
        )
        validate_entry_stream_authority_admission(admission)
    except EntryStreamAuthorityError as exc:
        raise ExecutorSequenceLaneAuthorityClosureError(f"EXECUTOR_SEQUENCE_STREAM_AUTHORITY_UNAVAILABLE:{exc}") from exc

    checks = {
        "generation": (lane_binding.generation, admission.generation),
        "source_kind": (lane_binding.source_kind, admission.source_kind),
        "source_id": (lane_binding.source_id, admission.source_id),
        "stream_id": (lane_binding.stream_id, admission.stream_id),
    }
    for field, (left, right) in checks.items():
        _need(left == right, f"EXECUTOR_SEQUENCE_STREAM_AUTHORITY_MISMATCH:{field}")

    material = {
        "schema": SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "lane_schema": LANE_SCHEMA,
        "lane_binding_schema": LANE_BINDING_SCHEMA,
        "generation": current_generation,
        "executor_id": _text(lane_binding.executor_id, "executor_id", 256),
        "source_kind": _text(lane_binding.source_kind, "source_kind", 128),
        "source_id": _text(lane_binding.source_id, "source_id", 512),
        "stream_id": _text(lane_binding.stream_id, "stream_id", 512),
        "role": _text(lane_binding.role, "role", 256),
        "sequence_lane_id": _sha256(lane_binding.sequence_lane_id, "sequence_lane_id"),
        "lane_binding_sha256": _sha256(lane_binding.binding_sha256, "lane_binding_sha256"),
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
    }
    return ExecutorSequenceLaneAuthorityClosure(
        **material,
        closure_sha256=_canonical_sha256(material, "EXECUTOR_SEQUENCE_LANE_AUTHORITY_CLOSURE"),
    )


def revalidate_executor_sequence_lane_authority_closure(
    db: sqlite3.Connection,
    closure: ExecutorSequenceLaneAuthorityClosure,
    lane_binding: ExecutorSequenceLaneBinding,
    *,
    current_generation: int,
) -> None:
    """Re-read canonical stream authority and require exact closure reproduction."""
    validate_executor_sequence_lane_authority_closure(closure)
    expected = close_executor_sequence_lane_authority(
        db,
        lane_binding,
        current_generation=current_generation,
    )
    _need(
        closure == expected,
        "EXECUTOR_SEQUENCE_LANE_AUTHORITY_CLOSURE_SOURCE_REVALIDATION_MISMATCH",
    )


__all__ = [
    "SCHEMA",
    "ExecutorSequenceLaneAuthorityClosureError",
    "ExecutorSequenceLaneAuthorityClosure",
    "close_executor_sequence_lane_authority",
    "validate_executor_sequence_lane_authority_closure",
    "revalidate_executor_sequence_lane_authority_closure",
]
