from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate_v8 as gate


def base_v7(passes: bool = True) -> dict:
    return {
        "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v7",
        "scientifically_independent_vector_candidate": passes,
        "owner_trigger1_goal_credit_candidate": passes,
        "owner_trigger1_direct_free_api_model_credit_candidate": passes,
        "modular_hcu_jspace_control_candidate": passes,
        "full_native_jspace_vector_control_candidate": passes,
        "v7_failures": [] if passes else ["V7_FAIL"],
        "canonical_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
    }


def binding(passes: bool = True) -> dict:
    return {
        "schema": "CLAY_TRIGGER1_PREREG_RUNTIME_BINDING_GATE/v1",
        "pass": passes,
        "failures": [] if passes else ["PLAN_RUNTIME_DRIFT"],
        "bound_plan_sha256": "a" * 64,
        "bound_preregistration_receipt_sha256": "b" * 64,
    }


class Trigger1PromotionGateV8Tests(unittest.TestCase):
    def test_positive_candidate_requires_both_layers(self):
        with patch.object(gate.v7, "adjudicate", return_value=base_v7(True)), patch.object(
            gate.prereg_binding, "validate", return_value=binding(True)
        ):
            verdict = gate.adjudicate({})
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertTrue(verdict["modular_hcu_jspace_control_candidate"])
        self.assertTrue(verdict["full_native_jspace_vector_control_candidate"])
        self.assertTrue(verdict["preregistration_runtime_binding_pass"])
        self.assertFalse(verdict["canonical_credit_minted"])

    def test_binding_failure_revokes_all_positive_candidate_status(self):
        with patch.object(gate.v7, "adjudicate", return_value=base_v7(True)), patch.object(
            gate.prereg_binding, "validate", return_value=binding(False)
        ):
            verdict = gate.adjudicate({})
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["modular_hcu_jspace_control_candidate"])
        self.assertFalse(verdict["full_native_jspace_vector_control_candidate"])
        self.assertIn("PLAN_RUNTIME_DRIFT", verdict["v8_failures"])

    def test_binding_cannot_rescue_v7_failure(self):
        with patch.object(gate.v7, "adjudicate", return_value=base_v7(False)), patch.object(
            gate.prereg_binding, "validate", return_value=binding(True)
        ):
            verdict = gate.adjudicate({})
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["modular_hcu_jspace_control_candidate"])
        self.assertFalse(verdict["full_native_jspace_vector_control_candidate"])
        self.assertIn("V7_FAIL", verdict["v8_failures"])

    def test_credit_fields_remain_non_minting(self):
        with patch.object(gate.v7, "adjudicate", return_value=base_v7(True)), patch.object(
            gate.prereg_binding, "validate", return_value=binding(True)
        ):
            verdict = gate.adjudicate({})
        self.assertFalse(verdict["canonical_credit_minted"])
        self.assertFalse(verdict["canonical_semantics_promotion"])
        self.assertFalse(verdict["whole_entityos_hcu_credit"])
        self.assertFalse(verdict["whole_hcu_credit"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])
        self.assertFalse(verdict["training_credit"])


if __name__ == "__main__":
    unittest.main()
