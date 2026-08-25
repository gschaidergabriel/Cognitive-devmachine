from __future__ import annotations

import re
import unittest

from tools import trigger1_structural_label_free_cases_v2 as cases


class StructuralCaseV2Test(unittest.TestCase):
    def test_complete_target_code_query_polarity_factorial(self):
        bundle = cases.build_bundle()
        expected = {
            (target, code, polarity)
            for target in cases.TARGETS
            for code in cases.CODES
            for polarity in (False, True)
        }
        for split in ("calibration", "holdout"):
            rows = bundle[split]["cases"]
            self.assertEqual(len(rows), 18)
            observed = {
                (
                    row["semantic_target"],
                    row["output_code_identity"],
                    row["probe_query_negated"],
                )
                for row in rows
            }
            self.assertEqual(observed, expected)
            for target in cases.TARGETS:
                for code in cases.CODES:
                    polarities = {
                        row["probe_query_negated"]
                        for row in rows
                        if row["semantic_target"] == target
                        and row["output_code_identity"] == code
                    }
                    self.assertEqual(polarities, {False, True})

    def test_query_polarity_is_exactly_independent_of_target_and_code(self):
        bundle = cases.build_bundle()
        for split in ("calibration", "holdout"):
            audit = bundle[split]["query_polarity_factorial_audit"]
            self.assertTrue(audit["complete_target_x_code_x_query_polarity"])
            self.assertEqual(audit["cell_replication_count"], 1)
            self.assertAlmostEqual(
                audit["target_query_polarity_mutual_information_bits"], 0.0, places=12
            )
            self.assertAlmostEqual(
                audit["output_code_query_polarity_mutual_information_bits"], 0.0, places=12
            )
            self.assertAlmostEqual(
                audit["best_target_accuracy_using_query_polarity_alone"],
                audit["balanced_target_prior_accuracy"],
                places=12,
            )
            for target in cases.TARGETS:
                self.assertEqual(
                    audit["target_query_polarity_counts"][target],
                    {"positive_query": 3, "negated_query": 3},
                )

    def test_demo_context_does_not_encode_probe_polarity_phase(self):
        bundle = cases.build_bundle()
        for split in ("calibration", "holdout"):
            rows = bundle[split]["cases"]
            for target in cases.TARGETS:
                for code in cases.CODES:
                    pair = [
                        row
                        for row in rows
                        if row["semantic_target"] == target
                        and row["output_code_identity"] == code
                    ]
                    self.assertEqual(len(pair), 2)
                    prefixes = {
                        row["prompt"].split("|P[", 1)[0]
                        for row in pair
                    }
                    self.assertEqual(len(prefixes), 1)

    def test_lexical_disjointness_and_model_facing_lexeme_fence_survive(self):
        bundle = cases.build_bundle()
        audit = bundle["lexical_disjointness_audit"]
        self.assertTrue(audit["basis_holdout_lexically_disjoint"])
        self.assertEqual(audit["content_overlap_count"], 0)

        for split in ("calibration", "holdout"):
            for row in bundle[split]["cases"]:
                tokens = set(re.findall(r"[a-z_]+", row["prompt"].lower()))
                for word in cases.BANNED_MODEL_FACING:
                    self.assertNotIn(word, tokens)
                self.assertNotIn(row["semantic_target"].lower(), tokens)
                self.assertFalse(row["model_facing_target_identity_exposed"])
                self.assertFalse(row["model_facing_explicit_semantic_labels"])
                self.assertFalse(row["model_facing_query_polarity_phase_exposed"])

    def test_successor_is_execution_free_and_deterministic(self):
        first = cases.build_bundle()
        second = cases.build_bundle()
        self.assertEqual(first["bundle_sha256"], second["bundle_sha256"])
        self.assertFalse(first["model_executed"])
        self.assertFalse(first["runtime_credit_minted"])
        self.assertFalse(first["canonical_semantic_jspace_promotion"])
        self.assertFalse(first["frozen_v1_modified"])


if __name__ == "__main__":
    unittest.main()
