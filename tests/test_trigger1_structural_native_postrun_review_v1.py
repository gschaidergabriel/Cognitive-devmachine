from __future__ import annotations

import copy
import unittest

from tools import trigger1_structural_label_free_cases as structural
from tools import trigger1_structural_native_postrun_review_v1 as review


GOOD_MATRIX = {
    "AFFIRMATIVE": {"AFFIRMATIVE": 2.0, "NEGATIVE": 0.2, "NEUTRAL": 0.1},
    "NEGATIVE": {"AFFIRMATIVE": 0.1, "NEGATIVE": 2.2, "NEUTRAL": 0.2},
    "NEUTRAL": {"AFFIRMATIVE": 0.2, "NEGATIVE": 0.1, "NEUTRAL": 1.9},
}


def fake_result(matrix=None, *, passed=True):
    matrix = copy.deepcopy(matrix or GOOD_MATRIX)
    diagonal = [matrix[c][c] for c in review.CLASSES]
    off = [matrix[i][j] for i in review.CLASSES for j in review.CLASSES if i != j]
    return {
        "schema": review.RUNTIME_SCHEMA,
        "status": "PASS_ABSTRACT_NATIVE_DISCRIMINATOR" if passed else "FAIL_ABSTRACT_NATIVE_DISCRIMINATOR",
        "abstract_native_discriminator_pass": passed,
        "behavioral_causal_matrix": {
            "mean_delta_matrix_intervention_x_requested_target": matrix,
            "diagonal_mean": sum(diagonal) / len(diagonal),
            "off_diagonal_mean": sum(off) / len(off),
            "diagonal_advantage": sum(diagonal) / len(diagonal) - sum(off) / len(off),
            "diagonal_each_positive": all(x > 0 for x in diagonal),
        },
    }


class StructuralNativePostrunReviewTests(unittest.TestCase):
    def test_current_generator_is_lexically_disjoint_but_template_overlapping(self):
        bundle = structural.build_bundle()
        self.assertTrue(bundle["lexical_disjointness_audit"]["basis_holdout_lexically_disjoint"])
        audited = review.audit_templates(bundle)
        self.assertFalse(audited["template_disjoint"])
        self.assertGreater(audited["overlap_count"], 0)
        self.assertIn("CALIBRATION_HOLDOUT_STRUCTURAL_TEMPLATE_OVERLAP", audited["failures"])

    def test_strong_structural_candidate_does_not_imply_template_invariant_semantics(self):
        result = review.adjudicate(fake_result(), structural.build_bundle())
        self.assertTrue(result["strong_structural_native_component_candidate"])
        self.assertFalse(result["template_invariant_abstract_semantic_candidate"])
        self.assertFalse(result["semantic_jspace_promotion_candidate"])
        self.assertFalse(result["canonical_semantics_promotion"])
        self.assertEqual(result["jspace_model_runtime_credit"], 0)
        self.assertFalse(result["frozen_scientific_design_modified"])
        self.assertFalse(result["new_model_intervention_executed"])
        self.assertIn("TEMPLATE_INVARIANT_ABSTRACTION_NOT_ESTABLISHED", result["failures"])

    def test_one_failed_class_cannot_be_rescued_by_aggregate_effect(self):
        matrix = copy.deepcopy(GOOD_MATRIX)
        matrix["NEUTRAL"]["NEUTRAL"] = -0.1
        result = review.adjudicate(fake_result(matrix), structural.build_bundle())
        self.assertFalse(result["strong_structural_native_component_candidate"])
        audit = result["per_class_causal_selectivity"]
        self.assertFalse(audit["every_class_positive"])
        self.assertIn("NOT_EVERY_CLASS_HAS_POSITIVE_MATCHED_CAUSAL_EFFECT", audit["failures"])

    def test_row_nonselective_matched_intervention_fails(self):
        matrix = copy.deepcopy(GOOD_MATRIX)
        matrix["AFFIRMATIVE"]["NEGATIVE"] = 2.5
        result = review.adjudicate(fake_result(matrix), structural.build_bundle())
        self.assertFalse(result["strong_structural_native_component_candidate"])
        self.assertFalse(result["per_class_causal_selectivity"]["row_selective_every_class"])

    def test_column_nonselective_matched_intervention_fails(self):
        matrix = copy.deepcopy(GOOD_MATRIX)
        matrix["NEGATIVE"]["AFFIRMATIVE"] = 2.5
        result = review.adjudicate(fake_result(matrix), structural.build_bundle())
        self.assertFalse(result["strong_structural_native_component_candidate"])
        self.assertFalse(result["per_class_causal_selectivity"]["column_selective_every_class"])

    def test_runner_pass_claim_is_required(self):
        result = review.adjudicate(fake_result(passed=False), structural.build_bundle())
        self.assertFalse(result["strong_structural_native_component_candidate"])
        self.assertIn("FROZEN_RUNTIME_PASS_REQUIRED", result["failures"])


if __name__ == "__main__":
    unittest.main()
