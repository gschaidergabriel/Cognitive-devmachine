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
            expected = {(t, c, p) for t in cases.TARGETS for c in cases.CODES for p in (False, True)}
            self.assertEqual(set(counts), expected)
            self.assertTrue(all(v == 1 for v in counts.values()))

    def test_target_code_and_polarity_counts_are_exact_not_set_only(self):
        b = cases.build_bundle()
        for split in ("calibration", "holdout"):
            rows = b[split]["cases"]
            target_code = Counter((r["semantic_target"], r["output_code_identity"]) for r in rows)
            target_polarity = Counter((r["semantic_target"], r["probe_query_negated"]) for r in rows)
            for target in cases.TARGETS:
                for code in cases.CODES:
                    self.assertEqual(target_code[(target, code)], 2)
                    polarities = {
                        r["probe_query_negated"]
                        for r in rows
                        if r["semantic_target"] == target and r["output_code_identity"] == code
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

    def test_probe_lexical_identity_is_target_neutral_within_scenario(self):
        b = cases.build_bundle()
        for split in ("calibration", "holdout"):
            rows = b[split]["cases"]
            by_scenario = {}
            for row in rows:
                by_scenario.setdefault(row["scenario_family_sha256"], []).append(row)
            self.assertEqual(len(by_scenario), 6)
            for group in by_scenario.values():
                self.assertEqual(len(group), 3)
                self.assertEqual({r["semantic_target"] for r in group}, set(cases.TARGETS))
                self.assertEqual({r["output_code_identity"] for r in group}, set(cases.CODES))
                self.assertEqual(len({r["lexical_family_sha256"] for r in group}), 1)

    def test_deterministic_bundle_hash(self):
        a = cases.build_bundle()
        b = cases.build_bundle()
        self.assertEqual(a["bundle_sha256"], b["bundle_sha256"])


if __name__ == "__main__":
    unittest.main()
