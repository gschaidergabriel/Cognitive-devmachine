import os
import sqlite3
import tempfile
import unittest

from xeno_shared_state_boot_v1 import (
    COORDINATOR_LEASE_SCHEMA,
    COORDINATOR_POLICY_VERSION,
    CoordinatorLease,
    NodeResult,
    _sha256,
    capability_authority_binding,
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
        self.admitted = {
            "n1": ["REASON"],
            "c-a": ["REASON", "S1_COORDINATE"],
            "c-b": ["REASON", "S1_COORDINATE"],
        }
        self.binding = capability_authority_binding(self.admitted)
        self.genesis_snapshot = open_or_initialize(self.db_a, genesis_state=self.genesis)

    def tearDown(self):
        self.db_a.close()
        self.db_b.close()
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass

    def _lease(self, scope):
        return issue_coordinator_lease(
            self.db_a,
            node_id="c-b",
            scope=scope,
            admitted_capabilities_by_node=self.admitted,
            authority_binding_sha256=self.binding,
        )

    def _claim_and_make_result(self):
        lease = self._lease(["tasks"])
        tasks = [dict(row) for row in read_snapshot(self.db_a).state["tasks"]]
        tasks[0]["status"] = "IN_FLIGHT"
        tasks[0]["claimed_by"] = "n1"
        claimed = publish_delta(
            self.db_a,
            lease,
            node_id="c-b",
            delta={"tasks": tasks},
            expected_authority_binding_sha256=self.binding,
        )
        payload_sha = _sha256({"answer": 7})
        material = {
            "schema": "NODE_RESULT/v1",
            "node_id": "n1",
            "task_id": "t-high",
            "state_epoch": claimed.epoch,
            "state_digest": claimed.digest,
            "payload_ref": "mem://r1",
            "payload_sha256": payload_sha,
            "canonical_truth": False,
            "effect_authority": False,
        }
        return NodeResult(
            "NODE_RESULT/v1",
            _sha256(material),
            "n1",
            "t-high",
            claimed.epoch,
            claimed.digest,
            "mem://r1",
            payload_sha,
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

    def test_shared_snapshot_visible_from_second_connection_and_reopen_never_resets(self):
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
            COORDINATOR_POLICY_VERSION,
            self.binding,
        )
        with self.assertRaisesRegex(S1StoreError, "COORDINATOR_LEASE_IDENTITY_MISMATCH"):
            publish_delta(
                self.db_a,
                fake,
                node_id="c-b",
                delta={"workspace": {"branches": ["x"]}},
                expected_authority_binding_sha256=self.binding,
            )

        material = {
            "schema": COORDINATOR_LEASE_SCHEMA,
            "node_id": "c-b",
            "scope": ["workspace"],
            "state_epoch": snap.epoch,
            "state_digest": snap.digest,
            "policy_version": COORDINATOR_POLICY_VERSION,
            "authority_binding_sha256": self.binding,
        }
        internally_consistent_but_unadmitted = CoordinatorLease(
            COORDINATOR_LEASE_SCHEMA,
            _sha256(material),
            "c-b",
            ("workspace",),
            snap.epoch,
            snap.digest,
            COORDINATOR_POLICY_VERSION,
            self.binding,
        )
        with self.assertRaisesRegex(S1StoreError, "COORDINATOR_LEASE_NOT_ADMITTED"):
            publish_delta(
                self.db_a,
                internally_consistent_but_unadmitted,
                node_id="c-b",
                delta={"workspace": {"branches": ["x"]}},
                expected_authority_binding_sha256=self.binding,
            )

    def test_persisted_deterministic_lease_enables_one_cas_and_then_stales(self):
        with self.assertRaisesRegex(S1StoreError, "NODE_NOT_DETERMINISTIC_COORDINATOR"):
            issue_coordinator_lease(
                self.db_a,
                node_id="c-a",
                scope=["workspace"],
                admitted_capabilities_by_node=self.admitted,
                authority_binding_sha256=self.binding,
            )
        lease = self._lease(["workspace"])
        after = publish_delta(
            self.db_a,
            lease,
            node_id="c-b",
            delta={"workspace": {"branches": ["b1"]}},
            expected_authority_binding_sha256=self.binding,
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
                expected_authority_binding_sha256=self.binding,
            )

    def test_capability_authority_binding_mismatch_fails_closed(self):
        with self.assertRaisesRegex(S1StoreError, "COORDINATOR_AUTHORITY_BINDING_MISMATCH"):
            issue_coordinator_lease(
                self.db_a,
                node_id="c-b",
                scope=["workspace"],
                admitted_capabilities_by_node=self.admitted,
                authority_binding_sha256="0" * 64,
            )

    def test_gwt_broadcast_is_shared_consequence_visible_to_another_reader(self):
        lease = self._lease(["gwt"])
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
            expected_authority_binding_sha256=self.binding,
        )
        other = read_snapshot(self.db_b)
        self.assertEqual(after.digest, other.digest)
        self.assertEqual("g1", other.state["gwt"]["broadcast"][0]["broadcast_id"])

    def test_result_ingestion_is_scoped_coordinator_only_and_idempotent(self):
        result = self._claim_and_make_result()
        no_results_scope = self._lease(["workspace"])
        with self.assertRaisesRegex(S1StoreError, "COORDINATOR_LEASE_SCOPE_REQUIRED:results"):
            ingest_node_result(
                self.db_a,
                no_results_scope,
                coordinator_node_id="c-b",
                result=result,
                expected_authority_binding_sha256=self.binding,
            )

        lease = self._lease(["results"])
        first = ingest_node_result(
            self.db_a,
            lease,
            coordinator_node_id="c-b",
            result=result,
            expected_authority_binding_sha256=self.binding,
        )
        second = ingest_node_result(
            self.db_a,
            lease,
            coordinator_node_id="c-b",
            result=result,
            expected_authority_binding_sha256=self.binding,
        )
        self.assertFalse(first["idempotent"])
        self.assertTrue(second["idempotent"])
        rows = list_ingested_results(
            self.db_b,
            lease,
            coordinator_node_id="c-b",
            expected_authority_binding_sha256=self.binding,
        )
        self.assertEqual([result.result_id], [row["result_id"] for row in rows])

    def test_result_identity_mismatch_fails_closed(self):
        result = self._claim_and_make_result()
        bad = NodeResult(
            result.schema,
            "0" * 64,
            result.node_id,
            result.task_id,
            result.state_epoch,
            result.state_digest,
            result.payload_ref,
            result.payload_sha256,
        )
        lease = self._lease(["results"])
        with self.assertRaisesRegex(S1StoreError, "NODE_RESULT_IDENTITY_MISMATCH"):
            ingest_node_result(
                self.db_a,
                lease,
                coordinator_node_id="c-b",
                result=bad,
                expected_authority_binding_sha256=self.binding,
            )

    def test_old_result_is_rejected_after_state_epoch_changes(self):
        old_result = self._claim_and_make_result()
        lease1 = self._lease(["workspace"])
        publish_delta(
            self.db_a,
            lease1,
            node_id="c-b",
            delta={"workspace": {"branches": ["new"]}},
            expected_authority_binding_sha256=self.binding,
        )
        lease2 = self._lease(["results"])
        with self.assertRaisesRegex(S1StoreError, "STALE_NODE_RESULT"):
            ingest_node_result(
                self.db_a,
                lease2,
                coordinator_node_id="c-b",
                result=old_result,
                expected_authority_binding_sha256=self.binding,
            )

    def test_persisted_state_digest_tamper_fails_closed(self):
        self.db_a.execute("UPDATE hcu_s1_state SET state_json=? WHERE slot=1", ('{"tasks":[]}',))
        self.db_a.commit()
        with self.assertRaisesRegex(S1StoreError, "S1_PERSISTED_DIGEST_MISMATCH"):
            read_snapshot(self.db_a)


if __name__ == "__main__":
    unittest.main()
