import math
import unittest
from loop_dynamics_quality_gate import *


def R(**kw):
    base = dict(
        loop_id="gwt.reentry",
        state_epoch=17,
        state_delta_norm=.01,
        residual_pressure=.4,
        low_delta_streak=2,
        oscillation_indicator=0.0,
        marginal_utility_next=.03,
        residual_estimator_id="residual-v1",
        residual_estimator_version="1",
        residual_uncertainty=.01,
        measurement_age_cycles=0,
    )
    base.update(kw)
    return LoopDynamicsReadout(**base)


class GateTests(unittest.TestCase):
    def test_low_delta_high_residual_is_stalled(self):
        self.assertEqual(decide_recurrence(R()).decision, "ESCALATE_STALLED")

    def test_valid_low_residual_can_converge(self):
        x = decide_recurrence(R(residual_pressure=.03, low_delta_streak=3))
        self.assertEqual(x.decision, "HALT_CANDIDATE_CONVERGED")
        self.assertEqual(x.reason, "low_delta_and_low_residual_with_valid_readout")

    def test_high_delta_low_residual_cannot_mint_convergence(self):
        x = decide_recurrence(R(state_delta_norm=.20, residual_pressure=.03, low_delta_streak=0))
        self.assertEqual(x.decision, "CONTINUE")
        self.assertNotEqual(x.reason, "low_delta_and_low_residual_with_valid_readout")

    def test_single_low_delta_frame_cannot_mint_convergence(self):
        x = decide_recurrence(R(state_delta_norm=.01, residual_pressure=.03, low_delta_streak=1))
        self.assertEqual(x.decision, "CONTINUE")

    def test_noisy_residual_cannot_mint_convergence(self):
        x = decide_recurrence(R(residual_pressure=.03, residual_uncertainty=.2))
        self.assertEqual(x.decision, "ROUTE_READOUT_UNCERTAIN")
        self.assertEqual(x.authority, "NONE")
        self.assertFalse(x.effect_eligible)

    def test_stale_residual_cannot_mint_convergence(self):
        self.assertEqual(decide_recurrence(R(residual_pressure=.03, measurement_age_cycles=2)).decision, "ROUTE_READOUT_UNCERTAIN")

    def test_missing_estimator_identity_routes_uncertain(self):
        self.assertEqual(decide_recurrence(R(residual_estimator_id="")).decision, "ROUTE_READOUT_UNCERTAIN")

    def test_productive_cycle_can_continue(self):
        x = decide_recurrence(R(state_delta_norm=.08, residual_pressure=.28, low_delta_streak=0, oscillation_indicator=.8, marginal_utility_next=.04))
        self.assertEqual(x.decision, "CONTINUE")

    def test_negative_marginal_utility_can_halt_without_convergence_claim(self):
        x = decide_recurrence(R(state_delta_norm=.04, residual_pressure=.20, low_delta_streak=0, marginal_utility_next=-.01))
        self.assertEqual(x.decision, "HALT_MARGINAL")

    def test_receipt_hash_changes_with_readout(self):
        self.assertNotEqual(decide_recurrence(R()).readout_sha256, decide_recurrence(R(state_epoch=18)).readout_sha256)

    def test_decision_never_grants_authority(self):
        cases = [
            R(),
            R(residual_pressure=.03),
            R(residual_uncertainty=.2),
            R(measurement_age_cycles=3),
            R(state_delta_norm=.08, residual_pressure=.4, low_delta_streak=0),
        ]
        for r in cases:
            x = decide_recurrence(r)
            self.assertEqual(x.authority, "NONE")
            self.assertFalse(x.effect_eligible)
            self.assertTrue(x.effect_gate_required)

    def test_invalid_numeric_domains_rejected(self):
        cases = [
            R(residual_uncertainty=-1.0),
            R(measurement_age_cycles=-1),
            R(residual_uncertainty=math.nan),
            R(residual_pressure=math.nan),
            R(residual_pressure=-.1),
            R(state_delta_norm=math.inf),
            R(oscillation_indicator=1.1),
            R(low_delta_streak=-1),
        ]
        for r in cases:
            with self.subTest(r=r):
                with self.assertRaises(ValueError):
                    decide_recurrence(r)

    def test_policy_identity_is_receipt_bound(self):
        r = R(residual_pressure=.03, low_delta_streak=3)
        a = decide_recurrence(r, controller_policy_id="A", converged_residual=.08)
        b = decide_recurrence(r, controller_policy_id="B", converged_residual=.08)
        c = decide_recurrence(r, controller_policy_id="A", converged_residual=.02)
        self.assertEqual(a.readout_sha256, b.readout_sha256)
        self.assertNotEqual(a.policy_sha256, b.policy_sha256)
        self.assertNotEqual(a.receipt_sha256, b.receipt_sha256)
        self.assertEqual(a.readout_sha256, c.readout_sha256)
        self.assertNotEqual(a.policy_sha256, c.policy_sha256)
        self.assertNotEqual(a.receipt_sha256, c.receipt_sha256)
        self.assertNotEqual(a.decision, c.decision)

    def test_receipt_is_deterministic(self):
        self.assertEqual(decide_recurrence(R()), decide_recurrence(R()))

    def test_invalid_policy_rejected(self):
        with self.assertRaises(ValueError):
            decide_recurrence(R(), max_residual_uncertainty=math.nan)
        with self.assertRaises(ValueError):
            decide_recurrence(R(), max_measurement_age_cycles=-1)
        with self.assertRaises(ValueError):
            decide_recurrence(R(), stalled_residual=.01, converged_residual=.08)


if __name__ == "__main__":
    unittest.main(verbosity=2)
