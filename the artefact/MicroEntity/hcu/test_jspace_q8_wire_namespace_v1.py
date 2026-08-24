import unittest
from dataclasses import replace

from jspace_vector_control_v1 import (
    ABI_SCHEMA,
    LEGACY_COLLIDING_ABI_SCHEMA,
    JSpaceVectorControlError,
    encode_vector,
    validate_packet,
)


class JSpaceQ8WireNamespaceTests(unittest.TestCase):
    def test_q8_wire_abi_is_explicitly_noncolliding(self):
        self.assertEqual(ABI_SCHEMA, "JSPACE_Q8_VECTOR_CONTROL_WIRE_ABI/v1")
        self.assertEqual(LEGACY_COLLIDING_ABI_SCHEMA, "JSPACE_VECTOR_CONTROL_ABI/v1")
        self.assertNotEqual(ABI_SCHEMA, LEGACY_COLLIDING_ABI_SCHEMA)

    def test_encoder_emits_only_noncolliding_q8_wire_abi(self):
        packet = encode_vector(
            (1.0, -0.5),
            basis_id="basis:test:namespace",
            basis_sha256="a" * 64,
            generation=1,
            role="critic",
        )
        self.assertEqual(packet.abi_schema, ABI_SCHEMA)
        self.assertNotEqual(packet.abi_schema, LEGACY_COLLIDING_ABI_SCHEMA)
        validate_packet(packet)

    def test_historical_colliding_abi_is_not_accepted_as_wire_alias(self):
        packet = encode_vector(
            (1.0, -0.5),
            basis_id="basis:test:namespace",
            basis_sha256="a" * 64,
            generation=1,
            role="critic",
        )
        colliding = replace(packet, abi_schema=LEGACY_COLLIDING_ABI_SCHEMA)
        with self.assertRaisesRegex(JSpaceVectorControlError, "VECTOR_CONTROL_SCHEMA_UNSUPPORTED"):
            validate_packet(colliding)


if __name__ == "__main__":
    unittest.main()
