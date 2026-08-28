#!/usr/bin/env python3
"""GRID10 unified cognitive runtime v5: one latched control frame across Pulse + GRID/GWT.

v5 is a narrow successor to v4, not a competing state authority. It reuses v4's Agency
transaction and the same physical UnifiedDB, but fixes one important control-law ambiguity:
``gain == 0`` is *not* COMPUTE_OFF. Mode decides whether computation/output is permitted;
gain decides how strongly an otherwise permitted result may influence the action path.

When an explicit admitted ``inference_fn`` is supplied, the same immutable ControlSnapshot
is also passed into ``grid10_live_control_binding_v1`` so specialist execution and GWT fan-in
consume the exact same control epoch/digest as the persistent Pulse/Agency checkpoint.
There is deliberately no default provider call.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
import time

from frankenstein2_cognitive_control_plane_v1 import (
    CognitiveControlPlane,
    ControlMode,
    ControlSnapshot,
)
from grid10_cognitive_unified_runtime_v3 import build_unified_agency_runtime
from grid10_cognitive_unified_runtime_v4 import (
    ACTION_GRID_CELLS,
    CHECKPOINT_SCHEMA,
    RuntimeCycleNotDue,
    _atomic_commit_cycle,
    _init_cycle_schema,
)
from grid10_glm_cognitive_cycle_v1 import CognitiveCycleConfig
from grid10_glm_inference_provider_v1 import GLMInferenceResult
from grid10_live_control_binding_v1 import (
    ControlledCognitiveCycleResult,
    run_control_bound_cognitive_cycle,
    sanitized_control_receipt,
)
from grid10_persistent_agency_v1 import PersistentAgencyStore

SCHEMA = "GRID10_UNIFIED_COGNITIVE_RUNTIME/v5"


@dataclass(frozen=True)
class UnifiedCycleResultV5:
    tick_id: str
    heartbeat_result: Any
    woken_goal_ids: tuple[str, ...]
    agency_epoch_before: int
    agency_epoch_after: int
    assurance_mode: str
    raw_next_action: str
    next_action: str
    next_tick_not_before: float
    control_epoch: int
    control_snapshot_digest: str
    checkpoint: Mapping[str, Any]
    controlled_cognitive_cycle: ControlledCognitiveCycleResult | None


def _grid_control_view_v5(
    snapshot: ControlSnapshot,
    action: str,
) -> tuple[Mapping[str, Any], ...]:
    """Report mode and influence separately; gain never impersonates COMPUTE_OFF."""
    rows: list[Mapping[str, Any]] = []
    for cell in ACTION_GRID_CELLS.get(action, ()):
        mode = snapshot.mode(f"grid.{cell}.mode")
        gain = snapshot.float(f"grid.{cell}.gain")
        rows.append(
            {
                "cell": cell,
                "mode": mode.value,
                "gain": float(gain),
                "compute_enabled": mode != ControlMode.COMPUTE_OFF,
                "output_enabled": mode not in {
                    ControlMode.COMPUTE_OFF,
                    ControlMode.OUTPUT_OFF,
                },
                "normal_memory_reentry_enabled": mode == ControlMode.ON,
            }
        )
    return tuple(rows)


def _apply_grid_action_controls_v5(
    snapshot: ControlSnapshot,
    raw_action: str,
) -> tuple[str, tuple[str, ...], tuple[Mapping[str, Any], ...]]:
    cells = _grid_control_view_v5(snapshot, raw_action)
    if not cells or raw_action == "HOLD":
        return raw_action, (), cells

    reasons: list[str] = []
    mode_blocked = [
        str(row["cell"])
        for row in cells
        if not bool(row["compute_enabled"]) or not bool(row["output_enabled"])
    ]
    threshold = snapshot.float("pulse.salience_threshold")
    min_gain = min(float(row["gain"]) for row in cells)
    if mode_blocked:
        reasons.append("GRID_MODE_BLOCK:" + ",".join(mode_blocked))
    if min_gain < threshold:
        reasons.append(f"GRID_GAIN_BELOW_SALIENCE:{min_gain:.6f}<{threshold:.6f}")

    if not reasons:
        return raw_action, (), cells

    orientation = _grid_control_view_v5(snapshot, "OBSERVE")
    orientation_ok = bool(orientation) and all(
        bool(row["compute_enabled"])
        and bool(row["output_enabled"])
        and float(row["gain"]) >= threshold
        for row in orientation
    )
    fallback = "OBSERVE" if raw_action != "OBSERVE" and orientation_ok else "HOLD"
    return fallback, tuple(reasons), cells


class UnifiedCognitiveRuntimeV5:
    """One cycle boundary owns wake lineage, ControlSnapshot, heartbeat and GRID/GWT binding."""

    def __init__(
        self,
        heartbeat_runtime: Any,
        agency: PersistentAgencyStore,
        *,
        control_plane: CognitiveControlPlane | None = None,
        inference_fn: Callable[..., GLMInferenceResult] | None = None,
        cognitive_config: CognitiveCycleConfig = CognitiveCycleConfig(),
    ):
        self.heartbeat_runtime = heartbeat_runtime
        self.agency = agency
        self.control_plane = control_plane or CognitiveControlPlane(Path(agency.path))
        self.inference_fn = inference_fn
        self.cognitive_config = cognitive_config
        _init_cycle_schema(Path(agency.path))

    def tick_once(
        self,
        *,
        tick_id: str,
        interval: float | None = None,
        hold_interval: float | None = None,
        now_ts: float | None = None,
        observed_events: Iterable[str] = (),
        trusted_axes: Mapping[str, Any] | None = None,
        extra_variables: Mapping[str, Any] | None = None,
        cognitive_context: Mapping[str, Any] | None = None,
    ) -> UnifiedCycleResultV5:
        now = time.time() if now_ts is None else float(now_ts)

        # v4/f5 continuation law: this runtime is the sole wake_due owner.
        woken = self.agency.wake_due(
            now_ts=now,
            observed_events=tuple(observed_events),
            event_id_prefix=f"{tick_id}:wake",
        )
        before = self.agency.snapshot()
        if not woken and not self.agency.due_for_tick(now_ts=now):
            raise RuntimeCycleNotDue(f"NEXT_TICK_NOT_DUE:{before.next_tick_not_before}")

        # Exactly one control snapshot for the whole burst.
        control = self.control_plane.snapshot()

        heartbeat = self.heartbeat_runtime.tick_once(
            tick_id=tick_id,
            trusted_axes=trusted_axes,
            extra_variables=extra_variables,
        )
        assurance_mode = getattr(
            heartbeat.assurance_mode,
            "value",
            str(heartbeat.assurance_mode),
        )
        raw_next_action = str(heartbeat.next_action)
        next_action, control_reasons, grid_controls = _apply_grid_action_controls_v5(
            control,
            raw_next_action,
        )

        if raw_next_action == "HOLD":
            selected_interval = (
                float(hold_interval)
                if hold_interval is not None
                else control.float("pulse.hold_interval_seconds")
            )
        else:
            selected_interval = (
                float(interval)
                if interval is not None
                else control.float("pulse.active_interval_seconds")
            )
        next_tick_not_before = now + max(0.05, float(selected_interval))

        controlled: ControlledCognitiveCycleResult | None = None
        cognitive_receipt: Mapping[str, Any]
        if self.inference_fn is None:
            cognitive_receipt = {
                "schema": "GRID10_CONTROL_BOUND_COGNITIVE_CYCLE_NOT_RUN/v1",
                "reason": "NO_EXPLICIT_ADMITTED_INFERENCE_FN",
                "control_epoch": int(control.control_epoch),
                "control_snapshot_digest": control.snapshot_digest,
                "provider_calls": 0,
            }
        elif next_action == "HOLD":
            cognitive_receipt = {
                "schema": "GRID10_CONTROL_BOUND_COGNITIVE_CYCLE_NOT_RUN/v1",
                "reason": "DETERMINISTIC_HOLD",
                "control_epoch": int(control.control_epoch),
                "control_snapshot_digest": control.snapshot_digest,
                "provider_calls": 0,
            }
        else:
            context = dict(cognitive_context or {})
            context.setdefault("tick_id", tick_id)
            context.setdefault("woken_goal_ids", list(woken))
            context.setdefault("controller_action", next_action)
            controlled = run_control_bound_cognitive_cycle(
                tick_id=tick_id,
                assurance_mode=heartbeat.assurance_mode,
                controller_action=next_action,
                fabric=self.heartbeat_runtime.fabric,
                context=context,
                control_snapshot=control,
                config=self.cognitive_config,
                inference_fn=self.inference_fn,
            )
            cognitive_receipt = sanitized_control_receipt(controlled)

        checkpoint = {
            "schema": CHECKPOINT_SCHEMA,
            "runtime_schema": SCHEMA,
            "tick_id": tick_id,
            "source_state_epoch": int(heartbeat.state_epoch),
            "assurance_mode": assurance_mode,
            "raw_next_action": raw_next_action,
            "next_action": next_action,
            "woken_goal_ids": list(woken),
            "heartbeat_reasons": list(getattr(heartbeat, "reasons", ())),
            "control_snapshot": {
                "schema": control.schema,
                "control_epoch": int(control.control_epoch),
                "snapshot_digest": control.snapshot_digest,
            },
            "pulse_interval_seconds_consumed": float(selected_interval),
            "grid_controls_consumed": list(grid_controls),
            "control_reasons": list(control_reasons),
            "controlled_cognitive_cycle_receipt": cognitive_receipt,
            "external_effect_executed": False,
        }
        after_epoch = _atomic_commit_cycle(
            self.agency,
            expected_agency_epoch=before.state_epoch,
            tick_id=tick_id,
            source_state_epoch=int(heartbeat.state_epoch),
            assurance_mode=assurance_mode,
            next_action=next_action,
            woken_goal_ids=tuple(woken),
            checkpoint=checkpoint,
            next_tick_not_before=next_tick_not_before,
            now_ts=now,
        )
        return UnifiedCycleResultV5(
            tick_id=tick_id,
            heartbeat_result=heartbeat,
            woken_goal_ids=tuple(woken),
            agency_epoch_before=before.state_epoch,
            agency_epoch_after=after_epoch,
            assurance_mode=assurance_mode,
            raw_next_action=raw_next_action,
            next_action=next_action,
            next_tick_not_before=next_tick_not_before,
            control_epoch=int(control.control_epoch),
            control_snapshot_digest=control.snapshot_digest,
            checkpoint=checkpoint,
            controlled_cognitive_cycle=controlled,
        )


def build_unified_cognitive_runtime_v5(
    unified_db: Path,
    *,
    allow_regulator_writes: bool = False,
    inference_fn: Callable[..., GLMInferenceResult] | None = None,
    cognitive_config: CognitiveCycleConfig = CognitiveCycleConfig(),
):
    fabric, heartbeat_store, agency, heartbeat_runtime, fingerprint = build_unified_agency_runtime(
        unified_db,
        allow_regulator_writes=allow_regulator_writes,
    )
    control_plane = CognitiveControlPlane(Path(unified_db))
    runtime = UnifiedCognitiveRuntimeV5(
        heartbeat_runtime,
        agency,
        control_plane=control_plane,
        inference_fn=inference_fn,
        cognitive_config=cognitive_config,
    )
    return fabric, heartbeat_store, agency, runtime, fingerprint
