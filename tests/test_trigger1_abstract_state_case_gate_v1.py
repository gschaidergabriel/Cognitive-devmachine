from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_abstract_relational_design_v1 as designer
import trigger1_abstract_state_case_gate_v1 as gate
import trigger1_v7_factorial_case_evidence as producer

EXPECTED_DESIGN_SHA256 = "e4840576910ebbb2ec1764fd4fc4733b119edd23fef99d464f42241c2838d5fa"


def candidate_from_design(design: dict) -> dict:
    cal = producer.build_plan("CALIBRATION", copy.deepcopy(design["factorial_calibration"]["cases"]))
    hold = producer.build_plan("HOLDOUT", copy.deepcopy(design["holdout"]["cases"]))
    return {
        "abstract_state_design": copy.deepcopy(design),
        "preregistration_evidence": {"case_plans": {"CALIBRATION": cal, "HOLDOUT": hold}},
    }


class Trigger1AbstractStateCaseGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.design = designer.build_design()

    def test_frozen_design_and_producer_plans_pass(self):
        self.assertEqual(self.design["design_sha256"], EXPECTED_DESIGN_SHA256)
        verdict = gate.validate(candidate_from_design(self.design))
        self.assertTrue(verdict["pass"], verdict["failures"])
        self.assertEqual(verdict["payload_lexicon_overlaps"]["basis_x_calibration"], [])
        self.assertEqual(verdict["payload_lexicon_overlaps"]["basis_x_holdout"], [])
        self.assertEqual(verdict["payload_lexicon_overlaps"]["calibration_x_holdout"], [])
        self.assertEqual(verdict["payload_lexicon_sizes"], {"basis": 18, "calibration": 9, "holdout": 9})

    def test_model_facing_generic_decision_lexeme_is_rejected(self):
        candidate = candidate_from_design(self.design)
        row = candidate["preregistration_evidence"]["case_plans"]["CALIBRATION"]["cases"][0]
        row["prompt"] += "\napproval"
        row["prompt_sha256"] = hashlib.sha256(row["prompt"].encode()).hexdigest()
        verdict = gate.validate(candidate)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any("FORBIDDEN_MODEL_FACING_LEXEMES:approval" in x for x in verdict["failures"]))

    def test_payload_lexicon_overlap_across_basis_and_holdout_is_rejected(self):
        candidate = candidate_from_design(self.design)
        row = candidate["preregistration_evidence"]["case_plans"]["HOLDOUT"]["cases"][0]
        row["prompt"] = row["prompt"].replace("cim>yot,yot>lef;query=cim>yot", "miv>zor,zor>pel;query=miv>zor")
        row["prompt_sha256"] = hashlib.sha256(row["prompt"].encode()).hexdigest()
        verdict = gate.validate(candidate)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any(x.startswith("PAYLOAD_LEXICON_OVERLAP:basis_x_holdout") for x in verdict["failures"]))

    def test_structural_state_not_metadata_assertion_controls_target(self):
        candidate = candidate_from_design(self.design)
        row = candidate["preregistration_evidence"]["case_plans"]["CALIBRATION"]["cases"][0]
        row["semantic_target"] = "NEGATIVE"
        verdict = gate.validate(candidate)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any("SEMANTIC_TARGET_NOT_STRUCTURALLY_DERIVED" in x for x in verdict["failures"]))

    def test_operational_codebook_controls_output_code(self):
        candidate = candidate_from_design(self.design)
        row = candidate["preregistration_evidence"]["case_plans"]["CALIBRATION"]["cases"][0]
        row["output_code_identity"] = "B"
        verdict = gate.validate(candidate)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any("OUTPUT_CODE_NOT_OPERATIONALLY_DERIVED" in x for x in verdict["failures"]))


if __name__ == "__main__":
    unittest.main()
