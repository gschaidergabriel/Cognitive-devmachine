import os
import sqlite3
import tempfile
import unittest

from xeno_shared_state_boot_v1 import (
    COORDINATOR_LEASE_SCHEMA,
    CoordinatorLease,
    NodeDescriptor,
    S1StateFabric,
    _sha256,
)
from xeno_s1_sqlite_cas_v1 import (
    S1StoreError,
    ingest_node_result,
    issue_coordinator_lease,
    list_ingested_results,
    open_or_initialize,
    publish_delta,
    read_snapshot,
)


def base_state():
    return {
        "nodes": [
            {"node_id": "n1", "capabilities": ["REASON"], "healthy": True, "load_milli": 5},
            {"node_id": "c-a", "capabilities": ["REASON", "S1_COORDINATE"], "healthy": True, "load_milli": 30},
            {"node_id": "c-b", "capabilities": ["REASON", "S1_COORDINATE"], "healthy": True, "load_milli": 10},
        ],
        "tasks": [
            {"task_id": "t-high", "priority": 9, "required_capabilities": ["REASON"], "status": "PENDING", "claimed_by": None},
        ],
        "workspace": {"branches": []},
        "gwt": {"broadcast": [], "uptake": [], "reentry": []},
    }


class PersistentS1CASTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(prefix="xeno-s1-", suffix=".sqlite3")
        os.close(fd)
        self.db_a = sqlite3.connect(self.path)
        self.db_b = sqlite3.connect(self.path)
        self.genesis = base_state()
        self.genesis_snapshot = open_or_initialize(self.db_a, genesis_state=self.genesis)
        self.worker = NodeDescriptor.admit("n1", ["REASON"])
        self.logic = S1StateFabric(self.genesis)

    def tearDown(self):
        self.db_a.close()
        self.db_b.close()
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass

    def _result(self):
        boot = self.logic.autonomous_boot(self.worker, admitted_capabilities=["REASON"])
        return self.logic.emit_node_result(
            boot,
            task_id="t-high",
            payload_ref="mem://r1",
            payload={"answer": 7},
        )

    def test_ordinary_read_path_never_installs_schema(self):
        fd, path = tempfile.mkstemp(prefix="xeno-empty-", suffix=".sqlite3")
        os.close(fd)
        db = sqlite3.connect(path)
        try:
            before = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            with self.assertRaisesRegex(S1StoreError, "S1_STORE_UNINITIALIZED"):
                read_snapshot(db)
            after = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            self.assertEqual(before, after)
        finally:
            db.close()
            os.unlink(path)

    def test_shared_snapshot_is_visible_from_second_connection_and_reopen_never_resets(self):
        observed = read_snapshot(self.db_b)
        self.assertEqual(self.genesis_snapshot.epoch, observed.epoch)
        self.assertEqual(self.genesis_snapshot.digest, observed.digest)
        reopened = open_or_initialize(self.db_b)
        self.assertEqual(observed.digest, reopened.digest)

    def test_forged_or_unadmitted_lease_is_rejected(self):
        snap = read_snapshot(self.db_a)
        fake = CoordinatorLease(
            COORDINATOR_LEASE_SCHEMA,
            "0" * 64,
            "c-b",
            ("workspace",),
            snap.epoch,
            snap.digest,
        )
        with self.assertRaisesRegex(S1StoreError, "COORDINATOR_LEASE_IDENTITY_MISMATCH"):
            publish_delta(self.db_a, fake, node_id="c-b", delta={"workspace": {"branches": ["x"]}})

        material = {
            "schema": COORDINATOR_LEASE_SCHEMA,
            "node_id": "c-b",
            "scope": ["workspace"],
            "state_epoch": snap.epoch,
            "state_digest": snap.digest,
        }
        internally_consistent_but_unadmitted = CoordinatorLease(
            COORDINATOR_LEASE_SCHEMA,
            _sha256(material),
            "c-b",
            ("workspace",),
            snap.epoch,
            snap.digest,
        )
        with self.assertRaisesRegex(S1StoreError, "COORDINATOR_LEASE_NOT_ADMITTED"):
            publish_delta(
                self.db_a,
                internally_consistent_but_unadmitted,
                node_id="c-b",
                delta={"workspace": {"branches": ["x"]}},
            )

    def test_persisted_deterministic_lease_enables_one_cas_and_then_stales(self):
        with self.assertRaisesRegex(S1StoreError, "NODE_NOT_DETERMINISTIC_COORDINATOR"):
            issue_coordinator_lease(self.db_a, node_id="c-a", scope=["workspace"])
        lease = issue_coordinator_lease(self.db_a, node_id="c-b", scope=["workspace"])
        after = publish_delta(
            self.db_a,
            lease,
            node_id="c-b",
            delta={"workspace": {"branches": ["b1"]}},
        )
        observed = read_snapshot(self.db_b)
        self.assertEqual(after.epoch, observed.epoch)
        self.assertEqual(after.digest, observed.digest)
        with self.assertRaisesRegex(S1StoreError, "STALE_COORDINATOR_LEASE"):
            publish_delta(
                self.db_b,
                lease,
                node_id="c-b",
                delta={"workspace": {"branches": ["b2"]}},
            )

    def test_gwt_broadcast_is_shared_consequence_visible_to_another_reader(self):
        lease = issue_coordinator_lease(self.db_a, node_id="c-b", scope=["gwt"])
        after = publish_delta(
            self.db_a,
            lease,
            node_id="c-b",
            delta={
                "gwt": {
                    "broadcast": [{"broadcast_id": "g1", "content_ref": "mem://g1"}],
                    "uptake": [],
                    "reentry": [],
                }
            },
        )
        other = read_snapshot(self.db_b)
        self.assertEqual(after.digest, other.digest)
        self.assertEqual("g1", other.state["gwt"]["broadcast"][0]["broadcast_id"])

    def test_result_ingestion_is_scoped_coordinator_only_and_idempotent(self):
        result = self._result()
        no_results_scope = issue_coordinator_lease(self.db_a, node_id="c-b", scope=["workspace"])
        with self.assertRaisesRegex(S1StoreError, "COORDINATOR_LEASE_SCOPE_REQUIRED:results"):
            ingest_node_result(
                self.db_a,
                no_results_scope,
                coordinator_node_id="c-b",
                result=result,
            )

        lease = issue_coordinator_lease(self.db_a, node_id="c-b", scope=["results"])
        first = ingest_node_result(self.db_a, lease, coordinator_node_id="c-b", result=result)
        second = ingest_node_result(self.db_a, lease, coordinator_node_id="c-b", result=result)
        self.assertFalse(first["idempotent"])
        self.assertTrue(second["idempotent"])
        rows = list_ingested_results(self.db_b, lease, coordinator_node_id="c-b")
        self.assertEqual([result.result_id], [row["result_id"] for row in rows])

    def test_old_result_is_rejected_after_state_epoch_changes(self):
        old_result = self._result()
        lease0 = issue_coordinator_lease(self.db_a, node_id="c-b", scope=["workspace"])
        publish_delta(
            self.db_a,
            lease0,
            node_id="c-b",
            delta={"workspace": {"branches": ["new"]}},
        )
        lease1 = issue_coordinator_lease(self.db_a, node_id="c-b", scope=["results"])
        with self.assertRaisesRegex(S1StoreError, "STALE_NODE_RESULT"):
            ingest_node_result(self.db_a, lease1, coordinator_node_id="c-b", result=old_result)

    def test_persisted_state_digest_tamper_fails_closed(self):
        self.db_a.execute("UPDATE hcu_s1_state SET state_json=? WHERE slot=1", ('{"tasks":[]}',))
        self.db_a.commit()
        with self.assertRaisesRegex(S1StoreError, "S1_PERSISTED_DIGEST_MISMATCH"):
            read_snapshot(self.db_a)


if __name__ == "__main__":
    unittest.main()
