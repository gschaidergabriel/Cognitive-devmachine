import math
import unittest

from typed_canonical_v1 import CanonicalizationError, canonical_bytes, canonical_sha256


class TypedCanonicalTests(unittest.TestCase):
    def test_mapping_order_does_not_change_bytes_or_digest(self):
        a = {"b": 2, "a": [True, None, 1.5]}
        b = {"a": [True, None, 1.5], "b": 2}
        self.assertEqual(canonical_bytes(a, domain="test"), canonical_bytes(b, domain="test"))
        self.assertEqual(canonical_sha256(a, domain="test"), canonical_sha256(b, domain="test"))

    def test_domain_separation_changes_identity(self):
        value = {"same": 1}
        self.assertNotEqual(
            canonical_sha256(value, domain="event"),
            canonical_sha256(value, domain="policy"),
        )

    def test_int_and_float_are_distinct_typed_values(self):
        self.assertNotEqual(
            canonical_bytes({"v": 1}, domain="typed"),
            canonical_bytes({"v": 1.0}, domain="typed"),
        )

    def test_negative_zero_normalizes_to_positive_zero(self):
        self.assertEqual(
            canonical_bytes({"v": -0.0}, domain="typed"),
            canonical_bytes({"v": 0.0}, domain="typed"),
        )

    def test_nonfinite_float_fails_closed(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaisesRegex(CanonicalizationError, "FINITE_BINARY64_REQUIRED"):
                    canonical_bytes({"v": value}, domain="typed")

    def test_lone_surrogate_fails_closed(self):
        with self.assertRaisesRegex(CanonicalizationError, "VALID_UNICODE_REQUIRED"):
            canonical_bytes({"v": "\ud800"}, domain="typed")

    def test_unsupported_type_fails_closed(self):
        with self.assertRaisesRegex(CanonicalizationError, "UNSUPPORTED_TYPE"):
            canonical_bytes({"v": {1, 2}}, domain="typed")

    def test_sequence_order_is_preserved(self):
        self.assertNotEqual(
            canonical_bytes(["a", "b"], domain="typed"),
            canonical_bytes(["b", "a"], domain="typed"),
        )

    def test_string_key_utf8_order_is_deterministic(self):
        a = {"€": 1, "a": 2, "ö": 3}
        b = {"ö": 3, "€": 1, "a": 2}
        self.assertEqual(canonical_bytes(a, domain="typed"), canonical_bytes(b, domain="typed"))


if __name__ == "__main__":
    unittest.main()
