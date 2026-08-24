from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_attested_local_qwen_api as wrapper
import trigger1_jspace_promotion_gate as gate
import trigger1_source_attestation as attest

HEX64 = "a" * 64
HEAD40 = "b" * 40
TREE40 = "c" * 40


def intermediate_candidate() -> dict:
    return {
        "schema": gate.CANDIDATE_SCHEMA,
        "runtime_intervention_class": "LOCAL_PYTORCH_ACTIVATION_INTERVENTION",
        "source_identity": {
            "repo_head": HEAD40,
            "repo_tree": TREE40,
            "repo_dirty": False,
            "repo_status_sha256": HEX64,
            "runtime_build_sha256": HEX64,
            "checkpoint_sha256": HEX64,
            "tokenizer_sha256": HEX64,
        },
        "intervention": {
            "runtime_observed": True,
            "invocation_id": "inv",
            "activation_site": "model.model.layers[14]:output:last_token",
            "terminal_output_projection_shortcut": False,
            "source_packet_sha256": HEX64,
            "adapter_sha256": HEX64,
            "local_vector_sha256": HEX64,
            "applied_vector_sha256": HEX64,
            "runtime_intervention_receipt_sha256": HEX64,
            "gain": 4.0,
            "layer_start": 14,
            "layer_end": 14,
        },
        "controls": {name: {"runtime_receipt_sha256": HEX64} for name in gate.REQUIRED_CONTROLS},
        "calibration": {"family_id": "cal", "seeds": [1, 2]},
        "holdout": {
            "family_id": "hold",
            "seeds": [3, 4],
            "reproducible_directional_effect": True,
            "strongest_counterexample_recorded": True,
            "analysis_receipt_sha256": HEX64,
        },
        "transport": {
            "hosted_prompt_only": False,
            "api_served": True,
            "loopback_only": True,
            "endpoint": "http://127.0.0.1:8089/v1/jspace/logits",
        },
        "target": {
            "relation": gate.OWNER_API_TARGET_CLASS,
            "execution_surface": gate.LOCAL_API_SURFACE,
            "zero_provider_billing": True,
            "local_runtime_execution_receipt_sha256": HEX64,
            "provider": "local",
            "model_or_route": "Qwen/Qwen3-0.6B@exact",
        },
    }


class Trigger1SourceExecutionBindingTests(unittest.TestCase):
    def test_clean_local_pytorch_intermediate_candidate_can_reach_goal_candidate(self):
        verdict = gate.adjudicate(intermediate_candidate())
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])

    def test_dirty_local_pytorch_candidate_fails_closed(self):
        candidate = intermediate_candidate()
        candidate["source_identity"]["repo_dirty"] = True
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertIn("LOCAL_PYTORCH_DIRTY_SOURCE_FAIL_CLOSED", verdict["failures"])

    def test_missing_tree_and_status_digest_fail_closed(self):
        candidate = intermediate_candidate()
        del candidate["source_identity"]["repo_tree"]
        del candidate["source_identity"]["repo_status_sha256"]
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertIn("LOCAL_PYTORCH_EXACT_REPO_TREE_REQUIRED", verdict["failures"])
        self.assertIn("LOCAL_PYTORCH_REPO_STATUS_SHA256_REQUIRED", verdict["failures"])

    def test_clean_status_is_not_collapsed_to_unknown(self):
        calls = {
            ("rev-parse", "HEAD"): HEAD40,
            ("rev-parse", "HEAD^{tree}"): TREE40,
            ("status", "--porcelain=v1", "--untracked-files=all"): "",
        }
        with mock.patch.object(attest, "_git", side_effect=lambda _root, *args: calls[args]):
            identity = attest.exact_source_identity(ROOT)
        self.assertFalse(identity["repo_dirty"])
        self.assertEqual(hashlib.sha256(b"").hexdigest(), identity["repo_status_sha256"])

    def test_wrapper_binding_adds_clean_source_and_wraps_executor_receipt(self):
        source = {
            "repo_head": HEAD40,
            "repo_tree": TREE40,
            "repo_dirty": False,
            "repo_status_sha256": hashlib.sha256(b"").hexdigest(),
        }
        candidate = intermediate_candidate()
        candidate["source_identity"] = {
            "repo_head": HEAD40,
            "runtime_build_sha256": HEX64,
            "checkpoint_sha256": HEX64,
            "tokenizer_sha256": HEX64,
        }
        result = {"source": {"repo_head": HEAD40, "repo_tree": TREE40}, "result_sha256": HEX64}
        with tempfile.TemporaryDirectory() as tmp:
            candidate_path = Path(tmp) / "trigger1_direct_steering_candidate.json"
            result_path = Path(tmp) / "trigger1_local_activation_api_result.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            result_path.write_text(json.dumps(result), encoding="utf-8")
            binding_sha = wrapper._bind_candidate(
                candidate_path,
                result_path,
                "intermediate",
                source,
                ROOT / "tools" / "trigger1_local_qwen06_intermediate_api_execute.py",
            )
            rebound = json.loads(candidate_path.read_text(encoding="utf-8"))
            binding = json.loads((Path(tmp) / "trigger1_source_execution_binding.json").read_text(encoding="utf-8"))
        self.assertEqual(source["repo_tree"], rebound["source_identity"]["repo_tree"])
        self.assertFalse(rebound["source_identity"]["repo_dirty"])
        self.assertEqual(binding_sha, rebound["target"]["local_runtime_execution_receipt_sha256"])
        self.assertEqual(HEX64, rebound["target"]["executor_local_runtime_receipt_sha256"])
        self.assertEqual(binding_sha, binding["binding_sha256"])


if __name__ == "__main__":
    unittest.main()
