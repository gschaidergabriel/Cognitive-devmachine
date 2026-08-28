from __future__ import annotations

from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_swarm_model_health_v1 as mh


class ModelHealthTests(unittest.TestCase):
    def setUp(self) -> None:
        mh._HEALTH.clear()

    def test_three_deterministic_400s_quarantine_exact_model(self) -> None:
        for _ in range(mh.HARD_4XX_THRESHOLD):
            row = mh._record_result("nvidia", "dead-model", 400, 1.0)
        self.assertTrue(row["disabled"])
        self.assertIn("MODEL_HARD_4XX_CIRCUIT", row["disabled_reason"])
        sibling = mh._health("nvidia", "healthy-model")
        self.assertFalse(sibling["disabled"])

    def test_success_prevents_historical_hard_error_from_false_disable(self) -> None:
        mh._record_result("nvidia", "mixed", 200, 2.0)
        for _ in range(mh.HARD_4XX_THRESHOLD + 2):
            row = mh._record_result("nvidia", "mixed", 400, 2.0)
        self.assertFalse(row["disabled"])

    def test_repeated_5xx_cools_model_not_permanently_disables_it(self) -> None:
        for _ in range(mh.TRANSIENT_5XX_THRESHOLD):
            row = mh._record_result("nvidia", "flaky", 503, 2.0)
        self.assertFalse(row["disabled"])
        self.assertGreater(row["cooldown_until"], time.monotonic())
        self.assertEqual(mh._quality_weight(row), 0.0)

    def test_weight_rewards_success_latency_and_delta_yield(self) -> None:
        strong = mh._blank()
        strong.update({"total": 20, "success": 18, "delta_markers": 8, "accepted_deltas": 1, "latency_ema_s": 10.0})
        weak = mh._blank()
        weak.update({"total": 20, "success": 7, "delta_markers": 1, "accepted_deltas": 0, "latency_ema_s": 35.0, "transient_5xx": 5})
        self.assertGreater(mh._quality_weight(strong), mh._quality_weight(weak))

    def test_exploration_weight_declines_with_trials(self) -> None:
        a = mh._blank(); a["total"] = 0
        b = mh._blank(); b["total"] = 2
        self.assertGreater(mh._quality_weight(a), mh._quality_weight(b))


if __name__ == "__main__":
    unittest.main()
