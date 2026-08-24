#!/usr/bin/env python3
"""Bind one exact J-Space control packet to one verified model execution.

This module closes a narrow source/evidence edge only:

    TrainingTrace / JSPACE_VECTOR_CONTROL_ABI packet
        -> exact executor-input byte binding
        -> HCU_VERIFIED_MODEL_EXECUTION/v1

It deliberately does not assert t->t+1 ordering, hidden-state causality, model benefit,
reward truth, canonical state, or EffectGate authority. In particular it avoids caller-
supplied temporal/step labels: the execution identity comes from an already verified,
externally admitted actual model-executor observation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .jspace_training_trace_v1 import TrainingTrace, validate_training_trace
    from .model_input_control_binding_v1 import ModelInputControlBinding, validate_model_input_control_binding
    from .model_execution_receipt_v1 import VerifiedModelExecution, validate_verified_model_execution
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from jspace_training_trace_v1 import TrainingTrace, validate_training_trace
    from model_input_control_binding_v1 import ModelInputControlBinding, validate_model_input_control_binding
    from model_execution_receipt_v1 import VerifiedModelExecution, validate_verified_model_execution

BINDING_SCHEMA = "HCU_JSPACE_CONTROL_EXECUTION_BINDING/v1"


class JSpaceControlExecutionBindingError(ValueError):
    pass


@dataclass(frozen=True)
class JSpaceControlExecutionBinding:
    schema: str
    canonicalization_schema: str
    generation: int
    training_trace_sha256: str
    trace_family_id: str
    entry_event_sha256: str
    entry_admission_sha256: str
    route_decision_sha256: str
    grid_plan_sha256: str
    cell_id: str
    role: str
    vector_control_packet_sha256: str
    vector_control_condition: str
    model_input_control_binding_sha256: str
    executor_id: str
    invocation_id: str
    executor_input_sha256: str
    executor_input_size: int
    verified_model_execution_receipt_sha256: str
    verified_model_execution_observation_sha256: str
    binding_sha256: str


def _text(value: Any, field: str, max_len: int = 8192) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceControlExecutionBindingError(f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
    if normalized != value:
        raise JSpaceControlExecutionBindingError(f"{field}:NONCANONICAL_TEXT")
    if len(normalized) > max_len:
        raise JSpaceControlExecutionBindingError(f"{field}:TOO_LONG")
    return normalized


def _sha256(value: Any, field: str) -> str:
    normalized = _text(value, field, 64)
    if (
        len(normalized) != 64
        or normalized.lower() != normalized
        or any(ch not in "0123456789abcdef" for ch in normalized)
    ):
        raise JSpaceControlExecutionBindingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if normalized in {"0" * 64, "f" * 64}:
        raise JSpaceControlExecutionBindingError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return normalized


def _generation(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceControlExecutionBindingError("generation:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise JSpaceControlExecutionBindingError("generation:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _input_size(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise JSpaceControlExecutionBindingError("executor_input_size:POSITIVE_INTEGER_REQUIRED")
    if value > 64 * 1024 * 1024:
        raise JSpaceControlExecutionBindingError("executor_input_size:SIZE_OUT_OF_RANGE")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise JSpaceControlExecutionBindingError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _material(binding: JSpaceControlExecutionBinding) -> dict[str, Any]:
    data = asdict(binding)
    data.pop("binding_sha256", None)
    return data


def _validate_sources(
    trace: TrainingTrace,
    input_binding: ModelInputControlBinding,
    verified_execution: VerifiedModelExecution,
    consumed_input_bytes: bytes,
) -> None:
    try:
        validate_training_trace(trace)
    except Exception as exc:
        raise JSpaceControlExecutionBindingError(f"TRAINING_TRACE_REJECTED:{exc}") from exc
    try:
        validate_model_input_control_binding(input_binding, consumed_input_bytes)
    except Exception as exc:
        raise JSpaceControlExecutionBindingError(f"MODEL_INPUT_CONTROL_BINDING_REJECTED:{exc}") from exc
    try:
        validate_verified_model_execution(verified_execution)
    except Exception as exc:
        raise JSpaceControlExecutionBindingError(f"VERIFIED_MODEL_EXECUTION_REJECTED:{exc}") from exc

    generation = _generation(trace.generation)
    if input_binding.generation != generation or verified_execution.entity_generation != generation:
        raise JSpaceControlExecutionBindingError("CONTROL_EXECUTION_GENERATION_MISMATCH")

    for trace_value, input_value, code in (
        (trace.entry_event_sha256, input_binding.entry_event_sha256, "ENTRY_EVENT_MISMATCH"),
        (trace.entry_admission_sha256, input_binding.entry_admission_sha256, "ENTRY_ADMISSION_MISMATCH"),
        (trace.route_decision_sha256, input_binding.route_decision_sha256, "ROUTE_DECISION_MISMATCH"),
        (trace.grid_plan_sha256, input_binding.grid_plan_sha256, "TRACE_INPUT_GRID_PLAN_MISMATCH"),
        (trace.cell_id, input_binding.cell_id, "TRACE_INPUT_CELL_MISMATCH"),
        (trace.role, input_binding.role, "TRACE_INPUT_ROLE_MISMATCH"),
        (
            trace.vector_control_packet_sha256,
            input_binding.vector_control_packet_sha256,
            "VECTOR_CONTROL_PACKET_IDENTITY_MISMATCH",
        ),
        (
            trace.vector_control_packet_jcs_utf8,
            input_binding.vector_control_packet_jcs_utf8,
            "VECTOR_CONTROL_PACKET_WIRE_MISMATCH",
        ),
        (
            trace.vector_control_condition,
            input_binding.vector_control_condition,
            "VECTOR_CONTROL_CONDITION_MISMATCH",
        ),
        (trace.jspace_basis_id, input_binding.jspace_basis_id, "JSPACE_BASIS_ID_MISMATCH"),
        (trace.jspace_basis_sha256, input_binding.jspace_basis_sha256, "JSPACE_BASIS_SHA256_MISMATCH"),
    ):
        if trace_value != input_value:
            raise JSpaceControlExecutionBindingError(code)

    for input_value, execution_value, code in (
        (input_binding.grid_plan_sha256, verified_execution.grid_plan_sha256, "INPUT_EXECUTION_GRID_PLAN_MISMATCH"),
        (input_binding.cell_id, verified_execution.output_producing_cell_id, "INPUT_EXECUTION_CELL_MISMATCH"),
        (input_binding.role, verified_execution.role, "INPUT_EXECUTION_ROLE_MISMATCH"),
        (input_binding.executor_id, verified_execution.executor_id, "EXECUTOR_ID_MISMATCH"),
        (input_binding.invocation_id, verified_execution.invocation_id, "EXECUTOR_INVOCATION_MISMATCH"),
        (input_binding.input_sha256, verified_execution.input_sha256, "EXECUTOR_INPUT_SHA256_MISMATCH"),
        (input_binding.input_size, verified_execution.input_size, "EXECUTOR_INPUT_SIZE_MISMATCH"),
    ):
        if input_value != execution_value:
            raise JSpaceControlExecutionBindingError(code)


def bind_control_packet_to_verified_execution(
    trace: TrainingTrace,
    input_binding: ModelInputControlBinding,
    verified_execution: VerifiedModelExecution,
    consumed_input_bytes: bytes,
) -> JSpaceControlExecutionBinding:
    """Bind trace-produced control bytes to one externally admitted actual model execution."""
    _validate_sources(trace, input_binding, verified_execution, consumed_input_bytes)

    material = {
        "schema": BINDING_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "generation": _generation(trace.generation),
        "training_trace_sha256": _sha256(trace.trace_sha256, "training_trace_sha256"),
        "trace_family_id": _text(trace.trace_family_id, "trace_family_id", 256),
        "entry_event_sha256": _sha256(trace.entry_event_sha256, "entry_event_sha256"),
        "entry_admission_sha256": _sha256(trace.entry_admission_sha256, "entry_admission_sha256"),
        "route_decision_sha256": _sha256(trace.route_decision_sha256, "route_decision_sha256"),
        "grid_plan_sha256": _sha256(trace.grid_plan_sha256, "grid_plan_sha256"),
        "cell_id": _text(trace.cell_id, "cell_id", 256),
        "role": _text(trace.role, "role", 256),
        "vector_control_packet_sha256": _sha256(
            trace.vector_control_packet_sha256,
            "vector_control_packet_sha256",
        ),
        "vector_control_condition": _text(
            trace.vector_control_condition,
            "vector_control_condition",
            64,
        ),
        "model_input_control_binding_sha256": _sha256(
            input_binding.binding_sha256,
            "model_input_control_binding_sha256",
        ),
        "executor_id": _text(verified_execution.executor_id, "executor_id", 256),
        "invocation_id": _text(verified_execution.invocation_id, "invocation_id", 256),
        "executor_input_sha256": _sha256(verified_execution.input_sha256, "executor_input_sha256"),
        "executor_input_size": _input_size(verified_execution.input_size),
        "verified_model_execution_receipt_sha256": _sha256(
            verified_execution.receipt_sha256,
            "verified_model_execution_receipt_sha256",
        ),
        "verified_model_execution_observation_sha256": _sha256(
            verified_execution.observation_sha256,
            "verified_model_execution_observation_sha256",
        ),
    }
    provisional = JSpaceControlExecutionBinding(**material, binding_sha256="1" * 64)
    return JSpaceControlExecutionBinding(
        **material,
        binding_sha256=_canonical_sha256(_material(provisional), "JSPACE_CONTROL_EXECUTION_BINDING"),
    )


def validate_control_execution_binding(
    binding: JSpaceControlExecutionBinding,
    trace: TrainingTrace,
    input_binding: ModelInputControlBinding,
    verified_execution: VerifiedModelExecution,
    consumed_input_bytes: bytes,
) -> None:
    """Revalidate the persisted binding against all three exact upstream sources."""
    if not isinstance(binding, JSpaceControlExecutionBinding):
        raise JSpaceControlExecutionBindingError("JSPACE_CONTROL_EXECUTION_BINDING_REQUIRED")
    if binding.schema != BINDING_SCHEMA:
        raise JSpaceControlExecutionBindingError("JSPACE_CONTROL_EXECUTION_BINDING_SCHEMA_UNSUPPORTED")
    if binding.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceControlExecutionBindingError("JSPACE_CONTROL_EXECUTION_CANONICALIZATION_SCHEMA_UNSUPPORTED")

    observed = _sha256(binding.binding_sha256, "binding_sha256")
    expected = _canonical_sha256(_material(binding), "JSPACE_CONTROL_EXECUTION_BINDING")
    if observed != expected:
        raise JSpaceControlExecutionBindingError("JSPACE_CONTROL_EXECUTION_BINDING_DIGEST_MISMATCH")

    _validate_sources(trace, input_binding, verified_execution, consumed_input_bytes)
    expected_binding = bind_control_packet_to_verified_execution(
        trace,
        input_binding,
        verified_execution,
        consumed_input_bytes,
    )
    if binding != expected_binding:
        raise JSpaceControlExecutionBindingError("JSPACE_CONTROL_EXECUTION_SOURCE_REVALIDATION_MISMATCH")


def binding_dict(
    binding: JSpaceControlExecutionBinding,
    trace: TrainingTrace,
    input_binding: ModelInputControlBinding,
    verified_execution: VerifiedModelExecution,
    consumed_input_bytes: bytes,
) -> dict[str, Any]:
    validate_control_execution_binding(
        binding,
        trace,
        input_binding,
        verified_execution,
        consumed_input_bytes,
    )
    data = _material(binding)
    data["binding_sha256"] = binding.binding_sha256
    return data
