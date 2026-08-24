from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate as gate
import trigger1_midlayer_candidate_v3_bind as binder

HEX64 = "a" * 64
HEAD40 = "b" * 40


def candidate() -> dict:
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
            "invocation_id": "inv-1",
            "activation_site": "model.model.layers[14]:output:last_token",
            "source_packet_sha256": HEX64,
            "adapter_sha256": HEX64,
            "local_vector_sha256": HEX64,
            "applied_vector_sha256": HEX64,
            "runtime_intervention_receipt_sha256": HEX64,
            "gain": 1.0,
            "layer_start": 14,
            "layer_end": 14,
            "downstream_transformer_layers": 13,
            "terminal_output_projection_shortcut": False,
            "basis_constructed_without_output_head": True,
        },
        "controls": {
            name: {"runtime_receipt_sha256": HEX64, "observations": 3}
            for name in gate.REQUIRED_CONTROLS
        },
        "calibration": {
            "family_id": "gain-calibration-family",
            "basis_family_id": "basis-family",
            "seeds": [1701, 1702, 1703],
            "basis_seeds": [1101, 1102, 1103],
            "selected_gain": 1.0,
        },
        "holdout": {
            "family_id": "holdout-family",
            "seeds": [2718, 3141, 5772],
            "reproducible_directional_effect": True,
            "strongest_counterexample_recorded": True,
            "analysis_receipt_sha256": HEX64,
        },
        "transport": {
            "hosted_prompt_only": False,
            "api_served": True,
            "loopback_only": True,
            "endpoint": "http://127.0.0.1:41414/v1/jspace/logits",
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


def result() -> dict:
    return {
        "schema": binder.RESULT_SCHEMA,
        "basis_constructed_without_output_head": True,
        "terminal_output_projection_shortcut": False,
        "source": {"executor_sha256": HEX64},
        "token_ids": {"A": 10, "B": 11, "C": 12},
        "token_labels": {"A": "A", "B": "B", "C": "C"},
        "basis_receipts": [
            {"seed": 1101, "label": "A", "prompt_sha256": "1" * 64, "activation_sha256": "4" * 64},
            {"seed": 1102, "label": "B", "prompt_sha256": "2" * 64, "activation_sha256": "5" * 64},
            {"seed": 1103, "label": "C", "prompt_sha256": "3" * 64, "activation_sha256": "6" * 64},
        ],
        "holdout_rows": [
            {"prompt_sha256": "7" * 64},
            {"prompt_sha256": "8" * 64},
            {"prompt_sha256": "9" * 64},
        ],
    }


class Trigger1MidlayerCandidateV3BindTests(unittest.TestCase):
    def test_truth_binding_preserves_mechanism_but_keeps_goal_fail_closed(self):
        bound = binder.bind_candidate(result(), candidate())
        self.assertFalse(bound["vector_derivation"]["uses_output_head_weights"])
        self.assertFalse(bound["vector_derivation"]["uses_holdout_data"])
        self.assertTrue(bound["vector_derivation"]["uses_evaluation_output_labels"])
        self.assertTrue(bound["holdout"]["evaluation_independent_of_vector_derivation"])
        self.assertTrue(bound["holdout"]["metric_uses_output_tokens"])
        self.assertFalse(bound["holdout"]["label_mapping_counterbalanced"])

        verdict = gate.adjudicate(bound)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        failures = set(verdict["scientific_independence_failures"])
        self.assertIn("TOKEN_OUTPUT_METRIC_REQUIRES_COUNTERBALANCED_LABEL_MAPPING", failures)
        # Promotion-gate v4 adds the stronger label-identity independence law. Keep
        # this regression successor-compatible while the branch may still contain v3.
        if getattr(gate, "VERDICT_SCHEMA", "").endswith("/v4"):
            self.assertIn("VECTOR_DERIVATION_MUST_NOT_USE_EVALUATION_OUTPUT_LABELS", failures)

    def test_derivation_holdout_prompt_overlap_fails_closed(self):
        observed = result()
        observed["holdout_rows"][0]["prompt_sha256"] = observed["basis_receipts"][0]["prompt_sha256"]
        with self.assertRaisesRegex(binder.TruthBindingError, "VECTOR_DERIVATION_HOLDOUT_PROMPT_OVERLAP"):
            binder.bind_candidate(observed, candidate())

    def test_output_head_basis_claim_cannot_be_upgraded(self):
        observed = result()
        observed["basis_constructed_without_output_head"] = False
        with self.assertRaisesRegex(binder.TruthBindingError, "OUTPUT_HEAD_INDEPENDENT_BASIS_NOT_PROVEN"):
            binder.bind_candidate(observed, candidate())

    def test_terminal_intervention_cannot_be_upgraded(self):
        observed = result()
        observed["terminal_output_projection_shortcut"] = True
        with self.assertRaisesRegex(binder.TruthBindingError, "NONTERMINAL_INTERVENTION_REQUIRED"):
            binder.bind_candidate(observed, candidate())

    def test_missing_current_label_identity_coupling_does_not_get_invented(self):
        observed = result()
        for row, label in zip(observed["basis_receipts"], ("X", "Y", "Z")):
            row["label"] = label
        with self.assertRaisesRegex(binder.TruthBindingError, "EXPECTED_CURRENT_LABEL_IDENTITY_COUPLING_NOT_OBSERVED"):
            binder.bind_candidate(observed, candidate())


if __name__ == "__main__":
    unittest.main()
