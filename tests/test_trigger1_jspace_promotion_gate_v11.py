from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate_v11 as gate


class PromotionV11CompositionTests(unittest.TestCase):
    def test_requires_both_v10_and_abstraction(self):
        base = {
            "scientifically_independent_vector_candidate": True,
            "owner_trigger1_goal_credit_candidate": True,
            "modular_hcu_jspace_control_candidate": True,
            "v10_failures": [],
        }
        hard = {
            "semantic_abstraction_candidate": True,
            "abstraction_audit_sha256": "a" * 64,
            "basis_prompt_universe_sha256": "b" * 64,
            "failures": [],
        }
        with patch.object(gate.v10, "adjudicate", return_value=base), patch.object(gate.abstraction, "adjudicate", return_value=hard):
            result = gate.adjudicate({})
        self.assertTrue(result["owner_trigger1_goal_credit_candidate"])
        self.assertTrue(result["semantic_abstraction_candidate"])
        self.assertFalse(result["canonical_credit_minted"])

    def test_v10_positive_cannot_bypass_abstraction_failure(self):
        base = {
            "scientifically_independent_vector_candidate": True,
            "owner_trigger1_goal_credit_candidate": True,
            "modular_hcu_jspace_control_candidate": True,
            "v10_failures": [],
        }
        hard = {"semantic_abstraction_candidate": False, "failures": ["LEXICAL_SPLIT_OVERLAP:BASIS:HOLDOUT:x"]}
        with patch.object(gate.v10, "adjudicate", return_value=base), patch.object(gate.abstraction, "adjudicate", return_value=hard):
            result = gate.adjudicate({})
        self.assertFalse(result["scientifically_independent_vector_candidate"])
        self.assertFalse(result["owner_trigger1_goal_credit_candidate"])
        self.assertIn("LEXICAL_SPLIT_OVERLAP:BASIS:HOLDOUT:x", result["v11_failures"])

    def test_abstraction_positive_cannot_bypass_v10_failure(self):
        base = {
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "modular_hcu_jspace_control_candidate": False,
            "v10_failures": ["PREREGISTRATION_PLAN_SHA256_BINDING_MISMATCH"],
        }
        hard = {"semantic_abstraction_candidate": True, "failures": []}
        with patch.object(gate.v10, "adjudicate", return_value=base), patch.object(gate.abstraction, "adjudicate", return_value=hard):
            result = gate.adjudicate({})
        self.assertFalse(result["owner_trigger1_goal_credit_candidate"])
        self.assertIn("PREREGISTRATION_PLAN_SHA256_BINDING_MISMATCH", result["v11_failures"])


if __name__ == "__main__":
    unittest.main()
