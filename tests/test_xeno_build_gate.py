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
    def test_recursive_accepts_cross_group_progress_without_regression(self):
        result = MOD.evaluate(BASE, all_better(), claycode_migration=False)
        self.assertTrue(result["promotion_pass"])
        self.assertGreaterEqual(len(result["improved_groups"]), 2)

    def test_material_regression_rejects_recursive(self):
        after = all_better()
        after["rss_mb"] = 950
        result = MOD.evaluate(BASE, after, claycode_migration=False)
        self.assertFalse(result["promotion_pass"])
        self.assertIn("rss_mb", result["regressions"])

    def test_hard_invariant_rejects_even_small_regression(self):
        after = all_better()
        after["authority_boundary_pass_rate"] = BASE["authority_boundary_pass_rate"] - 0.0001
        result = MOD.evaluate(BASE, after, claycode_migration=False)
        self.assertFalse(result["promotion_pass"])
        self.assertIn("authority_boundary_pass_rate", result["regressions"])

    def test_tiny_metric_jitter_does_not_mint_progress(self):
        after = {name: value for name, value in BASE.items()}
        after["capability_pass_rate"] += 1e-6
        after["throughput_tokens_s"] += 1e-6
        result = MOD.evaluate(BASE, after, claycode_migration=False)
        self.assertFalse(result["promotion_pass"])
        self.assertEqual(result["improved_groups"], [])
        self.assertIn("capability_pass_rate", result["stable_metrics"])

    def test_jspace_need_not_improve_on_unrelated_candidate_but_must_not_regress(self):
        after = dict(BASE)
        after["capability_pass_rate"] = .81
        after["throughput_tokens_s"] = 22
        result = MOD.evaluate(BASE, after, claycode_migration=False)
        self.assertTrue(result["promotion_pass"])
        self.assertIn("jspace_causal_gain_score", result["stable_metrics"])

        after["jspace_causal_gain_score"] = .28
        result = MOD.evaluate(BASE, after, claycode_migration=False)
        self.assertFalse(result["promotion_pass"])
        self.assertIn("jspace_causal_gain_score", result["regressions"])

    def test_only_one_progress_group_is_insufficient(self):
        after = dict(BASE)
        after["capability_pass_rate"] = .81
        after["task_quality_score"] = .71
        result = MOD.evaluate(BASE, after, claycode_migration=False)
        self.assertFalse(result["promotion_pass"])
        self.assertEqual(result["improved_groups"], ["capability_quality"])

    def test_claycode_migration_requires_claycode_plus_cross_group_progress(self):
        after = dict(BASE)
        after["claycode_fraction"] = .25
        after["throughput_tokens_s"] = 22
        self.assertTrue(MOD.evaluate(BASE, after, claycode_migration=True)["promotion_pass"])

        no_claycode = dict(BASE)
        no_claycode["capability_pass_rate"] = .81
        no_claycode["throughput_tokens_s"] = 22
        self.assertFalse(MOD.evaluate(BASE, no_claycode, claycode_migration=True)["promotion_pass"])

    def test_claycode_migration_allows_stable_unrelated_metrics(self):
        after = dict(BASE)
        after["claycode_fraction"] = .25
        after["throughput_tokens_s"] = 22
        result = MOD.evaluate(BASE, after, claycode_migration=True)
        self.assertTrue(result["promotion_pass"])
        self.assertIn("recovery_pass_rate", result["stable_metrics"])


if __name__ == "__main__":
    unittest.main()
