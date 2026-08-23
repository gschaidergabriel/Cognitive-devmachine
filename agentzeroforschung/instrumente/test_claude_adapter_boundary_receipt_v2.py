from __future__ import annotations

import hashlib
import unittest

from validate_claude_adapter_boundary_receipt_v2 import (
    ReceiptError,
    canonical_sha256,
    diagnose,
    validate,
)


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def common() -> dict:
    return {
        "source_commit": hashlib.sha1(b"source-commit").hexdigest(),
        "source_tree": hashlib.sha1(b"source-tree").hexdigest(),
        "dirty": False,
        "claude_binary_sha256": digest("claude-binary"),
        "claude_version": "test-claude",
        "command_sha256": digest("command"),
        "input_sha256": digest("input"),
        "executor": {"os": "linux", "arch": "x86_64", "runtime": "isolated-test"},
        "started_at": "2026-08-23T03:30:00Z",
        "finished_at": "2026-08-23T03:30:01Z",
    }


def valid_receipt() -> dict:
    c = common()
    identity = canonical_sha256(c)
    stdout = digest("stdout")
    stderr = digest("stderr")
    result = digest("result")
    memory_env = {
        "CLAUDE_CODE_SKIP_PROMPT_HISTORY": "1",
        "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
        "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1",
    }
    generated_policy = {
        "DISABLE_AUTOUPDATER": "1",
        **memory_env,
    }
    return {
        "schema": "CLAUDE_ADAPTER_BOUNDARY_RECEIPT/v2",
        "common": c,
        "common_identity_sha256": identity,
        "boundaries": {
            "tool_less": {
                "schema": "TOOL_LESS_RECEIPT/v2",
                "common_identity_sha256": identity,
                "measured": True,
                "status": "PASS",
                "stdout_sha256": stdout,
                "stderr_sha256": stderr,
                "built_in_tools_enabled": False,
                "bash_enabled": False,
                "mcp_servers": [],
                "tool_invocation_count": 0,
            },
            "memory_authority": {
                "schema": "MEMORY_AUTHORITY_RECEIPT/v2",
                "common_identity_sha256": identity,
                "measured": True,
                "status": "PASS",
                "stdout_sha256": stdout,
                "stderr_sha256": stderr,
                "persistent_session_reused": False,
                "prompt_history_disabled": True,
                "auto_memory_disabled": True,
                "claude_md_memory_disabled": True,
                "home_mode": "PERSISTENT_AUTH_ONLY",
                "observed_memory_env": dict(memory_env),
                "memory_file_load_count": 0,
                "memory_file_write_count": 0,
            },
            "structured_output": {
                "schema": "STRUCTURED_OUTPUT_RECEIPT/v2",
                "common_identity_sha256": identity,
                "measured": True,
                "status": "PASS",
                "stdout_sha256": stdout,
                "stderr_sha256": stderr,
                "parse_ok": True,
                "candidate_only": True,
                "canonical_write_attempted": False,
                "result_sha256": result,
                "result_schema": "clayverse-decision/v1",
            },
            "env_isolation": {
                "schema": "ENV_ISOLATION_RECEIPT/v2",
                "common_identity_sha256": identity,
                "measured": True,
                "status": "PASS",
                "stdout_sha256": stdout,
                "stderr_sha256": stderr,
                "allowed_env_keys": ["PATH", "HOME", "ANTHROPIC_API_KEY"],
                "observed_child_env_keys": [
                    "PATH",
                    "HOME",
                    "ANTHROPIC_API_KEY",
                    "DISABLE_AUTOUPDATER",
                    "CLAUDE_CODE_SKIP_PROMPT_HISTORY",
                    "CLAUDE_CODE_DISABLE_AUTO_MEMORY",
                    "CLAUDE_CODE_DISABLE_CLAUDE_MDS",
                ],
                "generated_policy_env": generated_policy,
                "forbidden_key_count": 0,
                "secret_value_leak_count": 0,
                "environment_shape_sha256": digest("env-shape"),
            },
        },
        "aggregate_status": "PASS",
        "runtime_credit": "CLAUDE_ADAPTER_BOUNDARY_ONLY",
        "whole_product_credit": 0,
        "v1_runtime_credit_accepted": False,
    }


