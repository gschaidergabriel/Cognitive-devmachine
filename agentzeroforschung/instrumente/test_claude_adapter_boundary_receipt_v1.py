import unittest

from validate_claude_adapter_boundary_receipt_v1 import canonical_sha256, diagnose, validate, ReceiptError

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
        with self.assertRaises(ReceiptError): validate(x)

    def test_clean_fixture_passes(self):
        self.assertTrue(validate(fixture())["ok"])

    def test_placeholder_commit_rejected(self):
        self.assert_reject(lambda x: x["common"].__setitem__("source_commit", "0" * 40))

    def test_dirty_rejected(self):
        self.assert_reject(lambda x: x["common"].__setitem__("dirty", True))

    def test_common_tamper_rejected(self):
        self.assert_reject(lambda x: x["common"].__setitem__("claude_version", "tampered"))

    def test_missing_boundary_rejected(self):
        self.assert_reject(lambda x: x["boundaries"].pop("ephemeral"))

    def test_boundary_cross_run_rejected(self):
        self.assert_reject(lambda x: x["boundaries"]["tool_less"].__setitem__("common_identity_sha256", H64F))

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

    def test_diagnostic_rejects_contradictory_true_promotion_claim_on_fail(self):
        x = fixture()
        x["boundaries"]["tool_less"]["tool_invocation_count"] = 1
        mark_fail(x, "tool_less")
        x["promotion_eligible"] = True
        with self.assertRaisesRegex(ReceiptError, "promotion_eligible contradicts boundary observations"):
            diagnose(x)

    def test_strict_rejects_contradictory_false_promotion_claim_on_pass(self):
        x = fixture()
        x["promotion_eligible"] = False
        with self.assertRaisesRegex(ReceiptError, "promotion_eligible contradicts boundary observations"):
            validate(x)

    def test_explicit_matching_promotion_claims_are_accepted(self):
        clean = fixture()
        clean["promotion_eligible"] = True
        self.assertTrue(validate(clean)["ok"])
        red = fixture()
        red["boundaries"]["ephemeral"]["temporary_home_removed"] = False
        mark_fail(red, "ephemeral")
        red["promotion_eligible"] = False
        result = diagnose(red)
        self.assertFalse(result["promotion_eligible"])

    def test_legacy_missing_promotion_claim_remains_valid(self):
        self.assertTrue(validate(fixture())["ok"])

if __name__ == "__main__":
    unittest.main()
