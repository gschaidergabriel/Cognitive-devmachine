import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from capacity_guard_v1 import HCUCapacityError, UNRESOLVED, admit_measurement, unresolved_decision, validate_topology


def topology():
    return json.loads((HERE / "topology.kvm4.json").read_text(encoding="utf-8"))


def measurement():
    return {
        "schema": "HCU_CAPACITY_MEASUREMENT/v1",
        "source_commit_sha256": "1" * 64,
        "checkpoint_sha256": "2" * 64,
        "tokenizer_sha256": "3" * 64,
        "runtime_sha256": "4" * 64,
        "measurement_receipt_sha256": "5" * 64,
        "execution_surface": "AUTHORIZED_ISOLATED_SANDBOX",
        "host_profile_id": "kvm4-4c16g-200g-16tb",
        "model_class": "~0.8B_GENERIC_CLAYCOG",
        "shared_weight_rss_bytes": 1 * 1024**3,
        "incremental_logical_slot_rss_bytes": 512 * 1024**2,
        "safety_reserve_bytes": 4 * 1024**3,
        "measured_safe_logical_slots": 16,
        "measured_safe_resident_workers": 2,
        "measured_safe_physical_decode": 2,
    }


class HCUCapacityGuardTests(unittest.TestCase):
    def test_current_source_topology_validates_but_capacity_stays_unresolved(self):
        validate_topology(topology())
        decision = unresolved_decision(topology())
        self.assertEqual(decision.status, UNRESOLVED)
        self.assertEqual(decision.logical_slots, UNRESOLVED)

    def test_authority_fork_is_rejected(self):
        value = topology(); value["persistence"]["authority"] = "HCU_DB"
        with self.assertRaisesRegex(HCUCapacityError, "MINIUNIFIEDDB"):
            validate_topology(value)

    def test_regression_false_32_slot_runtime_claim_without_measurement_fails_closed(self):
        value = topology()
        value["logical_grid"]["target_slots"] = 32
        value["logical_grid"]["adaptive_ceiling"] = 32
        value["logical_grid"]["lanes"]["simulation"] += 16
        value["evidence"]["safe_slot_ceiling"] = 32
        with self.assertRaisesRegex(HCUCapacityError, "SOURCE_TOPOLOGY_CANNOT_MINT_RUNTIME_CLAIM"):
            validate_topology(value)

    def test_lane_sum_mismatch_is_rejected(self):
        value = topology(); value["logical_grid"]["lanes"]["world"] += 1
        with self.assertRaisesRegex(HCUCapacityError, "LOGICAL_LANE_SUM"):
            validate_topology(value)

    def test_measurement_must_be_from_authorized_isolated_surface(self):
        value = measurement(); value["execution_surface"] = "TARGET_VPS"
        with self.assertRaisesRegex(HCUCapacityError, "SURFACE_NOT_ADMITTED"):
            admit_measurement(topology(), value)

    def test_exact_measurement_can_bind_capacity_when_within_measured_bounds(self):
        decision = admit_measurement(topology(), measurement())
        self.assertEqual(decision.status, "EXACT_ISOLATED_MEASUREMENT_BOUND")
        self.assertEqual(decision.logical_slots, 16)
        self.assertEqual(decision.resident_workers, 2)
        self.assertEqual(decision.physical_decode_concurrency, 2)

    def test_memory_overclaim_is_rejected(self):
        value = measurement(); value["measured_safe_logical_slots"] = 23
        with self.assertRaisesRegex(HCUCapacityError, "EXCEED_MEMORY_BOUND"):
            admit_measurement(topology(), value)


if __name__ == "__main__":
    unittest.main()
