import unittest

from frank_reward_state_reference import (
    EvidenceClass,
    RewardDimension,
    RewardKernel,
    RewardOutcomeEvidence,
)


def ev(*, dim, utility, verified=True, causal=1.0, confidence=1.0,
       cls=EvidenceClass.VERIFIED_OUTCOME, novelty=0.0, idx=1):
    return RewardOutcomeEvidence(
        episode_id="ep",
        outcome_id=f"o{idx}",
        dimension=dim,
        utility=utility,
        confidence=confidence,
        causal_credit=causal,
        evidence_class=cls,
        verified=verified,
        source_ref=f"receipt:{idx}",
        novelty=novelty,
    )


class RewardKernelTests(unittest.TestCase):
    def test_verified_success_learns_and_rpe_shrinks(self):
        k = RewardKernel()
        first = k.observe(ev(dim=RewardDimension.TASK, utility=0.9, idx=1))
        last = first
        for i in range(2, 14):
            last = k.observe(ev(dim=RewardDimension.TASK, utility=0.9, idx=i))
        self.assertTrue(first.admitted)
        self.assertGreater(first.phasic_aggregate, 0)
        self.assertLess(abs(last.phasic_aggregate), abs(first.phasic_aggregate))
        self.assertGreater(k.state.dimensions[RewardDimension.TASK].tonic, 0)

    def test_self_proposal_cannot_mint_material_reward(self):
        k = RewardKernel()
        for i in range(1, 100):
            r = k.observe(ev(
                dim=RewardDimension.NOVELTY,
                utility=1.0,
                verified=False,
                causal=0.0,
                cls=EvidenceClass.SELF_PROPOSAL,
                novelty=1.0,
                idx=i,
            ))
            self.assertFalse(r.admitted)
            self.assertLessEqual(r.exploration_nudge, 0.12)
        ds = k.state.dimensions[RewardDimension.NOVELTY]
        self.assertEqual(ds.tonic, 0.0)
        self.assertEqual(ds.predictions["fast"].mean, 0.0)

    def test_verified_refutation_can_be_positive_epistemic_value(self):
        k = RewardKernel()
        r = k.observe(RewardOutcomeEvidence(
            episode_id="ep",
            outcome_id="refuted-hypothesis",
            dimension=RewardDimension.EPISTEMIC,
            utility=0.7,
            confidence=0.95,
            causal_credit=0.9,
            evidence_class=EvidenceClass.VERIFIED_EPISTEMIC,
            verified=True,
            source_ref="experiment:refutation",
        ))
        self.assertTrue(r.admitted)
        self.assertGreater(r.phasic_aggregate, 0)

    def test_multi_timescale_reversal_fast_adapts_faster_than_slow(self):
        k = RewardKernel(habituation_enabled=False, opponent_enabled=False)
        for i in range(1, 25):
            k.observe(ev(dim=RewardDimension.TASK, utility=0.8, idx=i))
        for i in range(25, 30):
            k.observe(ev(dim=RewardDimension.TASK, utility=-0.8, idx=i))
        ds = k.state.dimensions[RewardDimension.TASK]
        target = -0.8
        fast_dist = abs(ds.predictions["fast"].mean - target)
        slow_dist = abs(ds.predictions["slow"].mean - target)
        self.assertLess(fast_dist, slow_dist)

    def test_low_rpe_without_pressure_is_not_stagnation(self):
        k = RewardKernel(habituation_enabled=False, opponent_enabled=False)
        for i in range(1, 50):
            k.observe(ev(dim=RewardDimension.TASK, utility=0.2, idx=i))
        self.assertFalse(k.control(unresolved_pressure=0.05).stagnation_candidate)

    def test_low_rpe_with_unresolved_pressure_is_stagnation(self):
        k = RewardKernel(habituation_enabled=False, opponent_enabled=False)
        for i in range(1, 80):
            k.observe(ev(dim=RewardDimension.TASK, utility=0.2, idx=i))
        self.assertTrue(k.control(unresolved_pressure=0.9).stagnation_candidate)

    def test_negative_safety_can_veto_positive_task_persistence(self):
        k = RewardKernel(habituation_enabled=False, opponent_enabled=False)
        for i in range(1, 18):
            k.observe(ev(dim=RewardDimension.TASK, utility=0.9, idx=i))
        for i in range(18, 32):
            k.observe(ev(dim=RewardDimension.SAFETY, utility=-1.0, idx=i))
        c = k.control(unresolved_pressure=0.7)
        self.assertTrue(c.safety_veto)
        self.assertGreaterEqual(c.disengagement_bias, 0.0)

    def test_causal_credit_scales_learning(self):
        a = RewardKernel(habituation_enabled=False, opponent_enabled=False)
        b = RewardKernel(habituation_enabled=False, opponent_enabled=False)
        ra = a.observe(ev(dim=RewardDimension.TASK, utility=1.0, causal=1.0, idx=1))
        rb = b.observe(ev(dim=RewardDimension.TASK, utility=1.0, causal=0.2, idx=1))
        self.assertGreater(ra.observed_value, rb.observed_value)
        self.assertGreater(abs(ra.phasic_aggregate), abs(rb.phasic_aggregate))

    def test_compatibility_projection_is_explicitly_nonidentical(self):
        k = RewardKernel()
        p = k.compatibility_projection()["historical_nacc_projection"]
        self.assertEqual(p["equivalence_status"], "COMPATIBILITY_VIEW_NOT_SEMANTIC_IDENTITY")


if __name__ == "__main__":
    unittest.main()
