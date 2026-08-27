from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.validate_global_workspace_reentry_receipt_contract_v1 import (
    GlobalWorkspaceReentryContractError,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "research_entity/global/GLOBAL_WORKSPACE_REENTRY_RECEIPT_CONTRACT_v1.json"


class GlobalWorkspaceReentryReceiptContractV1Tests(unittest.TestCase):
    def setUp(self):
        self.value = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_exact_contract_passes(self):
        result = validate(self.value)
        self.assertTrue(result["ok"])
        self.assertEqual(result["receipt_schema"], "GLOBAL_WORKSPACE_REENTRY_RECEIPT/v1")
        self.assertEqual(result["control_binding_count"], 11)
        self.assertEqual(result["discriminator_count"], 6)
        self.assertEqual(result["maximum_causal_credit"], "OBSERVABLE_WORKSPACE_REENTRY")

    def test_matched_control_cannot_be_removed(self):
        bad = copy.deepcopy(self.value)
        bad["required_control_binding"].remove("matched_control_ref")
        with self.assertRaisesRegex(GlobalWorkspaceReentryContractError, "MATCHED_CONTROL_BINDING_INCOMPLETE"):
            validate(bad)

    def test_credit_cannot_jump_to_model_specific_jspace(self):
        bad = copy.deepcopy(self.value)
        bad["allowed_causal_credit"].append("MODEL_SPECIFIC_CAUSAL_JSPACE")
        with self.assertRaisesRegex(GlobalWorkspaceReentryContractError, "CAUSAL_CREDIT_SCOPE_INFLATED"):
            validate(bad)

    def test_claude_hidden_activation_claim_ceiling_is_fail_closed(self):
        bad = copy.deepcopy(self.value)
        bad["jspace_claim_ceiling"]["claude_hidden_activation_access"] = "ASSUMED_FROM_SESSION"
        with self.assertRaisesRegex(GlobalWorkspaceReentryContractError, "CLAUDE_HIDDEN_ACCESS_CLAIM_CEILING_MISSING"):
            validate(bad)

    def test_frozen_v1_negative_evidence_cannot_be_erased(self):
        bad = copy.deepcopy(self.value)
        bad["jspace_claim_ceiling"]["frozen_v1_negative_evidence"] = "IGNORE"
        with self.assertRaisesRegex(GlobalWorkspaceReentryContractError, "FROZEN_V1_NEGATIVE_EVIDENCE_MUST_BE_PRESERVED"):
            validate(bad)

    def test_effectgate_effectjournal_remain_sole_real_effect_path(self):
        bad = copy.deepcopy(self.value)
        bad["authority_fences"]["real_effect_path"] = "CLAUDE_DIRECT"
        with self.assertRaisesRegex(GlobalWorkspaceReentryContractError, "REAL_EFFECT_PATH_MISMATCH"):
            validate(bad)

    def test_runtime_credit_cannot_be_minted_by_contract(self):
        bad = copy.deepcopy(self.value)
        bad["credit_boundary"]["observable_workspace_reentry_runtime_credit"] = 1
        with self.assertRaisesRegex(GlobalWorkspaceReentryContractError, "RUNTIME_CREDIT_INFLATION:observable_workspace_reentry_runtime_credit"):
            validate(bad)


if __name__ == "__main__":
    unittest.main()
