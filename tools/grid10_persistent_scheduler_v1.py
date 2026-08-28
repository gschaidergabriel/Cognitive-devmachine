#!/usr/bin/env python3
"""Persistent GRID10 scheduler over the single UnifiedDB cognitive runtime.

This is a control-loop service wrapper, not a second cognition/state authority. It uses the
same physical SQLite opened by ``grid10_cognitive_unified_runtime_v4`` and delegates every
wake/heartbeat/checkpoint/next-tick cognitive transition to that v4 core. Idle/HOLD scheduling
uses the same v4 CAS helper so the service wrapper no longer owns a second write sequence.

The live Dynamic Frame is the default cadence authority: active and HOLD ticks are resolved
inside v4 from its single per-tick ControlSnapshot; an idle cycle latches one snapshot solely
to resolve ``pulse.idle_interval_seconds``. Explicit config/CLI interval values remain bounded
compatibility/test overrides and do not create a second durable control authority.

The key Stage-2 behavior is explicit and falsifiable:

    checkpoint -> HOLD/DORMANT -> process restart -> exact wake condition
    -> ACTIVE -> cognitive heartbeat -> checkpoint -> durable next-tick schedule

The scheduler may inspect whether a deferred wake condition is due, but it never performs the
wake transition itself. Only v4 calls ``wake_due`` and therefore only v4 may mint wake lineage
inside a cognitive-cycle receipt.
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
    RuntimeCycleNotDue,
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


def _pending_wake_due(snapshot, *, now_ts: float, observed_events: Iterable[str]) -> bool:
    """Pure preflight: report whether v4's next wake_due call should have work to do.

    This helper performs no writes and grants no wake provenance. It exists only so an idle
    service wrapper does not run a heartbeat when there is neither an active goal nor a due
    deferred intent.
    """
    observed = frozenset(str(x) for x in observed_events)
    goals = {g.goal_id: g for g in snapshot.goals}
    for intent in snapshot.deferred_intents:
        if getattr(intent.state, "value", str(intent.state)) != "PENDING":
            continue
        goal = goals.get(intent.goal_id)
        if goal is None:
            continue
        if goal.state != GoalState.DORMANT or goal.generation != intent.goal_generation:
            continue
        kind = getattr(intent.wake_kind, "value", str(intent.wake_kind))
        if kind in {"TIME_AT", "PERIODIC_REVIEW"}:
            try:
                if now_ts >= float(intent.wake_value):
                    return True
            except ValueError:
                continue
        elif kind == "EVENT" and intent.wake_value in observed:
            return True
    return False


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

    def _not_due_result(
        self,
        *,
        cycle_id: str,
        snapshot,
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

        # No active cognition and no legitimate wake is pending. The wrapper may either remain
        # NOT_DUE or write one atomic idle-HOLD checkpoint; it must not manufacture wake IDs.
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

        # Active work or a deterministically due wake enters v4. v4 owns wake_due and records
        # the exact goal IDs it actually woke; caller-supplied prewoken provenance is forbidden.
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
