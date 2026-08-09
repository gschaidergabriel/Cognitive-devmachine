import unittest

from loop_dynamics_reference import LoopDynamicsReadout
from recurrence_policy_differential import replay_policies


def r(epoch, **kw):
    base = dict(
        loop_id="l1",
        loop_family="reasoning",
        timescale="turn",
        state_epoch=epoch,
        state_delta_norm=.2,
        residual_pressure=.3,
        recurrence_count=epoch,
        recurrence_budget=8,
        marginal_utility_next=.1,
    )
    base.update(kw)
    return LoopDynamicsReadout(**base)


class TestRecurrencePolicyDifferential(unittest.TestCase):
    def test_transient_single_halt_is_visible_against_posthoc(self):
        xs = [
            r(1, state_delta_norm=.01, residual_pressure=.02, marginal_utility_next=-.01),
            r(2, state_delta_norm=.03, residual_pressure=.55, marginal_utility_next=.12),
            r(3, state_delta_norm=.04, residual_pressure=.50, marginal_utility_next=.10),
        ]
        out = replay_policies(xs)
        self.assertEqual(out["first_terminal"]["single_state_reference"]["state_epoch"], 1)
        self.assertIsNone(out["first_terminal"]["posthoc_trajectory"])
        self.assertEqual(out["first_terminal"]["fixed_depth_3"]["state_epoch"], 3)

    def test_shared_convergence_eventually_halts_both(self):
        xs = [
            r(1, state_delta_norm=.20, residual_pressure=.30, marginal_utility_next=.10),
            r(2, state_delta_norm=.04, residual_pressure=.08, marginal_utility_next=.01),
            r(3, state_delta_norm=.02, residual_pressure=.03, marginal_utility_next=-.01),
        ]
        out = replay_policies(xs)
        self.assertEqual(out["first_terminal"]["single_state_reference"]["decision"], "HALT_CANDIDATE_CONVERGED")
        self.assertEqual(out["first_terminal"]["posthoc_trajectory"]["decision"], "HALT_CANDIDATE_CONVERGED")

    def test_rollback_is_observable(self):
        xs = [
            r(1, state_delta_norm=.3),
            r(2, state_delta_norm=.7),
            r(3, state_delta_norm=.95, overthinking_indicator=.8, rollback_ref="checkpoint:2"),
        ]
        out = replay_policies(xs)
        self.assertEqual(out["policies"]["single_state_reference"][-1]["decision"], "ROLLBACK")
        self.assertEqual(out["policies"]["posthoc_trajectory"][-1]["decision"], "ROLLBACK")

    def test_deterministic_receipt(self):
        xs = [r(1), r(2), r(3)]
        self.assertEqual(replay_policies(xs), replay_policies(xs))
        self.assertEqual(replay_policies(xs)["authority"], "PROPOSAL_ONLY")

    def test_mixed_loop_rejected(self):
        with self.assertRaises(ValueError):
            replay_policies([r(1), r(2, loop_id="other")])


if __name__ == "__main__":
    unittest.main()
