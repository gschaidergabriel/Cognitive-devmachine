from __future__ import annotations

import unittest

from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import (
    EpochReadLifetime,
    decide_compile_from_pulse_history,
    estimate_read_horizon,
)


BASE = CompileEconomics(
    build_cost_us=72295.54633333333,
    online_query_us=60.76010636666667,
    compiled_query_us=4.294575966666667,
    online_quality=1.0,
    compiled_quality=1.0,
    expected_reads_before_invalidation=999999.0,  # overwritten by Pulse history
    safety_factor=1.20,
)


def history(*reads):
    return [EpochReadLifetime(i + 1, int(n)) for i, n in enumerate(reads)]


class CompileHorizonEstimatorV16Tests(unittest.TestCase):
    def test_sparse_history_fails_conservative_online(self):
        estimate, decision = decide_compile_from_pulse_history(BASE, history(9000, 8000, 7000))
        self.assertEqual(estimate.status, "INSUFFICIENT_HISTORY")
        self.assertEqual(estimate.expected_reads_lower_bound, 0.0)
        self.assertEqual(decision.mode, "ONLINE")

    def test_stable_long_lived_field_crosses_measured_break_even(self):
        estimate, decision = decide_compile_from_pulse_history(
            BASE, history(2100, 2200, 2050, 2300, 2150, 2250, 2400)
        )
        self.assertEqual(estimate.status, "HISTORY_BOUND")
        self.assertGreater(estimate.expected_reads_lower_bound, 1536.0)
        self.assertEqual(decision.mode, "COMPILE")
        self.assertEqual(decision.reason, "EXPECTED_LIFETIME_AMORTIZES_BUILD")

    def test_stable_short_lived_field_stays_online(self):
        estimate, decision = decide_compile_from_pulse_history(
            BASE, history(900, 1100, 1000, 1200, 1050, 980, 1150)
        )
        self.assertEqual(estimate.status, "HISTORY_BOUND")
        self.assertLess(estimate.expected_reads_lower_bound, 1536.0)
        self.assertEqual(decision.mode, "ONLINE")

    def test_recent_churn_collapse_uses_recent_floor(self):
        estimate, decision = decide_compile_from_pulse_history(
            BASE, history(5000, 4800, 5200, 5100, 4900, 140, 110, 90),
            recent_window=3,
        )
        self.assertTrue(estimate.churn_shock)
        self.assertEqual(estimate.status, "CHURN_SHOCK_BOUND")
        self.assertEqual(estimate.expected_reads_lower_bound, 90.0)
        self.assertEqual(decision.mode, "ONLINE")

    def test_fault_boundary_is_not_dropped_as_outlier(self):
        samples = history(2200, 2300, 2250, 2400, 2350, 2100)
        samples.append(EpochReadLifetime(7, 12, recovery_or_fault_boundary=True))
        estimate = estimate_read_horizon(samples, recent_window=3)
        self.assertLessEqual(estimate.expected_reads_lower_bound, estimate.empirical_q20)
        self.assertLessEqual(estimate.expected_reads_lower_bound, 2100.0)

    def test_incomplete_current_epoch_does_not_fake_long_lifetime(self):
        samples = history(1000, 1050, 1100, 950, 980)
        samples.append(EpochReadLifetime(6, 1000000, completed=False))
        estimate, decision = decide_compile_from_pulse_history(BASE, samples)
        self.assertEqual(estimate.completed_samples, 5)
        self.assertLess(estimate.expected_reads_lower_bound, 1536.0)
        self.assertEqual(decision.mode, "ONLINE")

    def test_quality_regression_overrides_large_horizon(self):
        worse = CompileEconomics(
            build_cost_us=BASE.build_cost_us,
            online_query_us=BASE.online_query_us,
            compiled_query_us=BASE.compiled_query_us,
            online_quality=1.0,
            compiled_quality=0.99,
            expected_reads_before_invalidation=0.0,
            safety_factor=1.20,
        )
        estimate, decision = decide_compile_from_pulse_history(
            worse, history(10000, 11000, 12000, 10500, 11500, 13000)
        )
        self.assertGreater(estimate.expected_reads_lower_bound, 1536.0)
        self.assertEqual(decision.mode, "ONLINE")
        self.assertEqual(decision.reason, "COMPILED_QUALITY_WORSE")

    def test_no_query_saving_overrides_large_horizon(self):
        slow = CompileEconomics(
            build_cost_us=100.0,
            online_query_us=10.0,
            compiled_query_us=11.0,
            online_quality=1.0,
            compiled_quality=1.0,
            expected_reads_before_invalidation=0.0,
            safety_factor=1.20,
        )
        _, decision = decide_compile_from_pulse_history(
            slow, history(10000, 11000, 12000, 10500, 11500, 13000)
        )
        self.assertEqual(decision.mode, "ONLINE")
        self.assertEqual(decision.reason, "NO_POSITIVE_QUERY_SAVING")

    def test_malformed_negative_lifetime_is_rejected(self):
        with self.assertRaises(ValueError):
            estimate_read_horizon(history(10, 20, 30, 40) + [EpochReadLifetime(5, -1)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
