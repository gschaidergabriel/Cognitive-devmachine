import unittest

from xeno_shared_state_boot_v1 import (
    NodeDescriptor,
    S1StateFabric,
    SharedStateError,
    capability_authority_binding,
)


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
        self.admitted = {
            "n1": ["REASON"],
            "c-a": ["REASON", "S1_COORDINATE"],
            "c-b": ["REASON", "S1_COORDINATE"],
        }
        self.binding = capability_authority_binding(self.admitted)

    def _lease(self, scope):
        return self.fabric.issue_coordinator_lease(
            self.coord_b,
            nodes=[self.coord_a, self.coord_b],
            scope=scope,
            admitted_capabilities_by_node=self.admitted,
            authority_binding_sha256=self.binding,
        )

    def test_autonomous_boot_is_ordinary_and_selects_needed_work(self):
        boot = self.fabric.autonomous_boot(self.worker, admitted_capabilities=["REASON"])
        self.assertEqual("ORDINARY", boot.role)
        self.assertEqual("t-high", boot.selected_task_id)
        self.assertEqual("HIGHEST_PRIORITY_CAPABLE_UNCLAIMED", boot.selection_reason)
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

    def test_node_result_requires_coordinator_claim_then_rejoin(self):
        boot = self.fabric.autonomous_boot(self.worker, admitted_capabilities=["REASON"])
        with self.assertRaisesRegex(SharedStateError, "NODE_RESULT_REQUIRES_COORDINATOR_ADMITTED_CLAIM"):
            self.fabric.emit_node_result(boot, task_id="t-high", payload_ref="mem://r0", payload={"answer": 0})

        lease = self._lease(["tasks"])
        claimed_tasks = [dict(row) for row in self.fabric.read_snapshot().state["tasks"]]
        for row in claimed_tasks:
            if row["task_id"] == "t-high":
                row["status"] = "IN_FLIGHT"
                row["claimed_by"] = "n1"
        self.fabric.publish_delta(
            lease,
            node_id="c-b",
            delta={"tasks": claimed_tasks},
            expected_authority_binding_sha256=self.binding,
        )

        resumed = self.fabric.autonomous_boot(self.worker, admitted_capabilities=["REASON"])
        self.assertEqual("t-high", resumed.selected_task_id)
        self.assertEqual("RESUME_OWN_COORDINATOR_CLAIM", resumed.selection_reason)
        result = self.fabric.emit_node_result(
            resumed,
            task_id="t-high",
            payload_ref="mem://r1",
            payload={"answer": 7},
        )
        self.fabric.validate_result_current(result)

        lease2 = self._lease(["workspace"])
        self.fabric.publish_delta(
            lease2,
            node_id="c-b",
            delta={"workspace": {"branches": ["b1"]}},
            expected_authority_binding_sha256=self.binding,
        )
        with self.assertRaisesRegex(SharedStateError, "STALE_NODE_RESULT"):
            self.fabric.validate_result_current(result)

    def test_node_result_cannot_switch_task_from_boot_selection(self):
        boot = self.fabric.autonomous_boot(self.worker, admitted_capabilities=["REASON"])
        with self.assertRaisesRegex(SharedStateError, "TASK_MUST_MATCH_BOOT_SELECTION"):
            self.fabric.emit_node_result(boot, task_id="t-low", payload_ref="mem://r", payload={"x": 1})

    def test_coordinator_selection_is_deterministic_and_order_independent(self):
        first = self.fabric.select_coordinator(
            [self.coord_a, self.coord_b],
            admitted_capabilities_by_node=self.admitted,
        )
        second = self.fabric.select_coordinator(
            [self.coord_b, self.coord_a],
            admitted_capabilities_by_node=self.admitted,
        )
        self.assertEqual("c-b", first.node_id)
        self.assertEqual("c-b", second.node_id)

    def test_self_declared_coordinator_capability_without_external_admission_is_rejected(self):
        rogue = NodeDescriptor.admit("rogue", ["S1_COORDINATE"], load_milli=0)
        admitted = dict(self.admitted)
        admitted["rogue"] = []
        with self.assertRaisesRegex(SharedStateError, "NODE_NOT_DETERMINISTIC_COORDINATOR|NO_ELIGIBLE_COORDINATOR"):
            self.fabric.issue_coordinator_lease(
                rogue,
                nodes=[rogue],
                scope=["workspace"],
                admitted_capabilities_by_node=admitted,
                authority_binding_sha256=capability_authority_binding(admitted),
            )

    def test_only_selected_leased_coordinator_can_write_scoped_s1(self):
        with self.assertRaisesRegex(SharedStateError, "NODE_NOT_DETERMINISTIC_COORDINATOR"):
            self.fabric.issue_coordinator_lease(
                self.coord_a,
                nodes=[self.coord_a, self.coord_b],
                scope=["workspace"],
                admitted_capabilities_by_node=self.admitted,
                authority_binding_sha256=self.binding,
            )
        lease = self._lease(["workspace"])
        with self.assertRaisesRegex(SharedStateError, "COORDINATOR_LEASE_NODE_MISMATCH"):
            self.fabric.publish_delta(
                lease,
                node_id="c-a",
                delta={"workspace": {"branches": ["x"]}},
                expected_authority_binding_sha256=self.binding,
            )
        with self.assertRaisesRegex(SharedStateError, "S1_DELTA_OUT_OF_SCOPE"):
            self.fabric.publish_delta(
                lease,
                node_id="c-b",
                delta={"gwt": {"broadcast": ["x"]}},
                expected_authority_binding_sha256=self.binding,
            )
        before = self.fabric.read_snapshot()
        after = self.fabric.publish_delta(
            lease,
            node_id="c-b",
            delta={"workspace": {"branches": ["x"]}},
            expected_authority_binding_sha256=self.binding,
        )
        self.assertEqual(before.epoch + 1, after.epoch)
        self.assertNotEqual(before.digest, after.digest)
        with self.assertRaisesRegex(SharedStateError, "STALE_COORDINATOR_LEASE"):
            self.fabric.publish_delta(
                lease,
                node_id="c-b",
                delta={"workspace": {"branches": ["y"]}},
                expected_authority_binding_sha256=self.binding,
            )

    def test_s1_cannot_smuggle_s0_authority_at_root_or_nested(self):
        with self.assertRaisesRegex(SharedStateError, "S1_FORBIDDEN_AUTHORITY_FIELD"):
            S1StateFabric({"canonical": {"truth": True}, "tasks": []})
        with self.assertRaisesRegex(SharedStateError, "S1_FORBIDDEN_AUTHORITY_FIELD"):
            S1StateFabric({"tasks": [], "workspace": {"effect_authority": True}})
        with self.assertRaisesRegex(SharedStateError, "LEASE_SCOPE_CANNOT_GRANT_S0_AUTHORITY"):
            self.fabric.issue_coordinator_lease(
                self.coord_b,
                nodes=[self.coord_b],
                scope=["effect_authority"],
                admitted_capabilities_by_node=self.admitted,
                authority_binding_sha256=self.binding,
            )

    def test_coordinator_authority_binding_mismatch_fails_closed(self):
        with self.assertRaisesRegex(SharedStateError, "COORDINATOR_AUTHORITY_BINDING_MISMATCH"):
            self.fabric.issue_coordinator_lease(
                self.coord_b,
                nodes=[self.coord_b],
                scope=["workspace"],
                admitted_capabilities_by_node=self.admitted,
                authority_binding_sha256="0" * 64,
            )
        lease = self._lease(["workspace"])
        with self.assertRaisesRegex(SharedStateError, "COORDINATOR_LEASE_AUTHORITY_BINDING_MISMATCH"):
            self.fabric.publish_delta(
                lease,
                node_id="c-b",
                delta={"workspace": {"branches": ["x"]}},
                expected_authority_binding_sha256="0" * 64,
            )


if __name__ == "__main__":
    unittest.main()
