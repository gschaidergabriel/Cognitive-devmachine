from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate as base_gate
import trigger1_jspace_runtime_result_gate as gate

HEAD = "1" * 40
RUNTIME = "2" * 64
CHECKPOINT = "3" * 64
TOKENIZER = "4" * 64
SOURCE_PACKET = "5" * 64
ADAPTER = "6" * 64
LOCAL_VECTOR = "7" * 64
APPLIED = "8" * 64


def pair() -> tuple[dict, dict]:
    endpoint = "http://127.0.0.1:49123/v1/jspace/logits"
    holdout_rows = []
    for idx, control in enumerate(base_gate.REQUIRED_CONTROLS):
        for seed in (2718, 3141):
            holdout_rows.append(
                {
                    "control": control,
                    "seed": seed,
                    "prompt_family": f"hold-{seed}",
                    "runtime_receipt_sha256": gate.canonical_sha([control, seed, idx]),
                    "applied_vector_sha256": APPLIED if control == "+VECTOR" else gate.canonical_sha(["vector", control]),
                    "hook_calls": 0 if control == "BASELINE" else 1,
                }
            )
    result = {
        "schema": gate.LOCAL_RESULT_SCHEMA,
        "status": "PASS",
        "source": {"repo_head": HEAD, "repo_tree": "9" * 40},
        "model": "Qwen/Qwen3-0.6B",
        "model_revision": "c1899de289a04d12100db370d81485cdf75e47ca",
        "runtime_build_sha256": RUNTIME,
        "checkpoint_sha256": CHECKPOINT,
        "tokenizer_sha256": TOKENIZER,
        "source_packet_sha256": SOURCE_PACKET,
        "adapter_sha256": ADAPTER,
        "local_vector_sha256": LOCAL_VECTOR,
        "api_endpoint": endpoint,
        "api_loopback_only": True,
        "zero_provider_billing": True,
        "external_provider_credentials_read": False,
        "calibration_rows": [{"runtime_receipt_sha256": "a" * 64}] * 3,
        "holdout_rows": holdout_rows,
        "selected_gain": 2.0,
        "verdict": {"pass": True, "classification": "DIRECT_LOCAL_HIDDEN_STATE_VECTOR_EFFECT_REPRODUCED"},
    }
    controls = {}
    for control in base_gate.REQUIRED_CONTROLS:
        receipts = [r["runtime_receipt_sha256"] for r in holdout_rows if r["control"] == control]
        controls[control] = {
            "runtime_receipt_sha256": gate.canonical_sha(receipts),
            "observations": len(receipts),
        }
    all_receipts = [r["runtime_receipt_sha256"] for r in holdout_rows]
    plus_rows = [r for r in holdout_rows if r["control"] == "+VECTOR"]
    plus_receipts = [r["runtime_receipt_sha256"] for r in plus_rows]
    analysis_sha = gate.canonical_sha({"verdict": result["verdict"], "holdout_receipts": all_receipts})
    local_runtime_sha = gate.canonical_sha(gate._runtime_receipt_material(result))
    candidate = {
        "schema": base_gate.CANDIDATE_SCHEMA,
        "runtime_intervention_class": "LOCAL_PYTORCH_ACTIVATION_INTERVENTION",
        "source_identity": {
            "repo_head": HEAD,
            "runtime_build_sha256": RUNTIME,
            "checkpoint_sha256": CHECKPOINT,
            "tokenizer_sha256": TOKENIZER,
        },
        "intervention": {
            "runtime_observed": True,
            "invocation_id": gate.canonical_sha(all_receipts),
            "activation_site": "model.model.norm:output:last_token",
            "source_packet_sha256": SOURCE_PACKET,
            "adapter_sha256": ADAPTER,
            "local_vector_sha256": LOCAL_VECTOR,
            "applied_vector_sha256": APPLIED,
            "runtime_intervention_receipt_sha256": gate.canonical_sha(plus_receipts),
            "gain": 2.0,
            "layer_start": 28,
            "layer_end": 28,
        },
        "controls": controls,
        "calibration": {"family_id": "cal-family", "seeds": [1701, 1702], "selected_gain": 2.0},
        "holdout": {
            "family_id": "hold-family",
            "seeds": [2718, 3141],
            "reproducible_directional_effect": True,
            "strongest_counterexample_recorded": True,
            "analysis_receipt_sha256": analysis_sha,
        },
        "transport": {
            "hosted_prompt_only": False,
            "api_served": True,
            "loopback_only": True,
            "endpoint": endpoint,
        },
        "target": {
            "relation": base_gate.OWNER_API_TARGET_CLASS,
            "execution_surface": base_gate.LOCAL_API_SURFACE,
            "zero_provider_billing": True,
            "local_runtime_execution_receipt_sha256": local_runtime_sha,
            "provider": "local",
            "model_or_route": f"{result['model']}@{result['model_revision']}",
        },
    }
    return candidate, result


