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
DERIVATION_PROMPTS = ["1" * 64, "2" * 64]


def _holdout_rows() -> list[dict]:
    rows: list[dict] = []
    cases = (
        ("MAP_AB", "A", "B", "3" * 64, 2718),
        ("MAP_BA", "B", "A", "4" * 64, 3141),
    )
    for label_map_id, positive_label, negative_label, prompt_sha, seed in cases:
        for control in bridge.REQUIRED_CONTROLS:
            rows.append(
                {
                    "split": "holdout",
                    "case_id": f"hold-{seed}",
                    "label_map_id": label_map_id,
                    "positive_label": positive_label,
                    "negative_label": negative_label,
                    "prompt_sha256": prompt_sha,
                    "seed": seed,
                    "control": control,
                    "runtime_receipt_sha256": HEX64,
                    "hook_calls": 1,
                    "applied_vector_sha256": HEX64,
                    **(
                        {
                            "wrong_layer_delta": -0.1,
                            "lesion_delta": -0.1,
                            "rescue_delta": 0.2,
                        }
                        if control == "+VECTOR"
                        else {}
                    ),
                }
            )
    return rows


def valid_inputs() -> tuple[dict, dict]:
    family = bridge.digest(DERIVATION_PROMPTS)
    verdict = {
        "pass": True,
        "classification": "INTERMEDIATE_REPRESENTATION_CAUSAL_CANDIDATE",
        "counterbalanced_label_mapping": True,
        "wrong_layer_evidence_complete": True,
        "wrong_layer_ok": True,
        "lesion_rescue_evidence_complete": True,
        "lesion_rescue_ok": True,
    }
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
                {"prompt_sha256": DERIVATION_PROMPTS[0]},
                {"prompt_sha256": DERIVATION_PROMPTS[1]},
            ],
            "directions": {"12": {"direction_sha256": HEX64}},
            "label_independence": {
                "schema": bridge.LABEL_INDEPENDENCE_SCHEMA,
                "derivation_input_family_sha256": family,
                "evaluation_output_labels_resolved_before_derivation": False,
                "uses_evaluation_output_labels": False,
                "construction": "semantic activations before output-label resolution",
            },
        },
        "calibration_rows": [
            {"prompt_sha256": "5" * 64, "seed": 1701, "split": "calibration"}
        ],
        "holdout_rows": _holdout_rows(),
        "verdict": verdict,
        "api_endpoint": "http://127.0.0.1:18081/v1/jspace/intermediate",
        "api_loopback_only": True,
        "zero_provider_billing": True,
        "external_provider_credentials_read": False,
        "provider_network_calls": 0,
    }
    intermediate = {
        "schema": bridge.INTERMEDIATE_CANDIDATE_SCHEMA,
        "candidate_sha256": HEX64,
        "verdict": verdict,
    }
    return result, intermediate


class Trigger1IntermediateLabelIndependenceTests(unittest.TestCase):
    def test_proven_false_survives_bridge_and_promotion_gate(self):
        result, intermediate = valid_inputs()
        direct = bridge.build_direct_candidate(result, intermediate)
        self.assertIs(
            direct["vector_derivation"]["uses_evaluation_output_labels"], False
        )
        self.assertEqual(
            64,
            len(direct["vector_derivation"]["label_independence_receipt_sha256"]),
        )
        verdict = gate.adjudicate(direct)
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])

    def test_missing_upstream_independence_receipt_blocks_bridge(self):
        result, intermediate = valid_inputs()
        del result["derivation"]["label_independence"]
        with self.assertRaisesRegex(
            bridge.BridgeError, "DERIVATION_LABEL_INDEPENDENCE_RECEIPT_REQUIRED"
        ):
            bridge.build_direct_candidate(result, intermediate)

    def test_true_upstream_label_use_blocks_bridge(self):
        result, intermediate = valid_inputs()
        result["derivation"]["label_independence"]["uses_evaluation_output_labels"] = True
        with self.assertRaisesRegex(
            bridge.BridgeError, "DERIVATION_MUST_PROVE_EVALUATION_LABEL_INDEPENDENCE"
        ):
            bridge.build_direct_candidate(result, intermediate)

    def test_tampered_derivation_family_blocks_bridge(self):
        result, intermediate = valid_inputs()
        result["derivation"]["label_independence"]["derivation_input_family_sha256"] = HEX64
        with self.assertRaisesRegex(
            bridge.BridgeError, "DERIVATION_LABEL_INDEPENDENCE_FAMILY_MISMATCH"
        ):
            bridge.build_direct_candidate(result, intermediate)

    def test_label_resolution_before_derivation_blocks_bridge(self):
        result, intermediate = valid_inputs()
        result["derivation"]["label_independence"][
            "evaluation_output_labels_resolved_before_derivation"
        ] = True
        with self.assertRaisesRegex(
            bridge.BridgeError, "DERIVATION_MUST_PRECEDE_EVALUATION_LABEL_RESOLUTION"
        ):
            bridge.build_direct_candidate(result, intermediate)


if __name__ == "__main__":
    unittest.main()
