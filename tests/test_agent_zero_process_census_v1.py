from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.validate_agent_zero_process_census_v1 import CensusValidationError, validate

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "research_entity/global/AGENT_ZERO_DISTRIBUTED_COGNITIVE_PROCESS_CENSUS_v1.json"


class AgentZeroProcessCensusV1Tests(unittest.TestCase):
    def setUp(self):
        self.value = json.loads(CENSUS.read_text(encoding="utf-8"))

    def test_exact_census_contract_passes(self):
        result = validate(self.value)
        self.assertTrue(result["ok"])
        self.assertEqual(result["process_count"], 20)
        self.assertEqual(result["covered_acceptance_dimensions"], list(range(1, 15)))
        self.assertEqual(result["sole_real_effect_process"], "AZP12")
        self.assertEqual(result["next_owner_gate"], "COGNITIVE_PROCESS_ABI")

    def test_fixed_grid10_target_is_rejected(self):
        bad = copy.deepcopy(self.value)
        bad["authority"]["grid_size_law"] = "GRID10_REQUIRED"
        with self.assertRaisesRegex(CensusValidationError, "GRID_SIZE_LAW_MISMATCH"):
            validate(bad)

    def test_cognitive_process_cannot_gain_real_effect_authority(self):
        bad = copy.deepcopy(self.value)
        bad["processes"][5]["effect_authority"] = "SOLE_REAL_EFFECT_PATH"
        with self.assertRaises(CensusValidationError):
            validate(bad)

    def test_missing_owner_acceptance_dimension_is_rejected(self):
        bad = copy.deepcopy(self.value)
        for process in bad["processes"]:
            process["acceptance_dimensions"] = [x for x in process["acceptance_dimensions"] if x != 13]
        with self.assertRaisesRegex(CensusValidationError, "UNCOVERED_OWNER_DIMENSIONS"):
            validate(bad)

    def test_jspace_cannot_become_unconditional_semantic_process(self):
        bad = copy.deepcopy(self.value)
        jspace = next(p for p in bad["processes"] if p["id"] == "AZP09")
        jspace["layer"] = "AGENT_ZERO_SEMANTIC"
        with self.assertRaisesRegex(CensusValidationError, "JSPACE_MUST_REMAIN_OPTIONAL"):
            validate(bad)

    def test_duplicate_process_identity_is_rejected(self):
        bad = copy.deepcopy(self.value)
        bad["processes"][1]["id"] = bad["processes"][0]["id"]
        with self.assertRaisesRegex(CensusValidationError, "DUPLICATE_PROCESS_ID"):
            validate(bad)


if __name__ == "__main__":
    unittest.main()
