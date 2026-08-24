#!/usr/bin/env python3
"""Require observed model-input delivery before causal J-Space training promotion.

This is deterministic evidence plumbing only. It creates no model, state store, effect path,
training authority, or runtime credit. The existing J-Space training pipeline already binds a
TrainingTrace to DatasetAdmission and ENTITYOS_HCU_JSPACE_INFERENCE_BINDING/v3. The donor
also has ENTITYOS_HCU_JSPACE_MODEL_INPUT_CONTROL_CLOSURE/v1, which proves byte-level delivery
of one exact Vector-Control packet into the exact model input associated with that inference.

This gate closes the remaining promotion boundary: non-BASELINE traces may not be treated as
causal intervention training evidence unless an externally admitted model-input-control
closure cross-binds the same trace ancestry and inference identity. BASELINE traces may remain
admissible without intervention-delivery evidence because they make no intervention claim.

Positive validation proves delivery/identity closure only. It does not prove hidden-state
causal use, model benefit, truth, effects, whole-runtime acceptance, or training benefit.
"""
from __future__ import annotations

from typing import Any, Mapping

try:
    from .jspace_inference_binding_v1 import JSpaceInferenceBinding
    from .jspace_model_input_control_closure_v1 import (
        JSpaceModelInputControlClosure,
        JSpaceModelInputControlClosureError,
        validate_closure,
    )
except ImportError:
    from jspace_inference_binding_v1 import JSpaceInferenceBinding
    from jspace_model_input_control_closure_v1 import (
        JSpaceModelInputControlClosure,
        JSpaceModelInputControlClosureError,
        validate_closure,
    )

SCHEMA = "ENTITYOS_HCU_JSPACE_TRAINING_CONTROL_DELIVERY_GATE/v1"
BASELINE_CONTROL_CONDITION = "BASELINE"


class JSpaceTrainingControlDeliveryError(ValueError):
    pass


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise JSpaceTrainingControlDeliveryError(f"{field}:MAPPING_REQUIRED")
    return value


