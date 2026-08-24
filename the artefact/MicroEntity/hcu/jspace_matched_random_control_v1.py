#!/usr/bin/env python3
"""Deterministic matched-norm random-direction primitive for EntityOS/HCU J-Space.

This module closes one *source-level* part of the causal-steering control gap without
creating a second J-Space wire. It generates an independently oriented random direction
from only ``family_id``, ``seed`` and ``dimension``, then rescales it to the source
vector's L2 norm. The source vector's orientation/content is never used to choose the
random direction.

The result is a candidate/control-generation receipt, not canonical truth, hidden-state
evidence, effect authority, model-runtime credit, or a JSPACE_VECTOR_CONTROL_ABI packet.
Until the single canonical ABI explicitly admits ``MATCHED_RANDOM``, callers MUST NOT
launder this vector through BASELINE, PERMUTED or another existing condition label.

Reproducibility is exact only at the bound Python/runtime/math-library identity because
the Gaussian transform uses libm transcendental functions. The emitted vector itself is
hash-bound, so downstream execution must bind the exact emitted vector digest rather than
silently regenerating it under a different runtime.
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

SCHEMA = "ENTITYOS_HCU_JSPACE_MATCHED_RANDOM_DIRECTION/v1"
GENERATOR = "SHA256_BOX_MULLER_GAUSSIAN_L2_MATCH/v1"
REQUIRED_CANONICAL_CONTROL_CONDITION = "MATCHED_RANDOM"
ABI_BLOCK_STATUS = "BLOCKED_UNTIL_SINGLE_JSPACE_VECTOR_CONTROL_ABI_ADMITS_MATCHED_RANDOM"
MAX_DIMENSION = 4096
MAX_FAMILY_ID_CHARS = 512
MAX_SAFE_IJSON_INT = 9_007_199_254_740_991
MAX_RELATIVE_L2_ERROR = 1e-12


class MatchedRandomControlError(ValueError):
    pass


@dataclass(frozen=True)
class MatchedRandomDirection:
    schema: str
    generator: str
    family_id: str
    seed: int
    dimension: int
    source_vector_sha256: str
    raw_direction_sha256: str
    matched_vector_sha256: str
    source_l2_norm: float
    matched_l2_norm: float
    relative_l2_error: float
    vector: tuple[float, ...]


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MatchedRandomControlError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > MAX_FAMILY_ID_CHARS:
        raise MatchedRandomControlError(f"{field}:TOO_LONG")
    return value


def _seed(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_SAFE_IJSON_INT:
        raise MatchedRandomControlError("seed:NONNEGATIVE_IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _finite(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MatchedRandomControlError(f"{field}:FINITE_BINARY64_REQUIRED")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise MatchedRandomControlError(f"{field}:FINITE_BINARY64_REQUIRED") from exc
    if not math.isfinite(number):
        raise MatchedRandomControlError(f"{field}:FINITE_BINARY64_REQUIRED")
    return 0.0 if number == 0.0 else number


def _vector(values: Sequence[Any], field: str = "source_vector") -> tuple[float, ...]:
    if isinstance(values, (str, bytes, bytearray)) or not isinstance(values, Sequence):
        raise MatchedRandomControlError(f"{field}:SEQUENCE_REQUIRED")
    if not 2 <= len(values) <= MAX_DIMENSION:
        raise MatchedRandomControlError(f"{field}:DIMENSION_2_TO_{MAX_DIMENSION}_REQUIRED")
    return tuple(_finite(value, f"{field}[{index}]") for index, value in enumerate(values))


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        encoded = canonicalize(value)
    except CanonicalizationError as exc:
        raise MatchedRandomControlError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(encoded).hexdigest()


def _open_unit_from_u64(value: int) -> float:
    """Map 64 deterministic bits into strict (0, 1) using a 53-bit binary64 mantissa."""
    mantissa = value >> 11
    return (mantissa + 1) / ((1 << 53) + 1)


def _gaussian_direction(*, family_id: str, seed: int, dimension: int) -> tuple[float, ...]:
    domain = canonicalize({
        "schema": SCHEMA,
        "generator": GENERATOR,
        "family_id": family_id,
        "seed": seed,
        "dimension": dimension,
    })
    values: list[float] = []
    pair_index = 0
    while len(values) < dimension:
        digest = hashlib.sha256(
            b"ENTITYOS_HCU_MATCHED_RANDOM\x00" + domain + pair_index.to_bytes(8, "big")
        ).digest()
        u1 = _open_unit_from_u64(int.from_bytes(digest[:8], "big"))
        u2 = _open_unit_from_u64(int.from_bytes(digest[8:16], "big"))
        radius = math.sqrt(-2.0 * math.log(u1))
        angle = math.tau * u2
        values.append(radius * math.cos(angle))
        if len(values) < dimension:
            values.append(radius * math.sin(angle))
        pair_index += 1
    result = tuple(0.0 if value == 0.0 else value for value in values)
    raw_norm = math.hypot(*result)
    if not math.isfinite(raw_norm) or raw_norm == 0.0:
        raise MatchedRandomControlError("RANDOM_DIRECTION_DEGENERATE")
    return result


def derive_matched_random_direction(
    source_vector: Sequence[Any],
    *,
    family_id: str,
    seed: int,
) -> MatchedRandomDirection:
    """Generate a source-orientation-independent Gaussian direction matched in L2 norm."""
    source = _vector(source_vector)
    family = _text(family_id, "family_id")
    seed_value = _seed(seed)
    source_norm = math.hypot(*source)
    if not math.isfinite(source_norm) or source_norm == 0.0:
        raise MatchedRandomControlError("source_vector:POSITIVE_FINITE_L2_NORM_REQUIRED")

    raw = _gaussian_direction(family_id=family, seed=seed_value, dimension=len(source))
    raw_norm = math.hypot(*raw)
    scale = source_norm / raw_norm
    matched = tuple(0.0 if value * scale == 0.0 else value * scale for value in raw)
    matched_norm = math.hypot(*matched)
    if not math.isfinite(matched_norm) or matched_norm == 0.0:
        raise MatchedRandomControlError("MATCHED_RANDOM_DIRECTION_NONFINITE_OR_ZERO")
    relative_error = abs(matched_norm - source_norm) / source_norm
    if relative_error > MAX_RELATIVE_L2_ERROR:
        raise MatchedRandomControlError("MATCHED_RANDOM_L2_TOLERANCE_EXCEEDED")

    return MatchedRandomDirection(
        schema=SCHEMA,
        generator=GENERATOR,
        family_id=family,
        seed=seed_value,
        dimension=len(source),
        source_vector_sha256=_canonical_sha256(list(source), "SOURCE_VECTOR"),
        raw_direction_sha256=_canonical_sha256(list(raw), "RAW_RANDOM_DIRECTION"),
        matched_vector_sha256=_canonical_sha256(list(matched), "MATCHED_RANDOM_DIRECTION"),
        source_l2_norm=source_norm,
        matched_l2_norm=matched_norm,
        relative_l2_error=relative_error,
        vector=matched,
    )


def validate_matched_random_direction(
    source_vector: Sequence[Any],
    receipt: MatchedRandomDirection,
) -> None:
    """Fail closed unless a receipt exactly replays at the currently bound runtime identity."""
    if not isinstance(receipt, MatchedRandomDirection):
        raise MatchedRandomControlError("MATCHED_RANDOM_DIRECTION_RECEIPT_REQUIRED")
    if receipt.schema != SCHEMA or receipt.generator != GENERATOR:
        raise MatchedRandomControlError("MATCHED_RANDOM_DIRECTION_SCHEMA_OR_GENERATOR_MISMATCH")
    expected = derive_matched_random_direction(
        source_vector,
        family_id=receipt.family_id,
        seed=receipt.seed,
    )
    if receipt != expected:
        raise MatchedRandomControlError("MATCHED_RANDOM_DIRECTION_REPLAY_MISMATCH")


def canonical_abi_admission_status(control_conditions: Sequence[str] | set[str] | frozenset[str]) -> str:
    """Report whether the *single* canonical vector-control ABI has admitted this label."""
    try:
        admitted = REQUIRED_CANONICAL_CONTROL_CONDITION in control_conditions
    except TypeError as exc:
        raise MatchedRandomControlError("control_conditions:CONTAINER_REQUIRED") from exc
    return "ADMITTED_BY_SINGLE_CANONICAL_ABI" if admitted else ABI_BLOCK_STATUS


__all__ = [
    "SCHEMA",
    "GENERATOR",
    "REQUIRED_CANONICAL_CONTROL_CONDITION",
    "ABI_BLOCK_STATUS",
    "MAX_RELATIVE_L2_ERROR",
    "MatchedRandomControlError",
    "MatchedRandomDirection",
    "derive_matched_random_direction",
    "validate_matched_random_direction",
    "canonical_abi_admission_status",
]
