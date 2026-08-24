from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "trigger1_local_qwen06_semantic_counterbalanced_execute.py"
_SPEC = importlib.util.spec_from_file_location("clay_trigger1_semantic_counterbalanced_test", MODULE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("TEST_MODULE_LOAD_FAILED")
mod = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = mod
_SPEC.loader.exec_module(mod)


class FakeTokenizer:
    def __init__(self, ids: list[int]):
        self.ids = list(ids)

    def encode(self, _text: str, add_special_tokens: bool = False):
        self.add_special_tokens = add_special_tokens
        return list(self.ids)


class SemanticCounterbalanceTests(unittest.TestCase):
    def test_gain_cases_are_complete_counterbalance(self):
        proof = mod.counterbalance_proof(mod.GAIN_CASES)
        self.assertTrue(proof["complete_latin_counterbalance"])
        for semantic in mod.SEMANTIC_CLASSES:
            self.assertEqual(proof["counts"][semantic], {"A": 1, "B": 1, "C": 1})

    def test_holdout_cases_are_complete_counterbalance(self):
        proof = mod.counterbalance_proof(mod.HOLDOUT_CASES)
        self.assertTrue(proof["complete_latin_counterbalance"])
        for semantic in mod.SEMANTIC_CLASSES:
            self.assertEqual(proof["counts"][semantic], {"A": 1, "B": 1, "C": 1})

    def test_mapping_must_be_full_abc_permutation(self):
        with self.assertRaisesRegex(ValueError, "OUTPUT_LABEL_MAPPING_MUST_BE_ABC_PERMUTATION"):
            mod._validate_mapping(
                {
                    mod.SEM_TARGET: "A",
                    mod.SEM_ALT1: "A",
                    mod.SEM_ALT2: "C",
                }
            )

    def test_basis_token_guard_accepts_disjoint_token_ids(self):
        receipts = mod.assert_basis_omits_evaluation_output_tokens(
            FakeTokenizer([91, 92, 93]),
            {"A": 1, "B": 2, "C": 3},
        )
        self.assertEqual(len(receipts), len(mod.BASIS_PROMPTS))
        self.assertTrue(all(row["evaluation_output_token_overlap"] == [] for row in receipts))

    def test_basis_token_guard_rejects_evaluation_token_leak(self):
        with self.assertRaisesRegex(RuntimeError, "BASIS_PROMPT_EVALUATION_OUTPUT_TOKEN_LEAK"):
            mod.assert_basis_omits_evaluation_output_tokens(
                FakeTokenizer([91, 2, 93]),
                {"A": 1, "B": 2, "C": 3},
            )

    def test_vector_derivation_is_semantic_not_output_label_named(self):
        self.assertEqual(
            mod.VECTOR_DERIVATION_METHOD,
            "INTERMEDIATE_SEMANTIC_ACTIVATION_CONTRAST_MEAN",
        )
        basis_semantics = {semantic for _seed, semantic, _prompt in mod.BASIS_PROMPTS}
        self.assertEqual(basis_semantics, set(mod.SEMANTIC_CLASSES))
        self.assertNotEqual(basis_semantics, {"A", "B", "C"})


if __name__ == "__main__":
    unittest.main()
