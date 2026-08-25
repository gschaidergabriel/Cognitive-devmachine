from __future__ import annotations

import unittest

from tools import forschungsrun1_dual_qwen06_jspace_blind_cumulative as run
from tools import trigger1_abstract_state_challenge_v1 as challenge


class BlindCumulativeSearchTests(unittest.TestCase):
    def test_partition_is_disjoint_three_by_three_and_prompt_blind(self):
        value = challenge.build_challenge()
        search, final, sf, ff = run.partition_holdout(value)
        self.assertEqual(len(search), 9)
        self.assertEqual(len(final), 9)
        self.assertEqual(len(sf), 3)
        self.assertEqual(len(ff), 3)
        self.assertTrue(set(sf).isdisjoint(ff))
        for rows in (search, final):
            by_family = {}
            for row in rows:
                by_family.setdefault(row["family_id"], []).append(row)
            for family_rows in by_family.values():
                self.assertEqual(len(family_rows), 3)
                self.assertEqual(len({row["prompt"] for row in family_rows}), 1)
                self.assertEqual({row["semantic_target"] for row in family_rows}, set(run.TARGETS))
                self.assertEqual({row["output_code_identity"] for row in family_rows}, {"A", "B", "C"})
                self.assertTrue(all(row["target_blind_prompt"] for row in family_rows))

    def test_global_coverage_forces_every_action_before_policy(self):
        target = "AFFIRMATIVE"
        turns = []
        for expected in range(run.ACTION_COUNT):
            ledger = run.ledger_stats(turns)
            executed, policy = run.choose_executed_action(target, 9, ledger, expected)
            self.assertEqual(executed, expected)
            self.assertEqual(policy, "FORCED_GLOBAL_COVERAGE")
            turns.append({
                "semantic_target": target,
                "executed_action": executed,
                "delta_vs_baseline": float(expected),
                "target_output": "A",
                "target_code": "A",
            })
        executed, policy = run.choose_executed_action(target, 3, run.ledger_stats(turns), 11)
        self.assertEqual(executed, 3)
        self.assertEqual(policy, "CONTROLLER_POLICY")

    def test_ledger_is_cumulative_across_arbitrary_episode_boundaries(self):
        turns = [
            {"semantic_target": "NEGATIVE", "executed_action": 2, "delta_vs_baseline": 1.0, "target_output": "B", "target_code": "B"},
            {"semantic_target": "AFFIRMATIVE", "executed_action": 2, "delta_vs_baseline": -1.0, "target_output": "C", "target_code": "A"},
            {"semantic_target": "NEGATIVE", "executed_action": 2, "delta_vs_baseline": 3.0, "target_output": "A", "target_code": "B"},
        ]
        stats = run.ledger_stats(turns)
        self.assertEqual(stats[("NEGATIVE", 2)]["n"], 2.0)
        self.assertAlmostEqual(stats[("NEGATIVE", 2)]["mean_delta"], 2.0)
        self.assertAlmostEqual(stats[("NEGATIVE", 2)]["hit_rate"], 0.5)
        self.assertAlmostEqual(stats[("AFFIRMATIVE", 2)]["mean_delta"], -1.0)

    def test_freeze_best_action_never_selects_baseline(self):
        turns = []
        for target in run.TARGETS:
            turns.extend([
                {"semantic_target": target, "executed_action": 0, "delta_vs_baseline": 99.0, "target_output": "A", "target_code": "A"},
                {"semantic_target": target, "executed_action": 1, "delta_vs_baseline": 0.2, "target_output": "A", "target_code": "A"},
                {"semantic_target": target, "executed_action": 2, "delta_vs_baseline": 0.8, "target_output": "A", "target_code": "A"},
            ])
        frozen = run.freeze_best_actions(turns)
        self.assertEqual(frozen, {target: 2 for target in run.TARGETS})

    def test_native_final_cases_keep_same_target_blind_prompt_per_family(self):
        value = challenge.build_challenge()
        _, final, _, _ = run.partition_holdout(value)
        rows = run.native_cases(final, "NEUTRAL", "candidate")
        self.assertEqual(len(rows), 3 * len(run.base.CONTROLS))
        prompts = {}
        for row in rows:
            prompts.setdefault(row["prompt_family"], set()).add(row["prompt"])
        self.assertTrue(all(len(values) == 1 for values in prompts.values()))


if __name__ == "__main__":
    unittest.main()
