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
        "holdout": {
            "family_id": "holdout-family",
            "evaluation_independent_of_vector_derivation": True,
            "metric_definition_sha256": HEX64,
            "metric_uses_output_tokens": False,
        },
    }


class Trigger1MetricModalityFailClosedTests(unittest.TestCase):
    def test_missing_metric_modality_fails_closed(self) -> None:
        candidate = scientific_candidate()
        candidate["holdout"].pop("metric_uses_output_tokens")
        ok, failures = gate._scientific_independence_evidence(candidate)
        self.assertFalse(ok)
        self.assertIn("HOLDOUT_METRIC_OUTPUT_TOKEN_MODALITY_REQUIRED", failures)

    def test_null_metric_modality_fails_closed(self) -> None:
        candidate = scientific_candidate()
        candidate["holdout"]["metric_uses_output_tokens"] = None
        ok, failures = gate._scientific_independence_evidence(candidate)
        self.assertFalse(ok)
        self.assertIn("HOLDOUT_METRIC_OUTPUT_TOKEN_MODALITY_REQUIRED", failures)

    def test_non_boolean_metric_modality_fails_closed(self) -> None:
        for value in ("false", 0, 1, [], {}):
            with self.subTest(value=value):
                candidate = scientific_candidate()
                candidate["holdout"]["metric_uses_output_tokens"] = value
                ok, failures = gate._scientific_independence_evidence(candidate)
                self.assertFalse(ok)
                self.assertIn("HOLDOUT_METRIC_OUTPUT_TOKEN_MODALITY_REQUIRED", failures)

    def test_explicit_non_token_metric_does_not_require_counterbalance(self) -> None:
        candidate = scientific_candidate()
        ok, failures = gate._scientific_independence_evidence(candidate)
        self.assertTrue(ok)
        self.assertNotIn("TOKEN_OUTPUT_METRIC_REQUIRES_COUNTERBALANCED_LABEL_MAPPING", failures)

    def test_token_metric_requires_counterbalance(self) -> None:
        candidate = scientific_candidate()
        candidate["holdout"]["metric_uses_output_tokens"] = True
        ok, failures = gate._scientific_independence_evidence(candidate)
        self.assertFalse(ok)
        self.assertIn("TOKEN_OUTPUT_METRIC_REQUIRES_COUNTERBALANCED_LABEL_MAPPING", failures)

        candidate["holdout"]["label_mapping_counterbalanced"] = True
        ok, failures = gate._scientific_independence_evidence(candidate)
        self.assertTrue(ok)
        self.assertNotIn("TOKEN_OUTPUT_METRIC_REQUIRES_COUNTERBALANCED_LABEL_MAPPING", failures)


if __name__ == "__main__":
    unittest.main()
