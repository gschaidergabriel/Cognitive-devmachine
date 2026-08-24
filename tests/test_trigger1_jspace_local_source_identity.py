from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate as gate

HEX64 = "a" * 64
HEAD40 = "b" * 40
TREE40 = "c" * 40


def local_pytorch_candidate() -> dict:
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
            "invocation_id": "inv-local-qwen",
            "activation_site": "model.model.norm:output:last_token",
            "source_packet_sha256": HEX64,
            "adapter_sha256": HEX64,
            "local_vector_sha256": HEX64,
            "applied_vector_sha256": HEX64,
            "runtime_intervention_receipt_sha256": HEX64,
            "gain": 2.0,
            "layer_start": 28,
            "layer_end": 28,
        },
        "controls": {
            name: {"runtime_receipt_sha256": HEX64}
            for name in gate.REQUIRED_CONTROLS
        },
        "calibration": {"family_id": "cal", "seeds": [1701, 1702]},
        "holdout": {
            "family_id": "hold",
            "seeds": [2718, 3141],
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


class Trigger1LocalSourceIdentityTests(unittest.TestCase):
    def test_clean_exact_local_pytorch_source_can_reach_candidate_verdict(self):
        verdict = gate.adjudicate(local_pytorch_candidate())
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])

    def test_dirty_local_pytorch_source_fails_closed(self):
        candidate = local_pytorch_candidate()
        candidate["source_identity"]["repo_dirty"] = True
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("LOCAL_PYTORCH_DIRTY_SOURCE_FAIL_CLOSED", verdict["failures"])

    def test_missing_tree_or_status_digest_fails_closed(self):
        candidate = local_pytorch_candidate()
        del candidate["source_identity"]["repo_tree"]
        del candidate["source_identity"]["repo_status_sha256"]
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertIn("LOCAL_PYTORCH_EXACT_REPO_TREE_REQUIRED", verdict["failures"])
        self.assertIn("LOCAL_PYTORCH_REPO_STATUS_SHA256_REQUIRED", verdict["failures"])


if __name__ == "__main__":
    unittest.main()
