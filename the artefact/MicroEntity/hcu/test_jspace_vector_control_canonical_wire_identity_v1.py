import unittest
from dataclasses import replace

from jspace_vector_control_v1 import (
    JSpaceVectorControlError,
    _canonical_sha256,
    _packet_material,
    encode_vector,
    validate_packet,
)


BASIS_SHA256 = "a" * 64
GENERATION = 91


class JSpaceVectorControlCanonicalWireIdentityTests(unittest.TestCase):
    def _packet(self):
        return encode_vector(
            (1.0, -0.5),
            basis_id="basis:test:canonical",
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role="critic",
        )

    def _rehash(self, packet):
        return replace(
            packet,
            packet_sha256=_canonical_sha256(_packet_material(packet), "VECTOR_CONTROL_PACKET"),
        )

    def test_encoder_normalizes_boundary_text_but_emits_one_canonical_wire_identity(self):
        packet = encode_vector(
            (1.0, -0.5),
            basis_id="  basis:test:canonical  ",
            basis_sha256=f"  {BASIS_SHA256}  ",
            generation=GENERATION,
            role="  critic  ",
        )
        self.assertEqual(packet.basis_id, "basis:test:canonical")
        self.assertEqual(packet.basis_sha256, BASIS_SHA256)
        self.assertEqual(packet.role, "critic")
        validate_packet(packet)

    def test_self_consistent_padded_basis_id_fails_closed(self):
        poisoned = self._rehash(replace(self._packet(), basis_id=" basis:test:canonical "))
        with self.assertRaisesRegex(JSpaceVectorControlError, "basis_id:NONCANONICAL_TEXT"):
            validate_packet(poisoned)

    def test_self_consistent_padded_role_fails_closed(self):
        poisoned = self._rehash(replace(self._packet(), role=" critic "))
        with self.assertRaisesRegex(JSpaceVectorControlError, "role:NONCANONICAL_TEXT"):
            validate_packet(poisoned)

    def test_self_consistent_padded_basis_digest_fails_closed(self):
        poisoned = self._rehash(replace(self._packet(), basis_sha256=f" {BASIS_SHA256} "))
        with self.assertRaisesRegex(JSpaceVectorControlError, "basis_sha256:NONCANONICAL_SHA256"):
            validate_packet(poisoned)

    def test_self_consistent_padded_source_digest_fails_closed(self):
        packet = self._packet()
        poisoned = self._rehash(
            replace(packet, source_vector_sha256=f" {packet.source_vector_sha256} ")
        )
        with self.assertRaisesRegex(JSpaceVectorControlError, "source_vector_sha256:NONCANONICAL_SHA256"):
            validate_packet(poisoned)

    def test_padded_packet_digest_alias_fails_closed(self):
        packet = self._packet()
        poisoned = replace(packet, packet_sha256=f" {packet.packet_sha256} ")
        with self.assertRaisesRegex(JSpaceVectorControlError, "packet_sha256:NONCANONICAL_SHA256"):
            validate_packet(poisoned)


if __name__ == "__main__":
    unittest.main()
