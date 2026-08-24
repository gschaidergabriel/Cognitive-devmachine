from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_semantic_counterbalance_v1 as semantic


def load_gate():
    path = TOOLS / "trigger1_jspace_promotion_gate.py"
    spec = importlib.util.spec_from_file_location("trigger1_jspace_promotion_gate", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def fake_candidate():
    contract = semantic.validate_contract()
    meta = semantic.scientific_independence_metadata("a" * 64)
    holdout = {
        "family_id": contract["holdout_family_id"],
        "seeds": [6101, 6102, 6103],
        "reproducible_directional_effect": True,
        "strongest_counterexample_recorded": True,
        "analysis_receipt_sha256": "b" * 64,
        **meta["holdout_science"],
    }
    controls = {
        name: {"runtime_receipt_sha256": f"{i + 1:x}" * 64}
        for i, name in enumerate((
            "BASELINE",
            "+VECTOR",
            "SIGN_FLIP",
            "NULL_VECTOR",
            "ORTHOGONAL_SAME_NORM",
            "PERMUTED_SAME_NORM",
        ))
    }
    return {
        "schema": "CLAY_TRIGGER1_JSPACE_DIRECT_STEERING_CANDIDATE/v1",
        "runtime_intervention_class": "LOCAL_PYTORCH_ACTIVATION_INTERVENTION",
        "source_identity": {
            "repo_head": "1" * 40,
            "runtime_build_sha256": "2" * 64,
            "checkpoint_sha256": "3" * 64,
            "tokenizer_sha256": "4" * 64,
        },
        "intervention": {
            "runtime_observed": True,
            "invocation_id": "semantic-counterbalanced-test",
            "activation_site": "model.model.layers[14]:output:last_token",
            "source_packet_sha256": "5" * 64,
            "adapter_sha256": "6" * 64,
            "local_vector_sha256": "7" * 64,
            "applied_vector_sha256": "8" * 64,
            "runtime_intervention_receipt_sha256": "9" * 64,
            "gain": 1.0,
            "layer_start": 14,
            "layer_end": 14,
            "terminal_output_projection_shortcut": False,
        },
        "controls": controls,
        "calibration": {
            "family_id": contract["calibration_family_id"],
            "seeds": [5101, 5102, 5103],
        },
        "holdout": holdout,
        "vector_derivation": meta["vector_derivation"],
        "transport": {
            "hosted_prompt_only": False,
            "api_served": True,
            "loopback_only": True,
            "endpoint": "http://127.0.0.1:12345/v1/jspace/logits",
        },
        "target": {
            "relation": "ZERO_COST_API_SERVED_MODEL_RUNTIME",
            "execution_surface": "LOCAL_LOOPBACK_API",
            "zero_provider_billing": True,
            "local_runtime_execution_receipt_sha256": "c" * 64,
            "provider": "local",
            "model_or_route": "Qwen/Qwen3-0.6B@pinned-test-revision",
        },
    }


class TestSemanticCounterbalance(unittest.TestCase):
    def test_contract_is_balanced_and_disjoint(self):
        row = semantic.validate_contract()
        self.assertTrue(row["pass"], row["failures"])
        self.assertEqual(row["calibration_label_counts"], {"A": 2, "B": 2, "C": 2})
        self.assertEqual(row["holdout_label_counts"], {"A": 2, "B": 2, "C": 2})
        self.assertNotEqual(row["derivation_family_id"], row["holdout_family_id"])
        self.assertNotEqual(row["calibration_family_id"], row["holdout_family_id"])

    def test_independence_metadata_is_truthful_by_construction(self):
        meta = semantic.scientific_independence_metadata("d" * 64)
        derivation = meta["vector_derivation"]
        holdout = meta["holdout_science"]
        self.assertFalse(derivation["uses_output_head_weights"])
        self.assertFalse(derivation["uses_holdout_data"])
        self.assertFalse(derivation["uses_evaluation_output_labels"])
        self.assertTrue(holdout["evaluation_independent_of_vector_derivation"])
        self.assertTrue(holdout["metric_uses_output_tokens"])
        self.assertTrue(holdout["label_mapping_counterbalanced"])
        for item in (*semantic.DERIVATION_POSITIVE, *semantic.DERIVATION_NEGATIVE):
            self.assertEqual(len(item), 2, "derivation tuples must not carry an output-label identity")

    def test_score_follows_rotated_semantic_target_not_fixed_A(self):
        self.assertEqual(semantic.score_token_logits({"A": 1.0, "B": 5.0, "C": 2.0}, "B"), 3.5)
        self.assertEqual(semantic.score_token_logits({"A": 5.0, "B": 1.0, "C": 2.0}, "A"), 3.5)
        self.assertEqual(semantic.score_token_logits({"A": 2.0, "B": 1.0, "C": 5.0}, "C"), 3.5)

    def test_current_promotion_gate_v4_accepts_scientific_contract_shape(self):
        gate = load_gate()
        verdict = gate.adjudicate(fake_candidate())
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"], verdict)
        self.assertTrue(verdict["scientifically_independent_vector_candidate"], verdict)
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"], verdict)
        self.assertFalse(verdict["canonical_credit_minted"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])

    def test_gate_rejects_non_counterbalanced_token_metric(self):
        gate = load_gate()
        candidate = fake_candidate()
        candidate["holdout"]["label_mapping_counterbalanced"] = False
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn(
            "TOKEN_OUTPUT_METRIC_REQUIRES_COUNTERBALANCED_LABEL_MAPPING",
            verdict["scientific_independence_failures"],
        )

    def test_successor_executor_wires_semantic_metadata_and_metric(self):
        source = (TOOLS / "trigger1_local_qwen06_semantic_counterbalanced_execute.py").read_text(encoding="utf-8")
        self.assertIn("semantic.score_token_logits", source)
        self.assertIn('"vector_derivation": independence["vector_derivation"]', source)
        self.assertIn('**independence["holdout_science"]', source)
        self.assertNotIn('raw = means["A"]', source)


if __name__ == "__main__":
    unittest.main()
