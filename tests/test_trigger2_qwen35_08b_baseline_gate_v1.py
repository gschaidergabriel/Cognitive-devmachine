from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger2_qwen35_08b_baseline_gate_v1 as gate

SHA = "a" * 64


def candidate(model: str, *, adapt: float | None = None) -> dict:
    packet = {
        "schema": gate.SCHEMA,
        "model_id": model,
        "identity": {
            "checkpoint_manifest_sha256": SHA,
            "tokenizer_sha256": SHA,
            "config_sha256": SHA,
        },
        "runtime": {
            "local_zero_cost_attested": True,
            "name": "hf-reference",
            "revision": "r1",
            "build_digest": "build",
            "device_class": "cpu",
            "dtype_or_quantization": "bf16",
        },
        "metrics": {
            "schema_exact": 0.99,
            "arithmetic_logic": 0.90,
            "language_en": 0.90,
            "language_de": 0.80,
            "authority_fail_closed": 1.0,
            "uncertainty_abstention": 0.95,
            "tool_protocol": 0.90,
            "hyperposition_keep_open": 0.55,
            "jspace_packet_comprehension": 0.50,
            "grf_projection": 0.50,
            "offdomain_generalist_accuracy": 0.80,
            "offdomain_confident_wrong_rate": 0.20,
            "reference_runtime_pass": True,
        },
        "efficiency": {
            "latency_ms": 100.0,
            "peak_rss_mb": 1000.0,
            "tokens_per_second": 10.0,
        },
    }
    if adapt is not None:
        packet["adaptation_proxy"] = {
            "measured": True,
            "weight_update_persisted": False,
            "score": adapt,
        }
    return packet


def pair(first: dict, second: dict) -> dict:
    return {"schema": gate.PAIR_SCHEMA, "candidates": [first, second]}


class Trigger2BaselineGateTests(unittest.TestCase):
    def test_no_model_selection_before_adaptation_proxy(self):
        result = gate.analyze(
            pair(candidate("Qwen/Qwen3.5-0.8B-Base"), candidate("Qwen/Qwen3.5-0.8B"))
        )
        self.assertEqual("NO_SELECTION_ADAPTATION_PROXY_PENDING", result["decision"])
        self.assertIsNone(result["selected_model_candidate"])
        self.assertFalse(result["training_job_authorized"])

    def test_hard_floor_failure_cannot_be_rescued_by_high_adaptation(self):
        base = candidate("Qwen/Qwen3.5-0.8B-Base", adapt=1.0)
        post = candidate("Qwen/Qwen3.5-0.8B", adapt=0.1)
        base["metrics"]["authority_fail_closed"] = 0.2
        result = gate.analyze(pair(base, post))
        self.assertEqual("NO_SELECTION_HARD_FLOOR_FAILURE", result["decision"])
        self.assertIsNone(result["selected_model_candidate"])

    def test_base_can_become_selection_candidate_only_after_all_gates(self):
        result = gate.analyze(
            pair(
                candidate("Qwen/Qwen3.5-0.8B-Base", adapt=0.90),
                candidate("Qwen/Qwen3.5-0.8B", adapt=0.50),
            )
        )
        self.assertEqual("SELECTION_CANDIDATE", result["decision"])
        self.assertEqual("Qwen/Qwen3.5-0.8B-Base", result["selected_model_candidate"])
        self.assertFalse(result["paid_execution_authorized"])
        self.assertEqual(0, result["training_credit"])

    def test_small_score_gap_remains_unresolved(self):
        result = gate.analyze(
            pair(
                candidate("Qwen/Qwen3.5-0.8B-Base", adapt=0.60),
                candidate("Qwen/Qwen3.5-0.8B", adapt=0.60),
            )
        )
        self.assertEqual("NO_SELECTION_SCORE_GAP_BELOW_PREREGISTERED_MARGIN", result["decision"])
        self.assertIsNone(result["selected_model_candidate"])

    def test_non_target_model_is_rejected(self):
        bad = candidate("Qwen/Qwen3-0.6B", adapt=0.9)
        with self.assertRaisesRegex(ValueError, "MODEL_NOT_TRIGGER2_QWEN35_08B"):
            gate.analyze(pair(bad, candidate("Qwen/Qwen3.5-0.8B", adapt=0.5)))

    def test_adaptation_proxy_must_not_persist_weight_update(self):
        base = candidate("Qwen/Qwen3.5-0.8B-Base")
        base["adaptation_proxy"] = {
            "measured": True,
            "weight_update_persisted": True,
            "score": 0.9,
        }
        with self.assertRaisesRegex(ValueError, "MUST_NOT_PERSIST_WEIGHT_UPDATE"):
            gate.analyze(pair(base, candidate("Qwen/Qwen3.5-0.8B", adapt=0.5)))

    def test_pair_requires_base_and_posttrained_exactly_once(self):
        same = candidate("Qwen/Qwen3.5-0.8B-Base", adapt=0.5)
        with self.assertRaisesRegex(ValueError, "BASE_AND_POSTTRAINED_BOTH_REQUIRED"):
            gate.analyze(pair(same, copy.deepcopy(same)))


if __name__ == "__main__":
    unittest.main()
