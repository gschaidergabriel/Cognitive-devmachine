import unittest
from unittest.mock import patch

import jspace_vector_control_text_admission_v1 as admission
from jspace_vector_control_v1 import encode_vector, packet_text


class JSpaceVectorControlTextAdmissionTests(unittest.TestCase):
    def test_canonical_packet_is_delegated_without_wire_change(self):
        packet = encode_vector(
            (0.25, -1.0, 0.5),
            basis_id="basis:text-admission:test",
            basis_sha256="a" * 64,
            generation=7,
            role="critic",
        )
        text = packet_text(packet)
        admitted = admission.admit_packet_text(text)
        self.assertEqual(admitted, packet)
        self.assertEqual(admission.ABI_SCHEMA, "JSPACE_VECTOR_CONTROL_ABI/v1")
        self.assertEqual(admission.WIRE_FORMAT, "RFC8785_JCS_JSON_UTF8")

    def test_oversized_text_is_rejected_before_canonical_json_parser(self):
        oversized = "x" * (admission.MAX_PACKET_TEXT_CHARS + 1)
        with patch.object(
            admission,
            "_parse_packet_text",
            side_effect=AssertionError("canonical parser must not run"),
        ):
            with self.assertRaisesRegex(
                admission.JSpaceVectorControlError,
                "VECTOR_CONTROL_TEXT_CHAR_BUDGET_EXCEEDED",
            ):
                admission.admit_packet_text(oversized)

    def test_non_utf8_scalar_is_rejected_before_canonical_json_parser(self):
        surrogate = chr(0xD800)
        with patch.object(
            admission,
            "_parse_packet_text",
            side_effect=AssertionError("canonical parser must not run"),
        ):
            with self.assertRaisesRegex(
                admission.JSpaceVectorControlError,
                "VECTOR_CONTROL_TEXT_UTF8_REQUIRED",
            ):
                admission.admit_packet_text(surrogate)

    def test_canonical_parser_recursion_is_normalized_to_domain_rejection(self):
        with patch.object(
            admission,
            "_parse_packet_text",
            side_effect=RecursionError("decoder nesting limit"),
        ):
            with self.assertRaisesRegex(
                admission.JSpaceVectorControlError,
                "VECTOR_CONTROL_TEXT_JSON_DEPTH_EXCEEDED",
            ):
                admission.admit_packet_text("{}")

    def test_deep_json_within_text_budget_never_leaks_recursion_error(self):
        depth = 10_000
        nested = "[" * depth + "0" + "]" * depth
        self.assertLess(len(nested), admission.MAX_PACKET_TEXT_CHARS)
        try:
            admission.admit_packet_text(nested)
        except admission.JSpaceVectorControlError:
            pass
        except RecursionError as exc:  # pragma: no cover - explicit regression sentinel
            self.fail(f"raw RecursionError escaped bounded admission: {exc}")
        else:
            self.fail("deep non-packet JSON unexpectedly admitted")

    def test_empty_or_non_text_input_fails_closed(self):
        for value in ("", None, b"{}"):
            with self.assertRaisesRegex(
                admission.JSpaceVectorControlError,
                "VECTOR_CONTROL_TEXT_REQUIRED",
            ):
                admission.admit_packet_text(value)


if __name__ == "__main__":
    unittest.main()
