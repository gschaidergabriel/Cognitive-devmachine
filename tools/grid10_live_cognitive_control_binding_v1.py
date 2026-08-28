#!/usr/bin/env python3
"""Bind the Frankenstein-2 cognitive control plane to the persistent GRID10 loop.

Triggerword-4 Stage-1/2 bridge.  This module consumes exactly one immutable
``ControlSnapshot`` at a cognitive-cycle boundary and derives two live consumers from that
same snapshot:

1. pulse cadence for the persistent scheduler; and
2. mechanically distinct GRID cell mode/gain decisions.

It deliberately does not create a second state authority, execute external effects, or call
providers.  The control plane, scheduler, AgencyState and heartbeat all use the same physical
UnifiedDB path.  Cell decisions are control metadata for cognition; they are not world facts.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from frankenstein2_cognitive_control_plane_v1 import (
    CognitiveControlPlane,
    ControlMode,
    ControlSnapshot,
)
from grid10_persistent_scheduler_v1 import (
    PersistentCognitiveScheduler,
    SchedulerConfig,
    SchedulerCycleResult,
)

SCHEMA = "GRID10_LIVE_COGNITIVE_CONTROL_BINDING/v1"

GRID_CELLS = (
    "orientation",
    "goal",
    "epistemic",
    "hypothesis",
    "world",
    "planning",
    "retrieval",
    "microlab",
    "delegation",
    "critic",
)


@dataclass(frozen=True)
class GridCellControl:
    cell: str
    mode: str
    gain: float
    compute_allowed: bool
    downstream_output_allowed: bool
    durable_memory_write_allowed: bool
    local_diagnostic_gain: float
    downstream_gain: float
    result_state: str


@dataclass(frozen=True)
class LatchedControlView:
    schema: str
    control_epoch: int
    snapshot_digest: str
    pulse_salience_threshold: float
    active_interval_seconds: float
    hold_interval_seconds: float
    idle_interval_seconds: float
    grid_cells: tuple[GridCellControl, ...]


@dataclass(frozen=True)
class ControlledCycleResult:
    schema: str
    control_epoch: int
    control_snapshot_digest: str
    scheduler: Mapping[str, Any]
    grid_cells: tuple[Mapping[str, Any], ...]
    external_effect_executed: bool
    provider_calls: int


def _grid_cell_control(snapshot: ControlSnapshot, cell: str) -> GridCellControl:
    if cell not in GRID_CELLS:
        raise ValueError(f"UNKNOWN_GRID_CELL:{cell}")
    mode = snapshot.mode(f"grid.{cell}.mode")
    gain = snapshot.float(f"grid.{cell}.gain")

    if mode == ControlMode.COMPUTE_OFF:
        return GridCellControl(
            cell=cell,
            mode=mode.value,
            gain=gain,
            compute_allowed=False,
            downstream_output_allowed=False,
            durable_memory_write_allowed=False,
            local_diagnostic_gain=0.0,
            downstream_gain=0.0,
            result_state="NOT_COMPUTED",
        )
    if mode == ControlMode.OUTPUT_OFF:
        return GridCellControl(
            cell=cell,
            mode=mode.value,
            gain=gain,
            compute_allowed=True,
            downstream_output_allowed=False,
            durable_memory_write_allowed=True,
            local_diagnostic_gain=gain,
            downstream_gain=0.0,
            result_state="LOCAL_ONLY_OUTPUT_WITHHELD",
        )
    if mode == ControlMode.MEMORY_OFF:
        return GridCellControl(
            cell=cell,
            mode=mode.value,
            gain=gain,
            compute_allowed=True,
            downstream_output_allowed=True,
            durable_memory_write_allowed=False,
            local_diagnostic_gain=gain,
            downstream_gain=gain,
            result_state="EPHEMERAL_NO_DURABLE_MEMORY",
        )
    return GridCellControl(
        cell=cell,
        mode=mode.value,
        gain=gain,
        compute_allowed=True,
        downstream_output_allowed=True,
        durable_memory_write_allowed=True,
        local_diagnostic_gain=gain,
        downstream_gain=gain,
        result_state="ACTIVE",
    )


def latch_control_view(snapshot: ControlSnapshot) -> LatchedControlView:
    """Compile one immutable snapshot into all currently wired live consumers."""
    return LatchedControlView(
        schema=SCHEMA,
        control_epoch=snapshot.control_epoch,
        snapshot_digest=snapshot.snapshot_digest,
        pulse_salience_threshold=snapshot.float("pulse.salience_threshold"),
        active_interval_seconds=snapshot.float("pulse.active_interval_seconds"),
        hold_interval_seconds=snapshot.float("pulse.hold_interval_seconds"),
        idle_interval_seconds=snapshot.float("pulse.idle_interval_seconds"),
        grid_cells=tuple(_grid_cell_control(snapshot, cell) for cell in GRID_CELLS),
    )


class LiveControlledCognitiveLoop:
    """Latch controls once, then run one scheduler cycle against that exact control view."""

    def __init__(
        self,
        unified_db: Path,
        frames_jsonl: Path,
        *,
        allow_regulator_writes: bool = False,
        trusted_normal_test_fixture: bool = False,
    ) -> None:
        self.unified_db = Path(unified_db)
        self.frames_jsonl = Path(frames_jsonl)
        self.allow_regulator_writes = bool(allow_regulator_writes)
        self.trusted_normal_test_fixture = bool(trusted_normal_test_fixture)
        self.controls = CognitiveControlPlane(self.unified_db)

    def latch(self) -> LatchedControlView:
        return latch_control_view(self.controls.snapshot())

    def _scheduler_for(self, view: LatchedControlView) -> PersistentCognitiveScheduler:
        return PersistentCognitiveScheduler(
            self.unified_db,
            self.frames_jsonl,
            config=SchedulerConfig(
                active_interval_seconds=view.active_interval_seconds,
                hold_poll_seconds=view.hold_interval_seconds,
                idle_poll_seconds=view.idle_interval_seconds,
                allow_regulator_writes=self.allow_regulator_writes,
                trusted_normal_test_fixture=self.trusted_normal_test_fixture,
            ),
        )

    def cycle_once(
        self,
        *,
        cycle_id: str,
        now_ts: float | None = None,
        observed_events: Iterable[str] = (),
    ) -> ControlledCycleResult:
        # Critical atomicity rule: latch exactly once at the boundary.  Any patch committed
        # after this read is visible only to a later cycle.
        view = self.latch()
        scheduler = self._scheduler_for(view)
        result: SchedulerCycleResult = scheduler.cycle_once(
            cycle_id=cycle_id,
            now_ts=now_ts,
            observed_events=tuple(observed_events),
        )
        return ControlledCycleResult(
            schema=SCHEMA,
            control_epoch=view.control_epoch,
            control_snapshot_digest=view.snapshot_digest,
            scheduler=asdict(result),
            grid_cells=tuple(asdict(cell) for cell in view.grid_cells),
            external_effect_executed=False,
            provider_calls=0,
        )


def grid_cell_map(view: LatchedControlView) -> dict[str, GridCellControl]:
    return {cell.cell: cell for cell in view.grid_cells}
