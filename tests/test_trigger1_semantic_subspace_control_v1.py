from __future__ import annotations

from copy import deepcopy
import hashlib
import math
from pathlib import Path
import struct
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_semantic_simplex_blocked_rank_v1 as ranker
import trigger1_semantic_subspace_control_v1 as controller


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def code_map(i: int) -> dict[str, str]:
    rotations = [
        {"AFFIRMATIVE": "A", "NEGATIVE": "B", "NEUTRAL": "C"},
        {"AFFIRMATIVE": "B", "NEGATIVE": "C", "NEUTRAL": "A"},
        {"AFFIRMATIVE": "C", "NEGATIVE": "A", "NEUTRAL": "B"},
    ]
    return rotations[i % 3]


def activation_packet(rank2: bool, families: int = 9) -> dict:
    rows = []
    for i in range(families):
        nuisance = np.array([50.0 + 3.0 * i, -20.0 + i, 5.0 * math.sin(i), 0.0])
        e1 = np.array([1.0, 0.0, 0.0, 0.0])
        e2 = np.array([0.0, 1.0, 0.0, 0.0])
        jitter = 0.002 * np.array([0.0, 0.0, math.cos(i), math.sin(i)])
        second = 1.0 if rank2 else 0.0
        rows.append({
            "family_id": f"f{i}",
            "split": "CALIBRATION",
            "code_map": code_map(i),
            "prompt_sha256": {
                "AFFIRMATIVE": h(f"f{i}:a"),
                "NEGATIVE": h(f"f{i}:n"),
                "NEUTRAL": h(f"f{i}:u"),
            },
            "source_receipt_sha256": h(f"receipt:f{i}"),
            "activations": {
                "AFFIRMATIVE": (nuisance + 1.2 * e1 + jitter).tolist(),
                "NEGATIVE": (nuisance - 0.6 * e1 + second * e2 - jitter).tolist(),
                "NEUTRAL": (nuisance - 0.6 * e1 - second * e2 + jitter).tolist(),
            },
        })
    return {
        "schema": ranker.SCHEMA_IN,
        "embedding_dim": 4,
        "source_identity": {
            "repo_head": "1" * 40,
            "runtime_build_sha256": h("runtime"),
            "checkpoint_sha256": h("checkpoint"),
            "tokenizer_sha256": h("tokenizer"),
            "model_or_route": "Qwen/Qwen3-0.6B@test",
            "activation_site": "model.model.layers[20]:output:last_token",
            "token_scope": "LAST_TOKEN_ONLY",
            "layer": 20,
            "embedding_dim": 4,
        },
        "design_attestation": {
            "calibration_only": True,
            "fresh_holdout_opened": False,
            "model_facing_label_free": True,
            "lexically_disjoint_families": True,
            "matched_scenario_triplets": True,
            "output_code_independent": True,
        },
        "preregistration": {
            "permutations": 256,
            "alpha": 0.05,
            "coherence_min": 0.4,
            "rank1_max_sigma2_over_sigma1": 0.05,
            "rank2_min_sigma2_over_sigma1": 0.20,
            "rank1_min_loo_fraction": 0.8,
            "rank2_min_loo_fraction": 0.8,
        },
        "families": rows,
    }


def request(rank_result: dict, *, h1: float = 2.0, h2: float = 0.0) -> dict:
    return {
        "schema": controller.REQUEST_SCHEMA,
        "rank_result_sha256": rank_result["result_sha256"],
        "coordinates": {"h1": h1, "h2": h2},
        "magnitude_policy": {
            "selected_on_calibration_only": True,
            "frozen_before_holdout": True,
            "operating_point_receipt_sha256": h("operating-point"),
            "max_vector_l2": 10.0,
            "residual_norm_reference": 20.0,
            "max_residual_norm_ratio": 0.5,
        },
        "native_target": {
            "api_symbol": controller.NATIVE_API,
            "native_runtime_observed": False,
            "model_or_route": "Qwen3-0.6B-Q8_0@test",
            "runtime_build_sha256": h("llama-build"),
            "gguf_sha256": h("gguf"),
            "tokenizer_sha256": h("native-tokenizer"),
            "mapping_receipt_sha256": h("mapping"),
            "llama_cpp_source_commit": "2" * 40,
            "n_embd": 4,
            "n_layer": 28,
            "source_layer": 20,
            "layer_start": 20,
            "layer_end": 20,
            "mapping_semantics": "EXACT_TRANSFORMER_BLOCK_INDEX_AFTER_ARCHITECTURE_ATTESTATION",
            "token_scope": "ALL_PROMPT_TOKENS",
        },
    }


