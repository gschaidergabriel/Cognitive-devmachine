import unittest
from loop_dynamics_reference import (
    DynamicRegime,
    LoopDynamicsReadout,
    RecurrenceDecision,
    decide_recurrence,
)


def r(**kw):
    base=dict(loop_id="l1",loop_family="reasoning",timescale="turn",state_epoch=7,
              state_delta_norm=.02,residual_pressure=.04,recurrence_count=2,
              recurrence_budget=8,marginal_utility_next=-.02)
    base.update(kw)
    return LoopDynamicsReadout(**base)


class TestLoopDynamicsReference(unittest.TestCase):
    def test_convergence_requires_low_pressure(self):
        x=decide_recurrence(r())
        self.assertEqual(x.regime,DynamicRegime.CONVERGING_FIXED_POINT)
        self.assertEqual(x.decision,RecurrenceDecision.HALT_CANDIDATE_CONVERGED)

    def test_low_delta_high_pressure_is_not_convergence(self):
        x=decide_recurrence(r(residual_pressure=.8,marginal_utility_next=.2))
        self.assertEqual(x.regime,DynamicRegime.STALLED)
        self.assertNotEqual(x.decision,RecurrenceDecision.HALT_CANDIDATE_CONVERGED)

    def test_stall_without_margin_escalates(self):
        x=decide_recurrence(r(residual_pressure=.8,marginal_utility_next=.01))
        self.assertEqual(x.decision,RecurrenceDecision.ESCALATE_STALLED)

    def test_productive_cycle_continues(self):
        x=decide_recurrence(r(state_delta_norm=.25,residual_pressure=.4,
                              marginal_utility_next=.18,oscillation_indicator=.8))
        self.assertEqual(x.regime,DynamicRegime.PRODUCTIVE_LIMIT_CYCLE)
        self.assertEqual(x.decision,RecurrenceDecision.CONTINUE)

    def test_overthinking_rolls_back_when_checkpoint_exists(self):
        x=decide_recurrence(r(state_delta_norm=.7,residual_pressure=.5,
                              marginal_utility_next=-.2,overthinking_indicator=.9,
                              rollback_ref="checkpoint:6"))
        self.assertEqual(x.regime,DynamicRegime.DIVERGING_OR_OVERTHINKING)
        self.assertEqual(x.decision,RecurrenceDecision.ROLLBACK)

    def test_budget_exhaustion_blocks_productive_continue(self):
        x=decide_recurrence(r(state_delta_norm=.25,residual_pressure=.4,
                              marginal_utility_next=.18,oscillation_indicator=.8,
                              recurrence_count=8,recurrence_budget=8))
        self.assertEqual(x.regime,DynamicRegime.CHAOTIC_OR_UNCLASSIFIED)
        self.assertEqual(x.decision,RecurrenceDecision.ROUTE)

    def test_receipt_never_mints_effect_authority(self):
        x=decide_recurrence(r())
        self.assertEqual(x.authority,"PROPOSAL_ONLY")
        self.assertEqual(len(x.input_hash),64)
        self.assertEqual(len(x.receipt_hash),64)

    def test_deterministic_receipt(self):
        self.assertEqual(decide_recurrence(r()),decide_recurrence(r()))

if __name__ == '__main__': unittest.main()
