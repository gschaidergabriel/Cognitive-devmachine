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
    app.add_event_handler("startup", lifecycle.startup)
    app.add_event_handler("shutdown", lifecycle.shutdown)
    app.state.autonomy_pulse_lifecycle = lifecycle
    return lifecycle
