#!/usr/bin/env python3
"""Persistent GRID10 scheduler over the single UnifiedDB cognitive runtime.

This is a control-loop service wrapper, not a second cognition/state authority. It uses the
same physical SQLite opened by ``grid10_cognitive_unified_runtime_v4`` and delegates every
heartbeat/checkpoint/next-tick state transition to that v4 core. Idle/HOLD scheduling uses the
same v4 CAS helper so the service wrapper no longer owns a second write sequence.

The live Dynamic Frame is the default cadence authority: active and HOLD ticks are resolved
inside v4 from its single per-tick ControlSnapshot; an idle cycle latches one snapshot solely
to resolve ``pulse.idle_interval_seconds``. Explicit config/CLI interval values remain bounded
compatibility/test overrides and do not create a second durable control authority.

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
from grid10_cognitive_unified_runtime_v4 import (
    _atomic_commit_idle_hold,
    build_unified_cognitive_runtime_v4,
)
from grid10_persistent_agency_v1 import GoalState


@dataclass(frozen=True)
class SchedulerConfig:
    active_interval_seconds: float | None = None
    hold_poll_seconds: float | None = None
    idle_poll_seconds: float | None = None
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
    """Keep the v4 durable AgencyState/heartbeat controller alive without a user prompt."""

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
        ) = build_unified_cognitive_runtime_v4(
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

        # Evaluate deferred intents exactly once. If a material event wakes a goal, pass those
        # exact IDs into v4 so the core receipt preserves the wake lineage without re-firing it.
        awakened = self.agency.wake_due(
            now_ts=now,
            observed_events=tuple(observed_events),
            event_id_prefix=f"{cycle_id}:wake",
        )
        before = self.agency.snapshot()
        active_goal_ids = self._active_goal_ids()

        if not awakened and not self.agency.due_for_tick(now_ts=now):
            return SchedulerCycleResult(
                cycle_id=cycle_id,
                status="NOT_DUE",
                awakened_goal_ids=awakened,
                active_goal_ids=active_goal_ids,
                heartbeat_tick_id=None,
                assurance_mode=None,
                cognitive_action=None,
                next_tick_not_before=before.next_tick_not_before,
                agency_state_epoch=before.state_epoch,
                unified_db_realpath=self.fingerprint.realpath,
            )

        if not active_goal_ids:
            # No cognitive heartbeat runs here, so this idle scheduler boundary may latch its
            # own immutable snapshot without violating the one-snapshot-per-cognitive-tick law.
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
                awakened_goal_ids=tuple(awakened),
                next_tick_not_before=next_due,
                now_ts=now,
            )
            return SchedulerCycleResult(
                cycle_id=cycle_id,
                status="HOLD_NO_ACTIVE_GOAL",
                awakened_goal_ids=awakened,
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
        cycle = self.runtime.tick_once(
            tick_id=tick_id,
            interval=self.config.active_interval_seconds,
            hold_interval=self.config.hold_poll_seconds,
            now_ts=now,
            prewoken_goal_ids=tuple(awakened),
            trusted_axes=trusted,
        )
        append_frame_jsonl(self.frames_jsonl, cycle.heartbeat_result.frame_json)

        return SchedulerCycleResult(
            cycle_id=cycle_id,
            status="HEARTBEAT_RAN",
            awakened_goal_ids=cycle.woken_goal_ids,
            active_goal_ids=active_goal_ids,
            heartbeat_tick_id=tick_id,
            assurance_mode=cycle.assurance_mode,
            cognitive_action=cycle.next_action,
            next_tick_not_before=cycle.next_tick_not_before,
            agency_state_epoch=cycle.agency_epoch_after,
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
    p.add_argument("--active-interval", type=float, default=None)
    p.add_argument("--hold-poll", type=float, default=None)
    p.add_argument("--idle-poll", type=float, default=None)
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