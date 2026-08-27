from __future__ import annotations

from pathlib import Path
import runpy
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate as gate

BASE = runpy.run_path(str(ROOT / "tests" / "test_trigger1_jspace_promotion_gate.py"))
valid_local_api_candidate = BASE["valid_local_api_candidate"]


class Trigger1MetricModalityV4Tests(unittest.TestCase):
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

    def test_counterbalanced_token_metric_can_still_pass(self):
        candidate = valid_local_api_candidate()
        candidate["holdout"]["metric_uses_output_tokens"] = True
        candidate["holdout"]["label_mapping_counterbalanced"] = True
        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])


if __name__ == "__main__":
    unittest.main()
