#!/usr/bin/env python3
"""Close admitted J-Space model-input control into the existing inference/J-Space chain.

This is a deterministic evidence projection only. It creates no database, model executor,
truth/effect authority, InferenceReceipt fork, or J-Space binding fork. It composes the
existing authorities by requiring one exact ``HCU_MODEL_INPUT_CONTROL_ADMISSION/v1`` plus
its exact revalidated binding/input bytes, the scheduler-owned GRID plan, the canonical
``HCU_INFERENCE_RECEIPT/v4`` and ``ENTITYOS_HCU_JSPACE_INFERENCE_BINDING/v3`` to describe
one identical causal execution.

Positive closure proves byte-level delivery of the exact Vector-Control packet to the exact
model input associated with the J-Space/inference evidence. It does NOT prove hidden-state
causal use, model benefit, truth, effects, runtime acceptance, or training benefit.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .grid10_scheduler_v1 import GridPlan, GridScheduleError, validate_grid_plan_identity
    from .inference_receipt_v1 import InferenceReceipt, SCHEMA as INFERENCE_SCHEMA, STATUS as INFERENCE_STATUS
    from .jspace_inference_binding_v1 import (
        JSpaceInferenceBinding,
        JSpaceInferenceBindingError,
        SCHEMA as JSPACE_BINDING_SCHEMA,
        validate_binding as validate_jspace_binding,
    )
    from .model_input_control_admission_store_v1 import (
        ADMISSION_SCHEMA as CONTROL_ADMISSION_SCHEMA,
        ModelInputControlAdmission,
    )
    from .model_input_control_binding_v1 import (
        BINDING_SCHEMA as CONTROL_BINDING_SCHEMA,
        ModelInputControlBinding,
        ModelInputControlBindingError,
        validate_model_input_control_binding,
    )
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from grid10_scheduler_v1 import GridPlan, GridScheduleError, validate_grid_plan_identity
    from inference_receipt_v1 import InferenceReceipt, SCHEMA as INFERENCE_SCHEMA, STATUS as INFERENCE_STATUS
    from jspace_inference_binding_v1 import (
        JSpaceInferenceBinding,
        JSpaceInferenceBindingError,
        SCHEMA as JSPACE_BINDING_SCHEMA,
        validate_binding as validate_jspace_binding,
    )
    from model_input_control_admission_store_v1 import (
        ADMISSION_SCHEMA as CONTROL_ADMISSION_SCHEMA,
        ModelInputControlAdmission,
    )
    from model_input_control_binding_v1 import (
        BINDING_SCHEMA as CONTROL_BINDING_SCHEMA,
        ModelInputControlBinding,
        ModelInputControlBindingError,
        validate_model_input_control_binding,
    )

SCHEMA = "ENTITYOS_HCU_JSPACE_MODEL_INPUT_CONTROL_CLOSURE/v1"


class JSpaceModelInputControlClosureError(ValueError):
    pass


@dataclass(frozen=True)
class JSpaceModelInputControlClosure:
    schema: str
    canonicalization_schema: str
    control_admission_schema: str
    control_admission_sha256: str
    control_binding_schema: str
    control_binding_sha256: str
    model_execution_observation_sha256: str
    inference_receipt_schema: str
    inference_receipt_sha256: str
    jspace_binding_schema: str
    jspace_binding_sha256: str
    generation: int
    entry_event_sha256: str
    entry_admission_sha256: str
    route_decision_sha256: str
    grid_plan_sha256: str
    cell_id: str
    role: str
    vector_control_packet_sha256: str
    executor_id: str
    invocation_id: str
    input_sha256: str
    input_size: int
    closure_sha256: str


def _text(value: Any, field: str, max_len: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceModelInputControlClosureError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise JSpaceModelInputControlClosureError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, 64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceModelInputControlClosureError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise JSpaceModelInputControlClosureError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceModelInputControlClosureError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise JSpaceModelInputControlClosureError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceModelInputControlClosureError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise JSpaceModelInputControlClosureError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _validate_inference_receipt(receipt: InferenceReceipt) -> None:
    if not isinstance(receipt, InferenceReceipt):
        raise JSpaceModelInputControlClosureError("HCU_INFERENCE_RECEIPT_REQUIRED")
    if receipt.schema != INFERENCE_SCHEMA or receipt.status != INFERENCE_STATUS:
        raise JSpaceModelInputControlClosureError("HCU_INFERENCE_RECEIPT_SCHEMA_OR_STATUS_UNSUPPORTED")
    material = asdict(receipt)
    observed = _sha256(material.pop("receipt_sha256", None), "inference_receipt.receipt_sha256")
    expected = _canonical_sha256(material, "HCU_INFERENCE_RECEIPT")
    if observed != expected:
        raise JSpaceModelInputControlClosureError("HCU_INFERENCE_RECEIPT_DIGEST_MISMATCH")


def _validate_control_admission(admission: ModelInputControlAdmission) -> None:
    if not isinstance(admission, ModelInputControlAdmission):
        raise JSpaceModelInputControlClosureError("MODEL_INPUT_CONTROL_ADMISSION_REQUIRED")
    if admission.schema != CONTROL_ADMISSION_SCHEMA:
        raise JSpaceModelInputControlClosureError("MODEL_INPUT_CONTROL_ADMISSION_SCHEMA_UNSUPPORTED")
    if admission.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceModelInputControlClosureError("MODEL_INPUT_CONTROL_ADMISSION_CANONICALIZATION_UNSUPPORTED")
    if admission.binding_schema != CONTROL_BINDING_SCHEMA:
        raise JSpaceModelInputControlClosureError("MODEL_INPUT_CONTROL_ADMISSION_BINDING_SCHEMA_UNSUPPORTED")
    material = asdict(admission)
    observed = _sha256(material.pop("admission_sha256", None), "control_admission.admission_sha256")
    expected = _canonical_sha256(material, "MODEL_INPUT_CONTROL_ADMISSION")
    if observed != expected:
        raise JSpaceModelInputControlClosureError("MODEL_INPUT_CONTROL_ADMISSION_DIGEST_MISMATCH")


def _validate_grid_plan(plan: GridPlan) -> None:
    if not isinstance(plan, GridPlan):
        raise JSpaceModelInputControlClosureError("GRID_PLAN_REQUIRED")
    try:
        observed = validate_grid_plan_identity(plan)
    except GridScheduleError as exc:
        raise JSpaceModelInputControlClosureError(f"GRID_PLAN_REJECTED:{exc}") from exc
    if observed != plan.plan_sha256:
        raise JSpaceModelInputControlClosureError("GRID_PLAN_IDENTITY_MISMATCH")


def _need_equal(field: str, *values: Any) -> None:
    if len(values) < 2 or any(value != values[0] for value in values[1:]):
        raise JSpaceModelInputControlClosureError(f"CONTROL_CLOSURE_MISMATCH:{field}")


def close_model_input_control_into_jspace(
    control_binding: ModelInputControlBinding,
    control_admission: ModelInputControlAdmission,
    consumed_input_bytes: bytes,
    grid_plan: GridPlan,
    inference_receipt: InferenceReceipt,
    jspace_binding: JSpaceInferenceBinding,
) -> JSpaceModelInputControlClosure:
    """Compose existing admitted evidence into one exact self-authenticating closure."""
    try:
        validate_model_input_control_binding(control_binding, consumed_input_bytes)
    except ModelInputControlBindingError as exc:
        raise JSpaceModelInputControlClosureError(f"MODEL_INPUT_CONTROL_BINDING_REJECTED:{exc}") from exc
    _validate_control_admission(control_admission)
    _validate_grid_plan(grid_plan)
    _validate_inference_receipt(inference_receipt)
    try:
        validate_jspace_binding(jspace_binding)
    except JSpaceInferenceBindingError as exc:
        raise JSpaceModelInputControlClosureError(f"JSPACE_BINDING_REJECTED:{exc}") from exc

    _need_equal("control_binding_sha256", control_admission.binding_sha256, control_binding.binding_sha256)
    _need_equal("generation", control_binding.generation, control_admission.generation, grid_plan.entity_generation, inference_receipt.entity_generation, jspace_binding.generation)
    _need_equal("grid_plan_sha256", control_binding.grid_plan_sha256, control_admission.grid_plan_sha256, grid_plan.plan_sha256, inference_receipt.grid_plan_sha256, jspace_binding.grid_plan_sha256)
    _need_equal("entry_event_sha256", control_binding.entry_event_sha256, grid_plan.entry_event_sha256, inference_receipt.event_sha256, jspace_binding.entry_event_sha256)
    _need_equal("entry_admission_sha256", control_binding.entry_admission_sha256, grid_plan.entry_admission_sha256, inference_receipt.entry_admission_sha256, jspace_binding.entry_admission_sha256)
    _need_equal("route_decision_sha256", control_binding.route_decision_sha256, grid_plan.route_decision_sha256, inference_receipt.decision_sha256, jspace_binding.route_decision_sha256)
    _need_equal("cell_id", control_binding.cell_id, control_admission.cell_id, inference_receipt.output_producing_cell_id, jspace_binding.cell_id, jspace_binding.output_producing_cell_id)
    _need_equal("role", control_binding.role, control_admission.role, inference_receipt.model_execution_role, jspace_binding.role, jspace_binding.model_execution_role)
    _need_equal("executor_id", control_binding.executor_id, control_admission.executor_id, inference_receipt.model_execution_executor_id, jspace_binding.model_execution_executor_id)
    _need_equal("invocation_id", control_binding.invocation_id, control_admission.invocation_id, inference_receipt.model_execution_invocation_id, inference_receipt.model_call_id, jspace_binding.model_execution_invocation_id, jspace_binding.model_call_id)
    _need_equal("input_sha256", control_binding.input_sha256, control_admission.input_sha256, inference_receipt.input_sha256, jspace_binding.input_sha256)
    _need_equal("input_size", control_binding.input_size, control_admission.input_size, inference_receipt.input_size, jspace_binding.input_size)
    _need_equal("vector_control_packet_sha256", control_binding.vector_control_packet_sha256, control_admission.vector_control_packet_sha256, jspace_binding.vector_control_packet_sha256)
    _need_equal("model_execution_observation_sha256", control_admission.model_execution_observation_sha256, inference_receipt.model_execution_observation_sha256, jspace_binding.model_execution_observation_sha256)
    _need_equal("inference_receipt_sha256", inference_receipt.receipt_sha256, jspace_binding.inference_receipt_sha256)

    material = {
        "schema": SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "control_admission_schema": CONTROL_ADMISSION_SCHEMA,
        "control_admission_sha256": _sha256(control_admission.admission_sha256, "control_admission.admission_sha256"),
        "control_binding_schema": CONTROL_BINDING_SCHEMA,
        "control_binding_sha256": _sha256(control_binding.binding_sha256, "control_binding.binding_sha256"),
        "model_execution_observation_sha256": _sha256(control_admission.model_execution_observation_sha256, "control_admission.model_execution_observation_sha256"),
        "inference_receipt_schema": INFERENCE_SCHEMA,
        "inference_receipt_sha256": _sha256(inference_receipt.receipt_sha256, "inference_receipt.receipt_sha256"),
        "jspace_binding_schema": JSPACE_BINDING_SCHEMA,
        "jspace_binding_sha256": _sha256(jspace_binding.binding_sha256, "jspace_binding.binding_sha256"),
        "generation": _generation(control_binding.generation, "generation"),
        "entry_event_sha256": _sha256(control_binding.entry_event_sha256, "entry_event_sha256"),
        "entry_admission_sha256": _sha256(control_binding.entry_admission_sha256, "entry_admission_sha256"),
        "route_decision_sha256": _sha256(control_binding.route_decision_sha256, "route_decision_sha256"),
        "grid_plan_sha256": _sha256(control_binding.grid_plan_sha256, "grid_plan_sha256"),
        "cell_id": _text(control_binding.cell_id, "cell_id", 256),
        "role": _text(control_binding.role, "role", 256),
        "vector_control_packet_sha256": _sha256(control_binding.vector_control_packet_sha256, "vector_control_packet_sha256"),
        "executor_id": _text(control_binding.executor_id, "executor_id", 256),
        "invocation_id": _text(control_binding.invocation_id, "invocation_id", 256),
        "input_sha256": _sha256(control_binding.input_sha256, "input_sha256"),
        "input_size": _nonnegative_int(control_binding.input_size, "input_size"),
    }
    return JSpaceModelInputControlClosure(
        **material,
        closure_sha256=_canonical_sha256(material, "JSPACE_MODEL_INPUT_CONTROL_CLOSURE"),
    )


def validate_closure(closure: JSpaceModelInputControlClosure) -> None:
    """Validate serialized closure identity; object-level causality is established by creation."""
    if not isinstance(closure, JSpaceModelInputControlClosure):
        raise JSpaceModelInputControlClosureError("JSPACE_MODEL_INPUT_CONTROL_CLOSURE_REQUIRED")
    if closure.schema != SCHEMA or closure.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceModelInputControlClosureError("JSPACE_MODEL_INPUT_CONTROL_CLOSURE_SCHEMA_UNSUPPORTED")
    if closure.control_admission_schema != CONTROL_ADMISSION_SCHEMA:
        raise JSpaceModelInputControlClosureError("CONTROL_ADMISSION_SCHEMA_MISMATCH")
    if closure.control_binding_schema != CONTROL_BINDING_SCHEMA:
        raise JSpaceModelInputControlClosureError("CONTROL_BINDING_SCHEMA_MISMATCH")
    if closure.inference_receipt_schema != INFERENCE_SCHEMA:
        raise JSpaceModelInputControlClosureError("INFERENCE_RECEIPT_SCHEMA_MISMATCH")
    if closure.jspace_binding_schema != JSPACE_BINDING_SCHEMA:
        raise JSpaceModelInputControlClosureError("JSPACE_BINDING_SCHEMA_MISMATCH")
    _generation(closure.generation, "closure.generation")
    _nonnegative_int(closure.input_size, "closure.input_size")
    for field in (
        "control_admission_sha256",
        "control_binding_sha256",
        "model_execution_observation_sha256",
        "inference_receipt_sha256",
        "jspace_binding_sha256",
        "entry_event_sha256",
        "entry_admission_sha256",
        "route_decision_sha256",
        "grid_plan_sha256",
        "vector_control_packet_sha256",
        "input_sha256",
    ):
        _sha256(getattr(closure, field), f"closure.{field}")
    for field in ("cell_id", "role", "executor_id", "invocation_id"):
        _text(getattr(closure, field), f"closure.{field}")
    material = asdict(closure)
    observed = _sha256(material.pop("closure_sha256", None), "closure.closure_sha256")
    expected = _canonical_sha256(material, "JSPACE_MODEL_INPUT_CONTROL_CLOSURE")
    if observed != expected:
        raise JSpaceModelInputControlClosureError("JSPACE_MODEL_INPUT_CONTROL_CLOSURE_DIGEST_MISMATCH")
