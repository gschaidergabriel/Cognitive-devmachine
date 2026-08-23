import unittest

import jspace_vector_control_abi_v1 as compat
import jspace_vector_control_v1 as canonical

BASIS_ID = "basis:test:42"
BASIS_SHA256 = "a" * 64
GENERATION = 91
ROLE = "critic"


class VectorControlABICompatibilityTests(unittest.TestCase):
    def test_compatibility_module_reexports_the_single_canonical_abi(self):
        self.assertEqual(compat.ABI_SCHEMA, canonical.ABI_SCHEMA)
        self.assertEqual(compat.PACKET_SCHEMA, canonical.PACKET_SCHEMA)
        self.assertEqual(compat.CODEC_SCHEMA, canonical.CODEC_SCHEMA)
        self.assertEqual(compat.WIRE_FORMAT, canonical.WIRE_FORMAT)
        self.assertIs(compat.VectorControlPacket, canonical.VectorControlPacket)

    def test_compatibility_encode_uses_exact_canonical_packet_identity(self):
        kwargs = dict(
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
            control_condition="LESION",
        )
        via_compat = compat.encode_vector((0.5, -1.0, 0.25, 0.0), **kwargs)
        direct = canonical.encode_vector((0.5, -1.0, 0.25, 0.0), **kwargs)
        self.assertEqual(via_compat, direct)
        self.assertEqual(compat.packet_bytes(via_compat), canonical.packet_bytes(direct))
        self.assertEqual(compat.packet_text(via_compat), canonical.packet_text(direct))

    def test_compatibility_parser_accepts_only_canonical_wire(self):
        packet = canonical.encode_vector(
            (0.125, -0.25, 0.5, -1.0),
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
        )
        parsed = compat.parse_packet_text(canonical.packet_text(packet))
        self.assertEqual(parsed, packet)
        decoded = compat.decode_vector(
            parsed,
            current_generation=GENERATION,
            expected_basis_id=BASIS_ID,
            expected_basis_sha256=BASIS_SHA256,
            expected_role=ROLE,
        )
        self.assertEqual(len(decoded), packet.dimension)

    def test_retired_second_wire_constructor_fails_closed(self):
        with self.assertRaisesRegex(
            canonical.JSpaceVectorControlError,
            "LEGACY_VECTOR_CONTROL_CONSTRUCTOR_RETIRED_USE_ENCODE_VECTOR",
        ):
            compat.encode_vector_control(
                [0.5, -1.0],
                basis_id="B42",
                role=ROLE,
                generation=GENERATION,
                gate=0.6,
                workspace_refs=["w:a"],
                lesion_indices=[1],
            )

    def test_retired_second_wire_decoder_fails_closed(self):
        with self.assertRaisesRegex(
            canonical.JSpaceVectorControlError,
            "LEGACY_VECTOR_CONTROL_DECODER_RETIRED_USE_PARSE_PACKET_TEXT_AND_DECODE_VECTOR",
        ):
            compat.decode_vector_control(b"<jctl:v1>{}</jctl>")


if __name__ == "__main__":
    unittest.main()
