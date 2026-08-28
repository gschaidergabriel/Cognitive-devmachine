from __future__ import annotations

import re
import unittest

from tools import trigger1_structural_label_free_cases as cases


class StructuralCaseTest(unittest.TestCase):
    def test_bundle_is_lexically_disjoint_and_3x3(self):
        b = cases.build_bundle()
        self.assertTrue(b["lexical_disjointness_audit"]["basis_holdout_lexically_disjoint"])
        self.assertEqual(b["lexical_disjointness_audit"]["content_overlap_count"], 0)
        for split in ("calibration", "holdout"):
            rows = b[split]["cases"]
            self.assertEqual(len(rows), 9)
            observed = {(r["semantic_target"], r["output_code_identity"]) for r in rows}
            expected = {(t, c) for t in cases.TARGETS for c in cases.CODES}
            self.assertEqual(observed, expected)

    def test_no_banned_semantic_or_compliance_lexemes_are_model_facing(self):
        b = cases.build_bundle()
        for split in ("calibration", "holdout"):
            for row in b[split]["cases"]:
                tokens = set(re.findall(r"[a-z_]+", row["prompt"].lower()))
                for word in cases.BANNED_MODEL_FACING:
                    self.assertNotIn(word, tokens)
                self.assertNotIn(row["semantic_target"].lower(), tokens)

    def test_query_polarity_is_not_a_class_shortcut(self):
        b = cases.build_bundle()
        for split in ("calibration", "holdout"):
            rows = b[split]["cases"]
            for target in cases.TARGETS:
                polarities = {r["probe_query_negated"] for r in rows if r["semantic_target"] == target}
                self.assertEqual(polarities, {False, True})

    def test_each_scenario_rotates_all_targets_and_codes(self):
        b = cases.build_bundle()
        for split in ("calibration", "holdout"):
            rows = b[split]["cases"]
            by_scenario = {}
            for row in rows:
                by_scenario.setdefault(row["scenario_family_sha256"], []).append(row)
            self.assertEqual(len(by_scenario), 3)
            for group in by_scenario.values():
                self.assertEqual({r["semantic_target"] for r in group}, set(cases.TARGETS))
                self.assertEqual({r["output_code_identity"] for r in group}, set(cases.CODES))
                self.assertEqual(len({r["lexical_family_sha256"] for r in group}), 1)

    def test_deterministic_bundle_hash(self):
        a = cases.build_bundle()
        b = cases.build_bundle()
        self.assertEqual(a["bundle_sha256"], b["bundle_sha256"])


if __name__ == "__main__":
    unittest.main()
