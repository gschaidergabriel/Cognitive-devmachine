#!/usr/bin/env python3
"""Deterministic canonical inference receipt for EntityOS/HCU.

This module invokes no model and grants no truth/effect authority. It consumes the
single canonical route, verified engine admission/load evidence, the scheduler-owned
GRID plan, and a separately verified/admitted actual model-execution receipt.

The output fields are never accepted as independent caller assertions. They are derived
from ``VerifiedModelExecution``, whose exact receipt must already exist in an admitted
registry. Source-level construction still grants zero runtime/model credit until the real
loader/executor boundaries actually emit and admit the underlying observations.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .engine_admission_v1 import ENGINE_ADMISSION_RECEIPT_SCHEMA, VerifiedEngineAdmission
    from .engine_load_lease_v1 import (
        ACTUAL_LOADER_EVIDENCE_SOURCE,
        VERIFIED_LOAD_SCHEMA,
        VerifiedEngineLoad,
    )
    from .grid10_scheduler_v1 import (
        ExecutionClass,
        GridPlan,
        GridScheduleError,
        validate_grid_plan_identity,
    )
    from .model_execution_receipt_v1 import (
        VERIFIED_EXECUTION_SCHEMA,
        ModelExecutionReceiptError,
        VerifiedModelExecution,
        validate_verified_model_execution,
    )
    from .reactive_event_router_v1 import (
        ENTRY_BINDING_SCHEMA,
        HASH_SERIALIZATION_SCHEMA,
        ReactiveRoutingError,
        RouteDecision,
        assert_inference_echo,
        resolve_admitted_entry_binding,
    )
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from engine_admission_v1 import ENGINE_ADMISSION_RECEIPT_SCHEMA, VerifiedEngineAdmission
    from engine_load_lease_v1 import ACTUAL_LOADER_EVIDENCE_SOURCE, VERIFIED_LOAD_SCHEMA, VerifiedEngineLoad
    from grid10_scheduler_v1 import ExecutionClass, GridPlan, GridScheduleError, validate_grid_plan_identity
    from model_execution_receipt_v1 import (
        VERIFIED_EXECUTION_SCHEMA,
        ModelExecutionReceiptError,
        VerifiedModelExecution,
        validate_verified_model_execution,
    )
    from reactive_event_router_v1 import (
        ENTRY_BINDING_SCHEMA,
        HASH_SERIALIZATION_SCHEMA,
        ReactiveRoutingError,
        RouteDecision,
        assert_inference_echo,
        resolve_admitted_entry_binding,
    )

SCHEMA = "HCU_INFERENCE_RECEIPT/v4"
STATUS = "CANDIDATE_ONLY"


class InferenceReceiptError(ValueError):
    pass


@dataclass(frozen=True)
class InferenceReceipt:
    schema: str
    status: str
    hash_serialization_schema: str
    entry_binding_schema: str
    entity_generation: int
    entry_admission_sha256: str
    event_sha256: str
    decision_sha256: str
    router_policy_sha256: str
    engine_identity_sha256: str
    resolved_engine_identity: str
    resolved_engine_class: str
    resolved_engine_artifact_sha256: str
    engine_admission_receipt_sha256: str
    engine_load_canonicalization_schema: str
    engine_load_loader_binding_sha256: str
    engine_load_lease_sha256: str
    engine_load_consumption_receipt_sha256: str
    engine_load_loader_id: str
    model_execution_canonicalization_schema: str
    model_execution_receipt_sha256: str
    model_execution_observation_sha256: str
    model_execution_executor_id: str
    model_execution_invocation_id: str
    grid_plan_sha256: str
    output_producing_cell_id: str
    model_execution_role: str
    input_sha256: str
    input_size: int
    model_call_id: str
    output_ref: str
    output_sha256: str
    output_size: int
    model_lanes: tuple[str, ...]
    receipt_sha256: str


def _canonical(value: Any) -> bytes:
    try:
        return canonicalize(value)
    except CanonicalizationError as exc:
        raise InferenceReceiptError(f"CANONICALIZATION_FAILED:{exc}") from exc


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise InferenceReceiptError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    value = value.strip()
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise InferenceReceiptError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise InferenceReceiptError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _text(value: Any, field: str, max_len: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InferenceReceiptError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise InferenceReceiptError(f"{field}:TOO_LONG")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InferenceReceiptError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _generation(
    decision: RouteDecision,
    *,
    current_generation: int,
    admitted_route_generations: Mapping[str, Any],
) -> int:
    current_generation = _nonnegative_int(current_generation, "current_generation")
    if not isinstance(admitted_route_generations, Mapping):
        raise InferenceReceiptError("ADMITTED_ROUTE_GENERATION_REGISTRY_REQUIRED")
    bound_generation = admitted_route_generations.get(decision.decision_sha256)
    if bound_generation is None:
        raise InferenceReceiptError("ROUTE_GENERATION_NOT_ADMITTED")
    bound_generation = _nonnegative_int(bound_generation, "admitted_route_generation")
    if bound_generation != current_generation:
        raise InferenceReceiptError("STALE_ROUTE_GENERATION")
    return bound_generation


def _artifact_material(value: Any, field: str, *, require_loader_evidence: bool = False) -> dict[str, Any]:
    material = {
        "kind": _text(getattr(value, "kind", None), f"{field}.kind"),
        "sha256": _sha256(getattr(value, "sha256", None), f"{field}.sha256"),
        "file_count": _nonnegative_int(getattr(value, "file_count", None), f"{field}.file_count"),
        "byte_count": _nonnegative_int(getattr(value, "byte_count", None), f"{field}.byte_count"),
    }
    if require_loader_evidence:
        evidence_source = _text(getattr(value, "evidence_source", None), f"{field}.evidence_source")
        if evidence_source != ACTUAL_LOADER_EVIDENCE_SOURCE:
            raise InferenceReceiptError(f"{field}:ACTUAL_LOADER_READ_EVIDENCE_REQUIRED")
        material["evidence_source"] = evidence_source
    return material


def _verify_engine_admission(
    verified: VerifiedEngineAdmission,
    *,
    admitted_engine_admission_receipts: Mapping[str, Any],
    generation: int,
    expected_engine_identity: str,
    expected_engine_class: str,
    expected_engine_artifact_sha256: str,
) -> str:
    if not isinstance(verified, VerifiedEngineAdmission):
        raise InferenceReceiptError("VERIFIED_ENGINE_ADMISSION_REQUIRED")
    if verified.entity_generation != generation:
        raise InferenceReceiptError("STALE_ENGINE_ADMISSION_RECEIPT_GENERATION")
    if verified.admission.engine_identity != expected_engine_identity:
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_IDENTITY_MISMATCH")
    if verified.admission.engine_class != expected_engine_class:
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_CLASS_MISMATCH")
    if verified.engine_artifact_sha256 != expected_engine_artifact_sha256:
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_ARTIFACT_MISMATCH")
    if verified.admission.engine_artifact_sha256 != verified.engine_artifact_sha256:
        raise InferenceReceiptError("ENGINE_ADMISSION_ARTIFACT_IDENTITY_MISMATCH")

    receipt = verified.receipt()
    if receipt.get("schema") != ENGINE_ADMISSION_RECEIPT_SCHEMA:
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_SCHEMA_UNSUPPORTED")
    if receipt.get("hash_serialization_schema") != CANONICALIZATION_SCHEMA:
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    if CANONICALIZATION_SCHEMA != HASH_SERIALIZATION_SCHEMA:
        raise InferenceReceiptError("ENGINE_ROUTER_CANONICALIZATION_SCHEMA_MISMATCH")

    receipt_sha256 = _sha256(receipt.get("receipt_sha256"), "engine_admission_receipt.receipt_sha256")
    if receipt_sha256 != _sha256(verified.receipt_sha256, "verified_engine_admission.receipt_sha256"):
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_IDENTITY_MISMATCH")
    material = dict(receipt)
    material.pop("receipt_sha256")
    if hashlib.sha256(_canonical(material)).hexdigest() != receipt_sha256:
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_DIGEST_MISMATCH")

    if not isinstance(admitted_engine_admission_receipts, Mapping):
        raise InferenceReceiptError("ADMITTED_ENGINE_ADMISSION_RECEIPT_REGISTRY_REQUIRED")
    admitted = admitted_engine_admission_receipts.get(receipt_sha256)
    if not isinstance(admitted, Mapping):
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_NOT_ADMITTED")
    if dict(admitted) != receipt:
        raise InferenceReceiptError("ENGINE_ADMISSION_RECEIPT_REGISTRY_MISMATCH")
    return receipt_sha256


def _verified_load_receipt(load: VerifiedEngineLoad) -> dict[str, Any]:
    material = {
        "schema": VERIFIED_LOAD_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "entity_generation": load.entity_generation,
        "loader_id": load.loader_id,
        "loader_binding_sha256": load.loader_binding_sha256,
        "engine_admission_receipt_sha256": load.engine_admission_receipt_sha256,
        "engine_load_lease_sha256": load.engine_load_lease_sha256,
        "engine_identity": load.engine_identity,
        "engine_class": load.engine_class,
        "engine_artifact_sha256": load.engine_artifact_sha256,
        "checkpoint": _artifact_material(load.checkpoint, "verified_engine_load.checkpoint", require_loader_evidence=True),
        "tokenizer": _artifact_material(load.tokenizer, "verified_engine_load.tokenizer", require_loader_evidence=True),
        "runtime": _artifact_material(load.runtime, "verified_engine_load.runtime", require_loader_evidence=True),
        "build": _artifact_material(load.build, "verified_engine_load.build", require_loader_evidence=True),
    }
    receipt_sha256 = _sha256(load.consumption_receipt_sha256, "verified_engine_load.consumption_receipt_sha256")
    if hashlib.sha256(_canonical(material)).hexdigest() != receipt_sha256:
        raise InferenceReceiptError("VERIFIED_ENGINE_LOAD_DIGEST_MISMATCH")
    return {**material, "consumption_receipt_sha256": receipt_sha256}


def _verify_engine_load(
    verified_load: VerifiedEngineLoad,
    *,
    admitted_verified_engine_loads: Mapping[str, Any],
    generation: int,
    expected_engine_admission_receipt_sha256: str,
    expected_engine_identity: str,
    expected_engine_class: str,
    expected_engine_artifact_sha256: str,
) -> dict[str, Any]:
    if not isinstance(verified_load, VerifiedEngineLoad):
        raise InferenceReceiptError("VERIFIED_ENGINE_LOAD_REQUIRED")
    if verified_load.schema != VERIFIED_LOAD_SCHEMA:
        raise InferenceReceiptError("VERIFIED_ENGINE_LOAD_SCHEMA_UNSUPPORTED")
    if verified_load.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise InferenceReceiptError("VERIFIED_ENGINE_LOAD_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    if verified_load.entity_generation != generation:
        raise InferenceReceiptError("STALE_VERIFIED_ENGINE_LOAD_GENERATION")
    if verified_load.engine_admission_receipt_sha256 != expected_engine_admission_receipt_sha256:
        raise InferenceReceiptError("VERIFIED_ENGINE_LOAD_ADMISSION_RECEIPT_MISMATCH")
    if verified_load.engine_identity != expected_engine_identity:
        raise InferenceReceiptError("VERIFIED_ENGINE_LOAD_IDENTITY_MISMATCH")
    if verified_load.engine_class != expected_engine_class:
        raise InferenceReceiptError("VERIFIED_ENGINE_LOAD_CLASS_MISMATCH")
    if verified_load.engine_artifact_sha256 != expected_engine_artifact_sha256:
        raise InferenceReceiptError("VERIFIED_ENGINE_LOAD_ARTIFACT_MISMATCH")

    receipt = _verified_load_receipt(verified_load)
    receipt_sha256 = receipt["consumption_receipt_sha256"]
    if not isinstance(admitted_verified_engine_loads, Mapping):
        raise InferenceReceiptError("ADMITTED_VERIFIED_ENGINE_LOAD_REGISTRY_REQUIRED")
    admitted = admitted_verified_engine_loads.get(receipt_sha256)
    if not isinstance(admitted, Mapping):
        raise InferenceReceiptError("VERIFIED_ENGINE_LOAD_NOT_ADMITTED")
    if dict(admitted) != receipt:
        raise InferenceReceiptError("VERIFIED_ENGINE_LOAD_REGISTRY_MISMATCH")
    return verified_load.inference_echo()


def _verify_grid_plan(
    grid_plan: GridPlan,
    decision: RouteDecision,
    *,
    generation: int,
    entry_admission_sha256: str,
) -> None:
    try:
        validate_grid_plan_identity(grid_plan)
    except GridScheduleError as exc:
        raise InferenceReceiptError(f"GRID10_PLAN_REJECTED:{exc}") from exc
    if grid_plan.entity_generation != generation:
        raise InferenceReceiptError("GRID10_INFERENCE_GENERATION_MISMATCH")
    if grid_plan.entry_event_sha256 != decision.event_sha256:
        raise InferenceReceiptError("GRID10_INFERENCE_ENTRY_EVENT_MISMATCH")
    if grid_plan.entry_admission_sha256 != entry_admission_sha256:
        raise InferenceReceiptError("GRID10_INFERENCE_ENTRY_ADMISSION_MISMATCH")
    if grid_plan.route_decision_sha256 != decision.decision_sha256:
        raise InferenceReceiptError("GRID10_INFERENCE_ROUTE_DECISION_MISMATCH")
    if grid_plan.router_policy_sha256 != decision.router_policy_sha256:
        raise InferenceReceiptError("GRID10_INFERENCE_ROUTER_POLICY_MISMATCH")
    if grid_plan.engine_identity_sha256 != decision.engine_identity_sha256:
        raise InferenceReceiptError("GRID10_INFERENCE_ENGINE_IDENTITY_MISMATCH")
    if grid_plan.resolved_engine_identity != decision.resolved_engine_identity:
        raise InferenceReceiptError("GRID10_INFERENCE_ENGINE_NAME_MISMATCH")
    if grid_plan.resolved_engine_class != decision.resolved_engine_class:
        raise InferenceReceiptError("GRID10_INFERENCE_ENGINE_CLASS_MISMATCH")
    if grid_plan.resolved_engine_artifact_sha256 != decision.resolved_engine_artifact_sha256:
        raise InferenceReceiptError("GRID10_INFERENCE_ENGINE_ARTIFACT_MISMATCH")


def _verify_model_execution(
    verified: VerifiedModelExecution,
    *,
    admitted_verified_model_executions: Mapping[str, Any],
    grid_plan: GridPlan,
    generation: int,
    expected_engine_load_consumption_receipt_sha256: str,
    expected_engine_identity: str,
    expected_engine_class: str,
    expected_engine_artifact_sha256: str,
    model_lanes: tuple[str, ...],
) -> dict[str, Any]:
    if not isinstance(verified, VerifiedModelExecution):
        raise InferenceReceiptError("VERIFIED_MODEL_EXECUTION_REQUIRED")
    try:
        validate_verified_model_execution(verified)
    except ModelExecutionReceiptError as exc:
        raise InferenceReceiptError(f"VERIFIED_MODEL_EXECUTION_REJECTED:{exc}") from exc
    if verified.schema != VERIFIED_EXECUTION_SCHEMA:
        raise InferenceReceiptError("VERIFIED_MODEL_EXECUTION_SCHEMA_UNSUPPORTED")
    if verified.entity_generation != generation:
        raise InferenceReceiptError("STALE_VERIFIED_MODEL_EXECUTION_GENERATION")
    if verified.engine_load_consumption_receipt_sha256 != expected_engine_load_consumption_receipt_sha256:
        raise InferenceReceiptError("MODEL_EXECUTION_ENGINE_LOAD_RECEIPT_MISMATCH")
    if verified.engine_identity != expected_engine_identity:
        raise InferenceReceiptError("MODEL_EXECUTION_ENGINE_IDENTITY_MISMATCH")
    if verified.engine_class != expected_engine_class:
        raise InferenceReceiptError("MODEL_EXECUTION_ENGINE_CLASS_MISMATCH")
    if verified.engine_artifact_sha256 != expected_engine_artifact_sha256:
        raise InferenceReceiptError("MODEL_EXECUTION_ENGINE_ARTIFACT_MISMATCH")
    if verified.grid_plan_sha256 != grid_plan.plan_sha256:
        raise InferenceReceiptError("MODEL_EXECUTION_GRID10_PLAN_MISMATCH")

    matching_cells = [cell for cell in grid_plan.cells if cell.cell_id == verified.output_producing_cell_id]
    if len(matching_cells) != 1:
        raise InferenceReceiptError("MODEL_EXECUTION_OUTPUT_CELL_NOT_UNIQUE_IN_GRID10_PLAN")
    cell = matching_cells[0]
    if cell.execution_class is not ExecutionClass.MODEL:
        raise InferenceReceiptError("MODEL_EXECUTION_OUTPUT_CELL_NOT_MODEL")
    if cell.function != f"MODEL:{verified.role}":
        raise InferenceReceiptError("MODEL_EXECUTION_OUTPUT_CELL_ROLE_MISMATCH")
    if verified.role not in model_lanes:
        raise InferenceReceiptError("MODEL_EXECUTION_ROLE_NOT_IN_ROUTE_MODEL_LANES")

    receipt = asdict(verified)
    receipt_sha256 = _sha256(receipt.get("receipt_sha256"), "verified_model_execution.receipt_sha256")
    if not isinstance(admitted_verified_model_executions, Mapping):
        raise InferenceReceiptError("ADMITTED_VERIFIED_MODEL_EXECUTION_REGISTRY_REQUIRED")
    admitted = admitted_verified_model_executions.get(receipt_sha256)
    if not isinstance(admitted, Mapping):
        raise InferenceReceiptError("VERIFIED_MODEL_EXECUTION_NOT_ADMITTED")
    if dict(admitted) != receipt:
        raise InferenceReceiptError("VERIFIED_MODEL_EXECUTION_REGISTRY_MISMATCH")
    return verified.inference_echo()


def make_inference_receipt(
    decision: RouteDecision,
    *,
    current_generation: int,
    admitted_route_generations: Mapping[str, Any],
    entry_admission_sha256: str,
    admitted_entry_bindings: Mapping[str, Any],
    admitted_engine_artifacts: Mapping[str, Any],
    verified_engine_admission: VerifiedEngineAdmission,
    admitted_engine_admission_receipts: Mapping[str, Any],
    verified_engine_load: VerifiedEngineLoad,
    admitted_verified_engine_loads: Mapping[str, Any],
    grid_plan: GridPlan,
    verified_model_execution: VerifiedModelExecution,
    admitted_verified_model_executions: Mapping[str, Any],
) -> InferenceReceipt:
    """Produce a candidate-only v4 receipt from admitted route/load/execution evidence."""
    if not isinstance(decision, RouteDecision):
        raise InferenceReceiptError("ROUTE_DECISION_REQUIRED")
    if decision.status != "SELECTIVE_MODEL_ACTIVATION":
        raise InferenceReceiptError("MODEL_ACTIVATION_ROUTE_REQUIRED")
    if decision.hash_serialization_schema != HASH_SERIALIZATION_SCHEMA or HASH_SERIALIZATION_SCHEMA != CANONICALIZATION_SCHEMA:
        raise InferenceReceiptError("ROUTE_CANONICALIZATION_SCHEMA_UNSUPPORTED")

    generation = _generation(
        decision,
        current_generation=current_generation,
        admitted_route_generations=admitted_route_generations,
    )
    admission_sha256 = _sha256(entry_admission_sha256, "entry_admission_sha256")
    if decision.entry_admission_sha256 != admission_sha256:
        raise InferenceReceiptError("ROUTE_ENTRY_ADMISSION_IDENTITY_MISMATCH")
    try:
        resolve_admitted_entry_binding(
            admitted_entry_bindings,
            admission_sha256,
            expected_event_sha256=decision.event_sha256,
        )
    except ReactiveRoutingError as exc:
        raise InferenceReceiptError(f"ENTRY_BINDING_REJECTED:{exc}") from exc

    engine_id = _text(decision.resolved_engine_identity, "resolved_engine_identity")
    engine_class = _text(decision.resolved_engine_class, "resolved_engine_class")
    engine_artifact_sha256 = _sha256(decision.resolved_engine_artifact_sha256, "resolved_engine_artifact_sha256")
    engine_identity_sha256 = _sha256(decision.engine_identity_sha256, "engine_identity_sha256")
    if not isinstance(admitted_engine_artifacts, Mapping):
        raise InferenceReceiptError("ADMITTED_ENGINE_ARTIFACT_REGISTRY_REQUIRED")
    current_engine_artifact = admitted_engine_artifacts.get(engine_id)
    if current_engine_artifact is None:
        raise InferenceReceiptError("ENGINE_ARTIFACT_NOT_CURRENTLY_ADMITTED")
    if _sha256(current_engine_artifact, "admitted_engine_artifact_sha256") != engine_artifact_sha256:
        raise InferenceReceiptError("ENGINE_ARTIFACT_ADMISSION_MISMATCH")

    engine_admission_receipt_sha256 = _verify_engine_admission(
        verified_engine_admission,
        admitted_engine_admission_receipts=admitted_engine_admission_receipts,
        generation=generation,
        expected_engine_identity=engine_id,
        expected_engine_class=engine_class,
        expected_engine_artifact_sha256=engine_artifact_sha256,
    )
    load_echo = _verify_engine_load(
        verified_engine_load,
        admitted_verified_engine_loads=admitted_verified_engine_loads,
        generation=generation,
        expected_engine_admission_receipt_sha256=engine_admission_receipt_sha256,
        expected_engine_identity=engine_id,
        expected_engine_class=engine_class,
        expected_engine_artifact_sha256=engine_artifact_sha256,
    )
    if load_echo.get("engine_load_canonicalization_schema") != CANONICALIZATION_SCHEMA:
        raise InferenceReceiptError("ENGINE_LOAD_ECHO_CANONICALIZATION_SCHEMA_UNSUPPORTED")

    _verify_grid_plan(
        grid_plan,
        decision,
        generation=generation,
        entry_admission_sha256=admission_sha256,
    )
    model_lanes = tuple(_text(lane, "model_lane", 256) for lane in decision.model_lanes)
    execution_echo = _verify_model_execution(
        verified_model_execution,
        admitted_verified_model_executions=admitted_verified_model_executions,
        grid_plan=grid_plan,
        generation=generation,
        expected_engine_load_consumption_receipt_sha256=load_echo["engine_load_consumption_receipt_sha256"],
        expected_engine_identity=engine_id,
        expected_engine_class=engine_class,
        expected_engine_artifact_sha256=engine_artifact_sha256,
        model_lanes=model_lanes,
    )

    payload = {
        "schema": SCHEMA,
        "status": STATUS,
        "hash_serialization_schema": CANONICALIZATION_SCHEMA,
        "entry_binding_schema": ENTRY_BINDING_SCHEMA,
        "entity_generation": generation,
        "entry_admission_sha256": admission_sha256,
        "event_sha256": decision.event_sha256,
        "decision_sha256": decision.decision_sha256,
        "router_policy_sha256": decision.router_policy_sha256,
        "engine_identity_sha256": engine_identity_sha256,
        "resolved_engine_identity": engine_id,
        "resolved_engine_class": engine_class,
        "resolved_engine_artifact_sha256": engine_artifact_sha256,
        "engine_admission_receipt_sha256": engine_admission_receipt_sha256,
        "engine_load_canonicalization_schema": load_echo["engine_load_canonicalization_schema"],
        "engine_load_loader_binding_sha256": load_echo["engine_load_loader_binding_sha256"],
        "engine_load_lease_sha256": load_echo["engine_load_lease_sha256"],
        "engine_load_consumption_receipt_sha256": load_echo["engine_load_consumption_receipt_sha256"],
        "engine_load_loader_id": load_echo["engine_load_loader_id"],
        "model_execution_canonicalization_schema": execution_echo["model_execution_canonicalization_schema"],
        "model_execution_receipt_sha256": execution_echo["model_execution_receipt_sha256"],
        "model_execution_observation_sha256": execution_echo["model_execution_observation_sha256"],
        "model_execution_executor_id": execution_echo["model_execution_executor_id"],
        "model_execution_invocation_id": execution_echo["model_execution_invocation_id"],
        "grid_plan_sha256": execution_echo["grid_plan_sha256"],
        "output_producing_cell_id": execution_echo["output_producing_cell_id"],
        "model_execution_role": execution_echo["model_execution_role"],
        "input_sha256": execution_echo["input_sha256"],
        "input_size": execution_echo["input_size"],
        "model_call_id": execution_echo["model_execution_invocation_id"],
        "output_ref": execution_echo["output_ref"],
        "output_sha256": execution_echo["output_sha256"],
        "output_size": execution_echo["output_size"],
        "model_lanes": model_lanes,
    }
    receipt_sha256 = hashlib.sha256(_canonical(payload)).hexdigest()
    receipt = InferenceReceipt(**payload, receipt_sha256=receipt_sha256)
    assert_inference_echo(decision, asdict(receipt))
    return receipt


def receipt_json(receipt: InferenceReceipt) -> str:
    if not isinstance(receipt, InferenceReceipt):
        raise InferenceReceiptError("INFERENCE_RECEIPT_REQUIRED")
    return json.dumps(asdict(receipt), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
