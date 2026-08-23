import unittest

from validate_claude_adapter_boundary_receipt_v1 import (
    CANONICAL_ENV_ALLOWLIST,
    ReceiptError,
    canonical_sha256,
    diagnose,
    validate,
)

H40A = "1234567890abcdef1234567890abcdef12345678"
H40B = "abcdef1234567890abcdef1234567890abcdef12"
H64A = "12" * 32
H64B = "34" * 32
H64C = "56" * 32
H64D = "78" * 32
H64E = "9a" * 32
H64F = "bc" * 32


def fixture():
    common = {
        "source_commit": H40A,
        "source_tree": H40B,
        "dirty": False,
        "claude_binary_sha256": H64A,
        "claude_version": "2.1.0-test",
        "command_sha256": H64B,
        "input_sha256": H64C,
        "invocation_id": "claude-adapter-run-0001",
        "executor": {"os": "ubuntu", "arch": "x86_64", "runtime": "python3.13"},
        "started_at": "2026-08-23T03:16:00Z",
        "finished_at": "2026-08-23T03:16:01Z",
    }
    cid = canonical_sha256(common)
    base = {"common_identity_sha256": cid, "measured": True, "status": "PASS", "stdout_sha256": H64D, "stderr_sha256": H64E}
    boundaries = {
        "tool_less": {**base, "schema": "TOOL_LESS_RECEIPT/v1", "built_in_tools_enabled": False, "bash_enabled": False, "mcp_servers": [], "tool_invocation_count": 0},
        "ephemeral": {**base, "schema": "EPHEMERAL_RECEIPT/v1", "persistent_session_reused": False, "prompt_history_written": False, "auto_memory_written": False, "temporary_home_created": True, "temporary_home_removed": True},
        "structured_output": {**base, "schema": "STRUCTURED_OUTPUT_RECEIPT/v1", "parse_ok": True, "candidate_only": True, "canonical_write_attempted": False, "result_sha256": H64F, "result_schema": "InferenceCandidate/v1"},
        "env_isolation": {**base, "schema": "ENV_ISOLATION_RECEIPT/v1", "allowed_env_keys": ["HOME", "PATH", "LANG"], "observed_child_env_keys": ["HOME", "PATH"], "forbidden_key_count": 0, "secret_value_leak_count": 0, "environment_shape_sha256": H64F},
    }
    return {"schema": "CLAUDE_ADAPTER_BOUNDARY_RECEIPT/v1", "common": common, "common_identity_sha256": cid, "boundaries": boundaries, "aggregate_status": "PASS", "runtime_credit": "CLAUDE_ADAPTER_BOUNDARY_ONLY", "whole_product_credit": 0}

def mark_fail(x, name):
    x["boundaries"][name]["status"] = "FAIL"
    x["aggregate_status"] = "FAIL"
    x["runtime_credit"] = "ZERO"

