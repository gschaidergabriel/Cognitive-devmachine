#!/usr/bin/env python3
"""High-fanout runtime policy for the 6000-worker FREE fabric.

Epoch-8.70 economic gating remains in v3.  This layer changes only transient
capacity control: a single 5xx/network failure must not freeze an entire healthy
provider while hundreds of unrelated routes are in flight.  429 remains the
provider-wide truth signal and is unchanged.
"""
from __future__ import annotations

import asyncio

import run_6000_free_swarm_v3 as gated

fabric = gated.fabric
FastProviderRuntime = fabric.FastProviderRuntime
_ORIGINAL_FAST_SUCCESS = FastProviderRuntime.on_success


async def high_fanout_success(self: FastProviderRuntime) -> None:
    await _ORIGINAL_FAST_SUCCESS(self)
    self._transient_streak = 0


async def high_fanout_transient_error(self: FastProviderRuntime) -> None:
    """AIMD for 5xx/network faults without provider-wide stop-the-world cooldown.

    In a 100+ request fabric a single route/backend 503 is weak evidence that the
    *whole* provider is unavailable.  We therefore keep dispatching other work,
    trim the target gently on repeated transient failures, and reserve hard global
    cooldowns for explicit 429 Retry-After signals handled by on_429().
    """
    async with self._condition:
        self.errors += 1
        self.success_streak = 0
        streak = int(getattr(self, "_transient_streak", 0)) + 1
        self._transient_streak = streak
        if streak >= 4:
            floor = max(2, len(self.enabled_keys()) * 2)
            reduced = max(floor, int(self.target_concurrency * 0.90))
            self.target_concurrency = min(self.max_concurrency, reduced)
            self._transient_streak = 0
        # Deliberately NO provider-wide cooldown_until mutation here.
        self._condition.notify_all()


FastProviderRuntime.on_success = high_fanout_success
FastProviderRuntime.on_transient_error = high_fanout_transient_error

run = gated.run
parse_args = gated.parse_args

if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
