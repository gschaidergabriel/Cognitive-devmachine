from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools import trigger2_training_artifact_registry_check_v1 as regcheck


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research_entity/claycode/training/TRIGGER2_TRAINING_ARTIFACT_REGISTRY_V1.json"


class Trigger2TrainingArtifactRegistryCheckV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_current_registry_passes(self):
        result = regcheck.validate(copy.deepcopy(self.data))
        self.assertTrue(result["pass"])
        self.assertEqual(10, result["entries"])
        self.assertEqual([], result["training_eligible_entries"])

    def test_v3_quarantine_cannot_be_silently_removed(self):
        bad = copy.deepcopy(self.data)
        entry = next(e for e in bad["entries"] if e["artifact_id"] == "T2-BINDING-ROUTER-V3")
        entry["status"] = "CURRENT_CANDIDATE"
        with self.assertRaisesRegex(AssertionError, "negative evidence regression"):
            regcheck.validate(bad)

    def test_revision_reason_is_mandatory(self):
        bad = copy.deepcopy(self.data)
        bad["entries"][0]["revision_reason"] = ""
        with self.assertRaisesRegex(AssertionError, "missing revision_reason"):
            regcheck.validate(bad)

    def test_lineage_must_be_reciprocal(self):
        bad = copy.deepcopy(self.data)
        source = next(e for e in bad["entries"] if e["artifact_id"] == "T2-QWEN35-CURRICULUM-V1")
        source["successor_ids"] = []
        with self.assertRaisesRegex(AssertionError, "lineage not reciprocal"):
            regcheck.validate(bad)

    def test_noneligible_status_cannot_claim_training_eligibility(self):
        bad = copy.deepcopy(self.data)
        entry = next(e for e in bad["entries"] if e["artifact_id"] == "T2-BINDING-BLUEPRINT-V22")
        entry["training_eligible"] = True
        with self.assertRaisesRegex(AssertionError, "cannot be training_eligible"):
            regcheck.validate(bad)

    def test_registry_cannot_mint_training_credit(self):
        bad = copy.deepcopy(self.data)
        bad["current_training_credit"] = 1
        with self.assertRaisesRegex(AssertionError, "must not mint training credit"):
            regcheck.validate(bad)


if __name__ == "__main__":
    unittest.main()
