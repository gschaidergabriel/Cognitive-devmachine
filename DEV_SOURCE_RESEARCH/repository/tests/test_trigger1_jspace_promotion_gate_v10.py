from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate_v10 as gate


def v7_result(passes: bool) -> dict:
    return {
        "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v7",
        "scientifically_independent_vector_candidate": passes,
        "owner_trigger1_goal_credit_candidate": passes,
        "modular_hcu_jspace_control_candidate": passes,
        "v7_failures": [] if passes else ["V7_FAIL"],
        "canonical_credit_minted": False,
    }


def binding_result(passes: bool) -> dict:
    return {
        "schema": "CLAY_TRIGGER1_PREREG_RUNTIME_BINDING_GATE/v2",
        "pass": passes,
        "failures": [] if passes else ["EXACT_CASE_PLAN_BINDING_FAIL"],
        "bound_plan_sha256": "a" * 64,
        "bound_preregistration_receipt_sha256": "b" * 64,
        "bound_factorial_case_plan_sha256": {
            "CALIBRATION": "c" * 64,
            "HOLDOUT": "d" * 64,
        },
    }


class Trigger1PromotionGateV10Tests(unittest.TestCase):
    def test_positive_requires_v7_and_exact_binding_v2(self):
        with patch.object(gate.v7, "adjudicate", return_value=v7_result(True)), patch.object(
            gate.prereg_binding_v2, "validate", return_value=binding_result(True)
        ):
            verdict = gate.adjudicate({})
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertTrue(verdict["modular_hcu_jspace_control_candidate"])
        self.assertTrue(verdict["preregistration_runtime_binding_v2_pass"])

    def test_exact_binding_failure_revokes_all_positive_status(self):
        with patch.object(gate.v7, "adjudicate", return_value=v7_result(True)), patch.object(
            gate.prereg_binding_v2, "validate", return_value=binding_result(False)
        ):
            verdict = gate.adjudicate({})
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["modular_hcu_jspace_control_candidate"])
        self.assertIn("EXACT_CASE_PLAN_BINDING_FAIL", verdict["v10_failures"])

    def test_binding_cannot_rescue_v7_failure(self):
        with patch.object(gate.v7, "adjudicate", return_value=v7_result(False)), patch.object(
            gate.prereg_binding_v2, "validate", return_value=binding_result(True)
        ):
            verdict = gate.adjudicate({})
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertIn("V7_FAIL", verdict["v10_failures"])

    def test_all_credit_fields_remain_non_minting(self):
        with patch.object(gate.v7, "adjudicate", return_value=v7_result(True)), patch.object(
            gate.prereg_binding_v2, "validate", return_value=binding_result(True)
        ):
            verdict = gate.adjudicate({})
        for key in (
            "canonical_credit_minted",
            "canonical_semantics_promotion",
            "whole_entityos_hcu_credit",
            "whole_hcu_credit",
            "jspace_model_runtime_credit",
            "training_credit",
        ):
            self.assertFalse(verdict[key], key)


if __name__ == "__main__":
    unittest.main()
