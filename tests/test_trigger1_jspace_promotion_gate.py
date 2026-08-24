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
TREE40 = "c" * 40
MODEL = "Qwen/Qwen3-0.6B"
REVISION = "d" * 40
ENDPOINT = "http://127.0.0.1:8089/v1/jspace/logits"


def valid_candidate() -> dict:
    controls = {name: {"runtime_receipt_sha256": HEX64} for name in gate.REQUIRED_CONTROLS}
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
            "relation": gate.LEGACY_OWNER_API_TARGET_CLASS,
            "typed_free_lane_admitted": True,
            "free_lane_execution_receipt_sha256": HEX64,
            "provider": "example-free-provider",
            "model_or_route": "exact-model",
        },
    }


def valid_local_api_pair() -> tuple[dict, dict]:
    candidate = valid_candidate()
    candidate["runtime_intervention_class"] = "LOCAL_PYTORCH_ACTIVATION_INTERVENTION"
    candidate["transport"] = {
        "hosted_prompt_only": False,
        "api_served": True,
        "loopback_only": True,
        "endpoint": ENDPOINT,
    }
    candidate["target"] = {
        "relation": gate.OWNER_API_TARGET_CLASS,
        "execution_surface": gate.LOCAL_API_SURFACE,
        "zero_provider_billing": True,
        "local_runtime_execution_receipt_sha256": HEX64,
        "provider": "local",
        "model_or_route": f"{MODEL}@{REVISION}",
    }
    calibration_rows = [
        {"control": "BASELINE", "runtime_receipt_sha256": "1" * 64},
        {"control": "+VECTOR", "runtime_receipt_sha256": "2" * 64},
        {"control": "SIGN_FLIP", "runtime_receipt_sha256": "3" * 64},
    ]
    holdout_rows = []
    nibble = 4
    for control in gate.REQUIRED_CONTROLS:
        receipts = []
        for _ in range(2):
            receipt = format(nibble, "x") * 64
            nibble += 1
            holdout_rows.append({"control": control, "runtime_receipt_sha256": receipt})
            receipts.append(receipt)
        candidate["controls"][control] = {
            "runtime_receipt_sha256": gate._canonical_sha(receipts),
            "observations": len(receipts),
        }
    verdict = {
        "pass": True,
        "classification": "DIRECT_LOCAL_HIDDEN_STATE_VECTOR_EFFECT_REPRODUCED",
    }
    candidate["holdout"]["analysis_receipt_sha256"] = gate._canonical_sha(
        {"verdict": verdict, "holdout_receipts": [row["runtime_receipt_sha256"] for row in holdout_rows]}
    )
    result = {
        "schema": gate.LOCAL_RESULT_SCHEMA,
        "status": "PASS",
        "source": {"repo_head": HEAD40, "repo_tree": TREE40},
        "model": MODEL,
        "model_revision": REVISION,
        "checkpoint_sha256": HEX64,
        "tokenizer_sha256": HEX64,
        "runtime_build_sha256": HEX64,
        "api_endpoint": ENDPOINT,
        "api_loopback_only": True,
        "zero_provider_billing": True,
        "external_provider_credentials_read": False,
        "calibration_rows": calibration_rows,
        "holdout_rows": holdout_rows,
        "verdict": verdict,
    }
    candidate["target"]["local_runtime_execution_receipt_sha256"] = gate._canonical_sha(
        {
            "endpoint": ENDPOINT,
            "runtime_build_sha256": HEX64,
            "checkpoint_sha256": HEX64,
            "tokenizer_sha256": HEX64,
            "source": result["source"],
            "api_invocations": len(calibration_rows) + len(holdout_rows),
        }
    )
    result["result_sha256"] = gate._canonical_sha(result)
    return candidate, result


