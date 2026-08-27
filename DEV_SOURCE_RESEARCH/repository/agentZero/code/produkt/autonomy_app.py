from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from .autonomy_pulse import AutonomyPulse


@dataclass
class AutonomyPulseLifecycle:
    """Bind one AutonomyPulse task to the existing FastAPI process lifecycle."""

    pulse: AutonomyPulse
    task: asyncio.Task | None = None

    async def startup(self) -> None:
        if self.task is not None and not self.task.done():
            raise RuntimeError("autonomy pulse task already running")
        self.task = asyncio.create_task(
            self.pulse.run_forever(),
            name="clayverse-autonomy-pulse",
        )

    async def shutdown(self) -> None:
        self.pulse.stop()
        task = self.task
        self.task = None
        if task is None:
            return
        try:
            await task
        except asyncio.CancelledError:
            raise


def install_autonomy_pulse(app: Any, pulse: AutonomyPulse) -> AutonomyPulseLifecycle:
    """Install pulse callbacks on an existing application; creates no second server."""
    lifecycle = AutonomyPulseLifecycle(pulse)
    # FastAPI removed add_event_handler in favour of lifespan. The router lists
    # are the same hooks the lifespan context drives, so this keeps the pulse
    # bound to the one existing process lifecycle and creates no second server.
    app.router.on_startup.append(lifecycle.startup)
    app.router.on_shutdown.append(lifecycle.shutdown)
    app.state.autonomy_pulse_lifecycle = lifecycle
    return lifecycle
