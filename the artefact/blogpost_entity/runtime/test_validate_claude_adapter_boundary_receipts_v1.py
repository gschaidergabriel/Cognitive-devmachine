from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import validate_claude_adapter_boundary_receipts_v1 as v


def sha(char: str = "1") -> str:
    return char * 64


def sha40(char: str = "a") -> str:
    return char * 40


def common() -> dict:
    base = {
        "source": {"commit_sha": sha40("a"), "tree_sha": sha40("b"), "dirty": False},
        "run": {"test_run_id": "gen276-adapter-boundary-001", "suite_digest": sha("2")},
        "executor": {"host_class": "UBUNTU", "executor_identity_sha256": sha("3"), "kernel": "6.8.0"},
        "claude": {"binary_sha256": sha("4"), "version": "claude-code/test"},
        "adapter": {"version": "adapter/v1", "source_sha256": sha("5")},
        "isolation": {
            "home_sha256": sha("6"),
            "environment_allowlist": ["HOME", "LANG", "PATH"],
            "environment_sha256": sha("7"),
            "tool_mcp_config_sha256": sha("8"),
        },
    }
    base["binding_sha256"] = v.validate_common(base).digest
    return base


def receipt(kind: str) -> dict:
    d = common()
    d["schema"] = v.SCHEMAS[kind]
    if kind == "tool_less":
        d["evidence"] = {
            "tools_admitted": [],
            "mcp_servers_admitted": [],
            "tool_call_count": 0,
            "passed": True,
        }
    elif kind == "ephemeral":
        d["evidence"] = {
            "home_mode": "TEMPORARY_EMPTY",
            "preexisting_state_count": 0,
            "postrun_persistent_artifact_count": 0,
            "session_reuse": False,
            "passed": True,
        }
    elif kind == "structured_output":
        d["evidence"] = {
            "parser_contract_sha256": sha("9"),
            "raw_stdout_sha256": sha("a"),
            "raw_stderr_sha256": sha("b"),
            "accepted_result_sha256": sha("c"),
            "malformed_probe_rejected": True,
            "unstructured_probe_rejected": True,
            "passed": True,
        }
    elif kind == "env_isolation":
        d["evidence"] = {
            "child_env_keys": ["HOME", "LANG", "PATH"],
            "ambient_secret_keys_seen": [],
            "ambient_probe_count": 4,
            "inherited_ambient_key_count": 0,
            "home_under_ephemeral_root": True,
            "passed": True,
        }
    return d


class Tests(unittest.TestCase):
    def write_bundle(self, docs: dict[str, dict], root: Path) -> dict[str, Path]:
        out = {}
        for kind, doc in docs.items():
            path = root / f"{kind}.json"
            path.write_text(json.dumps(doc), encoding="utf-8")
            out[kind] = path
        return out

    def test_clean_bundle_passes(self):
        with tempfile.TemporaryDirectory() as td:
            docs = {kind: receipt(kind) for kind in v.SCHEMAS}
            result = v.validate_bundle(self.write_bundle(docs, Path(td)))
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["whole_product_credit"], "ZERO")

    def test_cross_receipt_source_drift_fails(self):
        with tempfile.TemporaryDirectory() as td:
            docs = {kind: receipt(kind) for kind in v.SCHEMAS}
            docs["ephemeral"]["source"]["tree_sha"] = sha40("c")
            docs["ephemeral"]["binding_sha256"] = v.validate_common(docs["ephemeral"]).digest
            with self.assertRaisesRegex(v.ValidationError, "CROSS_RECEIPT_BINDING_MISMATCH"):
                v.validate_bundle(self.write_bundle(docs, Path(td)))

    def test_tool_admission_fails(self):
        data = receipt("tool_less")
        data["evidence"]["tools_admitted"] = ["Bash"]
        with self.assertRaisesRegex(v.ValidationError, "TOOLS_ADMITTED"):
            v.validate_one("tool_less", data)

    def test_session_reuse_fails(self):
        data = receipt("ephemeral")
        data["evidence"]["session_reuse"] = True
        with self.assertRaisesRegex(v.ValidationError, "SESSION_REUSE_OBSERVED"):
            v.validate_one("ephemeral", data)

    def test_unstructured_acceptance_fails(self):
        data = receipt("structured_output")
        data["evidence"]["unstructured_probe_rejected"] = False
        with self.assertRaisesRegex(v.ValidationError, "UNSTRUCTURED_OUTPUT_ACCEPTED"):
            v.validate_one("structured_output", data)

    def test_ambient_secret_visibility_fails(self):
        data = receipt("env_isolation")
        data["evidence"]["ambient_secret_keys_seen"] = ["AWS_SECRET_ACCESS_KEY"]
        with self.assertRaisesRegex(v.ValidationError, "AMBIENT_SECRET_VISIBLE"):
            v.validate_one("env_isolation", data)

    def test_child_env_outside_allowlist_fails(self):
        data = receipt("env_isolation")
        data["evidence"]["child_env_keys"] = ["HOME", "LANG", "PATH", "SSH_AUTH_SOCK"]
        with self.assertRaisesRegex(v.ValidationError, "CHILD_ENV_OUTSIDE_ALLOWLIST"):
            v.validate_one("env_isolation", data)

    def test_placeholder_source_identity_fails(self):
        data = receipt("tool_less")
        data["source"]["commit_sha"] = "0" * 40
        with self.assertRaisesRegex(v.ValidationError, "PLACEHOLDER_SHA40"):
            v.validate_one("tool_less", data)

    def test_binding_digest_tamper_fails(self):
        data = receipt("tool_less")
        data["binding_sha256"] = sha("d")
        with self.assertRaisesRegex(v.ValidationError, "BINDING_DIGEST_MISMATCH"):
            v.validate_one("tool_less", data)


if __name__ == "__main__":
    unittest.main()
