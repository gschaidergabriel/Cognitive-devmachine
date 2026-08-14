import unittest

from research_entity.runtime.gwt_reboot_echo_workspace_v1 import benchmark, run_episode


class GWTRebootEchoWorkspaceV1Test(unittest.TestCase):
    def test_no_phantom_pulses_or_downtime_cognition_claims(self):
        rows=[run_episode(i) for i in range(500)]
        self.assertEqual(sum(r['phantom_pulses_materialized'] for r in rows),0)
        self.assertFalse(any(r['downtime_cognition_claimed'] for r in rows))

    def test_echo_lesion_is_normal_control(self):
        result=benchmark(2_000)
        self.assertEqual(result['echo_lesion_control_rate'],1.0)

    def test_echo_loses_to_strong_checkpoint_plus_current_evidence_control(self):
        result=benchmark(5_000)
        self.assertLess(result['all']['echo_accuracy'],result['all']['control_accuracy'])
        self.assertLessEqual(result['all']['echo_utility'],result['all']['control_utility'])
        self.assertEqual(
            result['promotion_decision'],
            'REFUTED_USE_NORMAL_ELAPSED_CHECKPOINT_PLUS_CURRENT_EVIDENCE',
        )

    def test_short_gap_exposes_sticky_echo_hysteresis(self):
        result=benchmark(5_000)
        self.assertLess(result['short_gap']['echo_gain_vs_control'],0)
        self.assertGreater(result['short_gap']['echo_change_rate'],result['long_gap']['echo_change_rate'])


if __name__=='__main__':
    unittest.main()
