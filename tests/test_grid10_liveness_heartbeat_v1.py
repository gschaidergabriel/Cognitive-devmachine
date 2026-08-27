from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from grid10_fabric import Fabric
from grid10_liveness_heartbeat_v1 import (
    HeartbeatPump,
    LivenessError,
    runtime_liveness_heartbeat,
)


def _epoch(db: Path) -> int:
    con = sqlite3.connect(str(db))
    try:
        return int(con.execute("SELECT v FROM meta WHERE k='epoch'").fetchone()[0])
    finally:
        con.close()


def _last_seen(db: Path, node_id: str) -> float:
    con = sqlite3.connect(str(db))
    try:
        return float(con.execute("SELECT last_seen_ts FROM nodes WHERE node_id=?", (node_id,)).fetchone()[0])
    finally:
        con.close()


def test_liveness_heartbeat_does_not_advance_s1_epoch(tmp_path: Path) -> None:
    db = tmp_path / "fabric.sqlite"
    f = Fabric(db)
    f.runtime_join("node-a", "reason", 123)
    before = _epoch(db)
    runtime_liveness_heartbeat(f, "node-a")
    after = _epoch(db)
    assert after == before


def test_missing_node_fails_closed(tmp_path: Path) -> None:
    f = Fabric(tmp_path / "fabric.sqlite")
    with pytest.raises(LivenessError, match="NODE_NOT_ADMITTED"):
        runtime_liveness_heartbeat(f, "ghost")


def test_background_pump_stays_fresh_during_blocking_decode_window(tmp_path: Path) -> None:
    db = tmp_path / "fabric.sqlite"
    f = Fabric(db)
    f.runtime_join("node-a", "reason", 123)
    pump = HeartbeatPump(f, "node-a", interval_s=0.05).start()
    t0 = _last_seen(db, "node-a")
    # Simulates a blocking decode longer than the reclaim threshold used below.
    time.sleep(0.35)
    t1 = _last_seen(db, "node-a")
    stats = pump.stop()
    assert t1 > t0
    assert stats.successes >= 3
    assert stats.failures == 0


def test_healthy_blocked_worker_is_not_reclaimed_with_pump(tmp_path: Path) -> None:
    db = tmp_path / "fabric.sqlite"
    f = Fabric(db)
    f.runtime_join("worker", "reason", 111)
    f.runtime_join("rescuer", "reason", 222)
    f.seed_scope("scope-a")
    f.seed_task("task-a", "scope-a", 10, "reason", {"prompt": "x"})
    snap = f.snapshot()
    f.runtime_claim_task("task-a", "worker", expected_epoch=snap.epoch)

    pump = HeartbeatPump(f, "worker", interval_s=0.03).start()
    # Longer than stale_after_seconds.  Without a background heartbeat this exact
    # situation was empirically observed to cause false reclaim/thrashing.
    time.sleep(0.22)
    reclaimed = f.runtime_reclaim_stale_claims("rescuer", stale_after_seconds=0.08)
    pump.stop()
    assert reclaimed == []
    task = next(t for t in f.snapshot().tasks if t["task_id"] == "task-a")
    assert task["status"] == "CLAIMED"
    assert task["claimed_by"] == "worker"


def test_stopped_pump_allows_real_crash_reclaim(tmp_path: Path) -> None:
    db = tmp_path / "fabric.sqlite"
    f = Fabric(db)
    f.runtime_join("worker", "reason", 111)
    f.runtime_join("rescuer", "reason", 222)
    f.seed_scope("scope-a")
    f.seed_task("task-a", "scope-a", 10, "reason", {"prompt": "x"})
    snap = f.snapshot()
    f.runtime_claim_task("task-a", "worker", expected_epoch=snap.epoch)

    pump = HeartbeatPump(f, "worker", interval_s=0.02).start()
    time.sleep(0.06)
    pump.stop()  # models SIGKILL effect: heartbeats cease; row remains healthy=1
    time.sleep(0.11)
    reclaimed = f.runtime_reclaim_stale_claims("rescuer", stale_after_seconds=0.08)
    assert reclaimed == ["task-a"]
    task = next(t for t in f.snapshot().tasks if t["task_id"] == "task-a")
    assert task["status"] == "OPEN"
    assert task["claimed_by"] is None


def test_fast_heartbeats_do_not_create_global_cas_churn(tmp_path: Path) -> None:
    db = tmp_path / "fabric.sqlite"
    f = Fabric(db)
    f.runtime_join("worker", "reason", 111)
    f.seed_scope("scope-a")
    f.seed_task("task-a", "scope-a", 10, "reason", {"prompt": "x"})
    before = _epoch(db)
    pump = HeartbeatPump(f, "worker", interval_s=0.01).start()
    time.sleep(0.08)
    pump.stop()
    after = _epoch(db)
    assert after == before
