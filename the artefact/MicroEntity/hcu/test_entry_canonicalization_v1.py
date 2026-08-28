import json
import math
import struct
import unittest

from entry_canonicalization_v1 import (
    MAX_CANONICAL_NESTING_DEPTH,
    CanonicalizationError,
    canonicalize,
)


# RFC 8785 Appendix B finite-number sample set, excluding minus zero.
# Appendix B documents its serializer image as "0", but verified erratum
# EID 7920 says parsers SHOULD reject -0 to avoid signed-zero alias attacks.
# NaN/Infinity are separately covered by test_nonfinite_numbers_fail_closed.
NUMBER_VECTORS = [
    ("0000000000000000", "0"),
    ("0000000000000001", "5e-324"),
    ("8000000000000001", "-5e-324"),
    ("7fefffffffffffff", "1.7976931348623157e+308"),
    ("ffefffffffffffff", "-1.7976931348623157e+308"),
    ("4340000000000000", "9007199254740992"),
    ("c340000000000000", "-9007199254740992"),
    ("4430000000000000", "295147905179352830000"),
    ("44b52d02c7e14af5", "9.999999999999997e+22"),
    ("44b52d02c7e14af6", "1e+23"),
    ("44b52d02c7e14af7", "1.0000000000000001e+23"),
    ("444b1ae4d6e2ef4e", "999999999999999700000"),
    ("444b1ae4d6e2ef4f", "999999999999999900000"),
    ("444b1ae4d6e2ef50", "1e+21"),
    ("3eb0c6f7a0b5ed8c", "9.999999999999997e-7"),
    ("3eb0c6f7a0b5ed8d", "0.000001"),
    ("41b3de4355555553", "333333333.3333332"),
    ("41b3de4355555554", "333333333.33333325"),
    ("41b3de4355555555", "333333333.3333333"),
    ("41b3de4355555556", "333333333.3333334"),
    ("41b3de4355555557", "333333333.33333343"),
    ("becbf647612f3696", "-0.0000033333333333333333"),
    ("43143ff3c1cb0959", "1424953923781206.2"),
]


def f64(hex_value):
    return struct.unpack(">d", bytes.fromhex(hex_value))[0]


class EntryCanonicalizationTests(unittest.TestCase):
    def test_rfc8785_number_vectors(self):
        for hex_value, expected in NUMBER_VECTORS:
            self.assertEqual(
                canonicalize(f64(hex_value)).decode("utf-8"),
                expected,
                (hex_value, repr(f64(hex_value))),
            )

    def test_negative_zero_fails_closed_per_verified_erratum_7920(self):
        negative_zero = f64("8000000000000000")
        self.assertEqual(negative_zero, 0.0)
        self.assertLess(math.copysign(1.0, negative_zero), 0.0)
        with self.assertRaisesRegex(CanonicalizationError, "NEGATIVE_ZERO_FORBIDDEN"):
            canonicalize(negative_zero)
        self.assertEqual(canonicalize(0.0), b"0")

    def test_nonfinite_numbers_fail_closed(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.assertRaises(CanonicalizationError):
                canonicalize(value)

    def test_rfc8785_utf16_property_order(self):
        obj = {
            "\u20ac": "Euro Sign",
            "\r": "Carriage Return",
            "\ufb33": "Hebrew Letter Dalet With Dagesh",
            "1": "One",
            "😀": "Emoji: Grinning Face",
            "\u0080": "Control",
            "ö": "Latin Small Letter O With Diaeresis",
        }
        values = list(json.loads(canonicalize(obj).decode("utf-8")).values())
        self.assertEqual(
            values,
            [
                "Carriage Return",
                "One",
                "Control",
                "Latin Small Letter O With Diaeresis",
                "Euro Sign",
                "Emoji: Grinning Face",
                "Hebrew Letter Dalet With Dagesh",
            ],
        )

    def test_property_reordering_is_identity_neutral(self):
        self.assertEqual(
            canonicalize({"b": 1, "a": [3, 2, 1]}),
            canonicalize({"a": [3, 2, 1], "b": 1}),
        )

    def test_integer_input_uses_exact_binary64_semantics_not_host_safe_int_policy(self):
        # RFC 8785 Appendix B includes 2^53 as a valid Number serialization; the
        # safe-integer range is a SHOULD for application data, not a JCS algorithm gate.
        self.assertEqual(canonicalize(9007199254740991), b"9007199254740991")
        self.assertEqual(canonicalize(9007199254740992), b"9007199254740992")
        self.assertEqual(canonicalize(9007199254740992), canonicalize(float(9007199254740992)))

        # 2^68 is exactly representable as binary64 but ECMAScript/JCS chooses this
        # shortest decimal wire representation rather than Python's integer spelling.
        two_to_68 = 1 << 68
        self.assertEqual(canonicalize(two_to_68), b"295147905179352830000")
        self.assertEqual(canonicalize(two_to_68), canonicalize(float(two_to_68)))

        # 2^53+1 is not exactly representable as binary64; silently rounding it would
        # violate the admitted I-JSON value before canonicalization.
        with self.assertRaisesRegex(CanonicalizationError, "INTEGER_NOT_EXACT_BINARY64"):
            canonicalize(9007199254740993)

    def test_lone_surrogate_fails_closed(self):
        with self.assertRaisesRegex(CanonicalizationError, "LONE_SURROGATE"):
            canonicalize({"x": "\ud800"})

    def test_nesting_depth_boundary_fails_through_typed_channel(self):
        admitted = 0
        for _ in range(MAX_CANONICAL_NESTING_DEPTH):
            admitted = [admitted]
        canonicalize(admitted)

        rejected = [admitted]
        with self.assertRaisesRegex(CanonicalizationError, "MAX_NESTING_DEPTH_EXCEEDED"):
            canonicalize(rejected)

    def test_extreme_nesting_does_not_leak_python_recursion_error(self):
        value = 0
        for _ in range(5000):
            value = [value]
        with self.assertRaisesRegex(CanonicalizationError, "MAX_NESTING_DEPTH_EXCEEDED"):
            canonicalize(value)


if __name__ == "__main__":
    unittest.main()
