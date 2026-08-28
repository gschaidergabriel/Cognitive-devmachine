#!/usr/bin/env python3
"""Persistent GRID10 scheduler v2: autonomous cadence through unified runtime v6.

This is a service wrapper, not a second state or wake authority. It reuses the proven
scheduler-v1 preflight/idle semantics, but active or due-wake cognition enters
``grid10_cognitive_unified_runtime_v6`` so the same per-tick ControlSnapshot now governs:

    Agency/wake/pulse -> specialist compute -> GWT ignition -> receipt -> next tick.

V4 remains the sole wake/Agency transition owner inside V6. The scheduler only decides
whether there is active work or a due wake worth entering that controller. No provider is
implicit: without an explicitly supplied admitted ``inference_fn`` V6 records zero model
calls and the scheduler still advances the durable heartbeat/checkpoint path.
"""
from __future__ import annotations

from dataclasses import asdict
import argparse
import json
from pathlib import Path
import time
from typing import Callable, Iterable, Mapping, Any

from grid10_cognitive_heartbeat_v1 import _trusted_normal_axes, append_frame_jsonl
from grid10_cognitive_unified_runtime_v4 import RuntimeCycleNotDue, _atomic_commit_idle_hold
from grid10_cognitive_unified_runtime_v6 import build_unified_cognitive_runtime_v6
from grid10_glm_cognitive_cycle_v1 import CognitiveCycleConfig
from grid10_glm_inference_provider_v1 import GLMInferenceResult
from grid10_persistent_agency_v1 import GoalState
from grid10_persistent_scheduler_v1 import (
    SchedulerConfig,
    SchedulerCycleResult,
    _pending_wake_due,
)

SCHEMA = "GRID10_PERSISTENT_SCHEDULER/v2"