def _text(value: Any, field: str, max_len: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceTrainingControlDeliveryError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise JSpaceTrainingControlDeliveryError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, 64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceTrainingControlDeliveryError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise JSpaceTrainingControlDeliveryError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceTrainingControlDeliveryError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise JSpaceTrainingControlDeliveryError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceTrainingControlDeliveryError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _same(field: str, *values: Any) -> Any:
    if len(values) < 2 or any(value != values[0] for value in values[1:]):
        raise JSpaceTrainingControlDeliveryError(f"TRAINING_CONTROL_DELIVERY_MISMATCH:{field}")
    return values[0]


def require_model_input_control_closure(
    training_trace: Mapping[str, Any],
    inference_binding: JSpaceInferenceBinding,
    closure: JSpaceModelInputControlClosure | None,
) -> str | None:
    """Return the admitted closure digest or fail closed for non-baseline control traces.

    The caller remains responsible for validating the TrainingTrace, DatasetAdmission and
    JSpaceInferenceBinding through their existing single-authority validators before calling
    this guard. This function validates the supplied closure itself and only performs the
    cross-layer identity checks that are unique to intervention-delivery promotion.
    """
    training_trace = _mapping(training_trace, "training_trace")
    if not isinstance(inference_binding, JSpaceInferenceBinding):
        raise JSpaceTrainingControlDeliveryError("JSPACE_INFERENCE_BINDING_REQUIRED")

    control_condition = _text(
        training_trace.get("vector_control_condition"),
        "training_trace.vector_control_condition",
        64,
    ).upper()

    if closure is None:
        if control_condition == BASELINE_CONTROL_CONDITION:
            return None
        raise JSpaceTrainingControlDeliveryError(
            "MODEL_INPUT_CONTROL_CLOSURE_REQUIRED_FOR_NON_BASELINE_TRAINING"
        )

    if not isinstance(closure, JSpaceModelInputControlClosure):
        raise JSpaceTrainingControlDeliveryError("MODEL_INPUT_CONTROL_CLOSURE_REQUIRED")
    try:
        validate_closure(closure)
    except JSpaceModelInputControlClosureError as exc:
        raise JSpaceTrainingControlDeliveryError(
            f"MODEL_INPUT_CONTROL_CLOSURE_REJECTED:{exc}"
        ) from exc

    _same(
        "training_trace_sha256",
        _sha256(training_trace.get("trace_sha256"), "training_trace.trace_sha256"),
        _sha256(inference_binding.training_trace_sha256, "inference_binding.training_trace_sha256"),
    )
    _same(
        "generation",
        _generation(training_trace.get("generation"), "training_trace.generation"),
        _generation(inference_binding.generation, "inference_binding.generation"),
        _generation(closure.generation, "closure.generation"),
    )

    for field in (
        "entry_event_sha256",
        "entry_admission_sha256",
        "route_decision_sha256",
        "grid_plan_sha256",
    ):
        _same(
            field,
            _sha256(training_trace.get(field), f"training_trace.{field}"),
            _sha256(getattr(inference_binding, field), f"inference_binding.{field}"),
            _sha256(getattr(closure, field), f"closure.{field}"),
        )

    _same(
        "cell_id",
        _text(training_trace.get("cell_id"), "training_trace.cell_id", 256),
        _text(inference_binding.cell_id, "inference_binding.cell_id", 256),
        _text(closure.cell_id, "closure.cell_id", 256),
    )
    _same(
        "role",
        _text(training_trace.get("role"), "training_trace.role", 256),
        _text(inference_binding.role, "inference_binding.role", 256),
        _text(closure.role, "closure.role", 256),
    )
    _same(
        "vector_control_packet_sha256",
        _sha256(
            training_trace.get("vector_control_packet_sha256"),
            "training_trace.vector_control_packet_sha256",
        ),
        _sha256(
            inference_binding.vector_control_packet_sha256,
            "inference_binding.vector_control_packet_sha256",
        ),
        _sha256(closure.vector_control_packet_sha256, "closure.vector_control_packet_sha256"),
    )
    _same(
        "jspace_binding_sha256",
        _sha256(inference_binding.binding_sha256, "inference_binding.binding_sha256"),
        _sha256(closure.jspace_binding_sha256, "closure.jspace_binding_sha256"),
    )
    _same(
        "inference_receipt_sha256",
        _sha256(
            inference_binding.inference_receipt_sha256,
            "inference_binding.inference_receipt_sha256",
        ),
        _sha256(closure.inference_receipt_sha256, "closure.inference_receipt_sha256"),
    )
    _same(
        "model_execution_observation_sha256",
        _sha256(
            inference_binding.model_execution_observation_sha256,
            "inference_binding.model_execution_observation_sha256",
        ),
        _sha256(
            closure.model_execution_observation_sha256,
            "closure.model_execution_observation_sha256",
        ),
    )
    _same(
        "executor_id",
        _text(inference_binding.model_execution_executor_id, "inference_binding.model_execution_executor_id", 256),
        _text(closure.executor_id, "closure.executor_id", 256),
    )
    _same(
        "invocation_id",
        _text(inference_binding.model_execution_invocation_id, "inference_binding.model_execution_invocation_id", 256),
        _text(inference_binding.model_call_id, "inference_binding.model_call_id", 256),
        _text(closure.invocation_id, "closure.invocation_id", 256),
    )
    _same(
        "input_sha256",
        _sha256(inference_binding.input_sha256, "inference_binding.input_sha256"),
        _sha256(closure.input_sha256, "closure.input_sha256"),
    )
    _same(
        "input_size",
        _nonnegative_int(inference_binding.input_size, "inference_binding.input_size"),
        _nonnegative_int(closure.input_size, "closure.input_size"),
    )

    return _sha256(closure.closure_sha256, "closure.closure_sha256")
