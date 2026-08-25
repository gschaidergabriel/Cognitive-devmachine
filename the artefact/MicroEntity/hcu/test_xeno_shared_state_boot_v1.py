import unittest

from xeno_shared_state_boot_v1 import NodeDescriptor, S1StateFabric, SharedStateError


def base_state():
    return {
        "tasks": [
            {"task_id": "t-low", "priority": 1, "required_capabilities": ["REASON"], "status": "PENDING", "claimed_by": None},
            {"task_id": "t-high", "priority": 9, "required_capabilities": ["REASON"], "status": "PENDING", "claimed_by": None},
            {"task_id": "t-claimed", "priority": 99, "required_capabilities": ["REASON"], "status": "IN_FLIGHT", "claimed_by": "n9"},
        ],
        "workspace": {"branches": []},
        "gwt": {"broadcast": []},
    }


class SharedStateBootTests(unittest.TestCase):
    def setUp(self):
        self.fabric = S1StateFabric(base_state())
        self.worker = NodeDescriptor.admit("n1", ["REASON"])
        self.coord_a = NodeDescriptor.admit("c-a", ["REASON", "S1_COORDINATE"], load_milli=30)
        self.coord_b = NodeDescriptor.admit("c-b", ["REASON", "S1_COORDINATE"], load_milli=10)

    def test_autonomous_boot_is_ordinary_and_selects_needed_work(self):
        boot = self.fabric.autonomous_boot(self.worker, admitted_capabilities=["REASON"])
        self.assertEqual("ORDINARY", boot.role)
        self.assertEqual("t-high", boot.selected_task_id)
        self.assertEqual(self.fabric.read_snapshot().digest, boot.state_digest)

    def test_capability_self_grant_fails_closed(self):
        privileged = NodeDescriptor.admit("n2", ["REASON", "S1_COORDINATE"])
        with self.assertRaisesRegex(SharedStateError, "NODE_CAPABILITY_NOT_ADMITTED"):
            self.fabric.autonomous_boot(privileged, admitted_capabilities=["REASON"])

    def test_snapshot_is_copy_not_hidden_mutable_state(self):
        snap = self.fabric.read_snapshot()
        snap.state["tasks"][0]["priority"] = 999
        self.assertEqual(1, self.fabric.read_snapshot().state["tasks"][0]["priority"])
        self.assertEqual(snap.digest, self.fabric.read_snapshot().digest)

    def test_ordinary_node_write_is_hard_denied(self):
        with self.assertRaisesRegex(SharedStateError, "ORDINARY_NODE_S1_WRITE_FORBIDDEN"):
            self.fabric.publish_from_ordinary({"workspace": {"x": 1}})

    def test_node_result_binds_state_and_becomes_stale_after_s1_change(self):
        boot = self.fabric.autonomous_boot(self.worker, admitted_capabilities=["REASON"])
        result = self.fabric.emit_node_result(boot, task_id="t-high", payload_ref="mem://r1", payload={"answer": 7})
        self.fabric.validate_result_current(result)
        lease = self.fabric.issue_coordinator_lease(self.coord_b, nodes=[self.coord_a, self.coord_b], scope=["workspace"])
        self.fabric.publish_delta(lease, node_id="c-b", delta={"workspace": {"branches": ["b1"]}})
        with self.assertRaisesRegex(SharedStateError, "STALE_NODE_RESULT"):
            self.fabric.validate_result_current(result)

    def test_coordinator_selection_is_deterministic_and_order_independent(self):
        self.assertEqual("c-b", self.fabric.select_coordinator([self.coord_a, self.coord_b]).node_id)
        self.assertEqual("c-b", self.fabric.select_coordinator([self.coord_b, self.coord_a]).node_id)

    def test_only_selected_leased_coordinator_can_write_scoped_s1(self):
        with self.assertRaisesRegex(SharedStateError, "NODE_NOT_DETERMINISTIC_COORDINATOR"):
            self.fabric.issue_coordinator_lease(self.coord_a, nodes=[self.coord_a, self.coord_b], scope=["workspace"])
        lease = self.fabric.issue_coordinator_lease(self.coord_b, nodes=[self.coord_a, self.coord_b], scope=["workspace"])
        with self.assertRaisesRegex(SharedStateError, "COORDINATOR_LEASE_NODE_MISMATCH"):
            self.fabric.publish_delta(lease, node_id="c-a", delta={"workspace": {"branches": ["x"]}})
        with self.assertRaisesRegex(SharedStateError, "S1_DELTA_OUT_OF_SCOPE"):
            self.fabric.publish_delta(lease, node_id="c-b", delta={"gwt": {"broadcast": ["x"]}})
        before = self.fabric.read_snapshot()
        after = self.fabric.publish_delta(lease, node_id="c-b", delta={"workspace": {"branches": ["x"]}})
        self.assertEqual(before.epoch + 1, after.epoch)
        self.assertNotEqual(before.digest, after.digest)
        with self.assertRaisesRegex(SharedStateError, "STALE_COORDINATOR_LEASE"):
            self.fabric.publish_delta(lease, node_id="c-b", delta={"workspace": {"branches": ["y"]}})

    def test_s1_cannot_smuggle_s0_authority(self):
        with self.assertRaisesRegex(SharedStateError, "S1_FORBIDDEN_ROOT"):
            S1StateFabric({"canonical": {"truth": True}, "tasks": []})
        with self.assertRaisesRegex(SharedStateError, "LEASE_SCOPE_CANNOT_GRANT_S0_AUTHORITY"):
            self.fabric.issue_coordinator_lease(self.coord_b, nodes=[self.coord_b], scope=["effects"])


if __name__ == "__main__":
    unittest.main()
