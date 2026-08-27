"""Regression test for Fabric.elect_coordinator()'s TTL-expiry-aware re-election
(2026-08-27, GRID10 use-case-2 edge-resilience experiment).

Real gap found empirically: elect_coordinator() only ever checked `valid=1`, never
whether an existing lease had actually expired via LEASE_TTL_SECONDS. A dead
coordinator (SIGKILLed, not just left idle-but-alive past its TTL) left its lease
`valid=1` forever, permanently blocking election for that scope -- confirmed in a
live 10-process mass-SIGKILL experiment where a killed coordinator's scope never
recovered within a 40s bound. This test reproduces the bug deterministically (no
model, no forked processes needed) and verifies the fix.
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

from grid10_fabric import Fabric  # noqa: E402


def test_expired_lease_from_a_now_dead_coordinator_is_reelectable(tmp_path, monkeypatch):
    monkeypatch.setattr(grid10_fabric, "LEASE_TTL_SECONDS", 0.05)

    f = Fabric(tmp_path / "s1.sqlite")
    f.seed_scope("scope-a")
    f.runtime_join("dead-coordinator", "reason", pid=1)

    elected = f.elect_coordinator("scope-a", candidate_node_ids=["dead-coordinator"])
    assert elected is not None
    lease1, _token1 = elected

    # simulate the coordinator process being SIGKILLed -- nothing ever calls
    # revoke_lease() for it; its row simply stays valid=1 forever in the DB.
    time.sleep(0.1)  # let the tiny TTL actually elapse

    f.runtime_join("new-coordinator", "reason", pid=2)
    reelected = f.elect_coordinator("scope-a", candidate_node_ids=["new-coordinator"])
    assert reelected is not None, (
        "a TTL-expired lease from a dead coordinator must be re-electable -- if this "
        "is None, the permanent-starvation bug has regressed"
    )
    lease2, _token2 = reelected
    assert lease2["lease_id"] != lease1["lease_id"]
    assert lease2["node_id"] == "new-coordinator"

    # the old lease must actually be marked invalid now, not just bypassed
    snap = f.snapshot()
    old_row = [dict(l) for l in snap.leases if l["lease_id"] == lease1["lease_id"]][0]
    assert old_row["valid"] == 0


def test_non_expired_lease_still_blocks_election_as_before(tmp_path):
    f = Fabric(tmp_path / "s1.sqlite")
    f.seed_scope("scope-a")
    f.runtime_join("alive-coordinator", "reason", pid=1)
    elected = f.elect_coordinator("scope-a", candidate_node_ids=["alive-coordinator"])
    assert elected is not None

    f.runtime_join("other-node", "reason", pid=2)
    blocked = f.elect_coordinator("scope-a", candidate_node_ids=["other-node"])
    assert blocked is None, "a fresh, non-expired lease must still block re-election"
