from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.validate_cognitive_process_abi_v1 import (
    CognitiveProcessABIValidationError,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]
ABI = ROOT / "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json"

class CognitiveProcessABIV1Tests(unittest.TestCase):
    def setUp(self):
        self.value = json.loads(ABI.read_text(encoding="utf-8"))

    def test_exact_contract_passes(self):
        result = validate(self.value)
        self.assertTrue(result["ok"])
        self.assertEqual(result["process_count"], 20)
        self.assertEqual(result["packet_type_count"], 8)
        self.assertEqual(result["owner_acceptance_coverage"], 10)
        self.assertEqual(result["sole_real_effect_path"], "EFFECT_PROPOSAL/v1->EffectGate->EffectJournal")

    def test_grid_n_cannot_define_semantic_work_identity(self):
        bad = copy.deepcopy(self.value)
        bad["semantic_identity"]["work_id_inputs"].append("grid_n")
        with self.assertRaisesRegex(CognitiveProcessABIValidationError, "GRID_N_MUST_NOT_DEFINE_WORK_ID"):
            validate(bad)

    def test_model_packet_cannot_gain_direct_s0_write(self):
        bad = copy.deepcopy(self.value)
        bad["packet_types"]["COGNITIVE_RESULT/v1"]["may_write"] = ["S0", "S1"]
        with self.assertRaisesRegex(CognitiveProcessABIValidationError, "PACKET_DIRECT_S0_WRITE_FORBIDDEN"):
            validate(bad)

    def test_effect_path_cannot_bypass_gate_and_journal(self):
        bad = copy.deepcopy(self.value)
        bad["effect_boundary"]["only_real_effect_path"] = ["EFFECT_PROPOSAL/v1", "ClaudeCode"]
        with self.assertRaisesRegex(CognitiveProcessABIValidationError, "EFFECT_PATH_MISMATCH"):
            validate(bad)

    def test_claude_bridge_requires_matched_control_for_causal_reentry(self):
        bad = copy.deepcopy(self.value)
        bad["claude_code_bridge"]["causal_credit_rule"] = "TRANSFER_PRESENT_IS_ENOUGH"
        with self.assertRaisesRegex(CognitiveProcessABIValidationError, "REENTRY_CAUSAL_CONTROL_REQUIRED"):
            validate(bad)

    def test_jspace_frozen_v1_negative_evidence_cannot_be_erased(self):
        bad = copy.deepcopy(self.value)
        bad["jspace"]["frozen_v1_negative_evidence_preserved"] = False
        with self.assertRaisesRegex(CognitiveProcessABIValidationError, "FROZEN_V1_NEGATIVE_EVIDENCE_MUST_BE_PRESERVED"):
            validate(bad)

    def test_runtime_credit_cannot_be_minted_by_source_contract(self):
        bad = copy.deepcopy(self.value)
        bad["credit_boundary"]["jspace_model_runtime_credit"] = 1
        with self.assertRaisesRegex(CognitiveProcessABIValidationError, "CREDIT_INFLATION:jspace_model_runtime_credit"):
            validate(bad)

    def test_owner_final_acceptance_coverage_must_remain_complete(self):
        bad = copy.deepcopy(self.value)
        bad["owner_target_coverage"].pop("10_08b_specialized_low_refusal_capability_retained")
        with self.assertRaisesRegex(CognitiveProcessABIValidationError, "OWNER_ACCEPTANCE_COVERAGE_MUST_BE_10_OF_10"):
            validate(bad)

if __name__ == "__main__":
    unittest.main()
