from __future__ import annotations

import unittest

from tools import trigger1_jspace_promotion_gate as gate

HEX64 = "a" * 64


def scientific_candidate() -> dict:
    return {
        "vector_derivation": {
            "method": "CALIBRATION_ONLY_INTERMEDIATE_RESIDUAL_CONTRAST",
            "uses_output_head_weights": False,
            "uses_holdout_data": False,
            "uses_evaluation_output_labels": False,
            "derivation_family_id": "derivation-family",
            "derivation_receipt_sha256": HEX64,
        },
        "holdout": {
            "family_id": "holdout-family",
            "evaluation_independent_of_vector_derivation": True,
            "metric_definition_sha256": HEX64,
            "metric_uses_output_tokens": False,
        },
    }


class Trigger1MetricModalityFailClosedV4Tests(unittest.TestCase):
    def test_missing_metric_modality_fails_closed(self) -> None:
        candidate = scientific_candidate()
        del candidate["holdout"]["metric_uses_output_tokens"]
        ok, failures = gate._scientific_independence_evidence(candidate)
        self.assertFalse(ok)
        self.assertIn("HOLDOUT_METRIC_OUTPUT_TOKEN_MODALITY_REQUIRED", failures)

    def test_non_boolean_metric_modality_fails_closed(self) -> None:
        candidate = scientific_candidate()
        candidate["holdout"]["metric_uses_output_tokens"] = "false"
        ok, failures = gate._scientific_independence_evidence(candidate)
        self.assertFalse(ok)
        self.assertIn("HOLDOUT_METRIC_OUTPUT_TOKEN_MODALITY_REQUIRED", failures)

    def test_non_token_metric_does_not_require_label_counterbalance(self) -> None:
        ok, failures = gate._scientific_independence_evidence(scientific_candidate())
        self.assertTrue(ok)
        self.assertNotIn("TOKEN_OUTPUT_METRIC_REQUIRES_COUNTERBALANCED_LABEL_MAPPING", failures)

    def test_token_metric_requires_counterbalanced_mapping(self) -> None:
        candidate = scientific_candidate()
        candidate["holdout"]["metric_uses_output_tokens"] = True
        ok, failures = gate._scientific_independence_evidence(candidate)
        self.assertFalse(ok)
        self.assertIn("TOKEN_OUTPUT_METRIC_REQUIRES_COUNTERBALANCED_LABEL_MAPPING", failures)

    def test_counterbalanced_token_metric_can_pass_scientific_guard(self) -> None:
        candidate = scientific_candidate()
        candidate["holdout"]["metric_uses_output_tokens"] = True
        candidate["holdout"]["label_mapping_counterbalanced"] = True
        ok, failures = gate._scientific_independence_evidence(candidate)
        self.assertTrue(ok)
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
