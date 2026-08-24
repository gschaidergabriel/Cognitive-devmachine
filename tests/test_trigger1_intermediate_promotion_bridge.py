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
DIR64 = "d" * 64
DERIVATION_PROMPT64 = "c" * 64
CAL_PROMPT64 = "e" * 64
HOLD_AB_PROMPT64 = "f" * 64
HOLD_BA_PROMPT64 = "1" * 64
HEAD40 = "b" * 40


def _holdout_rows(seed: int = 2718) -> list[dict]:
    rows: list[dict] = []
    for label_map_id, positive_label, negative_label, prompt_sha in (
        ("MAP_AB", "A", "B", HOLD_AB_PROMPT64),
        ("MAP_BA", "B", "A", HOLD_BA_PROMPT64),
    ):
        for control in bridge.REQUIRED_CONTROLS:
            rows.append(
                {
                    "prompt_sha256": prompt_sha,
                    "seed": seed,
                    "positive_label": positive_label,
                    "negative_label": negative_label,
                    "label_map_id": label_map_id,
                    "control": control,
                    "runtime_receipt_sha256": HEX64,
                    "hook_calls": 1,
                    "applied_vector_sha256": HEX64,
                }
            )
    return rows


def valid_result(*, calibration_seed: int = 1701, holdout_seed: int = 2718) -> dict:
    return {
        "schema": bridge.INTERMEDIATE_SCHEMA,
        "status": "PASS",
        "credit_scope": "INTERMEDIATE_REPRESENTATION_CAUSAL_CANDIDATE_ONLY",
        "source": {"repo_head": HEAD40},
        "model": "Qwen/Qwen3-0.6B",
        "model_revision": "c1899de289a04d12100db370d81485cdf75e47ca",
        "runtime_build_sha256": HEX64,
        "checkpoint_sha256": HEX64,
        "tokenizer_sha256": HEX64,
        "selected": {"selected": True, "layer": 12, "gain": 4.0},
        "derivation": {
            "sources": [{"prompt_sha256": DERIVATION_PROMPT64}],
            "directions": {"12": {"direction_sha256": DIR64}},
        },
        "calibration_rows": [
            {
                "prompt_sha256": CAL_PROMPT64,
                "seed": calibration_seed,
            }
        ],
        "holdout_rows": _holdout_rows(holdout_seed),
        "verdict": {
            "pass": True,
            "classification": "INTERMEDIATE_REPRESENTATION_CAUSAL_CANDIDATE",
            "counterbalanced_label_mapping": True,
            "wrong_layer_evidence_complete": True,
            "wrong_layer_ok": True,
            "lesion_rescue_evidence_complete": True,
            "lesion_rescue_ok": True,
        },
        "api_endpoint": "http://127.0.0.1:8097/v1/jspace/intermediate",
        "api_loopback_only": True,
        "zero_provider_billing": True,
        "external_provider_credentials_read": False,
        "provider_network_calls": 0,
    }


def valid_intermediate() -> dict:
    return {
        "schema": bridge.INTERMEDIATE_CANDIDATE_SCHEMA,
        "candidate_sha256": HEX64,
        "verdict": {"pass": True},
    }


class Trigger1IntermediatePromotionBridgeTests(unittest.TestCase):
    def test_bridge_candidate_reaches_v4_scientific_independence_and_goal_gate(self):
        candidate = bridge.build_direct_candidate(valid_result(), valid_intermediate())

        self.assertFalse(candidate["vector_derivation"]["uses_output_head_weights"])
        self.assertFalse(candidate["vector_derivation"]["uses_holdout_data"])
        self.assertFalse(candidate["vector_derivation"]["uses_evaluation_output_labels"])
        self.assertTrue(candidate["holdout"]["label_mapping_counterbalanced"])

        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["scientifically_independent_vector_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])

    def test_calibration_holdout_seed_overlap_fails_closed(self):
        with self.assertRaisesRegex(
            bridge.BridgeError,
            "CALIBRATION_HOLDOUT_SEEDS_MUST_BE_DISJOINT",
        ):
            bridge.build_direct_candidate(
                valid_result(calibration_seed=2718, holdout_seed=2718),
                valid_intermediate(),
            )


if __name__ == "__main__":
    unittest.main()
