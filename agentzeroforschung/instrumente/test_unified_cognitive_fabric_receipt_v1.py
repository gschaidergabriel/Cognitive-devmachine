#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import unittest

from validate_unified_cognitive_fabric_receipt_v1 import (
    RECEIPT_VERSION,
    ReceiptError,
    canonical_digest,
    validate,
    validate_receipt,
)

ROOT = Path(__file__).resolve().parents[2]
_FIXTURE_SPEC = importlib.util.spec_from_file_location(
    "canonical_ucf_fixture", ROOT / "tests" / "test_unified_cognitive_fabric_receipt_v1.py"
)
if _FIXTURE_SPEC is None or _FIXTURE_SPEC.loader is None:
    raise RuntimeError("CANONICAL_UCF_TEST_FIXTURE_IMPORT_FAILED")
_FIXTURE = importlib.util.module_from_spec(_FIXTURE_SPEC)
_FIXTURE_SPEC.loader.exec_module(_FIXTURE)


def valid_receipt() -> dict:
    return _FIXTURE.valid_receipt()


class UnifiedCognitiveFabricCompatibilityEntryPointTests(unittest.TestCase):
    def test_canonical_receipt_has_identical_admission_through_legacy_entrypoint(self) -> None:
        receipt = valid_receipt()
        self.assertEqual(RECEIPT_VERSION, receipt["schema"])
        self.assertEqual(validate_receipt(receipt), [])
        self.assertEqual(validate(receipt)["receipt_digest"], receipt["receipt_envelope_digest"])

    def test_legacy_parallel_v1_shape_is_not_a_second_authority(self) -> None:
        legacy_shape = {"receipt_version": RECEIPT_VERSION}
        self.assertEqual(validate_receipt(legacy_shape), ["SCHEMA_MISMATCH"])
        with self.assertRaisesRegex(ReceiptError, "SCHEMA_MISMATCH"):
            validate(legacy_shape)

    def test_fail_closed_error_is_canonical_not_reimplemented(self) -> None:
        receipt = valid_receipt()
        receipt["source"]["dirty"] = True
        receipt["receipt_envelope_digest"] = canonical_digest(receipt)
        self.assertEqual(validate_receipt(receipt), ["SOURCE_DIRTY_OR_UNKNOWN"])
        with self.assertRaisesRegex(ReceiptError, "SOURCE_DIRTY_OR_UNKNOWN"):
            validate(receipt)

    def test_envelope_mutation_behavior_matches_canonical_validator(self) -> None:
        receipt = valid_receipt()
        mutated = copy.deepcopy(receipt)
        mutated["workspace"]["thalamus_gate_decisions"] = ["tampered"]
        self.assertEqual(validate_receipt(mutated), ["RECEIPT_ENVELOPE_DIGEST_MISMATCH"])

    def test_nonfinite_json_remains_fail_closed(self) -> None:
        receipt = valid_receipt()
        receipt["telemetry"] = {"score": float("nan")}
        self.assertEqual(validate_receipt(receipt), ["NONFINITE_JSON:$.telemetry.score"])


if __name__ == "__main__":
    unittest.main()
