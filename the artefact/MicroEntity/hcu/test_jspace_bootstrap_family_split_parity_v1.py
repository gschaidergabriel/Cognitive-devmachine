import unittest

import compile_jspace_bootstrap_dataset_v1 as compiler
import jspace_dataset_family_split_v1 as family_split


class BootstrapFamilySplitParityTests(unittest.TestCase):
    def test_compiler_reuses_single_split_function(self):
        self.assertIs(compiler.split_for_family, family_split.split_for_family)
        self.assertEqual(compiler.FAMILY_SPLIT_SCHEMA, family_split.SPLIT_SCHEMA)

    def test_known_previous_divergence_case_collapses_to_selected_authority(self):
        self.assertEqual(family_split.split_for_family("episode:1"), "train")
        self.assertEqual(compiler.split_for_family("episode:1"), "train")

    def test_broad_family_corpus_has_exact_parity(self):
        families = [f"episode:{index}" for index in range(256)]
        families.extend(("episode:A", "episode:B", "unicode:Δ", "nested/a:b"))
        for trace_family_id in families:
            with self.subTest(trace_family_id=trace_family_id):
                self.assertEqual(
                    compiler.split_for_family(trace_family_id),
                    family_split.split_for_family(trace_family_id),
                )


if __name__ == "__main__":
    unittest.main()
