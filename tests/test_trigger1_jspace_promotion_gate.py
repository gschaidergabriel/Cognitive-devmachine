from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate as gate

HEX64 = "a" * 64
HEAD40 = "b" * 40


def valid_candidate() -> dict:
    controls = {
        name: {"runtime_receipt_sha256": HEX64}
        for name in gate.REQUIRED_CONTROLS
    }
    return {
        "schema": gate.CANDIDATE_SCHEMA,
        "runtime_intervention_class": "PROVIDER_RUNTIME_INTERNAL_VECTOR_INTERVENTION",
        "source_identity": {
            "repo_head": HEAD40,
            "runtime_build_sha256": HEX64,
            "checkpoint_sha256": HEX64,
            "tokenizer_sha256": HEX64,
        },
        "intervention": {
            "runtime_observed": True,
            "invocation_id": "inv-1",
            "activation_site": "layer:12/residual",
            "source_packet_sha256": HEX64,
            "adapter_sha256": HEX64,
            "local_vector_sha256": HEX64,
            "applied_vector_sha256": HEX64,
            "runtime_intervention_receipt_sha256": HEX64,
            "gain": 0.75,
            "layer_start": 10,
            "layer_end": 20,
        },
        "vector_derivation": {
            "method": "ACTIVATION_CONTRAST_MEAN",
            "uses_output_head_weights": False,
            "uses_holdout_data": False,
            "uses_evaluation_output_labels": False,
            "derivation_family_id": "derivation-family",
            "derivation_receipt_sha256": HEX64,
        },
        "controls": controls,
        "calibration": {"family_id": "cal", "seeds": [1, 2]},
        "holdout": {
            "family_id": "hold",
            "seeds": [3, 4],
            "reproducible_directional_effect": True,
            "strongest_counterexample_recorded": True,
            "analysis_receipt_sha256": HEX64,
            "evaluation_independent_of_vector_derivation": True,
            "metric_definition_sha256": HEX64,
            "metric_uses_output_tokens": False,
        },
        "transport": {"hosted_prompt_only": False},
        "target": {
            "relation": gate.LEGACY_OWNER_API_TARGET_CLASS,
            "typed_free_lane_admitted": True,
            "free_lane_execution_receipt_sha256": HEX64,
            "provider": "example-free-provider",
            "model_or_route": "exact-model",
        },
    }


def valid_local_api_candidate() -> dict:
    candidate = valid_candidate()
    candidate["runtime_intervention_class"] = "LOCAL_LLAMA_CPP_CVEC_APPLIED"
    candidate["transport"] = {
        "hosted_prompt_only": False,
        "api_served": True,
        "loopback_only": True,
        "endpoint": "http://127.0.0.1:8089/v1/chat/completions",
    }
    candidate["target"] = {
        "relation": gate.OWNER_API_TARGET_CLASS,
        "execution_surface": gate.LOCAL_API_SURFACE,
        "zero_provider_billing": True,
        "local_runtime_execution_receipt_sha256": HEX64,
        "provider": "local",
        "model_or_route": "Qwen/Qwen3-0.6B-GGUF@exact",
    }
    return candidate


