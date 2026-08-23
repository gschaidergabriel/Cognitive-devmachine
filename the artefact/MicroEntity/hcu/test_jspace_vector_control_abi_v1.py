import math
import struct
import unittest

from jspace_vector_control_abi_v1 import (
    JSpaceVectorControlError,
    PACKET_PREFIX,
    PACKET_SUFFIX,
    decode_vector_control,
    encode_vector_control,
)


class VectorControlABITests(unittest.TestCase):
    def make(self, **kwargs):
        params = dict(
            vector=[0.5, -1.0, 0.25, 0.0],
            basis_id="B42",
            role="critic",
            generation=91,
            gate=0.6,
            workspace_refs=["w:b", "w:a"],
            lesion_indices=[],
        )
        params.update(kwargs)
        return encode_vector_control(**params)

    def decode(self, packet, **kwargs):
        params = dict(expected_basis_id="B42", current_generation=91, expected_role="critic")
        params.update(kwargs)
        raw = packet.packet_bytes if hasattr(packet, "packet_bytes") else packet
        return decode_vector_control(raw, **params)

    def test_deterministic_order_normalization(self):
        a = self.make(workspace_refs=["w:b", "w:a"], lesion_indices=[3, 1])
        b = self.make(workspace_refs=["w:a", "w:b", "w:a"], lesion_indices=[1, 3, 1])
        self.assertEqual(a.packet_bytes, b.packet_bytes)
        self.assertEqual(a.packet_sha256, b.packet_sha256)

    def test_reconstruction_error_is_quantization_bounded(self):
        packet = self.make()
        decoded = self.decode(packet)
        scale = struct.unpack(">d", bytes.fromhex(packet.scale_f64_be_hex))[0]
        for source, restored in zip([0.5, -1.0, 0.25, 0.0], decoded.vector):
            self.assertLessEqual(abs(source - restored), scale / 2.0 + 1e-12)

    def test_null_vector_roundtrip(self):
        packet = self.make(vector=[0.0, -0.0, 0.0])
        decoded = self.decode(packet)
        self.assertTrue(decoded.null_vector)
        self.assertEqual(decoded.vector, (0.0, 0.0, 0.0))

    def test_wrong_basis_fails_closed(self):
        with self.assertRaisesRegex(JSpaceVectorControlError, "WRONG_JSPACE_BASIS"):
            self.decode(self.make(), expected_basis_id="B43")

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(JSpaceVectorControlError, "STALE_ENTITY_GENERATION"):
            self.decode(self.make(), current_generation=92)

    def test_role_swap_fails_closed(self):
        with self.assertRaisesRegex(JSpaceVectorControlError, "ROLE_MISMATCH"):
            self.decode(self.make(), expected_role="planner")

    def test_lesion_is_bound_and_zeroes_coordinate(self):
        base = self.make()
        lesioned = self.make(lesion_indices=[1])
        decoded = self.decode(lesioned)
        self.assertEqual(decoded.vector[1], 0.0)
        self.assertNotEqual(base.packet_sha256, lesioned.packet_sha256)

    def test_random_vector_changes_packet_identity(self):
        a = self.make(vector=[0.125, -0.25, 0.5, -1.0])
        b = self.make(vector=[-0.125, 0.25, -0.5, 1.0])
        self.assertNotEqual(a.packet_sha256, b.packet_sha256)
        self.assertEqual(a.packet_sha256, self.make(vector=[0.125, -0.25, 0.5, -1.0]).packet_sha256)

    def test_digest_tamper_fails_closed(self):
        packet = self.make()
        with self.assertRaisesRegex(JSpaceVectorControlError, "DIGEST_MISMATCH"):
            decode_vector_control(
                packet.packet_bytes,
                expected_basis_id="B42",
                current_generation=91,
                expected_role="critic",
                expected_packet_sha256="0" * 64,
            )

    def test_nonfinite_input_rejected(self):
        with self.assertRaisesRegex(JSpaceVectorControlError, "FINITE_BINARY64_REQUIRED"):
            self.make(vector=[0.0, math.inf])

    def test_gate_roundtrip_is_u8_bounded(self):
        decoded = self.decode(self.make(gate=0.6))
        self.assertLessEqual(abs(decoded.gate - 0.6), 0.5 / 255.0 + 1e-12)

    def test_packet_envelope_is_explicit(self):
        packet = self.make()
        self.assertTrue(packet.packet_bytes.startswith(PACKET_PREFIX))
        self.assertTrue(packet.packet_bytes.endswith(PACKET_SUFFIX))


if __name__ == "__main__":
    unittest.main()
