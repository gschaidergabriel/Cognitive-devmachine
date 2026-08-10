import unittest

from research_entity.runtime.gwt_sibling_quorum_workspace_v1 import benchmark, run_episode


class GWTSiblingQuorumWorkspaceV1Test(unittest.TestCase):
    def test_peer_identity_and_lease_controls_fail_closed(self):
        rows=[run_episode(i) for i in range(500)]
        self.assertTrue(all(r['forged_origin_rejected'] for r in rows))
        self.assertTrue(all(r['stale_lease_rejected'] for r in rows))
        self.assertEqual(sum(r['self_attribution_errors'] for r in rows),0)

    def test_quorum_can_beat_single_but_not_strong_simple_reducer(self):
        result=benchmark(4_000)
        self.assertGreater(result['quorum_gain_vs_single_accuracy'],0)
        self.assertLess(result['quorum_gain_vs_median_accuracy'],0)
        self.assertLess(result['quorum_gain_vs_median_utility'],0)
        self.assertEqual(
            result['promotion_decision'],
            'REFUTED_USE_SIMPLE_PROVENANCE_VALIDATED_MEDIAN_REDUCER',
        )

    def test_byzantine_peer_exposes_quorum_fragility(self):
        result=benchmark(4_000)
        self.assertLess(result['byzantine']['quorum_accuracy'],result['byzantine']['median_accuracy'])
        self.assertLess(result['byzantine']['quorum_utility'],result['byzantine']['median_utility'])

    def test_exchange_lesion_is_explicit(self):
        result=benchmark(4_000)
        self.assertIn('lesion_accuracy',result['all'])
        self.assertIn('lesion_utility',result['all'])


if __name__=='__main__':
    unittest.main()