class TestReceipt(unittest.TestCase):
    def assert_reject(self, mutate):
        x = fixture(); mutate(x)
        with self.assertRaises(ReceiptError):
            validate(x)

    def test_clean_fixture_passes(self):
        self.assertTrue(validate(fixture())["ok"])

    def test_placeholder_commit_rejected(self):
        self.assert_reject(lambda x: x["common"].__setitem__("source_commit", "0" * 40))

    def test_dirty_rejected(self):
        self.assert_reject(lambda x: x["common"].__setitem__("dirty", True))

    def test_common_tamper_rejected(self):
        self.assert_reject(lambda x: x["common"].__setitem__("claude_version", "tampered"))

    def test_missing_invocation_id_rejected(self):
        self.assert_reject(lambda x: x["common"].pop("invocation_id"))

    def test_short_invocation_id_rejected(self):
        self.assert_reject(lambda x: x["common"].__setitem__("invocation_id", "short"))

    def test_invalid_timestamp_rejected(self):
        self.assert_reject(lambda x: x["common"].__setitem__("started_at", "not-a-timestamp"))

    def test_temporal_inversion_rejected(self):
        def mutate(x):
            x["common"]["started_at"] = "2026-08-23T03:16:01Z"
            x["common"]["finished_at"] = "2026-08-23T03:16:00Z"
            cid = canonical_sha256(x["common"])
            x["common_identity_sha256"] = cid
            for boundary in x["boundaries"].values():
                boundary["common_identity_sha256"] = cid
        self.assert_reject(mutate)

    def test_missing_boundary_rejected(self):
        self.assert_reject(lambda x: x["boundaries"].pop("ephemeral"))

    def test_boundary_cross_run_rejected(self):
        self.assert_reject(lambda x: x["boundaries"]["tool_less"].__setitem__("common_identity_sha256", H64F))

    def test_cross_boundary_stdout_mismatch_rejected(self):
        x = fixture()
        x["boundaries"]["structured_output"]["stdout_sha256"] = H64F
        with self.assertRaisesRegex(ReceiptError, "boundary stdout_sha256 mismatch"):
            diagnose(x)

    def test_cross_boundary_stderr_mismatch_rejected(self):
        x = fixture()
        x["boundaries"]["env_isolation"]["stderr_sha256"] = H64F
        with self.assertRaisesRegex(ReceiptError, "boundary stderr_sha256 mismatch"):
            diagnose(x)

    def test_unmeasured_rejected(self):
        self.assert_reject(lambda x: x["boundaries"]["tool_less"].__setitem__("measured", False))

    def test_tool_invocation_rejected(self):
        self.assert_reject(lambda x: x["boundaries"]["tool_less"].__setitem__("tool_invocation_count", 1))

    def test_persistent_session_reuse_rejected(self):
        self.assert_reject(lambda x: x["boundaries"]["ephemeral"].__setitem__("persistent_session_reused", True))

    def test_temp_home_leak_rejected(self):
        self.assert_reject(lambda x: x["boundaries"]["ephemeral"].__setitem__("temporary_home_removed", False))

    def test_canonical_write_attempt_rejected(self):
        self.assert_reject(lambda x: x["boundaries"]["structured_output"].__setitem__("canonical_write_attempted", True))

    def test_non_candidate_rejected(self):
        self.assert_reject(lambda x: x["boundaries"]["structured_output"].__setitem__("candidate_only", False))

    def test_extra_env_key_rejected(self):
        self.assert_reject(lambda x: x["boundaries"]["env_isolation"].__setitem__("observed_child_env_keys", ["HOME", "AWS_SECRET_ACCESS_KEY"]))

    def test_receipt_cannot_self_authorize_forbidden_env_key(self):
        self.assert_reject(lambda x: (
            x["boundaries"]["env_isolation"].__setitem__("allowed_env_keys", ["HOME", "PATH", "AWS_SECRET_ACCESS_KEY"]),
            x["boundaries"]["env_isolation"].__setitem__("observed_child_env_keys", ["HOME", "PATH", "AWS_SECRET_ACCESS_KEY"]),
        ))

    def test_route_endpoint_and_trust_keys_are_not_canonical(self):
        forbidden = (
            "HTTP_PROXY", "HTTPS_PROXY", "ANTHROPIC_BASE_URL",
            "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS",
        )
        for key in forbidden:
            with self.subTest(key=key):
                self.assertNotIn(key, CANONICAL_ENV_ALLOWLIST)
                self.assert_reject(lambda x, key=key: (
                    x["boundaries"]["env_isolation"].__setitem__("allowed_env_keys", ["HOME", "PATH", key]),
                    x["boundaries"]["env_isolation"].__setitem__("observed_child_env_keys", ["HOME", "PATH", key]),
                ))

    def test_current_ephemeral_and_memory_fence_keys_are_canonical(self):
        required = {
            "PATH", "HOME", "TMPDIR", "CLAUDE_CONFIG_DIR",
            "DISABLE_AUTOUPDATER", "CLAUDE_CODE_SKIP_PROMPT_HISTORY",
            "CLAUDE_CODE_DISABLE_AUTO_MEMORY", "CLAUDE_CODE_DISABLE_CLAUDE_MDS",
        }
        self.assertTrue(required.issubset(CANONICAL_ENV_ALLOWLIST))
        x = fixture()
        keys = sorted(required)
        x["boundaries"]["env_isolation"]["allowed_env_keys"] = keys
        x["boundaries"]["env_isolation"]["observed_child_env_keys"] = keys
        self.assertTrue(validate(x)["ok"])

    def test_secret_leak_rejected(self):
        self.assert_reject(lambda x: x["boundaries"]["env_isolation"].__setitem__("secret_value_leak_count", 1))

    def test_whole_product_credit_rejected(self):
        self.assert_reject(lambda x: x.__setitem__("whole_product_credit", 1))

    def test_diagnostic_preserves_one_red_and_three_green(self):
        x = fixture()
        x["boundaries"]["tool_less"]["tool_invocation_count"] = 1
        mark_fail(x, "tool_less")
        result = diagnose(x)
        self.assertEqual(result["aggregate_status"], "FAIL")
        self.assertFalse(result["promotion_eligible"])
        self.assertEqual(result["failing_boundaries"], ["tool_less"])
        self.assertEqual(result["violations"]["tool_less"], ["TOOL_INVOCATION_OBSERVED"])
        self.assertEqual(result["violations"]["ephemeral"], [])
        self.assertEqual(result["violations"]["structured_output"], [])
        self.assertEqual(result["violations"]["env_isolation"], [])

    def test_strict_validator_still_rejects_diagnostic_red(self):
        x = fixture()
        x["boundaries"]["ephemeral"]["temporary_home_removed"] = False
        mark_fail(x, "ephemeral")
        with self.assertRaisesRegex(ReceiptError, "aggregate_status must be PASS"):
            validate(x)

    def test_diagnostic_rejects_false_reported_pass(self):
        x = fixture()
        x["boundaries"]["env_isolation"]["secret_value_leak_count"] = 1
        with self.assertRaisesRegex(ReceiptError, "status does not match measured observations"):
            diagnose(x)

    def test_diagnostic_multiple_failures_are_retained(self):
        x = fixture()
        x["boundaries"]["tool_less"]["bash_enabled"] = True
        x["boundaries"]["structured_output"]["canonical_write_attempted"] = True
        x["boundaries"]["tool_less"]["status"] = "FAIL"
        x["boundaries"]["structured_output"]["status"] = "FAIL"
        x["aggregate_status"] = "FAIL"
        x["runtime_credit"] = "ZERO"
        result = diagnose(x)
        self.assertEqual(result["failing_boundaries"], ["tool_less", "structured_output"])
        self.assertEqual(result["violations"]["tool_less"], ["BASH_ENABLED"])
        self.assertEqual(result["violations"]["structured_output"], ["CANONICAL_WRITE_ATTEMPTED"])

if __name__ == "__main__":
    unittest.main()
