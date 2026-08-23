import importlib.util
import pathlib
import unittest


MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "hcu_typed_canonical_v1.py"
SPEC = importlib.util.spec_from_file_location("hcu_typed_canonical_v1", MODULE_PATH)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)

CanonicalizationError = module.CanonicalizationError
canonical_bytes = module.canonical_bytes
identity_sha256 = module.identity_sha256


class TypedCanonicalV1Tests(unittest.TestCase):
    def test_ascii_object_key_order_is_invariant(self):
        a = {"z": 1, "a": 2, "nested": {"b": True, "a": None}}
        b = {"nested": {"a": None, "b": True}, "a": 2, "z": 1}
        expected = b'{"a":2,"nested":{"a":null,"b":true},"z":1}'
        self.assertEqual(canonical_bytes(a), expected)
        self.assertEqual(canonical_bytes(a), canonical_bytes(b))
        self.assertEqual(identity_sha256(a), identity_sha256(b))

    def test_exact_replay_is_stable(self):
        value = {"schema": "HCU_ROUTE/v3", "generation": 17, "lanes": ["world", "critic"]}
        self.assertEqual(identity_sha256(value), identity_sha256(value))

    def test_floats_fail_closed_in_identity_domain(self):
        with self.assertRaisesRegex(CanonicalizationError, "FLOAT_FORBIDDEN"):
            canonical_bytes({"novelty": 0.55})

    def test_safe_integer_boundary(self):
        canonical_bytes({"n": 2**53 - 1})
        with self.assertRaisesRegex(CanonicalizationError, "INTEGER_OUTSIDE_IJSON_SAFE_RANGE"):
            canonical_bytes({"n": 2**53})

    def test_non_ascii_object_keys_fail_closed(self):
        with self.assertRaisesRegex(CanonicalizationError, "OBJECT_KEY_PRINTABLE_ASCII_REQUIRED"):
            canonical_bytes({"€": "value"})

    def test_unicode_values_are_preserved_not_normalized(self):
        composed = {"value": "é"}
        decomposed = {"value": "e\u0301"}
        self.assertNotEqual(canonical_bytes(composed), canonical_bytes(decomposed))
        self.assertNotEqual(identity_sha256(composed), identity_sha256(decomposed))

    def test_surrogate_values_fail_closed(self):
        with self.assertRaisesRegex(CanonicalizationError, "UNICODE_SURROGATE_FORBIDDEN"):
            canonical_bytes({"value": "\ud800"})

    def test_control_escape_bytes_are_fixed(self):
        self.assertEqual(
            canonical_bytes({"value": "\b\t\n\f\r\u0001\\\""}),
            b'{"value":"\\b\\t\\n\\f\\r\\u0001\\\\\\\""}',
        )

    def test_bool_does_not_alias_integer(self):
        self.assertNotEqual(canonical_bytes(True), canonical_bytes(1))
        self.assertNotEqual(identity_sha256(True), identity_sha256(1))

    def test_domain_rejects_opaque_objects(self):
        with self.assertRaisesRegex(CanonicalizationError, "TYPE_OUTSIDE_TYPED_CANONICAL_DOMAIN"):
            canonical_bytes({"value": object()})


if __name__ == "__main__":
    unittest.main()
