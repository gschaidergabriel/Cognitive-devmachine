import hashlib
import math
import unittest

from jspace_activation_steering_search_v1 import (
    HOOK_RECEIPT_SCHEMA,
    HookReceipt,
    SteeringObservation,
    applied_vector_sha256,
)
from jspace_activation_steering_trigger1_controls_v1 import (
    CONTROL_LABELS,
    search_trigger1_matched_controls,
)
from jspace_matched_orthogonal_control_v1 import (
    derive_matched_orthogonal_direction,
    validate_matched_orthogonal_direction,
)
from jspace_vector_control_v1 import encode_vector

BASIS_ID = "basis:test:trigger1-controls"
BASIS_SHA256 = "a" * 64
GENERATION = 19
ROLE = "critic"


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def score(observation):
    return float(observation.output_text)


def source_packet(vector=(1.0, 0.0)):
    return encode_vector(
        vector,
        basis_id=BASIS_ID,
        basis_sha256=BASIS_SHA256,
        generation=GENERATION,
        role=ROLE,
    )


class SyntheticExecutor:
    def __init__(self, mode="directional", target_layer="L3"):
        self.mode = mode
        self.target_layer = target_layer

    def run(self, prompt, *, layer_id, vector, alpha, seed):
        base = 0.10 + seed * 0.001
        if layer_id is None:
            return SteeringObservation(f"{base:.9f}", None)

        if self.mode == "directional":
            effect = (vector[0] if layer_id == self.target_layer else 0.0) * alpha
        elif self.mode == "norm_only":
            effect = (
                math.sqrt(sum(value * value for value in vector))
                if layer_id == self.target_layer else 0.0
            ) * alpha
        else:
            raise AssertionError("unknown mode")

        vector_sha = applied_vector_sha256(vector)
        pre = _sha(f"pre:{layer_id}:{seed}")
        post = pre if all(value == 0.0 for value in vector) else _sha(
            f"post:{layer_id}:{seed}:{alpha}:{vector_sha}"
        )
        receipt = HookReceipt(
            HOOK_RECEIPT_SCHEMA,
            "synthetic:trigger1-controls:v1",
            f"invocation:{seed}:{layer_id}:{alpha}:{vector_sha[:12]}",
            layer_id,
            seed,
            alpha,
            vector_sha,
            pre,
            post,
        )
        return SteeringObservation(f"{base + effect:.9f}", receipt)


class Trigger1MatchedControlTests(unittest.TestCase):
    def test_orthogonal_generator_is_deterministic_same_norm_and_orthogonal(self):
        source = (1.0, 2.0, -0.5, 0.25)
        a = derive_matched_orthogonal_direction(source)
        b = derive_matched_orthogonal_direction(source)
        self.assertEqual(a, b)
        validate_matched_orthogonal_direction(source, a)
        self.assertEqual("ORTHOGONAL_SAME_NORM", a.control_label)
        self.assertAlmostEqual(a.source_l2_norm, a.matched_l2_norm, places=12)
        self.assertLessEqual(a.abs_cosine, 1e-12)
        self.assertNotEqual(tuple(source), a.vector)

    def test_axis_aligned_source_gets_exact_other_axis(self):
        result = derive_matched_orthogonal_direction((2.0, 0.0))
        self.assertAlmostEqual(result.vector[0], 0.0, places=15)
        self.assertAlmostEqual(abs(result.vector[1]), 2.0, places=15)
        self.assertAlmostEqual(result.dot_product, 0.0, places=15)

    def test_directional_effect_survives_all_six_search_controls(self):
        result = search_trigger1_matched_controls(
            SyntheticExecutor(mode="directional"),
            "calibration probe",
            source_packet((1.0, 0.0)),
            current_generation=GENERATION,
            expected_basis_id=BASIS_ID,
            expected_basis_sha256=BASIS_SHA256,
            expected_role=ROLE,
            layer_ids=("L1", "L3"),
            alphas=(-2.0, -1.0, 1.0, 2.0),
            seeds=(1, 2, 3),
            permutation_seeds=(7,),
            score_fn=score,
            min_delta=0.5,
            min_directional_gap=1.0,
            min_orthogonal_gap=0.5,
            min_permuted_gap=0.5,
        )
        self.assertEqual(
            (
                "BASELINE",
                "+VECTOR",
                "SIGN_FLIP",
                "NULL_VECTOR",
                "ORTHOGONAL_SAME_NORM",
                "PERMUTED_SAME_NORM",
            ),
            CONTROL_LABELS,
        )
        self.assertTrue(result.base.success)
        self.assertTrue(result.success)
        self.assertFalse(result.jspace_causal_credit)
        self.assertGreaterEqual(result.directional_vs_orthogonal_gap, 0.5)
        self.assertGreaterEqual(result.directional_vs_permuted_gap, 0.5)
        self.assertIn("DISJOINT_CALIBRATION_TO_FROZEN_HOLDOUT", result.remaining_promotion_gates)

    def test_norm_only_false_positive_is_rejected_by_orthogonal_control(self):
        result = search_trigger1_matched_controls(
            SyntheticExecutor(mode="norm_only"),
            "calibration probe",
            source_packet((1.0, 0.0)),
            current_generation=GENERATION,
            expected_basis_id=BASIS_ID,
            expected_basis_sha256=BASIS_SHA256,
            expected_role=ROLE,
            layer_ids=("L3",),
            alphas=(-2.0, -1.0, 1.0, 2.0),
            seeds=(1, 2, 3),
            permutation_seeds=(7,),
            score_fn=score,
            min_delta=0.5,
            min_directional_gap=1.0,
            min_orthogonal_gap=0.1,
            min_permuted_gap=0.1,
        )
        self.assertFalse(result.base.success)
        self.assertFalse(result.success)
        self.assertAlmostEqual(result.directional_vs_orthogonal_gap, 0.0, places=9)

    def test_one_dimensional_source_rejected(self):
        with self.assertRaisesRegex(Exception, "DIMENSION_2_TO"):
            derive_matched_orthogonal_direction((1.0,))


if __name__ == "__main__":
    unittest.main()
