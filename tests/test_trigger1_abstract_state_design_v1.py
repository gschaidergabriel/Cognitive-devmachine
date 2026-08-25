from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_abstract_state_design_v1 as design
import trigger1_abstract_state_text_audit as audit


class AbstractStateDesignTests(unittest.TestCase):
    def test_frozen_design_passes_actual_text_audit(self):
        result = audit.audit({
            "schema": audit.SCHEMA,
            "basis_design": design.basis_design(),
            "calibration_plan": {"cases": design.case_specs("CALIBRATION")},
            "holdout_plan": {"cases": design.case_specs("HOLDOUT")},
        })
        self.assertTrue(result["pass"], result["failures"])
        self.assertEqual({}, result["diagnostics"]["basis_repeated_class_markers"])

    def test_each_split_is_exact_counterbalanced_three_by_three(self):
        for split in ("CALIBRATION", "HOLDOUT"):
            specs = design.case_specs(split)
            cells = {(row["semantic_target"], row["output_code_identity"]) for row in specs}
            self.assertEqual(
                {(target, code) for target in design.TARGETS for code in design.CODES},
                cells,
            )
            by_scenario = {}
            for row in specs:
                by_scenario.setdefault(row["scenario_family_sha256"], []).append(row)
            self.assertEqual(3, len(by_scenario))
            for rows in by_scenario.values():
                self.assertEqual(set(design.TARGETS), {row["semantic_target"] for row in rows})
                self.assertEqual(set(design.CODES), {row["output_code_identity"] for row in rows})

    def test_model_facing_text_contains_no_canonical_metadata_labels(self):
        texts = [row["prompt"] for row in design.basis_design()["rows"]]
        texts += [row["prompt"] for split in ("CALIBRATION", "HOLDOUT") for row in design.case_specs(split)]
        joined = "\n".join(texts).lower()
        for label in ("affirmative", "negative", "neutral"):
            self.assertNotIn(label, joined)


if __name__ == "__main__":
    unittest.main()
