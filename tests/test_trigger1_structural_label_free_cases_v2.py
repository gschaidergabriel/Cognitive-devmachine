from __future__ import annotations

from collections import Counter
import re
import unittest

from tools import trigger1_structural_label_free_cases_v2 as cases


class StructuralCaseV2Test(unittest.TestCase):
    def test_bundle_is_lexically_disjoint_and_exact_3x3x2(self):
        b = cases.build_bundle()
        self.assertTrue(b["lexical_disjointness_audit"]["basis_holdout_lexically_disjoint"])
        self.assertEqual(b["lexical_disjointness_audit"]["content_overlap_count"], 0)
        for split in ("calibration", "holdout"):
            rows = b[split]["cases"]
            self.assertEqual(len(rows), 18)
            counts = Counter(
                (r["semantic_target"], r["output_code_identity"], r["probe_query_negated"])
                for r in rows
            )
            expected = {
                (target, code, polarity)
                for target in cases.TARGETS
                for code in cases.CODES
                for polarity in (False, True)
            }
            self.assertEqual(set(counts), expected)
            self.assertTrue(all(v == 1 for v in counts.values()))

    def test_target_code_and_polarity_counts_are_exact_not_set_only(self):
        b = cases.build_bundle()
        for split in ("calibration", "holdout"):
            rows = b[split]["cases"]
            target_code = Counter(
                (r["semantic_target"], r["output_code_identity"])
                for r in rows
            )
            target_polarity = Counter(
                (r["semantic_target"], r["probe_query_negated"])
                for r in rows
            )
            for target in cases.TARGETS:
                for code in cases.CODES:
                    self.assertEqual(target_code[(target, code)], 2)
                    polarities = {
                        r["probe_query_negated"]
                        for r in rows
                        if r["semantic_target"] == target
                        and r["output_code_identity"] == code
                    }
                    self.assertEqual(polarities, {False, True})
                self.assertEqual(target_polarity[(target, False)], 3)
                self.assertEqual(target_polarity[(target, True)], 3)

    def test_no_banned_semantic_or_compliance_lexemes_are_model_facing(self):
        b = cases.build_bundle()
        for split in ("calibration", "holdout"):
            for row in b[split]["cases"]:
                tokens = set(re.findall(r"[a-z_]+", row["prompt"].lower()))
                for word in cases.BANNED_MODEL_FACING:
                    self.assertNotIn(word, tokens)
                self.assertNotIn(row["semantic_target"].lower(), tokens)

    def test_demo_and_probe_lexical_context_are_shared_across_polarities_and_targets(self):
        b = cases.build_bundle()
        for split in ("calibration", "holdout"):
            rows = b[split]["cases"]
            by_scenario = {}
            for row in rows:
                by_scenario.setdefault(row["scenario_family_sha256"], []).append(row)
            self.assertEqual(len(by_scenario), 3)
            for group in by_scenario.values():
                self.assertEqual(len(group), 6)
                self.assertEqual(
                    Counter(r["semantic_target"] for r in group),
                    Counter({target: 2 for target in cases.TARGETS}),
                )
                self.assertEqual(
                    Counter(r["probe_query_negated"] for r in group),
                    Counter({False: 3, True: 3}),
                )
                self.assertEqual(len({r["demo_context_sha256"] for r in group}), 1)
                self.assertEqual(len({r["lexical_family_sha256"] for r in group}), 1)
                for target in cases.TARGETS:
                    polarities = {
                        r["probe_query_negated"]
                        for r in group
                        if r["semantic_target"] == target
                    }
                    self.assertEqual(polarities, {False, True})

    def test_joint_demo_context_plus_query_polarity_has_zero_target_information(self):
        b = cases.build_bundle()
        for split in ("calibration", "holdout"):
            audit = b[split]["joint_nuisance_audit"]
            self.assertAlmostEqual(
                audit["target_query_polarity_mutual_information_bits"],
                0.0,
                places=12,
            )
            self.assertAlmostEqual(
                audit["target_joint_demo_context_query_polarity_mutual_information_bits"],
                0.0,
                places=12,
            )
            self.assertAlmostEqual(
                audit["best_target_accuracy_using_demo_context_plus_query_polarity"],
                audit["balanced_target_prior_accuracy"],
                places=12,
            )
            self.assertTrue(
                audit["every_demo_context_x_query_polarity_stratum_contains_all_targets_once"]
            )

    def test_joint_nuisance_audit_rejects_old_six_scenario_phase_coupling(self):
        bad = []
        for scenario in range(6):
            for target_index, target in enumerate(cases.TARGETS):
                bad.append(
                    {
                        "semantic_target": target,
                        "demo_context_sha256": f"demo-{scenario}",
                        "probe_query_negated": bool((scenario + target_index) % 2),
                    }
                )
        with self.assertRaisesRegex(
            AssertionError,
            "JOINT_DEMO_QUERY_TARGET_IMBALANCE|TARGET_JOINT_DEMO_QUERY_POLARITY_MI_NONZERO",
        ):
            cases._joint_nuisance_audit(bad)

    def test_deterministic_bundle_hash_and_nonpromotion_boundary(self):
        a = cases.build_bundle()
        b = cases.build_bundle()
        self.assertEqual(a["bundle_sha256"], b["bundle_sha256"])
        self.assertFalse(a["model_executed"])
        self.assertFalse(a["runtime_credit_minted"])
        self.assertFalse(a["canonical_semantic_jspace_promotion"])


if __name__ == "__main__":
    unittest.main()
