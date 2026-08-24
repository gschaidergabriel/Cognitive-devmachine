from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types
import unittest


# Lightweight stub: the successor's pure selection/adjudication logic must be
# testable without downloading/importing Torch or Transformers.
stub = types.ModuleType("trigger1_local_qwen06_intermediate_api_execute")
stub.CANDIDATE_LAYERS = (7, 14, 21)
stub.CALIBRATION_GAINS = (1.0, 4.0, 16.0, 64.0)
stub.POSITIVE_ANCHORS = ("positive-a", "positive-b")
stub.NEGATIVE_ANCHORS = ("negative-a", "negative-b")
stub.ROOT = Path("/tmp")
stub.__file__ = __file__
stub.canonical_sha = lambda value: __import__("hashlib").sha256(
    __import__("json").dumps(value, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
stub.sha256_file = lambda path: "0" * 64
stub.main = lambda: 0
sys.modules["trigger1_local_qwen06_intermediate_api_execute"] = stub

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "trigger1_intermediate_semantic_balance.py"
spec = importlib.util.spec_from_file_location("balanced", MODULE_PATH)
balanced = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(balanced)


def calibration_rows(effect):
    rows = []
    layer = 7
    gain = 4.0
    for case in balanced.CALIBRATION_CASES:
        seed = case["seed"]
        sign = balanced.expected_sign(seed)
        baseline = 0.2 * sign
        plus, flip = effect(sign, baseline)
        for control, value in (
            ("BASELINE", baseline),
            ("+VECTOR", plus),
            ("SIGN_FLIP", flip),
        ):
            rows.append({
                "seed": seed,
                "layer": layer,
                "gain": gain,
                "control": control,
                "target_score": value,
                "hook_calls": 1,
            })
    return rows


def holdout_rows(effect):
    rows = []
    layer = 7
    gain = 4.0
    for case in balanced.HOLDOUT_CASES:
        seed = case["seed"]
        sign = balanced.expected_sign(seed)
        baseline = 0.2 * sign
        plus, flip = effect(sign, baseline)
        values = {
            "BASELINE": baseline,
            "+VECTOR": plus,
            "SIGN_FLIP": flip,
            "NULL_VECTOR": baseline,
            "ORTHOGONAL_SAME_NORM": baseline + 0.05 * sign,
            "PERMUTED_SAME_NORM": baseline + 0.04 * sign,
        }
        for control, value in values.items():
            rows.append({
                "seed": seed,
                "layer": layer,
                "gain": gain,
                "control": control,
                "target_score": value,
                "hook_calls": 0 if control == "BASELINE" else 1,
            })
    return rows


class Trigger1IntermediateSemanticBalance(unittest.TestCase):
    def test_design_counterbalances_truth_and_output_labels(self):
        self.assertTrue(balanced.design_counterbalanced(balanced.CALIBRATION_CASES))
        self.assertTrue(balanced.design_counterbalanced(balanced.HOLDOUT_CASES))
        for cases in (balanced.CALIBRATION_CASES, balanced.HOLDOUT_CASES):
            self.assertEqual({"YES", "NO"}, {c["expected_label"] for c in cases})
            self.assertEqual({True, False}, {c["semantic_truth"] for c in cases})

    def test_literal_yes_bias_cannot_win_counterbalanced_calibration(self):
        # A raw YES-bias adds +1 to YES-minus-NO regardless of expected label.
        # That helps YES-mapped cases but harms NO-mapped cases.
        def literal_yes(_sign, baseline):
            return baseline + 1.0, baseline - 1.0

        self.assertIsNone(balanced.select_config(calibration_rows(literal_yes)))

    def test_semantic_correctness_effect_can_select(self):
        # Improve expected-label-oriented margin independent of output mapping.
        def semantic(sign, baseline):
            return baseline + sign * 1.0, baseline - sign * 1.0

        self.assertEqual((7, 4.0), balanced.select_config(calibration_rows(semantic)))

    def test_literal_yes_bias_fails_balanced_holdout(self):
        def literal_yes(_sign, baseline):
            return baseline + 1.0, baseline - 1.0

        verdict = balanced.adjudicate(holdout_rows(literal_yes), (7, 4.0))
        self.assertFalse(verdict["pass"])
        self.assertTrue(verdict["semantic_counterbalance"])
        self.assertLessEqual(verdict["strongest_counterexample_plus_delta"], 0)

    def test_semantic_effect_passes_with_nuisance_controls_below_target(self):
        def semantic(sign, baseline):
            return baseline + sign * 1.0, baseline - sign * 1.0

        verdict = balanced.adjudicate(holdout_rows(semantic), (7, 4.0))
        self.assertTrue(verdict["pass"])
        self.assertGreater(verdict["min_expected_margin_plus_vs_baseline"], 0)
        self.assertGreater(verdict["min_expected_margin_baseline_vs_sign_flip"], 0)
        self.assertGreater(verdict["mean_expected_margin_plus_delta"], verdict["best_same_norm_nuisance_delta"])


if __name__ == "__main__":
    unittest.main()
