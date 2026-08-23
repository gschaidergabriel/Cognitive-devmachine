import unittest
from dataclasses import replace

from jspace_vector_control_v1 import (
    ABI_SCHEMA,
    CODEC_SCHEMA,
    JSpaceVectorControlError,
    _canonical_sha256,
    _packet_material,
    decode_vector,
    encode_vector,
    packet_bytes,
    reconstruction_metrics,
    validate_packet,
)

BASIS_ID = "basis:test:42"
BASIS_SHA256 = "a" * 64
GENERATION = 91
ROLE = "critic"


class JSpaceVectorControlTests(unittest.TestCase):
    def test_deterministic_roundtrip_has_bounded_q8_error(self):
        vector = (0.125, -0.75, 1.5, -2.25, 0.0, 3.0)
        packet_a = encode_vector(
            vector,
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
        )
        packet_b = encode_vector(
            vector,
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
        )
        self.assertEqual(packet_a, packet_b)
        self.assertEqual(packet_a.abi_schema, ABI_SCHEMA)
        self.assertEqual(packet_a.codec_schema, CODEC_SCHEMA)
        reconstructed = decode_vector(
            packet_a,
            current_generation=GENERATION,
            expected_basis_id=BASIS_ID,
            expected_basis_sha256=BASIS_SHA256,
            expected_role=ROLE,
        )
        metrics = reconstruction_metrics(vector, reconstructed)
        self.assertLessEqual(metrics["normalized_max_error"], 1.0 / 254.0 + 1e-15)
        self.assertEqual(max(abs(value) for value in packet_a.q8_values), 127)
        self.assertEqual(packet_bytes(packet_a), packet_bytes(packet_b))

    def test_null_vector_is_explicit_and_stable(self):
        packet = encode_vector(
            (0.0, -0.0, 0),
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
            control_condition="NULL_VECTOR",
        )
        self.assertEqual(packet.q8_values, (0, 0, 0))
        self.assertEqual(packet.scale_numerator, "0")
        self.assertEqual(
            decode_vector(
                packet,
                current_generation=GENERATION,
                expected_basis_id=BASIS_ID,
                expected_basis_sha256=BASIS_SHA256,
                expected_role=ROLE,
                expected_control_condition="NULL_VECTOR",
            ),
            (0.0, 0.0, 0.0),
        )

    def test_generation_basis_role_and_control_condition_are_fail_closed(self):
        packet = encode_vector(
            (1.0, -0.5),
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
        )
        common = dict(
            packet=packet,
            current_generation=GENERATION,
            expected_basis_id=BASIS_ID,
            expected_basis_sha256=BASIS_SHA256,
            expected_role=ROLE,
        )
        with self.assertRaisesRegex(JSpaceVectorControlError, "STALE_VECTOR_CONTROL_GENERATION"):
            decode_vector(**{**common, "current_generation": GENERATION + 1})
        with self.assertRaisesRegex(JSpaceVectorControlError, "JSPACE_BASIS_ID_MISMATCH"):
            decode_vector(**{**common, "expected_basis_id": "basis:test:other"})
        with self.assertRaisesRegex(JSpaceVectorControlError, "JSPACE_BASIS_SHA256_MISMATCH"):
            decode_vector(**{**common, "expected_basis_sha256": "b" * 64})
        with self.assertRaisesRegex(JSpaceVectorControlError, "JSPACE_ROLE_MISMATCH"):
            decode_vector(**{**common, "expected_role": "world"})
        with self.assertRaisesRegex(JSpaceVectorControlError, "JSPACE_CONTROL_CONDITION_MISMATCH"):
            decode_vector(**common, expected_control_condition="LESION")

    def test_sign_flip_and_permutation_controls_change_identity_and_roundtrip(self):
        vector = (0.2, -0.7, 1.0, 0.4)
        baseline = encode_vector(
            vector,
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
        )
        sign_flip = encode_vector(
            tuple(-value for value in vector),
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
            control_condition="SIGN_FLIP",
        )
        permuted_values = (vector[2], vector[0], vector[3], vector[1])
        permuted = encode_vector(
            permuted_values,
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
            control_condition="PERMUTED",
        )
        self.assertEqual(len({baseline.packet_sha256, sign_flip.packet_sha256, permuted.packet_sha256}), 3)
        decoded_sign_flip = decode_vector(
            sign_flip,
            current_generation=GENERATION,
            expected_basis_id=BASIS_ID,
            expected_basis_sha256=BASIS_SHA256,
            expected_role=ROLE,
            expected_control_condition="SIGN_FLIP",
        )
        decoded_permuted = decode_vector(
            permuted,
            current_generation=GENERATION,
            expected_basis_id=BASIS_ID,
            expected_basis_sha256=BASIS_SHA256,
            expected_role=ROLE,
            expected_control_condition="PERMUTED",
        )
        self.assertLessEqual(reconstruction_metrics(tuple(-v for v in vector), decoded_sign_flip)["normalized_max_error"], 1.0 / 254.0 + 1e-15)
        self.assertLessEqual(reconstruction_metrics(permuted_values, decoded_permuted)["normalized_max_error"], 1.0 / 254.0 + 1e-15)

    def test_packet_tamper_is_detected_before_decode(self):
        packet = encode_vector(
            (1.0, 0.5, -0.25),
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
        )
        tampered = replace(packet, q8_values=(126,) + packet.q8_values[1:])
        with self.assertRaisesRegex(JSpaceVectorControlError, "VECTOR_CONTROL_PACKET_DIGEST_MISMATCH"):
            validate_packet(tampered)

    def test_self_consistent_extreme_scale_packet_fails_closed_before_decode(self):
        packet = encode_vector(
            (1.0, -0.5),
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
        )
        poisoned = replace(
            packet,
            scale_numerator="1" + ("0" * 309),
            packet_sha256="0" * 64,
        )
        poisoned = replace(
            poisoned,
            packet_sha256=_canonical_sha256(_packet_material(poisoned), "VECTOR_CONTROL_PACKET"),
        )
        with self.assertRaisesRegex(JSpaceVectorControlError, "SCALE_RATIONAL_BINARY64_RANGE_REQUIRED"):
            validate_packet(poisoned)
        with self.assertRaisesRegex(JSpaceVectorControlError, "SCALE_RATIONAL_BINARY64_RANGE_REQUIRED"):
            decode_vector(
                poisoned,
                current_generation=GENERATION,
                expected_basis_id=BASIS_ID,
                expected_basis_sha256=BASIS_SHA256,
                expected_role=ROLE,
            )

    def test_self_consistent_non_encoder_native_scale_fails_closed(self):
        packet = encode_vector(
            (1.0, -0.5),
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
        )
        forged = replace(
            packet,
            scale_numerator="1",
            scale_denominator="3",
            packet_sha256="0" * 64,
        )
        forged = replace(
            forged,
            packet_sha256=_canonical_sha256(_packet_material(forged), "VECTOR_CONTROL_PACKET"),
        )
        with self.assertRaisesRegex(JSpaceVectorControlError, "SCALE_RATIONAL_BINARY64_ANCHOR_EXACT_REQUIRED"):
            validate_packet(forged)
        with self.assertRaisesRegex(JSpaceVectorControlError, "SCALE_RATIONAL_BINARY64_ANCHOR_EXACT_REQUIRED"):
            decode_vector(
                forged,
                current_generation=GENERATION,
                expected_basis_id=BASIS_ID,
                expected_basis_sha256=BASIS_SHA256,
                expected_role=ROLE,
            )

    def test_binary64_scale_endpoints_remain_admitted(self):
        for value in (
            float.fromhex("0x0.0000000000001p-1022"),
            float.fromhex("0x1.fffffffffffffp+1023"),
        ):
            packet = encode_vector(
                (value,),
                basis_id=BASIS_ID,
                basis_sha256=BASIS_SHA256,
                generation=GENERATION,
                role=ROLE,
            )
            validate_packet(packet)
            self.assertEqual(
                decode_vector(
                    packet,
                    current_generation=GENERATION,
                    expected_basis_id=BASIS_ID,
                    expected_basis_sha256=BASIS_SHA256,
                    expected_role=ROLE,
                ),
                (value,),
            )

    def test_equivalent_nonreduced_scale_alias_fails_closed(self):
        packet = encode_vector(
            (1.0, -0.5),
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
        )
        aliased = replace(
            packet,
            scale_numerator=str(int(packet.scale_numerator) * 2),
            scale_denominator=str(int(packet.scale_denominator) * 2),
            packet_sha256="0" * 64,
        )
        aliased = replace(
            aliased,
            packet_sha256=_canonical_sha256(_packet_material(aliased), "VECTOR_CONTROL_PACKET"),
        )
        with self.assertRaisesRegex(JSpaceVectorControlError, "SCALE_RATIONAL_NOT_REDUCED"):
            validate_packet(aliased)

    def test_nonfinite_and_inexact_integer_inputs_fail_closed(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.assertRaisesRegex(JSpaceVectorControlError, "FINITE_BINARY64_REQUIRED"):
                encode_vector(
                    (value,), basis_id=BASIS_ID, basis_sha256=BASIS_SHA256,
                    generation=GENERATION, role=ROLE,
                )
        with self.assertRaisesRegex(JSpaceVectorControlError, "EXACT_BINARY64_REQUIRED"):
            encode_vector(
                (9007199254740993,), basis_id=BASIS_ID, basis_sha256=BASIS_SHA256,
                generation=GENERATION, role=ROLE,
            )


if __name__ == "__main__":
    unittest.main()
