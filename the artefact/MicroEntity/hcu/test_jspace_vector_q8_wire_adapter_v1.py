import unittest
from dataclasses import replace

import jspace_vector_control_v1 as legacy
from jspace_vector_q8_wire_adapter_v1 import (
    CANONICAL_MAIN_TRIGGER1_DESCRIPTOR_SCHEMA,
    LEGACY_COLLIDING_DONOR_ABI_SCHEMA,
    Q8_WIRE_ABI_SCHEMA,
    JSpaceQ8WireAdapterError,
    decode_q8_wire,
    encode_q8_wire,
    migrate_legacy_packet,
    validate_q8_wire_packet,
)


BASIS_ID = "basis:q8-wire-adapter:test"
BASIS_SHA256 = "a" * 64
GENERATION = 872
ROLE = "critic"


class JSpaceVectorQ8WireAdapterTests(unittest.TestCase):
    def _legacy(self):
        return legacy.encode_vector(
            (1.0, -0.5, 0.25),
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
        )

    def test_namespace_is_explicitly_noncolliding(self):
        self.assertEqual(legacy.ABI_SCHEMA, LEGACY_COLLIDING_DONOR_ABI_SCHEMA)
        self.assertEqual(
            CANONICAL_MAIN_TRIGGER1_DESCRIPTOR_SCHEMA,
            LEGACY_COLLIDING_DONOR_ABI_SCHEMA,
        )
        self.assertNotEqual(Q8_WIRE_ABI_SCHEMA, CANONICAL_MAIN_TRIGGER1_DESCRIPTOR_SCHEMA)
        self.assertEqual(Q8_WIRE_ABI_SCHEMA, "JSPACE_VECTOR_Q8_WIRE_ABI/v1")

    def test_migration_changes_only_namespace_and_digest_identity(self):
        historical = self._legacy()
        migrated = migrate_legacy_packet(historical)
        validate_q8_wire_packet(migrated)

        self.assertEqual(historical.abi_schema, LEGACY_COLLIDING_DONOR_ABI_SCHEMA)
        self.assertEqual(migrated.abi_schema, Q8_WIRE_ABI_SCHEMA)
        self.assertNotEqual(historical.packet_sha256, migrated.packet_sha256)
        self.assertNotEqual(legacy.packet_bytes(historical), legacy.packet_bytes(migrated))

        ignored = {"abi_schema", "packet_sha256"}
        old_fields = {k: v for k, v in historical.__dict__.items() if k not in ignored}
        new_fields = {k: v for k, v in migrated.__dict__.items() if k not in ignored}
        self.assertEqual(old_fields, new_fields)

    def test_new_wire_is_not_accepted_by_legacy_namespace_validator(self):
        migrated = migrate_legacy_packet(self._legacy())
        with self.assertRaisesRegex(legacy.JSpaceVectorControlError, "VECTOR_CONTROL_SCHEMA_UNSUPPORTED"):
            legacy.validate_packet(migrated)

    def test_legacy_wire_is_not_accepted_as_new_wire(self):
        historical = self._legacy()
        with self.assertRaisesRegex(JSpaceQ8WireAdapterError, "Q8_WIRE_ABI_SCHEMA_REQUIRED"):
            validate_q8_wire_packet(historical)

    def test_encode_decode_preserves_existing_semantic_fences(self):
        packet = encode_q8_wire(
            (1.0, -0.5, 0.25),
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
        )
        decoded = decode_q8_wire(
            packet,
            current_generation=GENERATION,
            expected_basis_id=BASIS_ID,
            expected_basis_sha256=BASIS_SHA256,
            expected_role=ROLE,
        )
        self.assertEqual(len(decoded), 3)
        self.assertLessEqual(
            legacy.reconstruction_metrics((1.0, -0.5, 0.25), decoded)["normalized_max_error"],
            1.0 / 254.0 + 1e-15,
        )

        with self.assertRaisesRegex(legacy.JSpaceVectorControlError, "STALE_VECTOR_CONTROL_GENERATION"):
            decode_q8_wire(
                packet,
                current_generation=GENERATION + 1,
                expected_basis_id=BASIS_ID,
                expected_basis_sha256=BASIS_SHA256,
                expected_role=ROLE,
            )

    def test_new_wire_digest_tamper_fails_before_legacy_semantics(self):
        packet = encode_q8_wire(
            (1.0, -0.5),
            basis_id=BASIS_ID,
            basis_sha256=BASIS_SHA256,
            generation=GENERATION,
            role=ROLE,
        )
        tampered = replace(packet, q8_values=(126, packet.q8_values[1]))
        with self.assertRaisesRegex(JSpaceQ8WireAdapterError, "Q8_WIRE_PACKET_DIGEST_MISMATCH"):
            validate_q8_wire_packet(tampered)


if __name__ == "__main__":
    unittest.main()
