#!/usr/bin/env python3
"""GRID10 unified cognitive runtime v6: one latched control basis through Pulse + GWT ignition.

v6 is a narrow successor to v5. V4 remains the sole owner of wake_due, heartbeat,
Agency checkpoint and pulse scheduling. V6 latches one immutable ControlSnapshot,
passes that exact object into V4, then passes the same object into
``grid10_live_control_binding_v2``.

The v2 binding makes ``grid.workspace_ignition_threshold`` a real runtime control:
specialists may execute while their outputs remain below the GWT ignition threshold;
in that case no workspace inference call is made. COMPUTE_OFF / OUTPUT_OFF /
MEMORY_OFF remain mechanically distinct and gain remains a compute-budget control.

There is no default provider call. An explicit admitted inference_fn is required to run
specialist/GWT cognition. Receipts are candidate-cognition evidence only and cannot mint
canonical truth, effects or completion.

V4 commits the durable Agency transition before the optional cognitive fan-out. V6 now
persists a create-once PREPARED crash-reconciliation intent before entering V4 and closes
that intent in the same SQLite transaction as the V6 cognition receipt. If the process dies
after V4 commit but before the V6 receipt transaction, the surviving PREPARED intent plus
V4 cycle row is machine-classifiable as RECOVERY_REQUIRED_POST_V4_COMMIT with unknown
provider-call state and no same-tick retry authorization. This is recovery observability,
not a claim of full two-phase atomicity.
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
from grid10_v6_crash_reconciliation_v1 import (
    install_reconciliation_schema,
    mark_intent_closed_in_transaction,
    prepare_cycle_intent,
)

SCHEMA = "GRID10_UNIFIED_COGNITIVE_RUNTIME/v6"
RECEIPT_SCHEMA = "GRID10_V6_CONTROL_BOUND_RECEIPT/v1"
FAILED_COGNITIVE_RECEIPT_SCHEMA = "GRID10_CONTROL_BOUND_COGNITIVE_CYCLE_FAILED/v1"


class CognitiveCycleExecutionError(RuntimeError):
    """Cognition failed after V4 committed the durable Agency transition."""


@dataclass(frozen=True)
class UnifiedCycleResultV6:
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


def _init_v6_schema(path: Path) -> None:
    con = _connect(path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS grid10_v6_control_bound_receipts(
              tick_id TEXT PRIMARY KEY,
              receipt_schema TEXT NOT NULL,
              agency_epoch_after INTEGER NOT NULL,
              control_epoch INTEGER NOT NULL,
              control_snapshot_digest TEXT NOT NULL,
              workspace_ignited INTEGER NOT NULL,
              workspace_ignition_threshold REAL NOT NULL,
              receipt_json TEXT NOT NULL,
              receipt_digest TEXT NOT NULL,
              created_ts REAL NOT NULL
            )
            """
        )
    finally:
        con.close()