class Trigger1PromotionGateTests(unittest.TestCase):
    def test_exact_instrumented_free_external_api_candidate_can_reach_both_candidate_verdicts(self):
        verdict = gate.adjudicate(valid_candidate())
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertTrue(verdict["owner_trigger1_direct_free_api_model_credit_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])

    def test_exact_zero_cost_loopback_api_cvec_candidate_can_reach_goal(self):
        verdict = gate.adjudicate(valid_local_api_candidate())
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertEqual([], verdict["owner_target_failures"])

    def test_terminal_output_projection_shortcut_fails_mechanism_and_goal(self):
        candidate = valid_local_api_candidate()
        candidate["runtime_intervention_class"] = "LOCAL_PYTORCH_ACTIVATION_INTERVENTION"
        candidate["intervention"]["activation_site"] = "model.model.norm:output:last_token"
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn(
            "TERMINAL_OUTPUT_PROJECTION_SHORTCUT_NOT_JSPACE_CAUSAL_EVIDENCE",
            verdict["failures"],
        )

    def test_declared_terminal_output_projection_shortcut_fails_closed(self):
        candidate = valid_local_api_candidate()
        candidate["intervention"]["terminal_output_projection_shortcut"] = True
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn(
            "TERMINAL_OUTPUT_PROJECTION_SHORTCUT_NOT_JSPACE_CAUSAL_EVIDENCE",
            verdict["failures"],
        )

    def test_output_head_derived_vector_is_mechanism_only(self):
        candidate = valid_local_api_candidate()
        candidate["vector_derivation"]["method"] = "LM_HEAD_READOUT_DIFFERENCE"
        candidate["vector_derivation"]["uses_output_head_weights"] = True
        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn(
            "OUTPUT_HEAD_DERIVED_VECTOR_CANNOT_SATISFY_JSPACE_GOAL",
            verdict["scientific_independence_failures"],
        )

    def test_vector_derivation_may_not_use_holdout(self):
        candidate = valid_local_api_candidate()
        candidate["vector_derivation"]["uses_holdout_data"] = True
        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn(
            "VECTOR_DERIVATION_MUST_NOT_USE_HOLDOUT_DATA",
            verdict["scientific_independence_failures"],
        )

    def test_vector_derivation_may_not_use_evaluation_output_labels(self):
        candidate = valid_local_api_candidate()
        candidate["vector_derivation"]["uses_evaluation_output_labels"] = True
        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn(
            "VECTOR_DERIVATION_MUST_NOT_USE_EVALUATION_OUTPUT_LABELS",
            verdict["scientific_independence_failures"],
        )

    def test_token_metric_requires_counterbalanced_mapping(self):
        candidate = valid_local_api_candidate()
        candidate["holdout"]["metric_uses_output_tokens"] = True
        candidate["holdout"]["label_mapping_counterbalanced"] = False
        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn(
            "TOKEN_OUTPUT_METRIC_REQUIRES_COUNTERBALANCED_LABEL_MAPPING",
            verdict["scientific_independence_failures"],
        )

    def test_hosted_prompt_only_fails_closed(self):
        candidate = valid_candidate()
        candidate["transport"]["hosted_prompt_only"] = True
        candidate["runtime_intervention_class"] = "HOSTED_TEXT_API"
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("HOSTED_PROMPT_ONLY_CANNOT_PROVE_VECTOR_STEERING", verdict["failures"])

    def test_local_cvec_without_api_boundary_is_mechanism_only(self):
        candidate = valid_candidate()
        candidate["runtime_intervention_class"] = "LOCAL_LLAMA_CPP_CVEC_APPLIED"
        candidate["target"] = {
            "relation": gate.OWNER_API_TARGET_CLASS,
            "execution_surface": gate.LOCAL_API_SURFACE,
            "zero_provider_billing": True,
            "local_runtime_execution_receipt_sha256": HEX64,
            "provider": "local",
            "model_or_route": "Qwen/Qwen3-0.6B-GGUF@exact",
        }
        candidate["transport"] = {"hosted_prompt_only": False, "api_served": False}
        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("API_SERVED_RUNTIME_REQUIRED", verdict["owner_target_failures"])
        self.assertIn("LOCAL_API_LOOPBACK_ONLY_REQUIRED", verdict["owner_target_failures"])

    def test_local_api_requires_zero_provider_billing(self):
        candidate = valid_local_api_candidate()
        candidate["target"]["zero_provider_billing"] = False
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("LOCAL_ZERO_PROVIDER_BILLING_REQUIRED", verdict["owner_target_failures"])

    def test_local_api_requires_loopback_endpoint(self):
        candidate = valid_local_api_candidate()
        candidate["transport"]["endpoint"] = "https://example.com/v1/chat/completions"
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("LOCAL_API_LOOPBACK_ENDPOINT_REQUIRED", verdict["owner_target_failures"])

    def test_calibration_holdout_overlap_fails_mechanism(self):
        candidate = valid_candidate()
        candidate["holdout"]["seeds"] = [2, 3]
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertIn("CALIBRATION_HOLDOUT_SEEDS_MUST_BE_DISJOINT", verdict["failures"])

    def test_missing_required_control_fails_mechanism(self):
        candidate = valid_candidate()
        del candidate["controls"]["ORTHOGONAL_SAME_NORM"]
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertIn("CONTROL_REQUIRED:ORTHOGONAL_SAME_NORM", verdict["failures"])

    def test_batch_scan_without_candidates_is_zero_credit(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = gate.scan_batch(Path(tmp))
        self.assertEqual(result["candidate_files_seen"], 0)
        self.assertFalse(result["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(result["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(result["canonical_credit_minted"])

    def test_batch_scan_reads_local_api_candidate_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lane" / "trigger1_direct_steering_candidate.json"
            path.parent.mkdir()
            path.write_text(json.dumps(valid_local_api_candidate()), encoding="utf-8")
            result = gate.scan_batch(Path(tmp))
        self.assertEqual(result["candidate_files_seen"], 1)
        self.assertTrue(result["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(result["scientifically_independent_vector_candidate"])
        self.assertTrue(result["owner_trigger1_goal_credit_candidate"])
        self.assertTrue(result["owner_trigger1_direct_free_api_model_credit_candidate"])


if __name__ == "__main__":
    unittest.main()
