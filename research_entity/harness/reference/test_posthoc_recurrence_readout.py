import unittest

from loop_dynamics_reference import LoopDynamicsReadout
from posthoc_recurrence_readout import PostHocDecision, decide_posthoc


def r(epoch, **kw):
    base = dict(
        loop_id="l1",
        loop_family="reasoning",
        timescale="turn",
        state_epoch=epoch,
        state_delta_norm=0.20,
        residual_pressure=0.30,
        recurrence_count=epoch,
        recurrence_budget=8,
        marginal_utility_next=0.10,
    )
    base.update(kw)
    return LoopDynamicsReadout(**base)


class TestPostHocRecurrenceReadout(unittest.TestCase):
    def test_requires_trajectory_before_halting(self):
        self.assertEqual(
            decide_posthoc([r(1, state_delta_norm=.01, residual_pressure=.02)]).decision,
            PostHocDecision.CONTINUE,
        )

    def test_halts_on_windowed_convergence(self):
        xs = [
            r(1, state_delta_norm=.08, residual_pressure=.15, marginal_utility_next=.02),
            r(2, state_delta_norm=.04, residual_pressure=.09, marginal_utility_next=.01),
            r(3, state_delta_norm=.02, residual_pressure=.04, marginal_utility_next=-.01),
        ]
        self.assertEqual(decide_posthoc(xs).decision, PostHocDecision.HALT_CANDIDATE_CONVERGED)

    def test_transient_low_delta_does_not_hide_pressure(self):
        xs = [
            r(1, state_delta_norm=.01, residual_pressure=.05),
            r(2, state_delta_norm=.02, residual_pressure=.50),
            r(3, state_delta_norm=.02, residual_pressure=.60, marginal_utility_next=.01),
        ]
        self.assertNotEqual(decide_posthoc(xs).decision, PostHocDecision.HALT_CANDIDATE_CONVERGED)

    def test_positive_recent_margin_continues(self):
        xs = [r(1), r(2, state_delta_norm=.18), r(3, state_delta_norm=.16)]
        self.assertEqual(decide_posthoc(xs).decision, PostHocDecision.CONTINUE)

    def test_divergence_rolls_back_when_checkpoint_exists(self):
        xs = [
            r(1, state_delta_norm=.30),
            r(2, state_delta_norm=.70),
            r(3, state_delta_norm=.95, overthinking_indicator=.7, rollback_ref="checkpoint:2"),
        ]
        self.assertEqual(decide_posthoc(xs).decision, PostHocDecision.ROLLBACK)

    def test_budget_exhaustion_routes(self):
        xs = [r(1), r(2), r(8, recurrence_count=8, recurrence_budget=8)]
        self.assertEqual(decide_posthoc(xs).decision, PostHocDecision.ROUTE)

    def test_receipt_is_deterministic_and_non_authoritative(self):
        xs = [r(1), r(2), r(3)]
        a, b = decide_posthoc(xs), decide_posthoc(xs)
        self.assertEqual(a, b)
        self.assertEqual(a.authority, "PROPOSAL_ONLY")
        self.assertEqual(len(a.trajectory_hash), 64)
        self.assertEqual(len(a.receipt_hash), 64)

    def test_mixed_loop_identity_rejected(self):
        xs = [r(1), r(2, loop_id="other"), r(3)]
        with self.assertRaises(ValueError):
            decide_posthoc(xs)

    def test_out_of_order_epoch_rejected(self):
        with self.assertRaises(ValueError):
            decide_posthoc([r(2), r(1)])


if __name__ == "__main__":
    unittest.main()
