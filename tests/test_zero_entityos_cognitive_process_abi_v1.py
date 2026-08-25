from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.validate_zero_entityos_cognitive_process_abi_v1 import ABIValidationError, validate

ABI = ROOT / "research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_ABI_v1.json"


class ZeroEntityOSCognitiveProcessABIV1Tests(unittest.TestCase):
    def setUp(self):
        self.value = json.loads(ABI.read_text(encoding="utf-8"))

    def test_exact_contract_passes(self):
        result = validate(self.value)
        self.assertTrue(result["ok"])
        self.assertEqual(result["wire_type_count"], 9)
        self.assertEqual(result["grid_size_law"], "N_IS_RUNTIME_PARAMETER")
        self.assertEqual(result["supervisor_epoch"], "8.78")
        self.assertEqual(result["runtime_credit"], 0)

    def test_fixed_grid_target_is_rejected(self):
        bad = copy.deepcopy(self.value)
        bad["authority"]["grid_size_law"] = "GRID10_REQUIRED"
        with self.assertRaisesRegex(ABIValidationError, "GRID_SIZE_LAW_MISMATCH"):
            validate(bad)

    def test_model_result_cannot_become_canonical(self):
        bad = copy.deepcopy(self.value)
        bad["wire_types"]["COGNITIVE_RESULT/v1"]["authority"] = "CANONICAL_WRITE"
        with self.assertRaisesRegex(ABIValidationError, "RESULT_AUTHORITY_ESCALATION"):
            validate(bad)

    def test_effect_proposal_cannot_execute_directly(self):
        bad = copy.deepcopy(self.value)
        bad["wire_types"]["EFFECT_PROPOSAL/v1"]["execution_rule"] = "MODEL_MAY_EXECUTE"
        with self.assertRaisesRegex(ABIValidationError, "EFFECT_EXECUTION_RULE_MISMATCH"):
            validate(bad)

    def test_ephemeral_lease_cannot_broaden_capability(self):
        bad = copy.deepcopy(self.value)
        bad["wire_types"]["EPHEMERAL_GRID_LEASE/v1"]["forbidden"].remove("CAPABILITY_BROADENING")
        with self.assertRaisesRegex(ABIValidationError, "LEASE_FORBIDDEN_SET_INCOMPLETE"):
            validate(bad)

    def test_frozen_jspace_v1_negative_evidence_cannot_be_erased(self):
        bad = copy.deepcopy(self.value)
        bad["wire_types"]["JSPACE_SUCCESSOR_CANDIDATE/v1"]["frozen_v1_status"] = "PROMOTABLE"
        with self.assertRaisesRegex(ABIValidationError, "FROZEN_V1_NEGATIVE_EVIDENCE_ERASED"):
            validate(bad)

    def test_jspace_successor_requires_fresh_preregistered_holdout(self):
        bad = copy.deepcopy(self.value)
        bad["wire_types"]["JSPACE_SUCCESSOR_CANDIDATE/v1"]["promotion_rule"] = "RETUNE_ON_EXISTING_HOLDOUT"
        with self.assertRaisesRegex(ABIValidationError, "JSPACE_SUCCESSOR_PROMOTION_RULE_MISMATCH"):
            validate(bad)

    def test_runtime_credit_inflation_is_rejected(self):
        bad = copy.deepcopy(self.value)
        bad["credit"]["distributed_runtime"] = 1
        with self.assertRaisesRegex(ABIValidationError, "CREDIT_INFLATION_DISTRIBUTED_RUNTIME"):
            validate(bad)


if __name__ == "__main__":
    unittest.main()
