#!/usr/bin/env python3
"""Model-bound J-Space -> residual-activation basis for direct EntityOS/HCU steering.

A Global J-Space vector and a model residual stream are different coordinate systems.  This
module prevents an arbitrary dimensional padding/truncation from masquerading as direct
J-Space control.  It builds a model/layer-specific linear basis from contrastive activation
capture pairs and projects an exact validated ``JSPACE_VECTOR_CONTROL_ABI/v1`` packet through
that basis into the model hidden dimension.

Calibration method: for each J-Space axis, average (positive - negative) residual activation
vectors from paired examples at one exact model/layer identity, then L2-normalize the mean
direction.  This is the standard contrastive-activation-addition family of construction, but
this implementation's evidence and identities remain local to EntityOS/HCU.

Source/calibration structure alone grants no runtime, hidden-state-causality, truth, effect or
training credit.  Positive steering still requires a real hook receipt plus sign/zero controls.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Any, Mapping, Sequence

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .jspace_vector_control_v1 import VectorControlPacket, decode_vector, validate_packet
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from jspace_vector_control_v1 import VectorControlPacket, decode_vector, validate_packet

BASIS_SCHEMA = "HCU_MODEL_JSPACE_ACTIVATION_BASIS/v1"
CAPTURE_SCHEMA = "HCU_MODEL_ACTIVATION_CAPTURE/v1"
PROJECTION_SCHEMA = "HCU_JSPACE_MODEL_ACTIVATION_PROJECTION/v1"
MAX_HIDDEN_SIZE = 65536
MAX_AXES = 4096


class JSpaceModelActivationBasisError(ValueError):
    pass


@dataclass(frozen=True)
class ActivationCapture:
    schema: str
    model_artifact_sha256: str
    tokenizer_artifact_sha256: str
    runtime_build_sha256: str
    layer_id: str
    prompt_family_id: str
    prompt_polarity: str
    seed: int
    activation: tuple[float, ...]
    activation_sha256: str


@dataclass(frozen=True)
class BasisAxis:
    axis_id: str
    pair_family_ids: tuple[str, ...]
    direction: tuple[float, ...]
    direction_sha256: str


@dataclass(frozen=True)
class ModelJSpaceActivationBasis:
    schema: str
    canonicalization_schema: str
    basis_id: str
    model_artifact_sha256: str
    tokenizer_artifact_sha256: str
    runtime_build_sha256: str
    layer_id: str
    hidden_size: int
    axes: tuple[BasisAxis, ...]
    basis_sha256: str


@dataclass(frozen=True)
class ModelActivationProjection:
    schema: str
    basis_id: str
    basis_sha256: str
    vector_control_packet_sha256: str
    layer_id: str
    hidden_size: int
    hidden_vector: tuple[float, ...]
    hidden_vector_sha256: str
    projection_sha256: str


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise JSpaceModelActivationBasisError(message)


def _text(value: Any, field: str, max_len: int = 1024) -> str:
    _need(isinstance(value, str) and bool(value.strip()), f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
    _need(value == normalized, f"{field}:NONCANONICAL_TEXT")
    _need(len(normalized) <= max_len, f"{field}:TOO_LONG")
    return normalized


def _sha(value: Any, field: str) -> str:
    value = _text(value, field, 64)
    _need(len(value) == 64 and value.lower() == value and all(ch in "0123456789abcdef" for ch in value), f"{field}:LOWERCASE_SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _finite(value: Any, field: str) -> float:
    _need(not isinstance(value, bool) and isinstance(value, (int, float)), f"{field}:FINITE_NUMBER_REQUIRED")
    value = float(value)
    _need(math.isfinite(value), f"{field}:FINITE_NUMBER_REQUIRED")
    return 0.0 if value == 0.0 else value


def _vector(values: Sequence[Any], field: str, *, expected: int | None = None) -> tuple[float, ...]:
    _need(not isinstance(values, (str, bytes, bytearray)) and isinstance(values, Sequence), f"{field}:SEQUENCE_REQUIRED")
    _need(1 <= len(values) <= MAX_HIDDEN_SIZE, f"{field}:DIMENSION_OUT_OF_RANGE")
    if expected is not None:
        _need(len(values) == expected, f"{field}:DIMENSION_MISMATCH")
    return tuple(_finite(value, f"{field}[{index}]") for index, value in enumerate(values))


def _canonical_sha(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise JSpaceModelActivationBasisError(f"{field}:CANONICALIZATION_FAILED") from exc


def _capture_material(capture: ActivationCapture) -> dict[str, Any]:
    data = asdict(capture)
    data.pop("activation_sha256", None)
    data["activation"] = list(capture.activation)
    return data


def validate_capture(capture: ActivationCapture) -> None:
    _need(isinstance(capture, ActivationCapture), "ACTIVATION_CAPTURE_REQUIRED")
    _need(capture.schema == CAPTURE_SCHEMA, "ACTIVATION_CAPTURE_SCHEMA_UNSUPPORTED")
    for value, field in (
        (capture.model_artifact_sha256, "model_artifact_sha256"),
        (capture.tokenizer_artifact_sha256, "tokenizer_artifact_sha256"),
        (capture.runtime_build_sha256, "runtime_build_sha256"),
    ):
        _sha(value, field)
    _text(capture.layer_id, "layer_id", 128)
    _text(capture.prompt_family_id, "prompt_family_id", 256)
    _need(capture.prompt_polarity in {"POSITIVE", "NEGATIVE"}, "prompt_polarity:UNSUPPORTED")
    _need(not isinstance(capture.seed, bool) and isinstance(capture.seed, int) and capture.seed >= 0, "seed:NONNEGATIVE_INTEGER_REQUIRED")
    _vector(capture.activation, "activation")
    _need(_sha(capture.activation_sha256, "activation_sha256") == _canonical_sha(_capture_material(capture), "ACTIVATION_CAPTURE"), "ACTIVATION_CAPTURE_DIGEST_MISMATCH")


def build_capture(
    activation: Sequence[float],
    *,
    model_artifact_sha256: str,
    tokenizer_artifact_sha256: str,
    runtime_build_sha256: str,
    layer_id: str,
    prompt_family_id: str,
    prompt_polarity: str,
    seed: int,
) -> ActivationCapture:
    normalized = _vector(activation, "activation")
    material = {
        "schema": CAPTURE_SCHEMA,
        "model_artifact_sha256": _sha(model_artifact_sha256, "model_artifact_sha256"),
        "tokenizer_artifact_sha256": _sha(tokenizer_artifact_sha256, "tokenizer_artifact_sha256"),
        "runtime_build_sha256": _sha(runtime_build_sha256, "runtime_build_sha256"),
        "layer_id": _text(layer_id, "layer_id", 128),
        "prompt_family_id": _text(prompt_family_id, "prompt_family_id", 256),
        "prompt_polarity": prompt_polarity,
        "seed": seed,
        "activation": list(normalized),
    }
    _need(prompt_polarity in {"POSITIVE", "NEGATIVE"}, "prompt_polarity:UNSUPPORTED")
    _need(not isinstance(seed, bool) and isinstance(seed, int) and seed >= 0, "seed:NONNEGATIVE_INTEGER_REQUIRED")
    digest = _canonical_sha(material, "ACTIVATION_CAPTURE")
    return ActivationCapture(**{**material, "activation": normalized}, activation_sha256=digest)


def _unit_direction(values: Sequence[float]) -> tuple[float, ...]:
    vector = _vector(values, "direction")
    norm = math.sqrt(sum(value * value for value in vector))
    _need(math.isfinite(norm) and norm > 0.0, "CONTRASTIVE_DIRECTION_ZERO_OR_NONFINITE")
    return tuple(value / norm for value in vector)


def _axis_material(axis: BasisAxis) -> dict[str, Any]:
    return {
        "axis_id": axis.axis_id,
        "pair_family_ids": list(axis.pair_family_ids),
        "direction": list(axis.direction),
    }


def calibrate_basis(
    axis_pairs: Mapping[str, Sequence[tuple[ActivationCapture, ActivationCapture]]],
    *,
    basis_id: str,
) -> ModelJSpaceActivationBasis:
    """Build one exact model/layer basis from paired positive-minus-negative captures."""
    _need(isinstance(axis_pairs, Mapping) and axis_pairs, "AXIS_PAIRS_REQUIRED")
    _need(len(axis_pairs) <= MAX_AXES, "AXIS_COUNT_OUT_OF_RANGE")
    basis_id = _text(basis_id, "basis_id", 256)
    axes: list[BasisAxis] = []
    common_identity: tuple[str, str, str, str, int] | None = None

    for axis_id in sorted(axis_pairs):
        axis_id = _text(axis_id, "axis_id", 256)
        pairs = axis_pairs[axis_id]
        _need(isinstance(pairs, Sequence) and pairs, f"axis_pairs[{axis_id}]:NONEMPTY_SEQUENCE_REQUIRED")
        deltas: list[tuple[float, ...]] = []
        families: list[str] = []
        for positive, negative in pairs:
            validate_capture(positive)
            validate_capture(negative)
            _need(positive.prompt_polarity == "POSITIVE" and negative.prompt_polarity == "NEGATIVE", "CONTRASTIVE_PAIR_POLARITY_MISMATCH")
            _need(positive.prompt_family_id == negative.prompt_family_id, "CONTRASTIVE_PAIR_FAMILY_MISMATCH")
            _need(positive.seed == negative.seed, "CONTRASTIVE_PAIR_SEED_MISMATCH")
            identity = (
                positive.model_artifact_sha256,
                positive.tokenizer_artifact_sha256,
                positive.runtime_build_sha256,
                positive.layer_id,
                len(positive.activation),
            )
            negative_identity = (
                negative.model_artifact_sha256,
                negative.tokenizer_artifact_sha256,
                negative.runtime_build_sha256,
                negative.layer_id,
                len(negative.activation),
            )
            _need(identity == negative_identity, "CONTRASTIVE_PAIR_MODEL_LAYER_IDENTITY_MISMATCH")
            if common_identity is None:
                common_identity = identity
            _need(identity == common_identity, "BASIS_MODEL_LAYER_IDENTITY_MISMATCH")
            deltas.append(tuple(p - n for p, n in zip(positive.activation, negative.activation)))
            families.append(positive.prompt_family_id)
        _need(len(set(families)) == len(families), "CONTRASTIVE_PAIR_FAMILY_DUPLICATE")
        hidden_size = len(deltas[0])
        mean = tuple(sum(delta[index] for delta in deltas) / len(deltas) for index in range(hidden_size))
        direction = _unit_direction(mean)
        provisional = BasisAxis(axis_id, tuple(sorted(families)), direction, "1" * 64)
        direction_sha = _canonical_sha(_axis_material(provisional), "BASIS_AXIS")
        axes.append(BasisAxis(axis_id, provisional.pair_family_ids, direction, direction_sha))

    _need(common_identity is not None, "BASIS_IDENTITY_UNRESOLVED")
    model_sha, tokenizer_sha, runtime_sha, layer_id, hidden_size = common_identity
    material = {
        "schema": BASIS_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "basis_id": basis_id,
        "model_artifact_sha256": model_sha,
        "tokenizer_artifact_sha256": tokenizer_sha,
        "runtime_build_sha256": runtime_sha,
        "layer_id": layer_id,
        "hidden_size": hidden_size,
        "axes": [
            {
                "axis_id": axis.axis_id,
                "pair_family_ids": list(axis.pair_family_ids),
                "direction": list(axis.direction),
                "direction_sha256": axis.direction_sha256,
            }
            for axis in axes
        ],
    }
    basis_sha = _canonical_sha(material, "MODEL_JSPACE_ACTIVATION_BASIS")
    return ModelJSpaceActivationBasis(
        schema=BASIS_SCHEMA,
        canonicalization_schema=CANONICALIZATION_SCHEMA,
        basis_id=basis_id,
        model_artifact_sha256=model_sha,
        tokenizer_artifact_sha256=tokenizer_sha,
        runtime_build_sha256=runtime_sha,
        layer_id=layer_id,
        hidden_size=hidden_size,
        axes=tuple(axes),
        basis_sha256=basis_sha,
    )


def project_control_packet(
    packet: VectorControlPacket,
    basis: ModelJSpaceActivationBasis,
    *,
    current_generation: int,
    expected_role: str,
) -> ModelActivationProjection:
    """Project one exact J-Space control packet into the exact model residual basis."""
    _need(isinstance(basis, ModelJSpaceActivationBasis), "MODEL_JSPACE_BASIS_REQUIRED")
    validate_packet(packet)
    _need(packet.basis_id == basis.basis_id, "CONTROL_PACKET_MODEL_BASIS_ID_MISMATCH")
    _need(packet.basis_sha256 == basis.basis_sha256, "CONTROL_PACKET_MODEL_BASIS_SHA256_MISMATCH")
    coordinates = decode_vector(
        packet,
        current_generation=current_generation,
        expected_basis_id=basis.basis_id,
        expected_basis_sha256=basis.basis_sha256,
        expected_role=expected_role,
    )
    _need(len(coordinates) == len(basis.axes), "CONTROL_PACKET_BASIS_AXIS_DIMENSION_MISMATCH")
    hidden = [0.0] * basis.hidden_size
    for coordinate, axis in zip(coordinates, basis.axes):
        _need(len(axis.direction) == basis.hidden_size, "BASIS_AXIS_HIDDEN_SIZE_MISMATCH")
        for index, direction_value in enumerate(axis.direction):
            hidden[index] += coordinate * direction_value
    hidden_vector = tuple(_finite(value, f"hidden_vector[{index}]") for index, value in enumerate(hidden))
    hidden_sha = _canonical_sha(list(hidden_vector), "PROJECTED_HIDDEN_VECTOR")
    material = {
        "schema": PROJECTION_SCHEMA,
        "basis_id": basis.basis_id,
        "basis_sha256": basis.basis_sha256,
        "vector_control_packet_sha256": packet.packet_sha256,
        "layer_id": basis.layer_id,
        "hidden_size": basis.hidden_size,
        "hidden_vector_sha256": hidden_sha,
    }
    return ModelActivationProjection(
        **material,
        hidden_vector=hidden_vector,
        projection_sha256=_canonical_sha(material, "JSPACE_MODEL_ACTIVATION_PROJECTION"),
    )


__all__ = [
    "BASIS_SCHEMA",
    "CAPTURE_SCHEMA",
    "PROJECTION_SCHEMA",
    "ActivationCapture",
    "BasisAxis",
    "ModelJSpaceActivationBasis",
    "ModelActivationProjection",
    "JSpaceModelActivationBasisError",
    "build_capture",
    "validate_capture",
    "calibrate_basis",
    "project_control_packet",
]