class UnifiedCognitiveRuntimeV6:
    """Reuse V4 state transition and bind the same snapshot into V2 GWT-gated cognition."""

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
        _init_v6_schema(self.unified_db)
        install_reconciliation_schema(self.unified_db)

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
    ) -> UnifiedCycleResultV6:
        # Single immutable current-cycle basis. V4 is explicitly supplied this exact snapshot,
        # so pulse scheduling and later specialist/GWT gating cannot read divergent revisions.
        control: ControlSnapshot = self.control_plane.snapshot()
        prepared_agency_epoch = int(self.agency.snapshot().state_epoch)
        prepare_cycle_intent(
            self.unified_db,
            tick_id=tick_id,
            agency_epoch_at_prepare=prepared_agency_epoch,
            control_epoch=int(control.control_epoch),
            control_snapshot_digest=control.snapshot_digest,
        )
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
        cognitive_error: Exception | None = None
        cognitive_cycle_status = "NOT_RUN"
        reserved_context_overrides: tuple[str, ...] = ()
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
            causal_context = {
                "tick_id": tick_id,
                "woken_goal_ids": list(base.woken_goal_ids),
                "controller_action": next_action,
            }
            # Caller context is candidate data, not causal identity authority. Record any
            # attempted collision, then deterministically bind the reserved fields to the
            # already-committed V4 cycle so GWT prompts cannot drift onto a foreign tick/action.
            reserved_context_overrides = tuple(
                sorted(
                    key
                    for key, value in causal_context.items()
                    if key in context and context[key] != value
                )
            )
            context.update(causal_context)
            try:
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
                cognitive_cycle_status = "SUCCESS"
            except Exception as exc:
                # V4 has already committed the Agency transition. Never leave that durable
                # transition without an exact v6 closure simply because candidate cognition
                # failed. Persist only bounded error metadata; arbitrary exception text may
                # contain provider/runtime data and is therefore represented by a digest.
                cognitive_error = exc
                cognitive_cycle_status = "FAILED"
                cognitive_receipt = {
                    "schema": FAILED_COGNITIVE_RECEIPT_SCHEMA,
                    "reason": "INFERENCE_OR_GWT_EXCEPTION_AFTER_V4_COMMIT",
                    "error_type": type(exc).__name__,
                    "error_digest": _digest({
                        "error_type": type(exc).__name__,
                        "error_text": str(exc),
                    }),
                    "control_epoch": int(control.control_epoch),
                    "control_snapshot_digest": control.snapshot_digest,
                    "agency_epoch_after": int(base.agency_epoch_after),
                    "provider_calls": None,
                    "provider_calls_status": "UNKNOWN_AFTER_EXCEPTION",
                    "retry_same_tick_authorized": False,
                }

        # V4 already committed the durable Agency/wake transition. This row is an append-only
        # causal control/cognition receipt; it is deliberately not a second Agency authority.
        workspace_ignited = bool(controlled.workspace_ignited) if controlled is not None else False
        ignition_threshold = (
            float(controlled.workspace_ignition_threshold)
            if controlled is not None
            else float(control.float("grid.workspace_ignition_threshold"))
        )
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "runtime_schema": SCHEMA,
            "tick_id": tick_id,
            "agency_epoch_before": base.agency_epoch_before,
            "agency_epoch_after": base.agency_epoch_after,
            "agency_epoch_at_prepare": prepared_agency_epoch,
            "assurance_mode": base.assurance_mode,
            "raw_next_action": raw_next_action,
            "next_action": next_action,
            "woken_goal_ids": list(base.woken_goal_ids),
            "next_tick_not_before": base.next_tick_not_before,
            "control_epoch": int(control.control_epoch),
            "control_snapshot_digest": control.snapshot_digest,
            "v4_checkpoint_control_snapshot": dict(base.checkpoint["control_snapshot"]),
            "v4_control_snapshot_source": base.checkpoint.get("control_snapshot_source"),
            "workspace_ignition_threshold": ignition_threshold,
            "workspace_ignited": workspace_ignited,
            "cognitive_cycle_status": cognitive_cycle_status,
            "post_v4_commit_failure": cognitive_error is not None,
            "same_tick_retry_authorized": False if cognitive_error is not None else None,
            "crash_reconciliation_intent_prepared": True,
            "reserved_cognitive_context_overrides": list(reserved_context_overrides),
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
                "INSERT INTO grid10_v6_control_bound_receipts VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    tick_id,
                    RECEIPT_SCHEMA,
                    int(base.agency_epoch_after),
                    int(control.control_epoch),
                    control.snapshot_digest,
                    1 if workspace_ignited else 0,
                    ignition_threshold,
                    _canon(receipt),
                    receipt_digest,
                    time.time(),
                ),
            )
            mark_intent_closed_in_transaction(
                con,
                tick_id=tick_id,
                closure_receipt_digest=receipt_digest,
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

        if cognitive_error is not None:
            raise CognitiveCycleExecutionError(
                f"COGNITIVE_CYCLE_FAILED_AFTER_V4_COMMIT:{tick_id}:{receipt_digest}"
            ) from cognitive_error

        return UnifiedCycleResultV6(
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


def build_unified_cognitive_runtime_v6(
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
    runtime = UnifiedCognitiveRuntimeV6(
        runtime_v4,
        control_plane=runtime_v4.control_plane,
        inference_fn=inference_fn,
        cognitive_config=cognitive_config,
    )
    return fabric, heartbeat_store, agency, runtime, fingerprint


__all__ = [
    "CognitiveCycleExecutionError",
    "UnifiedCycleResultV6",
    "UnifiedCognitiveRuntimeV6",
    "build_unified_cognitive_runtime_v6",
]
