import unittest

from test_claude_adapter_boundary_receipt_v1 import fixture
from validate_claude_adapter_boundary_receipt_v1 import (
    CANONICAL_ENV_ALLOWLIST,
    ReceiptError,
    validate,
)


class TestClaudeAdapterEnvPolicySync(unittest.TestCase):
    def test_adapter_defense_env_keys_are_canonical(self):
        self.assertIn("CLAUDE_CODE_DISABLE_AUTO_MEMORY", CANONICAL_ENV_ALLOWLIST)
        self.assertIn("CLAUDE_CODE_DISABLE_CLAUDE_MDS", CANONICAL_ENV_ALLOWLIST)

    def test_truthful_adapter_defense_env_receipt_passes(self):
        x = fixture()
        keys = [
            "HOME",
            "PATH",
            "CLAUDE_CODE_DISABLE_AUTO_MEMORY",
            "CLAUDE_CODE_DISABLE_CLAUDE_MDS",
        ]
        x["boundaries"]["env_isolation"]["allowed_env_keys"] = keys
        x["boundaries"]["env_isolation"]["observed_child_env_keys"] = keys
        self.assertTrue(validate(x)["ok"])

    def test_unrelated_secret_stays_forbidden(self):
        x = fixture()
        keys = ["HOME", "PATH", "AWS_SECRET_ACCESS_KEY"]
        x["boundaries"]["env_isolation"]["allowed_env_keys"] = keys
        x["boundaries"]["env_isolation"]["observed_child_env_keys"] = keys
        with self.assertRaisesRegex(ReceiptError, "exceed canonical Claude child policy"):
            validate(x)


if __name__ == "__main__":
    unittest.main()
