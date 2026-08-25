from __future__ import annotations

import copy
import unittest

from tools import trigger2_context_binding_generator_v1 as gen
from tools import trigger2_context_binding_split_audit_v1 as split_audit


class Trigger2ContextBindingSplitAuditTests(unittest.TestCase):
    def _rows(self, split: str, *, seed: int = 20260825):
        return gen.generate_rows(gen.demo_atoms(), split=split, blocks=1, seed=seed)

    def test_same_seed_same_atom_pool_across_splits_fails_closed(self):
        report = split_audit.audit_splits(
            {
                "TRAIN": self._rows("TRAIN"),
                "VALIDATION": self._rows("VALIDATION"),
                "HOLDOUT": self._rows("HOLDOUT"),
            }
        )
        self.assertFalse(report["pass"])
        self.assertEqual("FAIL_CLOSED", report["status"])
        codes = {x["code"] for x in report["failures"]}
        self.assertIn("CROSS_SPLIT_PROMPT_SHA256_OVERLAP", codes)
        self.assertIn("CROSS_SPLIT_ATOM_TOKEN_ID_OVERLAP", codes)
        self.assertIn("CROSS_SPLIT_NORMALIZED_FAMILY_OVERLAP", codes)
        self.assertIn("CROSS_SPLIT_SEMANTIC_SIGNATURE_OVERLAP", codes)
        self.assertFalse(report["holdout_isolated_on_atom_family_semantic_axes"])

    def test_different_seed_does_not_manufacture_semantic_family_independence(self):
        report = split_audit.audit_splits(
            {
                "TRAIN": self._rows("TRAIN", seed=1),
                "VALIDATION": self._rows("VALIDATION", seed=2),
                "HOLDOUT": self._rows("HOLDOUT", seed=3),
            }
        )
        self.assertFalse(report["pass"])
        codes = {x["code"] for x in report["failures"]}
        # Seed variation may change prompt/codebook order, but the semantic bank/family
        # is still shared and the same demo atom pool is reused.
        self.assertIn("CROSS_SPLIT_ATOM_TOKEN_ID_OVERLAP", codes)
        self.assertIn("CROSS_SPLIT_NORMALIZED_FAMILY_OVERLAP", codes)
        self.assertIn("CROSS_SPLIT_SEMANTIC_SIGNATURE_OVERLAP", codes)

    def test_split_prefix_cannot_hide_same_family(self):
        train = self._rows("TRAIN", seed=5)[0]
        holdout = copy.deepcopy(train)
        holdout["split"] = "HOLDOUT"
        holdout["family_id"] = holdout["family_id"].replace("CTX_BIND_TRAIN_", "CTX_BIND_HOLDOUT_", 1)
        holdout["provenance_ancestry_id"] = holdout["provenance_ancestry_id"].replace(":TRAIN:", ":HOLDOUT:", 1)
        self.assertEqual(
            split_audit.normalized_family_id(train),
            split_audit.normalized_family_id(holdout),
        )
        self.assertEqual(
            split_audit.provenance_without_split(train),
            split_audit.provenance_without_split(holdout),
        )

    def test_declared_split_mismatch_fails(self):
        train = self._rows("TRAIN", seed=7)
        val = self._rows("VALIDATION", seed=8)
        hold = self._rows("HOLDOUT", seed=9)
        bad = copy.deepcopy(hold)
        bad[0]["split"] = "TRAIN"
        report = split_audit.audit_splits({"TRAIN": train, "VALIDATION": val, "HOLDOUT": bad})
        self.assertFalse(report["pass"])
        self.assertTrue(any(x["code"] == "ROW_OR_SCHEMA_FAILURE" for x in report["failures"]))


if __name__ == "__main__":
    unittest.main()
