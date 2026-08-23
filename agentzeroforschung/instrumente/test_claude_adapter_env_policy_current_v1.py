import unittest

from test_claude_adapter_boundary_receipt_v1 import fixture
from validate_claude_adapter_boundary_receipt_v1 import (
    CANONICAL_ENV_ALLOWLIST,
    ReceiptError,
    validate,
)


class TestClaudeAdapterEnvPolicyCurrent(unittest.TestCase):
    def test_canonical_env_matches_current_product_authority_shape(self):
        required = {
            "PATH",
            "HOME",
            "CLAUDE_CONFIG_DIR",
            "TMPDIR",
            "LANG",
            "LC_ALL",
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_AUTH_TOKEN",
            "CLAUDE_CODE_OAUTH_TOKEN",
            "DISABLE_AUTOUPDATER",
            "CLAUDE_CODE_SKIP_PROMPT_HISTORY",
            "CLAUDE_CODE_DISABLE_AUTO_MEMORY",
            "CLAUDE_CODE_DISABLE_CLAUDE_MDS",
        }
        forbidden_ambient_authority = {
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ANTHROPIC_BASE_URL",
            "SSL_CERT_FILE",
            "SSL_CERT_DIR",
            "NODE_EXTRA_CA_CERTS",
            "CLAUDE_CODE_BIN",
        }
        self.assertEqual(CANONICAL_ENV_ALLOWLIST, required)
        self.assertTrue(forbidden_ambient_authority.isdisjoint(CANONICAL_ENV_ALLOWLIST))

    def test_truthful_current_product_env_shape_is_admissible(self):
        x = fixture()
        keys = sorted({
            "PATH",
            "HOME",
            "CLAUDE_CONFIG_DIR",
            "TMPDIR",
            "LANG",
            "CLAUDE_CODE_OAUTH_TOKEN",
            "DISABLE_AUTOUPDATER",
            "CLAUDE_CODE_SKIP_PROMPT_HISTORY",
            "CLAUDE_CODE_DISABLE_AUTO_MEMORY",
            "CLAUDE_CODE_DISABLE_CLAUDE_MDS",
        })
        x["boundaries"]["env_isolation"]["allowed_env_keys"] = keys
        x["boundaries"]["env_isolation"]["observed_child_env_keys"] = keys
        self.assertTrue(validate(x)["ok"])

    def test_removed_route_authority_cannot_be_self_authorized(self):
        for poison in (
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ANTHROPIC_BASE_URL",
            "SSL_CERT_FILE",
            "SSL_CERT_DIR",
            "NODE_EXTRA_CA_CERTS",
        ):
            with self.subTest(poison=poison):
                x = fixture()
                keys = ["HOME", "PATH", poison]
                x["boundaries"]["env_isolation"]["allowed_env_keys"] = keys
                x["boundaries"]["env_isolation"]["observed_child_env_keys"] = keys
                with self.assertRaisesRegex(ReceiptError, "exceed canonical Claude child policy"):
                    validate(x)


if __name__ == "__main__":
    unittest.main()
