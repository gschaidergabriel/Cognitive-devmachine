from __future__ import annotations

import unittest

from tests.test_trigger1_jspace_promotion_gate import gate, valid_local_api_candidate


class Trigger1MetricModalityFailClosed872Tests(unittest.TestCase):
    def test_missing_metric_output_token_modality_fails_closed(self):
        candidate = valid_local_api_candidate()
        del candidate["holdout"]["metric_uses_output_tokens"]
        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn(
            "HOLDOUT_METRIC_OUTPUT_TOKEN_MODALITY_REQUIRED",
            verdict["scientific_independence_failures"],
        )

    def test_non_boolean_metric_output_token_modality_fails_closed(self):
        candidate = valid_local_api_candidate()
        candidate["holdout"]["metric_uses_output_tokens"] = "false"
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn(
            "HOLDOUT_METRIC_OUTPUT_TOKEN_MODALITY_REQUIRED",
            verdict["scientific_independence_failures"],
        )

    def test_explicit_non_token_metric_remains_valid(self):
        candidate = valid_local_api_candidate()
        candidate["holdout"]["metric_uses_output_tokens"] = False
        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])

    def test_token_metric_still_requires_counterbalanced_mapping(self):
        candidate = valid_local_api_candidate()
        candidate["holdout"]["metric_uses_output_tokens"] = True
        candidate["holdout"]["label_mapping_counterbalanced"] = False
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertIn(
            "TOKEN_OUTPUT_METRIC_REQUIRES_COUNTERBALANCED_LABEL_MAPPING",
            verdict["scientific_independence_failures"],
        )

    def test_counterbalanced_token_metric_can_pass_modality_guard(self):
        candidate = valid_local_api_candidate()
        candidate["holdout"]["metric_uses_output_tokens"] = True
        candidate["holdout"]["label_mapping_counterbalanced"] = True
        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])


if __name__ == "__main__":
    unittest.main()
