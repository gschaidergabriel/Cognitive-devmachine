import unittest

from research_entity.runtime.gwt_split_pulse_twin_workspace_v1 import benchmark, run_episode


class SplitPulseTwinWorkspaceV1Test(unittest.TestCase):
    def test_origin_shuffle_is_rejected(self):
        self.assertTrue(run_episode(1)['origin_shuffle_rejected'])

    def test_no_self_attribution_error(self):
        self.assertEqual(
            sum(run_episode(i)['self_attribution_errors'] for i in range(500)), 0
        )

    def test_anti_phase_beats_naive_same_phase_duplicate_ignition(self):
        result = benchmark(4_000)
        self.assertGreater(result['anti_distinct_mean'], result['same_distinct_mean'])
        self.assertGreater(result['anti_gain_vs_same'], 0)

    def test_complex_twin_broadcast_is_refuted_by_simple_exact_seen_filter(self):
        result = benchmark(4_000)
        self.assertAlmostEqual(result['anti_gain_vs_simple'], 0.0, places=14)
        self.assertEqual(result['anti_equals_simple_rate'], 1.0)
        self.assertEqual(
            result['promotion_decision'],
            'REFUTED_AS_DISTINCT_MECHANISM_USE_SIMPLE_REENTRY_INHIBITION',
        )


if __name__ == '__main__':
    unittest.main()
