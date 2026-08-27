from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "free swarm/go_collective_metrics_v2.py"
SPEC = importlib.util.spec_from_file_location("go_collective_metrics_v2", MODULE_PATH)
assert SPEC and SPEC.loader
metrics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(metrics)


class GoCollectiveMetricsV2Tests(unittest.TestCase):
    def test_unresolved_macrocycle_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "EXACT_REPRODUCIBLE_MACROCYCLE_ID_REQUIRED"):
            metrics.select_macrocycle([], "MACROCYCLE_ID_UNRESOLVED")

    def test_scope_is_exact_macrocycle_only(self):
        rows = [
            {"worker_id": "a", "macrocycle_id": "go-A"},
            {"worker_id": "b", "macrocycle_id": "go-B"},
            {"worker_id": "u", "macrocycle_id": "MACROCYCLE_ID_UNRESOLVED"},
        ]
        out = metrics.select_macrocycle(rows, "go-A")
        self.assertEqual([r["worker_id"] for r in out], ["a"])

    def test_correlated_fanout_cannot_multiply_verified_utility(self):
        rows = [
            {
                "evidence_lineage": "same",
                "total_tokens": 100,
                "verified_utility_units": 2.0,
                "code_quality_score": 80.0,
                "verified_innovation_score": 60.0,
            },
            {
                "evidence_lineage": "same",
                "total_tokens": 100,
                "verified_utility_units": 2.0,
                "code_quality_score": 80.0,
                "verified_innovation_score": 60.0,
            },
        ]
        out = metrics.apply_lineage_collapse(rows, {})
        self.assertEqual(out["verified_utility_units_raw_worker_sum"], 4.0)
        self.assertEqual(out["verified_utility_units"], 2.0)
        self.assertEqual(out["total_tokens"], 200)
        self.assertEqual(out["token_quality_efficiency"], 10.0)
        self.assertEqual(out["lineage_count"], 1)

    def test_independent_lineages_can_add_utility(self):
        rows = [
            {"evidence_lineage": "a", "total_tokens": 100, "verified_utility_units": 1.0},
            {"evidence_lineage": "b", "total_tokens": 100, "verified_utility_units": 2.0},
        ]
        out = metrics.apply_lineage_collapse(rows, {})
        self.assertEqual(out["verified_utility_units"], 3.0)
        self.assertEqual(out["token_quality_efficiency"], 15.0)
        self.assertEqual(out["lineage_count"], 2)

    def test_quality_is_lineage_weighted_not_worker_weighted(self):
        rows = [
            {"evidence_lineage": "crowd", "code_quality_score": 100.0},
            {"evidence_lineage": "crowd", "code_quality_score": 100.0},
            {"evidence_lineage": "crowd", "code_quality_score": 100.0},
            {"evidence_lineage": "independent", "code_quality_score": 0.0},
        ]
        out = metrics.apply_lineage_collapse(rows, {})
        self.assertEqual(out["code_quality_score"], 50.0)

    def test_missing_lineage_collapses_together_instead_of_fake_independence(self):
        rows = [
            {"worker_id": "a", "verified_utility_units": 1.0},
            {"worker_id": "b", "verified_utility_units": 3.0},
        ]
        out = metrics.apply_lineage_collapse(rows, {})
        self.assertEqual(out["lineage_count"], 1)
        self.assertEqual(out["verified_utility_units"], 3.0)


if __name__ == "__main__":
    unittest.main()
