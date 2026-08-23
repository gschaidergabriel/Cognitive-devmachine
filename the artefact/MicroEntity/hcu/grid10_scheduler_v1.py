#!/usr/bin/env python3
"""Deterministic EntityOS/HCU GRID10/control-plane scheduler.

Consumes an already-admitted EntryPacket, the single canonical HCU RouteDecision, and a
separately trusted runtime-capacity snapshot. It allocates logical function cells; it does
not choose HCU mode, engine identity, truth, permissions, compute authority, or effects.
Logical cell population, model-call budget and physical decode concurrency remain
separate quantities.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

try:
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .reactive_event_router_v1 import (
        ENTRY_BINDING_SCHEMA,
        HASH_SERIALIZATION_SCHEMA,
        ReactiveRoutingError,
        RouteDecision,
        resolve_admitted_entry_binding,
    )
    from .xeno_entry_fabric_v1 import EntryFabricError, EntryPacket, admit_entry
except ImportError:
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from reactive_event_router_v1 import (
        ENTRY_BINDING_SCHEMA,
        HASH_SERIALIZATION_SCHEMA,
        ReactiveRoutingError,
        RouteDecision,
        resolve_admitted_entry_binding,
    )
    from xeno_entry_fabric_v1 import EntryFabricError, EntryPacket, admit_entry

PLAN_SCHEMA = "ENTITYOS_HCU_GRID_PLAN/v2"


class GridScheduleError(ValueError):
    pass


class HCUMode(str, Enum):
    GRID10 = "GRID10"
    COGSIM10 = "COGSIM10"
    WM_TEST = "WM_TEST"
    NESTED_SIM = "NESTED_SIM"
    SCALEOUT = "SCALEOUT"


class ExecutionClass(str, Enum):
    SCRIPT = "SCRIPT"
    MODEL = "MODEL"


@dataclass(frozen=True)
class RuntimeCapacity:
    profile_id: str
    capacity_receipt_sha256: str
    max_logical_cells: int
    physical_decoder_limit: int

    def validate(self) -> None:
        if not isinstance(self.profile_id, str) or not self.profile_id.strip():
            raise GridScheduleError("runtime_capacity.profile_id:NONEMPTY_STRING_REQUIRED")
        _sha256(self.capacity_receipt_sha256, "runtime_capacity.capacity_receipt_sha256")
        for name in ("max_logical_cells", "physical_decoder_limit"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise GridScheduleError(f"runtime_capacity.{name}:POSITIVE_INTEGER_REQUIRED")


@dataclass(frozen=True)
class CellLease:
    cell_id: str
    function: str
    execution_class: ExecutionClass
    model_token_budget: int
    physical_decoder_lane: int | None


@dataclass(frozen=True)
class GridPlan:
    schema: str
    canonicalization_schema: str
    entry_binding_schema: str
    plan_sha256: str
    ingress_id: str
    causal_id: str
    entity_generation: int
    entry_event_sha256: str
    entry_admission_sha256: str
    route_event_sha256: str
    route_decision_sha256: str
    router_policy_sha256: str
    engine_identity_sha256: str
    resolved_engine_identity: str
    resolved_engine_class: str
    resolved_engine_artifact_sha256: str
    capacity_receipt_sha256: str
    runtime_profile_id: str
    mode: HCUMode
    logical_cell_count: int
    model_call_count: int
    physical_decoder_limit: int
    max_wall_ms: int
    cells: tuple[CellLease, ...]


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise GridScheduleError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    value = value.strip()
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise GridScheduleError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GridScheduleError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def _verify_admitted_entry(
    packet: EntryPacket,
    admitted_entry_bindings: Mapping[str, Any],
    *,
    current_generation: int,
) -> dict[str, int]:
    """Re-verify packet integrity plus prior external Entry admission.

    The admission registry is external control-plane authority. GRID10 reuses the router's
    sole typed JCS admission->event binding law; it never interprets a legacy bare digest as
    current authority. Re-admission below is integrity reconstruction only and cannot mint
    capabilities or compute budget.
    """
    if not isinstance(packet, EntryPacket):
        raise GridScheduleError("ADMITTED_ENTRY_PACKET_REQUIRED")
    if isinstance(current_generation, bool) or not isinstance(current_generation, int) or current_generation < 0:
        raise GridScheduleError("CURRENT_GENERATION_INVALID")
    if packet.entity_generation != current_generation:
        raise GridScheduleError("STALE_ENTITY_GENERATION")
    try:
        resolve_admitted_entry_binding(
            admitted_entry_bindings,
            packet.admission_sha256,
            expected_event_sha256=packet.event_sha256,
        )
    except ReactiveRoutingError as exc:
        raise GridScheduleError(f"ENTRY_BINDING_REJECTED:{exc}") from exc

    try:
        rebuilt = admit_entry(
            {
                "schema": packet.schema,
                "ingress_id": packet.ingress_id,
                "causal_id": packet.causal_id,
                "entity_generation": packet.entity_generation,
                "source_kind": packet.source_kind,
                "source_id": packet.source_id,
                "modality": packet.modality,
                "observed_time": packet.observed_time,
                "received_time": packet.received_time,
                "provenance_ref": packet.provenance_ref,
                "provenance_sha256": packet.provenance_sha256,
                "capabilities": list(packet.capabilities),
                "capability_binding_sha256": packet.capability_binding_sha256,
                "parent_id": packet.parent_id,
                "stream_id": packet.stream_id,
                "budget": dict(packet.budget),
                "payload_ref": packet.payload_ref,
                "payload_sha256": packet.payload_sha256,
            },
            current_generation=current_generation,
            expected_capability_binding_sha256=packet.capability_binding_sha256,
            admitted_capabilities=packet.capabilities,
            admitted_budget=dict(packet.budget),
        )
    except (EntryFabricError, TypeError, ValueError) as exc:
        raise GridScheduleError("ENTRY_PACKET_SELF_VERIFICATION_FAILED") from exc
    if rebuilt != packet:
        raise GridScheduleError("ENTRY_PACKET_IDENTITY_MISMATCH")
    if "hcu.route" not in packet.capabilities:
        raise GridScheduleError("ENTRY_CAPABILITY_HCU_ROUTE_REQUIRED")

    budget = dict(packet.budget)
    required = {"max_model_calls", "max_tokens", "max_wall_ms"}
    if set(budget) != required:
        raise GridScheduleError("ENTRY_BUDGET_CONTRACT_MISMATCH")
    return budget


def _verify_capacity_authority(
    capacity: RuntimeCapacity,
    admitted_capacity_receipts: Mapping[str, Mapping[str, Any]],
) -> None:
    """Verify physical/logical capacity against external deterministic authority."""
    capacity.validate()
    if not isinstance(admitted_capacity_receipts, Mapping):
        raise GridScheduleError("ADMITTED_CAPACITY_RECEIPT_REGISTRY_REQUIRED")
    admitted = admitted_capacity_receipts.get(capacity.capacity_receipt_sha256)
    if not isinstance(admitted, Mapping):
        raise GridScheduleError("CAPACITY_RECEIPT_NOT_ADMITTED")
    required = {"profile_id", "max_logical_cells", "physical_decoder_limit"}
    if set(admitted) != required:
        raise GridScheduleError("ADMITTED_CAPACITY_RECEIPT_SCHEMA_MISMATCH")

    profile_id = admitted.get("profile_id")
    max_logical_cells = admitted.get("max_logical_cells")
    physical_decoder_limit = admitted.get("physical_decoder_limit")
    if not isinstance(profile_id, str) or not profile_id.strip():
        raise GridScheduleError("ADMITTED_CAPACITY_PROFILE_ID_INVALID")
    for field, value in (
        ("MAX_LOGICAL_CELLS", max_logical_cells),
        ("PHYSICAL_DECODER_LIMIT", physical_decoder_limit),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise GridScheduleError(f"ADMITTED_CAPACITY_{field}_INVALID")

    if capacity.profile_id.strip() != profile_id.strip():
        raise GridScheduleError("CAPACITY_PROFILE_ID_MISMATCH")
    if capacity.max_logical_cells != max_logical_cells:
        raise GridScheduleError("CAPACITY_MAX_LOGICAL_CELLS_MISMATCH")
    if capacity.physical_decoder_limit != physical_decoder_limit:
        raise GridScheduleError("CAPACITY_PHYSICAL_DECODER_LIMIT_MISMATCH")


def _verify_route_authority(packet: EntryPacket, decision: RouteDecision) -> tuple[str, ...]:
    """Bind GRID10 to the already-made canonical HCU route; never route again here."""
    if not isinstance(decision, RouteDecision):
        raise GridScheduleError("ADMITTED_HCU_ROUTE_DECISION_REQUIRED")
    if decision.status != "SELECTIVE_MODEL_ACTIVATION":
        raise GridScheduleError("GRID10_REQUIRES_SELECTIVE_MODEL_ROUTE")
    if decision.external_provider_dependency is not False:
        raise GridScheduleError("EXTERNAL_PROVIDER_DEPENDENCY_FORBIDDEN")
    if HASH_SERIALIZATION_SCHEMA != CANONICALIZATION_SCHEMA:
        raise GridScheduleError("GRID10_ROUTER_CANONICALIZATION_CONFIGURATION_MISMATCH")
    if decision.hash_serialization_schema != CANONICALIZATION_SCHEMA:
        raise GridScheduleError("ROUTE_CANONICALIZATION_SCHEMA_UNSUPPORTED")

    entry_event_sha256 = _sha256(packet.event_sha256, "entry_event_sha256")
    entry_admission_sha256 = _sha256(packet.admission_sha256, "entry_admission_sha256")
    route_event_sha256 = _sha256(decision.event_sha256, "route_event_sha256")
    if route_event_sha256 != entry_event_sha256:
        raise GridScheduleError("ROUTE_EVENT_ENTRY_EVENT_MISMATCH")
    if decision.entry_admission_sha256 != entry_admission_sha256:
        raise GridScheduleError("ROUTE_ENTRY_ADMISSION_MISMATCH")

    _sha256(decision.decision_sha256, "route_decision_sha256")
    _sha256(decision.router_policy_sha256, "router_policy_sha256")
    _sha256(decision.engine_identity_sha256, "engine_identity_sha256")
    _nonempty(decision.resolved_engine_identity, "resolved_engine_identity")
    _nonempty(decision.resolved_engine_class, "resolved_engine_class")
    _sha256(decision.resolved_engine_artifact_sha256, "resolved_engine_artifact_sha256")

    lanes = tuple(decision.model_lanes)
    if not lanes:
        raise GridScheduleError("GRID10_REQUIRES_MODEL_LANES")
    if len(lanes) != len(set(lanes)):
        raise GridScheduleError("ROUTE_MODEL_LANES_DUPLICATE")
    if len(lanes) > 7:
        raise GridScheduleError("GRID10_ROUTE_LANE_COUNT_EXCEEDED")
    for lane in lanes:
        _nonempty(lane, "model_lane")
    return lanes


def compile_plan(
    packet: EntryPacket,
    *,
    decision: RouteDecision,
    mode: HCUMode,
    capacity: RuntimeCapacity,
    current_generation: int,
    admitted_entry_bindings: Mapping[str, Any],
    admitted_capacity_receipts: Mapping[str, Mapping[str, Any]],
) -> GridPlan:
    """Compile an execution plan only after canonical HCU routing is complete.

    GRID10 is the currently admitted scheduling profile. COGSIM10/WM_TEST/NESTED_SIM and
    SCALEOUT remain explicit future profiles and fail closed here until their own control
    contracts exist. This prevents the scheduler from becoming a second route authority.
    """
    budget = _verify_admitted_entry(
        packet,
        admitted_entry_bindings,
        current_generation=current_generation,
    )
    _verify_capacity_authority(capacity, admitted_capacity_receipts)
    if not isinstance(mode, HCUMode):
        raise GridScheduleError("HCU_MODE_REQUIRED")
    if mode is not HCUMode.GRID10:
        raise GridScheduleError("MODE_REQUIRES_SEPARATE_ADMITTED_CONTROL_PROFILE")

    lanes = _verify_route_authority(packet, decision)
    model_count = len(lanes)
    if model_count > budget["max_model_calls"]:
        raise GridScheduleError("MODEL_CALL_BUDGET_EXCEEDED")
    if budget["max_tokens"] < model_count:
        raise GridScheduleError("MODEL_TOKEN_BUDGET_TOO_SMALL")
    if capacity.max_logical_cells < 10:
        raise GridScheduleError("LOGICAL_CELL_CAPACITY_EXCEEDED")

    effective_decoder_limit = min(capacity.physical_decoder_limit, model_count)
    per_model_tokens, remainder = divmod(budget["max_tokens"], model_count)
    cells: list[CellLease] = [
        CellLease("cell-00", "RETRIEVE", ExecutionClass.SCRIPT, 0, None),
        CellLease("cell-01", "PROVENANCE_BUDGET_CHECK", ExecutionClass.SCRIPT, 0, None),
    ]
    for ordinal, lane in enumerate(lanes):
        cells.append(
            CellLease(
                cell_id=f"cell-{len(cells):02d}",
                function=f"MODEL:{lane}",
                execution_class=ExecutionClass.MODEL,
                model_token_budget=per_model_tokens + (1 if ordinal < remainder else 0),
                physical_decoder_lane=ordinal % effective_decoder_limit,
            )
        )
    while len(cells) < 9:
        cells.append(CellLease(f"cell-{len(cells):02d}", "IDLE", ExecutionClass.SCRIPT, 0, None))
    cells.append(CellLease("cell-09", "SYNTHESIZE", ExecutionClass.SCRIPT, 0, None))
    if len(cells) != 10:
        raise GridScheduleError("GRID10_INTERNAL_CELL_COUNT_MISMATCH")

    canonical: dict[str, Any] = {
        "schema": PLAN_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "entry_binding_schema": ENTRY_BINDING_SCHEMA,
        "ingress_id": packet.ingress_id,
        "causal_id": packet.causal_id,
        "entity_generation": packet.entity_generation,
        "entry_event_sha256": packet.event_sha256,
        "entry_admission_sha256": packet.admission_sha256,
        "route_event_sha256": decision.event_sha256,
        "route_decision_sha256": decision.decision_sha256,
        "router_policy_sha256": decision.router_policy_sha256,
        "engine_identity_sha256": decision.engine_identity_sha256,
        "resolved_engine_identity": decision.resolved_engine_identity,
        "resolved_engine_class": decision.resolved_engine_class,
        "resolved_engine_artifact_sha256": decision.resolved_engine_artifact_sha256,
        "capacity_receipt_sha256": capacity.capacity_receipt_sha256,
        "runtime_profile_id": capacity.profile_id.strip(),
        "mode": mode.value,
        "logical_cell_count": 10,
        "model_call_count": model_count,
        "physical_decoder_limit": effective_decoder_limit,
        "max_wall_ms": budget["max_wall_ms"],
        "cells": [
            {
                "cell_id": cell.cell_id,
                "function": cell.function,
                "execution_class": cell.execution_class.value,
                "model_token_budget": cell.model_token_budget,
                "physical_decoder_lane": cell.physical_decoder_lane,
            }
            for cell in cells
        ],
    }
    try:
        plan_sha256 = hashlib.sha256(canonicalize(canonical)).hexdigest()
    except CanonicalizationError as exc:
        raise GridScheduleError(f"GRID_PLAN_CANONICALIZATION_FAILED:{exc}") from exc

    return GridPlan(
        schema=canonical["schema"],
        canonicalization_schema=CANONICALIZATION_SCHEMA,
        entry_binding_schema=ENTRY_BINDING_SCHEMA,
        plan_sha256=plan_sha256,
        ingress_id=packet.ingress_id,
        causal_id=packet.causal_id,
        entity_generation=packet.entity_generation,
        entry_event_sha256=packet.event_sha256,
        entry_admission_sha256=packet.admission_sha256,
        route_event_sha256=decision.event_sha256,
        route_decision_sha256=decision.decision_sha256,
        router_policy_sha256=decision.router_policy_sha256,
        engine_identity_sha256=decision.engine_identity_sha256,
        resolved_engine_identity=decision.resolved_engine_identity,
        resolved_engine_class=decision.resolved_engine_class,
        resolved_engine_artifact_sha256=decision.resolved_engine_artifact_sha256,
        capacity_receipt_sha256=capacity.capacity_receipt_sha256,
        runtime_profile_id=capacity.profile_id.strip(),
        mode=mode,
        logical_cell_count=10,
        model_call_count=model_count,
        physical_decoder_limit=effective_decoder_limit,
        max_wall_ms=budget["max_wall_ms"],
        cells=tuple(cells),
    )
