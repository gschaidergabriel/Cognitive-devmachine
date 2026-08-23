#!/usr/bin/env python3
"""Plan-bound scheduled inference evidence for the retained EntityOS/HCU path.

This module closes one downstream causal-evidence seam only: a canonical inference receipt
must remain bound to the exact admitted GRID10 v2 plan, capacity and MODEL cell/lane that
scheduled the computation. It does not route, schedule, load a model, mint truth, grant
capability/engine authority, or authorize effects.

All identity material is RFC8785/JCS and reuses the retained Entry/router/GRID/inference
contracts. No legacy plan digest is relabelled under a newer schema.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .grid10_scheduler_v1 import ExecutionClass, GridPlan, HCUMode, PLAN_SCHEMA
    from .inference_receipt_v1 import InferenceReceipt, make_inference_receipt
    from .reactive_event_router_v1 import ENTRY_BINDING_SCHEMA, HASH_SERIALIZATION_SCHEMA, RouteDecision
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from grid10_scheduler_v1 import ExecutionClass, GridPlan, HCUMode, PLAN_SCHEMA
    from inference_receipt_v1 import InferenceReceipt, make_inference_receipt
    from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA, HASH_SERIALIZATION_SCHEMA, RouteDecision

SCHEMA = "HCU_SCHEDULED_INFERENCE_RECEIPT/v4"
STATUS = "CANDIDATE_ONLY"
GRID_PLAN_BINDING_SCHEMA = "ENTITYOS_HCU_GRID_PLAN_ADMISSION_BINDING/v1"
GRID_PLAN_BINDING_FIELDS = frozenset(
    {
        "schema",
        "canonicalization_schema",
        "entry_binding_schema",
        "grid_plan_schema",
        "grid_plan_sha256",
        "route_decision_sha256",
        "entity_generation",
        "capacity_receipt_sha256",
    }
)


class ScheduledInferenceReceiptError(ValueError):
    pass


@dataclass(frozen=True)
class ScheduledInferenceReceipt:
    schema: str
    status: str
    canonicalization_schema: str
    entry_binding_schema: str
    inner_receipt_schema: str
    inner_receipt_sha256: str
    entity_generation: int
    entry_admission_sha256: str
    event_sha256: str
    decision_sha256: str
    router_policy_sha256: str
    engine_identity_sha256: str
    engine_admission_receipt_sha256: str
    engine_load_consumption_receipt_sha256: str
    grid_plan_schema: str
    grid_plan_sha256: str
    grid_plan_admission_sha256: str
    grid_cell_id: str
    model_lane: str
    physical_decoder_lane: int
    model_token_budget: int
    capacity_receipt_sha256: str
    runtime_profile_id: str
    model_call_id: str
    output_sha256: str
    output_size: int
    receipt_sha256: str


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScheduledInferenceReceiptError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > 1024:
        raise ScheduledInferenceReceiptError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise ScheduledInferenceReceiptError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise ScheduledInferenceReceiptError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ScheduledInferenceReceiptError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _positive_int(value: Any, field: str) -> int:
    value = _nonnegative_int(value, field)
    if value == 0:
        raise ScheduledInferenceReceiptError(f"{field}:POSITIVE_INTEGER_REQUIRED")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise ScheduledInferenceReceiptError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _grid_plan_material(plan: GridPlan) -> dict[str, Any]:
    if not isinstance(plan, GridPlan):
        raise ScheduledInferenceReceiptError("GRID_PLAN_REQUIRED")
    cells: list[dict[str, Any]] = []
    for cell in plan.cells:
        if not isinstance(cell.execution_class, ExecutionClass):
            raise ScheduledInferenceReceiptError("GRID_CELL_EXECUTION_CLASS_INVALID")
        physical_lane = cell.physical_decoder_lane
        if physical_lane is not None:
            physical_lane = _nonnegative_int(physical_lane, "grid_cell.physical_decoder_lane")
        cells.append(
            {
                "cell_id": _text(cell.cell_id, "grid_cell.cell_id"),
                "function": _text(cell.function, "grid_cell.function"),
                "execution_class": cell.execution_class.value,
                "model_token_budget": _nonnegative_int(cell.model_token_budget, "grid_cell.model_token_budget"),
                "physical_decoder_lane": physical_lane,
            }
        )
    return {
        "schema": plan.schema,
        "canonicalization_schema": plan.canonicalization_schema,
        "entry_binding_schema": plan.entry_binding_schema,
        "ingress_id": _text(plan.ingress_id, "grid_plan.ingress_id"),
        "causal_id": _text(plan.causal_id, "grid_plan.causal_id"),
        "entity_generation": _nonnegative_int(plan.entity_generation, "grid_plan.entity_generation"),
        "entry_event_sha256": _sha256(plan.entry_event_sha256, "grid_plan.entry_event_sha256"),
        "entry_admission_sha256": _sha256(plan.entry_admission_sha256, "grid_plan.entry_admission_sha256"),
        "route_event_sha256": _sha256(plan.route_event_sha256, "grid_plan.route_event_sha256"),
        "route_decision_sha256": _sha256(plan.route_decision_sha256, "grid_plan.route_decision_sha256"),
        "router_policy_sha256": _sha256(plan.router_policy_sha256, "grid_plan.router_policy_sha256"),
        "engine_identity_sha256": _sha256(plan.engine_identity_sha256, "grid_plan.engine_identity_sha256"),
        "resolved_engine_identity": _text(plan.resolved_engine_identity, "grid_plan.resolved_engine_identity"),
        "resolved_engine_class": _text(plan.resolved_engine_class, "grid_plan.resolved_engine_class"),
        "resolved_engine_artifact_sha256": _sha256(
            plan.resolved_engine_artifact_sha256,
            "grid_plan.resolved_engine_artifact_sha256",
        ),
        "capacity_receipt_sha256": _sha256(plan.capacity_receipt_sha256, "grid_plan.capacity_receipt_sha256"),
        "runtime_profile_id": _text(plan.runtime_profile_id, "grid_plan.runtime_profile_id"),
        "mode": plan.mode.value if isinstance(plan.mode, HCUMode) else None,
        "logical_cell_count": _positive_int(plan.logical_cell_count, "grid_plan.logical_cell_count"),
        "model_call_count": _positive_int(plan.model_call_count, "grid_plan.model_call_count"),
        "physical_decoder_limit": _positive_int(plan.physical_decoder_limit, "grid_plan.physical_decoder_limit"),
        "max_wall_ms": _positive_int(plan.max_wall_ms, "grid_plan.max_wall_ms"),
        "cells": cells,
    }


def _verify_grid_plan(
    decision: RouteDecision,
    plan: GridPlan,
    *,
    current_generation: int,
    entry_admission_sha256: str,
    admitted_grid_plan_bindings: Mapping[str, Any],
    grid_cell_id: str,
    model_lane: str,
) -> tuple[str, str, str, str, int, int, str]:
    if not isinstance(plan, GridPlan):
        raise ScheduledInferenceReceiptError("GRID_PLAN_REQUIRED")
    if plan.schema != PLAN_SCHEMA:
        raise ScheduledInferenceReceiptError("GRID_PLAN_SCHEMA_UNSUPPORTED")
    if plan.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise ScheduledInferenceReceiptError("GRID_PLAN_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    if plan.entry_binding_schema != ENTRY_BINDING_SCHEMA:
        raise ScheduledInferenceReceiptError("GRID_PLAN_ENTRY_BINDING_SCHEMA_UNSUPPORTED")
    if HASH_SERIALIZATION_SCHEMA != CANONICALIZATION_SCHEMA or decision.hash_serialization_schema != CANONICALIZATION_SCHEMA:
        raise ScheduledInferenceReceiptError("ROUTE_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    if not isinstance(plan.mode, HCUMode) or plan.mode is not HCUMode.GRID10:
        raise ScheduledInferenceReceiptError("GRID_PLAN_MODE_UNSUPPORTED")

    plan_sha256 = _sha256(plan.plan_sha256, "grid_plan_sha256")
    if _canonical_sha256(_grid_plan_material(plan), "GRID_PLAN") != plan_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_DIGEST_MISMATCH")

    generation = _nonnegative_int(current_generation, "current_generation")
    if plan.entity_generation != generation:
        raise ScheduledInferenceReceiptError("GRID_PLAN_GENERATION_MISMATCH")
    admission_sha256 = _sha256(entry_admission_sha256, "entry_admission_sha256")
    if plan.entry_admission_sha256 != admission_sha256 or decision.entry_admission_sha256 != admission_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_ENTRY_ADMISSION_MISMATCH")
    if plan.entry_event_sha256 != decision.event_sha256 or plan.route_event_sha256 != decision.event_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_EVENT_MISMATCH")
    if plan.route_decision_sha256 != decision.decision_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_ROUTE_DECISION_MISMATCH")
    if plan.router_policy_sha256 != decision.router_policy_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_ROUTER_POLICY_MISMATCH")
    if plan.engine_identity_sha256 != decision.engine_identity_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_ENGINE_IDENTITY_MISMATCH")
    if plan.resolved_engine_identity != decision.resolved_engine_identity or plan.resolved_engine_class != decision.resolved_engine_class:
        raise ScheduledInferenceReceiptError("GRID_PLAN_ENGINE_SELECTION_MISMATCH")
    if plan.resolved_engine_artifact_sha256 != decision.resolved_engine_artifact_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_ENGINE_ARTIFACT_MISMATCH")

    if not isinstance(admitted_grid_plan_bindings, Mapping):
        raise ScheduledInferenceReceiptError("ADMITTED_GRID_PLAN_BINDING_REGISTRY_REQUIRED")
    binding = admitted_grid_plan_bindings.get(plan_sha256)
    if not isinstance(binding, Mapping):
        raise ScheduledInferenceReceiptError("GRID_PLAN_NOT_ADMITTED")
    if set(binding) != GRID_PLAN_BINDING_FIELDS:
        raise ScheduledInferenceReceiptError("GRID_PLAN_BINDING_SCHEMA_MISMATCH")
    if binding.get("schema") != GRID_PLAN_BINDING_SCHEMA:
        raise ScheduledInferenceReceiptError("GRID_PLAN_BINDING_VERSION_UNSUPPORTED")
    if binding.get("canonicalization_schema") != CANONICALIZATION_SCHEMA:
        raise ScheduledInferenceReceiptError("GRID_PLAN_BINDING_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    if binding.get("entry_binding_schema") != ENTRY_BINDING_SCHEMA:
        raise ScheduledInferenceReceiptError("GRID_PLAN_BINDING_ENTRY_SCHEMA_UNSUPPORTED")
    if binding.get("grid_plan_schema") != PLAN_SCHEMA:
        raise ScheduledInferenceReceiptError("GRID_PLAN_BINDING_PLAN_SCHEMA_UNSUPPORTED")
    if _sha256(binding.get("grid_plan_sha256"), "grid_plan_binding.grid_plan_sha256") != plan_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_BINDING_DIGEST_MISMATCH")
    if _sha256(binding.get("route_decision_sha256"), "grid_plan_binding.route_decision_sha256") != decision.decision_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_BINDING_ROUTE_MISMATCH")
    if _nonnegative_int(binding.get("entity_generation"), "grid_plan_binding.entity_generation") != generation:
        raise ScheduledInferenceReceiptError("GRID_PLAN_BINDING_GENERATION_MISMATCH")
    capacity_sha256 = _sha256(plan.capacity_receipt_sha256, "capacity_receipt_sha256")
    if _sha256(binding.get("capacity_receipt_sha256"), "grid_plan_binding.capacity_receipt_sha256") != capacity_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_BINDING_CAPACITY_MISMATCH")
    binding_sha256 = _canonical_sha256(dict(binding), "GRID_PLAN_ADMISSION_BINDING")

    cell_id = _text(grid_cell_id, "grid_cell_id")
    lane = _text(model_lane, "model_lane")
    if lane not in tuple(decision.model_lanes):
        raise ScheduledInferenceReceiptError("MODEL_LANE_NOT_IN_ROUTE")
    matches = [cell for cell in plan.cells if cell.cell_id == cell_id]
    if len(matches) != 1:
        raise ScheduledInferenceReceiptError("GRID_MODEL_CELL_NOT_FOUND")
    cell = matches[0]
    if cell.execution_class is not ExecutionClass.MODEL:
        raise ScheduledInferenceReceiptError("GRID_CELL_NOT_MODEL_EXECUTION")
    if cell.function != f"MODEL:{lane}":
        raise ScheduledInferenceReceiptError("GRID_CELL_MODEL_LANE_MISMATCH")
    token_budget = _positive_int(cell.model_token_budget, "grid_cell.model_token_budget")
    physical_lane = _nonnegative_int(cell.physical_decoder_lane, "grid_cell.physical_decoder_lane")
    if physical_lane >= plan.physical_decoder_limit:
        raise ScheduledInferenceReceiptError("GRID_CELL_PHYSICAL_LANE_OUT_OF_RANGE")

    return plan_sha256, binding_sha256, cell_id, lane, physical_lane, token_budget, capacity_sha256


def make_scheduled_inference_receipt(
    decision: RouteDecision,
    *,
    grid_plan: GridPlan,
    admitted_grid_plan_bindings: Mapping[str, Any],
    grid_cell_id: str,
    model_lane: str,
    current_generation: int,
    admitted_route_generations: Mapping[str, Any],
    entry_admission_sha256: str,
    admitted_entry_bindings: Mapping[str, Any],
    admitted_engine_artifacts: Mapping[str, Any],
    verified_engine_admission: Any,
    admitted_engine_admission_receipts: Mapping[str, Any],
    verified_engine_load: Any,
    admitted_verified_engine_loads: Mapping[str, Any],
    model_call_id: str,
    output_ref: str,
    output_sha256: str,
    output_size: int,
) -> ScheduledInferenceReceipt:
    (
        plan_sha256,
        plan_binding_sha256,
        cell_id,
        lane,
        physical_lane,
        token_budget,
        capacity_sha256,
    ) = _verify_grid_plan(
        decision,
        grid_plan,
        current_generation=current_generation,
        entry_admission_sha256=entry_admission_sha256,
        admitted_grid_plan_bindings=admitted_grid_plan_bindings,
        grid_cell_id=grid_cell_id,
        model_lane=model_lane,
    )

    inner: InferenceReceipt = make_inference_receipt(
        decision,
        current_generation=current_generation,
        admitted_route_generations=admitted_route_generations,
        entry_admission_sha256=entry_admission_sha256,
        admitted_entry_bindings=admitted_entry_bindings,
        admitted_engine_artifacts=admitted_engine_artifacts,
        verified_engine_admission=verified_engine_admission,
        admitted_engine_admission_receipts=admitted_engine_admission_receipts,
        verified_engine_load=verified_engine_load,
        admitted_verified_engine_loads=admitted_verified_engine_loads,
        model_call_id=model_call_id,
        output_ref=output_ref,
        output_sha256=output_sha256,
        output_size=output_size,
    )
    if inner.schema != "HCU_INFERENCE_RECEIPT/v3":
        raise ScheduledInferenceReceiptError("INNER_INFERENCE_SCHEMA_UNSUPPORTED")
    if inner.hash_serialization_schema != CANONICALIZATION_SCHEMA or inner.entry_binding_schema != ENTRY_BINDING_SCHEMA:
        raise ScheduledInferenceReceiptError("INNER_INFERENCE_IDENTITY_SCHEMA_MISMATCH")
    if lane not in tuple(inner.model_lanes):
        raise ScheduledInferenceReceiptError("INNER_INFERENCE_MODEL_LANE_MISMATCH")

    payload = {
        "schema": SCHEMA,
        "status": STATUS,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "entry_binding_schema": ENTRY_BINDING_SCHEMA,
        "inner_receipt_schema": inner.schema,
        "inner_receipt_sha256": inner.receipt_sha256,
        "entity_generation": inner.entity_generation,
        "entry_admission_sha256": inner.entry_admission_sha256,
        "event_sha256": inner.event_sha256,
        "decision_sha256": inner.decision_sha256,
        "router_policy_sha256": inner.router_policy_sha256,
        "engine_identity_sha256": inner.engine_identity_sha256,
        "engine_admission_receipt_sha256": inner.engine_admission_receipt_sha256,
        "engine_load_consumption_receipt_sha256": inner.engine_load_consumption_receipt_sha256,
        "grid_plan_schema": grid_plan.schema,
        "grid_plan_sha256": plan_sha256,
        "grid_plan_admission_sha256": plan_binding_sha256,
        "grid_cell_id": cell_id,
        "model_lane": lane,
        "physical_decoder_lane": physical_lane,
        "model_token_budget": token_budget,
        "capacity_receipt_sha256": capacity_sha256,
        "runtime_profile_id": _text(grid_plan.runtime_profile_id, "runtime_profile_id"),
        "model_call_id": inner.model_call_id,
        "output_sha256": inner.output_sha256,
        "output_size": inner.output_size,
    }
    return ScheduledInferenceReceipt(
        **payload,
        receipt_sha256=_canonical_sha256(payload, "SCHEDULED_INFERENCE_RECEIPT"),
    )


def receipt_json(receipt: ScheduledInferenceReceipt) -> str:
    if not isinstance(receipt, ScheduledInferenceReceipt):
        raise ScheduledInferenceReceiptError("SCHEDULED_INFERENCE_RECEIPT_REQUIRED")
    return json.dumps(asdict(receipt), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
