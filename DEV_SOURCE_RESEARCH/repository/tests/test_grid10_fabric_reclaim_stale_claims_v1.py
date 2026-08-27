"""Regression tests for Fabric.runtime_reclaim_stale_claims() (2026-08-27, GRID10
use-case-1 research: found empirically that a task claimed by a node that then dies
before emitting a result was stuck forever -- no reclaim path existed at all).

Real sqlite (tmp_path), no mocking of the fabric itself.
"""
import importlib.util
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
spec = importlib.util.spec_from_file_location("grid10_fabric", TOOLS / "grid10_fabric.py")
grid10_fabric = importlib.util.module_from_spec(spec)
sys.modules["grid10_fabric"] = grid10_fabric
spec.loader.exec_module(grid10_fabric)

from grid10_fabric import Fabric, result_packet  # noqa: E402


def _fabric(tmp_path):
    f = Fabric(tmp_path / "s1.sqlite")
    f.seed_scope("scope-a")
    return f


def test_reclaims_task_from_explicitly_unhealthy_node(tmp_path):
    f = _fabric(tmp_path)
    f.runtime_join("dead-node", "reason", pid=1)
    f.seed_task("task-1", "scope-a", 90, "reason", {"prompt": "x"})
    snap = f.snapshot()
    f.runtime_claim_task("task-1", "dead-node", expected_epoch=snap.epoch)

    f.runtime_heartbeat("dead-node", healthy=False)
    f.runtime_join("rescuer", "reason", pid=2)

    reclaimed = f.runtime_reclaim_stale_claims("rescuer", stale_after_seconds=15.0)
    assert reclaimed == ["task-1"]

    row = [dict(r) for r in f.snapshot().tasks if r["task_id"] == "task-1"][0]
    assert row["status"] == "OPEN"
    assert row["claimed_by"] is None


def test_reclaims_task_from_hard_killed_node_that_never_reported_unhealthy(tmp_path):
    # The realistic case: a SIGKILL'd process never gets to call
    # runtime_heartbeat(healthy=False) at all -- healthy stays 1 forever, only a
    # stale last_seen_ts betrays it.
    f = _fabric(tmp_path)
    f.runtime_join("killed-node", "reason", pid=1)
    f.seed_task("task-2", "scope-a", 90, "reason", {"prompt": "x"})
    snap = f.snapshot()
    f.runtime_claim_task("task-2", "killed-node", expected_epoch=snap.epoch)
    f.runtime_join("rescuer", "reason", pid=2)

    time.sleep(0.08)
    reclaimed = f.runtime_reclaim_stale_claims("rescuer", stale_after_seconds=0.05)
    assert reclaimed == ["task-2"]


def test_does_not_reclaim_task_from_healthy_recently_seen_node(tmp_path):
    f = _fabric(tmp_path)
    f.runtime_join("alive-node", "reason", pid=1)
    f.seed_task("task-3", "scope-a", 90, "reason", {"prompt": "x"})
    snap = f.snapshot()
    f.runtime_claim_task("task-3", "alive-node", expected_epoch=snap.epoch)
    f.runtime_heartbeat("alive-node", healthy=True)
    f.runtime_join("rescuer", "reason", pid=2)

    reclaimed = f.runtime_reclaim_stale_claims("rescuer", stale_after_seconds=15.0)
    assert reclaimed == []
    row = [dict(r) for r in f.snapshot().tasks if r["task_id"] == "task-3"][0]
    assert row["status"] == "CLAIMED"
    assert row["claimed_by"] == "alive-node"


def test_does_not_reclaim_task_with_result_already_pending_in_outbox(tmp_path):
    f = _fabric(tmp_path)
    f.runtime_join("dead-node", "reason", pid=1)
    f.seed_task("task-4", "scope-a", 90, "reason", {"prompt": "x"})
    snap = f.snapshot()
    f.runtime_claim_task("task-4", "dead-node", expected_epoch=snap.epoch)

    fresh = f.snapshot()
    packet = result_packet("dead-node", fresh, "scope-a", {"task_id": "task-4", "answer": "42"})
    f.emit_node_result(packet)

    f.runtime_heartbeat("dead-node", healthy=False)
    f.runtime_join("rescuer", "reason", pid=2)

    reclaimed = f.runtime_reclaim_stale_claims("rescuer", stale_after_seconds=15.0)
    assert reclaimed == [], "must not reclaim -- a real result is already in flight in the outbox"
    row = [dict(r) for r in f.snapshot().tasks if r["task_id"] == "task-4"][0]
    assert row["status"] == "CLAIMED"


def test_reclaimed_task_is_really_claimable_again_at_fresh_epoch(tmp_path):
    f = _fabric(tmp_path)
    f.runtime_join("dead-node", "reason", pid=1)
    f.seed_task("task-5", "scope-a", 90, "reason", {"prompt": "x"})
    snap = f.snapshot()
    f.runtime_claim_task("task-5", "dead-node", expected_epoch=snap.epoch)
    f.runtime_heartbeat("dead-node", healthy=False)
    f.runtime_join("new-claimer", "reason", pid=2)

    f.runtime_reclaim_stale_claims("new-claimer", stale_after_seconds=15.0)

    fresh = f.snapshot()
    f.runtime_claim_task("task-5", "new-claimer", expected_epoch=fresh.epoch)
    row = [dict(r) for r in f.snapshot().tasks if r["task_id"] == "task-5"][0]
    assert row["status"] == "CLAIMED"
    assert row["claimed_by"] == "new-claimer"


def test_no_eligible_tasks_returns_empty_list_cleanly(tmp_path):
    f = _fabric(tmp_path)
    f.runtime_join("solo", "reason", pid=1)
    reclaimed = f.runtime_reclaim_stale_claims("solo", stale_after_seconds=15.0)
    assert reclaimed == []
    # fabric must remain queryable/consistent afterward
    f.snapshot()
