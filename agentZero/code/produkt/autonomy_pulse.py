from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from pathlib import Path

from .autonomy_dispatch import AutonomyDispatch, reserve_dispatch
from .autonomy_planner import AutonomyPlanner
from .identity import IdentityRouter
from .store import LeaseConflict, UnifiedDB, resolve_db_path
from .terminal_sessions import TerminalRuntimeError, TerminalSessionManager


@dataclass(frozen=True)
class PulseResult:
    user_id: str
    status: str
    goal_id: str | None = None
    step_id: str | None = None
    detail: str | None = None


class AutonomyPulse:
    """Event-loop task that wakes admitted goal work through the existing Claude terminal.

    It is not a second daemon, state authority, inference engine or effect path. Each tick
    opens the same UnifiedDB, uses AutonomyPlanner, reserves one existing DB lease, and
    injects only the one-shot terminal nonce into the managed Claude session.
    """

    CANONICAL_USERS = ("gabriel", "andreas")

    def __init__(
        self,
        state_root: str | Path,
        terminals: TerminalSessionManager,
        *,
        interval_seconds: float = 30.0,
    ) -> None:
        interval = float(interval_seconds)
        if not 5.0 <= interval <= 3600.0:
            raise ValueError("autonomy pulse interval out of range")
        self.state_root = Path(state_root)
        self.terminals = terminals
        self.interval_seconds = interval
        self._stop = asyncio.Event()

    @staticmethod
    def _linux_process_start_epoch(pid: int) -> float:
        if not isinstance(pid, int) or pid <= 1:
            raise TerminalRuntimeError("invalid managed Claude pane pid")
        try:
            stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
            fields = stat.split()
            if len(fields) <= 21:
                raise ValueError("short proc stat")
            start_ticks = int(fields[21])
            boot_time = None
            for line in Path("/proc/stat").read_text(encoding="utf-8").splitlines():
                if line.startswith("btime "):
                    boot_time = int(line.split()[1])
                    break
            if boot_time is None:
                raise ValueError("missing boot time")
            ticks_per_second = int(os.sysconf("SC_CLK_TCK"))
            if ticks_per_second <= 0:
                raise ValueError("invalid clock tick rate")
            return float(boot_time) + (float(start_ticks) / float(ticks_per_second))
        except (OSError, ValueError, IndexError) as exc:
            raise TerminalRuntimeError("managed Claude process start attestation unavailable") from exc

    def _pane_process_start(self, user_id: str) -> float:
        binding, pane_id = self.terminals.assert_detached_idle_claude(user_id)
        cp = self.terminals._run_tmux(
            binding,
            "display-message", "-p", "-t", pane_id, "#{pane_pid}",
        )
        if cp.returncode != 0:
            raise TerminalRuntimeError("managed Claude pane pid attestation unavailable")
        raw = cp.stdout.strip()
        if not raw.isdigit():
            raise TerminalRuntimeError("managed Claude pane pid malformed")
        return self._linux_process_start_epoch(int(raw))

    @staticmethod
    def _has_human_roundtrip_after(db: UnifiedDB, user_id: str, started_at: float) -> bool:
        session_id = f"session:{user_id}"
        rows = db.db.execute(
            "SELECT t.turn_id,t.provenance,w.state FROM turns t "
            "JOIN workspace_episodes w ON w.observation_turn_id=t.turn_id "
            "WHERE t.session_id=? AND t.user_id=? AND t.role='user' AND t.ts>=? "
            "ORDER BY t.ts DESC LIMIT 20",
            (session_id, user_id, float(started_at)),
        ).fetchall()
        for row in rows:
            if row["state"] not in ("SELECTED", "COMPLETED"):
                continue
            try:
                provenance = AutonomyPlanner(db).controller._loads(row["provenance"] or "{}")
            except Exception:
                continue
            if provenance.get("source") != "claude-hook:UserPromptSubmit":
                continue
            causal = provenance.get("causal_id")
            if not isinstance(causal, str) or not causal:
                continue
            terminal = db.db.execute(
                "SELECT 1 FROM causal_episodes WHERE causal_id=? AND observation_turn_id=? AND reentered=1",
                (causal, row["turn_id"]),
            ).fetchone()
            if terminal is not None:
                return True
        return False

    @staticmethod
    def _cancel_dispatch(db: UnifiedDB, dispatch: AutonomyDispatch) -> bool:
        with db.tx() as tx:
            cur = tx.execute(
                "DELETE FROM leases WHERE resource=? AND nonce=?",
                (f"autonomy-dispatch:{dispatch.session_id}", dispatch.nonce),
            )
            return cur.rowcount == 1

    def tick_user(self, user_id: str) -> PulseResult:
        if user_id not in self.CANONICAL_USERS:
            raise PermissionError("autonomy pulse requires canonical user")
        if not self.terminals.activity.try_reserve_autonomy(user_id):
            return PulseResult(user_id, "HUMAN_OR_AUTONOMY_ACTIVE")

        dispatch: AutonomyDispatch | None = None
        dispatched = False
        db: UnifiedDB | None = None
        try:
            process_start = self._pane_process_start(user_id)
            db = UnifiedDB(resolve_db_path(self.state_root))
            IdentityRouter(db, {})
            session_id = f"session:{user_id}"
            active = db.db.execute(
                "SELECT turn_id FROM active_turns WHERE session_id=?",
                (session_id,),
            ).fetchone()
            if active is not None:
                return PulseResult(user_id, "CANONICAL_TURN_ACTIVE")
            if not self._has_human_roundtrip_after(db, user_id, process_start):
                return PulseResult(user_id, "CLAUDE_RUNTIME_NOT_HUMAN_ATTESTED")

            prepared = AutonomyPlanner(db).prepare_next(user_id)
            if prepared is None:
                return PulseResult(user_id, "NO_RUNNABLE_GOAL")
            dispatch = reserve_dispatch(
                db,
                user_id=user_id,
                goal_id=prepared["goal_id"],
                step_id=prepared["step_id"],
                instruction=prepared["prompt"],
            )
            terminal_prompt = dispatch.terminal_prompt
            db.close()
            db = None

            # Re-attest detached/idle state inside dispatch_autonomy_prompt immediately
            # before the tmux server receives synthetic input.
            self.terminals.dispatch_autonomy_prompt(user_id, terminal_prompt)
            dispatched = True
            return PulseResult(
                user_id,
                "DISPATCHED",
                goal_id=prepared["goal_id"],
                step_id=prepared["step_id"],
            )
        except LeaseConflict:
            return PulseResult(user_id, "DISPATCH_ALREADY_RESERVED")
        except TerminalRuntimeError as exc:
            return PulseResult(user_id, "TERMINAL_NOT_SAFE", detail=type(exc).__name__)
        except Exception as exc:
            # A pulse is never allowed to kill the service event loop. Unknown internal
            # failures stay explicit and do not acquire execution/completion credit.
            return PulseResult(user_id, "PULSE_BLOCKED", detail=type(exc).__name__)
        finally:
            if db is not None:
                db.close()
            if dispatch is not None and not dispatched:
                cleanup = UnifiedDB(resolve_db_path(self.state_root))
                try:
                    self._cancel_dispatch(cleanup, dispatch)
                finally:
                    cleanup.close()
            self.terminals.activity.release_autonomy(user_id)

    def run_once(self) -> list[PulseResult]:
        return [self.tick_user(user_id) for user_id in self.CANONICAL_USERS]

    async def run_forever(self) -> None:
        while not self._stop.is_set():
            for user_id in self.CANONICAL_USERS:
                if self._stop.is_set():
                    break
                await asyncio.to_thread(self.tick_user, user_id)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self.interval_seconds)
            except TimeoutError:
                pass

    def stop(self) -> None:
        self._stop.set()
