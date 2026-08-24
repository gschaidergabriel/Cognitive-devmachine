from dataclasses import replace
import math
import unittest

from jspace_matched_random_control_v1 import (
    ABI_BLOCK_STATUS,
    MAX_RELATIVE_L2_ERROR,
    MatchedRandomControlError,
    canonical_abi_admission_status,
    derive_matched_random_direction,
    validate_matched_random_direction,
)
from jspace_vector_control_v1 import CONTROL_CONDITIONS, JSpaceVectorControlError, encode_vector


class JSpaceMatchedRandomControlTests(unittest.TestCase):
    def test_same_family_seed_and_source_replay_exactly(self):
        kwargs = {"family_id": "holdout:refusal:17", "seed": 7}
        first = derive_matched_random_direction((3.0, 4.0, -2.0, 1.0), **kwargs)
        second = derive_matched_random_direction((3.0, 4.0, -2.0, 1.0), **kwargs)
        self.assertEqual(first, second)
        validate_matched_random_direction((3.0, 4.0, -2.0, 1.0), first)

    def test_direction_depends_on_family_and_seed(self):
        source = (0.25, -0.5, 1.0, -2.0, 0.75, 0.125)
        base = derive_matched_random_direction(source, family_id="family:a", seed=11)
        changed_seed = derive_matched_random_direction(source, family_id="family:a", seed=12)
        changed_family = derive_matched_random_direction(source, family_id="family:b", seed=11)
        self.assertEqual(len({
            base.matched_vector_sha256,
            changed_seed.matched_vector_sha256,
            changed_family.matched_vector_sha256,
        }), 3)

    def test_random_orientation_uses_source_only_for_dimension_and_l2_norm(self):
        # Both sources have dimension 4 and L2 norm 5.  The generated control vector must be
        # identical even though source orientation/hash differs, preventing target-direction
        # leakage into the supposedly independent random control.
        source_a = (3.0, 4.0, 0.0, 0.0)
        source_b = (0.0, 0.0, 3.0, 4.0)
        a = derive_matched_random_direction(source_a, family_id="family:orientation", seed=99)
        b = derive_matched_random_direction(source_b, family_id="family:orientation", seed=99)
        self.assertNotEqual(a.source_vector_sha256, b.source_vector_sha256)
        self.assertEqual(a.vector, b.vector)
        self.assertEqual(a.matched_vector_sha256, b.matched_vector_sha256)

    def test_l2_norm_is_matched_within_declared_tolerance(self):
        source = (0.125, -0.5, 2.0, -4.0, 1.5, 0.25, -0.75)
        receipt = derive_matched_random_direction(source, family_id="family:norm", seed=12345)
        expected_norm = math.hypot(*source)
        self.assertEqual(receipt.source_l2_norm, expected_norm)
        self.assertLessEqual(receipt.relative_l2_error, MAX_RELATIVE_L2_ERROR)
        self.assertLessEqual(
            abs(receipt.matched_l2_norm - expected_norm) / expected_norm,
            MAX_RELATIVE_L2_ERROR,
        )

    def test_zero_nonfinite_bad_dimension_bad_seed_and_inexact_int_fail_closed(self):
        for source in (
            (0.0, 0.0),
            (float("nan"), 1.0),
            (1.0,),
            (1.0, float("inf")),
            (9_007_199_254_740_993, 1.0),
        ):
            with self.subTest(source=source), self.assertRaises(MatchedRandomControlError):
                derive_matched_random_direction(source, family_id="family:bad", seed=1)
        with self.assertRaisesRegex(MatchedRandomControlError, "EXACT_BINARY64_REQUIRED"):
            derive_matched_random_direction(
                (9_007_199_254_740_993, 1.0), family_id="family:alias", seed=1
            )
        for seed in (-1, True, 9_007_199_254_740_992):
            with self.subTest(seed=seed), self.assertRaises(MatchedRandomControlError):
                derive_matched_random_direction((1.0, 2.0), family_id="family:bad-seed", seed=seed)

    def test_mutated_receipt_fails_replay_validation(self):
        source = (1.0, -2.0, 0.5, 0.25)
        receipt = derive_matched_random_direction(source, family_id="family:tamper", seed=5)
        forged = replace(receipt, matched_vector_sha256="0" * 64)
        with self.assertRaisesRegex(MatchedRandomControlError, "REPLAY_MISMATCH"):
            validate_matched_random_direction(source, forged)

    def test_current_single_abi_remains_fail_closed_against_label_laundering(self):
        # The generator is intentionally useful before ABI promotion, but the current single
        # canonical v1 wire still lacks MATCHED_RANDOM.  Until a successor change admits it,
        # trying to serialize the generated control under that label must fail rather than be
        # mislabeled as PERMUTED/BASELINE.
        self.assertEqual(canonical_abi_admission_status(CONTROL_CONDITIONS), ABI_BLOCK_STATUS)
        receipt = derive_matched_random_direction((1.0, -1.0, 0.5), family_id="family:abi", seed=3)
        with self.assertRaisesRegex(JSpaceVectorControlError, "control_condition:UNSUPPORTED"):
            encode_vector(
                receipt.vector,
                basis_id="basis:test:matched-random",
                basis_sha256="a" * 64,
                generation=1,
                role="control",
                control_condition="MATCHED_RANDOM",
            )


if __name__ == "__main__":
    unittest.main()