class ClaudeAdapterBoundaryReceiptV2Tests(unittest.TestCase):
    def test_persistent_auth_home_is_admissible_when_memory_is_fenced(self):
        result = validate(valid_receipt())
        self.assertTrue(result["promotion_eligible"])
        self.assertEqual(result["failing_boundaries"], [])

    def test_temporary_home_is_also_admissible(self):
        receipt = valid_receipt()
        receipt["boundaries"]["memory_authority"]["home_mode"] = "TEMPORARY"
        self.assertTrue(validate(receipt)["promotion_eligible"])

    def test_auto_memory_enabled_is_preserved_as_negative_evidence(self):
        receipt = valid_receipt()
        memory = receipt["boundaries"]["memory_authority"]
        memory["auto_memory_disabled"] = False
        memory["status"] = "FAIL"
        receipt["aggregate_status"] = "FAIL"
        receipt["runtime_credit"] = "ZERO"
        diagnostic = diagnose(receipt)
        self.assertEqual(diagnostic["aggregate_status"], "FAIL")
        self.assertIn("AUTO_MEMORY_ENABLED", diagnostic["violations"]["memory_authority"])
        with self.assertRaisesRegex(ReceiptError, "aggregate_status must be PASS"):
            validate(receipt)

    def test_claude_md_memory_enabled_fails_promotion(self):
        receipt = valid_receipt()
        memory = receipt["boundaries"]["memory_authority"]
        memory["claude_md_memory_disabled"] = False
        memory["status"] = "FAIL"
        receipt["aggregate_status"] = "FAIL"
        receipt["runtime_credit"] = "ZERO"
        self.assertIn("CLAUDE_MD_MEMORY_ENABLED", diagnose(receipt)["violations"]["memory_authority"])

    def test_memory_env_fence_is_structural_not_self_reported(self):
        receipt = valid_receipt()
        del receipt["boundaries"]["memory_authority"]["observed_memory_env"]["CLAUDE_CODE_DISABLE_AUTO_MEMORY"]
        with self.assertRaisesRegex(ReceiptError, "observed_memory_env keys mismatch"):
            diagnose(receipt)

    def test_generated_policy_env_cannot_force_memory_back_on(self):
        receipt = valid_receipt()
        receipt["boundaries"]["env_isolation"]["generated_policy_env"]["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "0"
        with self.assertRaisesRegex(ReceiptError, "generated_policy_env differs from canonical Claude child policy"):
            diagnose(receipt)

    def test_env_receipt_cannot_self_authorize_forbidden_secret_key(self):
        receipt = valid_receipt()
        env = receipt["boundaries"]["env_isolation"]
        env["allowed_env_keys"].append("CLERK_SECRET_KEY")
        env["observed_child_env_keys"].append("CLERK_SECRET_KEY")
        with self.assertRaisesRegex(ReceiptError, "allowed_env_keys exceed canonical Claude child policy"):
            diagnose(receipt)

    def test_generated_policy_cannot_self_authorize_extra_key(self):
        receipt = valid_receipt()
        env = receipt["boundaries"]["env_isolation"]
        env["generated_policy_env"]["CLERK_SECRET_KEY"] = "redacted"
        env["observed_child_env_keys"].append("CLERK_SECRET_KEY")
        with self.assertRaisesRegex(ReceiptError, "generated_policy_env differs from canonical Claude child policy"):
            diagnose(receipt)

    def test_v1_receipt_is_not_silently_promoted(self):
        receipt = valid_receipt()
        receipt["schema"] = "CLAUDE_ADAPTER_BOUNDARY_RECEIPT/v1"
        with self.assertRaisesRegex(ReceiptError, "top-level schema mismatch"):
            diagnose(receipt)

    def test_mixed_run_child_identity_fails_closed(self):
        receipt = valid_receipt()
        receipt["boundaries"]["memory_authority"]["common_identity_sha256"] = digest("other-run")
        with self.assertRaisesRegex(ReceiptError, "memory_authority common identity mismatch"):
            diagnose(receipt)

    def test_v1_runtime_credit_flag_must_remain_false(self):
        receipt = valid_receipt()
        receipt["v1_runtime_credit_accepted"] = True
        with self.assertRaisesRegex(ReceiptError, "v1 current runtime credit must be disabled"):
            diagnose(receipt)

    def test_common_times_must_be_ordered_utc(self):
        receipt = valid_receipt()
        receipt["common"]["finished_at"] = "2026-08-23T03:29:59Z"
        receipt["common_identity_sha256"] = canonical_sha256(receipt["common"])
        for boundary in receipt["boundaries"].values():
            boundary["common_identity_sha256"] = receipt["common_identity_sha256"]
        with self.assertRaisesRegex(ReceiptError, "finished_at precedes started_at"):
            diagnose(receipt)


if __name__ == "__main__":
    unittest.main()
