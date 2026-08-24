import importlib.util
from pathlib import Path
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "trigger1_semantic_counterbalance_v1.py"
spec = importlib.util.spec_from_file_location("counterbalance", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class CounterbalanceTests(unittest.TestCase):
    def test_all_six_permutations_are_complete_and_balanced(self):
        receipt = mod.balance_receipt()
        self.assertTrue(receipt["label_mapping_counterbalanced"])
        self.assertEqual(receipt["mapping_count"], 6)
        for semantic in mod.SEMANTICS:
            self.assertEqual(
                receipt["per_semantic_physical_token_counts"][semantic],
                {"A": 2, "B": 2, "C": 2},
            )

    def test_basis_prompts_do_not_use_output_option_labels_or_target_words(self):
        for _, _, prompt in mod.BASIS_PROMPTS:
            lower = prompt.lower()
            self.assertNotIn("output only", lower)
            self.assertNotIn("option is a", lower)
            self.assertNotIn("option is b", lower)
            self.assertNotIn("option is c", lower)
            self.assertNotIn("increase", lower)
            self.assertNotIn("decrease", lower)

    def test_rendered_case_binds_bijective_mapping(self):
        mapping = {"INCREASE": "C", "DECREASE": "A", "SAME": "B"}
        _, prompt = mod.render_case(1, 2, 5, "T", mapping)
        self.assertEqual(mod.parse_mapping(prompt), mapping)
        self.assertIn("A: the ending value is smaller", prompt)
        self.assertIn("B: the ending value is unchanged", prompt)
        self.assertIn("C: the ending value is larger", prompt)

    def test_semantic_score_patch_remaps_physical_tokens(self):
        class DummyState:
            def __init__(self):
                self.token_ids = {"A": 10, "B": 20, "C": 30}

            def infer(self, payload):
                return {"seen": dict(self.token_ids), "target_score": 1.0}

        base = types.SimpleNamespace(RuntimeState=DummyState)
        mod.install_semantic_score_patch(base)
        state = base.RuntimeState()
        mapping = {"INCREASE": "C", "DECREASE": "A", "SAME": "B"}
        result = state.infer({"prompt": mod.mapping_marker(mapping)})
        self.assertEqual(result["seen"], {"A": 30, "B": 10, "C": 20})
        self.assertEqual(state.token_ids, {"A": 10, "B": 20, "C": 30})
        self.assertEqual(result["semantic_to_physical_token"], mapping)

    def test_calibration_and_holdout_use_disjoint_prompt_families(self):
        calibration = mod.build_family(mod.CALIBRATION_CASES)
        holdout = mod.build_family(mod.HOLDOUT_CASES)
        self.assertEqual(len(calibration), 6)
        self.assertEqual(len(holdout), 6)
        self.assertTrue({seed for seed, _ in calibration}.isdisjoint({seed for seed, _ in holdout}))
        self.assertTrue({prompt for _, prompt in calibration}.isdisjoint({prompt for _, prompt in holdout}))


if __name__ == "__main__":
    unittest.main()
