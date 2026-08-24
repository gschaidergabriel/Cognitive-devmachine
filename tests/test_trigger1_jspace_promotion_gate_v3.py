from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate as v2
import trigger1_jspace_promotion_gate_v3 as v3

HEX64 = "a" * 64
HEAD40 = "b" * 40
TREE40 = "c" * 40


def local_pytorch_candidate() -> dict:
    controls = {name: {"runtime_receipt_sha256": HEX64} for name in v2.REQUIRED_CONTROLS}
    return {
        "schema": v2.CANDIDATE_SCHEMA,
        "runtime_intervention_class": "LOCAL_PYTORCH_ACTIVATION_INTERVENTION",
        "source_identity": {
            "repo_head": HEAD40,
            "repo_tree": TREE40,
            "repo_dirty": False,
            "repo_dirty_state_sha256": HEX64,
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
            "gain": 2.0,
            "layer_start": 14,
            "layer_end": 14,
            "post_intervention_transform_depth": 13,
            "basis_derivation_class": v3.REQUIRED_LOCAL_BASIS_CLASS,
            "basis_source_family_id": "basis-family",
            "basis_source_seeds": [8111, 8112, 8221, 8222, 8331, 8332],
            "readout_target_weights_used": False,
            "direct_readout_algebraically_forced": False,
        },
        "controls": controls,
        "calibration": {"family_id": "cal-family", "seeds": [1701, 1702]},
        "holdout": {
            "family_id": "hold-family",
            "seeds": [2718, 3141],
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
            "relation": v2.OWNER_API_TARGET_CLASS,
            "execution_surface": v2.LOCAL_API_SURFACE,
            "zero_provider_billing": True,
            "local_runtime_execution_receipt_sha256": HEX64,
            "provider": "local",
            "model_or_route": "Qwen/Qwen3-0.6B@exact",
        },
    }


class Trigger1PromotionGateV3Tests(unittest.TestCase):
    def test_disjoint_midlayer_basis_can_reach_owner_goal_candidate(self):
        verdict = v3.adjudicate(local_pytorch_candidate())
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["scientific_identification_ok"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])

    def test_v2_shaped_local_candidate_is_mechanism_only(self):
        candidate = local_pytorch_candidate()
        for key in (
            "post_intervention_transform_depth",
            "basis_derivation_class",
            "basis_source_family_id",
            "basis_source_seeds",
            "readout_target_weights_used",
            "direct_readout_algebraically_forced",
        ):
            candidate["intervention"].pop(key)
        base_verdict = v2.adjudicate(candidate)
        verdict = v3.adjudicate(candidate)
        self.assertTrue(base_verdict["owner_trigger1_goal_credit_candidate"])
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("DISJOINT_HIDDEN_ACTIVATION_BASIS_REQUIRED", verdict["scientific_identification_failures"])

    def test_lm_head_derived_basis_fails_owner_goal(self):
        candidate = local_pytorch_candidate()
        candidate["intervention"]["basis_derivation_class"] = "DIRECT_LM_HEAD_TARGET_CONTRAST"
        candidate["intervention"]["readout_target_weights_used"] = True
        candidate["intervention"]["direct_readout_algebraically_forced"] = True
        verdict = v3.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("LM_HEAD_TARGET_WEIGHT_DERIVATION_FORBIDDEN_FOR_GOAL_CREDIT", verdict["scientific_identification_failures"])
        self.assertIn("DIRECT_READOUT_ALGEBRAIC_EFFECT_MUST_BE_FALSE", verdict["scientific_identification_failures"])

    def test_final_readout_without_downstream_depth_fails(self):
        candidate = local_pytorch_candidate()
        candidate["intervention"]["activation_site"] = "model.model.norm:output:last_token"
        candidate["intervention"]["post_intervention_transform_depth"] = 0
        verdict = v3.adjudicate(candidate)
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("POST_INTERVENTION_TRANSFORM_DEPTH_REQUIRED", verdict["scientific_identification_failures"])

    def test_basis_seed_overlap_fails(self):
        candidate = local_pytorch_candidate()
        candidate["intervention"]["basis_source_seeds"] = [1701, 8112]
        verdict = v3.adjudicate(candidate)
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("BASIS_CALIBRATION_HOLDOUT_SEEDS_MUST_BE_DISJOINT", verdict["scientific_identification_failures"])

    def test_dirty_source_remains_mechanism_only(self):
        candidate = local_pytorch_candidate()
        candidate["source_identity"]["repo_dirty"] = True
        verdict = v3.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("CLEAN_TRACKED_SOURCE_REQUIRED_FOR_OWNER_GOAL_CREDIT", verdict["scientific_identification_failures"])


if __name__ == "__main__":
    unittest.main()
