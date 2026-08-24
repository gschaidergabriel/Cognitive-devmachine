#!/usr/bin/env python3
"""High-fanout runtime policy for the 6000-worker FREE fabric.

This compatibility layer predates the successor model-health scheduler. When
model-health v1 is installed first, its model-scoped transient isolation wins and
this module becomes a no-op wrapper over v3. Without model-health, the historical
high-fanout transient policy remains available. Explicit 429 handling stays in the
provider runtime/economic gate.
"""
from __future__ import annotations

import asyncio

import run_6000_free_swarm_v3 as gated

fabric = gated.fabric
FastProviderRuntime = fabric.FastProviderRuntime
_ORIGINAL_FAST_SUCCESS = FastProviderRuntime.on_success
_ORIGINAL_TRANSIENT = FastProviderRuntime.on_transient_error


async def high_fanout_success(self: FastProviderRuntime) -> None:
    await _ORIGINAL_FAST_SUCCESS(self)
    self._transient_streak = 0


async def high_fanout_transient_error(self: FastProviderRuntime) -> None:
    """Fallback provider-level AIMD only when model-health routing is absent."""
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
        self._condition.notify_all()


# Successor-current fast launcher installs model-health before importing this
# module. Never replace its model-scoped transient isolation with the older
# provider-scoped fallback. Direct legacy v4 launches retain historical behavior.
if not getattr(FastProviderRuntime, "_model_health_v1_installed", False):
    FastProviderRuntime.on_success = high_fanout_success
    FastProviderRuntime.on_transient_error = high_fanout_transient_error

run = gated.run
parse_args = gated.parse_args

if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
