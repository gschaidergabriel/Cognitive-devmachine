import unittest

from omega.alignment import (
    AlignmentError,
    Decision,
    EffectBinding,
    ExecutorObservation,
    GateEvidence,
    OutcomeUnknown,
    dispatch,
)


def prepared():
    return EffectBinding.prepare(
        effect_id="effect-1",
        invocation_id="inv-1",
        tool_use_id="tool-1",
        delegation_id="deleg-1",
        child_identity_sha256="a" * 64,
        request={"op":"status"},
        organ_id="host:ai-core-node",
        owner_id="gabriel",
        machine_id="ai-core-node",
    )


def gate_for(b, decision=Decision.ALLOW, **overrides):
    values=dict(
        authority_ref="omega-effect-authority",
        decision_id="decision-1",
        decision=decision,
        effect_id=b.effect_id,
        binding_id=b.binding_id,
        invocation_id=b.invocation_id,
        tool_use_id=b.tool_use_id,
        delegation_id=b.delegation_id,
        child_identity_sha256=b.child_identity_sha256,
        request_sha256=b.request_sha256,
        organ_id=b.organ_id,
    )
    values.update(overrides)
    return GateEvidence(**values)


def observation_for(b, **overrides):
    values=dict(
        effect_id=b.effect_id,
        binding_id=b.binding_id,
        invocation_id=b.invocation_id,
        tool_use_id=b.tool_use_id,
        delegation_id=b.delegation_id,
        child_identity_sha256=b.child_identity_sha256,
        request_sha256=b.request_sha256,
        organ_id=b.organ_id,
        result_id="result-1",
        result_sha256="b"*64,
    )
    values.update(overrides)
    return ExecutorObservation(**values)


class AlignmentTests(unittest.TestCase):
    def test_exact_allow_dispatches(self):
        b=prepared()
        result=dispatch(b, authorize=lambda _:gate_for(b), executor=lambda _:observation_for(b))
        self.assertTrue(result.dispatched)

    def test_non_allow_never_dispatches(self):
        for decision in (Decision.DENY,Decision.REQUIRE_CONFIRMATION,Decision.DEGRADE_TO_PROPOSAL,Decision.UNKNOWN):
            b=prepared(); called=[]
            result=dispatch(b,authorize=lambda _,d=decision:gate_for(b,d),executor=lambda _:called.append(1))
            self.assertFalse(result.dispatched)
            self.assertEqual(called,[])

    def test_allow_for_other_request_is_rejected_before_executor(self):
        b=prepared(); called=[]
        with self.assertRaises(AlignmentError):
            dispatch(b,authorize=lambda _:gate_for(b,request_sha256="c"*64),executor=lambda _:called.append(1))
        self.assertEqual(called,[])

    def test_executor_exception_becomes_unknown_no_replay(self):
        b=prepared()
        with self.assertRaises(OutcomeUnknown):
            dispatch(b,authorize=lambda _:gate_for(b),executor=lambda _:(_ for _ in ()).throw(RuntimeError("boom")))

    def test_post_mismatch_becomes_unknown(self):
        b=prepared()
        with self.assertRaises(OutcomeUnknown):
            dispatch(b,authorize=lambda _:gate_for(b),executor=lambda _:observation_for(b,organ_id="host:andreas-maco"))


if __name__ == "__main__":
    unittest.main()
