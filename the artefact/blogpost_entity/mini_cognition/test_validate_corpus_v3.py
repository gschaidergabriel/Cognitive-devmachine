#!/usr/bin/env python3
import json
import unittest
from collections import Counter

import generate_sft_v3 as v3
from validate_sft_v1 import validate_code


class CorpusV3Tests(unittest.TestCase):
    def test_v3_cardinality_uniqueness_split_and_structural_validity(self):
        train, valid = v3.build()
        self.assertEqual((len(train), len(valid)), (2025, 225))
        train_canon = [v3.canonical_messages(x) for x in train]
        valid_canon = [v3.canonical_messages(x) for x in valid]
        self.assertEqual(len(set(train_canon)), 2025)
        self.assertEqual(len(set(valid_canon)), 225)
        self.assertFalse(set(train_canon) & set(valid_canon))
        self.assertFalse(
            {x["messages"][1]["content"] for x in train}
            & {x["messages"][1]["content"] for x in valid}
        )
        bad_train = [(x["scenario_id"], validate_code(x["messages"][-1]["content"])) for x in train]
        bad_valid = [(x["scenario_id"], validate_code(x["messages"][-1]["content"])) for x in valid]
        bad_train = [x for x in bad_train if x[1]]
        bad_valid = [x for x in bad_valid if x[1]]
        self.assertEqual(bad_train, [])
        self.assertEqual(bad_valid, [])

    def test_v3_preserves_exact_v2_rows_and_adds_only_declared_composition_families(self):
        train, valid = v3.build()
        base_train = [x for x in train if not x["scenario_id"].startswith("v3:")]
        base_valid = [x for x in valid if not x["scenario_id"].startswith("v3:")]
        comp_train = [x for x in train if x["scenario_id"].startswith("v3:")]
        comp_valid = [x for x in valid if x["scenario_id"].startswith("v3:")]
        self.assertEqual((len(base_train), len(base_valid)), (1485, 165))
        self.assertEqual((len(comp_train), len(comp_valid)), (540, 60))
        ct = Counter(x["family"] for x in comp_train + comp_valid)
        cv = Counter(x["family"] for x in comp_valid)
        self.assertEqual(ct, Counter(v3.COMP_TOTALS))
        self.assertEqual(cv, Counter(v3.COMP_VALID))

    def test_manifest_claims_match_generator_constants(self):
        self.assertEqual(sum(v3.COMP_TOTALS.values()), 600)
        self.assertEqual(sum(v3.COMP_VALID.values()), 60)
        self.assertEqual(v3.SEED, 20260826)
        self.assertEqual(len({x[0] for x in v3.COMP_OPS}), len(v3.COMP_OPS))


if __name__ == "__main__":
    unittest.main()
