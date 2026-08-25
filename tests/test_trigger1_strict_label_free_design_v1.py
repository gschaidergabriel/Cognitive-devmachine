from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_reconstructive_lexical_audit_gate_v1 as lexical
import trigger1_strict_label_free_design_v1 as design
import trigger1_v7_factorial_case_evidence as producer


class StrictLabelFreeDesignTest(unittest.TestCase):
    def _candidate(self) -> dict:
        return {
            "reconstructive_lexical_audit": {"basis_rows": design.basis_rows()},
            "preregistration_evidence": {
                "case_plans": {
                    "CALIBRATION": design.factorial_plan("CALIBRATION"),
                    "HOLDOUT": design.factorial_plan("HOLDOUT"),
                }
            },
            "abstract_state_deconfound": {
                "basis_model_facing_canonical_labels_absent": True,
                "holdout_model_facing_canonical_labels_absent": True,
                "basis_holdout_lexically_disjoint": True,
                "semantic_synonym_lexicon_disjoint": True,
                "lexical_audit_receipt_sha256": "a" * 64,
            },
        }

    def test_basis_has_six_exact_label_free_code_free_triads(self):
        rows = design.basis_rows()
        self.assertEqual(len(rows), 18)
        self.assertEqual(len({row["family_group_id"] for row in rows}), 6)
        for row in rows:
            lower = row["prompt"].lower()
            self.assertFalse(any(label.lower() in lower for label in design.TARGETS))
            self.assertIsNone(re.search(r"(?<![A-Za-z])[ABC](?![A-Za-z])", row["prompt"]))

    def test_factorials_are_exact_target_x_code_rotations(self):
        expected = {(target, code) for target in producer.TARGETS for code in producer.CODES}
        for split in ("CALIBRATION", "HOLDOUT"):
            plan = design.factorial_plan(split)
            self.assertEqual(
                {(row["semantic_target"], row["output_code_identity"]) for row in plan["cases"]},
                expected,
            )
            self.assertFalse(plan["model_facing_target_identity_exposed"])
            self.assertFalse(plan["model_facing_explicit_semantic_labels"])

    def test_full_strict_design_passes_reconstructive_lexical_gate(self):
        result = lexical.adjudicate(self._candidate())
        self.assertTrue(result["pass"], result["failures"])
        material = result["reconstructed_material"]
        self.assertEqual(material["within_partition_overlaps"]["basis"], [])
        self.assertEqual(material["within_partition_overlaps"]["calibration"], [])
        self.assertEqual(material["within_partition_overlaps"]["holdout"], [])
        self.assertEqual(material["cross_partition_overlap_tokens"]["BASIS_CALIBRATION"], [])
        self.assertEqual(material["cross_partition_overlap_tokens"]["BASIS_HOLDOUT"], [])
        self.assertEqual(material["cross_partition_overlap_tokens"]["CALIBRATION_HOLDOUT"], [])


if __name__ == "__main__":
    unittest.main()
