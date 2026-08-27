from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate_v13 as gate

V12_POSITIVE = {
    "abstract_native_semantic_jspace_candidate": True,
    "scientifically_independent_vector_candidate": True,
    "owner_trigger1_goal_credit_candidate": True,
    "modular_hcu_jspace_control_candidate": True,
    "cross_scope_causal_effect_equivalence_candidate": False,
    "v12_failures": [],
}
RAW_PASS = {"raw_abstract_state_evidence_pass": True, "failures": [], "readout": {}, "native_causal": {}, "opaque_code": {}}
RAW_FAIL = {"raw_abstract_state_evidence_pass": False, "failures": ["RAW_NATIVE_CAUSAL_ROWS_REQUIRED"], "readout": {}, "native_causal": {}, "opaque_code": {}}


class PromotionV13Tests(unittest.TestCase):
    def test_v12_positive_flags_cannot_escape_failed_raw_causal_gate(self):
        with mock.patch.object(gate.v12, "adjudicate", return_value=V12_POSITIVE), mock.patch.object(gate.raw_gate, "adjudicate", return_value=RAW_FAIL):
            r = gate.adjudicate({})
        self.assertFalse(r["abstract_native_semantic_jspace_candidate"])
        self.assertFalse(r["scientifically_independent_vector_candidate"])
        self.assertFalse(r["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(r["owner_trigger1_direct_free_api_model_credit_candidate"])
        self.assertFalse(r["modular_hcu_jspace_control_candidate"])

    def test_full_v12_and_raw_conjunction_can_form_nonminting_candidate(self):
        with mock.patch.object(gate.v12, "adjudicate", return_value=V12_POSITIVE), mock.patch.object(gate.raw_gate, "adjudicate", return_value=RAW_PASS):
            r = gate.adjudicate({})
        self.assertTrue(r["abstract_native_semantic_jspace_candidate"])
        self.assertTrue(r["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(r["canonical_credit_minted"])
        self.assertFalse(r["strict_micro_mechanistic_identity_candidate"])

    def test_cross_scope_equivalence_is_not_micro_identity(self):
        base = dict(V12_POSITIVE, cross_scope_causal_effect_equivalence_candidate=True)
        with mock.patch.object(gate.v12, "adjudicate", return_value=base), mock.patch.object(gate.raw_gate, "adjudicate", return_value=RAW_PASS):
            r = gate.adjudicate({})
        self.assertTrue(r["cross_scope_causal_effect_equivalence_candidate"])
        self.assertFalse(r["strict_micro_mechanistic_identity_candidate"])


if __name__ == "__main__":
    unittest.main()
