from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

try:
    from .entry_fabric_v1 import EntryAdmissionError, XenoIngressPacket
except ImportError:  # direct script/module execution
    from entry_fabric_v1 import EntryAdmissionError, XenoIngressPacket

ROUTE_SCHEMA_ID = "XENO_GRID10_ROUTE_DECISION/v1"
GRID10_CELL_COUNT = 10
ALLOWED_MODES = {"DIRECT", "XENO_GRID10", "XENO_COGSIM10", "XENO_WM_TEST", "XENO_NESTED_SIM"}


def _sha256(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class LogicalCell:
    slot: int
    function: str

    @property
    def cell_id(self) -> str:
        return f"xeno-cell-{self.slot:02d}"


DEFAULT_GRID10_FUNCTIONS = (
    "observe",
    "retrieve",
    "hypothesis",
    "counterhypothesis",
    "critic",
    "planner",
    "falsifier",
    "calibrator",
    "integrator",
    "reducer",
)


@dataclass(frozen=True)
class RouteDecision:
    event_sha256: str
    generation: int
    mode: str
    selected_cells: tuple[str, ...]
    selected_functions: tuple[str, ...]
    reason_code: str
    physical_worker_budget: int

    @property
    def decision_sha256(self) -> str:
        return _sha256(
            {
                "schema_id": ROUTE_SCHEMA_ID,
                "event_sha256": self.event_sha256,
                "generation": self.generation,
                "mode": self.mode,
                "selected_cells": list(self.selected_cells),
                "selected_functions": list(self.selected_functions),
                "reason_code": self.reason_code,
                "physical_worker_budget": self.physical_worker_budget,
            }
        )


class Grid10Scheduler:
    """Deterministic XPU-like control skeleton over logical function cells.

    This scheduler allocates logical cells only. physical_worker_budget is a separate
    execution ceiling and MUST NOT be reported as logical cell count.
    """

    def __init__(
        self,
        *,
        current_generation: int,
        physical_worker_budget: int = 1,
        functions: Iterable[str] = DEFAULT_GRID10_FUNCTIONS,
    ) -> None:
        if current_generation < 0:
            raise ValueError("current_generation must be non-negative")
        if physical_worker_budget <= 0:
            raise ValueError("physical_worker_budget must be positive")
        function_tuple = tuple(functions)
        if len(function_tuple) != GRID10_CELL_COUNT or len(set(function_tuple)) != GRID10_CELL_COUNT:
            raise ValueError("GRID10 requires exactly ten unique logical functions")
        self.current_generation = current_generation
        self.physical_worker_budget = physical_worker_budget
        self.cells = tuple(LogicalCell(i, fn) for i, fn in enumerate(function_tuple))

    def _mode_for(self, packet: XenoIngressPacket) -> tuple[str, str]:
        caps = set(packet.capability_scope)
        # Mode intent is an admitted capability hint; it cannot grant effect authority.
        if "mode:nested_sim" in caps:
            return "XENO_NESTED_SIM", "CAPABILITY_HINT_NESTED_SIM"
        if "mode:wm_test" in caps:
            return "XENO_WM_TEST", "CAPABILITY_HINT_WM_TEST"
        if "mode:cogsim10" in caps:
            return "XENO_COGSIM10", "CAPABILITY_HINT_COGSIM10"
        if "mode:grid10" in caps or packet.resource_budget.max_cells >= GRID10_CELL_COUNT:
            return "XENO_GRID10", "GRID10_BASELINE"
        return "DIRECT", "CHEAP_DIRECT_PATH"

    def route(self, packet: XenoIngressPacket) -> RouteDecision:
        packet.assert_current_generation(self.current_generation)
        if "effect_request" in packet.permissions and not packet.capability_scope:
            raise EntryAdmissionError("effect_request ingress requires explicit capability scope")

        mode, reason = self._mode_for(packet)
        if mode not in ALLOWED_MODES:
            raise EntryAdmissionError(f"unsupported routed mode: {mode}")

        if mode == "DIRECT":
            selected = (self.cells[0], self.cells[-1])
        elif mode == "XENO_GRID10":
            selected = self.cells
        elif mode == "XENO_COGSIM10":
            selected = self.cells
        elif mode == "XENO_WM_TEST":
            selected = tuple(c for c in self.cells if c.function in {
                "observe", "retrieve", "hypothesis", "counterhypothesis", "planner",
                "falsifier", "calibrator", "integrator", "reducer"
            })
        else:  # NESTED_SIM remains bounded by the same logical baseline in v1.
            selected = self.cells

        selected = selected[: packet.resource_budget.max_cells]
        return RouteDecision(
            event_sha256=packet.event_sha256,
            generation=packet.generation,
            mode=mode,
            selected_cells=tuple(c.cell_id for c in selected),
            selected_functions=tuple(c.function for c in selected),
            reason_code=reason,
            physical_worker_budget=self.physical_worker_budget,
        )
