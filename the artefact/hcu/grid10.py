#!/usr/bin/env python3
"""Deterministic 10-cell HCU baseline scheduler.

This module allocates logical function cells only. It does not execute a model, mutate
canonical state, or perform effects. Physical decode concurrency is carried as a separate
budget so logical-cell count can never silently become a hardware-performance claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable
import hashlib
import json

try:
    from .entry_fabric import EntityOSEntryPacket
except ImportError:  # direct-file execution / focused isolated tests
    from entry_fabric import EntityOSEntryPacket


class HCUMode(str, Enum):
    DIRECT = "DIRECT"
    GRID10 = "GRID10"
    COGSIM10 = "COGSIM10"
    WM_TEST = "WM_TEST"
    NESTED_SIM = "NESTED_SIM"
    SCALEOUT = "SCALEOUT"


class FunctionClass(str, Enum):
    RETRIEVE = "RETRIEVE"
    OBSERVE = "OBSERVE"
    HYPOTHESIS = "HYPOTHESIS"
    COUNTERHYPOTHESIS = "COUNTERHYPOTHESIS"
    CRITIC = "CRITIC"
    PLAN = "PLAN"
    CALIBRATE = "CALIBRATE"
    WORLD_PREDICT = "WORLD_PREDICT"
    SIMULATE = "SIMULATE"
    SYNTHESIZE = "SYNTHESIZE"


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
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be within [0,1]")


@dataclass(frozen=True)
class LogicalCellLease:
    cell_id: str
    function: FunctionClass
    token_budget: int
    context_budget: int
    physical_worker_lane: int


@dataclass(frozen=True)
class GridPlan:
    plan_id: str
    ingress_id: str
    causal_id: str
    generation: int
    mode: HCUMode
    logical_cell_count: int
    physical_decode_limit: int
    cells: tuple[LogicalCellLease, ...]
    world_state_canonical: bool = False
    direct_effect_authority: bool = False

    def validate(self) -> None:
        if self.logical_cell_count != len(self.cells):
            raise ValueError("logical_cell_count must equal number of leases")
        if self.mode in {HCUMode.GRID10, HCUMode.COGSIM10, HCUMode.WM_TEST, HCUMode.NESTED_SIM}:
            if self.logical_cell_count != 10:
                raise ValueError("baseline multi-cell modes require exactly 10 logical cells")
        if self.physical_decode_limit <= 0:
            raise ValueError("physical_decode_limit must be > 0")
        if self.physical_decode_limit > self.logical_cell_count:
            raise ValueError("physical decode concurrency cannot exceed logical cell population")
        if self.world_state_canonical:
            raise ValueError("simulation/world state cannot be canonical")
        if self.direct_effect_authority:
            raise ValueError("grid plans cannot hold direct effect authority")
        expected_ids = [f"cell-{index:02d}" for index in range(self.logical_cell_count)]
        if [cell.cell_id for cell in self.cells] != expected_ids:
            raise ValueError("cell ids must be contiguous and deterministic")
        for cell in self.cells:
            if cell.token_budget <= 0 or cell.context_budget <= 0:
                raise ValueError("cell budgets must be > 0")
            if not 0 <= cell.physical_worker_lane < self.physical_decode_limit:
                raise ValueError("physical_worker_lane outside admitted decode limit")


class HCUGrid10Scheduler:
    """Compile an immutable ingress packet into a bounded logical-cell plan."""

    _TOPOLOGIES: dict[HCUMode, tuple[FunctionClass, ...]] = {
        HCUMode.GRID10: (
            FunctionClass.RETRIEVE,
            FunctionClass.OBSERVE,
            FunctionClass.HYPOTHESIS,
            FunctionClass.COUNTERHYPOTHESIS,
            FunctionClass.CRITIC,
            FunctionClass.PLAN,
            FunctionClass.CALIBRATE,
            FunctionClass.HYPOTHESIS,
            FunctionClass.CRITIC,
            FunctionClass.SYNTHESIZE,
        ),
        HCUMode.COGSIM10: (
            FunctionClass.RETRIEVE,
            FunctionClass.HYPOTHESIS,
            FunctionClass.HYPOTHESIS,
            FunctionClass.COUNTERHYPOTHESIS,
            FunctionClass.COUNTERHYPOTHESIS,
            FunctionClass.CRITIC,
            FunctionClass.PLAN,
            FunctionClass.SIMULATE,
            FunctionClass.CALIBRATE,
            FunctionClass.SYNTHESIZE,
        ),
        HCUMode.WM_TEST: (
            FunctionClass.RETRIEVE,
            FunctionClass.OBSERVE,
            FunctionClass.HYPOTHESIS,
            FunctionClass.COUNTERHYPOTHESIS,
            FunctionClass.WORLD_PREDICT,
            FunctionClass.WORLD_PREDICT,
            FunctionClass.SIMULATE,
            FunctionClass.CRITIC,
            FunctionClass.CALIBRATE,
            FunctionClass.SYNTHESIZE,
        ),
        HCUMode.NESTED_SIM: (
            FunctionClass.RETRIEVE,
            FunctionClass.OBSERVE,
            FunctionClass.WORLD_PREDICT,
            FunctionClass.SIMULATE,
            FunctionClass.HYPOTHESIS,
            FunctionClass.COUNTERHYPOTHESIS,
            FunctionClass.PLAN,
            FunctionClass.CRITIC,
            FunctionClass.CALIBRATE,
            FunctionClass.SYNTHESIZE,
        ),
    }

    @staticmethod
    def choose_mode(signals: RoutingSignals) -> HCUMode:
        signals.validate()
        if signals.scaleout_admitted and signals.value_of_information >= 0.9:
            return HCUMode.SCALEOUT
        if (
            signals.cheaper_modes_exhausted
            and signals.environment_dynamics >= 0.75
            and signals.reasoning_horizon >= 0.75
            and signals.value_of_information >= 0.75
        ):
            return HCUMode.NESTED_SIM
        if signals.environment_dynamics >= 0.6 and signals.reasoning_horizon >= 0.45:
            return HCUMode.WM_TEST
        if signals.reasoning_horizon >= 0.55 or signals.effect_pressure >= 0.65:
            return HCUMode.COGSIM10
        if signals.ambiguity >= 0.2 or signals.value_of_information >= 0.35:
            return HCUMode.GRID10
        return HCUMode.DIRECT

    @classmethod
    def compile(cls, packet: EntityOSEntryPacket, mode: HCUMode) -> GridPlan:
        if mode is HCUMode.DIRECT:
            topology: tuple[FunctionClass, ...] = (FunctionClass.SYNTHESIZE,)
        elif mode is HCUMode.SCALEOUT:
            raise ValueError("SCALEOUT requires a separately admitted hardware/runtime profile")
        else:
            topology = cls._TOPOLOGIES[mode]

        logical_count = len(topology)
        physical_limit = min(packet.resource_budget.max_physical_decoders, logical_count)
        if mode is not HCUMode.DIRECT and packet.resource_budget.max_logical_cells < 10:
            raise ValueError("selected mode requires a 10-cell logical budget")

        total_tokens = packet.resource_budget.max_compute_tokens
        base_tokens = total_tokens // logical_count
        if base_tokens <= 0:
            raise ValueError("compute token budget too small for selected topology")
        remainder = total_tokens - base_tokens * logical_count

        context_budget = packet.resource_budget.max_context_tokens
        cells: list[LogicalCellLease] = []
        for index, function in enumerate(topology):
            token_budget = base_tokens + (1 if index < remainder else 0)
            cells.append(
                LogicalCellLease(
                    cell_id=f"cell-{index:02d}",
                    function=function,
                    token_budget=token_budget,
                    context_budget=context_budget,
                    physical_worker_lane=index % physical_limit,
                )
            )

        plan_payload = {
            "schema": "HCU_GRID_PLAN/v1",
            "ingress_id": packet.ingress_id,
            "causal_id": packet.causal_id,
            "generation": packet.generation,
            "mode": mode.value,
            "logical_cell_count": logical_count,
            "physical_decode_limit": physical_limit,
            "cells": [
                {
                    "cell_id": cell.cell_id,
                    "function": cell.function.value,
                    "token_budget": cell.token_budget,
                    "context_budget": cell.context_budget,
                    "physical_worker_lane": cell.physical_worker_lane,
                }
                for cell in cells
            ],
        }
        plan_id = hashlib.sha256(
            json.dumps(plan_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        plan = GridPlan(
            plan_id=plan_id,
            ingress_id=packet.ingress_id,
            causal_id=packet.causal_id,
            generation=packet.generation,
            mode=mode,
            logical_cell_count=logical_count,
            physical_decode_limit=physical_limit,
            cells=tuple(cells),
        )
        plan.validate()
        return plan


def functions(plan: GridPlan) -> Iterable[FunctionClass]:
    plan.validate()
    return (cell.function for cell in plan.cells)
