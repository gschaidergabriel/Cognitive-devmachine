#!/usr/bin/env python3
"""EntityOS/HCU scheduled inference receipt.

Wraps the current candidate-only inference receipt with one independently admitted
GRID10 plan and one concrete MODEL cell. This closes the route->plan->inference causal
alias without creating a second router, state authority, engine authority, or effect path.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from grid10_scheduler_v1 import ExecutionClass, GridPlan, HCUMode
from inference_receipt_v1 import InferenceReceipt, make_inference_receipt
from reactive_event_router_v1 import RouteDecision

SCHEMA = "HCU_SCHEDULED_INFERENCE_RECEIPT/v2"
STATUS = "CANDIDATE_ONLY"


class ScheduledInferenceReceiptError(ValueError):
    pass


@dataclass(frozen=True)
class ScheduledInferenceReceipt:
    schema: str
    status: str
    inner_receipt_schema: str
    inner_receipt_sha256: str
    entity_generation: int
    entry_admission_sha256: str
    event_sha256: str
    decision_sha256: str
    router_policy_sha256: str
    engine_identity_sha256: str
    engine_admission_receipt_sha256: str
    engine_load_lease_sha256: str
    grid_plan_sha256: str
    grid_cell_id: str
    capacity_receipt_sha256: str
    runtime_profile_id: str
    model_call_id: str
    output_sha256: str
    output_size: int
    receipt_sha256: str


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ScheduledInferenceReceiptError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    value = value.strip()
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise ScheduledInferenceReceiptError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise ScheduledInferenceReceiptError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScheduledInferenceReceiptError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > 1024:
        raise ScheduledInferenceReceiptError(f"{field}:TOO_LONG")
    return value


def _verify_grid_plan(
    decision: RouteDecision,
    *,
    grid_plan: GridPlan,
    admitted_grid_plans: Mapping[str, Any],
    grid_cell_id: str,
    current_generation: int,
    entry_admission_sha256: str,
) -> tuple[str, str, str, str]:
    if not isinstance(grid_plan, GridPlan):
        raise ScheduledInferenceReceiptError("GRID_PLAN_REQUIRED")
    if grid_plan.mode is not HCUMode.GRID10:
        raise ScheduledInferenceReceiptError("GRID_PLAN_MODE_UNSUPPORTED")

    plan_sha256 = _sha256(grid_plan.plan_sha256, "grid_plan_sha256")
    if not isinstance(admitted_grid_plans, Mapping):
        raise ScheduledInferenceReceiptError("ADMITTED_GRID_PLAN_REGISTRY_REQUIRED")
    admitted_route = admitted_grid_plans.get(plan_sha256)
    if admitted_route is None:
        raise ScheduledInferenceReceiptError("GRID_PLAN_NOT_ADMITTED")
    if _sha256(admitted_route, "admitted_grid_plan_route_sha256") != decision.decision_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_ROUTE_BINDING_MISMATCH")

    if grid_plan.entity_generation != current_generation:
        raise ScheduledInferenceReceiptError("GRID_PLAN_GENERATION_MISMATCH")
    if grid_plan.entry_admission_sha256 != entry_admission_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_ENTRY_ADMISSION_MISMATCH")
    if grid_plan.entry_event_sha256 != decision.event_sha256 or grid_plan.route_event_sha256 != decision.event_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_EVENT_MISMATCH")
    if grid_plan.route_decision_sha256 != decision.decision_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_ROUTE_DECISION_MISMATCH")
    if grid_plan.router_policy_sha256 != decision.router_policy_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_ROUTER_POLICY_MISMATCH")
    if grid_plan.engine_identity_sha256 != decision.engine_identity_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_ENGINE_IDENTITY_MISMATCH")
    if grid_plan.resolved_engine_identity != decision.resolved_engine_identity:
        raise ScheduledInferenceReceiptError("GRID_PLAN_ENGINE_NAME_MISMATCH")
    if grid_plan.resolved_engine_class != decision.resolved_engine_class:
        raise ScheduledInferenceReceiptError("GRID_PLAN_ENGINE_CLASS_MISMATCH")
    if grid_plan.resolved_engine_artifact_sha256 != decision.resolved_engine_artifact_sha256:
        raise ScheduledInferenceReceiptError("GRID_PLAN_ENGINE_ARTIFACT_MISMATCH")

    cell_id = _text(grid_cell_id, "grid_cell_id")
    matches = [cell for cell in grid_plan.cells if cell.cell_id == cell_id]
    if len(matches) != 1:
        raise ScheduledInferenceReceiptError("GRID_MODEL_CELL_NOT_FOUND")
    if matches[0].execution_class is not ExecutionClass.MODEL:
        raise ScheduledInferenceReceiptError("GRID_CELL_NOT_MODEL_EXECUTION")
    if matches[0].model_token_budget <= 0:
        raise ScheduledInferenceReceiptError("GRID_MODEL_CELL_TOKEN_BUDGET_INVALID")

    return (
        plan_sha256,
        cell_id,
        _sha256(grid_plan.capacity_receipt_sha256, "capacity_receipt_sha256"),
        _text(grid_plan.runtime_profile_id, "runtime_profile_id"),
    )


def make_scheduled_inference_receipt(
    decision: RouteDecision,
    *,
    grid_plan: GridPlan,
    admitted_grid_plans: Mapping[str, Any],
    grid_cell_id: str,
    current_generation: int,
    admitted_route_generations: Mapping[str, Any],
    entry_admission_sha256: str,
    admitted_entry_bindings: Mapping[str, Any],
    admitted_engine_artifacts: Mapping[str, Any],
    engine_admission_receipt_sha256: str,
    admitted_engine_admission_receipts: Mapping[str, Any],
    engine_load_lease_sha256: str,
    admitted_engine_load_leases: Mapping[str, Any],
    model_call_id: str,
    output_ref: str,
    output_sha256: str,
    output_size: int,
) -> ScheduledInferenceReceipt:
    admission_sha256 = _sha256(entry_admission_sha256, "entry_admission_sha256")
    plan_sha256, cell_id, capacity_sha256, runtime_profile_id = _verify_grid_plan(
        decision,
        grid_plan=grid_plan,
        admitted_grid_plans=admitted_grid_plans,
        grid_cell_id=grid_cell_id,
        current_generation=current_generation,
        entry_admission_sha256=admission_sha256,
    )

    inner: InferenceReceipt = make_inference_receipt(
        decision,
        current_generation=current_generation,
        admitted_route_generations=admitted_route_generations,
        entry_admission_sha256=admission_sha256,
        admitted_entry_bindings=admitted_entry_bindings,
        admitted_engine_artifacts=admitted_engine_artifacts,
        engine_admission_receipt_sha256=engine_admission_receipt_sha256,
        admitted_engine_admission_receipts=admitted_engine_admission_receipts,
        engine_load_lease_sha256=engine_load_lease_sha256,
        admitted_engine_load_leases=admitted_engine_load_leases,
        model_call_id=model_call_id,
        output_ref=output_ref,
        output_sha256=output_sha256,
        output_size=output_size,
    )

    payload = {
        "schema": SCHEMA,
        "status": STATUS,
        "inner_receipt_schema": inner.schema,
        "inner_receipt_sha256": inner.receipt_sha256,
        "entity_generation": inner.entity_generation,
        "entry_admission_sha256": inner.entry_admission_sha256,
        "event_sha256": inner.event_sha256,
        "decision_sha256": inner.decision_sha256,
        "router_policy_sha256": inner.router_policy_sha256,
        "engine_identity_sha256": inner.engine_identity_sha256,
        "engine_admission_receipt_sha256": inner.engine_admission_receipt_sha256,
        "engine_load_lease_sha256": inner.engine_load_lease_sha256,
        "grid_plan_sha256": plan_sha256,
        "grid_cell_id": cell_id,
        "capacity_receipt_sha256": capacity_sha256,
        "runtime_profile_id": runtime_profile_id,
        "model_call_id": inner.model_call_id,
        "output_sha256": inner.output_sha256,
        "output_size": inner.output_size,
    }
    receipt_sha256 = hashlib.sha256(_canonical(payload)).hexdigest()
    return ScheduledInferenceReceipt(**payload, receipt_sha256=receipt_sha256)


def receipt_json(receipt: ScheduledInferenceReceipt) -> str:
    if not isinstance(receipt, ScheduledInferenceReceipt):
        raise ScheduledInferenceReceiptError("SCHEDULED_INFERENCE_RECEIPT_REQUIRED")
    return json.dumps(asdict(receipt), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
