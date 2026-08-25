from __future__ import annotations

import unittest

from tools import forschungsrun1_dual_qwen06_jspace_search as dual


class DualQwen06SearchContractTest(unittest.TestCase):
    def test_episode_counterbalance_covers_all_semantics_and_codes(self):
        observed = {(s, c): 0 for s in dual.SEMANTICS for c in ("A", "B", "C")}
        for i in range(54):
            spec = dual.episode_spec(i)
            self.assertEqual(set(spec["mapping"]), {"A", "B", "C"})
            self.assertEqual(set(spec["mapping"].values()), set(dual.SEMANTICS))
            self.assertEqual(spec["mapping"][spec["target_code"]], spec["semantic_target"])
            observed[(spec["semantic_target"], spec["target_code"])] += 1
        self.assertTrue(all(v > 0 for v in observed.values()))

    def test_action_bank_is_bounded_and_has_required_controls(self):
        self.assertEqual(set(dual.ACTION_SPECS), set(range(10)))
        self.assertEqual(dual.ACTION_SPECS[0]["kind"], "baseline")
        self.assertTrue(any(s["kind"] == "anti_target" for s in dual.ACTION_SPECS.values()))
        self.assertTrue(any(s["kind"] == "mix_70_30" for s in dual.ACTION_SPECS.values()))
        self.assertTrue(any(int(s["layer"]) == 14 for s in dual.ACTION_SPECS.values()))
        self.assertTrue(any(int(s["layer"]) == 20 for s in dual.ACTION_SPECS.values()))

    def test_exploration_does_not_masquerade_as_controller_policy(self):
        for turn, expected in enumerate((0, 2, 5, 7)):
            executed, policy = dual.exploration_override(11, turn, 9)
            self.assertEqual(executed, expected)
            self.assertEqual(policy, "FORCED_INITIAL_COVERAGE")
        seen_policy = False
        seen_explore = False
        for turn in range(4, 24):
            executed, policy = dual.exploration_override(3, turn, 6)
            if policy == "CONTROLLER_POLICY":
                seen_policy = True
                self.assertEqual(executed, 6)
            if policy == "DETERMINISTIC_EXPLORATION":
                seen_explore = True
        self.assertTrue(seen_policy)
        self.assertTrue(seen_explore)

    def test_controller_prompt_exposes_feedback_not_target_prompt_channel(self):
        spec = dual.episode_spec(0)
        history = [{
            "turn": 0,
            "controller_selected_action": 2,
            "executed_action": 2,
            "target_output": "B",
            "target_score": 1.25,
            "delta_vs_baseline": 0.75,
        }]
        prompt = dual.controller_prompt(spec, history)
        self.assertIn("Semantic goal=AFFIRMATIVE", prompt)
        self.assertIn("target_output=B", prompt)
        self.assertIn("Return exactly one digit", prompt)
        self.assertNotIn(spec["prompt"], prompt)

    def test_native_holdout_has_exact_six_controls_per_code(self):
        cases = dual.native_holdout_cases("NEGATIVE", "candidate")
        self.assertEqual(len(cases), 18)
        for target_code in ("A", "B", "C"):
            subset = [r for r in cases if r["target_label"] == target_code]
            self.assertEqual({r["control"] for r in subset}, set(dual.base.CONTROLS))


if __name__ == "__main__":
    unittest.main()
