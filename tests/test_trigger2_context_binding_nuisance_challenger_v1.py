from __future__ import annotations

import copy
import unittest

from tools import trigger2_context_binding_generator_v2 as gen
from tools import trigger2_context_binding_nuisance_challenger_v1 as chal


class Trigger2ContextBindingNuisanceChallengerV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = gen.generate_rows()

    def test_clean_factorial_rows_force_nuisance_lookup_to_chance(self):
        result = chal.challenge_rows(self.rows)
        self.assertTrue(result["pass"], result["failures"])
        self.assertAlmostEqual(result["metrics"]["ablated_prompt_exact_lookup_semantic_class_accuracy"], 1/3, places=14)
        self.assertAlmostEqual(result["metrics"]["ablated_prompt_exact_lookup_target_slot_accuracy"], 1/3, places=14)
        self.assertEqual(result["metrics"]["ablated_class_support_min"], 3)
        self.assertEqual(result["metrics"]["ablated_target_support_min"], 3)

    def test_semantic_evidence_ablation_drops_exact_lookup_from_one_to_chance(self):
        result = chal.challenge_rows(self.rows)
        m = result["metrics"]
        self.assertAlmostEqual(m["full_prompt_exact_lookup_semantic_class_accuracy"], 1.0, places=14)
        self.assertAlmostEqual(m["semantic_ablation_drop_class_accuracy"], 2/3, places=14)
        self.assertAlmostEqual(m["semantic_ablation_drop_target_accuracy"], 2/3, places=14)

    def test_nonsemantic_class_correlated_tag_is_detected(self):
        bad = copy.deepcopy(self.rows)
        for row in bad:
            if row["audit_target_semantic_class"] == "ALLOW":
                row["prompt"] += "\nTAG=red"
        result = chal.challenge_rows(bad)
        self.assertFalse(result["pass"])
        self.assertTrue(any(x.startswith("ABLATED_CLASS_LOOKUP_NOT_CHANCE:") for x in result["failures"]))

    def test_nonsemantic_target_correlated_tag_is_detected(self):
        bad = copy.deepcopy(self.rows)
        tags = {slot: f"slot-tag-{i}" for i, slot in enumerate(gen.SLOTS)}
        for row in bad:
            row["prompt"] += "\n" + tags[row["target"]]
        result = chal.challenge_rows(bad)
        self.assertFalse(result["pass"])
        self.assertTrue(any(x.startswith("ABLATED_TARGET_LOOKUP_NOT_CHANCE:") for x in result["failures"]))

    def test_missing_semantic_class_support_is_detected(self):
        bad = [r for r in self.rows if r["audit_target_semantic_class"] != "ABSTAIN"]
        result = chal.challenge_rows(bad)
        self.assertFalse(result["pass"])
        self.assertIn("ABLATED_NUISANCE_SIGNATURE_NOT_CLASS_BALANCED", result["failures"])

    def test_model_visible_projection_violation_is_detected(self):
        bad = copy.deepcopy(self.rows)
        bad[0]["model_visible_fields"] = ["prompt", "audit_target_semantic_class"]
        result = chal.challenge_rows(bad)
        self.assertFalse(result["pass"])
        self.assertTrue(any(x.startswith("MODEL_VISIBLE_PROJECTION_VIOLATION:") for x in result["failures"]))

    def test_missing_evidence_span_fails_closed(self):
        bad = copy.deepcopy(self.rows)
        bad[0]["prompt"] = bad[0]["prompt"].replace("\nEVIDENCE\n", "\nOBSERVATION\n")
        result = chal.challenge_rows(bad)
        self.assertFalse(result["pass"])
        self.assertTrue(any(x.startswith("ROW_CHALLENGE_EXCEPTION:0:ValueError:") for x in result["failures"]))


if __name__ == "__main__":
    unittest.main()
