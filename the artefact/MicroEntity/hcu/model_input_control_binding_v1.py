#!/usr/bin/env python3
"""Exact executor-input binding for EntityOS/HCU J-Space Vector Control.

This primitive proves only a byte-level dataflow fact: one exact canonical
``JSPACE_VECTOR_CONTROL_ABI/v1`` packet occurs exactly once in the exact bytes observed at
an executor input boundary, and those bytes match the executor-observed input digest/size.
It does not prove that model hidden states causally used the control signal, does not mint
canonical truth, and does not create a second execution/effect authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .jspace_vector_control_v1 import (
        ABI_SCHEMA,
        VectorControlPacket,
        packet_bytes,
        parse_packet_text,
        validate_packet,
    )
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from jspace_vector_control_v1 import (
        ABI_SCHEMA,
        VectorControlPacket,
        packet_bytes,
        parse_packet_text,
        validate_packet,
    )

BINDING_SCHEMA = "HCU_MODEL_INPUT_CONTROL_BINDING/v1"
TRANSFORM_SCHEMA = "HCU_MODEL_INPUT_DIRECT_UNIQUE_PACKET_EMBED/v1"
MAX_INPUT_BYTES = 64 * 1024 * 1024


class ModelInputControlBindingError(ValueError):
    pass


@dataclass(frozen=True)
class ModelInputControlBinding:
    schema: str
    canonicalization_schema: str
    transform_schema: str
    generation: int
    entry_event_sha256: str
    entry_admission_sha256: str
    route_decision_sha256: str
    grid_plan_sha256: str
    cell_id: str
    role: str
    jspace_basis_id: str
    jspace_basis_sha256: str
    vector_control_abi: str
    vector_control_packet_sha256: str
    vector_control_packet_jcs_utf8: str
    vector_control_condition: str
    executor_id: str
    invocation_id: str
    input_sha256: str
    input_size: int
    packet_offset: int
    binding_sha256: str


def _text(value: Any, field: str, max_len: int = 8192) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelInputControlBindingError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise ModelInputControlBindingError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, 64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise ModelInputControlBindingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise ModelInputControlBindingError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _generation(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ModelInputControlBindingError("generation:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise ModelInputControlBindingError("generation:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _input_bytes(value: Any) -> bytes:
    if not isinstance(value, bytes):
        raise ModelInputControlBindingError("consumed_input_bytes:BYTES_REQUIRED")
    if not 1 <= len(value) <= MAX_INPUT_BYTES:
        raise ModelInputControlBindingError("consumed_input_bytes:SIZE_OUT_OF_RANGE")
    return value


def _declared_input_size(value: Any, field: str = "input_size") -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ModelInputControlBindingError(f"{field}:INTEGER_REQUIRED")
    if not 1 <= value <= MAX_INPUT_BYTES:
        raise ModelInputControlBindingError(f"{field}:SIZE_OUT_OF_RANGE")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        raw = canonicalize(value)
    except CanonicalizationError as exc:
        raise ModelInputControlBindingError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(raw).hexdigest()


def _material(binding: ModelInputControlBinding) -> dict[str, Any]:
    data = asdict(binding)
    data.pop("binding_sha256", None)
    return data


def _unique_packet_offset(input_bytes: bytes, packet_wire: bytes) -> int:
    first = input_bytes.find(packet_wire)
    if first < 0:
        raise ModelInputControlBindingError("VECTOR_CONTROL_PACKET_NOT_IN_EXECUTOR_INPUT")
    second = input_bytes.find(packet_wire, first + 1)
    if second >= 0:
        raise ModelInputControlBindingError("VECTOR_CONTROL_PACKET_INPUT_OCCURRENCE_AMBIGUOUS")
    return first


def bind_direct_unique_packet_input(
    vector_control_packet: VectorControlPacket,
    consumed_input_bytes: bytes,
    *,
    generation: int,
    entry_event_sha256: str,
    entry_admission_sha256: str,
    route_decision_sha256: str,
    grid_plan_sha256: str,
    cell_id: str,
    role: str,
    executor_id: str,
    invocation_id: str,
    executor_observed_input_sha256: str,
    executor_observed_input_size: int,
) -> ModelInputControlBinding:
    """Bind one exact packet to the exact bytes observed at model invocation admission.

    The caller must pass the same immutable bytes presented at the executor boundary. This
    function recomputes their digest/size and refuses a caller-only digest assertion. The
    integration site is responsible for calling it before or at invocation admission while
    those exact bytes are still authoritative.
    """
    try:
        validate_packet(vector_control_packet)
        wire = packet_bytes(vector_control_packet)
    except Exception as exc:
        raise ModelInputControlBindingError(f"VECTOR_CONTROL_PACKET_REJECTED:{exc}") from exc

    generation = _generation(generation)
    if vector_control_packet.generation != generation:
        raise ModelInputControlBindingError("VECTOR_CONTROL_GENERATION_MISMATCH")
    role = _text(role, "role", 256)
    if vector_control_packet.role != role:
        raise ModelInputControlBindingError("VECTOR_CONTROL_ROLE_MISMATCH")

    observed = _input_bytes(consumed_input_bytes)
    input_sha256 = hashlib.sha256(observed).hexdigest()
    input_size = len(observed)
    if _sha256(executor_observed_input_sha256, "executor_observed_input_sha256") != input_sha256:
        raise ModelInputControlBindingError("EXECUTOR_OBSERVED_INPUT_SHA256_MISMATCH")
    observed_input_size = _declared_input_size(
        executor_observed_input_size,
        "executor_observed_input_size",
    )
    if observed_input_size != input_size:
        raise ModelInputControlBindingError("EXECUTOR_OBSERVED_INPUT_SIZE_MISMATCH")

    packet_offset = _unique_packet_offset(observed, wire)
    material = {
        "schema": BINDING_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "transform_schema": TRANSFORM_SCHEMA,
        "generation": generation,
        "entry_event_sha256": _sha256(entry_event_sha256, "entry_event_sha256"),
        "entry_admission_sha256": _sha256(entry_admission_sha256, "entry_admission_sha256"),
        "route_decision_sha256": _sha256(route_decision_sha256, "route_decision_sha256"),
        "grid_plan_sha256": _sha256(grid_plan_sha256, "grid_plan_sha256"),
        "cell_id": _text(cell_id, "cell_id", 256),
        "role": role,
        "jspace_basis_id": _text(vector_control_packet.basis_id, "jspace_basis_id", 256),
        "jspace_basis_sha256": _sha256(vector_control_packet.basis_sha256, "jspace_basis_sha256"),
        "vector_control_abi": ABI_SCHEMA,
        "vector_control_packet_sha256": _sha256(vector_control_packet.packet_sha256, "vector_control_packet_sha256"),
        "vector_control_packet_jcs_utf8": wire.decode("utf-8", "strict"),
        "vector_control_condition": _text(vector_control_packet.control_condition, "vector_control_condition", 64),
        "executor_id": _text(executor_id, "executor_id", 256),
        "invocation_id": _text(invocation_id, "invocation_id", 256),
        "input_sha256": input_sha256,
        "input_size": input_size,
        "packet_offset": packet_offset,
    }
    provisional = ModelInputControlBinding(**material, binding_sha256="1" * 64)
    return ModelInputControlBinding(
        **material,
        binding_sha256=_canonical_sha256(_material(provisional), "MODEL_INPUT_CONTROL_BINDING"),
    )


def validate_model_input_control_binding(
    binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
) -> None:
    """Revalidate the binding against the exact executor-consumed input bytes."""
    if not isinstance(binding, ModelInputControlBinding):
        raise ModelInputControlBindingError("MODEL_INPUT_CONTROL_BINDING_REQUIRED")
    if binding.schema != BINDING_SCHEMA:
        raise ModelInputControlBindingError("MODEL_INPUT_CONTROL_BINDING_SCHEMA_UNSUPPORTED")
    if binding.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise ModelInputControlBindingError("MODEL_INPUT_CONTROL_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    if binding.transform_schema != TRANSFORM_SCHEMA:
        raise ModelInputControlBindingError("MODEL_INPUT_CONTROL_TRANSFORM_UNSUPPORTED")
    generation = _generation(binding.generation)

    observed_binding_sha = _sha256(binding.binding_sha256, "binding_sha256")
    if binding.binding_sha256 != observed_binding_sha:
        raise ModelInputControlBindingError("binding_sha256:NONCANONICAL_SHA256")
    expected_binding_sha = _canonical_sha256(_material(binding), "MODEL_INPUT_CONTROL_BINDING")
    if observed_binding_sha != expected_binding_sha:
        raise ModelInputControlBindingError("MODEL_INPUT_CONTROL_BINDING_DIGEST_MISMATCH")

    for value, field in (
        (binding.entry_event_sha256, "entry_event_sha256"),
        (binding.entry_admission_sha256, "entry_admission_sha256"),
        (binding.route_decision_sha256, "route_decision_sha256"),
        (binding.grid_plan_sha256, "grid_plan_sha256"),
        (binding.jspace_basis_sha256, "jspace_basis_sha256"),
        (binding.vector_control_packet_sha256, "vector_control_packet_sha256"),
        (binding.input_sha256, "input_sha256"),
    ):
        if value != _sha256(value, field):
            raise ModelInputControlBindingError(f"{field}:NONCANONICAL_SHA256")
    for value, field, max_len in (
        (binding.cell_id, "cell_id", 256),
        (binding.role, "role", 256),
        (binding.jspace_basis_id, "jspace_basis_id", 256),
        (binding.vector_control_condition, "vector_control_condition", 64),
        (binding.executor_id, "executor_id", 256),
        (binding.invocation_id, "invocation_id", 256),
    ):
        if value != _text(value, field, max_len):
            raise ModelInputControlBindingError(f"{field}:NONCANONICAL_TEXT")
    if binding.vector_control_abi != ABI_SCHEMA:
        raise ModelInputControlBindingError("VECTOR_CONTROL_ABI_MISMATCH")

    declared_input_size = _declared_input_size(binding.input_size)
    packet_text_value = _text(
        binding.vector_control_packet_jcs_utf8,
        "vector_control_packet_jcs_utf8",
        262144,
    )
    if binding.vector_control_packet_jcs_utf8 != packet_text_value:
        raise ModelInputControlBindingError("vector_control_packet_jcs_utf8:NONCANONICAL_TEXT")
    try:
        packet = parse_packet_text(packet_text_value)
    except Exception as exc:
        raise ModelInputControlBindingError(f"VECTOR_CONTROL_PACKET_REVALIDATION_FAILED:{exc}") from exc
    if packet.packet_sha256 != binding.vector_control_packet_sha256:
        raise ModelInputControlBindingError("VECTOR_CONTROL_PACKET_IDENTITY_MISMATCH")
    if packet.generation != generation:
        raise ModelInputControlBindingError("VECTOR_CONTROL_GENERATION_MISMATCH")
    if packet.role != binding.role:
        raise ModelInputControlBindingError("VECTOR_CONTROL_ROLE_MISMATCH")
    if packet.basis_id != binding.jspace_basis_id or packet.basis_sha256 != binding.jspace_basis_sha256:
        raise ModelInputControlBindingError("VECTOR_CONTROL_BASIS_MISMATCH")
    if packet.control_condition != binding.vector_control_condition:
        raise ModelInputControlBindingError("VECTOR_CONTROL_CONDITION_MISMATCH")

    observed = _input_bytes(consumed_input_bytes)
    if hashlib.sha256(observed).hexdigest() != binding.input_sha256:
        raise ModelInputControlBindingError("EXECUTOR_INPUT_SHA256_MISMATCH")
    if len(observed) != declared_input_size:
        raise ModelInputControlBindingError("EXECUTOR_INPUT_SIZE_MISMATCH")
    if isinstance(binding.packet_offset, bool) or not isinstance(binding.packet_offset, int) or binding.packet_offset < 0:
        raise ModelInputControlBindingError("packet_offset:NONNEGATIVE_INTEGER_REQUIRED")
    wire = packet_bytes(packet)
    observed_offset = _unique_packet_offset(observed, wire)
    if observed_offset != binding.packet_offset:
        raise ModelInputControlBindingError("VECTOR_CONTROL_PACKET_OFFSET_MISMATCH")


def binding_dict(binding: ModelInputControlBinding, consumed_input_bytes: bytes) -> dict[str, Any]:
    validate_model_input_control_binding(binding, consumed_input_bytes)
    data = _material(binding)
    data["binding_sha256"] = binding.binding_sha256
    return data
