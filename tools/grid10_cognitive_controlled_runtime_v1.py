#!/usr/bin/env python3
"""ControlSnapshot-bound persistent GRID10 runtime integration for Triggerword 4.

One immutable ControlSnapshot is latched before the cycle. That same object conditions the
v4 wake/heartbeat/pulse checkpoint and the downstream GRID cell/GWT/memory consumers.
Control changes during a cycle are observed only as an end-of-cycle change detector and do
not alter the current basis. Wake lineage remains owned exclusively by v4.

This adapter is provider-neutral and noncanonical. It never authorizes providers, effects,
completion, canonical truth, or model output as fact.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from typing import Any, Callable, Mapping

from frankenstein2_cognitive_control_plane_v1 import CognitiveControlPlane, ControlMode, ControlSnapshot
from grid10_cognitive_unified_runtime_v4 import (
    RuntimeCycleError,
    UnifiedCognitiveRuntimeV4,
    build_unified_cognitive_runtime_v4,
)

SCHEMA = "GRID10_CONTROLLED_COGNITIVE_RUNTIME/v1"
CELL_SCHEMA = "GRID10_CONTROLLED_CELL_EXECUTION/v1"
RECEIPT_SCHEMA = "GRID10_CONTROLLED_CYCLE_RECEIPT/v1"

GRID_CELL_NAMES: tuple[str, ...] = (
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

CellRunner = Callable[[str, float, Mapping[str, Any]], Any]


@dataclass(frozen=True)
class ControlledCellExecution:
    schema: str
    cell: str
    mode: str
    gain: float
    computed: bool
    emitted_to_gwt: bool
    eligible_for_memory_feed: bool
    candidate_digest: str | None
    error: str | None = None


@dataclass(frozen=True)
class ControlledCycleResult:
    schema: str
    tick_id: str
    control_epoch: int
    control_snapshot_digest: str
    control_epoch_after: int
    control_changed_during_cycle: bool
    active_interval_seconds: float
    hold_interval_seconds: float
    idle_interval_seconds: float
    workspace_ignition_threshold: float
    counterhypothesis_pressure: float
    agency_epoch_before: int
    agency_epoch_after: int
    assurance_mode: str
    next_action: str
    next_tick_not_before: float
    cells: tuple[ControlledCellExecution, ...]
    gwt_feed: tuple[Mapping[str, Any], ...]
    memory_feed: tuple[Mapping[str, Any], ...]
    receipt_digest: str


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path), isolation_level=None, timeout=10.0)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def _init_schema(path: Path) -> None:
    con = _connect(path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS grid10_controlled_cycle_receipts(
              tick_id TEXT PRIMARY KEY,
              receipt_schema TEXT NOT NULL,
              control_epoch INTEGER NOT NULL,
              control_snapshot_digest TEXT NOT NULL,
              control_epoch_after INTEGER NOT NULL,
              control_changed_during_cycle INTEGER NOT NULL,
              agency_epoch_before INTEGER NOT NULL,
              agency_epoch_after INTEGER NOT NULL,
              assurance_mode TEXT NOT NULL,
              next_action TEXT NOT NULL,
              receipt_json TEXT NOT NULL,
              receipt_digest TEXT NOT NULL,
              created_ts REAL NOT NULL
            )
            """
        )
    finally:
        con.close()


