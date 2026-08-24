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
}


class GateTests(unittest.TestCase):
    def test_recursive_accepts_required_progress_and_no_regressions(self):
        after = dict(BASE)
        after.update(
            capability_pass_rate=.81,
            task_quality_score=.71,
            p50_latency_ms=95,
            p95_latency_ms=175,
            throughput_tokens_s=22,
            rss_mb=890,
            recovery_pass_rate=.91,
            authority_boundary_pass_rate=.96,
            token_efficiency_score=.61,
            claycode_fraction=.25,
        )
        result = MOD.evaluate(BASE, after, claycode_migration=False)
        self.assertTrue(result["promotion_pass"])

    def test_any_regression_rejects_recursive(self):
        after = dict(BASE)
        after.update(
            capability_pass_rate=.81,
            task_quality_score=.71,
            p50_latency_ms=95,
            throughput_tokens_s=22,
            claycode_fraction=.25,
            rss_mb=950,
        )
        result = MOD.evaluate(BASE, after, claycode_migration=False)
        self.assertFalse(result["promotion_pass"])
        self.assertIn("rss_mb", result["regressions"])

    def test_claycode_migration_requires_every_metric_strictly_better(self):
        after = dict(BASE)
        after.update(
            capability_pass_rate=.81,
            task_quality_score=.71,
            p50_latency_ms=95,
            p95_latency_ms=175,
            throughput_tokens_s=22,
            rss_mb=890,
            recovery_pass_rate=.91,
            authority_boundary_pass_rate=.96,
            token_efficiency_score=.61,
            claycode_fraction=.25,
        )
        self.assertTrue(MOD.evaluate(BASE, after, claycode_migration=True)["promotion_pass"])
        after["recovery_pass_rate"] = BASE["recovery_pass_rate"]
        self.assertFalse(MOD.evaluate(BASE, after, claycode_migration=True)["promotion_pass"])


if __name__ == "__main__":
    unittest.main()
