from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate_v5 as gate

HEX64 = "a" * 64


def complete_v5_candidate() -> dict:
    return {
        "runtime_intervention_class": "LOCAL_LLAMA_CPP_CVEC_APPLIED",
        "vector_derivation": {
            "model_facing_label_free": True,
            "lexically_disjoint_basis_families": True,
            "lexical_nuisance_projection_or_control": True,
            "lexical_nuisance_receipt_sha256": HEX64,
        },
        "controls": {
            "LABEL_ONLY_NUISANCE_VECTOR": {"runtime_receipt_sha256": HEX64},
        },
        "calibration": {
            "semantic_target_x_output_code_factorial": True,
            "residual_norm_relative_intervention": True,
            "operating_point_selected_on_calibration_only": True,
            "operating_point_receipt_sha256": HEX64,
        },
        "holdout": {
            "semantic_target_x_output_code_factorial": True,
            "per_family_semantic_target_interaction": True,
            "operating_point_frozen_before_holdout": True,
            "cross_family_direction_coherence_test": True,
            "cross_family_direction_coherence_receipt_sha256": HEX64,
            "off_target_drift_test": True,
            "off_target_drift_within_preregistered_threshold": True,
            "off_target_drift_receipt_sha256": HEX64,
        },
        "intervention": {
            "residual_norm_ratio": 0.05,
            "token_scope": "ALL_PROMPT_TOKENS",
            "scope_classification": "NATIVE_CVEC_ALL_PROMPT_TOKENS",
            "strict_last_token_replication_claimed": False,
        },
        "measurement_protocol": {
            "frozen_before_holdout": True,
            "protocol_sha256": HEX64,
            "preregistered_off_target_drift_threshold": 0.10,
        },
    }


class Trigger1JSpacePromotionGateV5Tests(unittest.TestCase):
    def test_complete_successor_metrology_passes_extra_guard(self):
        ok, failures = gate._extra_specificity_evidence(complete_v5_candidate())
        self.assertTrue(ok)
        self.assertEqual([], failures)

    def test_affirmative_only_style_candidate_cannot_satisfy_v5_by_omission(self):
        candidate = complete_v5_candidate()
        for key in (
            "model_facing_label_free",
            "lexically_disjoint_basis_families",
            "lexical_nuisance_projection_or_control",
        ):
            candidate["vector_derivation"].pop(key)
        candidate["calibration"].pop("semantic_target_x_output_code_factorial")
        candidate["holdout"].pop("semantic_target_x_output_code_factorial")

        ok, failures = gate._extra_specificity_evidence(candidate)

        self.assertFalse(ok)
        self.assertIn("MODEL_FACING_LABEL_FREE_BASIS_REQUIRED", failures)
        self.assertIn("LEXICALLY_DISJOINT_BASIS_FAMILIES_REQUIRED", failures)
        self.assertIn("LEXICAL_NUISANCE_PROJECTION_OR_CONTROL_REQUIRED", failures)
        self.assertIn("CALIBRATION_SEMANTIC_TARGET_X_OUTPUT_CODE_FACTORIAL_REQUIRED", failures)
        self.assertIn("HOLDOUT_SEMANTIC_TARGET_X_OUTPUT_CODE_FACTORIAL_REQUIRED", failures)

    def test_native_cvec_scope_cannot_be_mislabeled_last_token_replication(self):
        candidate = complete_v5_candidate()
        candidate["intervention"]["token_scope"] = "LAST_TOKEN_ONLY"
        candidate["intervention"]["strict_last_token_replication_claimed"] = True

        ok, failures = gate._extra_specificity_evidence(candidate)

        self.assertFalse(ok)
        self.assertIn("NATIVE_CVEC_REQUIRES_ALL_PROMPT_TOKENS_SCOPE_CLASSIFICATION", failures)

    def test_raw_gain_without_norm_calibration_and_frozen_operating_point_fails(self):
        candidate = complete_v5_candidate()
        candidate["calibration"]["residual_norm_relative_intervention"] = False
        candidate["calibration"]["operating_point_selected_on_calibration_only"] = False
        candidate["holdout"]["operating_point_frozen_before_holdout"] = False
        candidate["intervention"]["residual_norm_ratio"] = None

        ok, failures = gate._extra_specificity_evidence(candidate)

        self.assertFalse(ok)
        self.assertIn("CALIBRATION_RESIDUAL_NORM_RELATIVE_INTERVENTION_REQUIRED", failures)
        self.assertIn("OPERATING_POINT_MUST_BE_SELECTED_ON_CALIBRATION_ONLY", failures)
        self.assertIn("OPERATING_POINT_MUST_BE_FROZEN_BEFORE_HOLDOUT", failures)
        self.assertIn("POSITIVE_RESIDUAL_NORM_RATIO_REQUIRED", failures)

    def test_v5_never_promotes_if_v4_scientific_gate_is_false(self):
        candidate = complete_v5_candidate()
        base = {
            "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v4",
            "mechanism_runtime_vector_credit_candidate": True,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "owner_trigger1_direct_free_api_model_credit_candidate": False,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "failures": [],
            "scientific_independence_failures": ["EXAMPLE_V4_FAILURE"],
            "owner_target_failures": ["EXAMPLE_V4_FAILURE"],
        }
        with patch.object(gate.v4, "adjudicate", return_value=base):
            verdict = gate.adjudicate(candidate)

        self.assertTrue(verdict["v5_specificity_controls_pass"])
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])
        self.assertFalse(verdict["training_credit"])


if __name__ == "__main__":
    unittest.main()
