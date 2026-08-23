import json
import math
import struct
import unittest

from entry_canonicalization_v1 import CanonicalizationError, canonicalize


# Complete RFC 8785 Appendix B finite-number sample set. NaN/Infinity are
# separately covered by test_nonfinite_numbers_fail_closed.
NUMBER_VECTORS = [
    ("0000000000000000", "0"),
    ("8000000000000000", "0"),
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

    def test_integer_input_stays_inside_ijson_safe_domain(self):
        self.assertEqual(canonicalize(9007199254740991), b"9007199254740991")
        with self.assertRaisesRegex(CanonicalizationError, "IJSON_SAFE_RANGE"):
            canonicalize(9007199254740992)

    def test_lone_surrogate_fails_closed(self):
        with self.assertRaisesRegex(CanonicalizationError, "LONE_SURROGATE"):
            canonicalize({"x": "\ud800"})


if __name__ == "__main__":
    unittest.main()
