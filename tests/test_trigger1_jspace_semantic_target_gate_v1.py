from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate as base
import trigger1_jspace_semantic_target_gate_v1 as semantic_gate

HEX64 = "a" * 64
HEAD40 = "b" * 40


def valid_local_token_candidate() -> dict:
    controls = {
        name: {"runtime_receipt_sha256": HEX64}
        for name in base.REQUIRED_CONTROLS
    }
    return {
        "schema": base.CANDIDATE_SCHEMA,
        "runtime_intervention_class": "LOCAL_LLAMA_CPP_CVEC_APPLIED",
        "source_identity": {
            "repo_head": HEAD40,
            "runtime_build_sha256": HEX64,
            "checkpoint_sha256": HEX64,
            "tokenizer_sha256": HEX64,
        },
        "intervention": {
            "runtime_observed": True,
            "invocation_id": "inv-1",
            "activation_site": "llama.cpp:qwen3:layer[20]:post_ffn_residual_cvec_before_next_layer",
            "source_packet_sha256": HEX64,
            "adapter_sha256": HEX64,
            "local_vector_sha256": HEX64,
            "applied_vector_sha256": HEX64,
            "runtime_intervention_receipt_sha256": HEX64,
            "gain": 32.0,
            "layer_start": 20,
            "layer_end": 20,
            "terminal_output_projection_shortcut": False,
        },
        "vector_derivation": {
            "method": "internal activation semantic contrast",
            "uses_output_head_weights": False,
            "uses_holdout_data": False,
            "uses_evaluation_output_labels": False,
            "derivation_family_id": "semantic-derivation-family",
            "derivation_receipt_sha256": HEX64,
        },
        "controls": controls,
        "calibration": {
            "family_id": "calibration-family",
            "seeds": [1, 2, 3],
        },
        "holdout": {
            "family_id": "holdout-family",
            "seeds": [4, 5, 6],
            "reproducible_directional_effect": True,
            "strongest_counterexample_recorded": True,
            "analysis_receipt_sha256": HEX64,
            "evaluation_independent_of_vector_derivation": True,
            "metric_definition_sha256": HEX64,
            "metric_uses_output_tokens": True,
            "label_mapping_counterbalanced": True,
            "requested_semantic_target_counterbalanced": True,
            "requested_semantic_targets": ["AFFIRMATIVE", "NEGATIVE", "NEUTRAL"],
        },
        "transport": {
            "hosted_prompt_only": False,
            "api_served": True,
            "loopback_only": True,
            "endpoint": "http://127.0.0.1:8089/v1/chat/completions",
        },
        "target": {
            "relation": base.OWNER_API_TARGET_CLASS,
            "execution_surface": base.LOCAL_API_SURFACE,
            "zero_provider_billing": True,
            "local_runtime_execution_receipt_sha256": HEX64,
            "provider": "local",
            "model_or_route": "Qwen/Qwen3-0.6B-GGUF@exact",
        },
    }


class Trigger1SemanticTargetGateTests(unittest.TestCase):
    def test_balanced_semantic_targets_preserve_predecessor_goal_candidate(self):
        verdict = semantic_gate.adjudicate(valid_local_token_candidate())
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["semantic_target_guard_pass"])
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])

    def test_all_affirmative_is_demoted_but_keeps_mechanism_credit(self):
        candidate = valid_local_token_candidate()
        candidate["holdout"]["requested_semantic_targets"] = ["AFFIRMATIVE"] * 3
        verdict = semantic_gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["semantic_target_guard_pass"])
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("REQUESTED_SEMANTIC_TARGET_VARIATION_REQUIRED", verdict["scientific_independence_failures"])

    def test_missing_semantic_counterbalance_declaration_fails_closed(self):
        candidate = valid_local_token_candidate()
        del candidate["holdout"]["requested_semantic_target_counterbalanced"]
        verdict = semantic_gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn(
            "TOKEN_OUTPUT_METRIC_REQUIRES_COUNTERBALANCED_REQUESTED_SEMANTIC_TARGET",
            verdict["scientific_independence_failures"],
        )

    def test_imbalanced_semantic_target_counts_fail_closed(self):
        candidate = valid_local_token_candidate()
        candidate["holdout"]["requested_semantic_targets"] = ["AFFIRMATIVE", "AFFIRMATIVE", "NEGATIVE"]
        verdict = semantic_gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn(
            "REQUESTED_SEMANTIC_TARGET_COUNTS_MUST_BE_BALANCED",
            verdict["scientific_independence_failures"],
        )

    def test_non_token_metric_is_not_overconstrained_by_semantic_target_guard(self):
        candidate = valid_local_token_candidate()
        candidate["holdout"]["metric_uses_output_tokens"] = False
        candidate["holdout"].pop("requested_semantic_target_counterbalanced")
        candidate["holdout"].pop("requested_semantic_targets")
        verdict = semantic_gate.adjudicate(candidate)
        self.assertTrue(verdict["semantic_target_guard_pass"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])


if __name__ == "__main__":
    unittest.main()
