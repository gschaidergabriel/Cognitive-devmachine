import unittest

from research_entity.runtime.gwt_chrono_bridge_counterfactual_v1 import benchmark, episode


class GWTChronoBridgeCounterfactualV1Test(unittest.TestCase):
    def test_simulated_slots_never_materialize_phantom_pulses(self):
        self.assertEqual(
            sum(episode(i)['phantom_pulses_materialized'] for i in range(500)), 0
        )

    def test_gap_awareness_beats_stale_checkpoint(self):
        result = benchmark(1_000)
        self.assertGreater(result['direct_gain_vs_stale'], 0)
        self.assertGreater(result['direct_accuracy'], result['stale_accuracy'])

    def test_chrono_bridge_is_refuted_by_direct_elapsed_time_recompute(self):
        result = benchmark(1_000)
        self.assertEqual(result['chrono_equals_direct_rate'], 1.0)
        self.assertAlmostEqual(result['chrono_gain_vs_direct'], 0.0, places=14)
        self.assertGreater(result['chrono_work_ratio_vs_direct'], 100)
        self.assertEqual(
            result['promotion_decision'],
            'REFUTED_AS_DISTINCT_MECHANISM_USE_DIRECT_TIME_RECOMPUTE',
        )

    def test_shuffled_gap_hurts_recovery(self):
        result = benchmark(1_000)
        self.assertGreater(result['direct_accuracy'], result['shuffled_accuracy'])


if __name__ == '__main__':
    unittest.main()
