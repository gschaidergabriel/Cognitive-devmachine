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


def local_pytorch_candidate() -> dict:
    return {
        "schema": gate.CANDIDATE_SCHEMA,
        "runtime_intervention_class": gate.LOCAL_PYTORCH_RUNTIME_CLASS,
        "source_identity": {
            "repo_head": HEAD40,
            "runtime_build_sha256": HEX64,
            "checkpoint_sha256": HEX64,
            "tokenizer_sha256": HEX64,
        },
        "intervention": {
            "runtime_observed": True,
            "invocation_id": "inv-local-pytorch-1",
            "activation_site": "model.model.norm:output:last_token",
            "source_packet_sha256": HEX64,
            "adapter_sha256": HEX64,
            "local_vector_sha256": HEX64,
            "applied_vector_sha256": HEX64,
            "runtime_intervention_receipt_sha256": HEX64,
            "gain": 8.0,
            "layer_start": 28,
            "layer_end": 28,
        },
        "controls": {
            name: {"runtime_receipt_sha256": HEX64}
            for name in gate.REQUIRED_CONTROLS
        },
        "calibration": {"family_id": "calibration-family", "seeds": [1701, 1702]},
        "holdout": {
            "family_id": "holdout-family",
            "seeds": [2718, 3141],
            "reproducible_directional_effect": True,
            "strongest_counterexample_recorded": True,
            "analysis_receipt_sha256": HEX64,
        },
        "transport": {
            "hosted_prompt_only": False,
            "api_served": True,
            "loopback_only": True,
            "endpoint": "http://127.0.0.1:19091/v1/jspace/logits",
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


class Trigger1CausalIndependenceTests(unittest.TestCase):
    def test_local_pytorch_without_independence_evidence_is_mechanism_only(self):
        candidate = local_pytorch_candidate()
        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["scientific_independence_pass"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn(
            "CAUSAL_INDEPENDENCE_EVIDENCE_REQUIRED_FOR_LOCAL_PYTORCH",
            verdict["scientific_independence_failures"],
        )

    def test_same_readout_vector_and_metric_fails_goal_even_with_runtime_controls(self):
        candidate = local_pytorch_candidate()
        candidate["scientific_independence"] = {
            "vector_construction_evaluation_independent": False,
            "holdout_target_independent_of_vector_construction": False,
            "readout_algebraically_forces_directional_metric": True,
            "evidence_receipt_sha256": HEX64,
        }
        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn(
            "VECTOR_CONSTRUCTION_MUST_BE_INDEPENDENT_OF_EVALUATION_READOUT",
            verdict["owner_target_failures"],
        )
        self.assertIn("READOUT_ALIGNED_TAUTOLOGY_NOT_EXCLUDED", verdict["owner_target_failures"])

    def test_independent_local_pytorch_discriminator_can_reach_goal_candidate(self):
        candidate = local_pytorch_candidate()
        candidate["scientific_independence"] = {
            "vector_construction_evaluation_independent": True,
            "holdout_target_independent_of_vector_construction": True,
            "readout_algebraically_forces_directional_metric": False,
            "evidence_receipt_sha256": HEX64,
        }
        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["scientific_independence_pass"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertEqual([], verdict["scientific_independence_failures"])


if __name__ == "__main__":
    unittest.main()
