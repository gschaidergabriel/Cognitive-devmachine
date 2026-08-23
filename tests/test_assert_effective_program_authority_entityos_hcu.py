import contextlib
import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "assert_effective_program_authority.py"
spec = importlib.util.spec_from_file_location("effective_authority_assertion", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class EffectiveAuthorityAssertionTests(unittest.TestCase):
    def _run(self, validator_result):
        out = io.StringIO()
        with mock.patch.object(mod, "validate", return_value=validator_result):
            with contextlib.redirect_stdout(out):
                code = mod.main()
        return code, json.loads(out.getvalue())

    def test_pass_reports_entityos_hcu_only(self):
        code, payload = self._run({"pass": True, "errors": []})
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["program"], "ENTITYOS_HCU")
        self.assertEqual(payload["stage"], "ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP")
        self.assertEqual(payload["product"], "EntityOS")
        self.assertEqual(payload["compute_architecture"], "HCU")
        self.assertEqual(payload["authority_validator"], "ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v1")
        self.assertNotIn("CLAYVERSE_SINGLE_CONTAINER", json.dumps(payload))

    def test_fail_preserves_current_identity_and_errors(self):
        code, payload = self._run({"pass": False, "errors": ["MANIFEST_ARTIFACT_MISMATCH"]})
        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["program"], "ENTITYOS_HCU")
        self.assertEqual(payload["product"], "EntityOS")
        self.assertEqual(payload["compute_architecture"], "HCU")
        self.assertEqual(payload["errors"], ["MANIFEST_ARTIFACT_MISMATCH"])
        self.assertEqual(payload["credit"], "ZERO_RUNTIME_CREDIT")
        self.assertNotIn("CLAYVERSE_SINGLE_CONTAINER", json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
