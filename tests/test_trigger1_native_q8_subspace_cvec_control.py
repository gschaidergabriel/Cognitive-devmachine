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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trigger1_native_q8_geometry_balance_v2 as geometry_v2
from tools import trigger1_native_q8_subspace_cvec_control as control
from tools import trigger1_semantic_simplex_rank_analyze as rank_analyzer


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def activation_payload(rank2: bool, families: int = 9) -> dict:
    rows = []
    for i in range(families):
        nuisance = np.array([30.0 + i, -15.0 + 0.4 * i, 2.0 * math.sin(i), 0.0], dtype=np.float64)
        e1 = np.array([1.0, 0.0, 0.0, 0.0])
        e2 = np.array([0.0, 1.0, 0.0, 0.0])
        second = 0.85 if rank2 else 0.0
        jitter = 0.002 * np.array([0.0, 0.0, math.cos(i), math.sin(i)])
        vectors = {
            "AFFIRMATIVE": nuisance + 1.2 * e1 + jitter,
            "NEGATIVE": nuisance - 0.6 * e1 + second * e2 - jitter,
            "NEUTRAL": nuisance - 0.6 * e1 - second * e2 + jitter,
        }
        for semantic, vector in vectors.items():
            rows.append({
                "row_id": f"f{i}:{semantic}",
                "family_group_id": f"family-{i}",
                "semantic_class": semantic,
                "activation": vector.tolist(),
            })
    return {
        "schema": rank_analyzer.INPUT_SCHEMA,
        "dimension": 4,
        "decision_config": {
            "alpha": 0.05,
            "rank1_equivalence_max_ratio": 0.05,
            "rank2_min_ratio": 0.20,
            "rank2_min_lofo_cosine": 0.80,
            "min_matched_families": 6,
            "max_exact_signflip_families": 12,
            "monte_carlo_signflips": 2048,
        },
        "rows": rows,
    }


def request(rank: dict, geometry: dict, *, h1: float = 2.0, h2: float = 0.0) -> dict:
    return {
        "schema": control.REQUEST_SCHEMA,
        "rank_analysis_receipt_sha256": rank["analysis_receipt_sha256"],
        "geometry_receipt_sha256": geometry["geometry_receipt_sha256"],
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
            "api_symbol": control.NATIVE_API,
            "native_runtime_observed": False,
            "runtime_build_sha256": h("runtime-build"),
            "gguf_sha256": h("qwen3-0.6b-q8"),
            "tokenizer_sha256": h("tokenizer"),
            "mapping_receipt_sha256": h("layer-map"),
            "conversion_receipt_sha256": h("torch-to-gguf-conversion"),
            "llama_cpp_source_commit": "2" * 40,
            "n_embd": 4,
            "n_layer": 28,
            "source_layer": 20,
            "layer_start": 20,
            "layer_end": 20,
            "mapping_semantics": "EXACT_TRANSFORMER_BLOCK_INDEX_AFTER_ARCHITECTURE_ATTESTATION",
            "token_scope": control.TOKEN_SCOPE,
        },
    }


