from __future__ import annotations

import copy
import hashlib
import unittest

from tools import trigger1_abstract_state_counterbalance_v1 as design


class AbstractStateCounterbalanceTests(unittest.TestCase):
    def test_design_closes_label_compliance_lexical_and_counterbalance_shortcuts(self):
        receipt = design.validate()
        self.assertEqual(receipt["row_count"], 36)
        self.assertEqual(receipt["family_count"], 12)
        self.assertEqual(receipt["families_per_split"], {"CALIBRATION": 6, "HOLDOUT": 6})
        self.assertTrue(receipt["model_facing_labels_absent"])
        self.assertTrue(receipt["generic_compliance_scaffold_absent"])
        self.assertEqual(receipt["calibration_holdout_content_lexeme_overlap"], [])
        self.assertTrue(receipt["nuisance_affect_counterbalanced"])
        self.assertTrue(receipt["surface_form_counterbalanced"])
        self.assertTrue(receipt["presentation_position_counterbalanced"])

    def test_all_rows_end_at_identical_neutral_suffix(self):
        rows = design.build_rows()
        self.assertEqual({row["prompt"].split()[-2:] for row in rows}, {("Context", "complete.")})

    def test_model_facing_evaluator_label_leak_fails_closed(self):
        rows = copy.deepcopy(design.build_rows())
        rows[0]["prompt"] += " AFFIRMATIVE"
        rows[0]["prompt_sha256"] = hashlib.sha256(rows[0]["prompt"].encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(ValueError, "MODEL_FACING_SHORTCUT_PRESENT"):
            design.validate(rows)

    def test_cross_split_content_lexeme_leak_fails_closed(self):
        rows = copy.deepcopy(design.build_rows())
        holdout = next(row for row in rows if row["split"] == "HOLDOUT")
        holdout["prompt"] = holdout["prompt"].replace("Context complete.", "charter Context complete.")
        holdout["prompt_sha256"] = hashlib.sha256(holdout["prompt"].encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(ValueError, "CALIBRATION_HOLDOUT_LEXICAL_OVERLAP"):
            design.validate(rows)

    def test_counterbalance_corruption_fails_closed(self):
        rows = copy.deepcopy(design.build_rows())
        subset = [r for r in rows if r["split"] == "CALIBRATION" and r["semantic_class"] == "AFFIRMATIVE"]
        subset[0]["nuisance_affect"] = subset[1]["nuisance_affect"]
        with self.assertRaisesRegex(ValueError, "COUNTERBALANCE_FAILED"):
            design.validate(rows)


if __name__ == "__main__":
    unittest.main()
