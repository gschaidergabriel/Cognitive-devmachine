import unittest

from validate_claude_adapter_boundary_receipt_v2 import (
    ReceiptError,
    canonical_sha256,
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
H64G = "de" * 32


def fixture():
    common = {
        "source_commit": H40A,
        "source_tree": H40B,
        "dirty": False,
        "claude_binary_sha256": H64A,
        "claude_version": "2.1.250-test",
        "command_sha256": H64B,
        "input_sha256": H64C,
        "executor": {"os": "ubuntu", "arch": "x86_64", "runtime": "python3.13"},
        "started_at": "2026-08-23T03:27:00Z",
        "finished_at": "2026-08-23T03:27:01Z",
    }
    cid = canonical_sha256(common)
    base = {
        "common_identity_sha256": cid,
        "measured": True,
        "status": "PASS",
        "stdout_sha256": H64D,
        "stderr_sha256": H64E,
    }
    boundaries = {
        "tool_less": {
            **base,
            "schema": "TOOL_LESS_RECEIPT/v2",
            "built_in_tools_enabled": False,
            "bash_enabled": False,
            "mcp_servers": [],
            "tool_invocation_count": 0,
        },
        "ephemeral": {
            **base,
            "schema": "EPHEMERAL_RECEIPT/v2",
            "persistent_session_reused": False,
            "no_session_persistence_requested": True,
            "prompt_history_suppressed": True,
            "auto_memory_disabled": True,
            "setting_sources": [],
            "auth_home_retained": True,
            "home_identity_sha256": H64F,
            "persistence_measurement_complete": True,
            "persistence_scope_schema": "CLAUDE_USER_PERSISTENCE_SURFACE/v1",
            "persistence_scope_kinds": ["auto_memory", "prompt_history", "transcripts"],
            "persistence_before_sha256": H64G,
            "persistence_after_sha256": H64G,
            "transcript_write_count": 0,
            "prompt_history_write_count": 0,
            "auto_memory_write_count": 0,
        },
        "structured_output": {
            **base,
            "schema": "STRUCTURED_OUTPUT_RECEIPT/v2",
            "parse_ok": True,
            "candidate_only": True,
            "canonical_write_attempted": False,
            "result_sha256": H64F,
            "result_schema": "InferenceCandidate/v1",
        },
        "env_isolation": {
            **base,
            "schema": "ENV_ISOLATION_RECEIPT/v2",
            "allowed_env_keys": [
                "HOME",
                "PATH",
                "CLAUDE_CODE_SKIP_PROMPT_HISTORY",
                "CLAUDE_CODE_DISABLE_AUTO_MEMORY",
                "DISABLE_AUTOUPDATER",
            ],
            "observed_child_env_keys": [
                "HOME",
                "PATH",
                "CLAUDE_CODE_SKIP_PROMPT_HISTORY",
                "CLAUDE_CODE_DISABLE_AUTO_MEMORY",
                "DISABLE_AUTOUPDATER",
            ],
            "forbidden_key_count": 0,
            "secret_value_leak_count": 0,
            "environment_shape_sha256": H64F,
        },
    }
    return {
        "schema": "CLAUDE_ADAPTER_BOUNDARY_RECEIPT/v2",
        "common": common,
        "common_identity_sha256": cid,
        "boundaries": boundaries,
        "aggregate_status": "PASS",
        "runtime_credit": "CLAUDE_ADAPTER_BOUNDARY_ONLY",
        "whole_product_credit": 0,
    }


class TestReceiptV2(unittest.TestCase):
    def assert_reject(self, mutate):
        doc = fixture()
        mutate(doc)
        with self.assertRaises(ReceiptError):
            validate(doc)

    def test_clean_retained_auth_fixture_passes(self):
        self.assertTrue(validate(fixture())["ok"])

    def test_v1_schema_is_not_silently_reinterpreted(self):
        self.assert_reject(
            lambda doc: doc.__setitem__("schema", "CLAUDE_ADAPTER_BOUNDARY_RECEIPT/v1")
        )

    def test_dirty_source_rejected(self):
        self.assert_reject(lambda doc: doc["common"].__setitem__("dirty", True))

    def test_cross_run_boundary_rejected(self):
        self.assert_reject(
            lambda doc: doc["boundaries"]["ephemeral"].__setitem__(
                "common_identity_sha256", H64A
            )
        )

    def test_auto_memory_must_be_disabled(self):
        self.assert_reject(
            lambda doc: doc["boundaries"]["ephemeral"].__setitem__(
                "auto_memory_disabled", False
            )
        )

    def test_prompt_history_must_be_suppressed(self):
        self.assert_reject(
            lambda doc: doc["boundaries"]["ephemeral"].__setitem__(
                "prompt_history_suppressed", False
            )
        )

    def test_no_session_persistence_flag_must_be_measured(self):
        self.assert_reject(
            lambda doc: doc["boundaries"]["ephemeral"].__setitem__(
                "no_session_persistence_requested", False
            )
        )

    def test_user_setting_source_rejected(self):
        self.assert_reject(
            lambda doc: doc["boundaries"]["ephemeral"].__setitem__(
                "setting_sources", ["user"]
            )
        )

    def test_retained_auth_home_is_explicit(self):
        self.assert_reject(
            lambda doc: doc["boundaries"]["ephemeral"].__setitem__(
                "auth_home_retained", False
            )
        )

    def test_persistence_measurement_must_be_complete(self):
        self.assert_reject(
            lambda doc: doc["boundaries"]["ephemeral"].__setitem__(
                "persistence_measurement_complete", False
            )
        )

    def test_persistence_scope_must_cover_all_three_kinds(self):
        self.assert_reject(
            lambda doc: doc["boundaries"]["ephemeral"].__setitem__(
                "persistence_scope_kinds", ["transcripts"]
            )
        )

    def test_changed_persistence_surface_rejected(self):
        self.assert_reject(
            lambda doc: doc["boundaries"]["ephemeral"].__setitem__(
                "persistence_after_sha256", H64A
            )
        )

    def test_transcript_write_rejected(self):
        self.assert_reject(
            lambda doc: doc["boundaries"]["ephemeral"].__setitem__(
                "transcript_write_count", 1
            )
        )

    def test_prompt_history_write_rejected(self):
        self.assert_reject(
            lambda doc: doc["boundaries"]["ephemeral"].__setitem__(
                "prompt_history_write_count", 1
            )
        )

    def test_auto_memory_write_rejected(self):
        self.assert_reject(
            lambda doc: doc["boundaries"]["ephemeral"].__setitem__(
                "auto_memory_write_count", 1
            )
        )

    def test_tool_invocation_rejected(self):
        self.assert_reject(
            lambda doc: doc["boundaries"]["tool_less"].__setitem__(
                "tool_invocation_count", 1
            )
        )

    def test_canonical_write_attempt_rejected(self):
        self.assert_reject(
            lambda doc: doc["boundaries"]["structured_output"].__setitem__(
                "canonical_write_attempted", True
            )
        )

    def test_extra_environment_key_rejected(self):
        self.assert_reject(
            lambda doc: doc["boundaries"]["env_isolation"].__setitem__(
                "observed_child_env_keys", ["HOME", "AWS_SECRET_ACCESS_KEY"]
            )
        )

    def test_secret_value_leak_rejected(self):
        self.assert_reject(
            lambda doc: doc["boundaries"]["env_isolation"].__setitem__(
                "secret_value_leak_count", 1
            )
        )

    def test_whole_product_credit_rejected(self):
        self.assert_reject(lambda doc: doc.__setitem__("whole_product_credit", 1))


if __name__ == "__main__":
    unittest.main()
