from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from grid10_fabric import Fabric, FabricError, connect, result_packet
from grid10_decode_safe_node_wrapper_v1 import DecodeSafeFabric


def _post_admission_pre_consumed_window(tmp_path: Path):
    db = tmp_path / "fabric.sqlite"
    retained = Fabric(db)
    retained.seed_scope("A")
    retained.runtime_join("worker", "general", 1001)
    retained.runtime_join("coord-old", "general", 1002)
    retained.runtime_join("coord-new", "general", 1003)

    packet = result_packet("worker", retained.snapshot(), "A", {"task_id": "t1", "value": 7})
    retained.emit_node_result(packet)
    elected = retained.elect_coordinator("A", ["coord-old"])
    assert elected is not None
    old_lease, old_token = elected

    # Deliberately reproduce the real crash window: admission commits, but the
    # separate outbox consumed ACK never runs because the old coordinator dies here.
    snap = retained.snapshot()
    retained.coordinator_commit(
        lease=old_lease,
        token=old_token,
        packet=packet,
        expected_epoch=snap.epoch,
        expected_digest=snap.state_digest,
    )

    con = connect(db)
    try:
        assert con.execute(
            "SELECT consumed FROM outbox WHERE packet_digest=?", (packet["packet_digest"],)
        ).fetchone()["consumed"] == 0
        assert con.execute(
            "SELECT COUNT(*) AS n FROM admitted_results WHERE result_digest=?", (packet["packet_digest"],)
        ).fetchone()["n"] == 1
    finally:
        con.close()

    # Model a hard-dead coordinator becoming ineligible. Lease-expiry is covered by
    # the retained election tests; here we isolate the post-admission recovery law.
    retained.revoke_lease(old_lease["lease_id"])
    elected2 = retained.elect_coordinator("A", ["coord-new"])
    assert elected2 is not None
    new_lease, new_token = elected2
    return db, retained, packet, new_lease, new_token


def test_replacement_coordinator_automatically_converges_exactly_once(tmp_path):
    db, retained, packet, new_lease, new_token = _post_admission_pre_consumed_window(tmp_path)
    safe = DecodeSafeFabric(db)
    before = safe.snapshot()

    drained = safe.coordinator_drain_and_commit("A", new_lease, new_token)
    after = safe.snapshot()

    assert drained == []
    receipt = safe.last_outbox_recovery_receipt()
    assert receipt is not None
    assert receipt["pass"] is True
    assert receipt["repaired"] == [packet["packet_digest"]]
    # Recovery changes only Result-Channel bookkeeping, never cognitive S1.
    assert after.epoch == before.epoch
    assert after.state_digest == before.state_digest

    con = connect(db)
    try:
        assert con.execute(
            "SELECT consumed FROM outbox WHERE packet_digest=?", (packet["packet_digest"],)
        ).fetchone()["consumed"] == 1
        assert con.execute(
            "SELECT COUNT(*) AS n FROM admitted_results WHERE result_digest=?", (packet["packet_digest"],)
        ).fetchone()["n"] == 1
    finally:
        con.close()

    # Identical replay is +0: no second S1 admit and no epoch movement.
    replay_before = safe.snapshot()
    assert safe.coordinator_drain_and_commit("A", new_lease, new_token) == []
    replay_after = safe.snapshot()
    assert replay_after.epoch == replay_before.epoch
    assert replay_after.state_digest == replay_before.state_digest


def test_scope_transplant_fails_closed_before_retained_drain(tmp_path):
    db, retained, packet, new_lease, new_token = _post_admission_pre_consumed_window(tmp_path)
    con = connect(db)
    try:
        con.execute("BEGIN IMMEDIATE")
        con.execute(
            "UPDATE admitted_results SET scope='B' WHERE result_digest=?", (packet["packet_digest"],)
        )
        con.execute("COMMIT")
    finally:
        con.close()

    safe = DecodeSafeFabric(db)
    before = safe.snapshot()
    with pytest.raises(FabricError, match="OUTBOX_CRASH_RECOVERY_CONFLICT"):
        safe.coordinator_drain_and_commit("A", new_lease, new_token)
    after = safe.snapshot()
    assert after.epoch == before.epoch
    assert after.state_digest == before.state_digest

    con = connect(db)
    try:
        assert con.execute(
            "SELECT consumed FROM outbox WHERE packet_digest=?", (packet["packet_digest"],)
        ).fetchone()["consumed"] == 0
    finally:
        con.close()
