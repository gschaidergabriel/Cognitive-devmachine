from __future__ import annotations

import copy
import itertools
import unittest

from tools import trigger2_context_binding_generator_v1 as gen


class Trigger2ContextBindingGeneratorTests(unittest.TestCase):
    def test_demo_generation_realizes_actual_s3_and_exact_counterbalance(self):
        rows = gen.generate_rows(gen.demo_atoms(), blocks=2, seed=20260825)
        audit = gen.validate_rows(rows)
        self.assertTrue(audit["pass"], audit["failures"])
        self.assertEqual(288, audit["rows_total"])
        self.assertEqual(audit["s3_groups"], audit["s3_groups_complete"])
        self.assertEqual(4, len(audit["template_counts"]))
        self.assertEqual(2, len(audit["polarity_counts"]))
        self.assertEqual(3, len(audit["target_class_counts"]))
        for symbol in set().union(*(set(v) for v in audit["class_symbol_counts"].values())):
            counts = [audit["class_symbol_counts"][klass].get(symbol, 0) for klass in gen.CLASSES]
            self.assertEqual(1, len(set(counts)), (symbol, counts))

    def test_metadata_permutation_changes_actual_mapping(self):
        rows = gen.generate_rows(gen.demo_atoms(), blocks=1, seed=7)
        seen = {}
        for row in rows:
            meta = row["curriculum"]
            key = (meta["template_family"], meta["query_polarity"], meta["base_semantic_class"])
            seen.setdefault(key, set()).add(tuple(sorted(meta["mapping"].items())))
        self.assertTrue(all(len(mappings) == 6 for mappings in seen.values()))

    def test_target_is_derived_from_prompt_mapping(self):
        rows = gen.generate_rows(gen.demo_atoms(), blocks=1, seed=11)
        for row in rows:
            parsed = gen.parse_codebook(row["prompt"])
            target_class = row["curriculum"]["target_semantic_class"]
            self.assertEqual(parsed[target_class], row["target"])

    def test_inverted_query_flips_known_binary_states_but_preserves_unknown(self):
        self.assertEqual("DENY", gen.semantic_after_polarity("ALLOW", "INVERTED"))
        self.assertEqual("ALLOW", gen.semantic_after_polarity("DENY", "INVERTED"))
        self.assertEqual("ABSTAIN", gen.semantic_after_polarity("ABSTAIN", "INVERTED"))

    def test_validator_rejects_target_tamper(self):
        rows = gen.generate_rows(gen.demo_atoms(), blocks=1, seed=13)
        bad = copy.deepcopy(rows)
        parsed = gen.parse_codebook(bad[0]["prompt"])
        wrong = next(v for k, v in parsed.items() if k != bad[0]["curriculum"]["target_semantic_class"])
        bad[0]["target"] = wrong
        audit = gen.validate_rows(bad)
        self.assertFalse(audit["pass"])
        self.assertTrue(any(x.startswith("TARGET_NOT_DERIVED_FROM_ACTUAL_MAPPING:0") for x in audit["failures"]))

    def test_validator_rejects_class_word_leak_outside_codebook(self):
        rows = gen.generate_rows(gen.demo_atoms(), blocks=1, seed=17)
        bad = copy.deepcopy(rows)
        bad[0]["prompt"] += "\nHint: ALLOW"
        audit = gen.validate_rows(bad)
        self.assertFalse(audit["pass"])
        self.assertTrue(any(x.startswith("CLASS_WORD_LEAK_OUTSIDE_CODEBOOK:0") for x in audit["failures"]))

    def test_validator_rejects_metadata_only_permutation_lie(self):
        rows = gen.generate_rows(gen.demo_atoms(), blocks=1, seed=19)
        bad = copy.deepcopy(rows)
        original = tuple(bad[0]["curriculum"]["s3_permutation"])
        replacement = next(p for p in itertools.permutations(range(3)) if p != original)
        bad[0]["curriculum"]["s3_permutation"] = list(replacement)
        audit = gen.validate_rows(bad)
        self.assertFalse(audit["pass"])
        self.assertTrue(any(x.startswith("S3_PERMUTATION_NOT_CAUSAL:0") for x in audit["failures"]))

    def test_generation_refuses_unverified_multitoken_or_unknown_atoms(self):
        atoms = [gen.Atom("a", 1, 1), gen.Atom("b", 2, 1), gen.Atom("c", None, -1)]
        with self.assertRaises(ValueError):
            gen.generate_rows(atoms)


if __name__ == "__main__":
    unittest.main()
