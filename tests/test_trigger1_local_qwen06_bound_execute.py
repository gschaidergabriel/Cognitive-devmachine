from __future__ import annotations

import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_local_qwen06_bound_execute as bound

HEX64_A = "a" * 64
HEX64_B = "b" * 64
HEAD = "c" * 40
TREE = "d" * 40


def attestation() -> dict:
    return {
        "repo_head": HEAD,
        "repo_tree": TREE,
        "repo_dirty": False,
        "git_status_porcelain_v1_z_sha256": bound.sha256_bytes(b""),
        "launcher_relpath": "tools/trigger1_local_qwen06_bound_execute.py",
        "launcher_sha256": HEX64_A,
        "executor_relpath": "tools/trigger1_local_qwen06_activation_api_execute.py",
        "executor_sha256": HEX64_B,
        "python_executable": "/usr/bin/python3",
        "python_executable_sha256": "e" * 64,
    }


def fixture() -> tuple[dict, dict, dict]:
    pre = attestation()
    runtime = {
        "python_version": "3.test",
        "python_executable": "/usr/bin/python3",
        "python_executable_sha256": pre["python_executable_sha256"],
        "platform": "linux-test",
        "torch_version": "2.test",
        "torch_module_sha256": "1" * 64,
        "transformers_version": "5.test",
        "transformers_module_sha256": "2" * 64,
        "model_class": "Qwen3ForCausalLM",
        "model_module": "transformers.models.qwen3.modeling_qwen3",
        "model_module_sha256": "3" * 64,
    }
    runtime_build = bound.canonical_sha(runtime)
    result = {
        "schema": bound.RESULT_SCHEMA,
        "status": "PASS",
        "source": {"repo_head": HEAD, "repo_tree": TREE},
        "model": bound.MODEL_ID,
        "model_revision": bound.MODEL_REVISION,
        "checkpoint_sha256": "4" * 64,
        "tokenizer_sha256": "5" * 64,
        "runtime_manifest": runtime,
        "runtime_build_sha256": runtime_build,
        "api_endpoint": "http://127.0.0.1:43210/v1/jspace/logits",
        "api_loopback_only": True,
        "zero_provider_billing": True,
        "external_provider_credentials_read": False,
        "calibration_rows": [{"runtime_receipt_sha256": "6" * 64}],
        "holdout_rows": [{"runtime_receipt_sha256": "7" * 64}],
        "promotion_candidate_written": True,
    }
    result["result_sha256"] = bound.canonical_sha(result)
    local_receipt = bound.canonical_sha({
        "endpoint": result["api_endpoint"],
        "runtime_build_sha256": runtime_build,
        "checkpoint_sha256": result["checkpoint_sha256"],
        "tokenizer_sha256": result["tokenizer_sha256"],
        "source": result["source"],
        "api_invocations": 2,
    })
    candidate = {
        "schema": bound.CANDIDATE_SCHEMA,
        "source_identity": {
            "repo_head": HEAD,
            "runtime_build_sha256": runtime_build,
            "checkpoint_sha256": result["checkpoint_sha256"],
            "tokenizer_sha256": result["tokenizer_sha256"],
        },
        "transport": {
            "api_served": True,
            "loopback_only": True,
            "endpoint": result["api_endpoint"],
        },
        "target": {
            "provider": "local",
            "model_or_route": f"{bound.MODEL_ID}@{bound.MODEL_REVISION}",
            "zero_provider_billing": True,
            "local_runtime_execution_receipt_sha256": local_receipt,
        },
    }
    base_verdict = {
        "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v2",
        "owner_trigger1_goal_credit_candidate": True,
        "canonical_credit_minted": False,
    }
    return result, candidate, base_verdict