class SemanticSubspaceControlTests(unittest.TestCase):
    def test_rank2_coordinates_build_exact_native_layout_without_runtime_credit(self):
        packet = activation_packet(True)
        rank_result = ranker.analyze(packet)
        self.assertEqual("TWO_DIMENSIONAL_REQUIRED", rank_result["decision"])
        candidate, raw = controller.build_candidate(packet, rank_result, request(rank_result, h1=2.0, h2=3.0))
        self.assertEqual(controller.OUTPUT_SCHEMA, candidate["schema"])
        self.assertAlmostEqual(math.sqrt(13.0), candidate["vector"]["l2"], places=6)
        self.assertEqual((28 - 1) * 4 * 4, len(raw))
        self.assertFalse(candidate["native_cvec"]["native_runtime_observed"])
        self.assertFalse(candidate["semantic_causality_established"])
        self.assertEqual(0, candidate["jspace_model_runtime_credit"])

    def test_native_layout_populates_only_attested_layer_range(self):
        packet = activation_packet(True)
        rank_result = ranker.analyze(packet)
        candidate, raw = controller.build_candidate(packet, rank_result, request(rank_result, h1=2.0, h2=3.0))
        values = struct.unpack("<" + "f" * ((28 - 1) * 4), raw)
        for il in range(1, 28):
            chunk = values[(il - 1) * 4: il * 4]
            if il == 20:
                self.assertTrue(any(abs(x) > 1e-8 for x in chunk))
            else:
                self.assertTrue(all(abs(x) <= 1e-8 for x in chunk))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), candidate["native_cvec"]["cvec_f32le_sha256"])

    def test_rank1_forbids_second_coordinate(self):
        packet = activation_packet(False)
        rank_result = ranker.analyze(packet)
        self.assertEqual("ONE_DIMENSIONAL_SUPPORTED", rank_result["decision"])
        with self.assertRaisesRegex(ValueError, "H2_COORDINATE_FORBIDDEN_UNDER_RANK1"):
            controller.build_candidate(packet, rank_result, request(rank_result, h1=2.0, h2=0.1))

    def test_exact_rank_result_recomputation_is_mandatory(self):
        packet = activation_packet(True)
        rank_result = ranker.analyze(packet)
        tampered = deepcopy(rank_result)
        tampered["observed"]["sigma1"] += 1e-6
        with self.assertRaisesRegex(ValueError, "RANK_RESULT_MUST_EQUAL_EXACT_RECOMPUTATION"):
            controller.build_candidate(packet, tampered, request(rank_result, h1=2.0, h2=1.0))

    def test_residual_norm_envelope_blocks_oversized_coordinate(self):
        packet = activation_packet(True)
        rank_result = ranker.analyze(packet)
        req = request(rank_result, h1=9.0, h2=0.0)
        req["magnitude_policy"]["max_residual_norm_ratio"] = 0.1
        with self.assertRaisesRegex(ValueError, "CONTROL_VECTOR_EXCEEDS_RESIDUAL_NORM_RATIO_ENVELOPE"):
            controller.build_candidate(packet, rank_result, req)

    def test_native_dimension_mismatch_blocks(self):
        packet = activation_packet(True)
        rank_result = ranker.analyze(packet)
        req = request(rank_result, h1=2.0, h2=1.0)
        req["native_target"]["n_embd"] = 1024
        with self.assertRaisesRegex(ValueError, "NATIVE_TARGET_EMBEDDING_DIM_MISMATCH"):
            controller.build_candidate(packet, rank_result, req)

    def test_native_runtime_cannot_be_preclaimed(self):
        packet = activation_packet(True)
        rank_result = ranker.analyze(packet)
        req = request(rank_result, h1=2.0, h2=1.0)
        req["native_target"]["native_runtime_observed"] = True
        with self.assertRaisesRegex(ValueError, "PREEXECUTION_CONTROLLER_MUST_NOT_PRECLAIM_NATIVE_RUNTIME"):
            controller.build_candidate(packet, rank_result, req)

    def test_same_inputs_are_byte_deterministic(self):
        packet = activation_packet(True)
        rank_result = ranker.analyze(packet)
        req = request(rank_result, h1=2.0, h2=3.0)
        one, raw_one = controller.build_candidate(packet, rank_result, req)
        two, raw_two = controller.build_candidate(deepcopy(packet), deepcopy(rank_result), deepcopy(req))
        self.assertEqual(one["candidate_sha256"], two["candidate_sha256"])
        self.assertEqual(raw_one, raw_two)


if __name__ == "__main__":
    unittest.main()
