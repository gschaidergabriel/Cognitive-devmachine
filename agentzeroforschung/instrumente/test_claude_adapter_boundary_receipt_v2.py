import unittest

from validate_claude_adapter_boundary_receipt_v2 import ReceiptError, canonical_sha256, diagnose, validate

H40A = "1234567890abcdef1234567890abcdef12345678"
H40B = "abcdef1234567890abcdef1234567890abcdef12"
H64A = "12" * 32
H64B = "34" * 32
H64C = "56" * 32
H64D = "78" * 32
H64E = "9a" * 32
H64F = "bc" * 32
H64G = "de" * 32


def fixture():
    common = {
        "source_commit": H40A,
        "source_tree": H40B,
        "dirty": False,
        "claude_binary_sha256": H64A,
        "claude_version": "2.1.233-test",
        "command_sha256": H64B,
        "input_sha256": H64C,
        "executor": {"os": "ubuntu", "arch": "x86_64", "runtime": "python3.13"},
        "started_at": "2026-08-23T03:35:00Z",
        "finished_at": "2026-08-23T03:35:01Z",
    }
    cid = canonical_sha256(common)
    base = {"common_identity_sha256": cid, "measured": True, "status": "PASS", "stdout_sha256": H64D, "stderr_sha256": H64E}
    boundaries = {
        "tool_less": {**base, "schema": "TOOL_LESS_RECEIPT/v2", "built_in_tools_enabled": False, "bash_enabled": False, "mcp_servers": [], "tool_invocation_count": 0},
        "ephemeral": {**base, "schema": "EPHEMERAL_RECEIPT/v2", "persistent_session_reused": False, "no_session_persistence_requested": True, "prompt_history_suppressed": True, "auto_memory_disabled": True, "claude_mds_disabled": True, "auth_home_retained": True, "home_identity_sha256": H64F, "persistence_measurement_complete": True, "persistence_scope_schema": "CLAUDE_USER_PERSISTENCE_SURFACE/v1", "persistence_scope_kinds": ["auto_memory", "prompt_history", "transcripts"], "persistence_before_sha256": H64G, "persistence_after_sha256": H64G, "transcript_write_count": 0, "prompt_history_write_count": 0, "auto_memory_write_count": 0},
        "structured_output": {**base, "schema": "STRUCTURED_OUTPUT_RECEIPT/v2", "parse_ok": True, "candidate_only": True, "canonical_write_attempted": False, "result_sha256": H64F, "result_schema": "InferenceCandidate/v1"},
        "env_isolation": {**base, "schema": "ENV_ISOLATION_RECEIPT/v2", "allowed_env_keys": ["HOME", "PATH", "CLAUDE_CODE_SKIP_PROMPT_HISTORY", "CLAUDE_CODE_DISABLE_AUTO_MEMORY", "CLAUDE_CODE_DISABLE_CLAUDE_MDS"], "observed_child_env_keys": ["HOME", "PATH", "CLAUDE_CODE_SKIP_PROMPT_HISTORY", "CLAUDE_CODE_DISABLE_AUTO_MEMORY", "CLAUDE_CODE_DISABLE_CLAUDE_MDS"], "forbidden_key_count": 0, "secret_value_leak_count": 0, "environment_shape_sha256": H64F},
    }
    return {"schema": "CLAUDE_ADAPTER_BOUNDARY_RECEIPT/v2", "common": common, "common_identity_sha256": cid, "boundaries": boundaries, "aggregate_status": "PASS", "runtime_credit": "CLAUDE_ADAPTER_BOUNDARY_ONLY", "whole_product_credit": 0}


def mark_fail(x, name):
    x["boundaries"][name]["status"] = "FAIL"
    x["aggregate_status"] = "FAIL"
    x["runtime_credit"] = "ZERO"


