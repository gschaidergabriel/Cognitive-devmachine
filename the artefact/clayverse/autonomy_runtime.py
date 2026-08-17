from __future__ import annotations

import time
from typing import Any

from .autonomy import AutonomyController, TickResult


class SupervisorAutonomyController:
    """Operational wrapper for the single ClayVerse supervisor autonomy path.

    It closes two failure modes that are unacceptable for a timer-driven agent:
    planner-declared missing prerequisites are durably blocked instead of re-polled,
    and an unexpected controller exception becomes a bounded blocked state rather than
    a hot retry loop. This wrapper owns no state; it writes only through the controller's
    existing AutonomyState/UnifiedDB authority.
    """

    def __init__(self, controller: AutonomyController):
        self.controller = controller
        self.state = controller.state

    def _durable_block(self, result: TickResult, reason: str) -> None:
        if result.goal_id is None or result.step_id is None:
            return
        now = time.time()
        with self.state.db.tx() as conn:
            conn.execute(
                "UPDATE autonomy_steps SET status='BLOCKED',last_error=?,updated_at=? WHERE step_id=? AND goal_id=? AND status!='VERIFIED'",
                (str(reason)[:1000], now, result.step_id, result.goal_id),
            )
            conn.execute(
                "UPDATE autonomy_goals SET status='BLOCKED',updated_at=? WHERE goal_id=? AND status='ACTIVE'",
                (now, result.goal_id),
            )

    def tick(self, *, trigger: str = "timer") -> TickResult:
        result = self.controller.tick(trigger=trigger)
        if result.state == "BLOCKED" and result.goal_id and result.step_id:
            # In particular this persists planner {kind:"blocked"} so the next timer
            # wake sees no frontier and therefore spends no additional model tokens.
            self._durable_block(result, result.reason)
        return result


class SupervisorAutonomyLoop:
    """Bounded in-process worker; never a second consciousness/state daemon."""

    def __init__(
        self,
        controller: SupervisorAutonomyController,
        *,
        interval_seconds: float = 30.0,
        error_backoff_seconds: float = 300.0,
    ):
        if interval_seconds < 1.0:
            raise ValueError("autonomy interval must be at least one second")
        if error_backoff_seconds < interval_seconds:
            raise ValueError("autonomy error backoff must not be shorter than interval")
        self.controller = controller
        self.interval_seconds = float(interval_seconds)
        self.error_backoff_seconds = float(error_backoff_seconds)

    def run_forever(self, stop_event: Any) -> None:
        while not stop_event.is_set():
            delay = self.interval_seconds
            try:
                result = self.controller.tick(trigger="timer")
                # BLOCKED and IDLE are quiescent states. The persistent frontier will
                # only reappear after admitted state changes, so periodic polling stays
                # bounded rather than immediately retrying.
                if result.state == "BLOCKED":
                    delay = self.error_backoff_seconds
            except Exception:
                # The supervisor must not spin if a capability provider/planner bridge
                # fails before the base controller can produce a TickResult.
                delay = self.error_backoff_seconds
            stop_event.wait(delay)
