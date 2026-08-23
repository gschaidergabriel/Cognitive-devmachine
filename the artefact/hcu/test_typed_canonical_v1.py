import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from typed_canonical_v1 import (
    SCHEMA,
    TypedCanonicalizationError,
    canonical_bytes,
    canonical_sha256,
    strict_loads,
)


class TypedCanonicalTests(unittest.TestCase):
    def test_object_key_order_is_canonical(self):
        a = {"z": 1, "a": {"y": 2, "b": 3}}
        b = {"a": {"b": 3, "y": 2}, "z": 1}
        self.assertEqual(canonical_bytes(a), canonical_bytes(b))
        self.assertEqual(canonical_sha256(a), canonical_sha256(b))

    def test_array_order_remains_material(self):
        self.assertNotEqual(canonical_sha256([1, 2]), canonical_sha256([2, 1]))

    def test_duplicate_json_key_fails_closed(self):
        with self.assertRaisesRegex(TypedCanonicalizationError, "DUPLICATE_OBJECT_KEY"):
            strict_loads('{"a":1,"a":2}')

    def test_float_fails_closed(self):
        with self.assertRaisesRegex(TypedCanonicalizationError, "FLOAT_FORBIDDEN"):
            canonical_sha256({"uncertainty": 0.5})
        with self.assertRaisesRegex(TypedCanonicalizationError, "FLOAT_FORBIDDEN"):
            strict_loads('{"uncertainty":0.5}')

    def test_safe_integer_boundary(self):
        canonical_sha256({"n": 9007199254740991})
        with self.assertRaisesRegex(TypedCanonicalizationError, "INTEGER_OUTSIDE_SAFE_RANGE"):
            canonical_sha256({"n": 9007199254740992})

    def test_non_ascii_structural_key_fails_closed(self):
        with self.assertRaisesRegex(TypedCanonicalizationError, "ASCII_DOMAIN"):
            canonical_sha256({"ä": 1})

    def test_unicode_values_are_not_normalized(self):
        composed = {"value": "é"}
        decomposed = {"value": "e\u0301"}
        self.assertNotEqual(canonical_bytes(composed), canonical_bytes(decomposed))
        self.assertNotEqual(canonical_sha256(composed), canonical_sha256(decomposed))

    def test_boolean_is_not_integer_alias(self):
        self.assertNotEqual(canonical_sha256({"v": True}), canonical_sha256({"v": 1}))

    def test_schema_version_is_bound_into_hash_preimage(self):
        payload = {"generation": 7, "causal_id": "ct1:g7:a1"}
        raw = canonical_bytes(payload)
        schema_bound = canonical_sha256(payload)
        self.assertEqual(SCHEMA, "ENTITYOS_TYPED_CANONICAL_JSON/v1")
        self.assertNotEqual(schema_bound, __import__("hashlib").sha256(raw).hexdigest())


if __name__ == "__main__":
    unittest.main()
