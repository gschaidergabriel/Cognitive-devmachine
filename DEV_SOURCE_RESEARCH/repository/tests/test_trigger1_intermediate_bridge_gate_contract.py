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
ALT64 = "c" * 64
HEAD40 = "b" * 40


def passing_inputs() -> tuple[dict, dict]:
    calibration = [
        {"prompt_sha256": "1" * 64, "seed": 1701},
        {"prompt_sha256": "2" * 64, "seed": 1702},
    ]
    holdout = []
    for label_map_id, positive_label, negative_label, prompt_sha in (
        ("MAP_AB", "A", "B", "3" * 64),
        ("MAP_BA", "B", "A", "4" * 64),
    ):
        for control in bridge.REQUIRED_CONTROLS:
            row = {
                "prompt_sha256": prompt_sha,
                "seed": 2718 if label_map_id == "MAP_AB" else 3141,
                "label_map_id": label_map_id,
                "positive_label": positive_label,
                "negative_label": negative_label,
                "control": control,
                "runtime_receipt_sha256": HEX64,
                "hook_calls": 1,
            }
            if control == "+VECTOR":
                row["applied_vector_sha256"] = ALT64
            holdout.append(row)

    verdict = {
        "pass": True,
        "classification": "INTERMEDIATE_REPRESENTATION_CAUSAL_CANDIDATE",
        "counterbalanced_label_mapping": True,
        "wrong_layer_evidence_complete": True,
        "wrong_layer_ok": True,
        "lesion_rescue_evidence_complete": True,
        "lesion_rescue_ok": True,
    }
    derivation_prompt_hashes = ["5" * 64, "6" * 64]
    result = {
        "schema": bridge.INTERMEDIATE_SCHEMA,
        "status": "PASS",
        "credit_scope": "INTERMEDIATE_REPRESENTATION_CAUSAL_CANDIDATE_ONLY",
        "source": {"repo_head": HEAD40},
        "runtime_build_sha256": HEX64,
        "checkpoint_sha256": HEX64,
        "tokenizer_sha256": HEX64,
        "model": "Qwen/Qwen3-0.6B",
        "model_revision": "exact-revision",
        "selected": {"selected": True, "layer": 12, "gain": 4.0},
        "derivation": {
            "sources": [
                {"prompt_sha256": derivation_prompt_hashes[0]},
                {"prompt_sha256": derivation_prompt_hashes[1]},
            ],
            "directions": {"12": {"direction_sha256": ALT64}},
            "label_independence": {
                "schema": bridge.LABEL_INDEPENDENCE_SCHEMA,
                "uses_evaluation_output_labels": False,
                "evaluation_output_labels_resolved_before_derivation": False,
                "derivation_input_family_sha256": bridge.digest(sorted(derivation_prompt_hashes)),
            },
        },
        "calibration_rows": calibration,
        "holdout_rows": holdout,
        "verdict": verdict,
        "api_endpoint": "http://127.0.0.1:8123/v1/jspace/intermediate",
        "api_loopback_only": True,
        "zero_provider_billing": True,
        "external_provider_credentials_read": False,
        "provider_network_calls": 0,
    }
    intermediate = {
        "schema": bridge.INTERMEDIATE_CANDIDATE_SCHEMA,
        "verdict": {"pass": True},
        "candidate_sha256": HEX64,
    }
    return result, intermediate


class Trigger1IntermediateBridgeGateContractTests(unittest.TestCase):
    def test_bridge_binds_label_independence_and_reaches_gate_v4_goal_candidate(self):
        result, intermediate = passing_inputs()
        direct = bridge.build_direct_candidate(result, intermediate)

        self.assertIs(False, direct["vector_derivation"]["uses_evaluation_output_labels"])
        self.assertEqual(
            bridge.digest(result["derivation"]["label_independence"]),
            direct["vector_derivation"]["label_independence_receipt_sha256"],
        )
        self.assertIs(True, direct["holdout"]["label_mapping_counterbalanced"])
        self.assertIs(True, direct["holdout"]["metric_uses_output_tokens"])

        verdict = gate.adjudicate(direct)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertEqual([], verdict["owner_target_failures"])
        self.assertFalse(verdict["canonical_credit_minted"])
        self.assertFalse(verdict["whole_entityos_hcu_credit"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])
        self.assertFalse(verdict["training_credit"])

    def test_missing_label_independence_receipt_blocks_bridge(self):
        result, intermediate = passing_inputs()
        del result["derivation"]["label_independence"]
        with self.assertRaisesRegex(
            bridge.BridgeError, "DERIVATION_LABEL_INDEPENDENCE_RECEIPT_REQUIRED"
        ):
            bridge.build_direct_candidate(result, intermediate)

    def test_true_evaluation_label_use_blocks_bridge(self):
        result, intermediate = passing_inputs()
        result["derivation"]["label_independence"]["uses_evaluation_output_labels"] = True
        with self.assertRaisesRegex(
            bridge.BridgeError, "DERIVATION_MUST_PROVE_EVALUATION_LABEL_INDEPENDENCE"
        ):
            bridge.build_direct_candidate(result, intermediate)

    def test_tampered_derivation_family_blocks_bridge(self):
        result, intermediate = passing_inputs()
        result["derivation"]["label_independence"]["derivation_input_family_sha256"] = HEX64
        with self.assertRaisesRegex(
            bridge.BridgeError, "DERIVATION_LABEL_INDEPENDENCE_FAMILY_MISMATCH"
        ):
            bridge.build_direct_candidate(result, intermediate)

    def test_label_resolution_before_derivation_blocks_bridge(self):
        result, intermediate = passing_inputs()
        result["derivation"]["label_independence"][
            "evaluation_output_labels_resolved_before_derivation"
        ] = True
        with self.assertRaisesRegex(
            bridge.BridgeError, "DERIVATION_MUST_PRECEDE_EVALUATION_LABEL_RESOLUTION"
        ):
            bridge.build_direct_candidate(result, intermediate)


if __name__ == "__main__":
    unittest.main()
