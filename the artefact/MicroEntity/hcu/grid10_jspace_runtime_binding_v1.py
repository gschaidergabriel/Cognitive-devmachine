#!/usr/bin/env python3
"""Fail-closed runtime binding between GRID10 and J-Space training evidence.

The current HCU inference receipt v3 binds Entry/route/engine/load/output identity but only
carries the *set* of route model lanes.  It does not identify which one lane produced a
particular output.  That is sufficient for a single-lane GRID10 request, but it is not
sufficient to assign one output to one model cell when a route contains multiple lanes.

This module therefore admits exactly the causally unambiguous v3 case:

    GridPlan(v2, exactly one MODEL cell)
        + InferenceReceipt(v3, exactly one model lane)
        -> GRID10/J-Space runtime binding(v1)

Multi-lane v3 receipts fail closed until the canonical inference receipt itself binds a
specific lane/cell.  The binding is derived telemetry only: it grants no truth, state,
capability, engine, or effect authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any

try:
    from .entry_canonicalization_v1 import (
        CANONICALIZATION_SCHEMA,
        CanonicalizationError,
        canonicalize,
    )
    from .grid10_scheduler_v1 import ExecutionClass, GridPlan, PLAN_SCHEMA
    from .inference_receipt_v1 import (
        InferenceReceipt,
        SCHEMA as INFERENCE_RECEIPT_SCHEMA,
        STATUS as INFERENCE_RECEIPT_STATUS,
    )
except ImportError:
    from entry_canonicalization_v1 import (
        CANONICALIZATION_SCHEMA,
        CanonicalizationError,
        canonicalize,
    )
    from grid10_scheduler_v1 import ExecutionClass, GridPlan, PLAN_SCHEMA
    from inference_receipt_v1 import (
        InferenceReceipt,
        SCHEMA as INFERENCE_RECEIPT_SCHEMA,
        STATUS as INFERENCE_RECEIPT_STATUS,
    )

SCHEMA = "ENTITYOS_HCU_GRID10_JSPACE_RUNTIME_BINDING/v1"
AUTHORITY = "DERIVED_RUNTIME_EVIDENCE_ONLY_NOT_TRUTH_STATE_OR_EFFECT_AUTHORITY"


class Grid10JSpaceRuntimeBindingError(ValueError):
    pass


@dataclass(frozen=True)
class Grid10JSpaceRuntimeBinding:
    schema: str
    canonicalization_schema: str
    authority: str
    entity_generation: int
    entry_event_sha256: str
    entry_admission_sha256: str
    route_decision_sha256: str
    grid_plan_sha256: str
    cell_id: str
    model_lane: str
    inference_receipt_sha256: str
    model_call_id: str
    output_ref: str
    output_sha256: str
    output_size: int
    engine_identity_sha256: str
    resolved_engine_identity: str
    resolved_engine_class: str
    resolved_engine_artifact_sha256: str
    engine_admission_receipt_sha256: str
    engine_load_loader_binding_sha256: str
    engine_load_lease_sha256: str
    engine_load_consumption_receipt_sha256: str
    engine_load_loader_id: str
    binding_sha256: str


def _canonical_bytes(value: Any, field: str) -> bytes:
    try:
        return canonicalize(value)
    except CanonicalizationError as exc:
        raise Grid10JSpaceRuntimeBindingError(
            f"{field}:CANONICALIZATION_FAILED:{exc}"
        ) from exc


def _canonical_sha256(value: Any, field: str) -> str:
    return hashlib.sha256(_canonical_bytes(value, field)).hexdigest()


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise Grid10JSpaceRuntimeBindingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    value = value.strip()
    if (
        len(value) != 64
        or value.lower() != value
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        raise Grid10JSpaceRuntimeBindingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise Grid10JSpaceRuntimeBindingError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _text(value: Any, field: str, *, max_len: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Grid10JSpaceRuntimeBindingError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise Grid10JSpaceRuntimeBindingError(f"{field}:TOO_LONG")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise Grid10JSpaceRuntimeBindingError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise Grid10JSpaceRuntimeBindingError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _grid_plan_material(plan: GridPlan) -> dict[str, Any]:
    return {
        "schema": plan.schema,
        "canonicalization_schema": plan.canonicalization_schema,
        "entry_binding_schema": plan.entry_binding_schema,
        "ingress_id": plan.ingress_id,
        "causal_id": plan.causal_id,
        "entity_generation": plan.entity_generation,
        "entry_event_sha256": plan.entry_event_sha256,
        "entry_admission_sha256": plan.entry_admission_sha256,
        "route_event_sha256": plan.route_event_sha256,
        "route_decision_sha256": plan.route_decision_sha256,
        "router_policy_sha256": plan.router_policy_sha256,
        "engine_identity_sha256": plan.engine_identity_sha256,
        "resolved_engine_identity": plan.resolved_engine_identity,
        "resolved_engine_class": plan.resolved_engine_class,
        "resolved_engine_artifact_sha256": plan.resolved_engine_artifact_sha256,
        "capacity_receipt_sha256": plan.capacity_receipt_sha256,
        "runtime_profile_id": plan.runtime_profile_id,
        "mode": plan.mode.value,
        "logical_cell_count": plan.logical_cell_count,
        "model_call_count": plan.model_call_count,
        "physical_decoder_limit": plan.physical_decoder_limit,
        "max_wall_ms": plan.max_wall_ms,
        "cells": [
            {
                "cell_id": cell.cell_id,
                "function": cell.function,
                "execution_class": cell.execution_class.value,
                "model_token_budget": cell.model_token_budget,
                "physical_decoder_lane": cell.physical_decoder_lane,
            }
            for cell in plan.cells
        ],
    }


def _verify_grid_plan(plan: GridPlan) -> None:
    if not isinstance(plan, GridPlan):
        raise Grid10JSpaceRuntimeBindingError("GRID_PLAN_REQUIRED")
    if plan.schema != PLAN_SCHEMA:
        raise Grid10JSpaceRuntimeBindingError("GRID_PLAN_SCHEMA_UNSUPPORTED")
    if plan.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise Grid10JSpaceRuntimeBindingError(
            "GRID_PLAN_CANONICALIZATION_SCHEMA_UNSUPPORTED"
        )
    observed = _sha256(plan.plan_sha256, "grid_plan_sha256")
    expected = _canonical_sha256(_grid_plan_material(plan), "GRID_PLAN")
    if observed != expected:
        raise Grid10JSpaceRuntimeBindingError("GRID_PLAN_DIGEST_MISMATCH")


def _inference_receipt_material(receipt: InferenceReceipt) -> dict[str, Any]:
    material = asdict(receipt)
    material.pop("receipt_sha256", None)
    return material


def _verify_inference_receipt(receipt: InferenceReceipt) -> None:
    if not isinstance(receipt, InferenceReceipt):
        raise Grid10JSpaceRuntimeBindingError("INFERENCE_RECEIPT_REQUIRED")
    if receipt.schema != INFERENCE_RECEIPT_SCHEMA:
        raise Grid10JSpaceRuntimeBindingError("INFERENCE_RECEIPT_SCHEMA_UNSUPPORTED")
    if receipt.status != INFERENCE_RECEIPT_STATUS:
        raise Grid10JSpaceRuntimeBindingError("INFERENCE_RECEIPT_STATUS_UNSUPPORTED")
    if receipt.hash_serialization_schema != CANONICALIZATION_SCHEMA:
        raise Grid10JSpaceRuntimeBindingError(
            "INFERENCE_RECEIPT_CANONICALIZATION_SCHEMA_UNSUPPORTED"
        )
    observed = _sha256(receipt.receipt_sha256, "inference_receipt_sha256")
    expected = _canonical_sha256(
        _inference_receipt_material(receipt),
        "INFERENCE_RECEIPT",
    )
    if observed != expected:
        raise Grid10JSpaceRuntimeBindingError("INFERENCE_RECEIPT_DIGEST_MISMATCH")


def _binding_material(binding: Grid10JSpaceRuntimeBinding) -> dict[str, Any]:
    material = asdict(binding)
    material.pop("binding_sha256", None)
    return material


def bind_single_lane_inference(
    plan: GridPlan,
    receipt: InferenceReceipt,
    *,
    current_generation: int,
    cell_id: str,
) -> Grid10JSpaceRuntimeBinding:
    """Bind one v3 inference output to one GRID10 model cell without guessing.

    v3 does not carry a concrete output-producing lane.  Therefore only an exact one-lane
    route is admitted.  A multi-lane v3 receipt is intentionally rejected even when the
    requested cell's role is present in ``receipt.model_lanes``.
    """
    _verify_grid_plan(plan)
    _verify_inference_receipt(receipt)

    current_generation = _nonnegative_int(current_generation, "current_generation")
    if (
        plan.entity_generation != current_generation
        or receipt.entity_generation != current_generation
    ):
        raise Grid10JSpaceRuntimeBindingError("STALE_RUNTIME_BINDING_GENERATION")

    if plan.model_call_count != 1:
        raise Grid10JSpaceRuntimeBindingError(
            "MULTI_LANE_GRID_PLAN_REQUIRES_LANE_BOUND_INFERENCE_RECEIPT"
        )
    if not isinstance(receipt.model_lanes, tuple) or len(receipt.model_lanes) != 1:
        raise Grid10JSpaceRuntimeBindingError(
            "MULTI_LANE_INFERENCE_RECEIPT_UNBOUND"
        )
    model_lane = _text(receipt.model_lanes[0], "model_lane", max_len=256)

    model_cells = [
        cell for cell in plan.cells if cell.execution_class is ExecutionClass.MODEL
    ]
    if len(model_cells) != 1:
        raise Grid10JSpaceRuntimeBindingError(
            "GRID_PLAN_SINGLE_MODEL_CELL_REQUIRED_FOR_V3_BINDING"
        )
    cell_id = _text(cell_id, "cell_id", max_len=256)
    cell = model_cells[0]
    if cell.cell_id != cell_id:
        raise Grid10JSpaceRuntimeBindingError("GRID_MODEL_CELL_ID_MISMATCH")
    if cell.function != f"MODEL:{model_lane}":
        raise Grid10JSpaceRuntimeBindingError("GRID_MODEL_CELL_LANE_MISMATCH")

    expected_pairs = {
        "entry_event_sha256": (receipt.event_sha256, plan.entry_event_sha256),
        "entry_admission_sha256": (
            receipt.entry_admission_sha256,
            plan.entry_admission_sha256,
        ),
        "route_decision_sha256": (
            receipt.decision_sha256,
            plan.route_decision_sha256,
        ),
        "router_policy_sha256": (
            receipt.router_policy_sha256,
            plan.router_policy_sha256,
        ),
        "engine_identity_sha256": (
            receipt.engine_identity_sha256,
            plan.engine_identity_sha256,
        ),
        "resolved_engine_identity": (
            receipt.resolved_engine_identity,
            plan.resolved_engine_identity,
        ),
        "resolved_engine_class": (
            receipt.resolved_engine_class,
            plan.resolved_engine_class,
        ),
        "resolved_engine_artifact_sha256": (
            receipt.resolved_engine_artifact_sha256,
            plan.resolved_engine_artifact_sha256,
        ),
    }
    for field, (observed, expected) in expected_pairs.items():
        if observed != expected:
            raise Grid10JSpaceRuntimeBindingError(
                f"RUNTIME_CAUSAL_IDENTITY_MISMATCH:{field}"
            )

    if receipt.engine_load_canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise Grid10JSpaceRuntimeBindingError(
            "ENGINE_LOAD_CANONICALIZATION_SCHEMA_UNSUPPORTED"
        )

    material = {
        "schema": SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "authority": AUTHORITY,
        "entity_generation": current_generation,
        "entry_event_sha256": _sha256(plan.entry_event_sha256, "entry_event_sha256"),
        "entry_admission_sha256": _sha256(
            plan.entry_admission_sha256,
            "entry_admission_sha256",
        ),
        "route_decision_sha256": _sha256(
            plan.route_decision_sha256,
            "route_decision_sha256",
        ),
        "grid_plan_sha256": _sha256(plan.plan_sha256, "grid_plan_sha256"),
        "cell_id": cell_id,
        "model_lane": model_lane,
        "inference_receipt_sha256": _sha256(
            receipt.receipt_sha256,
            "inference_receipt_sha256",
        ),
        "model_call_id": _text(receipt.model_call_id, "model_call_id"),
        "output_ref": _text(receipt.output_ref, "output_ref"),
        "output_sha256": _sha256(receipt.output_sha256, "output_sha256"),
        "output_size": _nonnegative_int(receipt.output_size, "output_size"),
        "engine_identity_sha256": _sha256(
            receipt.engine_identity_sha256,
            "engine_identity_sha256",
        ),
        "resolved_engine_identity": _text(
            receipt.resolved_engine_identity,
            "resolved_engine_identity",
        ),
        "resolved_engine_class": _text(
            receipt.resolved_engine_class,
            "resolved_engine_class",
        ),
        "resolved_engine_artifact_sha256": _sha256(
            receipt.resolved_engine_artifact_sha256,
            "resolved_engine_artifact_sha256",
        ),
        "engine_admission_receipt_sha256": _sha256(
            receipt.engine_admission_receipt_sha256,
            "engine_admission_receipt_sha256",
        ),
        "engine_load_loader_binding_sha256": _sha256(
            receipt.engine_load_loader_binding_sha256,
            "engine_load_loader_binding_sha256",
        ),
        "engine_load_lease_sha256": _sha256(
            receipt.engine_load_lease_sha256,
            "engine_load_lease_sha256",
        ),
        "engine_load_consumption_receipt_sha256": _sha256(
            receipt.engine_load_consumption_receipt_sha256,
            "engine_load_consumption_receipt_sha256",
        ),
        "engine_load_loader_id": _text(
            receipt.engine_load_loader_id,
            "engine_load_loader_id",
        ),
    }
    binding_sha256 = _canonical_sha256(material, "GRID10_JSPACE_RUNTIME_BINDING")
    return Grid10JSpaceRuntimeBinding(**material, binding_sha256=binding_sha256)


def validate_runtime_binding(binding: Grid10JSpaceRuntimeBinding) -> None:
    if not isinstance(binding, Grid10JSpaceRuntimeBinding):
        raise Grid10JSpaceRuntimeBindingError("GRID10_JSPACE_RUNTIME_BINDING_REQUIRED")
    if binding.schema != SCHEMA:
        raise Grid10JSpaceRuntimeBindingError("RUNTIME_BINDING_SCHEMA_UNSUPPORTED")
    if binding.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise Grid10JSpaceRuntimeBindingError(
            "RUNTIME_BINDING_CANONICALIZATION_SCHEMA_UNSUPPORTED"
        )
    if binding.authority != AUTHORITY:
        raise Grid10JSpaceRuntimeBindingError("RUNTIME_BINDING_AUTHORITY_INVALID")
    observed = _sha256(binding.binding_sha256, "binding_sha256")
    expected = _canonical_sha256(
        _binding_material(binding),
        "GRID10_JSPACE_RUNTIME_BINDING",
    )
    if observed != expected:
        raise Grid10JSpaceRuntimeBindingError("RUNTIME_BINDING_DIGEST_MISMATCH")


def binding_dict(binding: Grid10JSpaceRuntimeBinding) -> dict[str, Any]:
    validate_runtime_binding(binding)
    return asdict(binding)
