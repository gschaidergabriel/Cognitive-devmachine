from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate_v7 as gate


def v6_pass() -> dict:
    return {
        "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v6",
        "mechanism_runtime_vector_credit_candidate": True,
        "scientifically_independent_vector_candidate": True,
        "owner_trigger1_goal_credit_candidate": True,
        "owner_trigger1_direct_free_api_model_credit_candidate": True,
        "full_native_jspace_vector_control_candidate": True,
        "owner_target_failures": [],
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
    }


def factor_pass() -> dict:
    return {
        "schema": "CLAY_TRIGGER1_SEMANTIC_FACTORIAL_EVIDENCE_GATE/v1",
        "evidence_bound_semantic_factorial_candidate": True,
        "calibration_factorial_receipt_sha256": "a" * 64,
        "holdout_factorial_receipt_sha256": "b" * 64,
        "semantic_interaction_binding_sha256": "c" * 64,
        "failures": [],
        "canonical_credit_minted": False,
    }


class Trigger1JSpacePromotionGateV7Tests(unittest.TestCase):
    def test_v6_plus_case_bound_factorial_can_remain_research_candidate(self):
        with (
            patch.object(gate.v6, "adjudicate", return_value=v6_pass()),
            patch.object(gate.factorial, "adjudicate", return_value=factor_pass()),
        ):
            verdict = gate.adjudicate({})
        self.assertTrue(verdict["case_bound_semantic_factorial_evidence_pass"])
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertTrue(verdict["full_native_jspace_vector_control_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])
        self.assertFalse(verdict["training_credit"])

    def test_v6_pass_cannot_bypass_failed_case_bound_factorial(self):
        failed = factor_pass()
        failed["evidence_bound_semantic_factorial_candidate"] = False
        failed["failures"] = ["HOLDOUT_FULL_THREE_BY_THREE_FACTORIAL_REQUIRED"]
        with (
            patch.object(gate.v6, "adjudicate", return_value=v6_pass()),
            patch.object(gate.factorial, "adjudicate", return_value=failed),
        ):
            verdict = gate.adjudicate({})
        self.assertTrue(verdict["v6_scientific_candidate"])
        self.assertFalse(verdict["case_bound_semantic_factorial_evidence_pass"])
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["full_native_jspace_vector_control_candidate"])
        self.assertIn(
            "SEMANTIC_FACTORIAL_EVIDENCE:HOLDOUT_FULL_THREE_BY_THREE_FACTORIAL_REQUIRED",
            verdict["owner_target_failures"],
        )

    def test_case_bound_factorial_pass_cannot_repair_v6_failure(self):
        base = v6_pass()
        base["scientifically_independent_vector_candidate"] = False
        base["owner_trigger1_goal_credit_candidate"] = False
        base["full_native_jspace_vector_control_candidate"] = False
        with (
            patch.object(gate.v6, "adjudicate", return_value=base),
            patch.object(gate.factorial, "adjudicate", return_value=factor_pass()),
        ):
            verdict = gate.adjudicate({})
        self.assertTrue(verdict["case_bound_semantic_factorial_evidence_pass"])
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["full_native_jspace_vector_control_candidate"])

    def test_mechanism_component_evidence_is_not_erased_by_factorial_failure(self):
        failed = factor_pass()
        failed["evidence_bound_semantic_factorial_candidate"] = False
        failed["failures"] = ["CALIBRATION_SEMANTIC_FACTORIAL_RECEIPT_MISMATCH"]
        with (
            patch.object(gate.v6, "adjudicate", return_value=v6_pass()),
            patch.object(gate.factorial, "adjudicate", return_value=failed),
        ):
            verdict = gate.adjudicate({})
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])


if __name__ == "__main__":
    unittest.main()
