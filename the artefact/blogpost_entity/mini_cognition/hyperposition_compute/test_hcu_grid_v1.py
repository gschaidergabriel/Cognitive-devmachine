import json
import unittest
from pathlib import Path

from hcu_grid_v1 import HCUError, Proposal, aggregate_diversity_capped, plan_capacity


ROOT = Path(__file__).resolve().parent


class CapacityTests(unittest.TestCase):
    def test_capacity_uses_measured_rss_and_cpu_cap(self):
        plan = plan_capacity(
            total_ram_bytes=16 * 1024**3,
            measured_worker_rss_bytes=1024**3,
            cpu_cores=4,
            reserve_ratio=0.25,
        )
        self.assertEqual(plan.resident_slots, 12)
        self.assertEqual(plan.active_cpu_slots, 4)
        self.assertEqual(plan.queued_slots, 8)

    def test_capacity_refuses_unmeasured_worker(self):
        with self.assertRaisesRegex(HCUError, "measured_worker_rss_bytes"):
            plan_capacity(total_ram_bytes=16 * 1024**3, measured_worker_rss_bytes=0, cpu_cores=4)

    def test_capacity_refuses_ram_overcommit(self):
        with self.assertRaisesRegex(HCUError, "INSUFFICIENT_RAM"):
            plan_capacity(
                total_ram_bytes=16 * 1024**3,
                measured_worker_rss_bytes=15 * 1024**3,
                cpu_cores=4,
                reserve_ratio=0.25,
            )


class DiversityTests(unittest.TestCase):
    def test_correlated_clone_majority_does_not_multiply_authority(self):
        proposals = [
            Proposal(f"clone-{i}", "same-checkpoint-same-route", "A", 0.99)
            for i in range(16)
        ] + [
            Proposal("ind-1", "route-1", "B", 0.70),
            Proposal("ind-2", "route-2", "B", 0.70),
            Proposal("ind-3", "route-3", "B", 0.70),
        ]
        winner, scores = aggregate_diversity_capped(proposals)
        self.assertEqual(winner, "B")
        self.assertEqual(scores, {"A": 1.0, "B": 3.0})

    def test_grid_tie_fails_closed(self):
        with self.assertRaisesRegex(HCUError, "GRID_TIE_UNKNOWN"):
            aggregate_diversity_capped(
                [
                    Proposal("a", "g-a", "A", 0.9),
                    Proposal("b", "g-b", "B", 0.9),
                ]
            )

    def test_duplicate_proposal_id_fails_closed(self):
        with self.assertRaisesRegex(HCUError, "DUPLICATE_PROPOSAL_ID"):
            aggregate_diversity_capped(
                [
                    Proposal("same", "g-a", "A", 0.9),
                    Proposal("same", "g-b", "A", 0.8),
                ]
            )


class PackagingTests(unittest.TestCase):
    def test_release_manifest_recursively_includes_hcu_files(self):
        manifest = json.loads((ROOT / "release_manifest_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["include_policy"], "recursive_all_files")
        for relative in manifest["required_files"]:
            self.assertTrue((ROOT / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