class ControlledGridRuntimeV1:
    """Provider-neutral live-control bridge around the persistent v4 runtime."""

    def __init__(
        self,
        runtime: UnifiedCognitiveRuntimeV4,
        control_plane: CognitiveControlPlane,
        unified_db: Path,
    ) -> None:
        self.runtime = runtime
        self.control_plane = control_plane
        self.unified_db = Path(unified_db)
        _init_schema(self.unified_db)

    @staticmethod
    def _cell_control(snapshot: ControlSnapshot, cell: str) -> tuple[ControlMode, float]:
        return snapshot.mode(f"grid.{cell}.mode"), snapshot.float(f"grid.{cell}.gain")

    def tick_once(
        self,
        *,
        tick_id: str,
        now_ts: float | None = None,
        observed_events: tuple[str, ...] = (),
        prewoken_goal_ids: tuple[str, ...] | None = None,
        trusted_axes: Mapping[str, Any] | None = None,
        extra_variables: Mapping[str, Any] | None = None,
        cell_runner: CellRunner | None = None,
    ) -> ControlledCycleResult:
        if not tick_id.strip():
            raise ValueError("tick_id required")
        if prewoken_goal_ids is not None:
            raise RuntimeCycleError(
                "PREWOKEN_WAKE_LINEAGE_UNSUPPORTED:runtime_owns_wake_due"
            )

        # The one immutable current-cycle basis. v4 receives this exact object rather than
        # independently re-reading the control plane.
        latched = self.control_plane.snapshot()
        active_interval = latched.float("pulse.active_interval_seconds")
        hold_interval = latched.float("pulse.hold_interval_seconds")
        idle_interval = latched.float("pulse.idle_interval_seconds")
        ignition = latched.float("grid.workspace_ignition_threshold")
        counterpressure = latched.float("grid.counterhypothesis_pressure")

        control_variables = dict(extra_variables or {})
        control_variables.update(
            {
                "control_snapshot_digest": latched.snapshot_digest,
                "control_epoch": latched.control_epoch,
                "grid_workspace_ignition_threshold": ignition,
                "grid_counterhypothesis_pressure": counterpressure,
            }
        )

        cycle = self.runtime.tick_once(
            tick_id=tick_id,
            interval=active_interval,
            hold_interval=hold_interval,
            now_ts=now_ts,
            observed_events=observed_events,
            control_snapshot=latched,
            trusted_axes=trusted_axes,
            extra_variables=control_variables,
        )

        cell_rows: list[ControlledCellExecution] = []
        gwt_feed: list[Mapping[str, Any]] = []
        memory_feed: list[Mapping[str, Any]] = []
        basis = {
            "tick_id": tick_id,
            "control_epoch": latched.control_epoch,
            "control_snapshot_digest": latched.snapshot_digest,
            "assurance_mode": cycle.assurance_mode,
            "controller_action": cycle.next_action,
            "counterhypothesis_pressure": counterpressure,
        }

        for cell in GRID_CELL_NAMES:
            mode, gain = self._cell_control(latched, cell)
            if mode == ControlMode.COMPUTE_OFF:
                cell_rows.append(
                    ControlledCellExecution(
                        CELL_SCHEMA,
                        cell,
                        mode.value,
                        gain,
                        False,
                        False,
                        False,
                        None,
                    )
                )
                continue

            candidate: Any = None
            error: str | None = None
            if cell_runner is None:
                error = "NO_CELL_RUNNER"
            else:
                try:
                    candidate = cell_runner(cell, gain, basis)
                except Exception as exc:
                    error = f"{type(exc).__name__}:{exc}"[:500]

            computed = cell_runner is not None
            digest = None if error is not None else _digest(candidate)
            emitted = bool(error is None and mode != ControlMode.OUTPUT_OFF and gain >= ignition)
            # Owner control law: OUTPUT_OFF is local-only diagnostics/regulation and cannot
            # re-enter downstream cognition through durable memory. Normal memory re-entry is
            # therefore reserved for ON; MEMORY_OFF also computes/outputs but remains ephemeral.
            memory_eligible = bool(error is None and mode == ControlMode.ON)
            row = ControlledCellExecution(
                CELL_SCHEMA,
                cell,
                mode.value,
                gain,
                computed,
                emitted,
                memory_eligible,
                digest,
                error,
            )
            cell_rows.append(row)

            candidate_row = {
                "cell": cell,
                "gain": gain,
                "candidate": candidate,
                "candidate_digest": digest,
                "control_snapshot_digest": latched.snapshot_digest,
            }
            if emitted:
                gwt_feed.append(candidate_row)
            if memory_eligible:
                memory_feed.append(candidate_row)

        # This is change detection only. It cannot alter the already-completed cycle basis.
        after = self.control_plane.snapshot()
        changed_during = bool(
            after.control_epoch != latched.control_epoch
            or after.snapshot_digest != latched.snapshot_digest
        )

        body = {
            "schema": RECEIPT_SCHEMA,
            "tick_id": tick_id,
            "control_epoch": latched.control_epoch,
            "control_snapshot_digest": latched.snapshot_digest,
            "control_epoch_after": after.control_epoch,
            "control_changed_during_cycle": changed_during,
            "active_interval_seconds": active_interval,
            "hold_interval_seconds": hold_interval,
            "idle_interval_seconds": idle_interval,
            "workspace_ignition_threshold": ignition,
            "counterhypothesis_pressure": counterpressure,
            "agency_epoch_before": cycle.agency_epoch_before,
            "agency_epoch_after": cycle.agency_epoch_after,
            "assurance_mode": cycle.assurance_mode,
            "next_action": cycle.next_action,
            "next_tick_not_before": cycle.next_tick_not_before,
            "cells": [asdict(x) for x in cell_rows],
            "gwt_feed_digests": [x["candidate_digest"] for x in gwt_feed],
            "memory_feed_digests": [x["candidate_digest"] for x in memory_feed],
        }
        receipt_digest = _digest(body)
        body["receipt_digest"] = receipt_digest

        con = _connect(self.unified_db)
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "INSERT INTO grid10_controlled_cycle_receipts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    tick_id,
                    RECEIPT_SCHEMA,
                    latched.control_epoch,
                    latched.snapshot_digest,
                    after.control_epoch,
                    1 if changed_during else 0,
                    cycle.agency_epoch_before,
                    cycle.agency_epoch_after,
                    cycle.assurance_mode,
                    cycle.next_action,
                    _canon(body),
                    receipt_digest,
                    time.time(),
                ),
            )
            con.execute("COMMIT")
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

        return ControlledCycleResult(
            schema=SCHEMA,
            tick_id=tick_id,
            control_epoch=latched.control_epoch,
            control_snapshot_digest=latched.snapshot_digest,
            control_epoch_after=after.control_epoch,
            control_changed_during_cycle=changed_during,
            active_interval_seconds=active_interval,
            hold_interval_seconds=hold_interval,
            idle_interval_seconds=idle_interval,
            workspace_ignition_threshold=ignition,
            counterhypothesis_pressure=counterpressure,
            agency_epoch_before=cycle.agency_epoch_before,
            agency_epoch_after=cycle.agency_epoch_after,
            assurance_mode=cycle.assurance_mode,
            next_action=cycle.next_action,
            next_tick_not_before=cycle.next_tick_not_before,
            cells=tuple(cell_rows),
            gwt_feed=tuple(gwt_feed),
            memory_feed=tuple(memory_feed),
            receipt_digest=receipt_digest,
        )


def build_controlled_grid_runtime_v1(
    unified_db: Path,
    *,
    allow_regulator_writes: bool = False,
) -> tuple[Any, Any, Any, CognitiveControlPlane, ControlledGridRuntimeV1, Any]:
    fabric, heartbeat, agency, runtime, fingerprint = build_unified_cognitive_runtime_v4(
        Path(unified_db),
        allow_regulator_writes=allow_regulator_writes,
    )
    # Reuse the exact control-plane object already attached to v4. One data plane, one catalog.
    control = runtime.control_plane
    controlled = ControlledGridRuntimeV1(runtime, control, Path(unified_db))
    return fabric, heartbeat, agency, control, controlled, fingerprint
