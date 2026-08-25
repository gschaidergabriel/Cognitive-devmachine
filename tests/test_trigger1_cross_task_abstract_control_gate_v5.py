from __future__ import annotations

import unittest
from unittest.mock import patch

from tools import trigger1_cross_task_abstract_control_gate_v5 as g

SHA = "a" * 64


def axis(axis_id: str, vector: list[float]) -> dict:
    return {"axis_id": axis_id, "vector": vector, "vector_sha256": g.vector_sha256(vector)}


def semantic(vector: list[float]) -> dict:
    return {"vector": vector, "vector_sha256": g.vector_sha256(vector)}


def valid() -> dict:
    return {
        "schema": g.ATTESTATION_SCHEMA,
        "nuisance_subspace": {
            "schema": g.NUISANCE_SCHEMA,
            "fit_split": "CALIBRATION",
            "frozen_before_holdout": True,
            "receipt_sha256": SHA,
            "rank": 2,
            "axes": [axis("q0", [1.0, 0.0, 0.0]), axis("q1", [0.0, 1.0, 0.0])],
        },
        "semantic_control_vectors": {
            "schema": g.SEMANTIC_SCHEMA,
            "fit_split": "CALIBRATION",
            "frozen_before_holdout": True,
            "vectors_are_post_nuisance_residualization": True,
            "residualization_method": "ORTHOGONAL_PROJECTION_CALIBRATION_FROZEN",
            "receipt_sha256": SHA,
            "vectors": {
                "S0": semantic([0.0, 0.0, 1.0]),
                "S1": semantic([0.0, 0.0, -1.0]),
                "S2": semantic([0.0, 0.0, 2.0]),
            },
        },
        "holdout_causal_rows": [],
    }


class ExactNuisanceVectorGateV5Tests(unittest.TestCase):
    def test_valid_exact_geometry_can_delegate(self):
        x = valid()
        failures: list[str] = []
        audit = g._validate_vector_bindings(x, failures)
        self.assertEqual(failures, [])
        self.assertEqual(audit["axis_count"], 2)
        self.assertEqual(audit["max_axis_dot_abs"], 0.0)
        self.assertEqual(audit["semantic_projection_fraction"], {"S0": 0.0, "S1": 0.0, "S2": 0.0})
        with patch.object(g.v4, "adjudicate", return_value={"cross_task_abstract_native_control_pass": True, "failures": []}):
            out = g.adjudicate(x)
        self.assertTrue(out["cross_task_abstract_native_control_pass"])
        self.assertFalse(out["canonical_credit_minted"])

    def test_duplicate_vector_cannot_fake_rank_two(self):
        x = valid()
        x["nuisance_subspace"]["axes"][1] = axis("q1", [1.0, 0.0, 0.0])
        failures: list[str] = []
        g._validate_vector_bindings(x, failures)
        self.assertTrue(any("DUPLICATE_VECTOR_SHA256" in f for f in failures))

    def test_nonorthogonal_unique_axes_fail(self):
        x = valid()
        q = [2**-0.5, 2**-0.5, 0.0]
        x["nuisance_subspace"]["axes"][1] = axis("q1", q)
        failures: list[str] = []
        g._validate_vector_bindings(x, failures)
        self.assertTrue(any("NOT_ORTHOGONAL" in f for f in failures))

    def test_nonunit_axis_fails(self):
        x = valid()
        x["nuisance_subspace"]["axes"][1] = axis("q1", [0.0, 2.0, 0.0])
        failures: list[str] = []
        g._validate_vector_bindings(x, failures)
        self.assertTrue(any("NOT_UNIT_NORM" in f for f in failures))

    def test_axis_hash_must_bind_exact_vector(self):
        x = valid()
        x["nuisance_subspace"]["axes"][0]["vector_sha256"] = SHA
        failures: list[str] = []
        g._validate_vector_bindings(x, failures)
        self.assertTrue(any("VECTOR_SHA256_MISMATCH" in f for f in failures))

    def test_semantic_vector_inside_nuisance_span_fails(self):
        x = valid()
        x["semantic_control_vectors"]["vectors"]["S0"] = semantic([1.0, 0.0, 0.0])
        failures: list[str] = []
        audit = g._validate_vector_bindings(x, failures)
        self.assertEqual(audit["semantic_projection_fraction"]["S0"], 1.0)
        self.assertIn("V5_SEMANTIC_VECTOR_S0_NUISANCE_PROJECTION_TOO_LARGE", failures)

    def test_residualization_attestation_required(self):
        x = valid()
        x["semantic_control_vectors"]["vectors_are_post_nuisance_residualization"] = False
        failures: list[str] = []
        g._validate_vector_bindings(x, failures)
        self.assertIn("V5_POST_NUISANCE_RESIDUALIZATION_REQUIRED", failures)

    def test_v4_positive_cannot_leak_through_v5_geometry_failure(self):
        x = valid()
        x["nuisance_subspace"]["axes"][1] = axis("q1", [1.0, 0.0, 0.0])
        with patch.object(g.v4, "adjudicate", return_value={"cross_task_abstract_native_control_pass": True, "failures": []}):
            out = g.adjudicate(x)
        self.assertFalse(out["cross_task_abstract_native_control_pass"])
        self.assertFalse(out["canonical_semantics_promotion"])
        self.assertFalse(out["jspace_model_runtime_credit"])
        self.assertFalse(out["training_credit"])


if __name__ == "__main__":
    unittest.main()
