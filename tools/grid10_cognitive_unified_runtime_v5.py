#!/usr/bin/env python3
"""GRID10 unified cognitive runtime v5: one control basis across Pulse + GRID/GWT.

v5 is a thin successor integration layer, not a second state/wake authority. V4 remains the
sole owner of wake_due, heartbeat, Agency checkpoint and pulse scheduling. V5 latches one
immutable ControlSnapshot, passes that exact object into v4, and then passes the same object
into ``grid10_live_control_binding_v2`` for specialist compute/GWT/memory semantics.

GRID mode semantics have one home: the live control binding. Gain influences specialist
compute budget; ``grid.workspace_ignition_threshold`` mechanically controls which visible
specialist outputs can ignite/broadcast through GWT. It does not masquerade as COMPUTE_OFF
in the pulse controller.

There is no default provider call. An explicit admitted inference_fn is required to run the
GRID/GWT burst. The v5 augmented receipt is noncanonical and does not grant effect/completion
or whole-runtime credit.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
import hashlib
import json
import sqlite3
import time

from frankenstein2_cognitive_control_plane_v1 import CognitiveControlPlane, ControlSnapshot
from grid10_cognitive_unified_runtime_v4 import (
    UnifiedCognitiveRuntimeV4,
    build_unified_cognitive_runtime_v4,
)
from grid10_glm_cognitive_cycle_v1 import CognitiveCycleConfig
from grid10_glm_inference_provider_v1 import GLMInferenceResult
from grid10_live_control_binding_v2 import (
    ControlledCognitiveCycleResultV2,
    run_control_bound_cognitive_cycle_v2,
    sanitized_control_receipt_v2,
)

SCHEMA = "GRID10_UNIFIED_COGNITIVE_RUNTIME/v5"
RECEIPT_SCHEMA = "GRID10_V5_CONTROL_BOUND_RECEIPT/v1"


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
    controlled_cognitive_cycle: ControlledCognitiveCycleResultV2 | None
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


def _init_v5_schema(path: Path) -> None:
    con = _connect(path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS grid10_v5_control_bound_receipts(
              tick_id TEXT PRIMARY KEY,
              receipt_schema TEXT NOT NULL,
              agency_epoch_after INTEGER NOT NULL,
              control_epoch INTEGER NOT NULL,
              control_snapshot_digest TEXT NOT NULL,
              receipt_json TEXT NOT NULL,
              receipt_digest TEXT NOT NULL,
              created_ts REAL NOT NULL
            )
            """
        )
    finally:
        con.close()


class UnifiedCognitiveRuntimeV5:
    """Reuse v4's state transition and bind the same snapshot into live GRID/GWT compute."""

    def __init__(
        self,
        runtime_v4: UnifiedCognitiveRuntimeV4,
        *,
        control_plane: CognitiveControlPlane | None = None,
        inference_fn: Callable[..., GLMInferenceResult] | None = None,
        cognitive_config: CognitiveCycleConfig = CognitiveCycleConfig(),
    ):
        self.runtime_v4 = runtime_v4
        self.agency = runtime_v4.agency
        self.control_plane = control_plane or runtime_v4.control_plane
        self.inference_fn = inference_fn
        self.cognitive_config = cognitive_config
        self.unified_db = Path(self.agency.path)
        _init_v5_schema(self.unified_db)

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
        # One current-cycle basis. V4 is explicitly told to reuse it and therefore performs no
        # second control-plane snapshot read for pulse scheduling.
        control: ControlSnapshot = self.control_plane.snapshot()
        base = self.runtime_v4.tick_once(
            tick_id=tick_id,
            interval=interval,
            hold_interval=hold_interval,
            now_ts=now_ts,
            observed_events=tuple(observed_events),
            control_snapshot=control,
            trusted_axes=trusted_axes,
            extra_variables=extra_variables,
        )
        raw_next_action = str(base.heartbeat_result.next_action)
        next_action = str(base.next_action)

        controlled: ControlledCognitiveCycleResultV2 | None = None
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
            context.setdefault("woken_goal_ids", list(base.woken_goal_ids))
            context.setdefault("controller_action", next_action)
            controlled = run_control_bound_cognitive_cycle_v2(
                tick_id=tick_id,
                assurance_mode=base.heartbeat_result.assurance_mode,
                controller_action=next_action,
                fabric=self.runtime_v4.heartbeat_runtime.fabric,
                context=context,
                control_snapshot=control,
                config=self.cognitive_config,
                inference_fn=self.inference_fn,
            )
            cognitive_receipt = sanitized_control_receipt_v2(controlled)

        # V4's durable Agency checkpoint already committed the wake/pulse state transition.
        # This is an append-only causal binding receipt, not a second canonical checkpoint.
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "runtime_schema": SCHEMA,
            "tick_id": tick_id,
            "agency_epoch_before": base.agency_epoch_before,
            "agency_epoch_after": base.agency_epoch_after,
            "assurance_mode": base.assurance_mode,
            "raw_next_action": raw_next_action,
            "next_action": next_action,
            "woken_goal_ids": list(base.woken_goal_ids),
            "next_tick_not_before": base.next_tick_not_before,
            "control_epoch": int(control.control_epoch),
            "control_snapshot_digest": control.snapshot_digest,
            "v4_checkpoint_control_snapshot": dict(base.checkpoint["control_snapshot"]),
            "v4_control_snapshot_source": base.checkpoint.get("control_snapshot_source"),
            "controlled_cognitive_cycle_receipt": cognitive_receipt,
            "canonical_truth_minted": False,
            "external_effect_executed": False,
            "completion_minted": False,
        }
        receipt_digest = _digest(receipt)
        receipt["receipt_digest"] = receipt_digest

        con = _connect(self.unified_db)
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "INSERT INTO grid10_v5_control_bound_receipts VALUES(?,?,?,?,?,?,?,?)",
                (
                    tick_id,
                    RECEIPT_SCHEMA,
                    int(base.agency_epoch_after),
                    int(control.control_epoch),
                    control.snapshot_digest,
                    _canon(receipt),
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

        return UnifiedCycleResultV5(
            tick_id=tick_id,
            heartbeat_result=base.heartbeat_result,
            woken_goal_ids=base.woken_goal_ids,
            agency_epoch_before=base.agency_epoch_before,
            agency_epoch_after=base.agency_epoch_after,
            assurance_mode=base.assurance_mode,
            raw_next_action=raw_next_action,
            next_action=next_action,
            next_tick_not_before=base.next_tick_not_before,
            control_epoch=int(control.control_epoch),
            control_snapshot_digest=control.snapshot_digest,
            checkpoint=receipt,
            controlled_cognitive_cycle=controlled,
            receipt_digest=receipt_digest,
        )


def build_unified_cognitive_runtime_v5(
    unified_db: Path,
    *,
    allow_regulator_writes: bool = False,
    inference_fn: Callable[..., GLMInferenceResult] | None = None,
    cognitive_config: CognitiveCycleConfig = CognitiveCycleConfig(),
):
    fabric, heartbeat_store, agency, runtime_v4, fingerprint = build_unified_cognitive_runtime_v4(
        Path(unified_db),
        allow_regulator_writes=allow_regulator_writes,
    )
    runtime = UnifiedCognitiveRuntimeV5(
        runtime_v4,
        control_plane=runtime_v4.control_plane,
        inference_fn=inference_fn,
        cognitive_config=cognitive_config,
    )
    return fabric, heartbeat_store, agency, runtime, fingerprint
