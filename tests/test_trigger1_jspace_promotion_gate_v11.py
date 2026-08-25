import unittest
from unittest import mock

BASE_PASS = {
    "scientifically_independent_vector_candidate": True,
    "owner_trigger1_goal_credit_candidate": True,
    "modular_hcu_jspace_control_candidate": True,
    "v10_failures": [],
}
ABSTRACT_PASS = {
    "native_broadcast_abstract_state_candidate": True,
    "cross_intervention_equivalence_candidate": False,
    "native_scope_failures": [],
    "failures": [],
    "claim_scope": "NATIVE_QWEN06_Q8_LLAMA_CPP_CVEC_BROADCAST_ABSTRACT_STATE_ONLY",
}
ABSTRACT_FAIL = {
    "native_broadcast_abstract_state_candidate": False,
    "cross_intervention_equivalence_candidate": False,
    "native_scope_failures": ["LEXICAL_PAYLOAD_OVERLAP:BASIS:HOLDOUT:x"],
    "failures": ["LEXICAL_PAYLOAD_OVERLAP:BASIS:HOLDOUT:x"],
    "claim_scope": "BLOCKED",
}


class PromotionV11Tests(unittest.TestCase):
    def test_v10_positive_still_blocked_without_abstract_state(self):
        from tools import trigger1_jspace_promotion_gate_v11 as gate
        with mock.patch.object(gate.v10, "adjudicate", return_value=BASE_PASS), mock.patch.object(gate.abstract_gate, "adjudicate", return_value=ABSTRACT_FAIL):
            result = gate.adjudicate({})
        self.assertFalse(result["scientifically_independent_vector_candidate"])
        self.assertFalse(result["owner_trigger1_goal_credit_candidate"])

    def test_native_abstract_state_allows_narrow_promotion(self):
        from tools import trigger1_jspace_promotion_gate_v11 as gate
        with mock.patch.object(gate.v10, "adjudicate", return_value=BASE_PASS), mock.patch.object(gate.abstract_gate, "adjudicate", return_value=ABSTRACT_PASS):
            result = gate.adjudicate({})
        self.assertTrue(result["scientifically_independent_vector_candidate"])
        self.assertTrue(result["native_broadcast_abstract_state_candidate"])
        self.assertFalse(result["cross_intervention_equivalence_candidate"])

    def test_cross_equivalence_is_independent_stronger_flag(self):
        from tools import trigger1_jspace_promotion_gate_v11 as gate
        abstract = dict(ABSTRACT_PASS, cross_intervention_equivalence_candidate=True)
        with mock.patch.object(gate.v10, "adjudicate", return_value=BASE_PASS), mock.patch.object(gate.abstract_gate, "adjudicate", return_value=abstract):
            result = gate.adjudicate({})
        self.assertTrue(result["owner_trigger1_goal_credit_candidate"])
        self.assertTrue(result["cross_intervention_equivalence_candidate"])


if __name__ == "__main__":
    unittest.main()
