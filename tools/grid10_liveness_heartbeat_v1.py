#!/usr/bin/env python3
"""GRID10 runtime-liveness heartbeat decoupled from cognitive S1 epochs.

Why this exists
---------------
Real crash testing on 2026-08-27 showed that a healthy Xeno can be falsely
reclaimed while it is inside a blocking model decode because ``node_loop`` only
heartbeats between decode calls.  Simply adding a background thread around the
existing ``Fabric.runtime_heartbeat`` would create a second problem: that method
bumps the global fabric epoch on every heartbeat, so a fast liveness thread would
continuously invalidate otherwise unrelated task-claim CAS operations.

This module separates *runtime liveness* from *cognitive state progression*:

* ``runtime_liveness_heartbeat`` updates only ``nodes.healthy`` and
  ``nodes.last_seen_ts`` in a short SQLite transaction.  It deliberately does
  NOT mutate ``meta.epoch`` or any S1 scope/task state.
* ``HeartbeatPump`` runs that operation from a daemon thread while the main Xeno
  thread may be blocked inside model generation.

Authority boundary
------------------
This is deterministic runtime-membership metadata, not a model-originated S1
write.  It never grants coordinator authority and never writes canonical S0.
It performs no network/provider calls and reads no provider secrets.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from grid10_fabric import Fabric, connect


class LivenessError(RuntimeError):
    pass


def runtime_liveness_heartbeat(fabric: Fabric, node_id: str, healthy: bool = True) -> float:
    """Refresh one admitted node's liveness without advancing the S1 epoch.

    Returns the timestamp written.  Missing nodes fail closed rather than being
    silently created by a heartbeat.
    """
    ts = time.time()
    con = connect(Path(fabric.path))
    try:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute("SELECT node_id FROM nodes WHERE node_id=?", (node_id,)).fetchone()
        if row is None:
            raise LivenessError(f"NODE_NOT_ADMITTED:{node_id}")
        before_epoch = int(con.execute("SELECT v FROM meta WHERE k='epoch'").fetchone()["v"])
        con.execute(
            "UPDATE nodes SET healthy=?,last_seen_ts=? WHERE node_id=?",
            (1 if healthy else 0, ts, node_id),
        )
        after_epoch = int(con.execute("SELECT v FROM meta WHERE k='epoch'").fetchone()["v"])
        if after_epoch != before_epoch:
            raise LivenessError("LIVENESS_HEARTBEAT_CHANGED_S1_EPOCH")
        con.execute("COMMIT")
        return ts
    except Exception:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        con.close()


@dataclass
class HeartbeatStats:
    attempts: int = 0
    successes: int = 0
    failures: int = 0
    last_success_ts: float | None = None
    last_error: str | None = None


class HeartbeatPump:
    """Background runtime-liveness pump safe to run during blocking decode."""

    def __init__(
        self,
        fabric: Fabric,
        node_id: str,
        *,
        interval_s: float = 0.5,
        heartbeat_fn: Callable[[Fabric, str, bool], float] = runtime_liveness_heartbeat,
    ) -> None:
        if interval_s <= 0:
            raise ValueError("interval_s must be > 0")
        self.fabric = fabric
        self.node_id = node_id
        self.interval_s = float(interval_s)
        self.heartbeat_fn = heartbeat_fn
        self.stats = HeartbeatStats()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> "HeartbeatPump":
        if self.running:
            return self
        # Fail immediately if the node was never admitted.  Do not hide a bad
        # startup behind an eventually-failing daemon thread.
        self._beat_once()
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            name=f"grid10-heartbeat:{self.node_id}",
            daemon=True,
        )
        self._thread.start()
        return self

    def _beat_once(self) -> None:
        self.stats.attempts += 1
        try:
            ts = self.heartbeat_fn(self.fabric, self.node_id, True)
            self.stats.successes += 1
            self.stats.last_success_ts = ts
            self.stats.last_error = None
        except Exception as exc:  # liveness failure is observable, never silent
            self.stats.failures += 1
            self.stats.last_error = repr(exc)
            raise

    def _run(self) -> None:
        # wait() makes stop responsive instead of sleeping an entire interval.
        while not self._stop.wait(self.interval_s):
            try:
                self._beat_once()
            except Exception:
                # Keep trying: a transient SQLITE_BUSY must not permanently kill
                # liveness.  The failure count remains observable to the caller.
                continue

    def stop(self, *, mark_unhealthy: bool = False, timeout_s: float = 2.0) -> HeartbeatStats:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout_s)
        if mark_unhealthy:
            runtime_liveness_heartbeat(self.fabric, self.node_id, False)
        return self.stats


__all__ = [
    "HeartbeatPump",
    "HeartbeatStats",
    "LivenessError",
    "runtime_liveness_heartbeat",
]
