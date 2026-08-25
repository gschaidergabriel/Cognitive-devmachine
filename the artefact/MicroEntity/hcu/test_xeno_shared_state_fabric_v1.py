import unittest

from xeno_shared_state_fabric_v1 import (
    SharedStateError,
    WorkItem,
    HyperpositionBranchRef,
    GWTBroadcastRef,
    make_snapshot,
    validate_snapshot,
    boot_node,
    select_work,
    emit_node_result,
    grant_coordinator_lease,
    commit_s1_delta,
)

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64
F = "f" * 64


class SharedStateFabricTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = make_snapshot(
            generation=7,
            epoch=11,
            policy_sha256=A,
            work_items=(
                WorkItem("task-low", "branch-0", 1, "blob:low", B),
                WorkItem("task-high", "branch-1", 9, "blob:high", C),
            ),
            hyperposition_branches=(HyperpositionBranchRef("branch-1", D, "UNRESOLVED"),),
        )
        self.authority = {
            "node-a": ("hcu.s1.read", "hcu.coordinate.eligible"),
            "node-b": ("hcu.s1.read", "hcu.coordinate.eligible"),
            "node-c": ("hcu.s1.read",),
        }
        self.sessions = {
            node: boot_node(
                self.snapshot,
                node_id=node,
                current_generation=7,
                capability_binding_sha256=E,
                admitted_capabilities_by_node=self.authority,
            )
            for node in self.authority
        }

    def test_autonomous_boot_and_work_selection_no_fixed_role(self):
        session = self.sessions["node-c"]
        selected = select_work(self.snapshot, session)
        self.assertEqual(selected.task_id, "task-high")
        self.assertEqual(selected.branch_id, "branch-1")
        self.assertNotIn("hcu.coordinate.eligible", session.capabilities)

    def test_coordinator_selection_is_order_independent(self):
        one = grant_coordinator_lease(
            self.snapshot,
            [self.sessions["node-a"], self.sessions["node-b"]],
            scope="grid10/global",
            policy_sha256=A,
        )
        two = grant_coordinator_lease(
            self.snapshot,
            [self.sessions["node-b"], self.sessions["node-a"]],
            scope="grid10/global",
            policy_sha256=A,
        )
        self.assertEqual(one.node_id, two.node_id)
        self.assertEqual(one.lease_sha256, two.lease_sha256)

    def test_ordinary_node_cannot_write_s1_without_lease(self):
        with self.assertRaisesRegex(SharedStateError, "NO_VALID_COORDINATOR_LEASE_NO_S1_WRITE"):
            commit_s1_delta(self.snapshot, self.sessions["node-c"], None)

    def test_non_coordinator_cannot_use_other_nodes_lease(self):
        lease = grant_coordinator_lease(
            self.snapshot,
            [self.sessions["node-a"], self.sessions["node-b"]],
            scope="grid10/global",
            policy_sha256=A,
        )
        other = self.sessions["node-b"] if lease.node_id == "node-a" else self.sessions["node-a"]
        with self.assertRaisesRegex(SharedStateError, "COORDINATOR_LEASE_ACTOR_MISMATCH"):
            commit_s1_delta(self.snapshot, other, lease)

    def test_node_result_is_snapshot_bound_and_commit_is_cas(self):
        worker = self.sessions["node-c"]
        selection = select_work(self.snapshot, worker)
        result = emit_node_result(
            self.snapshot,
            worker,
            selection,
            payload_ref="result:task-high",
            payload_sha256=F,
            evidence_refs=(B, C),
        )
        lease = grant_coordinator_lease(
            self.snapshot,
            [self.sessions["node-a"], self.sessions["node-b"]],
            scope="grid10/global",
            policy_sha256=A,
        )
        coordinator = self.sessions[lease.node_id]
        updated_work = WorkItem("task-high", "branch-1", 9, "blob:high", C, "DONE", lease.node_id)
        new_snapshot, receipt = commit_s1_delta(
            self.snapshot,
            coordinator,
            lease,
            consumed_results=(result,),
            work_updates=(updated_work,),
            hyperposition_updates=(HyperpositionBranchRef("branch-2", B, "UNRESOLVED"),),
            gwt_broadcasts=(
                GWTBroadcastRef("broadcast-1", C, ("node-a", "node-c"), ("node-c",)),
            ),
        )
        self.assertEqual(new_snapshot.epoch, self.snapshot.epoch + 1)
        self.assertEqual(new_snapshot.previous_snapshot_sha256, self.snapshot.snapshot_sha256)
        self.assertEqual(receipt.new_snapshot_sha256, new_snapshot.snapshot_sha256)
        self.assertIn(result.result_sha256, receipt.consumed_result_sha256)
        self.assertEqual(validate_snapshot(new_snapshot), new_snapshot.snapshot_sha256)
        self.assertEqual(
            {b.branch_id for b in new_snapshot.hyperposition_branches},
            {"branch-1", "branch-2"},
        )
        self.assertEqual(new_snapshot.gwt_broadcasts[0].broadcast_id, "broadcast-1")

    def test_old_lease_and_session_fail_after_commit(self):
        lease = grant_coordinator_lease(
            self.snapshot,
            [self.sessions["node-a"], self.sessions["node-b"]],
            scope="grid10/global",
            policy_sha256=A,
        )
        coordinator = self.sessions[lease.node_id]
        new_snapshot, _ = commit_s1_delta(self.snapshot, coordinator, lease)
        with self.assertRaisesRegex(SharedStateError, "NODE_SESSION_STALE_S1_VIEW"):
            commit_s1_delta(new_snapshot, coordinator, lease)
        with self.assertRaisesRegex(SharedStateError, "NODE_SESSION_STALE_S1_VIEW"):
            select_work(new_snapshot, self.sessions["node-c"])

    def test_rejoin_and_coordinator_replacement_on_new_epoch(self):
        lease = grant_coordinator_lease(
            self.snapshot,
            [self.sessions["node-a"], self.sessions["node-b"]],
            scope="grid10/global",
            policy_sha256=A,
        )
        coordinator = self.sessions[lease.node_id]
        new_snapshot, _ = commit_s1_delta(self.snapshot, coordinator, lease)
        refreshed = {
            node: boot_node(
                new_snapshot,
                node_id=node,
                current_generation=7,
                capability_binding_sha256=E,
                admitted_capabilities_by_node=self.authority,
            )
            for node in ("node-a", "node-b")
        }
        replacement = [session for node, session in refreshed.items() if node != lease.node_id]
        new_lease = grant_coordinator_lease(
            new_snapshot,
            replacement,
            scope="grid10/global",
            policy_sha256=A,
        )
        self.assertNotEqual(new_lease.node_id, lease.node_id)
        self.assertEqual(new_lease.state_epoch, new_snapshot.epoch)

    def test_duplicate_result_rejected(self):
        worker = self.sessions["node-c"]
        result = emit_node_result(
            self.snapshot,
            worker,
            select_work(self.snapshot, worker),
            payload_ref="result:dup",
            payload_sha256=F,
        )
        lease = grant_coordinator_lease(
            self.snapshot,
            [self.sessions["node-a"], self.sessions["node-b"]],
            scope="grid10/global",
            policy_sha256=A,
        )
        with self.assertRaisesRegex(SharedStateError, "DUPLICATE_NODE_RESULT_REJECTED"):
            commit_s1_delta(
                self.snapshot,
                self.sessions[lease.node_id],
                lease,
                consumed_results=(result, result),
            )

    def test_resolved_hyperposition_branch_cannot_be_silently_reopened(self):
        resolved = make_snapshot(
            generation=7,
            epoch=1,
            policy_sha256=A,
            work_items=(WorkItem("t", "branch-x", 1, "p", B),),
            hyperposition_branches=(HyperpositionBranchRef("branch-x", C, "RESOLVED"),),
        )
        authority = {"node-a": ("hcu.s1.read", "hcu.coordinate.eligible")}
        session = boot_node(
            resolved,
            node_id="node-a",
            current_generation=7,
            capability_binding_sha256=E,
            admitted_capabilities_by_node=authority,
        )
        lease = grant_coordinator_lease(resolved, [session], scope="s", policy_sha256=A)
        with self.assertRaisesRegex(
            SharedStateError,
            "HYPERPOSITION_RESOLUTION_REVERSAL_REQUIRES_NEW_BRANCH",
        ):
            commit_s1_delta(
                resolved,
                session,
                lease,
                hyperposition_updates=(HyperpositionBranchRef("branch-x", D, "UNRESOLVED"),),
            )

    def test_lease_requires_external_eligible_capability(self):
        with self.assertRaisesRegex(SharedStateError, "NO_ELIGIBLE_COORDINATOR"):
            grant_coordinator_lease(
                self.snapshot,
                [self.sessions["node-c"]],
                scope="grid10/global",
                policy_sha256=A,
            )


if __name__ == "__main__":
    unittest.main()
