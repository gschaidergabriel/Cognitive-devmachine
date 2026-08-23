import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "assert_effective_program_authority.py"
spec = importlib.util.spec_from_file_location("effective_authority_assertion", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class EffectiveAuthorityAssertionTests(unittest.TestCase):
    def test_pass_payload_reports_current_entityos_hcu_authority(self):
        payload = mod.assertion_payload({"pass": True, "errors": []})
        self.assertEqual(payload["schema"], "EFFECTIVE_PROGRAM_AUTHORITY_ASSERTION/v3")
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["program"], "ENTITYOS_HCU")
        self.assertEqual(payload["stage"], "ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP")
        self.assertEqual(payload["product"], "EntityOS")
        self.assertEqual(payload["compute_architecture"], "HCU")
        self.assertEqual(payload["authority_validator"], "ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v1")
        self.assertEqual(payload["credit"], "SOURCE_CONTROL_ASSERTION_ONLY_ZERO_RUNTIME_CREDIT")

    def test_fail_payload_stays_current_but_grants_no_credit(self):
        payload = mod.assertion_payload({"pass": False, "errors": ["SENTINEL"]})
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["program"], "ENTITYOS_HCU")
        self.assertEqual(payload["product"], "EntityOS")
        self.assertEqual(payload["compute_architecture"], "HCU")
        self.assertEqual(payload["errors"], ["SENTINEL"])
        self.assertEqual(payload["credit"], "ZERO_RUNTIME_CREDIT")

    def test_historical_clayverse_labels_are_not_emitted(self):
        payload = mod.assertion_payload({"pass": True, "errors": []})
        rendered = repr(payload)
        self.assertNotIn("CLAYVERSE_SINGLE_CONTAINER", rendered)
        self.assertNotIn("CLAYVERSE_ARTIFACT", rendered)


if __name__ == "__main__":
    unittest.main()
