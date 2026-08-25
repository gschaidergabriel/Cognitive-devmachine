import unittest
from unittest import mock

from tools import trigger1_jspace_promotion_gate_v12 as gate

V11_POSITIVE={
    'abstract_native_semantic_jspace_candidate':True,
    'scientifically_independent_vector_candidate':True,
    'owner_trigger1_goal_credit_candidate':True,
    'modular_hcu_jspace_control_candidate':True,
    'cross_scope_causal_effect_equivalence_candidate':False,
    'v11_failures':[],
}
RAW_PASS={'raw_abstract_state_evidence_pass':True,'failures':[],'readout':{},'native_causal':{},'opaque_code':{}}
RAW_FAIL={'raw_abstract_state_evidence_pass':False,'failures':['RAW_PROMPT_DESIGN_REQUIRED'],'readout':{},'native_causal':{},'opaque_code':{}}


class PromotionV12Tests(unittest.TestCase):
    def test_v11_positive_cannot_leak_owner_credit_without_raw_evidence(self):
        with mock.patch.object(gate.v11,'adjudicate',return_value=V11_POSITIVE), mock.patch.object(gate.raw_gate,'adjudicate',return_value=RAW_FAIL):
            result=gate.adjudicate({})
        self.assertFalse(result['abstract_native_semantic_jspace_candidate'])
        self.assertFalse(result['scientifically_independent_vector_candidate'])
        self.assertFalse(result['owner_trigger1_goal_credit_candidate'])
        self.assertFalse(result['modular_hcu_jspace_control_candidate'])

    def test_full_conjunction_can_form_candidate_without_minting_credit(self):
        with mock.patch.object(gate.v11,'adjudicate',return_value=V11_POSITIVE), mock.patch.object(gate.raw_gate,'adjudicate',return_value=RAW_PASS):
            result=gate.adjudicate({})
        self.assertTrue(result['abstract_native_semantic_jspace_candidate'])
        self.assertTrue(result['owner_trigger1_goal_credit_candidate'])
        self.assertFalse(result['canonical_credit_minted'])
        self.assertFalse(result['strict_micro_mechanistic_identity_candidate'])

    def test_cross_scope_equivalence_stays_separate(self):
        base=dict(V11_POSITIVE,cross_scope_causal_effect_equivalence_candidate=True)
        with mock.patch.object(gate.v11,'adjudicate',return_value=base), mock.patch.object(gate.raw_gate,'adjudicate',return_value=RAW_PASS):
            result=gate.adjudicate({})
        self.assertTrue(result['cross_scope_causal_effect_equivalence_candidate'])
        self.assertFalse(result['strict_micro_mechanistic_identity_candidate'])


if __name__=='__main__':
    unittest.main()
