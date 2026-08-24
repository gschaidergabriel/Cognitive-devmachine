#!/usr/bin/env python3
"""Producer-derived J-Space control-packet consumption binding for EntityOS/HCU.

This primitive establishes one narrow source-level dataflow fact:

    validated TrainingTrace control packet
      == exact packet revalidated by ModelInputControlBinding
      -> exact executor-observed input bytes for one invocation.

It deliberately does NOT claim temporal order, successor-step semantics, hidden-state use,
counterfactual effect, model-runtime success, reward, canonical truth, or EffectGate authority.
Unlike the reverted temporal-binding candidate, it accepts no caller-supplied step labels.
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

CONSUMPTION_BINDING_SCHEMA = "HCU_JSPACE_CONTROL_CONSUMPTION_BINDING/v1"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class JSpaceControlConsumptionBindingError(ValueError):
    pass


@dataclass(frozen=True)
class JSpaceControlConsumptionBinding:
    schema: str
    canonicalization_schema: str
    generation: int
    trace_id: str
    trace_family_id: str
    training_trace_sha256: str
    prototype_trace_sha256: str
    entry_event_sha256: str
    entry_admission_sha256: str
    route_decision_sha256: str
    grid_plan_sha256: str
    cell_id: str
    role: str
    jspace_basis_id: str
    jspace_basis_sha256: str
    vector_control_packet_sha256: str
    vector_control_condition: str
    model_input_control_binding_sha256: str
    executor_id: str
    invocation_id: str
    input_sha256: str
    input_size: int
    packet_offset: int
    consumption_binding_sha256: str


def _text(value: Any, field: str, max_len: int = 8192) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceControlConsumptionBindingError(f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
    if len(normalized) > max_len:
        raise JSpaceControlConsumptionBindingError(f"{field}:TOO_LONG")
    return normalized


def _canonical_text(value: Any, field: str, max_len: int = 8192) -> str:
    normalized = _text(value, field, max_len)
    if value != normalized:
        raise JSpaceControlConsumptionBindingError(f"{field}:NONCANONICAL_TEXT")
    return normalized


def _sha256(value: Any, field: str) -> str:
    normalized = _canonical_text(value, field, 64)
    if len(normalized) != 64 or normalized.lower() != normalized or any(
        ch not in "0123456789abcdef" for ch in normalized
    ):
        raise JSpaceControlConsumptionBindingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if normalized in {"0" * 64, "f" * 64}:
        raise JSpaceControlConsumptionBindingError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return normalized


def _safe_nonnegative_integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceControlConsumptionBindingError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > MAX_SAFE_INTEGER:
        raise JSpaceControlConsumptionBindingError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        raw = canonicalize(value)
    except CanonicalizationError as exc:
        raise JSpaceControlConsumptionBindingError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc
    return hashlib.sha256(raw).hexdigest()


def _material(binding: JSpaceControlConsumptionBinding) -> dict[str, Any]:
    data = asdict(binding)
    data.pop("consumption_binding_sha256", None)
    return data


def _validate_source_edge(
    trace: TrainingTrace,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
) -> None:
    try:
        validate_training_trace(trace)
    except Exception as exc:
        raise JSpaceControlConsumptionBindingError(f"TRAINING_TRACE_REJECTED:{exc}") from exc
    try:
        validate_model_input_control_binding(input_binding, consumed_input_bytes)
    except Exception as exc:
        raise JSpaceControlConsumptionBindingError(f"MODEL_INPUT_CONTROL_BINDING_REJECTED:{exc}") from exc

    equalities = (
        (trace.generation, input_binding.generation, "GENERATION_MISMATCH"),
        (trace.entry_event_sha256, input_binding.entry_event_sha256, "ENTRY_EVENT_IDENTITY_MISMATCH"),
        (trace.entry_admission_sha256, input_binding.entry_admission_sha256, "ENTRY_ADMISSION_IDENTITY_MISMATCH"),
        (trace.route_decision_sha256, input_binding.route_decision_sha256, "ROUTE_DECISION_IDENTITY_MISMATCH"),
        (trace.grid_plan_sha256, input_binding.grid_plan_sha256, "GRID_PLAN_IDENTITY_MISMATCH"),
        (trace.cell_id, input_binding.cell_id, "CELL_ID_MISMATCH"),
        (trace.role, input_binding.role, "ROLE_MISMATCH"),
        (trace.jspace_basis_id, input_binding.jspace_basis_id, "JSPACE_BASIS_ID_MISMATCH"),
        (trace.jspace_basis_sha256, input_binding.jspace_basis_sha256, "JSPACE_BASIS_SHA256_MISMATCH"),
        (
            trace.vector_control_packet_sha256,
            input_binding.vector_control_packet_sha256,
            "CONTROL_PACKET_IDENTITY_MISMATCH",
        ),
        (
            trace.vector_control_packet_jcs_utf8,
            input_binding.vector_control_packet_jcs_utf8,
            "CONTROL_PACKET_WIRE_MISMATCH",
        ),
        (
            trace.vector_control_condition,
            input_binding.vector_control_condition,
            "CONTROL_CONDITION_MISMATCH",
        ),
    )
    for left, right, code in equalities:
        if left != right:
            raise JSpaceControlConsumptionBindingError(code)


def bind_trace_control_to_executor_input(
    trace: TrainingTrace,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
) -> JSpaceControlConsumptionBinding:
    """Bind validated trace-produced control bytes to one exact executor input observation."""
    _validate_source_edge(trace, input_binding, consumed_input_bytes)

    material = {
        "schema": CONSUMPTION_BINDING_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "generation": _safe_nonnegative_integer(trace.generation, "generation"),
        "trace_id": _canonical_text(trace.trace_id, "trace_id", 256),
        "trace_family_id": _canonical_text(trace.trace_family_id, "trace_family_id", 256),
        "training_trace_sha256": _sha256(trace.trace_sha256, "training_trace_sha256"),
        "prototype_trace_sha256": _sha256(trace.prototype_trace_sha256, "prototype_trace_sha256"),
        "entry_event_sha256": _sha256(trace.entry_event_sha256, "entry_event_sha256"),
        "entry_admission_sha256": _sha256(trace.entry_admission_sha256, "entry_admission_sha256"),
        "route_decision_sha256": _sha256(trace.route_decision_sha256, "route_decision_sha256"),
        "grid_plan_sha256": _sha256(trace.grid_plan_sha256, "grid_plan_sha256"),
        "cell_id": _canonical_text(trace.cell_id, "cell_id", 256),
        "role": _canonical_text(trace.role, "role", 256),
        "jspace_basis_id": _canonical_text(trace.jspace_basis_id, "jspace_basis_id", 256),
        "jspace_basis_sha256": _sha256(trace.jspace_basis_sha256, "jspace_basis_sha256"),
        "vector_control_packet_sha256": _sha256(
            trace.vector_control_packet_sha256,
            "vector_control_packet_sha256",
        ),
        "vector_control_condition": _canonical_text(
            trace.vector_control_condition,
            "vector_control_condition",
            64,
        ),
        "model_input_control_binding_sha256": _sha256(
            input_binding.binding_sha256,
            "model_input_control_binding_sha256",
        ),
        "executor_id": _canonical_text(input_binding.executor_id, "executor_id", 256),
        "invocation_id": _canonical_text(input_binding.invocation_id, "invocation_id", 256),
        "input_sha256": _sha256(input_binding.input_sha256, "input_sha256"),
        "input_size": _safe_nonnegative_integer(input_binding.input_size, "input_size"),
        "packet_offset": _safe_nonnegative_integer(input_binding.packet_offset, "packet_offset"),
    }
    provisional = JSpaceControlConsumptionBinding(
        **material,
        consumption_binding_sha256="1" * 64,
    )
    return JSpaceControlConsumptionBinding(
        **material,
        consumption_binding_sha256=_canonical_sha256(
            _material(provisional),
            "JSPACE_CONTROL_CONSUMPTION_BINDING",
        ),
    )


def validate_jspace_control_consumption_binding(
    binding: JSpaceControlConsumptionBinding,
    trace: TrainingTrace,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
) -> None:
    """Revalidate the self-authenticating binding against both exact upstream sources."""
    if not isinstance(binding, JSpaceControlConsumptionBinding):
        raise JSpaceControlConsumptionBindingError("JSPACE_CONTROL_CONSUMPTION_BINDING_REQUIRED")
    if binding.schema != CONSUMPTION_BINDING_SCHEMA:
        raise JSpaceControlConsumptionBindingError("JSPACE_CONTROL_CONSUMPTION_BINDING_SCHEMA_UNSUPPORTED")
    if binding.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceControlConsumptionBindingError("JSPACE_CONTROL_CONSUMPTION_CANONICALIZATION_SCHEMA_UNSUPPORTED")

    observed = _sha256(binding.consumption_binding_sha256, "consumption_binding_sha256")
    expected = _canonical_sha256(_material(binding), "JSPACE_CONTROL_CONSUMPTION_BINDING")
    if observed != expected:
        raise JSpaceControlConsumptionBindingError("JSPACE_CONTROL_CONSUMPTION_BINDING_DIGEST_MISMATCH")

    _validate_source_edge(trace, input_binding, consumed_input_bytes)
    expected_binding = bind_trace_control_to_executor_input(trace, input_binding, consumed_input_bytes)
    if binding != expected_binding:
        raise JSpaceControlConsumptionBindingError("JSPACE_CONTROL_CONSUMPTION_SOURCE_REVALIDATION_MISMATCH")


def consumption_binding_dict(
    binding: JSpaceControlConsumptionBinding,
    trace: TrainingTrace,
    input_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
) -> dict[str, Any]:
    validate_jspace_control_consumption_binding(
        binding,
        trace,
        input_binding,
        consumed_input_bytes,
    )
    data = _material(binding)
    data["consumption_binding_sha256"] = binding.consumption_binding_sha256
    return data