class BoundRuntimeTests(unittest.TestCase):
    def test_positive_binding_closes_all_declared_identities_without_minting_credit(self):
        result, candidate, verdict = fixture()
        pre = attestation()
        receipt = bound.build_binding(pre, copy.deepcopy(pre), result, candidate, verdict)
        self.assertEqual(bound.SCHEMA, receipt["schema"])
        self.assertTrue(bound.is_hex(receipt["runtime_binding_sha256"], 64))
        self.assertEqual(pre["executor_sha256"], receipt["source_attestation"]["executor_sha256"])
        self.assertEqual(result["api_endpoint"], receipt["transport"]["endpoint"])
        self.assertFalse(receipt["credit_boundary"]["canonical_credit_minted"])
        self.assertFalse(receipt["credit_boundary"]["jspace_model_runtime_credit"])

    def test_source_change_during_execution_fails_closed(self):
        result, candidate, verdict = fixture()
        pre = attestation()
        post = copy.deepcopy(pre)
        post["executor_sha256"] = "f" * 64
        with self.assertRaisesRegex(RuntimeError, "SOURCE_ATTESTATION_CHANGED_DURING_EXECUTION"):
            bound.build_binding(pre, post, result, candidate, verdict)

    def test_result_digest_tamper_fails_closed(self):
        result, candidate, verdict = fixture()
        result["device"] = "tampered-after-result-hash"
        pre = attestation()
        with self.assertRaisesRegex(RuntimeError, "RESULT_SHA256_MISMATCH"):
            bound.build_binding(pre, copy.deepcopy(pre), result, candidate, verdict)

    def test_local_runtime_receipt_mismatch_fails_closed(self):
        result, candidate, verdict = fixture()
        candidate["target"]["local_runtime_execution_receipt_sha256"] = "0" * 64
        pre = attestation()
        with self.assertRaisesRegex(RuntimeError, "LOCAL_RUNTIME_EXECUTION_RECEIPT_MISMATCH"):
            bound.build_binding(pre, copy.deepcopy(pre), result, candidate, verdict)

    def test_non_loopback_endpoint_fails_closed(self):
        result, candidate, verdict = fixture()
        result["api_endpoint"] = "https://example.com/v1/jspace/logits"
        payload = dict(result)
        payload.pop("result_sha256")
        result["result_sha256"] = bound.canonical_sha(payload)
        pre = attestation()
        with self.assertRaisesRegex(RuntimeError, "LOCAL_ENDPOINT_NOT_LOOPBACK"):
            bound.build_binding(pre, copy.deepcopy(pre), result, candidate, verdict)

    def test_python_identity_mismatch_fails_closed(self):
        result, candidate, verdict = fixture()
        result["runtime_manifest"]["python_executable_sha256"] = "9" * 64
        result["runtime_build_sha256"] = bound.canonical_sha(result["runtime_manifest"])
        candidate["source_identity"]["runtime_build_sha256"] = result["runtime_build_sha256"]
        payload = dict(result)
        payload.pop("result_sha256")
        result["result_sha256"] = bound.canonical_sha(payload)
        pre = attestation()
        with self.assertRaisesRegex(RuntimeError, "PYTHON_EXECUTABLE_IDENTITY_MISMATCH"):
            bound.build_binding(pre, copy.deepcopy(pre), result, candidate, verdict)

    def test_capture_source_attestation_rejects_dirty_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tools").mkdir()
            launcher = root / "tools" / "launcher.py"
            executor = root / "tools" / "executor.py"
            launcher.write_text("print('launcher')\n", encoding="utf-8")
            executor.write_text("print('executor')\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "test"], check=True)
            subprocess.run(["git", "-C", str(root), "add", "tools"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
            clean = bound.capture_source_attestation(root, launcher, executor)
            self.assertFalse(clean["repo_dirty"])
            executor.write_text("print('dirty')\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "SOURCE_WORKTREE_DIRTY_FAIL_CLOSED"):
                bound.capture_source_attestation(root, launcher, executor)


if __name__ == "__main__":
    unittest.main()
