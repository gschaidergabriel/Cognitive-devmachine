from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from grid10_fabric import Fabric, connect, result_packet
from grid10_outbox_recovery_v1 import reconcile_admitted_outbox


def _seed(tmp_path: Path):
    db = tmp_path / "fabric.sqlite"
    f = Fabric(db)
    f.seed_scope("A")
    f.runtime_join("n1", "general", 1001)
    f.runtime_join("n2", "general", 1002)
    snap = f.snapshot()
    packet = result_packet("n1", snap, "A", {"task_id": "t1", "value": 7})
    f.emit_node_result(packet)
    election = f.elect_coordinator("A", ["n2"])
    assert election is not None
    lease, token = election
    snap2 = f.snapshot()
    delta = f.coordinator_commit(
        lease=lease,
        token=token,
        packet=packet,
        expected_epoch=snap2.epoch,
        expected_digest=snap2.state_digest,
    )
    return db, f, packet, delta


def test_repairs_post_commit_pre_consumed_crash_window(tmp_path):
    db, f, packet, delta = _seed(tmp_path)
    before = f.snapshot()
    con = connect(db)
    try:
        pending = con.execute("SELECT consumed FROM outbox WHERE packet_digest=?", (packet["packet_digest"],)).fetchone()
        assert pending["consumed"] == 0
        assert con.execute("SELECT 1 FROM admitted_results WHERE result_digest=?", (packet["packet_digest"],)).fetchone()
    finally:
        con.close()

    receipt = reconcile_admitted_outbox(db)
    after = f.snapshot()
    assert receipt["pass"] is True
    assert receipt["repaired"] == [packet["packet_digest"]]
    assert after.epoch == before.epoch
    assert after.state_digest == before.state_digest

    con = connect(db)
    try:
        row = con.execute("SELECT consumed FROM outbox WHERE packet_digest=?", (packet["packet_digest"],)).fetchone()
        assert row["consumed"] == 1
        count = con.execute("SELECT COUNT(*) AS n FROM admitted_results WHERE result_digest=?", (packet["packet_digest"],)).fetchone()["n"]
        assert count == 1
    finally:
        con.close()


def test_unadmitted_pending_packet_is_not_consumed(tmp_path):
    db = tmp_path / "fabric.sqlite"
    f = Fabric(db)
    f.seed_scope("A")
    f.runtime_join("n1", "general", 1001)
    packet = result_packet("n1", f.snapshot(), "A", {"task_id": "t1"})
    f.emit_node_result(packet)
    receipt = reconcile_admitted_outbox(db)
    assert receipt["pass"] is True
    assert receipt["repaired"] == []
    con = connect(db)
    try:
        assert con.execute("SELECT consumed FROM outbox WHERE packet_digest=?", (packet["packet_digest"],)).fetchone()["consumed"] == 0
    finally:
        con.close()


def test_scope_mismatch_fails_closed_and_repairs_nothing(tmp_path):
    db, f, packet, _ = _seed(tmp_path)
    con = connect(db)
    try:
        con.execute("BEGIN IMMEDIATE")
        con.execute("UPDATE admitted_results SET scope='B' WHERE result_digest=?", (packet["packet_digest"],))
        con.execute("COMMIT")
    finally:
        con.close()
    receipt = reconcile_admitted_outbox(db)
    assert receipt["pass"] is False
    assert receipt["repaired"] == []
    assert receipt["conflicts"] == [packet["packet_digest"]]
    con = connect(db)
    try:
        assert con.execute("SELECT consumed FROM outbox WHERE packet_digest=?", (packet["packet_digest"],)).fetchone()["consumed"] == 0
    finally:
        con.close()


def test_idempotent_recovery(tmp_path):
    db, f, packet, _ = _seed(tmp_path)
    first = reconcile_admitted_outbox(db)
    second = reconcile_admitted_outbox(db)
    assert first["repaired"] == [packet["packet_digest"]]
    assert second["repaired"] == []
