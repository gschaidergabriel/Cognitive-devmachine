#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "trigger2_hyperposition_transition_seed_generator_v1.py"
spec = importlib.util.spec_from_file_location("tr2hpgen", MODULE_PATH)
g = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(g)


class TestTrigger2HyperpositionTransitionSeedGeneratorV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = g.rows()
        cls.audit = g.audit(cls.rows)

    def test_audit_passes(self):
        self.assertTrue(self.audit["pass"], self.audit["failures"])

    def test_expected_shape(self):
        self.assertEqual(len(self.rows), 24)
        self.assertEqual(self.audit["split_counts"], {"TRAIN": 16, "VALIDATION": 4, "HOLDOUT": 4})
        self.assertEqual(self.audit["families"], 6)

    def test_family_split_and_ancestry_integrity(self):
        by_family = {}
        for row in self.rows:
            by_family.setdefault(row["family_id"], []).append(row)
        for family, rows in by_family.items():
            self.assertEqual(len({r["split"] for r in rows}), 1, family)
            self.assertEqual(len({r["provenance_ancestry_id"] for r in rows}), 1, family)
            self.assertEqual(len(rows), 4, family)

    def test_every_family_crosses_branch_order_and_surface(self):
        by_family = {}
        for row in self.rows:
            by_family.setdefault(row["family_id"], []).append(row)
        for family, rows in by_family.items():
            self.assertEqual({r["branch_order_evaluator_only"] for r in rows}, {"AB", "BA"}, family)
            self.assertEqual({r["surface_evaluator_only"] for r in rows}, {"STRUCTURED", "NARRATIVE"}, family)

    def test_no_row_mints_authority_or_training_credit(self):
        for row in self.rows:
            self.assertFalse(row["canonical_truth_allowed"])
            self.assertFalse(row["direct_effect_authority"])
            self.assertFalse(row["selected_using_holdout"])
            self.assertTrue(row["semantic_hyperposition_native"])
            self.assertFalse(row["full_D_training_admission"])
            self.assertFalse(row["final_ft_eligible"])
            target = json.loads(row["target"])
            self.assertFalse(target["canonical_truth_minted"])
            self.assertFalse(target["direct_effect_authority"])
            self.assertTrue(target["training_only_reference"])

    def test_targets_keep_two_branches(self):
        for row in self.rows:
            target = json.loads(row["target"])
            self.assertGreaterEqual(len(target["hyperposition_state_after"]["branches"]), 2)

    def test_majority_family_never_resolves(self):
        rows = [r for r in self.rows if r["family_id"] == "TR2HP_LBL_MAJORITY_NO_COLLAPSE"]
        self.assertEqual(len(rows), 4)
        for row in rows:
            target = json.loads(row["target"])
            self.assertEqual(target["resolution"]["resolution_state"], "UNRESOLVED")
            self.assertEqual(target["resolution"]["reason"], "NONRESOLVING_SIGNAL")

    def test_qualified_resolve_family_resolves_only_synthetic_task(self):
        rows = [r for r in self.rows if r["family_id"] == "TR2HP_LBL_QUALIFIED_RESOLVE"]
        self.assertEqual(len(rows), 4)
        for row in rows:
            target = json.loads(row["target"])
            self.assertEqual(target["resolution"]["resolution_state"], "RESOLVED_SYNTHETIC_TASK")
            self.assertEqual(target["resolution"]["resolved_branch_id"], "b_alpha")
            self.assertFalse(target["resolution"]["canonical_truth_minted"])

    def test_projection_family_retains_filtered_branch(self):
        rows = [r for r in self.rows if r["family_id"] == "TR2HP_LBL_PROJECTION_NOT_DELETION"]
        for row in rows:
            target = json.loads(row["target"])
            branches = {b["branch_id"]: b for b in target["hyperposition_state_after"]["branches"]}
            self.assertIn("b_beta", branches)
            self.assertEqual(branches["b_beta"]["projection_visibility"], "FILTERED_BUT_RETAINED")

    def test_only_prompt_is_model_visible(self):
        for row in self.rows:
            self.assertEqual(row["model_visible_fields"], ["prompt"])
            self.assertFalse(row["metadata_model_visible"])
            self.assertTrue(row["target_visible_only_during_supervision"])


if __name__ == "__main__":
    unittest.main()
