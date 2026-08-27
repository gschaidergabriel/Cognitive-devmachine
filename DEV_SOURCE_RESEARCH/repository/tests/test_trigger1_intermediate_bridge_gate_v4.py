from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_intermediate_promotion_bridge as bridge
import trigger1_jspace_promotion_gate as gate

HEX64 = "a" * 64
HEAD40 = "b" * 40


def _holdout_rows() -> list[dict]:
    rows: list[dict] = []
    for seed, label_map_id, positive_label, negative_label, prompt_sha in (
        (2718, "MAP_AB", "A", "B", "1" * 64),
        (3141, "MAP_BA", "B", "A", "2" * 64),
    ):
        for control in bridge.REQUIRED_CONTROLS:
            row = {
                "seed": seed,
                "prompt_sha256": prompt_sha,
                "label_map_id": label_map_id,
                "positive_label": positive_label,
                "negative_label": negative_label,
                "control": control,
                "runtime_receipt_sha256": HEX64,
            }
            if control == "+VECTOR":
                row["hook_calls"] = 1
                row["applied_vector_sha256"] = "c" * 64
            rows.append(row)
    return rows


def _derivation() -> dict:
    sources = [
        {"polarity": "positive", "prompt_sha256": "6" * 64},
        {"polarity": "negative", "prompt_sha256": "7" * 64},
    ]
    prompt_hashes = sorted(row["prompt_sha256"] for row in sources)
    return {
        "sources": sources,
        "directions": {"12": {"direction_sha256": "8" * 64}},
        "label_independence": {
            "schema": bridge.LABEL_INDEPENDENCE_SCHEMA,
            "derivation_input_family_sha256": bridge.digest(prompt_hashes),
            "evaluation_output_labels_resolved_before_derivation": False,
            "uses_evaluation_output_labels": False,
            "construction": "fixed semantic positive/negative intermediate activations only; output-label resolution occurs after derivation",
        },
    }


def _result() -> dict:
    verdict = {
        "pass": True,
        "classification": "INTERMEDIATE_DIRECTIONAL_EFFECT_WITH_COUNTERBALANCED_CONTROLS",
        "counterbalanced_label_mapping": True,
        "wrong_layer_evidence_complete": True,
        "wrong_layer_ok": True,
        "lesion_rescue_evidence_complete": True,
        "lesion_rescue_ok": True,
    }
    return {
        "schema": bridge.INTERMEDIATE_SCHEMA,
        "status": "PASS",
        "credit_scope": "INTERMEDIATE_REPRESENTATION_CAUSAL_CANDIDATE_ONLY",
        "source": {"repo_head": HEAD40, "repo_tree": "d" * 40},
        "model": "Qwen/Qwen3-0.6B",
        "model_revision": "e" * 40,
        "runtime_build_sha256": "3" * 64,
        "checkpoint_sha256": "4" * 64,
        "tokenizer_sha256": "5" * 64,
        "selected": {"selected": True, "layer": 12, "gain": 4.0},
        "derivation": _derivation(),
        "calibration_rows": [{"seed": 1701, "prompt_sha256": "9" * 64}],
        "holdout_rows": _holdout_rows(),
        "verdict": verdict,
        "api_endpoint": "http://127.0.0.1:18181/v1/jspace/intermediate",
        "api_loopback_only": True,
        "zero_provider_billing": True,
        "external_provider_credentials_read": False,
        "provider_network_calls": 0,
    }


def _intermediate() -> dict:
    return {
        "schema": bridge.INTERMEDIATE_CANDIDATE_SCHEMA,
        "candidate_sha256": "f" * 64,
        "verdict": {"pass": True},
    }


class IntermediateBridgeGateV4Tests(unittest.TestCase):
    def test_proven_upstream_label_independence_survives_bridge_and_gate_v4(self):
        candidate = bridge.build_direct_candidate(_result(), _intermediate())
        derivation = candidate["vector_derivation"]
        self.assertIs(derivation["uses_evaluation_output_labels"], False)
        self.assertEqual(64, len(derivation["label_independence_receipt_sha256"]))

        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertEqual([], verdict["scientific_independence_failures"])

    def test_missing_upstream_label_independence_receipt_blocks_at_bridge(self):
        result = _result()
        result["derivation"].pop("label_independence")
        with self.assertRaisesRegex(bridge.BridgeError, "DERIVATION_LABEL_INDEPENDENCE_RECEIPT_REQUIRED"):
            bridge.build_direct_candidate(result, _intermediate())

    def test_true_upstream_label_use_blocks_at_bridge(self):
        result = _result()
        result["derivation"]["label_independence"]["uses_evaluation_output_labels"] = True
        with self.assertRaisesRegex(bridge.BridgeError, "DERIVATION_MUST_PROVE_EVALUATION_LABEL_INDEPENDENCE"):
            bridge.build_direct_candidate(result, _intermediate())

    def test_mismatched_derivation_family_blocks_at_bridge(self):
        result = _result()
        result["derivation"]["label_independence"]["derivation_input_family_sha256"] = "0" * 64
        with self.assertRaisesRegex(bridge.BridgeError, "DERIVATION_LABEL_INDEPENDENCE_FAMILY_MISMATCH"):
            bridge.build_direct_candidate(result, _intermediate())

    def test_gate_v4_still_rejects_direct_candidate_if_proven_field_is_removed_after_bridge(self):
        candidate = bridge.build_direct_candidate(_result(), _intermediate())
        candidate["vector_derivation"].pop("uses_evaluation_output_labels")

        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn(
            "VECTOR_DERIVATION_MUST_NOT_USE_EVALUATION_OUTPUT_LABELS",
            verdict["scientific_independence_failures"],
        )


if __name__ == "__main__":
    unittest.main()
