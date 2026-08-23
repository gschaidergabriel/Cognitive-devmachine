import math
import unittest

from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA as SELECTED_SCHEMA, canonicalize
from typed_entry_canonical_v1 import (
    ADAPTER_SCHEMA,
    CANONICALIZATION_SCHEMA,
    LEGACY_CANONICALIZATION_SCHEMA,
    CanonicalEncodingError,
    encode_canonical,
)


class TypedEntrySelectedCanonicalAdapterTests(unittest.TestCase):
    def test_adapter_exposes_exact_main_selected_schema(self):
        self.assertEqual(CANONICALIZATION_SCHEMA, "RFC8785_JCS_IJSON/v1")
        self.assertEqual(CANONICALIZATION_SCHEMA, SELECTED_SCHEMA)
        self.assertEqual(ADAPTER_SCHEMA, "ENTITYOS_HCU_ENTRY_CANONICAL_ADAPTER/v2")
        self.assertNotEqual(CANONICALIZATION_SCHEMA, LEGACY_CANONICALIZATION_SCHEMA)

    def test_entry_v2_shaped_values_are_byte_exact_with_selected_encoder(self):
        values = [
            {
                "schema": "ENTITYOS_HCU_ENTRY_EVENT_IDENTITY/v2",
                "canonicalization_schema": CANONICALIZATION_SCHEMA,
                "causal_id": "causal:adapter:κ",
                "entity_generation": 7,
                "source_kind": "HUMAN_PROMPT",
                "source_id": "user:test",
                "modality": "TEXT",
                "observed_time": "2026-08-23T16:24:00.000000Z",
                "provenance_ref": "unifieddb:source:test:1",
                "provenance_sha256": "a" * 64,
                "parent_id": None,
                "stream_id": "stream:test",
                "payload_sha256": "c" * 64,
            },
            {
                "schema": "ENTITYOS_HCU_ENTRY_ADMISSION_IDENTITY/v2",
                "canonicalization_schema": CANONICALIZATION_SCHEMA,
                "event_sha256": "d" * 64,
                "ingress_id": "ingress:test:1",
                "received_time": "2026-08-23T16:24:01.000000Z",
                "capabilities": ["hcu.route", "memory.read"],
                "capability_binding_sha256": "b" * 64,
                "budget": {"max_model_calls": 2, "max_tokens": 2048, "max_wall_ms": 5000},
                "payload_ref": "unifieddb:payload:test:1",
            },
            {"nested": [None, True, False, -24, 0, 24, 0.5, -0.0, "é", "😀"]},
        ]
        for value in values:
            self.assertEqual(encode_canonical(value), canonicalize(value))

    def test_mapping_input_order_does_not_change_bytes(self):
        left = {"z": 1, "aa": 2, "a": 3}
        right = {"a": 3, "z": 1, "aa": 2}
        self.assertEqual(encode_canonical(left), encode_canonical(right))

    def test_selected_number_domain_is_preserved(self):
        self.assertEqual(encode_canonical(7), canonicalize(7.0))
        self.assertEqual(encode_canonical(-0.0), b"0")
        for value in (math.inf, -math.inf, math.nan):
            with self.assertRaises(CanonicalEncodingError):
                encode_canonical(value)
        with self.assertRaises(CanonicalEncodingError):
            encode_canonical(9_007_199_254_740_993)

    def test_adapter_does_not_keep_hidden_legacy_byte_domain(self):
        with self.assertRaises(CanonicalEncodingError):
            encode_canonical(b"legacy-cbor-byte-string")


if __name__ == "__main__":
    unittest.main()
