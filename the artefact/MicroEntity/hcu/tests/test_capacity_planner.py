import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "capacity_planner.py"
SPEC = importlib.util.spec_from_file_location("hcu_capacity_planner", MODULE_PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class CapacityPlannerTests(unittest.TestCase):
    def setUp(self):
        self.host = MOD.HostProfile(vcpu=4, memory_gib=16.0, disk_gb=200.0, bandwidth_tb=16.0)
        self.safety = MOD.SafetyProfile(
            ram_utilization_fraction=0.85,
            non_model_reserve_gib=4.0,
            disk_reserve_gb=40.0,
            threads_per_active_tile=2,
        )
        self.tile = MOD.TileFootprint(
            resident_rss_gib=0.75,
            active_context_increment_gib=0.50,
            artifact_size_gb=0.60,
        )

    def test_owner_kvm4_planning_profile(self):
        plan = MOD.plan_capacity(self.host, self.safety, self.tile)
        self.assertEqual(plan.max_resident_tiles, 11)
        self.assertEqual(plan.max_parallel_active_tiles, 2)
        self.assertEqual(plan.max_cold_distinct_artifacts, 266)
        self.assertLessEqual(plan.estimated_total_ram_gib, plan.usable_ram_gib)
        self.assertEqual(plan.status, "PLANNING_ESTIMATE_NOT_RUNTIME_MEASURED")

    def test_cpu_limit_reduces_active_slots(self):
        safety = MOD.SafetyProfile(
            ram_utilization_fraction=0.85,
            non_model_reserve_gib=4.0,
            disk_reserve_gb=40.0,
            threads_per_active_tile=4,
        )
        plan = MOD.plan_capacity(self.host, safety, self.tile)
        self.assertEqual(plan.cpu_active_limit, 1)
        self.assertEqual(plan.max_parallel_active_tiles, 1)

    def test_smaller_measured_resident_footprint_can_increase_resident_count(self):
        smaller = MOD.TileFootprint(
            resident_rss_gib=0.50,
            active_context_increment_gib=0.25,
            artifact_size_gb=0.60,
        )
        baseline = MOD.plan_capacity(self.host, self.safety, self.tile)
        improved = MOD.plan_capacity(self.host, self.safety, smaller)
        self.assertGreater(improved.max_resident_tiles, baseline.max_resident_tiles)

    def test_invalid_ram_reserve_fails_closed(self):
        safety = MOD.SafetyProfile(
            ram_utilization_fraction=0.50,
            non_model_reserve_gib=8.0,
            disk_reserve_gb=40.0,
            threads_per_active_tile=2,
        )
        with self.assertRaises(MOD.CapacityError):
            MOD.plan_capacity(self.host, safety, self.tile)

    def test_invalid_tile_footprint_fails_closed(self):
        bad = MOD.TileFootprint(
            resident_rss_gib=0.0,
            active_context_increment_gib=0.50,
            artifact_size_gb=0.60,
        )
        with self.assertRaises(MOD.CapacityError):
            MOD.plan_capacity(self.host, self.safety, bad)


if __name__ == "__main__":
    unittest.main()