class TestReceiptV2(unittest.TestCase):
    def assert_reject(self, mutate):
        x = fixture(); mutate(x)
        with self.assertRaises(ReceiptError):
            validate(x)

    def test_clean_fixture_passes(self): self.assertTrue(validate(fixture())["ok"])
    def test_v1_not_reinterpreted(self): self.assert_reject(lambda x: x.__setitem__("schema", "CLAUDE_ADAPTER_BOUNDARY_RECEIPT/v1"))
    def test_placeholder_commit_rejected(self): self.assert_reject(lambda x: x["common"].__setitem__("source_commit", "0" * 40))
    def test_dirty_rejected(self): self.assert_reject(lambda x: x["common"].__setitem__("dirty", True))
    def test_common_tamper_rejected(self): self.assert_reject(lambda x: x["common"].__setitem__("claude_version", "tampered"))
    def test_invalid_timestamp_rejected(self): self.assert_reject(lambda x: x["common"].__setitem__("started_at", "not-a-timestamp"))

    def test_temporal_inversion_rejected(self):
        def mutate(x):
            x["common"]["started_at"] = "2026-08-23T03:35:01Z"; x["common"]["finished_at"] = "2026-08-23T03:35:00Z"
            cid = canonical_sha256(x["common"]); x["common_identity_sha256"] = cid
            for boundary in x["boundaries"].values(): boundary["common_identity_sha256"] = cid
        self.assert_reject(mutate)

    def test_missing_boundary_rejected(self): self.assert_reject(lambda x: x["boundaries"].pop("ephemeral"))
    def test_boundary_cross_run_rejected(self): self.assert_reject(lambda x: x["boundaries"]["tool_less"].__setitem__("common_identity_sha256", H64F))

    def test_cross_boundary_stdout_mismatch_rejected(self):
        x = fixture(); x["boundaries"]["structured_output"]["stdout_sha256"] = H64F
        with self.assertRaisesRegex(ReceiptError, "boundary stdout_sha256 mismatch"): diagnose(x)

    def test_cross_boundary_stderr_mismatch_rejected(self):
        x = fixture(); x["boundaries"]["env_isolation"]["stderr_sha256"] = H64F
        with self.assertRaisesRegex(ReceiptError, "boundary stderr_sha256 mismatch"): diagnose(x)

    def test_unmeasured_rejected(self): self.assert_reject(lambda x: x["boundaries"]["tool_less"].__setitem__("measured", False))
    def test_tool_invocation_rejected(self): self.assert_reject(lambda x: x["boundaries"]["tool_less"].__setitem__("tool_invocation_count", 1))
    def test_persistent_session_reuse_rejected(self): self.assert_reject(lambda x: x["boundaries"]["ephemeral"].__setitem__("persistent_session_reused", True))
    def test_no_session_flag_required(self): self.assert_reject(lambda x: x["boundaries"]["ephemeral"].__setitem__("no_session_persistence_requested", False))
    def test_prompt_history_guard_required(self): self.assert_reject(lambda x: x["boundaries"]["ephemeral"].__setitem__("prompt_history_suppressed", False))
    def test_auto_memory_guard_required(self): self.assert_reject(lambda x: x["boundaries"]["ephemeral"].__setitem__("auto_memory_disabled", False))
    def test_claude_mds_guard_required(self): self.assert_reject(lambda x: x["boundaries"]["ephemeral"].__setitem__("claude_mds_disabled", False))
    def test_retained_auth_home_required(self): self.assert_reject(lambda x: x["boundaries"]["ephemeral"].__setitem__("auth_home_retained", False))
    def test_measurement_complete_required(self): self.assert_reject(lambda x: x["boundaries"]["ephemeral"].__setitem__("persistence_measurement_complete", False))
    def test_scope_complete_required(self): self.assert_reject(lambda x: x["boundaries"]["ephemeral"].__setitem__("persistence_scope_kinds", ["transcripts"]))
    def test_surface_change_rejected(self): self.assert_reject(lambda x: x["boundaries"]["ephemeral"].__setitem__("persistence_after_sha256", H64A))
    def test_transcript_write_rejected(self): self.assert_reject(lambda x: x["boundaries"]["ephemeral"].__setitem__("transcript_write_count", 1))
    def test_prompt_history_write_rejected(self): self.assert_reject(lambda x: x["boundaries"]["ephemeral"].__setitem__("prompt_history_write_count", 1))
    def test_auto_memory_write_rejected(self): self.assert_reject(lambda x: x["boundaries"]["ephemeral"].__setitem__("auto_memory_write_count", 1))
    def test_canonical_write_attempt_rejected(self): self.assert_reject(lambda x: x["boundaries"]["structured_output"].__setitem__("canonical_write_attempted", True))
    def test_non_candidate_rejected(self): self.assert_reject(lambda x: x["boundaries"]["structured_output"].__setitem__("candidate_only", False))
    def test_extra_env_key_rejected(self): self.assert_reject(lambda x: x["boundaries"]["env_isolation"].__setitem__("observed_child_env_keys", ["HOME", "AWS_SECRET_ACCESS_KEY"]))
    def test_receipt_cannot_self_authorize_env_key(self): self.assert_reject(lambda x: (x["boundaries"]["env_isolation"].__setitem__("allowed_env_keys", ["HOME", "PATH", "AWS_SECRET_ACCESS_KEY"]), x["boundaries"]["env_isolation"].__setitem__("observed_child_env_keys", ["HOME", "PATH", "AWS_SECRET_ACCESS_KEY"])))
    def test_secret_leak_rejected(self): self.assert_reject(lambda x: x["boundaries"]["env_isolation"].__setitem__("secret_value_leak_count", 1))
    def test_whole_product_credit_rejected(self): self.assert_reject(lambda x: x.__setitem__("whole_product_credit", 1))

    def test_diagnostic_preserves_one_red_and_three_green(self):
        x = fixture(); x["boundaries"]["ephemeral"]["auto_memory_write_count"] = 1; mark_fail(x, "ephemeral")
        result = diagnose(x)
        self.assertEqual(result["aggregate_status"], "FAIL"); self.assertFalse(result["promotion_eligible"])
        self.assertEqual(result["failing_boundaries"], ["ephemeral"])
        self.assertEqual(result["violations"]["ephemeral"], ["AUTO_MEMORY_WRITE_OBSERVED"])
        self.assertEqual(result["violations"]["tool_less"], []); self.assertEqual(result["violations"]["structured_output"], []); self.assertEqual(result["violations"]["env_isolation"], [])

    def test_strict_validator_rejects_diagnostic_red(self):
        x = fixture(); x["boundaries"]["ephemeral"]["persistence_after_sha256"] = H64A; mark_fail(x, "ephemeral")
        with self.assertRaisesRegex(ReceiptError, "aggregate_status must be PASS"): validate(x)

    def test_diagnostic_rejects_false_reported_pass(self):
        x = fixture(); x["boundaries"]["ephemeral"]["transcript_write_count"] = 1
        with self.assertRaisesRegex(ReceiptError, "status does not match measured observations"): diagnose(x)

    def test_diagnostic_multiple_failures_retained(self):
        x = fixture(); x["boundaries"]["tool_less"]["bash_enabled"] = True; x["boundaries"]["ephemeral"]["prompt_history_write_count"] = 1
        x["boundaries"]["tool_less"]["status"] = "FAIL"; x["boundaries"]["ephemeral"]["status"] = "FAIL"; x["aggregate_status"] = "FAIL"; x["runtime_credit"] = "ZERO"
        result = diagnose(x)
        self.assertEqual(result["failing_boundaries"], ["tool_less", "ephemeral"])
        self.assertEqual(result["violations"]["tool_less"], ["BASH_ENABLED"])
        self.assertEqual(result["violations"]["ephemeral"], ["PROMPT_HISTORY_WRITE_OBSERVED"])


if __name__ == "__main__":
    unittest.main()
