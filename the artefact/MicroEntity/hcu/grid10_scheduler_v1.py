#!/usr/bin/env python3
"""Deterministic HCU GRID10/control-plane scheduler candidate.

Consumes an already-admitted EntryPacket and a separately trusted runtime-capacity
snapshot. It allocates logical function cells, not model identities or effect authority.
Logical cell population, model-call budget and physical decode concurrency remain
separate quantities.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from xeno_entry_fabric_v1 import EntryPacket


class GridScheduleError(ValueError):
    pass


class HCUMode(str, Enum):
    DIRECT = "DIRECT"
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
        if len(self.capacity_receipt_sha256) != 64 or any(
            ch not in "0123456789abcdef" for ch in self.capacity_receipt_sha256
        ):
            raise GridScheduleError("runtime_capacity.capacity_receipt_sha256:LOWERCASE_SHA256_REQUIRED")
        for name in ("max_logical_cells", "physical_decoder_limit"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise GridScheduleError(f"runtime_capacity.{name}:POSITIVE_INTEGER_REQUIRED")


@dataclass(frozen=True)
class RoutingSignals:
    ambiguity: float = 0.0
    reasoning_horizon: float = 0.0
    environment_dynamics: float = 0.0
    effect_pressure: float = 0.0
    value_of_information: float = 0.0
    cheaper_modes_exhausted: bool = False
    scaleout_admitted: bool = False

    def validate(self) -> None:
        for name in (
            "ambiguity",
            "reasoning_horizon",
            "environment_dynamics",
            "effect_pressure",
            "value_of_information",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise GridScheduleError(f"routing.{name}:NUMBER_REQUIRED")
            if not 0.0 <= float(value) <= 1.0:
                raise GridScheduleError(f"routing.{name}:UNIT_INTERVAL_REQUIRED")
        if not isinstance(self.cheaper_modes_exhausted, bool) or not isinstance(self.scaleout_admitted, bool):
            raise GridScheduleError("routing.boolean_flags:BOOLEAN_REQUIRED")


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
    plan_sha256: str
    ingress_id: str
    causal_id: str
    entity_generation: int
    entry_admission_sha256: str
    capacity_receipt_sha256: str
    runtime_profile_id: str
    mode: HCUMode
    logical_cell_count: int
    model_call_count: int
    physical_decoder_limit: int
    max_wall_ms: int
    cells: tuple[CellLease, ...]


_TOPOLOGIES: dict[HCUMode, tuple[tuple[str, ExecutionClass], ...]] = {
    HCUMode.DIRECT: (("DIRECT_DETERMINISTIC", ExecutionClass.SCRIPT),),
    HCUMode.GRID10: (
        ("RETRIEVE", ExecutionClass.SCRIPT),
        ("OBSERVE", ExecutionClass.SCRIPT),
        ("HYPOTHESIS", ExecutionClass.MODEL),
        ("COUNTERHYPOTHESIS", ExecutionClass.MODEL),
        ("CRITIC", ExecutionClass.SCRIPT),
        ("PLAN", ExecutionClass.SCRIPT),
        ("CALIBRATE", ExecutionClass.SCRIPT),
        ("PROVENANCE_CHECK", ExecutionClass.SCRIPT),
        ("BUDGET_CHECK", ExecutionClass.SCRIPT),
        ("SYNTHESIZE", ExecutionClass.SCRIPT),
    ),
    HCUMode.COGSIM10: (
        ("RETRIEVE", ExecutionClass.SCRIPT),
        ("HYPOTHESIS_A", ExecutionClass.MODEL),
        ("HYPOTHESIS_B", ExecutionClass.MODEL),
        ("COUNTERHYPOTHESIS", ExecutionClass.MODEL),
        ("CRITIC", ExecutionClass.MODEL),
        ("PLAN", ExecutionClass.SCRIPT),
        ("SIMULATE", ExecutionClass.SCRIPT),
        ("CALIBRATE", ExecutionClass.SCRIPT),
        ("PROVENANCE_CHECK", ExecutionClass.SCRIPT),
        ("SYNTHESIZE", ExecutionClass.SCRIPT),
    ),
    HCUMode.WM_TEST: (
        ("RETRIEVE", ExecutionClass.SCRIPT),
        ("OBSERVE", ExecutionClass.SCRIPT),
        ("TRANSITION_HYPOTHESIS", ExecutionClass.MODEL),
        ("COUNTER_TRANSITION", ExecutionClass.MODEL),
        ("WORLD_PREDICT_A", ExecutionClass.MODEL),
        ("WORLD_PREDICT_B", ExecutionClass.MODEL),
        ("FALSIFIER", ExecutionClass.SCRIPT),
        ("CALIBRATE", ExecutionClass.SCRIPT),
        ("PROVENANCE_CHECK", ExecutionClass.SCRIPT),
        ("SYNTHESIZE", ExecutionClass.SCRIPT),
    ),
    HCUMode.NESTED_SIM: (
        ("RETRIEVE", ExecutionClass.SCRIPT),
        ("WORLD_PREDICT", ExecutionClass.MODEL),
        ("SIMULATED_COGNITION_A", ExecutionClass.MODEL),
        ("SIMULATED_COGNITION_B", ExecutionClass.MODEL),
        ("HYPOTHESIS", ExecutionClass.MODEL),
        ("COUNTERHYPOTHESIS", ExecutionClass.MODEL),
        ("PLAN", ExecutionClass.SCRIPT),
        ("FALSIFIER", ExecutionClass.SCRIPT),
        ("CALIBRATE", ExecutionClass.SCRIPT),
        ("SYNTHESIZE", ExecutionClass.SCRIPT),
    ),
}


def choose_mode(signals: RoutingSignals) -> HCUMode:
    signals.validate()
    if signals.scaleout_admitted and signals.value_of_information >= 0.90:
        return HCUMode.SCALEOUT
    if (
        signals.cheaper_modes_exhausted
        and signals.environment_dynamics >= 0.75
        and signals.reasoning_horizon >= 0.75
        and signals.value_of_information >= 0.75
    ):
        return HCUMode.NESTED_SIM
    if signals.environment_dynamics >= 0.60 and signals.reasoning_horizon >= 0.45:
        return HCUMode.WM_TEST
    if signals.reasoning_horizon >= 0.55 or signals.effect_pressure >= 0.65:
        return HCUMode.COGSIM10
    if signals.ambiguity >= 0.20 or signals.value_of_information >= 0.35:
        return HCUMode.GRID10
    return HCUMode.DIRECT


def _entry_budget(packet: EntryPacket) -> dict[str, int]:
    if not isinstance(packet, EntryPacket):
        raise GridScheduleError("ADMITTED_ENTRY_PACKET_REQUIRED")
    budget = dict(packet.budget)
    required = {"max_model_calls", "max_tokens", "max_wall_ms"}
    if set(budget) != required:
        raise GridScheduleError("ENTRY_BUDGET_CONTRACT_MISMATCH")
    return budget


def compile_plan(packet: EntryPacket, *, mode: HCUMode, capacity: RuntimeCapacity) -> GridPlan:
    budget = _entry_budget(packet)
    capacity.validate()
    if not isinstance(mode, HCUMode):
        raise GridScheduleError("HCU_MODE_REQUIRED")
    if mode is HCUMode.SCALEOUT:
        raise GridScheduleError("SCALEOUT_REQUIRES_SEPARATE_ADMITTED_SCALE_PROFILE")

    topology = _TOPOLOGIES[mode]
    logical_count = len(topology)
    if logical_count > capacity.max_logical_cells:
        raise GridScheduleError("LOGICAL_CELL_CAPACITY_EXCEEDED")

    model_indices = [index for index, (_, execution) in enumerate(topology) if execution is ExecutionClass.MODEL]
    model_count = len(model_indices)
    if model_count > budget["max_model_calls"]:
        raise GridScheduleError("MODEL_CALL_BUDGET_EXCEEDED")
    if model_count and budget["max_tokens"] < model_count:
        raise GridScheduleError("MODEL_TOKEN_BUDGET_TOO_SMALL")

    effective_decoder_limit = min(capacity.physical_decoder_limit, model_count) if model_count else 0
    per_model_tokens = budget["max_tokens"] // model_count if model_count else 0
    token_remainder = budget["max_tokens"] - per_model_tokens * model_count if model_count else 0
    model_ordinal = 0
    cells: list[CellLease] = []
    for index, (function, execution_class) in enumerate(topology):
        if execution_class is ExecutionClass.MODEL:
            model_token_budget = per_model_tokens + (1 if model_ordinal < token_remainder else 0)
            decoder_lane = model_ordinal % effective_decoder_limit
            model_ordinal += 1
        else:
            model_token_budget = 0
            decoder_lane = None
        cells.append(
            CellLease(
                cell_id=f"cell-{index:02d}",
                function=function,
                execution_class=execution_class,
                model_token_budget=model_token_budget,
                physical_decoder_lane=decoder_lane,
            )
        )

    canonical: dict[str, Any] = {
        "schema": "HCU_GRID_PLAN/v1",
        "ingress_id": packet.ingress_id,
        "causal_id": packet.causal_id,
        "entity_generation": packet.entity_generation,
        "entry_admission_sha256": packet.admission_sha256,
        "capacity_receipt_sha256": capacity.capacity_receipt_sha256,
        "runtime_profile_id": capacity.profile_id.strip(),
        "mode": mode.value,
        "logical_cell_count": logical_count,
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
    plan_sha256 = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return GridPlan(
        plan_sha256=plan_sha256,
        cells=tuple(cells),
        **{key: value for key, value in canonical.items() if key != "cells"},
    )
