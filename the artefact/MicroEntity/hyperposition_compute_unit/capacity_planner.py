#!/usr/bin/env python3
"""Static HCU capacity planner.

This is planning-only math. It does not benchmark or mint runtime acceptance evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Optional


MIB = 1024 * 1024
GIB = 1024 * MIB


@dataclass(frozen=True)
class Hardware:
    cpu_cores: int
    memory_gib: float
    reserve_gib: float = 3.0

    @property
    def usable_bytes(self) -> int:
        return max(0, int((self.memory_gib - self.reserve_gib) * GIB))


@dataclass(frozen=True)
class PlanningAssumptions:
    parameters: int = 800_000_000
    bits_per_weight: float = 4.5
    shared_base_dynamic_overhead_mib: int = 768
    shared_cell_incremental_state_mib: int = 192
    full_cell_runtime_overhead_mib: int = 384
    full_cell_kv_state_mib: int = 256

    @property
    def quantized_weight_bytes(self) -> int:
        return int(self.parameters * self.bits_per_weight / 8.0)


@dataclass(frozen=True)
class CapacityEstimate:
    mode: str
    logical_cells: int
    simultaneous_cpu_lanes: int
    classification: str
    bytes_per_cell_or_increment: int
    shared_bytes: int = 0


def plan_shared_base(hw: Hardware, a: PlanningAssumptions) -> CapacityEstimate:
    shared = a.quantized_weight_bytes + a.shared_base_dynamic_overhead_mib * MIB
    increment = a.shared_cell_incremental_state_mib * MIB
    remaining = max(0, hw.usable_bytes - shared)
    cells = floor(remaining / increment) if increment else 0
    return CapacityEstimate(
        mode="SHARED_BASE_08B_CELL",
        logical_cells=max(0, cells),
        simultaneous_cpu_lanes=min(hw.cpu_cores, max(0, cells)),
        classification="PLANNING_ONLY_NOT_RUNTIME_EVIDENCE",
        bytes_per_cell_or_increment=increment,
        shared_bytes=shared,
    )


def plan_full_resident(hw: Hardware, a: PlanningAssumptions) -> CapacityEstimate:
    per_cell = (
        a.quantized_weight_bytes
        + a.full_cell_runtime_overhead_mib * MIB
        + a.full_cell_kv_state_mib * MIB
    )
    cells = floor(hw.usable_bytes / per_cell) if per_cell else 0
    return CapacityEstimate(
        mode="FULL_RESIDENT_08B_CELL",
        logical_cells=max(0, cells),
        simultaneous_cpu_lanes=min(hw.cpu_cores, max(0, cells)),
        classification="PLANNING_ONLY_NOT_RUNTIME_EVIDENCE",
        bytes_per_cell_or_increment=per_cell,
    )


def measured_capacity(
    hw: Hardware,
    measured_rss_mib: Optional[float],
    *,
    mode: str,
) -> CapacityEstimate:
    if measured_rss_mib is None or measured_rss_mib <= 0:
        raise ValueError("exact measured RSS is required for measured capacity")
    per_cell = int(measured_rss_mib * MIB)
    cells = floor(hw.usable_bytes / per_cell)
    return CapacityEstimate(
        mode=mode,
        logical_cells=max(0, cells),
        simultaneous_cpu_lanes=min(hw.cpu_cores, max(0, cells)),
        classification="MEASURED_INPUT_REQUIRED_EXTERNAL_TO_THIS_PLANNER",
        bytes_per_cell_or_increment=per_cell,
    )


def main() -> None:
    hw = Hardware(cpu_cores=4, memory_gib=16, reserve_gib=3)
    a = PlanningAssumptions()
    for estimate in (plan_shared_base(hw, a), plan_full_resident(hw, a)):
        print(
            f"{estimate.mode}: logical_cells={estimate.logical_cells} "
            f"cpu_lanes={estimate.simultaneous_cpu_lanes} "
            f"classification={estimate.classification}"
        )


if __name__ == "__main__":
    main()
