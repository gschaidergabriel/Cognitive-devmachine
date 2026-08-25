from __future__ import annotations

import unittest

from tools import forschungsrun1_dual_qwen06_robust_analyze as a


def result():
    robust = {}
    final = []
    frozen = {}
    for ti, target in enumerate(a.TARGETS, start=1):
        frozen[target] = ti
        robust[f"{target}:{ti}"] = {
            "family_count": 3,
            "worst_family_delta": 0.1,
            "median_family_delta": 0.2,
            "mean_delta": 0.3,
            "mean_hit_rate": 0.8,
        }
        robust[f"{target}:9"] = {
            "family_count": 3,
            "worst_family_delta": -0.2,
            "median_family_delta": 1.0,
            "mean_delta": 1.5,
            "mean_hit_rate": 1.0,
        }
        for family, delta in (("x", 0.05), ("y", 0.1), ("z", 0.2)):
            final.append({"semantic_target": target, "family_id": family, "delta_vs_baseline": delta})
    return {
        "schema": "CLAY_FORSCHUNGSRUN1_DUAL_QWEN06_BLIND_ROBUST/v3",
        "result_sha256": "a" * 64,
        "frozen_best_actions": frozen,
        "robust_stats": robust,
        "fast_final_eval": final,
        "deconfounded_qwen_policy": {"turns": 5, "mean_delta": 0.2, "positive_fraction": 0.8},
        "robust_bandit_comparator": {"turns": 5, "mean_delta": 0.3, "positive_fraction": 1.0},
    }


class RobustAnalysisTests(unittest.TestCase):
    def test_positive_robust_transfer(self):
        r = a.analyze(result())
        self.assertTrue(r["global"]["all_targets_robust_positive_transfer"])
        self.assertEqual(r["global"]["targets_with_positive_worst_search_and_final"], list(a.TARGETS))
        self.assertAlmostEqual(r["controller_comparison"]["qwen_minus_bandit_mean_delta"], -0.1)
        for target in a.TARGETS:
            self.assertTrue(r["targets"][target]["robust_positive_transfer"])
            self.assertEqual(r["stable_positive_search_actions"][target], [int(result()["frozen_best_actions"][target])])

    def test_final_sign_reversal_blocks_robust_transfer(self):
        x = result()
        x["fast_final_eval"][0]["delta_vs_baseline"] = -0.5
        r = a.analyze(x)
        self.assertFalse(r["targets"]["AFFIRMATIVE"]["robust_positive_transfer"])
        self.assertFalse(r["global"]["all_targets_robust_positive_transfer"])

    def test_wrong_schema_fails(self):
        x = result(); x["schema"] = "wrong"
        with self.assertRaisesRegex(ValueError, "V3_RESULT_REQUIRED"):
            a.analyze(x)


if __name__ == "__main__":
    unittest.main()
