#!/usr/bin/env python3
"""Persistent GRID10 scheduler over the single UnifiedDB cognitive runtime.

This is a control-loop adapter, not a second cognition/state authority. It uses the same
physical SQLite opened by ``grid10_cognitive_unified_runtime_v2`` and turns durable
AgencyState/DeferredIntent state into repeatable heartbeat scheduling. It never executes
external effects and it does not treat model/GRID output as verified world state.

The key Stage-2 behavior is explicit and falsifiable:

    checkpoint -> HOLD/DORMANT -> process restart -> exact wake condition
    -> ACTIVE -> cognitive heartbeat -> checkpoint -> durable next-tick schedule

A wake event may make cognition immediately due even when an idle poll was scheduled later.
This prevents HOLD from degenerating into busy-waiting while still allowing material new
evidence to resume the goal promptly.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import json
from pathlib import Path
import time
from typing import Iterable

from grid10_cognitive_heartbeat_v1 import _trusted_normal_axes, append_frame_jsonl
from grid10_cognitive_unified_runtime_v2 import build_shared_runtime
from grid10_persistent_agency_v1 import GoalState


@dataclass(frozen=True)
class SchedulerConfig:
    active_interval_seconds: float = 1.0
    hold_poll_seconds: float = 15.0
    idle_poll_seconds: float = 30.0
    allow_regulator_writes: bool = False
    trusted_normal_test_fixture: bool = False


@dataclass(frozen=True)
class SchedulerCycleResult:
    cycle_id: str
    status: str
    awakened_goal_ids: tuple[str, ...]
    active_goal_ids: tuple[str, ...]
    heartbeat_tick_id: str | None
    assurance_mode: str | None
    cognitive_action: str | None
    next_tick_not_before: float | None
    agency_state_epoch: int
    unified_db_realpath: str


class PersistentCognitiveScheduler:
    """Drive durable AgencyState into the existing GRID10 heartbeat without a user prompt."""

    def __init__(
        self,
        unified_db: Path,
        frames_jsonl: Path,
        *,
        config: SchedulerConfig = SchedulerConfig(),
    ):
        self.unified_db = Path(unified_db)
        self.frames_jsonl = Path(frames_jsonl)
        self.config = config
        (
            self.fabric,
            self.heartbeat_store,
            self.agency,
            self.runtime,
            self.fingerprint,
        ) = build_shared_runtime(
            self.unified_db,
            allow_regulator_writes=config.allow_regulator_writes,
        )

    def _active_goal_ids(self) -> tuple[str, ...]:
        snap = self.agency.snapshot()
        return tuple(
            g.goal_id
            for g in snap.goals
            if g.state in {GoalState.ACTIVE, GoalState.TRIAL}
        )

    def cycle_once(
        self,
        *,
        cycle_id: str,
        now_ts: float | None = None,
        observed_events: Iterable[str] = (),
    ) -> SchedulerCycleResult:
        now = time.time() if now_ts is None else float(now_ts)

        # Deferred-intent evaluation happens before due-time evaluation. Material evidence is
        # allowed to wake a goal immediately rather than waiting for a later idle poll.
        awakened = self.agency.wake_due(
            now_ts=now,
            observed_events=tuple(observed_events),
            event_id_prefix=f"{cycle_id}:wake",
        )
        active_goal_ids = self._active_goal_ids()

        if not awakened and not self.agency.due_for_tick(now_ts=now):
            snap = self.agency.snapshot()
            return SchedulerCycleResult(
                cycle_id=cycle_id,
                status="NOT_DUE",
                awakened_goal_ids=awakened,
                active_goal_ids=active_goal_ids,
                heartbeat_tick_id=None,
                assurance_mode=None,
                cognitive_action=None,
                next_tick_not_before=snap.next_tick_not_before,
                agency_state_epoch=snap.state_epoch,
                unified_db_realpath=self.fingerprint.realpath,
            )

        if not active_goal_ids:
            next_due = now + max(0.05, float(self.config.idle_poll_seconds))
            self.agency.schedule_next_tick(
                not_before=next_due,
                mode="HOLD",
                event_id=f"{cycle_id}:idle-schedule",
                now_ts=now,
            )
            self.agency.set_continuation_checkpoint(
                {
                    "cycle_id": cycle_id,
                    "mode": "HOLD",
                    "reason": "NO_ACTIVE_OR_TRIAL_GOAL",
                    "next_tick_not_before": next_due,
                },
                event_id=f"{cycle_id}:idle-checkpoint",
                now_ts=now,
            )
            snap = self.agency.snapshot()
            return SchedulerCycleResult(
                cycle_id=cycle_id,
                status="HOLD_NO_ACTIVE_GOAL",
                awakened_goal_ids=awakened,
                active_goal_ids=(),
                heartbeat_tick_id=None,
                assurance_mode=None,
                cognitive_action="HOLD",
                next_tick_not_before=next_due,
                agency_state_epoch=snap.state_epoch,
                unified_db_realpath=self.fingerprint.realpath,
            )

        trusted = _trusted_normal_axes() if self.config.trusted_normal_test_fixture else None
        tick_id = f"{cycle_id}:heartbeat"
        result = self.runtime.tick_once(tick_id=tick_id, trusted_axes=trusted)
        append_frame_jsonl(self.frames_jsonl, result.frame_json)

        interval = (
            self.config.hold_poll_seconds
            if result.next_action == "HOLD"
            else self.config.active_interval_seconds
        )
        next_due = now + max(0.05, float(interval))
        self.agency.set_continuation_checkpoint(
            {
                "cycle_id": cycle_id,
                "heartbeat_tick_id": tick_id,
                "active_goal_ids": list(active_goal_ids),
                "awakened_goal_ids": list(awakened),
                "assurance_mode": result.assurance_mode.value,
                "cognitive_action": result.next_action,
                "next_tick_not_before": next_due,
                "external_effect_executed": False,
            },
            event_id=f"{cycle_id}:checkpoint",
            now_ts=now,
        )
        self.agency.schedule_next_tick(
            not_before=next_due,
            mode=result.assurance_mode.value,
            event_id=f"{cycle_id}:next-tick",
            now_ts=now,
        )
        snap = self.agency.snapshot()
        return SchedulerCycleResult(
            cycle_id=cycle_id,
            status="HEARTBEAT_RAN",
            awakened_goal_ids=awakened,
            active_goal_ids=active_goal_ids,
            heartbeat_tick_id=tick_id,
            assurance_mode=result.assurance_mode.value,
            cognitive_action=result.next_action,
            next_tick_not_before=next_due,
            agency_state_epoch=snap.state_epoch,
            unified_db_realpath=self.fingerprint.realpath,
        )

    def run_forever(self) -> None:
        """Run autonomous next ticks until the process is externally stopped.

        This method intentionally performs no effect execution. It only keeps the cognition
        controller alive and durable. A service manager may restart the process; all scheduling
        and goal continuation state is re-opened from the same UnifiedDB.
        """
        while True:
            now = time.time()
            snap = self.agency.snapshot()
            if snap.next_tick_not_before is not None and now < snap.next_tick_not_before:
                time.sleep(min(1.0, max(0.05, snap.next_tick_not_before - now)))
                continue
            cycle_id = f"scheduler-{time.time_ns()}"
            row = self.cycle_once(cycle_id=cycle_id, now_ts=now)
            print(json.dumps(asdict(row), sort_keys=True), flush=True)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--unified-db", required=True)
    p.add_argument("--frames-jsonl", required=True)
    p.add_argument("--cycles", type=int, default=1)
    p.add_argument("--forever", action="store_true")
    p.add_argument("--active-interval", type=float, default=1.0)
    p.add_argument("--hold-poll", type=float, default=15.0)
    p.add_argument("--idle-poll", type=float, default=30.0)
    p.add_argument("--allow-regulator-writes", action="store_true")
    p.add_argument("--trusted-normal-test-fixture", action="store_true")
    p.add_argument("--event", action="append", default=[])
    args = p.parse_args()

    scheduler = PersistentCognitiveScheduler(
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

    rows = []
    for i in range(max(0, int(args.cycles))):
        now = time.time()
        row = scheduler.cycle_once(
            cycle_id=f"bounded-scheduler-{time.time_ns()}-{i}",
            now_ts=now,
            observed_events=args.event if i == 0 else (),
        )
        rows.append(asdict(row))
        print(json.dumps(rows[-1], sort_keys=True))
        if i + 1 < args.cycles:
            snap = scheduler.agency.snapshot()
            if snap.next_tick_not_before is not None:
                time.sleep(max(0.05, snap.next_tick_not_before - time.time()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
