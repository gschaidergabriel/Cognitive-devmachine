from __future__ import annotations

import time
from typing import Any

from .autonomy import AutonomyController, AutonomyState, TickResult


def recover_autonomy_after_restart(state: AutonomyState) -> dict[str, int]:
    """Fail closed on autonomy work interrupted by a process/container restart.

    Recovery of the normal turn/effect spine advances the global entity generation
    first. This pass never replays a RUNNING autonomy step. A step that was in-flight
    is epistemically unknown and therefore becomes BLOCKED with an explicit recovery
    tick. WAITING_VERIFICATION remains quiescent and its goal is forced PAUSED.
    """
    generation = state.db.entity_generation()
    counts = {
        "running_blocked_unknown": 0,
        "waiting_goals_paused": 0,
        "generation": generation,
    }
    now = time.time()
    with state.db.tx() as conn:
        running = conn.execute(
            "SELECT step_id,goal_id FROM autonomy_steps WHERE status='RUNNING' ORDER BY updated_at,step_id"
        ).fetchall()
        for row in running:
            reason = "UNKNOWN_AFTER_RESTART:autonomy_step_interrupted"
            conn.execute(
                "UPDATE autonomy_steps SET status='BLOCKED',last_error=?,updated_at=? WHERE step_id=?",
                (reason, now, row["step_id"]),
            )
            conn.execute(
                "UPDATE autonomy_goals SET status='BLOCKED',updated_at=? WHERE goal_id=? AND status NOT IN ('DONE','CANCELLED')",
                (now, row["goal_id"]),
            )
            conn.execute(
                "INSERT INTO autonomy_ticks(tick_id,goal_id,step_id,generation,trigger,proposal,action_state,receipt_id,reason,ts) VALUES(?,?,?,?, 'recovery',NULL,'BLOCKED',NULL,?,?)",
                (
                    __import__("uuid").uuid4().hex,
                    row["goal_id"],
                    row["step_id"],
                    generation,
                    reason,
                    now,
                ),
            )
            counts["running_blocked_unknown"] += 1

        waiting_goals = conn.execute(
            "SELECT DISTINCT g.goal_id FROM autonomy_goals g JOIN autonomy_steps s ON s.goal_id=g.goal_id WHERE g.status='ACTIVE' AND s.status='WAITING_VERIFICATION'"
        ).fetchall()
        for row in waiting_goals:
            conn.execute(
                "UPDATE autonomy_goals SET status='PAUSED',updated_at=? WHERE goal_id=?",
                (now, row["goal_id"]),
            )
            counts["waiting_goals_paused"] += 1
    return counts


class SupervisorAutonomyController:
    """Operational wrapper for the single ClayVerse supervisor autonomy path.

    The base controller already persists semantic blockers and effect uncertainty.
    This wrapper is the one supervisor-facing entry point and defensively re-applies a
    durable block if any future controller implementation returns BLOCKED without one.
    """

    def __init__(self, controller: AutonomyController):
        self.controller = controller
        self.state = controller.state

    def tick(self, *, trigger: str = "timer") -> TickResult:
        result = self.controller.tick(trigger=trigger)
        if result.state == "BLOCKED" and result.goal_id and result.step_id:
            self.state.block(result.goal_id, result.step_id, result.reason)
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
                if result.state in {"BLOCKED", "WAITING_VERIFICATION"}:
                    delay = self.error_backoff_seconds
            except Exception:
                # The supervisor must not spin if a provider/capability bridge fails
                # outside the bounded base controller. No success is inferred here.
                delay = self.error_backoff_seconds
            stop_event.wait(delay)
