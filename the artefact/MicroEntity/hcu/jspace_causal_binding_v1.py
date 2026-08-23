#!/usr/bin/env python3
"""Exact causal binding receipt for EntityOS/HCU J-Space training evidence.

This module does not create truth, reward, compute authority or effects. It binds an
already-admitted Typed Entry, canonical HCU RouteDecision and GRID10 plan into one
versioned receipt so training telemetry cannot label arbitrary digest strings as an
"exact" causal path.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .grid10_scheduler_v1 import ExecutionClass, GridPlan, PLAN_SCHEMA
    from .reactive_event_router_v1 import ENTRY_BINDING_SCHEMA, HASH_SERIALIZATION_SCHEMA, RouteDecision
    from .xeno_entry_fabric_v1 import EntryPacket
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from grid10_scheduler_v1 import ExecutionClass, GridPlan, PLAN_SCHEMA
    from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA, HASH_SERIALIZATION_SCHEMA, RouteDecision
    from xeno_entry_fabric_v1 import EntryPacket

BINDING_SCHEMA = "ENTITYOS_HCU_JSPACE_TRAINING_CAUSAL_BINDING/v1"


class JSpaceCausalBindingError(ValueError):
    pass


@dataclass(frozen=True)
class CausalBinding:
    schema: str
    canonicalization_schema: str
    generation: int
    entry_event_sha256: str
    entry_admission_sha256: str
    route_decision_sha256: str
    grid_plan_sha256: str
    binding_sha256: str


def _generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9_007_199_254_740_991:
        raise JSpaceCausalBindingError(f"{field}:IJSON_NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceCausalBindingError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise JSpaceCausalBindingError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def binding_sha256_from_fields(
    *,
    generation: int,
    entry_event_sha256: str,
    entry_admission_sha256: str,
    route_decision_sha256: str,
    grid_plan_sha256: str,
) -> str:
    material = {
        "schema": BINDING_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "generation": _generation(generation, "generation"),
        "entry_event_sha256": _sha256(entry_event_sha256, "entry_event_sha256"),
        "entry_admission_sha256": _sha256(entry_admission_sha256, "entry_admission_sha256"),
        "route_decision_sha256": _sha256(route_decision_sha256, "route_decision_sha256"),
        "grid_plan_sha256": _sha256(grid_plan_sha256, "grid_plan_sha256"),
    }
    return _canonical_sha256(material, "JSPACE_TRAINING_CAUSAL_BINDING")


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


def _verify_grid_plan_integrity(plan: GridPlan) -> None:
    if not isinstance(plan, GridPlan):
        raise JSpaceCausalBindingError("GRID_PLAN_REQUIRED")
    if plan.schema != PLAN_SCHEMA or plan.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceCausalBindingError("GRID_PLAN_SCHEMA_OR_CANONICALIZATION_UNSUPPORTED")
    if plan.entry_binding_schema != ENTRY_BINDING_SCHEMA:
        raise JSpaceCausalBindingError("GRID_PLAN_ENTRY_BINDING_SCHEMA_UNSUPPORTED")
    observed = _sha256(plan.plan_sha256, "grid_plan.plan_sha256")
    expected = _canonical_sha256(_grid_plan_material(plan), "GRID_PLAN")
    if observed != expected:
        raise JSpaceCausalBindingError("GRID_PLAN_DIGEST_MISMATCH")
    if not isinstance(plan.cells, tuple) or not plan.cells:
        raise JSpaceCausalBindingError("GRID_PLAN_CELLS_REQUIRED")
    model_cells = [cell for cell in plan.cells if cell.execution_class is ExecutionClass.MODEL]
    if len(model_cells) != plan.model_call_count:
        raise JSpaceCausalBindingError("GRID_PLAN_MODEL_CELL_COUNT_MISMATCH")


def bind_causal_path(
    packet: EntryPacket,
    decision: RouteDecision,
    plan: GridPlan,
    *,
    current_generation: int,
) -> CausalBinding:
    """Bind the actual current Entry -> route -> GRID10 identities into one receipt."""
    if not isinstance(packet, EntryPacket):
        raise JSpaceCausalBindingError("ENTRY_PACKET_REQUIRED")
    if not isinstance(decision, RouteDecision):
        raise JSpaceCausalBindingError("ROUTE_DECISION_REQUIRED")
    _verify_grid_plan_integrity(plan)
    generation = _generation(current_generation, "current_generation")
    if packet.entity_generation != generation or plan.entity_generation != generation:
        raise JSpaceCausalBindingError("STALE_CAUSAL_BINDING_GENERATION")
    if HASH_SERIALIZATION_SCHEMA != CANONICALIZATION_SCHEMA or decision.hash_serialization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceCausalBindingError("ROUTE_CANONICALIZATION_SCHEMA_UNSUPPORTED")
    if decision.external_provider_dependency is not False:
        raise JSpaceCausalBindingError("EXTERNAL_PROVIDER_DEPENDENCY_FORBIDDEN")
    if decision.status != "SELECTIVE_MODEL_ACTIVATION":
        raise JSpaceCausalBindingError("MODEL_ROUTE_REQUIRED")

    expected = {
        "decision.event_sha256": (decision.event_sha256, packet.event_sha256),
        "decision.entry_admission_sha256": (decision.entry_admission_sha256, packet.admission_sha256),
        "plan.ingress_id": (plan.ingress_id, packet.ingress_id),
        "plan.causal_id": (plan.causal_id, packet.causal_id),
        "plan.entry_event_sha256": (plan.entry_event_sha256, packet.event_sha256),
        "plan.entry_admission_sha256": (plan.entry_admission_sha256, packet.admission_sha256),
        "plan.route_event_sha256": (plan.route_event_sha256, decision.event_sha256),
        "plan.route_decision_sha256": (plan.route_decision_sha256, decision.decision_sha256),
        "plan.router_policy_sha256": (plan.router_policy_sha256, decision.router_policy_sha256),
        "plan.engine_identity_sha256": (plan.engine_identity_sha256, decision.engine_identity_sha256),
        "plan.resolved_engine_identity": (plan.resolved_engine_identity, decision.resolved_engine_identity),
        "plan.resolved_engine_class": (plan.resolved_engine_class, decision.resolved_engine_class),
        "plan.resolved_engine_artifact_sha256": (plan.resolved_engine_artifact_sha256, decision.resolved_engine_artifact_sha256),
    }
    for field, (observed, wanted) in expected.items():
        if observed != wanted:
            raise JSpaceCausalBindingError(f"CAUSAL_PATH_IDENTITY_MISMATCH:{field}")

    event_sha = _sha256(packet.event_sha256, "entry_event_sha256")
    admission_sha = _sha256(packet.admission_sha256, "entry_admission_sha256")
    decision_sha = _sha256(decision.decision_sha256, "route_decision_sha256")
    plan_sha = _sha256(plan.plan_sha256, "grid_plan_sha256")
    binding_sha = binding_sha256_from_fields(
        generation=generation,
        entry_event_sha256=event_sha,
        entry_admission_sha256=admission_sha,
        route_decision_sha256=decision_sha,
        grid_plan_sha256=plan_sha,
    )
    return CausalBinding(
        schema=BINDING_SCHEMA,
        canonicalization_schema=CANONICALIZATION_SCHEMA,
        generation=generation,
        entry_event_sha256=event_sha,
        entry_admission_sha256=admission_sha,
        route_decision_sha256=decision_sha,
        grid_plan_sha256=plan_sha,
        binding_sha256=binding_sha,
    )


def validate_binding(binding: CausalBinding) -> None:
    if not isinstance(binding, CausalBinding):
        raise JSpaceCausalBindingError("CAUSAL_BINDING_REQUIRED")
    if binding.schema != BINDING_SCHEMA or binding.canonicalization_schema != CANONICALIZATION_SCHEMA:
        raise JSpaceCausalBindingError("CAUSAL_BINDING_SCHEMA_UNSUPPORTED")
    expected = binding_sha256_from_fields(
        generation=binding.generation,
        entry_event_sha256=binding.entry_event_sha256,
        entry_admission_sha256=binding.entry_admission_sha256,
        route_decision_sha256=binding.route_decision_sha256,
        grid_plan_sha256=binding.grid_plan_sha256,
    )
    if _sha256(binding.binding_sha256, "binding_sha256") != expected:
        raise JSpaceCausalBindingError("CAUSAL_BINDING_DIGEST_MISMATCH")


def binding_dict(binding: CausalBinding) -> dict[str, Any]:
    validate_binding(binding)
    return asdict(binding)
