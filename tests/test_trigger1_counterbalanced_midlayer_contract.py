from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate as gate
import trigger1_local_qwen06_counterbalanced_midlayer_execute as cb

HEX64 = "a" * 64
HEAD40 = "b" * 40


def promotion_candidate() -> dict:
    controls = {name: {"runtime_receipt_sha256": HEX64, "observations": 3} for name in gate.REQUIRED_CONTROLS}
    return {
        "schema": gate.CANDIDATE_SCHEMA,
        "runtime_intervention_class": "LOCAL_PYTORCH_ACTIVATION_INTERVENTION",
        "source_identity": {
            "repo_head": HEAD40,
            "runtime_build_sha256": HEX64,
            "checkpoint_sha256": HEX64,
            "tokenizer_sha256": HEX64,
        },
        "intervention": {
            "runtime_observed": True,
            "invocation_id": HEX64,
            "activation_site": "model.model.layers[14]:output:last_token",
            "source_packet_sha256": HEX64,
            "adapter_sha256": HEX64,
            "local_vector_sha256": HEX64,
            "applied_vector_sha256": HEX64,
            "runtime_intervention_receipt_sha256": HEX64,
            "gain": 1.0,
            "layer_start": 14,
            "layer_end": 14,
            "terminal_output_projection_shortcut": False,
        },
        "vector_derivation": {
            "method": cb.VECTOR_DERIVATION_METHOD,
            "uses_output_head_weights": False,
            "uses_holdout_data": False,
            "derivation_family_id": cb.family_id(cb.BASIS_PROMPTS),
            "derivation_receipt_sha256": HEX64,
        },
        "controls": controls,
        "calibration": {
            "family_id": cb.family_id(cb.GAIN_CALIBRATION),
            "seeds": [seed for seed, _target, _prompt in cb.GAIN_CALIBRATION],
        },
        "holdout": {
            "family_id": cb.family_id(cb.HOLDOUT),
            "seeds": [seed for seed, _target, _prompt in cb.HOLDOUT],
            "reproducible_directional_effect": True,
            "strongest_counterexample_recorded": True,
            "analysis_receipt_sha256": HEX64,
            "evaluation_independent_of_vector_derivation": True,
            "metric_definition_sha256": cb.metric_definition_sha256(),
            "metric_uses_output_tokens": True,
            "label_mapping_counterbalanced": True,
        },
        "transport": {
            "hosted_prompt_only": False,
            "api_served": True,
            "loopback_only": True,
            "endpoint": "http://127.0.0.1:49123/v1/jspace/logits",
        },
        "target": {
            "relation": gate.OWNER_API_TARGET_CLASS,
            "execution_surface": gate.LOCAL_API_SURFACE,
            "zero_provider_billing": True,
            "local_runtime_execution_receipt_sha256": HEX64,
            "provider": "local",
            "model_or_route": "Qwen/Qwen3-0.6B@c1899de289a04d12100db370d81485cdf75e47ca",
        },
    }


class CounterbalancedMidlayerContractTests(unittest.TestCase):
    def test_calibration_and_holdout_each_counterbalance_abc_exactly_once(self):
        for rows in (cb.GAIN_CALIBRATION, cb.HOLDOUT):
            manifest = cb.counterbalance_manifest(rows)
            self.assertTrue(manifest["exact_once_each"])
            self.assertEqual({"A": 1, "B": 1, "C": 1}, manifest["counts"])

    def test_vector_derivation_family_is_disjoint_from_holdout(self):
        self.assertNotEqual(cb.family_id(cb.BASIS_PROMPTS), cb.family_id(cb.HOLDOUT))
        self.assertTrue(set(seed for seed, _role, _prompt in cb.BASIS_PROMPTS).isdisjoint(
            seed for seed, _target, _prompt in cb.HOLDOUT
        ))

    def test_basis_prompts_do_not_contain_surface_codebook(self):
        for _seed, _role, prompt in cb.BASIS_PROMPTS:
            lowered = prompt.lower()
            self.assertNotIn("codebook", lowered)
            self.assertNotIn("fresh code", lowered)
            self.assertNotIn("a/b/c", lowered)

    def test_target_score_rotates_with_surface_mapping(self):
        logits = {"A": 5.0, "B": 2.0, "C": -1.0}
        self.assertAlmostEqual(4.5, cb.target_score(logits, "A"))
        self.assertAlmostEqual(0.0, cb.target_score(logits, "B"))
        self.assertAlmostEqual(-4.5, cb.target_score(logits, "C"))

    def test_metric_receipt_declares_real_token_counterbalance(self):
        metric = cb.metric_definition()
        self.assertTrue(metric["metric_uses_output_tokens"])
        self.assertTrue(metric["label_mapping_counterbalanced"])
        self.assertTrue(metric["gain_calibration_counterbalance"]["exact_once_each"])
        self.assertTrue(metric["holdout_counterbalance"]["exact_once_each"])
        self.assertEqual(64, len(cb.metric_definition_sha256()))

    def test_v3_gate_can_accept_scientifically_complete_counterbalanced_candidate(self):
        verdict = gate.adjudicate(promotion_candidate())
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertEqual([], verdict["scientific_independence_failures"])

    def test_v3_gate_rejects_same_candidate_when_counterbalance_claim_is_false(self):
        candidate = promotion_candidate()
        candidate["holdout"]["label_mapping_counterbalanced"] = False
        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn(
            "TOKEN_OUTPUT_METRIC_REQUIRES_COUNTERBALANCED_LABEL_MAPPING",
            verdict["scientific_independence_failures"],
        )

    def test_vector_derivation_evidence_never_claims_output_head_or_holdout_use(self):
        evidence = cb.vector_derivation_evidence([
            {"seed": 1101, "semantic_role": "TARGET", "activation_sha256": HEX64}
        ])
        self.assertEqual(cb.VECTOR_DERIVATION_METHOD, evidence["method"])
        self.assertIs(evidence["uses_output_head_weights"], False)
        self.assertIs(evidence["uses_holdout_data"], False)
        self.assertEqual(64, len(evidence["derivation_receipt_sha256"]))


if __name__ == "__main__":
    unittest.main()
