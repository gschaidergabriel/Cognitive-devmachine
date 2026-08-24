import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("xeno_build_gate", ROOT / "tools/xeno_build_gate.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)

BASE = {
    "capability_pass_rate": 0.80,
    "task_quality_score": 0.70,
    "p50_latency_ms": 100.0,
    "p95_latency_ms": 180.0,
    "throughput_tokens_s": 20.0,
    "rss_mb": 900.0,
    "recovery_pass_rate": 0.90,
    "authority_boundary_pass_rate": 0.95,
    "token_efficiency_score": 0.60,
    "claycode_fraction": 0.20,
    "engine_swap_pass_rate": 0.82,
    "two_slot_harness_pass_rate": 0.84,
    "prestage_pipeline_pass_rate": 0.80,
    "grid10_pass_rate": 0.76,
    "peer_link_pass_rate": 0.74,
    "dashboard_config_pass_rate": 0.86,
    "jspace_causal_gain_score": 0.30,
}


def all_better():
    return {
        "capability_pass_rate": .81,
        "task_quality_score": .71,
        "p50_latency_ms": 95,
        "p95_latency_ms": 175,
        "throughput_tokens_s": 22,
        "rss_mb": 890,
        "recovery_pass_rate": .91,
        "authority_boundary_pass_rate": .96,
        "token_efficiency_score": .61,
        "claycode_fraction": .25,
        "engine_swap_pass_rate": .83,
        "two_slot_harness_pass_rate": .85,
        "prestage_pipeline_pass_rate": .81,
        "grid10_pass_rate": .77,
        "peer_link_pass_rate": .75,
        "dashboard_config_pass_rate": .87,
        "jspace_causal_gain_score": .32,
    }


class GateTests(unittest.TestCase):
    def test_recursive_accepts_required_progress_and_no_regressions(self):
        after = dict(BASE)
        after.update(all_better())
        result = MOD.evaluate(BASE, after, claycode_migration=False)
        self.assertTrue(result["promotion_pass"])

    def test_any_regression_rejects_recursive(self):
        after = dict(BASE)
        after.update(all_better())
        after["rss_mb"] = 950
        result = MOD.evaluate(BASE, after, claycode_migration=False)
        self.assertFalse(result["promotion_pass"])
        self.assertIn("rss_mb", result["regressions"])

    def test_jspace_must_progress_in_recursive_mode(self):
        after = dict(BASE)
        after.update(all_better())
        after["jspace_causal_gain_score"] = BASE["jspace_causal_gain_score"]
        result = MOD.evaluate(BASE, after, claycode_migration=False)
        self.assertFalse(result["promotion_pass"])
        self.assertIn("jspace_causal_gain_score", result["equal_metrics"])

    def test_harness_regression_rejects_recursive(self):
        after = dict(BASE)
        after.update(all_better())
        after["peer_link_pass_rate"] = .70
        result = MOD.evaluate(BASE, after, claycode_migration=False)
        self.assertFalse(result["promotion_pass"])
        self.assertIn("peer_link_pass_rate", result["regressions"])

    def test_claycode_migration_requires_every_metric_strictly_better(self):
        after = dict(BASE)
        after.update(all_better())
        self.assertTrue(MOD.evaluate(BASE, after, claycode_migration=True)["promotion_pass"])
        after["recovery_pass_rate"] = BASE["recovery_pass_rate"]
        self.assertFalse(MOD.evaluate(BASE, after, claycode_migration=True)["promotion_pass"])


if __name__ == "__main__":
    unittest.main()
