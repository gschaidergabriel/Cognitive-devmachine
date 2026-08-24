#!/usr/bin/env python3
"""Model-specific LatentBasisAdapter from canonical J-Space intent to local residual coordinates.

The synthetic steering result established an important boundary: the *semantic/control intent*
may be shared across model instances, but an unmodified residual vector does not reliably
transfer across independently initialized latent coordinate systems.  This module therefore
keeps two basis identities explicit:

    canonical Global J-Space basis
        -> JSPACE_LATENT_BASIS_ADAPTER/v1
        -> model/version/layer-specific local residual basis
        -> local JSPACE_VECTOR_CONTROL_ABI/v1 packet
        -> native model steering mechanism (for the retained Qwen3 lane: llama.cpp cvec)

The adapter is a deterministic calibrated artifact.  Each row maps one source J-Space axis to
one unit direction in the exact target model hidden dimension.  ``adapt_control_packet``
revalidates the source packet, performs the linear projection, then emits a NEW local control
packet whose basis SHA is the adapter SHA.  The source and local packet identities remain
separate and are both recorded in the adaptation receipt.

This module performs no model loading or inference and grants zero runtime/causal/training
credit by itself.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Any, Sequence

try:
    from .entry_canonicalization_v1 import CanonicalizationError, canonicalize
    from .jspace_vector_control_v1 import (
        VectorControlPacket,
        decode_vector,
        encode_vector,
        validate_packet,
    )
except ImportError:
    from entry_canonicalization_v1 import CanonicalizationError, canonicalize
    from jspace_vector_control_v1 import VectorControlPacket, decode_vector, encode_vector, validate_packet

ADAPTER_SCHEMA = "JSPACE_LATENT_BASIS_ADAPTER/v1"
ADAPTATION_SCHEMA = "ENTITYOS_HCU_JSPACE_LATENT_ADAPTATION/v1"
MAX_AXES = 4096
MAX_HIDDEN_SIZE = 65536
MAX_SAFE_INTEGER = 9_007_199_254_740_991
UNIT_TOLERANCE = 1e-6


class JSpaceLatentBasisAdapterError(ValueError):
    pass


@dataclass(frozen=True)
class LatentAxis:
    axis_id: str
    calibration_family_sha256: str
    direction: tuple[float, ...]
    direction_sha256: str


@dataclass(frozen=True)
class LatentBasisAdapter:
    schema: str
    source_jspace_basis_id: str
    source_jspace_basis_sha256: str
    local_basis_id: str
    checkpoint_sha256: str
    tokenizer_container_sha256: str
    runtime_source_commit: str
    runtime_build_sha256: str
    role: str
    n_embd: int
    n_layer: int
    il_start: int
    il_end: int
    calibration_dataset_sha256: str
    calibration_split_sha256: str
    holdout_split_sha256: str
    axes: tuple[LatentAxis, ...]
    adapter_sha256: str


@dataclass(frozen=True)
class LatentAdaptation:
    schema: str
    adapter_sha256: str
    source_packet_sha256: str
    source_basis_id: str
    source_basis_sha256: str
    local_packet_sha256: str
    local_basis_id: str
    local_basis_sha256: str
    checkpoint_sha256: str
    runtime_build_sha256: str
    role: str
    generation: int
    control_condition: str
    n_embd: int
    il_start: int
    il_end: int
    hidden_vector_sha256: str
    adaptation_sha256: str


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise JSpaceLatentBasisAdapterError(message)


def _text(value: Any, field: str, max_len: int = 1024) -> str:
    _need(isinstance(value, str) and bool(value.strip()), f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
    _need(value == normalized, f"{field}:NONCANONICAL_TEXT")
    _need(len(normalized) <= max_len, f"{field}:TOO_LONG")
    return normalized


def _sha(value: Any, field: str) -> str:
    value = _text(value, field, 64)
    _need(
        len(value) == 64
        and value.lower() == value
        and all(ch in "0123456789abcdef" for ch in value)
        and value not in {"0" * 64, "f" * 64},
        f"{field}:LOWERCASE_NONPLACEHOLDER_SHA256_REQUIRED",
    )
    return value


def _commit(value: Any) -> str:
    value = _text(value, "runtime_source_commit", 40)
    _need(
        len(value) == 40
        and value.lower() == value
        and all(ch in "0123456789abcdef" for ch in value)
        and value not in {"0" * 40, "f" * 40},
        "runtime_source_commit:LOWERCASE_NONPLACEHOLDER_GIT_SHA1_REQUIRED",
    )
    return value


def _positive_int(value: Any, field: str, maximum: int) -> int:
    _need(not isinstance(value, bool) and isinstance(value, int) and 1 <= value <= maximum, f"{field}:OUT_OF_RANGE")
    return value


def _finite(value: Any, field: str) -> float:
    _need(not isinstance(value, bool) and isinstance(value, (int, float)), f"{field}:FINITE_NUMBER_REQUIRED")
    value = float(value)
    _need(math.isfinite(value), f"{field}:FINITE_NUMBER_REQUIRED")
    return 0.0 if value == 0.0 else value


def _canonical_sha(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise JSpaceLatentBasisAdapterError(f"{field}:CANONICALIZATION_FAILED") from exc


def _direction(values: Sequence[Any], n_embd: int, field: str) -> tuple[float, ...]:
    _need(not isinstance(values, (str, bytes, bytearray)) and isinstance(values, Sequence), f"{field}:SEQUENCE_REQUIRED")
    _need(len(values) == n_embd, f"{field}:HIDDEN_DIMENSION_MISMATCH")
    normalized = tuple(_finite(value, f"{field}[{index}]") for index, value in enumerate(values))
    norm = math.sqrt(sum(value * value for value in normalized))
    _need(math.isfinite(norm) and abs(norm - 1.0) <= UNIT_TOLERANCE, f"{field}:UNIT_DIRECTION_REQUIRED")
    return normalized


def _axis_material(axis_id: str, family_sha: str, direction: Sequence[float]) -> dict[str, Any]:
    return {
        "axis_id": axis_id,
        "calibration_family_sha256": family_sha,
        "direction": list(direction),
    }


def _adapter_material(adapter: LatentBasisAdapter) -> dict[str, Any]:
    data = asdict(adapter)
    data.pop("adapter_sha256", None)
    data["axes"] = [
        {
            "axis_id": axis.axis_id,
            "calibration_family_sha256": axis.calibration_family_sha256,
            "direction": list(axis.direction),
            "direction_sha256": axis.direction_sha256,
        }
        for axis in adapter.axes
    ]
    return data


def build_latent_basis_adapter(
    axis_directions: Sequence[tuple[str, str, Sequence[float]]],
    *,
    source_jspace_basis_id: str,
    source_jspace_basis_sha256: str,
    local_basis_id: str,
    checkpoint_sha256: str,
    tokenizer_container_sha256: str,
    runtime_source_commit: str,
    runtime_build_sha256: str,
    role: str,
    n_embd: int,
    n_layer: int,
    il_start: int,
    il_end: int,
    calibration_dataset_sha256: str,
    calibration_split_sha256: str,
    holdout_split_sha256: str,
) -> LatentBasisAdapter:
    """Freeze an empirically calibrated source-axis -> target-residual mapping."""
    _need(isinstance(axis_directions, Sequence) and axis_directions, "AXIS_DIRECTIONS_REQUIRED")
    _need(len(axis_directions) <= MAX_AXES, "AXIS_COUNT_OUT_OF_RANGE")
    n_embd = _positive_int(n_embd, "n_embd", MAX_HIDDEN_SIZE)
    n_layer = _positive_int(n_layer, "n_layer", MAX_SAFE_INTEGER)
    _need(n_layer >= 2 and isinstance(il_start, int) and isinstance(il_end, int), "LAYER_RANGE_INVALID")
    _need(1 <= il_start <= il_end < n_layer, "LAYER_RANGE_INVALID")

    calibration_dataset_sha = _sha(calibration_dataset_sha256, "calibration_dataset_sha256")
    calibration_split_sha = _sha(calibration_split_sha256, "calibration_split_sha256")
    holdout_split_sha = _sha(holdout_split_sha256, "holdout_split_sha256")
    _need(calibration_split_sha != holdout_split_sha, "CALIBRATION_HOLDOUT_SPLIT_ALIAS")

    axes = []
    seen = set()
    for index, item in enumerate(axis_directions):
        _need(isinstance(item, tuple) and len(item) == 3, f"axis_directions[{index}]:TRIPLE_REQUIRED")
        axis_id = _text(item[0], f"axis_directions[{index}].axis_id", 256)
        _need(axis_id not in seen, "AXIS_ID_DUPLICATE")
        seen.add(axis_id)
        family_sha = _sha(item[1], f"axis_directions[{index}].calibration_family_sha256")
        direction = _direction(item[2], n_embd, f"axis_directions[{index}].direction")
        direction_sha = _canonical_sha(_axis_material(axis_id, family_sha, direction), "LATENT_AXIS")
        axes.append(LatentAxis(axis_id, family_sha, direction, direction_sha))

    material = {
        "schema": ADAPTER_SCHEMA,
        "source_jspace_basis_id": _text(source_jspace_basis_id, "source_jspace_basis_id", 256),
        "source_jspace_basis_sha256": _sha(source_jspace_basis_sha256, "source_jspace_basis_sha256"),
        "local_basis_id": _text(local_basis_id, "local_basis_id", 256),
        "checkpoint_sha256": _sha(checkpoint_sha256, "checkpoint_sha256"),
        "tokenizer_container_sha256": _sha(tokenizer_container_sha256, "tokenizer_container_sha256"),
        "runtime_source_commit": _commit(runtime_source_commit),
        "runtime_build_sha256": _sha(runtime_build_sha256, "runtime_build_sha256"),
        "role": _text(role, "role", 256),
        "n_embd": n_embd,
        "n_layer": n_layer,
        "il_start": il_start,
        "il_end": il_end,
        "calibration_dataset_sha256": calibration_dataset_sha,
        "calibration_split_sha256": calibration_split_sha,
        "holdout_split_sha256": holdout_split_sha,
        "axes": [
            {
                "axis_id": axis.axis_id,
                "calibration_family_sha256": axis.calibration_family_sha256,
                "direction": list(axis.direction),
                "direction_sha256": axis.direction_sha256,
            }
            for axis in axes
        ],
    }
    adapter_sha = _canonical_sha(material, "LATENT_BASIS_ADAPTER")
    return LatentBasisAdapter(
        schema=ADAPTER_SCHEMA,
        source_jspace_basis_id=material["source_jspace_basis_id"],
        source_jspace_basis_sha256=material["source_jspace_basis_sha256"],
        local_basis_id=material["local_basis_id"],
        checkpoint_sha256=material["checkpoint_sha256"],
        tokenizer_container_sha256=material["tokenizer_container_sha256"],
        runtime_source_commit=material["runtime_source_commit"],
        runtime_build_sha256=material["runtime_build_sha256"],
        role=material["role"],
        n_embd=n_embd,
        n_layer=n_layer,
        il_start=il_start,
        il_end=il_end,
        calibration_dataset_sha256=material["calibration_dataset_sha256"],
        calibration_split_sha256=material["calibration_split_sha256"],
        holdout_split_sha256=material["holdout_split_sha256"],
        axes=tuple(axes),
        adapter_sha256=adapter_sha,
    )


def validate_latent_basis_adapter(adapter: LatentBasisAdapter) -> None:
    _need(isinstance(adapter, LatentBasisAdapter), "LATENT_BASIS_ADAPTER_REQUIRED")
    _need(adapter.schema == ADAPTER_SCHEMA, "LATENT_BASIS_ADAPTER_SCHEMA_UNSUPPORTED")
    calibration_split_sha = _sha(adapter.calibration_split_sha256, "calibration_split_sha256")
    holdout_split_sha = _sha(adapter.holdout_split_sha256, "holdout_split_sha256")
    _need(calibration_split_sha != holdout_split_sha, "CALIBRATION_HOLDOUT_SPLIT_ALIAS")
    _need(1 <= len(adapter.axes) <= MAX_AXES, "AXIS_COUNT_OUT_OF_RANGE")
    seen = set()
    for axis in adapter.axes:
        _need(isinstance(axis, LatentAxis), "LATENT_AXIS_REQUIRED")
        _need(axis.axis_id not in seen, "AXIS_ID_DUPLICATE")
        seen.add(axis.axis_id)
        direction = _direction(axis.direction, adapter.n_embd, f"axis[{axis.axis_id}].direction")
        family_sha = _sha(axis.calibration_family_sha256, f"axis[{axis.axis_id}].calibration_family_sha256")
        expected = _canonical_sha(_axis_material(axis.axis_id, family_sha, direction), "LATENT_AXIS")
        _need(_sha(axis.direction_sha256, f"axis[{axis.axis_id}].direction_sha256") == expected, "LATENT_AXIS_DIGEST_MISMATCH")
    expected_adapter = _canonical_sha(_adapter_material(adapter), "LATENT_BASIS_ADAPTER")
    _need(_sha(adapter.adapter_sha256, "adapter_sha256") == expected_adapter, "LATENT_BASIS_ADAPTER_DIGEST_MISMATCH")


def adapt_control_packet(
    source_packet: VectorControlPacket,
    adapter: LatentBasisAdapter,
    *,
    current_generation: int,
) -> tuple[VectorControlPacket, LatentAdaptation]:
    """Project canonical J-Space coordinates into one exact local residual basis."""
    validate_latent_basis_adapter(adapter)
    validate_packet(source_packet)
    coordinates = decode_vector(
        source_packet,
        current_generation=current_generation,
        expected_basis_id=adapter.source_jspace_basis_id,
        expected_basis_sha256=adapter.source_jspace_basis_sha256,
        expected_role=adapter.role,
    )
    _need(len(coordinates) == len(adapter.axes), "SOURCE_JSPACE_DIMENSION_DOES_NOT_MATCH_ADAPTER_AXES")

    hidden = [0.0] * adapter.n_embd
    for coordinate, axis in zip(coordinates, adapter.axes):
        for index, component in enumerate(axis.direction):
            hidden[index] += coordinate * component
    hidden_vector = tuple(_finite(value, f"hidden_vector[{index}]") for index, value in enumerate(hidden))
    hidden_sha = _canonical_sha(list(hidden_vector), "LOCAL_HIDDEN_VECTOR")

    local_packet = encode_vector(
        hidden_vector,
        basis_id=adapter.local_basis_id,
        basis_sha256=adapter.adapter_sha256,
        generation=source_packet.generation,
        role=source_packet.role,
        control_condition=source_packet.control_condition,
    )
    material = {
        "schema": ADAPTATION_SCHEMA,
        "adapter_sha256": adapter.adapter_sha256,
        "source_packet_sha256": source_packet.packet_sha256,
        "source_basis_id": source_packet.basis_id,
        "source_basis_sha256": source_packet.basis_sha256,
        "local_packet_sha256": local_packet.packet_sha256,
        "local_basis_id": local_packet.basis_id,
        "local_basis_sha256": local_packet.basis_sha256,
        "checkpoint_sha256": adapter.checkpoint_sha256,
        "runtime_build_sha256": adapter.runtime_build_sha256,
        "role": source_packet.role,
        "generation": source_packet.generation,
        "control_condition": source_packet.control_condition,
        "n_embd": adapter.n_embd,
        "il_start": adapter.il_start,
        "il_end": adapter.il_end,
        "hidden_vector_sha256": hidden_sha,
    }
    receipt = LatentAdaptation(
        **material,
        adaptation_sha256=_canonical_sha(material, "LATENT_ADAPTATION"),
    )
    return local_packet, receipt


__all__ = [
    "ADAPTER_SCHEMA",
    "ADAPTATION_SCHEMA",
    "LatentAxis",
    "LatentBasisAdapter",
    "LatentAdaptation",
    "JSpaceLatentBasisAdapterError",
    "build_latent_basis_adapter",
    "validate_latent_basis_adapter",
    "adapt_control_packet",
]