class Trigger1RuntimeResultBindingTests(unittest.TestCase):
    def test_exact_candidate_and_runtime_result_bind(self):
        candidate, result = pair()
        verdict = gate.bind(candidate, result)
        self.assertTrue(verdict["runtime_result_binding_pass"])
        self.assertTrue(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertEqual([], verdict["failures"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])
        self.assertFalse(verdict["training_credit"])

    def test_arbitrary_64hex_local_runtime_receipt_is_rejected(self):
        candidate, result = pair()
        candidate["target"]["local_runtime_execution_receipt_sha256"] = "f" * 64
        verdict = gate.bind(candidate, result)
        self.assertFalse(verdict["runtime_result_binding_pass"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertIn("LOCAL_RUNTIME_EXECUTION_RECEIPT_DIGEST_MISMATCH", verdict["failures"])

    def test_transplanted_checkpoint_result_is_rejected(self):
        candidate, result = pair()
        result["checkpoint_sha256"] = "e" * 64
        verdict = gate.bind(candidate, result)
        self.assertFalse(verdict["runtime_result_binding_pass"])
        self.assertIn("RESULT_IDENTITY_MISMATCH:checkpoint_sha256", verdict["failures"])
        self.assertIn("LOCAL_RUNTIME_EXECUTION_RECEIPT_DIGEST_MISMATCH", verdict["failures"])

    def test_mutated_holdout_receipt_is_rejected(self):
        candidate, result = pair()
        result = copy.deepcopy(result)
        result["holdout_rows"][0]["runtime_receipt_sha256"] = "d" * 64
        verdict = gate.bind(candidate, result)
        self.assertFalse(verdict["runtime_result_binding_pass"])
        self.assertTrue(any(x.startswith("CONTROL_RESULT_RECEIPT_MISMATCH:") for x in verdict["failures"]))
        self.assertIn("INTERVENTION_INVOCATION_RESULT_MISMATCH", verdict["failures"])
        self.assertIn("HOLDOUT_ANALYSIS_RESULT_MISMATCH", verdict["failures"])

    def test_endpoint_transplant_is_rejected(self):
        candidate, result = pair()
        result["api_endpoint"] = "http://127.0.0.1:49999/v1/jspace/logits"
        verdict = gate.bind(candidate, result)
        self.assertFalse(verdict["runtime_result_binding_pass"])
        self.assertIn("RESULT_LOOPBACK_ENDPOINT_MISMATCH", verdict["failures"])
        self.assertIn("LOCAL_RUNTIME_EXECUTION_RECEIPT_DIGEST_MISMATCH", verdict["failures"])

    def test_external_provider_candidate_cannot_use_local_binding_gate(self):
        candidate, result = pair()
        candidate["target"]["execution_surface"] = base_gate.EXTERNAL_API_SURFACE
        verdict = gate.bind(candidate, result)
        self.assertFalse(verdict["runtime_result_binding_pass"])
        self.assertIn("LOCAL_RUNTIME_RESULT_BINDING_GATE_LOCAL_ONLY", verdict["failures"])


if __name__ == "__main__":
    unittest.main()
