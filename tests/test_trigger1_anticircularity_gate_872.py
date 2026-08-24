from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate as base
import trigger1_jspace_promotion_gate_anticircular_872 as gate

HEX64 = "a" * 64
HEAD40 = "b" * 40


def candidate() -> dict:
    controls = {name: {"runtime_receipt_sha256": HEX64} for name in base.REQUIRED_CONTROLS}
    return {
        "schema": base.CANDIDATE_SCHEMA,
        "runtime_intervention_class": gate.LOCAL_PYTORCH_CLASS,
        "source_identity": {
            "repo_head": HEAD40,
            "runtime_build_sha256": HEX64,
            "checkpoint_sha256": HEX64,
            "tokenizer_sha256": HEX64,
        },
        "intervention": {
            "runtime_observed": True,
            "invocation_id": "inv-anticircular",
            "activation_site": "model.model.layers.14:output:last_token",
            "source_packet_sha256": HEX64,
            "adapter_sha256": HEX64,
            "local_vector_sha256": HEX64,
            "applied_vector_sha256": HEX64,
            "runtime_intervention_receipt_sha256": HEX64,
            "gain": 2.0,
            "layer_start": 14,
            "layer_end": 14,
            "vector_basis_class": "DETERMINISTIC_WEIGHT_INDEPENDENT_PROBE",
            "derived_from_output_embeddings": False,
            "injected_after_final_norm": False,
            "readout_separation_layers": 13,
            "vector_derivation_receipt_sha256": HEX64,
        },
        "controls": controls,
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
            "relation": base.OWNER_API_TARGET_CLASS,
            "execution_surface": base.LOCAL_API_SURFACE,
            "zero_provider_billing": True,
            "local_runtime_execution_receipt_sha256": HEX64,
            "provider": "local",
            "model_or_route": "Qwen/Qwen3-0.6B@exact",
        },
    }


class Trigger1AntiCircularityGateTests(unittest.TestCase):
    def test_upstream_weight_independent_probe_can_reach_candidate_boundary(self):
        verdict = gate.adjudicate(candidate())
        self.assertTrue(verdict["anti_circularity_pass"])
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])

    def test_output_embedding_vector_at_final_norm_is_rejected(self):
        c = candidate()
        c["intervention"].update(
            {
                "activation_site": "model.model.norm:output:last_token",
                "layer_start": 28,
                "layer_end": 28,
                "vector_basis_class": "OUTPUT_EMBEDDING_TARGET_CONTRAST",
                "derived_from_output_embeddings": True,
                "injected_after_final_norm": True,
                "readout_separation_layers": 0,
            }
        )
        verdict = gate.adjudicate(c)
        self.assertFalse(verdict["anti_circularity_pass"])
        self.assertFalse(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("OUTPUT_EMBEDDING_DERIVED_VECTOR_FORBIDDEN", verdict["failures"])
        self.assertIn("POST_FINAL_NORM_INJECTION_FORBIDDEN", verdict["failures"])
        self.assertIn("UPSTREAM_READOUT_LAYER_SEPARATION_REQUIRED", verdict["failures"])
        self.assertIn("READOUT_ADJACENT_ACTIVATION_SITE_FORBIDDEN", verdict["failures"])

    def test_missing_derivation_receipt_fails_closed(self):
        c = candidate()
        del c["intervention"]["vector_derivation_receipt_sha256"]
        verdict = gate.adjudicate(c)
        self.assertFalse(verdict["anti_circularity_pass"])
        self.assertIn("VECTOR_DERIVATION_RECEIPT_REQUIRED", verdict["failures"])

    def test_non_pytorch_candidate_delegates_without_new_requirement(self):
        c = candidate()
        c["runtime_intervention_class"] = "LOCAL_LLAMA_CPP_CVEC_APPLIED"
        for key in (
            "vector_basis_class",
            "derived_from_output_embeddings",
            "injected_after_final_norm",
            "readout_separation_layers",
            "vector_derivation_receipt_sha256",
        ):
            c["intervention"].pop(key, None)
        verdict = gate.adjudicate(c)
        self.assertTrue(verdict["anti_circularity_pass"])
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])


if __name__ == "__main__":
    unittest.main()
