#!/usr/bin/env python3
"""Deterministic ORTHOGONAL_SAME_NORM control for EntityOS/HCU J-Space.

This module emits a source-level control-generation receipt only. It does not
create a second J-Space packet wire, canonical state authority, model-runtime
receipt, or causal credit. Downstream execution must bind the exact emitted
vector digest and an invocation-owned hook/runtime receipt.

The construction is deterministic: choose the canonical coordinate axis least
aligned with the source vector, project that axis onto the source-orthogonal
subspace, then rescale to the source L2 norm. The emitted receipt records both
same-norm and orthogonality error bounds.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Any, Sequence

try:
    from .entry_canonicalization_v1 import CanonicalizationError, canonicalize
except ImportError:
    from entry_canonicalization_v1 import CanonicalizationError, canonicalize

SCHEMA = "ENTITYOS_HCU_JSPACE_ORTHOGONAL_SAME_NORM/v1"
GENERATOR = "CANONICAL_AXIS_GRAM_SCHMIDT_L2_MATCH/v1"
CONTROL_LABEL = "ORTHOGONAL_SAME_NORM"
MAX_DIMENSION = 4096
MAX_RELATIVE_L2_ERROR = 1e-12
MAX_ABS_COSINE = 1e-12


class MatchedOrthogonalControlError(ValueError):
    pass


@dataclass(frozen=True)
class MatchedOrthogonalDirection:
    schema: str
    generator: str
    control_label: str
    dimension: int
    source_vector_sha256: str
    matched_vector_sha256: str
    canonical_axis: int
    source_l2_norm: float
    matched_l2_norm: float
    relative_l2_error: float
    dot_product: float
    abs_cosine: float
    vector: tuple[float, ...]


def _finite(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MatchedOrthogonalControlError(f"{field}:FINITE_BINARY64_REQUIRED")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise MatchedOrthogonalControlError(f"{field}:FINITE_BINARY64_REQUIRED") from exc
    if not math.isfinite(number):
        raise MatchedOrthogonalControlError(f"{field}:FINITE_BINARY64_REQUIRED")
    if isinstance(value, int) and int(number) != value:
        raise MatchedOrthogonalControlError(f"{field}:EXACT_BINARY64_REQUIRED")
    return 0.0 if number == 0.0 else number


def _vector(values: Sequence[Any]) -> tuple[float, ...]:
    if isinstance(values, (str, bytes, bytearray)) or not isinstance(values, Sequence):
        raise MatchedOrthogonalControlError("source_vector:SEQUENCE_REQUIRED")
    if not 2 <= len(values) <= MAX_DIMENSION:
        raise MatchedOrthogonalControlError(
            f"source_vector:DIMENSION_2_TO_{MAX_DIMENSION}_REQUIRED"
        )
    return tuple(_finite(value, f"source_vector[{index}]") for index, value in enumerate(values))


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        raw = canonicalize(value)
    except CanonicalizationError as exc:
        raise MatchedOrthogonalControlError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(raw).hexdigest()


def derive_matched_orthogonal_direction(
    source_vector: Sequence[Any],
) -> MatchedOrthogonalDirection:
    """Return one deterministic vector orthogonal to source with equal L2 norm."""
    source = _vector(source_vector)
    source_norm = math.hypot(*source)
    if not math.isfinite(source_norm) or source_norm == 0.0:
        raise MatchedOrthogonalControlError("source_vector:POSITIVE_FINITE_L2_NORM_REQUIRED")
    norm_sq = sum(value * value for value in source)
    if not math.isfinite(norm_sq) or norm_sq == 0.0:
        raise MatchedOrthogonalControlError("source_vector:FINITE_NORM_SQUARED_REQUIRED")

    # Stable tie break on index makes the construction host-RNG independent.
    axes = sorted(range(len(source)), key=lambda index: (abs(source[index]), index))
    candidate: tuple[float, ...] | None = None
    chosen_axis: int | None = None
    for axis in axes:
        coefficient = source[axis] / norm_sq
        raw = [-(coefficient * value) for value in source]
        raw[axis] += 1.0
        raw_tuple = tuple(0.0 if value == 0.0 else value for value in raw)
        raw_norm = math.hypot(*raw_tuple)
        if math.isfinite(raw_norm) and raw_norm > 1e-15:
            candidate = raw_tuple
            chosen_axis = axis
            break
    if candidate is None or chosen_axis is None:
        raise MatchedOrthogonalControlError("ORTHOGONAL_DIRECTION_DEGENERATE")

    candidate_norm = math.hypot(*candidate)
    scale = source_norm / candidate_norm
    matched = tuple(0.0 if value * scale == 0.0 else value * scale for value in candidate)
    matched_norm = math.hypot(*matched)
    if not math.isfinite(matched_norm) or matched_norm == 0.0:
        raise MatchedOrthogonalControlError("ORTHOGONAL_MATCHED_VECTOR_NONFINITE_OR_ZERO")

    dot = sum(a * b for a, b in zip(source, matched))
    relative_error = abs(matched_norm - source_norm) / source_norm
    abs_cosine = abs(dot) / (source_norm * matched_norm)
    if relative_error > MAX_RELATIVE_L2_ERROR:
        raise MatchedOrthogonalControlError("ORTHOGONAL_EQUAL_L2_TOLERANCE_EXCEEDED")
    if abs_cosine > MAX_ABS_COSINE:
        raise MatchedOrthogonalControlError("ORTHOGONAL_DOT_TOLERANCE_EXCEEDED")

    return MatchedOrthogonalDirection(
        schema=SCHEMA,
        generator=GENERATOR,
        control_label=CONTROL_LABEL,
        dimension=len(source),
        source_vector_sha256=_canonical_sha256(list(source), "SOURCE_VECTOR"),
        matched_vector_sha256=_canonical_sha256(list(matched), "ORTHOGONAL_VECTOR"),
        canonical_axis=chosen_axis,
        source_l2_norm=source_norm,
        matched_l2_norm=matched_norm,
        relative_l2_error=relative_error,
        dot_product=dot,
        abs_cosine=abs_cosine,
        vector=matched,
    )


def validate_matched_orthogonal_direction(
    source_vector: Sequence[Any],
    receipt: MatchedOrthogonalDirection,
) -> None:
    if not isinstance(receipt, MatchedOrthogonalDirection):
        raise MatchedOrthogonalControlError("MATCHED_ORTHOGONAL_DIRECTION_RECEIPT_REQUIRED")
    if receipt.schema != SCHEMA or receipt.generator != GENERATOR or receipt.control_label != CONTROL_LABEL:
        raise MatchedOrthogonalControlError("MATCHED_ORTHOGONAL_SCHEMA_OR_GENERATOR_MISMATCH")
    expected = derive_matched_orthogonal_direction(source_vector)
    if receipt != expected:
        raise MatchedOrthogonalControlError("MATCHED_ORTHOGONAL_REPLAY_MISMATCH")


__all__ = [
    "SCHEMA",
    "GENERATOR",
    "CONTROL_LABEL",
    "MAX_RELATIVE_L2_ERROR",
    "MAX_ABS_COSINE",
    "MatchedOrthogonalControlError",
    "MatchedOrthogonalDirection",
    "derive_matched_orthogonal_direction",
    "validate_matched_orthogonal_direction",
]
