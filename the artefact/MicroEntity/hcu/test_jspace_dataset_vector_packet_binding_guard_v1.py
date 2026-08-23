import unittest
from dataclasses import asdict

from jspace_dataset_vector_packet_binding_guard_v1 import (
    JSpaceDatasetVectorPacketBindingError,
    verify_admitted_vector_packet_binding,
)
from jspace_vector_control_v1 import encode_vector


BASIS_ID = "basis:dataset:7"
BASIS_SHA256 = "d" * 64
GENERATION = 7
ROLE = "world"
CONDITION = "BASELINE"


def packet(*, generation=GENERATION, basis_id=BASIS_ID, basis_sha256=BASIS_SHA256, role=ROLE, condition=CONDITION):
    return encode_vector(
        [1.0, -0.5, 0.25],
        basis_id=basis_id,
        basis_sha256=basis_sha256,
        generation=generation,
        role=role,
        control_condition=condition,
    )


def verify(candidate, registry=None, **overrides):
    expected = {
        "expected_packet_sha256": candidate.packet_sha256,
        "expected_generation": GENERATION,
        "expected_basis_id": BASIS_ID,
        "expected_basis_sha256": BASIS_SHA256,
        "expected_role": ROLE,
        "expected_control_condition": CONDITION,
    }
    expected.update(overrides)
    return verify_admitted_vector_packet_binding(
        {candidate.packet_sha256: candidate} if registry is None else registry,
        **expected,
    )


class DatasetVectorPacketBindingGuardTests(unittest.TestCase):
    def test_exact_admitted_packet_object_and_wire_mapping_pass(self):
        admitted = packet()
        self.assertEqual(verify(admitted), admitted)
        mapped = asdict(admitted)
        mapped["q8_values"] = list(mapped["q8_values"])
        observed = verify(admitted, registry={admitted.packet_sha256: mapped})
        self.assertEqual(observed.packet_sha256, admitted.packet_sha256)

    def test_shared_trace_hash_without_admitted_packet_fails_closed(self):
        admitted = packet()
        with self.assertRaisesRegex(
            JSpaceDatasetVectorPacketBindingError,
            "VECTOR_CONTROL_PACKET_NOT_ADMITTED",
        ):
            verify(admitted, registry={})

    def test_byte_distinct_registry_value_cannot_reuse_packet_digest(self):
        admitted = packet()
        tampered = asdict(admitted)
        tampered["role"] = "critic"
        with self.assertRaisesRegex(
            JSpaceDatasetVectorPacketBindingError,
            "VECTOR_CONTROL_PACKET_INVALID:VECTOR_CONTROL_PACKET_DIGEST_MISMATCH",
        ):
            verify(admitted, registry={admitted.packet_sha256: tampered})

    def test_registry_key_cannot_alias_a_different_valid_packet(self):
        expected = packet()
        other = packet(role="critic")
        with self.assertRaisesRegex(
            JSpaceDatasetVectorPacketBindingError,
            "VECTOR_CONTROL_PACKET_IDENTITY_MISMATCH",
        ):
            verify(expected, registry={expected.packet_sha256: other})

    def test_self_consistent_packet_still_must_match_dataset_generation(self):
        admitted = packet(generation=GENERATION + 1)
        with self.assertRaisesRegex(
            JSpaceDatasetVectorPacketBindingError,
            "VECTOR_CONTROL_PACKET_GENERATION_MISMATCH",
        ):
            verify(admitted)

    def test_self_consistent_packet_still_must_match_dataset_basis(self):
        admitted = packet(basis_id="basis:other:7")
        with self.assertRaisesRegex(
            JSpaceDatasetVectorPacketBindingError,
            "VECTOR_CONTROL_PACKET_BASIS_ID_MISMATCH",
        ):
            verify(admitted)

        admitted = packet(basis_sha256="e" * 64)
        with self.assertRaisesRegex(
            JSpaceDatasetVectorPacketBindingError,
            "VECTOR_CONTROL_PACKET_BASIS_SHA256_MISMATCH",
        ):
            verify(admitted)

    def test_self_consistent_packet_still_must_match_dataset_role(self):
        admitted = packet(role="critic")
        with self.assertRaisesRegex(
            JSpaceDatasetVectorPacketBindingError,
            "VECTOR_CONTROL_PACKET_ROLE_MISMATCH",
        ):
            verify(admitted)

    def test_shared_control_label_cannot_override_packet_condition(self):
        admitted = packet(condition="BASELINE")
        with self.assertRaisesRegex(
            JSpaceDatasetVectorPacketBindingError,
            "VECTOR_CONTROL_PACKET_CONDITION_MISMATCH",
        ):
            verify(admitted, expected_control_condition="LESION")


if __name__ == "__main__":
    unittest.main()
