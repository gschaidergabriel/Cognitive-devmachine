from __future__ import annotations

import unittest

from tools import forschungsrun1_dual_qwen06_jspace_blind_robust as run


class RobustBlindControllerTests(unittest.TestCase):
    def test_action_code_mapping_is_bijective_and_rotates(self):
        seen = set()
        for turn in range(20):
            mapping = run.action_code_mapping(turn, "AFFIRMATIVE")
            self.assertEqual(set(mapping), set(run.DIGITS))
            self.assertEqual(set(mapping.values()), set(range(run.ACTION_COUNT)))
            seen.add(tuple(mapping[str(i)] for i in range(run.ACTION_COUNT)))
        self.assertGreaterEqual(len(seen), 10)

    def test_coverage_is_per_target_action_family(self):
        turns = []
        target, family = "NEGATIVE", "drawbridge"
        for expected in range(run.ACTION_COUNT):
            self.assertEqual(run.coverage_action(turns, target, family), expected)
            turns.append({"semantic_target": target, "family_id": family, "executed_action": expected, "delta_vs_baseline": 0.0, "target_output": "A", "target_code": "A"})
        self.assertIsNone(run.coverage_action(turns, target, family))
        self.assertEqual(run.coverage_action(turns, target, "clinic"), 0)

    def test_robust_stats_preserve_family_sign_reversals(self):
        rows = []
        for family, delta in (("a", 1.0), ("b", 0.5), ("c", -0.25)):
            rows.append({"semantic_target": "AFFIRMATIVE", "family_id": family, "executed_action": 5, "delta_vs_baseline": delta, "target_output": "A", "target_code": "A"})
        s = run.robust_stats(rows)[("AFFIRMATIVE", 5)]
        self.assertEqual(s["family_count"], 3)
        self.assertAlmostEqual(s["worst_family_delta"], -0.25)
        self.assertAlmostEqual(s["median_family_delta"], 0.5)
        self.assertAlmostEqual(s["mean_delta"], (1.0 + 0.5 - 0.25) / 3)

    def test_robust_best_prefers_consistency_over_large_single_family_peak(self):
        rows = []
        for family, delta in (("a", 2.0), ("b", 2.0), ("c", -1.0)):
            rows.append({"semantic_target": "NEUTRAL", "family_id": family, "executed_action": 1, "delta_vs_baseline": delta, "target_output": "A", "target_code": "A"})
        for family, delta in (("a", 0.2), ("b", 0.25), ("c", 0.15)):
            rows.append({"semantic_target": "NEUTRAL", "family_id": family, "executed_action": 2, "delta_vs_baseline": delta, "target_output": "A", "target_code": "A"})
        self.assertEqual(run.robust_best("NEUTRAL", run.robust_stats(rows), include_baseline=False), 2)

    def test_freeze_excludes_baseline_and_requires_three_families(self):
        rows = []
        for target in run.TARGETS:
            for family in ("a", "b", "c"):
                rows.extend([
                    {"semantic_target": target, "family_id": family, "executed_action": 0, "delta_vs_baseline": 9.0, "target_output": "A", "target_code": "A"},
                    {"semantic_target": target, "family_id": family, "executed_action": 1, "delta_vs_baseline": 0.1, "target_output": "A", "target_code": "A"},
                    {"semantic_target": target, "family_id": family, "executed_action": 2, "delta_vs_baseline": 0.2, "target_output": "A", "target_code": "A"},
                ])
        self.assertEqual(run.freeze_best(rows), {target: 2 for target in run.TARGETS})


if __name__ == "__main__":
    unittest.main()
