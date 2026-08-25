from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.validate_agent_zero_process_census_v1 import CensusValidationError, validate

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research_entity/global/AGENT_ZERO_DISTRIBUTED_COGNITIVE_PROCESS_CENSUS_v1.json"
OVERLAY = ROOT / "research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_CURRENT_OWNER_OVERLAY_v1.json"


class ZeroEntityOSCognitiveProcessCensusV1Tests(unittest.TestCase):
    def setUp(self):
        self.base = json.loads(BASE.read_text(encoding="utf-8"))
        self.overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))

    def test_current_composite_census_contract_passes(self):
        result = validate(self.base, self.overlay)
        self.assertTrue(result["ok"])
        self.assertEqual(result["schema"], "ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS/v1")
        self.assertEqual(result["process_count"], 22)
        self.assertEqual(result["covered_functional_dimensions"], list(range(1, 15)))
        self.assertEqual(result["covered_current_owner_acceptance"], list(range(1, 11)))
        self.assertEqual(result["sole_real_effect_process"], "AZP12")
        self.assertEqual(result["database_boundary_process"], "AZP21")
        self.assertEqual(result["claude_code_bridge_process"], "AZP22")
        self.assertEqual(result["next_owner_gate"], "COGNITIVE_PROCESS_ABI")

    def test_stale_owner_commit_is_rejected_as_current_authority(self):
        bad = copy.deepcopy(self.overlay)
        bad["authority"]["owner_target_commit"] = "72bc01e5562391528cd3a91c2851f77ad33ebf00"
        with self.assertRaisesRegex(CensusValidationError, "OWNER_COMMIT_MISMATCH"):
            validate(self.base, bad)

    def test_fixed_grid10_target_is_rejected(self):
        bad = copy.deepcopy(self.overlay)
        bad["authority"]["grid_size_law"] = "GRID10_REQUIRED"
        with self.assertRaisesRegex(CensusValidationError, "GRID_SIZE_LAW_MISMATCH"):
            validate(self.base, bad)

    def test_db_boundary_cannot_be_removed_from_owner_acceptance(self):
        bad = copy.deepcopy(self.overlay)
        bad["current_owner_acceptance"]["3"]["process_ids"].remove("AZP21")
        with self.assertRaisesRegex(CensusValidationError, "OWNER_ACCEPTANCE_3_REQUIRES_DB_BOUNDARY"):
            validate(self.base, bad)

    def test_claude_bridge_cannot_claim_hidden_state_authority(self):
        bad = copy.deepcopy(self.overlay)
        bridge = next(p for p in bad["delta_processes"] if p["id"] == "AZP22")
        bridge["distribution"] = "CLAUDE_ACTIVATION_SPACE_DIRECT_AUTHORITY"
        with self.assertRaisesRegex(CensusValidationError, "CLAUDE_BRIDGE_MUST_DENY_HIDDEN_STATE_AUTHORITY"):
            validate(self.base, bad)

    def test_delta_cannot_create_second_real_effect_path(self):
        bad = copy.deepcopy(self.overlay)
        db = next(p for p in bad["delta_processes"] if p["id"] == "AZP21")
        db["effect_authority"] = "SOLE_REAL_EFFECT_PATH"
        with self.assertRaisesRegex(CensusValidationError, "DELTA_CANNOT_CREATE_SECOND_REAL_EFFECT_PATH"):
            validate(self.base, bad)

    def test_jspace_base_process_remains_optional(self):
        bad_base = copy.deepcopy(self.base)
        jspace = next(p for p in bad_base["processes"] if p["id"] == "AZP09")
        jspace["layer"] = "AGENT_ZERO_SEMANTIC"
        with self.assertRaisesRegex(CensusValidationError, "JSPACE_MUST_REMAIN_OPTIONAL"):
            validate(bad_base, self.overlay)

    def test_frozen_v1_negative_evidence_cannot_be_promoted(self):
        bad = copy.deepcopy(self.overlay)
        bad["negative_evidence"]["promotion_credit"] = 1
        with self.assertRaisesRegex(CensusValidationError, "MUST_NOT_MINT_PROMOTION_CREDIT"):
            validate(self.base, bad)

    def test_duplicate_base_process_identity_is_rejected(self):
        bad_base = copy.deepcopy(self.base)
        bad_base["processes"][1]["id"] = bad_base["processes"][0]["id"]
        with self.assertRaises(CensusValidationError):
            validate(bad_base, self.overlay)


if __name__ == "__main__":
    unittest.main()
