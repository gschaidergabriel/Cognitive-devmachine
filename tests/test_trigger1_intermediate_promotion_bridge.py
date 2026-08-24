from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
TESTS = ROOT / "tests"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

import trigger1_intermediate_promotion_bridge as bridge
import trigger1_jspace_promotion_gate as gate
from test_trigger1_intermediate_promotion_bridge_raw_recompute_current import valid_inputs


class Trigger1IntermediatePromotionBridgeTests(unittest.TestCase):
    def test_bridge_candidate_reaches_v4_scientific_independence_and_goal_gate(self):
        result, intermediate = valid_inputs()
        candidate = bridge.build_direct_candidate(result, intermediate)

        self.assertFalse(candidate["vector_derivation"]["uses_output_head_weights"])
        self.assertFalse(candidate["vector_derivation"]["uses_holdout_data"])
        self.assertFalse(candidate["vector_derivation"]["uses_evaluation_output_labels"])
        self.assertTrue(candidate["holdout"]["label_mapping_counterbalanced"])
        self.assertTrue(candidate["intermediate_protocol"]["raw_selection_recomputed"])
        self.assertTrue(candidate["intermediate_protocol"]["raw_holdout_verdict_recomputed"])

        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])

    def test_calibration_holdout_seed_overlap_fails_closed(self):
        result, intermediate = valid_inputs(calibration_seed=2718)
        with self.assertRaisesRegex(
            bridge.BridgeError,
            "CALIBRATION_HOLDOUT_SEEDS_MUST_BE_DISJOINT",
        ):
            bridge.build_direct_candidate(result, intermediate)

    def test_calibration_holdout_prompt_overlap_fails_closed_with_disjoint_seeds(self):
        result, intermediate = valid_inputs(calibration_prompt="2" * 64)
        with self.assertRaisesRegex(
            bridge.BridgeError,
            "CALIBRATION_HOLDOUT_PROMPTS_MUST_BE_DISJOINT",
        ):
            bridge.build_direct_candidate(result, intermediate)


if __name__ == "__main__":
    unittest.main()
