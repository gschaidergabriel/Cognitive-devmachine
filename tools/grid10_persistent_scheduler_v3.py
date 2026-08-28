#!/usr/bin/env python3
"""Persistent GRID10 scheduler v3: scheduler-v2 semantics through crash-reconciling v7.

The scheduler remains a service wrapper rather than a wake/Agency/GWT authority. Its only
functional delta from v2 is that active/due-wake ticks enter unified runtime v7, which places
a durable attempt identity around the existing v6 path and can later type a V4-committed but
v6-unclosed crash window as UNKNOWN without same-tick replay.
"""
from __future__ import annotations

from dataclasses import asdict
import argparse
import json
from pathlib import Path
import time
from typing import Any, Callable, Iterable, Mapping

from grid10_cognitive_unified_runtime_v7 import build_unified_cognitive_runtime_v7
from grid10_glm_cognitive_cycle_v1 import CognitiveCycleConfig
from grid10_glm_inference_provider_v1 import GLMInferenceResult
from grid10_persistent_scheduler_v1 import SchedulerConfig, SchedulerCycleResult
from grid10_persistent_scheduler_v2 import PersistentCognitiveSchedulerV2

SCHEMA = "GRID10_PERSISTENT_SCHEDULER/v3"


class PersistentCognitiveSchedulerV3(PersistentCognitiveSchedulerV2):
    """Reuse v2 scheduling policy while routing cognition through unified runtime v7."""

    def __init__(
        self,
        unified_db: Path,
        frames_jsonl: Path,
        *,
        config: SchedulerConfig = SchedulerConfig(),
        inference_fn: Callable[..., GLMInferenceResult] | None = None,
        cognitive_config: CognitiveCycleConfig = CognitiveCycleConfig(),
        recovery_stale_after_seconds: float = 60.0,
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
        ) = build_unified_cognitive_runtime_v7(
            self.unified_db,
            allow_regulator_writes=config.allow_regulator_writes,
            inference_fn=inference_fn,
            cognitive_config=cognitive_config,
            recovery_stale_after_seconds=recovery_stale_after_seconds,
        )

    def cycle_once(
        self,
        *,
        cycle_id: str,
        now_ts: float | None = None,
        observed_events: Iterable[str] = (),
        cognitive_context: Mapping[str, Any] | None = None,
    ) -> SchedulerCycleResult:
        # Eventual restart closure for stale attempts. Fresh attempts are deliberately skipped
        # so another live process cannot be declared dead merely because it is still computing.
        self.runtime.reconcile_pending_attempts()
        return super().cycle_once(
            cycle_id=cycle_id,
            now_ts=now_ts,
            observed_events=observed_events,
            cognitive_context=cognitive_context,
        )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--unified-db", required=True)
    p.add_argument("--frames-jsonl", required=True)
    p.add_argument("--cycles", type=int, default=1)
    p.add_argument("--forever", action="store_true")
    p.add_argument("--active-interval", type=float, default=None)
    p.add_argument("--hold-poll", type=float, default=None)
    p.add_argument("--idle-poll", type=float, default=None)
    p.add_argument("--recovery-stale-after", type=float, default=60.0)
    p.add_argument("--allow-regulator-writes", action="store_true")
    p.add_argument("--trusted-normal-test-fixture", action="store_true")
    p.add_argument("--event", action="append", default=[])
    args = p.parse_args()

    # As in v2, the CLI intentionally exposes no provider selector. Plain service/CLI use
    # therefore cannot create an implicit provider route.
    scheduler = PersistentCognitiveSchedulerV3(
        Path(args.unified_db),
        Path(args.frames_jsonl),
        config=SchedulerConfig(
            active_interval_seconds=args.active_interval,
            hold_poll_seconds=args.hold_poll,
            idle_poll_seconds=args.idle_poll,
            allow_regulator_writes=bool(args.allow_regulator_writes),
            trusted_normal_test_fixture=bool(args.trusted_normal_test_fixture),
        ),
        recovery_stale_after_seconds=float(args.recovery_stale_after),
    )
    if args.forever:
        scheduler.run_forever()
        return 0

    for i in range(max(0, int(args.cycles))):
        now = time.time()
        row = scheduler.cycle_once(
            cycle_id=f"bounded-scheduler-v3-{time.time_ns()}-{i}",
            now_ts=now,
            observed_events=args.event if i == 0 else (),
        )
        print(json.dumps(asdict(row), sort_keys=True))
        if row.heartbeat_tick_id is not None:
            # Inherited cycle_once already appended the frame. This branch is intentionally
            # a no-op marker: v3 does not create a second frame/event authority.
            pass
        if i + 1 < args.cycles:
            snap = scheduler.agency.snapshot()
            if snap.next_tick_not_before is not None:
                time.sleep(max(0.05, snap.next_tick_not_before - time.time()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "SCHEMA",
    "PersistentCognitiveSchedulerV3",
    "SchedulerConfig",
    "SchedulerCycleResult",
]