class NativeQ8SubspaceControlTests(unittest.TestCase):
    def make(self, rank2: bool):
        payload = activation_payload(rank2)
        rank = rank_analyzer.analyze(payload)
        geometry = geometry_v2.finalize(payload, rank)
        return payload, rank, geometry

    def test_rank2_continuous_coordinates_build_native_cvec_without_runtime_credit(self):
        payload, rank, geometry = self.make(True)
        self.assertEqual("TWO_DIMENSIONAL_REQUIRED", rank["verdict"])
        result, raw = control.build(payload, rank, geometry, request(rank, geometry, h1=2.0, h2=3.0))
        self.assertEqual(control.OUTPUT_SCHEMA, result["schema"])
        self.assertAlmostEqual(math.sqrt(13.0), result["vector"]["l2"], places=6)
        self.assertEqual((28 - 1) * 4 * 4, len(raw))
        self.assertFalse(result["native_cvec"]["native_runtime_observed"])
        self.assertFalse(result["semantic_causality_established"])
        self.assertEqual(0, result["jspace_model_runtime_credit"])

    def test_cvec_populates_only_attested_native_layer(self):
        payload, rank, geometry = self.make(True)
        result, raw = control.build(payload, rank, geometry, request(rank, geometry, h1=2.0, h2=3.0))
        values = struct.unpack("<" + "f" * ((28 - 1) * 4), raw)
        for layer in range(1, 28):
            chunk = values[(layer - 1) * 4: layer * 4]
            if layer == 20:
                self.assertTrue(any(abs(value) > 1e-8 for value in chunk))
            else:
                self.assertTrue(all(abs(value) <= 1e-8 for value in chunk))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), result["native_cvec"]["sha256_f32le"])

    def test_rank1_forbids_second_coordinate(self):
        payload, rank, geometry = self.make(False)
        self.assertEqual("ONE_DIMENSIONAL_SUPPORTED", rank["verdict"])
        with self.assertRaisesRegex(control.ControlError, "H2_COORDINATE_FORBIDDEN_UNDER_RANK1"):
            control.build(payload, rank, geometry, request(rank, geometry, h1=2.0, h2=0.1))

    def test_rank_tamper_fails_exact_recomputation(self):
        payload, rank, geometry = self.make(True)
        tampered = deepcopy(rank)
        tampered["geometry"]["h1_norm"] += 1e-6
        with self.assertRaisesRegex(control.ControlError, "DECLARED_RANK_RESULT_DIFFERS_FROM_EXACT_RECOMPUTATION"):
            control.build(payload, tampered, geometry, request(rank, geometry, h1=2.0, h2=1.0))

    def test_geometry_tamper_fails_exact_recomputation(self):
        payload, rank, geometry = self.make(True)
        tampered = deepcopy(geometry)
        tampered["balanced_shared_geometry_scale"] += 1e-6
        with self.assertRaisesRegex(control.ControlError, "DECLARED_GEOMETRY_RESULT_DIFFERS_FROM_EXACT_RECOMPUTATION"):
            control.build(payload, rank, tampered, request(rank, geometry, h1=2.0, h2=1.0))

    def test_residual_norm_envelope_blocks_oversized_control(self):
        payload, rank, geometry = self.make(True)
        req = request(rank, geometry, h1=5.0, h2=0.0)
        req["magnitude_policy"]["max_residual_norm_ratio"] = 0.1
        with self.assertRaisesRegex(control.ControlError, "CONTROL_VECTOR_EXCEEDS_FROZEN_RESIDUAL_RATIO_ENVELOPE"):
            control.build(payload, rank, geometry, req)

    def test_native_dimension_mismatch_fails_closed(self):
        payload, rank, geometry = self.make(True)
        req = request(rank, geometry, h1=2.0, h2=1.0)
        req["native_target"]["n_embd"] = 1024
        with self.assertRaisesRegex(control.ControlError, "NATIVE_TARGET_EMBEDDING_DIMENSION_MISMATCH"):
            control.build(payload, rank, geometry, req)

    def test_conversion_receipt_is_required(self):
        payload, rank, geometry = self.make(True)
        req = request(rank, geometry, h1=2.0, h2=1.0)
        del req["native_target"]["conversion_receipt_sha256"]
        with self.assertRaisesRegex(control.ControlError, "NATIVE_TARGET_CONVERSION_RECEIPT_SHA256_REQUIRED"):
            control.build(payload, rank, geometry, req)

    def test_native_runtime_cannot_be_preclaimed(self):
        payload, rank, geometry = self.make(True)
        req = request(rank, geometry, h1=2.0, h2=1.0)
        req["native_target"]["native_runtime_observed"] = True
        with self.assertRaisesRegex(control.ControlError, "PREEXECUTION_REQUEST_MUST_NOT_PRECLAIM_RUNTIME"):
            control.build(payload, rank, geometry, req)

    def test_same_inputs_are_byte_deterministic(self):
        payload, rank, geometry = self.make(True)
        req = request(rank, geometry, h1=2.0, h2=3.0)
        one, raw_one = control.build(payload, rank, geometry, req)
        two, raw_two = control.build(deepcopy(payload), deepcopy(rank), deepcopy(geometry), deepcopy(req))
        self.assertEqual(one["candidate_receipt_sha256"], two["candidate_receipt_sha256"])
        self.assertEqual(raw_one, raw_two)


if __name__ == "__main__":
    unittest.main()
