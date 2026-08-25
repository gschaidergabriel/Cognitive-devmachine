from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from validate_claycode_cognitive_protocol_v1 import ProtocolValidationError, validate

PROTOCOL = ROOT / "research_entity/global/CLAYCODE_COGNITIVE_PROTOCOL_v1.clay"
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"


class ClayCodeCognitiveProtocolV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PROTOCOL.read_text(encoding="utf-8")
        cls.grammar = GRAMMAR.read_text(encoding="utf-8")

    def test_current_protocol_parses_and_validates(self):
        result = validate(self.source, self.grammar)
        self.assertTrue(result["ok"])
        self.assertEqual("ClayCodeBaseFrontendAST/v1", result["frontend_schema"])
        self.assertEqual("BASE_D_V18_REWARD_RELATIONS", result["surface"])
        self.assertEqual("cd75d706b5d1d1734fe57143c8581ddc46411af8905c879ee4c78ebfef4d1b3f", result["semantic_hash"])
        self.assertEqual(0, result["runtime_credit"])
        self.assertEqual(0, result["jspace_credit"])
        self.assertEqual(0, result["training_credit"])

    def test_result_class_cannot_gain_deterministic_or_effect_authority(self):
        bad = self.source.replace(
            "type ResultClass = CANDIDATE|PROJECTION|MEASUREMENT",
            "type ResultClass = CANDIDATE|PROJECTION|MEASUREMENT|DETERMINISTIC_CONTROL_RESULT",
        )
        with self.assertRaisesRegex(ProtocolValidationError, "RESULT_CLASS_AUTHORITY_ESCALATION"):
            validate(bad, self.grammar)

    def test_effect_proposal_cannot_lose_effectgate_fence(self):
        bad = self.source.replace("rule EffectProposal cannot_authorize RealEffect\n", "")
        with self.assertRaisesRegex(ProtocolValidationError, "MANDATORY_AUTHORITY_RULE_MISSING"):
            validate(bad, self.grammar)

    def test_work_packet_cannot_drop_generation(self):
        bad = self.source.replace("generation:Int\nwork_id:String\nprocess_id:String\n", "work_id:String\nprocess_id:String\n", 1)
        with self.assertRaisesRegex(ProtocolValidationError, "REQUIRED_FIELD_MISSING_CognitiveWorkPacket"):
            validate(bad, self.grammar)

    def test_current_abi_parent_cannot_be_removed(self):
        bad = self.source.replace("@research_entity/global/COGNITIVE_PROCESS_ABI_v1.json,", "")
        with self.assertRaisesRegex(ProtocolValidationError, "CURRENT_CONTRACT_PARENT_MISSING"):
            validate(bad, self.grammar)

    def test_grid_n_cannot_define_process_identity(self):
        bad = self.source.replace("rule GridRuntime.requested_N never_implies CognitiveProcessIdentity\n", "")
        with self.assertRaisesRegex(ProtocolValidationError, "MANDATORY_AUTHORITY_RULE_MISSING"):
            validate(bad, self.grammar)

    def test_jspace_measurement_cannot_mint_fact(self):
        bad = self.source.replace("rule JSpaceMeasurement never_confers CanonicalFact\n", "")
        with self.assertRaisesRegex(ProtocolValidationError, "MANDATORY_AUTHORITY_RULE_MISSING"):
            validate(bad, self.grammar)

    def test_unknown_cannot_collapse_to_false(self):
        bad = self.source.replace("rule UNKNOWN distinct_from false\n", "")
        with self.assertRaisesRegex(ProtocolValidationError, "MANDATORY_AUTHORITY_RULE_MISSING"):
            validate(bad, self.grammar)


if __name__ == "__main__":
    unittest.main()
