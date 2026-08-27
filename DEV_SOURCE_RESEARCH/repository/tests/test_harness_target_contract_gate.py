import json
import unittest
from pathlib import Path

from tools.harness_target_contract_gate import audit_freeze


OVERLAY_PATH = Path("research_entity/harness/REFERENCE_HARNESS_OWNER_FIXED_TARGET_OVERLAY_20260810.json")


def base_fixture():
    return {
        "target_host": "UBUNTU_LINUX_DEVELOPER_SYSTEM",
        "architecture_semantic_hash": "b92521a77690fcee8e6e247597e091c1478f790d38f780381d899b1200e85a0f",
        "exact_contract_hash": "73450c51d1ca84f63556ba3d8adad3eb663ec848b02384e744af9ebd28421540",
        "modules": [
            {"id": "effect_gateway"},
            {"id": "gwt_workspace"},
            {"id": "semantic_state"},
            {"id": "digital_retina"},
        ],
        "state_contracts": {},
        "mandatory_acceptance_families": ["MVC-E1"],
        "invariants": [
            "model_output_is_not_execution_authority",
            "needle_is_only_intentional_non_clay_semantic_subsystem",
        ],
        "source_records": [],
    }


class GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.overlay = json.loads(OVERLAY_PATH.read_text(encoding="utf-8"))

    def test_legacy_20260809_freeze_is_rejected_without_overlay(self):
        result = audit_freeze(base_fixture())
        self.assertFalse(result["pass"])
        codes = set(result["failure_codes"])
        self.assertIn("TARGET_HOST_STALE", codes)
        self.assertIn("OWNER_FIXED_MODULES_MISSING", codes)
        self.assertIn("OWNER_FIXED_STATE_CONTRACTS_MISSING", codes)
        self.assertIn("OWNER_FIXED_ACCEPTANCE_FAMILIES_MISSING", codes)
        self.assertIn("OWNER_FIXED_INVARIANTS_MISSING", codes)
        self.assertIn("TARGET_IDENTITY_CONTRACT_MISSING_OR_STALE", codes)
        self.assertIn("OWNER_FIXED_SOURCE_BINDINGS_MISSING", codes)

    def test_hash_bound_owner_overlay_closes_contract_gap(self):
        result = audit_freeze(base_fixture(), self.overlay)
        self.assertTrue(result["pass"], result)
        self.assertTrue(result["assembled_with_overlay"])
        self.assertGreaterEqual(result["checked_counts"]["state_contracts"], 12)
        self.assertGreaterEqual(result["checked_counts"]["acceptance_families"], 17)
        self.assertGreaterEqual(result["checked_counts"]["source_bindings"], 5)

    def test_overlay_rejected_when_base_semantic_hash_differs(self):
        base = base_fixture()
        base["architecture_semantic_hash"] = "wrong"
        result = audit_freeze(base, self.overlay)
        self.assertFalse(result["pass"])
        self.assertIn("OVERLAY_BASE_SEMANTIC_HASH_MISMATCH", result["failure_codes"])

    def test_overlay_rejected_when_base_exact_hash_differs(self):
        base = base_fixture()
        base["exact_contract_hash"] = "wrong"
        result = audit_freeze(base, self.overlay)
        self.assertFalse(result["pass"])
        self.assertIn("OVERLAY_BASE_EXACT_HASH_MISMATCH", result["failure_codes"])

    def test_required_source_binding_must_be_hashed(self):
        overlay = json.loads(json.dumps(self.overlay))
        overlay["source_records"][0].pop("git_blob_sha")
        result = audit_freeze(base_fixture(), overlay)
        self.assertFalse(result["pass"])
        self.assertIn("OWNER_FIXED_SOURCE_BINDINGS_UNHASHED", result["failure_codes"])


if __name__ == "__main__":
    unittest.main()
