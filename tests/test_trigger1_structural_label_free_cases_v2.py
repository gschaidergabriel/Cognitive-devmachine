from __future__ import annotations

import re
import unittest
from collections import Counter, defaultdict

from tools import trigger1_structural_label_free_cases_v2 as cases


class StructuralCompleteFactorialV2Test(unittest.TestCase):
    def test_bundle_is_lexically_disjoint_and_complete_3x3x2(self):
        bundle = cases.build_bundle()
        self.assertTrue(bundle["lexical_disjointness_audit"]["basis_holdout_lexically_disjoint"])
        self.assertEqual(bundle["lexical_disjointness_audit"]["content_overlap_count"], 0)
        for split in ("calibration", "holdout"):
            rows = bundle[split]["cases"]
            self.assertEqual(len(rows), 18)
            counts = Counter(
                (row["semantic_target"], row["output_code_identity"], row["probe_query_negated"])
                for row in rows
            )
            expected = {(t, c, p) for t in cases.TARGETS for c in cases.CODES for p in cases.POLARITIES}
            self.assertEqual(set(counts), expected)
            self.assertEqual(set(counts.values()), {1})

    def test_query_polarity_is_exactly_independent_of_target_and_code(self):
        bundle = cases.build_bundle()
        for split in ("calibration", "holdout"):
            rows = bundle[split]["cases"]
            target_counts = Counter((r["semantic_target"], r["probe_query_negated"]) for r in rows)
            for target in cases.TARGETS:
                self.assertEqual(target_counts[(target, False)], target_counts[(target, True)])
            target_code_counts = Counter(
                (r["semantic_target"], r["output_code_identity"], r["probe_query_negated"]) for r in rows
            )
            for target in cases.TARGETS:
                for code in cases.CODES:
                    self.assertEqual(target_code_counts[(target, code, False)], 1)
                    self.assertEqual(target_code_counts[(target, code, True)], 1)

    def test_paired_polarity_cases_share_demonstrations_and_symbols(self):
        bundle = cases.build_bundle()
        for split in ("calibration", "holdout"):
            grouped = defaultdict(list)
            for row in bundle[split]["cases"]:
                grouped[row["paired_polarity_family_sha256"]].append(row)
            self.assertEqual(len(grouped), 9)
            for pair in grouped.values():
                self.assertEqual(len(pair), 2)
                self.assertEqual({r["probe_query_negated"] for r in pair}, {False, True})
                prompts = [r["prompt"] for r in pair]
                demos = [p.split("|P[", 1)[0] for p in prompts]
                self.assertEqual(demos[0], demos[1])

    def test_no_banned_semantic_or_compliance_lexemes_are_model_facing(self):
        bundle = cases.build_bundle()
        for split in ("calibration", "holdout"):
            for row in bundle[split]["cases"]:
                tokens = set(re.findall(r"[a-z_]+", row["prompt"].lower()))
                for word in cases.BANNED_MODEL_FACING:
                    self.assertNotIn(word, tokens)
                self.assertNotIn(row["semantic_target"].lower(), tokens)

    def test_every_scenario_rotates_all_targets_and_codes_for_each_polarity(self):
        bundle = cases.build_bundle()
        for split in ("calibration", "holdout"):
            by_scenario = defaultdict(list)
            for row in bundle[split]["cases"]:
                by_scenario[row["scenario_family_sha256"]].append(row)
            self.assertEqual(len(by_scenario), 3)
            for group in by_scenario.values():
                self.assertEqual(len(group), 6)
                for polarity in cases.POLARITIES:
                    stratum = [r for r in group if r["probe_query_negated"] is polarity]
                    self.assertEqual({r["semantic_target"] for r in stratum}, set(cases.TARGETS))
                    self.assertEqual({r["output_code_identity"] for r in stratum}, set(cases.CODES))

    def test_deterministic_bundle_hash(self):
        self.assertEqual(cases.build_bundle()["bundle_sha256"], cases.build_bundle()["bundle_sha256"])


if __name__ == "__main__":
    unittest.main()
