from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate_v12 as gate
from tests.test_trigger1_reconstructive_lexical_audit_gate_v1 import candidate


class PromotionV12Test(unittest.TestCase):
    def test_positive_v11_requires_reconstructed_text_audit(self):
        c = candidate()
        with mock.patch.object(gate.v11, "adjudicate", return_value={
            "abstract_native_semantic_jspace_candidate": True,
            "cross_scope_causal_effect_equivalence_candidate": True,
            "v11_failures": [],
        }):
            result = gate.adjudicate(c)
        self.assertTrue(result["abstract_native_semantic_jspace_candidate"], result["v12_failures"])
        self.assertTrue(result["reconstructive_lexical_audit_pass"])
        self.assertFalse(result["strict_micro_mechanistic_identity_candidate"])
        self.assertFalse(result["native_last_token_causal_identity_required"])
        self.assertFalse(result["canonical_credit_minted"])

    def test_boolean_v11_lexical_claim_cannot_rescue_actual_overlap(self):
        c = candidate()
        rows = c["reconstructive_lexical_audit"]["basis_rows"]
        rows[3]["prompt"] = rows[3]["prompt"].replace("admitted", "ratified")
        with mock.patch.object(gate.v11, "adjudicate", return_value={
            "abstract_native_semantic_jspace_candidate": True,
            "cross_scope_causal_effect_equivalence_candidate": False,
            "v11_failures": [],
        }):
            result = gate.adjudicate(c)
        self.assertFalse(result["abstract_native_semantic_jspace_candidate"])
        self.assertFalse(result["reconstructive_lexical_audit_pass"])
        self.assertTrue(any("LEXICAL_OVERLAP" in x for x in result["v12_failures"]))

    def test_reconstructive_pass_cannot_rescue_failed_v11(self):
        c = candidate()
        with mock.patch.object(gate.v11, "adjudicate", return_value={
            "abstract_native_semantic_jspace_candidate": False,
            "cross_scope_causal_effect_equivalence_candidate": False,
            "v11_failures": ["UPSTREAM_V11_FAIL"],
        }):
            result = gate.adjudicate(c)
        self.assertFalse(result["abstract_native_semantic_jspace_candidate"])
        self.assertTrue(result["reconstructive_lexical_audit_pass"])
        self.assertIn("UPSTREAM_V11_FAIL", result["v12_failures"])


if __name__ == "__main__":
    unittest.main()
