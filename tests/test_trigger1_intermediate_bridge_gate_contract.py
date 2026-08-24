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
    semantic_cases = (
        ("positive", 2718, "3" * 64, "7" * 64),
        ("negative", 3141, "4" * 64, "8" * 64),
    )
    for label_map_id, positive_label, negative_label in (
        ("MAP_AB", "A", "B"),
        ("MAP_BA", "B", "A"),
    ):
        for polarity, seed, prompt_sha, stimulus_sha in semantic_cases:
            for control in bridge.REQUIRED_CONTROLS:
                row = {
                    "prompt_sha256": prompt_sha,
                    "seed": seed,
                    "case_id": f"semantic-{seed}-{polarity}",
                    "label_map_id": label_map_id,
                    "positive_label": positive_label,
                    "negative_label": negative_label,
                    "stimulus_polarity": polarity,
                    "stimulus_family_id": "hold-cross-domain-v1",
                    "stimulus_sha256": stimulus_sha,
                    "control": control,
                    "runtime_receipt_sha256": HEX64,
                    "hook_calls": 1,
                }
                if control == "+VECTOR":
                    row["applied_vector_sha256"] = ALT64
                holdout.append(row)

    verdict = {
        "pass": True,
        "classification": "INTERMEDIATE_SEMANTIC_REPRESENTATION_CAUSAL_CANDIDATE",
        "counterbalanced_label_mapping": True,
        "semantic_polarities": ["negative", "positive"],
        "semantic_stimulus_count": 2,
        "semantic_baseline_correct_count": 4,
        "semantic_baseline_case_count": 4,
        "semantic_baseline_min_signed_margin": 0.75,
        "wrong_layer_evidence_complete": True,
        "wrong_layer_ok": True,
        "lesion_rescue_evidence_complete": True,
        "lesion_rescue_ok": True,
    }
    semantic = {
        "derivation_family_sha256": "9" * 64,
        "calibration_family": "cal-municipal-v1",
        "calibration_stimulus_sha256": ["1" * 64, "2" * 64],
        "holdout_family": "hold-cross-domain-v1",
        "holdout_stimulus_sha256": ["7" * 64, "8" * 64],
        "holdout_polarities": ["negative", "positive"],
        "counterbalanced_label_maps": ["MAP_AB", "MAP_BA"],
        "baseline_semantic_discrimination_required": True,
    }
    result = {
        "schema": "CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v2",
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
                {"prompt_sha256": "5" * 64},
                {"prompt_sha256": "6" * 64},
            ],
            "directions": {"12": {"direction_sha256": ALT64}},
        },
        "semantic_transfer_evidence": semantic,
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
        "schema": "CLAY_TRIGGER1_INTERMEDIATE_JSPACE_CAUSAL_CANDIDATE/v2",
        "verdict": verdict,
        "semantic_transfer_evidence": semantic,
        "candidate_sha256": HEX64,
    }
    return result, intermediate


class Trigger1IntermediateBridgeGateContractTests(unittest.TestCase):
    def test_semantic_bridge_reaches_gate_v4_goal_candidate(self):
        result, intermediate = passing_inputs()
        direct = bridge.build_direct_candidate(result, intermediate)
        self.assertIs(False, direct["vector_derivation"]["uses_evaluation_output_labels"])
        self.assertIs(True, direct["holdout"]["label_mapping_counterbalanced"])
        self.assertIs(True, direct["intermediate_protocol"]["semantic_transfer"])

        verdict = gate.adjudicate(direct)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertEqual([], verdict["owner_target_failures"])
        self.assertFalse(verdict["canonical_credit_minted"])
        self.assertFalse(verdict["whole_entityos_hcu_credit"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])
        self.assertFalse(verdict["training_credit"])

    def test_historical_symbol_only_pass_fails_closed(self):
        result, intermediate = passing_inputs()
        result["verdict"] = {
            "pass": True,
            "classification": "INTERMEDIATE_REPRESENTATION_CAUSAL_CANDIDATE",
            "counterbalanced_label_mapping": True,
            "wrong_layer_evidence_complete": True,
            "wrong_layer_ok": True,
            "lesion_rescue_evidence_complete": True,
            "lesion_rescue_ok": True,
        }
        intermediate["verdict"] = result["verdict"]
        with self.assertRaisesRegex(bridge.BridgeError, "SEMANTIC_INTERMEDIATE_PROTOCOL_PASS_REQUIRED"):
            bridge.build_direct_candidate(result, intermediate)


if __name__ == "__main__":
    unittest.main()