class Trigger1PromotionGateTests(unittest.TestCase):
    def test_exact_instrumented_free_external_api_candidate_can_reach_both_candidate_verdicts(self):
        verdict = gate.adjudicate(valid_candidate())
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])

    def test_local_opaque_hash_without_runtime_result_fails_closed(self):
        candidate, _ = valid_local_api_pair()
        verdict = gate.adjudicate(candidate)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("LOCAL_RUNTIME_RESULT_REQUIRED", verdict["owner_target_failures"])

    def test_exact_local_runtime_sidecar_can_reach_goal_candidate(self):
        candidate, result = valid_local_api_pair()
        verdict = gate.adjudicate(candidate, local_runtime_result=result)
        self.assertTrue(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertEqual([], verdict["owner_target_failures"])

    def test_forged_local_runtime_receipt_hash_fails_closed(self):
        candidate, result = valid_local_api_pair()
        candidate["target"]["local_runtime_execution_receipt_sha256"] = "f" * 64
        verdict = gate.adjudicate(candidate, local_runtime_result=result)
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("LOCAL_RUNTIME_EXECUTION_RECEIPT_MISMATCH", verdict["owner_target_failures"])

    def test_mutated_local_source_head_fails_closed(self):
        candidate, result = valid_local_api_pair()
        result["source"]["repo_head"] = "e" * 40
        result["result_sha256"] = gate._canonical_sha({k: v for k, v in result.items() if k != "result_sha256"})
        verdict = gate.adjudicate(candidate, local_runtime_result=result)
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("LOCAL_RUNTIME_SOURCE_HEAD_MISMATCH", verdict["owner_target_failures"])

    def test_mutated_result_after_self_hash_fails_closed(self):
        candidate, result = valid_local_api_pair()
        result["device"] = "forged-after-hash"
        verdict = gate.adjudicate(candidate, local_runtime_result=result)
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("LOCAL_RUNTIME_RESULT_SHA256_MISMATCH", verdict["owner_target_failures"])

    def test_missing_local_control_observations_fail_closed(self):
        candidate, result = valid_local_api_pair()
        result["holdout_rows"] = [row for row in result["holdout_rows"] if row["control"] != "ORTHOGONAL_SAME_NORM"]
        result["result_sha256"] = gate._canonical_sha({k: v for k, v in result.items() if k != "result_sha256"})
        verdict = gate.adjudicate(candidate, local_runtime_result=result)
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("LOCAL_RUNTIME_CONTROL_OBSERVATIONS_REQUIRED:ORTHOGONAL_SAME_NORM", verdict["owner_target_failures"])

    def test_terminal_output_projection_shortcut_fails_mechanism_and_goal(self):
        candidate, result = valid_local_api_pair()
        candidate["intervention"]["activation_site"] = "model.model.norm:output:last_token"
        verdict = gate.adjudicate(candidate, local_runtime_result=result)
        self.assertFalse(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("TERMINAL_OUTPUT_PROJECTION_SHORTCUT_NOT_JSPACE_CAUSAL_EVIDENCE", verdict["failures"])

    def test_declared_terminal_output_projection_shortcut_fails_closed(self):
        candidate, result = valid_local_api_pair()
        candidate["intervention"]["terminal_output_projection_shortcut"] = True
        verdict = gate.adjudicate(candidate, local_runtime_result=result)
        self.assertFalse(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("TERMINAL_OUTPUT_PROJECTION_SHORTCUT_NOT_JSPACE_CAUSAL_EVIDENCE", verdict["failures"])

    def test_hosted_prompt_only_fails_closed(self):
        candidate = valid_candidate()
        candidate["transport"]["hosted_prompt_only"] = True
        candidate["runtime_intervention_class"] = "HOSTED_TEXT_API"
        verdict = gate.adjudicate(candidate)
        self.assertFalse(verdict["mechanism_runtime_vector_credit_candidate"])
        self.assertIn("HOSTED_PROMPT_ONLY_CANNOT_PROVE_VECTOR_STEERING", verdict["failures"])

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

    def test_batch_scan_requires_and_reads_local_runtime_sidecar(self):
        candidate, result = valid_local_api_pair()
        with tempfile.TemporaryDirectory() as tmp:
            lane = Path(tmp) / "lane"
            lane.mkdir()
            (lane / "trigger1_direct_steering_candidate.json").write_text(json.dumps(candidate), encoding="utf-8")
            (lane / gate.LOCAL_RESULT_FILENAME).write_text(json.dumps(result), encoding="utf-8")
            scan = gate.scan_batch(Path(tmp))
        self.assertEqual(scan["candidate_files_seen"], 1)
        self.assertTrue(scan["mechanism_runtime_vector_credit_candidate"])
        self.assertTrue(scan["owner_trigger1_goal_credit_candidate"])

    def test_batch_scan_without_sidecar_keeps_goal_credit_zero(self):
        candidate, _ = valid_local_api_pair()
        with tempfile.TemporaryDirectory() as tmp:
            lane = Path(tmp) / "lane"
            lane.mkdir()
            (lane / "trigger1_direct_steering_candidate.json").write_text(json.dumps(candidate), encoding="utf-8")
            scan = gate.scan_batch(Path(tmp))
        self.assertEqual(scan["candidate_files_seen"], 1)
        self.assertTrue(scan["mechanism_runtime_vector_credit_candidate"])
        self.assertFalse(scan["owner_trigger1_goal_credit_candidate"])


if __name__ == "__main__":
    unittest.main()
