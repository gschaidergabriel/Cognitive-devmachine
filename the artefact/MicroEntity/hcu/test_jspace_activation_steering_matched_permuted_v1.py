import hashlib
import unittest

from jspace_activation_steering_matched_permuted_v1 import (
    derive_permuted_null_control,
    search_activation_steering_with_permuted_nulls,
)
from jspace_activation_steering_search_v1 import (
    HOOK_RECEIPT_SCHEMA,
    HookReceipt,
    SteeringObservation,
    applied_vector_sha256,
)
from jspace_vector_control_v1 import encode_vector


BASIS_ID = "basis:test:matched-permuted"
BASIS_SHA256 = "a" * 64
GENERATION = 17
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
        elif self.mode == "permutation_invariant":
            # Deliberately passes sign + zero controls while being blind to
            # coordinate direction. PERMUTED controls must falsify it.
            effect = (
                sum(abs(value) for value in vector)
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
            "synthetic:matched-permuted:v1",
            f"invocation:{seed}:{layer_id}:{alpha}:{vector_sha[:12]}",
            layer_id,
            seed,
            alpha,
            vector_sha,
            pre,
            post,
        )
        return SteeringObservation(f"{base + effect:.9f}", receipt)


class MatchedPermutedSteeringTests(unittest.TestCase):
    def test_permuted_control_is_deterministic_and_preserves_exact_q8_multiset(self):
        packet = source_packet((1.0, 0.5, -0.25))
        a = derive_permuted_null_control(
            packet,
            current_generation=GENERATION,
            expected_basis_id=BASIS_ID,
            expected_basis_sha256=BASIS_SHA256,
            expected_role=ROLE,
            seed=11,
        )
        b = derive_permuted_null_control(
            packet,
            current_generation=GENERATION,
            expected_basis_id=BASIS_ID,
            expected_basis_sha256=BASIS_SHA256,
            expected_role=ROLE,
            seed=11,
        )
        self.assertEqual(a, b)
        self.assertEqual(a.packet.control_condition, "PERMUTED")
        self.assertNotEqual(a.packet.packet_sha256, packet.packet_sha256)
        self.assertEqual(sorted(a.packet.q8_values), sorted(packet.q8_values))
        self.assertEqual(a.packet.scale_numerator, packet.scale_numerator)
        self.assertEqual(a.packet.scale_denominator, packet.scale_denominator)

    def test_directional_effect_survives_permuted_null_without_minting_causality(self):
        result = search_activation_steering_with_permuted_nulls(
            SyntheticExecutor(mode="directional"),
            "probe",
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
            min_permuted_gap=0.5,
        )
        self.assertTrue(result.base.success)
        self.assertFalse(result.jspace_causal_credit)
        self.assertIn("SHAM_CONTROL", result.remaining_causal_controls)
        self.assertIn("OFF_TARGET_CONTROL", result.remaining_causal_controls)
        self.assertTrue(result.success)
        self.assertGreaterEqual(result.directional_vs_permuted_gap, 0.5)

    def test_permutation_invariant_false_positive_is_rejected(self):
        result = search_activation_steering_with_permuted_nulls(
            SyntheticExecutor(mode="permutation_invariant"),
            "probe",
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
            min_permuted_gap=0.1,
        )
        self.assertTrue(result.base.success)
        self.assertFalse(result.jspace_causal_credit)
        self.assertFalse(result.success)
        self.assertAlmostEqual(result.directional_vs_permuted_gap, 0.0)

    def test_one_dimensional_source_cannot_fake_permuted_null(self):
        packet = source_packet((1.0,))
        with self.assertRaisesRegex(Exception, "DIMENSION_AT_LEAST_TWO"):
            derive_permuted_null_control(
                packet,
                current_generation=GENERATION,
                expected_basis_id=BASIS_ID,
                expected_basis_sha256=BASIS_SHA256,
                expected_role=ROLE,
                seed=1,
            )


if __name__ == "__main__":
    unittest.main()
