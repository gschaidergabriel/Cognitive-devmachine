from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate as gate

HEX64 = "a" * 64
HEAD40 = "b" * 40


def valid_candidate() -> dict:
    controls = {
        name: {"runtime_receipt_sha256": HEX64}
        for name in gate.REQUIRED_CONTROLS
    }
    return {
        "schema": gate.CANDIDATE_SCHEMA,
        "runtime_intervention_class": "PROVIDER_RUNTIME_INTERNAL_VECTOR_INTERVENTION",
        "source_identity": {
            "repo_head": HEAD40,
            "runtime_build_sha256": HEX64,
            "checkpoint_sha256": HEX64,
            "tokenizer_sha256": HEX64,
        },
        "intervention": {
            "runtime_observed": True,
            "invocation_id": "inv-1",
            "activation_site": "layer:12/residual",
            "source_packet_sha256": HEX64,
            "adapter_sha256": HEX64,
            "local_vector_sha256": HEX64,
            "applied_vector_sha256": HEX64,
            "runtime_intervention_receipt_sha256": HEX64,
            "gain": 0.75,
            "layer_start": 10,
            "layer_end": 20,
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
        "transport": {"hosted_prompt_only": False},
        "target": {
            "relation": gate.OWNER_API_TARGET_CLASS,
            "typed_free_lane_admitted": True,
            "free_lane_execution_receipt_sha256": HEX64,
            "provider": "example-free-provider",
            "model_or_route": "exact-model",
        },
    }


class Trigger1PromotionGateTests(unittest.TestCase):
    def test_exact_instrumented_free_api_candidate_can_reach_both_candidate_verdicts(self):
        verdict = gate.adjudicate(valid_candidate())
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["owner_trigger1_direct_free_api_model_credit_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])

    def test_hosted_prompt_only_fails_closed(self):
        candidate = valid_candidate()
        candidate["transport"]["hosted_prompt_only"] = True
        candidate["runtime_intervention_class"] = "HOSTED_TEXT_API"
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_direct_free_api_model_credit_candidate"])
        self.assertIn("HOSTED_PROMPT_ONLY_CANNOT_PROVE_VECTOR_STEERING", verdict["failures"])

    def test_local_cvec_can_be_mechanism_candidate_but_not_literal_api_target(self):
        candidate = valid_candidate()
        candidate["runtime_intervention_class"] = "LOCAL_LLAMA_CPP_CVEC_APPLIED"
        candidate["target"] = {
            "relation": "LOCAL_CHECKPOINT_SURROGATE",
            "typed_free_lane_admitted": False,
            "provider": "local",
            "model_or_route": "same-family-local-checkpoint",
        }
        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_direct_free_api_model_credit_candidate"])
        self.assertIn("EXACT_ADMITTED_FREE_API_MODEL_RUNTIME_REQUIRED", verdict["owner_target_failures"])

    def test_calibration_holdout_overlap_fails_mechanism(self):
        candidate = valid_candidate()
        candidate["holdout"]["seeds"] = [2, 3]
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertIn("CALIBRATION_HOLDOUT_SEEDS_MUST_BE_DISJOINT", verdict["failures"])

    def test_missing_required_control_fails_mechanism(self):
        candidate = valid_candidate()
        del candidate["controls"]["ORTHOGONAL_SAME_NORM"]
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertIn("CONTROL_REQUIRED:ORTHOGONAL_SAME_NORM", verdict["failures"])

    def test_batch_scan_without_candidates_is_zero_credit(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = gate.scan_batch(Path(tmp))
        self.assertEqual(result["candidate_files_seen"], 0)
        self.assertFalse(result["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(result["owner_trigger1_direct_free_api_model_credit_candidate"])
        self.assertFalse(result["canonical_credit_minted"])

    def test_batch_scan_reads_candidate_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lane" / "trigger1_direct_steering_candidate.json"
            path.parent.mkdir()
            path.write_text(json.dumps(valid_candidate()), encoding="utf-8")
            result = gate.scan_batch(Path(tmp))
        self.assertEqual(result["candidate_files_seen"], 1)
        self.assertTrue(result["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(result["owner_trigger1_direct_free_api_model_credit_candidate"])


if __name__ == "__main__":
    unittest.main()
