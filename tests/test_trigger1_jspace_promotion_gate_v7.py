from __future__ import annotations

from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

# The real modularity companion composes promotion-v6. This deterministic composition
# harness supplies only its adjudication surface so v7 can be tested without importing
# the full predecessor chain.
if "trigger1_jspace_modularity_companion_v1" not in sys.modules:
    stub = types.ModuleType("trigger1_jspace_modularity_companion_v1")
    stub.adjudicate = lambda _candidate: {}
    sys.modules["trigger1_jspace_modularity_companion_v1"] = stub

import trigger1_jspace_promotion_gate_v7 as v7


BASE_PASS = {
    "scientifically_independent_vector_candidate": True,
    "owner_trigger1_goal_credit_candidate": True,
    "owner_trigger1_direct_free_api_model_credit_candidate": True,
    "modular_hcu_jspace_control_candidate": True,
    "full_native_jspace_vector_control_candidate": True,
    "v5_specificity_failures": [],
    "modularity_failures": [],
}
BOUND_PASS = {
    "evidence_bound_semantic_factorial_candidate": True,
    "failures": [],
    "calibration_factorial_receipt_sha256": "a" * 64,
    "holdout_factorial_receipt_sha256": "b" * 64,
    "semantic_interaction_binding_sha256": "c" * 64,
}


class Trigger1PromotionGateV7Tests(unittest.TestCase):
    def test_upstream_pass_without_evidence_binding_is_rejected(self):
        with patch.object(v7.modularity, "adjudicate", return_value=dict(BASE_PASS)), patch.object(
            v7.factorial,
            "adjudicate",
            return_value={**BOUND_PASS, "evidence_bound_semantic_factorial_candidate": False, "failures": ["LYING_SUMMARY"]},
        ):
            verdict = v7.adjudicate({})
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["modular_hcu_jspace_control_candidate"])
        self.assertFalse(verdict["full_native_jspace_vector_control_candidate"])
        self.assertIn("LYING_SUMMARY", verdict["v7_failures"])

    def test_evidence_binding_cannot_repair_upstream_scientific_failure(self):
        upstream = {
            **BASE_PASS,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "full_native_jspace_vector_control_candidate": False,
        }
        with patch.object(v7.modularity, "adjudicate", return_value=upstream), patch.object(
            v7.factorial, "adjudicate", return_value=dict(BOUND_PASS)
        ):
            verdict = v7.adjudicate({})
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["full_native_jspace_vector_control_candidate"])

    def test_both_chains_must_pass_and_verdict_remains_non_minting(self):
        with patch.object(v7.modularity, "adjudicate", return_value=dict(BASE_PASS)), patch.object(
            v7.factorial, "adjudicate", return_value=dict(BOUND_PASS)
        ):
            verdict = v7.adjudicate({})
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertTrue(verdict["modular_hcu_jspace_control_candidate"])
        self.assertTrue(verdict["full_native_jspace_vector_control_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])
        self.assertFalse(verdict["training_credit"])


if __name__ == "__main__":
    unittest.main()
