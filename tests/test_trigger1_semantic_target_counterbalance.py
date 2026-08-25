from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate as gate

HEX64 = "a" * 64


def scientific_candidate() -> dict:
    return {
        "vector_derivation": {
            "method": "ACTIVATION_CONTRAST_MEAN",
            "uses_output_head_weights": False,
            "uses_holdout_data": False,
            "uses_evaluation_output_labels": False,
            "derivation_family_id": "derivation-family",
            "derivation_receipt_sha256": HEX64,
        },
        "calibration": {
            "family_id": "calibration-family",
            "semantic_target_counterbalanced": True,
            "semantic_targets": ["AFFIRMATIVE", "NEGATIVE", "NEUTRAL"],
        },
        "holdout": {
            "family_id": "holdout-family",
            "evaluation_independent_of_vector_derivation": True,
            "metric_definition_sha256": HEX64,
            "metric_uses_output_tokens": True,
            "label_mapping_counterbalanced": True,
            "semantic_target_counterbalanced": True,
            "semantic_targets": ["AFFIRMATIVE", "NEGATIVE", "NEUTRAL"],
            "semantic_target_interaction_test": True,
        },
    }


class Trigger1SemanticTargetCounterbalanceTests(unittest.TestCase):
    def test_output_code_counterbalance_alone_does_not_establish_semantic_specificity(self):
        candidate = scientific_candidate()
        candidate["calibration"]["semantic_target_counterbalanced"] = False
        candidate["calibration"]["semantic_targets"] = ["AFFIRMATIVE", "AFFIRMATIVE", "AFFIRMATIVE"]
        candidate["holdout"]["semantic_target_counterbalanced"] = False
        candidate["holdout"]["semantic_targets"] = ["AFFIRMATIVE", "AFFIRMATIVE", "AFFIRMATIVE"]

        ok, failures = gate._scientific_independence_evidence(candidate)

        self.assertFalse(ok)
        self.assertIn("CALIBRATION_SEMANTIC_TARGET_COUNTERBALANCE_REQUIRED", failures)
        self.assertIn("HOLDOUT_SEMANTIC_TARGET_COUNTERBALANCE_REQUIRED", failures)
        self.assertIn("CALIBRATION_SEMANTIC_TARGET_SET_MUST_BE_AFFIRMATIVE_NEGATIVE_NEUTRAL", failures)
        self.assertIn("HOLDOUT_SEMANTIC_TARGET_SET_MUST_BE_AFFIRMATIVE_NEGATIVE_NEUTRAL", failures)

    def test_holdout_balance_cannot_repair_single_target_calibration_selection(self):
        candidate = scientific_candidate()
        candidate["calibration"]["semantic_target_counterbalanced"] = False
        candidate["calibration"]["semantic_targets"] = ["AFFIRMATIVE"]

        ok, failures = gate._scientific_independence_evidence(candidate)

        self.assertFalse(ok)
        self.assertIn("CALIBRATION_SEMANTIC_TARGET_COUNTERBALANCE_REQUIRED", failures)
        self.assertIn("CALIBRATION_SEMANTIC_TARGET_SET_MUST_BE_AFFIRMATIVE_NEGATIVE_NEUTRAL", failures)

    def test_semantic_target_interaction_is_required_for_token_output_promotion(self):
        candidate = scientific_candidate()
        candidate["holdout"]["semantic_target_interaction_test"] = False

        ok, failures = gate._scientific_independence_evidence(candidate)

        self.assertFalse(ok)
        self.assertIn("HOLDOUT_SEMANTIC_TARGET_INTERACTION_TEST_REQUIRED", failures)

    def test_full_semantic_and_code_counterbalance_satisfies_this_guard(self):
        ok, failures = gate._scientific_independence_evidence(scientific_candidate())

        self.assertTrue(ok)
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
