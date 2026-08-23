import unittest

from capacity_planner import (
    Hardware,
    PlanningAssumptions,
    measured_capacity,
    plan_full_resident,
    plan_shared_base,
)


class CapacityPlannerTests(unittest.TestCase):
    def setUp(self):
        self.hw = Hardware(cpu_cores=4, memory_gib=16, reserve_gib=3)
        self.a = PlanningAssumptions()

    def test_shared_base_yields_more_logical_cells_than_full_copies(self):
        shared = plan_shared_base(self.hw, self.a)
        full = plan_full_resident(self.hw, self.a)
        self.assertGreater(shared.logical_cells, full.logical_cells)
        self.assertLessEqual(shared.simultaneous_cpu_lanes, 4)
        self.assertLessEqual(full.simultaneous_cpu_lanes, 4)

    def test_planning_estimates_cannot_claim_runtime_evidence(self):
        self.assertEqual(
            plan_shared_base(self.hw, self.a).classification,
            "PLANNING_ONLY_NOT_RUNTIME_EVIDENCE",
        )
        self.assertEqual(
            plan_full_resident(self.hw, self.a).classification,
            "PLANNING_ONLY_NOT_RUNTIME_EVIDENCE",
        )

    def test_measured_capacity_requires_measured_rss(self):
        with self.assertRaises(ValueError):
            measured_capacity(self.hw, None, mode="FULL_RESIDENT_08B_CELL")
        with self.assertRaises(ValueError):
            measured_capacity(self.hw, 0, mode="FULL_RESIDENT_08B_CELL")

    def test_measured_capacity_respects_cpu_lane_cap(self):
        estimate = measured_capacity(
            self.hw,
            512,
            mode="FULL_RESIDENT_08B_CELL",
        )
        self.assertGreater(estimate.logical_cells, 4)
        self.assertEqual(estimate.simultaneous_cpu_lanes, 4)


if __name__ == "__main__":
    unittest.main()
