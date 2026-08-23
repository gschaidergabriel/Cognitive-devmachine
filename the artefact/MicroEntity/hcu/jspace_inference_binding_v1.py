#!/usr/bin/env python3
"""Bind an observable J-Space training trace to the real HCU inference receipt chain.

This is deterministic research-evidence binding only. It does not mint truth, reward,
capability, model authority, runtime acceptance, or effects. Its job is to prevent a
training trace from claiming a model outcome unless the same generation, Typed Entry
event/admission, route decision, exact scheduler-owned GRID plan/cell, admitted engine/load
chain, executor-minted model-execution evidence, lane/role and output bytes are bound by
the canonical HCU_INFERENCE_RECEIPT/v4 producer.

InferenceReceipt/v4 carries an explicit output-producing GRID cell and role derived from an
admitted VerifiedModelExecution. Therefore a multi-lane route is no longer ambiguous when
the executor evidence names exactly one output-producing MODEL cell that belongs to the
same exact GRID plan. ``model_call_id`` remains correlation metadata, but v4 derives it
from the executor-minted invocation id rather than accepting an independent caller label.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .grid10_scheduler_v1 import ExecutionClass, GridPlan, GridScheduleError, validate_grid_plan_identity
    from .inference_receipt_v1 import (
        InferenceReceipt,
        SCHEMA as INFERENCE_RECEIPT_SCHEMA,
        STATUS as INFERENCE_RECEIPT_STATUS,
    )
    from .jspace_training_trace_v1 import (
        TRACE_SCHEMA as TRAINING_TRACE_SCHEMA,
        TrainingTrace,
        validate_training_trace,
    )
    from .model_execution_receipt_v1 import VERIFIED_EXECUTION_SCHEMA
    from .reactive_event_router_v1 import ENTRY_BINDING_SCHEMA
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from grid10_scheduler_v1 import ExecutionClass, GridPlan, GridScheduleError, validate_grid_plan_identity
    from inference_receipt_v1 import (
        InferenceReceipt,
        SCHEMA as INFERENCE_RECEIPT_SCHEMA,
        STATUS as INFERENCE_RECEIPT_STATUS,
    )
    from jspace_training_trace_v1 import (
        TRACE_SCHEMA as TRAINING_TRACE_SCHEMA,
        TrainingTrace,
        validate_training_trace,
    )
    from model_execution_receipt_v1 import VERIFIED_EXECUTION_SCHEMA
    from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA

SCHEMA = "ENTITYOS_HCU_JSPACE_INFERENCE_BINDING/v3"


class JSpaceInferenceBindingError(ValueError):
    pass


@dataclass(frozen=True)
class JSpaceInferenceBinding:
    schema: str
    canonicalization_schema: str
    training_trace_schema: str
    training_trace_sha256: str
    prototype_trace_sha256: str
    generation: int
    entry_event_sha256: str
    entry_admission_sha256: str
    route_decision_sha256: str
    grid_plan_sha256: str
    cell_id: str
    role: str
    vector_control_packet_sha256: str
    inference_receipt_schema: str
    inference_receipt_sha256: str
    engine_identity_sha256: str
    resolved_engine_identity: str
    resolved_engine_class: str
    resolved_engine_artifact_sha256: str
    engine_admission_receipt_sha256: str
    engine_load_loader_binding_sha256: str
    engine_load_lease_sha256: str
    engine_load_consumption_receipt_sha256: str
    engine_load_loader_id: str
    model_execution_schema: str
    model_execution_receipt_sha256: str
    model_execution_observation_sha256: str
    model_execution_executor_id: str
    model_execution_invocation_id: str
    input_sha256: str
    input_size: int
    model_call_id: str
    output_ref: str
    output_sha256: str
    output_size: int
    binding_sha256: str


def _text(value: Any, field: str, max_len: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceInferenceBindingError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise JSpaceInferenceBindingError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, 64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceInferenceBindingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise JSpaceInferenceBindingError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _safe_generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceInferenceBindingError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise JSpaceInferenceBindingError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise JSpaceInferenceBindingError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise JSpaceInferenceBindingError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _validate_inference_receipt(receipt: InferenceReceipt) -> None:
    if not isinstance(receipt, InferenceReceipt):
        raise JSpaceInferenceBindingError("HCU_INFERENCE_RECEIPT_REQUIRED")
    if receipt.schema != INFERENCE_RECEIPT_SCHEMA or receipt.status != INFERENCE_RECEIPT_STATUS:
        raise JSpaceInferenceBindingError("HCU_INFERENCE_RECEIPT_SCHEMA_OR_STATUS_UNSUPPORTED")
    if receipt.hash_serialization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceInferenceBindingError("HCU_INFERENCE_RECEIPT_CANONICALIZATION_MISMATCH")
    if receipt.entry_binding_schema != ENTRY_BINDING_SCHEMA:
        raise JSpaceInferenceBindingError("HCU_INFERENCE_RECEIPT_ENTRY_BINDING_SCHEMA_MISMATCH")
    if receipt.engine_load_canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceInferenceBindingError("HCU_INFERENCE_RECEIPT_ENGINE_LOAD_CANONICALIZATION_MISMATCH")
    if receipt.model_execution_schema != VERIFIED_EXECUTION_SCHEMA:
        raise JSpaceInferenceBindingError("HCU_INFERENCE_RECEIPT_MODEL_EXECUTION_SCHEMA_MISMATCH")
    if receipt.model_execution_canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceInferenceBindingError("HCU_INFERENCE_RECEIPT_MODEL_EXECUTION_CANONICALIZATION_MISMATCH")
    _sha256(receipt.model_execution_receipt_sha256, "inference_receipt.model_execution_receipt_sha256")
    _sha256(receipt.model_execution_observation_sha256, "inference_receipt.model_execution_observation_sha256")
    _sha256(receipt.grid_plan_sha256, "inference_receipt.grid_plan_sha256")
    _sha256(receipt.input_sha256, "inference_receipt.input_sha256")
    _text(receipt.output_producing_cell_id, "inference_receipt.output_producing_cell_id", 256)
    _text(receipt.model_execution_role, "inference_receipt.model_execution_role", 256)
    invocation_id = _text(receipt.model_execution_invocation_id, "inference_receipt.model_execution_invocation_id")
    if _text(receipt.model_call_id, "inference_receipt.model_call_id") != invocation_id:
        raise JSpaceInferenceBindingError("INFERENCE_MODEL_CALL_ID_NOT_EXECUTOR_INVOCATION")
    material = asdict(receipt)
    observed = _sha256(material.pop("receipt_sha256", None), "inference_receipt.receipt_sha256")
    expected = _canonical_sha256(material, "HCU_INFERENCE_RECEIPT")
    if observed != expected:
        raise JSpaceInferenceBindingError("HCU_INFERENCE_RECEIPT_DIGEST_MISMATCH")


def bind_training_trace_to_inference(
    training_trace: TrainingTrace,
    inference_receipt: InferenceReceipt,
    grid_plan: GridPlan,
) -> JSpaceInferenceBinding:
    """Create a fail-closed binding from one trace to one executor-proven model cell."""
    if not isinstance(training_trace, TrainingTrace):
        raise JSpaceInferenceBindingError("JSPACE_TRAINING_TRACE_REQUIRED")
    try:
        validate_training_trace(training_trace)
    except Exception as exc:
        raise JSpaceInferenceBindingError(f"JSPACE_TRAINING_TRACE_REJECTED:{exc}") from exc
    _validate_inference_receipt(inference_receipt)
    try:
        validate_grid_plan_identity(grid_plan)
    except GridScheduleError as exc:
        raise JSpaceInferenceBindingError(str(exc)) from exc

    generation = _safe_generation(training_trace.generation, "training_trace.generation")
    if inference_receipt.entity_generation != generation:
        raise JSpaceInferenceBindingError("INFERENCE_GENERATION_MISMATCH")
    if grid_plan.entity_generation != generation:
        raise JSpaceInferenceBindingError("GRID10_GENERATION_MISMATCH")
    if inference_receipt.event_sha256 != training_trace.entry_event_sha256:
        raise JSpaceInferenceBindingError("INFERENCE_ENTRY_EVENT_MISMATCH")
    if inference_receipt.entry_admission_sha256 != training_trace.entry_admission_sha256:
        raise JSpaceInferenceBindingError("INFERENCE_ENTRY_ADMISSION_MISMATCH")
    if inference_receipt.decision_sha256 != training_trace.route_decision_sha256:
        raise JSpaceInferenceBindingError("INFERENCE_ROUTE_DECISION_MISMATCH")
    if grid_plan.entry_event_sha256 != training_trace.entry_event_sha256:
        raise JSpaceInferenceBindingError("GRID10_ENTRY_EVENT_MISMATCH")
    if grid_plan.entry_admission_sha256 != training_trace.entry_admission_sha256:
        raise JSpaceInferenceBindingError("GRID10_ENTRY_ADMISSION_MISMATCH")
    if grid_plan.route_decision_sha256 != training_trace.route_decision_sha256:
        raise JSpaceInferenceBindingError("GRID10_ROUTE_DECISION_MISMATCH")
    if grid_plan.plan_sha256 != training_trace.grid_plan_sha256:
        raise JSpaceInferenceBindingError("GRID10_TRAINING_TRACE_PLAN_MISMATCH")
    if inference_receipt.grid_plan_sha256 != grid_plan.plan_sha256:
        raise JSpaceInferenceBindingError("INFERENCE_GRID10_PLAN_MISMATCH")

    if grid_plan.router_policy_sha256 != inference_receipt.router_policy_sha256:
        raise JSpaceInferenceBindingError("GRID10_INFERENCE_ROUTER_POLICY_MISMATCH")
    if grid_plan.engine_identity_sha256 != inference_receipt.engine_identity_sha256:
        raise JSpaceInferenceBindingError("GRID10_INFERENCE_ENGINE_IDENTITY_MISMATCH")
    if grid_plan.resolved_engine_identity != inference_receipt.resolved_engine_identity:
        raise JSpaceInferenceBindingError("GRID10_INFERENCE_ENGINE_NAME_MISMATCH")
    if grid_plan.resolved_engine_class != inference_receipt.resolved_engine_class:
        raise JSpaceInferenceBindingError("GRID10_INFERENCE_ENGINE_CLASS_MISMATCH")
    if grid_plan.resolved_engine_artifact_sha256 != inference_receipt.resolved_engine_artifact_sha256:
        raise JSpaceInferenceBindingError("GRID10_INFERENCE_ENGINE_ARTIFACT_MISMATCH")

    role = _text(training_trace.role, "training_trace.role", 256)
    lanes = tuple(_text(lane, "inference_receipt.model_lane", 256) for lane in inference_receipt.model_lanes)
    if role not in lanes:
        raise JSpaceInferenceBindingError("INFERENCE_MODEL_LANE_DOES_NOT_BIND_TRACE_ROLE")
    if _text(inference_receipt.model_execution_role, "inference_receipt.model_execution_role", 256) != role:
        raise JSpaceInferenceBindingError("MODEL_EXECUTION_ROLE_DOES_NOT_BIND_TRACE_ROLE")

    cell_id = _text(training_trace.cell_id, "training_trace.cell_id", 256)
    if _text(inference_receipt.output_producing_cell_id, "inference_receipt.output_producing_cell_id", 256) != cell_id:
        raise JSpaceInferenceBindingError("MODEL_EXECUTION_CELL_DOES_NOT_BIND_TRACE_CELL")
    matching_cells = [cell for cell in grid_plan.cells if cell.cell_id == cell_id]
    if len(matching_cells) != 1:
        raise JSpaceInferenceBindingError("GRID10_MODEL_CELL_NOT_UNIQUE")
    model_cell = matching_cells[0]
    if model_cell.execution_class is not ExecutionClass.MODEL:
        raise JSpaceInferenceBindingError("GRID10_MODEL_CELL_DOES_NOT_BIND_TRACE_CELL")
    if model_cell.function != f"MODEL:{role}":
        raise JSpaceInferenceBindingError("GRID10_MODEL_CELL_DOES_NOT_BIND_TRACE_ROLE")

    model_execution_receipt_sha256 = _sha256(
        inference_receipt.model_execution_receipt_sha256,
        "inference_receipt.model_execution_receipt_sha256",
    )
    model_execution_observation_sha256 = _sha256(
        inference_receipt.model_execution_observation_sha256,
        "inference_receipt.model_execution_observation_sha256",
    )
    model_execution_executor_id = _text(
        inference_receipt.model_execution_executor_id,
        "inference_receipt.model_execution_executor_id",
    )
    model_execution_invocation_id = _text(
        inference_receipt.model_execution_invocation_id,
        "inference_receipt.model_execution_invocation_id",
    )

    material = {
        "schema": SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "training_trace_schema": TRAINING_TRACE_SCHEMA,
        "training_trace_sha256": _sha256(training_trace.trace_sha256, "training_trace.trace_sha256"),
        "prototype_trace_sha256": _sha256(training_trace.prototype_trace_sha256, "training_trace.prototype_trace_sha256"),
        "generation": generation,
        "entry_event_sha256": _sha256(training_trace.entry_event_sha256, "training_trace.entry_event_sha256"),
        "entry_admission_sha256": _sha256(training_trace.entry_admission_sha256, "training_trace.entry_admission_sha256"),
        "route_decision_sha256": _sha256(training_trace.route_decision_sha256, "training_trace.route_decision_sha256"),
        "grid_plan_sha256": _sha256(grid_plan.plan_sha256, "grid_plan.plan_sha256"),
        "cell_id": cell_id,
        "role": role,
        "vector_control_packet_sha256": _sha256(training_trace.vector_control_packet_sha256, "training_trace.vector_control_packet_sha256"),
        "inference_receipt_schema": INFERENCE_RECEIPT_SCHEMA,
        "inference_receipt_sha256": _sha256(inference_receipt.receipt_sha256, "inference_receipt.receipt_sha256"),
        "engine_identity_sha256": _sha256(inference_receipt.engine_identity_sha256, "inference_receipt.engine_identity_sha256"),
        "resolved_engine_identity": _text(inference_receipt.resolved_engine_identity, "inference_receipt.resolved_engine_identity"),
        "resolved_engine_class": _text(inference_receipt.resolved_engine_class, "inference_receipt.resolved_engine_class"),
        "resolved_engine_artifact_sha256": _sha256(inference_receipt.resolved_engine_artifact_sha256, "inference_receipt.resolved_engine_artifact_sha256"),
        "engine_admission_receipt_sha256": _sha256(inference_receipt.engine_admission_receipt_sha256, "inference_receipt.engine_admission_receipt_sha256"),
        "engine_load_loader_binding_sha256": _sha256(inference_receipt.engine_load_loader_binding_sha256, "inference_receipt.engine_load_loader_binding_sha256"),
        "engine_load_lease_sha256": _sha256(inference_receipt.engine_load_lease_sha256, "inference_receipt.engine_load_lease_sha256"),
        "engine_load_consumption_receipt_sha256": _sha256(inference_receipt.engine_load_consumption_receipt_sha256, "inference_receipt.engine_load_consumption_receipt_sha256"),
        "engine_load_loader_id": _text(inference_receipt.engine_load_loader_id, "inference_receipt.engine_load_loader_id"),
        "model_execution_schema": VERIFIED_EXECUTION_SCHEMA,
        "model_execution_receipt_sha256": model_execution_receipt_sha256,
        "model_execution_observation_sha256": model_execution_observation_sha256,
        "model_execution_executor_id": model_execution_executor_id,
        "model_execution_invocation_id": model_execution_invocation_id,
        "input_sha256": _sha256(inference_receipt.input_sha256, "inference_receipt.input_sha256"),
        "input_size": _nonnegative_int(inference_receipt.input_size, "inference_receipt.input_size"),
        "model_call_id": model_execution_invocation_id,
        "output_ref": _text(inference_receipt.output_ref, "inference_receipt.output_ref"),
        "output_sha256": _sha256(inference_receipt.output_sha256, "inference_receipt.output_sha256"),
        "output_size": _nonnegative_int(inference_receipt.output_size, "inference_receipt.output_size"),
    }
    binding_sha256 = _canonical_sha256(material, "JSPACE_INFERENCE_BINDING")
    return JSpaceInferenceBinding(**material, binding_sha256=binding_sha256)


def validate_binding(binding: JSpaceInferenceBinding) -> None:
    if not isinstance(binding, JSpaceInferenceBinding):
        raise JSpaceInferenceBindingError("JSPACE_INFERENCE_BINDING_REQUIRED")
    if binding.schema != SCHEMA or binding.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceInferenceBindingError("JSPACE_INFERENCE_BINDING_SCHEMA_UNSUPPORTED")
    material = asdict(binding)
    observed = _sha256(material.pop("binding_sha256", None), "binding.binding_sha256")
    expected = _canonical_sha256(material, "JSPACE_INFERENCE_BINDING")
    if observed != expected:
        raise JSpaceInferenceBindingError("JSPACE_INFERENCE_BINDING_DIGEST_MISMATCH")
