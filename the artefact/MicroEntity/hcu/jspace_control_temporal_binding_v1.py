#!/usr/bin/env python3
"""Fail-closed temporal identity edge for recurrent EntityOS/HCU J-Space control.

This primitive closes one source-level causality gap only:

    predecessor TrainingTrace(t)
      -> exact JSPACE_VECTOR_CONTROL packet(t)
      -> exact HCU_MODEL_INPUT_CONTROL_BINDING/v1
      -> controlled model invocation(t+1)

It deliberately does NOT claim that the successor model used the control packet internally,
does NOT validate successor execution/inference/J-Space receipts, and does NOT establish a
counterfactual effect. Those remain later promotion gates. Canonical state/effect authority
also remains outside this module.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .jspace_training_trace_v1 import TrainingTrace, validate_training_trace
    from .model_input_control_binding_v1 import (
        ModelInputControlBinding,
        validate_model_input_control_binding,
    )
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from jspace_training_trace_v1 import TrainingTrace, validate_training_trace
    from model_input_control_binding_v1 import (
        ModelInputControlBinding,
        validate_model_input_control_binding,
    )

TEMPORAL_BINDING_SCHEMA = "HCU_JSPACE_CONTROL_TEMPORAL_BINDING/v1"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class JSpaceControlTemporalBindingError(ValueError):
    pass


@dataclass(frozen=True)
class JSpaceControlTemporalBinding:
    schema: str
    canonicalization_schema: str
    generation: int
    predecessor_step_index: int
    controlled_step_index: int
    predecessor_trace_id: str
    predecessor_trace_family_id: str
    predecessor_trace_sha256: str
    control_packet_sha256: str
    model_input_control_binding_sha256: str
    controlled_invocation_id: str
    temporal_binding_sha256: str


def _text(value: Any, field: str, max_len: int = 8192) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceControlTemporalBindingError(f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
    if len(normalized) > max_len:
        raise JSpaceControlTemporalBindingError(f"{field}:TOO_LONG")
    return normalized


def _canonical_text(value: Any, field: str, max_len: int = 8192) -> str:
    normalized = _text(value, field, max_len)
    if value != normalized:
        raise JSpaceControlTemporalBindingError(f"{field}:NONCANONICAL_TEXT")
    return normalized


def _sha256(value: Any, field: str) -> str:
    normalized = _text(value, field, 64)
    if value != normalized:
        raise JSpaceControlTemporalBindingError(f"{field}:NONCANONICAL_SHA256")
    if len(normalized) != 64 or normalized.lower() != normalized or any(
        ch not in "0123456789abcdef" for ch in normalized
    ):
        raise JSpaceControlTemporalBindingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if normalized in {"0" * 64, "f" * 64}:
        raise JSpaceControlTemporalBindingError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return normalized


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceControlTemporalBindingError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > MAX_SAFE_INTEGER:
        raise JSpaceControlTemporalBindingError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        raw = canonicalize(value)
    except CanonicalizationError as exc:
        raise JSpaceControlTemporalBindingError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(raw).hexdigest()


def _material(binding: JSpaceControlTemporalBinding) -> dict[str, Any]:
    data = asdict(binding)
    data.pop("temporal_binding_sha256", None)
    return data


def _validate_source_edge(
    predecessor_trace: TrainingTrace,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    *,
    generation: int,
    predecessor_step_index: int,
    controlled_step_index: int,
    controlled_invocation_id: str,
) -> None:
    try:
        validate_training_trace(predecessor_trace)
    except Exception as exc:
        raise JSpaceControlTemporalBindingError(f"PREDECESSOR_TRACE_REJECTED:{exc}") from exc
    try:
        validate_model_input_control_binding(input_binding, consumed_input_bytes)
    except Exception as exc:
        raise JSpaceControlTemporalBindingError(f"MODEL_INPUT_CONTROL_BINDING_REJECTED:{exc}") from exc

    generation = _integer(generation, "generation")
    predecessor_step_index = _integer(predecessor_step_index, "predecessor_step_index")
    controlled_step_index = _integer(controlled_step_index, "controlled_step_index")
    if predecessor_step_index >= MAX_SAFE_INTEGER or controlled_step_index != predecessor_step_index + 1:
        raise JSpaceControlTemporalBindingError("TEMPORAL_SUCCESSOR_EXACTLY_ONE_STEP_REQUIRED")

    controlled_invocation_id = _canonical_text(controlled_invocation_id, "controlled_invocation_id", 256)
    if predecessor_trace.generation != generation or input_binding.generation != generation:
        raise JSpaceControlTemporalBindingError("TEMPORAL_GENERATION_MISMATCH")
    if input_binding.invocation_id != controlled_invocation_id:
        raise JSpaceControlTemporalBindingError("CONTROLLED_INVOCATION_ID_MISMATCH")

    # The predecessor trace must be the producer envelope for the same exact packet bytes
    # that the successor model-input binding observed before/at invocation admission.
    if predecessor_trace.vector_control_packet_sha256 != input_binding.vector_control_packet_sha256:
        raise JSpaceControlTemporalBindingError("TEMPORAL_CONTROL_PACKET_IDENTITY_MISMATCH")
    if predecessor_trace.vector_control_packet_jcs_utf8 != input_binding.vector_control_packet_jcs_utf8:
        raise JSpaceControlTemporalBindingError("TEMPORAL_CONTROL_PACKET_WIRE_MISMATCH")
    if predecessor_trace.role != input_binding.role:
        raise JSpaceControlTemporalBindingError("TEMPORAL_CONTROL_ROLE_MISMATCH")
    if predecessor_trace.jspace_basis_id != input_binding.jspace_basis_id:
        raise JSpaceControlTemporalBindingError("TEMPORAL_CONTROL_BASIS_MISMATCH")
    if predecessor_trace.jspace_basis_sha256 != input_binding.jspace_basis_sha256:
        raise JSpaceControlTemporalBindingError("TEMPORAL_CONTROL_BASIS_SHA256_MISMATCH")
    if predecessor_trace.vector_control_condition != input_binding.vector_control_condition:
        raise JSpaceControlTemporalBindingError("TEMPORAL_CONTROL_CONDITION_MISMATCH")


def bind_predecessor_control_to_successor_invocation(
    predecessor_trace: TrainingTrace,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    *,
    generation: int,
    predecessor_step_index: int,
    controlled_step_index: int,
    controlled_invocation_id: str,
) -> JSpaceControlTemporalBinding:
    """Bind exact trace(t) control bytes to exact executor-observed input at t+1."""
    _validate_source_edge(
        predecessor_trace,
        input_binding,
        consumed_input_bytes,
        generation=generation,
        predecessor_step_index=predecessor_step_index,
        controlled_step_index=controlled_step_index,
        controlled_invocation_id=controlled_invocation_id,
    )

    material = {
        "schema": TEMPORAL_BINDING_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "generation": _integer(generation, "generation"),
        "predecessor_step_index": _integer(predecessor_step_index, "predecessor_step_index"),
        "controlled_step_index": _integer(controlled_step_index, "controlled_step_index"),
        "predecessor_trace_id": _canonical_text(predecessor_trace.trace_id, "predecessor_trace_id", 256),
        "predecessor_trace_family_id": _canonical_text(
            predecessor_trace.trace_family_id,
            "predecessor_trace_family_id",
            256,
        ),
        "predecessor_trace_sha256": _sha256(predecessor_trace.trace_sha256, "predecessor_trace_sha256"),
        "control_packet_sha256": _sha256(
            predecessor_trace.vector_control_packet_sha256,
            "control_packet_sha256",
        ),
        "model_input_control_binding_sha256": _sha256(
            input_binding.binding_sha256,
            "model_input_control_binding_sha256",
        ),
        "controlled_invocation_id": _canonical_text(
            controlled_invocation_id,
            "controlled_invocation_id",
            256,
        ),
    }
    provisional = JSpaceControlTemporalBinding(**material, temporal_binding_sha256="1" * 64)
    return JSpaceControlTemporalBinding(
        **material,
        temporal_binding_sha256=_canonical_sha256(_material(provisional), "JSPACE_CONTROL_TEMPORAL_BINDING"),
    )


def validate_jspace_control_temporal_binding(
    binding: JSpaceControlTemporalBinding,
    predecessor_trace: TrainingTrace,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
) -> None:
    """Revalidate self-authentication and the exact predecessor->successor source edge."""
    if not isinstance(binding, JSpaceControlTemporalBinding):
        raise JSpaceControlTemporalBindingError("JSPACE_CONTROL_TEMPORAL_BINDING_REQUIRED")
    if binding.schema != TEMPORAL_BINDING_SCHEMA:
        raise JSpaceControlTemporalBindingError("JSPACE_CONTROL_TEMPORAL_BINDING_SCHEMA_UNSUPPORTED")
    if binding.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceControlTemporalBindingError("JSPACE_CONTROL_TEMPORAL_CANONICALIZATION_SCHEMA_UNSUPPORTED")

    observed = _sha256(binding.temporal_binding_sha256, "temporal_binding_sha256")
    expected = _canonical_sha256(_material(binding), "JSPACE_CONTROL_TEMPORAL_BINDING")
    if observed != expected:
        raise JSpaceControlTemporalBindingError("JSPACE_CONTROL_TEMPORAL_BINDING_DIGEST_MISMATCH")

    generation = _integer(binding.generation, "generation")
    predecessor_step_index = _integer(binding.predecessor_step_index, "predecessor_step_index")
    controlled_step_index = _integer(binding.controlled_step_index, "controlled_step_index")
    if predecessor_step_index >= MAX_SAFE_INTEGER or controlled_step_index != predecessor_step_index + 1:
        raise JSpaceControlTemporalBindingError("TEMPORAL_SUCCESSOR_EXACTLY_ONE_STEP_REQUIRED")

    for value, field in (
        (binding.predecessor_trace_sha256, "predecessor_trace_sha256"),
        (binding.control_packet_sha256, "control_packet_sha256"),
        (binding.model_input_control_binding_sha256, "model_input_control_binding_sha256"),
    ):
        _sha256(value, field)
    for value, field in (
        (binding.predecessor_trace_id, "predecessor_trace_id"),
        (binding.predecessor_trace_family_id, "predecessor_trace_family_id"),
        (binding.controlled_invocation_id, "controlled_invocation_id"),
    ):
        _canonical_text(value, field, 256)

    _validate_source_edge(
        predecessor_trace,
        input_binding,
        consumed_input_bytes,
        generation=generation,
        predecessor_step_index=predecessor_step_index,
        controlled_step_index=controlled_step_index,
        controlled_invocation_id=binding.controlled_invocation_id,
    )

    if binding.predecessor_trace_id != predecessor_trace.trace_id:
        raise JSpaceControlTemporalBindingError("PREDECESSOR_TRACE_ID_MISMATCH")
    if binding.predecessor_trace_family_id != predecessor_trace.trace_family_id:
        raise JSpaceControlTemporalBindingError("PREDECESSOR_TRACE_FAMILY_ID_MISMATCH")
    if binding.predecessor_trace_sha256 != predecessor_trace.trace_sha256:
        raise JSpaceControlTemporalBindingError("PREDECESSOR_TRACE_SHA256_MISMATCH")
    if binding.control_packet_sha256 != predecessor_trace.vector_control_packet_sha256:
        raise JSpaceControlTemporalBindingError("TEMPORAL_CONTROL_PACKET_IDENTITY_MISMATCH")
    if binding.model_input_control_binding_sha256 != input_binding.binding_sha256:
        raise JSpaceControlTemporalBindingError("MODEL_INPUT_CONTROL_BINDING_SHA256_MISMATCH")


def temporal_binding_dict(
    binding: JSpaceControlTemporalBinding,
    predecessor_trace: TrainingTrace,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
) -> dict[str, Any]:
    validate_jspace_control_temporal_binding(
        binding,
        predecessor_trace,
        input_binding,
        consumed_input_bytes,
    )
    data = _material(binding)
    data["temporal_binding_sha256"] = binding.temporal_binding_sha256
    return data
