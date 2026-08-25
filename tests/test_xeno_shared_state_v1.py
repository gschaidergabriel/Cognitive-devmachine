import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("xeno_shared_state_v1", ROOT / "tools/xeno_shared_state_v1.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)


def digest(ch: str) -> str:
    return ch * 64


class XenoSharedStateV1Tests(unittest.TestCase):
    def snapshot(self):
        return MOD.build_snapshot(
            epoch=7,
            generation=3,
            scope="grid10/task-alpha",
            tasks=[
                {"task_id": "low", "priority": 1, "required_capabilities": ["reason"], "status": "OPEN"},
                {"task_id": "high", "priority": 9, "required_capabilities": ["reason"], "status": "OPEN"},
                {"task_id": "claimed", "priority": 20, "required_capabilities": ["reason"], "status": "CLAIMED"},
            ],
            claims=[{"task_id": "claimed", "node_id": "n9"}],
            hyperposition_branches=[{"branch_id": "b1", "state": "UNRESOLVED"}],
            gwt_broadcasts=[{"broadcast_id": "g1"}],
            provenance_refs=["s0:entity-generation:3"],
        )

    def lease(self, snap, *, ticks=5):
        return MOD.select_coordinator(
            snap,
            candidates=[
                {"node_id": "n3", "capabilities": ["reason", "integrate"], "load": 2, "healthy": True, "policy_eligible": True},
                {"node_id": "n1", "capabilities": ["reason", "integrate"], "load": 2, "healthy": True, "policy_eligible": True},
                {"node_id": "n0", "capabilities": ["reason", "integrate"], "load": 0, "healthy": True, "policy_eligible": False},
            ],
            required_capabilities=["integrate"],
            now_tick=10,
            lease_ticks=ticks,
            lease_id="lease-1",
        )

    def test_autonomous_boot_selects_highest_priority_unclaimed_work_and_defaults_ordinary(self):
        snap = self.snapshot()
        plan = MOD.autonomous_boot(snap, node_id="n2", capabilities=["reason"], now_tick=10)
        self.assertEqual(plan["role"], "ORDINARY")
        self.assertEqual(plan["s1_access"], "READ_ONLY")
        self.assertEqual(plan["selected_task_id"], "high")
        self.assertEqual(plan["bound_state_digest"], snap["state_digest"])

    def test_ordinary_node_direct_write_is_rejected(self):
        plan = MOD.autonomous_boot(self.snapshot(), node_id="n2", capabilities=["reason"], now_tick=10)
        with self.assertRaisesRegex(MOD.XenoSharedStateError, "ORDINARY_NODE_S1_WRITE_FORBIDDEN"):
            MOD.reject_direct_s1_write(plan)

    def test_coordinator_selection_is_deterministic_and_policy_gated(self):
        lease = self.lease(self.snapshot())
        self.assertEqual(lease["holder_node_id"], "n1")
        self.assertEqual(lease["selection_rule"], "POLICY_ELIGIBLE_HEALTHY_MIN_LOAD_THEN_NODE_ID")

    def test_valid_lease_changes_role_but_keeps_direct_write_forbidden(self):
        snap = self.snapshot()
        lease = self.lease(snap)
        plan = MOD.autonomous_boot(
            snap, node_id="n1", capabilities=["reason", "integrate"], now_tick=11, coordinator_lease=lease
        )
        self.assertEqual(plan["role"], "COORDINATOR")
        self.assertEqual(plan["s1_access"], "LEASE_SCOPED_WRITE_VIA_GATE_ONLY")
        with self.assertRaisesRegex(MOD.XenoSharedStateError, "DIRECT_S1_WRITE_FORBIDDEN_USE_COORDINATOR_GATE"):
            MOD.reject_direct_s1_write(plan)

    def test_node_result_to_coordinator_write_authorization_preserves_s0_boundary(self):
        snap = self.snapshot()
        lease = self.lease(snap)
        ordinary = MOD.autonomous_boot(snap, node_id="n2", capabilities=["reason"], now_tick=10)
        result = MOD.make_node_result(
            ordinary,
            result_id="r1",
            payload_ref="cas:payload:r1",
            payload_digest=digest("a"),
            evidence_refs=["evidence:1"],
        )
        auth = MOD.authorize_s1_write(
            snap,
            coordinator_node_id="n1",
            lease=lease,
            node_results=[result],
            expected_epoch=snap["epoch"],
            expected_state_digest=snap["state_digest"],
            now_tick=11,
        )
        self.assertEqual(auth["write_class"], "S1_CANDIDATE_DELTA_ONLY")
        self.assertFalse(auth["s0_truth_effect_security_authority"])
        self.assertEqual(auth["accepted_result_digests"], [result["result_digest"]])

    def test_stale_lease_duplicate_result_and_snapshot_tamper_fail_closed(self):
        snap = self.snapshot()
        short = self.lease(snap, ticks=1)
        ordinary = MOD.autonomous_boot(snap, node_id="n2", capabilities=["reason"], now_tick=10)
        result = MOD.make_node_result(
            ordinary, result_id="r1", payload_ref="cas:r1", payload_digest=digest("b"), evidence_refs=["e:1"]
        )
        with self.assertRaisesRegex(MOD.XenoSharedStateError, "LEASE_NOT_CURRENT"):
            MOD.authorize_s1_write(
                snap, coordinator_node_id="n1", lease=short, node_results=[result],
                expected_epoch=7, expected_state_digest=snap["state_digest"], now_tick=11,
            )
        lease = self.lease(snap)
        with self.assertRaisesRegex(MOD.XenoSharedStateError, "NODE_RESULT_DUPLICATE"):
            MOD.authorize_s1_write(
                snap, coordinator_node_id="n1", lease=lease, node_results=[result, result],
                expected_epoch=7, expected_state_digest=snap["state_digest"], now_tick=11,
            )
        snap["tasks"][0]["priority"] = 999
        with self.assertRaisesRegex(MOD.XenoSharedStateError, "S1_DIGEST_MISMATCH"):
            MOD.validate_snapshot(snap)


if __name__ == "__main__":
    unittest.main()
