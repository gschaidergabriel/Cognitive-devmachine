from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "free swarm/go_collective_metrics.py"
SPEC = importlib.util.spec_from_file_location("go_collective_metrics", MODULE_PATH)
assert SPEC and SPEC.loader
metrics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(metrics)

CONFIG = json.loads((ROOT / "research_entity/continuity/go_metrics/GO_METRICS_CONFIG_V1.json").read_text())


class GoCollectiveMetricsV1Tests(unittest.TestCase):
    def test_code_quality_fails_closed_on_low_evidence_coverage(self):
        score, coverage = metrics.code_quality({
            "tests_passed": 10,
            "tests_failed": 0,
        }, CONFIG)
        self.assertIsNone(score)
        self.assertLess(coverage, CONFIG["code_quality"]["min_evidence_coverage"])

    def test_accepted_delta_requires_reproducibility_and_hard_gates(self):
        base = {
            "status": "accepted",
            "relative_improvement_pct": 5.0,
            "reproducible_runs": 2,
            "tests_failed": 0,
            "negative_tests_failed": 0,
            "static_checks_failed": 0,
            "benchmark_non_regression": True,
            "reverted": False,
        }
        self.assertTrue(metrics.accepted_delta(base))
        bad = dict(base, tests_failed=1)
        self.assertFalse(metrics.accepted_delta(bad))
        bad = dict(base, reproducible_runs=1)
        self.assertFalse(metrics.accepted_delta(bad))

    def test_information_latency_requires_real_consumption_ack(self):
        self.assertIsNone(metrics.information_latency({
            "evidence_emitted_at": "2026-08-24T10:00:00+00:00"
        }))
        self.assertEqual(metrics.information_latency({
            "evidence_emitted_at": "2026-08-24T10:00:00+00:00",
            "first_downstream_consumed_at": "2026-08-24T10:00:02+00:00",
        }), 2.0)

    def test_lineage_collapse_does_not_count_same_lineage_as_independent(self):
        probs = {m: 0.8 for m in CONFIG["hcu_confidence"]["milestones"]}
        rows = [
            {"worker_id": "a", "evidence_lineage": "same", "hcu_forecast": {"milestone_probabilities": probs}},
            {"worker_id": "b", "evidence_lineage": "same", "hcu_forecast": {"milestone_probabilities": probs}},
        ]
        out = metrics.hcu_forecast(rows, CONFIG)
        self.assertEqual(out["independent_forecast_lineages"], 1)
        self.assertAlmostEqual(out["forecast_probability"], 0.8, places=6)

    def test_seed_forecast_is_explicitly_uncalibrated(self):
        out = metrics.hcu_forecast([], CONFIG)
        self.assertTrue(out["seed_used"])
        self.assertEqual(out["calibration_state"], "UNCALIBRATED")
        self.assertGreater(out["forecast_probability"], 0.0)
        self.assertLess(out["forecast_probability"], 1.0)

    def test_single_scalar_selection_is_forbidden(self):
        self.assertEqual(CONFIG["selection_policy"], "PARETO_WITH_HARD_GATES_NO_SINGLE_SCALAR")
        self.assertTrue(CONFIG["anti_goodhart"]["score_can_decrease"])
        self.assertTrue(CONFIG["anti_goodhart"]["evidence_lineage_collapse"])


if __name__ == "__main__":
    unittest.main()