class PersistentCognitiveSchedulerV2:
    """Keep the V6 Agency + GRID/GWT controller alive without a new user prompt."""

    def __init__(
        self,
        unified_db: Path,
        frames_jsonl: Path,
        *,
        config: SchedulerConfig = SchedulerConfig(),
        inference_fn: Callable[..., GLMInferenceResult] | None = None,
        cognitive_config: CognitiveCycleConfig = CognitiveCycleConfig(),
    ):
        self.unified_db = Path(unified_db)
        self.frames_jsonl = Path(frames_jsonl)
        self.config = config
        self.inference_fn = inference_fn
        self.cognitive_config = cognitive_config
        (
            self.fabric,
            self.heartbeat_store,
            self.agency,
            self.runtime,
            self.fingerprint,
        ) = build_unified_cognitive_runtime_v6(
            self.unified_db,
            allow_regulator_writes=config.allow_regulator_writes,
            inference_fn=inference_fn,
            cognitive_config=cognitive_config,
        )

    def _active_goal_ids(self) -> tuple[str, ...]:
        snap = self.agency.snapshot()
        return tuple(
            g.goal_id
            for g in snap.goals
            if g.state in {GoalState.ACTIVE, GoalState.TRIAL}
        )

    def _not_due_result(
        self,
        *,
        cycle_id: str,
        snapshot: Any,
        active_goal_ids: tuple[str, ...],
    ) -> SchedulerCycleResult:
        return SchedulerCycleResult(
            cycle_id=cycle_id,
            status="NOT_DUE",
            awakened_goal_ids=(),
            active_goal_ids=active_goal_ids,
            heartbeat_tick_id=None,
            assurance_mode=None,
            cognitive_action=None,
            next_tick_not_before=snapshot.next_tick_not_before,
            agency_state_epoch=snapshot.state_epoch,
            unified_db_realpath=self.fingerprint.realpath,
        )

    def cycle_once(
        self,
        *,
        cycle_id: str,
        now_ts: float | None = None,
        observed_events: Iterable[str] = (),
        cognitive_context: Mapping[str, Any] | None = None,
    ) -> SchedulerCycleResult:
        now = time.time() if now_ts is None else float(now_ts)
        observed_events = tuple(str(x) for x in observed_events)
        before = self.agency.snapshot()
        active_goal_ids = tuple(
            g.goal_id
            for g in before.goals
            if g.state in {GoalState.ACTIVE, GoalState.TRIAL}
        )
        wake_expected = _pending_wake_due(
            before,
            now_ts=now,
            observed_events=observed_events,
        )

        # Keep scheduler-v1's fail-closed idle semantics. The service wrapper never performs
        # wake_due and never manufactures wake provenance.
        if not active_goal_ids and not wake_expected:
            if not self.agency.due_for_tick(now_ts=now):
                return self._not_due_result(
                    cycle_id=cycle_id,
                    snapshot=before,
                    active_goal_ids=active_goal_ids,
                )
            if self.config.idle_poll_seconds is None:
                control = self.runtime.control_plane.snapshot()
                idle_interval = control.float("pulse.idle_interval_seconds")
            else:
                idle_interval = float(self.config.idle_poll_seconds)
            next_due = now + max(0.05, float(idle_interval))
            after_epoch, _checkpoint = _atomic_commit_idle_hold(
                self.agency,
                expected_agency_epoch=before.state_epoch,
                cycle_id=cycle_id,
                awakened_goal_ids=(),
                next_tick_not_before=next_due,
                now_ts=now,
            )
            return SchedulerCycleResult(
                cycle_id=cycle_id,
                status="HOLD_NO_ACTIVE_GOAL",
                awakened_goal_ids=(),
                active_goal_ids=(),
                heartbeat_tick_id=None,
                assurance_mode=None,
                cognitive_action="HOLD",
                next_tick_not_before=next_due,
                agency_state_epoch=after_epoch,
                unified_db_realpath=self.fingerprint.realpath,
            )

        trusted = _trusted_normal_axes() if self.config.trusted_normal_test_fixture else None
        tick_id = f"{cycle_id}:heartbeat"
        try:
            cycle = self.runtime.tick_once(
                tick_id=tick_id,
                interval=self.config.active_interval_seconds,
                hold_interval=self.config.hold_poll_seconds,
                now_ts=now,
                observed_events=observed_events,
                trusted_axes=trusted,
                cognitive_context=cognitive_context,
            )
        except RuntimeCycleNotDue:
            current = self.agency.snapshot()
            return self._not_due_result(
                cycle_id=cycle_id,
                snapshot=current,
                active_goal_ids=self._active_goal_ids(),
            )

        append_frame_jsonl(self.frames_jsonl, cycle.heartbeat_result.frame_json)
        active_after = self._active_goal_ids()
        return SchedulerCycleResult(
            cycle_id=cycle_id,
            status="HEARTBEAT_RAN",
            awakened_goal_ids=cycle.woken_goal_ids,
            active_goal_ids=active_after,
            heartbeat_tick_id=tick_id,
            assurance_mode=cycle.assurance_mode,
            cognitive_action=cycle.next_action,
            next_tick_not_before=cycle.next_tick_not_before,
            agency_state_epoch=cycle.agency_epoch_after,
            unified_db_realpath=self.fingerprint.realpath,
        )

    def run_forever(self) -> None:
        """Run autonomous next ticks until externally stopped; execute no effects here."""
        while True:
            now = time.time()
            snap = self.agency.snapshot()
            if snap.next_tick_not_before is not None and now < snap.next_tick_not_before:
                time.sleep(min(1.0, max(0.05, snap.next_tick_not_before - now)))
                continue
            cycle_id = f"scheduler-v2-{time.time_ns()}"
            row = self.cycle_once(cycle_id=cycle_id, now_ts=now)
            print(json.dumps(asdict(row), sort_keys=True), flush=True)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--unified-db", required=True)
    p.add_argument("--frames-jsonl", required=True)
    p.add_argument("--cycles", type=int, default=1)
    p.add_argument("--forever", action="store_true")
    p.add_argument("--active-interval", type=float, default=None)
    p.add_argument("--hold-poll", type=float, default=None)
    p.add_argument("--idle-poll", type=float, default=None)
    p.add_argument("--allow-regulator-writes", action="store_true")
    p.add_argument("--trusted-normal-test-fixture", action="store_true")
    p.add_argument("--event", action="append", default=[])
    args = p.parse_args()

    # CLI intentionally exposes no provider selection. A finished service adapter must inject
    # an already-admitted inference_fn explicitly; plain CLI operation therefore performs zero
    # model-network calls while exercising persistent Agency/heartbeat scheduling.
    scheduler = PersistentCognitiveSchedulerV2(
        Path(args.unified_db),
        Path(args.frames_jsonl),
        config=SchedulerConfig(
            active_interval_seconds=args.active_interval,
            hold_poll_seconds=args.hold_poll,
            idle_poll_seconds=args.idle_poll,
            allow_regulator_writes=bool(args.allow_regulator_writes),
            trusted_normal_test_fixture=bool(args.trusted_normal_test_fixture),
        ),
    )
    if args.forever:
        scheduler.run_forever()
        return 0

    for i in range(max(0, int(args.cycles))):
        now = time.time()
        row = scheduler.cycle_once(
            cycle_id=f"bounded-scheduler-v2-{time.time_ns()}-{i}",
            now_ts=now,
            observed_events=args.event if i == 0 else (),
        )
        print(json.dumps(asdict(row), sort_keys=True))
        if i + 1 < args.cycles:
            snap = scheduler.agency.snapshot()
            if snap.next_tick_not_before is not None:
                time.sleep(max(0.05, snap.next_tick_not_before - time.time()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "SCHEMA",
    "PersistentCognitiveSchedulerV2",
    "SchedulerConfig",
    "SchedulerCycleResult",
]
