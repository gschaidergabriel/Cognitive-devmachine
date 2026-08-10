import unittest

from tools.harness_target_contract_gate import audit_freeze


class GateTests(unittest.TestCase):
    def test_legacy_20260809_freeze_is_rejected(self):
        legacy = {
            "target_host": "UBUNTU_LINUX_DEVELOPER_SYSTEM",
            "modules": [
                {"id": "effect_gateway"},
                {"id": "gwt_workspace"},
                {"id": "semantic_state"},
                {"id": "digital_retina"},
            ],
            "invariants": [
                "model_output_is_not_execution_authority",
                "needle_is_only_intentional_non_clay_semantic_subsystem",
            ],
        }
        result = audit_freeze(legacy)
        self.assertFalse(result["pass"])
        codes = {f["code"] for f in result["failures"]}
        self.assertIn("TARGET_HOST_STALE", codes)
        self.assertIn("OWNER_FIXED_MODULES_MISSING", codes)
        self.assertIn("OWNER_FIXED_INVARIANTS_MISSING", codes)

    def test_current_owner_fixed_fixture_passes(self):
        current = {
            "target_host": "TARGET_VPS",
            "modules": [{"id": x} for x in [
                "token_api",
                "de_to_clay_translator",
                "clay_to_de_translator",
                "proactive_agency",
                "web_ingress_guard",
                "research_entity_bridge",
            ]],
            "invariants": [
                "native_identity=self.root",
                "cognition=CLAYCODE_ONLY",
                "body=TARGET_VPS",
                "token API credential not identity",
                "proactive agency persists",
                "open web authority=UNTRUSTED_EXTERNAL_DATA",
            ],
        }
        result = audit_freeze(current)
        self.assertTrue(result["pass"], result)


if __name__ == "__main__":
    unittest.main()
